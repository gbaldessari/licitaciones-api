# licitaciones-api

Servicio Django + DRF para obtener y filtrar licitaciones desde la API pública de Mercado Público.

Pasos de instalación rápida:

1) Crear entorno e instalar dependencias
   - py -m venv .venv
   - .venv\Scripts\activate
   - pip install -r requirements.txt

2) Crear proyecto y app (si aún no existen en este repo)
   - django-admin startproject licitaciones_api .
   - py manage.py startapp licitaciones

3) Variables de entorno
   - Copiar `.env.example` a `.env` y definir `MERCADO_PUBLICO_API_KEY` (ticket de Mercado Público).

4) Configurar Django
   - Editar `licitaciones_api/settings.py` para:
     - Cargar `.env`
     - Agregar `rest_framework` y `licitaciones` en `INSTALLED_APPS`
   - Editar `licitaciones_api/urls.py` para añadir la ruta `/api/licitaciones`.

5) Archivos clave a crear/editar (ver bloques de código por archivo en este README):
   - requirements.txt
   - .env.example
   - licitaciones_api/settings.py (agregar configuraciones)
   - licitaciones_api/urls.py (agregar endpoint)
   - licitaciones/services/mercado_publico.py (servicio HTTP)
   - licitaciones/views.py (vista DRF)

6) Ejecutar
   - py manage.py runserver
   - Probar:
     - <http://127.0.0.1:8000/api/licitaciones?estado=abierta&fecha_desde=2025-01-01&fecha_hasta=2025-01-31>
     - <http://127.0.0.1:8000/api/licitaciones?codigo=12345-1-LQ25>

Endpoint

- GET /api/licitaciones/  ← nota el slash final
  - Query params:
    - estado: una de [publicada, cerrada, adjudicada, desierta, revocada, suspendida]
      - alias aceptado: abierta -> publicada
    - fecha_desde (YYYY-MM-DD): fecha inicial del rango
    - fecha_hasta (YYYY-MM-DD): fecha final del rango
      - para un solo día, usa solo fecha_desde (o solo fecha_hasta)
      - rango máximo permitido: 31 días
    - codigo: código exacto de licitación (si se envía, se prioriza y no se combinan otros filtros)
  - Respuesta: JSON con el payload de Mercado Público. Para rangos, se consolida como {"Cantidad","Listado"}.
  - Códigos de estado:
    - 200: OK
    - 400: validación (fechas inválidas, rango > 31 días, etc.)
    - 500: configuración local (API key faltante)
    - 502: error HTTP del upstream (detalle incluido)
    - 503: servicio ocupado (peticiones simultáneas). Incluye Retry-After.
    - 504: timeout del upstream

Ejemplos (curl)
- Rango de 7 días (usa alias 'abierta' => 'publicada'):
  curl -s "http://127.0.0.1:8000/api/licitaciones/?estado=abierta&fecha_desde=2025-01-01&fecha_hasta=2025-01-07"

- Un solo día:
  curl -s "http://127.0.0.1:8000/api/licitaciones/?estado=publicada&fecha_desde=2025-01-15"

- Solo por estado (sin fechas):
  curl -s "http://127.0.0.1:8000/api/licitaciones/?estado=publicada"

- Búsqueda por código exacto:
  curl -s "http://127.0.0.1:8000/api/licitaciones/?codigo=12345-1-LQ25"

Ejemplos (navegador)
- http://127.0.0.1:8000/api/licitaciones/?estado=abierta&fecha_desde=2025-01-01&fecha_hasta=2025-01-07
- http://127.0.0.1:8000/api/licitaciones/?estado=publicada&fecha_desde=2025-01-15
- http://127.0.0.1:8000/api/licitaciones/?estado=publicada
- http://127.0.0.1:8000/api/licitaciones/?codigo=12345-1-LQ25

Notas
- Usa siempre el slash final (/api/licitaciones/) para evitar redirecciones 301.
- Define MERCADO_PUBLICO_API_KEY en .env antes de ejecutar.
