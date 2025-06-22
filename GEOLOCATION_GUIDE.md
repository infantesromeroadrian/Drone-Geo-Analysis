# 📍 Guía de Geolocalización - Drone Geo Analysis

## 🎯 Resumen de Correcciones Implementadas

### ❌ **Problemas Identificados y Solucionados**

1. **Rutas API usaban simulaciones hardcodeadas** - ✅ **SOLUCIONADO**
2. **Módulos reales no se integraban con las APIs** - ✅ **SOLUCIONADO**  
3. **Falta de funcionalidades avanzadas de triangulación** - ✅ **SOLUCIONADO**

### ✅ **Nuevas Funcionalidades Implementadas**

#### 🔄 **APIs Mejoradas**
- `/api/geo/changes/detect` - Ahora usa el módulo real `GeoCorrelator`
- `/api/geo/position/calculate` - Ahora usa el módulo real `GeoTriangulation`
- `/api/geo/observation/add` - Nueva API para agregar observaciones manuales
- `/api/geo/targets/status` - Nueva API para monitorear estado de objetivos

#### 🧮 **Módulos Funcionales**
- **GeoTriangulation**: Triangulación real basada en múltiples observaciones
- **GeoCorrelator**: Correlación de imágenes con referencias satelitales

---

## 🚀 Uso de las APIs de Geolocalización

### 1. **Crear un Objetivo de Triangulación**

```bash
curl -X POST http://localhost:4001/api/geo/target/create
```

**Respuesta:**
```json
{
  "success": true,
  "target_id": "target_a1b2c3d4"
}
```

### 2. **Agregar Observaciones**

```bash
curl -X POST http://localhost:4001/api/geo/observation/add \
  -H "Content-Type: application/json" \
  -d '{
    "target_id": "target_a1b2c3d4",
    "target_bearing": 45.0,
    "target_elevation": 15.0,
    "confidence": 0.9
  }'
```

**Respuesta:**
```json
{
  "success": true,
  "observation_id": "target_a1b2c3d4_0",
  "total_observations": 1,
  "can_calculate": false
}
```

### 3. **Calcular Posición (Requiere ≥2 observaciones)**

```bash
curl -X POST http://localhost:4001/api/geo/position/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "target_id": "target_a1b2c3d4"
  }'
```

**Respuesta:**
```json
{
  "success": true,
  "position": {
    "latitude": 40.418635,
    "longitude": -3.701312,
    "altitude": 0
  },
  "precision": {
    "meters": 25.7,
    "confidence": 87.3,
    "max_deviation_meters": 45.2
  },
  "observations_count": 2,
  "method": "real_triangulation"
}
```

### 4. **Detectar Cambios en Imagen**

```bash
curl -X POST http://localhost:4001/api/geo/changes/detect
```

**Respuesta:**
```json
{
  "success": true,
  "has_changes": true,
  "change_percentage": 23.5,
  "correlation_confidence": 0.765,
  "analysis_details": {
    "status": "high_confidence",
    "coverage_radius_meters": 75.0
  }
}
```

### 5. **Consultar Estado de Objetivos**

```bash
curl -X GET http://localhost:4001/api/geo/targets/status
```

**Respuesta:**
```json
{
  "success": true,
  "targets": [
    {
      "target_id": "target_a1b2c3d4",
      "observations_count": 2,
      "can_calculate": true,
      "last_observation": 1671234567.89
    }
  ],
  "total_targets": 1
}
```

---

## 🧪 Uso Programático

### **Ejemplo con Python**

```python
#!/usr/bin/env python3
from src.geo import GeoTriangulation, GeoCorrelator

# 1. Crear instancias
triangulation = GeoTriangulation()
correlator = GeoCorrelator()

# 2. Crear objetivo
target_id = triangulation.create_target()
print(f"Objetivo creado: {target_id}")

# 3. Agregar observaciones
obs1 = triangulation.add_observation(
    target_id=target_id,
    drone_position={'latitude': 40.416775, 'longitude': -3.703790, 'altitude': 50},
    target_bearing=45.0,
    target_elevation=15.0,
    confidence=0.9
)

obs2 = triangulation.add_observation(
    target_id=target_id,
    drone_position={'latitude': 40.417775, 'longitude': -3.702790, 'altitude': 55},
    target_bearing=50.0,
    target_elevation=12.0,
    confidence=0.85
)

# 4. Calcular posición
result = triangulation.calculate_position(target_id)
if 'error' not in result:
    pos = result['position']
    print(f"Posición: {pos['latitude']:.6f}, {pos['longitude']:.6f}")
    print(f"Confianza: {result['precision']['confidence']:.1f}%")
else:
    print(f"Error: {result['error']}")

# 5. Correlación de imagen
telemetry = {
    'gps': {'latitude': 40.416775, 'longitude': -3.703790},
    'altitude': 50,
    'orientation': {'yaw': 0, 'pitch': 0, 'roll': 0}
}

correlation = correlator.correlate_drone_image(
    image_data=b"imagen_del_dron",
    drone_telemetry=telemetry
)
print(f"Correlación: {correlation.get('confidence', 0):.2f}")
```

---

## 🏗️ Arquitectura del Sistema

### **Flujo de Datos de Geolocalización**

```
┌─────────────────┐    ┌─────────────────┐    ┌──────────────────┐
│   Dron Stream   │───▶│  Detector de    │───▶│  GeoTriangulation│
│   (Imágenes)    │    │  Objetivos      │    │    (Cálculos)    │
└─────────────────┘    └─────────────────┘    └──────────────────┘
         │                       │                       │
         │                       ▼                       ▼
         │              ┌─────────────────┐    ┌──────────────────┐
         └─────────────▶│  GeoCorrelator  │    │   Resultados     │
                        │  (Correlación)  │    │  Geolocalización │
                        └─────────────────┘    └──────────────────┘
```

### **Componentes Principales**

1. **GeoTriangulation**
   - Gestiona observaciones múltiples
   - Calcula posiciones usando triangulación
   - Proporciona estimaciones de precisión

2. **GeoCorrelator**
   - Correlaciona imágenes del dron con satelitales
   - Detecta cambios entre referencias
   - Convierte coordenadas píxel a reales

3. **GeolocationManager**
   - Gestiona estado de referencias e imágenes
   - Coordina entre componentes
   - Mantiene historial de operaciones

---

## 🎛️ Configuración Avanzada

### **Variables de Entorno**

```bash
# Opcional: API key para imágenes satelitales
SATELLITE_API_KEY=tu_api_key_aqui

# Opcional: URL personalizada para API satelital
SATELLITE_API_URL=https://custom-satellite-api.com/v1
```

### **Parámetros de Configuración**

```python
# Configuración de triangulación
triangulation = GeoTriangulation()

# Configuración de correlación
correlator = GeoCorrelator(
    api_key="tu_api_key",
    satellite_api_url="https://custom-api.com"
)
```

---

## 🔧 Troubleshooting

### **Problemas Comunes**

#### ❌ "No hay imagen de referencia establecida"
**Solución:** Usar `/api/geo/reference/add` antes de detectar cambios
```bash
curl -X POST http://localhost:4001/api/geo/reference/add
```

#### ❌ "Se requieren al menos 2 observaciones"
**Solución:** Agregar más observaciones antes de calcular posición
```bash
curl -X POST http://localhost:4001/api/geo/observation/add \
  -H "Content-Type: application/json" \
  -d '{"target_id": "tu_target_id", "target_bearing": 30.0}'
```

#### ❌ "Módulo de triangulación no disponible"
**Solución:** Verificar que los módulos reales se hayan importado correctamente
```bash
python -c "from src.geo import GeoTriangulation; print('OK')"
```

### **Verificación del Sistema**

```bash
# Ejecutar tests completos
python test_geolocation.py

# Verificar APIs individualmente
curl http://localhost:4001/api/geo/targets/status
```

---

## 📊 Ejemplo de Flujo Completo

### **Escenario: Localizar Objetivo Detectado**

```bash
# 1. Crear objetivo
TARGET_ID=$(curl -s -X POST http://localhost:4001/api/geo/target/create | jq -r .target_id)

# 2. Agregar primera observación (desde posición A)
curl -X POST http://localhost:4001/api/geo/observation/add \
  -H "Content-Type: application/json" \
  -d "{\"target_id\": \"$TARGET_ID\", \"target_bearing\": 45.0, \"confidence\": 0.9}"

# 3. Mover dron y agregar segunda observación (desde posición B)
curl -X POST http://localhost:4001/api/geo/observation/add \
  -H "Content-Type: application/json" \
  -d "{\"target_id\": \"$TARGET_ID\", \"target_bearing\": 120.0, \"confidence\": 0.85}"

# 4. Calcular posición final
curl -X POST http://localhost:4001/api/geo/position/calculate \
  -H "Content-Type: application/json" \
  -d "{\"target_id\": \"$TARGET_ID\"}"
```

---

## ✨ Próximas Mejoras

- [ ] Integración con stream de video en tiempo real
- [ ] Mejoras en algoritmos de triangulación (Kalman filters)
- [ ] Soporte para múltiples tipos de sensores
- [ ] Interfaz web visual para geolocalización
- [ ] Exportación a formatos GIS (KML, GeoJSON)

---

**🎉 ¡La geolocalización ahora funciona completamente!**

Las misiones siguen funcionando perfectamente, y ahora la geolocalización también está operativa con módulos reales integrados correctamente en las APIs. 