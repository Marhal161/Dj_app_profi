from django.shortcuts import render, get_object_or_404
from django.views.generic import View
from ..models import News
import jwt
from django.conf import settings
from rest_framework import viewsets, permissions, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from ..serializers.NewsSerializer import NewsSerializer
from ..decorators import check_auth_tokens
from django.utils.decorators import method_decorator
from django.db import DatabaseError

# Пагинатор для API
class NewsAPIPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

# API ViewSet для CRUD операций с новостями
class NewsViewSet(viewsets.ModelViewSet):
    serializer_class = NewsSerializer
    pagination_class = NewsAPIPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'content']
    ordering_fields = ['created_at', 'title']
    ordering = ['-created_at']
    
    def get_permissions(self):
        """
        Настройка прав доступа:
        - GET запросы доступны всем
        - POST, PUT, PATCH, DELETE доступны только авторизованным пользователям
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """
        Фильтрация новостей:
        - По умолчанию показываем только новости (не статьи)
        - Для обычных пользователей показываем только опубликованные новости
        - Для администраторов показываем все новости
        """
        try:
            # Пытаемся фильтровать по типу контента
            queryset = News.objects.filter(content_type='news').order_by('-created_at')
        except DatabaseError:
            # Если поле не существует, получаем все новости
            queryset = News.objects.all().order_by('-created_at')
        
        # Фильтрация по категории
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category=category)
        
        # Фильтрация по опубликованным/неопубликованным
        try:
            if not self.request.user.is_staff and hasattr(News, 'is_published'):
                queryset = queryset.filter(is_published=True)
        except:
            pass
        
        return queryset
    
    def perform_create(self, serializer):
        """Автоматически устанавливаем текущего пользователя как автора"""
        serializer.save(author=self.request.user)
    
    @action(detail=False, methods=['get'])
    def published(self, request):
        """Эндпоинт для получения только опубликованных новостей"""
        try:
            if hasattr(News, 'is_published'):
                queryset = self.get_queryset().filter(is_published=True)
            else:
                queryset = self.get_queryset()
        except DatabaseError:
            queryset = self.get_queryset()
            
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Эндпоинт для получения новостей по категории"""
        category = request.query_params.get('category', None)
        if not category:
            return Response(
                {"error": "Необходимо указать параметр category"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(category=category)
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def articles(self, request):
        """Эндпоинт для получения только статей"""
        try:
            queryset = self.get_queryset().filter(content_type='article')
        except DatabaseError:
            queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def news(self, request):
        """Эндпоинт для получения только новостей"""
        try:
            queryset = self.get_queryset().filter(content_type='news')
        except DatabaseError:
            queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

# Представление для отображения детальной страницы новости
class NewsDetailView(View):
    template_name = 'news_detail.html'
    
    @method_decorator(check_auth_tokens)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, pk, *args, **kwargs):
        # Получаем информацию о пользователе из контекста запроса
        user_info = request.user_info if hasattr(request, 'user_info') else None
        is_authenticated = request.is_authenticated if hasattr(request, 'is_authenticated') else False
        
        # Получаем новость по ID
        news = get_object_or_404(News, pk=pk, content_type='news')
        
        # Получаем связанные новости
        related_news = News.objects.filter(
            content_type='news',
            category=news.category
        ).exclude(pk=pk).order_by('-created_at')[:3]
        
        # Передаем информацию в шаблон
        context = {
            'title': f'{news.title} | Химия',
            'user_info': user_info,
            'is_authenticated': is_authenticated,
            'news': news,
            'related_news': related_news
        }
        
        return render(request, self.template_name, context) 