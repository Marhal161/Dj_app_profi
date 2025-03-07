from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View
from django.contrib import messages
from django.db.models import Q, F
from ..models import Class, User, ClassStudent, ClassInvitation
from ..decorators import check_auth_tokens, teacher_required
from django.utils.decorators import method_decorator
import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST

class ClassView(View):
    template_name = 'class.html'
    
    @method_decorator(check_auth_tokens)
    def dispatch(self, request, *args, **kwargs):
        # Проверяем тип пользователя
        if request.is_authenticated and request.user_info['user_type'] not in ['teacher', 'student']:
            messages.error(request, 'Доступ запрещен')
            return redirect('home_page')
            
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, class_id=None, *args, **kwargs):
        if not request.is_authenticated:
            messages.error(request, 'Необходимо войти в систему')
            return redirect('login_page')
            
        user_info = request.user_info
        
        context = {
            'title': 'Мой класс',
            'user_info': user_info,
            'is_authenticated': True
        }
        
        # Для учителя
        if user_info['user_type'] == 'teacher':
            if class_id:
                class_obj = get_object_or_404(Class, id=class_id, teacher__id=user_info['user_id'])
            else:
                class_obj = Class.objects.filter(teacher__id=user_info['user_id']).first()
                if not class_obj:
                    teacher = User.objects.get(id=user_info['user_id'])
                    class_obj = Class.objects.create(
                        name=f"Класс {teacher.username}",
                        teacher=teacher
                    )
            
            students = ClassStudent.objects.filter(class_group=class_obj).select_related('student')
            pending_invitations = ClassInvitation.objects.filter(
                class_group=class_obj,
                status='pending'
            ).select_related('student')
            
            context.update({
                'class': class_obj,
                'students': students,
                'pending_invitations': pending_invitations,
                'is_teacher': True
            })
            
        # Для ученика
        elif user_info['user_type'] == 'student':
            # Получаем класс, в котором состоит ученик
            student_class = ClassStudent.objects.filter(
                student__id=user_info['user_id']
            ).select_related('class_group', 'class_group__teacher').first()
            
            # Получаем активные приглашения для ученика
            invitations = ClassInvitation.objects.filter(
                student__id=user_info['user_id'],
                status='pending'
            ).select_related('class_group', 'class_group__teacher')
            
            if student_class:
                # Получаем учителя
                teacher = student_class.class_group.teacher
                has_liked = teacher.liked_by.filter(id=user_info['user_id']).exists()
                has_disliked = teacher.disliked_by.filter(id=user_info['user_id']).exists()
                
                context.update({
                    'class': student_class.class_group,
                    'teacher': teacher,
                    'has_liked': has_liked,
                    'has_disliked': has_disliked,
                    'classmates': ClassStudent.objects.filter(
                        class_group=student_class.class_group
                    ).select_related('student').exclude(student__id=user_info['user_id']),
                    'is_student': True
                })
            else:
                context.update({
                    'no_class': True,
                    'is_student': True,
                    'invitations': invitations
                })
        
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        if not request.is_authenticated:
            return JsonResponse({
                'success': False,
                'error': 'Необходимо войти в систему'
            })

        if request.user_info['user_type'] != 'student':
            return JsonResponse({
                'success': False,
                'error': 'Только ученики могут выполнять это действие'
            })

        try:
            data = json.loads(request.body)
            action = data.get('action')

            if action == 'leave_class':
                # Получаем запись о членстве ученика в классе
                class_student = ClassStudent.objects.filter(
                    student_id=request.user_info['user_id']
                ).first()

                if not class_student:
                    return JsonResponse({
                        'success': False,
                        'error': 'Вы не состоите в классе'
                    })

                # Удаляем все заявки ученика
                ClassInvitation.objects.filter(
                    student_id=request.user_info['user_id']
                ).delete()

                # Удаляем ученика из класса
                class_student.delete()

                return JsonResponse({
                    'success': True,
                    'message': 'Вы успешно покинули класс'
                })

            return JsonResponse({
                'success': False,
                'error': 'Неизвестное действие'
            })

        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Неверный формат данных'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })

class RenameClassView(View):
    @method_decorator(check_auth_tokens)
    @method_decorator(teacher_required)
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            new_name = data.get('name')
            
            if not new_name:
                return JsonResponse({'success': False, 'error': 'Название не может быть пустым'})
            
            # Получаем класс текущего учителя
            class_group = Class.objects.get(teacher_id=request.user_info['user_id'])
            class_group.name = new_name
            class_group.save()
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

class TeacherRatingView(View):
    @method_decorator(check_auth_tokens)
    @method_decorator(require_POST)
    def post(self, request, teacher_id):
        if not request.user_info or request.user_info['user_type'] != 'student':
            return JsonResponse({
                'success': False,
                'error': 'Только ученики могут оценивать учителей'
            })

        try:
            # Получаем данные из JSON
            data = json.loads(request.body)
            action = data.get('action', 'like')  # Изменено с request.POST на data.get()
            
            teacher = User.objects.get(id=teacher_id, user_type='teacher')
            student = User.objects.get(id=request.user_info['user_id'])

            # Проверяем текущее состояние
            is_liked = teacher.liked_by.filter(id=student.id).exists()
            is_disliked = teacher.disliked_by.filter(id=student.id).exists()

            # Убираем существующие оценки
            if is_liked:
                teacher.liked_by.remove(student)
                teacher.rating = F('rating') - 1
                teacher.save()
                
            if is_disliked:
                teacher.disliked_by.remove(student)
                teacher.rating = F('rating') + 1
                teacher.save()

            # Добавляем новую оценку, только если это не та же самая оценка
            if action == 'like' and not is_liked:
                teacher.liked_by.add(student)
                teacher.rating = F('rating') + 1
                teacher.save()
                liked = True
                disliked = False
            elif action == 'dislike' and not is_disliked:
                teacher.disliked_by.add(student)
                teacher.rating = F('rating') - 1
                teacher.save()
                liked = False
                disliked = True
            else:
                liked = False
                disliked = False

            # Получаем обновленный рейтинг
            teacher.refresh_from_db()
            
            return JsonResponse({
                'success': True,
                'rating': teacher.rating,
                'liked': liked,
                'disliked': disliked
            })

        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Неверный формат данных'
            })
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Учитель не найден'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })

class InvitationHandlerView(View):
    @method_decorator(check_auth_tokens)
    def post(self, request, invitation_id, action):
        if not request.user_info:
            return JsonResponse({
                'success': False,
                'error': 'Необходимо войти в систему'
            })

        try:
            # Получаем приглашение
            invitation = ClassInvitation.objects.select_related('class_group', 'student').get(
                id=invitation_id,
                status='pending'
            )

            # Проверяем права доступа
            if request.user_info['user_type'] == 'teacher':
                # Учитель может обрабатывать только приглашения в свой класс
                if invitation.class_group.teacher_id != request.user_info['user_id']:
                    return JsonResponse({
                        'success': False,
                        'error': 'У вас нет прав для обработки этой заявки'
                    })
            elif request.user_info['user_type'] == 'student':
                # Ученик может только отменять свои заявки
                if invitation.student_id != request.user_info['user_id']:
                    return JsonResponse({
                        'success': False,
                        'error': 'Вы можете отменять только свои заявки'
                    })
                if action != 'reject':
                    return JsonResponse({
                        'success': False,
                        'error': 'Ученики могут только отменять заявки'
                    })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Недостаточно прав'
                })

            if action == 'accept' and request.user_info['user_type'] == 'teacher':
                # Создаем запись о членстве в классе
                ClassStudent.objects.create(
                    class_group=invitation.class_group,
                    student=invitation.student
                )
                invitation.status = 'accepted'
                invitation.save()
                
                return JsonResponse({
                    'success': True,
                    'message': f'Ученик {invitation.student.username} принят в класс'
                })
                
            elif action == 'reject':
                invitation.status = 'rejected'
                invitation.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Заявка отклонена'
                })
                
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Неверное действие'
                })

        except ClassInvitation.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Заявка не найдена'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }) 