from django.views import View
from django.shortcuts import render, redirect
from django.db.models import Count, Q, Avg
from ..models import User, Class, ClassStudent
from ..decorators import check_auth_tokens
from django.utils.decorators import method_decorator
from django.http import JsonResponse
import json
from django.contrib import messages

class ProfileView(View):
    template_name = 'profile.html'
    
    @method_decorator(check_auth_tokens)
    def get(self, request, *args, **kwargs):
        user_info = request.user_info
        is_authenticated = request.is_authenticated
        
        if not is_authenticated:
            messages.error(request, 'Необходимо войти в систему')
            return redirect('login_page')
        
        user = User.objects.get(id=user_info['user_id'])
        
        context = {
            'title': 'Профиль',
            'user_info': user_info,
            'is_authenticated': is_authenticated,
            'user': user
        }
        
        if user.is_student():
            # Получаем статистику для ученика
            student_class = ClassStudent.objects.filter(student=user).select_related('class_group', 'class_group__teacher').first()
            student = User.objects.annotate(
                total_tests=Count('test_attempts__test', distinct=True),
                completed_tests=Count(
                    'test_attempts__test',
                    filter=Q(test_attempts__status='reviewed'),
                    distinct=True
                ),
                awaiting_tests=Count(
                    'test_attempts__test',
                    filter=Q(test_attempts__status='awaiting_review'),
                    distinct=True
                ),
                total_answers=Count(
                    'test_attempts__answers',
                    filter=Q(test_attempts__status='reviewed')
                ),
                correct_answers_count=Count(
                    'test_attempts__answers',
                    filter=Q(
                        test_attempts__status='reviewed'
                    ) & (
                        Q(
                            test_attempts__answers__question__question_type='part_a',
                            test_attempts__answers__is_correct=True
                        ) |
                        Q(
                            test_attempts__answers__question__question_type='part_b',
                            test_attempts__answers__points_awarded=2
                        )
                    )
                ),
                incorrect_answers_count=Count(
                    'test_attempts__answers',
                    filter=Q(
                        test_attempts__status='reviewed'
                    ) & (
                        Q(
                            test_attempts__answers__question__question_type='part_a',
                            test_attempts__answers__is_correct=False
                        ) |
                        Q(
                            test_attempts__answers__question__question_type='part_b',
                            test_attempts__answers__points_awarded=0
                        )
                    )
                )
            ).get(id=user.id)
            
            # Вычисляем статистику
            total_answers = student.correct_answers_count + student.incorrect_answers_count
            correct_answers_percent = (
                (student.correct_answers_count / total_answers * 100)
                if total_answers > 0 else 0
            )
            incorrect_answers_percent = (
                (student.incorrect_answers_count / total_answers * 100)
                if total_answers > 0 else 0
            )

            tests_completion = {
                'completed': student.completed_tests,
                'awaiting': student.awaiting_tests,
                'not_started': student.total_tests - student.completed_tests - student.awaiting_tests
            }
            
            context.update({
                'student': student,
                'correct_answers_percent': round(correct_answers_percent, 1),
                'incorrect_answers_percent': round(incorrect_answers_percent, 1),
                'tests_completion': tests_completion,
                'student_class': student_class.class_group if student_class else None,
            })
            return render(request, 'profile/student_profile.html', context)
            
        else:
            # Получаем информацию для учителя
            teacher_class = Class.objects.filter(teacher_id=user.id).first()
            students_count = ClassStudent.objects.filter(class_group=teacher_class).count() if teacher_class else 0
            
            rating_stats = user.get_rating_stats()
            rating_percentage = user.get_rating_percentage()
            
            context.update({
                'teacher_class': teacher_class,
                'students_count': students_count,
                'rating_stats': rating_stats,
                'rating_percentage': rating_percentage
            })
            return render(request, 'profile/teacher_profile.html', context)

    @method_decorator(check_auth_tokens)
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            user = User.objects.get(id=request.user_info['user_id'])
            
            # Обновляем основные поля
            if 'first_name' in data:
                user.first_name = data['first_name']
            if 'last_name' in data:
                user.last_name = data['last_name']
            if 'email' in data:
                user.email = data['email']
            if 'grade' in data and user.is_student():
                user.grade = data['grade']
                
            user.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Профиль успешно обновлен'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400) 