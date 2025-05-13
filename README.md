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

## Instalación con Docker

1. Clonar este repositorio:
```bash
git clone https://github.com/your-username/drone-geo-analysis.git
cd drone-geo-analysis
```

2. Configurar la clave API de OpenAI:

Crea un archivo `.env` en la raíz del proyecto con el siguiente contenido:
```
OPENAI_API_KEY=tu_clave_api_de_openai
```

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