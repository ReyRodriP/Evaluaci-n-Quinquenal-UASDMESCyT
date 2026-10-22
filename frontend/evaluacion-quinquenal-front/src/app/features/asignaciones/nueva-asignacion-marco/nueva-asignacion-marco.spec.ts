import { ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { of, Subject, throwError } from 'rxjs';
import { EvaluacionService } from '../../../core/services/evaluacion.service';
import { NuevaAsignacionMarco } from './nueva-asignacion-marco';

function contexto(): any {
  return { periodo: { id: 2, nombre: '2025–2030' }, version: { id: 1, nombre: 'Marco piloto', activo: false },
    unidades: [{ id: 23, nombre: 'Postgrado Barahona', ruta: 'UASD / Barahona / Postgrado', tipo: 'Unidad' }, { id: 21, nombre: 'Postgrado General', ruta: 'UASD / Postgrado General', tipo: 'Unidad' }],
    encargados: [{ id: 6, username: 'usuario1', nombre: 'Responsable' }], asignaciones_existentes: [],
    indicadores: [{ id: 7, ruta: {
      version: { id: 1, nombre: 'Marco piloto', slug: 'piloto', activo: false },
      dimension: { id: 1, codigo: 'VI', nombre: 'Personal académico' }, componente: { id: 2, codigo: '6.1', nombre: 'Carrera académica' },
      criterio: { id: 3, codigo: '6.1.1', nombre: 'Criterio' }, estandar: { id: 4, codigo: '6.1.1.2', nombre: 'Estándar' },
      indicador: { id: 7, codigo: '6.1.1.2-IND-01', codigo_sintetico: true, nombre: 'Indicador del marco', orden: 1 },
    } }],
  };
}

describe('NuevaAsignacionMarco', () => {
  let fixture: ComponentFixture<NuevaAsignacionMarco>;
  let component: NuevaAsignacionMarco;
  let service: jasmine.SpyObj<EvaluacionService>;
  beforeEach(async () => {
    service = jasmine.createSpyObj('EvaluacionService', ['contextoAsignacionMarco', 'crearAsignacion']);
    service.contextoAsignacionMarco.and.returnValue(of(contexto()));
    await TestBed.configureTestingModule({ imports: [NuevaAsignacionMarco, RouterTestingModule], providers: [{ provide: EvaluacionService, useValue: service }] }).compileComponents();
    fixture = TestBed.createComponent(NuevaAsignacionMarco); component = fixture.componentInstance;
    fixture.componentRef.setInput('periodoId', '2'); fixture.detectChanges();
  });
  function completar(): void {
    component.dimension = '1'; component.componente = '2'; component.criterio = '3'; component.estandar = '4'; component.indicador = '7'; component.unidad = '23'; component.encargado = '6';
  }

  it('utiliza la versión explícita y muestra la ruta del indicador sin activar el catálogo', () => {
    completar(); fixture.detectChanges();
    expect(service.contextoAsignacionMarco).toHaveBeenCalledWith('2', undefined);
    expect(fixture.nativeElement.textContent).toContain('Marco piloto');
    expect(fixture.nativeElement.textContent).toContain('versión global inactiva');
    expect(fixture.nativeElement.querySelector('app-ruta-marco').textContent).toContain('Identificador interno, no oficial');
  });
  it('limpia las selecciones descendientes al cambiar de dimensión', () => {
    completar(); component.cambiarJerarquia('dimension', '99');
    expect([component.componente, component.criterio, component.estandar, component.indicador]).toEqual(['', '', '', '']);
    expect(component.puedeGuardar).toBeFalse();
  });
  it('cambia de unidad sin conservar un encargado de la unidad anterior', () => {
    completar();
    service.contextoAsignacionMarco.and.returnValue(of({ ...contexto(), encargados: [] }));
    component.cambiarUnidad('21');
    expect(service.contextoAsignacionMarco).toHaveBeenCalledWith('2', '21');
    expect(component.encargado).toBe(''); expect(component.puedeGuardar).toBeFalse();
  });
  it('detecta duplicados y ofrece abrir la asignación existente', () => {
    completar(); component.contexto!.asignaciones_existentes = [{ id: 26, indicador_marco: 7 }]; fixture.detectChanges();
    expect(component.puedeGuardar).toBeFalse();
    expect(fixture.nativeElement.textContent).toContain('ya está asignado');
    expect(fixture.nativeElement.querySelector('a[href*="asignaciones/26/detalle"]')).toBeTruthy();
  });
  it('crea con referencia directa y encargado y evita dobles envíos', () => {
    completar(); const guardado = new Subject<any>(); service.crearAsignacion.and.returnValue(guardado);
    spyOn(component.creada, 'emit'); component.guardar(); component.guardar();
    expect(service.crearAsignacion).toHaveBeenCalledTimes(1);
    expect(service.crearAsignacion).toHaveBeenCalledWith({ periodo: 2, indicador_marco: 7, unidad_responsable: 23, encargado: 6 });
    guardado.next({ id: 30, periodo: 2, estado: 'pendiente' });
    expect(component.creada.emit).toHaveBeenCalledWith({ id: 30, periodo: 2, estado: 'pendiente' }); guardado.complete();
  });
  it('muestra el rechazo del servidor conservando las selecciones del formulario', () => {
    completar(); service.crearAsignacion.and.returnValue(throwError(() => ({ error: { encargado: ['El encargado dejó de estar activo.'] } })));
    component.guardar(); fixture.detectChanges();
    expect(component.error).toContain('dejó de estar activo'); expect(component.indicador).toBe('7'); expect(component.guardando).toBeFalse();
  });
  it('ignora respuestas de una selección de unidad anterior', () => {
    const anterior = new Subject<any>(), actual = new Subject<any>(); service.contextoAsignacionMarco.and.returnValues(anterior, actual);
    component.cambiarUnidad('23'); component.cambiarUnidad('21'); anterior.next(contexto());
    expect(component.contexto).toBeNull(); actual.next({ ...contexto(), encargados: [] });
    expect(component.contexto?.encargados).toEqual([]); anterior.complete(); actual.complete();
  });
});
