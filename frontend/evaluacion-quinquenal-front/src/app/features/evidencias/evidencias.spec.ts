import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ToastrModule } from 'ngx-toastr';
import { of } from 'rxjs';

import { AuthService } from '../../core/services/auth.service';
import { Evidencias } from './evidencias';

describe('Evidencias', () => {
  let component: Evidencias;
  let fixture: ComponentFixture<Evidencias>;

  beforeEach(async () => {
    const authService = jasmine.createSpyObj<AuthService>('AuthService', ['listarAsignaciones', 'listarEvidencias', 'crearEvidencia', 'subirVersionEvidencia', 'actualizarEvidencia']);
    authService.listarAsignaciones.and.returnValue(of([]));
    authService.listarEvidencias.and.returnValue(of([]));
    authService.crearEvidencia.and.returnValue(of({ id: 1 }));
    authService.subirVersionEvidencia.and.returnValue(of({ id: 1 }));
    authService.actualizarEvidencia.and.returnValue(of({ id: 1 }));

    await TestBed.configureTestingModule({
      imports: [Evidencias, HttpClientTestingModule, ToastrModule.forRoot()],
      providers: [{ provide: AuthService, useValue: authService }]
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
