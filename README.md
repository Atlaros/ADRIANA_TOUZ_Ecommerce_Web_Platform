# ADRIANA TOUZ - Plataforma Web de E-commerce

Este repositorio contiene la plataforma de comercio electrónico **ADRIANA TOUZ**, una aplicación moderna desarrollada con Streamlit que ofrece una experiencia de compra intuitiva y segura para una marca de moda exclusiva.

## 🚀 Demo en Vivo

Accede a la plataforma desplegada en Streamlit Cloud:

[https://xperience-ecommerce.streamlit.app/](https://xperience-ecommerce.streamlit.app/)

---

## ✨ Funcionalidades Principales

* **🔐 Autenticación con Google OAuth 2.0**: Inicio de sesión seguro y creación automática de usuarios.
* **🛒 Carrito de Compras Inteligente**: Añade, elimina y visualiza productos con persistencia en tiempo real en Firebase.
* **💳 Pago Seguro con Stripe**: Integración con Stripe Checkout para procesar pagos exitosos y gestionar cancelaciones.
* **📱 Diseño Responsive**: Interfaz adaptable a dispositivos móviles, tablets y escritorio.
* **📦 Control de Inventario Automático**: Actualización de stock tras cada orden exitosa.
* **📊 Panel de Administración Básico**: Vista de órdenes, usuarios y estado de colecciones en Firebase.

---

## 🛠 Tecnologías y Herramientas

* **Lenguaje**: Python 3.8+
* **Framework**: Streamlit
* **Base de Datos**: Firebase Firestore
* **Autenticación**: Google OAuth 2.0
* **Pasarela de Pagos**: Stripe API
* **Almacenamiento de Archivos**: Firebase Storage
* **Gestión de Variables de Entorno**: python-dotenv

---

## ⚙️ Instalación y Configuración

1. **Clonar el repositorio**

   ```bash
   git clone https://github.com/BootcampXperience/DS_Ecommerce_Web_Platform.git
   cd DS_Ecommerce_Web_Platform
   ```

2. **Instalar dependencias**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configurar variables de entorno**

   * Renombrar el archivo `.env.example` a `.env`
   * Añadir las siguientes variables:

     ```ini
     GOOGLE_CLIENT_ID=<tu_google_client_id>
     GOOGLE_SECRET_ID=<tu_google_secret_id>
     STRIPE_SECRET_KEY=<tu_stripe_secret_key>
     ```

4. **Configurar Firebase**

   * Descarga `serviceAccountKey.json` desde tu consola de Firebase y colócalo en la raíz del proyecto.
   * En Firebase Console, habilita Authentication (Google), Firestore Database y Storage.

5. **Ejecutar la aplicación**

   ```bash
   streamlit run app.py
   ```

---

## 📁 Estructura del Proyecto

```bash
DS_Ecommerce_Web_Platform/
├── app.py                    # Archivo principal de Streamlit
├── pages/                    # Páginas secundarias de la aplicación
│   ├── catalogo.py           # Catálogo de productos
│   └── compraok.py           # Página de confirmación de compra
├── estilos/                  # Archivos de estilos personalizados
│   ├── css_login.html
│   ├── css_catalogo.html
│   └── css_compra.html
├── serviceAccountKey.json    # Credenciales de Firebase (no subir a Git)
├── .env.example              # Plantilla de variables de entorno
├── requirements.txt          # Dependencias
└── README.md                 # Documentación del proyecto
```

---

## 🔧 Flujo de Configuración de Firebase

1. **Authentication**

   * Habilitar Google como proveedor.
2. **Firestore**

   * Crear colecciones: `usuarios`, `products`, `carts`, `orders`.
3. **Storage**

   * Configurar reglas de acceso para almacenar imágenes y recursos.

---

## 🎯 Mejoras Futuras

* [ ] Dashboard administrativo avanzado
* [ ] Sistema de reseñas y calificaciones
* [ ] Wishlist y lista de deseos
* [ ] Soporte multi-moneda
* [ ] Notificaciones por correo o push
* [ ] Gestión de cupones y descuentos

---

## ⚖️ Licencia

Este proyecto está bajo la licencia MIT. Consulta el archivo [LICENSE](LICENSE) para más detalles.
