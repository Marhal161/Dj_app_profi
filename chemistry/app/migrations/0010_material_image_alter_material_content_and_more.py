# Generated by Django 4.2.19 on 2025-03-03 14:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0009_remove_material_author_remove_material_category_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='material',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='material_images/', verbose_name='Изображение'),
        ),
        migrations.AlterField(
            model_name='material',
            name='content',
            field=models.TextField(verbose_name='Содержание'),
        ),
        migrations.AlterField(
            model_name='material',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Дата создания'),
        ),
        migrations.AlterField(
            model_name='material',
            name='title',
            field=models.CharField(max_length=200, verbose_name='Заголовок'),
        ),
    ]
