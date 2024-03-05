from rest_framework.permissions import BasePermission
from accounts.services import *

class IsSuperUser(BasePermission):

    def has_permission(self, request, view):
        user = request.user
        return user.is_superuser


class IsWarehouseOperator(BasePermission):

    def has_permission(self, request, view):
        user = request.user
        return check_warehouse_user(user) or user.is_superuser


class IsFinanceOperator(BasePermission):

    def has_permission(self, request, view):
        user = request.user
        return check_finance_user(user) or user.is_superuser