from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from inboicing_system.core.permissions import IsSuperUser
from .models import UserPermissions
from .choices import PermissionChoices

# Create your views here.
User = get_user_model()

@api_view(['POST'])
def register_user(request):
    data = request.data

    user = User.objects.create_user(
        username = data.get('email'),
        email = data.get('email'),
        password = data.get('password')
    )

    UserPermissions.objects.create(user=user)

    return Response({"success": True}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsSuperUser])
def change_superuser_access(request):
    data = request.data
    user_emails = data.get('user_emails', [])
    
    if user_emails:
        for email in user_emails:
            user = User.objects.get(email=email)
    
            if user:
                user.is_superuser = not user.is_superuser
                user.save()
        return Response({"success": True}, status=status.HTTP_200_OK)
    return Response({"success": False}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsSuperUser])
def update_permissions(request):
    data = request.data

    permission_type = data.get('permission_type', None)
    user_emails = data.get('user_emails', [])
    
    if user_emails:
        for email in user_emails:
            user = User.objects.get(email=email)
    
            if user and permission_type == 'warehouse':
                user_permissions, created = UserPermissions.objects.get_or_create(user_id=user.id, permission=PermissionChoices.WAREHOUSE_OPS)
                if not created:
                    user_permissions.delete()
            elif user and permission_type == 'finance':
                user_permissions, created = UserPermissions.objects.get_or_create(user_id=user.id, permission=PermissionChoices.FINANCE_OPS)
                if not created:
                    user_permissions.delete()
        return Response({"success": True}, status=status.HTTP_200_OK)
    return Response({"success": False}, status=status.HTTP_400_BAD_REQUEST)