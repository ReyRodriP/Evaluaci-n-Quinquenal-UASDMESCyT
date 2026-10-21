import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { OrganizacionService } from './organizacion.service';
import { environment } from '../../../environments/environment';

describe('OrganizacionService: ámbitos de revisión', () => {
  let service: OrganizacionService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({ providers: [provideHttpClient(), provideHttpClientTesting()] });
    service = TestBed.inject(OrganizacionService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('recupera todas las páginas del usuario sin perder ámbitos ni seguir URLs externas', () => {
    let resultado: any[] = [];
    service.listarAmbitosRevision(20).subscribe(items => resultado = items);
    const primera = http.expectOne(req => req.url === `${environment.apiUrl}/ambitos-revision/` && req.params.get('page') === '1');
    expect(primera.request.params.get('usuario')).toBe('20');
    primera.flush({ results: [{ id: 1 }], next: 'https://ejemplo.invalid/ambitos?page=2' });
    const segunda = http.expectOne(req => req.url === `${environment.apiUrl}/ambitos-revision/` && req.params.get('page') === '2');
    expect(segunda.request.params.get('usuario')).toBe('20');
    segunda.flush({ results: [{ id: 2 }], next: null });
    expect(resultado.map(item => item.id)).toEqual([1, 2]);
  });

  it('envía creación, revocación y consulta de configuración al contrato interno', () => {
    const payload = { usuario: 20, unidad_organizacional: 12, periodo: 2 };
    service.crearAmbitoRevision(payload).subscribe();
    const crear = http.expectOne(`${environment.apiUrl}/ambitos-revision/`);
    expect(crear.request.method).toBe('POST');
    expect(crear.request.body).toEqual(payload);
    crear.flush({ id: 1 });
    service.actualizarAmbitoRevision(1, { activo: false }).subscribe();
    const revocar = http.expectOne(`${environment.apiUrl}/ambitos-revision/1/`);
    expect(revocar.request.method).toBe('PATCH');
    expect(revocar.request.body).toEqual({ activo: false });
    revocar.flush({ id: 1, activo: false });
    service.configuracionAmbitosRevision().subscribe(config => expect(config.alcance_explicito_activo).toBeTrue());
    http.expectOne(`${environment.apiUrl}/ambitos-revision/configuracion/`).flush({ alcance_explicito_activo: true });
  });

  it('incluye unidades y períodos que están fuera de la primera página al configurar ámbitos', () => {
    for (const [recurso, consultar] of [
      ['unidades-organizacionales', () => service.listarUnidadesParaAmbitos()],
      ['periodos', () => service.listarPeriodosParaAmbitos()],
    ] as const) {
      let ids: number[] = [];
      consultar().subscribe(items => ids = items.map(item => item.id));
      http.expectOne(req => req.url === `${environment.apiUrl}/${recurso}/` && req.params.get('page') === '1')
        .flush({ results: [{ id: 1 }], next: '?page=2' });
      http.expectOne(req => req.url === `${environment.apiUrl}/${recurso}/` && req.params.get('page') === '2')
        .flush({ results: [{ id: 51 }], next: null });
      expect(ids).toEqual([1, 51]);
    }
  });
});
