#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Controlador para rutas de análisis de imágenes.
Responsabilidad única: Manejar las APIs HTTP de análisis geográfico.
"""

import logging
from flask import Blueprint, request, jsonify, send_from_directory
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Crear blueprint para rutas de análisis
analysis_blueprint = Blueprint('analysis', __name__)

# Variable global para el servicio de análisis (se inyectará desde main)
analysis_service = None

def init_analysis_controller(service):
    """Inicializa el controlador con el servicio de análisis."""
    global analysis_service
    analysis_service = service
    logger.info("Controlador de análisis inicializado")

@analysis_blueprint.route('/analyze', methods=['POST'])
def analyze():
    """Procesa una imagen y retorna los resultados del análisis."""
    try:
        if not analysis_service:
            return jsonify({'error': 'Servicio no inicializado', 'status': 'error'}), 500
            
        # Validar entrada
        if 'image' not in request.files:
            return jsonify({'error': 'No se envió ninguna imagen'}), 400
            
        image_file = request.files['image']
        if image_file.filename == '':
            return jsonify({'error': 'Nombre de archivo vacío'}), 400
        
        # Obtener parámetros de configuración
        config_params = _extract_analysis_params(request.form)
        
        # Procesar imagen usando el servicio
        result = analysis_service.analyze_image(image_file, config_params)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error en el análisis: {str(e)}")
        return jsonify({'error': str(e), 'status': 'error'}), 500

@analysis_blueprint.route('/results/<path:filename>')
def results(filename):
    """Sirve archivos de resultados guardados."""
    try:
        if not analysis_service:
            return jsonify({'error': 'Servicio no inicializado'}), 500
            
        return analysis_service.serve_result_file(filename)
        
    except Exception as e:
        logger.error(f"Error sirviendo archivo: {str(e)}")
        return jsonify({'error': str(e)}), 500

@analysis_blueprint.route('/api/analysis/status', methods=['GET'])
def analysis_status():
    """Obtiene el estado actual del análisis en progreso."""
    try:
        if not analysis_service:
            return jsonify({'error': 'Servicio no inicializado'}), 500
            
        analysis_id = request.args.get('id')
        result = analysis_service.get_analysis_status(analysis_id)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error obteniendo estado: {str(e)}")
        return jsonify({'error': str(e)}), 500

def _extract_analysis_params(form_data) -> Dict[str, Any]:
    """Extrae y valida parámetros de configuración del análisis."""
    return {
        'confidence_threshold': float(form_data.get('confidence_threshold', 0)),
        'model_version': form_data.get('model_version', 'default'),
        'detail_level': form_data.get('detail_level', 'normal')
    } 