/**
 * JavaScript para la página de subida de imágenes dermatológicas
 * Maneja la selección de pacientes, validación de formularios y subida de archivos
 */

// Variables globales para textos internacionalizados
let JS_TEXTS = {};

/**
 * Clase para manejar la funcionalidad de upload de imágenes
 */
class UploadManager {
    constructor() {
        this.initializeElements();
        this.initializeVariables();
        this.setupEventListeners();
        this.restoreInitialOptions();
    }

    /**
     * Inicializa los elementos del DOM
     */
    initializeElements() {
        this.patientSelect = document.getElementById('patient_select');
        this.btnAddNew = document.getElementById('btn-add-new');
        this.sectionPatientFields = document.getElementById('section-patient-fields');
        this.fileInput = document.getElementById('fileInput');
        this.uploadArea = document.getElementById('uploadArea');
        this.imagePreview = document.getElementById('imagePreview');
        this.siteSelect = document.getElementById('site_select');
        this.uploadForm = document.getElementById('uploadForm');
        this.loadingOverlay = document.getElementById('loadingOverlay');
        this.errorAlert = document.getElementById('errorAlert');
        this.csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

        // Campos del paciente
        this.firstNameInput = document.getElementById('first_name');
        this.lastNameInput = document.getElementById('last_name');
        this.dniInput = document.getElementById('dni');
        this.phoneInput = document.getElementById('phone');
        this.emailInput = document.getElementById('email');
        this.ageInput = document.getElementById('age_approx');
        this.sexSelect = document.getElementById('sex');
    }

    /**
     * Inicializa las variables de estado
     */
    initializeVariables() {
        this.initialOptions = Array.from(this.patientSelect.options).map(option => ({
            value: option.value,
            text: option.textContent,
            first: option.dataset.first,
            last: option.dataset.last,
            dni: option.dataset.dni,
            phone: option.dataset.phone,
            email: option.dataset.email,
            age: option.dataset.age,
            sex: option.dataset.sex
        }));
        
        this.currentPatients = [...this.initialOptions];
        this.searchTimeout = null;
        this.isTyping = false;
        this.typingValue = '';
        this.lastSelectedValue = '';
    }

    /**
     * Configura todos los event listeners
     */
    setupEventListeners() {
        this.setupPatientSelectListeners();
        this.setupImageUploadListeners();
        this.setupFormSubmitListener();
    }

    /**
     * Configura los listeners para la selección de pacientes
     */
    setupPatientSelectListeners() {
        this.patientSelect.addEventListener('keydown', (e) => this.handlePatientSelectKeydown(e));
        this.patientSelect.addEventListener('change', () => this.handlePatientSelectChange());
        this.patientSelect.addEventListener('focus', () => this.handlePatientSelectFocus());
        this.patientSelect.addEventListener('click', () => this.handlePatientSelectClick());
        this.patientSelect.addEventListener('blur', () => this.handlePatientSelectBlur());
        this.btnAddNew.addEventListener('click', () => this.handleAddNewPatient());
    }

    /**
     * Configura los listeners para la subida de imágenes
     */
    setupImageUploadListeners() {
        this.uploadArea.addEventListener('click', () => this.fileInput.click());
        this.fileInput.addEventListener('change', (e) => this.handleFileInputChange(e));
        this.uploadArea.addEventListener('dragover', (e) => this.handleDragOver(e));
        this.uploadArea.addEventListener('dragleave', () => this.handleDragLeave());
        this.uploadArea.addEventListener('drop', (e) => this.handleDrop(e));
    }

    /**
     * Configura el listener para el envío del formulario
     */
    setupFormSubmitListener() {
        this.uploadForm.addEventListener('submit', (e) => this.handleFormSubmit(e));
    }

    /**
     * Maneja el evento keydown del select de pacientes
     */
    handlePatientSelectKeydown(e) {
        if (e.key.length === 1 && !/^[0-9]$/.test(e.key)) {
            e.preventDefault();
            return;
        }
        
        if (this.typingValue.length >= 10 && e.key.length === 1) {
            e.preventDefault();
            return;
        }
        
        if (e.key.length === 1 || e.key === 'Backspace' || e.key === 'Delete') {
            this.isTyping = true;
            if (e.key === 'Backspace') {
                this.typingValue = this.typingValue.slice(0, -1);
            } else if (e.key === 'Delete') {
                this.typingValue = '';
            } else if (e.key.length === 1) {
                this.typingValue += e.key;
            }
            
            const placeholder = this.patientSelect.options[0];
            placeholder.textContent = this.typingValue ? 
                `${JS_TEXTS.searchingPrefix} ${this.typingValue}` : 
                JS_TEXTS.searchPlaceholderDefault;
            
            this.searchPatients(this.typingValue);
            e.preventDefault();
        } else if (e.key === 'Enter') {
            e.preventDefault();
            if (this.patientSelect.options.length === 2) {
                this.patientSelect.selectedIndex = 1;
                this.patientSelect.dispatchEvent(new Event('change'));
                this.isTyping = false;
                this.typingValue = '';
                this.patientSelect.options[0].textContent = JS_TEXTS.searchPlaceholderDefault;
                this.restoreInitialOptions(this.patientSelect.value);
            }
        } else if (e.key === 'Escape') {
            this.isTyping = false;
            this.typingValue = '';
            this.patientSelect.options[0].textContent = JS_TEXTS.searchPlaceholderDefault;
            this.restoreInitialOptions(this.patientSelect.value);
        } else if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
            if (!this.isTyping) {
                this.restoreInitialOptions(this.patientSelect.value);
            }
        }
    }

    /**
     * Maneja el cambio de selección de paciente
     */
    handlePatientSelectChange() {
        const selected = this.patientSelect.selectedOptions[0];
        this.lastSelectedValue = this.patientSelect.value;
        
        if (selected && selected.value) {
            this.sectionPatientFields.style.display = 'block';
            this.fillPatientFields(selected);
            this.setPatientFieldsReadonly(true);
            this.isTyping = false;
            this.typingValue = '';
            this.patientSelect.options[0].textContent = JS_TEXTS.searchPlaceholderDefault;
            this.updatePatientOptions(this.currentPatients, this.patientSelect.value);
        } else {
            this.sectionPatientFields.style.display = 'none';
            this.isTyping = false;
            this.typingValue = '';
            this.patientSelect.options[0].textContent = JS_TEXTS.searchPlaceholderDefault;
            this.restoreInitialOptions();
        }
    }

    /**
     * Rellena los campos del paciente con los datos seleccionados
     */
    fillPatientFields(selected) {
        this.firstNameInput.value = selected.dataset.first;
        this.lastNameInput.value = selected.dataset.last;
        this.dniInput.value = selected.dataset.dni;
        this.phoneInput.value = selected.dataset.phone;
        this.emailInput.value = selected.dataset.email;
        this.ageInput.value = selected.dataset.age;
        this.sexSelect.value = selected.dataset.sex;
    }

    /**
     * Establece los campos del paciente como solo lectura o editables
     */
    setPatientFieldsReadonly(readonly) {
        const fields = [
            this.firstNameInput, this.lastNameInput, this.dniInput,
            this.phoneInput, this.emailInput, this.ageInput, this.sexSelect
        ];
        
        fields.forEach(field => {
            if (readonly) {
                field.setAttribute('readonly', true);
                field.disabled = true;
            } else {
                field.removeAttribute('readonly');
                field.disabled = false;
            }
            this.removeErrorMessage(field);
        });
    }

    /**
     * Maneja el foco en el select de pacientes
     */
    handlePatientSelectFocus() {
        if (!this.isTyping) {
            this.restoreInitialOptions(this.lastSelectedValue);
        } else if (this.typingValue) {
            this.patientSelect.options[0].textContent = `${JS_TEXTS.searchingPrefix} ${this.typingValue}`;
        }
    }

    /**
     * Maneja el click en el select de pacientes
     */
    handlePatientSelectClick() {
        if (!this.isTyping && !this.typingValue) {
            this.restoreInitialOptions(this.lastSelectedValue);
            this.patientSelect.options[0].textContent = JS_TEXTS.searchPlaceholderDefault;
        }
    }

    /**
     * Maneja la pérdida de foco del select de pacientes
     */
    handlePatientSelectBlur() {
        if (!this.patientSelect.value && !this.typingValue) {
            this.isTyping = false;
            this.patientSelect.options[0].textContent = JS_TEXTS.searchPlaceholderDefault;
            this.restoreInitialOptions();
        } else if (this.typingValue) {
            this.patientSelect.options[0].textContent = `${JS_TEXTS.searchingPrefix} ${this.typingValue}`;
        }
    }

    /**
     * Maneja el botón de agregar nuevo paciente
     */
    handleAddNewPatient() {
        this.sectionPatientFields.style.display = 'block';
        this.clearPatientFields();
        this.setPatientFieldsReadonly(false);
        this.patientSelect.value = '';
        this.lastSelectedValue = '';
        this.isTyping = false;
        this.typingValue = '';
        this.patientSelect.options[0].textContent = JS_TEXTS.searchPlaceholderDefault;
        this.restoreInitialOptions();
    }

    /**
     * Limpia los campos del paciente
     */
    clearPatientFields() {
        const fields = [
            this.firstNameInput, this.lastNameInput, this.dniInput,
            this.phoneInput, this.emailInput, this.ageInput, this.sexSelect
        ];
        
        fields.forEach(field => {
            field.value = '';
            this.removeErrorMessage(field);
        });
    }

    /**
     * Busca pacientes en el servidor
     */
    searchPatients(query) {
        if (this.searchTimeout) {
            clearTimeout(this.searchTimeout);
        }
        
        this.searchTimeout = setTimeout(() => {
            const currentSelected = this.patientSelect.value;
            
            if (!query.trim()) {
                this.restoreInitialOptions(currentSelected);
                this.patientSelect.options[0].textContent = JS_TEXTS.searchPlaceholderDefault;
                return;
            }
            
            const searchUrl = this.patientSelect.closest('form').dataset.searchUrl || '/search-patients/';
            
            fetch(`${searchUrl}?dni=${encodeURIComponent(query)}`)
                .then(res => res.json())
                .then(data => {
                    const newPatients = this.convertServerDataToOptions(data.patients);
                    
                    if (currentSelected) {
                        const selectedOption = this.initialOptions.find(p => p.value === currentSelected);
                        if (selectedOption && !newPatients.find(p => p.value === currentSelected)) {
                            newPatients.unshift(selectedOption);
                        }
                    }
                    
                    this.currentPatients = newPatients;
                    this.updatePatientOptions(this.currentPatients, currentSelected);
                    this.patientSelect.options[0].textContent = `${JS_TEXTS.searchingPrefix} ${query}`;
                })
                .catch(err => {
                    console.error(JS_TEXTS.errorSearchingPatients, err);
                    this.errorAlert.textContent = `${JS_TEXTS.errorSearchingPatients} ${err.message}`;
                    this.errorAlert.style.display = 'block';
                });
        }, 300);
    }

    /**
     * Convierte los datos del servidor a opciones del select
     */
    convertServerDataToOptions(serverPatients) {
        return serverPatients.map(patient => ({
            value: patient.id.toString(),
            text: `${patient.dni} - ${patient.first_name} ${patient.last_name}`,
            first: patient.first_name,
            last: patient.last_name,
            dni: patient.dni,
            phone: patient.phone,
            email: patient.email,
            age: patient.age_approx,
            sex: patient.sex
        }));
    }

    /**
     * Actualiza las opciones del select de pacientes
     */
    updatePatientOptions(patients, selectedValue = '') {
        this.patientSelect.innerHTML = `<option value="">${JS_TEXTS.searchPlaceholderDefault}</option>`;
        
        patients.forEach(patient => {
            if (patient.value) {
                const option = document.createElement('option');
                option.value = patient.value;
                option.textContent = patient.text;
                
                Object.keys(patient).forEach(key => {
                    if (key !== 'value' && key !== 'text' && patient[key] !== undefined) {
                        option.dataset[key] = patient[key];
                    }
                });
                
                if (patient.value === selectedValue) {
                    option.selected = true;
                }
                
                this.patientSelect.appendChild(option);
            }
        });
    }

    /**
     * Restaura las opciones iniciales del select
     */
    restoreInitialOptions(selectedValue = '') {
        this.currentPatients = [...this.initialOptions].sort((a, b) => 
            (b.value && a.value) ? parseInt(b.value) - parseInt(a.value) : 0
        );
        this.updatePatientOptions(this.currentPatients, selectedValue);
    }

    /**
     * Maneja el cambio del input de archivo
     */
    handleFileInputChange(event) {
        this.removeErrorMessage(this.fileInput);
        const files = event.target.files;

        if (files && files.length > 0) {
            const file = files[0];
            const imageError = this.validateImage(file);

            if (imageError) {
                this.createErrorMessage(this.fileInput, imageError);
                this.resetImagePreview();
            } else {
                this.displayImagePreview(file);
            }
        }
    }

    /**
     * Maneja el drag over del área de subida
     */
    handleDragOver(e) {
        e.preventDefault();
        this.uploadArea.style.borderColor = '#007bff';
        this.uploadArea.style.backgroundColor = '#f8fbff';
    }

    /**
     * Maneja el drag leave del área de subida
     */
    handleDragLeave() {
        this.uploadArea.style.borderColor = '#ccc';
        this.uploadArea.style.backgroundColor = '';
    }

    /**
     * Maneja el drop de archivos
     */
    handleDrop(e) {
        e.preventDefault();
        this.uploadArea.style.borderColor = '#ccc';
        this.uploadArea.style.backgroundColor = '';

        const droppedFiles = e.dataTransfer.files;
        if (droppedFiles.length > 0) {
            this.fileInput.files = droppedFiles;
            const changeEvent = new Event('change', { bubbles: true });
            this.fileInput.dispatchEvent(changeEvent);
        }
    }

    /**
     * Valida una imagen
     */
    validateImage(file) {
        if (!file) {
            return JS_TEXTS.validation.imageRequired;
        }
        
        const validTypes = ['image/jpeg', 'image/png', 'image/jpg'];
        if (!validTypes.includes(file.type)) {
            return JS_TEXTS.validation.imageInvalidType;
        }
        
        const maxSize = 5 * 1024 * 1024; // 5MB
        if (file.size > maxSize) {
            return JS_TEXTS.validation.imageMaxSize;
        }
        
        return null;
    }

    /**
     * Muestra la previsualización de la imagen
     */
    displayImagePreview(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            this.imagePreview.src = e.target.result;
            this.imagePreview.style.display = 'block';
            
            // Ocultar el texto de "Arrastra aquí"
            this.uploadArea.querySelector('i').style.display = 'none';
            this.uploadArea.querySelector('h4').style.display = 'none';
            this.uploadArea.querySelector('p.text-muted').style.display = 'none';
        };
        reader.readAsDataURL(file);
    }

    /**
     * Resetea la previsualización de la imagen
     */
    resetImagePreview() {
        this.imagePreview.src = '#';
        this.imagePreview.style.display = 'none';
        this.fileInput.value = '';
        this.removeErrorMessage(this.fileInput);
        
        // Mostrar de nuevo el texto de "Arrastra aquí"
        this.uploadArea.querySelector('i').style.display = '';
        this.uploadArea.querySelector('h4').style.display = '';
        this.uploadArea.querySelector('p.text-muted').style.display = '';
    }

    /**
     * Maneja el envío del formulario
     */
    handleFormSubmit(e) {
        e.preventDefault();
        let hasErrors = false;
        this.errorAlert.style.display = 'none';
        this.errorAlert.textContent = '';

        // Limpiar errores previos
        const allFields = [
            this.firstNameInput, this.lastNameInput, this.dniInput,
            this.phoneInput, this.emailInput, this.ageInput,
            this.sexSelect, this.fileInput, this.siteSelect
        ];
        allFields.forEach(field => this.removeErrorMessage(field));

        // Validar campos del paciente si no hay paciente seleccionado
        if (!this.patientSelect.value) {
            hasErrors = this.validatePatientFields() || hasErrors;
        }

        // Validar imagen
        const currentFile = this.fileInput.files[0];
        const imageSubmitError = this.validateImage(currentFile);
        if (!currentFile) {
            this.createErrorMessage(this.fileInput, JS_TEXTS.validation.imageRequired);
            hasErrors = true;
        } else if (imageSubmitError) {
            this.createErrorMessage(this.fileInput, imageSubmitError);
            hasErrors = true;
        }

        // Validar sitio anatómico
        if (!this.siteSelect.value) {
            this.createErrorMessage(this.siteSelect, JS_TEXTS.validation.siteRequired);
            hasErrors = true;
        }

        if (hasErrors) {
            this.errorAlert.textContent = JS_TEXTS.generalErrors.formErrors;
            this.errorAlert.style.display = 'block';
            return;
        }

        this.submitForm();
    }

    /**
     * Valida los campos del paciente
     */
    validatePatientFields() {
        let hasErrors = false;

        const firstNameError = this.validateFullName(this.firstNameInput.value);
        if (firstNameError) {
            this.createErrorMessage(this.firstNameInput, firstNameError);
            hasErrors = true;
        }

        const lastNameError = this.validateFullName(this.lastNameInput.value);
        if (lastNameError) {
            this.createErrorMessage(this.lastNameInput, lastNameError);
            hasErrors = true;
        }

        const dniResult = this.validateDni(this.dniInput.value);
        if (dniResult) {
            this.createErrorMessage(this.dniInput, dniResult.message, dniResult.isWarning);
            if (!dniResult.isWarning) hasErrors = true;
        }

        const phoneError = this.validatePhone(this.phoneInput.value);
        if (phoneError) {
            this.createErrorMessage(this.phoneInput, phoneError);
            hasErrors = true;
        }

        const emailError = this.validateEmail(this.emailInput.value);
        if (emailError) {
            this.createErrorMessage(this.emailInput, emailError);
            hasErrors = true;
        }

        const ageError = this.validateAge(this.ageInput.value);
        if (ageError) {
            this.createErrorMessage(this.ageInput, ageError);
            hasErrors = true;
        }

        if (!this.sexSelect.value) {
            this.createErrorMessage(this.sexSelect, JS_TEXTS.validation.emptyField);
            hasErrors = true;
        }

        return hasErrors;
    }

    /**
     * Envía el formulario al servidor
     */
    submitForm() {
        this.loadingOverlay.style.display = 'flex';
        const formData = new FormData();

        if (this.patientSelect.value) {
            formData.append('patient', this.patientSelect.value);
        } else {
            formData.append('first_name', this.firstNameInput.value);
            formData.append('last_name', this.lastNameInput.value);
            formData.append('dni', this.dniInput.value);
            formData.append('phone', this.phoneInput.value);
            formData.append('email', this.emailInput.value);
            formData.append('age_approx', this.ageInput.value);
            formData.append('sex', this.sexSelect.value);
        }
        
        formData.append('image', this.fileInput.files[0]);
        formData.append('anatom_site_general', this.siteSelect.value);

        const submitUrl = this.uploadForm.action || this.uploadForm.dataset.submitUrl;

        fetch(submitUrl, {
            method: 'POST',
            body: formData,
            headers: { 'X-CSRFToken': this.csrfToken }
        })
        .then(res => {
            if (!res.ok) {
                return res.json().then(data => {
                    const errorDetail = data.errors || { general: `Error: ${res.status}` };
                    throw { status: res.status, data: errorDetail };
                });
            }
            return res.json();
        })
        .then(data => {
            if (data.success && data.redirect_url) {
                window.location.href = data.redirect_url;
            } else {
                throw { data: data.errors || { general: JS_TEXTS.generalErrors.serverError } };
            }
        })
        .catch(errObj => {
            this.handleSubmitError(errObj);
        });
    }

    /**
     * Maneja los errores del envío del formulario
     */
    handleSubmitError(errObj) {
        this.loadingOverlay.style.display = 'none';
        let errorMessageText = JS_TEXTS.generalErrors.serverError;

        if (errObj && errObj.data) {
            Object.keys(errObj.data).forEach(key => {
                const field = document.getElementById(key) || 
                              (key === 'image' ? this.fileInput : null) || 
                              (key === 'anatom_site_general' ? this.siteSelect : null);
                              
                const message = Array.isArray(errObj.data[key]) ? 
                               errObj.data[key].join(', ') : errObj.data[key];

                if (field) {
                    this.createErrorMessage(field, message);
                } else if (key === 'general' || key === '__all__') {
                    errorMessageText = message;
                } else {
                    console.warn(`Error de backend no mapeado a campo: ${key} - ${message}`);
                    if (errorMessageText === JS_TEXTS.generalErrors.serverError) {
                        errorMessageText = "";
                    }
                    errorMessageText += `${key}: ${message} `;
                }
            });

            if (Object.keys(errObj.data).length > 0 && 
                errorMessageText === JS_TEXTS.generalErrors.serverError) {
                errorMessageText = JS_TEXTS.generalErrors.formErrors;
            }
        } else if (errObj && errObj.message) {
            errorMessageText = errObj.message;
        }

        this.errorAlert.textContent = errorMessageText.trim();
        this.errorAlert.style.display = 'block';
    }

    /**
     * Funciones de validación
     */
    validateFullName(value) {
        const trimmedValue = value.trim();
        if (!trimmedValue) return JS_TEXTS.validation.emptyField;
        if (trimmedValue.length < 3) return JS_TEXTS.validation.nameMinLength;
        if (trimmedValue.length > 50) return JS_TEXTS.validation.nameMaxLength;
        if (!/^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$/.test(trimmedValue)) return JS_TEXTS.validation.nameRegex;
        return null;
    }

    validateDni(value) {
        const trimmedValue = value.trim();
        if (!trimmedValue) return { message: JS_TEXTS.validation.emptyField, isWarning: false };
        if (trimmedValue.length !== 10) return { message: JS_TEXTS.validation.dniExactLength, isWarning: false };
        if (!/^\d+$/.test(trimmedValue)) return { message: JS_TEXTS.validation.dniNumeric, isWarning: false };
        
        const coeficientes = [2, 1, 2, 1, 2, 1, 2, 1, 2];
        let total = 0;
        
        for (let i = 0; i < 9; i++) {
            let valor = parseInt(trimmedValue[i]) * coeficientes[i];
            if (valor > 9) valor -= 9;
            total += valor;
        }
        
        const digitoVerificador = (total % 10) === 0 ? 0 : 10 - (total % 10);
        if (digitoVerificador !== parseInt(trimmedValue[9])) {
            return { message: JS_TEXTS.validation.dniInvalid, isWarning: false };
        }
        
        return null;
    }

    validateEmail(value) {
        const trimmedValue = value.trim();
        if (!trimmedValue) return JS_TEXTS.validation.emptyField;
        if (trimmedValue.length > 254) return JS_TEXTS.validation.emailMaxLength;
        if (!/^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(trimmedValue)) {
            return JS_TEXTS.validation.emailInvalid;
        }
        return null;
    }

    validatePhone(value) {
        const trimmedValue = value.trim();
        if (!trimmedValue) return JS_TEXTS.validation.emptyField;
        if (!/^(\+593\s\d{2}\s\d{3}\s\d{4}|0\d{9})$/.test(trimmedValue)) {
            return JS_TEXTS.validation.phoneInvalidFormat;
        }
        return null;
    }

    validateAge(value) {
        if (!value) return JS_TEXTS.validation.emptyField;
        const age = parseInt(value);
        if (isNaN(age) || age < 0 || age > 120) return JS_TEXTS.validation.ageInvalid;
        return null;
    }

    /**
     * Funciones para manejo de mensajes de error
     */
    createErrorMessage(inputElement, message, isWarning = false) {
        this.removeErrorMessage(inputElement);
        const errorDiv = document.createElement('div');
        errorDiv.className = isWarning ? 'warning-message' : 'error-message';
        errorDiv.textContent = message;
        
        const parentContainer = inputElement.id === 'fileInput' ? 
                               this.uploadArea.parentNode : inputElement.parentNode;
        parentContainer.appendChild(errorDiv);
        inputElement.classList.add(isWarning ? 'warning' : 'error');
    }

    removeErrorMessage(inputElement) {
        const parentContainer = inputElement.id === 'fileInput' ? 
                               this.uploadArea.parentNode : inputElement.parentNode;
        const errorMsg = parentContainer.querySelector('.error-message, .warning-message');
        if (errorMsg) errorMsg.remove();
        inputElement.classList.remove('error', 'warning');
    }
}

/**
 * Función para inicializar la aplicación de upload
 */
function initializeUpload(jsTexts) {
    JS_TEXTS = jsTexts;
    new UploadManager();
}

// Exportar para uso en el template
window.initializeUpload = initializeUpload;