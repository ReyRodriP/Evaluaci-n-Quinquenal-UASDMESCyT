import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { CatalogoService } from './catalogo.service';
import { environment } from '../../../environments/environment';

describe('CatalogoService', () => {
  let service: CatalogoService;
  let httpMock: HttpTestingController;
  const base = `${environment.apiUrl}/catalogo`;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(CatalogoService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('listarVersiones hace GET a /catalogo/versiones/ y desempaqueta results', () => {
    let resultado: any[] = [];
    service.listarVersiones().subscribe((d) => (resultado = d));
    const req = httpMock.expectOne(`${base}/versiones/`);
    expect(req.request.method).toBe('GET');
    req.flush({ count: 1, results: [{ id: 1, slug: 'eq' }] });
    expect(resultado).toEqual([{ id: 1, slug: 'eq' }]);
  });

  it('listarDimensiones envia el filtro version', () => {
    let resultado: any[] = [];
    service.listarDimensiones('eq-sidaces-2019-res27-2019').subscribe((d) => (resultado = d));
    const req = httpMock.expectOne(
      (r) => r.url === `${base}/dimensiones/` && r.params.get('version') === 'eq-sidaces-2019-res27-2019'
    );
    expect(req.request.method).toBe('GET');
    req.flush({ results: [{ id: 15, codigo: 'VI' }] });
    expect(resultado.length).toBe(1);
  });

  it('listarIndicadores envia el filtro estandar', () => {
    let resultado: any[] = [];
    service.listarIndicadores(3).subscribe((d) => (resultado = d));
    const req = httpMock.expectOne(
      (r) => r.url === `${base}/indicadores/` && r.params.get('estandar') === '3'
    );
    req.flush({ results: [] });
    expect(resultado).toEqual([]);
  });

  it('acepta tambien respuesta como arreglo plano', () => {
    let resultado: any[] = [];
    service.listarComponentes(1).subscribe((d) => (resultado = d));
    const req = httpMock.expectOne(
      (r) => r.url === `${base}/componentes/` && r.params.get('dimension') === '1'
    );
    req.flush([{ id: 2 }]);
    expect(resultado).toEqual([{ id: 2 }]);
  });

  it('exportarCsv hace GET blob a /catalogo/exportar/ con filtro version', () => {
    let resultado: Blob | null = null;
    service.exportarCsv('eq-sidaces-2019-res27-2019').subscribe((d) => (resultado = d));
    const req = httpMock.expectOne(
      (r) =>
        r.url === `${base}/exportar/` &&
        r.params.get('version') === 'eq-sidaces-2019-res27-2019'
    );
    expect(req.request.method).toBe('GET');
    expect(req.request.responseType).toBe('blob');
    req.flush(new Blob(['a,b\n1,2\n']));
    expect(resultado).toBeTruthy();
  });
});
