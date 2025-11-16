// Chart.js Dark Theme Configuration for Intruviz Honeypot
// Add this to your dashboard JavaScript file (dashboard.js or live_dashboard.js)

// ============================================
// Global Chart.js Dark Theme Settings
// ============================================

// Set default colors for all charts
Chart.defaults.color = '#e4e6eb'; // Text color (off-white)
Chart.defaults.borderColor = 'rgba(0, 234, 255, 0.2)'; // Grid lines (neon cyan)

// ============================================
// Cybersecurity Color Palette
// ============================================

const cyberColors = {
    primary: '#00eaff',      // Neon cyan
    success: '#00ff88',      // Neon green
    warning: '#ffab00',      // Amber
    danger: '#ef5350',       // Red
    info: '#64b5f6',         // Light blue
    purple: '#ab47bc',       // Purple
    pink: '#ec407a',         // Pink
};

const chartColorPalette = [
    cyberColors.primary,
    cyberColors.success,
    cyberColors.danger,
    cyberColors.warning,
    cyberColors.info,
    cyberColors.purple,
    cyberColors.pink,
];

// ============================================
// Common Chart Options
// ============================================

const darkThemeOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            labels: {
                color: '#e4e6eb',
                font: {
                    family: "'Inter', 'Segoe UI', sans-serif",
                    size: 12,
                    weight: '500'
                },
                padding: 15,
                usePointStyle: true,
            }
        },
        tooltip: {
            backgroundColor: 'rgba(17, 28, 68, 0.95)',
            titleColor: '#00eaff',
            bodyColor: '#e4e6eb',
            borderColor: 'rgba(0, 234, 255, 0.3)',
            borderWidth: 1,
            padding: 12,
            displayColors: true,
            callbacks: {
                title: function (context) {
                    return context[0].label || '';
                },
                label: function (context) {
                    let label = context.dataset.label || '';
                    if (label) {
                        label += ': ';
                    }
                    label += context.parsed.y || context.parsed;
                    return label;
                }
            }
        }
    },
    scales: {
        x: {
            ticks: {
                color: '#e4e6eb',
                font: {
                    size: 11
                }
            },
            grid: {
                color: 'rgba(0, 234, 255, 0.1)',
                drawBorder: false
            }
        },
        y: {
            ticks: {
                color: '#e4e6eb',
                font: {
                    size: 11
                }
            },
            grid: {
                color: 'rgba(0, 234, 255, 0.1)',
                drawBorder: false
            }
        }
    }
};

// ============================================
// Example Chart Configurations
// ============================================

// 1. TIMELINE CHART (Line Chart)
// ============================================
function createTimelineChart(ctx, labels, data) {
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Attack Events',
                data: data,
                borderColor: cyberColors.primary,
                backgroundColor: 'rgba(0, 234, 255, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4, // Smooth curves
                pointBackgroundColor: cyberColors.primary,
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: cyberColors.primary,
                pointRadius: 4,
                pointHoverRadius: 6
            }]
        },
        options: {
            ...darkThemeOptions,
            plugins: {
                ...darkThemeOptions.plugins,
                title: {
                    display: false
                }
            }
        }
    });
}

// 2. COUNTRIES CHART (Horizontal Bar Chart)
// ============================================
function createCountriesChart(ctx, labels, data) {
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Attacks by Country',
                data: data,
                backgroundColor: chartColorPalette.map(color => color + '99'), // 60% opacity
                borderColor: chartColorPalette,
                borderWidth: 1,
                borderRadius: 6,
                barThickness: 'flex',
                maxBarThickness: 30
            }]
        },
        options: {
            ...darkThemeOptions,
            indexAxis: 'y', // Horizontal bars
            plugins: {
                ...darkThemeOptions.plugins,
                legend: {
                    display: false
                }
            }
        }
    });
}

// 3. TOP IPs CHART (Horizontal Bar Chart)
// ============================================
function createIPsChart(ctx, labels, data) {
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Attacks by IP',
                data: data,
                backgroundColor: cyberColors.danger + '99',
                borderColor: cyberColors.danger,
                borderWidth: 1,
                borderRadius: 6
            }]
        },
        options: {
            ...darkThemeOptions,
            indexAxis: 'y',
            plugins: {
                ...darkThemeOptions.plugins,
                legend: {
                    display: false
                }
            },
            scales: {
                ...darkThemeOptions.scales,
                x: {
                    ...darkThemeOptions.scales.x,
                    ticks: {
                        ...darkThemeOptions.scales.x.ticks,
                        callback: function (value) {
                            return value; // Display integer values
                        }
                    }
                }
            }
        }
    });
}

// 4. ATTACK TYPES CHART (Doughnut Chart)
// ============================================
function createAttackTypesChart(ctx, labels, data) {
    return new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: chartColorPalette.map(color => color + 'CC'), // 80% opacity
                borderColor: chartColorPalette,
                borderWidth: 2,
                hoverOffset: 8
            }]
        },
        options: {
            ...darkThemeOptions,
            cutout: '60%', // Doughnut hole size
            plugins: {
                ...darkThemeOptions.plugins,
                legend: {
                    ...darkThemeOptions.plugins.legend,
                    position: 'right',
                    labels: {
                        ...darkThemeOptions.plugins.legend.labels,
                        boxWidth: 15,
                        padding: 10
                    }
                }
            }
        }
    });
}

// ============================================
// Usage Example
// ============================================

/*
// In your dashboard initialization code:

// Timeline Chart
const timelineCtx = document.getElementById('timeline-chart').getContext('2d');
const timelineChart = createTimelineChart(
    timelineCtx,
    ['12:00', '13:00', '14:00', '15:00', '16:00'],
    [5, 12, 8, 15, 10]
);

// Countries Chart
const countriesCtx = document.getElementById('countries-chart').getContext('2d');
const countriesChart = createCountriesChart(
    countriesCtx,
    ['USA', 'China', 'Russia', 'Brazil', 'Germany'],
    [45, 38, 25, 18, 12]
);

// IPs Chart
const ipsCtx = document.getElementById('ips-chart').getContext('2d');
const ipsChart = createIPsChart(
    ipsCtx,
    ['203.0.113.45', '198.51.100.22', '192.0.2.100'],
    [15, 12, 8]
);

// Attack Types Chart
const typesCtx = document.getElementById('types-chart').getContext('2d');
const attackTypesChart = createAttackTypesChart(
    typesCtx,
    ['Login Attempt', 'SQL Injection', 'XSS', 'Directory Traversal'],
    [40, 30, 20, 10]
);
*/

// ============================================
// Chart Update Functions
// ============================================

// Update chart data dynamically
function updateChart(chart, newLabels, newData) {
    chart.data.labels = newLabels;
    chart.data.datasets[0].data = newData;
    chart.update('none'); // Update without animation for real-time updates
}

// Animate chart update
function animateChartUpdate(chart, newLabels, newData) {
    chart.data.labels = newLabels;
    chart.data.datasets[0].data = newData;
    chart.update('active'); // Update with animation
}

// ============================================
// Export Configuration
// ============================================

// Make functions available globally if needed
window.ChartDarkTheme = {
    cyberColors,
    chartColorPalette,
    darkThemeOptions,
    createTimelineChart,
    createCountriesChart,
    createIPsChart,
    createAttackTypesChart,
    updateChart,
    animateChartUpdate
};
