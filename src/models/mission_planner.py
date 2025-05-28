#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de planificación de misiones con IA.
Permite crear misiones inteligentes usando LLM para control de drones.
"""

import json
import os
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import openai
from dataclasses import dataclass
import geojson
import math

# Importar funciones de utilidad para rutas
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.helpers import get_missions_directory, get_project_root

@dataclass
class Waypoint:
    """Clase para representar un waypoint de la misión."""
    latitude: float
    longitude: float
    altitude: float
    action: str = "navigate"  # navigate, hover, scan, land, etc.
    duration: float = 0.0  # tiempo en segundos
    description: str = ""

@dataclass
class MissionArea:
    """Clase para representar un área de misión."""
    name: str
    boundaries: List[Tuple[float, float]]  # Lista de (lat, lng)
    restrictions: List[str] = None
    points_of_interest: List[Dict] = None

class LLMMissionPlanner:
    """Planificador de misiones inteligente usando LLM."""
    
    def __init__(self):
        """Inicializa el planificador."""
        self.client = openai.OpenAI()
        self.missions_dir = get_missions_directory()
        self.cartography_dir = os.path.join(get_project_root(), "cartography")
        self.current_mission = None
        self.loaded_areas = {}
        
        # Crear directorio de cartografía si no existe
        os.makedirs(self.cartography_dir, exist_ok=True)
    
    def load_cartography(self, file_path: str, area_name: str) -> bool:
        """
        Carga cartografía desde archivo (GeoJSON, KML, etc.).
        
        Args:
            file_path: Ruta al archivo de cartografía
            area_name: Nombre del área
            
        Returns:
            bool: True si se cargó correctamente
        """
        try:
            if file_path.endswith('.geojson') or file_path.endswith('.json'):
                with open(file_path, 'r') as f:
                    geo_data = geojson.load(f)
                
                # Extraer información del GeoJSON
                area = self._process_geojson(geo_data, area_name)
                self.loaded_areas[area_name] = area
                return True
                
            elif file_path.endswith('.kml'):
                # Implementar parser KML si es necesario
                pass
                
        except Exception as e:
            print(f"Error cargando cartografía: {e}")
            return False
    
    def _process_geojson(self, geo_data: dict, area_name: str) -> MissionArea:
        """Procesa datos GeoJSON y extrae información relevante."""
        boundaries = []
        points_of_interest = []
        
        for feature in geo_data.get('features', []):
            geometry = feature.get('geometry', {})
            properties = feature.get('properties', {})
            
            if geometry.get('type') == 'Polygon':
                # Extraer perímetro
                coords = geometry.get('coordinates', [[]])[0]
                boundaries = [(lat, lng) for lng, lat in coords]
                
            elif geometry.get('type') == 'Point':
                # Punto de interés
                coords = geometry.get('coordinates', [0, 0])
                points_of_interest.append({
                    'name': properties.get('name', 'POI'),
                    'coordinates': (coords[1], coords[0]),  # lat, lng
                    'type': properties.get('type', 'general')
                })
        
        return MissionArea(
            name=area_name,
            boundaries=boundaries,
            points_of_interest=points_of_interest
        )
    
    def get_area_center_coordinates(self, area_name: str) -> Optional[Tuple[float, float]]:
        """
        Obtiene las coordenadas del centro de un área cargada.
        
        Args:
            area_name: Nombre del área
            
        Returns:
            Tuple[float, float]: (latitud, longitud) del centro o None si no existe
        """
        if area_name not in self.loaded_areas:
            return None
            
        area = self.loaded_areas[area_name]
        
        if not area.boundaries:
            # Si no hay boundaries, usar el primer POI
            if area.points_of_interest:
                return area.points_of_interest[0]['coordinates']
            return None
        
        # Calcular centro de los boundaries
        lats = [coord[0] for coord in area.boundaries]
        lngs = [coord[1] for coord in area.boundaries]
        
        center_lat = sum(lats) / len(lats)
        center_lng = sum(lngs) / len(lngs)
        
        return (center_lat, center_lng)
    
    def create_mission_from_command(self, natural_command: str, area_name: str = None) -> Dict:
        """
        Crea una misión a partir de un comando en lenguaje natural.
        
        Args:
            natural_command: Comando en lenguaje natural
            area_name: Nombre del área cargada (opcional)
            
        Returns:
            Dict: Misión generada
        """
        try:
            # Obtener información del área si está disponible
            area_info = ""
            center_coordinates = None
            boundary_coordinates = None
            
            if area_name and area_name in self.loaded_areas:
                area = self.loaded_areas[area_name]
                center_coordinates = self.get_area_center_coordinates(area_name)
                
                if center_coordinates:
                    area_info = f"""
                ÁREA GEOGRÁFICA ESPECÍFICA: {area.name}
                
                COORDENADAS DEL CENTRO: 
                - Latitud: {center_coordinates[0]:.6f}
                - Longitud: {center_coordinates[1]:.6f}
                
                LÍMITES DEL ÁREA: {area.boundaries}
                
                PUNTOS DE INTERÉS:
                {area.points_of_interest}
                
                INSTRUCCIONES IMPORTANTES:
                - TODOS los waypoints deben estar dentro o cerca de estas coordenadas específicas
                - USA las coordenadas del centro como punto de referencia principal
                - NO uses coordenadas genéricas o de otras ubicaciones
                - Genera waypoints en un radio máximo de 2km desde el centro
                """
            
            # Prompt mejorado para el LLM
            system_prompt = """
            Eres un experto piloto de drones militar con conocimientos avanzados en planificación de misiones.
            Tu tarea es convertir comandos en lenguaje natural en misiones de vuelo específicas.
            
            REGLAS CRÍTICAS PARA COORDENADAS:
            1. Si se proporciona un área geográfica específica, DEBES usar exclusivamente esas coordenadas
            2. NUNCA uses coordenadas genéricas como Madrid (40.416775, -3.703790)
            3. Los waypoints deben estar dentro del área especificada
            4. Usa las coordenadas del centro como referencia principal
            5. Genera waypoints realistas para la zona geográfica indicada
            
            Debes generar waypoints con coordenadas GPS precisas, altitudes apropiadas y acciones específicas.
            Considera factores como seguridad, eficiencia de combustible, cobertura del área y objetivos tácticos.
            
            Responde ÚNICAMENTE con un JSON válido con esta estructura:
            {
                "mission_name": "string",
                "description": "string", 
                "estimated_duration": "number (minutos)",
                "waypoints": [
                    {
                        "latitude": number,
                        "longitude": number,
                        "altitude": number,
                        "action": "string",
                        "duration": number,
                        "description": "string"
                    }
                ],
                "safety_considerations": ["string"],
                "success_criteria": ["string"],
                "area_used": "string"
            }
            
            Acciones disponibles: navigate, hover, scan, photograph, patrol, land, takeoff, search, monitor
            """
            
            user_prompt = f"""
            Comando: {natural_command}
            
            {area_info if area_info else "ÁREA: No se especificó área geográfica - usa coordenadas genéricas apropiadas"}
            
            Genera una misión detallada para este comando usando las coordenadas específicas del área.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3
            )
            
            # Parsear respuesta JSON
            mission_data = json.loads(response.choices[0].message.content)
            
            # Añadir metadatos
            mission_data['id'] = str(uuid.uuid4())
            mission_data['created_at'] = datetime.now().isoformat()
            mission_data['status'] = 'planned'
            mission_data['area_name'] = area_name
            mission_data['original_command'] = natural_command
            
            # Añadir coordenadas del centro si están disponibles
            if center_coordinates:
                mission_data['area_center'] = {
                    'latitude': center_coordinates[0],
                    'longitude': center_coordinates[1]
                }
            
            # Guardar misión
            mission_file = os.path.join(self.missions_dir, f"mission_{mission_data['id']}.json")
            with open(mission_file, 'w') as f:
                json.dump(mission_data, f, indent=2)
            
            self.current_mission = mission_data
            return mission_data
            
        except Exception as e:
            print(f"Error creando misión: {e}")
            return None
    
    def adaptive_mission_control(self, current_position: Tuple[float, float], 
                               situation_report: str, mission_id: str) -> Dict:
        """
        Control adaptativo de misión usando LLM para tomar decisiones en tiempo real.
        
        Args:
            current_position: Posición actual del dron (lat, lng)
            situation_report: Reporte de situación actual
            mission_id: ID de la misión actual
            
        Returns:
            Dict: Decisiones y modificaciones a la misión
        """
        try:
            # Cargar misión actual
            mission_file = os.path.join(self.missions_dir, f"mission_{mission_id}.json")
            with open(mission_file, 'r') as f:
                mission = json.load(f)
            
            system_prompt = """
            Eres un comandante de drones con capacidad de tomar decisiones tácticas en tiempo real.
            Basándote en la situación actual y la misión original, debes decidir si continuar, 
            modificar la ruta, cambiar prioridades o abortar la misión.
            
            Responde con JSON:
            {
                "decision": "continue|modify|abort|investigate",
                "reasoning": "string",
                "new_waypoints": [...], // si aplica
                "priority_change": "string", // si aplica
                "immediate_action": "string"
            }
            """
            
            user_prompt = f"""
            Posición actual: {current_position}
            Situación: {situation_report}
            Misión original: {mission['mission_name']} - {mission['description']}
            Waypoints restantes: {mission['waypoints']}
            
            ¿Qué decisión tomas?
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            print(f"Error en control adaptativo: {e}")
            return {"decision": "continue", "reasoning": "Error en análisis"}
    
    def get_available_missions(self) -> List[Dict]:
        """Obtiene lista de misiones disponibles."""
        missions = []
        
        for filename in os.listdir(self.missions_dir):
            if filename.startswith('mission_') and filename.endswith('.json'):
                try:
                    with open(os.path.join(self.missions_dir, filename), 'r') as f:
                        mission = json.load(f)
                        missions.append({
                            'id': mission['id'],
                            'name': mission['mission_name'],
                            'description': mission['description'],
                            'status': mission.get('status', 'planned'),
                            'created_at': mission['created_at']
                        })
                except Exception as e:
                    print(f"Error cargando misión {filename}: {e}")
        
        return missions
    
    def calculate_distance(self, point1: Tuple[float, float], 
                          point2: Tuple[float, float]) -> float:
        """Calcula distancia entre dos puntos GPS en metros."""
        lat1, lon1 = math.radians(point1[0]), math.radians(point1[1])
        lat2, lon2 = math.radians(point2[0]), math.radians(point2[1])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        r = 6371000  # Radio de la Tierra en metros
        
        return c * r
    
    def validate_mission_safety(self, mission: Dict) -> List[str]:
        """Valida la seguridad de una misión."""
        warnings = []
        
        for i, waypoint in enumerate(mission.get('waypoints', [])):
            # Verificar altitud
            if waypoint['altitude'] > 120:  # Límite legal en muchos países
                warnings.append(f"Waypoint {i+1}: Altitud excede límite legal (120m)")
            
            # Verificar distancia entre waypoints
            if i > 0:
                prev_wp = mission['waypoints'][i-1]
                distance = self.calculate_distance(
                    (prev_wp['latitude'], prev_wp['longitude']),
                    (waypoint['latitude'], waypoint['longitude'])
                )
                if distance > 10000:  # 10km
                    warnings.append(f"Waypoint {i+1}: Distancia muy larga ({distance/1000:.1f}km)")
        
        return warnings 