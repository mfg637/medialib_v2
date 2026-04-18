from django.contrib.auth.models import User
from django.http import HttpRequest


def is_user_nsfw_member(user: User):
    return user.groups.filter(name="nsfw").exists() or user.is_superuser


def check_user_nsfw_member(request: HttpRequest):
    return is_user_nsfw_member(request.user)
