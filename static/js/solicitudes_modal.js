(function(){
    'use strict';

        function ensureModalContainer(){
                if(document.getElementById('solicitudModal')) return;
                const container = document.createElement('div');
                container.innerHTML = `
                <div class="modal fade" id="solicitudModal" tabindex="-1" aria-hidden="true">
                    <div class="modal-dialog modal-xl modal-dialog-centered modal-dialog-scrollable">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title" id="solicitudModalLabel">Detalle</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                            </div>
                            <div class="modal-body" id="solicitudModalBody">
                                <!-- Contenido cargado por AJAX -->
                            </div>
                        </div>
                    </div>
                </div>`;
                document.body.appendChild(container);
        }

    // Delegar clicks en enlaces con clase .solicitudes-modal-link
    document.addEventListener('click', function(ev){
        const a = ev.target.closest('a.solicitudes-modal-link');
        if(!a) return;
        ev.preventDefault();

        // Construir URL y forzar modal=1 para que la vista devuelva parcial
        try {
            const url = new URL(a.href, window.location.origin);
            url.searchParams.set('modal','1');

            // Asegurar que exista el contenedor del modal; si no, crearlo dinámicamente
            ensureModalContainer();

            const modalEl = document.getElementById('solicitudModal');
            const modalBody = document.getElementById('solicitudModalBody');
            const modalTitle = document.getElementById('solicitudModalLabel');
            if(modalTitle && a.dataset.modalTitle) modalTitle.textContent = a.dataset.modalTitle;

            fetch(url.toString(), { headers: {'X-Requested-With': 'XMLHttpRequest'} })
                .then(resp => resp.text())
                .then(html => {
                    modalBody.innerHTML = html;
                    // Inicializar comportamientos dentro del modal
                    initModalBindings(modalBody);
                    // Mostrar modal usando Bootstrap 5
                    const bsModal = new bootstrap.Modal(modalEl);
                    bsModal.show();
                })
                .catch(err => {
                    console.error('Error cargando modal:', err);
                });
        } catch(e) {
            console.error('URL inválida', e);
        }
    });

    // Inicializa bindings para formularios y botones dentro del modal
    function initModalBindings(root){
        if(!root) return;

        // Manejar submits de TODOS los formularios en el modal
        root.querySelectorAll('form').forEach(function(form){
            form.addEventListener('submit', function(ev){
                ev.preventDefault();
                submitFormViaAjax(form, root);
            });
        });

        // Botón para agregar filas al formset
        // Definir addFormRow y toggleSeccionActividad localmente para evitar mezclar JS en plantillas
        window.addFormRow = function(){
            const tbody = root.querySelector('#detalles-tbody');
            const totalForms = root.querySelector('#id_detalles-TOTAL_FORMS') || document.querySelector('#id_detalles-TOTAL_FORMS');
            if(!tbody || !totalForms) return;
            const formIdx = parseInt(totalForms.value);
            const lastRow = tbody.querySelector('.detalle-row:last-child');
            if(!lastRow) return;
            const newRow = lastRow.cloneNode(true);
            const html = newRow.innerHTML.replace(/detalles-(\d+)-/g, `detalles-${formIdx}-`);
            newRow.innerHTML = html;
            // Limpiar valores
            newRow.querySelectorAll('input, select, textarea').forEach(field => {
                if(field.type === 'checkbox' || field.type === 'radio') field.checked = false;
                else if(field.tagName === 'SELECT') field.selectedIndex = 0;
                else if(field.name && !field.name.includes('id')) field.value = '';
            });
            tbody.appendChild(newRow);
            totalForms.value = formIdx + 1;
        };

        window.toggleSeccionActividad = function(){
            const tipoSolicitudSelect = root.querySelector('select[name="tipo_solicitud"]') || document.querySelector('select[name="tipo_solicitud"]');
            const seccionActividad = root.querySelector('#seccion-actividad');
            if(!tipoSolicitudSelect || !seccionActividad) return;
            const selectedOption = tipoSolicitudSelect.options[tipoSolicitudSelect.selectedIndex];
            const selectedText = selectedOption ? selectedOption.text.toLowerCase() : '';
            if(selectedText.includes('materiales')) seccionActividad.style.display = '';
            else seccionActividad.style.display = 'none';
        };

        // Vincular cambio de tipo de solicitud
        const tipoSelect = root.querySelector('select[name="tipo_solicitud"]');
        if(tipoSelect){
            tipoSelect.addEventListener('change', function(){ window.toggleSeccionActividad(); });
            // Ejecutar inicial
            window.toggleSeccionActividad();
        }

        // Si hay botones dentro del modal que abren otros modales (editar dentro del detalle), vincularlos
        root.querySelectorAll('a.solicitudes-modal-link').forEach(a => {
            a.addEventListener('click', function(ev){
                ev.preventDefault();
                a.click(); // reusar el delegado global
            });
        });
    }

    function submitFormViaAjax(form, root){
        const action = form.getAttribute('action') || window.location.href;
        const method = (form.getAttribute('method') || 'POST').toUpperCase();
        const formData = new FormData(form);

        fetch(action + (action.includes('?') ? '&' : '?') + 'modal=1', {
            method: method,
            headers: {'X-Requested-With': 'XMLHttpRequest'},
            body: formData
        })
        .then(resp => resp.text())
        .then(html => {
            // Reemplazar el contenido del modal con la respuesta (que puede ser formulario con errores o detalle actualizado)
            const modalBody = document.getElementById('solicitudModalBody');
            if(modalBody){
                modalBody.innerHTML = html;
                initModalBindings(modalBody);
            }
            // Si la respuesta contiene elementos que indiquen éxito, podríamos cerrar el modal y refrescar la lista.
            // Para mantener simpleza: si el HTML no contiene "form" asumimos que es vista de detalle -> refrescar lista
            if(!html.includes('<form')){
                // Cerrar modal y refrescar la página para ver cambios
                const modalEl = document.getElementById('solicitudModal');
                const bsModal = bootstrap.Modal.getInstance(modalEl);
                if(bsModal) bsModal.hide();
                // Refrescar la lista (o recargar la página)
                window.location.reload();
            }
        })
        .catch(err => {
            console.error('Error enviando formulario:', err);
        });
    }

})();
