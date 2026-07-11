import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../../../core/services/api.service';
import { AuthService } from '../../../auth/services/auth-service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.css',
})
export class Dashboard implements OnInit {
  stats = {
    usuarios: 0,
    facultades: 0,
    departamentos: 0,
    periodos: 0,
    criterios: 0,
    indicadores: 0,
    asignaciones: 0,
    evidencias: 0,
    pendientes: 0,
    completadas: 0
  };

  constructor(private api: ApiService, public auth: AuthService) {}

  ngOnInit() {
    this.api.getUsuarios().subscribe(data => this.stats.usuarios = data.length);
    this.api.getFacultades().subscribe(data => this.stats.facultades = data.length);
    this.api.getDepartamentos().subscribe(data => this.stats.departamentos = data.length);
    this.api.getPeriodos().subscribe(data => this.stats.periodos = data.length);
    this.api.getCriterios().subscribe(data => this.stats.criterios = data.length);
    this.api.getIndicadores().subscribe(data => this.stats.indicadores = data.length);
    this.api.getAsignaciones().subscribe(data => {
      this.stats.asignaciones = data.length;
      this.stats.pendientes = data.filter(a => a.estado === 'pendiente' || a.estado === 'en_progreso').length;
      this.stats.completadas = data.filter(a => a.estado === 'completado' || a.estado === 'aprobado').length;
    });
    this.api.getEvidencias().subscribe(data => this.stats.evidencias = data.length);
  }

  get user() {
    return this.auth.getCurrentUser();
  }
}
