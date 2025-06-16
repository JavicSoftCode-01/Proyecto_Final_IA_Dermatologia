/**
 * Funcionalidad para la página de lista de reportes
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Inicializando ReportListManager...');
    
    // Inicializar funcionalidades
    initializeEmailModals();
    initializeFormValidation();
    initializeButtonHandlers();
    animateCards();
});

/**
 * Inicializa los modales de email
 */
function initializeEmailModals() {
    // Configurar eventos para todos los botones de email
    const emailButtons = document.querySelectorAll('[data-bs-target^="#emailModal"]');
    console.log(`Encontrados ${emailButtons.length} botones de email`);
    
    emailButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            console.log('Botón de email clickeado:', this.getAttribute('data-bs-target'));
            const modalId = this.getAttribute('data-bs-target');
            const modal = document.querySelector(modalId);
            
            if (modal) {
                prepareEmailModal(modal, this);
            } else {
                console.error('Modal no encontrado:', modalId);
            }
        });
    });

    // Configurar eventos de envío de formularios
    const emailForms = document.querySelectorAll('.email-form');
    console.log(`Encontrados ${emailForms.length} formularios de email`);
    
    emailForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            return handleEmailSubmit(e, this);
        });
    });
}

/**
 * Prepara el modal de email con la información del reporte
 */
function prepareEmailModal(modal, triggerButton) {
    // Obtener datos del botón
    const reportId = triggerButton.getAttribute('data-report-id');
    const patientName = triggerButton.getAttribute('data-patient-name');
    const patientEmail = triggerButton.getAttribute('data-patient-email');
    const condition = triggerButton.getAttribute('data-condition');

    console.log('Datos del reporte:', { reportId, patientName, patientEmail, condition });

    // Actualizar el título del modal
    const modalTitle = modal.querySelector('.modal-title');
    if (modalTitle) {
        modalTitle.innerHTML = `
            <i class="fas fa-envelope me-2"></i>
            Enviar Reporte #${reportId}
        `;
    }

    // Pre-llenar el email si está disponible
    const emailInput = modal.querySelector('input[name="email"]');
    if (emailInput) {
        if (patientEmail && patientEmail.trim() !== '' && patientEmail !== 'N/A') {
            emailInput.value = patientEmail;
        } else {
            emailInput.value = '';
        }
    }

    // Actualizar la información del paciente en el modal
    const patientNameDisplay = modal.querySelector('.patient-name-display');
    if (patientNameDisplay) {
        patientNameDisplay.textContent = patientName || 'Paciente desconocido';
    }

    const conditionDisplay = modal.querySelector('.condition-display');
    if (conditionDisplay) {
        conditionDisplay.textContent = condition || 'Sin condición especificada';
    }
}

/**
 * Inicializa la validación de formularios
 */
function initializeFormValidation() {
    document.querySelectorAll('input[name="email"]').forEach(input => {
        input.addEventListener('blur', function() {
            validateEmail(this);
        });

        input.addEventListener('input', function() {
            clearValidationError(this);
        });
    });
}

/**
 * Valida el formato del email
 */
function validateEmail(input) {
    const email = input.value.trim();
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    
    if (email && !emailRegex.test(email)) {
        showValidationError(input, 'Por favor ingrese un email válido');
        return false;
    }
    
    clearValidationError(input);
    return true;
}

/**
 * Muestra error de validación
 */
function showValidationError(input, message) {
    input.classList.add('is-invalid');
    
    const errorDiv = input.parentElement.querySelector('.invalid-feedback');
    if (errorDiv) {
        errorDiv.textContent = message;
    }
}

/**
 * Limpia errores de validación
 */
function clearValidationError(input) {
    input.classList.remove('is-invalid');
    const errorDiv = input.parentElement.querySelector('.invalid-feedback');
    if (errorDiv) {
        errorDiv.textContent = '';
    }
}

/**
 * Maneja el envío del formulario de email
 */
function handleEmailSubmit(e, form) {
    const emailInput = form.querySelector('input[name="email"]');
    
    if (!emailInput || !emailInput.value.trim()) {
        e.preventDefault();
        showValidationError(emailInput, 'El email es requerido');
        emailInput.focus();
        return false;
    }

    if (!validateEmail(emailInput)) {
        e.preventDefault();
        emailInput.focus();
        return false;
    }

    // Mostrar loading en el botón de envío
    const submitButton = form.querySelector('button[type="submit"]');
    if (submitButton) {
        showButtonLoading(submitButton);
    }

    return true; // Permitir el envío del formulario
}

/**
 * Inicializa manejadores de botones
 */
function initializeButtonHandlers() {
    // Botones de descarga PDF
    document.querySelectorAll('.btn-pdf').forEach(button => {
        button.addEventListener('click', function(e) {
            handlePdfDownload(e, this);
        });
    });

    // Animaciones de hover en tarjetas
    document.querySelectorAll('.report-card').forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-4px)';
        });

        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
}

/**
 * Maneja la descarga de PDF
 */
function handlePdfDownload(e, button) {
    showButtonLoading(button, 'Generando...');
    
    // El enlace se procesará normalmente, pero mostraremos feedback
    setTimeout(() => {
        resetButtonLoading(button, '<i class="fas fa-file-pdf"></i> PDF');
    }, 3000);
}

/**
 * Muestra estado de carga en un botón
 */
function showButtonLoading(button, text = 'Enviando...') {
    button.disabled = true;
    button.dataset.originalText = button.innerHTML;
    button.innerHTML = `<i class="fas fa-spinner fa-spin"></i> ${text}`;
}

/**
 * Restaura el estado original del botón
 */
function resetButtonLoading(button, originalText = null) {
    button.disabled = false;
    button.innerHTML = originalText || button.dataset.originalText || button.innerHTML;
}

/**
 * Anima la aparición de las tarjetas
 */
function animateCards() {
    const cards = document.querySelectorAll('.report-card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            card.style.transition = 'all 0.6s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });
}

// Manejar eventos de Bootstrap para modales
document.addEventListener('show.bs.modal', function(e) {
    if (e.target.id.startsWith('emailModal')) {
        console.log('Modal abierto:', e.target.id);
        const emailInput = e.target.querySelector('input[name="email"]');
        setTimeout(() => {
            if (emailInput) {
                emailInput.focus();
                emailInput.select();
            }
        }, 300);
    }
});

document.addEventListener('hidden.bs.modal', function(e) {
    if (e.target.id.startsWith('emailModal')) {
        console.log('Modal cerrado:', e.target.id);
        const form = e.target.querySelector('.email-form');
        if (form) {
            // Limpiar errores de validación
            const invalidInputs = form.querySelectorAll('.is-invalid');
            invalidInputs.forEach(input => {
                input.classList.remove('is-invalid');
            });
            const errorDivs = form.querySelectorAll('.invalid-feedback');
            errorDivs.forEach(div => div.textContent = '');
            
            // Restaurar botón de envío
            const submitButton = form.querySelector('button[type="submit"]');
            if (submitButton && submitButton.dataset.originalText) {
                submitButton.disabled = false;
                submitButton.innerHTML = submitButton.dataset.originalText;
            }
        }
    }
});

// Manejar alertas con auto-cierre
document.addEventListener('DOMContentLoaded', () => {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        // Auto-ocultar después de 5 segundos
        setTimeout(() => {
            if (alert.parentElement) {
                alert.style.transition = 'all 0.3s ease';
                alert.style.opacity = '0';
                alert.style.transform = 'translateX(100%)';
                setTimeout(() => {
                    if (alert.parentElement) {
                        alert.remove();
                    }
                }, 300);
            }
        }, 5000);

        // Botón de cierre manual
        const closeButton = alert.querySelector('.btn-close, .close');
        if (closeButton) {
            closeButton.addEventListener('click', () => {
                alert.style.transition = 'all 0.3s ease';
                alert.style.opacity = '0';
                alert.style.transform = 'translateX(100%)';
                setTimeout(() => {
                    if (alert.parentElement) {
                        alert.remove();
                    }
                }, 300);
            });
        }
    });
});