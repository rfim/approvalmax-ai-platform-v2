#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


REPORT_DIR = Path("recovery")
REPORT_JSON = REPORT_DIR / "compliance_change_review.json"
REPORT_MD = REPORT_DIR / "compliance_change_review.md"

SECRET_PATH_TOKENS = {
    "auth.json",
    "profiles.yml",
    ".databrickscfg",
    ".env",
    "token",
    "secret",
    "credential",
}

GOVERNANCE_PATHS = {
    "src/dashboards/",
    "resources/dashboard_candidates/",
    "resources/app_candidates/",
    "metadata/",
    "models/",
    "sample_data/",
    "src/",
    "resources/",
    ".github/workflows/",
    "scripts/",
}

GDPR_RIGHTS = [
    "access",
    "rectification",
    "erasure",
    "right to be forgotten",
    "restriction",
    "portability",
    "objection",
    "automated decision",
    "profiling",
    "consent",
    "lawful basis",
    "retention",
]

SOC2_CONTROLS = {
    "change_management": [
        "databricks.yml",
        "resources/",
        "src/",
        "models/",
        ".github/workflows/",
        "scripts/",
    ],
    "processing_integrity": [
        "models/",
        "src/",
        "scripts/",
        "metadata/",
        "sample_data/",
    ],
    "confidentiality_privacy": [
        "src/dashboards/",
        "src/apps/",
        "resources/dashboard_candidates/",
        "resources/app_candidates/",
        "metadata/client_integrations.yml",
    ],
    "availability": [
        ".github/workflows/",
        "resources/",
        "databricks.yml",
    ],
}


def run_git(args: list[str]) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def changed_files(base: str, head: str) -> list[str]:
    output = run_git(["diff", "--name-only", f"{base}...{head}"])
    return [line for line in output.splitlines() if line.strip()]


def diff_text(base: str, head: str) -> str:
    return run_git(["diff", "--unified=0", f"{base}...{head}"])


def touches(path: str, prefixes: list[str] | tuple[str, ...] | set[str]) -> bool:
    return any(path == prefix.rstrip("/") or path.startswith(prefix) for prefix in prefixes)


def severity(statuses: list[str]) -> str:
    if "failed" in statuses:
        return "failed"
    if "warning" in statuses:
        return "warning"
    return "passed"


def add_check(checks: list[dict], name: str, status: str, framework: str, details: str) -> None:
    checks.append(
        {
            "name": name,
            "status": status,
            "framework": framework,
            "details": details,
        }
    )


def review(base: str, head: str) -> dict:
    files = changed_files(base, head)
    diff = diff_text(base, head)
    lower_diff = diff.lower()
    checks: list[dict] = []

    changed_governance_files = [path for path in files if touches(path, GOVERNANCE_PATHS)]
    add_check(
        checks,
        "governance_relevant_change_detected",
        "warning" if changed_governance_files else "passed",
        "GDPR,SOC2",
        f"{len(changed_governance_files)} governance-relevant file(s) changed.",
    )

    secret_like_paths = [
        path
        for path in files
        if any(token in path.lower() for token in SECRET_PATH_TOKENS)
    ]
    add_check(
        checks,
        "no_secret_or_auth_file_changes",
        "failed" if secret_like_paths else "passed",
        "SOC2",
        f"Secret/auth-like files changed: {', '.join(secret_like_paths)}"
        if secret_like_paths
        else "No secret/auth-like file paths changed.",
    )

    business_key_changes = [
        line
        for line in diff.splitlines()
        if line.startswith(("+", "-")) and "business_key" in line and not line.startswith(("+++", "---"))
    ]
    add_check(
        checks,
        "business_key_changes_require_human_review",
        "warning" if business_key_changes else "passed",
        "SOC2",
        "Business key metadata changed; explicit human review required."
        if business_key_changes
        else "No business key metadata changes detected.",
    )

    metric_terms = ["total_amount", "mrr", "approval_cycle_time", "sla_breach", "financial metric"]
    metric_changes = [
        line
        for line in diff.splitlines()
        if line.startswith(("+", "-")) and any(term in line.lower() for term in metric_terms)
    ]
    add_check(
        checks,
        "financial_or_operational_metric_changes_require_review",
        "warning" if metric_changes else "passed",
        "SOC2",
        "Metric-bearing SQL or metadata changed; finance/data owner review required."
        if metric_changes
        else "No metric-bearing changes detected.",
    )

    quality_gate_terms = [
        "dbt test",
        "great_expectations",
        "dashboard_quality_status",
        "bundle validate",
        "detect_client_integration_changes",
        "detect_new_cdc_contexts",
    ]
    removed_quality_gate = [
        line
        for line in diff.splitlines()
        if line.startswith("-") and any(term in line.lower() for term in quality_gate_terms)
    ]
    add_check(
        checks,
        "quality_gates_not_removed",
        "failed" if removed_quality_gate else "passed",
        "SOC2",
        "Quality gate references were removed; this needs explicit approval."
        if removed_quality_gate
        else "No quality gate removals detected.",
    )

    deployed_dashboard_resource = [
        path for path in files if path.startswith("resources/") and "dashboard_candidates" not in path
    ]
    dashboard_files = [path for path in files if path.startswith("src/dashboards/")]
    add_check(
        checks,
        "dashboard_changes_require_privacy_and_uc_review",
        "warning" if dashboard_files or deployed_dashboard_resource else "passed",
        "GDPR,SOC2",
        "Dashboard/resource changes detected; validate SQL, tenant isolation, UC permissions, and data minimisation."
        if dashboard_files or deployed_dashboard_resource
        else "No dashboard resource changes detected.",
    )

    app_files = [path for path in files if path.startswith("src/apps/") or path.startswith("resources/app_candidates/")]
    add_check(
        checks,
        "app_changes_require_access_review",
        "warning" if app_files else "passed",
        "SOC2",
        "Databricks App changes detected; review SQL warehouse binding, OAuth scope, and UC permissions."
        if app_files
        else "No Databricks App changes detected.",
    )

    gdpr_terms_present = sorted({term for term in GDPR_RIGHTS if term in lower_diff})
    add_check(
        checks,
        "gdpr_rights_terms_reviewed",
        "warning" if gdpr_terms_present else "passed",
        "GDPR",
        f"GDPR rights/control terms found: {', '.join(gdpr_terms_present)}"
        if gdpr_terms_present
        else "No explicit GDPR rights/control terms changed.",
    )

    cdc_or_client_changes = [
        path
        for path in files
        if path.startswith("sample_data/")
        or path.startswith("metadata/client_integrations.yml")
        or path.startswith("metadata/supported_cdc_contexts.yml")
    ]
    add_check(
        checks,
        "client_or_cdc_changes_require_privacy_review",
        "warning" if cdc_or_client_changes else "passed",
        "GDPR,SOC2",
        "Client/CDC metadata changed; review data minimisation, lawful basis, retention, and tenant separation."
        if cdc_or_client_changes
        else "No client/CDC metadata changes detected.",
    )

    soc2_impacts = {
        control: [path for path in files if touches(path, prefixes)]
        for control, prefixes in SOC2_CONTROLS.items()
    }
    for control, impacted_files in soc2_impacts.items():
        add_check(
            checks,
            f"soc2_{control}_impact",
            "warning" if impacted_files else "passed",
            "SOC2",
            f"{control.replace('_', ' ').title()} impacted by: {', '.join(impacted_files[:8])}"
            if impacted_files
            else f"No {control.replace('_', ' ')} impact detected.",
        )

    status = severity([check["status"] for check in checks])
    return {
        "status": status,
        "base": base,
        "head": head,
        "changed_files": files,
        "checks": checks,
        "summary": {
            "failed": sum(1 for check in checks if check["status"] == "failed"),
            "warning": sum(1 for check in checks if check["status"] == "warning"),
            "passed": sum(1 for check in checks if check["status"] == "passed"),
        },
    }


def write_reports(result: dict) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(result, indent=2), encoding="utf-8")

    lines = [
        "# Automated GDPR and SOC 2 Change Review",
        "",
        f"Status: `{result['status']}`",
        f"Base: `{result['base']}`",
        f"Head: `{result['head']}`",
        "",
        "## Summary",
        "",
        f"- Failed: `{result['summary']['failed']}`",
        f"- Warnings: `{result['summary']['warning']}`",
        f"- Passed: `{result['summary']['passed']}`",
        "",
        "## Changed Files",
        "",
    ]
    lines.extend(f"- `{path}`" for path in result["changed_files"])
    lines.extend(
        [
            "",
            "## Checks",
            "",
            "| Check | Framework | Status | Details |",
            "| --- | --- | --- | --- |",
        ]
    )
    for check in result["checks"]:
        details = check["details"].replace("|", "\\|").replace("\n", " ")
        lines.append(f"| `{check['name']}` | `{check['framework']}` | `{check['status']}` | {details} |")
    lines.extend(
        [
            "",
            "## Human Review Notes",
            "",
            "- Failed checks must be resolved before merge.",
            "- Warning checks require reviewer acknowledgement, not automatic deployment.",
            "- GDPR review should confirm data minimisation, lawful basis, retention, data-subject rights, and tenant isolation.",
            "- SOC 2 review should confirm change approval, access controls, processing integrity, confidentiality, and availability impact.",
        ]
    )
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", default="HEAD")
    args = parser.parse_args()

    result = review(args.base, args.head)
    write_reports(result)
    print(json.dumps(result["summary"], indent=2))
    return 1 if result["status"] == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
