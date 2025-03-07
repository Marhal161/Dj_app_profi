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
from .views.ClassView import ClassView, RenameClassView, TeacherRatingView
from .views.MaterialView import MaterialView
from .views.TestView import (
    TestListView, TestDetailView, TestTakeView, 
    TestResultView, TestReviewView, TestReviewDetailView, TestStartView
)
from .views.TeacherView import TeacherDashboardView, StudentDetailView, StudentTestsView
from django.views.decorators.csrf import csrf_protect
from .views.ProfileView import ProfileView
from .views.TeacherRatingView import TeacherRatingListView

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
    path('tests/', TestListView.as_view(), name='test_list'),
    path('tests/<int:test_id>/', TestDetailView.as_view(), name='test_detail'),
    path('tests/<int:test_id>/start/', TestStartView.as_view(), name='test_start'),
    path('tests/<int:test_id>/take/<int:attempt_id>/', TestTakeView.as_view(), name='test_take'),
    path('tests/<int:test_id>/result/<int:attempt_id>/', TestResultView.as_view(), name='test_result'),
    path('tests/review/', TestReviewView.as_view(), name='test_review'),
    path('tests/review/class/<int:class_id>/', TestReviewView.as_view(), name='test_review_class'),
    path('tests/review/<int:attempt_id>/', TestReviewDetailView.as_view(), name='test_review_detail'),
    
    # Панель учителя
    path('dashboard/', TeacherDashboardView.as_view(), name='teacher_dashboard'),
    path('dashboard/student/<int:student_id>/', StudentDetailView.as_view(), name='student_detail'),
    path('dashboard/student/<int:student_id>/tests/', StudentTestsView.as_view(), name='student_tests'),
    path('api/class/rename/', csrf_protect(RenameClassView.as_view()), name='rename_class'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('api/teacher/<int:teacher_id>/rate/', csrf_protect(TeacherRatingView.as_view()), name='rate_teacher'),
    path('teachers/ratings/', TeacherRatingListView.as_view(), name='teacher_ratings'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)