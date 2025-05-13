#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Detector de cambios entre imágenes de la misma zona geográfica.
"""

import cv2
import numpy as np
import logging
from typing import Dict, Any, List, Tuple, Optional

logger = logging.getLogger(__name__)

class ChangeDetector:
    """Detector de cambios entre imágenes de la misma zona geográfica."""
    
    def __init__(self, sensitivity: float = 0.2):
        """
        Inicializa el detector de cambios.
        
        Args:
            sensitivity: Sensibilidad de detección (0.0-1.0)
        """
        self.sensitivity = sensitivity
        self.reference_images = {}  # Diccionario de imágenes de referencia por coordenadas
        logger.info(f"Detector de cambios inicializado (sensibilidad: {sensitivity})")
    
    def add_reference_image(self, image_data: bytes, coordinates: Dict[str, float], 
                           metadata: Dict[str, Any]) -> str:
        """
        Añade una imagen de referencia para una ubicación.
        
        Args:
            image_data: Datos de la imagen en bytes
            coordinates: Coordenadas geográficas (latitud, longitud)
            metadata: Metadatos adicionales
            
        Returns:
            ID de referencia
        """
        try:
            # Generar ID de ubicación
            location_id = f"{coordinates['latitude']:.5f}_{coordinates['longitude']:.5f}"
            
            # Decodificar imagen
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Convertir a escala de grises y aplicar blur para reducir ruido
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            blur = cv2.GaussianBlur(gray, (21, 21), 0)
            
            # Guardar imagen de referencia
            self.reference_images[location_id] = {
                "image": blur,
                "original": image,
                "metadata": metadata,
                "coordinates": coordinates
            }
            
            logger.info(f"Imagen de referencia añadida para ubicación: {location_id}")
            return location_id
        except Exception as e:
            logger.error(f"Error al añadir imagen de referencia: {str(e)}")
            return ""
    
    def detect_changes(self, image_data: bytes, location_id: str) -> Dict[str, Any]:
        """
        Detecta cambios entre la imagen actual y la de referencia.
        
        Args:
            image_data: Datos de la imagen actual en bytes
            location_id: ID de la ubicación de referencia
            
        Returns:
            Diccionario con los resultados de la detección
        """
        try:
            if location_id not in self.reference_images:
                return {"error": "Ubicación de referencia no encontrada"}
            
            # Obtener imagen de referencia
            reference = self.reference_images[location_id]
            
            # Decodificar imagen actual
            nparr = np.frombuffer(image_data, np.uint8)
            current_image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Convertir a escala de grises y aplicar blur
            gray = cv2.cvtColor(current_image, cv2.COLOR_BGR2GRAY)
            blur = cv2.GaussianBlur(gray, (21, 21), 0)
            
            # Calcular diferencia absoluta entre imágenes
            frame_delta = cv2.absdiff(reference["image"], blur)
            
            # Aplicar umbral para destacar diferencias
            thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
            
            # Dilatar imagen umbralizada para llenar huecos
            dilated = cv2.dilate(thresh, None, iterations=2)
            
            # Encontrar contornos de las áreas de cambio
            contours, _ = cv2.findContours(dilated.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Filtrar contornos por tamaño
            min_area = current_image.shape[0] * current_image.shape[1] * 0.005  # 0.5% del área total
            significant_contours = [c for c in contours if cv2.contourArea(c) > min_area]
            
            # Calcular porcentaje de cambio
            change_pixels = np.sum(thresh > 0)
            total_pixels = thresh.shape[0] * thresh.shape[1]
            change_percentage = (change_pixels / total_pixels) * 100
            
            # Crear imagen con cambios marcados
            changes_image = current_image.copy()
            for contour in significant_contours:
                (x, y, w, h) = cv2.boundingRect(contour)
                cv2.rectangle(changes_image, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            # Codificar imagen resultante
            _, buffer = cv2.imencode('.jpg', changes_image)
            changes_image_bytes = buffer.tobytes()
            
            # Determinar si hay cambios significativos
            has_significant_changes = change_percentage > (self.sensitivity * 100)
            
            result = {
                "location_id": location_id,
                "has_changes": has_significant_changes,
                "change_percentage": change_percentage,
                "significant_areas": len(significant_contours),
                "changes_image": changes_image_bytes,
                "timestamp": reference["metadata"].get("timestamp", 0)
            }
            
            logger.info(f"Detección de cambios completada: {change_percentage:.2f}% de cambio")
            return result
        except Exception as e:
            logger.error(f"Error en detección de cambios: {str(e)}")
            return {"error": str(e)}
    
    def get_reference_image(self, location_id: str) -> Optional[bytes]:
        """
        Obtiene la imagen de referencia para una ubicación.
        
        Args:
            location_id: ID de la ubicación
            
        Returns:
            Datos de la imagen de referencia o None si no existe
        """
        if location_id not in self.reference_images:
            return None
        
        reference = self.reference_images[location_id]
        _, buffer = cv2.imencode('.jpg', reference["original"])
        return buffer.tobytes()
    
    def remove_reference_image(self, location_id: str) -> bool:
        """
        Elimina una imagen de referencia.
        
        Args:
            location_id: ID de la ubicación
            
        Returns:
            True si se eliminó correctamente
        """
        if location_id not in self.reference_images:
            return False
        
        del self.reference_images[location_id]
        logger.info(f"Imagen de referencia eliminada: {location_id}")
        return True 