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
    subirVersionEvidencia: jasmine.createSpy('subirVersionEvidencia'),
    editarVersionEvidencia: jasmine.createSpy('editarVersionEvidencia'),
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
    evidenciasMock.subirVersionEvidencia.calls.reset();
    evidenciasMock.editarVersionEvidencia.calls.reset();
    evaluacionMock.obtenerIndicador.calls.reset();
    vinculacionMock.contextoIndicador.calls.reset();
    catalogoMock.obtenerIndicadorMarco.calls.reset();

    evidenciasMock.detalleEvidencia.and.returnValue(of(evidencia()));
    evidenciasMock.subirVersionEvidencia.and.returnValue(of({}));
    evidenciasMock.editarVersionEvidencia.and.returnValue(of({}));
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

  it('retira el panel de aprobación si el backend deja de autorizar la consulta', () => {
    evidenciasMock.detalleEvidencia.and.returnValue(of(evidencia({ puede_cambiar_estado: true })));
    crear();
    expect(texto()).toContain('Revisar evidencia');
    evidenciasMock.detalleEvidencia.and.returnValue(throwError(() => ({ status: 404 })));
    component.cargarDetalle(3);
    fixture.detectChanges();
    expect(component.evidencia).toBeNull();
    expect(texto()).not.toContain('Revisar evidencia');
    expect(texto()).toContain('No se pudo cargar el detalle');
  });

  it('presenta la ruta de una evidencia del marco sin enviar su ID al contexto operativo', () => {
    const datos = evidencia();
    datos.asignacion_info = {
      ...datos.asignacion_info, indicador: null, indicador_marco: 7, tipo_origen: 'marco',
      ruta_marco: {
        version: { id: 1, nombre: 'Marco técnico', slug: 'marco-tecnico', activo: false },
        dimension: { id: 5, codigo: 'VI', nombre: 'Personal académico' },
        componente: { id: 6, codigo: '6.1', nombre: 'Carrera académica' },
        criterio: { id: 11, codigo: '6.1.1', nombre: 'Criterio del marco' },
        estandar: { id: 20, codigo: '6.1.1.2', nombre: 'Estándar técnico' },
        indicador: { id: 7, codigo: '6.1.1.2-IND-01', nombre: 'Indicador del marco', orden: 1, codigo_sintetico: true },
      },
    };
    evidenciasMock.detalleEvidencia.and.returnValue(of(datos));
    crear();
    expect(texto()).toContain('Personal académico');
    expect(texto()).toContain('Asignación directa al marco');
    expect(vinculacionMock.contextoIndicador).not.toHaveBeenCalled();
    expect(fixture.nativeElement.querySelector('app-marco-relacionado')).toBeNull();
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

  it('rechaza una extension no permitida sin disparar la peticion de subida', () => {
    evidenciasMock.detalleEvidencia.and.returnValue(of(evidencia({ puede_subir_version: true })));
    crear();
    component.nuevoArchivo = null;
    component.archivoError = '';

    const input = document.createElement('input');
    input.type = 'file';
    const malicious = new File(['MZ'], 'malware.exe', { type: 'application/octet-stream' });
    Object.defineProperty(input, 'files', { value: [malicious], configurable: true });

    component.onFileChange({ target: input } as unknown as Event);

    expect(component.archivoError).toContain('no permitida');
    expect(component.nuevoArchivo).toBeFalsy();
    expect(evidenciasMock.subirVersionEvidencia).not.toHaveBeenCalled();
  });

  it('rechaza un archivo que supera el limite de tamano sin disparar la peticion de subida', () => {
    evidenciasMock.detalleEvidencia.and.returnValue(of(evidencia({ puede_subir_version: true })));
    crear();
    component.nuevoArchivo = null;
    component.archivoError = '';

    const input = document.createElement('input');
    input.type = 'file';
    const big = new File(['contenido'], 'grande.pdf', { type: 'application/pdf' });
    Object.defineProperty(big, 'size', { value: component.MAX_ARCHIVO_MB * 1024 * 1024 + 1, configurable: true });
    Object.defineProperty(input, 'files', { value: [big], configurable: true });

    component.onFileChange({ target: input } as unknown as Event);

    expect(component.archivoError).toContain('supera el tamaño máximo');
    expect(component.nuevoArchivo).toBeFalsy();
    expect(evidenciasMock.subirVersionEvidencia).not.toHaveBeenCalled();
  });

  it('acepta una extension valida y permite subir la version', () => {
    evidenciasMock.detalleEvidencia.and.returnValue(of(evidencia({ puede_subir_version: true })));
    crear();
    component.nuevoArchivo = null;
    component.archivoError = '';

    const input = document.createElement('input');
    input.type = 'file';
    const ok = new File(['%PDF-1.4'], 'informe.pdf', { type: 'application/pdf' });
    Object.defineProperty(input, 'files', { value: [ok], configurable: true });

    component.onFileChange({ target: input } as unknown as Event);

    expect(component.archivoError).toBe('');
    expect(component.nuevoArchivo).toBeTruthy();

    component.subirVersion();
    expect(evidenciasMock.subirVersionEvidencia).toHaveBeenCalled();
  });

  it('rechaza una extension no permitida al editar una version', () => {
    evidenciasMock.detalleEvidencia.and.returnValue(of(evidencia({ puede_subir_version: true })));
    crear();
    component.versionEditFile = null;
    component.versionEditFileError = '';

    const input = document.createElement('input');
    input.type = 'file';
    const malicious = new File(['MZ'], 'malware.exe', { type: 'application/octet-stream' });
    Object.defineProperty(input, 'files', { value: [malicious], configurable: true });

    component.onVersionEditFileChange({ target: input } as unknown as Event);

    expect(component.versionEditFileError).toContain('no permitida');
    expect(component.versionEditFile).toBeFalsy();
    expect(evidenciasMock.editarVersionEvidencia).not.toHaveBeenCalled();
  });
});
