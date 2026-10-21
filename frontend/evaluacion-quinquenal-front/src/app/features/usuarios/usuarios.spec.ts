import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Usuarios } from './usuarios';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { ToastrModule } from 'ngx-toastr';
import { ToastrService } from 'ngx-toastr';
import { of, Subject, throwError } from 'rxjs';
import { OrganizacionService } from '../../core/services/organizacion.service';
import { EvaluacionService } from '../../core/services/evaluacion.service';
import { PermisosService } from '../../core/services/permisos.service';

describe('Usuarios', () => {
  let component: Usuarios;
  let fixture: ComponentFixture<Usuarios>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Usuarios, ToastrModule.forRoot(), RouterTestingModule],
      providers: [provideHttpClient(), provideHttpClientTesting()]
    })
    .compileComponents();

    fixture = TestBed.createComponent(Usuarios);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should define the main columns for the users table', () => {
    expect(component.columnas).toContain('Nombre');
    expect(component.columnas).toContain('Correo');
    expect(component.columnas).toContain('Unidad');
    expect(component.columnas).toContain('Rol');
    expect(component.columnas).toContain('Estado');
  });
});

describe('Usuarios: ámbitos de revisión', () => {
  let component: Usuarios;
  let fixture: ComponentFixture<Usuarios>;
  let organizacion: jasmine.SpyObj<OrganizacionService>;
  let permisos: Set<string>;
  const revisor = { id: 20, username: 'revisor', rol: 'Revisor Institucional' };
  const externo = { id: 30, username: 'externo', rol: 'Evaluador Externo' };

  beforeEach(async () => {
    permisos = new Set([
      'organization.view_ambitorevision', 'organization.add_ambitorevision',
      'organization.change_ambitorevision', 'organization.add_ambitoevaluacion',
      'organization.change_ambitoevaluacion',
    ]);
    organizacion = jasmine.createSpyObj('OrganizacionService', [
      'listarUsuarios', 'listarPerfiles', 'listarUnidadesOrganizacionales', 'listarRoles',
      'listarAmbitosRevision', 'configuracionAmbitosRevision', 'crearAmbitoRevision', 'actualizarAmbitoRevision',
      'listarUnidadesParaAmbitos', 'listarPeriodosParaAmbitos',
      'listarAmbitosEvaluacion', 'crearAmbitoEvaluacion', 'actualizarAmbitoEvaluacion',
    ]);
    for (const metodo of ['listarUsuarios', 'listarPerfiles', 'listarUnidadesOrganizacionales', 'listarRoles', 'listarAmbitosEvaluacion'] as const) {
      organizacion[metodo].and.returnValue(of([]));
    }
    organizacion.listarAmbitosRevision.and.returnValue(of([
      { id: 5, unidad_nombre: 'Centro de prueba', periodo_nombre: 'P1', activo: true },
    ]));
    organizacion.configuracionAmbitosRevision.and.returnValue(of({ alcance_explicito_activo: false }));
    organizacion.listarUnidadesParaAmbitos.and.returnValue(of([]));
    organizacion.listarPeriodosParaAmbitos.and.returnValue(of([]));
    organizacion.crearAmbitoRevision.and.returnValue(of({ id: 6 }));
    organizacion.actualizarAmbitoRevision.and.returnValue(of({ id: 5, activo: false }));
    await TestBed.configureTestingModule({
      imports: [Usuarios, RouterTestingModule],
      providers: [
        { provide: OrganizacionService, useValue: organizacion },
        { provide: EvaluacionService, useValue: { listarPeriodos: () => of([]) } },
        { provide: PermisosService, useValue: {
          tienePermiso: (permiso: string) => permisos.has(permiso),
          tieneAlgunPermiso: (lista: string[]) => lista.some(permiso => permisos.has(permiso)),
        } },
        { provide: ToastrService, useValue: jasmine.createSpyObj('toast', ['success', 'error']) },
      ],
    }).compileComponents();
    fixture = TestBed.createComponent(Usuarios);
    component = fixture.componentInstance;
  });

  it('muestra el ámbito del centro y avisa que la transición no está activada', () => {
    component.abrirAmbitos(revisor, 'revision');
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Centro de prueba');
    expect(fixture.nativeElement.textContent).toContain('todavía no está activado');
    expect(organizacion.listarAmbitosEvaluacion).not.toHaveBeenCalled();
  });

  it('informa que sin ámbitos no hay acceso cuando el modo explícito está activo', () => {
    organizacion.configuracionAmbitosRevision.and.returnValue(of({ alcance_explicito_activo: true }));
    organizacion.listarAmbitosRevision.and.returnValue(of([]));
    component.abrirAmbitos(revisor, 'revision');
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('sin ámbitos activos');
    expect(fixture.nativeElement.textContent).not.toContain('todavía no está activado');
  });

  it('crea y revoca ámbitos internos mediante endpoints separados', () => {
    component.abrirAmbitos(revisor, 'revision');
    component.nuevoAmbitoUnidad = '12';
    component.nuevoAmbitoPeriodo = '2';
    component.crearAmbito();
    expect(organizacion.crearAmbitoRevision).toHaveBeenCalledWith({ usuario: 20, unidad_organizacional: 12, periodo: 2 });
    component.alternarAmbito({ id: 5, activo: true });
    expect(organizacion.actualizarAmbitoRevision).toHaveBeenCalledWith(5, { activo: false });
    expect(organizacion.crearAmbitoEvaluacion).not.toHaveBeenCalled();
    expect(organizacion.actualizarAmbitoEvaluacion).not.toHaveBeenCalled();
  });

  it('no abre la gestión interna con permisos exclusivos de ámbitos externos', () => {
    permisos.delete('organization.view_ambitorevision');
    component.abrirAmbitos(revisor, 'revision');
    expect(component.showAmbitos).toBeFalse();
    expect(organizacion.listarAmbitosRevision).not.toHaveBeenCalled();
    component.abrirAmbitos(externo);
    expect(component.showAmbitos).toBeTrue();
    expect(organizacion.listarAmbitosEvaluacion).toHaveBeenCalledWith(30);
  });

  it('separa permisos de creación y de cambio', () => {
    permisos.delete('organization.add_ambitorevision');
    component.abrirAmbitos(revisor, 'revision');
    component.nuevoAmbitoUnidad = '12';
    component.nuevoAmbitoPeriodo = '2';
    component.crearAmbito();
    fixture.detectChanges();
    expect(organizacion.crearAmbitoRevision).not.toHaveBeenCalled();
    expect(fixture.nativeElement.querySelector('.scope-form')).toBeNull();
    expect(fixture.nativeElement.querySelector('.scope-toggle-btn')).not.toBeNull();
  });

  it('muestra el error de carga sin presentar una lista vacía como resultado válido', () => {
    organizacion.listarAmbitosRevision.and.returnValue(throwError(() => ({ status: 500 })));
    component.abrirAmbitos(revisor, 'revision');
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('[role="alert"]').textContent).toContain('No se pudieron cargar');
    expect(fixture.nativeElement.textContent).not.toContain('Este usuario aún no tiene ámbitos');
    component.nuevoAmbitoUnidad = '12';
    component.nuevoAmbitoPeriodo = '2';
    component.crearAmbito();
    expect(organizacion.crearAmbitoRevision).not.toHaveBeenCalled();
  });

  it('ignora respuestas tardías de otro usuario o tipo de ámbito', () => {
    const pendientes = new Subject<any[]>();
    organizacion.listarAmbitosRevision.and.returnValue(pendientes);
    component.abrirAmbitos(revisor, 'revision');
    component.cerrarAmbitos();
    component.abrirAmbitos(externo);
    pendientes.next([{ id: 999, unidad_nombre: 'Ámbito interno' }]);
    pendientes.complete();
    expect(component.tipoAmbito).toBe('evaluacion');
    expect(component.ambitosUsuario).toEqual([]);
    expect(component.alcanceRevisionExplicito).toBeNull();
  });
});
