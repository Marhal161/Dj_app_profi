from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    user_type = serializers.CharField(required=True, write_only=True)
    grade = serializers.CharField(required=False, write_only=True, allow_blank=True)
    
    class Meta:
        model = User
        fields = ('username', 'password', 'email', 'first_name', 'last_name', 'user_type', 'grade')
    
    def validate(self, data):
        user_type = data.get('user_type')
        if user_type not in ['student', 'teacher']:
            raise serializers.ValidationError({"user_type": "Тип пользователя должен быть 'student' или 'teacher'"})
        
        if user_type == 'student' and not data.get('grade'):
            raise serializers.ValidationError({"grade": "Поле 'grade' обязательно для учеников"})
        
        return data
    
    def create(self, validated_data):
        # Извлекаем поля, которые не относятся к модели User
        user_type = validated_data.pop('user_type')
        grade = validated_data.pop('grade', '')
        
        # Создаем пользователя с правильным хешированием пароля
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            password=validated_data['password'],  # create_user автоматически хеширует пароль
            user_type=user_type,
            grade=grade if user_type == 'student' else ''
        )
        
        return user
    
    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError('Пароль должен содержать не менее 8 символов')
        return value
    
    
    