from django.contrib import admin
from .models import User, News, Comment, Category, Test, Article, Material, ClassInvitation, TestQuestion, TestAttempt, TestAnswer, QuestionImage, Class, ClassStudent

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

class QuestionImageInline(admin.TabularInline):
    model = QuestionImage
    extra = 2
    fields = ['image', 'caption', 'order']

class TestQuestionInline(admin.TabularInline):
    model = TestQuestion
    extra = 3
    fields = ['question_type', 'question_text', 'answer', 'image', 'points', 'order']
    inlines = [QuestionImageInline]

@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'created_at', 'is_published')
    list_filter = ('category', 'is_published', 'created_at')
    search_fields = ('title', 'description')
    inlines = [TestQuestionInline]

@admin.register(TestAttempt)
class TestAttemptAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_id', 'test', 'status', 'score', 'started_at', 'completed_at')
    list_filter = ('status', 'test')
    search_fields = ('user_id', 'test__title')
    readonly_fields = ('started_at',)

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

@admin.register(TestQuestion)
class TestQuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'question_text_short', 'test', 'question_type', 'points')
    list_filter = ('test', 'question_type')
    search_fields = ('question_text',)
    fields = ['test', 'question_type', 'question_text', 'answer', 'image', 'points', 'order']
    inlines = [QuestionImageInline]
    
    def question_text_short(self, obj):
        return obj.question_text[:50] + '...' if obj.question_text and len(obj.question_text) > 50 else obj.question_text
    question_text_short.short_description = 'Вопрос'

# В конце файла добавьте регистрацию новой модели, если она нужна отдельно
admin.site.register(QuestionImage)
