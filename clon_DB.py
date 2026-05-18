#!/usr/bin/env python3
"""
Script per clonar la base de dades remota (PostgreSQL a Neon) a la base de dades local (SQLite).
Útil per treballar en local (DEBUG=True) amb les dades reals de producció.
"""

import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
DUMP_FILE = BASE_DIR / "data_dump.json"

'''
def load_env():
    
    env_file = BASE_DIR / ".env"
    if not env_file.exists():
        print("❌ No s'ha trobat el fitxer .env")
        sys.exit(1)
    load_dotenv(env_file)
'''

def run_manage(args, env_override=None, description=""):
    """
    Funció auxiliar per executar comandes de Django ('manage.py') de manera segura.
    Afegeix variables d'entorn personalitzades si és necessari i controla els errors.
    """

    #copia el diccionari de variables d'entorn
    env = os.environ.copy()
    # Si s'han passat variables per sobreescriure (ex: DJANGO_DEBUG), les afegeix o modifica
    if env_override:
        env.update(env_override)

    print(f"⏳ {description}...")

    # Executa el procés fill a la terminal (equival a posar "python manage.py <comanda>")
    result = subprocess.run(
        [sys.executable, "manage.py"] + args,
        env=env,
        cwd=BASE_DIR,
        timeout=180,
    )

    # Si el codi de sortida no és 0, significa que el procés ha fallat

    if result.returncode != 0:
        print(f"❌ Error (codi {result.returncode})")
        return False

    # Si tot ha anat bé, retorna True
    return True


def main():
    """
    Funció principal que orquestra tot el procés de clonació de la base de dades.
    """
    # Carrega les variables d'entorn del fitxer .env
    load_dotenv()

    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL no definit al .env")
        sys.exit(1)

    # Variables d'entorn per executar les comandes com si estiguéssim en producció
    prod_env = {"DJANGO_DEBUG": "False"} #per a fer que s'accedeixi a la base de dades de producció
    

    # Executa el dumpdata per extreure totes les dades de la base de dades de producció# PAS 1: Exporta totes les dades del PostgreSQL remot a un fitxer JSON
    ok = run_manage(
        [
            "dumpdata",
            "--natural-foreign",
            "--natural-primary",
            "--exclude", "contenttypes",
            "--exclude", "auth.Permission",
            "-o", str(DUMP_FILE),
        ],
        env_override=prod_env,
        description="Exportant dades de PostgreSQL (Neon)",
    )
    if not ok:
        sys.exit(1)

    # Força que Django canviï a l'entorn local (SQLite) activant el mode DEBUG
    local_env = {"DJANGO_DEBUG": "True"}

    db_path = BASE_DIR / "db.sqlite3"
    if db_path.exists():
        db_path.unlink()
        print("🗑️  Base de dades local anterior eliminada")

    # Executa la migración (syncdb) sobre el nuevo SQLite para crear el esquema vacío
    ok = run_manage(
        ["migrate", "--run-syncdb"],
        env_override=local_env,
        description="Executant migracions a SQLite",
    )
    if not ok:
        sys.exit(1)

    load_script = (
        "import django;"
        "from django.core.management import call_command;"
        "from django.db.models.signals import post_save;"
        "from web_app.models import CustomUser;"
        "from web_app.signals import create_user_profile, save_user_profile;"
        "post_save.disconnect(create_user_profile, sender=CustomUser);"
        "post_save.disconnect(save_user_profile, sender=CustomUser);"
        "call_command('loaddata', '{}')".format(DUMP_FILE)
    )

    ok = run_manage(
        ["shell", "-c", load_script],
        env_override=local_env,
        description="Important dades a SQLite (sense signals)",
    )
    if not ok:
        sys.exit(1)

    if DUMP_FILE.exists():
        DUMP_FILE.unlink()

    print("\n✅ Base de dades local actualitzada correctament!")
    print(f"📁 {db_path}")


if __name__ == "__main__":
    main()
