from django.shortcuts import render
from django.views.generic import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from ..decorators import check_auth_tokens
from ..models import News
from django.utils.decorators import method_decorator
from django.db import DatabaseError

class HomePageView(View):
    template_name = 'home.html'
    
    def get(self, request, *args, **kwargs):
        # Получаем информацию о пользователе из контекста запроса
        user_info = request.user_info if hasattr(request, 'user_info') else None
        is_authenticated = request.is_authenticated if hasattr(request, 'is_authenticated') else False
        
        # Получаем только новости (не статьи)
        try:
            # Пробуем фильтровать по content_type
            news_list = News.objects.filter(content_type='news').order_by('-created_at')
        except DatabaseError as e:
            # Если поле не существует, получаем все новости
            # В этом случае мы не можем разделить новости и статьи
            # Поэтому нужно запустить скрипт add_content_type.py
            news_list = News.objects.all().order_by('-created_at')
        
        # Пагинация
        page = request.GET.get('page', 1)
        paginator = Paginator(news_list, 6)  # 6 новостей на страницу
        
        try:
            news_items = paginator.page(page)
        except PageNotAnInteger:
            news_items = paginator.page(1)
        except EmptyPage:
            news_items = paginator.page(paginator.num_pages)
        
        # Передаем информацию в шаблон
        context = {
            'title': 'Главная страница | Химия',
            'user_info': user_info,
            'is_authenticated': is_authenticated,
            'news_list': news_items
        }
        
        return render(request, self.template_name, context)
    
    @method_decorator(check_auth_tokens)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs) 