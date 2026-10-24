import { Component, Input, OnChanges, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subscription } from 'rxjs';
import { EvaluacionService } from '../../../core/services/evaluacion.service';
import { RegistroHistorialAsignacion } from '../../../core/models/historial-asignacion.model';
import { Pagination } from '../../../shared/components/CRUD/pagination/pagination';

@Component({
  selector: 'app-historial-asignacion',
  imports: [CommonModule, Pagination],
  templateUrl: './historial-asignacion.html',
  styleUrls: ['../../evidencias/evidencia-detalle/evidencia-detalle.css', './historial-asignacion.css'],
})
export class HistorialAsignacion implements OnChanges, OnDestroy {
  @Input({ required: true }) asignacionId = 0;
  @Input() periodoId: number | string = '';
  registros: RegistroHistorialAsignacion[] = [];
  total = 0;
  pagina = 1;
  pageSize = 10;
  cargando = false;
  restringido = false;
  error = '';
  private consulta?: Subscription;

  constructor(private evaluacion: EvaluacionService) {}
  ngOnChanges(): void { this.cargar(); }
  ngOnDestroy(): void { this.consulta?.unsubscribe(); }

  cargar(pagina = 1): void {
    this.consulta?.unsubscribe(); this.registros = []; this.total = 0; this.error = ''; this.restringido = false;
    this.pagina = pagina;
    if (!this.asignacionId) { this.cargando = false; return; }
    this.cargando = true;
    this.consulta = this.evaluacion.historialAsignacion(this.asignacionId, this.periodoId, pagina, this.pageSize).subscribe({
      next: datos => {
        this.registros = datos.results; this.total = datos.count; this.pagina = datos.page; this.pageSize = datos.page_size;
        this.cargando = false;
      },
      error: err => {
        this.cargando = false;
        if (err.status === 403) this.restringido = true;
        else this.error = 'No se pudo consultar el historial global o perdió el acceso a esta asignación.';
      },
    });
  }

  autor(registro: RegistroHistorialAsignacion): string {
    return registro.usuario_nombre?.trim() || registro.usuario_identificador || 'Sin cuenta asociada';
  }
}
