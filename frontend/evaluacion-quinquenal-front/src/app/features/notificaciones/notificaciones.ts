import { Component, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { Subscription } from 'rxjs';
import { ToastrService } from 'ngx-toastr';
import { NotificacionesService } from '../../core/services/notificaciones.service';
import { destinoNotificacion } from '../../core/models/notificacion.model';

@Component({
  selector: 'app-notificaciones',
  imports: [CommonModule],
  templateUrl: './notificaciones.html',
  styleUrl: './notificaciones.css',
})
export class Notificaciones implements OnInit, OnDestroy {
  notificaciones: any[] = []
  loading = false
  marcandoTodas = false
  abriendo = new Set<number>()
  destinoNotificacion = destinoNotificacion
  private consulta?: Subscription
  private operaciones = new Subscription()

  constructor(
    private notificacionesService: NotificacionesService,
    private toast: ToastrService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.cargar()
  }

  cargar(): void {
    this.consulta?.unsubscribe()
    this.notificaciones = []
    this.loading = true
    this.consulta = this.notificacionesService.listarNotificaciones().subscribe({
      next: (data) => {
        this.notificaciones = data ?? []
        this.loading = false
      },
      error: () => {
        this.notificaciones = []
        this.toast.error('No se pudieron cargar las notificaciones')
        this.loading = false
      },
    })
  }

  ngOnDestroy(): void { this.consulta?.unsubscribe(); this.operaciones.unsubscribe() }

  abrir(n: any): void {
    if (!destinoNotificacion(n) || this.abriendo.has(n.id)) return
    this.abriendo.add(n.id)
    this.operaciones.add(this.notificacionesService.marcarNotificacionLeida(n.id).subscribe({
      next: actualizada => {
        this.abriendo.delete(n.id)
        n.leida = true
        n.destino = actualizada.destino ?? null
        const destino = destinoNotificacion(actualizada)
        if (destino) void this.router.navigate(destino.comandos, { queryParams: destino.queryParams })
      },
      error: () => {
        this.abriendo.delete(n.id)
        this.toast.error('El aviso ya no está disponible en su alcance')
        this.cargar()
      },
    }))
  }

  get pendientes(): number {
    return this.notificaciones.filter(n => !n.leida).length
  }

  marcarLeida(n: any): void {
    if (n.leida || this.abriendo.has(n.id)) return
    this.operaciones.add(this.notificacionesService.marcarNotificacionLeida(n.id).subscribe({
      next: () => n.leida = true,
      error: () => { this.toast.error('No se pudo marcar como leída'); this.cargar() },
    }))
  }

  marcarTodas(): void {
    this.marcandoTodas = true
    this.operaciones.add(this.notificacionesService.marcarTodasLeidas().subscribe({
      next: () => {
        this.notificaciones.forEach(n => n.leida = true)
        this.marcandoTodas = false
        this.toast.success('Todas las notificaciones marcadas como leídas')
      },
      error: () => {
        this.marcandoTodas = false
        this.toast.error('No se pudieron marcar como leídas')
      },
    }))
  }
}
