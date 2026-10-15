import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { Catalogo } from './catalogo';
import { environment } from '../../../environments/environment';

describe('Catalogo', () => {
  let component: Catalogo;
  let fixture: ComponentFixture<Catalogo>;
  let httpMock: HttpTestingController;
  const base = `${environment.apiUrl}/catalogo`;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Catalogo],
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
});
