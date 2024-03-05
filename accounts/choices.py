from django.db import models

class PermissionChoices(models.TextChoices):
    WAREHOUSE_OPS = "warehouse_ops"
    FINANCE_OPS = "finance_ops"