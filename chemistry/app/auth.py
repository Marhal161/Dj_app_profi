from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()

class EmailOrUsernameModelBackend(ModelBackend):
    """
    Аутентификация по email или username
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Проверяем, является ли введенное значение email
            if '@' in username:
                user = User.objects.get(email=username)
            else:
                user = User.objects.get(username=username)
                
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None
        except Exception as e:
            return None 