with finance_documents as (
    select * from {{ source('silver', 'finance_documents_current') }}
),

companies as (
    select * from {{ source('silver', 'companies_current') }}
),

approval_events as (
    select * from {{ source('silver', 'approval_events') }}
),

event_rollup as (
    select
        document_id,
        workflow_id,
        min(case when event_type = 'submitted' then approval_event_timestamp end) as first_submitted_event_at,
        max(case when event_type = 'approved' then approval_event_timestamp end) as final_approved_event_at,
        max(case when event_type = 'rejected' then approval_event_timestamp end) as final_rejected_event_at,
        count(*) as approval_event_count
    from approval_events
    group by document_id, workflow_id
),

final as (
    select
        d.document_id,
        d.company_id,
        c.company_name,
        d.document_type,
        d.document_status,
        d.supplier_id,
        d.supplier_name,
        d.total_amount,
        d.currency,
        d.created_at,
        d.submitted_at,
        d.approved_at,
        d.rejected_at,
        d.paid_at,
        d.updated_at,
        d.approval_deadline_at,
        e.workflow_id,
        e.approval_event_count,
        e.first_submitted_event_at,
        e.final_approved_event_at,
        e.final_rejected_event_at,
        case
            when d.submitted_at is not null and d.approved_at is not null
            then timestampdiff(minute, d.submitted_at, d.approved_at)
        end as approval_cycle_time_minutes,
        case
            when d.approval_deadline_at is not null
             and d.approved_at is not null
             and d.approved_at > d.approval_deadline_at
            then 1
            else 0
        end as approval_sla_breach_flag,
        current_timestamp() as dbt_built_at
    from finance_documents d
    left join companies c on d.company_id = c.company_id
    left join event_rollup e on d.document_id = e.document_id
)

select * from final

