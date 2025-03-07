from django.shortcuts import render
from django.views.generic import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from ..decorators import check_auth_tokens
from ..models import News, Article
from django.utils.decorators import method_decorator
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

class HomePageView(View):
    template_name = 'home.html'
    
    @method_decorator(check_auth_tokens)
    def get(self, request, *args, **kwargs):
        # Получаем все опубликованные новости, отсортированные по дате
        news_list = News.objects.filter(is_published=True).order_by('-created_at')
        
        # Логируем количество найденных новостей
        logger.debug(f"Found {news_list.count()} published news")
        
        # Пагинация: 6 новостей на страницу
        paginator = Paginator(news_list, 6)
        page = request.GET.get('page')
        news = paginator.get_page(page)
        
        context = {
            'title': 'Главная',
            'news_list': news,  # Передаем пагинированные новости
            'is_authenticated': hasattr(request, 'user_info') and request.user_info is not None,
            'user_info': getattr(request, 'user_info', None),
            'debug': settings.DEBUG
        }
        
        return render(request, self.template_name, context)
    
    @method_decorator(check_auth_tokens)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs) 