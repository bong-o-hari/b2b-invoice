from .models import UserPermissions
from .choices import *

def check_warehouse_user(user):
    permission_obj = UserPermissions.objects.get_or_none(user_id=user, permission=PermissionChoices.WAREHOUSE_OPS)
    if permission_obj:
        return True
    return False


def check_finance_user(user):
    permission_obj = UserPermissions.objects.get_or_none(user_id=user, permission=PermissionChoices.FINANCE_OPS)
    if permission_obj:
        return True
    return False