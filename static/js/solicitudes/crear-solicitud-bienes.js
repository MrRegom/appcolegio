/**
 * Funcionalidad para crear solicitudes de bienes/activos
 * @module solicitudes/crear-solicitud-bienes
 * @description Maneja la selección dinámica de activos, cantidades y validaciones
 */

(function() {
    'use strict';

    // Variables globales
    let bienesSeleccionados = [];
    let modalBien;
    let contadorFilas = 0;

    /**
     * Inicializa la funcionalidad del formulario de solicitud
     */
    function inicializar() {
        // Inicializar modal de Bootstrap
        const modalElement = document.getElementById('modalBien');
        if (modalElement) {
            modalBien = new bootstrap.Modal(modalElement);
        }

        // Event listeners
        setupEventListeners();

        // Actualizar visualización inicial
        actualizarVisualizacionBienes();
    }

    /**
     * Configura todos los event listeners
     */
    function setupEventListeners() {
        // Botón para abrir modal de agregar bien
        const btnAgregar = document.getElementById('btn-agregar-bien');
        if (btnAgregar) {
            btnAgregar.addEventListener('click', () => {
                modalBien.show();
            });
        }

        // Buscador de bienes en el modal
        const inputBuscar = document.getElementById('buscar-bien');
        if (inputBuscar) {
            inputBuscar.addEventListener('input', filtrarBienes);
        }

        // Botones de selección de bienes en el modal
        document.querySelectorAll('.btn-seleccionar-bien').forEach(btn => {
            btn.addEventListener('click', seleccionarBien);
        });

        // Submit del formulario
        const form = document.getElementById('formSolicitud');
        if (form) {
            form.addEventListener('submit', validarYEnviarFormulario);
        }
    }

    /**
     * Filtra la lista de bienes en el modal según el término de búsqueda
     * @param {Event} e - Evento input
     */
    function filtrarBienes(e) {
        const termino = e.target.value.toLowerCase();
        const filas = document.querySelectorAll('#tbody-lista-bienes tr');

        filas.forEach(fila => {
            const codigo = fila.dataset.bienCodigo.toLowerCase();
            const nombre = fila.dataset.bienNombre.toLowerCase();

            if (codigo.includes(termino) || nombre.includes(termino)) {
                fila.style.display = '';
            } else {
                fila.style.display = 'none';
            }
        });
    }

    /**
     * Selecciona un bien y lo agrega a la tabla
     * @param {Event} e - Evento click
     */
    function seleccionarBien(e) {
        const fila = e.target.closest('tr');
        const bienId = parseInt(fila.dataset.bienId);

        // Verificar si el bien ya está seleccionado
        if (bienesSeleccionados.some(b => b.id === bienId)) {
            mostrarAlerta('Este bien/activo ya ha sido agregado', 'warning');
            return;
        }

        // Agregar bien a la lista
        const bien = {
            id: bienId,
            codigo: fila.dataset.bienCodigo,
            nombre: fila.dataset.bienNombre
        };

        bienesSeleccionados.push(bien);
        agregarFilaBien(bien);

        // Cerrar modal
        modalBien.hide();

        // Limpiar búsqueda
        document.getElementById('buscar-bien').value = '';
        document.querySelectorAll('#tbody-lista-bienes tr').forEach(tr => {
            tr.style.display = '';
        });

        // Actualizar visualización
        actualizarVisualizacionBienes();
    }

    /**
     * Agrega una fila de bien a la tabla
     * @param {Object} bien - Datos del bien
     */
    function agregarFilaBien(bien) {
        const tbody = document.getElementById('tbody-bienes');
        const fila = document.createElement('tr');
        fila.dataset.bienId = bien.id;
        fila.dataset.filaId = contadorFilas;

        fila.innerHTML = `
            <td>
                <strong>${bien.nombre}</strong><br>
                <small class="text-muted">Código: ${bien.codigo}</small>
                <input type="hidden" name="detalles[${contadorFilas}][activo_id]" value="${bien.id}">
            </td>
            <td>
                <input type="number"
                       name="detalles[${contadorFilas}][cantidad_solicitada]"
                       class="form-control form-control-sm"
                       min="1"
                       step="1"
                       required
                       placeholder="0">
            </td>
            <td>
                <input type="text"
                       name="detalles[${contadorFilas}][observaciones]"
                       class="form-control form-control-sm"
                       placeholder="Opcional">
            </td>
            <td class="text-center">
                <button type="button" class="btn btn-sm btn-danger btn-eliminar-fila" data-fila-id="${contadorFilas}">
                    <i class="ri-delete-bin-line"></i>
                </button>
            </td>
        `;

        tbody.appendChild(fila);

        // Event listener para eliminar fila
        fila.querySelector('.btn-eliminar-fila').addEventListener('click', eliminarFilaBien);

        contadorFilas++;
    }

    /**
     * Elimina una fila de bien
     * @param {Event} e - Evento click
     */
    function eliminarFilaBien(e) {
        const filaId = e.target.closest('button').dataset.filaId;
        const fila = document.querySelector(`tr[data-fila-id="${filaId}"]`);
        const bienId = parseInt(fila.dataset.bienId);

        // Remover de la lista de seleccionados
        bienesSeleccionados = bienesSeleccionados.filter(b => b.id !== bienId);

        // Remover del DOM
        fila.remove();

        // Actualizar visualización
        actualizarVisualizacionBienes();
    }

    /**
     * Actualiza la visualización de bienes (muestra/oculta mensaje de vacío)
     */
    function actualizarVisualizacionBienes() {
        const tbody = document.getElementById('tbody-bienes');
        const sinBienes = document.getElementById('sin-bienes');
        const tabla = document.getElementById('tabla-bienes');

        if (bienesSeleccionados.length === 0) {
            tabla.style.display = 'none';
            sinBienes.style.display = 'block';
        } else {
            tabla.style.display = 'table';
            sinBienes.style.display = 'none';
        }
    }

    /**
     * Valida y envía el formulario
     * @param {Event} e - Evento submit
     */
    function validarYEnviarFormulario(e) {
        // Validar que haya al menos un bien
        if (bienesSeleccionados.length === 0) {
            e.preventDefault();
            mostrarAlerta('Debe agregar al menos un bien/activo a la solicitud', 'warning');
            return false;
        }

        // Validar cantidades
        const inputsCantidad = document.querySelectorAll('input[name^="detalles"][name$="[cantidad_solicitada]"]');
        let todasValidas = true;

        inputsCantidad.forEach(input => {
            const valor = parseFloat(input.value);
            if (!valor || valor <= 0) {
                todasValidas = false;
                input.classList.add('is-invalid');
            } else {
                input.classList.remove('is-invalid');
            }
        });

        if (!todasValidas) {
            e.preventDefault();
            mostrarAlerta('Todas las cantidades deben ser mayores a cero', 'warning');
            return false;
        }

        // Si todo está bien, permitir envío
        return true;
    }

    /**
     * Muestra una alerta temporal
     * @param {string} mensaje - Mensaje a mostrar
     * @param {string} tipo - Tipo de alerta (success, warning, danger, info)
     */
    function mostrarAlerta(mensaje, tipo = 'info') {
        const alerta = document.createElement('div');
        alerta.className = `alert alert-${tipo} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
        alerta.style.zIndex = '9999';
        alerta.innerHTML = `
            ${mensaje}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;

        document.body.appendChild(alerta);

        // Auto-cerrar después de 5 segundos
        setTimeout(() => {
            alerta.remove();
        }, 5000);
    }

    // Inicializar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', inicializar);
    } else {
        inicializar();
    }

})();
