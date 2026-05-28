// Dashboard Charts
(function() {
    "use strict";

    // Initialize dashboard charts when DOM is ready
    $(document).ready(function() {
        initTaskStatusChart();
    });

    function initTaskStatusChart() {
        // Check if chart container exists
        const chartContainer = document.querySelector("#taskStatusChart");
        if (!chartContainer) return;

        // Get chart data from global variables (passed from template)
        const pending = typeof window.chartData !== 'undefined' ? window.chartData.pending : 0;
        const inProgress = typeof window.chartData !== 'undefined' ? window.chartData.inProgress : 0;
        const completed = typeof window.chartData !== 'undefined' ? window.chartData.completed : 0;
        const cancelled = typeof window.chartData !== 'undefined' ? window.chartData.cancelled : 0;

        var options = {
            series: [pending, inProgress, completed, cancelled],
            chart: {
                type: 'pie',
                height: 300
            },
            labels: ['Pending', 'In Progress', 'Completed', 'Cancelled'],
            colors: ['#fdba74', '#60a5fa', '#34d399', '#9ca3af'],
            legend: {
                position: 'bottom'
            },
            responsive: [{
                breakpoint: 480,
                options: {
                    chart: {
                        width: 200
                    },
                    legend: {
                        position: 'bottom'
                    }
                }
            }]
        };

        var chart = new ApexCharts(chartContainer, options);
        chart.render();
    }

})();