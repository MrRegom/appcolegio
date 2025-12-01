/**
<<<<<<< HEAD
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
=======
 * Dashboard Counters - Animación de contadores para las métricas
 * 
 * Separación de responsabilidades: JavaScript en archivo dedicado
 * No mezclar JS con HTML (SRP - Single Responsibility Principle)
 */

(function() {
    'use strict';

    /**
     * Función para animar contadores numéricos
     * @param {HTMLElement} element - Elemento que contiene el contador
     */
    function animateCounter(element) {
        const targetText = element.getAttribute('data-target');
        let target;
        
        // Manejar números con decimales
        if (targetText.includes('.')) {
            target = parseFloat(targetText);
        } else {
            target = parseInt(targetText) || 0;
        }
        
        const duration = 2000; // 2 segundos
>>>>>>> b8346a8f8f921bf1c6d1feafdd4856ee9f79e413
        const increment = target / (duration / 16); // 60 FPS
        let current = 0;
        
        const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
<<<<<<< HEAD
                element.textContent = target;
                clearInterval(timer);
            } else {
                element.textContent = Math.floor(current);
=======
                if (targetText.includes('.')) {
                    element.textContent = target.toFixed(2);
                } else {
                    element.textContent = Math.floor(target);
                }
                clearInterval(timer);
            } else {
                if (targetText.includes('.')) {
                    element.textContent = current.toFixed(2);
                } else {
                    element.textContent = Math.floor(current);
                }
>>>>>>> b8346a8f8f921bf1c6d1feafdd4856ee9f79e413
            }
        }, 16);
    }

<<<<<<< HEAD
=======
    /**
     * Inicializa las animaciones de contadores cuando el DOM está listo
     */
>>>>>>> b8346a8f8f921bf1c6d1feafdd4856ee9f79e413
    document.addEventListener("DOMContentLoaded", function() {
        // Aplicar animación a todos los contadores con delay escalonado
        document.querySelectorAll('.counter-value').forEach((counter, index) => {
            setTimeout(() => {
                animateCounter(counter);
<<<<<<< HEAD
            }, index * 200);
        });
    });
})();

=======
            }, index * 200); // Delay de 200ms entre cada contador
        });
    });
})();
>>>>>>> b8346a8f8f921bf1c6d1feafdd4856ee9f79e413
