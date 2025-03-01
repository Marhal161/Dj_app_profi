// JavaScript для работы с API новостей
document.addEventListener('DOMContentLoaded', function() {
    // Функция для получения токена из cookie
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
    
    // Базовые настройки для fetch запросов
    const fetchOptions = {
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        }
    };
    
    // Если есть токен доступа, добавляем его в заголовки
    const accessToken = getCookie('access_token');
    if (accessToken) {
        fetchOptions.headers['Authorization'] = `Bearer ${accessToken}`;
    }
    
    // Функция для загрузки новостей через API
    async function loadNews(page = 1, category = null) {
        try {
            let url = `/api/news/?page=${page}`;
            if (category && category !== 'all') {
                url += `&category=${category}`;
            }
            
            const response = await fetch(url, {
                method: 'GET',
                ...fetchOptions
            });
            
            if (!response.ok) {
                throw new Error('Ошибка при загрузке новостей');
            }
            
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Ошибка:', error);
            return null;
        }
    }
    
    // Функция для создания новой новости
    async function createNews(newsData) {
        try {
            const response = await fetch('/api/news/', {
                method: 'POST',
                ...fetchOptions,
                body: JSON.stringify(newsData)
            });
            
            if (!response.ok) {
                throw new Error('Ошибка при создании новости');
            }
            
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Ошибка:', error);
            return null;
        }
    }
    
    // Функция для обновления новости
    async function updateNews(id, newsData) {
        try {
            const response = await fetch(`/api/news/${id}/`, {
                method: 'PUT',
                ...fetchOptions,
                body: JSON.stringify(newsData)
            });
            
            if (!response.ok) {
                throw new Error('Ошибка при обновлении новости');
            }
            
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Ошибка:', error);
            return null;
        }
    }
    
    // Функция для удаления новости
    async function deleteNews(id) {
        try {
            const response = await fetch(`/api/news/${id}/`, {
                method: 'DELETE',
                ...fetchOptions
            });
            
            if (!response.ok) {
                throw new Error('Ошибка при удалении новости');
            }
            
            return true;
        } catch (error) {
            console.error('Ошибка:', error);
            return false;
        }
    }
    
    // Экспортируем функции для использования в других скриптах
    window.newsAPI = {
        loadNews,
        createNews,
        updateNews,
        deleteNews
    };
}); 