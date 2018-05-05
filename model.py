from peewee import *
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
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


class UserDB(BaseModel):
    id = PrimaryKeyField()
    username = CharField()
    email = CharField()
    password_hash = TextField()

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


def initialize_db():
    proxy.connect()
    proxy.create_tables([Post], safe=True)
    proxy.create_tables([UserDB], safe=True)

