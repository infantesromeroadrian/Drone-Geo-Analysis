#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Planificador principal de misiones con IA.
Clase principal que orquesta la generación de misiones usando LLM.
Refactorizado para cumplir con principios de Single Responsibility.
"""

import json
import os
import uuid
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import openai
from openai.types.chat import ChatCompletionMessageParam

from src.utils.helpers import get_missions_directory, get_project_root
from src.utils.config import get_llm_config
from .mission_models import MissionArea
from .mission_parser import extract_json_from_response
from .mission_validator import validate_mission_safety
from .mission_utils import calculate_area_center

# Configurar logger
logger = logging.getLogger(__name__)


class LLMMissionPlanner:
    """
    Planificador de misiones inteligente usando LLM.
    Responsabilidad única: Generar misiones desde comandos naturales.
    """
    
    def __init__(self):
        """Inicializa el planificador con configuración LLM."""
        self.llm_config = get_llm_config()
        self.provider = self.llm_config["provider"]
        self.config = self.llm_config["config"]
        
        # Configurar cliente y directorios
        self._setup_client()
        self._setup_directories()
        
        logger.info(f"Mission Planner inicializado: {self.provider}")
    
    def _setup_client(self) -> None:
        """Configura el cliente LLM según el proveedor."""
        if self.provider == "docker":
            logger.info(f"Docker Model: {self.config['model']}")
            self.client = openai.OpenAI(
                base_url=self.config["base_url"],
                api_key=self.config["api_key"]
            )
        elif self.provider == "openai":
            logger.info("OpenAI API configurada")
            self.client = openai.OpenAI(api_key=self.config["api_key"])
    
    def _setup_directories(self) -> None:
        """Configura los directorios necesarios."""
        self.missions_dir = get_missions_directory()
        self.cartography_dir = os.path.join(get_project_root(), 
                                          "cartography")
        self.current_mission = None
        self.loaded_areas = {}
        
        # Crear directorio de cartografía si no existe
        os.makedirs(self.cartography_dir, exist_ok=True)
    
    def create_mission_from_command(self, natural_command: str, 
                                  area_name: Optional[str] = None) -> Optional[Dict]:
        """
        Crea una misión a partir de un comando en lenguaje natural.
        
        Args:
            natural_command: Comando en lenguaje natural
            area_name: Nombre del área cargada (opcional)
            
        Returns:
            Dict: Misión generada o None si falla
        """
        try:
            # Preparar información del área
            area_info, center_coords = self._prepare_area_info(area_name)
            
            # Crear prompts
            system_prompt = self._build_system_prompt()
            user_prompt = self._build_user_prompt(natural_command, area_info)
            
            # Obtener respuesta del LLM
            response_content = self._create_chat_completion([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ], temperature=0.3)
            
            # Procesar y enriquecer la misión
            mission_data = self._process_mission_response(
                response_content, natural_command, area_name, center_coords
            )
            
            # Guardar misión
            self._save_mission(mission_data)
            
            self.current_mission = mission_data
            logger.info(f"Misión creada: {mission_data['mission_name']}")
            return mission_data
            
        except Exception as e:
            logger.error(f"Error creando misión: {e}")
            return None
    
    def _create_chat_completion(self, messages: List[ChatCompletionMessageParam], 
                              temperature: Optional[float] = None) -> str:
        """Crea completion de chat usando el proveedor configurado."""
        temp = temperature if temperature is not None else self.config["temperature"]
        
        try:
            if self.provider == "docker":
                response = self._create_docker_completion(messages, temp)
            elif self.provider == "openai":
                response = self._create_openai_completion(messages, temp)
            
            content = response.choices[0].message.content
            return content if content else ""
            
        except Exception as e:
            logger.error(f"Error en {self.provider} completion: {e}")
            raise
    
    def _create_docker_completion(self, messages: List[ChatCompletionMessageParam], 
                                temperature: float):
        """Crea completion usando Docker Models."""
        return self.client.chat.completions.create(
            model=self.config["model"],
            messages=messages,
            temperature=temperature,
            max_tokens=self.config["max_tokens"],
            timeout=self.config.get("timeout", 60)
        )
    
    def _create_openai_completion(self, messages: List[ChatCompletionMessageParam], 
                                temperature: float):
        """Crea completion usando OpenAI API."""
        return self.client.chat.completions.create(
            model=self.config["model"],
            messages=messages,
            temperature=temperature,
            max_tokens=self.config["max_tokens"]
        )
    
    def load_cartography(self, file_path: str, area_name: str) -> bool:
        """
        Carga cartografía desde archivo.
        
        Args:
            file_path: Ruta al archivo de cartografía
            area_name: Nombre del área
            
        Returns:
            bool: True si se cargó correctamente
        """
        try:
            if file_path.endswith(('.geojson', '.json')):
                return self._load_geojson_cartography(file_path, area_name)
            elif file_path.endswith('.kml'):
                logger.warning("Soporte KML no implementado")
                return False
                
        except Exception as e:
            logger.error(f"Error cargando cartografía: {e}")
            return False
        
        return False
    
    def _load_geojson_cartography(self, file_path: str, area_name: str) -> bool:
        """Carga cartografía desde archivo GeoJSON."""
        try:
            logger.info(f"Cargando GeoJSON desde: {file_path}")
            
            # Verificar que el archivo existe
            if not os.path.exists(file_path):
                logger.error(f"Archivo no encontrado: {file_path}")
                return False
            
            # Leer y parsear archivo JSON
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                logger.info(f"Archivo leído, tamaño: {len(content)} caracteres")
                
                # Verificar que no esté vacío
                if not content.strip():
                    logger.error("Archivo GeoJSON está vacío")
                    return False
                
                # Parsear JSON
                try:
                    geo_data = json.loads(content)
                    logger.info("JSON parseado correctamente")
                except json.JSONDecodeError as json_error:
                    logger.error(f"Error parseando JSON: {json_error}")
                    logger.error(f"Contenido problemático (primeros 500 chars): {content[:500]}")
                    return False
            
            # Validar estructura GeoJSON básica
            if not isinstance(geo_data, dict):
                logger.error("GeoJSON debe ser un objeto JSON")
                return False
            
            if 'type' not in geo_data:
                logger.error("GeoJSON debe tener un campo 'type'")
                return False
            
            if geo_data.get('type') != 'FeatureCollection':
                logger.warning(f"Tipo GeoJSON inesperado: {geo_data.get('type')}, esperado 'FeatureCollection'")
            
            # Procesar features
            features = geo_data.get('features', [])
            logger.info(f"Procesando {len(features)} features")
            
            area = self._process_geojson(geo_data, area_name)
            self.loaded_areas[area_name] = area
            
            logger.info(f"Área '{area_name}' cargada exitosamente con {len(area.boundaries)} límites y {len(area.points_of_interest)} POIs")
            return True
            
        except Exception as e:
            logger.error(f"Error procesando GeoJSON: {e}", exc_info=True)
            return False
    
    def _process_geojson(self, geo_data: dict, area_name: str) -> MissionArea:
        """Procesa datos GeoJSON y extrae información relevante."""
        boundaries = []
        points_of_interest = []
        
        for feature in geo_data.get('features', []):
            geometry = feature.get('geometry', {})
            properties = feature.get('properties', {})
            
            if geometry.get('type') == 'Polygon':
                boundaries = self._extract_polygon_boundaries(geometry)
            elif geometry.get('type') == 'Point':
                poi = self._extract_point_of_interest(geometry, properties)
                points_of_interest.append(poi)
        
        return MissionArea(
            name=area_name,
            boundaries=boundaries,
            points_of_interest=points_of_interest
        )
    
    def _extract_polygon_boundaries(self, geometry: Dict) -> List[Tuple[float, float]]:
        """Extrae perímetro de un polígono."""
        coords = geometry.get('coordinates', [[]])[0]
        return [(lat, lng) for lng, lat in coords]
    
    def _extract_point_of_interest(self, geometry: Dict, 
                                 properties: Dict) -> Dict:
        """Extrae punto de interés."""
        coords = geometry.get('coordinates', [0, 0])
        return {
            'name': properties.get('name', 'POI'),
            'coordinates': (coords[1], coords[0]),  # lat, lng
            'type': properties.get('type', 'general')
        }
    
    def get_area_center_coordinates(self, area_name: str) -> Optional[Tuple[float, float]]:
        """Obtiene las coordenadas del centro de un área cargada."""
        if area_name not in self.loaded_areas:
            return None
            
        area = self.loaded_areas[area_name]
        return calculate_area_center(area)
    
    def _prepare_area_info(self, area_name: Optional[str]) -> Tuple[str, Optional[Tuple[float, float]]]:
        """Prepara la información del área para la generación de misión."""
        area_info = ""
        center_coordinates = None
        
        if area_name and area_name in self.loaded_areas:
            area = self.loaded_areas[area_name]
            center_coordinates = self.get_area_center_coordinates(area_name)
            
            if center_coordinates:
                area_info = self._format_area_info(area, center_coordinates)
        
        return area_info, center_coordinates
    
    def _format_area_info(self, area: MissionArea, 
                         center_coordinates: Tuple[float, float]) -> str:
        """Formatea la información del área para el prompt."""
        return f"""
        ÁREA GEOGRÁFICA ESPECÍFICA: {area.name}
        
        COORDENADAS DEL CENTRO: 
        - Latitud: {center_coordinates[0]:.6f}
        - Longitud: {center_coordinates[1]:.6f}
        
        LÍMITES DEL ÁREA: {area.boundaries}
        
        PUNTOS DE INTERÉS: {area.points_of_interest}
        
        INSTRUCCIONES:
        - Usar coordenadas específicas del área
        - Generar waypoints dentro del área
        - Radio máximo: 2km desde el centro
        """
    
    def _build_system_prompt(self) -> str:
        """Construye el prompt de sistema para generación de misiones."""
        return """
        Eres un experto en planificación de misiones de drones militares.
        Convierte comandos naturales en misiones de vuelo estructuradas.
        
        REGLAS CRÍTICAS:
        1. Usar coordenadas específicas del área si se proporciona
        2. Cada waypoint debe tener coordenadas GPS únicas
        3. Distribuir waypoints geográficamente (min 50-100m)
        4. Crear rutas lógicas con puntos progresivos
        5. Nunca repetir coordenadas exactas
        
        Responde ÚNICAMENTE con JSON válido:
        {
            "mission_name": "string",
            "description": "string", 
            "estimated_duration": number,
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
        
        Acciones: navigate, hover, scan, photograph, patrol, land, takeoff
        """
    
    def _build_user_prompt(self, natural_command: str, area_info: str) -> str:
        """Construye el prompt del usuario para generación de misiones."""
        area_context = (area_info if area_info else 
                       "ÁREA: No especificada - usar coordenadas apropiadas")
        
        return f"""
        Comando: {natural_command}
        
        {area_context}
        
        Genera una misión detallada para este comando.
        """
    
    def _process_mission_response(self, response_content: str, 
                                natural_command: str, 
                                area_name: Optional[str], 
                                center_coordinates: Optional[Tuple[float, float]]) -> Dict:
        """Procesa la respuesta del LLM y enriquece la misión."""
        # Parsear respuesta JSON
        mission_data = extract_json_from_response(response_content)
        
        # Añadir metadatos
        self._add_metadata(mission_data, natural_command, area_name)
        
        # Añadir coordenadas del centro si están disponibles
        if center_coordinates:
            mission_data['area_center'] = {
                'latitude': center_coordinates[0],
                'longitude': center_coordinates[1]
            }
        
        return mission_data
    
    def _add_metadata(self, mission_data: Dict, natural_command: str, 
                     area_name: Optional[str]) -> None:
        """Añade metadatos básicos a la misión."""
        mission_data['id'] = str(uuid.uuid4())
        mission_data['created_at'] = datetime.now().isoformat()
        mission_data['status'] = 'planned'
        mission_data['area_name'] = area_name
        mission_data['original_command'] = natural_command
        mission_data['llm_provider'] = self.provider
        mission_data['llm_model'] = self.config["model"]
    
    def _save_mission(self, mission_data: Dict) -> None:
        """Guarda la misión en archivo JSON."""
        mission_file = os.path.join(
            self.missions_dir, 
            f"mission_{mission_data['id']}.json"
        )
        with open(mission_file, 'w', encoding='utf-8') as f:
            json.dump(mission_data, f, indent=2, ensure_ascii=False)
    
    def get_available_missions(self) -> List[Dict]:
        """Obtiene lista de misiones disponibles."""
        missions = []
        
        for filename in os.listdir(self.missions_dir):
            if filename.startswith('mission_') and filename.endswith('.json'):
                try:
                    mission_info = self._load_mission_info(filename)
                    if mission_info:
                        missions.append(mission_info)
                except Exception as e:
                    logger.error(f"Error cargando misión {filename}: {e}")
        
        return missions
    
    def _load_mission_info(self, filename: str) -> Optional[Dict]:
        """Carga información básica de una misión."""
        try:
            with open(os.path.join(self.missions_dir, filename), 
                     'r', encoding='utf-8') as f:
                mission = json.load(f)
                return {
                    'id': mission['id'],
                    'name': mission['mission_name'],
                    'description': mission['description'],
                    'status': mission.get('status', 'planned'),
                    'created_at': mission['created_at']
                }
        except Exception:
            return None
    
    def validate_mission(self, mission: Dict) -> List[str]:
        """
        Valida la seguridad de una misión.
        Delegada al módulo de validación.
        """
        return validate_mission_safety(mission) 