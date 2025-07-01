# Herramienta de Análisis Geográfico OSINT

Esta herramienta de OSINT militar analiza imágenes para determinar ubicaciones geográficas basándose en características visuales como arquitectura, señalización, vegetación, personas, vehículos y estructura urbana.

## Características

- Interfaz gráfica intuitiva para cargar y analizar imágenes
- Análisis de ubicación geográfica con GPT-4 Vision
- Detección de país, ciudad, distrito, barrio y calle
- Identificación de elementos visuales que respaldan las conclusiones
- Propuesta de ubicaciones alternativas posibles
- Exportación de resultados en formato JSON

## Requisitos

- Docker y Docker Compose
- Clave API de OpenAI con acceso a GPT-4 Vision
- Para Windows: Servidor X (VcXsrv o Xming)

## 🚀 Configuración

### Opción 1: Docker Model Runner (Recomendado) 🐳

**Prerrequisitos:**
- Docker Desktop 4.40+ con Model Runner habilitado
- Su modelo Llama 3.2 ya descargado con `docker model pull ai/llama3.2:latest`

1. **Verificar Docker Model Runner:**
```bash
docker model status
# Debe mostrar: "Docker Model Runner is running"

docker model ls
# Debe mostrar su modelo ai/llama3.2:latest
```

2. **Iniciar el modelo:**
```bash
docker model run ai/llama3.2:latest
```

3. **Configurar variables de entorno:**
```bash
cp .env.example .env
# Editar .env y configurar:
LLM_PROVIDER=docker
DOCKER_MODEL_NAME=ai/llama3.2:latest
```

### Opción 2: OpenAI API (Alternativa)

1. **Configurar variables de entorno:**
```bash
cp .env.example .env
# Editar .env y configurar:
LLM_PROVIDER=openai
OPENAI_API_KEY=tu_clave_api_aqui
```

### Instalación de dependencias

2. **Instalar dependencias de Python:**
```bash
pip install -r requirements.txt
```

3. **Ejecutar la aplicación:**
```bash
python src/main.py
```

4. **Acceder a la interfaz:**
   - Panel principal: http://localhost:5000
   - Control de drones: http://localhost:5000/drone_control

## 🤖 Uso de Misiones Inteligentes

### Comando de ejemplo:
```
"Patrulla el perímetro norte de la base a 50 metros de altura, busca vehículos sospechosos"
```

### Resultado:
El LLM (Llama 3.2 local o GPT-4) generará automáticamente:
- ✅ Waypoints GPS específicos
- ✅ Altitudes apropiadas 
- ✅ Acciones para cada punto
- ✅ Consideraciones de seguridad
- ✅ Criterios de éxito

## 🔧 Ventajas de Docker Models

- **🔒 Privacidad total:** Los datos nunca salen de tu máquina
- **💰 Sin costos por token:** Una vez descargado, uso ilimitado
- **⚡ Baja latencia:** Sin llamadas a APIs externas
- **🛠️ Personalizable:** Puedes entrenar modelos específicos
- **📡 Funciona offline:** No requiere conexión a internet

## Configuración para Windows

Para ejecutar la aplicación GUI en Docker con Windows:

1. Instala un servidor X:
   - Descarga e instala [VcXsrv](https://sourceforge.net/projects/vcxsrv/) o [Xming](https://sourceforge.net/projects/xming/)
   
2. Configura XLaunch (parte de VcXsrv):
   - Inicia XLaunch desde el menú de inicio
   - Selecciona "Multiple windows" y "Display number: 0"
   - En la página de "Clients", selecciona "Start no client"
   - En "Extra settings", **MARCA "Disable access control"** (muy importante)
   - Finaliza y guarda la configuración

3. La variable DISPLAY ya está configurada en los archivos docker-compose como `host.docker.internal:0.0`

## Ejecución con Docker Compose

1. Para desarrollo con GUI:
```bash
docker-compose up --build
```

2. Para web (accesible vía localhost:5000):
```bash
docker-compose -f docker-compose.web.yml up --build
```

3. Para producción:
```bash
docker-compose -f docker-compose.prod.yml up --build -d
```

4. Para detener la aplicación:
```bash
# En desarrollo (con logs visibles):
# Presiona Ctrl+C

# En producción (ejecutándose en segundo plano):
docker-compose -f docker-compose.prod.yml down
```

## Modo de Acceso Web

La herramienta también ofrece una interfaz web accesible desde el navegador:

1. Ejecuta el contenedor web:
```bash
docker-compose -f docker-compose.web.yml up --build
```

2. Abre un navegador y accede a: http://localhost:5000

3. La interfaz web permite:
   - Cargar imágenes para análisis
   - Visualizar los resultados en formato JSON
   - Descargar los análisis guardados

Este modo es ideal para acceder a la herramienta sin necesidad de configurar un servidor X.

## Solución de problemas

Si encuentras errores de visualización, verifica:

1. Que el servidor X está ejecutándose (VcXsrv/Xming)
2. Que has desactivado el control de acceso en el servidor X
3. Que el firewall de Windows permite conexiones a XServer
4. Que Docker tiene permisos para acceder a la red

## Uso de la Aplicación

Una vez ejecutado el contenedor:

1. La interfaz gráfica se abrirá automáticamente
2. Selecciona "Cargar imagen" y navega a cualquier imagen en tu sistema
3. Haz clic en "Analizar imagen" para comenzar el análisis con GPT-4 Vision
4. Los resultados se mostrarán en el panel derecho
5. Puedes guardar el análisis usando "Guardar resultados"

Los resultados se guardarán en la carpeta `results/` y los logs en `logs/`.

## Estructura del Proyecto

```
drone-geo-analysis/
├── src/                      # Código fuente
│   ├── controllers/          # Controladores 
│   │   └── image_controller.py
│   ├── models/               # Modelos
│   │   └── geo_analyzer.py   
│   ├── utils/                # Utilidades
│   │   ├── config.py
│   │   └── helpers.py
│   └── main.py               # Punto de entrada
├── logs/                     # Registros
├── results/                  # Resultados de análisis
├── .env                      # Variables de entorno (no incluido en repo)
├── .dockerignore             # Archivos a ignorar en la imagen Docker
├── Dockerfile                # Definición del contenedor
├── docker-compose.yml        # Configuración para desarrollo
├── docker-compose.prod.yml   # Configuración para producción
├── requirements.txt          # Dependencias de Python
└── README.md                 # Este archivo
```

## Limitaciones

- La precisión depende de la calidad de la imagen y elementos distintivos visibles
- Requiere conexión a Internet para comunicarse con la API de OpenAI
- El análisis consume tokens de la API de OpenAI

## Uso responsable

Esta herramienta está diseñada para fines de inteligencia y uso militar legítimo. Utilice esta tecnología de manera ética y legal, respetando la privacidad y las regulaciones aplicables. 