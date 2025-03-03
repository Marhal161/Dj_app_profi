from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, get_user_model
from django.http import JsonResponse
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

class LoginView(APIView):
    @staticmethod
    def post(request):
        try:
            username = request.data.get('username')
            password = request.data.get('password')
            
            logger.debug(f"Попытка входа для пользователя: {username}")
            
            if not username or not password:
                logger.warning("Отсутствует имя пользователя или пароль")
                return JsonResponse({
                    'success': False,
                    'message': 'Необходимо указать имя пользователя и пароль',
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Проверяем, существует ли пользователь по username или email
            try:
                # Проверяем, является ли введенное значение email
                if '@' in username:
                    user_exists = User.objects.filter(email=username).exists()
                    if user_exists:
                        # Если пользователь найден по email, получаем его username
                        user_obj = User.objects.get(email=username)
                        username = user_obj.username
                        logger.debug(f"Найден пользователь по email, username: {username}")
                else:
                    user_exists = User.objects.filter(username=username).exists()
                
                if not user_exists:
                    logger.warning(f"Пользователь не найден: {username}")
                    return JsonResponse({
                        'success': False,
                        'message': 'Неверное имя пользователя или пароль',
                    }, status=status.HTTP_401_UNAUTHORIZED)
            except Exception as e:
                logger.error(f"Ошибка при проверке существования пользователя: {str(e)}")
            
            # Аутентификация пользователя
            user = authenticate(username=username, password=password)
            logger.debug(f"Результат аутентификации: {user is not None}")
            
            if user is not None:
                # Создаем токен
                refresh = RefreshToken.for_user(user)
                
                # Добавляем пользовательские данные в токен
                refresh['username'] = user.username
                refresh['email'] = user.email
                refresh['user_type'] = user.user_type
                refresh['user_id'] = user.id
                
                # Получаем access token
                access_token = str(refresh.access_token)
                
                response_data = {
                    'success': True,
                    'message': 'Вход выполнен успешно',
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'user_type': user.user_type,
                    }
                }
                
                response = JsonResponse(response_data, status=status.HTTP_200_OK)
                
                # Устанавливаем куки
                response.set_cookie(
                    key='access_token',
                    value=access_token,
                    httponly=True,
                    samesite='Lax',
                    max_age=3600  # 1 час
                )
                response.set_cookie(
                    key='refresh_token',
                    value=str(refresh),
                    httponly=True,
                    samesite='Lax',
                    max_age=86400  # 24 часа
                )
                
                logger.debug(f"Токены установлены для пользователя: {user.username}")
                return response
            else:
                logger.warning(f"Неверный пароль для пользователя: {username}")
                return JsonResponse({
                    'success': False,
                    'message': 'Неверное имя пользователя или пароль',
                }, status=status.HTTP_401_UNAUTHORIZED)
                
        except Exception as e:
            logger.error(f"Error in LoginView: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': 'Произошла ошибка при входе',
                'error': str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            
            