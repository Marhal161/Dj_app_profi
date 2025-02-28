from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from .views.RegisterView import RegisterView
from .views.LoginView import LoginView
from .views.auth_views import LoginPageView, RegisterPageView

urlpatterns = [
    # HTML страницы (без слеша в конце)
    path('login', LoginPageView.as_view(), name='login_page'),
    path('register', RegisterPageView.as_view(), name='register_page'),
    
    # API эндпоинты (со слешем в конце)
    path('api/register/', RegisterView.as_view(), name='register_api'),
    path('api/login/', LoginView.as_view(), name='login_api'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)