#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servicio de análisis de imágenes para lógica de negocio.
Responsabilidad única: Gestionar análisis geográfico de imágenes.
"""

import logging
import os
import tempfile
from datetime import datetime
from flask import send_from_directory
from typing import Dict, Any

from src.utils.helpers import get_image_metadata, save_analysis_results_with_filename

logger = logging.getLogger(__name__)

class AnalysisService:
    """
    Servicio que encapsula la lógica de negocio para análisis de imágenes.
    Maneja el procesamiento y almacenamiento de resultados.
    """
    
    def __init__(self, geo_analyzer):
        """
        Inicializa el servicio de análisis.
        
        Args:
            geo_analyzer: Instancia del analizador geográfico
        """
        self.analyzer = geo_analyzer
        logger.info("Servicio de análisis inicializado")
    
    def analyze_image(self, image_file, config_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa una imagen y retorna los resultados del análisis.
        
        Args:
            image_file: Archivo de imagen Flask
            config_params: Parámetros de configuración del análisis
            
        Returns:
            Diccionario con resultados del análisis
        """
        try:
            # Guardar imagen en directorio temporal
            temp_path = self._save_temp_image(image_file)
            
            # Obtener metadatos y agregar configuración
            metadata = self._prepare_metadata(temp_path, config_params)
            
            # Codificar imagen en base64
            encoded_result = self._encode_image(temp_path)
            if not encoded_result:
                return {
                    'error': 'Error al procesar la imagen. Formato no compatible.',
                    'status': 'error'
                }
            
            encoded_image, image_format = encoded_result
            
            # Analizar la imagen
            results = self.analyzer.analyze_image(encoded_image, metadata, image_format)
            
            # Aplicar filtro de confianza si es necesario
            self._apply_confidence_filter(results, config_params.get('confidence_threshold', 0))
            
            # Guardar resultados
            save_path = self._save_results(results)
            
            return {
                'results': results,
                'saved_path': save_path,
                'status': 'completed'
            }
            
        except Exception as e:
            logger.error(f"Error en análisis: {str(e)}")
            return {'error': str(e), 'status': 'error'}
    
    def serve_result_file(self, filename: str):
        """
        Sirve archivos de resultados guardados.
        
        Args:
            filename: Nombre del archivo a servir
            
        Returns:
            Respuesta Flask con el archivo
        """
        results_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "results"
        )
        return send_from_directory(results_dir, filename)
    
    def get_analysis_status(self, analysis_id: str) -> Dict[str, Any]:
        """
        Obtiene el estado de un análisis en progreso.
        
        Args:
            analysis_id: ID del análisis
            
        Returns:
            Estado del análisis
        """
        # En una implementación real, esto consultaría una base de datos
        # Aquí simulamos para demostración
        return {
            'id': analysis_id,
            'status': 'processing',
            'progress': 70,
            'estimated_time_remaining': '30 segundos'
        }
    
    def _save_temp_image(self, image_file) -> str:
        """Guarda la imagen en un directorio temporal."""
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, image_file.filename)
        image_file.save(temp_path)
        return temp_path
    
    def _prepare_metadata(self, temp_path: str, config_params: Dict[str, Any]) -> Dict[str, Any]:
        """Prepara metadatos combinando información de imagen y configuración."""
        metadata = get_image_metadata(temp_path)
        metadata.update(config_params)
        return metadata
    
    def _encode_image(self, temp_path: str):
        """Codifica la imagen en base64."""
        try:
            from src.utils.helpers import encode_image_to_base64
            return encode_image_to_base64(temp_path)
        except ImportError:
            # Fallback si no está disponible
            import base64
            with open(temp_path, 'rb') as f:
                encoded = base64.b64encode(f.read()).decode('utf-8')
            return encoded, 'jpeg'
    
    def _apply_confidence_filter(self, results: Dict[str, Any], confidence_threshold: float):
        """Aplica filtro de confianza a los resultados."""
        if confidence_threshold > 0:
            if results.get('confidence', 0) < confidence_threshold:
                results['warning'] = (
                    f"Resultados por debajo del umbral de confianza ({confidence_threshold}%)"
                )
    
    def _save_results(self, results: Dict[str, Any]) -> str:
        """Guarda los resultados del análisis."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"analysis_{timestamp}.json"
        return save_analysis_results_with_filename(results, filename) 