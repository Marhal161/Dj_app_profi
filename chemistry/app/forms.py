from django import forms
from .models import News

class NewsAdminForm(forms.ModelForm):
    class Meta:
        model = News
        fields = '__all__'
    
    def clean(self):
        cleaned_data = super().clean()
        content_type = cleaned_data.get('content_type')
        category = cleaned_data.get('category')
        
        # Если это статья, проверяем, что категория соответствует
        if content_type == 'article' and category != 'article':
            # Автоматически устанавливаем категорию 'article' для статей
            cleaned_data['category'] = 'article'
        
        return cleaned_data 