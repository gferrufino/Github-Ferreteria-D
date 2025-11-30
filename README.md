# 🛠️ Sistema de Gestión de Órdenes de Compra — Ferretería-D

---

## 📋 Descripción del Proyecto

Este proyecto consiste en un sistema web desarrollado con **Python** y **Streamlit** para la gestión integral de una Ferretería.  
Permite registrar órdenes de compra, emitir boletas con IVA, despachar productos a clientes, gestionar usuarios mediante login seguro y automatizar procesos mediante **CI/CD con GitHub Actions**.

El sistema utiliza **SQLite** como motor de base de datos y está diseñado siguiendo buenas prácticas de control de versiones usando ramas `feature`, `dev`, `qa` y `main`.

---

## 👥 Integrantes del Grupo

- 👨‍💻 **Abraham López** (Dev)
- 👨‍💻 **Gabriel Ferrufino** (Dev)
- 👨‍💻 **Jorge Albornoz** (Dev)

---

## 🎯 Requerimientos Funcionales (RF)

| Código | Descripción | Estado |
|--------|-------------|--------|
| **RF1** | Registro de órdenes de compra | ✔ Implementado |
| **RF2** | Login y control de usuario | ✔ Implementado |
| **RF3** | Menú principal (Home, Registrar, Listar) | ✔ Implementado |
| **RF4** | Emisión de boleta/factura con IVA (19%) | ✔ Implementado |
| **RF5** | Envío de productos con confirmación | ✔ Implementado |
| **RF6** | Pipeline CI/CD usando GitHub Actions (YAML) | ✔ Implementado |

---

## ⚙️ Tecnologías Utilizadas

### 🧰 Tecnologías principales

- **Python 3.11**
- **Streamlit** (Frontend Web)
- **SQLite** (Base de datos)
- **Git y GitHub**
- **GitHub Actions** (CI/CD)

### 📦 Librerías usadas

| Librería      | Uso |
|---------------|-----|
| `streamlit`   | Interfaz web |
| `pandas`      | Manejo de datos |
| `sqlite3`     | Conexión BD SQLite |
| `json`        | Manejo de ítems de órdenes |
| `hashlib`     | Hash de contraseñas |
| `secrets`     | Tokens seguros |

Instalación rápida:



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
├── database/
│ └── proyecto.db
│
├── evidencias/
│ ├── Evidencia Commits 1.png
│ ├── Evidencia Commits 2.png
│ ├── Evidencia Merge dev a qa.png
│ ├── Evidencia Merge qa a main.png
│ ├── Evidencia Merge.png
│ ├── ramas.png
│ └── Tablero Kanban.png
│
├── github/
│ └── workflows/
│ └── pipeline.yml ← (CI/CD)
│
├── src/
│ ├── pycache/
│ ├── app.py ← Aplicación principal Streamlit
│ ├── db.py ← Conexión y configuración BD
│ ├── login.py ← Login + usuarios
│ ├── menu.py ← Navegación UI
│ ├── orden_compra.py ← Órdenes, boletas, envíos
│ └── init.py
│
├── .gitignore
└── README.md
