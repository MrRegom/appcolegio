/**
 * Módulo para creación de órdenes de compra
 * Refactorizado siguiendo principios SOLID y Clean Code
 *
 * Responsabilidades separadas:
 * - FormValidator: Validación de datos
 * - DataCollector: Recolección de datos de tablas
 * - RowBuilder: Construcción de filas HTML
 * - TotalesCalculator: Cálculos de totales
 * - APIClient: Comunicación con backend
 * - OrdenCompraController: Coordinador principal
 */

// =============================================================================
// UTILIDADES
// =============================================================================

class DOMUtils {
    /**
     * Escapa HTML para prevenir XSS
     */
    static escapeHtml(text) {
        if (!text) return '';
        return String(text)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    /**
     * Formatea números con separadores de miles
     */
    static formatNumber(num) {
        return new Intl.NumberFormat('es-CL').format(num || 0);
    }
}

// =============================================================================
// VALIDACIÓN
// =============================================================================

class FormValidator {
    /**
     * Valida un artículo individual
     */
    static validateArticulo(index) {
        const articuloInput = document.getElementById(`select_articulo_${index}`);
        const inputCantidad = document.getElementById(`cantidad_articulo_${index}`);

        if (!articuloInput || !articuloInput.value) {
            alert('Seleccione un artículo en todas las filas.');
            return false;
        }

        if (!inputCantidad || !inputCantidad.value || parseInt(inputCantidad.value) <= 0) {
            alert('Ingrese una cantidad válida en todas las filas de artículos.');
            return false;
        }

        return true;
    }

    /**
     * Valida un bien individual
     */
    static validateBien(index) {
        const bienInput = document.getElementById(`select_bien_${index}`);
        const inputCantidad = document.getElementById(`cantidad_bien_${index}`);

        if (!bienInput || !bienInput.value) {
            alert('Seleccione un bien/activo en todas las filas.');
            return false;
        }

        if (!inputCantidad || !inputCantidad.value || parseInt(inputCantidad.value) <= 0) {
            alert('Ingrese una cantidad válida en todas las filas de bienes.');
            return false;
        }

        return true;
    }
}

// =============================================================================
// RECOLECCIÓN DE DATOS
// =============================================================================

class DataCollector {
    /**
     * Recolecta datos de un artículo
     */
    static collectArticuloData(index) {
        const articuloInput = document.getElementById(`select_articulo_${index}`);
        const inputCantidad = document.getElementById(`cantidad_articulo_${index}`);
        const inputPrecio = document.getElementById(`precio_articulo_${index}`);
        const inputDescuento = document.getElementById(`descuento_articulo_${index}`);

        return {
            articulo_id: parseInt(articuloInput.value),
            cantidad: parseInt(inputCantidad.value),
            precio_unitario: parseFloat(inputPrecio.value) || 0,
            descuento: parseFloat(inputDescuento.value) || 0
        };
    }

    /**
     * Recolecta datos de un bien
     */
    static collectBienData(index) {
        const bienInput = document.getElementById(`select_bien_${index}`);
        const inputCantidad = document.getElementById(`cantidad_bien_${index}`);
        const inputPrecio = document.getElementById(`precio_bien_${index}`);
        const inputDescuento = document.getElementById(`descuento_bien_${index}`);

        return {
            activo_id: parseInt(bienInput.value),
            cantidad: parseInt(inputCantidad.value),
            precio_unitario: parseFloat(inputPrecio.value) || 0,
            descuento: parseFloat(inputDescuento.value) || 0
        };
    }

    /**
     * Recolecta todos los artículos del formulario
     */
    static collectAllArticulos(contador) {
        const articulos = [];

        for (let i = 0; i < contador; i++) {
            const fila = document.getElementById(`fila_articulo_${i}`);
            if (!fila) continue;

            if (!FormValidator.validateArticulo(i)) {
                throw new Error('Validación de artículo fallida');
            }

            articulos.push(this.collectArticuloData(i));
        }

        return articulos;
    }

    /**
     * Recolecta todos los bienes del formulario
     */
    static collectAllBienes(contador) {
        const bienes = [];

        for (let i = 0; i < contador; i++) {
            const fila = document.getElementById(`fila_bien_${i}`);
            if (!fila) continue;

            if (!FormValidator.validateBien(i)) {
                throw new Error('Validación de bien fallida');
            }

            bienes.push(this.collectBienData(i));
        }

        return bienes;
    }
}

// =============================================================================
// CÁLCULO DE TOTALES
// =============================================================================

class TotalesCalculator {
    /**
     * Calcula el subtotal de un item
     */
    static calculateSubtotal(cantidad, precioUnitario, descuento = 0) {
        return (cantidad * precioUnitario) - descuento;
    }

    /**
     * Actualiza el subtotal de un artículo en el DOM
     */
    static updateArticuloSubtotal(index) {
        const cantidad = parseFloat(document.getElementById(`cantidad_articulo_${index}`)?.value) || 0;
        const precio = parseFloat(document.getElementById(`precio_articulo_${index}`)?.value) || 0;
        const descuento = parseFloat(document.getElementById(`descuento_articulo_${index}`)?.value) || 0;

        const subtotal = this.calculateSubtotal(cantidad, precio, descuento);
        const subtotalElement = document.getElementById(`subtotal_articulo_${index}`);

        if (subtotalElement) {
            subtotalElement.textContent = `$${DOMUtils.formatNumber(subtotal)}`;
        }

        return subtotal;
    }

    /**
     * Actualiza el subtotal de un bien en el DOM
     */
    static updateBienSubtotal(index) {
        const cantidad = parseFloat(document.getElementById(`cantidad_bien_${index}`)?.value) || 0;
        const precio = parseFloat(document.getElementById(`precio_bien_${index}`)?.value) || 0;
        const descuento = parseFloat(document.getElementById(`descuento_bien_${index}`)?.value) || 0;

        const subtotal = this.calculateSubtotal(cantidad, precio, descuento);
        const subtotalElement = document.getElementById(`subtotal_bien_${index}`);

        if (subtotalElement) {
            subtotalElement.textContent = `$${DOMUtils.formatNumber(subtotal)}`;
        }

        return subtotal;
    }

    /**
     * Calcula y actualiza todos los totales
     */
    static updateAllTotales(contadorArticulos, contadorBienes) {
        let totalArticulos = 0;
        let totalBienes = 0;

        // Sumar artículos
        for (let i = 0; i < contadorArticulos; i++) {
            if (document.getElementById(`fila_articulo_${i}`)) {
                totalArticulos += this.updateArticuloSubtotal(i);
            }
        }

        // Sumar bienes
        for (let i = 0; i < contadorBienes; i++) {
            if (document.getElementById(`fila_bien_${i}`)) {
                totalBienes += this.updateBienSubtotal(i);
            }
        }

        const totalGeneral = totalArticulos + totalBienes;

        // Actualizar DOM
        const totalArticulosElement = document.getElementById('total-articulos');
        const totalBienesElement = document.getElementById('total-bienes');
        const totalGeneralElement = document.getElementById('total-general');

        if (totalArticulosElement) {
            totalArticulosElement.textContent = `$${DOMUtils.formatNumber(totalArticulos)}`;
        }
        if (totalBienesElement) {
            totalBienesElement.textContent = `$${DOMUtils.formatNumber(totalBienes)}`;
        }
        if (totalGeneralElement) {
            totalGeneralElement.textContent = `$${DOMUtils.formatNumber(totalGeneral)}`;
        }

        return { totalArticulos, totalBienes, totalGeneral };
    }
}

// =============================================================================
// CONSTRUCCIÓN DE FILAS (UI)
// =============================================================================

class InputBuilder {
    /**
     * Crea input de cantidad
     */
    static createCantidadInput(index, tipo, initialValue = '') {
        const input = document.createElement('input');
        input.type = 'number';
        input.id = `cantidad_${tipo}_${index}`;
        input.className = 'form-control form-control-sm';
        input.min = '1';
        input.step = '1';
        input.value = initialValue;
        input.required = true;
        return input;
    }

    /**
     * Crea input de precio
     */
    static createPrecioInput(index, tipo, initialValue = '0') {
        const input = document.createElement('input');
        input.type = 'number';
        input.id = `precio_${tipo}_${index}`;
        input.className = 'form-control form-control-sm';
        input.min = '0';
        input.step = '0.01';
        input.value = initialValue;
        return input;
    }

    /**
     * Crea input de descuento
     */
    static createDescuentoInput(index, tipo) {
        const input = document.createElement('input');
        input.type = 'number';
        input.id = `descuento_${tipo}_${index}`;
        input.className = 'form-control form-control-sm';
        input.min = '0';
        input.step = '0.01';
        input.value = '0';
        return input;
    }

    /**
     * Crea botón eliminar
     */
    static createEliminarButton(index, tipo, onClickHandler) {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'btn btn-sm btn-danger';
        btn.innerHTML = '<i class="ri-delete-bin-line"></i>';
        btn.onclick = () => onClickHandler(index, tipo);
        return btn;
    }
}

class ArticuloRowBuilder {
    /**
     * Construye una fila de artículo
     */
    static buildRow(detalle, index, onDelete, onInputChange) {
        const fila = document.createElement('tr');
        fila.id = `fila_articulo_${index}`;

        // Columna: Artículo
        const celdaArticulo = document.createElement('td');
        celdaArticulo.innerHTML = `
            <strong>${DOMUtils.escapeHtml(detalle.codigo)} - ${DOMUtils.escapeHtml(detalle.nombre)}</strong><br>
            <small class="text-muted">Categoría: ${DOMUtils.escapeHtml(detalle.categoria)}</small><br>
            <small class="text-info">Desde solicitud: ${DOMUtils.escapeHtml(detalle.solicitud_numero)}</small>
        `;

        // Hidden input para el ID
        const hiddenInput = document.createElement('input');
        hiddenInput.type = 'hidden';
        hiddenInput.id = `select_articulo_${index}`;
        hiddenInput.value = detalle.articulo_id;
        celdaArticulo.appendChild(hiddenInput);

        // Columna: Cantidad
        const celdaCantidad = document.createElement('td');
        const inputCantidad = InputBuilder.createCantidadInput(index, 'articulo', detalle.cantidad_aprobada);
        inputCantidad.addEventListener('input', onInputChange);
        celdaCantidad.appendChild(inputCantidad);

        // Columna: Precio
        const celdaPrecio = document.createElement('td');
        const inputPrecio = InputBuilder.createPrecioInput(index, 'articulo', detalle.precio_unitario || '0');
        inputPrecio.addEventListener('input', onInputChange);
        celdaPrecio.appendChild(inputPrecio);

        // Columna: Descuento
        const celdaDescuento = document.createElement('td');
        const inputDescuento = InputBuilder.createDescuentoInput(index, 'articulo');
        inputDescuento.addEventListener('input', onInputChange);
        celdaDescuento.appendChild(inputDescuento);

        // Columna: Subtotal
        const celdaSubtotal = document.createElement('td');
        const subtotal = TotalesCalculator.calculateSubtotal(
            parseFloat(detalle.cantidad_aprobada),
            parseFloat(detalle.precio_unitario || 0)
        );
        celdaSubtotal.innerHTML = `<strong id="subtotal_articulo_${index}" class="text-end d-block">$${DOMUtils.formatNumber(subtotal)}</strong>`;

        // Columna: Acciones
        const celdaAcciones = document.createElement('td');
        const btnEliminar = InputBuilder.createEliminarButton(index, 'articulo', onDelete);
        celdaAcciones.appendChild(btnEliminar);

        // Agregar todas las celdas
        fila.appendChild(celdaArticulo);
        fila.appendChild(celdaCantidad);
        fila.appendChild(celdaPrecio);
        fila.appendChild(celdaDescuento);
        fila.appendChild(celdaSubtotal);
        fila.appendChild(celdaAcciones);

        return fila;
    }
}

class BienRowBuilder {
    /**
     * Construye una fila de bien/activo
     */
    static buildRow(detalle, index, onDelete, onInputChange) {
        const fila = document.createElement('tr');
        fila.id = `fila_bien_${index}`;

        // Columna: Bien
        const celdaBien = document.createElement('td');
        celdaBien.innerHTML = `
            <strong>${DOMUtils.escapeHtml(detalle.codigo)} - ${DOMUtils.escapeHtml(detalle.nombre)}</strong><br>
            <small class="text-muted">Categoría: ${DOMUtils.escapeHtml(detalle.categoria)}</small><br>
            <small class="text-info">Desde solicitud: ${DOMUtils.escapeHtml(detalle.solicitud_numero)}</small>
        `;

        // Hidden input para el ID
        const hiddenInput = document.createElement('input');
        hiddenInput.type = 'hidden';
        hiddenInput.id = `select_bien_${index}`;
        hiddenInput.value = detalle.activo_id;
        celdaBien.appendChild(hiddenInput);

        // Columna: Cantidad
        const celdaCantidad = document.createElement('td');
        const inputCantidad = InputBuilder.createCantidadInput(index, 'bien', detalle.cantidad_aprobada);
        inputCantidad.addEventListener('input', onInputChange);
        celdaCantidad.appendChild(inputCantidad);

        // Columna: Precio
        const celdaPrecio = document.createElement('td');
        const inputPrecio = InputBuilder.createPrecioInput(index, 'bien', detalle.precio_unitario || '0');
        inputPrecio.addEventListener('input', onInputChange);
        celdaPrecio.appendChild(inputPrecio);

        // Columna: Descuento
        const celdaDescuento = document.createElement('td');
        const inputDescuento = InputBuilder.createDescuentoInput(index, 'bien');
        inputDescuento.addEventListener('input', onInputChange);
        celdaDescuento.appendChild(inputDescuento);

        // Columna: Subtotal
        const celdaSubtotal = document.createElement('td');
        const subtotal = TotalesCalculator.calculateSubtotal(
            parseFloat(detalle.cantidad_aprobada),
            parseFloat(detalle.precio_unitario || 0)
        );
        celdaSubtotal.innerHTML = `<strong id="subtotal_bien_${index}" class="text-end d-block">$${DOMUtils.formatNumber(subtotal)}</strong>`;

        // Columna: Acciones
        const celdaAcciones = document.createElement('td');
        const btnEliminar = InputBuilder.createEliminarButton(index, 'bien', onDelete);
        celdaAcciones.appendChild(btnEliminar);

        // Agregar todas las celdas
        fila.appendChild(celdaBien);
        fila.appendChild(celdaCantidad);
        fila.appendChild(celdaPrecio);
        fila.appendChild(celdaDescuento);
        fila.appendChild(celdaSubtotal);
        fila.appendChild(celdaAcciones);

        return fila;
    }
}

// =============================================================================
// CLIENTE API
// =============================================================================

class APIClient {
    /**
     * Obtiene detalles de solicitudes
     */
    static async fetchDetallesSolicitudes(solicitudIds) {
        if (solicitudIds.length === 0) return [];

        const params = new URLSearchParams();
        solicitudIds.forEach(id => params.append('solicitudes[]', id));
        const url = `/compras/api/obtener-detalles-solicitudes/?${params.toString()}`;

        try {
            const response = await fetch(url);
            const data = await response.json();
            return data.detalles || [];
        } catch (error) {
            console.error('Error al cargar detalles de solicitudes:', error);
            throw error;
        }
    }
}

// =============================================================================
// CONTROLADOR PRINCIPAL
// =============================================================================

class OrdenCompraController {
    constructor(articulos, activos) {
        this.articulosDisponibles = articulos;
        this.activosDisponibles = activos;
        this.solicitudesSeleccionadas = [];
        this.contadorArticulos = 0;
        this.contadorBienes = 0;

        this.init();
    }

    init() {
        this.setupEventListeners();
        console.log('OrdenCompraController inicializado correctamente');
    }

    setupEventListeners() {
        // Formulario principal
        const form = document.getElementById('form-orden-compra');
        if (form) {
            form.addEventListener('submit', (e) => this.handleFormSubmit(e));
            console.log('Event listener agregado al formulario de orden');
        }

        // Tabla de solicitudes
        const tablaSolicitudes = document.getElementById('tabla-solicitudes-disponibles');
        if (tablaSolicitudes) {
            tablaSolicitudes.addEventListener('click', (e) => this.handleSolicitudClick(e));
        }
    }

    handleSolicitudClick(event) {
        const btnToggle = event.target.closest('.btn-toggle-solicitud');
        if (!btnToggle) return;

        const solicitudId = btnToggle.getAttribute('data-solicitud-id');
        const action = btnToggle.getAttribute('data-action');

        if (action === 'agregar') {
            this.agregarSolicitud(solicitudId);
        } else {
            this.quitarSolicitud(solicitudId);
        }
    }

    async agregarSolicitud(solicitudId) {
        if (this.solicitudesSeleccionadas.includes(solicitudId)) return;

        this.solicitudesSeleccionadas.push(solicitudId);
        await this.cargarArticulosDeSolicitudes();
    }

    quitarSolicitud(solicitudId) {
        const index = this.solicitudesSeleccionadas.indexOf(solicitudId);
        if (index > -1) {
            this.solicitudesSeleccionadas.splice(index, 1);
        }
    }

    async cargarArticulosDeSolicitudes() {
        try {
            const detalles = await APIClient.fetchDetallesSolicitudes(this.solicitudesSeleccionadas);
            this.procesarDetalles(detalles);
        } catch (error) {
            console.error('Error al procesar solicitudes:', error);
            alert('Error al cargar los detalles de las solicitudes');
        }
    }

    procesarDetalles(detalles) {
        detalles.forEach(detalle => {
            if (detalle.tipo === 'articulo') {
                this.agregarArticuloSolicitud(detalle);
            } else {
                this.agregarBienSolicitud(detalle);
            }
        });
    }

    agregarArticuloSolicitud(detalle) {
        const tbody = document.getElementById('tbody-articulos-orden');
        if (!tbody) return;

        // Limpiar mensaje "vacío" si existe
        if (tbody.children.length === 1 && tbody.children[0].cells.length === 1) {
            tbody.innerHTML = '';
        }

        const fila = ArticuloRowBuilder.buildRow(
            detalle,
            this.contadorArticulos,
            (index) => this.eliminarFila(index, 'articulo'),
            () => this.actualizarTotales()
        );

        tbody.appendChild(fila);
        this.contadorArticulos++;
        this.actualizarTotales();
    }

    agregarBienSolicitud(detalle) {
        const tbody = document.getElementById('tbody-bienes-orden');
        if (!tbody) return;

        // Limpiar mensaje "vacío" si existe
        if (tbody.children.length === 1 && tbody.children[0].cells.length === 1) {
            tbody.innerHTML = '';
        }

        const fila = BienRowBuilder.buildRow(
            detalle,
            this.contadorBienes,
            (index) => this.eliminarFila(index, 'bien'),
            () => this.actualizarTotales()
        );

        tbody.appendChild(fila);
        this.contadorBienes++;
        this.actualizarTotales();
    }

    eliminarFila(index, tipo) {
        const fila = document.getElementById(`fila_${tipo}_${index}`);
        if (fila) {
            fila.remove();
            this.actualizarTotales();
        }
    }

    actualizarTotales() {
        TotalesCalculator.updateAllTotales(this.contadorArticulos, this.contadorBienes);
    }

    handleFormSubmit(event) {
        console.log('=== INICIANDO validación y envío del formulario ===');

        try {
            // Recolectar datos
            const articulos = DataCollector.collectAllArticulos(this.contadorArticulos);
            const bienes = DataCollector.collectAllBienes(this.contadorBienes);

            // Guardar en campos ocultos
            this.saveToHiddenFields(articulos, bienes);

            console.log('Artículos:', articulos);
            console.log('Bienes:', bienes);
            console.log('=== Formulario listo para enviar ===');

            // Permitir que el formulario se envíe normalmente
            return true;

        } catch (error) {
            // Si hay error de validación, prevenir el envío
            event.preventDefault();
            console.error('Error en validación:', error);
            return false;
        }
    }

    saveToHiddenFields(articulos, bienes) {
        const articulosInput = document.getElementById('articulosJson');
        const bienesInput = document.getElementById('bienesJson');

        if (articulosInput) {
            articulosInput.value = JSON.stringify(articulos);
            console.log('Artículos JSON guardado:', articulosInput.value);
        }

        if (bienesInput) {
            bienesInput.value = JSON.stringify(bienes);
            console.log('Bienes JSON guardado:', bienesInput.value);
        }
    }
}

// =============================================================================
// INICIALIZACIÓN
// =============================================================================

document.addEventListener('DOMContentLoaded', function() {
    if (typeof ARTICULOS_DISPONIBLES !== 'undefined' && typeof ACTIVOS_DISPONIBLES !== 'undefined') {
        window.ordenCompraController = new OrdenCompraController(
            ARTICULOS_DISPONIBLES,
            ACTIVOS_DISPONIBLES
        );
    } else {
        console.error('Datos de artículos/activos no disponibles');
    }
});
