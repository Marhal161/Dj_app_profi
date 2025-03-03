from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View
from django.contrib import messages
from django.db.models import Q
from ..models import Class, User, ClassStudent, ClassInvitation
from ..decorators import check_auth_tokens
from django.utils.decorators import method_decorator

class ClassView(View):
    template_name = 'class.html'
    
    @method_decorator(check_auth_tokens)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, class_id=None, *args, **kwargs):
        user_info = request.user_info
        is_authenticated = request.is_authenticated
        
        if not is_authenticated:
            messages.error(request, 'Необходимо войти в систему')
            return redirect('login_page')
        
        context = {
            'title': 'Мой класс',
            'user_info': user_info,
            'is_authenticated': is_authenticated,
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
                context.update({
                    'class': student_class.class_group,
                    'teacher': student_class.class_group.teacher,
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
    
    def post(self, request, class_id=None, *args, **kwargs):
        user_info = request.user_info
        action = request.POST.get('action')
        
        if user_info['user_type'] == 'teacher':
            # Получаем объект класса
            class_obj = get_object_or_404(Class, id=class_id, teacher__id=user_info['user_id'])
            
            if action == 'invite_student':
                student_identifier = request.POST.get('student_identifier')
                
                try:
                    # Добавим логирование
                    print(f"Sending invitation to: {student_identifier}")
                    
                    # Ищем пользователя по имени пользователя или email
                    student = User.objects.filter(
                        Q(username=student_identifier) | 
                        Q(email=student_identifier)
                    ).first()
                    
                    print(f"Found student: {student}")
                    if student:
                        print(f"Student user_type: {getattr(student, 'user_type', 'не указан')}")
                    
                    if not student:
                        messages.error(request, 'Пользователь не найден')
                        return redirect('class_detail', class_id=class_id)
                    
                    # Проверка, что приглашаемый пользователь - ученик
                    if student.user_type != 'student':
                        messages.error(request, f'Пользователь {student.username} не является учеником')
                        return redirect('class_detail', class_id=class_id)
                    
                    # Проверяем, не является ли пользователь уже участником класса
                    if ClassStudent.objects.filter(class_group=class_obj, student=student).exists():
                        messages.warning(request, 'Этот пользователь уже добавлен в класс')
                        return redirect('class_detail', class_id=class_id)
                    
                    # Проверяем все существующие приглашения для этого пользователя
                    existing_invitation = ClassInvitation.objects.filter(
                        class_group=class_obj,
                        student=student
                    ).first()
                    
                    if existing_invitation:
                        # Обрабатываем разные статусы приглашений
                        if existing_invitation.status == 'pending':
                            messages.info(request, 'Приглашение уже отправлено этому пользователю')
                        elif existing_invitation.status == 'rejected':
                            # Если приглашение было отклонено или ученик был удален из класса, можно повторно пригласить
                            existing_invitation.status = 'pending'
                            existing_invitation.save()
                            messages.success(request, f'Приглашение повторно отправлено пользователю {student.username}')
                        elif existing_invitation.status == 'accepted':
                            # Проверяем, был ли ученик удален из класса
                            if not ClassStudent.objects.filter(class_group=class_obj, student=student).exists():
                                # Если ученик был удален, но приглашение осталось в статусе accepted
                                existing_invitation.status = 'pending'
                                existing_invitation.save()
                                messages.success(request, f'Приглашение повторно отправлено пользователю {student.username}')
                            else:
                                messages.warning(request, 'Этот пользователь уже добавлен в класс')
                        return redirect('class_detail', class_id=class_id)
                    
                    # Создаем новое приглашение
                    invitation = ClassInvitation(
                        class_group=class_obj,
                        student=student,
                        status='pending'
                    )
                    invitation.save()
                    
                    print(f"Created invitation: {invitation.id}")
                    
                    # Проверка всех приглашений в классе
                    all_invites = ClassInvitation.objects.filter(class_group=class_obj)
                    print(f"All invitations in class: {all_invites.count()}")
                    for inv in all_invites:
                        print(f"Invite: {inv.id}, Student: {inv.student.username}, Status: {inv.status}")
                    
                    messages.success(request, f'Приглашение отправлено пользователю {student.username}')
                    
                except Exception as e:
                    print(f"Exception: {e}")
                    messages.error(request, f'Ошибка при отправке приглашения: {str(e)}')
                
                return redirect('class_detail', class_id=class_id)
            
            elif action == 'remove_student':
                student_id = request.POST.get('student_id')
                if student_id:
                    # Удаляем ученика из класса
                    ClassStudent.objects.filter(
                        class_group=class_obj,
                        student_id=student_id
                    ).delete()
                    
                    # Также обновляем все приглашения этого ученика в данный класс
                    # Устанавливаем статус "rejected", чтобы потом можно было повторно пригласить
                    ClassInvitation.objects.filter(
                        class_group=class_obj,
                        student_id=student_id,
                    ).update(status='rejected')
                    
                    messages.success(request, 'Ученик удален из класса')
            
            elif action == 'cancel_invitation':
                invitation_id = request.POST.get('invitation_id')
                if invitation_id:
                    # Проверяем, что приглашение принадлежит классу этого учителя
                    invitation = get_object_or_404(
                        ClassInvitation, 
                        id=invitation_id,
                        class_group=class_obj,
                        status='pending'
                    )
                    # Удаляем приглашение
                    invitation.delete()
                    messages.success(request, 'Приглашение отменено')
            
            return redirect('class_detail', class_id=class_id)
            
        elif user_info['user_type'] == 'student':
            if action in ['accept_invitation', 'reject_invitation']:
                invitation_id = request.POST.get('invitation_id')
                print(f"Processing invitation ID: {invitation_id}")
                
                # Проверяем, существует ли приглашение
                try:
                    invitation = ClassInvitation.objects.get(id=invitation_id)
                    print(f"Found invitation: {invitation.id}, status: {invitation.status}")
                    
                    # Проверяем, принадлежит ли приглашение этому ученику
                    if invitation.student.id != user_info['user_id']:
                        print(f"Invitation belongs to student {invitation.student.id}, not {user_info['user_id']}")
                        messages.error(request, 'Это приглашение вам не принадлежит')
                        return redirect('class')
                        
                    if action == 'accept_invitation':
                        # Создаем связь ученика с классом
                        ClassStudent.objects.create(
                            class_group=invitation.class_group,
                            student_id=user_info['user_id']
                        )
                        invitation.status = 'accepted'
                        messages.success(request, f'Вы присоединились к классу {invitation.class_group.name}')
                    else:  # reject_invitation
                        invitation.status = 'rejected'
                        messages.info(request, 'Вы отклонили приглашение')
                    
                    invitation.save()
                
                except ClassInvitation.DoesNotExist:
                    print(f"Invitation {invitation_id} not found")
                    messages.error(request, 'Приглашение не найдено')
                    return redirect('class')
            
            return redirect('class')
        
        messages.error(request, 'Недопустимое действие')
        return redirect('class') 