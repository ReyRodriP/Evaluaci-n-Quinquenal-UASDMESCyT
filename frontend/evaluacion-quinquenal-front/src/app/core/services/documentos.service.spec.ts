import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { DocumentosService } from './documentos.service';
import { environment } from '../../../environments/environment';
import { calcularMetricas, FilaSeguimiento } from '../models/seguimiento.model';

describe('DocumentosService', () => {
  let service: DocumentosService;
  let http: HttpTestingController;
  beforeEach(() => {
    TestBed.configureTestingModule({ providers: [provideHttpClient(), provideHttpClientTesting()] });
    service = TestBed.inject(DocumentosService);
    http = TestBed.inject(HttpTestingController);
  });
  afterEach(() => http.verify());

  it('recupera todas las solicitudes paginadas de la asignación', () => {
    let resultado: any[] = [];
    service.listar(26).subscribe(items => resultado = items);
    const primera = http.expectOne(`${environment.apiUrl}/solicitudes-documentales/?asignacion=26`);
    const siguiente = `${environment.apiUrl}/solicitudes-documentales/?asignacion=26&page=2`;
    primera.flush({ results: [{ id: 1 }], next: siguiente });
    http.expectOne(siguiente).flush({ results: [{ id: 2 }], next: null });
    expect(resultado.map(item => item.id)).toEqual([1, 2]);
  });

  it('separa la decisión sobre versión del cierre global', () => {
    service.accion(3, 'aprobar', 12, 'Correcto').subscribe();
    const documento = http.expectOne(`${environment.apiUrl}/solicitudes-documentales/3/aprobar/`);
    expect(documento.request.body).toEqual({ version_id: 12, comentario: 'Correcto' });
    documento.flush({});
    service.aprobarGlobal(26).subscribe();
    const global = http.expectOne(`${environment.apiUrl}/asignaciones/26/aprobar/`);
    expect(global.request.method).toBe('POST');
    global.flush({});
  });

  it('consulta los documentos por período al reconstruir el listado de evidencias', () => {
    let resultado: any[] = [];
    service.listarPeriodo('2').subscribe(items => resultado = items);
    http.expectOne(`${environment.apiUrl}/solicitudes-documentales/?periodo=2`).flush({ results: [{ id: 3, asignacion: 27 }], next: null });
    expect(resultado).toEqual([{ id: 3, asignacion: 27 }]);
  });

  it('cuenta una asignación con dos documentos como una sola con evidencia', () => {
    const fila = { asignacionId: 26, evidenciaId: null, claveRevision: 'en_revision', documentosResumen: { solicitados: 2, entregados: 2, aprobados: 1, observados: 0 } } as FilaSeguimiento;
    const metricas = calcularMetricas([fila], false);
    expect(metricas.total).toBe(1);
    expect(metricas.conEvidencia).toBe(1);
    expect(metricas.sinEvidencia).toBe(0);
  });
});
