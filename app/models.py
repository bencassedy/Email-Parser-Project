from mongoengine import *

class Email(Document):
    tags = ListField(StringField(max_length=30))
    comments = ListField(EmbeddedDocumentField(Comment))

class User(Document):
    email = StringField(required=True)
    first_name = StringField(max_length=50)
    last_name = StringField(max_length=50)

class Comment(EmbeddedDocument):
    body = StringField()
    author = ReferenceField(User)

    meta = {'allow_inheritance': True}

class PrivilegeDescription(Comment):
    # inherits from Comment class
    priv_tags = ListField(StringField(max_length=30))

