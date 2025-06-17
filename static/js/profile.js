document.addEventListener("DOMContentLoaded", function () {
  // Elementos del archivo de perfil
  const profileInput = document.getElementById("id_profile_picture");
  const previewImg = document.getElementById("profile-preview");
  const fileStatus = document.querySelector(".file-status");
  const fileButton = document.querySelector(".file-button");

  // Elementos de los campos del formulario
  const firstNameInput = document.getElementById("{{ form.first_name.id_for_label }}");
  const lastNameInput = document.getElementById("{{ form.last_name.id_for_label }}");
  const dniInput = document.getElementById("{{ form.dni.id_for_label }}");
  const emailInput = document.getElementById("{{ form.email.id_for_label }}");
  const addressInput = document.getElementById("{{ form.address.id_for_label }}");
  const cityInput = document.getElementById("{{ form.city.id_for_label }}");
  const phoneInput = document.getElementById("{{ form.phone.id_for_label }}");

  const form = document.querySelector("form");
  const updateBtn = form.querySelector(".btn-update");
  const updateBtnText = 'Actualizar Perfil';

  // Variable para rastrear si la foto de perfil es válida
  let profilePictureValid = false;

  // Guardar valores iniciales de los campos
  const initialValues = {};
  [firstNameInput, lastNameInput, dniInput, emailInput, addressInput, cityInput, phoneInput].forEach(function (input) {
    if (input) {
      initialValues[input.name] = (input.value || "").trim();
    }
  });

  // Icono de candado y tooltip
  function setLockIconAndTooltip(show) {
    if (!updateBtn) return;
    if (show) {
      updateBtn.innerHTML = '<i class="fa fa-lock"></i> ' + updateBtnText;
      updateBtn.setAttribute("title", "SE HABILITARÁ CUANDO REALICE ALGÚN CAMBIO EN EL FORMULARIO");
    } else {
      updateBtn.innerHTML = updateBtnText;
      updateBtn.removeAttribute("title");
    }
  }

  // Verificar si el formulario ha cambiado
  function isFormChanged() {
    let changed = profilePictureValid;
    [firstNameInput, lastNameInput, dniInput, emailInput, addressInput, cityInput, phoneInput].forEach(function (input) {
      if (input) {
        const current = (input.value || "").trim();
        if (current !== initialValues[input.name]) {
          changed = true;
        }
      }
    });
    return changed;
  }

  // Habilitar/deshabilitar botón según cambios
  function checkFormChangeAndToggleBtn() {
    if (isFormChanged()) {
      updateBtn.disabled = false;
      setLockIconAndTooltip(false);
    } else {
      updateBtn.disabled = true;
      setLockIconAndTooltip(true);
    }
  }

  // Deshabilitar el botón al cargar y poner candado
  if (updateBtn) {
    updateBtn.disabled = true;
    setLockIconAndTooltip(true);
  }

  // Detectar cambios en los campos de texto
  [firstNameInput, lastNameInput, dniInput, emailInput, addressInput, cityInput, phoneInput].forEach(function (input) {
    if (input) {
      input.addEventListener("input", checkFormChangeAndToggleBtn);
      input.addEventListener("blur", checkFormChangeAndToggleBtn);
    }
  });

  // Función para crear mensajes de error
  function createErrorMessage(input, message, isWarning = false) {
    removeErrorMessage(input);
    const errorDiv = document.createElement("div");
    errorDiv.className = isWarning ? "warning-message" : "error-message";
    errorDiv.textContent = message;
    input.parentNode.appendChild(errorDiv);
    if (!isWarning) {
      input.classList.add("error");
    } else {
      input.classList.add("warning");
    }
  }

  // Función para remover mensajes de error
  function removeErrorMessage(input) {
    const errorMsg = input.parentNode.querySelector(".error-message");
    const warningMsg = input.parentNode.querySelector(".warning-message");
    if (errorMsg) errorMsg.remove();
    if (warningMsg) warningMsg.remove();
    input.classList.remove("error", "warning");
  }

  // Validación de imagen de perfil
  function validateProfilePicture(file) {
    if (!file) {
      return {message: "El campo esta vacio (opcional rellenarlo)", isWarning: true};
    }
    const validExtensions = ["png", "jpg", "jpeg"];
    const extension = file.name.split(".").pop().toLowerCase();
    if (!validExtensions.includes(extension)) {
      return {message: "Solo se permiten imágenes en formato PNG, JPG o JPEG.", isWarning: false};
    }
    return null;
  }

  // Manejo de la foto de perfil
  if (profileInput) {
    profileInput.addEventListener("change", function () {
      removeErrorMessage(this);
      if (this.files && this.files[0]) {
        const result = validateProfilePicture(this.files[0]);
        if (result && !result.isWarning) {
          createErrorMessage(this, result.message, result.isWarning);
          profilePictureValid = false;
        } else {
          if (result && result.isWarning) {
            createErrorMessage(this, result.message, result.isWarning);
          }
          profilePictureValid = true;
          const reader = new FileReader();
          reader.onload = function (e) {
            if (previewImg) {
              previewImg.src = e.target.result;
            }
          };
          reader.readAsDataURL(this.files[0]);
        }
      } else {
        profilePictureValid = false;
      }
      checkFormChangeAndToggleBtn();
    });
  }

  // Validación de email
  function validateEmail(value) {
    const trimmedValue = value.trim();
    if (!trimmedValue) {
      return "El campo está vacío, por favor rellénelo.";
    }
    if (trimmedValue.length > 50) {
      return "El correo electrónico no puede tener más de 50 caracteres.";
    }
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    if (!emailRegex.test(trimmedValue)) {
      return "Ingrese un correo electrónico válido.";
    }
    return null;
  }

  // Validación de nombres completos
  function validateFullName(value) {
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

  // Validación de DNI
  function validateDni(value) {
    const trimmedValue = value.trim();
    if (!trimmedValue) {
      return {message: "El campo esta vacio (opcional rellenarlo)", isWarning: true};
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
      const digito = parseInt(trimmedValue[i]);
      const coeficiente = coeficientes[i];
      let producto = digito * coeficiente;
      if (producto > 9) {
        producto -= 9;
      }
      total += producto;
    }
    const digitoVerificador = (total * 9) % 10;
    if (digitoVerificador !== parseInt(trimmedValue[9])) {
      return {message: "La cédula no es válida.", isWarning: false};
    }
    return null;
  }

  // Validación de dirección y ciudad
  function validateAddressAndCity(value) {
    const trimmedValue = value.trim();
    if (!trimmedValue) {
      return {message: "El campo esta vacio (opcional rellenarlo)", isWarning: true};
    }
    if (trimmedValue.length > 255) {
      return {message: "El campo no puede tener más de 255 caracteres.", isWarning: false};
    }
    if (trimmedValue.length < 5) {
      return {message: "El campo debe tener mas de 5 caracteres.", isWarning: false};
    }
    const addressRegex = /^[a-zA-ZáéíóúÁÉÍÓÚñÑ.\s]+$/;
    if (!addressRegex.test(trimmedValue)) {
      return {
        message: "El campo solo puede contener letras y espacios, incluyendo caracteres especiales como la Ñ, letras con tilde o Puntuación ( . ).",
        isWarning: false
      };
    }
    return null;
  }

  // Validación de teléfono
  function validatePhone(value) {
    const trimmedValue = value.trim();
    if (!trimmedValue) {
      return {message: "El campo esta vacio (opcional rellenarlo)", isWarning: true};
    }
    if (trimmedValue.length > 16) {
      return {message: "El campo no puede tener más de 16 caracteres.", isWarning: false};
    }
    const phoneRegex = /^(\+593\s\d{2}\s\d{3}\s\d{4}|0\d{9})$/;
    if (!phoneRegex.test(trimmedValue)) {
      return {
        message: "El teléfono debe estar en un formato válido, como 0995336523 o +593 99 533 6523. Solo digitos y el unico caracter ( + )",
        isWarning: false
      };
    }
    return null;
  }

  // Event listeners para validación en blur

  // Nombres (obligatorio)
  if (firstNameInput) {
    firstNameInput.addEventListener("blur", function () {
      const error = validateFullName(this.value);
      if (error) {
        createErrorMessage(this, error);
      } else {
        removeErrorMessage(this);
      }
    });
  }

  // Apellidos (obligatorio)
  if (lastNameInput) {
    lastNameInput.addEventListener("blur", function () {
      const error = validateFullName(this.value);
      if (error) {
        createErrorMessage(this, error);
      } else {
        removeErrorMessage(this);
      }
    });
  }

  // Email (obligatorio)
  if (emailInput) {
    emailInput.addEventListener("blur", function () {
      const error = validateEmail(this.value);
      if (error) {
        createErrorMessage(this, error);
      } else {
        removeErrorMessage(this);
      }
    });
  }

  // DNI (opcional)
  if (dniInput) {
    dniInput.addEventListener("blur", function () {
      const result = validateDni(this.value);
      if (result) {
        createErrorMessage(this, result.message, result.isWarning);
      } else {
        removeErrorMessage(this);
      }
    });
  }

  // Dirección (opcional)
  if (addressInput) {
    addressInput.addEventListener("blur", function () {
      const result = validateAddressAndCity(this.value);
      if (result) {
        createErrorMessage(this, result.message, result.isWarning);
      } else {
        removeErrorMessage(this);
      }
    });
  }

  // Ciudad (opcional)
  if (cityInput) {
    cityInput.addEventListener("blur", function () {
      const result = validateAddressAndCity(this.value);
      if (result) {
        createErrorMessage(this, result.message, result.isWarning);
      } else {
        removeErrorMessage(this);
      }
    });
  }

  // Teléfono (opcional)
  if (phoneInput) {
    phoneInput.addEventListener("blur", function () {
      const result = validatePhone(this.value);
      if (result) {
        createErrorMessage(this, result.message, result.isWarning);
      } else {
        removeErrorMessage(this);
      }
    });
  }
});