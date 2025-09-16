import uuid, datetime

def make_json_safe(obj):
    """
    Recursively convert UUIDs and datetimes to strings so obj is json-serializable.
    Works for nested dicts/lists.
    """
    if isinstance(obj, uuid.UUID):
        return str(obj)
    if isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: make_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [make_json_safe(v) for v in obj]
    return obj
