# Licitaciones API (NestJS + Mercado Público)

API mínima en NestJS para consultar licitaciones desde la API pública de Mercado Público.

## Requisitos

- Node.js 18+ y npm
- Dependencias:
  - npm i @nestjs/axios
  - npm i @nestjs/config

## Variables de entorno

El proyecto lee automáticamente los archivos .ENV o .env gracias a @nestjs/config.

```sh
MP_API_TICKET=TU_TICKET_AQUI
MP_API_BASE_URL=https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json
MP_API_RETRY_ATTEMPTS=3
MP_API_RETRY_DELAY_MS=1500
```

## Servicio: MercadoPublicoService

Servicio que consume la API de Mercado Público.

Métodos:

- getLicitacionesPorEstado(estado = 'publicada', extraParams?: Record<string, string | number>)
  - Retorna licitaciones filtradas por estado.
  - Puedes agregar parámetros extra soportados por la API (p.ej., fecha, pagina, codigoEntidad, etc.).
- getLicitacionPorCodigo(codigo: string)
  - Retorna una licitación específica por su código (ej: 1234-5-LR24).

Errores:

- 500 si falta MP_API_TICKET.
- 502 si hay un error al consultar Mercado Público (propaga status y mensaje del upstream cuando es posible).

Uso interno (inyección en controladores/servicios):

```ts
constructor(private readonly mp: MercadoPublicoService) {}

await this.mp.getLicitacionesPorEstado('publicada');
// o
await this.mp.getLicitacionPorCodigo('1234-5-LR24');
```

## Endpoints REST

Base URL local: <http://localhost:3000>

- GET /licitaciones
  - Query:
    - estado?: string (por defecto: publicada)
    - codigo?: string (si envías ambos, se prioriza codigo)

Ejemplos:

- Por estado

```bash
curl "http://localhost:3000/licitaciones?estado=publicada"
```

- Por código

```bash
curl "http://localhost:3000/licitaciones?codigo=1234-5-LR24"
```

Respuesta (ejemplo resumido de Mercado Público):

```json
{
  "Cantidad": 1,
  "FechaCreacion": "2024-10-10T12:34:56Z",
  "Listado": [
    {
      "CodigoExterno": "1234-5-LR24",
      "Nombre": "Adquisición de servicios ...",
      "Estado": "Publicada"
      // ...
    }
  ]
}
```

## Reintentos y límites de la API

La API de Mercado Público puede responder con:

- 429/5xx (saturación/indisponibilidad)
- Cuerpo con error: `{"Codigo":10500,"Mensaje":"Lo sentimos. Hemos detectado que existen peticiones simultáneas."}`

El servicio implementa reintentos automáticos con backoff simple:

- MP_API_RETRY_ATTEMPTS: número de intentos (por defecto 3).
- MP_API_RETRY_DELAY_MS: retraso base entre intentos en ms (por defecto 1500). El retraso crece linealmente por intento.

Además, se cargan automáticamente variables desde .env.

## Ejecución local

```bash
npm install
npm run start:dev
# Abrir: http://localhost:3000/licitaciones?estado=publicada
```
