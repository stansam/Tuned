document.addEventListener('DOMContentLoaded', function() {
    // Revenue Chart initialization
    let revenueChart;
    let orderStatusChart;
    let servicesChart;
    
    const revenueChartCtx = document.getElementById('revenueChart').getContext('2d');
    const orderStatusChartCtx = document.getElementById('orderStatusChart').getContext('2d');
    const servicesChartCtx = document.getElementById('servicesChart').getContext('2d');
    
    // Function to initialize revenue chart
    function initRevenueChart(period = 'weekly') {
        const url = `${API_BASE_URL}/admin/revenue-chart-data?period=${period}`;
        
        fetch(url, {credentials: 'include'})
            .then(response => response.json())
            .then(data => {
                // Destroy existing chart if it exists
                if (revenueChart) {
                    revenueChart.destroy();
                }
                
                // Update period labels
                if (period === 'weekly') {
                    document.getElementById('current-period-label').textContent = 'Current Week';
                    document.getElementById('previous-period-label').textContent = 'Previous Week';
                } else if (period === 'monthly') {
                    document.getElementById('current-period-label').textContent = 'Current Year';
                    document.getElementById('previous-period-label').textContent = 'Previous Year';
                } else {
                    document.getElementById('current-period-label').textContent = 'Revenue';
                    document.getElementById('previous-period-label').textContent = '';
                }
                
                // Calculate totals
                const currentTotal = data.current.reduce((a, b) => a + b, 0);
                document.getElementById('current-period-total').textContent = `$${currentTotal.toFixed(2)}`;
                
                if (data.previous.length > 0) {
                    const previousTotal = data.previous.reduce((a, b) => a + b, 0);
                    document.getElementById('previous-period-total').textContent = `$${previousTotal.toFixed(2)}`;
                } else {
                    document.getElementById('previous-period-total').textContent = '';
                }
                
                // Create new chart
                revenueChart = new Chart(revenueChartCtx, {
                    type: 'line',
                    data: {
                        labels: data.labels,
                        datasets: [
                            {
                                label: 'Current',
                                data: data.current,
                                borderColor: '#4CAF50',
                                backgroundColor: 'rgba(76, 175, 80, 0.1)',
                                tension: 0.4,
                                fill: true
                            },
                            ...(data.previous.length > 0 ? [{
                                label: 'Previous',
                                data: data.previous,
                                borderColor: '#2196F3',
                                backgroundColor: 'rgba(33, 150, 243, 0.1)',
                                tension: 0.4,
                                fill: true
                            }] : [])
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                display: false
                            },
                            tooltip: {
                                mode: 'index',
                                intersect: false,
                                callbacks: {
                                    label: function(context) {
                                        let label = context.dataset.label || '';
                                        if (label) {
                                            label += ': ';
                                        }
                                        if (context.parsed.y !== null) {
                                            label += new Intl.NumberFormat('en-US', {
                                                style: 'currency',
                                                currency: 'USD'
                                            }).format(context.parsed.y);
                                        }
                                        return label;
                                    }
                                }
                            }
                        },
                        scales: {
                            x: {
                                grid: {
                                    display: false
                                }
                            },
                            y: {
                                grid: {
                                    borderDash: [2, 2]
                                },
                                beginAtZero: true,
                                ticks: {
                                    callback: function(value) {
                                        return '$' + value;
                                    }
                                }
                            }
                        }
                    }
                });
            })
            .catch(error => console.error('Error loading revenue chart data:', error));
    }
    
    // Initialize status chart
    function initOrderStatusChart() {
        fetch(`${API_BASE_URL}/admin/orders-by-status`, {credentials: 'include'})
            .then(response => response.json())
            .then(data => {
                // Destroy existing chart if it exists
                if (orderStatusChart) {
                    orderStatusChart.destroy();
                }
                
                // Create new chart
                orderStatusChart = new Chart(orderStatusChartCtx, {
                    type: 'doughnut',
                    data: {
                        labels: data.labels,
                        datasets: [{
                            data: data.data,
                            backgroundColor: data.colors,
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                display: false
                            },
                            tooltip: {
                                callbacks: {
                                    label: function(context) {
                                        const label = context.label || '';
                                        const value = context.raw;
                                        const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                        const percentage = Math.round((value / total) * 100);
                                        return `${label}: ${value} (${percentage}%)`;
                                    }
                                }
                            }
                        },
                        cutout: '65%'
                    }
                });
            })
            .catch(error => console.error('Error loading order status chart data:', error));
    }
    
    // Initialize services chart
    function initServicesChart() {
        fetch(`${API_BASE_URL}/admin/orders-by-service`, {credentials: 'include'})
            .then(response => response.json())
            .then(data => {
                // Destroy existing chart if it exists
                if (servicesChart) {
                    servicesChart.destroy();
                }
                
                // Create new chart
                servicesChart = new Chart(servicesChartCtx, {
                    type: 'bar',
                    data: {
                        labels: data.labels,
                        datasets: [{
                            label: 'Orders',
                            data: data.data,
                            backgroundColor: [
                                'rgba(76, 175, 80, 0.7)',
                                'rgba(33, 150, 243, 0.7)',
                                'rgba(255, 152, 0, 0.7)',
                                'rgba(156, 39, 176, 0.7)',
                                'rgba(0, 188, 212, 0.7)'
                            ],
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                display: false
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: true,
                                ticks: {
                                    precision: 0
                                }
                            }
                        }
                    }
                });
            })
            .catch(error => console.error('Error loading services chart data:', error));
    }
    
    // Initialize all charts
    initRevenueChart('weekly');
    initOrderStatusChart();
    initServicesChart();
    
    // Period buttons event listeners
    document.getElementById('revenue-weekly').addEventListener('click', function() {
        this.classList.add('active');
        document.getElementById('revenue-monthly').classList.remove('active');
        document.getElementById('revenue-yearly').classList.remove('active');
        initRevenueChart('weekly');
    });
    
    document.getElementById('revenue-monthly').addEventListener('click', function() {
        this.classList.add('active');
        document.getElementById('revenue-weekly').classList.remove('active');
        document.getElementById('revenue-yearly').classList.remove('active');
        initRevenueChart('monthly');
    });
    
    document.getElementById('revenue-yearly').addEventListener('click', function() {
        this.classList.add('active');
        document.getElementById('revenue-weekly').classList.remove('active');
        document.getElementById('revenue-monthly').classList.remove('active');
        initRevenueChart('yearly');
    });
    
    // Task checkbox event listeners
    document.querySelectorAll('.form-check-input').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const listItem = this.closest('.list-group-item');
            if (this.checked) {
                listItem.style.opacity = '0.6';
                listItem.querySelector('h6').style.textDecoration = 'line-through';
            } else {
                listItem.style.opacity = '1';
                listItem.querySelector('h6').style.textDecoration = 'none';
            }
        });
    });
});