#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Clase base abstracta para todos los controladores de drones.
"""

from abc import ABC, abstractmethod
import logging
from typing import Dict, Any, List, Tuple, Optional

logger = logging.getLogger(__name__)

class BaseDrone(ABC):
    """Clase base abstracta para todos los controladores de drones."""
    
    @abstractmethod
    def connect(self) -> bool:
        """Establece conexión con el dron."""
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """Desconecta del dron."""
        pass
    
    @abstractmethod
    def take_off(self, altitude: float) -> bool:
        """Despega el dron hasta la altitud especificada."""
        pass
    
    @abstractmethod
    def land(self) -> bool:
        """Aterriza el dron."""
        pass
    
    @abstractmethod
    def move_to(self, latitude: float, longitude: float, altitude: float) -> bool:
        """Mueve el dron a las coordenadas especificadas."""
        pass
    
    @abstractmethod
    def capture_image(self) -> str:
        """Captura una imagen y devuelve la ruta al archivo."""
        pass
    
    @abstractmethod
    def start_video_stream(self) -> str:
        """Inicia la transmisión de video y devuelve el URL del stream."""
        pass
    
    @abstractmethod
    def stop_video_stream(self) -> bool:
        """Detiene la transmisión de video."""
        pass
    
    @abstractmethod
    def get_telemetry(self) -> Dict[str, Any]:
        """Obtiene datos telemétricos del dron."""
        pass
    
    @abstractmethod
    def execute_mission(self, mission_data: Dict[str, Any]) -> bool:
        """Ejecuta una misión pre-programada."""
        pass 