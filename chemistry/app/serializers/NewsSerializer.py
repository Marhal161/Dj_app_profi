from rest_framework import serializers
from ..models import News, User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'user_type']

class NewsSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    category_display = serializers.SerializerMethodField()
    
    class Meta:
        model = News
        fields = [
            'id', 'title', 'content', 'image', 'category', 
            'category_display', 'author', 'created_at', 
            'updated_at', 'is_published'
        ]
    
    def get_category_display(self, obj):
        return obj.get_category_display()
    
    def create(self, validated_data):
        # Получаем текущего пользователя из контекста запроса
        user = self.context['request'].user
        news = News.objects.create(author=user, **validated_data)
        return news 