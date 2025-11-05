import { Controller, Get, Query } from '@nestjs/common';
import { MercadoPublicoService } from './mercado-publico.service';

@Controller()
export class AppController {
  constructor(
    private readonly mercadoPublico: MercadoPublicoService,
  ) {}

  @Get('licitaciones')
  async getLicitaciones(
    @Query('estado') estado?: string,
    @Query('codigo') codigo?: string,
  ): Promise<any> {
    if (codigo) {
      return this.mercadoPublico.getLicitacionPorCodigo(codigo);
    }
    return this.mercadoPublico.getLicitacionesPorEstado(estado ?? 'publicada');
  }
}
