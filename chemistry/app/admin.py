from django.contrib import admin
from .models import User, News, Comment, Category, Test, Article, Material, ClassInvitation

class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'created_at', 'is_published')
    list_filter = ('category', 'is_published', 'created_at')
    search_fields = ('title', 'content')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (None, {
            'fields': ('title', 'content', 'image', 'category', 'is_published')
        }),
    )

class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at', 'is_published')
    list_filter = ('is_published', 'created_at')
    search_fields = ('title', 'content')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (None, {
            'fields': ('title', 'content', 'image', 'is_published')
        }),
    )

class TestAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('title',)
    
    fieldsets = (
        (None, {
            'fields': ('title', 'category')
        }),
    )

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'user_type')
    list_filter = ('user_type',)
    search_fields = ('username', 'email')

@admin.register(ClassInvitation)
class ClassInvitationAdmin(admin.ModelAdmin):
    list_display = ('class_group', 'student', 'status')
    list_filter = ('status',)

# Регистрируем модели в админке
admin.site.register(News, NewsAdmin)
admin.site.register(Article, ArticleAdmin)
admin.site.register(Comment)
admin.site.register(Category)
admin.site.register(Test, TestAdmin)

# Регистрация модели Material в админке
@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at')
    search_fields = ('title', 'content')
    list_filter = ('created_at',)
    fieldsets = (
        (None, {
            'fields': ('title', 'content', 'image')
        }),
    )
