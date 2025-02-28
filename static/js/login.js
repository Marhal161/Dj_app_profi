document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('login-form');
    const messageBox = document.getElementById('message-box');
    
    setupPasswordToggle();
    addInputAnimations();
    
    loginForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Сбор данных формы
        const formData = {
            username: document.getElementById('username').value,
            password: document.getElementById('password').value
        };
        
        // Отправка запроса на авторизацию
        fetch('/app/api/login/', {
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
            console.log('Ответ сервера:', result); // Добавляем для отладки
            
            if (result.data.success) {
                // Успешная авторизация
                showMessage('Вход выполнен успешно! Перенаправление...', 'success');
                
                // Сохраняем информацию об аутентификации
                localStorage.setItem('isAuthenticated', 'true');
                localStorage.setItem('user', JSON.stringify(result.data.user));
                
                // Перенаправление на главную страницу
                setTimeout(() => {
                    window.location.href = '/';
                }, 2000);
            } else {
                // Ошибка авторизации
                let errorMessage = result.data.message || 'Неверное имя пользователя или пароль';
                
                showMessage(errorMessage, 'error');
                shakeButton();
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
    
    // Добавляем анимацию встряхивания для кнопки при ошибке
    function shakeButton() {
        const button = document.querySelector('.btn-primary');
        button.classList.add('shake');
        
        // Удаляем класс после завершения анимации
        setTimeout(() => {
            button.classList.remove('shake');
        }, 500);
    }
});

// Добавьте эти функции в начало файла login.js
function addInputAnimations() {
    const inputs = document.querySelectorAll('input');
    
    inputs.forEach(input => {
        // Добавляем класс активного поля при фокусе
        input.addEventListener('focus', function() {
            // Для поля пароля нужно добавить класс к родительскому элементу .form-group
            if (this.type === 'password' || this.type === 'text' && this.id === 'password') {
                this.closest('.form-group').classList.add('active-field');
            } else {
                this.parentElement.classList.add('active-field');
            }
        });
        
        // Удаляем класс активного поля при потере фокуса
        input.addEventListener('blur', function() {
            if (!this.value) {
                if (this.type === 'password' || this.type === 'text' && this.id === 'password') {
                    this.closest('.form-group').classList.remove('active-field');
                } else {
                    this.parentElement.classList.remove('active-field');
                }
            }
        });
        
        // Проверяем, есть ли значение при загрузке
        if (input.value) {
            if (input.type === 'password' || input.type === 'text' && input.id === 'password') {
                input.closest('.form-group').classList.add('active-field');
            } else {
                input.parentElement.classList.add('active-field');
            }
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