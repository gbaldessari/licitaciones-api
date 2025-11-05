import { Module } from '@nestjs/common';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { HttpModule } from '@nestjs/axios';
import { MercadoPublicoService } from './mercado-publico.service';
import { ConfigModule } from '@nestjs/config';

@Module({
  imports: [
    ConfigModule.forRoot({
      isGlobal: true,
      envFilePath: ['.ENV', '.env'],
    }),
    HttpModule,
  ],
  controllers: [AppController],
  providers: [
    AppService,
    MercadoPublicoService,
  ],
})
export class AppModule {}
