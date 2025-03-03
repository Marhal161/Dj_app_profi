from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import redirect
import logging

logger = logging.getLogger(__name__)

class LogoutView(APIView):
    def get(self, request):
        try:
            # Получаем refresh token из куки
            refresh_token = request.COOKIES.get('refresh_token')
            
            # Создаем ответ для редиректа
            response = redirect('home_page')
            
            # Удаляем куки независимо от наличия токена
            response.delete_cookie('access_token')
            response.delete_cookie('refresh_token')
            
            # Если есть refresh token, инвалидируем его
            if refresh_token:
                try:
                    token = RefreshToken(refresh_token)
                    token.blacklist()
                    logger.debug("Token blacklisted successfully")
                except Exception as e:
                    logger.error(f"Error blacklisting token: {e}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error in LogoutView: {e}")
            return redirect('home_page')
        
            
                
                