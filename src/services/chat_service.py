#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servicio de chat contextual para análisis de imágenes.
Permite hacer preguntas sobre imágenes ya analizadas usando YOLO + GPT-4 Vision.
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from openai import OpenAI
from src.utils.config import get_openai_config

logger = logging.getLogger(__name__)

class ChatService:
    """
    Servicio que maneja conversaciones contextuales sobre imágenes analizadas.
    Combina información de YOLO y GPT-4 Vision para responder preguntas específicas.
    """
    
    def __init__(self):
        """Inicializa el servicio de chat."""
        self.config = get_openai_config()
        self.client = OpenAI(api_key=self.config["api_key"])
        self.context_storage = {}  # Almacena contextos de análisis por sesión
        logger.info("Servicio de chat contextual inicializado")
    
    def store_analysis_context(self, session_id: str, analysis_results: Dict[str, Any], 
                             yolo_results: Dict[str, Any], image_filename: str) -> None:
        """
        Almacena el contexto de un análisis para futuras consultas.
        
        Args:
            session_id: ID único de la sesión
            analysis_results: Resultados del análisis geográfico
            yolo_results: Resultados de detección YOLO
            image_filename: Nombre del archivo de imagen
        """
        self.context_storage[session_id] = {
            "timestamp": datetime.now().isoformat(),
            "image_filename": image_filename,
            "geographic_analysis": analysis_results,
            "yolo_detection": yolo_results,
            "chat_history": []
        }
        logger.info(f"Contexto almacenado para sesión: {session_id}")
    
    def ask_question(self, session_id: str, question: str) -> Dict[str, Any]:
        """
        Procesa una pregunta sobre la imagen analizada.
        
        Args:
            session_id: ID de la sesión
            question: Pregunta del usuario
            
        Returns:
            Respuesta del chat con contexto
        """
        try:
            # Verificar si existe contexto para esta sesión
            if session_id not in self.context_storage:
                return {
                    "error": "No hay contexto de análisis disponible para esta sesión",
                    "response": "Por favor, analiza una imagen primero antes de hacer preguntas.",
                    "status": "error"
                }
            
            context = self.context_storage[session_id]
            
            # Construir prompt contextual
            system_prompt = self._build_chat_system_prompt(context)
            user_prompt = self._build_chat_user_prompt(question, context)
            
            # Crear conversación con historial
            messages = [
                {"role": "system", "content": system_prompt}
            ]
            
            # Agregar historial de chat
            for chat_entry in context["chat_history"]:
                messages.append({"role": "user", "content": chat_entry["question"]})
                messages.append({"role": "assistant", "content": chat_entry["response"]})
            
            # Agregar pregunta actual
            messages.append({"role": "user", "content": user_prompt})
            
            # Obtener respuesta de GPT-4
            response = self.client.chat.completions.create(
                model=self.config["model"],
                messages=messages,
                temperature=0.3,
                max_tokens=1000,
            )
            
            # Extraer respuesta
            answer = response.choices[0].message.content.strip()
            
            # Guardar en historial
            context["chat_history"].append({
                "question": question,
                "response": answer,
                "timestamp": datetime.now().isoformat()
            })
            
            return {
                "response": answer,
                "question": question,
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error en chat contextual: {str(e)}")
            return {
                "error": str(e),
                "response": "Lo siento, ocurrió un error al procesar tu pregunta.",
                "status": "error"
            }
    
    def get_chat_history(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Obtiene el historial de chat para una sesión.
        
        Args:
            session_id: ID de la sesión
            
        Returns:
            Lista del historial de chat
        """
        if session_id not in self.context_storage:
            return []
        
        return self.context_storage[session_id]["chat_history"]
    
    def clear_chat_history(self, session_id: str) -> bool:
        """
        Limpia el historial de chat para una sesión.
        
        Args:
            session_id: ID de la sesión
            
        Returns:
            True si se limpió exitosamente
        """
        if session_id in self.context_storage:
            self.context_storage[session_id]["chat_history"] = []
            return True
        return False
    
    def get_context_summary(self, session_id: str) -> Dict[str, Any]:
        """
        Obtiene un resumen del contexto de análisis.
        
        Args:
            session_id: ID de la sesión
            
        Returns:
            Resumen del contexto
        """
        if session_id not in self.context_storage:
            return {"error": "No hay contexto disponible"}
        
        context = self.context_storage[session_id]
        geo_analysis = context["geographic_analysis"]
        yolo_detection = context["yolo_detection"]
        
        return {
            "image_filename": context["image_filename"],
            "timestamp": context["timestamp"],
            "geographic_results": {
                "country": geo_analysis.get("country", "No determinado"),
                "city": geo_analysis.get("city", "No determinado"),
                "confidence": geo_analysis.get("confidence", 0)
            },
            "yolo_results": {
                "total_objects": yolo_detection.get("total_objects", 0),
                "categories": len(yolo_detection.get("object_summary", {})),
                "top_objects": list(yolo_detection.get("object_summary", {}).keys())[:5]
            },
            "chat_messages": len(context["chat_history"])
        }
    
    def _build_chat_system_prompt(self, context: Dict[str, Any]) -> str:
        """Construye el prompt de sistema para el chat."""
        geo_analysis = context["geographic_analysis"]
        yolo_detection = context["yolo_detection"]
        
        return f"""
        Eres un asistente especializado en análisis de imágenes que puede responder preguntas 
        sobre una imagen que ya fue analizada usando YOLO 11 para detección de objetos y 
        GPT-4 Vision para análisis geográfico.
        
        CONTEXTO DE LA IMAGEN ANALIZADA:
        - Archivo: {context["image_filename"]}
        - Fecha de análisis: {context["timestamp"]}
        
        RESULTADOS DEL ANÁLISIS GEOGRÁFICO:
        - País: {geo_analysis.get("country", "No determinado")}
        - Ciudad: {geo_analysis.get("city", "No determinado")}
        - Distrito: {geo_analysis.get("district", "No determinado")}
        - Confianza: {geo_analysis.get("confidence", 0)}%
        - Evidencia: {', '.join(geo_analysis.get("supporting_evidence", []))}
        
        RESULTADOS DE DETECCIÓN DE OBJETOS (YOLO 11):
        - Total de objetos: {yolo_detection.get("total_objects", 0)}
        - Objetos detectados: {json.dumps(yolo_detection.get("object_summary", {}), indent=2)}
        - Objetos prominentes: {json.dumps(yolo_detection.get("prominent_objects", []), indent=2)}
        - Indicadores geográficos: {json.dumps(yolo_detection.get("geographic_indicators", {}), indent=2)}
        
        INSTRUCCIONES:
        1. Responde preguntas específicas sobre la imagen usando esta información
        2. Combina datos de YOLO y análisis geográfico cuando sea relevante
        3. Sé preciso con números y detalles técnicos
        4. Explica cómo llegaste a tus conclusiones
        5. Si no tienes la información específica, di que no la tienes
        6. Mantén las respuestas concisas pero informativas
        7. Usa emojis apropiados para hacer las respuestas más amigables
        
        Puedes responder preguntas sobre:
        - Objetos detectados (tipos, cantidades, ubicaciones)
        - Análisis geográfico (por qué se determinó cierta ubicación)
        - Comparaciones entre diferentes elementos
        - Detalles técnicos del análisis
        - Confianza en los resultados
        """
    
    def _build_chat_user_prompt(self, question: str, context: Dict[str, Any]) -> str:
        """Construye el prompt del usuario para el chat."""
        return f"""
        Pregunta sobre la imagen "{context["image_filename"]}":
        
        {question}
        
        Por favor responde usando toda la información disponible del análisis.
        """
    
    def get_suggested_questions(self, session_id: str) -> List[str]:
        """
        Genera preguntas sugeridas basadas en el contexto.
        
        Args:
            session_id: ID de la sesión
            
        Returns:
            Lista de preguntas sugeridas
        """
        if session_id not in self.context_storage:
            return []
        
        context = self.context_storage[session_id]
        yolo_detection = context["yolo_detection"]
        geo_analysis = context["geographic_analysis"]
        
        suggestions = []
        
        # Preguntas sobre objetos detectados
        if yolo_detection.get("total_objects", 0) > 0:
            suggestions.append(f"¿Cuántos objetos detectó YOLO exactamente?")
            
            top_objects = list(yolo_detection.get("object_summary", {}).keys())
            if top_objects:
                suggestions.append(f"¿Puedes describir los {top_objects[0]} que detectaste?")
        
        # Preguntas sobre análisis geográfico
        if geo_analysis.get("confidence", 0) > 0:
            suggestions.append(f"¿Cómo determinaste que era {geo_analysis.get('country', 'este país')}?")
            suggestions.append(f"¿Qué nivel de confianza tienes en el análisis?")
        
        # Preguntas sobre la combinación
        suggestions.append("¿Cómo te ayudó YOLO a mejorar el análisis geográfico?")
        suggestions.append("¿Qué elementos fueron más importantes para la identificación?")
        
        return suggestions[:6]  # Máximo 6 sugerencias 