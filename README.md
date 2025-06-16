Claro, aquí tienes una versión reestructurada y mejorada del `README.md`. Está diseñada para ser más clara, profesional y fácil de navegar, utilizando tablas de manera efectiva, mejorando la jerarquía de la información y haciendo la estructura del proyecto más visual y comprensible.

He organizado el contenido en secciones lógicas, he añadido un índice para facilitar la navegación y he utilizado elementos de Markdown como blockquotes y tablas para resaltar la información importante. La estructura de archivos ahora es más legible y está mejor comentada.

Puedes copiar y pegar directamente el siguiente código en tu archivo `README.md`.

***

### Código del README.md para Copiar y Pegar:

````markdown
# Sistema de Análisis Dermatológico con Inteligencia Artificial

Un sistema web avanzado que combina un modelo de Deep Learning personalizado con la IA Generativa de Google Gemini para ofrecer un pre-diagnóstico preciso de condiciones dermatológicas.

[![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.2-darkgreen?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![TensorFlow](https://img.shields.io/badge/TensorFlow-2.19-orange?logo=tensorflow&logoColor=white)](https://www.tensorflow.org/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple?logo=bootstrap&logoColor=white)](https://getbootstrap.com/)

---

## 📚 Índice

- [📖 Descripción del Proyecto](#-descripción-del-proyecto)
- [✨ Características Principales](#-características-principales)
- [🛠️ Stack Tecnológico](#️-stack-tecnológico)
- [📁 Arquitectura del Proyecto](#-arquitectura-del-proyecto)
- [🚀 Guía de Instalación y Ejecución](#-guía-de-instalación-y-ejecución)
- [💻 Uso del Sistema](#-uso-del-sistema)
- [🩺 Condiciones Soportadas](#-condiciones-soportadas)
- [⚠️ Aviso Médico Importante](#️-aviso-médico-importante)
- [👥 Equipo del Proyecto](#-equipo-del-proyecto)
- [🤝 Contribuciones](#-contribuciones)

---

## 📖 Descripción del Proyecto

Este proyecto es un sistema web integral desarrollado en **Django** que utiliza una arquitectura de **inteligencia artificial dual** para el análisis preliminar de imágenes dermatológicas. La plataforma integra:

1.  Un modelo de **Deep Learning (CNN basado en MobileNetV2)** entrenado para clasificar 25 condiciones de la piel.
2.  La **API de Google Gemini** para interpretar los resultados, generar descripciones detalladas, ofrecer recomendaciones y crear reportes en lenguaje natural.

El sistema no solo proporciona un diagnóstico automatizado, sino que también ofrece **visualizaciones explicativas (Grad-CAM)** para entender qué áreas de la imagen influyeron en la decisión del modelo, junto con una gestión completa de pacientes y la generación de reportes profesionales en PDF.

## ✨ Características Principales

-   🧠 **Análisis Dual con IA:** Combinación de un modelo CNN propio y la IA generativa de Gemini para maximizar la precisión y la calidad de la descripción.
-   🎨 **Visualización Explicativa (XAI):** Generación de mapas de calor Grad-CAM que resaltan las áreas de interés en la imagen, haciendo el diagnóstico del modelo interpretable.
-   🖼️ **Interfaz Intuitiva:** Sistema de carga de imágenes `drag-and-drop` con validación de datos en tiempo real para una experiencia de usuario fluida.
-   👨‍⚕️ **Gestión Completa de Pacientes:** Módulo para registrar pacientes, gestionar su información personal y clínica, y mantener un historial completo de sus análisis.
-   📄 **Reportes Profesionales:** Generación automática de reportes en PDF con el diagnóstico, imágenes (original y Grad-CAM), y recomendaciones, listos para ser enviados por email.
-   🔒 **Seguridad y Autenticación:** Sistema robusto de gestión de usuarios, middleware de seguridad personalizado y protección de datos sensibles.

## 🛠️ Stack Tecnológico

| Categoría                 | Tecnología                                                                                                 |
| ------------------------- | ---------------------------------------------------------------------------------------------------------- |
| **Backend** | `Python 3.10+`, `Django 5.2`                                                                               |
| **Base de Datos** | `PostgreSQL` (producción), `SQLite3` (desarrollo)                                                          |
| **Inteligencia Artificial** | `TensorFlow 2.19`, `Keras`, `Google Gemini AI API`, `OpenCV`, `Scikit-learn`, `NumPy`, `Pandas`             |
| **Frontend** | `HTML5`, `CSS3`, `JavaScript (ES6+)`, `Bootstrap 5.3`, `Font Awesome`                                        |
| **Generación de Reportes** | `ReportLab`, `Pillow`                                                                                      |
| **Servicios en la Nube** | `Amazon S3` (para almacenamiento de archivos estáticos y media)                                            |
| **Entorno y Despliegue** | `Git`, `Docker` (opcional), `Gunicorn`/`Nginx` (producción)                                                  |

## 📁 Arquitectura del Proyecto

La estructura del proyecto está diseñada para ser modular y escalable, separando las responsabilidades en diferentes aplicaciones de Django.

```
Proyecto_Final_IA_Dermatologia/
├── 📁 apps/                           # Aplicaciones Django modulares
│   ├── 📁 auth/                       # Gestión de usuarios y autenticación
│   └── 📁 Dermatologia_IA/            # Módulo principal de IA y gestión de pacientes
│
├── 📁 IA/                             # Recursos de Inteligencia Artificial
│   └── 📁 Dermatological_AI_Model/    # Modelo entrenado y checkpoints
│       └── 📄 MODELO_IA_DERMATOLOGICO.keras
│
├── 📁 core/                           # Configuración principal de Django
│   ├── 📄 settings.py                 # Configuración del proyecto
│   └── 📄 urls.py                     # URLs principales
│
├── 📁 media/                          # Archivos subidos por los usuarios (en S3 en producción)
│   ├── 📁 skin_images/               # Imágenes de piel para análisis
│   ├── 📁 gradcam_images/            # Mapas de calor generados
│   ├── 📁 profile_pictures/          # Avatares de usuarios
│   └── 📁 reports/                   # Reportes PDF generados
│
├── 📁 static/                         # Archivos estáticos (CSS, JS, imágenes)
│   ├── 📁 css/
│   ├── 📁 js/
│   └── 📁 img/
│
├── 📁 templates/                      # Plantillas HTML de Django
│
├── 📁 utils/                          # Módulos de utilidad reutilizables
│   ├── 📄 logger.py                  # Sistema de logging personalizado
│   ├── 📄 validators.py              # Funciones de validación (ej. Cédula Ecuador)
│   └── 📄 s3_storage.py              # Configuración de almacenamiento en S3
│
├── 📄 manage.py                       # Script de gestión de Django
├── 📄 requirements.txt                # Lista de dependencias de Python
└── 📄 .env.example                    # Plantilla para variables de entorno
```

## 🚀 Guía de Instalación y Ejecución

### Prerrequisitos

-   Python `3.10` o superior.
-   `pip` y `venv` para la gestión de paquetes y entornos.
-   `Git` para clonar el repositorio.
-   Una cuenta de **Google AI Studio** para obtener la `GEMINI_API_KEY`.
-   (Opcional) Una cuenta de **AWS** para el almacenamiento en S3.

### Pasos de Instalación

1.  **Clonar el Repositorio**
    ```bash
    git clone [https://github.com/JavicSoftCode-01/Proyecto_Final_IA_Dermatologia.git](https://github.com/JavicSoftCode-01/Proyecto_Final_IA_Dermatologia.git)
    cd Proyecto_Final_IA_Dermatologia
    ```

2.  **Crear y Activar un Entorno Virtual**
    ```bash
    # En Windows
    python -m venv venv
    venv\Scripts\activate

    # En macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Instalar las Dependencias**
    ```bash
    pip install --upgrade pip
    pip install -r requirements.txt
    ```

4.  **Configurar Variables de Entorno**
    Crea un archivo `.env` en la raíz del proyecto (puedes copiar y renombrar `.env.example`) y llénalo con tus credenciales.
    ```env
    # Clave secreta de Django (genera una nueva, no uses esta)
    DJANGO_SECRET_KEY='django-insecure-xxxxxxxxxxxxxxxxxxxxxxxxxxxx'
    DEBUG=True

    # Clave de la API de Gemini
    GEMINI_API_KEY='tu_api_key_de_gemini_aqui'

    # Configuración de AWS S3 (opcional, si USE_S3 es True)
    USE_S3=False
    AWS_ACCESS_KEY_ID='tu_access_key_aqui'
    AWS_SECRET_ACCESS_KEY='tu_secret_key_aqui'
    AWS_STORAGE_BUCKET_NAME='tu_bucket_name'
    AWS_S3_REGION_NAME='us-east-1' # o tu región
    ```

5.  **Aplicar Migraciones de la Base de Datos**
    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```

6.  **Crear un Superusuario** (para acceder al panel de admin)
    ```bash
    python manage.py createsuperuser
    ```

7.  **Ejecutar el Servidor de Desarrollo**
    ```bash
    python manage.py runserver
    ```

    Ahora puedes acceder al sistema en tu navegador:
    -   **Página principal:** `http://127.0.0.1:8000/`
    -   **Panel de Administración:** `http://127.0.0.1:8000/admin/`

## 💻 Uso del Sistema

1.  **Registro / Inicio de Sesión:** Crea una cuenta de usuario o inicia sesión.
2.  **Gestión de Pacientes:** Desde el dashboard, puedes registrar nuevos pacientes o buscar existentes.
3.  **Realizar un Análisis:**
    -   Ve a la sección de "Nuevo Análisis".
    -   Sube una imagen de la lesión cutánea usando el área de `drag-and-drop`.
    -   Asocia el análisis a un paciente existente o crea uno nuevo.
    -   Inicia el análisis y espera los resultados.
4.  **Consultar Resultados:**
    -   El sistema mostrará el diagnóstico principal, el porcentaje de confianza y el mapa de calor Grad-CAM.
    -   La IA de Gemini proveerá una descripción detallada y recomendaciones.
5.  **Generar y Enviar Reporte:** Puedes descargar el informe completo en PDF o enviarlo directamente por correo electrónico al paciente.

## 🩺 Condiciones Soportadas

El modelo de IA está entrenado para identificar 25 condiciones dermatológicas distintas.

<details>
<summary><b>Haz clic aquí para ver la lista completa de condiciones</b></summary>
<br>

| Código | Condición                      | Tipo de Afección                    |
| :----- | :----------------------------- | :---------------------------------- |
| `MEL`  | Melanoma                       | Cáncer de Piel (Maligno)            |
| `BCC`  | Carcinoma de Células Basales   | Cáncer de Piel (Maligno)            |
| `SCC`  | Carcinoma de Células Escamosas | Cáncer de Piel (Maligno)            |
| `AK`   | Queratosis Actínica            | Lesión Pre-cancerosa                |
| `NV`   | Nevus (Lunar)                  | Lesión Benigna                      |
| `BKL`  | Queratosis Benigna             | Lesión Benigna                      |
| `DF`   | Dermatofibroma                 | Tumor Benigno                       |
| `VASC` | Lesiones Vasculares            | Afección Vascular                   |
| `ACN`  | Acné                           | Afección Inflamatoria               |
| `ROS`  | Rosácea                        | Enfermedad Inflamatoria Crónica     |
| `DER`  | Dermatitis                     | Inflamación de la Piel              |
| `ECZ`  | Eczema (Dermatitis Atópica)    | Inflamación de la Piel              |
| `PSO`  | Psoriasis                      | Enfermedad Autoinmune               |
| `IMP`  | Impétigo                       | Infección Bacteriana                |
| `CEL`  | Celulitis                      | Infección Bacteriana (Subcutánea)   |
| `RIN`  | Tiña (Ringworm)                | Infección Fúngica                   |
| `HER`  | Herpes                         | Infección Viral                     |
| `WAR`  | Verrugas                       | Infección Viral                     |
| `CPX`  | Varicela (Chickenpox)          | Infección Viral                     |
| `SHG`  | Herpes Zóster (Shingles)       | Infección Viral                     |
| `LUP`  | Lupus                          | Enfermedad Autoinmune Sistémica     |
| `HIV`  | Manifestaciones del VIH        | Relacionado con Inmunodeficiencia   |
| `SCA`  | Sarna (Scabies)                | Infestación Parasitaria             |
| `VAS`  | Vasculitis                     | Inflamación de Vasos Sanguíneos     |
| `UNK`  | Desconocido                    | Condición No Identificada           |

</details>

---

## ⚠️ Aviso Médico Importante

> **Este sistema es una herramienta de apoyo y no reemplaza un diagnóstico médico profesional.**
>
> Los resultados generados por la inteligencia artificial son preliminares y deben ser interpretados y validados por un dermatólogo certificado. El objetivo de esta plataforma es asistir a los profesionales de la salud, no sustituir su juicio clínico. Los creadores no se hacen responsables del uso indebido de la información proporcionada.

---

## 👥 Equipo del Proyecto

-   **Gabriel Leonardo Hasqui Ortega**
-   **Eduardo Javier Quinteros Pacheco**
-   **Gleyder Julissa Lescano Paredes**

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Si deseas colaborar, sigue estos pasos:

1.  Haz un **Fork** de este repositorio.
2.  Crea una nueva rama (`git checkout -b feature/nueva-caracteristica`).
3.  Realiza tus cambios y haz **commit** (`git commit -m 'Añade nueva característica'`).
4.  Haz **push** a tu rama (`git push origin feature/nueva-caracteristica`).
5.  Abre un **Pull Request** para que revisemos tus cambios.

Por favor, asegúrate de seguir los estándares de código (PEP 8) y de documentar cualquier nueva funcionalidad.
````