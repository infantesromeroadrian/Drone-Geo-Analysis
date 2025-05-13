#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo que implementa el modelo de análisis geográfico de imágenes.
"""

import logging
import openai
from typing import Dict, Any, List, Optional

from src.utils.config import get_openai_config

logger = logging.getLogger(__name__)

class GeoAnalyzer:
    """
    Clase que implementa la lógica para analizar imágenes y determinar
    su ubicación geográfica usando GPT-4 con análisis de visión.
    """
    
    def __init__(self):
        """Inicializa el analizador geográfico."""
        self.config = get_openai_config()
        openai.api_key = self.config["api_key"]
        logger.info("Inicializado el analizador geográfico")
        
    def analyze_image(self, base64_image: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analiza una imagen para detectar su ubicación geográfica.
        
        Args:
            base64_image: Imagen codificada en base64
            metadata: Metadatos de la imagen
            
        Returns:
            Diccionario con los resultados del análisis
        """
        logger.info(f"Analizando imagen: {metadata.get('filename', 'unknown')}")
        
        try:
            # Construir el sistema de prompt
            system_prompt = self._build_system_prompt()
            
            # Construir el mensaje del usuario
            user_prompt = self._build_user_prompt(metadata)
            
            # Crear la solicitud a la API
            response = openai.ChatCompletion.create(
                model=self.config["model"],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": [
                        {"type": "text", "text": user_prompt},
                        {"type": "image_url", 
                         "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]}
                ],
                temperature=self.config["temperature"],
                max_tokens=self.config["max_tokens"],
            )
            
            # Procesar respuesta
            result = self._process_response(response)
            logger.info("Análisis completado con éxito")
            return result
            
        except Exception as e:
            logger.error(f"Error en el análisis: {str(e)}")
            return {
                "error": str(e),
                "country": "Error",
                "city": "Error",
                "district": "Error",
                "neighborhood": "Error",
                "street": "Error",
                "confidence": 0,
                "supporting_evidence": []
            }
    
    def _build_system_prompt(self) -> str:
        """
        Construye el prompt de sistema para la API.
        
        Returns:
            Prompt de sistema
        """
        return """
        Eres un sistema avanzado de análisis de inteligencia visual OSINT especializado en 
        identificación geográfica. Tu tarea es analizar la imagen proporcionada y determinar 
        con la mayor precisión posible la ubicación geográfica donde fue tomada.
        
        Debes analizar cuidadosamente los siguientes elementos:
        1. Arquitectura y estilo de los edificios
        2. Señalización, carteles y texto visible
        3. Vegetación y paisaje natural
        4. Personas, vestimenta y características culturales
        5. Vehículos y sistemas de transporte
        6. Estructura urbana y organización de calles
        7. Monumentos o puntos de referencia
        8. Cualquier otro elemento distintivo
        
        Para cada identificación, proporciona:
        - País: Nombre del país
        - Ciudad: Nombre de la ciudad
        - Distrito: Área administrativa mayor
        - Barrio: Vecindario específico
        - Calle: Nombre de la calle si es visible
        - Coordenadas: Latitud y longitud aproximadas (con la mayor precisión posible)
        - Nivel de confianza: Porcentaje estimado de certeza (0-100%)
        - Evidencia de apoyo: Lista de elementos visuales que respaldan tu conclusión
        - Alternativas posibles: Otras ubicaciones que podrían coincidir
        
        Proporciona únicamente la información que puedas determinar con razonable certeza.
        Si no puedes identificar algún nivel, indica "No determinado".
        
        Responde ÚNICAMENTE en formato JSON para facilitar el procesamiento automático.
        """
    
    def _build_user_prompt(self, metadata: Dict[str, Any]) -> str:
        """
        Construye el prompt del usuario para la API.
        
        Args:
            metadata: Metadatos de la imagen
            
        Returns:
            Prompt del usuario
        """
        return f"""
        Analiza esta imagen y determina su ubicación geográfica (país, ciudad, distrito, barrio, calle) 
        basándote en las características visibles como arquitectura, carteles, vegetación, personas, 
        vehículos y estructura urbana.
        
        Formato de la imagen: {metadata.get('format', 'desconocido')}
        Dimensiones: {metadata.get('dimensions', (0, 0))}
        
        Por favor, presenta tus hallazgos en formato JSON con los siguientes campos:
        {{
            "country": "nombre del país",
            "city": "nombre de la ciudad",
            "district": "nombre del distrito",
            "neighborhood": "nombre del barrio",
            "street": "nombre de la calle",
            "coordinates": {{
                "latitude": valor de latitud (número decimal),
                "longitude": valor de longitud (número decimal)
            }},
            "confidence": porcentaje de confianza (0-100),
            "supporting_evidence": ["elemento 1", "elemento 2", ...],
            "possible_alternatives": [
                {{
                    "country": "país alternativo",
                    "city": "ciudad alternativa",
                    "confidence": porcentaje de confianza (0-100)
                }}
            ]
        }}
        """
        
    def _process_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa la respuesta de la API.
        
        Args:
            response: Respuesta completa de la API
            
        Returns:
            Datos extraídos de la respuesta
        """
        try:
            # Extraer el contenido de la respuesta
            content = response.choices[0].message.content.strip()
            
            # Intentar parsear el JSON
            import json
            import re
            
            # Extraer JSON de la respuesta si está envuelto en marcadores de código
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
            if json_match:
                content = json_match.group(1)
            else:
                # Intentar extraer JSON sin formato
                json_match = re.search(r'({[\s\S]*})', content)
                if json_match:
                    content = json_match.group(1)
            
            # Parsear el resultado
            result = json.loads(content)
            return result
            
        except Exception as e:
            logger.error(f"Error al procesar respuesta: {str(e)}")
            return {
                "error": f"Error al procesar la respuesta: {str(e)}",
                "country": "Error de formato",
                "city": "Error de formato",
                "district": "Error de formato",
                "neighborhood": "Error de formato",
                "street": "Error de formato",
                "confidence": 0,
                "supporting_evidence": [],
                "raw_response": content if 'content' in locals() else "No disponible"
            } 