import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ToastrModule } from 'ngx-toastr';
import { of } from 'rxjs';
import { RouterTestingModule } from '@angular/router/testing';

import { EvidenciasService } from '../../core/services/evidencias.service';
import { EvaluacionService } from '../../core/services/evaluacion.service';
import { Evidencias } from './evidencias';

describe('Evidencias', () => {
  let component: Evidencias;
  let fixture: ComponentFixture<Evidencias>;

  beforeEach(async () => {
    const evidenciasService = jasmine.createSpyObj<EvidenciasService>('EvidenciasService', ['listarEvidencias', 'crearEvidencia', 'subirVersionEvidencia', 'actualizarEvidencia', 'descargarMasiva']);
    const evaluacionService = jasmine.createSpyObj<EvaluacionService>('EvaluacionService', ['listarPeriodos', 'listarAsignaciones', 'periodoActivo']);
    evidenciasService.listarEvidencias.and.returnValue(of([
      { id_evidencia: 100, asignacion: 1, versiones: [{ id_version: 501, nombre_archivo: 'a.pdf' }] },
      { id_evidencia: 101, asignacion: 2, versiones: [{ id_version: 502, nombre_archivo: 'b.pdf' }] },
    ]));
    evidenciasService.crearEvidencia.and.returnValue(of({ id: 1 }));
    evidenciasService.subirVersionEvidencia.and.returnValue(of({ id: 1 }));
    evidenciasService.actualizarEvidencia.and.returnValue(of({ id: 1 }));
    evaluacionService.listarPeriodos.and.returnValue(of([
      { id: 10, nombre: 'Período actual', activo: true },
      { id: 11, nombre: 'Período anterior', activo: false },
    ]));
    evaluacionService.listarAsignaciones.and.callFake((periodoId) => of([
      {
        id: Number(periodoId) === 11 ? 2 : 1,
        periodo: periodoId,
        unidad_responsable_nombre: Number(periodoId) === 11 ? 'Unidad anterior' : 'Unidad activa',
      },
    ]));
    evaluacionService.periodoActivo.and.returnValue(of({ id: 10, nombre: 'Período actual' }));

    await TestBed.configureTestingModule({
      imports: [Evidencias, HttpClientTestingModule, ToastrModule.forRoot(), RouterTestingModule],
      providers: [
        { provide: EvidenciasService, useValue: evidenciasService },
        { provide: EvaluacionService, useValue: evaluacionService },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(Evidencias);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('loads assignments only for the active period', () => {
    expect(component).toBeTruthy();
    expect(component.rows.map((row) => row.id)).toEqual([1]);
    expect(component.rows[0].evidenciaId).toBe(100);
  });

  it('loads historical assignments as read-only', () => {
    component.onPeriodoChange('11');
    expect(component.rows.map((row) => row.id)).toEqual([2]);
    expect(component.periodoSeleccionadoEsActivo).toBeFalse();
    expect(component.puedeSubir).toBeFalse();
  });

  it('selects only rows with existing evidence and clears selection on period change', () => {
    const row = component.rows[0];
    component.cambiarSeleccionFila(row, { target: { checked: true } } as unknown as Event);
    expect(component.seleccionadas.has(100)).toBeTrue();

    component.onPeriodoChange('11');
    expect(component.rows[0].evidenciaId).toBe(101);
    expect(component.seleccionadas.size).toBe(0);
  });
});