#!/usr/bin/env python3
"""Crea la base de datos dedicada del piloto si aún no existe.

Conecta al servidor PostgreSQL usando las credenciales de backend/.env
(base de mantenimiento ``postgres``) y crea ``evaluacion_quinquenal_piloto``
(nombre opcional como primer argumento). Idempotente: si la base ya existe
no hace nada. La base creada queda sin tablas; después ejecutar
``manage.py migrate`` con ``DB_NAME`` apuntando a ella.
"""

import os
import sys
from pathlib import Path

import psycopg2
from psycopg2 import sql

BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND))

from evaluacionQuinquenal.settings import load_env_file  # noqa: E402

NOMBRE_DEFECTO = "evaluacion_quinquenal_piloto"


def main() -> int:
    """Crea la BD si falta; imprime el resultado y devuelve 0/1."""
    load_env_file(BACKEND / ".env")
    objetivo = sys.argv[1] if len(sys.argv) > 1 else NOMBRE_DEFECTO

    try:
        conn = psycopg2.connect(
            dbname="postgres",
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            user=os.getenv("DB_USER", ""),
            password=os.getenv("DB_PASSWORD", ""),
        )
    except psycopg2.Error as exc:
        print(f"no se pudo conectar al servidor: {exc}", file=sys.stderr)
        return 1

    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (objetivo,))
            if cur.fetchone():
                print(f"ya existe: {objetivo}")
                return 0
            cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(objetivo)))
        print(f"creada: {objetivo}")
        return 0
    except psycopg2.Error as exc:
        print(f"no se pudo crear la base: {exc}", file=sys.stderr)
        return 1
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
