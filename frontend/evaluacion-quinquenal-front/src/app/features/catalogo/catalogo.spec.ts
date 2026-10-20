import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { Catalogo } from './catalogo';
import { AuthService } from '../../features/auth/services/auth-service';
import { PermisosService } from '../../core/services/permisos.service';
import { environment } from '../../../environments/environment';

describe('Catalogo', () => {
  let component: Catalogo;
  let fixture: ComponentFixture<Catalogo>;
  let httpMock: HttpTestingController;
  const base = `${environment.apiUrl}/catalogo`;
  const vincBase = `${environment.apiUrl}/vinculacion/correspondencias`;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Catalogo, RouterTestingModule],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();

    httpMock = TestBed.inject(HttpTestingController);
    fixture = TestBed.createComponent(Catalogo);
    component = fixture.componentInstance;
  });

  afterEach(() => {
    httpMock.verify();
  });

  function resolverVersiones() {
    httpMock.expectOne(`${base}/versiones/`).flush({
      count: 1,
      results: [
        {
          id: 1,
          slug: 'eq-sidaces-2019-res27-2019',
          nombre: 'EQ-SIDACES-2019-Res27-2019',
          activo: false,
        },
      ],
    });
  }

  it('debe crear el componente', () => {
    fixture.detectChanges();
    resolverVersiones();
    expect(component).toBeTruthy();
  });

  it('carga las versiones al iniciar y muestra aviso de provisionalidad', () => {
    fixture.detectChanges();
    resolverVersiones();
    fixture.detectChanges();
    const texto: string = fixture.nativeElement.textContent;
    expect(component.nivelActual).toBe('versiones');
    expect(texto).toContain('no constituyen un catálogo');
    expect(texto).toContain('EQ-SIDACES-2019-Res27-2019');
    expect(texto).toContain('Inactiva');
  });

  it('al seleccionar una version navega a dimensiones con el filtro version', () => {
    fixture.detectChanges();
    resolverVersiones();
    component.seleccionar({
      id: 1,
      slug: 'eq-sidaces-2019-res27-2019',
      activo: false,
    });
    expect(component.nivelActual).toBe('dimensiones');
    const req = httpMock.expectOne(
      (r) =>
        r.url === `${base}/dimensiones/` &&
        r.params.get('version') === 'eq-sidaces-2019-res27-2019'
    );
    req.flush({ results: [{ id: 15, codigo: 'VI', nombre: 'PERSONAL ACADÉMICO' }] });
    expect(component.items.length).toBe(1);
  });

  it('marca estado de error y permite reintentar', () => {
    fixture.detectChanges();
    resolverVersiones();
    component.seleccionar({ id: 1, slug: 'eq-sidaces-2019-res27-2019', activo: false });
    httpMock.expectOne((r) => r.url === `${base}/dimensiones/`).error(new ProgressEvent('error'));
    expect(component.error).toBeTruthy();
    expect(component.items).toEqual([]);
    component.cargar();
    httpMock
      .expectOne((r) => r.url === `${base}/dimensiones/`)
      .flush({ results: [{ id: 15, codigo: 'VI', nombre: 'PERSONAL ACADÉMICO' }] });
    expect(component.error).toBeNull();
    expect(component.items.length).toBe(1);
  });

  it('volver al inicio recarga versiones', () => {
    fixture.detectChanges();
    resolverVersiones();
    component.seleccionar({ id: 1, slug: 'eq-sidaces-2019-res27-2019', activo: false });
    httpMock.expectOne((r) => r.url === `${base}/dimensiones/`).flush({ results: [] });
    component.volverAInicio();
    expect(component.nivelActual).toBe('versiones');
    httpMock.expectOne(`${base}/versiones/`).flush({ results: [] });
    expect(component.items).toEqual([]);
  });

  it('un nivel vacio muestra mensaje de lista vacia', () => {
    fixture.detectChanges();
    resolverVersiones();
    component.seleccionar({ id: 1, slug: 'eq-sidaces-2019-res27-2019', activo: false });
    httpMock.expectOne((r) => r.url === `${base}/dimensiones/`).flush({ results: [] });
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('No hay registros en este nivel');
  });

  it('el boton exportar aparece solo con una version seleccionada', () => {
    fixture.detectChanges();
    resolverVersiones();
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('.btn-exportar')).toBeNull();
    component.seleccionar({ id: 1, slug: 'eq-sidaces-2019-res27-2019', activo: false });
    httpMock.expectOne((r) => r.url === `${base}/dimensiones/`).flush({ results: [] });
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('.btn-exportar')).toBeTruthy();
  });

  it('exportar descarga el CSV de la version seleccionada', () => {
    fixture.detectChanges();
    resolverVersiones();
    component.seleccionar({ id: 1, slug: 'eq-sidaces-2019-res27-2019', activo: false });
    httpMock.expectOne((r) => r.url === `${base}/dimensiones/`).flush({ results: [] });
    const blob = new Blob(['nivel,version\n']);
    const descarga = spyOn(component, 'descargar');
    component.exportar();
    const req = httpMock.expectOne(
      (r) =>
        r.url === `${base}/exportar/` &&
        r.params.get('version') === 'eq-sidaces-2019-res27-2019'
    );
    expect(req.request.responseType).toBe('blob');
    req.flush(blob);
    expect(component.exportando).toBeFalse();
    expect(descarga).toHaveBeenCalledOnceWith(
      blob,
      'arbol_eq_sidaces_eq-sidaces-2019-res27-2019.csv'
    );
  });

  it('un error de exportacion muestra mensaje y permite reintentar', () => {
    fixture.detectChanges();
    resolverVersiones();
    component.seleccionar({ id: 1, slug: 'eq-sidaces-2019-res27-2019', activo: false });
    httpMock.expectOne((r) => r.url === `${base}/dimensiones/`).flush({ results: [] });
    component.exportar();
    httpMock.expectOne((r) => r.url === `${base}/exportar/`).error(new ProgressEvent('error'));
    expect(component.errorExport).toBeTruthy();
    expect(component.exportando).toBeFalse();
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('No se pudo exportar');
    const descarga = spyOn(component, 'descargar');
    component.exportar();
    httpMock.expectOne((r) => r.url === `${base}/exportar/`).flush(new Blob(['x']));
    expect(descarga).toHaveBeenCalled();
    expect(component.errorExport).toBeNull();
  });

  function navegarAIndicadores(): void {
    fixture.detectChanges();
    resolverVersiones();
    component.seleccionar({ id: 1, slug: 'eq-sidaces-2019-res27-2019', activo: false });
    httpMock
      .expectOne((r) => r.url === `${base}/dimensiones/`)
      .flush({ results: [{ id: 15, codigo: 'VI', nombre: 'PERSONAL ACADÉMICO' }] });
    component.seleccionar({ id: 15, codigo: 'VI' });
    httpMock
      .expectOne((r) => r.url === `${base}/componentes/`)
      .flush({ results: [{ id: 21, codigo: '6.1', codigo_completo: '6.1', nombre: 'Administración' }] });
    component.seleccionar({ id: 21 });
    httpMock
      .expectOne((r) => r.url === `${base}/criterios/`)
      .flush({ results: [{ id: 31, codigo: '6.1.1', codigo_completo: '6.1.1', nombre: 'Criterio' }] });
    component.seleccionar({ id: 31 });
    httpMock
      .expectOne((r) => r.url === `${base}/estandares/`)
      .flush({ results: [{ id: 41, codigo_completo: '6.1.1.1', nombre: 'Estándar 1' }] });
    component.seleccionar({ id: 41 });
    httpMock
      .expectOne((r) => r.url === `${base}/indicadores/`)
      .flush({
        results: [
          {
            id: 51,
            codigo_completo: '6.1.1.1-IND-01',
            codigo_sintetico: true,
            estado_revision: 'confirmado',
            redaccion_oficial: 'Existe el plan de gestión',
            estandar_codigo: '6.1.1.1',
          },
        ],
      });
  }

  const corrConfirmada = {
    id: 7,
    estado: 'confirmada',
    origen: { nivel: 'indicador', id: 90, texto: 'Indicador 90' },
    destino: { nivel: 'indicador_marco', id: 51, texto: '6.1.1.1-IND-01' },
    version_marco: { id: 1, nombre: 'EQ 2026', slug: 'eq-2026', activo: true },
    fecha_confirmacion: '2026-10-01T00:00:00Z',
    confirmado_por: 'maria',
  };

  const corrPropuesta = {
    id: 8,
    estado: 'propuesta',
    origen: { nivel: 'criterio', id: 31, texto: 'Criterio 6.1.1' },
    destino: { nivel: 'indicador_marco', id: 51, texto: '6.1.1.1-IND-01' },
    version_marco: { id: 1, nombre: 'EQ 2026', slug: 'eq-2026', activo: true },
    fecha_confirmacion: null,
    confirmado_por: null,
  };

  function resolverPanel(modo: 'ok' | 'sin-permisos' | 'error' | 'vacio' = 'ok'): void {
    const confirmadas = httpMock.expectOne(
      (r) =>
        r.url === `${vincBase}/` &&
        r.params.get('estado') === 'confirmada' &&
        r.params.get('indicador_marco') === '51'
    );
    const propuestas = httpMock.expectOne(
      (r) =>
        r.url === `${vincBase}/` &&
        r.params.get('estado') === 'propuesta' &&
        r.params.get('indicador_marco') === '51'
    );
    if (modo === 'sin-permisos') {
      confirmadas.error(new ProgressEvent('error'), { status: 403 } as any);
      propuestas.flush({ count: 0, results: [] });
    } else if (modo === 'error') {
      confirmadas.error(new ProgressEvent('error'), { status: 500 } as any);
      propuestas.flush({ count: 0, results: [] });
    } else if (modo === 'vacio') {
      confirmadas.flush({ count: 0, results: [] });
      propuestas.flush({ count: 0, results: [] });
    } else {
      confirmadas.flush({ count: 1, results: [corrConfirmada] });
      propuestas.flush({ count: 1, results: [corrPropuesta] });
    }
  }

  function resolverAsignaciones(): void {
    httpMock
      .expectOne(
        (r) =>
          r.url === `${environment.apiUrl}/asignaciones/` && r.params.get('indicador') === '90'
      )
      .flush({
        count: 2,
        results: [
          {
            id: 3,
            unidad_responsable_nombre: 'Unidad A',
            periodo_nombre: 'Período 1',
            estado_display: 'Pendiente',
          },
          {
            id: 4,
            unidad_responsable_nombre: 'Unidad A',
            periodo_nombre: 'Período 1',
            estado_display: 'En progreso',
          },
        ],
      });
  }

  it('al seleccionar un indicador abre el panel con correspondencias y asignaciones de origen', () => {
    navegarAIndicadores();
    component.seleccionar({ id: 51, codigo_completo: '6.1.1.1-IND-01' });

    expect(component.indicadorPanel?.id).toBe(51);
    resolverPanel();
    resolverAsignaciones();
    fixture.detectChanges();

    expect(component.correspondenciasConfirmadas.length).toBe(1);
    expect(component.correspondenciasPropuestas.length).toBe(1);
    expect(component.asignacionesDe(component.correspondenciasConfirmadas[0]).length).toBe(2);
    expect(component.panelError).toBe('');
    expect(component.panelSinPermiso).toBeFalse();

    const texto: string = fixture.nativeElement.textContent;
    expect(texto).toContain('Indicador del marco');
    expect(texto).toContain('6.1.1.1-IND-01');
    expect(texto).toContain('Correspondencia confirmada');
    expect(texto).toContain('Indicador 90');
    expect(texto).toContain('Unidad A');
    expect(texto).toContain('propuesta(s) pendiente(s)');
    const enlaces = Array.from(fixture.nativeElement.querySelectorAll('a[href]')).map(
      (a: any) => a.getAttribute('href') ?? ''
    );
    expect(enlaces.some((href: string) => href.includes('/asignaciones/3/detalle'))).toBeTrue();
    expect(enlaces.some((href: string) => href.includes('/asignaciones/4/detalle'))).toBeTrue();
  });

  it('un 403 en las correspondencias del panel muestra el mensaje sin permisos', () => {
    navegarAIndicadores();
    component.seleccionar({ id: 51 });
    resolverPanel('sin-permisos');
    fixture.detectChanges();

    expect(component.panelSinPermiso).toBeTrue();
    expect(component.panelError).toBe('');
    expect(fixture.nativeElement.textContent).toContain(
      'No tiene permisos para consultar las correspondencias del marco'
    );
  });

  it('un error de red en el panel muestra error recuperable con reintentar', () => {
    navegarAIndicadores();
    component.seleccionar({ id: 51 });
    resolverPanel('error');
    fixture.detectChanges();

    expect(component.panelError).toContain('No se pudieron cargar');
    const texto: string = fixture.nativeElement.textContent;
    expect(texto).toContain('No se pudieron cargar las correspondencias del marco.');

    component.cargarPanel();
    resolverPanel('ok');
    resolverAsignaciones();
    fixture.detectChanges();

    expect(component.panelError).toBe('');
    expect(component.correspondenciasConfirmadas.length).toBe(1);
  });

  it('un panel sin correspondencias muestra el estado vacio', () => {
    navegarAIndicadores();
    component.seleccionar({ id: 51 });
    resolverPanel('vacio');
    fixture.detectChanges();

    expect(component.correspondenciasConfirmadas.length).toBe(0);
    expect(component.correspondenciasPropuestas.length).toBe(0);
    expect(fixture.nativeElement.textContent).toContain(
      'Este indicador del marco no tiene correspondencias registradas'
    );
  });

  it('un origen de criterio operativo se explica y enlaza a Seguimiento sin consultar asignaciones', () => {
    navegarAIndicadores();
    component.seleccionar({ id: 51 });
    const confirmadas = httpMock.expectOne(
      (r) =>
        r.url === `${vincBase}/` &&
        r.params.get('estado') === 'confirmada' &&
        r.params.get('indicador_marco') === '51'
    );
    const propuestas = httpMock.expectOne(
      (r) =>
        r.url === `${vincBase}/` &&
        r.params.get('estado') === 'propuesta' &&
        r.params.get('indicador_marco') === '51'
    );
    confirmadas.flush({ count: 1, results: [{ ...corrConfirmada, origen: corrPropuesta.origen }] });
    propuestas.flush({ count: 0, results: [] });
    fixture.detectChanges();

    const texto: string = fixture.nativeElement.textContent;
    expect(texto).toContain('Criterio operativo');
    expect(texto).toContain('consultan desde la pantalla de Seguimiento');
    const enlaces = Array.from(fixture.nativeElement.querySelectorAll('a[href]')).map(
      (a: any) => a.getAttribute('href') ?? ''
    );
    expect(enlaces).toContain('/seguimiento');
  });

  it('cerrar el detalle limpia el panel', () => {
    navegarAIndicadores();
    component.seleccionar({ id: 51 });
    resolverPanel();
    resolverAsignaciones();
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('.panel-marco')).toBeTruthy();

    component.cerrarPanel();
    fixture.detectChanges();

    expect(component.indicadorPanel).toBeNull();
    expect(component.correspondenciasConfirmadas).toEqual([]);
    expect(fixture.nativeElement.querySelector('.panel-marco')).toBeNull();
  });

  function conPermisosVinculacion(): void {
    const auth = TestBed.inject(AuthService);
    spyOn(auth, 'getUser').and.returnValue({
      is_superuser: false,
      groups: ['Administrador General'],
      permisos: ['vinculacion.add_correspondencia'],
    });
  }

  function sinPermisosVinculacion(): void {
    const auth = TestBed.inject(AuthService);
    spyOn(auth, 'getUser').and.returnValue({ is_superuser: false, groups: [], permisos: [] });
  }

  function resolverOrigenesDelFormulario(): void {
    httpMock
      .expectOne((r) => r.url === `${environment.apiUrl}/indicadores/` && r.params.get('page') === '1')
      .flush({ count: 0, results: [], next: null, previous: null });
  }

  function botonProponer(): HTMLButtonElement | null {
    return (
      (Array.from(fixture.nativeElement.querySelectorAll('button')) as HTMLButtonElement[]).find(
        (b) => (b.textContent ?? '').includes('Proponer vínculo')
      ) ?? null
    );
  }

  it('sin permisos no se ofrece proponer vínculo', () => {
    sinPermisosVinculacion();
    fixture.detectChanges();
    resolverVersiones();
    component.seleccionar({ id: 1, slug: 'eq-sidaces-2019-res27-2019', activo: false });
    httpMock
      .expectOne((r) => r.url === `${base}/dimensiones/`)
      .flush({ results: [{ id: 15, codigo: 'VI', nombre: 'PERSONAL ACADÉMICO' }] });
    fixture.detectChanges();

    expect(botonProponer()).toBeNull();
    expect(component.puedeProponer).toBeFalse();
  });

  it('en niveles sin destino válido (componentes) no se ofrece proponer vínculo', () => {
    conPermisosVinculacion();
    fixture.detectChanges();
    resolverVersiones();
    component.seleccionar({ id: 1, slug: 'eq-sidaces-2019-res27-2019', activo: false });
    httpMock
      .expectOne((r) => r.url === `${base}/dimensiones/`)
      .flush({ results: [{ id: 15, codigo: 'VI', nombre: 'PERSONAL ACADÉMICO' }] });
    component.seleccionar({ id: 15, codigo: 'VI' });
    httpMock
      .expectOne((r) => r.url === `${base}/componentes/`)
      .flush({ results: [{ id: 21, codigo: '6.1', codigo_completo: '6.1', nombre: 'Administración' }] });
    fixture.detectChanges();

    expect(component.nivelActual).toBe('componentes');
    expect(botonProponer()).toBeNull();
  });

  it('abre el formulario de propuesta desde una dimensión con el destino correcto y se puede cancelar', () => {
    conPermisosVinculacion();
    fixture.detectChanges();
    resolverVersiones();
    component.seleccionar({ id: 1, slug: 'eq-sidaces-2019-res27-2019', activo: false });
    httpMock
      .expectOne((r) => r.url === `${base}/dimensiones/`)
      .flush({ results: [{ id: 15, codigo: 'VI', nombre: 'PERSONAL ACADÉMICO' }] });
    fixture.detectChanges();

    const boton = botonProponer()!;
    expect(boton).toBeTruthy();
    boton.click();
    fixture.detectChanges();

    expect(component.formPropuesta).toEqual(
      jasmine.objectContaining({ nivel: 'dimension', id: 15, version: 1 })
    );
    expect(fixture.nativeElement.querySelector('app-correspondencia-form')).toBeTruthy();
    resolverOrigenesDelFormulario();
    fixture.detectChanges();

    const cancelar = (Array.from(fixture.nativeElement.querySelectorAll('button')) as HTMLButtonElement[]).find(
      (b) => (b.textContent ?? '').includes('Cancelar')
    )!;
    cancelar.click();
    fixture.detectChanges();

    expect(component.formPropuesta).toBeNull();
    expect(fixture.nativeElement.querySelector('app-correspondencia-form')).toBeNull();
  });

  it('al crear una propuesta desde el panel se recargan las correspondencias', () => {
    conPermisosVinculacion();
    navegarAIndicadores();
    component.seleccionar({ id: 51 });
    resolverPanel();
    resolverAsignaciones();
    fixture.detectChanges();

    botonProponer()!.click();
    fixture.detectChanges();

    expect(component.formPropuesta).toEqual(
      jasmine.objectContaining({ nivel: 'indicador_marco', id: 51, version: 1 })
    );
    resolverOrigenesDelFormulario();
    fixture.detectChanges();

    component.onPropuestaCreada();
    resolverPanel();
    resolverAsignaciones();

    expect(component.correspondenciasConfirmadas.length).toBe(1);
    expect(component.panelError).toBe('');
  });

  it('el panel muestra el detalle de las propuestas pendientes', () => {
    navegarAIndicadores();
    component.seleccionar({ id: 51 });
    httpMock
      .expectOne(
        (r) =>
          r.url === `${vincBase}/` &&
          r.params.get('estado') === 'confirmada' &&
          r.params.get('indicador_marco') === '51'
      )
      .flush({ count: 0, results: [] });
    httpMock
      .expectOne(
        (r) =>
          r.url === `${vincBase}/` &&
          r.params.get('estado') === 'propuesta' &&
          r.params.get('indicador_marco') === '51'
      )
      .flush({
        count: 1,
        results: [
          {
            ...corrPropuesta,
            creado_por: 'ana',
            fecha_creacion: '2026-10-01T10:00:00Z',
            comentario: 'Vincula con el estándar',
          },
        ],
      });
    spyOn(TestBed.inject(PermisosService), 'puedeAccederRuta').and.returnValue(true);
    fixture.detectChanges();

    const texto: string = fixture.nativeElement.textContent;
    expect(texto).toContain('Propuesta (pendiente de validación)');
    expect(texto).toContain('Justificación: Vincula con el estándar');
    expect(texto).toContain('por ana');
    expect(texto).toContain('Ver origen operativo');
  });

  it('enlaza al indicador operativo de origen de una correspondencia confirmada', () => {
    navegarAIndicadores();
    component.seleccionar({ id: 51 });
    resolverPanel();
    resolverAsignaciones();
    fixture.detectChanges();

    const enlaces = Array.from(fixture.nativeElement.querySelectorAll('a[href]')).map(
      (a: any) => a.getAttribute('href') ?? ''
    );
    expect(enlaces.some((href: string) => href.includes('/indicadores/90/detalle'))).toBeTrue();
  });
});
