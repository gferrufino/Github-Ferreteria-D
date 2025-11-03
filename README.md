# 🛠️ **Sistema de Gestión de Órdenes de Compra — Ferretería**

---

## 📋 **Descripción del Proyecto**

Este proyecto consiste en un sistema web desarrollado con **Python** y **Streamlit** para la gestión de **Órdenes de Compra** en una ferretería.  
Permite registrar nuevas órdenes, almacenarlas en una base de datos **SQLite**, listar las órdenes registradas y controlar el acceso mediante un **login seguro**.

---

## 👥 **Integrantes del Grupo**

- 👨‍💻 **Abraham López** _(Dev)_
- 👨‍🎓 **Gabriel Ferrufino** _(Dev)_
- 👨‍🎓 **Jorge Albornoz** _(Dev)_

---

## ⚙️ **Requerimientos Técnicos y Librerías Usadas**

### 🧰 **Tecnologías**

- **Lenguaje:** Python 3.10 o superior
- **Framework UI:** Streamlit
- **Base de Datos:** SQLite
- **Entorno de Desarrollo:** Visual Studio Code
- **Control de Versiones:** Git + GitHub

---

### 📦 **Librerías**

| Librería             | Uso Principal                                     |
| -------------------- | ------------------------------------------------- |
| `streamlit`          | Interfaz web interactiva                          |
| `sqlite3`            | Conexión con la base de datos SQLite              |
| `hashlib`, `secrets` | Hash y seguridad de contraseñas                   |
| `json`               | Almacenamiento de ítems de compra en formato JSON |

**Instalación rápida:**

```bash
pip install streamlit

▶️ Instrucciones de Ejecución
1️⃣ Clonar o descargar el repositorio
git clone https://github.com/tu-usuario/Proyecto_Empresa.git
cd Proyecto_Empresa

2️⃣ (Opcional) Crear un entorno virtual
python -m venv venv
venv\Scripts\activate

3️⃣ Instalar dependencias
pip install streamlit

4️⃣ Ejecutar la aplicación

Desde la carpeta raíz del proyecto:

streamlit run src/app.py


o bien:

python -m streamlit run src/app.py

5️⃣ Abrir en el navegador

Cuando aparezca el mensaje:

You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501


Abre esa dirección en tu navegador.

6️⃣ Credenciales iniciales

👤 Usuario: admin

🔑 Contraseña: admin123

🧱 Estructura del Proyecto
Proyecto_Empresa/
├── src/
│   ├── app.py
│   ├── login.py
│   ├── orden_compra.py
│   ├── menu.py
│   └── __init__.py
│
├── database/
│   └── proyecto.db
│
├── evidencias/
│
├── README.md
└── .gitignore
```
