from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('student', 'Ученик'),
        ('teacher', 'Учитель'),
    )
    
    user_type = models.CharField(
        max_length=10,
        choices=USER_TYPE_CHOICES,
        default='student',
        verbose_name=_('тип пользователя')
    )
    
    grade = models.CharField(
        max_length=10,
        blank=True,
        verbose_name=_('класс')
    )
    
    def is_teacher(self):
        return self.user_type == 'teacher'
    
    def is_student(self):
        return self.user_type == 'student'
    
    class Meta:
        verbose_name = _('пользователь')
        verbose_name_plural = _('пользователи')

class News(models.Model):
    CATEGORY_CHOICES = (
        ('announcement', 'Объявление'),
        ('update', 'Обновление'),
        ('event', 'Событие'),
        ('article', 'Статья'),
    )
    
    CONTENT_TYPE_CHOICES = (
        ('news', 'Новость'),
        ('article', 'Статья'),
    )
    
    title = models.CharField(max_length=200, verbose_name='Заголовок')
    content = models.TextField(verbose_name='Содержание')
    image = models.ImageField(upload_to='news_images/', blank=True, null=True, verbose_name='Изображение')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='announcement', verbose_name='Категория')
    content_type = models.CharField(max_length=10, choices=CONTENT_TYPE_CHOICES, default='news', verbose_name='Тип контента')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Автор')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    is_published = models.BooleanField(default=True, verbose_name='Опубликовано')
    
    def __str__(self):
        return self.title
    
    def get_category_display(self):
        return dict(self.CATEGORY_CHOICES).get(self.category, '')
    
    class Meta:
        verbose_name = 'новость'
        verbose_name_plural = 'новости'
        ordering = ['-created_at']

class Article(News):
    class Meta:
        proxy = True
        verbose_name = 'статья'
        verbose_name_plural = 'статьи'

    def save(self, *args, **kwargs):
        self.content_type = 'article'
        self.category = 'article'
        super().save(*args, **kwargs)

class Material(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='materials')
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = _('материал')
        verbose_name_plural = _('материалы')

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    content_type = models.ForeignKey('contenttypes.ContentType', on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    
    def __str__(self):
        return f"Комментарий от {self.user.username}"
    
    class Meta:
        verbose_name = _('комментарий')
        verbose_name_plural = _('комментарии')

class Category(models.Model):
    title = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = _('категория')
        verbose_name_plural = _('категории')

class Test(models.Model):
    title = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tests')
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = _('тест')
        verbose_name_plural = _('тесты')
    
class TestQuestion(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='questions')
    question = models.TextField()
    answer = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.question
    
    class Meta:
        verbose_name = _('вопрос теста')
        verbose_name_plural = _('вопросы теста')