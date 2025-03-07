from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.utils import timezone
from ..models import Test, TestQuestion, TestAttempt, TestAnswer, Class, ClassStudent, User
from ..decorators import check_auth_tokens, teacher_required
from django.utils.decorators import method_decorator
from django.db.models import Sum, Count
from django.http import JsonResponse
import json
import logging

logger = logging.getLogger(__name__)

class TestListView(View):
    template_name = 'tests/test_list.html'
    
    @method_decorator(check_auth_tokens, name='dispatch')
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        user_info = request.user_info if hasattr(request, 'user_info') else None
        is_authenticated = request.is_authenticated if hasattr(request, 'is_authenticated') else False
        
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
        is_authenticated = hasattr(request, 'user_info') and request.user_info is not None
        
        test = get_object_or_404(Test, id=test_id)
        
        # Если пользователь учитель, показываем сообщение
        if is_authenticated and user_info.get('user_type') == 'teacher':
            messages.warning(request, 'Учителя не могут проходить тесты')
            return redirect('test_list')
        
        # Если тест не опубликован и пользователь не учитель
        if not test.is_published and (not is_authenticated or user_info.get('user_type') != 'teacher'):
            messages.error(request, 'Тест недоступен')
            return redirect('test_list')
        
        # Проверяем, есть ли уже попытка прохождения теста
        attempt = None
        if is_authenticated:
            attempt = TestAttempt.objects.filter(user_id=user_info['user_id'], test=test).first()
        else:
            # Для неавторизованных проверяем сессию
            session_attempt = request.session.get('temp_attempt', {})
            if session_attempt and str(session_attempt.get('test_id')) == str(test_id):
                attempt = type('TempAttempt', (), {
                    'status': session_attempt.get('status', 'in_progress'),
                    'started_at': session_attempt.get('started_at')
                })
        
        context = {
            'title': test.title,
            'test': test,
            'attempt': attempt,
            'user_info': user_info,
            'is_authenticated': is_authenticated,
        }
        return render(request, self.template_name, context)
    
    def post(self, request, test_id, *args, **kwargs):
        user_info = getattr(request, 'user_info', None)
        is_authenticated = getattr(request, 'is_authenticated', False)
        
        test = get_object_or_404(Test, id=test_id, is_published=True)
        
        # Начать новую попытку
        if 'start_test' in request.POST:
            if is_authenticated:
                # Для авторизованных пользователей - обычная логика с БД
                existing_attempt = TestAttempt.objects.filter(
                    user_id=user_info['user_id'], 
                    test=test,
                    status__in=['completed', 'awaiting_review', 'reviewed']
                ).first()
                
                if existing_attempt:
                    messages.error(request, 'Вы уже прошли этот тест')
                    return redirect('test_detail', test_id=test_id)
                
                # Удаляем незавершенные попытки
                TestAttempt.objects.filter(
                    user_id=user_info['user_id'], 
                    test=test, 
                    status='in_progress'
                ).delete()
                
                # Создаем новую попытку
                max_score = test.questions.all().aggregate(total=Sum('points'))['total'] or 0
                attempt = TestAttempt.objects.create(
                    user_id=user_info['user_id'],
                    test=test,
                    max_score=max_score,
                    status='in_progress'
                )
                
                return redirect('test_take', test_id=test_id, attempt_id=attempt.id)
            else:
                # Для неавторизованных - создаем временную попытку в сессии
                session_attempt = {
                    'test_id': test_id,
                    'started_at': timezone.now().isoformat(),
                    'status': 'in_progress',
                    'answers': {},
                    'max_score': test.questions.filter(
                        question_type='part_a'
                    ).aggregate(total=Sum('points'))['total'] or 0
                }
                request.session['temp_attempt'] = session_attempt
                return redirect('test_take', test_id=test_id, attempt_id=0)
        
        return redirect('test_detail', test_id=test_id)

class TestTakeView(View):
    template_name = 'tests/test_take.html'
    
    @method_decorator(check_auth_tokens)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, test_id, attempt_id, *args, **kwargs):
        user_info = request.user_info
        is_authenticated = hasattr(request, 'user_info') and request.user_info is not None
        
        test = get_object_or_404(Test, id=test_id, is_published=True)
        
        if is_authenticated:
            # Для авторизованных - обычная логика с БД
            attempt = get_object_or_404(TestAttempt, id=attempt_id, test=test)
            
            # Проверяем, что попытка принадлежит текущему пользователю
            if attempt.user_id != user_info['user_id']:
                messages.error(request, 'У вас нет доступа к этой попытке')
                return redirect('test_list')
            
            # Получаем все вопросы для авторизованного пользователя
            questions = TestQuestion.objects.filter(test=test).order_by('order')
            
            # Получаем уже данные ответы
            answers = TestAnswer.objects.filter(attempt=attempt)
            answered_questions = {answer.question_id: answer for answer in answers}
        else:
            # Для неавторизованных - берем данные из сессии
            session_attempt = request.session.get('temp_attempt', {})
            if not session_attempt or str(session_attempt.get('test_id')) != str(test_id):
                messages.error(request, 'Попытка не найдена')
                return redirect('test_list')
            
            # Получаем только вопросы части A
            questions = TestQuestion.objects.filter(test=test, question_type='part_a').order_by('order')
            answered_questions = session_attempt.get('answers', {})
            attempt = type('TempAttempt', (), {
                'id': 0,
                'status': session_attempt.get('status', 'in_progress'),
                'max_score': session_attempt.get('max_score', 0)
            })()
        
        context = {
            'title': test.title,
            'test': test,
            'attempt': attempt,
            'questions': questions,
            'answered_questions': answered_questions,
            'user_info': user_info,
            'is_authenticated': is_authenticated,
        }
        
        return render(request, self.template_name, context)
    
    def post(self, request, test_id, attempt_id, *args, **kwargs):
        user_info = getattr(request, 'user_info', None)
        is_authenticated = user_info is not None and 'user_id' in user_info
        
        test = get_object_or_404(Test, id=test_id, is_published=True)
        
        if is_authenticated:
            # Для авторизованных - обычная логика с БД
            attempt = get_object_or_404(TestAttempt, id=attempt_id, test=test)
            
            # Проверяем, что попытка принадлежит текущему пользователю
            if attempt.user_id != user_info['user_id']:
                messages.error(request, 'У вас нет доступа к этой попытке')
                return redirect('test_list')
            
            # Если тест уже завершен, перенаправляем на результаты
            if attempt.status != 'in_progress':
                return redirect('test_result', test_id=test_id, attempt_id=attempt_id)
            
            # Обработка ответов для авторизованных пользователей
            score = 0
            for question in TestQuestion.objects.filter(test=test):
                answer_text = request.POST.get(f'answer_{question.id}', '').strip()
                if answer_text:
                    answer, created = TestAnswer.objects.update_or_create(
                        attempt=attempt,
                        question=question,
                        defaults={'answer_text': answer_text}
                    )
                    
                    if question.question_type == 'part_a':
                        is_correct = answer_text.lower() == question.answer.lower()
                        answer.is_correct = is_correct
                        answer.points_awarded = question.points if is_correct else 0
                        score += answer.points_awarded
                    answer.save()
            
            # Обновляем статус попытки
            attempt.score = score
            attempt.status = 'awaiting_review'
            attempt.completed_at = timezone.now()
            attempt.save()
            
            return redirect('test_result', test_id=test_id, attempt_id=attempt_id)
        else:
            # Для неавторизованных - обрабатываем в сессии
            session_attempt = request.session.get('temp_attempt', {})
            if not session_attempt or session_attempt.get('test_id') != test_id:
                return redirect('test_list')
            
            questions = TestQuestion.objects.filter(test=test, question_type='part_a')
            answers = {}
            score = 0
            
            for question in questions:
                answer_text = request.POST.get(f'answer_{question.id}', '').strip()
                if answer_text:
                    is_correct = answer_text.lower() == question.answer.lower()
                    points = question.points if is_correct else 0
                    score += points
                    
                    answers[str(question.id)] = {
                        'answer_text': answer_text,
                        'is_correct': is_correct,
                        'points_awarded': points,
                        'question_text': question.question_text,
                        'correct_answer': question.answer,
                        'max_points': question.points
                    }
            
            session_attempt.update({
                'status': 'reviewed',
                'completed_at': timezone.now().isoformat(),
                'answers': answers,
                'score': score
            })
            
            request.session['temp_attempt'] = session_attempt
            
            return redirect('test_result', test_id=test_id, attempt_id=0)

class TestResultView(View):
    template_name = 'tests/test_result.html'
    
    @method_decorator(check_auth_tokens)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, test_id, attempt_id, *args, **kwargs):
        user_info = request.user_info
        is_authenticated = hasattr(request, 'user_info') and request.user_info is not None
        
        test = get_object_or_404(Test, id=test_id, is_published=True)
        
        if is_authenticated:
            # Для авторизованных - обычная логика с БД
            attempt = get_object_or_404(TestAttempt, id=attempt_id, test=test)
            answers = TestAnswer.objects.filter(attempt=attempt).select_related('question').order_by('question__order')
            
            # Разделяем ответы по типам вопросов
            answers_part_a = [a for a in answers if a.question.question_type == 'part_a']
            answers_part_b = [a for a in answers if a.question.question_type in ['part_b', 'long_answer']]
            
            # Считаем статистику
            total_score = attempt.score
            max_score = attempt.max_score
            
            # Вычисляем процент
            percentage = (total_score / max_score * 100) if max_score > 0 else 0
            
            context = {
                'title': f'Результаты теста: {test.title}',
                'test': test,
                'attempt': attempt,
                'answers_part_a': answers_part_a,
                'answers_part_b': answers_part_b,
                'total_score': total_score,
                'max_score': max_score,
                'percentage': round(percentage, 1),
                'user_info': user_info,
                'is_authenticated': is_authenticated,
            }
        else:
            # Для неавторизованных - берем данные из сессии
            session_attempt = request.session.get('temp_attempt', {})
            if not session_attempt or session_attempt.get('test_id') != test_id:
                return redirect('test_list')
            
            # Создаем временные объекты для шаблона
            answers_part_a = []
            for q_id, answer_data in session_attempt.get('answers', {}).items():
                answer = type('TempAnswer', (), {
                    'question': type('TempQuestion', (), {
                        'text': answer_data['question_text'],
                        'answer': answer_data['correct_answer'],
                        'points': answer_data['max_points']
                    })(),
                    'answer_text': answer_data['answer_text'],
                    'is_correct': answer_data['is_correct'],
                    'points_awarded': answer_data['points_awarded']
                })()
                answers_part_a.append(answer)
            
            context = {
                'title': f'Результаты теста: {test.title}',
                'test': test,
                'attempt': type('TempAttempt', (), {
                    'status': session_attempt.get('status', 'reviewed'),
                    'score': session_attempt.get('score', 0),
                    'max_score': session_attempt.get('max_score', 0)
                })(),
                'answers_part_a': answers_part_a,
                'answers_part_b': [],
                'total_score': session_attempt.get('score', 0),
                'max_score': session_attempt.get('max_score', 0),
                'percentage': round(session_attempt.get('score', 0) / session_attempt.get('max_score', 1) * 100, 1),
                'user_info': user_info,
                'is_authenticated': is_authenticated,
            }
            
            # Очищаем временную попытку из сессии
            if 'temp_attempt' in request.session:
                del request.session['temp_attempt']
        
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
    
    @method_decorator(check_auth_tokens)
    @method_decorator(teacher_required)
    def post(self, request, attempt_id):
        try:
            if not request.body:
                return JsonResponse({
                    'success': False,
                    'error': 'Отсутствуют данные для проверки'
                })

            data = json.loads(request.body)
            
            if 'score' not in data:
                return JsonResponse({
                    'success': False,
                    'error': 'Не указана оценка'
                })

            test_attempt = TestAttempt.objects.get(id=attempt_id)
            
            # Проверяем, что учитель имеет право проверять этот тест
            student_class = ClassStudent.objects.filter(
                student=test_attempt.user
            ).first()

            if not student_class or student_class.class_group.teacher_id != request.user_info['user_id']:
                return JsonResponse({
                    'success': False,
                    'error': 'У вас нет прав для проверки этого теста'
                })

            # Обновляем оценку и статус
            test_attempt.score = data['score']
            
            # Обновляем комментарии к ответам
            if 'feedback' in data and isinstance(data['feedback'], dict):
                for answer_id, comment in data['feedback'].items():
                    try:
                        answer = TestAnswer.objects.get(
                            id=answer_id,
                            attempt=test_attempt
                        )
                        answer.teacher_comment = comment
                        answer.save()
                    except TestAnswer.DoesNotExist:
                        continue

            test_attempt.status = 'checked'
            test_attempt.checked_at = timezone.now()
            test_attempt.save()

            # Увеличиваем активность учителя
            teacher = User.objects.get(id=request.user_info['user_id'])
            teacher.activity_score += 5
            teacher.save()
            teacher.update_rating()

            return JsonResponse({
                'success': True,
                'message': 'Тест успешно проверен'
            })

        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Неверный формат данных'
            })
        except Exception as e:
            logger.error(f"Error in test review: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': str(e)
            })

class TestStartView(View):
    template_name = 'tests/test_start.html'
    
    @method_decorator(check_auth_tokens)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, test_id, *args, **kwargs):
        user_info = request.user_info
        is_authenticated = hasattr(request, 'user_info') and request.user_info is not None
        
        test = get_object_or_404(Test, id=test_id, is_published=True)
        
        # Если пользователь авторизован
        if is_authenticated:
            # Проверка на учителя
            if user_info.get('user_type') == 'teacher':
                messages.warning(request, 'Учителя не могут проходить тесты')
                return redirect('test_list')
                
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
        user_info = getattr(request, 'user_info', None)
        is_authenticated = getattr(request, 'is_authenticated', False)
        
        test = get_object_or_404(Test, id=test_id, is_published=True)
        
        # Для авторизованных пользователей - обычная логика с БД
        if is_authenticated:
            # Проверяем только незавершенные попытки
            existing_attempt = TestAttempt.objects.filter(
                test=test,
                user_id=user_info['user_id'],
                status='in_progress'
            ).first()
            
            if existing_attempt:
                return redirect('test_take', test_id=test_id, attempt_id=existing_attempt.id)
            
            # Вычисляем максимальное количество баллов за тест
            max_score = TestQuestion.objects.filter(test=test).aggregate(
                total=Sum('points'))['total'] or 0
            
            # Создаем новую попытку теста
            attempt = TestAttempt.objects.create(
                test=test,
                user_id=user_info['user_id'],
                status='in_progress',
                started_at=timezone.now(),
                max_score=max_score
            )
            return redirect('test_take', test_id=test_id, attempt_id=attempt.id)
            
        # Для неавторизованных пользователей - используем сессию
        else:
            # Создаем временную попытку в сессии
            session_attempt = {
                'test_id': test_id,
                'started_at': timezone.now().isoformat(),
                'status': 'in_progress',
                'answers': {},
                'max_score': TestQuestion.objects.filter(
                    test=test,
                    question_type='part_a'
                ).aggregate(total=Sum('points'))['total'] or 0
            }
            
            # Сохраняем в сессии
            request.session['temp_attempt'] = session_attempt
            
            return redirect('test_take', test_id=test_id, attempt_id=0)  # используем attempt_id=0 для временной попытки 