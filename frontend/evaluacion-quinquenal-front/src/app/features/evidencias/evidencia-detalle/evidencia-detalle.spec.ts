import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap } from '@angular/router';
import { of, throwError } from 'rxjs';
import { ToastrService } from 'ngx-toastr';
import { EvidenciasService } from '../../../core/services/evidencias.service';
import { EvaluacionService } from '../../../core/services/evaluacion.service';
import { VinculacionService } from '../../../core/services/vinculacion.service';
import { CatalogoService } from '../../../core/services/catalogo.service';
import { PermisosService } from '../../../core/services/permisos.service';
import { EvidenciaDetalle } from './evidencia-detalle';

describe('EvidenciaDetalle con contexto EQ-SIDACES', () => {
  let component: EvidenciaDetalle;
  let fixture: ComponentFixture<EvidenciaDetalle>;

  const evidenciasMock = {
    detalleEvidencia: jasmine.createSpy('detalleEvidencia'),
  };

  const evaluacionMock = {
    obtenerIndicador: jasmine.createSpy('obtenerIndicador'),
    aprobarAsignacion: jasmine.createSpy('aprobarAsignacion'),
    rechazarAsignacion: jasmine.createSpy('rechazarAsignacion'),
    solicitarCambios: jasmine.createSpy('solicitarCambios'),
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

  const toastMock = {
    success: jasmine.createSpy('success'),
    error: jasmine.createSpy('error'),
  };

  function evidencia(overrides: any = {}): any {
    return {
      id_evidencia: 3,
      titulo: 'Memoria anual',
      descripcion: 'Documento de gestión',
      estado: 'activa',
      versiones: [],
      asignacion: 5,
      asignacion_info: {
        id: 5,
        indicador: 7,
        indicador_nombre: 'Indicador 7',
        unidad_responsable: 2,
        unidad_responsable_nombre: 'Facultad de Ciencias',
        periodo: 3,
        periodo_nombre: 'Período 2026',
        estado: 'en_progreso',
        estado_display: 'En progreso',
      },
      puede_editar_info: false,
      puede_subir_version: false,
      puede_cambiar_estado: false,
      historial_estados: [],
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
    fixture = TestBed.createComponent(EvidenciaDetalle);
    component = fixture.componentInstance;
    fixture.detectChanges();
  }

  function texto(): string {
    return (fixture.nativeElement as HTMLElement).textContent ?? '';
  }

  beforeEach(async () => {
    evidenciasMock.detalleEvidencia.calls.reset();
    evaluacionMock.obtenerIndicador.calls.reset();
    vinculacionMock.contextoIndicador.calls.reset();
    catalogoMock.obtenerIndicadorMarco.calls.reset();

    evidenciasMock.detalleEvidencia.and.returnValue(of(evidencia()));
    evaluacionMock.obtenerIndicador.and.returnValue(of({ id: 7, nombre: 'Indicador 7', criterio_nombre: 'Criterio A' }));
    vinculacionMock.contextoIndicador.and.returnValue(
      of({ origen: { nivel: 'indicador', id: 7, texto: 'Indicador 7' }, correspondencias: [corr()] })
    );
    catalogoMock.obtenerIndicadorMarco.and.returnValue(of({ codigo: null, codigo_sintetico: false }));

    await TestBed.configureTestingModule({
      imports: [EvidenciaDetalle],
      providers: [
        { provide: EvidenciasService, useValue: evidenciasMock },
        { provide: EvaluacionService, useValue: evaluacionMock },
        { provide: VinculacionService, useValue: vinculacionMock },
        { provide: CatalogoService, useValue: catalogoMock },
        { provide: PermisosService, useValue: permisosMock },
        { provide: ToastrService, useValue: toastMock },
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: {
              paramMap: convertToParamMap({ id: '3' }),
              queryParamMap: convertToParamMap({ periodo: '3' }),
            },
          },
        },
      ],
    }).compileComponents();
  });

  it('muestra la evidencia con el contexto EQ-SIDACES de su asignacion', () => {
    crear();

    expect(texto()).toContain('Memoria anual');
    expect(texto()).toContain('En progreso');
    expect(fixture.nativeElement.querySelector('app-marco-relacionado')).toBeTruthy();
    expect(texto()).toContain('Indicador operativo');
    expect(texto()).toContain('Indicador 7');
    expect(texto()).toContain('Correspondencia confirmada');
    expect(texto()).toContain('6.1.1.1');
  });

  it('sin indicador en la asignacion no se monta el marco y la evidencia sigue funcionando', () => {
    evidenciasMock.detalleEvidencia.and.returnValue(
      of(evidencia({ asignacion_info: { id: 5, estado: 'pendiente', estado_display: 'Pendiente' } }))
    );
    crear();

    expect(fixture.nativeElement.querySelector('app-marco-relacionado')).toBeNull();
    expect(texto()).toContain('Memoria anual');
    expect(texto()).toContain('Pendiente');
  });

  it('un error de contexto no impide consultar la evidencia', () => {
    vinculacionMock.contextoIndicador.and.returnValue(throwError(() => ({ status: 403 })));
    crear();

    expect(texto()).toContain('Memoria anual');
    expect(texto()).toContain('No tiene permisos para consultar el contexto');
    expect(component.error).toBe('');
  });

  it('sin correspondencia confirmada la evidencia se consulta normalmente', () => {
    vinculacionMock.contextoIndicador.and.returnValue(
      of({ origen: { nivel: 'indicador', id: 7, texto: 'Indicador 7' }, correspondencias: [] })
    );
    crear();

    expect(texto()).toContain('Memoria anual');
    expect(texto()).toContain('Sin correspondencia confirmada.');
    expect(fixture.nativeElement.querySelectorAll('.marco-badge-confirmada').length).toBe(0);
  });
});
