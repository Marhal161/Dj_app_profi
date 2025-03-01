from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.http import HttpResponseRedirect
from django.contrib.admin import SimpleListFilter
from .models import User, News, Comment, Category, Test, Article
from .forms import NewsAdminForm

class ContentTypeFilter(SimpleListFilter):
    title = 'Тип контента'
    parameter_name = 'content_type'
    
    def lookups(self, request, model_admin):
        return News.CONTENT_TYPE_CHOICES
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(content_type=self.value())
        return queryset

class NewsAdmin(admin.ModelAdmin):
    form = NewsAdminForm
    list_display = ('title', 'category', 'content_type', 'author', 'created_at', 'is_published')
    list_filter = ('category', 'content_type', 'is_published', 'created_at')
    search_fields = ('title', 'content')
    date_hierarchy = 'created_at'
    
    # Добавляем кнопки для создания новостей и статей
    change_list_template = 'admin/news_changelist.html'
    
    actions = ['make_news', 'make_article']
    
    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('add-news/', self.admin_site.admin_view(self.add_news_view), name='add_news'),
            path('add-article/', self.admin_site.admin_view(self.add_article_view), name='add_article'),
        ]
        return custom_urls + urls
    
    def add_news_view(self, request):
        """Представление для добавления новости"""
        return HttpResponseRedirect(
            f"{reverse('admin:app_news_add')}?content_type=news"
        )
    
    def add_article_view(self, request):
        """Представление для добавления статьи"""
        return HttpResponseRedirect(
            f"{reverse('admin:app_news_add')}?content_type=article"
        )
    
    def get_changeform_initial_data(self, request):
        """Предустановка значений при создании объекта"""
        initial = super().get_changeform_initial_data(request)
        
        # Если указан тип контента в параметрах запроса, используем его
        content_type = request.GET.get('content_type')
        if content_type in ['news', 'article']:
            initial['content_type'] = content_type
        
        return initial
    
    fieldsets = (
        (None, {
            'fields': ('title', 'content', 'image', 'category', 'content_type')
        }),
        ('Публикация', {
            'fields': ('author', 'is_published')
        }),
    )
    
    def get_list_display(self, request):
        """Динамически определяем поля для отображения в зависимости от наличия полей в модели"""
        list_display = ['title', 'category', 'author', 'created_at']
        
        # Добавляем поле content_type, если оно существует
        if hasattr(News, 'content_type'):
            list_display.append('content_type')
        
        # Добавляем поле is_published, если оно существует
        if hasattr(News, 'is_published'):
            list_display.append('is_published')
            
        return list_display
    
    def get_list_filter(self, request):
        """Динамически определяем фильтры в зависимости от наличия полей в модели"""
        list_filter = ['category', 'created_at']
        
        # Добавляем фильтр по content_type, если поле существует
        if hasattr(News, 'content_type'):
            list_filter.append('content_type')
        
        # Добавляем фильтр по is_published, если поле существует
        if hasattr(News, 'is_published'):
            list_filter.append('is_published')
            
        return list_filter
    
    def get_fieldsets(self, request, obj=None):
        """Динамически определяем поля для формы в зависимости от наличия полей в модели"""
        fieldsets = [
            (None, {
                'fields': ['title', 'content', 'image', 'category']
            }),
        ]
        
        # Добавляем поле content_type, если оно существует
        if hasattr(News, 'content_type'):
            fieldsets[0][1]['fields'].append('content_type')
        
        # Добавляем секцию публикации
        publication_fields = []
        
        # Добавляем поле author
        publication_fields.append('author')
        
        # Добавляем поле is_published, если оно существует
        if hasattr(News, 'is_published'):
            publication_fields.append('is_published')
        
        if publication_fields:
            fieldsets.append(('Публикация', {
                'fields': publication_fields
            }))
        
        return fieldsets
    
    def save_model(self, request, obj, form, change):
        if not obj.author:
            obj.author = request.user
        super().save_model(request, obj, form, change)
    
    def make_news(self, request, queryset):
        """Действие для преобразования выбранных записей в новости"""
        updated = queryset.update(content_type='news')
        self.message_user(request, f'{updated} записей преобразовано в новости.')
    make_news.short_description = "Преобразовать выбранные записи в новости"
    
    def make_article(self, request, queryset):
        """Действие для преобразования выбранных записей в статьи"""
        updated = queryset.update(content_type='article', category='article')
        self.message_user(request, f'{updated} записей преобразовано в статьи.')
    make_article.short_description = "Преобразовать выбранные записи в статьи"

class ArticleAdmin(admin.ModelAdmin):
    form = NewsAdminForm
    list_display = ('title', 'author', 'created_at', 'is_published')
    list_filter = ('is_published', 'created_at')
    search_fields = ('title', 'content')
    date_hierarchy = 'created_at'
    
    def get_queryset(self, request):
        """Получаем только статьи"""
        qs = super().get_queryset(request)
        return qs.filter(content_type='article')
    
    def save_model(self, request, obj, form, change):
        """Автоматически устанавливаем тип контента 'article'"""
        obj.content_type = 'article'
        obj.category = 'article'  # Устанавливаем категорию 'article' для статей
        if not obj.author:
            obj.author = request.user
        super().save_model(request, obj, form, change)

# Регистрируем модели в админке
admin.site.register(User)
admin.site.register(News, NewsAdmin)
admin.site.register(Article, ArticleAdmin)
admin.site.register(Comment)
admin.site.register(Category)
admin.site.register(Test)
