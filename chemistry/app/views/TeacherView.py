from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.db.models import Count, Avg, Sum, Q
from django.utils import timezone

from ..models import User, Class, ClassStudent, TestAttempt, TestAnswer, Test
from ..decorators import check_auth_tokens, teacher_required

class TeacherDashboardView(View):
    template_name = 'teacher/dashboard.html'
    
    @method_decorator(check_auth_tokens)
    @method_decorator(teacher_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        user_info = request.user_info
        is_authenticated = request.is_authenticated
        
        # Получаем класс этого учителя (предполагаем, что у учителя только 1 класс)
        teacher_class = Class.objects.filter(teacher_id=user_info['user_id']).first()
        
        # Если класс не найден, создаем его
        if not teacher_class:
            teacher = User.objects.get(id=user_info['user_id'])
            teacher_class = Class.objects.create(
                name=f"Класс {teacher.username}",
                teacher=teacher
            )
        
        # Получаем всех учеников из класса этого учителя
        students = User.objects.filter(
            user_type='student',
            id__in=ClassStudent.objects.filter(
                class_group=teacher_class
            ).values_list('student_id', flat=True)
        ).annotate(
            total_tests=Count('test_attempts__test', distinct=True),
            completed_tests=Count('test_attempts__test', 
                filter=Q(test_attempts__status='reviewed'),
                distinct=True
            ),
            avg_score=Avg(
                'test_attempts__score',
                filter=Q(test_attempts__status__in=['completed', 'reviewed'])
            ),
            awaiting_count=Count('test_attempts',
                filter=Q(test_attempts__status='awaiting_review'),
                distinct=True
            ),
            total_answers=Count('test_attempts__answers', 
                filter=Q(
                    test_attempts__status='reviewed'
                )
            ),
            correct_answers=Count('test_attempts__answers',
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
            )
        ).order_by('username')
        
        # Получаем количество тестов, требующих проверки
        tests_awaiting_review = TestAttempt.objects.filter(
            status='awaiting_review',
            user_id__in=students.values_list('id', flat=True)
        ).count()
        
        context = {
            'title': 'Панель учителя',
            'user_info': user_info,
            'is_authenticated': is_authenticated,
            'teacher_class': teacher_class,
            'students': students,
            'tests_awaiting_review': tests_awaiting_review,
            'active_page': 'dashboard'
        }
        
        return render(request, self.template_name, context)

class StudentDetailView(View):
    template_name = 'teacher/student_detail.html'
    
    @method_decorator(check_auth_tokens)
    @method_decorator(teacher_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, student_id, *args, **kwargs):
        user_info = request.user_info
        
        # Получаем ученика со всей необходимой статистикой
        student = get_object_or_404(
            User.objects.annotate(
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
            ),
            id=student_id,
            user_type='student'
        )
        
        # Вычисляем количество правильных и неправильных ответов
        total_answers = student.correct_answers_count + student.incorrect_answers_count
        correct_answers_percent = (
            (student.correct_answers_count / total_answers * 100)
            if total_answers > 0 else 0
        )
        incorrect_answers_percent = (
            (student.incorrect_answers_count / total_answers * 100)
            if total_answers > 0 else 0
        )

        # Вычисляем процент выполненных тестов
        tests_completion = {
            'completed': student.completed_tests,
            'awaiting': student.awaiting_tests,
            'not_started': student.total_tests - student.completed_tests - student.awaiting_tests
        }

        context = {
            'title': f'Ученик: {student.username}',
            'user_info': user_info,
            'student': student,
            'correct_answers_percent': round(correct_answers_percent, 1),
            'incorrect_answers_percent': round(incorrect_answers_percent, 1),
            'tests_completion': tests_completion,
            'active_page': 'students'
        }
        
        return render(request, self.template_name, context)

class StudentTestsView(View):
    template_name = 'teacher/student_tests.html'
    
    @method_decorator(check_auth_tokens)
    @method_decorator(teacher_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, student_id, *args, **kwargs):
        user_info = request.user_info
        is_authenticated = request.is_authenticated
        
        # Получаем класс учителя
        teacher_class = Class.objects.filter(teacher_id=user_info['user_id']).first()
        
        # Проверяем, что ученик принадлежит классу учителя
        student = get_object_or_404(
            User, 
            id=student_id, 
            user_type='student',
            id__in=ClassStudent.objects.filter(
                class_group=teacher_class
            ).values_list('student_id', flat=True)
        )
        
        # Получаем класс ученика
        student_class = ClassStudent.objects.filter(
            student=student,
            class_group=teacher_class
        ).select_related('class_group').first()
        
        # Получаем все попытки прохождения тестов
        test_attempts = TestAttempt.objects.filter(
            user=student
        ).select_related('test').order_by('-started_at')
        
        context = {
            'title': f'Тесты ученика: {student.username}',
            'user_info': user_info,
            'is_authenticated': is_authenticated,
            'student': student,
            'student_class': student_class,
            'test_attempts': test_attempts,
            'active_page': 'students'
        }
        
        return render(request, self.template_name, context)