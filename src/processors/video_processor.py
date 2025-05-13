#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Procesador de video en tiempo real desde drones.
"""

import cv2
import threading
import time
import queue
import logging
import base64
from typing import Dict, Any, Optional, List, Tuple

from src.models.geo_analyzer import GeoAnalyzer

logger = logging.getLogger(__name__)

class VideoProcessor:
    """Procesador de video en tiempo real desde drones."""
    
    def __init__(self, analyzer: GeoAnalyzer, analysis_interval: int = 5):
        """
        Inicializa el procesador de video.
        
        Args:
            analyzer: Instancia del analizador geográfico
            analysis_interval: Intervalo entre análisis en segundos
        """
        self.analyzer = analyzer
        self.analysis_interval = analysis_interval
        self.stream_url = None
        self.processing = False
        self.last_frame = None
        self.last_analysis = None
        self.frame_queue = queue.Queue(maxsize=10)
        self.analysis_queue = queue.Queue(maxsize=5)
        self.capture_thread = None
        self.analysis_thread = None
        logger.info("Procesador de video inicializado")
    
    def start_processing(self, stream_url: str) -> bool:
        """
        Inicia el procesamiento del stream de video.
        
        Args:
            stream_url: URL del stream de video
            
        Returns:
            True si se inició correctamente, False en caso contrario
        """
        try:
            self.stream_url = stream_url
            self.processing = True
            
            # Iniciar thread de captura
            self.capture_thread = threading.Thread(target=self._capture_frames)
            self.capture_thread.daemon = True
            self.capture_thread.start()
            
            # Iniciar thread de análisis
            self.analysis_thread = threading.Thread(target=self._analyze_frames)
            self.analysis_thread.daemon = True
            self.analysis_thread.start()
            
            logger.info(f"Procesamiento de video iniciado para: {stream_url}")
            return True
        except Exception as e:
            logger.error(f"Error al iniciar procesamiento de video: {str(e)}")
            return False
    
    def stop_processing(self) -> bool:
        """
        Detiene el procesamiento del stream de video.
        
        Returns:
            True si se detuvo correctamente
        """
        self.processing = False
        if self.capture_thread:
            self.capture_thread.join(timeout=2.0)
        if self.analysis_thread:
            self.analysis_thread.join(timeout=2.0)
        
        logger.info("Procesamiento de video detenido")
        return True
    
    def get_last_frame(self) -> Optional[bytes]:
        """
        Obtiene el último frame capturado.
        
        Returns:
            Último frame en formato JPEG o None
        """
        if self.last_frame is None:
            return None
        
        return self.last_frame
    
    def get_last_analysis(self) -> Optional[Dict[str, Any]]:
        """
        Obtiene el último análisis realizado.
        
        Returns:
            Diccionario con los resultados del análisis o None
        """
        return self.last_analysis
    
    def _capture_frames(self):
        """Thread para capturar frames del stream de video."""
        try:
            # Intentar abrir stream de video
            cap = cv2.VideoCapture(self.stream_url)
            if not cap.isOpened():
                logger.error(f"No se pudo abrir el stream: {self.stream_url}")
                return
            
            last_frame_time = 0
            
            while self.processing:
                ret, frame = cap.read()
                if not ret:
                    logger.warning("Error al leer frame, reintentando...")
                    time.sleep(0.5)
                    continue
                
                # Procesar solo cada 200ms para no sobrecargar
                current_time = time.time()
                if current_time - last_frame_time > 0.2:
                    # Convertir frame a JPEG
                    _, buffer = cv2.imencode('.jpg', frame)
                    jpeg_bytes = buffer.tobytes()
                    
                    # Actualizar último frame
                    self.last_frame = jpeg_bytes
                    
                    # Añadir a la cola para análisis si hay espacio
                    if not self.frame_queue.full():
                        self.frame_queue.put(jpeg_bytes)
                    
                    last_frame_time = current_time
            
            cap.release()
        except Exception as e:
            logger.error(f"Error en thread de captura: {str(e)}")
    
    def _analyze_frames(self):
        """Thread para analizar frames periódicamente."""
        last_analysis_time = 0
        
        while self.processing:
            current_time = time.time()
            
            # Analizar solo en el intervalo especificado
            if current_time - last_analysis_time > self.analysis_interval:
                try:
                    # Obtener el frame más reciente de la cola (descartar antiguos)
                    frame = None
                    while not self.frame_queue.empty():
                        frame = self.frame_queue.get()
                    
                    if frame is None:
                        time.sleep(0.5)
                        continue
                    
                    # Convertir frame a base64 para el análisis
                    base64_image = base64.b64encode(frame).decode('utf-8')
                    
                    # Crear metadatos
                    metadata = {
                        "source": "drone_stream",
                        "timestamp": current_time,
                        "format": "JPEG",
                        "dimensions": (640, 480)  # Tamaño aproximado
                    }
                    
                    # Analizar la imagen
                    results = self.analyzer.analyze_image(base64_image, metadata)
                    
                    # Actualizar último análisis
                    self.last_analysis = results
                    
                    # Añadir a la cola de análisis si hay espacio
                    if not self.analysis_queue.full():
                        self.analysis_queue.put({
                            "timestamp": current_time,
                            "results": results,
                            "frame": frame
                        })
                    
                    last_analysis_time = current_time
                    logger.info("Análisis de frame completado")
                    
                except Exception as e:
                    logger.error(f"Error en análisis de frame: {str(e)}")
                    time.sleep(1.0)  # Esperar un poco antes de reintentar
            
            time.sleep(0.1)  # Evitar uso excesivo de CPU 