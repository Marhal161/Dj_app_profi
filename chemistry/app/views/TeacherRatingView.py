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
        ).order_by('-rating', '-activity_score')  # Сначала по рейтингу, потом по активности
        
        context = {
            'title': 'Рейтинг учителей',
            'teachers': teachers,
            'is_authenticated': getattr(request, 'is_authenticated', False),
            'user_info': getattr(request, 'user_info', None)
        }
        
        return render(request, self.template_name, context)

    def post(self, request, teacher_id):
        logger.debug(f"Received join request for teacher {teacher_id}")
        
        # Проверяем аутентификацию через user_info
        if not hasattr(request, 'user_info') or not request.user_info:
            logger.warning("User not authenticated")
            return JsonResponse({
                'success': False,
                'error': 'Необходимо войти в систему'
            })

        if request.user_info['user_type'] != 'student':
            logger.warning(f"Wrong user type: {request.user_info['user_type']}")
            return JsonResponse({
                'success': False,
                'error': 'Только ученики могут отправлять заявки'
            })

        try:
            teacher = User.objects.get(id=teacher_id, user_type='teacher')
            student = User.objects.get(id=request.user_info['user_id'])
            
            logger.debug(f"Processing request from student {student.id} to teacher {teacher.id}")

            # Проверяем, не состоит ли ученик уже в каком-либо классе
            if ClassStudent.objects.filter(student=student).exists():
                logger.warning(f"Student {student.id} already in a class")
                return JsonResponse({
                    'success': False,
                    'error': 'Вы уже состоите в классе'
                })

            # Получаем класс учителя
            teacher_class = Class.objects.filter(teacher=teacher).first()
            if not teacher_class:
                logger.warning(f"Teacher {teacher.id} has no active class")
                return JsonResponse({
                    'success': False,
                    'error': 'У учителя нет активного класса'
                })

            # Проверяем существующие приглашения
            existing_invitation = ClassInvitation.objects.filter(
                student=student,
                class_group=teacher_class
            ).first()

            if existing_invitation:
                if existing_invitation.status == 'pending':
                    return JsonResponse({
                        'success': False,
                        'error': 'У вас уже есть активная заявка к этому учителю'
                    })
                else:
                    # Обновляем существующее приглашение
                    existing_invitation.status = 'pending'
                    existing_invitation.initiated_by = 'student'
                    existing_invitation.save()
                    logger.info(f"Updated invitation {existing_invitation.id} for student {student.id} to class {teacher_class.id}")
                    
                    return JsonResponse({
                        'success': True,
                        'message': 'Заявка успешно отправлена'
                    })
            else:
                # Создаем новое приглашение
                invitation = ClassInvitation.objects.create(
                    class_group=teacher_class,
                    student=student,
                    initiated_by='student'
                )
                logger.info(f"Created invitation {invitation.id} for student {student.id} to class {teacher_class.id}")

                return JsonResponse({
                    'success': True,
                    'message': 'Заявка успешно отправлена'
                })

        except User.DoesNotExist:
            logger.error(f"Teacher {teacher_id} not found")
            return JsonResponse({
                'success': False,
                'error': 'Учитель не найден'
            })
        except Exception as e:
            logger.error(f"Error processing join request: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': str(e)
            }) 