// JavaScript для работы с API статей
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
    
    // Функция для загрузки статей через API
    async function loadArticles(page = 1, category = null, search = null) {
        try {
            let url = `/api/articles/?page=${page}`;
            if (category && category !== 'all') {
                url += `&category=${category}`;
            }
            if (search) {
                url += `&search=${encodeURIComponent(search)}`;
            }
            
            const response = await fetch(url, {
                method: 'GET',
                ...fetchOptions
            });
            
            if (!response.ok) {
                throw new Error('Ошибка при загрузке статей');
            }
            
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Ошибка:', error);
            return null;
        }
    }
    
    // Функция для загрузки статей по категории
    async function loadArticlesByCategory(category, page = 1) {
        try {
            const response = await fetch(`/api/articles/by_category/?category=${category}&page=${page}`, {
                method: 'GET',
                ...fetchOptions
            });
            
            if (!response.ok) {
                throw new Error('Ошибка при загрузке статей по категории');
            }
            
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Ошибка:', error);
            return null;
        }
    }
    
    // Функция для получения деталей статьи
    async function getArticleDetails(id) {
        try {
            const response = await fetch(`/api/articles/${id}/`, {
                method: 'GET',
                ...fetchOptions
            });
            
            if (!response.ok) {
                throw new Error('Ошибка при загрузке деталей статьи');
            }
            
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Ошибка:', error);
            return null;
        }
    }
    
    // Экспортируем функции для использования в других скриптах
    window.articleAPI = {
        loadArticles,
        loadArticlesByCategory,
        getArticleDetails
    };
    
    // Инициализация фильтров и сортировки на странице статей
    if (document.querySelector('.articles-container')) {
        const filterButtons = document.querySelectorAll('.filter-btn');
        const sortSelect = document.querySelector('.sort-select');
        const articlesGrid = document.querySelector('.articles-grid');
        
        // Обработчик для фильтрации по категориям
        filterButtons.forEach(button => {
            button.addEventListener('click', async function() {
                const category = this.getAttribute('data-category');
                
                // Визуальное выделение активной кнопки
                filterButtons.forEach(btn => btn.classList.remove('active'));
                this.classList.add('active');
                
                // Загрузка статей по категории через API
                if (category !== 'all') {
                    const articlesData = await loadArticlesByCategory(category);
                    if (articlesData && articlesData.results) {
                        updateArticlesGrid(articlesData.results);
                    }
                } else {
                    const articlesData = await loadArticles();
                    if (articlesData && articlesData.results) {
                        updateArticlesGrid(articlesData.results);
                    }
                }
            });
        });
        
        // Функция для обновления сетки статей
        function updateArticlesGrid(articles) {
            // Очищаем текущие статьи
            articlesGrid.innerHTML = '';
            
            if (articles.length === 0) {
                articlesGrid.innerHTML = `
                    <div class="no-articles">
                        <div class="no-articles-icon">
                            <i class="far fa-file-alt"></i>
                        </div>
                        <h3>Статьи не найдены</h3>
                        <p>По вашему запросу не найдено статей. Попробуйте изменить параметры поиска.</p>
                    </div>
                `;
                return;
            }
            
            // Добавляем новые статьи
            articles.forEach(article => {
                const articleDate = new Date(article.created_at).toLocaleDateString('ru-RU');
                const articleImage = article.image ? `<div class="article-image">
                    <img src="${article.image}" alt="${article.title}">
                    <div class="article-category">${article.category_display}</div>
                </div>` : '';
                
                const articleAuthor = article.author ? `<span class="article-author"><i class="far fa-user"></i> ${article.author.username}</span>` : '';
                
                const articleCard = document.createElement('article');
                articleCard.className = 'article-card hover-lift';
                articleCard.setAttribute('data-category', article.category);
                articleCard.innerHTML = `
                    ${articleImage}
                    <div class="article-content">
                        <div class="article-meta">
                            <span class="article-date"><i class="far fa-calendar-alt"></i> ${articleDate}</span>
                            ${articleAuthor}
                        </div>
                        <h3 class="article-title">${article.title}</h3>
                        <p class="article-excerpt">${article.content.substring(0, 150)}...</p>
                        <a href="/app/articles/${article.id}/" class="article-read-more">Читать далее <i class="fas fa-arrow-right"></i></a>
                    </div>
                `;
                
                articlesGrid.appendChild(articleCard);
            });
        }
    }
}); 