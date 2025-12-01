/**
<<<<<<< HEAD
 * Dashboard Sparklines Initialization
 * 
 * Inicializa los gráficos sparkline para las cards del dashboard.
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

        // Función para crear sparkline chart
        function createSparklineChart(elementId, data, colorVar) {
            const element = document.getElementById(elementId);
            if (!element) return;

            // Obtener color desde CSS variable
            const computedStyle = getComputedStyle(document.documentElement);
            const color = computedStyle.getPropertyValue(colorVar).trim() || '#405189';

            // Generar datos si no se proporcionan (últimos 7 días)
            if (!data || data.length === 0) {
                data = Array.from({ length: 7 }, () => Math.floor(Math.random() * 100));
            }

            const options = {
                series: [{
                    name: 'Valor',
                    data: data
                }],
                chart: {
                    type: 'area',
                    height: 60,
                    sparkline: {
                        enabled: true
                    },
                    toolbar: {
                        show: false
                    }
                },
                stroke: {
                    curve: 'smooth',
                    width: 2
                },
                fill: {
                    type: 'gradient',
                    gradient: {
                        shadeIntensity: 1,
                        opacityFrom: 0.4,
                        opacityTo: 0.1,
                        stops: [0, 100]
                    }
                },
                colors: [color],
                tooltip: {
                    fixed: {
                        enabled: false
                    },
                    x: {
                        show: false
                    },
                    y: {
                        title: {
                            formatter: function() {
                                return '';
                            }
                        }
                    },
                    marker: {
                        show: false
                    }
                }
            };

            const chart = new ApexCharts(element, options);
            chart.render();
        }

        // Obtener datos desde data attributes o generar datos de ejemplo
        const solicitudesElement = document.getElementById('solicitudes_pendientes');
        const ordenesElement = document.getElementById('ordenes_en_proceso');
        const stockElement = document.getElementById('articulos_stock_critico');
        const entregasElement = document.getElementById('solicitudes_entregadas_mes');

        // Datos para sparklines (últimos 7 días simulados)
        const solicitudesData = solicitudesElement?.dataset?.data 
            ? JSON.parse(solicitudesElement.dataset.data) 
            : Array.from({ length: 7 }, () => Math.floor(Math.random() * 50) + 1);

        const ordenesData = ordenesElement?.dataset?.data 
            ? JSON.parse(ordenesElement.dataset.data) 
            : Array.from({ length: 7 }, () => Math.floor(Math.random() * 30));

        const stockData = stockElement?.dataset?.data 
            ? JSON.parse(stockElement.dataset.data) 
            : Array.from({ length: 7 }, () => Math.floor(Math.random() * 20));

        const entregasData = entregasElement?.dataset?.data 
            ? JSON.parse(entregasElement.dataset.data) 
            : Array.from({ length: 7 }, () => Math.floor(Math.random() * 40));

        // Crear los sparklines
        createSparklineChart('solicitudes_pendientes', solicitudesData, '--tb-warning');
        createSparklineChart('ordenes_en_proceso', ordenesData, '--tb-info');
        createSparklineChart('articulos_stock_critico', stockData, '--tb-danger');
        createSparklineChart('solicitudes_entregadas_mes', entregasData, '--tb-success');
    });
})();

=======
 * Dashboard Sparklines - Gráficos sparkline para las cards del dashboard
 * 
 * Separación de responsabilidades: JavaScript en archivo dedicado
 * No mezclar JS con HTML (SRP - Single Responsibility Principle)
 */

(function() {
    'use strict';

    /**
     * Función para crear gráficos sparkline
     * @param {string} elementId - ID del elemento donde se renderizará el gráfico
     * @param {Array} data - Datos para el gráfico
     * @param {string} colorVar - Variable CSS para el color
     */
    function createSparklineChart(elementId, data, colorVar) {
        var colors = getChartColorsArray(elementId);
        if (!colors || !document.getElementById(elementId)) return;
        
        var options = {
            series: [{data: data}],
            chart: {
                type: 'line',
                height: 70,
                sparkline: {enabled: true},
                toolbar: {show: false}
            },
            colors: colors,
            stroke: {
                curve: 'smooth',
                width: 2
            },
            tooltip: {
                fixed: {enabled: false},
                x: {show: false},
                y: {
                    title: {
                        formatter: function (val) {
                            return '';
                        }
                    }
                },
                marker: {show: false}
            }
        };
        
        var chart = new ApexCharts(document.querySelector("#" + elementId), options);
        chart.render();
    }

    /**
     * Inicializa los gráficos sparkline cuando el DOM está listo
     */
    document.addEventListener("DOMContentLoaded", function() {
        // Obtener datos desde data-attributes (práctica limpia)
        var solicitudesElement = document.getElementById('solicitudes_pendientes');
        var ordenesElement = document.getElementById('ordenes_en_proceso');
        var stockCriticoElement = document.getElementById('articulos_stock_critico');
        var entregasElement = document.getElementById('solicitudes_entregadas_mes');

        // Datos para los gráficos sparkline (simulados basados en tendencias)
        // Tendencia ascendente = más solicitudes pendientes (malo)
        var solicitudesData = [12, 15, 18, 20, 22, 18, 20, 22];
        
        // Tendencia ascendente = más OC en proceso (bueno - hay actividad)
        var ordenesData = [15, 18, 20, 22, 24, 22, 24, 25];
        
        // Tendencia descendente = menos artículos críticos (bueno)
        var stockCriticoData = [8, 7, 6, 5, 4, 3, 2, 0];
        
        // Tendencia ascendente = más entregas (bueno - más productividad)
        var entregasData = [5, 8, 10, 12, 15, 12, 14, 16];
        
        // Crear gráficos sparkline con los nuevos IDs
        if (solicitudesElement) {
            createSparklineChart('solicitudes_pendientes', solicitudesData, '--tb-warning');
        }
        if (ordenesElement) {
            createSparklineChart('ordenes_en_proceso', ordenesData, '--tb-info');
        }
        if (stockCriticoElement) {
            createSparklineChart('articulos_stock_critico', stockCriticoData, '--tb-danger');
        }
        if (entregasElement) {
            createSparklineChart('solicitudes_entregadas_mes', entregasData, '--tb-success');
        }
    });
})();
>>>>>>> b8346a8f8f921bf1c6d1feafdd4856ee9f79e413
