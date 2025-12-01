/**
 * Funcionalidad para crear solicitudes de artículos
 * @module solicitudes/crear-solicitud-articulos
 * @description Maneja la selección dinámica de artículos, cantidades y validaciones
 */

(function() {
    'use strict';

    // Variables globales
    let articulosSeleccionados = [];
    let modalArticulo;
    let contadorFilas = 0;

    /**
     * Inicializa la funcionalidad del formulario de solicitud
     */
    function inicializar() {
        // Inicializar modal de Bootstrap
        const modalElement = document.getElementById('modalArticulo');
        if (modalElement) {
            modalArticulo = new bootstrap.Modal(modalElement);
        }

        // Event listeners
        setupEventListeners();

        // Configurar estado inicial: ocultar tabla y mostrar empty state
        const tabla = document.getElementById('tabla-articulos');
        const sinArticulos = document.getElementById('sin-articulos');
        if (tabla && sinArticulos) {
            if (articulosSeleccionados.length === 0) {
                tabla.style.display = 'none';
                sinArticulos.style.display = 'block';
            } else {
                tabla.style.display = 'table';
                sinArticulos.style.display = 'none';
            }
        }
    }

    /**
     * Configura todos los event listeners
     */
    function setupEventListeners() {
        // Botón para abrir modal de agregar artículo
        const btnAgregar = document.getElementById('btn-agregar-articulo');
        if (btnAgregar) {
            btnAgregar.addEventListener('click', () => {
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

        // Submit del formulario
        const form = document.getElementById('formSolicitud');
        if (form) {
            form.addEventListener('submit', validarYEnviarFormulario);
        }
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
            unidad: fila.dataset.articuloUnidad
        };

        articulosSeleccionados.push(articulo);
        
        // Eliminar empty state INMEDIATAMENTE antes de agregar la fila
        const sinArticulos = document.getElementById('sin-articulos');
        if (sinArticulos && sinArticulos.parentNode) {
            sinArticulos.remove();
        }
        
        // Asegurar que la tabla esté visible
        const tabla = document.getElementById('tabla-articulos');
        const tablaContainer = tabla ? tabla.closest('.table-responsive') : null;
        if (tabla) {
            tabla.style.cssText = 'display: table !important;';
        }
        if (tablaContainer) {
            tablaContainer.style.cssText = 'display: block !important;';
        }
        
        agregarFilaArticulo(articulo);

        // Cerrar modal
        modalArticulo.hide();

        // Limpiar búsqueda
        document.getElementById('buscar-articulo').value = '';
        document.querySelectorAll('#tbody-lista-articulos tr').forEach(tr => {
            tr.style.display = '';
        });
    }

    /**
     * Agrega una fila de artículo a la tabla
     * @param {Object} articulo - Datos del artículo
     */
    function agregarFilaArticulo(articulo) {
        const tbody = document.getElementById('tbody-articulos');
        if (!tbody) return;
        
        // ELIMINAR empty state del DOM si existe (más efectivo que ocultarlo)
        const sinArticulos = document.getElementById('sin-articulos');
        if (sinArticulos && sinArticulos.parentNode) {
            sinArticulos.remove();
        }
        
        // Asegurar que la tabla esté visible
        const tabla = document.getElementById('tabla-articulos');
        const tablaContainer = tabla ? tabla.closest('.table-responsive') : null;
        if (tabla) {
            tabla.style.cssText = 'display: table !important;';
        }
        if (tablaContainer) {
            tablaContainer.style.cssText = 'display: block !important;';
        }
        
        const fila = document.createElement('tr');
        fila.dataset.articuloId = articulo.id;
        fila.dataset.filaId = contadorFilas;

        fila.innerHTML = `
            <td>
                <strong>${articulo.nombre}</strong><br>
                <small class="text-muted">Código: ${articulo.codigo}</small>
                <input type="hidden" name="detalles[${contadorFilas}][articulo_id]" value="${articulo.id}">
            </td>
            <td>
                <input type="number"
                       name="detalles[${contadorFilas}][cantidad_solicitada]"
                       class="form-control form-control-sm"
                       min="0.01"
                       step="0.01"
                       required
                       placeholder="0.00">
                <small class="text-muted">${articulo.unidad}</small>
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
        fila.querySelector('.btn-eliminar-fila').addEventListener('click', eliminarFilaArticulo);

        contadorFilas++;
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
        const tbody = document.getElementById('tbody-articulos');
        const sinArticulos = document.getElementById('sin-articulos');
        const tabla = document.getElementById('tabla-articulos');
        const tablaContainer = tabla ? tabla.closest('.table-responsive') : null;
        const cardBody = tabla ? tabla.closest('.card-body') : null;

        if (!tbody || !tabla) {
            return;
        }

        // Contar filas reales en el tbody (no solo el array)
        const filasReales = tbody.querySelectorAll('tr').length;

        if (filasReales === 0 || articulosSeleccionados.length === 0) {
            // Mostrar empty state (recrearlo si fue eliminado)
            if (!sinArticulos && cardBody) {
                const nuevoSinArticulos = document.createElement('div');
                nuevoSinArticulos.id = 'sin-articulos';
                nuevoSinArticulos.className = 'text-center text-muted py-4';
                nuevoSinArticulos.innerHTML = '<i class="ri-inbox-line" style="font-size: 3rem;"></i><p class="mb-0">No hay artículos agregados. Haga clic en "Agregar Artículo" para comenzar.</p>';
                cardBody.appendChild(nuevoSinArticulos);
            } else if (sinArticulos) {
                sinArticulos.style.cssText = 'display: block !important;';
            }
            if (tablaContainer) tablaContainer.style.display = 'none';
            tabla.style.display = 'none';
        } else {
            // Eliminar empty state si existe
            if (sinArticulos && sinArticulos.parentNode) {
                sinArticulos.remove();
            }
            if (tablaContainer) tablaContainer.style.cssText = 'display: block !important;';
            tabla.style.cssText = 'display: table !important;';
        }
    }

    /**
     * Valida y envía el formulario
     * @param {Event} e - Evento submit
     */
    function validarYEnviarFormulario(e) {
        // Validar que haya al menos un artículo
        if (articulosSeleccionados.length === 0) {
            e.preventDefault();
            mostrarAlerta('Debe agregar al menos un artículo a la solicitud', 'warning');
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
