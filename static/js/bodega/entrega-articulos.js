/**
 * Funcionalidad para crear entregas de artículos
 * @module bodega/entrega-articulos
 * @description Maneja la selección dinámica de artículos, cantidades, validaciones de stock y carga desde solicitudes
 */

(function() {
    'use strict';

    // Variables globales
    let articulosSeleccionados = [];
    let articulosDisponibles = [];
    let modalArticulo;
    let contadorFilas = 0;
    let solicitudCargada = false;

    /**
     * Inicializa la funcionalidad del formulario de entrega
     */
    function inicializar() {
        // Cargar artículos disponibles desde la variable global
        if (typeof ARTICULOS_DISPONIBLES !== 'undefined') {
            articulosDisponibles = ARTICULOS_DISPONIBLES;
        }

        // Inicializar modal de Bootstrap
        const modalElement = document.getElementById('modalArticulo');
        if (modalElement) {
            modalArticulo = new bootstrap.Modal(modalElement);
        }

        // Event listeners
        setupEventListeners();

        // Actualizar visualización inicial
        actualizarVisualizacionArticulos();
    }

    /**
     * Configura todos los event listeners
     */
    function setupEventListeners() {
        // Botón para abrir modal de agregar artículo
        const btnAgregar = document.getElementById('btn-agregar-articulo');
        if (btnAgregar) {
            btnAgregar.addEventListener('click', () => {
                if (solicitudCargada) {
                    mostrarAlerta('No puede agregar artículos manualmente cuando hay una solicitud cargada', 'warning');
                    return;
                }
                modalArticulo.show();
            });
        }

        // Buscador de artículos en el modal
        const inputBuscar = document.getElementById('buscar-articulo');
        if (inputBuscar) {
            inputBuscar.addEventListener('input', filtrarArticulos);
        }

        // Botones de selección de artículos en el modal
        document.querySelectorAll('.btn-seleccionar-articulo').forEach(btn => {
            btn.addEventListener('click', seleccionarArticulo);
        });

        // Selector de solicitud
        const selectSolicitud = document.getElementById('id_solicitud');
        if (selectSolicitud) {
            selectSolicitud.addEventListener('change', handleSolicitudChange);
        }

        // Submit del formulario
        const form = document.getElementById('formEntregaArticulo');
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
            await cargarArticulosSolicitud(solicitudId);
        } else {
            limpiarArticulosSolicitud();
        }
    }

    /**
     * Carga artículos de una solicitud via AJAX
     * @param {number} solicitudId - ID de la solicitud
     */
    async function cargarArticulosSolicitud(solicitudId) {
        try {
            const response = await fetch(`/bodega/ajax/solicitud/${solicitudId}/articulos/`);
            const data = await response.json();

            if (data.success) {
                mostrarInfoSolicitud(data.solicitud);
                cargarArticulosEnTabla(data.articulos, data.solicitud);
                solicitudCargada = true;

                // Auto-seleccionar bodega origen si está disponible
                if (data.solicitud.bodega_origen_id) {
                    const selectBodega = document.getElementById('id_bodega_origen');
                    if (selectBodega) {
                        selectBodega.value = data.solicitud.bodega_origen_id;
                    }
                }

                mostrarAlerta('Artículos cargados desde la solicitud correctamente', 'success');
            } else {
                mostrarAlerta('Error al cargar artículos de la solicitud: ' + (data.error || data.message), 'danger');
            }
        } catch (error) {
            console.error('Error:', error);
            mostrarAlerta('Error al cargar artículos de la solicitud', 'danger');
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
     * Carga artículos en la tabla desde solicitud
     * @param {Array} articulos - Array de artículos de la solicitud
     * @param {Object} solicitud - Datos de la solicitud
     */
    function cargarArticulosEnTabla(articulos, solicitud) {
        // Limpiar artículos existentes
        articulosSeleccionados = [];
        const tbody = document.getElementById('tbody-articulos');
        tbody.innerHTML = '';

        // Agregar cada artículo de la solicitud
        articulos.forEach(art => {
            const articuloData = {
                id: art.articulo_id,
                codigo: art.articulo_codigo || art.codigo,
                nombre: art.articulo_nombre || art.nombre,
                stock: parseFloat(art.stock_actual || 0),
                unidad: art.unidad_medida || art.unidad || 'unidad',
                cantidadSolicitada: parseFloat(art.cantidad_solicitada || art.cantidad_aprobada || 0),
                cantidadPendiente: parseFloat(art.cantidad_pendiente || 0)
            };

            articulosSeleccionados.push(articuloData);
            agregarFilaArticulo(articuloData, true, art.cantidad_pendiente);
        });

        actualizarVisualizacionArticulos();
    }

    /**
     * Limpia datos de solicitud
     */
    function limpiarArticulosSolicitud() {
        const infoDiv = document.getElementById('infoSolicitud');
        if (infoDiv) {
            infoDiv.classList.add('d-none');
        }

        // Limpiar artículos
        articulosSeleccionados = [];
        const tbody = document.getElementById('tbody-articulos');
        tbody.innerHTML = '';

        solicitudCargada = false;
        actualizarVisualizacionArticulos();
    }

    /**
     * Filtra la lista de artículos en el modal según el término de búsqueda
     * @param {Event} e - Evento input
     */
    function filtrarArticulos(e) {
        const termino = e.target.value.toLowerCase();
        const filas = document.querySelectorAll('#tbody-lista-articulos tr');

        filas.forEach(fila => {
            const codigo = fila.dataset.articuloCodigo.toLowerCase();
            const nombre = fila.dataset.articuloNombre.toLowerCase();

            if (codigo.includes(termino) || nombre.includes(termino)) {
                fila.style.display = '';
            } else {
                fila.style.display = 'none';
            }
        });
    }

    /**
     * Selecciona un artículo y lo agrega a la tabla
     * @param {Event} e - Evento click
     */
    function seleccionarArticulo(e) {
        const fila = e.target.closest('tr');
        const articuloId = parseInt(fila.dataset.articuloId);

        // Verificar si el artículo ya está seleccionado
        if (articulosSeleccionados.some(a => a.id === articuloId)) {
            mostrarAlerta('Este artículo ya ha sido agregado', 'warning');
            return;
        }

        // Agregar artículo a la lista
        const articulo = {
            id: articuloId,
            codigo: fila.dataset.articuloCodigo,
            nombre: fila.dataset.articuloNombre,
            stock: parseFloat(fila.dataset.articuloStock),
            unidad: fila.dataset.articuloUnidad
        };

        articulosSeleccionados.push(articulo);
        agregarFilaArticulo(articulo, false);

        // Cerrar modal
        modalArticulo.hide();

        // Limpiar búsqueda
        document.getElementById('buscar-articulo').value = '';
        document.querySelectorAll('#tbody-lista-articulos tr').forEach(tr => {
            tr.style.display = '';
        });

        // Actualizar visualización
        actualizarVisualizacionArticulos();
    }

    /**
     * Agrega una fila de artículo a la tabla
     * @param {Object} articulo - Datos del artículo
     * @param {boolean} desdeSolicitud - Si viene de una solicitud
     * @param {number} cantidadSugerida - Cantidad sugerida (desde solicitud)
     */
    function agregarFilaArticulo(articulo, desdeSolicitud = false, cantidadSugerida = null) {
        const tbody = document.getElementById('tbody-articulos');
        const fila = document.createElement('tr');
        fila.dataset.articuloId = articulo.id;
        fila.dataset.filaId = contadorFilas;

        // Determinar clase de badge según stock
        let badgeClass = 'bg-success';
        if (articulo.stock === 0) {
            badgeClass = 'bg-danger';
        } else if (articulo.stock < 10) {
            badgeClass = 'bg-warning';
        }

        fila.innerHTML = `
            <td>
                <strong>${articulo.nombre}</strong><br>
                <small class="text-muted">Código: ${articulo.codigo}</small>
            </td>
            <td>
                <span class="badge ${badgeClass}">${articulo.stock} ${articulo.unidad}</span>
            </td>
            <td>
                ${articulo.cantidadSolicitada ? `<span class="badge bg-info">${articulo.cantidadSolicitada} ${articulo.unidad}</span>` : '<span class="text-muted">-</span>'}
            </td>
            <td>
                <input type="number"
                       class="form-control form-control-sm input-cantidad"
                       data-stock="${articulo.stock}"
                       data-pendiente="${articulo.cantidadPendiente || 0}"
                       min="0.01"
                       step="0.01"
                       max="${articulo.cantidadPendiente || articulo.stock}"
                       value="${cantidadSugerida || ''}"
                       required
                       placeholder="0.00">
                <small class="text-muted">${articulo.unidad}</small>
            </td>
            <td>
                <input type="text"
                       class="form-control form-control-sm input-lote"
                       placeholder="Opcional">
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
                        ${desdeSolicitud ? 'disabled title="No puede eliminar artículos de una solicitud"' : ''}>
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
            fila.querySelector('.btn-eliminar-fila').addEventListener('click', eliminarFilaArticulo);
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
        const stock = parseFloat(input.dataset.stock) || 0;
        const pendiente = parseFloat(input.dataset.pendiente) || 0;

        // Validar contra stock
        if (cantidad > stock) {
            input.classList.add('is-invalid');
            input.setCustomValidity('La cantidad excede el stock disponible');
        }
        // Validar contra cantidad pendiente si existe
        else if (pendiente > 0 && cantidad > pendiente) {
            input.classList.add('is-invalid');
            input.setCustomValidity('La cantidad excede la cantidad pendiente');
        }
        else {
            input.classList.remove('is-invalid');
            input.setCustomValidity('');
        }
    }

    /**
     * Elimina una fila de artículo
     * @param {Event} e - Evento click
     */
    function eliminarFilaArticulo(e) {
        const filaId = e.target.closest('button').dataset.filaId;
        const fila = document.querySelector(`tr[data-fila-id="${filaId}"]`);
        const articuloId = parseInt(fila.dataset.articuloId);

        // Remover de la lista de seleccionados
        articulosSeleccionados = articulosSeleccionados.filter(a => a.id !== articuloId);

        // Remover del DOM
        fila.remove();

        // Actualizar visualización
        actualizarVisualizacionArticulos();
    }

    /**
     * Actualiza la visualización de artículos (muestra/oculta mensaje de vacío)
     */
    function actualizarVisualizacionArticulos() {
        const sinArticulos = document.getElementById('sin-articulos');
        const tbody = document.getElementById('tbody-articulos');

        if (!sinArticulos || !tbody) {
            console.warn('Elementos de visualización no encontrados');
            return;
        }

        // Contar filas reales en tbody
        const numFilas = tbody.querySelectorAll('tr').length;

        console.log('Actualizando visualización. Filas en tabla:', numFilas, 'Artículos seleccionados:', articulosSeleccionados.length);

        // Buscar el contenedor de la tabla
        const tabla = document.getElementById('tabla-articulos');
        const tablaContainer = tabla ? tabla.parentElement : null;

        if (numFilas === 0) {
            // No hay artículos: ocultar tabla, mostrar mensaje
            if (tablaContainer) tablaContainer.style.display = 'none';
            sinArticulos.style.display = 'block';
        } else {
            // Hay artículos: mostrar tabla, ocultar mensaje
            if (tablaContainer) tablaContainer.style.display = 'block';
            sinArticulos.style.display = 'none';
        }
    }

    /**
     * Valida y envía el formulario
     * @param {Event} e - Evento submit
     */
    function validarYEnviarFormulario(e) {
        e.preventDefault();

        // Validar que haya al menos un artículo
        if (articulosSeleccionados.length === 0) {
            mostrarAlerta('Debe agregar al menos un artículo a la entrega', 'warning');
            return false;
        }

        const detalles = [];
        const tbody = document.getElementById('tbody-articulos');
        const filas = tbody.querySelectorAll('tr');

        let todasValidas = true;

        filas.forEach((fila, index) => {
            const articuloId = parseInt(fila.dataset.articuloId);
            const inputCantidad = fila.querySelector('.input-cantidad');
            const inputLote = fila.querySelector('.input-lote');
            const inputObservaciones = fila.querySelector('.input-observaciones');

            if (!inputCantidad) return;

            const cantidad = parseFloat(inputCantidad.value);
            const stock = parseFloat(inputCantidad.dataset.stock);
            const pendiente = parseFloat(inputCantidad.dataset.pendiente) || 0;

            // Validaciones
            if (!cantidad || cantidad <= 0) {
                todasValidas = false;
                inputCantidad.classList.add('is-invalid');
                return;
            }

            if (cantidad > stock) {
                todasValidas = false;
                inputCantidad.classList.add('is-invalid');
                mostrarAlerta(`La cantidad (${cantidad}) excede el stock disponible (${stock})`, 'danger');
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
                articulo_id: articuloId,
                cantidad: cantidad,
                lote: inputLote.value || null,
                observaciones: inputObservaciones.value || null
            });
        });

        if (!todasValidas) {
            mostrarAlerta('Por favor corrija los errores en el formulario', 'warning');
            return false;
        }

        if (detalles.length === 0) {
            mostrarAlerta('Debe agregar al menos un artículo a la entrega', 'warning');
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
