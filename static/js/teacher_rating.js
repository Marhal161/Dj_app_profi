document.addEventListener('DOMContentLoaded', function() {
    const ratingButtons = document.querySelectorAll('.btn-rating');
    
    ratingButtons.forEach(button => {
        button.addEventListener('click', function() {
            const teacherId = this.dataset.teacherId;
            const action = this.dataset.action;
            
            fetch(`/app/api/teacher/${teacherId}/rate/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({ action: action })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Обновляем счетчик рейтинга
                    const ratingCount = document.querySelector('.rating-count');
                    ratingCount.textContent = data.rating;
                    
                    // Обновляем состояние кнопок
                    const likeButton = document.getElementById('likeTeacher');
                    const dislikeButton = document.getElementById('dislikeTeacher');
                    
                    likeButton.classList.toggle('active', data.liked);
                    dislikeButton.classList.toggle('active', data.disliked);
                    
                    // Показываем сообщение
                    let message = '';
                    if (data.liked) {
                        message = 'Вы поставили лайк учителю!';
                    } else if (data.disliked) {
                        message = 'Вы поставили дизлайк учителю';
                    } else {
                        message = 'Вы убрали свою оценку';
                    }
                    showMessage('success', message);
                } else {
                    showMessage('error', data.error || 'Произошла ошибка');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showMessage('error', 'Произошла ошибка при выполнении запроса');
            });
        });
    });
}); 