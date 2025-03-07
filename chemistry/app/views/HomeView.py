from django.shortcuts import render
from django.views.generic import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from ..decorators import check_auth_tokens
from ..models import News, Article
from django.utils.decorators import method_decorator

class HomePageView(View):
    @method_decorator(check_auth_tokens)
    def get(self, request):
        # Получаем последние новости и статьи
        latest_news = News.objects.filter(is_published=True).order_by('-created_at')[:3]
        latest_articles = Article.objects.filter(is_published=True).order_by('-created_at')[:3]
        
        context = {
            'title': 'Главная',
            'latest_news': latest_news,
            'latest_articles': latest_articles,
            'is_authenticated': getattr(request, 'is_authenticated', False),
            'user_info': getattr(request, 'user_info', None)
        }
        
        return render(request, 'home.html', context)
    
    @method_decorator(check_auth_tokens)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs) 