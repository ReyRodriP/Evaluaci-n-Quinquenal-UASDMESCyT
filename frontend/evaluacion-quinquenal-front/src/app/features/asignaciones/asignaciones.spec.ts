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
});
