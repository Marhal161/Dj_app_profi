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
    )
    
    title = models.CharField(max_length=200, verbose_name='Заголовок')
    content = models.TextField(verbose_name='Содержание')
    image = models.ImageField(upload_to='news_images/', blank=True, null=True, verbose_name='Изображение')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='announcement', verbose_name='Категория')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    is_published = models.BooleanField(default=True, verbose_name='Опубликовано')
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = 'новость'
        verbose_name_plural = 'новости'
        ordering = ['-created_at']

class Article(models.Model):
    title = models.CharField(max_length=200, verbose_name='Заголовок')
    content = models.TextField(verbose_name='Содержание')
    image = models.ImageField(upload_to='article_images/', blank=True, null=True, verbose_name='Изображение')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    is_published = models.BooleanField(default=True, verbose_name='Опубликовано')
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = 'статья'
        verbose_name_plural = 'статьи'
        ordering = ['-created_at']

class Material(models.Model):
    title = models.CharField(max_length=200, verbose_name='Заголовок')
    content = models.TextField(verbose_name='Содержание')
    image = models.ImageField(upload_to='material_images/', blank=True, null=True, verbose_name='Изображение')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    
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
    title = models.CharField(max_length=200, verbose_name='Название')
    description = models.TextField(verbose_name='Описание', blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name='Категория')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    is_published = models.BooleanField(default=True, verbose_name='Опубликован')
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = _('тест')
        verbose_name_plural = _('тесты')

class TestQuestion(models.Model):
    QUESTION_TYPES = (
        ('part_a', 'Часть A (краткий ответ)'),
        ('part_b', 'Часть B (развернутый ответ)'),
    )
    
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField(verbose_name='Текст вопроса', null=True, blank=True)
    question_type = models.CharField(max_length=10, choices=QUESTION_TYPES, default='part_a', verbose_name='Тип вопроса')
    answer = models.TextField(verbose_name='Правильный ответ', blank=True, help_text='Для вопросов части A')
    image = models.ImageField(upload_to='question_images/', blank=True, null=True, verbose_name='Основное изображение')
    points = models.PositiveIntegerField(default=1, verbose_name='Баллы')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')
    
    def __str__(self):
        return f"{self.question_text[:50]}..."
    
    class Meta:
        verbose_name = _('вопрос теста')
        verbose_name_plural = _('вопросы теста')
        ordering = ['order', 'id']

class QuestionImage(models.Model):
    question = models.ForeignKey(TestQuestion, on_delete=models.CASCADE, related_name='additional_images')
    image = models.ImageField(upload_to='question_images/', verbose_name='Изображение')
    caption = models.CharField(max_length=255, blank=True, verbose_name='Подпись')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')
    
    def __str__(self):
        return f"Изображение {self.order+1} для вопроса {self.question.id}"
    
    class Meta:
        verbose_name = _('изображение вопроса')
        verbose_name_plural = _('изображения вопросов')
        ordering = ['order']

class TestAttempt(models.Model):
    STATUS_CHOICES = (
        ('in_progress', 'В процессе'),
        ('completed', 'Завершен'),
        ('awaiting_review', 'Ожидает проверки'),
        ('reviewed', 'Проверен'),
        ('archived', 'В архиве'),
    )
    
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='attempts')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='test_attempts')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    score = models.PositiveIntegerField(default=0)
    max_score = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return f"{self.user.username} - {self.test.title}"
    
    def get_percent_score(self):
        if self.max_score == 0:
            return 0
        return int((self.score / self.max_score) * 100)

class TestAnswer(models.Model):
    attempt = models.ForeignKey(TestAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(TestQuestion, on_delete=models.CASCADE)
    answer_text = models.TextField(verbose_name='Ответ')
    is_correct = models.BooleanField(null=True, blank=True, verbose_name='Правильно')
    points_awarded = models.PositiveIntegerField(default=0, verbose_name='Начислено баллов')
    teacher_comment = models.TextField(blank=True, verbose_name='Комментарий учителя')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_answers')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Ответ на вопрос {self.question.id}"

class Class(models.Model):
    name = models.CharField(max_length=50, verbose_name=_('название класса'))
    teacher = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        limit_choices_to={'user_type': 'teacher'},
        related_name='teaching_classes',
        verbose_name=_('учитель')
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('дата создания'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('дата обновления'))
    
    def __str__(self):
        return f"{self.name} - {self.teacher.username}"
    
    class Meta:
        verbose_name = _('класс')
        verbose_name_plural = _('классы')
        unique_together = ['name', 'teacher']

class ClassStudent(models.Model):
    class_group = models.ForeignKey(
        Class, 
        on_delete=models.CASCADE, 
        related_name='students',
        verbose_name=_('класс')
    )
    student = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        limit_choices_to={'user_type': 'student'},
        related_name='enrolled_classes',
        verbose_name=_('ученик')
    )
    joined_at = models.DateTimeField(auto_now_add=True, verbose_name=_('дата присоединения'))
    
    def __str__(self):
        return f"{self.student.username} в классе {self.class_group.name}"
    
    class Meta:
        verbose_name = _('ученик класса')
        verbose_name_plural = _('ученики класса')
        unique_together = ['class_group', 'student']
        ordering = ['joined_at']

class ClassInvitation(models.Model):
    class_group = models.ForeignKey('Class', on_delete=models.CASCADE, related_name='invitations')
    student = models.ForeignKey('User', on_delete=models.CASCADE, related_name='class_invitations')
    status = models.CharField(max_length=20, choices=[
        ('pending', 'В ожидании'),
        ('accepted', 'Принято'),
        ('rejected', 'Отклонено')
    ], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('class_group', 'student')
        ordering = ['-created_at']