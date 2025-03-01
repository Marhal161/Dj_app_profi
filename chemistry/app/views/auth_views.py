from django.shortcuts import render, redirect
from django.views.generic import TemplateView

class LoginPageView(TemplateView):
    template_name = 'auth/login.html'

class RegisterPageView(TemplateView):
    template_name = 'auth/register.html'

def logout_view(request):
    """
    Представление для выхода из системы
    """
    # Создаем ответ с перенаправлением на главную страницу
    response = redirect('home')
    
    # Удаляем токены из cookies
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')
    
    return response 