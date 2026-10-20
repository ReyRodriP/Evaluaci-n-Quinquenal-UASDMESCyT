import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { ToastrModule, ToastrService } from 'ngx-toastr';
import { Vinculacion } from './vinculacion';
import { AuthService } from '../../features/auth/services/auth-service';
import { environment } from '../../../environments/environment';
import { Correspondencia } from '../../core/models/vinculacion.model';

describe('Vinculacion', () => {
  let component: Vinculacion;
  let fixture: ComponentFixture<Vinculacion>;
  let httpMock: HttpTestingController;
  let toast: ToastrService;
  const base = `${environment.apiUrl}/vinculacion/correspondencias`;

  const propuesta: Correspondencia = {
    id: 1,
    estado: 'propuesta',
    procedencia: 'manual',
    criterio_op: null,
    indicador_op: 9,
    dimension: null,
    estandar: null,
    indicador_marco: 51,
    version_marco: { id: 1, nombre: 'EQ 2026', slug: 'eq-2026', activo: true },
    origen: { nivel: 'indicador', id: 9, texto: 'Indicador 9' },
    destino: { nivel: 'estandar', id: 41, texto: '6.1.1.1' },
    creado_por: 'ana',
    fecha_creacion: '2026-10-01T10:00:00Z',
    confirmado_por: null,
    fecha_confirmacion: null,
    rechazado_por: null,
    fecha_rechazo: null,
    comentario: 'Vincula con el marco',
  };

  const confirmada: Correspondencia = { ...propuesta, id: 2, estado: 'confirmada' };

  beforeEach(async () => {
    localStorage.removeItem('auth_user');
    await TestBed.configureTestingModule({
      imports: [Vinculacion, RouterTestingModule, ToastrModule.forRoot()],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();

    httpMock = TestBed.inject(HttpTestingController);
    toast = TestBed.inject(ToastrService);
    spyOn(toast, 'success');
    spyOn(toast, 'error');
    fixture = TestBed.createComponent(Vinculacion);
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
      permisos: ['vinculacion.view_correspondencia', 'vinculacion.change_correspondencia'],
    });
  }

  function sinPermisos(): void {
    const auth = TestBed.inject(AuthService);
    spyOn(auth, 'getUser').and.returnValue({ is_superuser: false, groups: ['Consulta'], permisos: ['vinculacion.view_correspondencia'] });
  }

  function responder(estado: string | null, cuerpo: any): void {
    httpMock
      .expectOne((r) => {
        if (r.url !== `${base}/`) return false;
        const param = r.params.get('estado');
        return estado === null ? param === null : param === estado;
      })
      .flush(cuerpo);
  }

  function boton(texto: string): HTMLButtonElement | null {
    const botones = Array.from(fixture.nativeElement.querySelectorAll('button')) as HTMLButtonElement[];
    return botones.find((b) => (b.textContent ?? '').includes(texto)) ?? null;
  }

  it('carga y muestra las correspondencias al iniciar', () => {
    fixture.detectChanges();
    responder(null, { count: 1, results: [propuesta], next: null, previous: null });
    fixture.detectChanges();

    const texto: string = fixture.nativeElement.textContent;
    expect(texto).toContain('Propuesta (pendiente de validación)');
    expect(texto).toContain('Indicador operativo');
    expect(texto).toContain('Indicador 9');
    expect(texto).toContain('Vincula con el marco');
    expect(texto).toContain('Creada por ana');
    expect(toast.success).not.toHaveBeenCalled();
  });

  it('filtra por estado rechazadas y muestra el estado vacío correspondiente', () => {
    fixture.detectChanges();
    responder(null, { count: 1, results: [propuesta], next: null, previous: null });
    fixture.detectChanges();

    boton('Rechazadas')!.click();
    responder('rechazada', { count: 0, results: [], next: null, previous: null });
    fixture.detectChanges();

    expect(component.estadoFiltro).toBe('rechazada');
    expect(fixture.nativeElement.textContent).toContain('No hay correspondencias rechazadas');
  });

  it('muestra el mensaje de sin permisos ante un 403', () => {
    fixture.detectChanges();
    httpMock
      .expectOne((r) => r.url === `${base}/`)
      .error(new ProgressEvent('error'), { status: 403 } as any);
    fixture.detectChanges();

    expect(component.sinPermiso).toBeTrue();
    expect(fixture.nativeElement.textContent).toContain(
      'No tiene permisos para consultar las correspondencias'
    );
  });

  it('muestra un error recuperable ante un fallo del servidor y permite reintentar', () => {
    fixture.detectChanges();
    httpMock
      .expectOne((r) => r.url === `${base}/`)
      .error(new ProgressEvent('error'), { status: 500 } as any);
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('No se pudieron cargar las correspondencias');

    boton('Reintentar')!.click();
    responder(null, { count: 1, results: [propuesta], next: null, previous: null });
    fixture.detectChanges();
    expect(component.error).toBe('');
    expect(fixture.nativeElement.textContent).toContain('Indicador 9');
  });

  it('no muestra acciones de estado sin permisos de cambio', () => {
    sinPermisos();
    fixture.detectChanges();
    responder(null, { count: 1, results: [propuesta], next: null, previous: null });
    fixture.detectChanges();

    expect(component.puedeTransicionar).toBeFalse();
    expect(boton('Confirmar')).toBeNull();
    expect(boton('Rechazar')).toBeNull();
    expect(httpMock.match((r) => r.method === 'POST')).toEqual([]);
  });

  it('confirmar exige un paso previo y actualiza la fila con la respuesta del servidor', () => {
    conPermisos();
    fixture.detectChanges();
    responder(null, { count: 1, results: [propuesta], next: null, previous: null });
    fixture.detectChanges();

    boton('Confirmar…')!.click();
    fixture.detectChanges();
    expect(httpMock.match((r) => r.method === 'POST')).toEqual([]);
    expect(fixture.nativeElement.textContent).toContain('¿Confirma este vínculo');

    boton('Sí, confirmar')!.click();
    const peticiones = httpMock.match(
      (r) => r.method === 'POST' && r.url === `${base}/1/confirmar/`
    );
    expect(peticiones.length).toBe(1);
    peticiones[0].flush({
      ...propuesta,
      estado: 'confirmada',
      confirmado_por: 'jefe',
      fecha_confirmacion: '2026-10-02T09:00:00Z',
    });
    fixture.detectChanges();

    expect(toast.success).toHaveBeenCalledWith('Correspondencia confirmada');
    const texto: string = fixture.nativeElement.textContent;
    expect(texto).toContain('Confirmada');
    expect(texto).toContain('Confirmada por jefe');
    expect(component.transicion).toBeNull();
  });

  it('cancelar el paso de confirmación no ejecuta la acción', () => {
    conPermisos();
    fixture.detectChanges();
    responder(null, { count: 1, results: [propuesta], next: null, previous: null });
    fixture.detectChanges();

    boton('Confirmar…')!.click();
    fixture.detectChanges();
    boton('Cancelar')!.click();
    fixture.detectChanges();

    expect(component.transicion).toBeNull();
    expect(httpMock.match((r) => r.method === 'POST')).toEqual([]);
    expect(fixture.nativeElement.textContent).toContain('Propuesta (pendiente de validación)');
  });

  it('rechazar exige comentario antes de ejecutar', () => {
    conPermisos();
    fixture.detectChanges();
    responder(null, { count: 1, results: [propuesta], next: null, previous: null });
    fixture.detectChanges();

    boton('Rechazar…')!.click();
    fixture.detectChanges();
    const confirmar = boton('Rechazar')!;
    expect(confirmar.disabled).toBeTrue();

    component.transicion!.comentario = 'No aplica';
    fixture.detectChanges();
    expect(boton('Rechazar')!.disabled).toBeFalse();

    boton('Rechazar')!.click();
    const peticiones = httpMock.match(
      (r) => r.method === 'POST' && r.url === `${base}/1/rechazar/`
    );
    expect(peticiones.length).toBe(1);
    expect(peticiones[0].request.body).toEqual({ comentario: 'No aplica' });
    peticiones[0].flush({ ...propuesta, estado: 'rechazada', rechazado_por: 'jefe' });
    fixture.detectChanges();

    expect(toast.success).toHaveBeenCalledWith('Correspondencia rechazada');
    expect(fixture.nativeElement.textContent).toContain('Rechazada');
  });

  it('un error del servidor no se presenta como éxito y conserva el estado', () => {
    conPermisos();
    fixture.detectChanges();
    responder(null, { count: 1, results: [propuesta], next: null, previous: null });
    fixture.detectChanges();

    boton('Confirmar…')!.click();
    fixture.detectChanges();
    boton('Sí, confirmar')!.click();
    httpMock
      .match((r) => r.method === 'POST' && r.url === `${base}/1/confirmar/`)[0]
      .flush({ detail: 'Transición no permitida' }, { status: 500, statusText: 'Internal Server Error' });
    fixture.detectChanges();

    expect(toast.success).not.toHaveBeenCalled();
    expect(component.errorTransicion).toBe('Transición no permitida');
    const texto: string = fixture.nativeElement.textContent;
    expect(texto).toContain('Transición no permitida');
    expect(texto).toContain('Propuesta (pendiente de validación)');
    expect(component.transicion).not.toBeNull();
  });

  it('desconfirmar una correspondencia confirmada la devuelve a propuesta', () => {
    conPermisos();
    fixture.detectChanges();
    responder(null, { count: 1, results: [confirmada], next: null, previous: null });
    fixture.detectChanges();

    boton('Desconfirmar…')!.click();
    fixture.detectChanges();
    component.transicion!.comentario = 'Revisión pendiente';
    fixture.detectChanges();
    boton('Devolver a propuesta')!.click();
    const peticiones = httpMock.match(
      (r) => r.method === 'POST' && r.url === `${base}/2/desconfirmar/`
    );
    expect(peticiones.length).toBe(1);
    peticiones[0].flush({ ...confirmada, estado: 'propuesta' });
    fixture.detectChanges();

    expect(toast.success).toHaveBeenCalledWith('Correspondencia devuelta a propuesta');
    expect(fixture.nativeElement.textContent).toContain('Propuesta (pendiente de validación)');
  });

  it('al confirmar con un filtro de estado activo recarga la lista del servidor', () => {
    conPermisos();
    fixture.detectChanges();
    responder(null, { count: 1, results: [propuesta], next: null, previous: null });
    fixture.detectChanges();

    boton('Propuestas')!.click();
    responder('propuesta', { count: 1, results: [propuesta], next: null, previous: null });
    fixture.detectChanges();

    boton('Confirmar…')!.click();
    fixture.detectChanges();
    boton('Sí, confirmar')!.click();
    httpMock
      .match((r) => r.method === 'POST' && r.url === `${base}/1/confirmar/`)[0]
      .flush({ ...propuesta, estado: 'confirmada' });
    responder('propuesta', { count: 0, results: [], next: null, previous: null });
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('No hay propuestas pendientes');
  });

  it('pagina hacia adelante cuando el servidor indica página siguiente', () => {
    fixture.detectChanges();
    responder(null, { count: 60, results: [propuesta], next: `${base}/?page=2`, previous: null });
    fixture.detectChanges();

    boton('Siguiente →')!.click();
    httpMock
      .expectOne((r) => r.url === `${base}/` && r.params.get('page') === '2')
      .flush({ count: 60, results: [confirmada], next: null, previous: `${base}/?page=1` });
    fixture.detectChanges();

    expect(component.pagina).toBe(2);
    expect(boton('← Anterior')!.disabled).toBeFalse();
    expect(fixture.nativeElement.textContent).toContain('Página 2');
  });

  it('enlaza al origen operativo cuando el usuario puede consultarlo', () => {
    fixture.detectChanges();
    responder(null, { count: 1, results: [propuesta], next: null, previous: null });
    fixture.detectChanges();

    const enlaces = Array.from(fixture.nativeElement.querySelectorAll('a[href]')).map(
      (a: any) => a.getAttribute('href') ?? ''
    );
    expect(enlaces.some((href: string) => href.includes('/indicadores/9/detalle'))).toBeTrue();
  });
});
