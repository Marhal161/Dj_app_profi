from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from ..serializers.RegisterSerializer import RegisterSerializer
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

class RegisterView(APIView):
    @staticmethod
    def post(request):
        try:
            validate_password(request.data['password'])

            serializer = RegisterSerializer(data=request.data)
            if serializer.is_valid():
                try:
                    user = serializer.save()

                    refresh = RefreshToken.for_user(user)
                    access_token = str(refresh.access_token)

                    # Создание профилей больше не требуется, так как мы используем поля в модели User
                    # Комментарии можно удалить
                    
                    request_data = {
                        'success': True,
                        'message': 'Пользователь успешно зарегистрирован',
                        'user': {
                            'id': user.id,
                            'username': user.username,
                            'email': user.email,
                            'first_name': user.first_name,
                            'last_name': user.last_name,
                            'user_type': user.user_type,  # Добавляем тип пользователя в ответ
                        },
                        'access_token': access_token,
                        'refresh_token': str(refresh),
                    }

                    responce = JsonResponse(request_data, status=status.HTTP_201_CREATED)

                    responce.set_cookie(key='access_token', value=access_token, httponly=True, secure=True, samesite='None', max_age=3600)
                    responce.set_cookie(key='refresh_token', value=str(refresh), httponly=True, secure=True, samesite='None', max_age=604800)

                    return responce
            
                except Exception as e:
                    logger.error(f"Error in RegisterView: {str(e)}")
                    return JsonResponse({
                        'success': False,
                        'message': str(e),
                        'errors': serializer.errors if serializer else None,
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
            return JsonResponse({
                'success': False,
                'message': 'Ошибка в веденных данных',
                'errors': serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)
            
            
        except ValidationError as e:
            return JsonResponse({
                'success': False,
                'message': 'Ошибка валидации данных',
                'errors': list(e.messages),
            }, status=status.HTTP_400_BAD_REQUEST)
    
        except Exception as e:
            logger.error(f"Error in RegisterView: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': 'Произошла неизвестная ошибка',
                'errors': str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
