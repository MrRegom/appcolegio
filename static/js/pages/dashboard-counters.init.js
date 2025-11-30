/**
 * Dashboard Counters Animation
 * 
 * Anima los valores numéricos de las cards del dashboard.
 * Separación de responsabilidades: solo animación de contadores.
 */
(function() {
    'use strict';

    function animateCounter(element) {
        const target = parseInt(element.getAttribute('data-target')) || 0;
        const duration = 1500; // 1.5 segundos
        const increment = target / (duration / 16); // 60 FPS
        let current = 0;
        
        const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
                element.textContent = target;
                clearInterval(timer);
            } else {
                element.textContent = Math.floor(current);
            }
        }, 16);
    }

    document.addEventListener("DOMContentLoaded", function() {
        // Aplicar animación a todos los contadores con delay escalonado
        document.querySelectorAll('.counter-value').forEach((counter, index) => {
            setTimeout(() => {
                animateCounter(counter);
            }, index * 200);
        });
    });
})();

