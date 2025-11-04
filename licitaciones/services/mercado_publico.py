import datetime as dt
from typing import Dict, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from django.conf import settings

BASE_URL = "https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json"


class MercadoPublicoError(Exception):
    pass

class MercadoPublicoConfigError(MercadoPublicoError):
    """Error por configuración local (p.ej. API key faltante)."""
    pass

class MercadoPublicoTimeout(MercadoPublicoError):
    """Timeout al consultar el servicio de Mercado Público."""
    pass

class MercadoPublicoBusy(MercadoPublicoError):
    """El servicio de Mercado Público reporta saturación o peticiones simultáneas."""
    pass


def _validate_date(value: str, field: str) -> None:
    try:
        dt.datetime.strptime(value, "%Y-%m-%d")
    except Exception:
        raise ValueError(f"{field} debe tener formato YYYY-MM-DD")


def _build_session() -> requests.Session:
    retry = Retry(
        total=getattr(settings, "MERCADO_PUBLICO_RETRIES", 3),
        backoff_factor=getattr(settings, "MERCADO_PUBLICO_BACKOFF", 0.5),
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retry)
    s = requests.Session()
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    return s


def fetch_licitaciones(filters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Filtros soportados (query params entrantes):
      - estado        -> 'estado' (publicada, cerrada, etc.)
      - fecha_desde   -> rango (YYYY-MM-DD)
      - fecha_hasta   -> rango (YYYY-MM-DD)
      - codigo        -> 'codigo' (código exacto)
    Implementación:
      - Upstream acepta 'fecha' (un día). Para rangos se itera por día.
    """
    api_key = getattr(settings, "MERCADO_PUBLICO_API_KEY", "") or ""
    if not api_key:
        raise MercadoPublicoConfigError("MERCADO_PUBLICO_API_KEY no está configurada.")

    session = _build_session()
    timeout = getattr(settings, "MERCADO_PUBLICO_TIMEOUT", 15)

    def _do_request(params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            resp = session.get(
                BASE_URL,
                params=params,
                timeout=timeout,
                headers={
                    "User-Agent": "licitaciones-api/1.0",
                    "Accept": "application/json",
                    "Accept-Language": "es-CL,es;q=0.9",
                },
            )
            if not (200 <= resp.status_code < 300):
                body_text = (resp.text or "")[:500]
                body_json: Dict[str, Any] = {}
                try:
                    body_json = resp.json()
                except Exception:
                    body_json = {}
                if resp.status_code in (429, 503) or str(body_json.get("Codigo")) == "10500" or "simultáneas" in body_text:
                    raise MercadoPublicoBusy("Servicio ocupado en Mercado Público (peticiones simultáneas).")
                resp.raise_for_status()
            try:
                return resp.json()
            except ValueError as ex:
                snippet = (resp.text or "")[:200]
                raise MercadoPublicoError(f"Respuesta no es JSON válido. Body: {snippet}") from ex
        except requests.Timeout as ex:
            raise MercadoPublicoTimeout("Timeout consultando Mercado Público.") from ex
        except requests.HTTPError as ex:
            status_code = getattr(resp, "status_code", "desconocido")
            snippet = (getattr(resp, "text", "") or "")[:200]
            raise MercadoPublicoError(f"Error HTTP {status_code} en Mercado Público. Body: {snippet}") from ex
        except MercadoPublicoBusy:
            raise
        except Exception as ex:
            raise MercadoPublicoError("Error inesperado consultando Mercado Público.") from ex

    # Normalización simple de 'estado'
    estado_synonyms = {"abierta": "publicada"}
    estado_param = None
    if estado := filters.get("estado"):
        estado_param = estado_synonyms.get(estado.lower(), estado).lower()

    codigo = filters.get("codigo")
    fd = filters.get("fecha_desde")
    fh = filters.get("fecha_hasta")

    # Validaciones de fechas
    if fd:
        _validate_date(fd, "fecha_desde")
    if fh:
        _validate_date(fh, "fecha_hasta")

    # Si viene código, priorizar búsqueda por código (evitar combinar con fecha/estado para prevenir 400)
    if codigo:
        params = {"ticket": api_key, "codigo": codigo}
        return _do_request(params)

    # Helper para construir params comunes
    def base_params() -> Dict[str, Any]:
        p = {"ticket": api_key}
        if estado_param:
            p["estado"] = estado_param
        return p

    # Sin rango: un solo día si viene alguna fecha, o sin fecha (posible gran volumen en upstream)
    if fd and not fh:
        params = base_params()
        params["fecha"] = fd
        return _do_request(params)
    if fh and not fd:
        params = base_params()
        params["fecha"] = fh
        return _do_request(params)

    # Rango: iterar día a día con límite para proteger el servicio
    if fd and fh:
        start = dt.datetime.strptime(fd, "%Y-%m-%d").date()
        end = dt.datetime.strptime(fh, "%Y-%m-%d").date()
        if end < start:
            raise ValueError("fecha_hasta debe ser mayor o igual a fecha_desde.")
        max_days = 31
        if (end - start).days + 1 > max_days:
            raise ValueError(f"Rango de fechas demasiado amplio (máximo {max_days} días).")

        merged: list = []
        current = start
        while current <= end:
            params = base_params()
            params["fecha"] = current.strftime("%Y-%m-%d")
            data = _do_request(params)
            listado = data.get("Listado")
            if isinstance(listado, list):
                merged.extend(listado)
            current += dt.timedelta(days=1)

        return {"Cantidad": len(merged), "Listado": merged}

    # Sin fechas: solo filtrar por estado (si se envió)
    params = base_params()
    return _do_request(params)
