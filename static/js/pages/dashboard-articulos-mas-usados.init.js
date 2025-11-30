/**
 * Dashboard Articulos Mas Usados - Grafico de barras para articulos mas utilizados
 * 
 * Separacion de responsabilidades: JavaScript en archivo dedicado
 * No mezclar JS con HTML (SRP - Single Responsibility Principle)
 * 
 * Los datos se obtienen desde data-attributes del elemento HTML
 */

(function() {
    'use strict';

    /**
     * Inicializa el grafico de articulos mas usados cuando el DOM esta listo
     */
    document.addEventListener("DOMContentLoaded", function() {
        // Verificar que ApexCharts este disponible
        if (typeof ApexCharts === 'undefined') {
            console.warn('ApexCharts no esta disponible');
            return;
        }

        var chartElement = document.getElementById('articulos_mas_usados');
        if (!chartElement) {
            console.warn('Elemento articulos_mas_usados no encontrado');
            return;
        }

        // Obtener datos desde data-attributes (practica limpia)
        var nombresAttr = chartElement.getAttribute('data-nombres');
        var cantidadesAttr = chartElement.getAttribute('data-cantidades');
        var colorsAttr = chartElement.getAttribute('data-colors');

        if (!nombresAttr || !cantidadesAttr) {
            console.warn('Faltan datos para el grafico de articulos mas usados');
            chartElement.innerHTML = '<div class="text-center text-muted py-4"><p>No hay datos disponibles</p></div>';
            return;
        }

        var articulosNombres = [];
        var articulosCantidades = [];
        var colors = ['#405189', '#299cdb'];

        try {
            articulosNombres = JSON.parse(nombresAttr);
            articulosCantidades = JSON.parse(cantidadesAttr);
            
            // Obtener colores desde CSS variables si estan disponibles
            if (colorsAttr) {
                var computedStyle = getComputedStyle(document.documentElement);
                var color1 = computedStyle.getPropertyValue('--tb-primary').trim() || '#405189';
                var color2 = computedStyle.getPropertyValue('--tb-info').trim() || '#299cdb';
                colors = [color1, color2];
            }
        } catch (e) {
            console.error('Error al parsear datos del grafico:', e);
            chartElement.innerHTML = '<div class="text-center text-muted py-4"><p>Error al cargar datos</p></div>';
            return;
        }

        if (!articulosNombres.length || !articulosCantidades.length) {
            chartElement.innerHTML = '<div class="text-center text-muted py-4"><p>No hay datos disponibles</p></div>';
            return;
        }
        
        var options = {
            series: [{
                name: 'Movimientos',
                data: articulosCantidades
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
                categories: articulosNombres,
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
                    formatter: function (val) {
                        return val + " movimientos";
                    }
                }
            },
            grid: {
                borderColor: '#e9ecef',
                strokeDashArray: 4
            }
        };
        
        var chart = new ApexCharts(chartElement, options);
        chart.render();
    });
})();
