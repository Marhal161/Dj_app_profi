function addInputAnimations() {
    const inputs = document.querySelectorAll('input, select');
    
    inputs.forEach(input => {
        // Добавляем класс активного поля при фокусе
        input.addEventListener('focus', function() {
            this.parentElement.classList.add('active-field');
        });
        
        // Удаляем класс активного поля при потере фокуса
        input.addEventListener('blur', function() {
            if (!this.value) {
                this.parentElement.classList.remove('active-field');
            }
        });
        
        // Проверяем, есть ли значение при загрузке
        if (input.value) {
            input.parentElement.classList.add('active-field');
        }
    });
}

// Добавляем функцию для переключения видимости пароля
function setupPasswordToggle() {
    const passwordToggle = document.querySelector('.password-toggle');
    const passwordField = document.getElementById('password');
    
    if (passwordToggle && passwordField) {
        passwordToggle.addEventListener('click', function() {
            const icon = this.querySelector('i');
            
            // Переключаем тип поля между password и text
            if (passwordField.type === 'password') {
                passwordField.type = 'text';
                icon.classList.remove('fa-eye-slash');
                icon.classList.add('fa-eye');
            } else {
                passwordField.type = 'password';
                icon.classList.remove('fa-eye');
                icon.classList.add('fa-eye-slash');
            }
            
            // Фокусируемся на поле пароля
            passwordField.focus();
        });
    }
}

document.addEventListener('DOMContentLoaded', function() {
    // Существующий код...
    
    // Добавляем вызов новой функции
    setupPasswordToggle();
    addInputAnimations();
    
    const step1 = document.getElementById('step-1');
    const step2 = document.getElementById('step-2');
    const userTypeCards = document.querySelectorAll('.user-type-card');
    const userTypeInput = document.getElementById('user_type');
    const gradeGroup = document.getElementById('grade-group');
    const registerForm = document.getElementById('register-form');
    const messageBox = document.getElementById('message-box');
    const changeUserType = document.getElementById('change-user-type');
    
    // Обработка выбора типа пользователя
    userTypeCards.forEach(card => {
        card.addEventListener('click', function() {
            const userType = this.getAttribute('data-type');
            userTypeInput.value = userType;

            // Убираем выделение со всех карточек
            userTypeCards.forEach(c => c.classList.remove('selected'));
            // Добавляем выделение выбранной карточке
            this.classList.add('selected');

            // Показываем поле для класса только для учеников
            if (userType === 'student') {
                gradeGroup.style.display = 'block';
            } else {
                gradeGroup.style.display = 'none';
            }

            // Переходим к шагу 2
            step1.classList.remove('active-step');
            step2.classList.add('active-step');
        });
    });
    
    // Возврат к выбору типа пользователя
    if (changeUserType) {
        changeUserType.addEventListener('click', function(e) {
            e.preventDefault();
            step2.classList.remove('active-step');
            step1.classList.add('active-step');
        });
    }
    
    // Обработка отправки формы
    registerForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Проверяем, выбран ли тип пользователя
        if (!userTypeInput.value) {
            showMessage('Пожалуйста, выберите тип пользователя', 'error');
            step2.classList.remove('active-step');
            step1.classList.add('active-step');
            return;
        }
        
        // Сбор данных формы
        const formData = {
            username: document.getElementById('username').value,
            email: document.getElementById('email').value,
            first_name: document.getElementById('first_name').value,
            last_name: document.getElementById('last_name').value,
            password: document.getElementById('password').value,
            user_type: userTypeInput.value,
            grade: document.getElementById('grade').value || ''
        };
        
        // Отправка запроса на регистрацию
        fetch('/app/api/register/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(formData),
            credentials: 'same-origin'
        })
        .then(response => {
            return response.json().then(data => {
                return { status: response.status, data };
            });
        })
        .then(result => {
            if (result.data.success) {
                // Успешная регистрация
                showMessage('Регистрация успешна! Перенаправление...', 'success');
                
                // Перенаправление на страницу входа
                setTimeout(() => {
                    window.location.href = '/app/login';
                }, 2000);
            } else {
                // Ошибка регистрации
                let errorMessage = result.data.message || 'Произошла ошибка при регистрации';
                
                // Если есть детальные ошибки, добавляем их
                if (result.data.errors) {
                    if (typeof result.data.errors === 'object') {
                        const errors = [];
                        for (const field in result.data.errors) {
                            if (Array.isArray(result.data.errors[field])) {
                                errors.push(`${field}: ${result.data.errors[field].join(', ')}`);
                            } else {
                                errors.push(`${field}: ${result.data.errors[field]}`);
                            }
                        }
                        errorMessage += '<br>' + errors.join('<br>');
                    } else if (Array.isArray(result.data.errors)) {
                        errorMessage += '<br>' + result.data.errors.join('<br>');
                    } else {
                        errorMessage += '<br>' + result.data.errors;
                    }
                }
                
                showMessage(errorMessage, 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showMessage('Произошла ошибка при отправке запроса', 'error');
        });
    });
    
    // Функция для отображения сообщений
    function showMessage(message, type) {
        messageBox.innerHTML = message;
        messageBox.className = 'message-box message-' + type;
        messageBox.style.display = 'block';
        
        // Прокрутка к сообщению
        messageBox.scrollIntoView({ behavior: 'smooth' });
    }
    
    // Функция для получения CSRF-токена из cookies
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
}); 