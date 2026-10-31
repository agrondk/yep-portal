BEAT_SCHEDULE = {
    "deliver-outbox-every-minute": {
        "task": "app.tasks.deliver_outbox",
        "schedule": 60.0,
    }
}
