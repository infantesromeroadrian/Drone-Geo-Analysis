# 🌍 Guía de Coordenadas Dinámicas - Drone Geo Analysis

## 🎯 **NUEVA FUNCIONALIDAD IMPLEMENTADA**

Ahora el sistema **adapta automáticamente** la posición del dron y las misiones AI a las coordenadas del GeoJSON que cargues.

---

## 🚀 **CÓMO FUNCIONA**

### **1. 📁 Cargar GeoJSON Dinámico**
1. Ve al panel de control: `http://localhost:4001/drone_control.html`
2. En la sección "Cartografía", haz clic en **"Seleccionar Archivo"**
3. Carga cualquier archivo GeoJSON con coordenadas reales
4. **¡AUTOMÁTICAMENTE:**
   - 🚁 El dron se reposiciona a las coordenadas del GeoJSON
   - 🗺️ El mapa se centra en la nueva ubicación
   - 📡 La telemetría se actualiza con las nuevas coordenadas

### **2. 🤖 Crear Misiones AI Contextuales**
1. Con el GeoJSON cargado, ve a "Misiones LLM"
2. Selecciona el área cargada en el desplegable
3. Escribe un comando como: *"Patrulla el perímetro y toma fotos de los puntos de interés"*
4. **¡La IA generará waypoints específicos para esa ubicación!**

---

## 📋 **ARCHIVOS DE PRUEBA INCLUIDOS**

### **🇺🇸 Nueva York - Central Park**
```bash
# Cargar: test_newyork.geojson
# Centro: 40.7735°N, 73.9615°W
# Características: Helipad, Torre de comunicaciones, Zona de emergencia
```

### **🇯🇵 Tokio - Bahía de Tokio**
```bash
# Cargar: test_tokyo.geojson  
# Centro: 35.6612°N, 139.7664°E
# Características: Zona marítima, Plataforma de aterrizaje, Base de emergencia
```

### **🇪🇸 Madrid - Base Militar (Original)**
```bash
# Cargar: base_militar_ejemplo.geojson
# Centro: 40.4168°N, 3.7038°W
# Características: Base militar, Hangar, Pista de aterrizaje
```

---

## 🔧 **PASOS PARA PROBAR**

### **Test 1: Reposicionamiento Automático**
```bash
1. Iniciar: docker-compose up --build
2. Abrir: http://localhost:4001/drone_control.html
3. Observar: Dron en Madrid (40.416775, -3.703790)
4. Cargar: test_newyork.geojson con nombre "Central Park Ops"
5. ✅ Resultado: Dron se mueve a Nueva York (40.7735, -73.9615)
```

### **Test 2: Misiones AI Contextuales**
```bash
1. Con Nueva York cargado
2. Crear misión LLM: "Reconocimiento de seguridad del parque"
3. Seleccionar área: "Central Park Ops"
4. ✅ Resultado: Waypoints generados alrededor de Central Park, NO en Madrid
```

### **Test 3: Cambio Dinámico de Ubicación**
```bash
1. Cargar: test_tokyo.geojson con nombre "Tokyo Bay Ops"
2. ✅ Resultado: Dron se mueve automáticamente a Tokio
3. Crear misión: "Patrulla marítima de la bahía"
4. ✅ Resultado: Waypoints generados en la Bahía de Tokio
```

---

## 🎮 **COMANDOS DE MISIÓN SUGERIDOS**

### **Para Central Park (Nueva York):**
```
- "Reconocimiento de seguridad del parque desde el aire"
- "Patrulla perimetral con fotografía de puntos clave"
- "Inspección de áreas de aterrizaje de emergencia"
- "Vigilancia de eventos especiales en el parque"
```

### **Para Tokyo Bay (Tokio):**
```
- "Patrulla marítima de seguridad portuaria"
- "Inspección de infraestructura naval"
- "Reconocimiento costero con detección de embarcaciones"
- "Vigilancia de zona de operaciones especiales"
```

---

## 📊 **ANTES vs DESPUÉS**

### **❌ ANTES (Problema):**
```
1. Cargas GeoJSON de Nueva York
2. Dron permanece en Madrid
3. AI genera misiones en Madrid
4. Desconexión total entre cartografía y operación
```

### **✅ AHORA (Solucionado):**
```
1. Cargas GeoJSON de Nueva York
2. Dron se reposiciona automáticamente a Nueva York
3. AI genera misiones específicas para Nueva York
4. Coherencia total: cartografía → posición → misiones
```

---

## 🔍 **DETALLES TÉCNICOS IMPLEMENTADOS**

### **Backend (mission_planner.py):**
- ✅ Cálculo automático de coordenadas del centro
- ✅ Prompt LLM mejorado con coordenadas específicas
- ✅ Validación de área geográfica en misiones

### **Backend (app.py):**
- ✅ MockDroneController con posición dinámica
- ✅ API actualizada para retornar coordenadas del centro
- ✅ Sincronización automática entre cartografía y telemetría

### **Frontend (drone_control.html):**
- ✅ Reposicionamiento automático del marcador de dron
- ✅ Centrado del mapa en nuevas coordenadas
- ✅ Notificaciones de cambio de ubicación

---

## 🌐 **INTEGRACIÓN CON MAPBOX (OPCIONAL)**

### **Para usar tu API de Mapbox:**
```javascript
// Reemplazar en drone_control.html línea 1346:
mapboxgl.accessToken = 'pk.eyJ1IjoiaW5mYW50ZXNyb21lcm9hZHJpYW4iLCJhIjoiY21hY296bTVtMDY4bzJsc2R5bWE1Zmd0bSJ9.zwVv0C887m4zLkiLUxFoHg';

const map = new mapboxgl.Map({
    container: 'map',
    style: 'mapbox://styles/mapbox/satellite-v9', // Ideal para análisis militar
    center: [lng, lat], // Coordenadas dinámicas
    zoom: 13
});
```

**Beneficios de Mapbox:**
- 🛰️ Imágenes satelitales de alta resolución
- 🎯 Mejor precisión para análisis militar
- 🔧 Herramientas avanzadas de análisis geoespacial

---

## 🎉 **CONCLUSIÓN**

La herramienta ahora es **verdaderamente global**:
- 🌍 Funciona con cualquier ubicación del mundo
- 🤖 IA contextual según la geografía cargada  
- 🚁 Dron que se adapta automáticamente
- 📊 Coherencia total entre todos los componentes

**¡Prueba cargando coordenadas de tu ciudad y crea misiones específicas para esa ubicación!** 🚀 