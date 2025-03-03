from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, View
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.pagination import PageNumberPagination
from ..models import Article
from ..serializers.ArticleSerializer import ArticleSerializer
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
class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all().order_by('-created_at')
    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = ArticleAPIPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'content']
    ordering_fields = ['created_at', 'title']
    ordering = ['-created_at']

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=True, methods=['get'])
    def related(self, request, pk=None):
        """Получение связанных статей"""
        article = self.get_object()
        related_articles = Article.objects.exclude(
            pk=article.pk
        ).order_by('-created_at')[:3]
        
        serializer = self.get_serializer(related_articles, many=True)
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
        user_info = request.user_info if hasattr(request, 'user_info') else None
        is_authenticated = request.is_authenticated if hasattr(request, 'is_authenticated') else False
        
        # Получаем все статьи из модели Article
        articles_list = Article.objects.filter(is_published=True).order_by('-created_at')
        
        # Пагинация
        page = request.GET.get('page', 1)
        paginator = Paginator(articles_list, 9)  # 9 статей на страницу
        
        try:
            articles = paginator.page(page)
        except PageNotAnInteger:
            articles = paginator.page(1)
        except EmptyPage:
            articles = paginator.page(paginator.num_pages)
        
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
        user_info = request.user_info if hasattr(request, 'user_info') else None
        is_authenticated = request.is_authenticated if hasattr(request, 'is_authenticated') else False
        
        # Получаем статью из модели Article
        article = get_object_or_404(Article, pk=pk)
        
        # Получаем просто последние статьи вместо фильтрации по категории
        related_articles = Article.objects.filter(
            is_published=True
        ).exclude(
            pk=pk
        ).order_by('-created_at')[:3]
        
        context = {
            'title': f'{article.title} | Химия',
            'user_info': user_info,
            'is_authenticated': is_authenticated,
            'article': article,
            'related_articles': related_articles
        }
        
        return render(request, self.template_name, context)