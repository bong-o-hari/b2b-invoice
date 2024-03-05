from django.contrib.auth import get_user_model

User = get_user_model()

def get_user_by_email(email):
    if email and (user := User.objects.get(email=email, is_active=True)):
        return user
    return None