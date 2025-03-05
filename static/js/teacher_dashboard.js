document.addEventListener('DOMContentLoaded', function() {
    // Удаляем initializeCharts() так как диаграммы больше не нужны
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
            if (this.classList.contains('active')) {
                this.innerHTML = '<i class="fas fa-chevron-up"></i>';
                detailsRow.style.display = 'table-row'; // Показываем строку
            } else {
                this.innerHTML = '<i class="fas fa-chevron-down"></i>';
                detailsRow.style.display = 'none'; // Скрываем строку
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
                    if (detailsRow && detailsRow.classList.contains('show')) {
                        detailsRow.style.display = '';
                    }
                } else {
                    row.style.display = 'none';
                    if (detailsRow) {
                        detailsRow.style.display = 'none';
                    }
                }
            });
        });
    }
} 

