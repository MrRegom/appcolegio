/**
 * Reportes Dinamicos - Logica de seleccion y filtros dinamicos
 * 
 * Separacion de responsabilidades: JavaScript en archivo dedicado
 * No mezclar JS con HTML (SRP - Single Responsibility Principle)
 */

(function() {
    'use strict';

    /**
     * Selecciona un reporte y muestra sus filtros
     */
    function seleccionarReporte(codigo) {
        // Remover seleccion anterior
        document.querySelectorAll('.reporte-card').forEach(card => {
            card.classList.remove('selected');
        });
        
        // Marcar como seleccionado
        const card = document.querySelector(`[data-reporte-codigo="${codigo}"]`);
        if (card) {
            card.classList.add('selected');
        }
        
        // Construir URL con el reporte seleccionado
        const url = new URL(window.location.href);
        url.searchParams.set('reporte', codigo);
        url.searchParams.delete('crear_informe');
        
        // Redirigir para mostrar filtros
        window.location.href = url.toString();
    }

    /**
     * Inicializa la vista cuando el DOM esta listo
     */
    document.addEventListener("DOMContentLoaded", function() {
        // Hacer la funcion seleccionarReporte disponible globalmente
        window.seleccionarReporte = seleccionarReporte;
        
        // Si hay un reporte seleccionado, marcar su card
        const urlParams = new URLSearchParams(window.location.search);
        const reporteSeleccionado = urlParams.get('reporte');
        
        if (reporteSeleccionado) {
            const card = document.querySelector(`[data-reporte-codigo="${reporteSeleccionado}"]`);
            if (card) {
                card.classList.add('selected');
                // Scroll suave hacia la card seleccionada
                card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }
        }
        
        // Si hay resultados, hacer scroll suave hacia ellos
        const resultadosContainer = document.getElementById('resultados-container');
        if (resultadosContainer) {
            setTimeout(() => {
                resultadosContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }, 300);
        }
    });
})();

