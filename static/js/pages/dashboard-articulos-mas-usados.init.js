/**
<<<<<<< HEAD
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
=======
 * Dashboard Artículos Más Usados - Gráfico de barras para artículos más utilizados
 * 
 * Separación de responsabilidades: JavaScript en archivo dedicado
 * No mezclar JS con HTML (SRP - Single Responsibility Principle)
 * 
 * Los datos se obtienen desde data-attributes del elemento HTML
 */

(function() {
    'use strict';

    /**
     * Inicializa el gráfico de artículos más usados cuando el DOM está listo
     */
    document.addEventListener("DOMContentLoaded", function() {
        var chartElement = document.getElementById('articulos_mas_usados');
        if (!chartElement) return;

        var colors = getChartColorsArray("articulos_mas_usados");
        if (!colors) return;

        // Obtener datos desde data-attributes (práctica limpia)
        var articulosNombres = JSON.parse(chartElement.getAttribute('data-nombres') || '[]');
        var articulosCantidades = JSON.parse(chartElement.getAttribute('data-cantidades') || '[]');

        if (!articulosNombres.length || !articulosCantidades.length) return;
        
        var options = {
            series: [{
                name: 'Movimientos',
                data: articulosCantidades
            }],
            chart: {
                type: 'bar',
                height: 300,
                toolbar: { show: false }
>>>>>>> b8346a8f8f921bf1c6d1feafdd4856ee9f79e413
            },
            plotOptions: {
                bar: {
                    horizontal: false,
                    columnWidth: '55%',
<<<<<<< HEAD
                    endingShape: 'rounded',
                    borderRadius: 8
                }
            },
            dataLabels: {
                enabled: true,
                formatter: function(val) {
                    return Math.round(val);
                }
=======
                    endingShape: 'rounded'
                }
            },
            dataLabels: {
                enabled: false
>>>>>>> b8346a8f8f921bf1c6d1feafdd4856ee9f79e413
            },
            stroke: {
                show: true,
                width: 2,
                colors: ['transparent']
            },
            xaxis: {
<<<<<<< HEAD
                categories: nombres,
                labels: {
                    rotate: -45,
                    rotateAlways: true,
                    style: {
                        fontSize: '12px'
                    }
=======
                categories: articulosNombres,
                labels: {
                    rotate: -45,
                    rotateAlways: true
>>>>>>> b8346a8f8f921bf1c6d1feafdd4856ee9f79e413
                }
            },
            yaxis: {
                title: {
                    text: 'Cantidad de Movimientos'
                }
            },
            fill: {
<<<<<<< HEAD
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
=======
                opacity: 1
>>>>>>> b8346a8f8f921bf1c6d1feafdd4856ee9f79e413
            },
            colors: colors,
            tooltip: {
                y: {
<<<<<<< HEAD
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

=======
                    formatter: function (val) {
                        return val + " movimientos";
                    }
                }
            }
        };
        
        var chart = new ApexCharts(chartElement, options);
        chart.render();
    });
})();
>>>>>>> b8346a8f8f921bf1c6d1feafdd4856ee9f79e413
