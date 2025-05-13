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

# Agregar la ruta del proyecto al PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar módulos internos
from src.models.geo_analyzer import GeoAnalyzer
from src.utils.config import setup_logging
from src.utils.helpers import get_image_metadata, save_analysis_results

# Importaciones que causan problemas - COMENTADAS para pruebas
# from src.drones.dji_controller import DJIDroneController
# from src.processors.video_processor import VideoProcessor
# from src.processors.change_detector import ChangeDetector
# from src.geo.geo_triangulation import GeoTriangulation
# from src.geo.geo_correlator import GeoCorrelator

# Configurar aplicación Flask
app = Flask(__name__, 
           static_folder='templates/static',
           template_folder='templates')

# Cargar variables de entorno
load_dotenv()

# Configurar logging
setup_logging()
logger = logging.getLogger(__name__)

# Verificar API key
if "OPENAI_API_KEY" not in os.environ:
    logger.error("No se encontró OPENAI_API_KEY en las variables de entorno")
    print("Error: Se requiere una API key de OpenAI. Agrégala al archivo .env")
    sys.exit(1)

# Inicializar componentes
analyzer = GeoAnalyzer()

# Objetos mock para pruebas
class MockDroneController:
    def connect(self): return True
    def disconnect(self): return True
    def take_off(self, altitude): return True
    def land(self): return True
    def start_video_stream(self): return "mock://stream"
    def stop_video_stream(self): return True
    def get_telemetry(self): 
        return {
            "battery": 75,
            "gps": {
                "latitude": 40.416775,
                "longitude": -3.703790,
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
drone_controller = MockDroneController()
video_processor = MockProcessor()
change_detector = MockProcessor()
geo_triangulation = MockProcessor()
geo_correlator = MockProcessor()

# Variables globales
current_reference_image = None
reference_images = {}
targets = {}

@app.route('/')
def index():
    """Ruta principal que muestra la interfaz web."""
    return render_template('drone_control.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    """Procesa una imagen y retorna los resultados del análisis."""
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No se envió ninguna imagen'}), 400
            
        image_file = request.files['image']
        if image_file.filename == '':
            return jsonify({'error': 'Nombre de archivo vacío'}), 400
            
        # Guardar imagen en directorio temporal
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, image_file.filename)
        image_file.save(temp_path)
        
        # Obtener metadatos
        metadata = get_image_metadata(temp_path)
        
        # Codificar imagen en base64
        with open(temp_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        # Analizar la imagen
        results = analyzer.analyze_image(encoded_image, metadata)
        
        # Guardar resultados
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"analysis_{timestamp}.json"
        save_path = save_analysis_results(results, filename)
        
        # Devolver resultados como JSON
        return jsonify({
            'results': results,
            'saved_path': save_path
        })
        
    except Exception as e:
        logger.error(f"Error en el análisis: {str(e)}")
        return jsonify({'error': str(e)}), 500

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
                    'latitude': 40.416775,
                    'longitude': -3.703790
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

# API para geolocalización
@app.route('/api/geo/reference/add', methods=['POST'])
def add_reference():
    """Añade una imagen de referencia para detección de cambios."""
    try:
        global current_reference_image, reference_images
        
        # En un caso real, se capturaría una imagen del dron
        # Simulamos para demo
        ref_id = f"ref_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        reference_images[ref_id] = {
            'timestamp': datetime.now().isoformat(),
            'location': drone_controller.get_telemetry()['gps']
        }
        current_reference_image = ref_id
        
        return jsonify({'success': True, 'reference_id': ref_id})
    except Exception as e:
        logger.error(f"Error al añadir referencia: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/geo/changes/detect', methods=['POST'])
def detect_changes():
    """Detecta cambios entre imagen actual y referencia."""
    try:
        # Simulación simple para demostración
        has_changes = True
        change_percentage = 15.7  # Porcentaje de cambio detectado
        
        return jsonify({
            'success': True, 
            'has_changes': has_changes,
            'change_percentage': change_percentage
        })
    except Exception as e:
        logger.error(f"Error en detección de cambios: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/geo/target/create', methods=['POST'])
def create_target():
    """Crea un nuevo objetivo para triangulación."""
    try:
        global targets
        
        # En un caso real, se procesaría la imagen del dron
        # Simulamos para demo
        target_id = f"target_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        targets[target_id] = {
            'captures': [],
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify({'success': True, 'target_id': target_id})
    except Exception as e:
        logger.error(f"Error al crear objetivo: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/geo/position/calculate', methods=['POST'])
def calculate_position():
    """Calcula la posición geográfica de un objetivo."""
    try:
        data = request.json
        target_id = data.get('target_id')
        
        if not target_id:
            return jsonify({'success': False, 'error': 'ID de objetivo no especificado'})
        
        # Simulamos resultados para demo
        return jsonify({
            'success': True,
            'position': {
                'latitude': 40.416775 + (hash(target_id) % 100) / 10000,
                'longitude': -3.703790 + (hash(target_id[::-1]) % 100) / 10000
            },
            'precision': {
                'confidence': 87.5,
                'error_radius': 15.3
            }
        })
    except Exception as e:
        logger.error(f"Error al calcular posición: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

def main():
    """Función principal que inicia el servidor web."""
    from waitress import serve
    
    host = '0.0.0.0'  # Escuchar en todas las interfaces
    port = 5000
    
    logger.info(f"Iniciando servidor web en {host}:{port}")
    print(f"Servidor iniciado en http://{host}:{port}")
    print(f"Accede a través de: http://localhost:{port}")
    
    # Usar waitress para producción
    serve(app, host=host, port=port)

if __name__ == "__main__":
    main() 