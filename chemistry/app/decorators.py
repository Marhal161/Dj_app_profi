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
            request.user_info = None
            request.is_authenticated = False
            return view_func(request, *args, **kwargs)  # Позволяем продолжить без авторизации
        
        try:
            # Пытаемся декодировать access_token используя SimpleJWT
            token = AccessToken(access_token)
            token_payload = token.payload
            
            # Если токен валидный, устанавливаем информацию о пользователе
            request.user_info = {
                'user_id': token_payload.get('user_id'),
                'username': token_payload.get('username', ''),
                'email': token_payload.get('email', ''),
                'user_type': token_payload.get('user_type', '')
            }
            request.is_authenticated = True
            
            logger.debug(f"User info from token: {request.user_info}")
            
            return view_func(request, *args, **kwargs)
            
        except TokenError:
            # Если access_token истек или невалиден, пытаемся обновить
            try:
                # Создаем объект RefreshToken
                refresh = RefreshToken(refresh_token)
                
                # Получаем новый access token
                new_access_token = str(refresh.access_token)
                
                # Декодируем новый токен для получения информации о пользователе
                new_token = AccessToken(new_access_token)
                new_token_payload = new_token.payload
                
                request.user_info = {
                    'user_id': new_token_payload.get('user_id'),
                    'username': new_token_payload.get('username', ''),
                    'email': new_token_payload.get('email', ''),
                    'user_type': new_token_payload.get('user_type', '')
                }
                request.is_authenticated = True
                
                response = view_func(request, *args, **kwargs)
                
                # Устанавливаем новые токены в cookies
                response.set_cookie(
                    'access_token',
                    new_access_token,
                    max_age=3600,
                    httponly=True,
                    samesite='Lax'
                )
                response.set_cookie(
                    'refresh_token',
                    str(refresh),
                    max_age=86400,
                    httponly=True,
                    samesite='Lax'
                )
                return response
                
            except TokenError as e:
                logger.error(f"Error refreshing token: {e}")
                request.user_info = None
                request.is_authenticated = False
                return view_func(request, *args, **kwargs)  # Позволяем продолжить без авторизации
                
        except Exception as e:
            # Если произошла любая другая ошибка при проверке токена
            logger.error(f"Error verifying token: {e}")
            request.user_info = None
            request.is_authenticated = False
            return view_func(request, *args, **kwargs)  # Позволяем продолжить без авторизации
    
    return wrapper

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