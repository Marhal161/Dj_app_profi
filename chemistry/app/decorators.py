import logging
from django.shortcuts import redirect
from django.urls import reverse
from functools import wraps
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from django.contrib.auth import get_user_model
import jwt
from django.conf import settings
import json
import requests
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def check_auth_tokens(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Получаем токены из cookies
        access_token = request.COOKIES.get('access_token')
        refresh_token = request.COOKIES.get('refresh_token')
        
        # Если нет токенов, пользователь не аутентифицирован
        if not access_token or not refresh_token:
            request.is_authenticated = False
            request.user_info = None
            return view_func(request, *args, **kwargs)
        
        try:
            # Пытаемся декодировать access_token
            payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=['HS256'])
            user_id = payload.get('user_id')
            username = payload.get('username')
            user_type = payload.get('user_type')
            exp = payload.get('exp')
            
            # Проверяем, не истек ли токен
            current_time = datetime.now().timestamp()
            
            # Если токен скоро истечет (осталось менее 5 минут), обновляем его
            if exp - current_time < 300:  # 5 минут в секундах
                # Пытаемся обновить токен
                new_tokens = refresh_access_token(refresh_token)
                if new_tokens:
                    access_token = new_tokens['access']
                    refresh_token = new_tokens['refresh']
                    
                    # Декодируем новый access_token
                    payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=['HS256'])
                    user_id = payload.get('user_id')
                    username = payload.get('username')
                    user_type = payload.get('user_type')
                    
                    # Устанавливаем новые токены в cookies
                    response = view_func(request, *args, **kwargs)
                    response.set_cookie('access_token', access_token, httponly=True, samesite='Lax')
                    response.set_cookie('refresh_token', refresh_token, httponly=True, samesite='Lax')
                    
                    # Устанавливаем информацию о пользователе
                    request.is_authenticated = True
                    request.user_info = {
                        'user_id': user_id,
                        'username': username,
                        'user_type': user_type
                    }
                    
                    return response
            
            # Если токен действителен, устанавливаем информацию о пользователе
            request.is_authenticated = True
            request.user_info = {
                'user_id': user_id,
                'username': username,
                'user_type': user_type
            }
            
            return view_func(request, *args, **kwargs)
            
        except jwt.ExpiredSignatureError:
            # Если access_token истек, пытаемся обновить его с помощью refresh_token
            new_tokens = refresh_access_token(refresh_token)
            
            if new_tokens:
                # Если удалось обновить токены
                access_token = new_tokens['access']
                refresh_token = new_tokens['refresh']
                
                # Декодируем новый access_token
                try:
                    payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=['HS256'])
                    user_id = payload.get('user_id')
                    username = payload.get('username')
                    user_type = payload.get('user_type')
                    
                    # Устанавливаем информацию о пользователе
                    request.is_authenticated = True
                    request.user_info = {
                        'user_id': user_id,
                        'username': username,
                        'user_type': user_type
                    }
                    
                    # Выполняем исходную функцию представления
                    response = view_func(request, *args, **kwargs)
                    
                    # Устанавливаем новые токены в cookies
                    response.set_cookie('access_token', access_token, httponly=True, samesite='Lax')
                    response.set_cookie('refresh_token', refresh_token, httponly=True, samesite='Lax')
                    
                    return response
                    
                except jwt.InvalidTokenError:
                    # Если новый токен недействителен
                    request.is_authenticated = False
                    request.user_info = None
            else:
                # Если не удалось обновить токены
                request.is_authenticated = False
                request.user_info = None
                
                # Удаляем недействительные токены
                response = view_func(request, *args, **kwargs)
                response.delete_cookie('access_token')
                response.delete_cookie('refresh_token')
                return response
                
        except jwt.InvalidTokenError:
            # Если токен недействителен
            request.is_authenticated = False
            request.user_info = None
        
        return view_func(request, *args, **kwargs)
    
    return wrapper

def refresh_access_token(refresh_token):
    """
    Функция для обновления access_token с помощью refresh_token
    """
    try:
        # URL для обновления токена
        token_refresh_url = f"{settings.API_BASE_URL}/api/token/refresh/"
        logger.debug(f"Attempting to refresh token at URL: {token_refresh_url}")
        
        # Отправляем запрос на обновление токена
        response = requests.post(
            token_refresh_url,
            json={"refresh": refresh_token},
            headers={"Content-Type": "application/json"}
        )
        
        # Если запрос успешен
        logger.debug(f"Token refresh response status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            logger.debug("Token refresh successful")
            return result
        else:
            logger.error(f"Token refresh failed: {response.text}")
        
        return None
    except Exception as e:
        logger.error(f"Error refreshing token: {e}")
        return None