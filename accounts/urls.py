from django.urls import path
from .views import *

urlpatterns = [
    path("register/", register_user, name="register"),
    path("superuser_access/", change_superuser_access, name="superuser-access"),
    path("permissions/", update_permissions, name="update-permissions")
]