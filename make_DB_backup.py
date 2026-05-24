import subprocess
from datetime import datetime
import os
from dotenv import load_dotenv

'''
necessari:
sudo apt update
sudo apt-get install -y postgresql-client-17
sudo apt install postgresql postgresql-contrib

sudo systemctl enable postgresql
sudo systemctl start postgresql

sudo systemctl status postgresql #comprovar estat, ha de dir active (running)
sudo systemctl stop postgresql #parar servei postgresql

sudo -u postgres psql
CREATE ROLE admin WITH LOGIN SUPERUSER PASSWORD 'admin';

\q
'''

# --- CONFIGURACIÓN ---
load_dotenv()
NEON_DB_URL = os.getenv("DATABASE_URL") # URL de Neon
LOCAL_DB_NAME = "db_auxiliar"           # Nombre que usará Django en local
LOCAL_DB_USER = "admin"              # Tu usuario de Postgres local

# Nombre del archivo temporal
FILENAME = f"backup_neon_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"

def run_command(command, env=None, description=""):
    try:
        print(f"⏳ {description}...")
        subprocess.run(command, check=True, capture_output=True, text=True, env=env)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error en {description}: {e.stderr}")
        return False

def create_backup():
    # 1. DESCARGAR DE NEON
    dump_cmd = [
        "pg_dump",
        "--dbname", NEON_DB_URL,
        "--file", FILENAME,
        "--clean",
        "--if-exists",
        "--no-owner" # Evita errores de permisos al restaurar en otra DB
    ]
    
    if not run_command(dump_cmd, description="Descargando backup de Neon"):
        return
'''
    # 2. CREAR LA BASE DE DATOS LOCAL SI NO EXISTE
    # Conectamos a 'postgres' (que siempre existe) para crear la nuestra
    create_db_script = r"SELECT 'CREATE DATABASE {LOCAL_DB_NAME}' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '{LOCAL_DB_NAME}')\gexec"
    #create_cmd = ["psql", "-d", "postgres", "-c", create_db_script]
    create_cmd = [
    "psql", "-h", "localhost", "-U", LOCAL_DB_USER, "-d", "postgres", "-c", create_db_script
]
    run_command(create_cmd, description=f"Verificando que la DB '{LOCAL_DB_NAME}' exista")

    # 3. RESTAURAR EN LOCAL
    #restore_cmd = ["psql","-d", LOCAL_DB_NAME,"f", FILENAME]
    #restore_cmd = ["psql", "-h", "localhost", "-U", LOCAL_DB_USER, "-d", LOCAL_DB_NAME, "-f", FILENAME]
    
    restore_cmd = ["psql", "-h", "localhost", "-U", LOCAL_DB_USER, "-d", LOCAL_DB_NAME, "-f", FILENAME]

    if run_command(restore_cmd, description="Restaurando datos en la DB local"):
        print(f"✅ ¡Todo listo! Tu DB local '{LOCAL_DB_NAME}' está sincronizada.")
        # Opcional: borrar el archivo .sql después de restaurar para no llenar el disco
        # os.remove(FILENAME) 
    else:
        print("⚠️ El backup se descargó pero no se pudo restaurar en local.")
'''
if __name__ == "__main__":
    create_backup()