document.addEventListener("DOMContentLoaded", () => {
  const emptyMsg = 'El campo está vacío, por favor rellénelo.';
  
  const createErrorDiv = input => {
    let div = input.parentElement.querySelector('.error-message-js');
    if (!div) {
      div = document.createElement('div');
      div.className = 'error-message error-message-js';
      div.style.marginTop = '5px';
      input.parentElement.appendChild(div);
    }
    return div;
  };
  
  const showError = (input, msg) => createErrorDiv(input).textContent = msg;
  
  const clearError = input => {
    const div = input.parentElement.querySelector('.error-message-js');
    if (div) div.remove();
  };
  
  const onBlurValidate = (input, fn) => {
    input.addEventListener('blur', () => fn(input));
    input.addEventListener('input', () => {
      if (input.parentElement.querySelector('.error-message-js')) fn(input);
    });
  };
  
  document.querySelectorAll('.alert').forEach(alert => {
    if (!alert.querySelector('.close-btn')) {
      const btn = document.createElement('button');
      btn.className = 'close-btn';
      btn.textContent = '×';
      Object.assign(btn.style, {
        float: 'right',
        background: 'none',
        border: 'none',
        fontSize: '1.2rem',
        cursor: 'pointer',
        marginLeft: '10px'
      });
      btn.onclick = () => alert.style.display = 'none';
      alert.insertBefore(btn, alert.firstChild);
    }
  });
  
  setTimeout(() => {
    document.querySelectorAll('.alert').forEach(alert => {
      alert.style.transition = 'opacity 0.5s';
      alert.style.opacity = '0';
      setTimeout(() => alert.style.display = 'none', 500);
    });
  }, 5000);
  
  const validators = {
    fullName: v => {
      if (!v) return emptyMsg;
      if (v.length < 3) return 'Debe tener al menos 3 caracteres.';
      if (v.length > 50) return 'No puede tener más de 50 caracteres.';
      if (!/^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$/.test(v)) return 'Solo letras y espacios.';
    },
    email: v => {
      if (!v) return emptyMsg;
      if (v.length > 50) return 'Máx. 50 caracteres.';
      if (!/^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/.test(v)) return 'Ingrese un correo válido.';
    },
    dni: v => {
      if (!/^[0-9]{10}$/.test(v)) return 'La cédula debe tener 10 dígitos numéricos.';
      const coef = [2, 1, 2, 1, 2, 1, 2, 1, 2];
      let sum = [...v].slice(0, 9).reduce((a, d, i) => {
        let p = +d * coef[i];
        return a + (p > 9 ? p - 9 : p);
      }, 0);
      if (((sum * 9) % 10) != +v[9]) return 'La cédula no es válida.';
    },
    addressCity: v => {
      if (!v) return;
      if (v.length > 255) return 'Máx. 255 caracteres.';
      if (!/^[A-Za-zÁÉÍÓÚáéíóúÑñ.\s]+$/.test(v)) return 'Solo letras, puntos y espacios.';
    },
    phone: v => {
      if (!v) return;
      if (v.length > 16) return 'Máx. 16 caracteres.';
      if (!/^(\+593\s\d{2}\s\d{3}\s\d{4}|0\d{9})$/.test(v)) return 'Formato: 0995336523 o +593 99 533 6523.';
    },
    password: v => {
      if (!v) return emptyMsg;
      if (v.length < 8) return 'La contraseña debe tener al menos 8 caracteres.';
    },
    confirmPassword: (v, p1) => {
      if (!v) return emptyMsg;
      if (v !== p1) return 'Las contraseñas no coinciden.';
    }
  };
  
  [
    ['id_first_name', 'fullName'], 
    ['id_last_name', 'fullName'],
    ['id_email', 'email'], 
    ['id_dni', 'dni'],
    ['id_address', 'addressCity'], 
    ['id_city', 'addressCity'], 
    ['id_phone', 'phone']
  ].forEach(([id, key]) => {
    const el = document.getElementById(id);
    if (el) onBlurValidate(el, inp => {
      const msg = validators[key](inp.value.trim());
      msg ? showError(inp, msg) : clearError(inp);
    });
  });
  
  const p1 = document.getElementById('id_password1');
  const p2 = document.getElementById('id_password2');
  if (p1) onBlurValidate(p1, inp => {
    const msg = validators.password(inp.value.trim());
    msg ? showError(inp, msg) : clearError(inp);
  });
  if (p2 && p1) onBlurValidate(p2, inp => {
    const msg = validators.confirmPassword(inp.value.trim(), p1.value.trim());
    msg ? showError(inp, msg) : clearError(inp);
  });
  
  const lE = document.getElementById('id_username');
  const lP = document.getElementById('id_password');
  if (lE) onBlurValidate(lE, inp => {
    const msg = validators.email(inp.value.trim());
    msg ? showError(inp, msg) : clearError(inp);
  });
  if (lP) onBlurValidate(lP, inp => {
    const msg = !inp.value.trim() ? emptyMsg : null;
    msg ? showError(inp, msg) : clearError(inp);
  });
});
