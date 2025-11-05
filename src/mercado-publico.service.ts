import { Injectable, HttpException } from '@nestjs/common';
import { HttpService } from '@nestjs/axios';
import { firstValueFrom } from 'rxjs';

@Injectable()
export class MercadoPublicoService {
  private readonly baseUrl =
    process.env.MP_API_BASE_URL ??
    'https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json';
  private readonly retryAttempts = parseInt(process.env.MP_API_RETRY_ATTEMPTS ?? '3', 10);
  private readonly retryDelayMs = parseInt(process.env.MP_API_RETRY_DELAY_MS ?? '1500', 10);

  constructor(private readonly http: HttpService) {}

  private ensureTicket() {
    if (!process.env.MP_API_TICKET) {
      throw new HttpException('Falta la variable de entorno MP_API_TICKET', 500);
    }
  }

  private sleep(ms: number) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  private isRetryable(errOrData: any): boolean {
    // Errores HTTP típicos de saturación o intermitencia
    const status = errOrData?.response?.status;
    if (status && [429, 502, 503].includes(status)) return true;

    // Errores de timeout/conexión
    const code = errOrData?.code;
    if (code && ['ECONNABORTED', 'ETIMEDOUT', 'ECONNRESET'].includes(code)) return true;

    // Errores reportados por la API en el cuerpo (p. ej., peticiones simultáneas 10500)
    const data = errOrData?.response?.data ?? errOrData;
    if (data && typeof data === 'object' && Number(data.Codigo) === 10500) return true;

    return false;
  }

  private async fetch(params: Record<string, any>): Promise<any> {
    let lastError: any;
    for (let attempt = 0; attempt < this.retryAttempts; attempt++) {
      try {
        const { data } = await firstValueFrom(
          this.http.get(this.baseUrl, {
            params,
            headers: { Accept: 'application/json' },
          }),
        );

        // La API puede responder 200 con objeto de error { Codigo, Mensaje }
        if (data && typeof data === 'object' && 'Codigo' in data && 'Mensaje' in data) {
          if (this.isRetryable(data) && attempt < this.retryAttempts - 1) {
            await this.sleep(this.retryDelayMs * (attempt + 1));
            continue;
          }
          throw new HttpException(data, 502);
        }

        return data;
      } catch (e: any) {
        lastError = e;
        if (this.isRetryable(e) && attempt < this.retryAttempts - 1) {
          await this.sleep(this.retryDelayMs * (attempt + 1));
          continue;
        }
        throw new HttpException(
          e?.response?.data ?? e?.message ?? 'Error consultando Mercado Público',
          e?.response?.status ?? 502,
        );
      }
    }
    throw new HttpException(
      lastError?.response?.data ?? lastError?.message ?? 'Error consultando Mercado Público',
      lastError?.response?.status ?? 502,
    );
  }

  async getLicitacionesPorEstado(
    estado: string = 'publicada',
    extraParams: Record<string, string | number> = {},
  ): Promise<any> {
    this.ensureTicket();
    const params = {
      estado,
      ticket: process.env.MP_API_TICKET!,
      ...extraParams,
    };
    return this.fetch(params);
  }

  async getLicitacionPorCodigo(codigo: string): Promise<any> {
    this.ensureTicket();
    const params = {
      codigo,
      ticket: process.env.MP_API_TICKET!,
    };
    return this.fetch(params);
  }
}
