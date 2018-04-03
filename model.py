from peewee import *
import datetime

proxy = Proxy()


class BaseModel(Model):
    class Meta:
        database = proxy


class Post(BaseModel):
    id = PrimaryKeyField()
    date = DateTimeField(default=datetime.datetime.now)
    title = CharField()
    text = TextField()
    score = IntegerField()


def initialize_db():
    proxy.connect()
    proxy.create_tables([Post], safe=True)

