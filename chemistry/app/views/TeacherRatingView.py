from django.views import View
from django.shortcuts import render
from django.utils.decorators import method_decorator
from ..decorators import check_auth_tokens
from ..models import User, ClassStudent, ClassInvitation, Class
from django.db.models import Count
from django.http import JsonResponse
import logging

logger = logging.getLogger(__name__)

class TeacherRatingListView(View):
    template_name = 'ratings/teacher_ratings.html'
    
    @method_decorator(check_auth_tokens)
    def dispatch(self, request, *args, **kwargs):
        # Этот метод будет вызываться перед get и post
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request):
        # Получаем всех учителей, отсортированных по рейтингу
        teachers = User.objects.filter(user_type='teacher').annotate(
            likes_count=Count('liked_by'),
            dislikes_count=Count('disliked_by')
        ).order_by('-rating', '-activity_score')

        # Если пользователь аутентифицирован и является студентом
        if getattr(request, 'is_authenticated', False) and request.user_info['user_type'] == 'student':
            student_id = request.user_info['user_id']
            
            # Проверяем, состоит ли студент в каком-либо классе
            has_class = ClassStudent.objects.filter(student_id=student_id).exists()
            
            # Получаем список ID учителей, которым студент уже отправил заявки
            pending_requests = ClassInvitation.objects.filter(
                student_id=student_id,
                status='pending'
            ).values_list('class_group__teacher_id', flat=True)

            # Добавляем информацию к каждому учителю
            for teacher in teachers:
                teacher.has_pending_request = teacher.id in pending_requests
        else:
            has_class = False

        context = {
            'title': 'Рейтинг учителей',
            'teachers': teachers,
            'is_authenticated': getattr(request, 'is_authenticated', False),
            'user_info': {
                **(request.user_info or {}),
                'has_class': has_class
            }
        }
        
        return render(request, self.template_name, context)

    def post(self, request, teacher_id):
        logger.debug(f"Received join request for teacher {teacher_id}")
        
        # Проверяем аутентификацию
        if not hasattr(request, 'user_info') or not request.user_info:
            return JsonResponse({
                'success': False,
                'error': 'Необходимо войти в систему'
            })

        if request.user_info['user_type'] != 'student':
            return JsonResponse({
                'success': False,
                'error': 'Только ученики могут отправлять заявки'
            })

        try:
            student = User.objects.get(id=request.user_info['user_id'])
            
            # Проверяем, не состоит ли ученик уже в классе
            if ClassStudent.objects.filter(student=student).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Вы уже состоите в классе'
                })

            teacher = User.objects.get(id=teacher_id, user_type='teacher')
            
            # Проверяем существующие заявки
            if ClassInvitation.objects.filter(
                student=student,
                status='pending'
            ).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'У вас уже есть активная заявка'
                })

            # Получаем класс учителя
            teacher_class = Class.objects.filter(teacher=teacher).first()
            if not teacher_class:
                return JsonResponse({
                    'success': False,
                    'error': 'У учителя нет активного класса'
                })

            # Создаем новое приглашение
            ClassInvitation.objects.create(
                class_group=teacher_class,
                student=student,
                initiated_by='student'
            )

            return JsonResponse({
                'success': True,
                'message': 'Заявка успешно отправлена'
            })

        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Пользователь не найден'
            })
        except Exception as e:
            logger.error(f"Error processing join request: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': 'Произошла ошибка при обработке запроса'
            }) 