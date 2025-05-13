#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo principal para la herramienta de análisis geográfico de imágenes.
Este módulo coordina los diferentes componentes del sistema para analizar
imágenes y determinar ubicaciones geográficas.
"""

import os
import sys
import logging
import time
from dotenv import load_dotenv

# Agregar la ruta del proyecto al PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar módulos internos
from src.controllers.image_controller import ImageController
from src.utils.config import setup_logging

def main():
    """Función principal que inicia la aplicación."""
    # Cargar variables de entorno
    load_dotenv()
    
    # Configurar logging
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Iniciando la aplicación de análisis geográfico OSINT")
    
    # Verificar API key
    if "OPENAI_API_KEY" not in os.environ:
        logger.error("No se encontró OPENAI_API_KEY en las variables de entorno")
        print("Error: Se requiere una API key de OpenAI. Agrégala al archivo .env")
        sys.exit(1)
    
    # Verificar variable DISPLAY para GUI
    if not os.environ.get("DISPLAY"):
        logger.warning("Variable DISPLAY no configurada. Intentando establecer un valor predeterminado.")
        # En Windows con Docker, intentar usar host.docker.internal
        os.environ["DISPLAY"] = "host.docker.internal:0.0"
        logger.info(f"DISPLAY establecido a: {os.environ['DISPLAY']}")
    
    # Añadir un retraso para asegurar que el servidor X esté disponible
    time.sleep(1)
    
    try:
        # Imprimir información para debugging
        logger.info(f"Sistema operativo: {sys.platform}")
        logger.info(f"Variable DISPLAY: {os.environ.get('DISPLAY', 'No configurada')}")
        
        # Iniciar controlador de imágenes
        controller = ImageController()
        controller.run()
    except KeyboardInterrupt:
        logger.info("Aplicación terminada por el usuario")
        print("\nAplicación terminada")
    except Exception as e:
        logger.error(f"Error no controlado: {str(e)}")
        print(f"Error: {str(e)}")
        
        # Si el error está relacionado con la visualización, dar instrucciones específicas
        if "display" in str(e).lower() or "tkinter" in str(e).lower():
            print("\nError de visualización detectado. Asegúrate de que:")
            print("1. Tienes un servidor X (VcXsrv, XMing) ejecutándose en Windows")
            print("2. El servidor X está configurado para permitir conexiones remotas")
            print("3. La variable DISPLAY está configurada correctamente en el archivo .env o docker-compose.yml")
            print("   Valor recomendado para Windows: host.docker.internal:0.0")
        
        sys.exit(1)

if __name__ == "__main__":
    main() 