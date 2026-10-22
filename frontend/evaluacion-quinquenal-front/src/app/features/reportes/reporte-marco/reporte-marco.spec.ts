import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of, Subject, throwError } from 'rxjs';
import { ReporteMarco } from './reporte-marco';
import { ReportesService } from '../../../core/services/reportes.service';

function resultado(): any {
  const resumen = { asignaciones: 1, con_archivos: 1, aprobadas_globalmente: 0, pendientes_cierre: 1,
    documentos_solicitados: 2, documentos_entregados: 2, documentos_aprobados: 2,
    documentos_en_revision: 0, documentos_observados: 0, aprobacion_global_porcentaje: 0 };
  const dimension = { id: 3, codigo: 'VIII', nombre: 'Gestión institucional', orden: 8 };
  const estandar = { id: 7, codigo: '8.4.1.1', nombre: 'Gestión de riesgos', dimension_id: 3 };
  return { periodo: { id: 2, nombre: '2025–2030' }, version_periodo: { id: 1, nombre: 'Marco piloto' }, agrupar: 'dimension', resumen,
    rows: [{ ...resumen, version: { id: 1, nombre: 'Marco piloto' }, dimension, estandar: null }],
    opciones: { dimensiones: [dimension], estandares: [estandar] }, total: 1, page: 1, page_size: 10, total_pages: 1 };
}

describe('ReporteMarco', () => {
  let fixture: ComponentFixture<ReporteMarco>;
  let component: ReporteMarco;
  let service: jasmine.SpyObj<ReportesService>;
  beforeEach(async () => {
    service = jasmine.createSpyObj('ReportesService', ['reporteMarco', 'exportarReporte']);
    service.reporteMarco.and.returnValue(of(resultado()));
    await TestBed.configureTestingModule({ imports: [ReporteMarco], providers: [{ provide: ReportesService, useValue: service }] }).compileComponents();
    fixture = TestBed.createComponent(ReporteMarco);
    component = fixture.componentInstance;
    fixture.componentRef.setInput('periodoId', '2');
    fixture.componentRef.setInput('periodos', [{ id: 2, nombre: '2025–2030', activo: true }]);
    fixture.detectChanges();
  });

  it('distingue documentos aprobados del cierre global pendiente', () => {
    const texto = fixture.nativeElement.textContent;
    expect(texto).toContain('Marco piloto');
    expect(texto).toContain('Pendientes de cierre global');
    expect(texto).toContain('2/2');
    expect(component.datos?.resumen.aprobadas_globalmente).toBe(0);
    expect(component.datos?.resumen.documentos_aprobados).toBe(2);
    expect(texto).toContain('0 %');
  });

  it('filtra por dimensión y estándar y reinicia la página', () => {
    component.filtros.estandar = '99'; component.pagina = 3;
    component.cambiarDimension('3');
    expect(component.filtros.estandar).toBe('');
    expect(service.reporteMarco.calls.mostRecent().args[0]).toEqual({ periodo: '2', agrupar: 'dimension', dimension: '3', page: '1', page_size: '10' });
    component.filtros.estandar = '7'; component.filtros.agrupar = 'estandar'; component.cargar();
    expect(service.reporteMarco.calls.mostRecent().args[0]['estandar']).toBe('7');
  });

  it('la exportación conserva filtros sin limitarse a la página visible', () => {
    service.exportarReporte.and.returnValue(of(new Blob(['reporte'])));
    spyOn(URL, 'createObjectURL').and.returnValue('blob:reporte');
    spyOn(URL, 'revokeObjectURL'); spyOn(HTMLAnchorElement.prototype, 'click');
    component.filtros.dimension = '3'; component.pagina = 2;
    component.exportar('csv');
    expect(service.exportarReporte).toHaveBeenCalledWith('marco', 'csv', { periodo: '2', agrupar: 'dimension', dimension: '3' });
  });

  it('retira datos y exportaciones al perder acceso al período', () => {
    service.reporteMarco.and.returnValue(throwError(() => ({ status: 404 })));
    component.cargar(); fixture.detectChanges();
    expect(component.datos).toBeNull();
    expect(fixture.nativeElement.querySelector('.marco-table')).toBeNull();
    expect(fixture.nativeElement.querySelector('.reporte-exportar')).toBeNull();
    expect(fixture.nativeElement.textContent).toContain('perdió el acceso');
  });

  it('no restaura una respuesta anterior al cambiar de filtros', () => {
    const anterior = new Subject<any>(), actual = new Subject<any>();
    service.reporteMarco.and.returnValues(anterior, actual);
    component.cargar(); component.cambiarDimension('3');
    anterior.next(resultado());
    expect(component.datos).toBeNull();
    actual.next(resultado());
    expect(component.datos?.resumen.asignaciones).toBe(1);
    anterior.complete(); actual.complete();
  });

  it('el cambio de período limpia filtros de la versión anterior', () => {
    component.filtros.dimension = '3'; component.filtros.estandar = '7';
    fixture.componentRef.setInput('periodoId', '1'); fixture.detectChanges();
    expect(component.filtros.dimension).toBe(''); expect(component.filtros.estandar).toBe('');
    expect(service.reporteMarco.calls.mostRecent().args[0]['periodo']).toBe('1');
  });
});
