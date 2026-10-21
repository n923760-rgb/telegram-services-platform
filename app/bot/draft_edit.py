"""Generic edits to unsubmitted drafts, preserving unrelated input and original data."""

from copy import deepcopy

from sqlalchemy import select

from app.core.db import sessions
from app.core.models import Order
from app.services.base import InputSchema, active_field


def _remove(inputs, name):
    parts = name.split(".")
    cursor = inputs
    for part in parts[:-1]:
        cursor = cursor.get(part)
        if not isinstance(cursor, dict):
            return
    cursor.pop(parts[-1], None)


def begin_edit(data, index):
    fields = InputSchema.model_validate(data["schema"]).conversation()
    if not 0 <= index < len(fields) or not active_field(fields[index], data["inputs"]):
        raise ValueError("invalid edit field")
    data = deepcopy(data)
    data["_edit_original"] = deepcopy(data["inputs"])
    affected = {fields[index].name}
    queue = [index]
    # Conditions reference only earlier fields, so one ordered pass also finds
    # transitive dependencies. Remove hidden old values before final admission.
    for position in range(index + 1, len(fields)):
        if affected.intersection(fields[position].when):
            affected.add(fields[position].name)
            queue.append(position)
    for name in affected:
        _remove(data["inputs"], name)
    data["_edit_queue"] = queue
    data["index"] = index
    return data


def next_index(data, fields):
    if "_edit_queue" in data:
        queue = data["_edit_queue"]
        while queue and not active_field(fields[queue[0]], data["inputs"]):
            queue.pop(0)
        if queue:
            data["_edit_queue"] = queue
            return queue[0]
        data.pop("_edit_queue")
        data.pop("_edit_original", None)
        return len(fields)
    index = data["index"]
    while index < len(fields) and not active_field(fields[index], data["inputs"]):
        index += 1
    return index


def advance(data):
    if "_edit_queue" in data:
        data["_edit_queue"].pop(0)
    else:
        data["index"] += 1


def abort_edit(data):
    data = deepcopy(data)
    data["inputs"] = data.pop("_edit_original")
    data.pop("_edit_queue")
    data["index"] = len(InputSchema.model_validate(data["schema"]).conversation())
    return data


async def accepted_draft(user_id, key):
    # An invoice send/FSM failure can leave a confirmation visible after submit
    # committed. Never turn that accepted request into a fresh purchase key.
    async with sessions() as db:
        return (
            await db.scalar(
                select(Order.id).where(Order.user_id == user_id, Order.idempotency_key == key)
            )
            is not None
        )
