import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap } from '@angular/router';
import { of, throwError } from 'rxjs';
import { EvaluacionService } from '../../../core/services/evaluacion.service';
import { VinculacionService } from '../../../core/services/vinculacion.service';
import { CatalogoService } from '../../../core/services/catalogo.service';
import { PermisosService } from '../../../core/services/permisos.service';
import { AsignacionDetalle } from './asignacion-detalle';
import { DocumentosService } from '../../../core/services/documentos.service';

describe('AsignacionDetalle', () => {
  let component: AsignacionDetalle;
  let fixture: ComponentFixture<AsignacionDetalle>;

  const evaluacionMock = {
    obtenerAsignacion: jasmine.createSpy('obtenerAsignacion'),
    obtenerIndicador: jasmine.createSpy('obtenerIndicador'),
    historialAsignacion: jasmine.createSpy('historialAsignacion'),
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
    evaluacionMock.historialAsignacion.calls.reset();
    evaluacionMock.historialAsignacion.and.returnValue(of({ count: 0, results: [], next: null, previous: null, page: 1, page_size: 10 }));
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
        { provide: DocumentosService, useValue: { contexto: () => of({ gestion_documental: false }), listar: () => of([]) } },
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

  it('muestra la ruta directa y el encargado sin consultar correspondencias operativas', () => {
    evaluacionMock.obtenerAsignacion.and.returnValue(of(asignacion({
      indicador: null, indicador_marco: 7, tipo_origen: 'marco', encargado_nombre: 'responsable',
      ruta_marco: {
        version: { id: 1, nombre: 'Marco técnico', slug: 'marco-tecnico', activo: false },
        dimension: { id: 5, codigo: 'VI', nombre: 'Personal académico' },
        componente: { id: 6, codigo: '6.1', nombre: 'Carrera académica' },
        criterio: { id: 11, codigo: '6.1.1', nombre: 'Criterio del marco' },
        estandar: { id: 20, codigo: '6.1.1.2', nombre: 'Estándar técnico' },
        indicador: { id: 7, codigo: '6.1.1.2-IND-01', nombre: 'Indicador del marco', orden: 1, codigo_sintetico: true },
      },
    })));
    crear();
    expect(texto()).toContain('Personal académico');
    expect(texto()).toContain('6.1.1.2');
    expect(texto()).toContain('responsable');
    expect(texto()).toContain('no oficial');
    expect(vinculacionMock.contextoIndicador).not.toHaveBeenCalled();
    expect(fixture.nativeElement.querySelector('app-marco-relacionado')).toBeNull();
  });

  it('retira información ya cargada cuando una nueva consulta pierde autorización', () => {
    crear();
    evaluacionMock.obtenerAsignacion.and.returnValue(throwError(() => ({ status: 404 })));
    component.cargar();
    fixture.detectChanges();
    expect(component.asignacion).toBeNull();
    expect(fixture.nativeElement.querySelector('.asignacion-card')).toBeNull();
  });

  it('consulta el detalle histórico con el período de la navegación', () => {
    const route = TestBed.inject(ActivatedRoute);
    (route.snapshot as any).queryParamMap = convertToParamMap({ periodo: '3' });
    crear();
    expect(evaluacionMock.obtenerAsignacion).toHaveBeenCalledWith(11, '3');
  });
});
