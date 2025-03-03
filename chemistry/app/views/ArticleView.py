from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, View
from rest_framework import viewsets, permissions, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from ..models import News
from ..serializers.NewsSerializer import NewsSerializer
from ..decorators import check_auth_tokens
import jwt
from django.conf import settings
from django.utils.decorators import method_decorator
from django.db import DatabaseError
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

# API пагинатор для статей
class ArticleAPIPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 100

# API ViewSet для статей
class ArticleViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NewsSerializer
    pagination_class = ArticleAPIPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'content']
    ordering_fields = ['created_at', 'title']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Получаем только статьи
        """
        try:
            # Пробуем фильтровать по content_type, если поле существует
            return News.objects.filter(content_type='article').order_by('-created_at')
        except DatabaseError:
            # Если поле не существует, возвращаем пустой список
            # Это гарантирует, что API для статей не будет возвращать новости
            return News.objects.none()
    
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Эндпоинт для получения статей по категории"""
        category = request.query_params.get('category', None)
        if not category:
            return Response(
                {"error": "Необходимо указать параметр category"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            queryset = self.get_queryset().filter(category=category)
        except DatabaseError:
            queryset = News.objects.filter(category=category)
            
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

# Базовый класс для представлений с проверкой аутентификации
class AuthenticatedView(View):
    @method_decorator(check_auth_tokens)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

# Представление для списка статей (HTML)
class ArticleListView(View):
    template_name = 'articles.html'
    
    @method_decorator(check_auth_tokens)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        # Получаем информацию о пользователе из контекста запроса
        user_info = request.user_info if hasattr(request, 'user_info') else None
        is_authenticated = request.is_authenticated if hasattr(request, 'is_authenticated') else False
        
        # Получаем только статьи
        try:
            articles_list = News.objects.filter(content_type='article').order_by('-created_at')
        except DatabaseError:
            # Если поле не существует, возвращаем пустой список
            # Это гарантирует, что на странице статей не будут отображаться новости
            articles_list = News.objects.none()
        
        # Пагинация
        page = request.GET.get('page', 1)
        paginator = Paginator(articles_list, 9)  # 9 статей на страницу
        
        try:
            articles = paginator.page(page)
        except PageNotAnInteger:
            articles = paginator.page(1)
        except EmptyPage:
            articles = paginator.page(paginator.num_pages)
        
        # Передаем информацию в шаблон
        context = {
            'title': 'Статьи | Химия',
            'user_info': user_info,
            'is_authenticated': is_authenticated,
            'articles_list': articles,
            'is_paginated': True,
            'page_obj': articles
        }
        
        return render(request, self.template_name, context)

# Представление для детальной страницы статьи (HTML)
class ArticleDetailView(View):
    template_name = 'article_detail.html'
    
    def get(self, request, pk, *args, **kwargs):
        # Получаем информацию о пользователе из контекста запроса
        user_info = request.user_info if hasattr(request, 'user_info') else None
        is_authenticated = request.is_authenticated if hasattr(request, 'is_authenticated') else False
        
        # Получаем статью по ID
        article = get_object_or_404(News, pk=pk, content_type='article')
        
        # Получаем связанные статьи
        try:
            related_articles = News.objects.filter(
                content_type='article',
                category=article.category
            ).exclude(pk=pk).order_by('-created_at')[:3]
        except DatabaseError:
            # Если поле не существует, не показываем связанные статьи
            related_articles = News.objects.none()
        
        # Передаем информацию в шаблон
        context = {
            'title': f'{article.title} | Химия',
            'user_info': user_info,
            'is_authenticated': is_authenticated,
            'article': article,
            'related_articles': related_articles
        }
        
        return render(request, self.template_name, context)