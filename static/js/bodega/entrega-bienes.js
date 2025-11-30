/**
 * Funcionalidad para crear entregas de bienes
 * @module bodega/entrega-bienes
 * @description Maneja la selección dinámica de bienes, cantidades, validaciones y carga desde solicitudes
 */

(function() {
    'use strict';

    // Variables globales
    let bienesSeleccionados = [];
    let bienesDisponibles = [];
    let modalBien;
    let contadorFilas = 0;
    let solicitudCargada = false;

    /**
     * Inicializa la funcionalidad del formulario de entrega
     */
    function inicializar() {
        // Cargar bienes disponibles desde la variable global
        if (typeof BIENES_DISPONIBLES !== 'undefined') {
            bienesDisponibles = BIENES_DISPONIBLES;
        }

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
                if (solicitudCargada) {
                    mostrarAlerta('No puede agregar bienes manualmente cuando hay una solicitud cargada', 'warning');
                    return;
                }
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

        // Selector de solicitud
        const selectSolicitud = document.getElementById('id_solicitud');
        if (selectSolicitud) {
            selectSolicitud.addEventListener('change', handleSolicitudChange);
        }

        // Submit del formulario
        const form = document.getElementById('formEntregaBien');
        if (form) {
            form.addEventListener('submit', validarYEnviarFormulario);
        }
    }

    /**
     * Maneja el cambio en el selector de solicitud
     * @param {Event} e - Evento change
     */
    async function handleSolicitudChange(e) {
        const solicitudId = e.target.value;

        if (solicitudId) {
            await cargarBienesSolicitud(solicitudId);
        } else {
            limpiarBienesSolicitud();
        }
    }

    /**
     * Carga bienes de una solicitud via AJAX
     * @param {number} solicitudId - ID de la solicitud
     */
    async function cargarBienesSolicitud(solicitudId) {
        try {
            const response = await fetch(`/bodega/ajax/solicitud/${solicitudId}/bienes/`);
            const data = await response.json();

            if (data.success) {
                mostrarInfoSolicitud(data.solicitud);
                cargarBienesEnTabla(data.bienes, data.solicitud);
                solicitudCargada = true;

                mostrarAlerta('Bienes cargados desde la solicitud correctamente', 'success');
            } else {
                mostrarAlerta('Error al cargar bienes de la solicitud: ' + (data.error || data.message), 'danger');
            }
        } catch (error) {
            console.error('Error:', error);
            mostrarAlerta('Error al cargar bienes de la solicitud', 'danger');
        }
    }

    /**
     * Muestra información de la solicitud
     * @param {Object} solicitud - Datos de la solicitud
     */
    function mostrarInfoSolicitud(solicitud) {
        const infoDiv = document.getElementById('infoSolicitud');
        const datosDiv = document.getElementById('datosSolicitud');

        if (!infoDiv || !datosDiv) return;

        datosDiv.innerHTML = `
            <p class="mb-1"><strong>Número:</strong> ${solicitud.numero}</p>
            <p class="mb-1"><strong>Solicitante:</strong> ${solicitud.solicitante}</p>
            <p class="mb-1"><strong>Departamento:</strong> ${solicitud.departamento || 'N/A'}</p>
            <p class="mb-0"><strong>Motivo:</strong> ${solicitud.motivo || 'N/A'}</p>
        `;

        infoDiv.classList.remove('d-none');
    }

    /**
     * Carga bienes en la tabla desde solicitud
     * @param {Array} bienes - Array de bienes de la solicitud
     * @param {Object} solicitud - Datos de la solicitud
     */
    function cargarBienesEnTabla(bienes, solicitud) {
        // Limpiar bienes existentes
        bienesSeleccionados = [];
        const tbody = document.getElementById('tbody-bienes');
        tbody.innerHTML = '';

        // Agregar cada bien de la solicitud
        bienes.forEach(bien => {
            const bienData = {
                id: bien.activo_id || bien.equipo_id,
                codigo: bien.activo_codigo || bien.codigo,
                nombre: bien.activo_nombre || bien.nombre,
                categoria: bien.categoria || '-',
                cantidadSolicitada: parseFloat(bien.cantidad_solicitada || bien.cantidad_aprobada || 0),
                cantidadPendiente: parseFloat(bien.cantidad_pendiente || 0)
            };

            bienesSeleccionados.push(bienData);
            agregarFilaBien(bienData, true, bien.cantidad_pendiente);
        });

        actualizarVisualizacionBienes();
    }

    /**
     * Limpia datos de solicitud
     */
    function limpiarBienesSolicitud() {
        const infoDiv = document.getElementById('infoSolicitud');
        if (infoDiv) {
            infoDiv.classList.add('d-none');
        }

        // Limpiar bienes
        bienesSeleccionados = [];
        const tbody = document.getElementById('tbody-bienes');
        tbody.innerHTML = '';

        solicitudCargada = false;
        actualizarVisualizacionBienes();
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
            mostrarAlerta('Este bien ya ha sido agregado', 'warning');
            return;
        }

        // Agregar bien a la lista
        const bien = {
            id: bienId,
            codigo: fila.dataset.bienCodigo,
            nombre: fila.dataset.bienNombre,
            categoria: fila.dataset.bienCategoria,
            estado: fila.dataset.bienEstado
        };

        bienesSeleccionados.push(bien);
        agregarFilaBien(bien, false);

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
     * @param {boolean} desdeSolicitud - Si viene de una solicitud
     * @param {number} cantidadSugerida - Cantidad sugerida (desde solicitud)
     */
    function agregarFilaBien(bien, desdeSolicitud = false, cantidadSugerida = null) {
        const tbody = document.getElementById('tbody-bienes');
        const fila = document.createElement('tr');
        fila.dataset.bienId = bien.id;
        fila.dataset.filaId = contadorFilas;

        fila.innerHTML = `
            <td>
                <strong>${bien.nombre}</strong><br>
                <small class="text-muted">Código: ${bien.codigo}</small>
            </td>
            <td>
                <span class="badge bg-secondary">${bien.categoria || '-'}</span>
            </td>
            <td>
                ${bien.cantidadSolicitada ? `<span class="badge bg-info">${bien.cantidadSolicitada}</span>` : '<span class="text-muted">-</span>'}
            </td>
            <td>
                <input type="number"
                       class="form-control form-control-sm input-cantidad"
                       data-pendiente="${bien.cantidadPendiente || 0}"
                       min="1"
                       step="1"
                       max="${bien.cantidadPendiente || 999}"
                       value="${cantidadSugerida || ''}"
                       required
                       placeholder="1">
            </td>
            <td>
                <input type="text"
                       class="form-control form-control-sm input-observaciones"
                       placeholder="Opcional">
            </td>
            <td class="text-center">
                <button type="button"
                        class="btn btn-sm btn-danger btn-eliminar-fila"
                        data-fila-id="${contadorFilas}"
                        ${desdeSolicitud ? 'disabled title="No puede eliminar bienes de una solicitud"' : ''}>
                    <i class="ri-delete-bin-line"></i>
                </button>
            </td>
        `;

        tbody.appendChild(fila);

        // Event listener para validar cantidad en tiempo real
        const inputCantidad = fila.querySelector('.input-cantidad');
        inputCantidad.addEventListener('input', validarCantidadEnTiempoReal);

        // Event listener para eliminar fila (solo si no viene de solicitud)
        if (!desdeSolicitud) {
            fila.querySelector('.btn-eliminar-fila').addEventListener('click', eliminarFilaBien);
        }

        contadorFilas++;
    }

    /**
     * Valida la cantidad en tiempo real
     * @param {Event} e - Evento input
     */
    function validarCantidadEnTiempoReal(e) {
        const input = e.target;
        const cantidad = parseFloat(input.value) || 0;
        const pendiente = parseFloat(input.dataset.pendiente) || 0;

        // Validar contra cantidad pendiente si existe
        if (pendiente > 0 && cantidad > pendiente) {
            input.classList.add('is-invalid');
            input.setCustomValidity('La cantidad excede la cantidad pendiente');
        } else {
            input.classList.remove('is-invalid');
            input.setCustomValidity('');
        }
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
        const sinBienes = document.getElementById('sin-bienes');
        const tbody = document.getElementById('tbody-bienes');

        if (!sinBienes || !tbody) {
            console.warn('Elementos de visualización no encontrados');
            return;
        }

        // Contar filas reales en tbody
        const numFilas = tbody.querySelectorAll('tr').length;

        console.log('Actualizando visualización. Filas en tabla:', numFilas, 'Bienes seleccionados:', bienesSeleccionados.length);

        // Buscar el contenedor de la tabla
        const tabla = document.getElementById('tabla-bienes');
        const tablaContainer = tabla ? tabla.parentElement : null;

        if (numFilas === 0) {
            // No hay bienes: ocultar tabla, mostrar mensaje
            if (tablaContainer) tablaContainer.style.display = 'none';
            sinBienes.style.display = 'block';
        } else {
            // Hay bienes: mostrar tabla, ocultar mensaje
            if (tablaContainer) tablaContainer.style.display = 'block';
            sinBienes.style.display = 'none';
        }
    }

    /**
     * Valida y envía el formulario
     * @param {Event} e - Evento submit
     */
    function validarYEnviarFormulario(e) {
        e.preventDefault();

        // Validar que haya al menos un bien
        if (bienesSeleccionados.length === 0) {
            mostrarAlerta('Debe agregar al menos un bien a la entrega', 'warning');
            return false;
        }

        const detalles = [];
        const tbody = document.getElementById('tbody-bienes');
        const filas = tbody.querySelectorAll('tr');

        let todasValidas = true;

        filas.forEach((fila, index) => {
            const bienId = parseInt(fila.dataset.bienId);
            const inputCantidad = fila.querySelector('.input-cantidad');
            const inputObservaciones = fila.querySelector('.input-observaciones');

            if (!inputCantidad) return;

            const cantidad = parseInt(inputCantidad.value);
            const pendiente = parseFloat(inputCantidad.dataset.pendiente) || 0;

            // Validaciones
            if (!cantidad || cantidad <= 0) {
                todasValidas = false;
                inputCantidad.classList.add('is-invalid');
                return;
            }

            if (pendiente > 0 && cantidad > pendiente) {
                todasValidas = false;
                inputCantidad.classList.add('is-invalid');
                mostrarAlerta(`La cantidad (${cantidad}) excede la cantidad pendiente (${pendiente})`, 'danger');
                return;
            }

            inputCantidad.classList.remove('is-invalid');

            // Agregar a detalles
            detalles.push({
                equipo_id: bienId,
                cantidad: cantidad,
                observaciones: inputObservaciones.value || null
            });
        });

        if (!todasValidas) {
            mostrarAlerta('Por favor corrija los errores en el formulario', 'warning');
            return false;
        }

        if (detalles.length === 0) {
            mostrarAlerta('Debe agregar al menos un bien a la entrega', 'warning');
            return false;
        }

        // Guardar JSON en campo oculto
        const detallesInput = document.getElementById('detallesJson');
        if (detallesInput) {
            detallesInput.value = JSON.stringify(detalles);
        }

        // Enviar formulario
        e.target.submit();
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
