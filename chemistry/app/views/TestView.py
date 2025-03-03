from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.utils import timezone
from ..models import Test, TestQuestion, TestAttempt, TestAnswer
from ..decorators import check_auth_tokens
from django.utils.decorators import method_decorator
from django.db.models import Sum, Count

class TestListView(View):
    template_name = 'tests/test_list.html'
    
    @method_decorator(check_auth_tokens)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        user_info = request.user_info
        is_authenticated = request.is_authenticated
        
        if not is_authenticated:
            messages.error(request, 'Необходимо войти в систему')
            return redirect('login_page')
        
        tests = Test.objects.filter(is_published=True).order_by('-created_at')
        
        # Добавляем информацию о попытках пользователя
        test_statuses = {}
        if is_authenticated:
            user_attempts = TestAttempt.objects.filter(user_id=user_info['user_id'])
            for attempt in user_attempts:
                test_statuses[attempt.test_id] = {
                    'status': attempt.status,
                    'score': attempt.score,
                    'max_score': attempt.max_score,
                    'percent': attempt.get_percent_score()
                }
        
        context = {
            'title': 'Тесты',
            'tests': tests,
            'test_statuses': test_statuses,
            'user_info': user_info,
            'is_authenticated': is_authenticated,
        }
        return render(request, self.template_name, context)

class TestDetailView(View):
    template_name = 'tests/test_detail.html'
    
    @method_decorator(check_auth_tokens)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, test_id, *args, **kwargs):
        user_info = request.user_info
        is_authenticated = request.is_authenticated
        
        if not is_authenticated:
            messages.error(request, 'Необходимо войти в систему')
            return redirect('login_page')
        
        test = get_object_or_404(Test, id=test_id, is_published=True)
        
        # Проверяем, есть ли уже попытка прохождения теста
        attempt = TestAttempt.objects.filter(user_id=user_info['user_id'], test=test).first()
        
        context = {
            'title': test.title,
            'test': test,
            'attempt': attempt,
            'user_info': user_info,
            'is_authenticated': is_authenticated,
        }
        return render(request, self.template_name, context)
    
    def post(self, request, test_id, *args, **kwargs):
        user_info = request.user_info
        is_authenticated = request.is_authenticated
        
        if not is_authenticated:
            messages.error(request, 'Необходимо войти в систему')
            return redirect('login_page')
        
        test = get_object_or_404(Test, id=test_id, is_published=True)
        
        # Начать новую попытку
        if 'start_test' in request.POST:
            # Проверяем, существует ли уже завершенная попытка
            existing_attempt = TestAttempt.objects.filter(
                user_id=user_info['user_id'], 
                test=test,
                status__in=['completed', 'awaiting_review', 'reviewed']
            ).first()
            
            if existing_attempt:
                messages.error(request, 'Вы уже прошли этот тест')
                return redirect('test_detail', test_id=test_id)
            
            # Удаляем незавершенные попытки
            TestAttempt.objects.filter(user_id=user_info['user_id'], test=test, status='in_progress').delete()
            
            # Создаем новую попытку
            questions = test.questions.all()
            max_score = questions.aggregate(total=Sum('points'))['total'] or 0
            
            attempt = TestAttempt.objects.create(
                user_id=user_info['user_id'],
                test=test,
                max_score=max_score,
                status='in_progress'
            )
            
            return redirect('test_take', test_id=test_id, attempt_id=attempt.id)
        
        return redirect('test_detail', test_id=test_id)

class TestTakeView(View):
    template_name = 'tests/test_take.html'
    
    @method_decorator(check_auth_tokens)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, test_id, attempt_id, *args, **kwargs):
        user_info = request.user_info
        is_authenticated = request.is_authenticated
        
        if not is_authenticated:
            messages.error(request, 'Необходимо войти в систему')
            return redirect('login_page')
        
        test = get_object_or_404(Test, id=test_id, is_published=True)
        attempt = get_object_or_404(
            TestAttempt, 
            id=attempt_id, 
            user_id=user_info['user_id'], 
            test=test, 
            status='in_progress'
        )
        
        questions = test.questions.all().order_by('order', 'id')
        
        # Получаем уже сохраненные ответы
        saved_answers = {}
        for answer in TestAnswer.objects.filter(attempt=attempt):
            saved_answers[answer.question_id] = answer.answer_text
        
        context = {
            'title': f'Прохождение теста: {test.title}',
            'test': test,
            'attempt': attempt,
            'questions': questions,
            'saved_answers': saved_answers,
            'user_info': user_info,
            'is_authenticated': is_authenticated,
        }
        return render(request, self.template_name, context)
    
    def post(self, request, test_id, attempt_id, *args, **kwargs):
        user_info = request.user_info
        is_authenticated = request.is_authenticated
        
        if not is_authenticated:
            messages.error(request, 'Необходимо войти в систему')
            return redirect('login_page')
        
        test = get_object_or_404(Test, id=test_id, is_published=True)
        attempt = get_object_or_404(
            TestAttempt, 
            id=attempt_id, 
            user_id=user_info['user_id'], 
            test=test, 
            status='in_progress'
        )
        
        # Сохранение ответов без завершения теста
        if 'save_answers' in request.POST:
            for key, value in request.POST.items():
                if key.startswith('answer_'):
                    question_id = key.split('_')[1]
                    try:
                        question = TestQuestion.objects.get(id=question_id, test=test)
                        # Проверяем, существует ли уже ответ
                        answer, created = TestAnswer.objects.get_or_create(
                            attempt=attempt,
                            question=question,
                            defaults={'answer_text': value}
                        )
                        if not created:
                            answer.answer_text = value
                            answer.save()
                    except TestQuestion.DoesNotExist:
                        continue
            
            messages.success(request, 'Ответы сохранены')
            return redirect('test_take', test_id=test_id, attempt_id=attempt_id)
        
        # Завершение теста
        elif 'finish_test' in request.POST:
            questions = test.questions.all()
            
            # Сначала сохраняем все ответы
            for key, value in request.POST.items():
                if key.startswith('answer_'):
                    question_id = key.split('_')[1]
                    try:
                        question = TestQuestion.objects.get(id=question_id, test=test)
                        answer, created = TestAnswer.objects.get_or_create(
                            attempt=attempt,
                            question=question,
                            defaults={'answer_text': value}
                        )
                        if not created:
                            answer.answer_text = value
                            answer.save()
                    except TestQuestion.DoesNotExist:
                        continue
            
            # Проверяем ответы на часть A
            score = 0
            has_part_b = False
            
            for question in questions:
                answer = TestAnswer.objects.filter(attempt=attempt, question=question).first()
                if not answer:
                    continue
                    
                if question.question_type == 'part_a':
                    # Автоматическая проверка для части A
                    if answer.answer_text.strip().lower() == question.answer.strip().lower():
                        answer.is_correct = True
                        answer.points_awarded = question.points
                        score += question.points
                    else:
                        answer.is_correct = False
                        answer.points_awarded = 0
                    answer.save()
                else:
                    # Для части B отмечаем, что требуется проверка
                    has_part_b = True
            
            # Обновляем статус попытки
            attempt.score = score
            attempt.completed_at = timezone.now()
            
            if has_part_b:
                attempt.status = 'awaiting_review'
            else:
                attempt.status = 'completed'
                
            attempt.save()
            
            messages.success(request, 'Тест завершен')
            return redirect('test_result', test_id=test_id, attempt_id=attempt_id)
        
        return redirect('test_take', test_id=test_id, attempt_id=attempt_id)

class TestResultView(View):
    template_name = 'tests/test_result.html'
    
    @method_decorator(check_auth_tokens)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, test_id, attempt_id, *args, **kwargs):
        user_info = request.user_info
        is_authenticated = request.is_authenticated
        
        if not is_authenticated:
            messages.error(request, 'Необходимо войти в систему')
            return redirect('login_page')
        
        test = get_object_or_404(Test, id=test_id)
        attempt = get_object_or_404(
            TestAttempt, 
            id=attempt_id, 
            user_id=user_info['user_id'], 
            test=test
        )
        
        # Если тест еще не завершен, перенаправляем
        if attempt.status == 'in_progress':
            return redirect('test_take', test_id=test_id, attempt_id=attempt_id)
        
        answers = TestAnswer.objects.filter(attempt=attempt).select_related('question')
        
        context = {
            'title': f'Результаты теста: {test.title}',
            'test': test,
            'attempt': attempt,
            'answers': answers,
            'user_info': user_info,
            'is_authenticated': is_authenticated,
        }
        return render(request, self.template_name, context)

class TestReviewView(View):
    template_name = 'tests/test_review.html'
    
    @method_decorator(check_auth_tokens)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        user_info = request.user_info
        is_authenticated = request.is_authenticated
        
        if not is_authenticated or user_info.get('user_type') != 'teacher':
            messages.error(request, 'Доступ запрещен')
            return redirect('home_page')
        
        # Получаем попытки, ожидающие проверки
        if 'class_id' in kwargs:
            # Если указан класс, показываем только учеников этого класса
            class_id = kwargs['class_id']
            class_obj = get_object_or_404(Class, id=class_id, teacher_id=user_info['user_id'])
            
            student_ids = ClassStudent.objects.filter(class_group=class_obj).values_list('student_id', flat=True)
            
            pending_attempts = TestAttempt.objects.filter(
                status='awaiting_review',
                user_id__in=student_ids
            ).select_related('user', 'test')
        else:
            # Показываем всех учеников, которые проходили тесты
            pending_attempts = TestAttempt.objects.filter(
                status='awaiting_review'
            ).select_related('user', 'test')
        
        context = {
            'title': 'Проверка тестов',
            'pending_attempts': pending_attempts,
            'user_info': user_info,
            'is_authenticated': is_authenticated,
        }
        return render(request, self.template_name, context)

class TestReviewDetailView(View):
    template_name = 'tests/test_review_detail.html'
    
    @method_decorator(check_auth_tokens)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, attempt_id, *args, **kwargs):
        user_info = request.user_info
        is_authenticated = request.is_authenticated
        
        if not is_authenticated or user_info.get('user_type') != 'teacher':
            messages.error(request, 'Доступ запрещен')
            return redirect('home_page')
        
        attempt = get_object_or_404(TestAttempt, id=attempt_id)
        
        # Если тест уже проверен, показываем результаты
        if attempt.status not in ['awaiting_review', 'reviewed']:
            messages.error(request, 'Этот тест не нуждается в проверке')
            return redirect('test_review')
        
        # Получаем ответы на часть B
        answers = TestAnswer.objects.filter(
            attempt=attempt,
            question__question_type='part_b'
        ).select_related('question')
        
        # Получаем уже проверенные ответы на часть A
        part_a_answers = TestAnswer.objects.filter(
            attempt=attempt,
            question__question_type='part_a'
        ).select_related('question')
        
        context = {
            'title': f'Проверка теста: {attempt.test.title}',
            'attempt': attempt,
            'answers': answers,
            'part_a_answers': part_a_answers,
            'user_info': user_info,
            'is_authenticated': is_authenticated,
        }
        return render(request, self.template_name, context)
    
    def post(self, request, attempt_id, *args, **kwargs):
        user_info = request.user_info
        is_authenticated = request.is_authenticated
        
        if not is_authenticated or user_info.get('user_type') != 'teacher':
            messages.error(request, 'Доступ запрещен')
            return redirect('home_page')
        
        attempt = get_object_or_404(TestAttempt, id=attempt_id)
        
        # Если тест уже проверен, показываем результаты
        if attempt.status not in ['awaiting_review', 'reviewed']:
            messages.error(request, 'Этот тест не нуждается в проверке')
            return redirect('test_review')
        
        if 'save_review' in request.POST:
            additional_score = 0
            
            for key, value in request.POST.items():
                if key.startswith('points_'):
                    answer_id = key.split('_')[1]
                    try:
                        answer = TestAnswer.objects.get(id=answer_id, attempt=attempt)
                        points = int(value) if value.isdigit() else 0
                        # Ограничиваем количество баллов максимумом для вопроса
                        max_points = answer.question.points
                        points = min(points, max_points)
                        
                        answer.points_awarded = points
                        
                        # Получаем комментарий
                        comment_key = f'comment_{answer_id}'
                        if comment_key in request.POST:
                            answer.teacher_comment = request.POST[comment_key]
                        
                        answer.reviewed_by_id = user_info['user_id']
                        answer.reviewed_at = timezone.now()
                        answer.save()
                        
                        additional_score += points
                    except (TestAnswer.DoesNotExist, ValueError):
                        continue
            
            # Обновляем общий балл и статус попытки
            attempt.score += additional_score
            attempt.status = 'reviewed'
            attempt.save()
            
            messages.success(request, 'Тест проверен')
            return redirect('test_review')
        
        return redirect('test_review_detail', attempt_id=attempt_id) 