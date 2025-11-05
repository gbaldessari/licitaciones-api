import { Controller, Get, Query } from '@nestjs/common';
import { AppService } from './app.service';
import { MercadoPublicoService } from './mercado-publico.service';

@Controller()
export class AppController {
  constructor(
    private readonly appService: AppService,
    private readonly mercadoPublico: MercadoPublicoService,
  ) {}

  @Get()
  getHello(): string {
    return this.appService.getHello();
  }

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
