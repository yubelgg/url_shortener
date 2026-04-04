import datetime

from playhouse.shortcuts import model_to_dict


def serialize(model_instance, recurse=False, **kwargs):
    """Convert a Peewee model instance to a JSON-safe dict with ISO datetime strings."""
    data = model_to_dict(model_instance, recurse=recurse, **kwargs)
    for key, value in data.items():
        if isinstance(value, (datetime.datetime, datetime.date)):
            data[key] = value.isoformat()
    return data
