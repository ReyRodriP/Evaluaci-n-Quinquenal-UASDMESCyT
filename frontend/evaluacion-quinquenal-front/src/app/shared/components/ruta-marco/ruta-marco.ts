import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RutaMarcoAsignacion } from '../../../core/models/asignacion-marco.model';

@Component({
  selector: 'app-ruta-marco',
  imports: [CommonModule],
  template: `
    <section *ngIf="ruta" aria-label="Ruta del indicador en el marco de evaluación" class="ruta-marco">
      <h3>Asignación directa al marco de evaluación</h3>
      <p><strong>Versión seleccionada:</strong> {{ ruta.version.nombre }}</p>
      <dl>
        <dt>Dimensión</dt><dd>{{ ruta.dimension.codigo }} — {{ ruta.dimension.nombre }}</dd>
        <dt>Componente</dt><dd>{{ ruta.componente.codigo }} — {{ ruta.componente.nombre }}</dd>
        <dt>Criterio del marco</dt><dd>{{ ruta.criterio.codigo }} — {{ ruta.criterio.nombre }}</dd>
        <dt>Estándar</dt><dd>{{ ruta.estandar.codigo }} — {{ ruta.estandar.nombre }}</dd>
        <dt>Indicador</dt><dd>{{ ruta.indicador.nombre }}</dd>
      </dl>
      <p *ngIf="ruta.indicador.codigo_sintetico"><strong>Identificador interno, no oficial:</strong> {{ ruta.indicador.codigo }}</p>
    </section>
  `,
  styles: `
    .ruta-marco { padding: 1rem; margin-block: 1rem; border: 1px solid var(--border-color, #d1d5db); border-radius: .5rem; overflow-wrap: anywhere; }
    dt { font-weight: 600; margin-top: .5rem; } dd { margin-left: 0; }
  `,
})
export class RutaMarco {
  @Input() ruta: RutaMarcoAsignacion | null = null;
}
