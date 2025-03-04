document.addEventListener('DOMContentLoaded', function() {
    // Инициализируем круговые диаграммы для каждого ученика
    initializeCharts();
    initializeAnswersCharts();  // Добавляем инициализацию диаграмм ответов
    
    // Инициализируем обработчики событий
    initializeEventHandlers();
});

function initializeCharts() {
    const students = window.teacherDashboardData.students || [];
    students.forEach(student => {
        const ctx = document.getElementById(`chart-${student.id}`);
        if (!ctx) return;
        
        // Определяем данные для диаграммы
        const completedTests = student.completed_tests || 0;
        const awaitingTests = student.awaiting_count || 0;
        const otherTests = Math.max(0, (student.total_tests || 0) - completedTests - awaitingTests);
        
        // Создаем диаграмму
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Завершено', 'На проверке', 'Не начато'],
                datasets: [{
                    data: [completedTests, awaitingTests, otherTests],
                    backgroundColor: ['#4caf50', '#ff9800', '#e0e0e0'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                },
                cutout: '70%'
            }
        });
    });
}

function initializeAnswersCharts() {
    const students = window.teacherDashboardData.students || [];
    students.forEach(student => {
        const ctx = document.getElementById(`answersChart${student.id}`);
        if (!ctx) return;
        
        // Создаем диаграмму правильных/неправильных ответов
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Правильные', 'Неправильные'],
                datasets: [{
                    data: [
                        student.correct_answers || 0,
                        (student.total_answers || 0) - (student.correct_answers || 0)
                    ],
                    backgroundColor: ['#28a745', '#dc3545']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        });
    });
}

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

