from rest_framework import serializers
from ..models import Article, User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'user_type']

class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = [
            'id', 'title', 'content', 'image',
            'created_at', 'updated_at', 'is_published'
        ] 