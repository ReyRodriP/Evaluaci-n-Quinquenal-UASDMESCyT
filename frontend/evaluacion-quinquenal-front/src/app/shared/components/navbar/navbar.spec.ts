import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Navbar } from './navbar';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { ToastrModule } from 'ngx-toastr';
import { Router } from '@angular/router';
import { of } from 'rxjs';
import { NotificacionesService } from '../../../core/services/notificaciones.service';

describe('Navbar', () => {
  let component: Navbar;
  let fixture: ComponentFixture<Navbar>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Navbar, ToastrModule.forRoot(), RouterTestingModule],
      providers: [provideHttpClient(), provideHttpClientTesting()]
    })
    .compileComponents();

    fixture = TestBed.createComponent(Navbar);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('abre un aviso documental con el destino autorizado devuelto por el servidor', () => {
    component.notificaciones = [{ id: 8, leida: false }]; component.dropdownOpen = true;
    spyOn(TestBed.inject(NotificacionesService), 'marcarNotificacionLeida').and.returnValue(of({
      id: 8, leida: true, destino: { asignacion_id: 27, periodo_id: 2, solicitud_id: 4, version_id: 9 },
    }));
    const navegar = spyOn(TestBed.inject(Router), 'navigate').and.resolveTo(true);
    component.marcarYcerrar(8);
    expect(component.notificaciones[0].leida).toBeTrue(); expect(component.dropdownOpen).toBeFalse();
    expect(navegar).toHaveBeenCalledWith(['/asignaciones', 27, 'detalle'], { queryParams: { periodo: 2, documento: 4, version_documento: 9 } });
  });

  it('mantiene el marcado de lectura de avisos anteriores sin inventar un destino', () => {
    component.notificaciones = [{ id: 7, leida: false }];
    spyOn(TestBed.inject(NotificacionesService), 'marcarNotificacionLeida').and.returnValue(of({ id: 7, leida: true, destino: null }));
    const navegar = spyOn(TestBed.inject(Router), 'navigate').and.resolveTo(true);
    component.marcarYcerrar(7);
    expect(component.notificaciones[0].leida).toBeTrue(); expect(navegar).not.toHaveBeenCalled();
  });
});
