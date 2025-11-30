/**
 * Dashboard Artículos Más Usados Chart
 * 
 * Inicializa el gráfico de barras para artículos más utilizados.
 * Separación de responsabilidades: solo lógica de visualización.
 */
(function() {
    'use strict';

    document.addEventListener("DOMContentLoaded", function() {
        // Verificar que ApexCharts esté disponible
        if (typeof ApexCharts === 'undefined') {
            console.warn('ApexCharts no está disponible');
            return;
        }

        const chartElement = document.getElementById('articulos_mas_usados');
        if (!chartElement) return;

        // Obtener datos desde data attributes
        const nombresAttr = chartElement.getAttribute('data-nombres');
        const cantidadesAttr = chartElement.getAttribute('data-cantidades');
        const colorsAttr = chartElement.getAttribute('data-colors');

        if (!nombresAttr || !cantidadesAttr) {
            console.warn('Faltan datos para el gráfico de artículos más usados');
            return;
        }

        let nombres = [];
        let cantidades = [];
        let colors = ['#405189', '#299cdb'];

        try {
            nombres = JSON.parse(nombresAttr);
            cantidades = JSON.parse(cantidadesAttr);
            
            if (colorsAttr) {
                const computedStyle = getComputedStyle(document.documentElement);
                const color1 = computedStyle.getPropertyValue('--tb-primary').trim() || '#405189';
                const color2 = computedStyle.getPropertyValue('--tb-info').trim() || '#299cdb';
                colors = [color1, color2];
            }
        } catch (e) {
            console.error('Error al parsear datos del gráfico:', e);
            return;
        }

        // Si no hay datos, no mostrar el gráfico
        if (nombres.length === 0 || cantidades.length === 0) {
            chartElement.innerHTML = '<div class="text-center text-muted py-4"><p>No hay datos disponibles</p></div>';
            return;
        }

        const options = {
            series: [{
                name: 'Cantidad de Movimientos',
                data: cantidades
            }],
            chart: {
                type: 'bar',
                height: 350,
                toolbar: {
                    show: false
                }
            },
            plotOptions: {
                bar: {
                    horizontal: false,
                    columnWidth: '55%',
                    endingShape: 'rounded',
                    borderRadius: 8
                }
            },
            dataLabels: {
                enabled: true,
                formatter: function(val) {
                    return Math.round(val);
                }
            },
            stroke: {
                show: true,
                width: 2,
                colors: ['transparent']
            },
            xaxis: {
                categories: nombres,
                labels: {
                    rotate: -45,
                    rotateAlways: true,
                    style: {
                        fontSize: '12px'
                    }
                }
            },
            yaxis: {
                title: {
                    text: 'Cantidad de Movimientos'
                }
            },
            fill: {
                opacity: 1,
                type: 'gradient',
                gradient: {
                    shade: 'light',
                    type: 'vertical',
                    shadeIntensity: 0.3,
                    gradientToColors: colors,
                    inverseColors: false,
                    opacityFrom: 0.8,
                    opacityTo: 0.5,
                    stops: [0, 100]
                }
            },
            colors: colors,
            tooltip: {
                y: {
                    formatter: function(val) {
                        return val + " movimientos";
                    }
                }
            },
            grid: {
                borderColor: '#e9ecef',
                strokeDashArray: 4
            }
        };

        const chart = new ApexCharts(chartElement, options);
        chart.render();
    });
})();

