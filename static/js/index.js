// Utilidades generales
const utils = {
    /**
     * Crea un div de mensaje de error
     * @param {HTMLElement} input - Elemento de entrada
     * @param {string} message - Mensaje de error
     * @param {boolean} isWarning - Si es una advertencia en lugar de error
     */
    createErrorMessage(input, message, isWarning = false) {
        this.removeErrorMessage(input);
        const errorDiv = document.createElement('div');
        errorDiv.className = isWarning ? 'warning-message' : 'error-message';
        errorDiv.textContent = message;
        input.parentNode.appendChild(errorDiv);
        
        if (!isWarning) {
            input.classList.add('error');
        }
    },

    /**
     * Elimina mensajes de error existentes
     * @param {HTMLElement} input - Elemento de entrada
     */
    removeErrorMessage(input) {
        const errorMsg = input.parentNode.querySelector('.error-message');
        const warningMsg = input.parentNode.querySelector('.warning-message');
        if (errorMsg) errorMsg.remove();
        if (warningMsg) warningMsg.remove();
        input.classList.remove('error', 'warning');
    },

    /**
     * Configura las alertas con botón de cierre y auto-ocultado
     */    setupAlerts() {
        // Agregar botones de cierre y estilizar alertas
        document.querySelectorAll('.alert').forEach(alert => {
            // Agregar icono según el tipo de alerta
            const type = alert.classList.contains('alert-success') ? 'check-circle' :
                        alert.classList.contains('alert-warning') ? 'exclamation-circle' :
                        alert.classList.contains('alert-error') ? 'exclamation-triangle' : 'info-circle';
            
            if (!alert.querySelector('.alert-icon')) {
                const icon = document.createElement('i');
                icon.className = `fas fa-${type} alert-icon`;
                alert.insertBefore(icon, alert.firstChild);
            }

            // Agregar botón de cierre si no existe
            if (!alert.querySelector('.close-btn')) {
                const closeBtn = document.createElement('button');
                closeBtn.className = 'close-btn';
                closeBtn.innerHTML = '&times;';
                Object.assign(closeBtn.style, {
                    float: 'right',
                    background: 'none',
                    border: 'none',
                    fontSize: '1.2rem',
                    cursor: 'pointer',
                    marginLeft: '10px',
                    color: 'inherit',
                    opacity: '0.5',
                    transition: 'opacity 0.2s'
                });
                closeBtn.addEventListener('mouseover', () => closeBtn.style.opacity = '1');
                closeBtn.addEventListener('mouseout', () => closeBtn.style.opacity = '0.5');
                closeBtn.addEventListener('click', () => {
                    alert.style.height = alert.offsetHeight + 'px';
                    alert.style.opacity = '0';
                    alert.style.marginTop = '-' + alert.offsetHeight + 'px';
                    setTimeout(() => alert.remove(), 300);
                });
                alert.appendChild(closeBtn);
            }

            // Aplicar estilos al alert
            Object.assign(alert.style, {
                display: 'flex',
                alignItems: 'center',
                padding: '1rem',
                marginBottom: '1rem',
                borderRadius: '0.5rem',
                transition: 'all 0.3s ease',
                overflow: 'hidden'
            });
        });

        // Auto-ocultar alertas después de 5 segundos con animación suave
        setTimeout(() => {
            document.querySelectorAll('.alert').forEach(alert => {
                const height = alert.offsetHeight;
                alert.style.height = height + 'px';
                alert.style.transition = 'all 0.3s ease';
                
                setTimeout(() => {
                    alert.style.height = alert.offsetHeight + 'px';
                    alert.style.opacity = '0';
                    alert.style.marginTop = '-' + alert.offsetHeight + 'px';
                    setTimeout(() => alert.remove(), 300);
                }, 100);
            });
        }, 5000);
    }
};

// Validadores de formularios
const validators = {
    emptyMsg: 'El campo está vacío, por favor rellénelo.',

    /**
     * Valida nombre completo
     * @param {string} value - Valor a validar
     * @returns {string|null} Mensaje de error o null si es válido
     */
    fullName(value) {
        if (!value.trim()) return this.emptyMsg;
        if (!/^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$/.test(value)) {
            return 'Solo letras y espacios permitidos.';
        }
        return null;
    },

    /**
     * Valida email
     * @param {string} value - Valor a validar
     */
    email(value) {
        if (!value.trim()) return this.emptyMsg;
        const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
        if (!emailRegex.test(value)) {
            return 'Ingrese un correo electrónico válido.';
        }
        return null;
    },

    /**
     * Valida cédula ecuatoriana
     * @param {string} value - Valor a validar
     */
    dni(value) {
        if (!value.trim()) return null; // Opcional
        if (!/^\d{10}$/.test(value)) {
            return 'La cédula debe tener 10 dígitos numéricos.';
        }
        // Algoritmo de validación de cédula ecuatoriana
        let sum = 0;
        const coeficientes = [2, 1, 2, 1, 2, 1, 2, 1, 2];
        for (let i = 0; i < 9; i++) {
            let valor = parseInt(value[i]) * coeficientes[i];
            sum += valor > 9 ? valor - 9 : valor;
        }
        const verificador = (sum * 9) % 10;
        if (verificador !== parseInt(value[9])) {
            return 'La cédula no es válida.';
        }
        return null;
    },

    /**
     * Valida dirección y ciudad
     * @param {string} value - Valor a validar
     */
    addressCity(value) {
        if (!value.trim()) return null; // Opcional
        if (!/^[a-zA-ZáéíóúÁÉÍÓÚñÑ0-9\s.,#-]+$/.test(value)) {
            return 'Caracteres no permitidos en la dirección.';
        }
        return null;
    },

    /**
     * Valida número de teléfono
     * @param {string} value - Valor a validar
     */
    phone(value) {
        if (!value.trim()) return null; // Opcional
        if (!/^(\+593\s\d{2}\s\d{3}\s\d{4}|0\d{9})$/.test(value)) {
            return 'Formato válido: 0991234567 o +593 99 123 4567';
        }
        return null;
    },

    /**
     * Valida contraseña
     * @param {string} value - Valor a validar
     */
    password(value) {
        if (!value.trim()) return this.emptyMsg;
        if (value.length < 8) {
            return 'La contraseña debe tener al menos 8 caracteres.';
        }
        return null;
    },

    /**
     * Valida confirmación de contraseña
     * @param {string} value - Valor a validar
     * @param {string} password - Contraseña original
     */
    confirmPassword(value, password) {
        if (!value.trim()) return this.emptyMsg;
        if (value !== password) {
            return 'Las contraseñas no coinciden.';
        }
        return null;
    }
};

// Manejadores de formularios específicos
const formHandlers = {
    /**
     * Configura validación para un campo
     * @param {string} inputId - ID del campo
     * @param {Function} validatorFn - Función validadora
     */
    setupFieldValidation(inputId, validatorFn) {
        const input = document.getElementById(inputId);
        if (!input) return;

        input.addEventListener('blur', () => {
            const error = validatorFn(input.value);
            if (error) {
                utils.createErrorMessage(input, error);
            } else {
                utils.removeErrorMessage(input);
            }
        });

        // Validar también al escribir si hay error
        input.addEventListener('input', () => {
            if (input.parentElement.querySelector('.error-message')) {
                const error = validatorFn(input.value);
                if (error) {
                    utils.createErrorMessage(input, error);
                } else {
                    utils.removeErrorMessage(input);
                }
            }
        });
    },    /**
     * Configura los campos base comunes entre formularios
     * @param {Array} additionalFields - Campos adicionales específicos del formulario
     */
    setupBaseFields(additionalFields = []) {
        const baseFields = [
            { id: 'id_first_name', validator: validators.fullName.bind(validators) },
            { id: 'id_last_name', validator: validators.fullName.bind(validators) },
            { id: 'id_email', validator: validators.email.bind(validators) }
        ];

        const allFields = [...baseFields, ...additionalFields];
        allFields.forEach(({ id, validator }) => {
            this.setupFieldValidation(id, validator);
        });
    },

    /**
     * Configura validación de contraseñas
     * @param {string} pwd1Id - ID del campo de contraseña
     * @param {string} pwd2Id - ID del campo de confirmación
     */
    setupPasswordValidation(pwd1Id, pwd2Id) {
        const pwd1 = document.getElementById(pwd1Id);
        const pwd2 = document.getElementById(pwd2Id);

        if (pwd1) {
            this.setupFieldValidation(pwd1Id, validators.password.bind(validators));
        }

        if (pwd2 && pwd1) {
            this.setupFieldValidation(pwd2Id, (value) => 
                validators.confirmPassword(value, pwd1.value));
        }
    },

    /**
     * Inicializa el formulario de registro
     */
    initRegisterForm() {
        // Configurar campos base
        this.setupBaseFields();

        // Configurar validación de contraseñas
        this.setupPasswordValidation('id_password1', 'id_password2');
    },

    /**
     * Inicializa el formulario de login
     */
    initLoginForm() {
        this.setupFieldValidation('id_username', validators.email.bind(validators));
        this.setupFieldValidation('id_password', validators.password.bind(validators));
    },

    /**
     * Inicializa el formulario de actualización de perfil
     */
    initProfileUpdateForm() {
        // Configurar campos base más campos adicionales específicos
        const additionalFields = [
            { id: 'id_dni', validator: validators.dni.bind(validators) },
            { id: 'id_address', validator: validators.addressCity.bind(validators) },
            { id: 'id_city', validator: validators.addressCity.bind(validators) },
            { id: 'id_phone', validator: validators.phone.bind(validators) }
        ];
        
        this.setupBaseFields(additionalFields);// Configurar preview de imagen con validación mejorada
        const profileInput = document.getElementById('id_profile_picture');
        const previewImg = document.getElementById('profile-preview');

        if (profileInput && previewImg) {
            profileInput.addEventListener('change', (e) => {
                const file = e.target.files[0];
                if (file) {
                    // Validar tipo de archivo
                    if (!file.type.startsWith('image/')) {
                        utils.createErrorMessage(profileInput, 'Por favor seleccione un archivo de imagen válido (PNG, JPG, GIF)');
                        return;
                    }
                    
                    // Validar tamaño (máximo 5MB)
                    if (file.size > 5 * 1024 * 1024) {
                        utils.createErrorMessage(profileInput, 'La imagen no debe superar los 5MB');
                        return;
                    }

                    const reader = new FileReader();
                    reader.onload = (e) => {
                        previewImg.src = e.target.result;
                        utils.removeErrorMessage(profileInput);
                    };
                    reader.onerror = () => {
                        utils.createErrorMessage(profileInput, 'Error al leer el archivo. Por favor intente nuevamente.');
                    };
                    reader.readAsDataURL(file);
                }
            });
        }
    }
};

/**
 * Inicializa el formulario de restablecimiento de contraseña
 */
formHandlers.initPasswordResetForm = function() {
    const newPassword1 = document.getElementById('id_new_password1');
    const newPassword2 = document.getElementById('id_new_password2');

    if (newPassword1) {
        this.setupFieldValidation('id_new_password1', validators.password.bind(validators));
    }

    if (newPassword2 && newPassword1) {
        this.setupFieldValidation('id_new_password2', (value) => 
            validators.confirmPassword(value, newPassword1.value));
    }
};

// Inicialización cuando el DOM está listo
document.addEventListener('DOMContentLoaded', () => {
    // Configurar alertas en todas las páginas
    utils.setupAlerts();

    // Inicializar formularios según la página actual
    const currentPage = document.body.dataset.page;
    switch (currentPage) {
        case 'register':
            formHandlers.initRegisterForm();
            break;
        case 'login':
            formHandlers.initLoginForm();
            break;
        case 'profile-update':
            formHandlers.initProfileUpdateForm();
            break;
        case 'password-reset':
            formHandlers.initPasswordResetForm();
            break;
    }
});