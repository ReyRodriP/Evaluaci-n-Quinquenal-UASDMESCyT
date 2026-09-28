import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ToastrModule } from 'ngx-toastr';
import { of } from 'rxjs';

import { EvidenciasService } from '../../core/services/evidencias.service';
import { EvaluacionService } from '../../core/services/evaluacion.service';
import { Evidencias } from './evidencias';

describe('Evidencias', () => {
  let component: Evidencias;
  let fixture: ComponentFixture<Evidencias>;

  beforeEach(async () => {
    const evidenciasService = jasmine.createSpyObj<EvidenciasService>('EvidenciasService', ['listarEvidencias', 'crearEvidencia', 'subirVersionEvidencia', 'actualizarEvidencia']);
    const evaluacionService = jasmine.createSpyObj<EvaluacionService>('EvaluacionService', ['listarAsignaciones']);
    evidenciasService.listarEvidencias.and.returnValue(of([]));
    evidenciasService.crearEvidencia.and.returnValue(of({ id: 1 }));
    evidenciasService.subirVersionEvidencia.and.returnValue(of({ id: 1 }));
    evidenciasService.actualizarEvidencia.and.returnValue(of({ id: 1 }));
    evaluacionService.listarAsignaciones.and.returnValue(of([]));

    await TestBed.configureTestingModule({
      imports: [Evidencias, HttpClientTestingModule, ToastrModule.forRoot()],
      providers: [
        { provide: EvidenciasService, useValue: evidenciasService },
        { provide: EvaluacionService, useValue: evaluacionService },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(Evidencias);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create and initialize the evidence rows', () => {
    expect(component).toBeTruthy();
    expect(component.rows).toEqual([]);
  });
});