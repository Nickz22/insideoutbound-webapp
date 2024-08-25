from datetime import datetime
from collections import defaultdict
from app.data_models import Activation


def generate_summary(activations: list[Activation]) -> dict:
    today = datetime.now().date()
    summary = {
        "total_activations": len(activations),
        "activations_today": 0,
        "total_tasks": 0,
        "total_events": 0,
        "total_contacts": 0,
        "total_accounts": 0,
        "total_deals": 0,
        "total_pipeline_value": 0,
        "engaged_activations": 0,
    }

    account_contacts = defaultdict(set)

    for activation in activations:
        if activation.activated_date == today:
            summary["activations_today"] += 1

        summary["total_tasks"] += len(activation.task_ids)
        summary["total_events"] += (
            len(activation.event_ids) if activation.event_ids else 0
        )
        account_id = activation.account.id
        account_contacts[account_id].update(activation.active_contact_ids)

        if activation.opportunity:
            summary["total_deals"] += 1
            summary["total_pipeline_value"] += activation.opportunity.amount
        if activation.status == "Engaged":
            summary["engaged_activations"] += 1

    summary["total_contacts"] = sum(
        len(contacts) for contacts in account_contacts.values()
    )
    summary["total_accounts"] = len(account_contacts)
    summary["avg_tasks_per_contact"] = (
        summary["total_tasks"] / summary["total_contacts"]
        if summary["total_contacts"] > 0
        else 0
    )
    summary["avg_contacts_per_account"] = (
        summary["total_contacts"] / summary["total_accounts"]
        if summary["total_accounts"] > 0
        else 0
    )


    return summary
