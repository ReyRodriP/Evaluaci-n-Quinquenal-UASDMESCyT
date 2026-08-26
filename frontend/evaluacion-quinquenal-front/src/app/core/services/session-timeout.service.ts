import { Injectable, OnDestroy } from '@angular/core';
import { Router } from '@angular/router';
import { ActiveToast, ToastrService } from 'ngx-toastr';
import { AuthService } from '../../features/auth/services/auth-service';

@Injectable({
  providedIn: 'root',
})
export class SessionTimeoutService implements OnDestroy {
  private readonly IDLE_MINUTOS = 50;
  private readonly TIEMPO_AVISO_SEG = 120;

  private activo = false;
  private timerId: any = null;
  private timerAviso: any = null;
  private ultimaActividad = 0;
  private limpiadores: Array<() => void> = [];
  private avisoRef: ActiveToast<any> | null = null;

  constructor(
    private router: Router,
    private authService: AuthService,
    private toast: ToastrService
  ) {}

  iniciar(): void {
    if (this.activo || !this.authService.isLoggedIn()) return;
    this.activo = true;
    this.registrarEventos();
    this.reiniciarTemporizador();
  }

  detener(): void {
    this.activo = false;
    this.limpiarTemporizadores();
    this.cerrarAviso();
    this.limpiadores.forEach((fn) => fn());
    this.limpiadores = [];
  }

  ngOnDestroy(): void {
    this.detener();
  }

  private registrarEventos(): void {
    const eventos = ['mousemove', 'mousedown', 'keydown', 'wheel', 'touchstart', 'scroll'];
    const onActividad = () => this.reiniciarTemporizador();
    eventos.forEach((nombre) => {
      window.addEventListener(nombre, onActividad, { passive: true });
      this.limpiadores.push(() => window.removeEventListener(nombre, onActividad));
    });
  }

  private reiniciarTemporizador(): void {
    if (!this.activo) return;
    const ahora = Date.now();
    if (ahora - this.ultimaActividad < 1000) return;
    this.ultimaActividad = ahora;
    this.limpiarTemporizadores();
    this.cerrarAviso();
    this.timerAviso = setTimeout(
      () => this.mostrarAviso(),
      (this.IDLE_MINUTOS * 60 - this.TIEMPO_AVISO_SEG) * 1000
    );
    this.timerId = setTimeout(() => this.cerrarSesion(), this.IDLE_MINUTOS * 60 * 1000);
  }

  private limpiarTemporizadores(): void {
    if (this.timerAviso) {
      clearTimeout(this.timerAviso);
      this.timerAviso = null;
    }
    if (this.timerId) {
      clearTimeout(this.timerId);
      this.timerId = null;
    }
  }

  private cerrarAviso(): void {
    if (this.avisoRef) {
      this.toast.clear(this.avisoRef.toastId);
      this.avisoRef = null;
    }
  }

  private mostrarAviso(): void {
    if (!this.activo || this.avisoRef) return;
    this.avisoRef = this.toast.warning(
      `Su sesión se cerrará en ${this.TIEMPO_AVISO_SEG / 60} minutos si no hay actividad.`,
      'Sesión por expirar',
      { timeOut: this.TIEMPO_AVISO_SEG * 1000, extendedTimeOut: 0 }
    );
  }

  private cerrarSesion(): void {
    this.detener();
    this.authService.logoutApi().subscribe({
      next: () => this.redirigirLogin(),
      error: () => this.redirigirLogin(),
    });
  }

  private redirigirLogin(): void {
    this.authService.logout();
    this.router.navigate(['/auth/login']);
  }
}
