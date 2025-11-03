# src/db.py
import os
import sqlite3

# sqlite | sqlserver | oracle
ENGINE = os.getenv("DB_ENGINE", "sqlite").lower()


def get_conn():
    if ENGINE == "sqlite":
        base_dir = os.path.abspath(os.path.join(
            os.path.dirname(__file__), "..", "database"))
        os.makedirs(base_dir, exist_ok=True)
        db_path = os.path.join(base_dir, "proyecto.db")
        return sqlite3.connect(db_path, check_same_thread=False)

    elif ENGINE == "sqlserver":
        # Solo importamos si realmente vamos a usar SQL Server
        try:
            import pyodbc
        except ImportError as e:
            raise RuntimeError(
                "Falta el paquete 'pyodbc'. Instálalo con: pip install pyodbc\n"
                "Además, en Windows debes tener instalado el 'ODBC Driver 18 for SQL Server'."
            ) from e

        dsn = os.getenv("DB_DSN")  # si configuraste un DSN, úsalo
        if dsn:
            conn_str = f"DSN={dsn}"
        else:
            driver = os.getenv("DB_DRIVER", "{ODBC Driver 18 for SQL Server}")
            server = os.getenv("DB_SERVER", "localhost")
            database = os.getenv("DB_DATABASE", "ProyectoEmpresa")
            uid = os.getenv("DB_USERNAME", "sa")
            pwd = os.getenv("DB_PASSWORD", "TuPasswordSeguro!123")
            encrypt = os.getenv("DB_ENCRYPT", "yes")
            trust = os.getenv("DB_TRUST_SERVER_CERTIFICATE", "yes")
            conn_str = (
                f"DRIVER={driver};SERVER={server};DATABASE={database};"
                f"UID={uid};PWD={pwd};Encrypt={encrypt};TrustServerCertificate={trust}"
            )
        return pyodbc.connect(conn_str)

    elif ENGINE == "oracle":
        # Usamos 'oracledb' (modo thin) para no requerir Instant Client
        try:
            import oracledb
        except ImportError as e:
            raise RuntimeError(
                "Falta el paquete 'oracledb'. Instálalo con: pip install oracledb\n"
                "Con 'oracledb' en modo thin no necesitas Oracle Instant Client."
            ) from e

        host = os.getenv("DB_HOST", "localhost")
        port = int(os.getenv("DB_PORT", "1521"))
        service = os.getenv("DB_SERVICE", "FREEPDB1")
        user = os.getenv("DB_USERNAME", "system")
        pwd = os.getenv("DB_PASSWORD", "oracle")

        dsn = f"{host}:{port}/{service}"  # formato host:port/service
        return oracledb.connect(user=user, password=pwd, dsn=dsn)

    else:
        raise RuntimeError(f"DB_ENGINE no soportado: {ENGINE}")
