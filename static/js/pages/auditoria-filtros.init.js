/**
 * Auditoría de Actividades - Filtros y Búsqueda
 * 
 * Separación de responsabilidades: JavaScript en archivo dedicado
 * No mezclar JS con HTML (SRP - Single Responsibility Principle)
 */

(function() {
    'use strict';

    /**
     * Inicializa los filtros cuando el DOM está listo
     */
    document.addEventListener("DOMContentLoaded", function() {
        var filtrosForm = document.getElementById('filtros-form');
        var filtroTipo = document.getElementById('filtro-tipo');
        var filtroModulo = document.getElementById('filtro-modulo');
        var filtroUsuario = document.getElementById('filtro-usuario');
        var filtroBuscar = document.getElementById('filtro-buscar');
        var filtroFechaDesde = document.getElementById('filtro-fecha-desde');
        var filtroFechaHasta = document.getElementById('filtro-fecha-hasta');

        if (!filtrosForm) return;

        /**
         * Validar que fecha_desde no sea mayor que fecha_hasta
         */
        function validarFechas() {
            if (filtroFechaDesde && filtroFechaHasta && 
                filtroFechaDesde.value && filtroFechaHasta.value) {
                var fechaDesde = new Date(filtroFechaDesde.value);
                var fechaHasta = new Date(filtroFechaHasta.value);

                if (fechaDesde > fechaHasta) {
                    alert('La fecha "Desde" no puede ser mayor que la fecha "Hasta"');
                    filtroFechaHasta.value = filtroFechaDesde.value;
                    return false;
                }
            }
            return true;
        }

        /**
         * Auto-submit del formulario cuando cambian los select
         */
        if (filtroTipo) {
            filtroTipo.addEventListener('change', function() {
                if (validarFechas()) {
                    filtrosForm.submit();
                }
            });
        }

        if (filtroModulo) {
            filtroModulo.addEventListener('change', function() {
                if (validarFechas()) {
                    filtrosForm.submit();
                }
            });
        }

        if (filtroUsuario) {
            filtroUsuario.addEventListener('change', function() {
                if (validarFechas()) {
                    filtrosForm.submit();
                }
            });
        }

        /**
         * Validar fechas antes de submit
         */
        filtrosForm.addEventListener('submit', function(e) {
            if (!validarFechas()) {
                e.preventDefault();
                return false;
            }
        });

        /**
         * Búsqueda con debounce (esperar 500ms después de que el usuario deje de escribir)
         */
        var buscarTimeout;
        if (filtroBuscar) {
            filtroBuscar.addEventListener('input', function() {
                clearTimeout(buscarTimeout);
                buscarTimeout = setTimeout(function() {
                    if (filtroBuscar.value.length >= 3 || filtroBuscar.value.length === 0) {
                        if (validarFechas()) {
                            filtrosForm.submit();
                        }
                    }
                }, 500);
            });
        }

        /**
         * Establecer fecha por defecto (últimos 30 días) si no hay fechas
         */
        if (filtroFechaDesde && !filtroFechaDesde.value) {
            var hoy = new Date();
            var hace30Dias = new Date();
            hace30Dias.setDate(hace30Dias.getDate() - 30);
            
            filtroFechaDesde.value = hace30Dias.toISOString().split('T')[0];
            filtroFechaHasta.value = hoy.toISOString().split('T')[0];
        }
    });
})();


