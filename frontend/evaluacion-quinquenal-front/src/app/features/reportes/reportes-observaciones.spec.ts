import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';
import { of, Subject, throwError } from 'rxjs';
import { ToastrService } from 'ngx-toastr';
import { Reportes } from './reportes';
import { ReportesService } from '../../core/services/reportes.service';
import { EvaluacionService } from '../../core/services/evaluacion.service';
import { OrganizacionService } from '../../core/services/organizacion.service';
import { PermisosService } from '../../core/services/permisos.service';

function respuesta(): any {
  const comun = { evidencia: 'Documento', indicador: 'Indicador', unidad_responsable: 'Unidad de prueba', periodo: 'P2', periodo_id: 2,
    recurso_id: 3, version: 1, observador: 'jorge', observador_id: 9, comentario: 'Corregir fecha', fecha: '22/10/2026 12:00', total_observaciones: 1 };
  return { total_observaciones: 2, evidencias_observadas: 2, observadores: [{ id: 9, username: 'jorge' }], page: 1, rows: [
    { ...comun, tipo_recurso: 'documento', origen: 'Documento solicitado', decision: 'observada', decision_display: 'Cambios solicitados', asignacion_id: 27, version_id: 8 },
    { ...comun, tipo_recurso: 'evidencia', origen: 'Evidencia anterior', decision: 'comentario', decision_display: 'Comentario', asignacion_id: 26, version_id: 50 },
  ] };
}

describe('Reportes: observaciones de ambos flujos', () => {
  let fixture: ComponentFixture<Reportes>;
  let component: Reportes;
  let reportes: jasmine.SpyObj<ReportesService>;
  beforeEach(async () => {
    reportes = jasmine.createSpyObj('ReportesService', ['reporteObservaciones', 'exportarReporte']);
    reportes.reporteObservaciones.and.returnValue(of(respuesta()));
    await TestBed.configureTestingModule({ imports: [Reportes, RouterTestingModule], providers: [
      { provide: ReportesService, useValue: reportes },
      { provide: EvaluacionService, useValue: { listarPeriodos: () => of([{ id: 2, nombre: 'P2', activo: true }]), periodoActivo: () => of({ id: 2, nombre: 'P2', activo: true }), listarCriterios: () => of([]) } },
      { provide: OrganizacionService, useValue: { listarFacultades: () => of([]), listarDepartamentos: () => of([]), listarUnidadesOrganizacionales: () => of([]) } },
      { provide: PermisosService, useValue: { esSuperuser: false, tieneGrupo: () => false, tieneAlgunPermiso: () => false } },
      { provide: ToastrService, useValue: { error: () => {}, success: () => {} } },
      { provide: ActivatedRoute, useValue: { snapshot: { queryParamMap: convertToParamMap({ reporte: 'observaciones', periodo: '2' }) } } },
    ] }).compileComponents();
    fixture = TestBed.createComponent(Reportes); component = fixture.componentInstance; fixture.detectChanges();
  });

  it('muestra comentarios de ambos flujos con unidad y observadores autorizados', () => {
    expect(component.pestanaActiva).toBe('observaciones');
    const texto = fixture.nativeElement.textContent;
    expect(texto).toContain('Documento solicitado'); expect(texto).toContain('Evidencia anterior');
    expect(texto).toContain('Cambios solicitados'); expect(texto).toContain('Unidad de prueba');
    expect(fixture.nativeElement.querySelector('select[name=obs_usuario]').textContent).toContain('jorge');
    expect(component.obsResumen.evidencias).toBe(2);
  });

  it('cada enlace conserva recurso, período e identificador de versión sin colisiones', () => {
    const enlaces: HTMLAnchorElement[] = Array.from(fixture.nativeElement.querySelectorAll('.observation-detail-link'));
    const doc = enlaces.find(a => a.getAttribute('href')?.includes('/asignaciones/27/detalle'))!;
    expect(doc.getAttribute('href')).toContain('documento=3'); expect(doc.getAttribute('href')).toContain('version_documento=8');
    const anterior = enlaces.find(a => a.getAttribute('href')?.includes('/evidencias/3/detalle'))!;
    expect(anterior.getAttribute('href')).toContain('version=50'); expect(anterior.getAttribute('href')).toContain('periodo=2');
  });

  it('envía filtros documentales y mantiene los mismos filtros al exportar', () => {
    component.obsFiltros.origen = 'documento'; component.obsFiltros.decision = 'observada'; component.obsFiltros.usuario = '9';
    component.cargarObservaciones();
    expect(reportes.reporteObservaciones.calls.mostRecent().args[0]).toEqual({ periodo: '2', origen: 'documento', decision: 'observada', usuario: '9', page: 1, page_size: 10 });
    reportes.exportarReporte.and.returnValue(of(new Blob(['excel'])));
    spyOn(URL, 'createObjectURL').and.returnValue('blob:excel'); spyOn(URL, 'revokeObjectURL'); spyOn(HTMLAnchorElement.prototype, 'click');
    component.exportar('xlsx');
    expect(reportes.exportarReporte).toHaveBeenCalledWith('observaciones', 'xlsx', { periodo: '2', origen: 'documento', decision: 'observada', usuario: '9' });
  });

  it('retira filas, observadores y exportación habilitada al perder el acceso', () => {
    reportes.reporteObservaciones.and.returnValue(throwError(() => ({ status: 404 })));
    component.cargarObservaciones(); fixture.detectChanges();
    expect(component.obsRows).toEqual([]); expect(component.obsObservadores).toEqual([]);
    expect(component.obsResumen.total).toBe(0);
    expect(fixture.nativeElement.querySelector('app-crud-table')).toBeNull();
    expect(fixture.nativeElement.querySelector('.btn-exportar.excel').disabled).toBeTrue();
  });

  it('descarta una respuesta anterior después de cambiar los filtros', () => {
    const anterior = new Subject<any>(), actual = new Subject<any>();
    reportes.reporteObservaciones.and.returnValues(anterior, actual);
    component.cargarObservaciones(); component.obsFiltros.origen = 'documento'; component.cargarObservaciones();
    actual.next({ ...respuesta(), rows: [respuesta().rows[0]], total_observaciones: 1 });
    anterior.next(respuesta());
    expect(component.obsRows.map(r => r.tipo_recurso)).toEqual(['documento']);
    anterior.complete(); actual.complete();
  });

  it('invalida los resultados visibles si la exportación rechaza el acceso', () => {
    reportes.exportarReporte.and.returnValue(throwError(() => ({ status: 403 })));
    component.exportar('xlsx'); fixture.detectChanges();
    expect(component.obsRows).toEqual([]); expect(component.obsObservadores).toEqual([]);
    expect(fixture.nativeElement.querySelector('.btn-exportar.excel').disabled).toBeTrue();
  });
});
