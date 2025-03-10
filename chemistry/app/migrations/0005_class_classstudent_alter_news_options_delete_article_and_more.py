# Generated by Django 4.2.19 on 2025-03-03 11:48

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0004_news_content_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='Class',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='название класса')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='дата создания')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='дата обновления')),
                ('teacher', models.ForeignKey(limit_choices_to={'user_type': 'teacher'}, on_delete=django.db.models.deletion.CASCADE, related_name='teaching_classes', to=settings.AUTH_USER_MODEL, verbose_name='учитель')),
            ],
            options={
                'verbose_name': 'класс',
                'verbose_name_plural': 'классы',
                'unique_together': {('name', 'teacher')},
            },
        ),
        migrations.CreateModel(
            name='ClassStudent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('joined_at', models.DateTimeField(auto_now_add=True, verbose_name='дата присоединения')),
                ('class_group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='students', to='app.class', verbose_name='класс')),
                ('student', models.ForeignKey(limit_choices_to={'user_type': 'student'}, on_delete=django.db.models.deletion.CASCADE, related_name='enrolled_classes', to=settings.AUTH_USER_MODEL, verbose_name='ученик')),
            ],
            options={
                'verbose_name': 'ученик класса',
                'verbose_name_plural': 'ученики класса',
                'ordering': ['joined_at'],
                'unique_together': {('class_group', 'student')},
            },
        ),
        migrations.AlterModelOptions(
            name='news',
            options={'ordering': ['-created_at'], 'verbose_name': 'новость', 'verbose_name_plural': 'новости'},
        ),
        migrations.DeleteModel(
            name='Article',
        ),
        migrations.CreateModel(
            name='Article',
            fields=[
            ],
            options={
                'verbose_name': 'статья',
                'verbose_name_plural': 'статьи',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('app.news',),
        ),
    ]
