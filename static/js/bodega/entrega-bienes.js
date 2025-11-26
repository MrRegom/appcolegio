/**
 * JavaScript para gestión de entregas de bienes/activos
 * Siguiendo buenas prácticas de JavaScript moderno y Django
 */

const EntregaBienes = {
    activosDisponibles: [],
    detallesBienes: [],
    contadorFilas: 0,

    /**
     * Inicializa el módulo
     */
    init(activos) {
        this.activosDisponibles = activos;
        this.setupEventListeners();
    },

    /**
     * Configura event listeners
     */
    setupEventListeners() {
        // Event listener para el botón de agregar bien
        const btnAgregar = document.getElementById('btnAgregarBien');
        if (btnAgregar) {
            btnAgregar.addEventListener('click', () => this.agregarBien());
        }

        // Event listener para el submit del formulario
        const form = document.getElementById('formEntregaBien');
        if (form) {
            form.addEventListener('submit', (e) => this.validarYEnviarFormulario(e));
        }

        // Event listener para el select de solicitud
        const selectSolicitud = document.getElementById('id_solicitud');
        if (selectSolicitud) {
            selectSolicitud.addEventListener('change', (e) => this.cargarBienesSolicitud(e.target.value));
        }
    },

    /**
     * Agrega una fila de bien
     */
    agregarBien() {
        const tbody = document.getElementById('bienesBody');
        if (!tbody) return;

        // Limpiar fila vacía si existe
        if (tbody.children.length === 1 && tbody.children[0].cells.length === 1) {
            tbody.innerHTML = '';
        }

        const fila = tbody.insertRow();
        fila.id = `fila_${this.contadorFilas}`;
        const idFila = this.contadorFilas;

        // Celda de selección de activo
        const celdaActivo = fila.insertCell(0);
        const selectActivo = this.crearSelectActivo(idFila);
        celdaActivo.appendChild(selectActivo);

        // Celda de "Solicitado" (vacía para bienes agregados manualmente)
        const celdaSolicitado = fila.insertCell(1);
        const spanSolicitado = document.createElement('span');
        spanSolicitado.className = 'text-muted';
        spanSolicitado.textContent = '-';
        celdaSolicitado.appendChild(spanSolicitado);

        // Celda de cantidad a despachar
        const celdaCantidad = fila.insertCell(2);
        const inputCantidad = this.crearInputCantidad(idFila);
        celdaCantidad.appendChild(inputCantidad);

        // Celda de acciones
        const celdaAcciones = fila.insertCell(3);
        const btnEliminar = this.crearBotonEliminar(idFila);
        celdaAcciones.appendChild(btnEliminar);

        this.contadorFilas++;
    },

    /**
     * Carga bienes de una solicitud mediante AJAX
     */
    async cargarBienesSolicitud(solicitudId) {
        if (!solicitudId) {
            // Si no hay solicitud, limpiar la tabla
            this.limpiarTablaBienes();
            return;
        }

        try {
            const response = await fetch(`/bodega/ajax/solicitud/${solicitudId}/bienes/`, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                }
            });

            const data = await response.json();

            if (data.success) {
                this.cargarBienesEnTabla(data.bienes, data.solicitud);
            } else {
                alert(`Error: ${data.error}`);
            }
        } catch (error) {
            console.error('Error al cargar bienes:', error);
            alert('Error al cargar los bienes de la solicitud.');
        }
    },

    /**
     * Carga bienes en la tabla
     */
    cargarBienesEnTabla(bienes, solicitud) {
        // Limpiar tabla actual
        this.limpiarTablaBienes();

        if (!bienes || bienes.length === 0) {
            alert('Esta solicitud no tiene bienes/activos asociados.');
            return;
        }

        // Agregar cada bien a la tabla
        bienes.forEach(bien => {
            this.agregarBienDesdeSolicitud(bien);
        });

        // Rellenar otros campos del formulario
        if (solicitud) {
            // Rellenar motivo si está vacío
            const inputMotivo = document.getElementById('id_motivo');
            if (inputMotivo && !inputMotivo.value) {
                inputMotivo.value = solicitud.motivo || '';
            }
        }
    },

    /**
     * Agrega un bien desde una solicitud
     */
    agregarBienDesdeSolicitud(bien) {
        const tbody = document.getElementById('bienesBody');
        if (!tbody) return;

        // Limpiar fila vacía si existe
        if (tbody.children.length === 1 && tbody.children[0].cells.length === 1) {
            tbody.innerHTML = '';
        }

        const fila = tbody.insertRow();
        fila.id = `fila_${this.contadorFilas}`;
        const idFila = this.contadorFilas;

        // Celda de selección de activo (pre-seleccionado)
        const celdaActivo = fila.insertCell(0);
        const selectActivo = this.crearSelectActivo(idFila);
        selectActivo.value = bien.activo_id;
        celdaActivo.appendChild(selectActivo);

        // Celda de "Solicitado" con información de seguimiento
        const celdaSolicitado = fila.insertCell(1);
        const divInfo = document.createElement('div');
        divInfo.innerHTML = `
            <div><strong>${bien.cantidad_solicitada}</strong> <span class="text-muted">solicitado(s)</span></div>
            <small class="text-muted">Aprobado: ${bien.cantidad_aprobada} | Despachado: ${bien.cantidad_despachada}</small>
        `;
        celdaSolicitado.appendChild(divInfo);

        // Celda de cantidad a despachar (pre-llenada con cantidad pendiente)
        const celdaCantidad = fila.insertCell(2);
        const inputCantidad = this.crearInputCantidad(idFila);
        inputCantidad.value = bien.cantidad_pendiente || bien.cantidad_aprobada || 1;
        inputCantidad.max = bien.cantidad_pendiente || bien.cantidad_aprobada;
        celdaCantidad.appendChild(inputCantidad);

        // Agregar información de pendiente debajo del input
        const smallPendiente = document.createElement('small');
        smallPendiente.className = 'text-muted d-block mt-1';
        smallPendiente.textContent = `Pendiente: ${bien.cantidad_pendiente}`;
        celdaCantidad.appendChild(smallPendiente);

        // Celda de acciones
        const celdaAcciones = fila.insertCell(3);
        const btnEliminar = this.crearBotonEliminar(idFila);
        celdaAcciones.appendChild(btnEliminar);

        // Guardar el detalle_solicitud_id para enviar en el formulario
        fila.dataset.detalleSolicitudId = bien.detalle_solicitud_id;

        this.contadorFilas++;
    },

    /**
     * Limpia la tabla de bienes
     */
    limpiarTablaBienes() {
        const tbody = document.getElementById('bienesBody');
        if (!tbody) return;

        tbody.innerHTML = `
            <tr>
                <td colspan="4" class="text-center text-muted">
                    No hay bienes agregados. Haga clic en "Agregar Bien" para comenzar.
                </td>
            </tr>
        `;
        this.contadorFilas = 0;
    },

    /**
     * Crea select de activos
     */
    crearSelectActivo(idFila) {
        const select = document.createElement('select');
        select.className = 'form-select form-select-sm';
        select.id = `activo_${idFila}`;
        select.required = true;
        select.innerHTML = '<option value="">Seleccione...</option>';

        this.activosDisponibles.forEach(activo => {
            const categoria = activo.categoria || '-';
            const codigo = activo.codigo || '';
            select.innerHTML += `<option value="${activo.id}">
                ${this.escapeHtml(activo.nombre)} - ${this.escapeHtml(codigo)} (${this.escapeHtml(categoria)})
            </option>`;
        });

        return select;
    },

    /**
     * Crea input de cantidad
     */
    crearInputCantidad(idFila) {
        const input = document.createElement('input');
        input.type = 'number';
        input.className = 'form-control form-control-sm';
        input.id = `cantidad_${idFila}`;
        input.step = '1';
        input.min = '1';
        input.value = '1';
        input.required = true;
        return input;
    },

    /**
     * Crea input de número de serie
     */
    crearInputSerie(idFila) {
        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'form-control form-control-sm';
        input.id = `serie_${idFila}`;
        input.placeholder = 'Número de serie (opcional)';
        return input;
    },

    /**
     * Crea select de estado físico
     */
    crearSelectEstado(idFila) {
        const select = document.createElement('select');
        select.className = 'form-select form-select-sm';
        select.id = `estado_fisico_${idFila}`;
        select.innerHTML = `
            <option value="">Seleccione...</option>
            <option value="EXCELENTE">Excelente</option>
            <option value="BUENO">Bueno</option>
            <option value="REGULAR">Regular</option>
            <option value="MALO">Malo</option>
        `;
        return select;
    },

    /**
     * Crea botón de eliminar
     */
    crearBotonEliminar(idFila) {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'btn btn-sm btn-danger';
        btn.innerHTML = '<i class="ri-delete-bin-line"></i>';
        btn.addEventListener('click', () => this.eliminarFila(idFila));
        return btn;
    },

    /**
     * Elimina una fila de la tabla
     */
    eliminarFila(idFila) {
        const fila = document.getElementById(`fila_${idFila}`);
        if (fila) {
            fila.remove();
        }

        // Si no quedan filas, mostrar mensaje
        const tbody = document.getElementById('bienesBody');
        if (tbody && tbody.children.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="4" class="text-center text-muted">
                        No hay bienes agregados. Haga clic en "Agregar Bien" para comenzar.
                    </td>
                </tr>
            `;
        }
    },

    /**
     * Valida y envía el formulario
     */
    validarYEnviarFormulario(e) {
        e.preventDefault();

        const detalles = [];
        const tbody = document.getElementById('bienesBody');

        // Validar que haya bienes
        if (!tbody || tbody.children.length === 0 || tbody.children[0].cells.length === 1) {
            alert('Debe agregar al menos un bien a la entrega.');
            return false;
        }

        // Recorrer filas y construir array de detalles
        for (let i = 0; i < this.contadorFilas; i++) {
            const fila = document.getElementById(`fila_${i}`);
            if (!fila) continue;

            const selectActivo = document.getElementById(`activo_${i}`);
            const inputCantidad = document.getElementById(`cantidad_${i}`);

            if (!selectActivo || !selectActivo.value) {
                alert('Seleccione un activo/bien en todas las filas.');
                return false;
            }

            if (!inputCantidad || !inputCantidad.value || parseInt(inputCantidad.value) <= 0) {
                alert('Ingrese una cantidad válida en todas las filas.');
                return false;
            }

            // Obtener detalle_solicitud_id si existe
            const detalleSolicitudId = fila.dataset.detalleSolicitudId ? parseInt(fila.dataset.detalleSolicitudId) : null;

            detalles.push({
                equipo_id: parseInt(selectActivo.value),
                cantidad: parseInt(inputCantidad.value),
                detalle_solicitud_id: detalleSolicitudId
            });
        }

        // Guardar JSON en campo oculto
        const detallesInput = document.getElementById('detallesJson');
        if (detallesInput) {
            detallesInput.value = JSON.stringify(detalles);
        }

        // Enviar formulario
        e.target.submit();
        return true;
    },

    /**
     * Escapa HTML para prevenir XSS
     */
    escapeHtml(unsafe) {
        if (!unsafe) return '';
        return unsafe
            .toString()
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
};

// Exportar para uso global
window.EntregaBienes = EntregaBienes;
