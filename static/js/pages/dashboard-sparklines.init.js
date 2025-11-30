/**
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

