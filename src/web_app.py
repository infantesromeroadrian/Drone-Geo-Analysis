#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Versión web de la herramienta de análisis geográfico de imágenes.
Esta versión usa Flask para proporcionar una interfaz web en lugar de Tkinter.
"""

import os
import sys
import logging
import json
import tempfile
from flask import Flask, request, render_template, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Agregar la ruta del proyecto al PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar módulos internos
from src.models.geo_analyzer import GeoAnalyzer
from src.utils.helpers import (
    encode_image_to_base64,
    get_image_metadata,
    format_geo_results,
    save_analysis_results
)
from src.utils.config import setup_logging

# Configuración
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logger = setup_logging()

# Inicializar analizador
analyzer = GeoAnalyzer()

def allowed_file(filename):
    """Verifica si la extensión del archivo es permitida."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Página principal."""
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_image():
    """Analiza una imagen cargada por el usuario."""
    # Verificar que se haya enviado un archivo
    if 'file' not in request.files:
        return jsonify({'error': 'No se envió ningún archivo'}), 400
    
    file = request.files['file']
    
    # Verificar que se haya seleccionado un archivo
    if file.filename == '':
        return jsonify({'error': 'No se seleccionó ningún archivo'}), 400
    
    # Verificar que el archivo tenga una extensión permitida
    if not allowed_file(file.filename):
        return jsonify({'error': 'Tipo de archivo no permitido'}), 400
    
    try:
        # Guardar archivo temporalmente
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Obtener metadatos
        metadata = get_image_metadata(filepath)
        
        # Codificar imagen a base64
        base64_image = encode_image_to_base64(filepath)
        
        if not base64_image:
            return jsonify({'error': 'No se pudo codificar la imagen'}), 500
        
        # Realizar análisis
        results = analyzer.analyze_image(base64_image, metadata)
        
        # Formatear resultados
        formatted_results = format_geo_results(results)
        
        # Guardar resultados
        output_path = save_analysis_results(formatted_results, filepath)
        
        # Eliminar archivo temporal
        os.remove(filepath)
        
        # Devolver resultados
        return jsonify({
            'results': formatted_results,
            'output_file': os.path.basename(output_path) if output_path else None
        })
        
    except Exception as e:
        logger.error(f"Error en el análisis: {str(e)}")
        return jsonify({'error': f"Error en el análisis: {str(e)}"}), 500

@app.route('/results/<filename>')
def download_file(filename):
    """Descarga un archivo de resultados."""
    results_dir = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "results")
    return send_from_directory(results_dir, filename)

if __name__ == '__main__':
    # Verificar API key
    if "OPENAI_API_KEY" not in os.environ:
        logger.error("No se encontró OPENAI_API_KEY en las variables de entorno")
        print("Error: Se requiere una API key de OpenAI. Agrégala al archivo .env")
        sys.exit(1)
    
    # Crear directorio para resultados si no existe
    results_dir = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "results")
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
    
    logger.info("Iniciando aplicación web de análisis geográfico OSINT")
    app.run(host='0.0.0.0', port=8080, debug=False) 