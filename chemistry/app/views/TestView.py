from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.utils import timezone
from ..models import Test, TestQuestion, TestAttempt, TestAnswer, Class, ClassStudent
from ..decorators import check_auth_tokens, teacher_required
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
        attempt = get_object_or_404(TestAttempt, id=attempt_id, user_id=user_info['user_id'], test_id=test_id)
        
        # Проверяем, что отправка теста, а не промежуточное сохранение
        if 'submit_test' in request.POST:
            # Получаем все вопросы теста
            questions = TestQuestion.objects.filter(test=test)
            # Базовый балл
            score = 0
            # Флаг наличия вопросов части B
            has_part_b = False
            
            # Обрабатываем ответы
            for question in questions:
                # Сначала сохраняем все ответы
                if f'answer_{question.id}' in request.POST:
                    answer_text = request.POST.get(f'answer_{question.id}')
                    # Проверяем существует ли уже ответ
                    answer, created = TestAnswer.objects.get_or_create(
                        attempt=attempt,
                        question=question,
                        defaults={'answer_text': answer_text}
                    )
                    # Если ответ уже существовал, обновляем его
                    if not created:
                        answer.answer_text = answer_text
                        answer.save()
                    
                    # Проверяем тип вопроса
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
                    elif question.question_type == 'long_answer' or question.question_type == 'part_b':
                        # Для части B отмечаем, что требуется проверка
                        has_part_b = True
            
            # Обновляем статус попытки
            attempt.score = score
            attempt.completed_at = timezone.now()
            
            # После обработки всех ответов
            
            # Проверяем, есть ли в тесте вопросы части B
            has_part_b = TestQuestion.objects.filter(
                test_id=test_id, 
                question_type__in=['long_answer', 'part_b']
            ).exists()
            
            # Если есть вопросы части B, то статус "ожидает проверки", иначе "завершен"
            if has_part_b:
                attempt.status = 'awaiting_review'
            else:
                attempt.status = 'completed'
                
            attempt.save()
            
            messages.success(request, 'Тест успешно завершен')
            return redirect('test_result', test_id=test_id, attempt_id=attempt.id)
        # Обработка промежуточного сохранения (можно убрать)
        else:
            # Сохраняем ответы без завершения теста
            questions = TestQuestion.objects.filter(test=test)
            for question in questions:
                if f'answer_{question.id}' in request.POST:
                    answer_text = request.POST.get(f'answer_{question.id}')
                    answer, created = TestAnswer.objects.get_or_create(
                        attempt=attempt,
                        question=question,
                        defaults={'answer_text': answer_text}
                    )
                    if not created:
                        answer.answer_text = answer_text
                        answer.save()
            
            messages.success(request, 'Ответы сохранены')
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
        
        # Получаем все ответы
        all_answers = TestAnswer.objects.filter(attempt=attempt).select_related('question')
        
        # Разделяем ответы по типам вопросов
        answers_part_a = all_answers.filter(question__question_type='part_a')
        answers_part_b = all_answers.filter(question__question_type__in=['part_b', 'long_answer'])
        
        context = {
            'title': f'Результаты теста: {test.title}',
            'test': test,
            'attempt': attempt,
            'answers': all_answers,
            'answers_part_a': answers_part_a,
            'answers_part_b': answers_part_b,
            'user_info': user_info,
            'is_authenticated': is_authenticated,
        }
        return render(request, self.template_name, context)

class TestReviewView(View):
    template_name = 'tests/test_review.html'
    
    @method_decorator(check_auth_tokens)
    @method_decorator(teacher_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, class_id=None, *args, **kwargs):
        user_info = request.user_info
        is_authenticated = request.is_authenticated
        
        # Получаем класс учителя
        teacher_class = Class.objects.filter(teacher_id=user_info['user_id']).first()
        
        if not teacher_class:
            messages.error(request, 'У вас нет созданных классов')
            return redirect('teacher_dashboard')
            
        # Получаем ID учеников из класса учителя
        student_ids = ClassStudent.objects.filter(
            class_group=teacher_class
        ).values_list('student_id', flat=True)
        
        # Получаем попытки, требующие проверки
        awaiting_attempts = TestAttempt.objects.filter(
            status='awaiting_review',
            user_id__in=student_ids
        ).select_related('test', 'user').order_by('-completed_at')
        
        context = {
            'title': 'Проверка работ',
            'user_info': user_info,
            'is_authenticated': is_authenticated,
            'selected_class': teacher_class,
            'awaiting_attempts': awaiting_attempts,
            'active_page': 'review'
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
        
        # Получаем ответы на часть B (включая long_answer)
        answers_part_b = TestAnswer.objects.filter(
            attempt=attempt,
            question__question_type__in=['part_b', 'long_answer']
        ).select_related('question')
        
        # Получаем уже проверенные ответы на часть A
        answers_part_a = TestAnswer.objects.filter(
            attempt=attempt,
            question__question_type='part_a'
        ).select_related('question')
        
        # Получаем статистику ученика по всем тестам
        student_id = attempt.user_id
        student_answers = TestAnswer.objects.filter(
            attempt__user_id=student_id,
            question__question_type='part_a'  # Только часть A имеет автоматическую проверку
        )
        
        # Общее количество ответов
        total_answers = student_answers.count()
        # Правильные ответы
        correct_answers = student_answers.filter(is_correct=True).count()
        # Неправильные ответы
        incorrect_answers = total_answers - correct_answers
        
        # Процент правильных ответов
        correct_percentage = 0
        if total_answers > 0:
            correct_percentage = round((correct_answers / total_answers) * 100)
        
        # Статистика для текущего теста
        current_test_total = answers_part_a.count()
        current_test_correct = answers_part_a.filter(is_correct=True).count()
        current_test_percentage = 0
        if current_test_total > 0:
            current_test_percentage = round((current_test_correct / current_test_total) * 100)
        
        context = {
            'title': f'Проверка теста: {attempt.test.title}',
            'attempt': attempt,
            'answers_part_b': answers_part_b,
            'answers_part_a': answers_part_a,
            'user_info': user_info,
            'is_authenticated': is_authenticated,
            # Статистика
            'total_answers': total_answers,
            'correct_answers': correct_answers,
            'incorrect_answers': incorrect_answers,
            'correct_percentage': correct_percentage,
            'current_test_total': current_test_total,
            'current_test_correct': current_test_correct,
            'current_test_percentage': current_test_percentage,
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
        
        # Проверка, была ли отправлена форма оценки
        if 'save_review' in request.POST:
            # Получаем все ответы на часть B
            answers_part_b = TestAnswer.objects.filter(
                attempt=attempt,
                question__question_type__in=['part_b', 'long_answer']
            )
            
            # Сумма баллов для части B
            part_b_score = 0
            
            # Обрабатываем оценки и комментарии для каждого ответа
            for answer in answers_part_b:
                points_key = f'points_{answer.id}'
                comment_key = f'comment_{answer.id}'
                
                if points_key in request.POST:
                    # Получаем баллы
                    points = int(request.POST.get(points_key, 0))
                    # Ограничиваем баллы от 0 до 2
                    points = max(0, min(points, 2))
                    
                    # Сохраняем баллы
                    answer.points_awarded = points
                    part_b_score += points
                
                if comment_key in request.POST:
                    # Сохраняем комментарий
                    answer.teacher_comment = request.POST.get(comment_key, '')
                
                answer.save()
            
            # Обновляем общий балл за тест
            # Получаем сумму баллов за часть A
            part_a_score = TestAnswer.objects.filter(
                attempt=attempt,
                question__question_type='part_a',
                is_correct=True
            ).aggregate(Sum('points_awarded'))['points_awarded__sum'] or 0
            
            # Общий балл - сумма баллов за обе части
            attempt.score = part_a_score + part_b_score
            
            # Обновляем статус на "проверен"
            attempt.status = 'reviewed'
            attempt.reviewed_at = timezone.now()
            attempt.save()
            
            messages.success(request, 'Оценка успешно сохранена')
            return redirect('test_review')
        
        # Если форма не отправлена, возвращаемся на страницу
        return self.get(request, attempt_id, *args, **kwargs)

class TestStartView(View):
    template_name = 'tests/test_start.html'
    
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
        
        # Проверяем только незавершенные попытки
        existing_attempt = TestAttempt.objects.filter(
            test=test,
            user_id=user_info['user_id'],
            status='in_progress'
        ).first()
        
        if existing_attempt:
            # Если есть незавершенная попытка, перенаправляем на неё
            return redirect('test_take', test_id=test_id, attempt_id=existing_attempt.id)
        
        context = {
            'title': f'Начать тест: {test.title}',
            'test': test,
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
        
        # Проверяем только незавершенные попытки
        existing_attempt = TestAttempt.objects.filter(
            test=test,
            user_id=user_info['user_id'],
            status='in_progress'
        ).first()
        
        if existing_attempt:
            # Если есть незавершенная попытка, перенаправляем на неё
            return redirect('test_take', test_id=test_id, attempt_id=existing_attempt.id)
        
        # Вычисляем максимальное количество баллов за тест
        max_score = TestQuestion.objects.filter(test=test).aggregate(
            total=Sum('points'))['total'] or 0
        
        # Создаем новую попытку теста
        attempt = TestAttempt.objects.create(
            test=test,
            user_id=user_info['user_id'],  # Django автоматически обработает это
            status='in_progress',
            started_at=timezone.now(),
            max_score=max_score
        )
        
        messages.success(request, 'Тест начат')
        return redirect('test_take', test_id=test_id, attempt_id=attempt.id) 