import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { EvidenciasService } from './evidencias.service';
import { environment } from '../../../environments/environment';

describe('EvidenciasService: ZIP mixto', () => {
  it('mantiene el contrato anterior y separa IDs de documentos cuando se incluyen', () => {
    TestBed.configureTestingModule({ providers: [provideHttpClient(), provideHttpClientTesting()] });
    const service = TestBed.inject(EvidenciasService), http = TestBed.inject(HttpTestingController);
    const url = `${environment.apiUrl}/evidencias/descargas-masivas/`;
    service.descargarMasiva([1]).subscribe();
    const anterior = http.expectOne(url);
    expect(anterior.request.body).toEqual({ evidencias: [1] }); anterior.flush(new Blob(['zip']));
    service.descargarMasiva([1], [1, 2]).subscribe();
    const mixto = http.expectOne(url);
    expect(mixto.request.body).toEqual({ evidencias: [1], solicitudes: [1, 2] });
    expect(mixto.request.responseType).toBe('blob'); mixto.flush(new Blob(['zip'])); http.verify();
  });
});
