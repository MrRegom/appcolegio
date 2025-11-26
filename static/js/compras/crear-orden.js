/**
 * Funcionalidad para crear órdenes de compra
 * Basado en el patrón de entrega de artículos/bienes
 */

const OrdenCompra = {
    articulosDisponibles: [],
    activosDisponibles: [],
    solicitudesSeleccionadas: [],
    articulosOrden: [],
    bienesOrden: [],
    contadorArticulos: 0,
    contadorBienes: 0,

    /**
     * Inicializa el módulo
     */
    init(articulos, activos) {
        this.articulosDisponibles = articulos;
        this.activosDisponibles = activos;
        this.setupEventListeners();
        this.mostrarSeccionesVacias();
        console.log('OrdenCompra inicializado correctamente');
    },

    /**
     * Configura event listeners
     */
    setupEventListeners() {
        // Botones de agregar manual
        const btnAgregarArticulo = document.getElementById('btn-agregar-articulo-manual');
        const btnAgregarBien = document.getElementById('btn-agregar-bien-manual');

        if (btnAgregarArticulo) {
            btnAgregarArticulo.addEventListener('click', () => this.agregarArticulo());
        }

        if (btnAgregarBien) {
            btnAgregarBien.addEventListener('click', () => this.agregarBien());
        }

        // Form submit handler - usar ID específico para evitar conflictos con otros formularios
        const form = document.getElementById('form-orden-compra');
        console.log('Formulario de orden encontrado:', form);
        if (form) {
            console.log('Agregando event listener al formulario de orden');
            form.addEventListener('submit', (e) => {
                console.log('!!! EVENTO SUBMIT DISPARADO EN FORMULARIO DE ORDEN !!!');
                this.validarYEnviarFormulario(e);
            });
        } else {
            console.error('NO se encontró el formulario de orden de compra!');
        }

        // También agregar listener al botón de submit como backup
        const btnSubmit = form ? form.querySelector('button[type="submit"]') : null;
        console.log('Botón submit del formulario encontrado:', btnSubmit);
        if (btnSubmit) {
            btnSubmit.addEventListener('click', (e) => {
                console.log('!!! CLICK EN BOTÓN SUBMIT DEL FORMULARIO DE ORDEN !!!');
            });
        }

        // Event listeners para solicitudes
        const tablaDisponibles = document.getElementById('tabla-solicitudes-disponibles');
        if (tablaDisponibles) {
            tablaDisponibles.addEventListener('click', (e) => {
                const btnToggle = e.target.closest('.btn-toggle-solicitud');
                if (btnToggle) {
                    const solicitudId = btnToggle.getAttribute('data-solicitud-id');
                    const action = btnToggle.getAttribute('data-action');

                    if (action === 'agregar') {
                        this.agregarSolicitud(solicitudId);
                    } else {
                        this.quitarSolicitud(solicitudId);
                    }
                }
            });
        }
    },

    /**
     * Muestra las secciones vacías
     */
    mostrarSeccionesVacias() {
        const seccionArticulos = document.getElementById('seccion-articulos');
        const seccionBienes = document.getElementById('seccion-bienes');

        if (seccionArticulos) {
            seccionArticulos.style.display = 'block';
        }
        if (seccionBienes) {
            seccionBienes.style.display = 'block';
        }
    },

    /**
     * Agrega un artículo manualmente
     */
    agregarArticulo() {
        const tbody = document.getElementById('tbody-articulos-orden');
        if (!tbody) return;

        // Limpiar fila vacía si existe
        if (tbody.children.length === 1 && tbody.children[0].cells.length === 1) {
            tbody.innerHTML = '';
        }

        const fila = tbody.insertRow();
        fila.id = `fila_articulo_${this.contadorArticulos}`;
        const idFila = this.contadorArticulos;

        // Celda de select de artículo
        const celdaArticulo = fila.insertCell(0);
        const selectArticulo = this.crearSelectArticulo(idFila);
        celdaArticulo.appendChild(selectArticulo);

        // Celda de cantidad
        const celdaCantidad = fila.insertCell(1);
        const inputCantidad = this.crearInputCantidad(idFila, 'articulo');
        celdaCantidad.appendChild(inputCantidad);

        // Celda de precio unitario
        const celdaPrecio = fila.insertCell(2);
        const inputPrecio = this.crearInputPrecio(idFila, 'articulo');
        celdaPrecio.appendChild(inputPrecio);

        // Celda de descuento
        const celdaDescuento = fila.insertCell(3);
        const inputDescuento = this.crearInputDescuento(idFila, 'articulo');
        celdaDescuento.appendChild(inputDescuento);

        // Celda de subtotal
        const celdaSubtotal = fila.insertCell(4);
        celdaSubtotal.innerHTML = `<strong id="subtotal_articulo_${idFila}" class="text-end d-block">$0</strong>`;

        // Celda de acciones
        const celdaAcciones = fila.insertCell(5);
        const btnEliminar = this.crearBotonEliminar(idFila, 'articulo');
        celdaAcciones.appendChild(btnEliminar);

        this.contadorArticulos++;
        this.actualizarTotales();
    },

    /**
     * Agrega un bien/activo manualmente
     */
    agregarBien() {
        const tbody = document.getElementById('tbody-bienes-orden');
        if (!tbody) return;

        // Limpiar fila vacía si existe
        if (tbody.children.length === 1 && tbody.children[0].cells.length === 1) {
            tbody.innerHTML = '';
        }

        const fila = tbody.insertRow();
        fila.id = `fila_bien_${this.contadorBienes}`;
        const idFila = this.contadorBienes;

        // Celda de select de bien
        const celdaBien = fila.insertCell(0);
        const selectBien = this.crearSelectBien(idFila);
        celdaBien.appendChild(selectBien);

        // Celda de cantidad
        const celdaCantidad = fila.insertCell(1);
        const inputCantidad = this.crearInputCantidad(idFila, 'bien');
        celdaCantidad.appendChild(inputCantidad);

        // Celda de precio unitario
        const celdaPrecio = fila.insertCell(2);
        const inputPrecio = this.crearInputPrecio(idFila, 'bien');
        celdaPrecio.appendChild(inputPrecio);

        // Celda de descuento
        const celdaDescuento = fila.insertCell(3);
        const inputDescuento = this.crearInputDescuento(idFila, 'bien');
        celdaDescuento.appendChild(inputDescuento);

        // Celda de subtotal
        const celdaSubtotal = fila.insertCell(4);
        celdaSubtotal.innerHTML = `<strong id="subtotal_bien_${idFila}" class="text-end d-block">$0</strong>`;

        // Celda de acciones
        const celdaAcciones = fila.insertCell(5);
        const btnEliminar = this.crearBotonEliminar(idFila, 'bien');
        celdaAcciones.appendChild(btnEliminar);

        this.contadorBienes++;
        this.actualizarTotales();
    },

    /**
     * Crea select de artículos
     */
    crearSelectArticulo(idFila) {
        const select = document.createElement('select');
        select.className = 'form-select form-select-sm';
        select.id = `select_articulo_${idFila}`;
        select.required = true;
        select.innerHTML = '<option value="">Seleccione un artículo...</option>';

        this.articulosDisponibles.forEach(art => {
            select.innerHTML += `<option value="${art.id}"
                data-codigo="${this.escapeHtml(art.codigo)}"
                data-nombre="${this.escapeHtml(art.nombre)}"
                data-categoria="${this.escapeHtml(art.categoria)}"
                data-unidad="${this.escapeHtml(art.unidad)}">
                ${this.escapeHtml(art.codigo)} - ${this.escapeHtml(art.nombre)} (${this.escapeHtml(art.categoria)})
            </option>`;
        });

        return select;
    },

    /**
     * Crea select de bienes/activos
     */
    crearSelectBien(idFila) {
        const select = document.createElement('select');
        select.className = 'form-select form-select-sm';
        select.id = `select_bien_${idFila}`;
        select.required = true;
        select.innerHTML = '<option value="">Seleccione un bien/activo...</option>';

        this.activosDisponibles.forEach(activo => {
            select.innerHTML += `<option value="${activo.id}"
                data-codigo="${this.escapeHtml(activo.codigo)}"
                data-nombre="${this.escapeHtml(activo.nombre)}"
                data-categoria="${this.escapeHtml(activo.categoria)}">
                ${this.escapeHtml(activo.codigo)} - ${this.escapeHtml(activo.nombre)} (${this.escapeHtml(activo.categoria)})
            </option>`;
        });

        return select;
    },

    /**
     * Crea input de cantidad
     */
    crearInputCantidad(idFila, tipo) {
        const input = document.createElement('input');
        input.type = 'number';
        input.className = 'form-control form-control-sm';
        input.id = `cantidad_${tipo}_${idFila}`;
        input.step = '0.01';
        input.min = '0.01';
        input.value = '1';
        input.required = true;
        input.addEventListener('input', () => this.calcularSubtotal(idFila, tipo));
        return input;
    },

    /**
     * Crea input de precio
     */
    crearInputPrecio(idFila, tipo) {
        const input = document.createElement('input');
        input.type = 'number';
        input.className = 'form-control form-control-sm';
        input.id = `precio_${tipo}_${idFila}`;
        input.step = '0.01';
        input.min = '0';
        input.value = '0';
        input.required = true;
        input.addEventListener('input', () => this.calcularSubtotal(idFila, tipo));
        return input;
    },

    /**
     * Crea input de descuento
     */
    crearInputDescuento(idFila, tipo) {
        const input = document.createElement('input');
        input.type = 'number';
        input.className = 'form-control form-control-sm';
        input.id = `descuento_${tipo}_${idFila}`;
        input.step = '0.01';
        input.min = '0';
        input.value = '0';
        input.addEventListener('input', () => this.calcularSubtotal(idFila, tipo));
        return input;
    },

    /**
     * Crea botón de eliminar
     */
    crearBotonEliminar(idFila, tipo) {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'btn btn-sm btn-danger';
        btn.innerHTML = '<i class="ri-delete-bin-line"></i>';
        btn.addEventListener('click', () => this.eliminarFila(idFila, tipo));
        return btn;
    },

    /**
     * Calcula subtotal de una fila
     */
    calcularSubtotal(idFila, tipo) {
        const inputCantidad = document.getElementById(`cantidad_${tipo}_${idFila}`);
        const inputPrecio = document.getElementById(`precio_${tipo}_${idFila}`);
        const inputDescuento = document.getElementById(`descuento_${tipo}_${idFila}`);
        const spanSubtotal = document.getElementById(`subtotal_${tipo}_${idFila}`);

        if (!inputCantidad || !inputPrecio || !inputDescuento || !spanSubtotal) return;

        const cantidad = parseFloat(inputCantidad.value) || 0;
        const precio = parseFloat(inputPrecio.value) || 0;
        const descuento = parseFloat(inputDescuento.value) || 0;

        const subtotal = (cantidad * precio) - descuento;
        spanSubtotal.textContent = '$' + this.formatearNumero(subtotal);

        this.actualizarTotales();
    },

    /**
     * Actualiza los totales
     */
    actualizarTotales() {
        // Total artículos
        let totalArticulos = 0;
        for (let i = 0; i < this.contadorArticulos; i++) {
            const fila = document.getElementById(`fila_articulo_${i}`);
            if (fila) {
                const inputCantidad = document.getElementById(`cantidad_articulo_${i}`);
                const inputPrecio = document.getElementById(`precio_articulo_${i}`);
                const inputDescuento = document.getElementById(`descuento_articulo_${i}`);

                if (inputCantidad && inputPrecio && inputDescuento) {
                    const cantidad = parseFloat(inputCantidad.value) || 0;
                    const precio = parseFloat(inputPrecio.value) || 0;
                    const descuento = parseFloat(inputDescuento.value) || 0;
                    totalArticulos += (cantidad * precio) - descuento;
                }
            }
        }

        // Total bienes
        let totalBienes = 0;
        for (let i = 0; i < this.contadorBienes; i++) {
            const fila = document.getElementById(`fila_bien_${i}`);
            if (fila) {
                const inputCantidad = document.getElementById(`cantidad_bien_${i}`);
                const inputPrecio = document.getElementById(`precio_bien_${i}`);
                const inputDescuento = document.getElementById(`descuento_bien_${i}`);

                if (inputCantidad && inputPrecio && inputDescuento) {
                    const cantidad = parseFloat(inputCantidad.value) || 0;
                    const precio = parseFloat(inputPrecio.value) || 0;
                    const descuento = parseFloat(inputDescuento.value) || 0;
                    totalBienes += (cantidad * precio) - descuento;
                }
            }
        }

        const spanTotalArticulos = document.getElementById('total-articulos');
        const spanTotalBienes = document.getElementById('total-bienes');

        if (spanTotalArticulos) {
            spanTotalArticulos.textContent = '$' + this.formatearNumero(totalArticulos);
        }
        if (spanTotalBienes) {
            spanTotalBienes.textContent = '$' + this.formatearNumero(totalBienes);
        }
    },

    /**
     * Elimina una fila
     */
    eliminarFila(idFila, tipo) {
        if (!confirm('¿Está seguro de eliminar este item?')) return;

        const fila = document.getElementById(`fila_${tipo}_${idFila}`);
        if (fila) {
            fila.remove();
        }

        // Verificar si quedan filas
        const tbody = document.getElementById(`tbody-${tipo === 'articulo' ? 'articulos' : 'bienes'}-orden`);
        if (tbody && tbody.children.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" class="text-center text-muted">
                No hay ${tipo === 'articulo' ? 'artículos' : 'bienes'} agregados. Haga clic en "Añadir ${tipo === 'articulo' ? 'Artículo' : 'Bien/Activo'}" para comenzar.
            </td></tr>`;
        }

        this.actualizarTotales();
    },

    /**
     * Agrega una solicitud
     */
    agregarSolicitud(solicitudId) {
        if (this.solicitudesSeleccionadas.includes(solicitudId)) return;

        const fila = document.querySelector(`#tabla-solicitudes-disponibles tr[data-solicitud-id="${solicitudId}"]`);
        if (!fila) return;

        this.solicitudesSeleccionadas.push(solicitudId);
        fila.classList.add('table-success');

        const btnToggle = fila.querySelector('.btn-toggle-solicitud');
        if (btnToggle) {
            btnToggle.classList.remove('btn-success');
            btnToggle.classList.add('btn-danger');
            btnToggle.setAttribute('data-action', 'quitar');
            btnToggle.innerHTML = '<i class="ri-close-line"></i> Quitar';
        }

        this.actualizarInputsOcultos();
        this.cargarArticulosDeSolicitudes();
    },

    /**
     * Quita una solicitud
     */
    quitarSolicitud(solicitudId) {
        const index = this.solicitudesSeleccionadas.indexOf(solicitudId);
        if (index > -1) {
            this.solicitudesSeleccionadas.splice(index, 1);
        }

        const fila = document.querySelector(`#tabla-solicitudes-disponibles tr[data-solicitud-id="${solicitudId}"]`);
        if (!fila) return;

        fila.classList.remove('table-success');

        const btnToggle = fila.querySelector('.btn-toggle-solicitud');
        if (btnToggle) {
            btnToggle.classList.remove('btn-danger');
            btnToggle.classList.add('btn-success');
            btnToggle.setAttribute('data-action', 'agregar');
            btnToggle.innerHTML = '<i class="ri-add-line"></i> Agregar';
        }

        this.actualizarInputsOcultos();
        this.cargarArticulosDeSolicitudes();
    },

    /**
     * Actualiza los inputs ocultos
     */
    actualizarInputsOcultos() {
        const container = document.getElementById('solicitudes-hidden-inputs');
        if (!container) return;

        container.innerHTML = '';

        this.solicitudesSeleccionadas.forEach(solicitudId => {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'solicitudes';
            input.value = solicitudId;
            container.appendChild(input);
        });
    },

    /**
     * Carga artículos de solicitudes
     */
    async cargarArticulosDeSolicitudes() {
        if (this.solicitudesSeleccionadas.length === 0) return;

        const params = new URLSearchParams();
        this.solicitudesSeleccionadas.forEach(id => params.append('solicitudes[]', id));
        const url = '/compras/api/obtener-detalles-solicitudes/';

        try {
            const response = await fetch(`${url}?${params.toString()}`);
            const data = await response.json();
            this.procesarDetalles(data.detalles);
        } catch (error) {
            console.error('Error al cargar artículos:', error);
        }
    },

    /**
     * Procesa detalles de solicitudes
     */
    procesarDetalles(detalles) {
        detalles.forEach(detalle => {
            if (detalle.tipo === 'articulo') {
                this.agregarArticuloSolicitud(detalle);
            } else {
                this.agregarBienSolicitud(detalle);
            }
        });
    },

    /**
     * Agrega artículo desde solicitud
     */
    agregarArticuloSolicitud(detalle) {
        console.log('agregarArticuloSolicitud llamado con:', detalle);
        const tbody = document.getElementById('tbody-articulos-orden');
        if (!tbody) {
            console.error('tbody-articulos-orden no encontrado');
            return;
        }

        if (tbody.children.length === 1 && tbody.children[0].cells.length === 1) {
            tbody.innerHTML = '';
        }

        const fila = tbody.insertRow();
        fila.id = `fila_articulo_${this.contadorArticulos}`;
        const idFila = this.contadorArticulos;

        // Artículo (mostrar información + hidden input con ID)
        const celdaArticulo = fila.insertCell(0);
        const articuloInfo = document.createElement('div');
        articuloInfo.innerHTML = `
            <strong>${this.escapeHtml(detalle.codigo)} - ${this.escapeHtml(detalle.nombre)}</strong><br>
            <small class="text-muted">Categoría: ${this.escapeHtml(detalle.categoria)}</small><br>
            <small class="text-info">Desde solicitud: ${this.escapeHtml(detalle.solicitud_numero)}</small>
        `;
        celdaArticulo.appendChild(articuloInfo);

        // Hidden input para el ID del artículo
        const hiddenInput = document.createElement('input');
        hiddenInput.type = 'hidden';
        hiddenInput.id = `select_articulo_${idFila}`;
        hiddenInput.value = detalle.articulo_id;
        celdaArticulo.appendChild(hiddenInput);

        // Cantidad (input editable prellenado)
        const celdaCantidad = fila.insertCell(1);
        const inputCantidad = this.crearInputCantidad(idFila, 'articulo');
        inputCantidad.value = detalle.cantidad_aprobada;
        celdaCantidad.appendChild(inputCantidad);

        // Precio unitario (input editable prellenado)
        const celdaPrecio = fila.insertCell(2);
        const inputPrecio = this.crearInputPrecio(idFila, 'articulo');
        inputPrecio.value = detalle.precio_unitario || '0';
        celdaPrecio.appendChild(inputPrecio);

        // Descuento (input editable)
        const celdaDescuento = fila.insertCell(3);
        const inputDescuento = this.crearInputDescuento(idFila, 'articulo');
        celdaDescuento.appendChild(inputDescuento);

        // Subtotal (calculado)
        const celdaSubtotal = fila.insertCell(4);
        celdaSubtotal.innerHTML = `<strong id="subtotal_articulo_${idFila}" class="text-end d-block">$${this.formatearNumero(detalle.cantidad_aprobada * (detalle.precio_unitario || 0))}</strong>`;

        // Acciones (botón eliminar)
        const celdaAcciones = fila.insertCell(5);
        const btnEliminar = this.crearBotonEliminar(idFila, 'articulo');
        celdaAcciones.appendChild(btnEliminar);

        this.contadorArticulos++;
        console.log(`Artículo agregado. Contador ahora: ${this.contadorArticulos}, ID fila: ${idFila}, Artículo ID: ${detalle.articulo_id}`);
        this.actualizarTotales();
    },

    /**
     * Agrega bien desde solicitud
     */
    agregarBienSolicitud(detalle) {
        console.log('agregarBienSolicitud llamado con:', detalle);
        const tbody = document.getElementById('tbody-bienes-orden');
        if (!tbody) {
            console.error('tbody-bienes-orden no encontrado');
            return;
        }

        if (tbody.children.length === 1 && tbody.children[0].cells.length === 1) {
            tbody.innerHTML = '';
        }

        const fila = tbody.insertRow();
        fila.id = `fila_bien_${this.contadorBienes}`;
        const idFila = this.contadorBienes;

        // Bien (mostrar información + hidden input con ID)
        const celdaBien = fila.insertCell(0);
        const bienInfo = document.createElement('div');
        bienInfo.innerHTML = `
            <strong>${this.escapeHtml(detalle.codigo)} - ${this.escapeHtml(detalle.nombre)}</strong><br>
            <small class="text-muted">Categoría: ${this.escapeHtml(detalle.categoria)}</small><br>
            <small class="text-info">Desde solicitud: ${this.escapeHtml(detalle.solicitud_numero)}</small>
        `;
        celdaBien.appendChild(bienInfo);

        // Hidden input para el ID del bien
        const hiddenInput = document.createElement('input');
        hiddenInput.type = 'hidden';
        hiddenInput.id = `select_bien_${idFila}`;
        hiddenInput.value = detalle.activo_id;
        celdaBien.appendChild(hiddenInput);

        // Cantidad (input editable prellenado)
        const celdaCantidad = fila.insertCell(1);
        const inputCantidad = this.crearInputCantidad(idFila, 'bien');
        inputCantidad.value = detalle.cantidad_aprobada;
        celdaCantidad.appendChild(inputCantidad);

        // Precio unitario (input editable prellenado)
        const celdaPrecio = fila.insertCell(2);
        const inputPrecio = this.crearInputPrecio(idFila, 'bien');
        inputPrecio.value = detalle.precio_unitario || '0';
        celdaPrecio.appendChild(inputPrecio);

        // Descuento (input editable)
        const celdaDescuento = fila.insertCell(3);
        const inputDescuento = this.crearInputDescuento(idFila, 'bien');
        celdaDescuento.appendChild(inputDescuento);

        // Subtotal (calculado)
        const celdaSubtotal = fila.insertCell(4);
        celdaSubtotal.innerHTML = `<strong id="subtotal_bien_${idFila}" class="text-end d-block">$${this.formatearNumero(detalle.cantidad_aprobada * (detalle.precio_unitario || 0))}</strong>`;

        // Acciones (botón eliminar)
        const celdaAcciones = fila.insertCell(5);
        const btnEliminar = this.crearBotonEliminar(idFila, 'bien');
        celdaAcciones.appendChild(btnEliminar);

        this.contadorBienes++;
        console.log(`Bien agregado. Contador ahora: ${this.contadorBienes}, ID fila: ${idFila}, Activo ID: ${detalle.activo_id}`);
        this.actualizarTotales();
    },

    /**
     * Formatea un número
     */
    formatearNumero(numero) {
        const num = parseFloat(numero);
        if (isNaN(num)) return '0';
        return num.toLocaleString('es-CL', {
            minimumFractionDigits: 0,
            maximumFractionDigits: 2
        });
    },

    /**
     * Escapa HTML
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
    },

    /**
     * Valida y envía el formulario
     */
    validarYEnviarFormulario(e) {
        console.log('=== INICIANDO validarYEnviarFormulario ===');

        const articulosDetalles = [];
        const bienesDetalles = [];

        console.log('Contadores:', {
            articulos: this.contadorArticulos,
            bienes: this.contadorBienes
        });

        // Recolectar artículos
        for (let i = 0; i < this.contadorArticulos; i++) {
            console.log(`Procesando artículo ${i}`);
            const fila = document.getElementById(`fila_articulo_${i}`);
            if (!fila) {
                console.log(`Fila articulo ${i} no encontrada, continuando...`);
                continue;
            }

            // Puede ser select (manual) o hidden input (desde solicitud)
            const articuloInput = document.getElementById(`select_articulo_${i}`);
            const inputCantidad = document.getElementById(`cantidad_articulo_${i}`);
            const inputPrecio = document.getElementById(`precio_articulo_${i}`);
            const inputDescuento = document.getElementById(`descuento_articulo_${i}`);

            console.log(`Artículo ${i} - Input:`, articuloInput, 'Valor:', articuloInput?.value);
            console.log(`Artículo ${i} - Cantidad:`, inputCantidad, 'Valor:', inputCantidad?.value);
            console.log(`Artículo ${i} - Precio:`, inputPrecio, 'Valor:', inputPrecio?.value);
            console.log(`Artículo ${i} - Descuento:`, inputDescuento, 'Valor:', inputDescuento?.value);

            if (!articuloInput || !articuloInput.value) {
                e.preventDefault();
                alert('Seleccione un artículo en todas las filas.');
                return false;
            }

            if (!inputCantidad || !inputCantidad.value || parseInt(inputCantidad.value) <= 0) {
                e.preventDefault();
                alert('Ingrese una cantidad válida en todas las filas de artículos.');
                return false;
            }

            articulosDetalles.push({
                articulo_id: parseInt(articuloInput.value),
                cantidad: parseInt(inputCantidad.value),
                precio_unitario: parseFloat(inputPrecio.value) || 0,
                descuento: parseFloat(inputDescuento.value) || 0
            });
        }

        // Recolectar bienes/activos
        for (let i = 0; i < this.contadorBienes; i++) {
            console.log(`Procesando bien ${i}`);
            const fila = document.getElementById(`fila_bien_${i}`);
            if (!fila) {
                console.log(`Fila bien ${i} no encontrada, continuando...`);
                continue;
            }

            // Puede ser select (manual) o hidden input (desde solicitud)
            const bienInput = document.getElementById(`select_bien_${i}`);
            const inputCantidad = document.getElementById(`cantidad_bien_${i}`);
            const inputPrecio = document.getElementById(`precio_bien_${i}`);
            const inputDescuento = document.getElementById(`descuento_bien_${i}`);

            console.log(`Bien ${i} - Input:`, bienInput, 'Valor:', bienInput?.value);
            console.log(`Bien ${i} - Cantidad:`, inputCantidad, 'Valor:', inputCantidad?.value);
            console.log(`Bien ${i} - Precio:`, inputPrecio, 'Valor:', inputPrecio?.value);
            console.log(`Bien ${i} - Descuento:`, inputDescuento, 'Valor:', inputDescuento?.value);

            if (!bienInput || !bienInput.value) {
                e.preventDefault();
                alert('Seleccione un bien/activo en todas las filas.');
                return false;
            }

            if (!inputCantidad || !inputCantidad.value || parseInt(inputCantidad.value) <= 0) {
                e.preventDefault();
                alert('Ingrese una cantidad válida en todas las filas de bienes.');
                return false;
            }

            bienesDetalles.push({
                activo_id: parseInt(bienInput.value),
                cantidad: parseInt(inputCantidad.value),
                precio_unitario: parseFloat(inputPrecio.value) || 0,
                descuento: parseFloat(inputDescuento.value) || 0
            });
        }

        // Guardar JSON en campos ocultos
        const articulosInput = document.getElementById('articulosJson');
        const bienesInput = document.getElementById('bienesJson');

        if (articulosInput) {
            articulosInput.value = JSON.stringify(articulosDetalles);
            console.log('Artículos JSON:', articulosInput.value);
        }

        if (bienesInput) {
            bienesInput.value = JSON.stringify(bienesDetalles);
            console.log('Bienes JSON:', bienesInput.value);
        }

        console.log('Total artículos:', articulosDetalles.length);
        console.log('Total bienes:', bienesDetalles.length);
        console.log('Artículos:', articulosDetalles);
        console.log('Bienes:', bienesDetalles);

        // NO llamar a e.target.submit() porque esto omite las validaciones
        // Simplemente dejamos que el evento submit continúe normalmente
        // Los campos ocultos ya están llenos con los datos
        console.log('=== Formulario listo para enviar, permitiendo submit normal ===');
        return true;
    }
};

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    if (typeof ARTICULOS_DISPONIBLES !== 'undefined' && typeof ACTIVOS_DISPONIBLES !== 'undefined') {
        OrdenCompra.init(ARTICULOS_DISPONIBLES, ACTIVOS_DISPONIBLES);
    } else {
        console.error('Datos de artículos/activos no disponibles');
    }
});

// Exportar para uso global
window.OrdenCompra = OrdenCompra;
