document.addEventListener('DOMContentLoaded', function() {
    initializeEventHandlers();
});

function initializeEventHandlers() {
    const toggleButtons = document.querySelectorAll('.toggle-student-details');
    toggleButtons.forEach(button => {
        button.addEventListener('click', function() {
            const studentId = this.getAttribute('data-student-id');
            const detailsRow = document.getElementById(`details-${studentId}`);
            
            // Переключаем класс для строки и значок
            this.classList.toggle('active');
            
            // Проверяем текущее состояние отображения
            const isVisible = detailsRow.classList.contains('visible');
            
            // Сначала скрываем все детали
            document.querySelectorAll('.student-details-row').forEach(row => {
                row.classList.remove('visible');
            });
            document.querySelectorAll('.toggle-student-details').forEach(btn => {
                btn.classList.remove('active');
                btn.innerHTML = '<i class="fas fa-chevron-down"></i>';
            });
            
            // Если строка была скрыта, показываем её
            if (!isVisible) {
                detailsRow.classList.add('visible');
                this.classList.add('active');
                this.innerHTML = '<i class="fas fa-chevron-up"></i>';
            }
        });
    });
    
    // Поиск по таблице учеников
    const searchInput = document.getElementById('studentSearch');
    if (searchInput) {
        searchInput.addEventListener('keyup', function() {
            const searchValue = this.value.toLowerCase();
            const rows = document.querySelectorAll('.student-row');
            
            rows.forEach(row => {
                const studentName = row.querySelector('.student-name').textContent.toLowerCase();
                const detailsId = row.getAttribute('data-student-id');
                const detailsRow = document.getElementById(`details-${detailsId}`);
                
                if (studentName.includes(searchValue)) {
                    row.style.display = '';
                    // Показываем детали только если они были открыты
                    if (detailsRow && row.querySelector('.toggle-student-details').classList.contains('active')) {
                        detailsRow.classList.add('visible');
                    }
                } else {
                    row.style.display = 'none';
                    if (detailsRow) {
                        detailsRow.classList.remove('visible');
                    }
                }
            });
        });
    }
} 

