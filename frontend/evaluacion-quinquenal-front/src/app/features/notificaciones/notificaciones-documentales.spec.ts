import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';
import { of, Subject, throwError } from 'rxjs';
import { ToastrService } from 'ngx-toastr';
import { Notificaciones } from './notificaciones';
import { NotificacionesService } from '../../core/services/notificaciones.service';

describe('Notificaciones documentales', () => {
  let fixture: ComponentFixture<Notificaciones>;
  let component: Notificaciones;
  let service: jasmine.SpyObj<NotificacionesService>;
  const aviso = () => ({ id: 8, titulo: 'Documento enviado a revisión', mensaje: 'Documento de prueba', leida: false,
    destino: { asignacion_id: 27, periodo_id: 2, solicitud_id: 4, version_id: 9 } });
  const anterior = () => ({ id: 7, titulo: 'Anterior', mensaje: 'https://example.test/avisos', leida: false, destino: null });

  beforeEach(async () => {
    service = jasmine.createSpyObj('NotificacionesService', ['listarNotificaciones', 'marcarNotificacionLeida', 'marcarTodasLeidas']);
    service.listarNotificaciones.and.returnValue(of([aviso(), anterior()]));
    await TestBed.configureTestingModule({ imports: [Notificaciones, RouterTestingModule], providers: [
      { provide: NotificacionesService, useValue: service },
      { provide: ToastrService, useValue: { error: () => {}, success: () => {} } },
    ] }).compileComponents();
    fixture = TestBed.createComponent(Notificaciones); component = fixture.componentInstance; fixture.detectChanges();
  });

  it('ofrece detalle solo para destinos estructurados, sin interpretar URLs del mensaje', () => {
    expect(fixture.nativeElement.querySelectorAll('.notif-abrir').length).toBe(1);
    expect(fixture.nativeElement.querySelectorAll('a').length).toBe(0);
    component.notificaciones = [{ ...anterior(), destino: { url: 'javascript:alert(1)' } }]; fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('.notif-abrir')).toBeNull();
  });

  it('revalida incluso un aviso leído y utiliza el destino devuelto al abrirlo', () => {
    const n = { ...aviso(), leida: true };
    service.marcarNotificacionLeida.and.returnValue(of({ ...n, destino: { ...n.destino, version_id: 10 } }));
    const navegar = spyOn(TestBed.inject(Router), 'navigate').and.resolveTo(true);
    component.abrir(n);
    expect(service.marcarNotificacionLeida).toHaveBeenCalledWith(8);
    expect(navegar).toHaveBeenCalledWith(['/asignaciones', 27, 'detalle'], { queryParams: { periodo: 2, documento: 4, version_documento: 10 } });
  });

  it('no navega al destino anterior si el servidor retira el acceso', () => {
    service.marcarNotificacionLeida.and.returnValue(throwError(() => ({ status: 404 })));
    service.listarNotificaciones.and.returnValue(of([anterior()]));
    const navegar = spyOn(TestBed.inject(Router), 'navigate').and.resolveTo(true);
    component.abrir(aviso()); fixture.detectChanges();
    expect(navegar).not.toHaveBeenCalled();
    expect(component.notificaciones.map(n => n.id)).toEqual([7]);
    expect(fixture.nativeElement.querySelector('.notif-abrir')).toBeNull();
  });

  it('evita aperturas duplicadas y cancela la navegación si se abandona la pantalla', () => {
    const apertura = new Subject<any>(); service.marcarNotificacionLeida.and.returnValue(apertura);
    const navegar = spyOn(TestBed.inject(Router), 'navigate').and.resolveTo(true);
    component.abrir(aviso()); component.abrir(aviso());
    expect(service.marcarNotificacionLeida).toHaveBeenCalledTimes(1);
    fixture.destroy(); apertura.next(aviso()); apertura.complete();
    expect(navegar).not.toHaveBeenCalled();
  });
});
