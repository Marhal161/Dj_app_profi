from django.shortcuts import render
from django.views.generic import TemplateView

class LoginPageView(TemplateView):
    template_name = 'auth/login.html'

class RegisterPageView(TemplateView):
    template_name = 'auth/register.html' 