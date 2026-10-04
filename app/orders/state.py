ALLOWED = {
    "waiting_confirmation": {"queued", "cancelled", "failed"},
    "queued": {"processing", "failed", "cancelled"},
    "processing": {"queued", "delivering", "failed", "cancelled", "waiting_confirmation"},
    "delivering": {"completed", "failed", "cancelled"},
    "completed": {"refunded"},
    "failed": set(),
    "cancelled": set(),
    "refunded": set(),
}


def transition(order, target):
    if order.status == target:
        return
    if target not in ALLOWED.get(order.status, set()):
        raise ValueError("invalid order transition")
    order.status = target
