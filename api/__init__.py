import re

def validate_email(email):
    return re.match(r'^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,3})$', email)

def validate_name_or_fullname(value):
    return re.match(r'^([a-zA-Z]+[ ]*[a-zA-Z]*){3,25}$', value)

def validate_nickname(nickname):
    return re.match(r'^\w{4,15}$', nickname)
