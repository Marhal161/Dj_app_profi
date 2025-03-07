import logging
from django.shortcuts import redirect
from django.urls import reverse
from functools import wraps
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from django.contrib.auth import get_user_model
import jwt
from django.conf import settings
import json
import requests
from datetime import datetime, timedelta
from django.contrib import messages
from django.http import JsonResponse

logger = logging.getLogger(__name__)

def check_auth_tokens(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Получаем токены из cookies
        access_token = request.COOKIES.get('access_token')
        refresh_token = request.COOKIES.get('refresh_token')
        
        logger.debug(f"Checking tokens - Access: {bool(access_token)}, Refresh: {bool(refresh_token)}")
        
        # Если нет токенов, пользователь не аутентифицирован
        if not access_token or not refresh_token:
            request.is_authenticated = False
            request.user_info = None
            return view_func(request, *args, **kwargs)
        
        try:
            # Пытаемся декодировать access_token
            token_payload = jwt.decode(
                access_token,
                settings.SECRET_KEY,
                algorithms=['HS256']
            )
            
            # Получаем информацию о пользователе из токена
            request.is_authenticated = True
            request.user_info = {
                'user_id': token_payload.get('user_id'),
                'username': token_payload.get('username', ''),
                'email': token_payload.get('email', ''),
                'user_type': token_payload.get('user_type', '')
            }
            
            logger.debug(f"User info from token: {request.user_info}")
            
            return view_func(request, *args, **kwargs)
            
        except jwt.ExpiredSignatureError:
            # Если access_token истек, пытаемся обновить
            try:
                new_tokens = refresh_access_token(refresh_token)
                if new_tokens:
                    # Декодируем новый токен для получения информации о пользователе
                    new_token_payload = jwt.decode(
                        new_tokens['access'],
                        settings.SECRET_KEY,
                        algorithms=['HS256']
                    )
                    
                    request.is_authenticated = True
                    request.user_info = {
                        'user_id': new_token_payload.get('user_id'),
                        'username': new_token_payload.get('username', ''),
                        'email': new_token_payload.get('email', ''),
                        'user_type': new_token_payload.get('user_type', '')
                    }
                    
                    response = view_func(request, *args, **kwargs)
                    response.set_cookie(
                        'access_token',
                        new_tokens['access'],
                        max_age=3600,
                        httponly=True,
                        samesite='Lax'
                    )
                    response.set_cookie(
                        'refresh_token',
                        new_tokens['refresh'],
                        max_age=86400,
                        httponly=True,
                        samesite='Lax'
                    )
                    return response
            except Exception as e:
                logger.error(f"Error refreshing token: {e}")
        
        # Если что-то пошло не так, считаем пользователя не аутентифицированным
        request.is_authenticated = False
        request.user_info = None
        return view_func(request, *args, **kwargs)
    
    return wrapper

def refresh_access_token(refresh_token):
    """
    Функция для обновления access_token с помощью refresh_token используя Simple JWT
    """
    try:
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken(refresh_token)
        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        }
    except Exception as e:
        logger.error(f"Error refreshing token: {e}")
        return None

def teacher_required(view_func):
    def wrapper(request, *args, **kwargs):
        # Проверяем, что пользователь авторизован и информация о нем доступна
        if not hasattr(request, 'user_info') or not request.user_info:
            messages.error(request, 'Необходимо войти в систему')
            return redirect('login_page')
        
        # Проверяем, что пользователь является учителем
        if request.user_info.get('user_type') != 'teacher':
            messages.error(request, 'Доступ запрещен. Требуются права учителя.')
            return redirect('home_page')
        
        return view_func(request, *args, **kwargs)
    return wrapper