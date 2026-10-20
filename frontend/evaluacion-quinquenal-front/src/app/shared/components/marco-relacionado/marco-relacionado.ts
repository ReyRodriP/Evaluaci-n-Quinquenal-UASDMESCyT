import { Component, Input, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { catchError, of } from 'rxjs';
import { VinculacionService } from '../../../core/services/vinculacion.service';
import { EvaluacionService } from '../../../core/services/evaluacion.service';
import { CatalogoService } from '../../../core/services/catalogo.service';
import { PermisosService } from '../../../core/services/permisos.service';
import { Correspondencia } from '../../../core/models/vinculacion.model';

@Component({
  selector: 'app-marco-relacionado',
  imports: [CommonModule, RouterLink],
  templateUrl: './marco-relacionado.html',
  styleUrl: './marco-relacionado.css',
})
export class MarcoRelacionado implements OnChanges {
  @Input({ required: true }) indicadorId: number | null = null;
  @Input() indicadorNombre = '';

  cargando = false;
  errorCarga = '';
  puedeReintentar = true;
  sinAlcance = false;
  criterioOperativo = '';
  origenTexto = '';
  correspondencias: Correspondencia[] = [];
  naturalezas: Record<string, 'oficial' | 'sintetico'> = {};
  cadenas: Record<
    string,
    {
      dimension: any | null;
      componente: any | null;
      criterio: any | null;
      estandar: any | null;
    }
  > = {};

  constructor(
    private vinculacionService: VinculacionService,
    private evaluacionService: EvaluacionService,
    private catalogoService: CatalogoService,
    private permisos: PermisosService
  ) {}

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['indicadorId'] && this.indicadorId) {
      this.cargar();
    }
  }

  get confirmadas(): Correspondencia[] {
    return this.correspondencias.filter((c) => c.estado === 'confirmada');
  }

  get propuestasPendientes(): number {
    return this.correspondencias.filter((c) => c.estado === 'propuesta').length;
  }

  cadenaDe(corr: Correspondencia):
    | { dimension: any | null; componente: any | null; criterio: any | null; estandar: any | null }
    | null {
    return this.cadenas[String(corr.id)] ?? null;
  }

  etiquetaCadena(nivel: string): string {
    const etiquetas: Record<string, string> = {
      dimension: 'Dimensión',
      componente: 'Componente',
      criterio: 'Criterio del marco',
      estandar: 'Estándar',
    };
    return etiquetas[nivel] ?? nivel;
  }

  textoCadena(nodo: any): string {
    if (!nodo) return '';
    const codigo = nodo.codigo_completo || nodo.codigo || '';
    const texto = nodo.nombre || nodo.redaccion || '';
    if (codigo && texto) return `${codigo} — ${texto}`;
    return codigo || texto;
  }

  get puedeGestionar(): boolean {
    if (this.permisos.esSuperuser) return true;
    const escritura =
      this.permisos.tieneGrupo('Administrador General') || this.permisos.tieneGrupo('Coordinador Quinquenal');
    return (
      escritura &&
      this.permisos.tieneAlgunPermiso(['vinculacion.add_correspondencia', 'vinculacion.change_correspondencia'])
    );
  }

  get nombreOperativo(): string {
    return this.indicadorNombre || this.origenTexto || 'Indicador operativo';
  }

  etiquetaNivel(nivel: string): string {
    const etiquetas: Record<string, string> = {
      dimension: 'Dimensión',
      estandar: 'Estándar',
      indicador_marco: 'Indicador del marco',
    };
    return etiquetas[nivel] ?? nivel;
  }

  naturalezaDe(destino: Correspondencia['destino']): string | null {
    if (!destino) return null;
    const valor = this.naturalezas[String(destino.id)];
    if (valor === 'sintetico') return 'Código sintético (no oficial)';
    if (valor === 'oficial') return 'Código oficial';
    return null;
  }

  cargar(): void {
    if (!this.indicadorId) return;
    const id = this.indicadorId;
    this.cargando = true;
    this.errorCarga = '';
    this.sinAlcance = false;
    this.puedeReintentar = true;
    this.cadenas = {};

    this.evaluacionService.obtenerIndicador(id).pipe(catchError(() => of(null))).subscribe((indicador) => {
      if (indicador) {
        this.criterioOperativo = indicador.criterio_nombre || '';
        if (!this.indicadorNombre && indicador.nombre) {
          this.origenTexto = indicador.nombre;
        }
      }
    });

    this.vinculacionService.contextoIndicador(id).subscribe({
      next: (contexto) => {
        this.origenTexto = contexto.origen?.texto || this.origenTexto;
        this.correspondencias = contexto.correspondencias ?? [];
        this.cargando = false;
        this.cargarNaturalezas();
        this.cargarCadenas();
      },
      error: (err) => {
        this.correspondencias = [];
        this.naturalezas = {};
        this.cadenas = {};
        this.cargando = false;
        if (err?.status === 404) {
          this.sinAlcance = true;
        } else if (err?.status === 403) {
          this.errorCarga = 'No tiene permisos para consultar el contexto de correspondencias';
          this.puedeReintentar = false;
        } else {
          this.errorCarga = 'No se pudo cargar el contexto de correspondencias';
        }
      },
    });
  }

  private cargarCadenas(): void {
    for (const corr of this.confirmadas) {
      if (!corr.destino) continue;
      if (corr.destino.nivel === 'estandar' && typeof corr.destino.id === 'number') {
        this.resolverEstandarParaCadena(String(corr.id), corr.destino.id);
      } else if (corr.destino.nivel === 'indicador_marco' && typeof corr.destino.id === 'number') {
        this.catalogoService
          .obtenerIndicadorMarco(corr.destino.id)
          .pipe(catchError(() => of(null)))
          .subscribe((indicador) => {
            if (indicador && typeof indicador.estandar === 'number') {
              this.resolverEstandarParaCadena(String(corr.id), indicador.estandar);
            }
          });
      }
    }
  }

  private resolverEstandarParaCadena(clave: string, estandarId: number): void {
    this.catalogoService
      .obtenerEstandar(estandarId)
      .pipe(catchError(() => of(null)))
      .subscribe((estandar) => {
        if (!estandar) return;
        this.cadenas = {
          ...this.cadenas,
          [clave]: {
            dimension: estandar.dimension ?? null,
            componente: estandar.componente ?? null,
            criterio: estandar.criterio ?? null,
            estandar: {
              id: estandar.id,
              codigo_completo: estandar.codigo_completo,
              redaccion: estandar.redaccion,
            },
          },
        };
      });
  }

  private cargarNaturalezas(): void {
    this.naturalezas = {};
    this.confirmadas
      .filter((c) => c.destino?.nivel === 'indicador_marco' && c.destino.id)
      .forEach((c) => {
        const destinoId = c.destino!.id;
        this.catalogoService
          .obtenerIndicadorMarco(destinoId)
          .pipe(catchError(() => of(null)))
          .subscribe((indicador) => {
            if (!indicador) return;
            if (indicador.codigo_sintetico) {
              this.naturalezas[String(destinoId)] = 'sintetico';
            } else if (indicador.codigo) {
              this.naturalezas[String(destinoId)] = 'oficial';
            }
          });
      });
  }
}
