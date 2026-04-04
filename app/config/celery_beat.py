"""
Celery Beat schedule — all periodic tasks defined here.

Schedules:
    compute_churn_scores:         daily at 02:00 UTC
    process_pending_revenue:      hourly
    refresh_dashboard_cache:      every 5 minutes
"""

from __future__ import annotations

from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    "compute-churn-scores-daily": {
        "task": "app.tasks.churn_tasks.compute_churn_scores",
        "schedule": crontab(hour=2, minute=0),
        "args": (),
    },
    "process-pending-revenue-hourly": {
        "task": "app.tasks.revenue_tasks.process_pending_revenue",
        "schedule": crontab(minute=0),
        "args": (),
    },
    "refresh-dashboard-cache": {
        "task": "app.tasks.metrics_tasks.refresh_dashboard_cache",
        "schedule": 300.0,  # every 5 minutes
        "args": (),
    },
}
