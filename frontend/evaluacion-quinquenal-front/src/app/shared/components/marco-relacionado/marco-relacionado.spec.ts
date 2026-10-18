import { ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { Subject, throwError, of } from 'rxjs';
import { VinculacionService } from '../../../core/services/vinculacion.service';
import { EvaluacionService } from '../../../core/services/evaluacion.service';
import { CatalogoService } from '../../../core/services/catalogo.service';
import { PermisosService } from '../../../core/services/permisos.service';
import { MarcoRelacionado } from './marco-relacionado';

describe('MarcoRelacionado', () => {
  let component: MarcoRelacionado;
  let fixture: ComponentFixture<MarcoRelacionado>;

  const vinculacionMock = {
    contextoIndicador: jasmine.createSpy('contextoIndicador'),
  };

  const evaluacionMock = {
    obtenerIndicador: jasmine.createSpy('obtenerIndicador'),
  };

  const catalogoMock = {
    obtenerIndicadorMarco: jasmine.createSpy('obtenerIndicadorMarco'),
  };

  const permisosMock = {
    esSuperuser: false,
    tieneGrupo: jasmine.createSpy('tieneGrupo'),
    tieneAlgunPermiso: jasmine.createSpy('tieneAlgunPermiso'),
  };

  function contexto(...correspondencias: any[]): any {
    return {
      origen: { nivel: 'indicador', id: 7, texto: 'Indicador 7' },
      correspondencias,
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

  function crear(indicadorId = 7): void {
    fixture.componentRef.setInput('indicadorId', indicadorId);
    fixture.detectChanges();
  }

  function texto(): string {
    return (fixture.nativeElement as HTMLElement).textContent ?? '';
  }

  beforeEach(async () => {
    vinculacionMock.contextoIndicador.calls.reset();
    evaluacionMock.obtenerIndicador.calls.reset();
    catalogoMock.obtenerIndicadorMarco.calls.reset();
    permisosMock.tieneGrupo.calls.reset();
    permisosMock.tieneAlgunPermiso.calls.reset();

    vinculacionMock.contextoIndicador.and.returnValue(of(contexto()));
    evaluacionMock.obtenerIndicador.and.returnValue(of({ id: 7, nombre: 'Indicador 7', criterio_nombre: 'Criterio A' }));
    catalogoMock.obtenerIndicadorMarco.and.returnValue(of({ codigo: '6.1.1.1-IND-01', codigo_sintetico: true }));
    permisosMock.esSuperuser = false;
    permisosMock.tieneGrupo.and.returnValue(false);
    permisosMock.tieneAlgunPermiso.and.returnValue(false);

    await TestBed.configureTestingModule({
      imports: [MarcoRelacionado, RouterTestingModule],
      providers: [
        { provide: VinculacionService, useValue: vinculacionMock },
        { provide: EvaluacionService, useValue: evaluacionMock },
        { provide: CatalogoService, useValue: catalogoMock },
        { provide: PermisosService, useValue: permisosMock },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(MarcoRelacionado);
    component = fixture.componentInstance;
  });

  it('muestra la correspondencia confirmada con destino, version y estado', () => {
    vinculacionMock.contextoIndicador.and.returnValue(of(contexto(corr())));
    crear(7);

    expect(texto()).toContain('Indicador operativo');
    expect(texto()).toContain('Indicador 7');
    expect(texto()).toContain('Criterio operativo');
    expect(texto()).toContain('Criterio A');
    expect(texto()).toContain('Correspondencia confirmada');
    expect(texto()).toContain('6.1.1.1');
    expect(texto()).toContain('Estándar');
    expect(texto()).toContain('EQ-SIDACES 2019');
    expect(fixture.nativeElement.querySelectorAll('.marco-badge-confirmada').length).toBe(1);
  });

  it('no presenta una propuesta como vinculo vigente', () => {
    vinculacionMock.contextoIndicador.and.returnValue(
      of(contexto(corr({ id: 9, estado: 'propuesta', destino: { nivel: 'dimension', id: 6, texto: 'VI PERSONAL ACADÉMICO' } })))
    );
    crear(7);

    expect(fixture.nativeElement.querySelectorAll('.marco-badge-confirmada').length).toBe(0);
    expect(texto()).toContain('Sin correspondencia confirmada.');
    expect(texto()).toContain('propuesta(s) pendiente(s)');
    expect(texto()).not.toContain('VI PERSONAL ACADÉMICO');
    expect(texto()).not.toContain('Correspondencia confirmada');
  });

  it('muestra error 403 sin opcion de reintentar', () => {
    vinculacionMock.contextoIndicador.and.returnValue(throwError(() => ({ status: 403 })));
    crear(7);

    expect(component.errorCarga).toContain('No tiene permisos');
    expect(texto()).toContain('No tiene permisos para consultar el contexto de correspondencias');
    const botones = Array.from((fixture.nativeElement as HTMLElement).querySelectorAll('button')).map((b) =>
      b.textContent?.trim()
    );
    expect(botones).not.toContain('Reintentar');
  });

  it('error recuperable permite reintentar y recarga el contexto', () => {
    vinculacionMock.contextoIndicador.and.returnValue(throwError(() => ({ status: 500 })));
    crear(7);
    expect(texto()).toContain('No se pudo cargar el contexto de correspondencias');

    vinculacionMock.contextoIndicador.and.returnValue(of(contexto(corr())));
    fixture.detectChanges();
    const boton = Array.from((fixture.nativeElement as HTMLElement).querySelectorAll('button')).find(
      (b) => b.textContent?.trim() === 'Reintentar'
    );
    boton?.click();
    fixture.detectChanges();

    expect(vinculacionMock.contextoIndicador).toHaveBeenCalledTimes(2);
    expect(component.errorCarga).toBe('');
    expect(texto()).toContain('Correspondencia confirmada');
  });

  it('contexto fuera de alcance muestra estado vacio sin error', () => {
    vinculacionMock.contextoIndicador.and.returnValue(throwError(() => ({ status: 404 })));
    crear(7);

    expect(component.sinAlcance).toBe(true);
    expect(texto()).toContain('No hay contexto EQ-SIDACES disponible');
    expect(component.errorCarga).toBe('');
  });

  it('muestra el enlace de gestion solo para roles con permiso', () => {
    vinculacionMock.contextoIndicador.and.returnValue(of(contexto(corr())));
    crear(7);
    expect(fixture.nativeElement.querySelector('a.marco-gestionar')).toBeNull();

    permisosMock.tieneGrupo.and.callFake((g: string) => g === 'Coordinador Quinquenal');
    permisosMock.tieneAlgunPermiso.and.returnValue(true);
    fixture.detectChanges();

    const enlace = fixture.nativeElement.querySelector('a.marco-gestionar') as HTMLAnchorElement | null;
    expect(enlace).toBeTruthy();
    expect(enlace?.getAttribute('href')).toBe('/indicadores/7/detalle');
  });

  it('refresca el contexto cuando el estado de la correspondencia cambia', () => {
    vinculacionMock.contextoIndicador.and.returnValue(
      of(contexto(corr({ id: 5, estado: 'propuesta' })))
    );
    crear(7);
    expect(texto()).toContain('Sin correspondencia confirmada.');

    vinculacionMock.contextoIndicador.and.returnValue(of(contexto(corr({ id: 5, estado: 'confirmada' }))));
    component.cargar();
    fixture.detectChanges();

    expect(texto()).toContain('Correspondencia confirmada');
    expect(fixture.nativeElement.querySelectorAll('.marco-badge-confirmada').length).toBe(1);
  });

  it('muestra la naturaleza sintetica del destino indicador del marco', () => {
    vinculacionMock.contextoIndicador.and.returnValue(
      of(contexto(corr({ destino: { nivel: 'indicador_marco', id: 42, texto: '6.1.1.1-IND-01' } })))
    );
    crear(7);

    expect(catalogoMock.obtenerIndicadorMarco).toHaveBeenCalledWith(42);
    expect(texto()).toContain('Código sintético (no oficial)');
  });

  it('no consulta el catalogo para destinos que no son indicador del marco', () => {
    vinculacionMock.contextoIndicador.and.returnValue(of(contexto(corr({ destino: { nivel: 'estandar', id: 3, texto: '6.1.1.1' } }))));
    crear(7);

    expect(catalogoMock.obtenerIndicadorMarco).not.toHaveBeenCalled();
    expect(texto()).not.toContain('Código sintético');
  });

  it('el contexto sigue visible si falla la carga del indicador operativo', () => {
    evaluacionMock.obtenerIndicador.and.returnValue(throwError(() => ({ status: 500 })));
    vinculacionMock.contextoIndicador.and.returnValue(of(contexto(corr())));
    crear(7);

    expect(texto()).toContain('Correspondencia confirmada');
    expect(texto()).not.toContain('Criterio operativo');
    expect(component.criterioOperativo).toBe('');
  });

  it('muestra estado de carga mientras responde el contexto', () => {
    vinculacionMock.contextoIndicador.and.returnValue(new Subject<any>().asObservable());
    crear(7);

    expect(component.cargando).toBe(true);
    expect(texto()).toContain('Cargando contexto EQ-SIDACES');
  });
});
