import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap } from '@angular/router';
import { of, throwError } from 'rxjs';
import { EvaluacionService } from '../../../core/services/evaluacion.service';
import { VinculacionService } from '../../../core/services/vinculacion.service';
import { CatalogoService } from '../../../core/services/catalogo.service';
import { PermisosService } from '../../../core/services/permisos.service';
import { AsignacionDetalle } from './asignacion-detalle';

describe('AsignacionDetalle', () => {
  let component: AsignacionDetalle;
  let fixture: ComponentFixture<AsignacionDetalle>;

  const evaluacionMock = {
    obtenerAsignacion: jasmine.createSpy('obtenerAsignacion'),
    obtenerIndicador: jasmine.createSpy('obtenerIndicador'),
  };

  const vinculacionMock = {
    contextoIndicador: jasmine.createSpy('contextoIndicador'),
  };

  const catalogoMock = {
    obtenerIndicadorMarco: jasmine.createSpy('obtenerIndicadorMarco'),
  };

  const permisosMock = {
    esSuperuser: false,
    tieneGrupo: jasmine.createSpy('tieneGrupo').and.returnValue(false),
    tieneAlgunPermiso: jasmine.createSpy('tieneAlgunPermiso').and.returnValue(false),
  };

  function asignacion(overrides: any = {}): any {
    return {
      id: 11,
      indicador: 7,
      indicador_nombre: 'Indicador 7',
      unidad_responsable: 2,
      unidad_responsable_nombre: 'Facultad de Ciencias',
      periodo: 3,
      periodo_nombre: 'Período 2026',
      estado: 'en_progreso',
      estado_display: 'En progreso',
      ...overrides,
    };
  }

  function corr(overrides: any = {}): any {
    return {
      id: 1,
      estado: 'confirmada',
      procedencia: 'manual',
      version_marco: { id: 1, nombre: 'EQ-SIDACES 2019', slug: 'eq-2019', activo: true },
      origen: { nivel: 'indicador', id: 7, texto: 'Indicador 7' },
      destino: { nivel: 'estandar', id: 3, texto: '6.1.1.1' },
      creado_por: 'ana',
      fecha_creacion: '2026-10-01T10:00:00Z',
      confirmado_por: 'maria',
      fecha_confirmacion: '2026-10-10T12:00:00Z',
      rechazado_por: null,
      fecha_rechazo: null,
      comentario: '',
      ...overrides,
    };
  }

  function crear(): void {
    fixture = TestBed.createComponent(AsignacionDetalle);
    component = fixture.componentInstance;
    fixture.detectChanges();
  }

  function texto(): string {
    return (fixture.nativeElement as HTMLElement).textContent ?? '';
  }

  beforeEach(async () => {
    evaluacionMock.obtenerAsignacion.calls.reset();
    evaluacionMock.obtenerIndicador.calls.reset();
    vinculacionMock.contextoIndicador.calls.reset();
    catalogoMock.obtenerIndicadorMarco.calls.reset();

    evaluacionMock.obtenerAsignacion.and.returnValue(of(asignacion()));
    evaluacionMock.obtenerIndicador.and.returnValue(of({ id: 7, nombre: 'Indicador 7', criterio_nombre: 'Criterio A' }));
    vinculacionMock.contextoIndicador.and.returnValue(
      of({ origen: { nivel: 'indicador', id: 7, texto: 'Indicador 7' }, correspondencias: [corr()] })
    );
    catalogoMock.obtenerIndicadorMarco.and.returnValue(of({ codigo: null, codigo_sintetico: false }));

    await TestBed.configureTestingModule({
      imports: [AsignacionDetalle],
      providers: [
        { provide: EvaluacionService, useValue: evaluacionMock },
        { provide: VinculacionService, useValue: vinculacionMock },
        { provide: CatalogoService, useValue: catalogoMock },
        { provide: PermisosService, useValue: permisosMock },
        {
          provide: ActivatedRoute,
          useValue: { snapshot: { paramMap: convertToParamMap({ id: '11' }), queryParamMap: convertToParamMap({}) } },
        },
      ],
    }).compileComponents();
  });

  it('carga la asignacion y muestra su marco relacionado', () => {
    crear();

    expect(evaluacionMock.obtenerAsignacion).toHaveBeenCalledWith(11);
    expect(texto()).toContain('Indicador 7');
    expect(texto()).toContain('Facultad de Ciencias');
    expect(texto()).toContain('En progreso');
    expect(texto()).toContain('Correspondencia confirmada');
    expect(texto()).toContain('6.1.1.1');
    expect(fixture.nativeElement.querySelector('app-marco-relacionado')).toBeTruthy();
  });

  it('muestra sin correspondencia confirmada cuando no hay vinculos confirmados', () => {
    vinculacionMock.contextoIndicador.and.returnValue(
      of({ origen: { nivel: 'indicador', id: 7, texto: 'Indicador 7' }, correspondencias: [] })
    );
    crear();

    expect(texto()).toContain('Sin correspondencia confirmada.');
    expect(texto()).toContain('Indicador 7');
  });

  it('error al cargar la asignacion es recuperable con reintento', () => {
    evaluacionMock.obtenerAsignacion.and.returnValue(throwError(() => ({ status: 500 })));
    crear();
    expect(texto()).toContain('No se pudo cargar la asignación');

    evaluacionMock.obtenerAsignacion.and.returnValue(of(asignacion()));
    const boton = Array.from((fixture.nativeElement as HTMLElement).querySelectorAll('button')).find(
      (b) => b.textContent?.trim() === 'Reintentar'
    );
    boton?.click();
    fixture.detectChanges();

    expect(evaluacionMock.obtenerAsignacion).toHaveBeenCalledTimes(2);
    expect(texto()).toContain('Facultad de Ciencias');
    expect(texto()).toContain('Correspondencia confirmada');
  });

  it('sin indicador en la asignacion no se monta el marco relacionado', () => {
    evaluacionMock.obtenerAsignacion.and.returnValue(
      of(asignacion({ indicador: null, indicador_nombre: '' }))
    );
    crear();

    expect(fixture.nativeElement.querySelector('app-marco-relacionado')).toBeNull();
    expect(texto()).toContain('Facultad de Ciencias');
  });

  it('un error de contexto no impide ver la asignacion', () => {
    vinculacionMock.contextoIndicador.and.returnValue(throwError(() => ({ status: 403 })));
    crear();

    expect(texto()).toContain('Facultad de Ciencias');
    expect(texto()).toContain('No tiene permisos para consultar el contexto');
  });
});
