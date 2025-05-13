#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de configuración para la aplicación.
Gestiona la configuración de logging y otras utilidades.
"""

import os
import logging
from datetime import datetime

def setup_logging():
    """Configura el sistema de logging para la aplicación."""
    # Crear directorio de logs si no existe
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))), "logs")
    
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    # Nombre del archivo de log con timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(logs_dir, f"geo_analysis_{timestamp}.log")
    
    # Configuración básica de logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    # Reducir verbosidad de bibliotecas externas
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)
    
    return logging.getLogger(__name__)

def get_openai_config():
    """Obtiene la configuración para la API de OpenAI."""
    return {
        "api_key": os.environ.get("OPENAI_API_KEY"),
        "model": "gpt-4.1", # Usar el modelo más reciente disponible
        "temperature": 0.3,            # Baja temperatura para respuestas precisas
        "max_tokens": 2000,            # Límite de tokens para la respuesta
        "top_p": 1.0,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0,
    } 