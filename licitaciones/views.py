from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services.mercado_publico import (
    fetch_licitaciones,
    MercadoPublicoError,
    MercadoPublicoConfigError,
    MercadoPublicoTimeout,
    MercadoPublicoBusy,
)


class LicitacionesView(APIView):
    """
    GET /api/licitaciones?estado=&fecha_desde=&fecha_hasta=&codigo=
    Devuelve JSON crudo de la API de Mercado Público.
    """
    def get(self, request):
        filters = {
            "estado": request.query_params.get("estado"),
            "fecha_desde": request.query_params.get("fecha_desde"),
            "fecha_hasta": request.query_params.get("fecha_hasta"),
            "codigo": request.query_params.get("codigo"),
        }

        # Limpiar None
        filters = {k: v for k, v in filters.items() if v}

        try:
            data = fetch_licitaciones(filters)
            return Response(data, status=status.HTTP_200_OK)
        except ValueError as ve:
            return Response({"detail": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except MercadoPublicoConfigError as ce:
            return Response({"detail": str(ce)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except MercadoPublicoTimeout as te:
            return Response({"detail": str(te)}, status=status.HTTP_504_GATEWAY_TIMEOUT)
        except MercadoPublicoBusy as be:
            return Response({"detail": str(be)}, status=status.HTTP_503_SERVICE_UNAVAILABLE, headers={"Retry-After": "2"})
        except MercadoPublicoError as me:
            return Response({"detail": str(me)}, status=status.HTTP_502_BAD_GATEWAY)

# Create your views here.
