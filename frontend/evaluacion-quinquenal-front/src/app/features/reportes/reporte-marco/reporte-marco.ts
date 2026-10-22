import { Component, EventEmitter, Input, OnChanges, OnDestroy, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subscription } from 'rxjs';
import { ReportesService } from '../../../core/services/reportes.service';
import { ReporteResultadosMarco } from '../../../core/models/resultados-marco.model';
import { Pagination } from '../../../shared/components/CRUD/pagination/pagination';

@Component({
  selector: 'app-reporte-marco',
  imports: [CommonModule, FormsModule, Pagination],
  templateUrl: './reporte-marco.html',
  styleUrls: ['../reportes.css', './reporte-marco.css'],
})
export class ReporteMarco implements OnChanges, OnDestroy {
  @Input() periodoId = '';
  @Input() periodos: any[] = [];
  @Input() unidades: any[] = [];
  @Output() periodoChange = new EventEmitter<string>();
  datos: ReporteResultadosMarco | null = null;
  filtros = { agrupar: 'dimension', dimension: '', estandar: '', unidad: '' };
  cargando = false;
  exportando = false;
  error = '';
  pagina = 1;
  pageSize = 10;
  private consulta?: Subscription;
  private exportacion?: Subscription;

  constructor(private reportes: ReportesService) {}

  ngOnChanges(changes: any): void {
    if (changes.periodoId) {
      this.filtros.dimension = ''; this.filtros.estandar = ''; this.filtros.unidad = '';
      this.exportacion?.unsubscribe(); this.exportando = false;
      this.cargar();
    }
  }
  ngOnDestroy(): void { this.consulta?.unsubscribe(); this.exportacion?.unsubscribe(); }

  get estandaresDisponibles() {
    return (this.datos?.opciones.estandares ?? []).filter(e => !this.filtros.dimension || String(e.dimension_id) === this.filtros.dimension);
  }

  parametros(): Record<string, string> {
    const params: Record<string, string> = { periodo: this.periodoId };
    for (const [campo, valor] of Object.entries(this.filtros)) if (valor) params[campo] = valor;
    return params;
  }

  cargar(pagina = 1): void {
    this.consulta?.unsubscribe(); this.exportacion?.unsubscribe(); this.exportando = false;
    this.pagina = pagina; this.datos = null; this.error = '';
    if (!this.periodoId) { this.cargando = false; return; }
    this.cargando = true;
    this.consulta = this.reportes.reporteMarco({ ...this.parametros(), page: String(pagina), page_size: String(this.pageSize) }).subscribe({
      next: datos => { this.datos = datos; this.cargando = false; },
      error: () => { this.cargando = false; this.error = 'No se pudo consultar el reporte del marco o perdió el acceso a este período.'; },
    });
  }

  cambiarDimension(valor: string): void { this.filtros.dimension = valor; this.filtros.estandar = ''; this.cargar(); }
  cambiarUnidad(valor: string): void { this.filtros.unidad = valor; this.filtros.dimension = ''; this.filtros.estandar = ''; this.cargar(); }
  limpiar(): void { this.filtros = { agrupar: 'dimension', dimension: '', estandar: '', unidad: '' }; this.cargar(); }

  exportar(formato: 'csv' | 'xlsx' | 'pdf'): void {
    if (this.cargando || this.exportando || !this.datos?.total) return;
    this.exportando = true; this.error = '';
    this.exportacion = this.reportes.exportarReporte('marco', formato, this.parametros()).subscribe({
      next: blob => {
        const url = URL.createObjectURL(blob);
        const enlace = document.createElement('a');
        enlace.href = url; enlace.download = `resultados_marco_${this.periodoId}_${this.filtros.agrupar}.${formato}`;
        enlace.click(); URL.revokeObjectURL(url); this.exportando = false;
      },
      error: () => { this.exportando = false; this.error = 'No se pudo exportar el reporte. Vuelva a consultar para verificar su acceso.'; this.datos = null; },
    });
  }
}
