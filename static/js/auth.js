function login(event) {
    event.preventDefault();
    
    const identifier = document.getElementById('username').value || document.getElementById('email').value;
    const password = document.getElementById('password').value;
    
    const loginData = {
        password: password
    };

    // Определяем, что было введено: email или username
    if (identifier.includes('@')) {
        loginData.email = identifier;
    } else {
        loginData.username = identifier;
    }
    
    fetch('/app/api/login/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify(loginData),
        credentials: 'include'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        console.log('Login response:', data);
        if (data.success) {
            showSuccess('Успешный вход! Перенаправление...');
            setTimeout(() => {
                window.location.href = '/app/';
            }, 1000); // Задержка в 1 секунду для показа сообщения об успехе
        } else {
            showError(data.message);
        }
    })
    .catch(error => {
        console.error('Login error:', error);
        showError('Произошла ошибка при входе');
    });
}

function showSuccess(message) {
    const messageDiv = document.getElementById('message');
    if (messageDiv) {
        messageDiv.textContent = message;
        messageDiv.className = 'alert alert-success';
        messageDiv.style.display = 'block';
    }
}

function showError(message) {
    const messageDiv = document.getElementById('message');
    if (messageDiv) {
        messageDiv.textContent = message;
        messageDiv.className = 'alert alert-error';
        messageDiv.style.display = 'block';
    } else {
        alert(message);
    }
}

// Вспомогательная функция для получения CSRF токена
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