#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de interfaz web para la herramienta de análisis geográfico de imágenes.
Permite usar la herramienta a través de un navegador web.
"""

import os
import sys
import logging
import json
import base64
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from dotenv import load_dotenv
import tempfile
import time
from typing import Dict, Any

# Agregar la ruta del proyecto al PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar módulos internos
from src.models.geo_analyzer import GeoAnalyzer
from src.models.mission_planner import LLMMissionPlanner
from src.utils.config import setup_logging
from src.utils.helpers import get_image_metadata, save_analysis_results_with_filename

# Configurar aplicación Flask
app = Flask(__name__, 
           static_folder='templates/static',
           template_folder='templates')

# Cargar variables de entorno
load_dotenv()

# Configurar logging ANTES de las importaciones condicionales
setup_logging()
logger = logging.getLogger(__name__)

# Verificar API key
if "OPENAI_API_KEY" not in os.environ:
    logger.error("No se encontró OPENAI_API_KEY en las variables de entorno")
    print("Error: Se requiere una API key de OpenAI. Agrégala al archivo .env")
    sys.exit(1)

# Importaciones condicionales - usar módulos reales si están disponibles, sino usar mocks
try:
    from src.drones.dji_controller import DJIDroneController
    from src.processors.video_processor import VideoProcessor
    from src.processors.change_detector import ChangeDetector
    from src.geo.geo_triangulation import GeoTriangulation
    from src.geo.geo_correlator import GeoCorrelator
    USE_REAL_MODULES = True
    logger.info("Módulos reales importados correctamente")
except ImportError as e:
    logger.warning(f"No se pudieron importar módulos reales: {e}. Usando mocks.")
    USE_REAL_MODULES = False

# Inicializar componentes
analyzer = GeoAnalyzer()
mission_planner = LLMMissionPlanner()

# Objetos mock para pruebas
class MockDroneController:
    def __init__(self):
        # Coordenadas por defecto (Madrid), pero se pueden actualizar dinámicamente
        self.current_position = {
            "latitude": 40.416775,
            "longitude": -3.703790
        }
    
    def connect(self): return True
    def disconnect(self): return True
    def take_off(self, altitude): return True
    def land(self): return True
    def start_video_stream(self): return "mock://stream"
    def stop_video_stream(self): return True
    
    def update_position(self, latitude: float, longitude: float):
        """Actualiza la posición actual del dron mock."""
        self.current_position["latitude"] = latitude
        self.current_position["longitude"] = longitude
        logger.info(f"🚁 MockDrone reposicionado a: {latitude:.6f}, {longitude:.6f}")
    
    def get_telemetry(self): 
        return {
            "battery": 75,
            "gps": {
                "latitude": self.current_position["latitude"],
                "longitude": self.current_position["longitude"],
                "satellites": 8,
                "signal_quality": 4
            },
            "altitude": 50.5,
            "speed": {
                "horizontal": 5.2,
                "vertical": 0.0
            },
            "orientation": {
                "pitch": 0.0,
                "roll": 0.0,
                "yaw": 90.0
            },
            "signal_strength": 85,
            "timestamp": datetime.now().timestamp()
        }

class MockProcessor:
    def __init__(self, *args): pass
    def start_processing(self, *args): return True
    def stop_processing(self): return True

# Usar objetos mock en lugar de implementaciones reales
# drone_controller = MockDroneController()
# video_processor = MockProcessor()
# change_detector = MockProcessor()
# geo_triangulation = MockProcessor()
# geo_correlator = MockProcessor()

# Inicializar componentes según disponibilidad
if USE_REAL_MODULES:
    try:
        drone_controller = DJIDroneController()
        video_processor = VideoProcessor(analyzer)
        change_detector = ChangeDetector()
        geo_triangulation = GeoTriangulation()
        geo_correlator = GeoCorrelator()
        logger.info("Módulos reales inicializados correctamente")
    except Exception as e:
        logger.error(f"Error inicializando módulos reales: {e}. Usando mocks como fallback.")
        drone_controller = MockDroneController()
        video_processor = MockProcessor()
        change_detector = MockProcessor()
        geo_triangulation = MockProcessor()
        geo_correlator = MockProcessor()
else:
    # Usar objetos mock
    drone_controller = MockDroneController()
    video_processor = MockProcessor()
    change_detector = MockProcessor()
    geo_triangulation = MockProcessor()
    geo_correlator = MockProcessor()
    logger.info("Usando objetos mock para módulos no disponibles")

# Variables globales
# current_reference_image = None
# reference_images = {}
# targets = {}

class GeolocationManager:
    """Gestiona el estado de geolocalización, referencias e imágenes."""
    
    def __init__(self):
        """Inicializa el gestor de geolocalización."""
        self.current_reference_image = None
        self.reference_images = {}
        self.targets = {}
        logger.info("Gestor de geolocalización inicializado")
    
    def add_reference_image(self, drone_telemetry: Dict[str, Any]) -> str:
        """Añade una imagen de referencia."""
        ref_id = f"ref_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.reference_images[ref_id] = {
            'timestamp': datetime.now().isoformat(),
            'location': drone_telemetry.get('gps', {})
        }
        self.current_reference_image = ref_id
        logger.info(f"Imagen de referencia añadida: {ref_id}")
        return ref_id
    
    def create_target(self) -> str:
        """Crea un nuevo objetivo para triangulación."""
        target_id = f"target_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.targets[target_id] = {
            'captures': [],
            'timestamp': datetime.now().isoformat()
        }
        logger.info(f"Objetivo creado: {target_id}")
        return target_id
    
    def get_reference_images(self) -> Dict[str, Any]:
        """Obtiene todas las imágenes de referencia."""
        return self.reference_images
    
    def get_targets(self) -> Dict[str, Any]:
        """Obtiene todos los objetivos."""
        return self.targets

# Inicializar gestor de geolocalización
geo_manager = GeolocationManager()

@app.route('/')
def index():
    """Ruta principal que muestra la nueva interfaz moderna."""
    return render_template('index.html')

@app.route('/drone_control.html')
def drone_control():
    """Ruta para el panel de control completo de drones."""
    return render_template('drone_control.html')

@app.route('/web_index.html')
def web_index():
    """Ruta para el análisis rápido."""
    return render_template('web_index.html')

@app.route('/mission_instructions.html')
def mission_instructions():
    """Ruta para las instrucciones de misiones LLM."""
    return render_template('mission_instructions.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    """Procesa una imagen y retorna los resultados del análisis."""
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No se envió ninguna imagen'}), 400
            
        image_file = request.files['image']
        if image_file.filename == '':
            return jsonify({'error': 'Nombre de archivo vacío'}), 400
        
        # Obtener parámetros de configuración
        confidence_threshold = float(request.form.get('confidence_threshold', 0))
        model_version = request.form.get('model_version', 'default')
        detail_level = request.form.get('detail_level', 'normal')
            
        # Guardar imagen en directorio temporal
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, image_file.filename)
        image_file.save(temp_path)
        
        # Obtener metadatos
        metadata = get_image_metadata(temp_path)
        
        # Agregar parámetros de configuración a los metadatos
        metadata['confidence_threshold'] = confidence_threshold
        metadata['model_version'] = model_version
        metadata['detail_level'] = detail_level
        
        # Codificar imagen en base64
        with open(temp_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        # Analizar la imagen
        results = analyzer.analyze_image(encoded_image, metadata)
        
        # Si se especificó un umbral de confianza, filtrar resultados
        if confidence_threshold > 0:
            if results.get('confidence', 0) < confidence_threshold:
                results['warning'] = f"Resultados por debajo del umbral de confianza ({confidence_threshold}%)"
        
        # Guardar resultados
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"analysis_{timestamp}.json"
        save_path = save_analysis_results_with_filename(results, filename)
        
        # Devolver resultados como JSON
        return jsonify({
            'results': results,
            'saved_path': save_path,
            'status': 'completed'
        })
        
    except Exception as e:
        logger.error(f"Error en el análisis: {str(e)}")
        return jsonify({'error': str(e), 'status': 'error'}), 500

@app.route('/results/<path:filename>')
def results(filename):
    """Sirve archivos de resultados guardados."""
    results_dir = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "results")
    return send_from_directory(results_dir, filename)

# API para control de drones
@app.route('/api/drone/connect', methods=['POST'])
def connect_drone():
    """Conecta con el dron."""
    try:
        success = drone_controller.connect()
        if success:
            return jsonify({
                'success': True,
                'position': {
                    'latitude': drone_controller.current_position["latitude"],
                    'longitude': drone_controller.current_position["longitude"]
                }
            })
        else:
            return jsonify({'success': False, 'error': 'Error al conectar con el dron'})
    except Exception as e:
        logger.error(f"Error al conectar: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/drone/disconnect', methods=['POST'])
def disconnect_drone():
    """Desconecta del dron."""
    try:
        success = drone_controller.disconnect()
        return jsonify({'success': success})
    except Exception as e:
        logger.error(f"Error al desconectar: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/drone/takeoff', methods=['POST'])
def takeoff_drone():
    """Despega el dron."""
    try:
        data = request.json
        altitude = data.get('altitude', 10.0)
        success = drone_controller.take_off(altitude)
        return jsonify({'success': success})
    except Exception as e:
        logger.error(f"Error al despegar: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/drone/land', methods=['POST'])
def land_drone():
    """Aterriza el dron."""
    try:
        success = drone_controller.land()
        return jsonify({'success': success})
    except Exception as e:
        logger.error(f"Error al aterrizar: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/drone/stream/start', methods=['POST'])
def start_stream():
    """Inicia la transmisión de video."""
    try:
        stream_url = drone_controller.start_video_stream()
        success = video_processor.start_processing(stream_url)
        return jsonify({'success': success})
    except Exception as e:
        logger.error(f"Error al iniciar stream: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/drone/stream/stop', methods=['POST'])
def stop_stream():
    """Detiene la transmisión de video."""
    try:
        video_processor.stop_processing()
        success = drone_controller.stop_video_stream()
        return jsonify({'success': success})
    except Exception as e:
        logger.error(f"Error al detener stream: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/drone/telemetry')
def get_telemetry():
    """Obtiene datos de telemetría del dron."""
    try:
        telemetry = drone_controller.get_telemetry()
        return jsonify({'success': True, 'telemetry': telemetry})
    except Exception as e:
        logger.error(f"Error al obtener telemetría: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

# API para misiones
@app.route('/api/missions')
def get_missions():
    """Obtiene la lista de misiones disponibles."""
    try:
        # Simulación simple para demostración
        missions = [
            {'id': '1', 'name': 'Reconocimiento Área 1'},
            {'id': '2', 'name': 'Vigilancia Perímetro'},
            {'id': '3', 'name': 'Inspección Estructura'}
        ]
        return jsonify({'success': True, 'missions': missions})
    except Exception as e:
        logger.error(f"Error al obtener misiones: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/missions/start', methods=['POST'])
def start_mission():
    """Inicia una misión."""
    try:
        data = request.json
        mission_id = data.get('id')
        if not mission_id:
            return jsonify({'success': False, 'error': 'ID de misión no especificado'})
        
        # Aquí se implementaría la ejecución real de la misión
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error al iniciar misión: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/missions/abort', methods=['POST'])
def abort_mission():
    """Aborta la misión actual."""
    try:
        # Implementación de aborto de misión
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error al abortar misión: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

# API para misiones con LLM
@app.route('/api/missions/llm/create', methods=['POST'])
def create_llm_mission():
    """Crea una misión usando comandos en lenguaje natural con LLM."""
    try:
        data = request.json
        natural_command = data.get('command')
        area_name = data.get('area_name')
        
        if not natural_command:
            return jsonify({'success': False, 'error': 'Comando no especificado'})
        
        # Crear misión usando LLM
        mission = mission_planner.create_mission_from_command(natural_command, area_name)
        
        if mission:
            # Validar seguridad
            warnings = mission_planner.validate_mission_safety(mission)
            mission['safety_warnings'] = warnings
            
            return jsonify({
                'success': True, 
                'mission': mission,
                'safety_warnings': warnings
            })
        else:
            return jsonify({'success': False, 'error': 'Error creando misión con LLM'})
            
    except Exception as e:
        logger.error(f"Error creando misión LLM: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/missions/llm/adaptive', methods=['POST'])
def adaptive_mission_control():
    """Control adaptativo de misión usando LLM."""
    try:
        data = request.json
        mission_id = data.get('mission_id')
        current_position = data.get('current_position', [40.416775, -3.703790])
        situation_report = data.get('situation_report', '')
        
        if not mission_id:
            return jsonify({'success': False, 'error': 'ID de misión no especificado'})
        
        # Obtener decisión del LLM
        decision = mission_planner.adaptive_mission_control(
            tuple(current_position), situation_report, mission_id
        )
        
        return jsonify({'success': True, 'decision': decision})
        
    except Exception as e:
        logger.error(f"Error en control adaptativo: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/cartography/upload', methods=['POST'])
def upload_cartography():
    """Sube y procesa archivos de cartografía."""
    try:
        if 'cartography_file' not in request.files:
            return jsonify({'success': False, 'error': 'No se envió archivo de cartografía'})
        
        file = request.files['cartography_file']
        area_name = request.form.get('area_name', 'area_sin_nombre')
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Nombre de archivo vacío'})
        
        # Guardar archivo temporalmente
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, file.filename)
        file.save(temp_path)
        
        # Cargar cartografía
        success = mission_planner.load_cartography(temp_path, area_name)
        
        if success:
            # Obtener coordenadas del centro para reposicionar el dron
            center_coordinates = mission_planner.get_area_center_coordinates(area_name)
            
            response_data = {
                'success': True, 
                'message': f'Cartografía "{area_name}" cargada correctamente',
                'area_name': area_name
            }
            
            # Agregar coordenadas del centro si están disponibles
            if center_coordinates:
                response_data['center_coordinates'] = {
                    'latitude': center_coordinates[0],
                    'longitude': center_coordinates[1]
                }
                logger.info(f"Área '{area_name}' cargada con centro en: {center_coordinates[0]:.6f}, {center_coordinates[1]:.6f}")
                
                # Actualizar posición del mock drone
                drone_controller.update_position(center_coordinates[0], center_coordinates[1])
            
            return jsonify(response_data)
        else:
            return jsonify({'success': False, 'error': 'Error procesando cartografía'})
            
    except Exception as e:
        logger.error(f"Error subiendo cartografía: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/cartography/areas', methods=['GET'])
def get_loaded_areas():
    """Obtiene las áreas de cartografía cargadas."""
    try:
        areas = []
        for area_name, area_data in mission_planner.loaded_areas.items():
            areas.append({
                'name': area_name,
                'boundaries_count': len(area_data.boundaries),
                'poi_count': len(area_data.points_of_interest or [])
            })
        
        return jsonify({'success': True, 'areas': areas})
        
    except Exception as e:
        logger.error(f"Error obteniendo áreas: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/missions/llm/list', methods=['GET'])
def get_llm_missions():
    """Obtiene lista de misiones LLM creadas."""
    try:
        missions = mission_planner.get_available_missions()
        return jsonify({'success': True, 'missions': missions})
        
    except Exception as e:
        logger.error(f"Error obteniendo misiones LLM: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

# API para geolocalización
@app.route('/api/geo/reference/add', methods=['POST'])
def add_reference():
    """Añade una imagen de referencia para detección de cambios."""
    try:
        drone_telemetry = drone_controller.get_telemetry()
        ref_id = geo_manager.add_reference_image(drone_telemetry)
        return jsonify({'success': True, 'reference_id': ref_id})
    except Exception as e:
        logger.error(f"Error al añadir referencia: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/geo/changes/detect', methods=['POST'])
def detect_changes():
    """Detecta cambios entre imagen actual y referencia."""
    try:
        # Verificar si tenemos datos para procesar
        if not geo_manager.current_reference_image:
            return jsonify({
                'success': False, 
                'error': 'No hay imagen de referencia establecida'
            })
        
        # Obtener telemetría actual del dron
        drone_telemetry = drone_controller.get_telemetry()
        
        # Si tenemos el módulo real de correlación, usarlo
        if hasattr(geo_correlator, 'correlate_drone_image') and not isinstance(geo_correlator, MockProcessor):
            # Simular imagen actual (en implementación real, vendría del stream del dron)
            mock_image_data = b"mock_image_data"  # Placeholder para imagen real
            
            # Usar el correlador real para detección de cambios
            correlation_result = geo_correlator.correlate_drone_image(
                mock_image_data, 
                drone_telemetry,
                confidence_threshold=0.6
            )
            
            if 'error' in correlation_result:
                return jsonify({
                    'success': False,
                    'error': correlation_result['error']
                })
            
            # Determinar si hay cambios basándose en la correlación
            confidence = correlation_result.get('confidence', 0)
            has_changes = confidence < 0.8  # Si la confianza es baja, hay cambios
            change_percentage = (1 - confidence) * 100
            
            return jsonify({
                'success': True,
                'has_changes': has_changes,
                'change_percentage': round(change_percentage, 2),
                'correlation_confidence': confidence,
                'analysis_details': correlation_result
            })
        else:
            # Fallback a simulación si no hay módulo real
            logger.warning("Usando simulación para detección de cambios - módulo real no disponible")
            return jsonify({
                'success': True, 
                'has_changes': True,
                'change_percentage': 15.7,
                'note': 'Resultado simulado - módulo real no disponible'
            })
            
    except Exception as e:
        logger.error(f"Error en detección de cambios: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/geo/target/create', methods=['POST'])
def create_target():
    """Crea un nuevo objetivo para triangulación."""
    try:
        # Usar el módulo real de triangulación si está disponible
        if hasattr(geo_triangulation, 'create_target') and not isinstance(geo_triangulation, MockProcessor):
            target_id = geo_triangulation.create_target()
            
            # También registrar en el gestor local
            geo_manager.targets[target_id] = {
                'captures': [],
                'timestamp': datetime.now().isoformat(),
                'created_by': 'triangulation_module'
            }
            
            logger.info(f"Objetivo creado usando módulo real: {target_id}")
            return jsonify({'success': True, 'target_id': target_id})
        else:
            # Fallback al gestor local
            target_id = geo_manager.create_target()
            logger.warning(f"Objetivo creado usando fallback: {target_id}")
            return jsonify({
                'success': True, 
                'target_id': target_id,
                'note': 'Creado con módulo fallback'
            })
            
    except Exception as e:
        logger.error(f"Error al crear objetivo: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/geo/position/calculate', methods=['POST'])
def calculate_position():
    """Calcula la posición geográfica de un objetivo usando triangulación real."""
    try:
        data = request.json
        target_id = data.get('target_id')
        
        if not target_id:
            return jsonify({'success': False, 'error': 'ID de objetivo no especificado'})
        
        # Usar el módulo real de triangulación si está disponible
        if hasattr(geo_triangulation, 'calculate_position') and not isinstance(geo_triangulation, MockProcessor):
            
            # Verificar si necesitamos agregar observaciones automáticamente
            drone_telemetry = drone_controller.get_telemetry()
            gps = drone_telemetry.get('gps', {})
            
            if target_id not in geo_triangulation.observations or len(geo_triangulation.observations.get(target_id, [])) < 2:
                # Agregar observaciones simuladas para demostración
                # En una implementación real, estas vendrían de detecciones visuales reales
                
                # Observación 1 (posición actual del dron)
                geo_triangulation.add_observation(
                    target_id=target_id,
                    drone_position={
                        'latitude': gps.get('latitude', 40.416775),
                        'longitude': gps.get('longitude', -3.703790),
                        'altitude': drone_telemetry.get('altitude', 50)
                    },
                    target_bearing=45.0,  # En implementación real: detección visual
                    target_elevation=15.0,  # En implementación real: cálculo de ángulos
                    confidence=0.9
                )
                
                # Observación 2 (posición ligeramente diferente)
                geo_triangulation.add_observation(
                    target_id=target_id,
                    drone_position={
                        'latitude': gps.get('latitude', 40.416775) + 0.001,
                        'longitude': gps.get('longitude', -3.703790) + 0.001,
                        'altitude': drone_telemetry.get('altitude', 50) + 10
                    },
                    target_bearing=50.0,
                    target_elevation=12.0,
                    confidence=0.85
                )
                
                logger.info(f"Agregadas observaciones automáticas para objetivo {target_id}")
            
            # Calcular posición usando triangulación real
            result = geo_triangulation.calculate_position(target_id)
            
            if 'error' in result:
                return jsonify({'success': False, 'error': result['error']})
            
            return jsonify({
                'success': True,
                'position': result['position'],
                'precision': result['precision'],
                'observations_count': result['observations_count'],
                'timestamp': result['timestamp'],
                'method': 'real_triangulation'
            })
        else:
            # Fallback a simulación
            logger.warning("Usando simulación para cálculo de posición - módulo real no disponible")
            return jsonify({
                'success': True,
                'position': {
                    'latitude': 40.416775 + (hash(target_id) % 100) / 10000,
                    'longitude': -3.703790 + (hash(target_id[::-1]) % 100) / 10000
                },
                'precision': {
                    'confidence': 75.0,
                    'error_radius': 25.0
                },
                'method': 'simulated',
                'note': 'Resultado simulado - módulo real no disponible'
            })
            
    except Exception as e:
        logger.error(f"Error al calcular posición: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

# Nueva ruta para agregar observaciones manuales
@app.route('/api/geo/observation/add', methods=['POST'])
def add_observation():
    """Agrega una observación manual para triangulación."""
    try:
        data = request.json
        target_id = data.get('target_id')
        target_bearing = data.get('target_bearing')  # grados
        target_elevation = data.get('target_elevation', 0)  # grados
        confidence = data.get('confidence', 1.0)
        
        if not target_id or target_bearing is None:
            return jsonify({
                'success': False, 
                'error': 'target_id y target_bearing son requeridos'
            })
        
        # Usar el módulo real de triangulación si está disponible
        if hasattr(geo_triangulation, 'add_observation') and not isinstance(geo_triangulation, MockProcessor):
            # Obtener posición actual del dron
            drone_telemetry = drone_controller.get_telemetry()
            gps = drone_telemetry.get('gps', {})
            
            drone_position = {
                'latitude': gps.get('latitude', 40.416775),
                'longitude': gps.get('longitude', -3.703790),
                'altitude': drone_telemetry.get('altitude', 50)
            }
            
            # Agregar observación
            observation_id = geo_triangulation.add_observation(
                target_id=target_id,
                drone_position=drone_position,
                target_bearing=float(target_bearing),
                target_elevation=float(target_elevation),
                confidence=float(confidence)
            )
            
            # Obtener número total de observaciones para este objetivo
            obs_count = len(geo_triangulation.observations.get(target_id, []))
            
            return jsonify({
                'success': True,
                'observation_id': observation_id,
                'total_observations': obs_count,
                'can_calculate': obs_count >= 2
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Módulo de triangulación no disponible'
            })
            
    except Exception as e:
        logger.error(f"Error al agregar observación: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

# Nueva ruta para obtener estado de objetivos
@app.route('/api/geo/targets/status', methods=['GET'])
def get_targets_status():
    """Obtiene el estado de todos los objetivos de triangulación."""
    try:
        if hasattr(geo_triangulation, 'get_all_targets') and not isinstance(geo_triangulation, MockProcessor):
            targets = geo_triangulation.get_all_targets()
            
            targets_status = []
            for target_id in targets:
                observations = geo_triangulation.observations.get(target_id, [])
                targets_status.append({
                    'target_id': target_id,
                    'observations_count': len(observations),
                    'can_calculate': len(observations) >= 2,
                    'last_observation': observations[-1]['timestamp'] if observations else None
                })
            
            return jsonify({
                'success': True,
                'targets': targets_status,
                'total_targets': len(targets)
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Módulo de triangulación no disponible'
            })
            
    except Exception as e:
        logger.error(f"Error al obtener estado de objetivos: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/analysis/status', methods=['GET'])
def analysis_status():
    """Obtiene el estado actual del análisis en progreso."""
    analysis_id = request.args.get('id')
    # En una implementación real, esto consultaría el estado del análisis
    # Aquí simulamos para demostración
    return jsonify({
        'id': analysis_id,
        'status': 'processing',
        'progress': 70,
        'estimated_time_remaining': '30 segundos'
    })

# Rutas para simulación de vuelo
@app.route('/api/drone/simulate/paths', methods=['GET'])
def get_simulation_paths():
    """Obtiene rutas predefinidas para simulación de vuelo."""
    # Rutas de vuelo simuladas predefinidas
    simulated_paths = [
        {
            "id": "route_1",
            "name": "Reconocimiento urbano",
            "description": "Ruta de reconocimiento urbano básico",
            "waypoints": [
                {"lat": 40.416775, "lng": -3.703790, "alt": 50},
                {"lat": 40.415800, "lng": -3.702500, "alt": 80},
                {"lat": 40.414900, "lng": -3.704000, "alt": 100},
                {"lat": 40.416200, "lng": -3.705500, "alt": 80},
                {"lat": 40.417500, "lng": -3.704800, "alt": 50},
                {"lat": 40.416775, "lng": -3.703790, "alt": 30}
            ]
        },
        {
            "id": "route_2",
            "name": "Patrulla perimetral",
            "description": "Ruta circular para vigilancia de perímetro",
            "waypoints": [
                {"lat": 40.416775, "lng": -3.703790, "alt": 50},
                {"lat": 40.417900, "lng": -3.702000, "alt": 60},
                {"lat": 40.419100, "lng": -3.703400, "alt": 70},
                {"lat": 40.418400, "lng": -3.705900, "alt": 70},
                {"lat": 40.416500, "lng": -3.706200, "alt": 60},
                {"lat": 40.415200, "lng": -3.704900, "alt": 50},
                {"lat": 40.416775, "lng": -3.703790, "alt": 40}
            ]
        },
        {
            "id": "route_3",
            "name": "Exploración en zigzag",
            "description": "Patrón de búsqueda en zigzag para cubrir área",
            "waypoints": [
                {"lat": 40.416775, "lng": -3.703790, "alt": 60},
                {"lat": 40.417800, "lng": -3.702500, "alt": 80},
                {"lat": 40.418700, "lng": -3.704200, "alt": 100},
                {"lat": 40.417600, "lng": -3.705800, "alt": 100},
                {"lat": 40.416500, "lng": -3.707100, "alt": 80},
                {"lat": 40.415400, "lng": -3.705700, "alt": 60},
                {"lat": 40.414300, "lng": -3.704200, "alt": 50},
                {"lat": 40.415500, "lng": -3.702800, "alt": 40},
                {"lat": 40.416775, "lng": -3.703790, "alt": 30}
            ]
        }
    ]
    
    return jsonify({"success": True, "paths": simulated_paths})

@app.route('/api/drone/simulate/start', methods=['POST'])
def start_simulation():
    """Inicia una simulación de vuelo."""
    try:
        data = request.json
        path_id = data.get('path_id')
        
        if not path_id:
            return jsonify({'success': False, 'error': 'ID de ruta no especificado'})
        
        # En una implementación real, iniciaríamos un proceso de simulación
        # Aquí simplemente devolvemos éxito para que el frontend pueda animar
        return jsonify({
            'success': True,
            'message': f'Simulación iniciada para ruta {path_id}',
            'simulation_id': f'sim_{int(time.time())}'
        })
    except Exception as e:
        logger.error(f"Error al iniciar simulación: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

def main():
    """Función principal que inicia el servidor web."""
    from waitress import serve
    
    host = '0.0.0.0'  # Escuchar en todas las interfaces
    port = 5000
    
    logger.info(f"Iniciando servidor web en {host}:{port}")
    print(f"🚀 Servidor iniciado en http://{host}:{port} (puerto interno del contenedor)")
    print(f"🌐 Accede desde tu navegador en: http://localhost:4001")
    print(f"🎮 Panel de Control: http://localhost:4001/drone_control.html")
    print(f"⚡ Análisis Rápido: http://localhost:4001/web_index.html")
    print(f"📱 Mapeo de puertos: localhost:4001 → contenedor:5000")
    
    # Usar waitress para producción
    serve(app, host=host, port=port)

if __name__ == "__main__":
    main() 