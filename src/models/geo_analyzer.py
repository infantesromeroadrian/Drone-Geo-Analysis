#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo que implementa el modelo de análisis geográfico de imágenes.
"""

import logging
import json
import re
from openai import OpenAI
from openai.types.chat import ChatCompletion
from typing import Dict, Any, List, Optional

from src.utils.config import get_llm_config

logger = logging.getLogger(__name__)

class GeoAnalyzer:
    """
    Clase que implementa la lógica para analizar imágenes y determinar
    su ubicación geográfica usando LLM con análisis de visión.
    """
    
    def __init__(self):
        """Inicializa el analizador geográfico."""
        self.llm_config = get_llm_config()
        self.provider = self.llm_config["provider"]
        self.config = self.llm_config["config"]
        
        # Configurar cliente según proveedor
        self._setup_client()
        
        logger.info(f"Analizador geográfico inicializado con proveedor: {self.provider}")
    
    def _setup_client(self) -> None:
        """Configura el cliente LLM según el proveedor."""
        if self.provider == "docker":
            logger.warning("⚠️ Docker Models no soporta análisis de imágenes. Usando OpenAI como fallback.")
            self._setup_openai_fallback()
        elif self.provider == "openai":
            logger.info("Inicializando OpenAI API para análisis de imágenes")
            self.client = OpenAI(api_key=self.config["api_key"])
        
    def _setup_openai_fallback(self) -> None:
        """Configura OpenAI como fallback para análisis de imágenes."""
        from src.utils.config import get_openai_config
        self.config = get_openai_config()
        self.client = OpenAI(api_key=self.config["api_key"])
        self.provider = "openai"  # Override para este caso específico
        
    def analyze_image(self, base64_image: str, metadata: Dict[str, Any], image_format: str = 'jpeg') -> Dict[str, Any]:
        """
        Analiza una imagen para detectar su ubicación geográfica.
        
        Args:
            base64_image: Imagen codificada en base64
            metadata: Metadatos de la imagen
            image_format: Formato de la imagen ('jpeg', 'png', 'gif', 'webp')
            
        Returns:
            Diccionario con los resultados del análisis
        """
        logger.info(f"Analizando imagen: {metadata.get('filename', 'unknown')} con {self.provider}")
        
        # Validar configuración de API
        api_validation = self._validate_api_configuration()
        if "error" in api_validation:
            return api_validation
        
        try:
            # Crear solicitud a la API
            response = self._create_vision_request(base64_image, metadata, image_format)
            
            # Procesar respuesta
            result = self._process_response(response)
            logger.info(f"Análisis completado con éxito usando {self.provider}")
            return result
            
        except Exception as e:
            logger.error(f"Error en el análisis con {self.provider}: {str(e)}")
            return self._create_error_response(str(e))
    
    def _validate_api_configuration(self) -> Dict[str, Any]:
        """Valida la configuración de la API."""
        if not self.config.get("api_key") or self.config["api_key"].startswith("your_"):
            logger.error("API key de OpenAI no configurada o inválida")
            return {
                "error": "API key de OpenAI no configurada. El análisis de imágenes requiere OpenAI GPT-4 Vision.",
                "country": "No configurado",
                "city": "No configurado", 
                "district": "No configurado",
                "neighborhood": "No configurado",
                "street": "No configurado",
                "confidence": 0,
                "supporting_evidence": ["API key de OpenAI requerida para análisis de imágenes"]
            }
        return {"valid": True}
        
    def _create_vision_request(self, base64_image: str, metadata: Dict[str, Any], image_format: str):
        """Crea la solicitud a la API de visión."""
            system_prompt = self._build_system_prompt()
            user_prompt = self._build_user_prompt(metadata)
            
        return self.client.chat.completions.create(
                model=self.config["model"],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": [
                        {"type": "text", "text": user_prompt},
                        {"type": "image_url", 
                     "image_url": {"url": f"data:image/{image_format};base64,{base64_image}"}}
                    ]}
                ],
                temperature=self.config["temperature"],
                max_tokens=self.config["max_tokens"],
            )
            
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Crea una respuesta de error estandarizada."""
            return {
            "error": error_message,
                "country": "Error",
                "city": "Error",
                "district": "Error",
                "neighborhood": "Error",
                "street": "Error",
                "confidence": 0,
            "supporting_evidence": [f"Error con {self.provider}: {error_message}"]
            }
    
    def _build_system_prompt(self) -> str:
        """Construye el prompt de sistema para la API."""
        return self._get_osint_analysis_instructions()
        
    def _get_osint_analysis_instructions(self) -> str:
        """Obtiene las instrucciones de análisis OSINT."""
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
        """Construye el prompt del usuario para la API."""
        image_info = self._extract_image_metadata(metadata)
        json_format = self._get_response_format_template()
        
        return f"""
        Analiza esta imagen y determina su ubicación geográfica (país, ciudad, distrito, barrio, calle) 
        basándote en las características visibles como arquitectura, carteles, vegetación, personas, 
        vehículos y estructura urbana.
        
        {image_info}
        
        Por favor, presenta tus hallazgos en formato JSON con los siguientes campos:
        {json_format}
        """
    
    def _extract_image_metadata(self, metadata: Dict[str, Any]) -> str:
        """Extrae metadatos relevantes de la imagen."""
        return f"""Formato de la imagen: {metadata.get('format', 'desconocido')}
        Dimensiones: {metadata.get('dimensions', (0, 0))}"""
    
    def _get_response_format_template(self) -> str:
        """Obtiene la plantilla del formato de respuesta JSON."""
        return """{
            "country": "nombre del país",
            "city": "nombre de la ciudad",
            "district": "nombre del distrito",
            "neighborhood": "nombre del barrio",
            "street": "nombre de la calle",
            "coordinates": {
                "latitude": valor de latitud (número decimal),
                "longitude": valor de longitud (número decimal)
            },
            "confidence": porcentaje de confianza (0-100),
            "supporting_evidence": ["elemento 1", "elemento 2", ...],
            "possible_alternatives": [
                {
                    "country": "país alternativo",
                    "city": "ciudad alternativa",
                    "confidence": porcentaje de confianza (0-100)
                }
            ]
        }"""
        
    def _process_response(self, response: ChatCompletion) -> Dict[str, Any]:
        """Procesa la respuesta de la API."""
        try:
            content = self._extract_response_content(response)
            parsed_json = self._parse_json_response(content)
            return parsed_json
            
        except Exception as e:
            logger.error(f"Error al procesar respuesta: {str(e)}")
            return self._create_parsing_error_response(str(e), content if 'content' in locals() else "No disponible")
    
    def _extract_response_content(self, response: ChatCompletion) -> str:
        """Extrae el contenido de la respuesta de la API."""
        content = response.choices[0].message.content
        return content.strip() if content else ""
    
    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """Parsea el contenido JSON de la respuesta."""
        # Extraer JSON de marcadores de código
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
            if json_match:
                content = json_match.group(1)
            else:
                # Intentar extraer JSON sin formato
                json_match = re.search(r'({[\s\S]*})', content)
                if json_match:
                    content = json_match.group(1)
            
        return json.loads(content)
            
    def _create_parsing_error_response(self, error_message: str, raw_content: str) -> Dict[str, Any]:
        """Crea una respuesta de error de parsing."""
            return {
            "error": f"Error al procesar la respuesta: {error_message}",
                "country": "Error de formato",
                "city": "Error de formato",
                "district": "Error de formato",
                "neighborhood": "Error de formato",
                "street": "Error de formato",
                "confidence": 0,
                "supporting_evidence": [],
            "raw_response": raw_content
            } 