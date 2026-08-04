import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ToastrService } from 'ngx-toastr';
import { AuthService } from '../auth/services/auth-service';

@Component({
  selector: 'app-notificaciones',
  imports: [CommonModule],
  templateUrl: './notificaciones.html',
  styleUrl: './notificaciones.css',
})
export class Notificaciones implements OnInit {
  notificaciones: any[] = []
  loading = false
  marcandoTodas = false

  constructor(
    private authService: AuthService,
    private toast: ToastrService
  ) {}

  ngOnInit(): void {
    this.cargar()
  }

  cargar(): void {
    this.loading = true
    this.authService.listarNotificaciones().subscribe({
      next: (data) => {
        this.notificaciones = data
        this.loading = false
      },
      error: () => {
        this.toast.error('No se pudieron cargar las notificaciones')
        this.loading = false
      },
    })
  }

  get pendientes(): number {
    return this.notificaciones.filter(n => !n.leida).length
  }

  marcarLeida(n: any): void {
    if (n.leida) return
    this.authService.marcarNotificacionLeida(n.id).subscribe({
      next: () => n.leida = true,
      error: () => this.toast.error('No se pudo marcar como leída'),
    })
  }

  marcarTodas(): void {
    this.marcandoTodas = true
    this.authService.marcarTodasLeidas().subscribe({
      next: () => {
        this.notificaciones.forEach(n => n.leida = true)
        this.marcandoTodas = false
        this.toast.success('Todas las notificaciones marcadas como leídas')
      },
      error: () => {
        this.marcandoTodas = false
        this.toast.error('No se pudieron marcar como leídas')
      },
    })
  }
}
