document.addEventListener('DOMContentLoaded', function() {
    initializeEmailModals();
    initializeFormValidation();
    initializeButtonHandlers();
    animateCards();
});

function initializeEmailModals() {
    const emailButtons = document.querySelectorAll('[data-bs-target^="#emailModal"]');
    emailButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const modalId = this.getAttribute('data-bs-target');
            const modal = document.querySelector(modalId);
            if (modal) {
                prepareEmailModal(modal, this);
            }
        });
    });

    const emailForms = document.querySelectorAll('.email-form');
    emailForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            return handleEmailSubmit(e, this);
        });
    });
}

function prepareEmailModal(modal, triggerButton) {
    const reportId = triggerButton.getAttribute('data-report-id');
    const patientName = triggerButton.getAttribute('data-patient-name');
    const patientEmail = triggerButton.getAttribute('data-patient-email');
    const condition = triggerButton.getAttribute('data-condition');

    const modalTitle = modal.querySelector('.modal-title');
    if (modalTitle) {
        modalTitle.innerHTML = `
            <i class="fas fa-envelope me-2"></i>
            Enviar Reporte #${reportId}
        `;
    }

    const emailInput = modal.querySelector('input[name="email"]');
    if (emailInput) {
        if (patientEmail && patientEmail.trim() !== '' && patientEmail !== 'N/A') {
            emailInput.value = patientEmail;
        } else {
            emailInput.value = '';
        }
    }

    const patientNameDisplay = modal.querySelector('.patient-name-display');
    if (patientNameDisplay) {
        patientNameDisplay.textContent = patientName || 'Paciente desconocido';
    }

    const conditionDisplay = modal.querySelector('.condition-display');
    if (conditionDisplay) {
        conditionDisplay.textContent = condition || 'Sin condición especificada';
    }
}

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

function showValidationError(input, message) {
    input.classList.add('is-invalid');
    const errorDiv = input.parentElement.querySelector('.invalid-feedback');
    if (errorDiv) {
        errorDiv.textContent = message;
    }
}

function clearValidationError(input) {
    input.classList.remove('is-invalid');
    const errorDiv = input.parentElement.querySelector('.invalid-feedback');
    if (errorDiv) {
        errorDiv.textContent = '';
    }
}

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
    const submitButton = form.querySelector('button[type="submit"]');
    if (submitButton) {
        showButtonLoading(submitButton);
    }
    return true;
}

function initializeButtonHandlers() {
    document.querySelectorAll('.btn-pdf').forEach(button => {
        button.addEventListener('click', function(e) {
            handlePdfDownload(e, this);
        });
    });

    document.querySelectorAll('.report-card').forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-4px)';
        });

        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
}

function handlePdfDownload(e, button) {
    showButtonLoading(button, 'Generando...');
    setTimeout(() => {
        resetButtonLoading(button, '<i class="fas fa-file-pdf"></i> PDF');
    }, 3000);
}

function showButtonLoading(button, text = 'Enviando...') {
    button.disabled = true;
    button.dataset.originalText = button.innerHTML;
    button.innerHTML = `<i class="fas fa-spinner fa-spin"></i> ${text}`;
}

function resetButtonLoading(button, originalText = null) {
    button.disabled = false;
    button.innerHTML = originalText || button.dataset.originalText || button.innerHTML;
}

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

document.addEventListener('show.bs.modal', function(e) {
    if (e.target.id.startsWith('emailModal')) {
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
        const form = e.target.querySelector('.email-form');
        if (form) {
            const invalidInputs = form.querySelectorAll('.is-invalid');
            invalidInputs.forEach(input => {
                input.classList.remove('is-invalid');
            });
            const errorDivs = form.querySelectorAll('.invalid-feedback');
            errorDivs.forEach(div => div.textContent = '');
            const submitButton = form.querySelector('button[type="submit"]');
            if (submitButton && submitButton.dataset.originalText) {
                submitButton.disabled = false;
                submitButton.innerHTML = submitButton.dataset.originalText;
            }
        }
    }
});

document.addEventListener('DOMContentLoaded', () => {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
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
