document.addEventListener('DOMContentLoaded', function() {
    // Функция для проверки, виден ли элемент в области просмотра
    function isElementInViewport(el) {
        const rect = el.getBoundingClientRect();
        return (
            rect.top <= (window.innerHeight || document.documentElement.clientHeight) * 0.8 &&
            rect.bottom >= 0
        );
    }
    
    // Функция для анимации элементов при прокрутке
    function animateOnScroll() {
        // Анимация для элементов с классом fade-in
        document.querySelectorAll('.fade-in').forEach(element => {
            if (isElementInViewport(element) && !element.classList.contains('visible')) {
                element.classList.add('visible');
            }
        });
        
        // Анимация для элементов с классом slide-in-left
        document.querySelectorAll('.slide-in-left').forEach(element => {
            if (isElementInViewport(element) && !element.classList.contains('visible')) {
                // Добавляем задержку, если указана
                const delay = element.getAttribute('data-delay') || 0;
                setTimeout(() => {
                    element.classList.add('visible');
                }, delay);
            }
        });
        
        // Анимация для элементов с классом slide-in-right
        document.querySelectorAll('.slide-in-right').forEach(element => {
            if (isElementInViewport(element) && !element.classList.contains('visible')) {
                const delay = element.getAttribute('data-delay') || 0;
                setTimeout(() => {
                    element.classList.add('visible');
                }, delay);
            }
        });
    }
    
    // Запускаем анимацию при загрузке страницы
    animateOnScroll();
    
    // Запускаем анимацию при прокрутке
    window.addEventListener('scroll', animateOnScroll);
    
    // Плавная прокрутка для якорных ссылок
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                window.scrollTo({
                    top: targetElement.offsetTop - 80, // Учитываем высоту шапки
                    behavior: 'smooth'
                });
            }
        });
    });
    
    // Анимация для кнопок
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
        });
        
        button.addEventListener('mouseleave', function() {
            this.style.transform = '';
        });
    });
    
    // Создаем заглушку для изображения, если оно не загрузилось
    function createPlaceholderSVG() {
        return `
        <svg width="400" height="300" viewBox="0 0 400 300" xmlns="http://www.w3.org/2000/svg">
            <rect width="400" height="300" fill="#f0f0f0"/>
            <text x="50%" y="50%" font-family="Arial" font-size="24" fill="#999" text-anchor="middle">Химия</text>
            <circle cx="200" cy="150" r="70" fill="none" stroke="#3498db" stroke-width="2"/>
            <circle cx="170" cy="130" r="20" fill="#3498db"/>
            <circle cx="230" cy="130" r="20" fill="#3498db"/>
            <circle cx="200" cy="180" r="20" fill="#3498db"/>
        </svg>
        `;
    }
    
    // Создаем файл SVG-заглушки, если его нет
    const placeholderPath = '/static/images/chemistry-placeholder.svg';
    fetch(placeholderPath)
        .catch(() => {
            // Если файл не существует, создаем его
            const svgBlob = new Blob([createPlaceholderSVG()], {type: 'image/svg+xml'});
            const url = URL.createObjectURL(svgBlob);
            
            // Заменяем все изображения с ошибками на заглушку
            document.querySelectorAll('img[onerror]').forEach(img => {
                img.onerror = function() {
                    this.src = url;
                    this.onerror = null;
                };
            });
        });
}); 