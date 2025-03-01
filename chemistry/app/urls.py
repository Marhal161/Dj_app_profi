from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from .views.RegisterView import RegisterView
from .views.LoginView import LoginView
from .views.auth_views import LoginPageView, RegisterPageView
from .views.LogoutView import LogoutView
from .views.home_views import HomePageView
from .views import NewsView
from .views import article_views

# Создаем роутер для API
router = DefaultRouter()
router.register(r'api/news', NewsView.NewsViewSet, basename='news')
router.register(r'api/articles', article_views.ArticleViewSet, basename='articles')

urlpatterns = [
    path('', HomePageView.as_view(), name='home_page'),
    # HTML страницы (со слешем в конце)
    path('login/', LoginPageView.as_view(), name='login_page'),
    path('register/', RegisterPageView.as_view(), name='register_page'),
    
    # API эндпоинты (со слешем в конце)
    path('api/register/', RegisterView.as_view(), name='register_api'),
    path('api/login/', LoginView.as_view(), name='login_api'),
    path('api/logout/', LogoutView.as_view(), name='logout_api'),
    
    # URL для детальной страницы новости
    path('news/<int:pk>/', NewsView.NewsDetailView.as_view(), name='news_detail'),
    
    # URL для статей
    path('articles/', article_views.ArticleListView.as_view(), name='articles_list'),
    path('articles/<int:pk>/', article_views.ArticleDetailView.as_view(), name='article_detail'),
    
    # Включаем все URL из роутера
    path('', include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)