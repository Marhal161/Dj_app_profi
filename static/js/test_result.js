document.addEventListener('DOMContentLoaded', function() {
    // Скрываем сообщения через 3 секунды
    const messageDivs = document.querySelectorAll('.messages .alert');
    messageDivs.forEach(function(message) {
        setTimeout(function() {
            message.style.opacity = '0';
            setTimeout(function() {
                message.remove();
            }, 300);
        }, 3000);
    });
}); 