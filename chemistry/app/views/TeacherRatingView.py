from django.views import View
from django.shortcuts import render
from django.utils.decorators import method_decorator
from ..decorators import check_auth_tokens
from ..models import User
from django.db.models import Count

class TeacherRatingListView(View):
    template_name = 'ratings/teacher_ratings.html'
    
    @method_decorator(check_auth_tokens)
    def get(self, request):
        # Получаем всех учителей, отсортированных по рейтингу
        teachers = User.objects.filter(user_type='teacher').annotate(
            likes_count=Count('liked_by'),
            dislikes_count=Count('disliked_by')
        ).order_by('-rating')
        
        context = {
            'title': 'Рейтинг учителей',
            'teachers': teachers,
            'is_authenticated': getattr(request, 'is_authenticated', False),
            'user_info': getattr(request, 'user_info', None)
        }
        
        return render(request, self.template_name, context) 