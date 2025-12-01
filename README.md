# 🛠️ **Sistema de Gestión de Órdenes de Compra — Ferretería-D**

Sistema web desarrollado con Python y Streamlit para la gestión integral de una ferretería, incluyendo órdenes de compra, emisión de boletas con IVA, autenticación de usuarios, despachos y despliegue automatizado mediante CI/CD y Streamlit Cloud.

---

# 📋 **1. Descripción General del Proyecto**

Este sistema permite:

- Registrar órdenes de compra con múltiples productos.
- Autenticar usuarios mediante login seguro.
- Emitir boletas/facturas con IVA del 19%.
- Confirmar envíos y despachos.
- Listar órdenes registradas.
- Mantener base de datos con SQLite.
- Implementar CI/CD con GitHub Actions.
- Desplegar automáticamente en Streamlit Cloud.

Aplicación desplegada:
https://app-ferreteria-d-e6yingxwuyjgzjuxyejq5s.streamlit.app/

---

# 👥 **2. Integrantes del Equipo**

- Abraham López — Developer
- Gabriel Ferrufino — Developer
- Jorge Albornoz — Developer

---

# 🎯 **3. Requerimientos Funcionales**

RF1: Registro de órdenes de compra — Implementado  
RF2: Login y autenticación — Implementado  
RF3: Menú principal — Implementado  
RF4: Emisión de boleta — Implementado  
RF5: Registro de despachos — Implementado  
RF6: Pipeline CI/CD — Implementado  
RF7: Despliegue Streamlit Cloud — Implementado  
RF8: Gestión SQLite — Implementado

---

# ⚙️ **4. Tecnologías Utilizadas**

Python 3.11  
Streamlit  
SQLite  
Git y GitHub  
GitHub Actions  
Streamlit Cloud

Librerías:
streamlit, pandas, sqlite3, json, hashlib, secrets, pytest

---

# 📦 **5. Instalación y Configuración**

Instalar dependencias con requirements.txt:
pip install -r requirements.txt

Instalación rápida:
pip install streamlit

---

# ▶️ **6. Instrucciones de Ejecución**

1. Clonar el repositorio:
   git clone https://github.com/tu-usuario/Proyecto_Empresa.git
   cd Proyecto_Empresa

2. Crear entorno virtual (opcional):
   python -m venv venv
   venv\Scripts\activate (Windows)
   source venv/bin/activate (Linux/Mac)

3. Instalar dependencias:
   pip install -r requirements.txt

4. Ejecutar la aplicación:
   streamlit run src/app.py
   o
   python -m streamlit run src/app.py

5. Abrir en el navegador:
   http://localhost:8501

6. Credenciales:
   Usuario: admin
   Contraseña: admin123

---

# 🧱 **7. Estructura del Proyecto**

Proyecto_Empresa/
├── database/
│ └── proyecto.db
├── evidencias/
│ ├── Evidencia Commits 1.png
│ ├── Evidencia Commits 2.png
│ ├── Evidencia Merge dev a qa.png
│ ├── Evidencia Merge qa a main.png
│ ├── Evidencia Merge.png
│ ├── ramas.png
│ └── Tablero Kanban.png
├── github/
│ └── workflows/
│ └── pipeline.yml
├── src/
│ ├── app.py
│ ├── db.py
│ ├── login.py
│ ├── menu.py
│ ├── orden_compra.py
│ └── **init**.py
├── .gitignore
└── README.md

---

# 🏁 **8. Estado del Proyecto**

Proyecto funcional  
CI/CD operativo  
Despliegue automático  
Requerimientos completos
