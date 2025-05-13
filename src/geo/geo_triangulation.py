#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Triangulación geográfica basada en múltiples capturas del dron.
"""

import numpy as np
import logging
import time
import uuid
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

class GeoTriangulation:
    """Triangulación geográfica basada en múltiples capturas del dron."""
    
    def __init__(self):
        """Inicializa el sistema de triangulación."""
        self.observations = {}  # Observaciones organizadas por ID de objetivo
        logger.info("Sistema de triangulación geográfica inicializado")
    
    def add_observation(self, target_id: str, drone_position: Dict[str, float], 
                       target_bearing: float, target_elevation: float, 
                       confidence: float = 1.0) -> str:
        """
        Añade una observación para triangulación.
        
        Args:
            target_id: Identificador del objetivo
            drone_position: Posición del dron {latitude, longitude, altitude}
            target_bearing: Rumbo hacia el objetivo en grados (0-360)
            target_elevation: Ángulo de elevación hacia el objetivo en grados
            confidence: Confianza en la medición (0-1)
            
        Returns:
            ID de la observación
        """
        if target_id not in self.observations:
            self.observations[target_id] = []
        
        # Generar ID único para esta observación
        observation_id = f"{target_id}_{len(self.observations[target_id])}"
        
        # Guardar observación
        self.observations[target_id].append({
            "id": observation_id,
            "drone_position": drone_position,
            "target_bearing": target_bearing,
            "target_elevation": target_elevation,
            "confidence": confidence,
            "timestamp": time.time()
        })
        
        logger.info(f"Observación añadida para objetivo {target_id}: {observation_id}")
        return observation_id
    
    def calculate_position(self, target_id: str) -> Dict[str, Any]:
        """
        Calcula la posición de un objetivo basándose en múltiples observaciones.
        
        Args:
            target_id: Identificador del objetivo
            
        Returns:
            Posición calculada y metadatos
        """
        if target_id not in self.observations or len(self.observations[target_id]) < 2:
            return {
                "error": f"Se requieren al menos 2 observaciones (actual: {len(self.observations.get(target_id, []))})"
            }
        
        observations = self.observations[target_id]
        
        # En un sistema real, implementaríamos un algoritmo de triangulación completo
        # Por simplicidad, simulamos un resultado basado en las observaciones
        
        # Extraer posiciones y direcciones
        positions = []
        bearings = []
        elevations = []
        weights = []  # Basados en la confianza
        
        for obs in observations:
            pos = obs["drone_position"]
            positions.append([pos["latitude"], pos["longitude"], pos["altitude"]])
            bearings.append(obs["target_bearing"])
            elevations.append(obs["target_elevation"])
            weights.append(obs["confidence"])
        
        # Convertir a arrays de numpy
        positions = np.array(positions)
        bearings = np.array(bearings)
        elevations = np.array(elevations)
        weights = np.array(weights)
        
        # Calcular promedios ponderados para una estimación simple
        # (Una implementación real utilizaría un algoritmo más sofisticado)
        
        # Normalizar pesos
        weights = weights / np.sum(weights)
        
        # Calculamos un punto aproximado extrapolando desde cada observación
        # y luego promediando los resultados
        earth_radius = 6371000  # Radio de la Tierra en metros
        
        estimated_points = []
        
        for i in range(len(observations)):
            lat, lon, alt = positions[i]
            bearing = np.radians(bearings[i])
            elevation = np.radians(elevations[i])
            
            # Calcular distancia estimada al objetivo basada en la elevación y altitud
            if elevation > 0:
                # Si el objetivo está por encima del horizonte
                distance = alt / np.sin(elevation)
            else:
                # Si el objetivo está por debajo del horizonte
                # Estimación simplificada
                distance = 1000  # metros, valor arbitrario
            
            # Limitar distancia a un valor razonable
            distance = min(distance, 10000)  # máximo 10km
            
            # Convertir coordenadas a radianes
            lat_rad = np.radians(lat)
            lon_rad = np.radians(lon)
            
            # Calcular la nueva posición
            # Fórmula simplificada, no consideramos curvatura de la Tierra para distancias cortas
            target_lat_rad = lat_rad + (distance / earth_radius) * np.cos(bearing)
            target_lon_rad = lon_rad + (distance / earth_radius) * np.sin(bearing) / np.cos(lat_rad)
            
            # Convertir de vuelta a grados
            target_lat = np.degrees(target_lat_rad)
            target_lon = np.degrees(target_lon_rad)
            
            estimated_points.append([target_lat, target_lon])
        
        # Convertir a array y calcular promedio ponderado
        estimated_points = np.array(estimated_points)
        weighted_avg = np.average(estimated_points, axis=0, weights=weights)
        
        # Calcular una estimación de precisión basada en la dispersión de los puntos
        # y el número de observaciones
        distances = np.linalg.norm(estimated_points - weighted_avg, axis=1)
        max_distance = np.max(distances)  # Máxima desviación
        avg_distance = np.average(distances)  # Desviación promedio
        num_observations = len(observations)
        
        # Precision improves with more observations but is limited by observation quality
        precision = 100 * (1 - avg_distance / 0.001) * np.tanh(num_observations / 3)
        precision = max(0, min(99, precision))  # Limitar entre 0 y 99%
        
        # Resultado final
        result = {
            "target_id": target_id,
            "position": {
                "latitude": float(weighted_avg[0]),
                "longitude": float(weighted_avg[1]),
                "altitude": 0  # No estimamos altitud en este ejemplo simplificado
            },
            "precision": {
                "meters": float(avg_distance * 111000),  # Conversión aproximada a metros
                "confidence": float(precision),
                "max_deviation_meters": float(max_distance * 111000)
            },
            "observations_count": num_observations,
            "timestamp": time.time()
        }
        
        logger.info(f"Posición calculada para objetivo {target_id}: {result['position']}")
        return result
    
    def reset_target(self, target_id: str) -> bool:
        """
        Elimina todas las observaciones de un objetivo.
        
        Args:
            target_id: Identificador del objetivo
            
        Returns:
            True si se eliminaron las observaciones
        """
        if target_id in self.observations:
            del self.observations[target_id]
            logger.info(f"Observaciones eliminadas para objetivo {target_id}")
            return True
        return False
    
    def get_all_targets(self) -> List[str]:
        """
        Obtiene todos los IDs de objetivos con observaciones.
        
        Returns:
            Lista de IDs de objetivos
        """
        return list(self.observations.keys())
    
    def create_target(self) -> str:
        """
        Crea un nuevo objetivo con ID único.
        
        Returns:
            ID del nuevo objetivo
        """
        target_id = f"target_{uuid.uuid4().hex[:8]}"
        self.observations[target_id] = []
        logger.info(f"Nuevo objetivo creado: {target_id}")
        return target_id 