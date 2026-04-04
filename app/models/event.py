import datetime

from peewee import AutoField, CharField, DateTimeField, ForeignKeyField, IntegerField
from playhouse.postgres_ext import BinaryJSONField

from app.database import BaseModel
from app.models.url import Url


class Event(BaseModel):
    id = AutoField()
    url_id = ForeignKeyField(Url, backref="events", column_name="url_id", on_delete="CASCADE")
    user_id = IntegerField(null=True)
    event_type = CharField()
    timestamp = DateTimeField(default=datetime.datetime.now)
    details = BinaryJSONField(null=True)

    class Meta:
        table_name = "events"
