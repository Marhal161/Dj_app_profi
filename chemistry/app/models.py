from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('teacher', 'Учитель'),
        ('student', 'Ученик'),
    )
    
    user_type = models.CharField(
        _('тип пользователя'),
        max_length=10,
        choices=USER_TYPE_CHOICES,
        default='student'
    )
    
    grade = models.CharField(max_length=20, blank=True)
    
    def is_teacher(self):
        return self.user_type == 'teacher'
    
    def is_student(self):
        return self.user_type == 'student'
    
    class Meta:
        verbose_name = _('пользователь')
        verbose_name_plural = _('пользователи')

class News(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = _('новость')
        verbose_name_plural = _('новости')

class Article(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='articles')
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = _('статья')
        verbose_name_plural = _('статьи')

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
