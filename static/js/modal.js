document.addEventListener('DOMContentLoaded', function() {
    const modalOverlay = document.getElementById('modalOverlay');
    const openBtn = document.getElementById('openModalBtn');
    const closeBtn = document.querySelector('.modal-close');
    const cancelBtn = document.querySelector('.modal-cancel');

    function openModal() {
        modalOverlay.style.display = 'flex';
        document.body.style.overflow = 'hidden';
        // Даем время для начала анимации
        requestAnimationFrame(() => {
            modalOverlay.classList.add('active');
        });
    }

    function closeModal() {
        modalOverlay.classList.remove('active');
        // Ждем окончания анимации перед скрытием
        setTimeout(() => {
            modalOverlay.style.display = 'none';
            document.body.style.overflow = '';
        }, 300);
    }

    // Открытие модального окна
    openBtn.addEventListener('click', openModal);

    // Закрытие модального окна
    closeBtn.addEventListener('click', closeModal);
    cancelBtn.addEventListener('click', closeModal);

    // Закрытие при клике вне окна
    modalOverlay.addEventListener('click', function(event) {
        if (event.target === modalOverlay) {
            closeModal();
        }
    });

    // Закрытие по Escape
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape' && modalOverlay.classList.contains('active')) {
            closeModal();
        }
    });
}); 