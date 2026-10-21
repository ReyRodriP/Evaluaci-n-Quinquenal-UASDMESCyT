import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { CorrespondenciaForm, DestinoFijo, OrigenFijo } from './correspondencia-form';
import { AuthService } from '../../../features/auth/services/auth-service';
import { environment } from '../../../../environments/environment';

describe('CorrespondenciaForm', () => {
  let component: CorrespondenciaForm;
  let fixture: ComponentFixture<CorrespondenciaForm>;
  let httpMock: HttpTestingController;
  const api = environment.apiUrl;
  const vincBase = `${api}/vinculacion/correspondencias`;

  const destino: DestinoFijo = {
    nivel: 'estandar',
    id: 41,
    version: 1,
    codigo: '6.1.1.1',
    texto: 'Estándar 1',
  };

  const origen: OrigenFijo = { nivel: 'criterio', id: 3, texto: 'Criterio demo' };

  beforeEach(async () => {
    localStorage.removeItem('auth_user');
    await TestBed.configureTestingModule({
      imports: [CorrespondenciaForm, RouterTestingModule],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();

    httpMock = TestBed.inject(HttpTestingController);
    fixture = TestBed.createComponent(CorrespondenciaForm);
    component = fixture.componentInstance;
  });

  afterEach(() => {
    httpMock.verify();
  });

  function conPermisos(): void {
    const auth = TestBed.inject(AuthService);
    spyOn(auth, 'getUser').and.returnValue({
      is_superuser: false,
      groups: ['Administrador General'],
      permisos: ['vinculacion.add_correspondencia'],
    });
  }

  function sinPermisos(): void {
    const auth = TestBed.inject(AuthService);
    spyOn(auth, 'getUser').and.returnValue({ is_superuser: false, groups: [], permisos: [] });
  }

  function resolverOrigenes(url: string, resultados: any[]): void {
    httpMock
      .expectOne((r) => r.url === url && r.params.get('page') === '1')
      .flush({ count: resultados.length, results: resultados, next: null, previous: null });
  }

  describe('modo destino fijo (explorador)', () => {
    it('carga los orígenes operativos y habilita el envío solo tras elegir uno', () => {
      conPermisos();
      component.destinoFijo = destino;
      fixture.detectChanges();
      resolverOrigenes(`${api}/indicadores/`, [{ id: 9, nombre: 'Indicador demo' }]);
      fixture.detectChanges();

      const select = fixture.nativeElement.querySelector('#cf-origen') as HTMLSelectElement;
      expect(select).toBeTruthy();
      expect(select.options.length).toBe(2);
      const boton = fixture.nativeElement.querySelector('button[type="submit"]') as HTMLButtonElement;
      expect(boton.disabled).toBeTrue();

      component.origenSeleccionado = '9';
      fixture.detectChanges();
      expect(boton.disabled).toBeFalse();
    });

    it('envía el payload con el destino fijado y el origen seleccionado', () => {
      conPermisos();
      const creada = jasmine.createSpy('creada');
      component.creada.subscribe(creada);
      component.destinoFijo = destino;
      fixture.detectChanges();
      resolverOrigenes(`${api}/indicadores/`, [{ id: 9, nombre: 'Indicador demo' }]);
      fixture.detectChanges();

      component.origenSeleccionado = '9';
      component.comentario = 'Vincula con el estándar';
      component.crear();

      const peticiones = httpMock.match((r) => r.method === 'POST' && r.url === `${vincBase}/`);
      expect(peticiones.length).toBe(1);
      expect(peticiones[0].request.body).toEqual({
        version_marco: 1,
        indicador_op: 9,
        estandar: 41,
        comentario: 'Vincula con el estándar',
      });
      peticiones[0].flush({ id: 10, estado: 'propuesta' });
      fixture.detectChanges();

      expect(component.exito).toBeTrue();
      expect(component.errorCreacion).toBe('');
      expect(creada).toHaveBeenCalled();
      expect(fixture.nativeElement.textContent).toContain('Propuesta de correspondencia creada');
    });

    it('cambia el tipo de origen a criterio operativo y recarga la lista', () => {
      conPermisos();
      component.destinoFijo = destino;
      fixture.detectChanges();
      resolverOrigenes(`${api}/indicadores/`, [{ id: 9, nombre: 'Indicador demo' }]);
      fixture.detectChanges();

      const tipo = fixture.nativeElement.querySelector('#cf-tipo-origen') as HTMLSelectElement;
      tipo.value = 'criterio';
      tipo.dispatchEvent(new Event('change'));
      fixture.detectChanges();
      resolverOrigenes(`${api}/criterios/`, [{ id: 3, nombre: 'Criterio demo' }]);
      fixture.detectChanges();

      expect(component.tipoOrigen).toBe('criterio');
      expect(component.origenes.length).toBe(1);
      expect(component.origenSeleccionado).toBe('');
      expect(fixture.nativeElement.textContent).toContain('Criterio operativo');
    });

    it('no ofrece el formulario cuando el usuario no tiene permisos', () => {
      sinPermisos();
      component.destinoFijo = destino;
      fixture.detectChanges();

      expect(fixture.nativeElement.textContent).toContain(
        'No tiene permisos para proponer correspondencias'
      );
      expect(fixture.nativeElement.querySelector('#cf-origen')).toBeNull();
      expect(fixture.nativeElement.querySelector('button[type="submit"]')).toBeNull();
    });

    it('muestra el error 403 del servidor como falta de permisos', () => {
      conPermisos();
      component.destinoFijo = destino;
      fixture.detectChanges();
      resolverOrigenes(`${api}/indicadores/`, [{ id: 9, nombre: 'Indicador demo' }]);
      fixture.detectChanges();

      component.origenSeleccionado = '9';
      component.crear();
      httpMock
        .match((r) => r.method === 'POST' && r.url === `${vincBase}/`)[0]
        .error(new ProgressEvent('error'), { status: 403 } as any);
      fixture.detectChanges();

      expect(component.errorCreacion).toBe('No tiene permisos para realizar esta operación');
      expect(component.exito).toBeFalse();
    });

    it('muestra el detalle del backend cuando la API rechaza un duplicado', () => {
      conPermisos();
      component.destinoFijo = destino;
      fixture.detectChanges();
      resolverOrigenes(`${api}/indicadores/`, [{ id: 9, nombre: 'Indicador demo' }]);
      fixture.detectChanges();

      component.origenSeleccionado = '9';
      component.crear();
      httpMock
        .match((r) => r.method === 'POST' && r.url === `${vincBase}/`)[0]
        .flush({ detalle: 'Ya existe una correspondencia viva con este origen y destino.' }, {
          status: 400,
          statusText: 'Bad Request',
        });
      fixture.detectChanges();

      expect(component.errorCreacion).toContain('Ya existe una correspondencia viva');
      expect(component.exito).toBeFalse();
    });

    it('no envía dos peticiones si se presiona guardar repetidamente', () => {
      conPermisos();
      component.destinoFijo = destino;
      fixture.detectChanges();
      resolverOrigenes(`${api}/indicadores/`, [{ id: 9, nombre: 'Indicador demo' }]);
      fixture.detectChanges();

      component.origenSeleccionado = '9';
      component.crear();
      component.crear();

      const peticiones = httpMock.match((r) => r.method === 'POST' && r.url === `${vincBase}/`);
      expect(peticiones.length).toBe(1);
      peticiones[0].flush({ id: 10, estado: 'propuesta' });
    });

    it('cierra el formulario emitiendo cancelada', () => {
      conPermisos();
      const cancelada = jasmine.createSpy('cancelada');
      component.cancelada.subscribe(cancelada);
      component.destinoFijo = destino;
      fixture.detectChanges();
      resolverOrigenes(`${api}/indicadores/`, [{ id: 9, nombre: 'Indicador demo' }]);

      component.cerrar();
      expect(cancelada).toHaveBeenCalled();
    });
  });

  describe('modo origen fijo (elemento operativo)', () => {
    it('carga las versiones del marco al iniciar', () => {
      conPermisos();
      component.origenFijo = origen;
      fixture.detectChanges();
      httpMock
        .expectOne(`${api}/catalogo/versiones/`)
        .flush({ count: 1, results: [{ id: 1, nombre: 'EQ 2026', activo: true }] });
      fixture.detectChanges();

      expect(component.versiones.length).toBe(1);
      expect(fixture.nativeElement.textContent).toContain('Criterio operativo');
      expect(fixture.nativeElement.textContent).toContain('Criterio demo');
    });

    it('la cascada de destino permite seleccionar un estándar y envía el payload correcto', () => {
      conPermisos();
      const creada = jasmine.createSpy('creada');
      component.creada.subscribe(creada);
      component.origenFijo = origen;
      fixture.detectChanges();
      httpMock
        .expectOne(`${api}/catalogo/versiones/`)
        .flush({ count: 1, results: [{ id: 1, nombre: 'EQ 2026', activo: true }] });

      component.versionSeleccionada = '1';
      component.onVersionChange();
      httpMock
        .expectOne((r) => r.url === `${api}/catalogo/dimensiones/` && r.params.get('version') === '1')
        .flush({ results: [{ id: 15, codigo: 'VI', nombre: 'Personal' }] });

      component.dimensionSeleccionada = '15';
      component.onDimensionChange();
      httpMock
        .expectOne((r) => r.url === `${api}/catalogo/componentes/` && r.params.get('dimension') === '15')
        .flush({ results: [{ id: 21, codigo: '6.1', codigo_completo: '6.1', nombre: 'Administración' }] });

      component.componenteSeleccionado = '21';
      component.onComponenteChange();
      httpMock
        .expectOne((r) => r.url === `${api}/catalogo/criterios/` && r.params.get('componente') === '21')
        .flush({ results: [{ id: 31, codigo: '6.1.1', codigo_completo: '6.1.1', nombre: 'Criterio' }] });

      component.criterioSeleccionado = '31';
      component.onCriterioChange();
      httpMock
        .expectOne((r) => r.url === `${api}/catalogo/estandares/` && r.params.get('criterio') === '31')
        .flush({ results: [{ id: 41, codigo_completo: '6.1.1.1', nombre: 'Estándar 1' }] });

      component.estandarSeleccionado = '41';
      fixture.detectChanges();
      expect(component.destinoListo).toBeTrue();

      component.crear();
      const peticiones = httpMock.match((r) => r.method === 'POST' && r.url === `${vincBase}/`);
      expect(peticiones.length).toBe(1);
      expect(peticiones[0].request.body).toEqual({
        version_marco: 1,
        criterio_op: 3,
        estandar: 41,
        comentario: '',
      });
      peticiones[0].flush({ id: 12, estado: 'propuesta' });
      expect(creada).toHaveBeenCalled();
    });

    it('no permite crear sin permisos de correspondencia', () => {
      sinPermisos();
      component.origenFijo = origen;
      fixture.detectChanges();

      expect(fixture.nativeElement.textContent).toContain(
        'No tiene permisos para proponer correspondencias'
      );
      expect(component.listo).toBeFalse();
      component.crear();
      httpMock.expectNone((r) => r.method === 'POST' && r.url === `${vincBase}/`);
    });

    it('muestra inline un error de carga de la cascada', () => {
      conPermisos();
      component.origenFijo = origen;
      fixture.detectChanges();
      httpMock.expectOne(`${api}/catalogo/versiones/`).flush({ results: [] });

      component.versionSeleccionada = '1';
      component.onVersionChange();
      httpMock
        .expectOne((r) => r.url === `${api}/catalogo/dimensiones/`)
        .error(new ProgressEvent('error'));
      fixture.detectChanges();

      expect(component.errorCarga).toBe('No se pudieron cargar las dimensiones del marco');
      expect(fixture.nativeElement.textContent).toContain('No se pudieron cargar las dimensiones del marco');
    });
  });

  describe('edición de destino y búsqueda de orígenes (D4.11.1)', () => {
    const destinoConRuta: DestinoFijo = {
      nivel: 'dimension',
      id: 15,
      version: 1,
      codigo: 'VI',
      texto: 'Personal',
      ruta: ['VI — Personal'],
    };

    function flushOrigenes(resultados: any[], count = resultados.length): void {
      httpMock
        .expectOne((r) => r.url === `${api}/indicadores/` && r.params.get('page') === '1' && !r.params.get('search'))
        .flush({ count, results: resultados, next: null, previous: null });
    }

    function flushDimensiones(resultados: any[]): void {
      httpMock
        .expectOne((r) => r.url === `${api}/catalogo/dimensiones/` && r.params.get('version') === '1')
        .flush({ results: resultados });
    }

    function botonPorTexto(texto: string): HTMLButtonElement {
      return (Array.from(fixture.nativeElement.querySelectorAll('button')) as HTMLButtonElement[]).find((b) =>
        (b.textContent ?? '').includes(texto)
      )!;
    }

    it('muestra origen y destino por separado con la ruta del destino inicial', () => {
      conPermisos();
      component.destinoFijo = destinoConRuta;
      fixture.detectChanges();
      flushOrigenes([{ id: 9, nombre: 'Indicador demo' }]);
      fixture.detectChanges();

      const texto: string = fixture.nativeElement.textContent;
      expect(texto).toContain('Origen operativo (elemento de la evaluación)');
      expect(texto).toContain('Destino EQ-SIDACES (nodo del marco)');
      expect(texto).toContain('Ruta del destino: VI — Personal');
      expect(component.editandoDestino).toBeFalse();
    });

    it('permite cambiar el destino manteniendo la versión y el origen seleccionado', () => {
      conPermisos();
      component.destinoFijo = destinoConRuta;
      fixture.detectChanges();
      flushOrigenes([{ id: 9, nombre: 'Indicador demo' }]);
      component.origenSeleccionado = '9';
      component.comentario = 'Cambio de destino justificado';
      fixture.detectChanges();

      botonPorTexto('Cambiar destino').click();
      fixture.detectChanges();
      flushDimensiones([
        { id: 15, codigo: 'VI', nombre: 'Personal' },
        { id: 16, codigo: 'VII', nombre: 'Investigación' },
      ]);
      fixture.detectChanges();

      expect(component.editandoDestino).toBeTrue();
      expect(component.versionSeleccionada).toBe('1');
      expect(component.nivelDestino).toBe('dimension');
      expect(component.dimensionSeleccionada).toBe('15');
      expect(component.origenSeleccionado).toBe('9');
      expect(component.comentario).toBe('Cambio de destino justificado');
      expect(fixture.nativeElement.textContent).toContain('Usar destino original');

      component.dimensionSeleccionada = '16';
      component.onDimensionChange();
      fixture.detectChanges();
      expect(component.listo).toBeTrue();

      component.crear();
      const peticiones = httpMock.match((r) => r.method === 'POST' && r.url === `${vincBase}/`);
      expect(peticiones.length).toBe(1);
      expect(peticiones[0].request.body).toEqual({
        version_marco: 1,
        indicador_op: 9,
        dimension: 16,
        comentario: 'Cambio de destino justificado',
      });
      peticiones[0].flush({ id: 12, estado: 'propuesta' });
      expect(component.exito).toBeTrue();
    });

    it('restaurar el destino original vuelve al resumen fijo y envía el destino inicial', () => {
      conPermisos();
      component.destinoFijo = destino;
      fixture.detectChanges();
      flushOrigenes([{ id: 9, nombre: 'Indicador demo' }]);
      fixture.detectChanges();

      botonPorTexto('Cambiar destino').click();
      fixture.detectChanges();
      flushDimensiones([{ id: 15, codigo: 'VI', nombre: 'Personal' }]);
      fixture.detectChanges();

      botonPorTexto('Usar destino original').click();
      fixture.detectChanges();

      expect(component.editandoDestino).toBeFalse();
      expect(fixture.nativeElement.textContent).toContain('Estándar del marco');
      expect(fixture.nativeElement.querySelector('#cf-nivel-destino')).toBeNull();

      component.origenSeleccionado = '9';
      fixture.detectChanges();
      component.crear();
      const peticiones = httpMock.match((r) => r.method === 'POST' && r.url === `${vincBase}/`);
      expect(peticiones[0].request.body).toEqual({
        version_marco: 1,
        indicador_op: 9,
        estandar: 41,
        comentario: '',
      });
      peticiones[0].flush({ id: 13, estado: 'propuesta' });
    });

    it('avisa cuando hay más orígenes que los de la página cargada', () => {
      conPermisos();
      component.destinoFijo = destino;
      fixture.detectChanges();
      flushOrigenes([{ id: 9, nombre: 'Indicador demo' }], 60);
      fixture.detectChanges();

      expect(component.origenesTruncado).toBeTrue();
      expect(fixture.nativeElement.textContent).toContain('Hay más orígenes operativos');
    });

    it('la búsqueda de orígenes consulta ?search= en el servidor tras el debounce', fakeAsync(() => {
      conPermisos();
      component.destinoFijo = destino;
      fixture.detectChanges();
      flushOrigenes(Array.from({ length: 13 }, (_, i) => ({ id: i + 1, nombre: `Indicador ${i + 1}` })));
      fixture.detectChanges();

      component.filtroOrigen = 'demo';
      component.onFiltroOrigenChange();
      tick(300);
      fixture.detectChanges();

      httpMock
        .expectOne(
          (r) =>
            r.url === `${api}/indicadores/` &&
            r.params.get('page') === '1' &&
            r.params.get('search') === 'demo'
        )
        .flush({ count: 1, results: [{ id: 99, nombre: 'Indicador demo' }], next: null, previous: null });
      fixture.detectChanges();

      expect(component.origenes.length).toBe(1);
      expect(component.origenTotal).toBe(1);
      expect(component.origenSeleccionado).toBe('');
    }));
  });
});
