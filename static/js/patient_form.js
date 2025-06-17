/**
 * JavaScript para formularios de pacientes
 */

class PatientFormManager {
    constructor() {
        this.initializeElements();
        this.initializeVariables();
        this.setupEventListeners();
        this.initializeFormState();
    }

    initializeElements() {
        this.form = document.querySelector('form');
        this.submitBtn = this.form.querySelector('button[type="submit"]');

        // Campos del formulario
        this.firstNameInput = document.getElementById('id_first_name');
        this.lastNameInput = document.getElementById('id_last_name');
        this.dniInput = document.getElementById('id_dni');
        this.phoneInput = document.getElementById('id_phone');
        this.emailInput = document.getElementById('id_email');
        this.ageInput = document.getElementById('id_age_approx');
        this.sexSelect = document.getElementById('id_sex');

        this.allFields = [
            this.firstNameInput, this.lastNameInput, this.dniInput,
            this.phoneInput, this.emailInput, this.ageInput, this.sexSelect
        ].filter(field => field !== null);
    }

    initializeVariables() {
        // Guardar valores iniciales
        this.initialValues = {};
        this.allFields.forEach(field => {
            this.initialValues[field.name] = (field.value || '').trim();
        });

        this.submitBtnText = this.submitBtn.textContent;
        this.isFormValid = true;
    }

    setupEventListeners() {
        // Event listeners para cada campo
        this.allFields.forEach(field => {
            field.addEventListener('input', () => this.handleFieldInput(field));
            field.addEventListener('blur', () => this.handleFieldBlur(field));
            field.addEventListener('change', () => this.checkFormChanges());
        });

        // Event listener para el envío del formulario
        this.form.addEventListener('submit', (e) => this.handleFormSubmit(e));

        // Formatear DNI en tiempo real
        if (this.dniInput) {
            this.dniInput.addEventListener('input', () => this.formatDNIInput());
        }

        // Formatear teléfono en tiempo real
        if (this.phoneInput) {
            this.phoneInput.addEventListener('input', () => this.formatPhoneInput());
        }
    }

    initializeFormState() {
        this.setSubmitButtonState(true); // Inicialmente deshabilitado
        this.checkFormChanges();
    }

    handleFieldInput(field) {
        this.removeErrorMessage(field);
        this.checkFormChanges();
    }

    handleFieldBlur(field) {
        this.validateField(field);
        this.checkFormChanges();
    }

    formatDNIInput() {
        let value = this.dniInput.value.replace(/\D/g, '');
        if (value.length > 10) {
            value = value.slice(0, 10);
        }
        this.dniInput.value = value;
    }

    formatPhoneInput() {
        let value = this.phoneInput.value;

        // Permitir solo números, + y espacios
        value = value.replace(/[^\d+\s]/g, '');

        // Si empieza con +593, formatear automáticamente
        if (value.startsWith('+593') && value.length > 4) {
            value = value.replace(/(\+593)(\d{0,2})(\d{0,3})(\d{0,4})/, (match, p1, p2, p3, p4) => {
                let formatted = p1;
                if (p2) formatted += ' ' + p2;
                if (p3) formatted += ' ' + p3;
                if (p4) formatted += ' ' + p4;
                return formatted;
            });
        }

        this.phoneInput.value = value;
    }

    checkFormChanges() {
        const hasChanges = this.allFields.some(field => {
            const currentValue = (field.value || '').trim();
            return currentValue !== this.initialValues[field.name];
        });

        this.setSubmitButtonState(!hasChanges);
    }

    setSubmitButtonState(disabled) {
        this.submitBtn.disabled = disabled;

        if (disabled) {
            this.submitBtn.innerHTML = '<i class="fa fa-lock"></i> ' + this.submitBtnText;
            // this.submitBtn.setAttribute('title', 'SE HABILITARÁ CUANDO REALICE ALGÚN CAMBIO EN EL FORMULARIO');
        } else {
            this.submitBtn.innerHTML = this.submitBtnText;
            this.submitBtn.removeAttribute('title');
        }
    }

    validateField(field) {
        let error = null;
        let isWarning = false;

        switch (field.name) {
            case 'first_name':
            case 'last_name':
                error = this.validateFullName(field.value);
                break;
            case 'dni':
                const dniResult = this.validateDni(field.value);
                if (dniResult) {
                    error = dniResult.message;
                    isWarning = dniResult.isWarning;
                }
                break;
            case 'phone':
                error = this.validatePhone(field.value);
                break;
            case 'email':
                error = this.validateEmail(field.value);
                break;
            case 'age_approx':
                error = this.validateAge(field.value);
                break;
            case 'sex':
                if (!field.value) {
                    error = 'Por favor seleccione una opción';
                }
                break;
        }

        if (error) {
            this.createErrorMessage(field, error, isWarning);
            if (!isWarning) {
                this.isFormValid = false;
            }
        } else {
            this.removeErrorMessage(field);
        }

        return !error || isWarning;
    }

    validateFullName(value) {
        const trimmedValue = value.trim();

        if (!trimmedValue) {
            return "El campo está vacío, por favor rellénelo.";
        }

        if (trimmedValue.length < 3) {
            return "El nombre o apellido debe tener al menos 3 caracteres.";
        }

        if (trimmedValue.length > 50) {
            return "El nombre o apellido no puede tener más de 50 caracteres.";
        }

        const nameRegex = /^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$/;
        if (!nameRegex.test(trimmedValue)) {
            return "Solo puede contener letras, incluyendo letras especiales como la Ñ o tilde.";
        }

        return null;
    }

    validateDni(value) {
        const trimmedValue = value.trim();

        if (!trimmedValue) {
            return {message: "El campo está vacío, por favor rellénelo.", isWarning: false};
        }

        if (trimmedValue.length !== 10) {
            return {message: "La cédula debe contener exactamente 10 dígitos.", isWarning: false};
        }

        if (!/^\d+$/.test(trimmedValue)) {
            return {message: "La cédula debe contener solo números.", isWarning: false};
        }

        // Algoritmo de validación ecuatoriano
        const coeficientes = [2, 1, 2, 1, 2, 1, 2, 1, 2];
        let total = 0;

        for (let i = 0; i < 9; i++) {
            let valor = parseInt(trimmedValue[i]) * coeficientes[i];
            if (valor > 9) valor -= 9;
            total += valor;
        }

        const digitoVerificador = (total % 10) === 0 ? 0 : 10 - (total % 10);
        if (digitoVerificador !== parseInt(trimmedValue[9])) {
            return {message: "La cédula ingresada no es válida.", isWarning: false};
        }

        return null;
    }

    validateEmail(value) {
        const trimmedValue = value.trim();

        if (!trimmedValue) {
            return "El campo está vacío, por favor rellénelo.";
        }

        if (trimmedValue.length > 254) {
            return "El correo electrónico no puede tener más de 254 caracteres.";
        }

        const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
        if (!emailRegex.test(trimmedValue)) {
            return "Ingrese un correo electrónico válido.";
        }

        return null;
    }

    validatePhone(value) {
        const trimmedValue = value.trim();

        if (!trimmedValue) {
            return "El campo está vacío, por favor rellénelo.";
        }

        if (!/^(\+593\s\d{2}\s\d{3}\s\d{4}|0\d{9})$/.test(trimmedValue)) {
            return "Ingrese un número válido (formato: +593 99 999 9999 o 0999999999)";
        }

        return null;
    }

    validateAge(value) {
        if (!value) {
            return "El campo está vacío, por favor rellénelo.";
        }

        const age = parseInt(value);
        if (isNaN(age) || age < 0 || age > 120) {
            return "Ingrese una edad válida entre 0 y 120 años.";
        }

        return null;
    }

    createErrorMessage(field, message, isWarning = false) {
        this.removeErrorMessage(field);

        const errorDiv = document.createElement('div');
        errorDiv.className = isWarning ? 'warning-message' : 'error-message';
        errorDiv.textContent = message;

        field.parentNode.appendChild(errorDiv);
        field.classList.add(isWarning ? 'warning' : 'error');
    }

    removeErrorMessage(field) {
        const parentNode = field.parentNode;
        const errorMsg = parentNode.querySelector('.error-message');
        const warningMsg = parentNode.querySelector('.warning-message');

        if (errorMsg) errorMsg.remove();
        if (warningMsg) warningMsg.remove();

        field.classList.remove('error', 'warning');
    }

    handleFormSubmit(e) {
        this.isFormValid = true;

        // Validar todos los campos
        this.allFields.forEach(field => {
            this.validateField(field);
        });

        if (!this.isFormValid) {
            e.preventDefault();
            this.showAlert('Por favor corrija los errores en el formulario', 'error');
        }
    }

    showAlert(message, type = 'info') {
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show`;
        alert.style.position = 'fixed';
        alert.style.top = '20px';
        alert.style.right = '20px';
        alert.style.zIndex = '9999';
        alert.style.minWidth = '300px';

        alert.innerHTML = `
            <i class="fas fa-${this.getAlertIcon(type)}"></i>
            ${message}
            <button type="button" class="btn-close" aria-label="Close"></button>
        `;

        document.body.appendChild(alert);

        setTimeout(() => {
            alert.remove();
        }, 5000);

        const closeBtn = alert.querySelector('.btn-close');
        closeBtn.addEventListener('click', () => {
            alert.remove();
        });
    }

    getAlertIcon(type) {
        const icons = {
            'success': 'check-circle',
            'error': 'exclamation-circle',
            'warning': 'exclamation-triangle',
            'info': 'info-circle'
        };
        return icons[type] || 'info-circle';
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    new PatientFormManager();
});