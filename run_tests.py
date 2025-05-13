#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para ejecutar las pruebas del proyecto.
Proporciona una interfaz sencilla para ejecutar tests específicos o todos.
"""

import os
import sys
import argparse
import subprocess

def run_tests(module=None, verbose=False, coverage=False):
    """
    Ejecuta las pruebas del proyecto.
    
    Args:
        module: Módulo específico a testear (p.ej. 'utils.test_helpers')
        verbose: Si se debe mostrar información detallada
        coverage: Si se debe generar un reporte de cobertura
    """
    # Directorio raíz del proyecto
    root_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Comando base para pytest
    cmd = ["pytest"]
    
    # Añadir flags según los parámetros
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend(["--cov=src", "--cov-report=term", "--cov-report=html"])
    
    # Si se especifica un módulo, añadirlo al comando
    if module:
        if not module.startswith("tests/"):
            module = f"tests/{module}"
        cmd.append(module)
    
    # Ejecutar el comando
    print(f"Ejecutando: {' '.join(cmd)}")
    return subprocess.call(cmd, cwd=root_dir)

def main():
    """Función principal."""
    parser = argparse.ArgumentParser(description="Ejecutor de pruebas para el proyecto")
    
    parser.add_argument(
        "-m", "--module", 
        help="Módulo específico a testear (p.ej. 'utils/test_helpers.py')"
    )
    
    parser.add_argument(
        "-v", "--verbose", 
        action="store_true",
        help="Mostrar información detallada"
    )
    
    parser.add_argument(
        "-c", "--coverage", 
        action="store_true",
        help="Generar reporte de cobertura"
    )
    
    args = parser.parse_args()
    
    # Si se solicita cobertura pero no está instalado pytest-cov
    if args.coverage:
        try:
            import pytest_cov
        except ImportError:
            print("ERROR: Se requiere pytest-cov para generar reportes de cobertura.")
            print("Instálalo con: pip install pytest-cov")
            return 1
    
    # Ejecutar las pruebas
    return run_tests(args.module, args.verbose, args.coverage)

if __name__ == "__main__":
    sys.exit(main()) 