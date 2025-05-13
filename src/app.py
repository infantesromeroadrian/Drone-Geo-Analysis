#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de interfaz web para la herramienta de análisis geográfico de imágenes.
Permite usar la herramienta a través de un navegador web.
"""

import os
import sys
import logging
import json
import base64
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from dotenv import load_dotenv
import tempfile

# Agregar la ruta del proyecto al PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar módulos internos
from src.models.geo_analyzer import GeoAnalyzer
from src.utils.config import setup_logging
from src.utils.helpers import get_image_metadata, save_analysis_results

# Configurar aplicación Flask
app = Flask(__name__, 
           static_folder='templates/static',
           template_folder='templates')

# Cargar variables de entorno
load_dotenv()

# Configurar logging
setup_logging()
logger = logging.getLogger(__name__)

# Verificar API key
if "OPENAI_API_KEY" not in os.environ:
    logger.error("No se encontró OPENAI_API_KEY en las variables de entorno")
    print("Error: Se requiere una API key de OpenAI. Agrégala al archivo .env")
    sys.exit(1)

# Inicializar el analizador geográfico
analyzer = GeoAnalyzer()

@app.route('/')
def index():
    """Ruta principal que muestra la interfaz web."""
    return render_template('web_index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    """Procesa una imagen y retorna los resultados del análisis."""
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No se envió ninguna imagen'}), 400
            
        image_file = request.files['image']
        if image_file.filename == '':
            return jsonify({'error': 'Nombre de archivo vacío'}), 400
            
        # Guardar imagen en directorio temporal
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, image_file.filename)
        image_file.save(temp_path)
        
        # Obtener metadatos
        metadata = get_image_metadata(temp_path)
        
        # Codificar imagen en base64
        with open(temp_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        # Analizar la imagen
        results = analyzer.analyze_image(encoded_image, metadata)
        
        # Guardar resultados
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"analysis_{timestamp}.json"
        save_path = save_analysis_results(results, filename)
        
        # Devolver resultados como JSON
        return jsonify({
            'results': results,
            'saved_path': save_path
        })
        
    except Exception as e:
        logger.error(f"Error en el análisis: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/results/<path:filename>')
def results(filename):
    """Sirve archivos de resultados guardados."""
    results_dir = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "results")
    return send_from_directory(results_dir, filename)

def main():
    """Función principal que inicia el servidor web."""
    from waitress import serve
    
    host = '0.0.0.0'  # Escuchar en todas las interfaces
    port = 5000
    
    logger.info(f"Iniciando servidor web en {host}:{port}")
    print(f"Servidor iniciado en http://{host}:{port}")
    print(f"Accede a través de: http://localhost:{port}")
    
    # Usar waitress para producción
    serve(app, host=host, port=port)

if __name__ == "__main__":
    main() 