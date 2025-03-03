document.addEventListener('DOMContentLoaded', function() {
    // Анимация появления элементов при прокрутке
    const animateOnScroll = () => {
        const elements = document.querySelectorAll('.student-card, .invitation-card');
        elements.forEach(element => {
            const elementTop = element.getBoundingClientRect().top;
            const elementBottom = element.getBoundingClientRect().bottom;
            
            if (elementTop < window.innerHeight && elementBottom > 0) {
                element.style.opacity = '1';
                element.style.transform = 'translateY(0)';
            }
        });
    };

    // Анимация для форм
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitButton = this.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.classList.add('loading');
                submitButton.disabled = true;
            }
        });
    });

    // Анимация для кнопок
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
        });
        
        button.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });

    // Анимация для карточек студентов
    const studentCards = document.querySelectorAll('.student-card');
    studentCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });

    // Автоматическое скрытие сообщений
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-20px)';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });

    // Анимация для поля ввода
    const inputs = document.querySelectorAll('.form-control');
    inputs.forEach(input => {
        input.addEventListener('focus', function() {
            this.parentElement.classList.add('focused');
        });
        
        input.addEventListener('blur', function() {
            if (!this.value) {
                this.parentElement.classList.remove('focused');
            }
        });
    });

    // Модальное окно
    const modal = document.getElementById('addStudentModal');
    const btn = document.getElementById('addStudentBtn');
    const span = document.getElementsByClassName('close')[0];
    const closeModalBtn = document.querySelector('.close-modal');
    
    function openModal() {
        modal.style.display = "block";
        document.body.style.overflow = 'hidden'; // Предотвращаем прокрутку фона
    }

    function closeModal() {
        modal.style.display = "none";
        document.body.style.overflow = ''; // Возвращаем прокрутку
    }

    if (btn && modal) {
        // Открытие модального окна
        btn.onclick = openModal;

        // Закрытие по клику на крестик
        if (span) {
            span.onclick = closeModal;
        }

        // Закрытие по клику на кнопку "Отмена"
        if (closeModalBtn) {
            closeModalBtn.onclick = closeModal;
        }

        // Закрытие по клику вне модального окна
        window.onclick = function(event) {
            if (event.target == modal) {
                closeModal();
            }
        }

        // Закрытие по нажатию Esc
        document.addEventListener('keydown', function(event) {
            if (event.key === 'Escape' && modal.style.display === 'block') {
                closeModal();
            }
        });
    }

    // Анимация для строк таблицы
    const tableRows = document.querySelectorAll('.table tr');
    tableRows.forEach(row => {
        row.addEventListener('mouseenter', function() {
            this.style.transition = 'background-color 0.3s ease';
        });
    });

    // Подтверждение удаления
    const removeForms = document.querySelectorAll('.remove-student-form');
    removeForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!confirm('Вы уверены, что хотите удалить этого ученика из класса?')) {
                e.preventDefault();
            }
        });
    });

    // Инициализация анимаций при загрузке
    animateOnScroll();
    window.addEventListener('scroll', animateOnScroll);
});

// Функция для плавного появления новых элементов
function animateElement(element) {
    element.style.opacity = '0';
    element.style.transform = 'translateY(20px)';
    
    setTimeout(() => {
        element.style.opacity = '1';
        element.style.transform = 'translateY(0)';
    }, 100);
} 