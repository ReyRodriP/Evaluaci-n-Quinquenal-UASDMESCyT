import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { EvaluacionService } from '../../../core/services/evaluacion.service';
import { MarcoRelacionado } from '../../../shared/components/marco-relacionado/marco-relacionado';
import { RutaMarco } from '../../../shared/components/ruta-marco/ruta-marco';
import { DocumentosAsignacion } from '../documentos-asignacion/documentos-asignacion';

@Component({
  selector: 'app-asignacion-detalle',
  imports: [CommonModule, RouterLink, MarcoRelacionado, RutaMarco, DocumentosAsignacion],
  templateUrl: './asignacion-detalle.html',
  styleUrl: './asignacion-detalle.css',
})
export class AsignacionDetalle implements OnInit {
  asignacionId = 0;
  periodoId = '';
  asignacion: any = null;
  cargando = false;
  errorCarga = '';

  constructor(
    private route: ActivatedRoute,
    private evaluacionService: EvaluacionService
  ) {}

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    this.periodoId = this.route.snapshot.queryParamMap.get('periodo') || '';
    this.asignacionId = id ? +id : 0;
    if (!this.asignacionId) {
      this.errorCarga = 'Identificador de asignación no válido';
      return;
    }
    this.cargar();
  }

  cargar(): void {
    this.cargando = true;
    this.errorCarga = '';
    const consulta = this.periodoId
      ? this.evaluacionService.obtenerAsignacion(this.asignacionId, this.periodoId)
      : this.evaluacionService.obtenerAsignacion(this.asignacionId);
    consulta.subscribe({
      next: (asignacion) => {
        this.asignacion = asignacion;
        this.cargando = false;
      },
      error: () => {
        this.asignacion = null;
        this.errorCarga = 'No se pudo cargar la asignación';
        this.cargando = false;
      },
    });
  }

  get periodoConsulta(): { periodo: string } | Record<string, never> {
    return this.asignacion?.periodo ? { periodo: String(this.asignacion.periodo) } : {};
  }
}
