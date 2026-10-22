import { Component, EventEmitter, Input, OnChanges, OnDestroy, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { Subscription } from 'rxjs';
import { EvaluacionService } from '../../../core/services/evaluacion.service';
import { ContextoAsignacionMarco } from '../../../core/models/contexto-asignacion-marco.model';
import { RutaMarco } from '../../../shared/components/ruta-marco/ruta-marco';

@Component({
  selector: 'app-nueva-asignacion-marco',
  imports: [CommonModule, FormsModule, RouterLink, RutaMarco],
  templateUrl: './nueva-asignacion-marco.html',
  styleUrls: ['../../evidencias/evidencia-detalle/evidencia-detalle.css', './nueva-asignacion-marco.css'],
})
export class NuevaAsignacionMarco implements OnChanges, OnDestroy {
  @Input({ required: true }) periodoId = '';
  @Output() creada = new EventEmitter<any>();
  @Output() cerrar = new EventEmitter<void>();
  contexto: ContextoAsignacionMarco | null = null;
  cargando = false;
  guardando = false;
  error = '';
  dimension = ''; componente = ''; criterio = ''; estandar = ''; indicador = '';
  unidad = ''; encargado = '';
  private consulta?: Subscription;
  private guardado?: Subscription;

  constructor(private evaluacion: EvaluacionService) {}
  ngOnChanges(): void { this.dimension = ''; this.componente = ''; this.criterio = ''; this.estandar = ''; this.indicador = ''; this.unidad = ''; this.encargado = ''; this.cargar(); }
  ngOnDestroy(): void { this.consulta?.unsubscribe(); this.guardado?.unsubscribe(); }

  cargar(): void {
    this.consulta?.unsubscribe(); this.contexto = null; this.error = '';
    if (!this.periodoId) return;
    this.cargando = true;
    this.consulta = this.evaluacion.contextoAsignacionMarco(this.periodoId, this.unidad || undefined).subscribe({
      next: contexto => {
        this.contexto = contexto; this.cargando = false;
        if (!contexto.indicadores.some(i => String(i.id) === this.indicador)) this.indicador = '';
      },
      error: err => { this.cargando = false; this.error = this.mensajeError(err); },
    });
  }

  get indicadoresFiltrados() {
    return (this.contexto?.indicadores ?? []).filter(i =>
      (!this.dimension || String(i.ruta.dimension.id) === this.dimension) &&
      (!this.componente || String(i.ruta.componente.id) === this.componente) &&
      (!this.criterio || String(i.ruta.criterio.id) === this.criterio) &&
      (!this.estandar || String(i.ruta.estandar.id) === this.estandar));
  }
  opciones(nivel: 'dimension' | 'componente' | 'criterio' | 'estandar'): any[] {
    const campos = ['dimension', 'componente', 'criterio', 'estandar'] as const;
    const indice = campos.indexOf(nivel);
    const candidatas = (this.contexto?.indicadores ?? []).filter(i => campos.slice(0, indice).every(campo => !this[campo] || String(i.ruta[campo].id) === this[campo]));
    return [...new Map(candidatas.map(i => [i.ruta[nivel].id, i.ruta[nivel]])).values()];
  }
  cambiarJerarquia(nivel: 'dimension' | 'componente' | 'criterio' | 'estandar', valor: string): void {
    this[nivel] = valor;
    const campos = ['dimension', 'componente', 'criterio', 'estandar', 'indicador'] as const;
    for (const campo of campos.slice(campos.indexOf(nivel) + 1)) this[campo] = '';
  }
  cambiarUnidad(valor: string): void { this.unidad = valor; this.encargado = ''; this.cargar(); }
  get seleccionado() { return this.indicadoresFiltrados.find(i => String(i.id) === this.indicador); }
  get existente() { return this.contexto?.asignaciones_existentes.find(a => String(a.indicador_marco) === this.indicador); }
  get puedeGuardar(): boolean {
    return !this.cargando && !this.guardando && !!this.seleccionado && !!this.unidad
      && !!this.contexto?.encargados.some(u => String(u.id) === this.encargado) && !this.existente;
  }
  guardar(): void {
    if (!this.puedeGuardar) return;
    this.guardando = true; this.error = '';
    this.guardado = this.evaluacion.crearAsignacion({ periodo: Number(this.periodoId), indicador_marco: Number(this.indicador),
      unidad_responsable: Number(this.unidad), encargado: Number(this.encargado) }).subscribe({
      next: asignacion => { this.guardando = false; this.creada.emit(asignacion); },
      error: err => { this.guardando = false; this.error = this.mensajeError(err); },
    });
  }
  private mensajeError(err: any): string {
    const detalle = err?.error;
    if (typeof detalle === 'string') return detalle;
    if (detalle && typeof detalle === 'object') return Object.values(detalle).flat().map(String).join(' ');
    return 'No se pudo preparar o guardar la asignación. Vuelva a consultar para verificar sus permisos y el período.';
  }
}
