from django.views import View
from django.shortcuts import redirect
from django.http import JsonResponse
import logging

logger = logging.getLogger(__name__)

class LogoutView(View):
    def get(self, request):
        response = redirect('home_page')  # Перенаправляем на главную страницу
        # Удаляем токены из cookies
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        return response

    def post(self, request):
        response = JsonResponse({'success': True})
        # Удаляем токены из cookies
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        return response
        
            
                
                