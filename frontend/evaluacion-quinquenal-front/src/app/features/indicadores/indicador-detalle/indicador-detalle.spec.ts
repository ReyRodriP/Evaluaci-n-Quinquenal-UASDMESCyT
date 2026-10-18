import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap } from '@angular/router';
import { of, Subject, throwError } from 'rxjs';
import { ToastrService } from 'ngx-toastr';

import { IndicadorDetalle } from './indicador-detalle';
import { VinculacionService } from '../../../core/services/vinculacion.service';
import { CatalogoService } from '../../../core/services/catalogo.service';
import { EvaluacionService } from '../../../core/services/evaluacion.service';
import { PermisosService } from '../../../core/services/permisos.service';

describe('IndicadorDetalle', () => {
  let component: IndicadorDetalle;
  let fixture: ComponentFixture<IndicadorDetalle>;

  const vinculacionMock = {
    contextoIndicador: jasmine.createSpy('contextoIndicador'),
    crearCorrespondencia: jasmine.createSpy('crearCorrespondencia'),
    confirmarCorrespondencia: jasmine.createSpy('confirmarCorrespondencia'),
    rechazarCorrespondencia: jasmine.createSpy('rechazarCorrespondencia'),
    desconfirmarCorrespondencia: jasmine.createSpy('desconfirmarCorrespondencia'),
  };

  const catalogoMock = {
    listarVersiones: jasmine.createSpy('listarVersiones'),
    listarDimensiones: jasmine.createSpy('listarDimensiones'),
    listarComponentes: jasmine.createSpy('listarComponentes'),
    listarCriterios: jasmine.createSpy('listarCriterios'),
    listarEstandares: jasmine.createSpy('listarEstandares'),
    listarIndicadores: jasmine.createSpy('listarIndicadores'),
  };

  const evaluacionMock = {
    obtenerIndicador: jasmine.createSpy('obtenerIndicador'),
  };

  const permisosMock = {
    esSuperuser: false,
    tienePermiso: jasmine.createSpy('tienePermiso'),
    tieneGrupo: jasmine.createSpy('tieneGrupo'),
  };

  const toastMock = {
    success: jasmine.createSpy('success'),
    error: jasmine.createSpy('error'),
  };

  function corr(overrides: any = {}): any {
    return {
      id: 1,
      estado: 'propuesta',
      procedencia: 'manual',
      version_marco: { id: 1, nombre: 'EQ 2019', slug: 'eq', activo: true },
      origen: { nivel: 'indicador', id: 7, texto: 'I-7' },
      destino: { nivel: 'estandar', id: 3, texto: 'D.C.05.E03' },
      creado_por: 'ana',
      fecha_creacion: '2026-10-01T10:00:00Z',
      confirmado_por: null,
      fecha_confirmacion: null,
      rechazado_por: null,
      fecha_rechazo: null,
      comentario: '',
      ...overrides,
    };
  }

  function contexto(...correspondencias: any[]): any {
    return {
      origen: { nivel: 'indicador', id: 7, texto: 'I-7' },
      correspondencias,
    };
  }

  beforeEach(async () => {
    Object.values(vinculacionMock).forEach((spy) => spy.calls.reset());
    Object.values(catalogoMock).forEach((spy) => spy.calls.reset());
    evaluacionMock.obtenerIndicador.calls.reset();
    permisosMock.tienePermiso.calls.reset();
    permisosMock.tieneGrupo.calls.reset();
    toastMock.success.calls.reset();
    toastMock.error.calls.reset();

    vinculacionMock.contextoIndicador.and.returnValue(of(contexto()));
    vinculacionMock.crearCorrespondencia.and.returnValue(of(corr({ id: 99 })));
    vinculacionMock.confirmarCorrespondencia.and.returnValue(of(corr({ estado: 'confirmada' })));
    vinculacionMock.rechazarCorrespondencia.and.returnValue(of(corr({ estado: 'rechazada' })));
    vinculacionMock.desconfirmarCorrespondencia.and.returnValue(of(corr({ estado: 'propuesta' })));
    catalogoMock.listarVersiones.and.returnValue(of([]));
    catalogoMock.listarDimensiones.and.returnValue(of([]));
    catalogoMock.listarComponentes.and.returnValue(of([]));
    catalogoMock.listarCriterios.and.returnValue(of([]));
    catalogoMock.listarEstandares.and.returnValue(of([]));
    catalogoMock.listarIndicadores.and.returnValue(of([]));
    evaluacionMock.obtenerIndicador.and.returnValue(of({ id: 7, nombre: 'I-7', criterio_nombre: 'Criterio A' }));
    permisosMock.esSuperuser = false;
    permisosMock.tienePermiso.and.returnValue(false);
    permisosMock.tieneGrupo.and.returnValue(false);

    await TestBed.configureTestingModule({
      imports: [IndicadorDetalle],
      providers: [
        { provide: VinculacionService, useValue: vinculacionMock },
        { provide: CatalogoService, useValue: catalogoMock },
        { provide: EvaluacionService, useValue: evaluacionMock },
        { provide: PermisosService, useValue: permisosMock },
        { provide: ToastrService, useValue: toastMock },
        { provide: ActivatedRoute, useValue: { snapshot: { paramMap: convertToParamMap({ id: '7' }) } } },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(IndicadorDetalle);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('crea el componente y carga el indicador con su contexto', () => {
    expect(component).toBeTruthy();
    expect(evaluacionMock.obtenerIndicador).toHaveBeenCalledWith(7);
    expect(vinculacionMock.contextoIndicador).toHaveBeenCalledTimes(1);
    expect(component.indicador.nombre).toBe('I-7');
  });

  it('muestra estado vacio cuando no hay correspondencias', () => {
    const texto = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(texto).toContain('aún no tiene correspondencias');
  });

  it('muestra error 403 al fallar el contexto y permite reintentar', () => {
    vinculacionMock.contextoIndicador.and.returnValue(throwError(() => ({ status: 403 })));
    component.cargarTodo();
    fixture.detectChanges();
    const texto = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(component.errorCarga).toContain('No tiene permisos');
    expect(texto).toContain('No tiene permisos');

    vinculacionMock.contextoIndicador.and.returnValue(of(contexto()));
    evaluacionMock.obtenerIndicador.calls.reset();
    const boton = Array.from((fixture.nativeElement as HTMLElement).querySelectorAll('button')).find(
      (b) => b.textContent?.trim() === 'Reintentar'
    );
    boton?.click();
    fixture.detectChanges();
    expect(evaluacionMock.obtenerIndicador).toHaveBeenCalledTimes(1);
    expect(component.errorCarga).toBe('');
  });

  it('muestra tarjetas con badge de estado para cada correspondencia', () => {
    vinculacionMock.contextoIndicador.and.returnValue(of(contexto(corr(), corr({ id: 2, estado: 'confirmada' }))));
    component.cargarContexto();
    fixture.detectChanges();
    const tarjetas = (fixture.nativeElement as HTMLElement).querySelectorAll('.tarjeta-correspondencia');
    expect(tarjetas.length).toBe(2);
    expect(tarjetas[0].getAttribute('data-estado')).toBe('propuesta');
    expect(tarjetas[1].getAttribute('data-estado')).toBe('confirmada');
    expect((fixture.nativeElement as HTMLElement).textContent).toContain('D.C.05.E03');
  });

  it('oculta creacion y acciones sin permisos de escritura', () => {
    vinculacionMock.contextoIndicador.and.returnValue(of(contexto(corr())));
    component.cargarContexto();
    fixture.detectChanges();
    const botones = Array.from((fixture.nativeElement as HTMLElement).querySelectorAll('button')).map((b) =>
      b.textContent?.trim()
    );
    expect(botones).not.toContain('Proponer correspondencia');
    expect(botones).not.toContain('Confirmar');
    expect(botones).not.toContain('Rechazar…');
  });

  it('muestra acciones de transicion con change_correspondencia y grupo de escritura', () => {
    permisosMock.tienePermiso.and.callFake((c: string) => c === 'vinculacion.change_correspondencia');
    permisosMock.tieneGrupo.and.callFake((g: string) => g === 'Coordinador Quinquenal');
    vinculacionMock.contextoIndicador.and.returnValue(of(contexto(corr())));
    component.cargarContexto();
    fixture.detectChanges();
    const botones = Array.from((fixture.nativeElement as HTMLElement).querySelectorAll('button')).map((b) =>
      b.textContent?.trim()
    );
    expect(botones).toContain('Confirmar');
    expect(botones).toContain('Rechazar…');
    expect(botones).not.toContain('Proponer correspondencia');
  });

  it('confirmar llama al servicio y recarga el contexto', () => {
    const item = corr();
    component.correspondencias = [item];
    component.confirmar(item);
    expect(vinculacionMock.confirmarCorrespondencia).toHaveBeenCalledTimes(1);
    expect(vinculacionMock.confirmarCorrespondencia).toHaveBeenCalledWith(1);
    expect(vinculacionMock.contextoIndicador).toHaveBeenCalledTimes(2);
    expect(toastMock.success).toHaveBeenCalled();
  });

  it('previene doble envio en confirmar', () => {
    const pendiente = new Subject<any>();
    vinculacionMock.confirmarCorrespondencia.and.returnValue(pendiente.asObservable());
    const item = corr();
    component.confirmar(item);
    component.confirmar(item);
    expect(vinculacionMock.confirmarCorrespondencia).toHaveBeenCalledTimes(1);
    pendiente.next(item);
    pendiente.complete();
  });

  it('rechazar exige comentario y no llama al servicio sin el', () => {
    const item = corr();
    component.iniciarTransicion(item, 'rechazar');
    component.ejecutarTransicion();
    expect(vinculacionMock.rechazarCorrespondencia).not.toHaveBeenCalled();
    expect(component.errorTransicion).toContain('comentario es obligatorio');
  });

  it('rechazar envia el comentario y recarga el contexto', () => {
    const item = corr();
    component.iniciarTransicion(item, 'rechazar');
    component.formTransicion!.comentario = 'No corresponde';
    component.ejecutarTransicion();
    expect(vinculacionMock.rechazarCorrespondencia).toHaveBeenCalledWith(1, 'No corresponde');
    expect(vinculacionMock.contextoIndicador).toHaveBeenCalledTimes(2);
    expect(component.formTransicion).toBeNull();
    expect(toastMock.success).toHaveBeenCalled();
  });

  it('abrirFormCreacion carga las versiones del marco', () => {
    const versiones = [{ id: 1, nombre: 'EQ 2019', slug: 'eq', activo: true }];
    catalogoMock.listarVersiones.and.returnValue(of(versiones));
    component.abrirFormCreacion();
    expect(component.mostrandoFormCreacion).toBe(true);
    expect(catalogoMock.listarVersiones).toHaveBeenCalledTimes(1);
    expect(component.versiones.length).toBe(1);
  });

  it('crear envia el payload con la cascada version-dimension-estandar completa', () => {
    catalogoMock.listarVersiones.and.returnValue(of([{ id: 1, nombre: 'EQ 2019', slug: 'eq', activo: true }]));
    catalogoMock.listarDimensiones.and.returnValue(of([{ id: 15, codigo: 'VI', nombre: 'Docencia' }]));
    catalogoMock.listarComponentes.and.returnValue(of([{ id: 2, codigo_completo: 'D.C', nombre: 'Curricular' }]));
    catalogoMock.listarCriterios.and.returnValue(of([{ id: 5, codigo_completo: 'D.C.05', nombre: 'Criterio 5' }]));
    catalogoMock.listarEstandares.and.returnValue(of([{ id: 3, codigo_completo: 'D.C.05.E03' }]));

    component.abrirFormCreacion();
    component.versionSeleccionada = '1';
    component.onVersionChange();
    component.nivelDestino = 'estandar';
    component.dimensionSeleccionada = '15';
    component.onDimensionChange();
    component.componenteSeleccionado = '2';
    component.onComponenteChange();
    component.criterioSeleccionado = '5';
    component.onCriterioChange();
    component.estandarSeleccionado = '3';
    component.comentarioCreacion = 'Vinculo propuesto';

    expect(component.destinoListo).toBe(true);

    component.crear();
    expect(vinculacionMock.crearCorrespondencia).toHaveBeenCalledWith({
      version_marco: 1,
      indicador_op: 7,
      comentario: 'Vinculo propuesto',
      estandar: 3,
    });
    expect(toastMock.success).toHaveBeenCalled();
    expect(component.mostrandoFormCreacion).toBe(false);
  });

  it('muestra el error del backend en la creacion y mantiene el formulario abierto', () => {
    vinculacionMock.crearCorrespondencia.and.returnValue(throwError(() => ({ status: 403 })));
    catalogoMock.listarVersiones.and.returnValue(of([{ id: 1, nombre: 'EQ 2019', slug: 'eq', activo: true }]));
    catalogoMock.listarDimensiones.and.returnValue(of([{ id: 15, codigo: 'VI', nombre: 'Docencia' }]));
    component.abrirFormCreacion();
    component.versionSeleccionada = '1';
    component.onVersionChange();
    component.dimensionSeleccionada = '15';
    component.estandarSeleccionado = '3';
    component.crear();
    expect(component.errorCreacion).toContain('No tiene permisos');
    expect(component.mostrandoFormCreacion).toBe(true);
    expect(component.creando).toBe(false);
  });
});
