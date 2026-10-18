import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { VinculacionService } from './vinculacion.service';
import { environment } from '../../../environments/environment';

describe('VinculacionService', () => {
  let service: VinculacionService;
  let httpMock: HttpTestingController;
  const base = `${environment.apiUrl}/vinculacion/correspondencias`;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(VinculacionService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('listarCorrespondencias hace GET paginado a /vinculacion/correspondencias/', () => {
    let resultado: any = null;
    service.listarCorrespondencias().subscribe((d) => (resultado = d));
    const req = httpMock.expectOne(`${base}/`);
    expect(req.request.method).toBe('GET');
    req.flush({ count: 0, next: null, previous: null, results: [] });
    expect(resultado.results).toEqual([]);
  });

  it('listarCorrespondencias envia filtros de estado, version y page', () => {
    let resultado: any = null;
    service.listarCorrespondencias({ estado: 'propuesta', version: 'eq', page: 2 }).subscribe((d) => (resultado = d));
    const req = httpMock.expectOne(
      (r) =>
        r.url === `${base}/` &&
        r.params.get('estado') === 'propuesta' &&
        r.params.get('version') === 'eq' &&
        r.params.get('page') === '2'
    );
    expect(req.request.method).toBe('GET');
    req.flush({ count: 0, results: [] });
    expect(resultado.results).toEqual([]);
  });

  it('obtenerCorrespondencia hace GET al detalle', () => {
    let resultado: any = null;
    service.obtenerCorrespondencia(9).subscribe((d) => (resultado = d));
    const req = httpMock.expectOne(`${base}/9/`);
    expect(req.request.method).toBe('GET');
    req.flush({ id: 9, estado: 'confirmada' });
    expect(resultado.id).toBe(9);
  });

  it('contextoCriterio hace GET a contexto/criterio/{id}/', () => {
    let resultado: any = null;
    service.contextoCriterio(5).subscribe((d) => (resultado = d));
    const req = httpMock.expectOne(`${environment.apiUrl}/vinculacion/contexto/criterio/5/`);
    expect(req.request.method).toBe('GET');
    req.flush({ origen: { nivel: 'criterio', id: 5, texto: 'C-1' }, correspondencias: [] });
    expect(resultado.correspondencias).toEqual([]);
  });

  it('contextoIndicador hace GET a contexto/indicador/{id}/', () => {
    let resultado: any = null;
    service.contextoIndicador(12).subscribe((d) => (resultado = d));
    const req = httpMock.expectOne(`${environment.apiUrl}/vinculacion/contexto/indicador/12/`);
    expect(req.request.method).toBe('GET');
    req.flush({ origen: { nivel: 'indicador', id: 12, texto: 'I-1' }, correspondencias: [] });
    expect(resultado.origen.id).toBe(12);
  });

  it('crearCorrespondencia hace POST con el payload', () => {
    let resultado: any = null;
    service.crearCorrespondencia({ version_marco: 1, indicador_op: 7, estandar: 3 }).subscribe((d) => (resultado = d));
    const req = httpMock.expectOne(`${base}/`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ version_marco: 1, indicador_op: 7, estandar: 3 });
    req.flush({ id: 1, estado: 'propuesta' });
    expect(resultado.estado).toBe('propuesta');
  });

  it('confirmarCorrespondencia hace POST a confirmar/ con comentario vacio', () => {
    let resultado: any = null;
    service.confirmarCorrespondencia(4).subscribe((d) => (resultado = d));
    const req = httpMock.expectOne(`${base}/4/confirmar/`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ comentario: '' });
    req.flush({ id: 4, estado: 'confirmada' });
    expect(resultado.estado).toBe('confirmada');
  });

  it('rechazarCorrespondencia hace POST a rechazar/ con el comentario', () => {
    let resultado: any = null;
    service.rechazarCorrespondencia(4, 'No aplica').subscribe((d) => (resultado = d));
    const req = httpMock.expectOne(`${base}/4/rechazar/`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ comentario: 'No aplica' });
    req.flush({ id: 4, estado: 'rechazada' });
    expect(resultado.estado).toBe('rechazada');
  });

  it('desconfirmarCorrespondencia hace POST a desconfirmar/ con el comentario', () => {
    let resultado: any = null;
    service.desconfirmarCorrespondencia(2, 'Revisión pendiente').subscribe((d) => (resultado = d));
    const req = httpMock.expectOne(`${base}/2/desconfirmar/`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ comentario: 'Revisión pendiente' });
    req.flush({ id: 2, estado: 'propuesta' });
    expect(resultado.estado).toBe('propuesta');
  });
});
