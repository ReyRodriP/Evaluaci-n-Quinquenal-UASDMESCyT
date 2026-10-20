import { ComponentFixture, TestBed } from '@angular/core/testing';
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
});
