import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Asignaciones } from './asignaciones';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { ToastrModule } from 'ngx-toastr';
import { Router } from '@angular/router';
import { of } from 'rxjs';
import { EvaluacionService } from '../../core/services/evaluacion.service';
import { PermisosService } from '../../core/services/permisos.service';

describe('Asignaciones', () => {
  let component: Asignaciones;
  let fixture: ComponentFixture<Asignaciones>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Asignaciones, ToastrModule.forRoot(), RouterTestingModule],
      providers: [provideHttpClient(), provideHttpClientTesting()]
    })
    .compileComponents();

    fixture = TestBed.createComponent(Asignaciones);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('mantiene separados los grupos operativos y del marco y protege la edición del formulario anterior', () => {
    component.periodoSeleccionadoId = '1';
    const comun = { unidad_responsable: 10, unidad_responsable_nombre: 'Unidad', periodo: 1, periodo_nombre: 'P1', estado: 'pendiente' };
    const evaluacion = TestBed.inject(EvaluacionService);
    spyOn(evaluacion, 'listarAsignaciones').and.returnValue(of([
      { ...comun, id: 1, indicador: 7, indicador_nombre: 'Operativo' },
      { ...comun, id: 2, indicador: null, indicador_marco: 7, indicador_nombre: 'Del marco', tipo_origen: 'marco' },
    ]));
    const actualizar = spyOn(evaluacion, 'actualizarAsignacion');
    const navegar = spyOn(TestBed.inject(Router), 'navigate').and.resolveTo(true);
    component.loadAsignaciones();
    expect(component.datos.length).toBe(2);
    const marco = component.datos.find(row => row.tipo_origen === 'marco');
    expect(marco.asignaciones).toEqual([{ id: 2, indicador: null, indicador_marco: 7 }]);
    component.openEdit(marco);
    expect(component.showModal).toBeFalse();
    expect(navegar).toHaveBeenCalledWith(['/asignaciones', 2, 'detalle'], { queryParams: { periodo: '1' } });
    expect(actualizar).not.toHaveBeenCalled();
  });

  it('abre el alta directa para coordinación y navega a su gestión al guardar', () => {
    const permisos = TestBed.inject(PermisosService);
    spyOn(permisos, 'tieneAlgunPermiso').and.returnValue(true);
    spyOn(permisos, 'tieneGrupo').and.callFake(rol => rol === 'Coordinador Quinquenal');
    component.periodos = [{ id: 2, activo: true }]; component.periodoSeleccionadoId = '2';
    component.abrirMarco(); expect(component.showMarco).toBeTrue();
    const navegar = spyOn(TestBed.inject(Router), 'navigate').and.resolveTo(true);
    component.asignacionMarcoCreada({ id: 30, periodo: 2 });
    expect(navegar).toHaveBeenCalledWith(['/asignaciones', 30, 'detalle'], { queryParams: { periodo: 2 } });
    expect(component.showMarco).toBeFalse();
  });

  it('no ofrece el alta del marco en un período finalizado ni a roles de revisión', () => {
    const permisos = TestBed.inject(PermisosService);
    spyOn(permisos, 'tieneAlgunPermiso').and.returnValue(true);
    spyOn(permisos, 'tieneGrupo').and.returnValue(false);
    component.periodos = [{ id: 2, activo: true }]; component.periodoSeleccionadoId = '2';
    expect(component.puedeCrearMarco).toBeFalse();
    component.periodos[0].activo = false; component.abrirMarco(); expect(component.showMarco).toBeFalse();
  });

  function habilitarGestion(): void {
    const permisos = TestBed.inject(PermisosService);
    spyOn(permisos, 'tieneAlgunPermiso').and.returnValue(true);
    spyOn(permisos, 'tieneGrupo').and.callFake(rol => rol === 'Coordinador Quinquenal');
    component.periodos = [{ id: 2, activo: true }]; component.periodoSeleccionadoId = '2';
  }

  it('presenta una única entrada de alta y abre el formulario del marco', () => {
    habilitarGestion();
    spyOn(TestBed.inject(EvaluacionService), 'contextoAsignacionMarco').and.returnValue(of({
      periodo: { id: 2, nombre: 'P2' }, version: { id: 1, nombre: 'Marco', activo: false }, unidades: [], indicadores: [], encargados: [], asignaciones_existentes: [],
    }));
    fixture.detectChanges();
    const botones = Array.from((fixture.nativeElement as HTMLElement).querySelectorAll('button')).filter(b => b.textContent?.trim() === 'Asignar indicador del marco');
    expect(botones.length).toBe(1);
    expect(fixture.nativeElement.textContent).not.toContain('+ Nuevo Registro');
    botones[0].click(); fixture.detectChanges();
    expect(component.showMarco).toBeTrue(); expect(component.showModal).toBeFalse();
    expect(fixture.nativeElement.querySelector('app-nueva-asignacion-marco')).toBeTruthy();
    expect(fixture.nativeElement.querySelector('app-modal')).toBeNull();
  });

  it('no utiliza el guardado anterior para crear asignaciones sin un registro existente', () => {
    habilitarGestion();
    const service = TestBed.inject(EvaluacionService);
    const crear = spyOn(service, 'crearAsignacion'), actualizar = spyOn(service, 'actualizarAsignacion');
    component.onModalSave({ unidad_responsable: 10, periodo: 2, indicador: [7], estado: 'pendiente' });
    expect(crear).not.toHaveBeenCalled(); expect(actualizar).not.toHaveBeenCalled();
  });

  it('edita todos los registros operativos existentes sin crear, eliminar o cambiar sus indicadores', () => {
    habilitarGestion();
    const service = TestBed.inject(EvaluacionService);
    const crear = spyOn(service, 'crearAsignacion'), eliminar = spyOn(service, 'eliminarAsignacion');
    const actualizar = spyOn(service, 'actualizarAsignacion').and.returnValue(of({}));
    spyOn(service, 'listarAsignaciones').and.returnValue(of([]));
    component.openEdit({ id: 1, tipo_origen: 'operativo', unidadResponsableId: 10, periodoId: 2, estadoRaw: 'pendiente',
      indicadores: [{ id: 7 }, { id: 8 }], asignaciones: [{ id: 1, indicador: 7 }, { id: 2, indicador: 8 }] });
    expect(component.showModal).toBeTrue();
    expect(component.asignacionFields.some(campo => campo.name === 'indicador')).toBeFalse();
    component.onModalSave({ unidad_responsable: 10, periodo: 2, estado: 'en_progreso', indicador: [99] });
    expect(actualizar.calls.allArgs()).toEqual([
      [1, { unidad_responsable: 10, periodo: 2, estado: 'en_progreso', indicador: 7 }],
      [2, { unidad_responsable: 10, periodo: 2, estado: 'en_progreso', indicador: 8 }],
    ]);
    expect(crear).not.toHaveBeenCalled(); expect(eliminar).not.toHaveBeenCalled();
  });

  it('mantiene la edición operativa en solo consulta al seleccionar un período finalizado', () => {
    habilitarGestion(); component.periodos[0].activo = false;
    component.openEdit({ id: 1, tipo_origen: 'operativo', indicador: 7 });
    expect(component.showModal).toBeFalse();
    expect(component.ocultarAcciones).toEqual(['edit', 'toggle', 'remove']);
  });
});
