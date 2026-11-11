/**
 * Online Complaint Management System (OCMS) - IIIT Vadodara
 * Interactive scripts and Chart.js integrations
 */

document.addEventListener('DOMContentLoaded', function () {
    // 1. Mobile Sidebar Toggle
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');

    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function () {
            sidebar.classList.toggle('show');
        });

        // Close sidebar when clicking outside on mobile
        document.addEventListener('click', function (e) {
            if (window.innerWidth <= 992 && sidebar.classList.contains('show')) {
                if (!sidebar.contains(e.target) && !sidebarToggle.contains(e.target)) {
                    sidebar.classList.remove('show');
                }
            }
        });
    }

    // 2. Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) {
                bsAlert.close();
            }
        }, 5000);
    });

    // 3. Demo Login Credentials Autofill
    const demoButtons = document.querySelectorAll('.demo-login-fill');
    demoButtons.forEach(function (btn) {
        btn.addEventListener('click', function () {
            const email = this.getAttribute('data-email');
            const password = this.getAttribute('data-password');
            const emailInput = document.getElementById('email');
            const passwordInput = document.getElementById('password');

            if (emailInput && passwordInput) {
                emailInput.value = email;
                passwordInput.value = password;
                emailInput.classList.add('is-valid');
                passwordInput.classList.add('is-valid');
            }
        });
    });

    // 4. Star Rating selector for User Feedback
    const starContainers = document.querySelectorAll('.star-rating-select');
    starContainers.forEach(function (container) {
        const stars = container.querySelectorAll('.star-icon');
        const hiddenInput = container.querySelector('input[type="hidden"]');

        stars.forEach(function (star, index) {
            star.addEventListener('click', function () {
                const rating = index + 1;
                if (hiddenInput) hiddenInput.value = rating;

                stars.forEach(function (s, i) {
                    if (i < rating) {
                        s.classList.remove('bi-star');
                        s.classList.add('bi-star-fill', 'text-warning');
                    } else {
                        s.classList.remove('bi-star-fill', 'text-warning');
                        s.classList.add('bi-star');
                    }
                });
            });
        });
    });

    // 5. Initialize Admin Charts if canvas elements exist
    initAdminCharts();
});

function initAdminCharts() {
    const statusCanvas = document.getElementById('statusChart');
    const categoryCanvas = document.getElementById('categoryChart');
    const trendCanvas = document.getElementById('trendChart');
    const priorityCanvas = document.getElementById('priorityChart');

    if (!statusCanvas && !categoryCanvas && !trendCanvas && !priorityCanvas) {
        return;
    }

    fetch('/api/admin/chart-data')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // A. Status Doughnut Chart
            if (statusCanvas) {
                new Chart(statusCanvas, {
                    type: 'doughnut',
                    data: {
                        labels: data.status.labels,
                        datasets: [{
                            data: data.status.counts,
                            backgroundColor: [
                                '#f59e0b', // Pending (amber)
                                '#06b6d4', // Assigned (cyan)
                                '#2563eb', // In Progress (blue)
                                '#10b981', // Resolved (green)
                                '#ef4444'  // Rejected (red)
                            ],
                            borderWidth: 2,
                            borderColor: '#ffffff'
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'bottom',
                                labels: { boxWidth: 12, font: { family: "'Plus Jakarta Sans', sans-serif", size: 12 } }
                            }
                        },
                        cutout: '68%'
                    }
                });
            }

            // B. Category Horizontal Bar Chart
            if (categoryCanvas) {
                new Chart(categoryCanvas, {
                    type: 'bar',
                    data: {
                        labels: data.category.labels,
                        datasets: [{
                            label: 'Complaints',
                            data: data.category.counts,
                            backgroundColor: '#3b82f6',
                            borderRadius: 6
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        indexAxis: 'y',
                        plugins: {
                            legend: { display: false }
                        },
                        scales: {
                            x: {
                                beginAtZero: true,
                                ticks: { stepSize: 1, font: { family: "'Plus Jakarta Sans', sans-serif" } },
                                grid: { color: '#f1f5f9' }
                            },
                            y: {
                                ticks: { font: { family: "'Plus Jakarta Sans', sans-serif", size: 11 } },
                                grid: { display: false }
                            }
                        }
                    }
                });
            }

            // C. Weekly Trend Line Chart
            if (trendCanvas) {
                new Chart(trendCanvas, {
                    type: 'line',
                    data: {
                        labels: data.trend.labels,
                        datasets: [{
                            label: 'New Complaints',
                            data: data.trend.counts,
                            borderColor: '#2563eb',
                            backgroundColor: 'rgba(37, 99, 235, 0.08)',
                            fill: true,
                            tension: 0.35,
                            pointBackgroundColor: '#1d4ed8',
                            pointBorderColor: '#ffffff',
                            pointBorderWidth: 2,
                            pointRadius: 5
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: false }
                        },
                        scales: {
                            y: {
                                beginAtZero: true,
                                ticks: { stepSize: 1, font: { family: "'Plus Jakarta Sans', sans-serif" } },
                                grid: { color: '#f1f5f9' }
                            },
                            x: {
                                grid: { display: false },
                                ticks: { font: { family: "'Plus Jakarta Sans', sans-serif" } }
                            }
                        }
                    }
                });
            }

            // D. Priority Breakdown Polar / Bar Chart
            if (priorityCanvas) {
                new Chart(priorityCanvas, {
                    type: 'pie',
                    data: {
                        labels: data.priority.labels,
                        datasets: [{
                            data: data.priority.counts,
                            backgroundColor: [
                                '#94a3b8', // Low
                                '#38bdf8', // Medium
                                '#f97316', // High
                                '#dc2626'  // Urgent
                            ],
                            borderWidth: 2,
                            borderColor: '#ffffff'
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'bottom',
                                labels: { boxWidth: 12, font: { family: "'Plus Jakarta Sans', sans-serif", size: 12 } }
                            }
                        }
                    }
                });
            }
        })
        .catch(error => {
            console.error('Error loading analytics chart data:', error);
        });
}
