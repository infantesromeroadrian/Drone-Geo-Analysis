#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Planificador de misiones para drones.
"""

import json
import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class MissionPlanner:
    """Planificador de misiones para drones."""
    
    def __init__(self, missions_dir: str = None):
        """
        Inicializa el planificador de misiones.
        
        Args:
            missions_dir: Directorio para guardar las misiones
        """
        self.missions_dir = missions_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "missions"
        )
        
        # Crear directorio si no existe
        if not os.path.exists(self.missions_dir):
            os.makedirs(self.missions_dir)
        
        logger.info(f"Planificador de misiones inicializado. Directorio: {self.missions_dir}")
    
    def create_mission(self, name: str, description: str, waypoints: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Crea una nueva misión.
        
        Args:
            name: Nombre de la misión
            description: Descripción de la misión
            waypoints: Lista de waypoints con acciones
            
        Returns:
            Diccionario con los datos de la misión
        """
        mission = {
            "id": f"mission_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "name": name,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "waypoints": waypoints
        }
        
        # Guardar misión en archivo
        file_path = os.path.join(self.missions_dir, f"{mission['id']}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(mission, f, ensure_ascii=False, indent=4)
        
        logger.info(f"Misión creada: {name} ({mission['id']})")
        return mission
    
    def get_mission(self, mission_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene una misión por su ID.
        
        Args:
            mission_id: ID de la misión
            
        Returns:
            Diccionario con los datos de la misión o None si no existe
        """
        file_path = os.path.join(self.missions_dir, f"{mission_id}.json")
        if not os.path.exists(file_path):
            logger.error(f"Misión no encontrada: {mission_id}")
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            mission = json.load(f)
        
        return mission
    
    def list_missions(self) -> List[Dict[str, Any]]:
        """
        Lista todas las misiones disponibles.
        
        Returns:
            Lista de misiones
        """
        missions = []
        for file_name in os.listdir(self.missions_dir):
            if file_name.endswith('.json'):
                with open(os.path.join(self.missions_dir, file_name), 'r', encoding='utf-8') as f:
                    mission = json.load(f)
                    missions.append({
                        "id": mission["id"],
                        "name": mission["name"],
                        "description": mission["description"],
                        "created_at": mission["created_at"],
                        "waypoints_count": len(mission["waypoints"])
                    })
        
        return missions
    
    def create_reconnaissance_mission(self, name: str, area_coordinates: List[Dict[str, float]], 
                                     altitude: float, image_interval: int = 5) -> Dict[str, Any]:
        """
        Crea una misión de reconocimiento que cubre un área.
        
        Args:
            name: Nombre de la misión
            area_coordinates: Lista de coordenadas que definen el perímetro del área
            altitude: Altitud del vuelo en metros
            image_interval: Intervalo para capturar imágenes en segundos
            
        Returns:
            Diccionario con los datos de la misión
        """
        # Implementar algoritmo para generar waypoints que cubran un área
        # Aquí se implementaría un algoritmo de cobertura de área (como patrones de zigzag o espiral)
        # Por ahora, simplement usamos los puntos del perímetro como waypoints
        
        waypoints = []
        for point in area_coordinates:
            waypoint = {
                "latitude": point["latitude"],
                "longitude": point["longitude"],
                "altitude": altitude,
                "actions": [
                    {"type": "capture_image"}
                ]
            }
            waypoints.append(waypoint)
        
        # Añadir acción de espera y captura de imagen periódica
        for waypoint in waypoints:
            waypoint["actions"].append({"type": "wait", "duration": image_interval})
        
        description = f"Misión de reconocimiento a {altitude}m de altitud"
        return self.create_mission(name, description, waypoints)
    
    def delete_mission(self, mission_id: str) -> bool:
        """
        Elimina una misión.
        
        Args:
            mission_id: ID de la misión
            
        Returns:
            True si se eliminó correctamente, False en caso contrario
        """
        file_path = os.path.join(self.missions_dir, f"{mission_id}.json")
        if not os.path.exists(file_path):
            logger.error(f"Misión no encontrada: {mission_id}")
            return False
        
        try:
            os.remove(file_path)
            logger.info(f"Misión eliminada: {mission_id}")
            return True
        except Exception as e:
            logger.error(f"Error al eliminar misión {mission_id}: {str(e)}")
            return False 