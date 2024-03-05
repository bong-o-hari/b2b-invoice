from django.db import models
from django.contrib.auth import get_user_model
from inboicing_system.core.managers import GetOrNoneManager
from .choices import *

# Create your models here.

User = get_user_model()

class UserPermissions(models.Model):

    user = models.ForeignKey(User, related_name='user_permission', on_delete=models.CASCADE)
    permission = models.CharField(choices=PermissionChoices.choices, default=PermissionChoices.FINANCE_OPS, max_length=50)
    objects = GetOrNoneManager()