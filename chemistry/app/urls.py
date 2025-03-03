from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from .views.RegisterView import RegisterView
from .views.LoginView import LoginView
from .views.auth_views import LoginPageView, RegisterPageView
from .views.LogoutView import LogoutView
from .views.HomeView import HomePageView
from .views import NewsView
from .views.ArticleView import ArticleViewSet, ArticleListView, ArticleDetailView
from .views.ClassView import ClassView
from .views.MaterialView import MaterialView

# Создаем роутер для API
router = DefaultRouter()
router.register(r'news', NewsView.NewsViewSet, basename='news-api')
router.register(r'articles', ArticleViewSet, basename='articles-api')

urlpatterns = [
    path('', HomePageView.as_view(), name='home_page'),
    # HTML страницы
    path('login/', LoginPageView.as_view(), name='login_page'),
    path('register/', RegisterPageView.as_view(), name='register_page'),
    
    # API эндпоинты
    path('api/register/', RegisterView.as_view(), name='register_api'),
    path('api/login/', LoginView.as_view(), name='login_api'),
    path('api/logout/', LogoutView.as_view(), name='logout_api'),
    
    # HTML страницы для новостей и статей
    path('news/<int:pk>/', NewsView.NewsDetailView.as_view(), name='news_detail'),
    path('articles/', ArticleListView.as_view(), name='articles_list'),
    path('articles/<int:pk>/', ArticleDetailView.as_view(), name='article_detail'),
    
    # API URLs
    path('api/', include(router.urls)),
    path('class/', ClassView.as_view(), name='class'),
    path('class/<int:class_id>/', ClassView.as_view(), name='class_detail'),
    path('materials/', MaterialView.as_view(), name='materials'),
    path('materials/<int:material_id>/', MaterialView.as_view(), name='material_detail'),
    path('materials/delete/<int:material_id>/', MaterialView.as_view(), name='delete_material'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)