import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of, Subject, throwError } from 'rxjs';
import { HistorialAsignacion } from './historial-asignacion';
import { EvaluacionService } from '../../../core/services/evaluacion.service';

function pagina(): any {
  return { count: 1, next: null, previous: null, page: 1, page_size: 10, results: [{
    id: 7, asignacion: 27, estado_anterior: 'en_progreso', estado_anterior_display: 'En progreso',
    estado_nuevo: 'aprobado', estado_nuevo_display: 'Aprobado', usuario: 9, usuario_nombre: '', usuario_identificador: 'jorge',
    comentario: 'Cierre global confirmado', fecha: '2026-10-23T14:00:00Z',
  }] };
}

describe('HistorialAsignacion', () => {
  let fixture: ComponentFixture<HistorialAsignacion>;
  let component: HistorialAsignacion;
  let service: jasmine.SpyObj<EvaluacionService>;
  beforeEach(async () => {
    service = jasmine.createSpyObj('EvaluacionService', ['historialAsignacion']);
    service.historialAsignacion.and.returnValue(of(pagina()));
    await TestBed.configureTestingModule({ imports: [HistorialAsignacion], providers: [{ provide: EvaluacionService, useValue: service }] }).compileComponents();
    fixture = TestBed.createComponent(HistorialAsignacion); component = fixture.componentInstance;
    fixture.componentRef.setInput('asignacionId', 27); fixture.componentRef.setInput('periodoId', 2); fixture.detectChanges();
  });

  it('muestra la decisión global con actor, estados y comentario registrado', () => {
    const texto = fixture.nativeElement.textContent;
    expect(texto).toContain('jorge'); expect(texto).toContain('En progreso'); expect(texto).toContain('Aprobado');
    expect(texto).toContain('Cierre global confirmado');
    expect(service.historialAsignacion).toHaveBeenCalledWith(27, 2, 1, 10);
  });

  it('consulta páginas posteriores del historial sin limitarse a los diez recientes', () => {
    component.cargar(2);
    expect(service.historialAsignacion.calls.mostRecent().args).toEqual([27, 2, 2, 10]);
  });

  it('no atribuye un registro a una cuenta que ya no está asociada', () => {
    service.historialAsignacion.and.returnValue(of({ ...pagina(), results: [{ ...pagina().results[0], usuario: null, usuario_identificador: null }] }));
    component.cargar(); fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Sin cuenta asociada');
    expect(fixture.nativeElement.textContent).toContain('Cierre global confirmado');
  });

  it('retira registros al perder el ámbito y oculta la sección si el rol es externo', () => {
    service.historialAsignacion.and.returnValue(throwError(() => ({ status: 404 })));
    component.cargar(); fixture.detectChanges();
    expect(component.registros).toEqual([]); expect(fixture.nativeElement.textContent).not.toContain('Cierre global confirmado');
    service.historialAsignacion.and.returnValue(throwError(() => ({ status: 403 })));
    component.cargar(); fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('section')).toBeNull();
  });

  it('no restaura respuestas de una asignación anterior al cambiar el contexto', () => {
    const anterior = new Subject<any>(), actual = new Subject<any>();
    service.historialAsignacion.and.returnValues(anterior, actual);
    component.cargar(); fixture.componentRef.setInput('asignacionId', 30); fixture.detectChanges();
    anterior.next(pagina()); expect(component.registros).toEqual([]);
    actual.next({ ...pagina(), count: 0, results: [] }); fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Aún no hay cambios de estado registrados');
    anterior.complete(); actual.complete();
  });
});
