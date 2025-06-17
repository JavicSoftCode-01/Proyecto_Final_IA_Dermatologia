/**
 * JavaScript para la gestión de la lista de pacientes
 */

class PatientListManager {
    constructor() {
        this.initializeElements();
        this.setupEventListeners();
        this.initializeModals();
    }

    initializeElements() {
        this.searchInput = document.querySelector('.search-input');
        this.searchForm = document.querySelector('.search-form');
        this.patientsTable = document.querySelector('.patients-table');
        this.modals = document.querySelectorAll('.modal');
        this.viewButtons = document.querySelectorAll('.btn-view');
    }

    setupEventListeners() {
        // Búsqueda en tiempo real
        if (this.searchInput) {
            this.searchInput.addEventListener('input', (e) => {
                this.handleSearchInput(e);
            });
        }

        // Envío del formulario de búsqueda
        if (this.searchForm) {
            this.searchForm.addEventListener('submit', (e) => {
                this.handleSearchSubmit(e);
            });
        }

        // Botones de acción en la tabla
        if (this.patientsTable) {
            this.patientsTable.addEventListener('click', (e) => {
                this.handleTableActions(e);
            });
        }

        // Botones "Ver" específicos
        this.viewButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                this.handleViewPatient(button);
            });
        });

        // Escape para cerrar modales
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeAllModals();
            }
        });
    }

    handleSearchInput(e) {
        const value = e.target.value;

        // Validar que solo sean números
        if (value && !/^\d*$/.test(value)) {
            e.target.value = value.replace(/\D/g, '');
        }

        // Limitar a 10 caracteres
        if (e.target.value.length > 10) {
            e.target.value = e.target.value.slice(0, 10);
        }
    }

    handleSearchSubmit(e) {
        const searchValue = this.searchInput.value.trim();

        if (searchValue && searchValue.length < 3) {
            e.preventDefault();
            this.showAlert('La búsqueda debe tener al menos 3 caracteres', 'warning');
        }
    }

    handleTableActions(e) {
        const target = e.target.closest('.btn-action');
        if (!target) return;

        if (target.classList.contains('btn-view')) {
            e.preventDefault();
            this.handleViewPatient(target);
        } else if (target.classList.contains('btn-edit')) {
            this.handleEditPatient(target);
        }
    }

    handleViewPatient(button) {
        const patientId = button.dataset.patientId;
        const modalId = `patientModal${patientId}`;
        const modal = document.getElementById(modalId);

        console.log('Intentando abrir modal:', modalId);
        console.log('Modal encontrado:', modal);

        if (modal) {
            // Crear backdrop manualmente
            const backdrop = document.createElement('div');
            backdrop.className = 'modal-backdrop fade show';
            backdrop.style.zIndex = '1040';
            document.body.appendChild(backdrop);

            // Mostrar modal
            modal.style.display = 'block';
            modal.style.zIndex = '1050';
            modal.classList.add('show');
            document.body.classList.add('modal-open');

            // Configurar cierre del modal
            this.setupModalClose(modal, backdrop);
        } else {
            console.error('Modal no encontrado:', modalId);
            this.showAlert('Error al mostrar los detalles del paciente', 'error');
        }
    }

    setupModalClose(modal, backdrop) {
        const closeModal = () => {
            modal.style.display = 'none';
            modal.classList.remove('show');
            document.body.classList.remove('modal-open');
            if (backdrop && backdrop.parentNode) {
                backdrop.parentNode.removeChild(backdrop);
            }
        };

        // Botón de cerrar
        const closeButtons = modal.querySelectorAll('.btn-close, [data-bs-dismiss="modal"]');
        closeButtons.forEach(btn => {
            btn.addEventListener('click', closeModal);
        });

        // Click en backdrop
        backdrop.addEventListener('click', closeModal);

        // Click fuera del modal
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeModal();
            }
        });

        // Tecla Escape
        const escapeHandler = (e) => {
            if (e.key === 'Escape') {
                closeModal();
                document.removeEventListener('keydown', escapeHandler);
            }
        };
        document.addEventListener('keydown', escapeHandler);
    }

    handleEditPatient(button) {
        const editUrl = button.href;
        if (editUrl) {
            window.location.href = editUrl;
        }
    }

    initializeModals() {
        // Este método ya no es necesario con el nuevo enfoque
        console.log('Modales encontrados:', this.modals.length);
    }

    closeAllModals() {
        // Cerrar todos los modales abiertos
        const openModals = document.querySelectorAll('.modal.show');
        const backdrops = document.querySelectorAll('.modal-backdrop');

        openModals.forEach(modal => {
            modal.style.display = 'none';
            modal.classList.remove('show');
        });

        backdrops.forEach(backdrop => {
            if (backdrop.parentNode) {
                backdrop.parentNode.removeChild(backdrop);
            }
        });

        document.body.classList.remove('modal-open');
    }

    showAlert(message, type = 'info') {
        // Crear alerta temporal
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show`;
        alert.style.position = 'fixed';
        alert.style.top = '20px';
        alert.style.right = '20px';
        alert.style.zIndex = '9999';
        alert.style.minWidth = '300px';
        alert.style.padding = '12px 16px';
        alert.style.borderRadius = '8px';
        alert.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';

        // Colores según tipo
        const colors = {
            'success': { bg: '#d1fae5', border: '#10b981', text: '#065f46' },
            'warning': { bg: '#fef3c7', border: '#f59e0b', text: '#92400e' },
            'error': { bg: '#fee2e2', border: '#ef4444', text: '#991b1b' },
            'info': { bg: '#dbeafe', border: '#3b82f6', text: '#1e40af' }
        };

        const color = colors[type] || colors.info;
        alert.style.backgroundColor = color.bg;
        alert.style.borderLeft = `4px solid ${color.border}`;
        alert.style.color = color.text;

        alert.innerHTML = `
            <div style="display: flex; align-items: center; gap: 8px;">
                <i class="fas fa-${this.getAlertIcon(type)}"></i>
                <span>${message}</span>
                <button type="button" style="background: none; border: none; color: ${color.text}; cursor: pointer; margin-left: auto; font-size: 18px;" aria-label="Close">&times;</button>
            </div>
        `;

        document.body.appendChild(alert);

        // Configurar cierre automático
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 5000);

        // Configurar cierre manual
        const closeBtn = alert.querySelector('button');
        closeBtn.addEventListener('click', () => {
            alert.remove();
        });
    }

    getAlertIcon(type) {
        const icons = {
            'success': 'check-circle',
            'warning': 'exclamation-triangle',
            'error': 'exclamation-circle',
            'info': 'info-circle'
        };
        return icons[type] || 'info-circle';
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    console.log('Inicializando PatientListManager...');

    const manager = new PatientListManager();
    console.log('PatientListManager inicializado correctamente');
});