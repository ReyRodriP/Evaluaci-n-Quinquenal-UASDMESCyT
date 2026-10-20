import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { ToastrService } from 'ngx-toastr';
import { VinculacionService } from '../../core/services/vinculacion.service';
import { PermisosService } from '../../core/services/permisos.service';
import {
  Correspondencia,
  EstadoCorrespondencia,
  FiltroCorrespondencias,
  RespuestaPaginada,
} from '../../core/models/vinculacion.model';

type AccionTransicion = 'confirmar' | 'rechazar' | 'desconfirmar';

/**
 * @brief Bandeja de gestión de correspondencias (vínculos EQ-SIDACES).
 * @details Consulta propuestas, confirmadas y rechazadas con filtros de
 * estado y paginación. Las acciones de estado se ejecutan siempre detrás
 * de un paso de confirmación inline y se aplican con la respuesta real
 * del servidor (sin asumir éxito).
 */
@Component({
  selector: 'app-vinculacion',
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './vinculacion.html',
  styleUrl: './vinculacion.css',
})
export class Vinculacion implements OnInit {
  estadoFiltro: EstadoCorrespondencia | '' = '';
  pagina = 1;
  respuesta: RespuestaPaginada<Correspondencia> | null = null;
  cargando = false;
  error = '';
  sinPermiso = false;

  transicion: { id: number; accion: AccionTransicion; comentario: string } | null = null;
  enTransicionId: number | null = null;
  errorTransicion = '';

  constructor(
    private vinculacionService: VinculacionService,
    private permisos: PermisosService,
    private toast: ToastrService
  ) {}

  ngOnInit(): void {
    this.cargar();
  }

  get puedeTransicionar(): boolean {
    const rolEscritura =
      this.permisos.tieneGrupo('Administrador General') || this.permisos.tieneGrupo('Coordinador Quinquenal');
    return (
      this.permisos.esSuperuser || (this.permisos.tienePermiso('vinculacion.change_correspondencia') && rolEscritura)
    );
  }

  get hayAnterior(): boolean {
    return this.pagina > 1;
  }

  get haySiguiente(): boolean {
    return !!this.respuesta?.next;
  }

  get tituloEstado(): string {
    const titulos: Record<string, string> = {
      '': 'Todas las correspondencias',
      propuesta: 'Propuestas pendientes',
      confirmada: 'Correspondencias confirmadas',
      rechazada: 'Correspondencias rechazadas',
    };
    return titulos[this.estadoFiltro] ?? 'Correspondencias';
  }

  cargar(): void {
    this.cargando = true;
    this.error = '';
    this.sinPermiso = false;
    const filtro: FiltroCorrespondencias = { page: this.pagina };
    if (this.estadoFiltro) filtro.estado = this.estadoFiltro;
    this.vinculacionService.listarCorrespondencias(filtro).subscribe({
      next: (respuesta) => {
        this.respuesta = respuesta;
        this.cargando = false;
      },
      error: (err) => {
        this.respuesta = null;
        this.cargando = false;
        if (err?.status === 403) {
          this.sinPermiso = true;
          return;
        }
        this.error = 'No se pudieron cargar las correspondencias. Verifique su conexión e inténtelo de nuevo.';
      },
    });
  }

  seleccionarEstado(estado: EstadoCorrespondencia | ''): void {
    if (this.estadoFiltro === estado) return;
    this.estadoFiltro = estado;
    this.pagina = 1;
    this.limpiarTransicion();
    this.cargar();
  }

  irPagina(pagina: number): void {
    if (pagina < 1 || pagina === this.pagina) return;
    this.pagina = pagina;
    this.limpiarTransicion();
    this.cargar();
  }

  iniciarTransicion(corr: Correspondencia, accion: AccionTransicion): void {
    this.errorTransicion = '';
    this.transicion = { id: corr.id, accion, comentario: '' };
  }

  cancelarTransicion(): void {
    if (this.enTransicionId != null) return;
    this.limpiarTransicion();
  }

  ejecutarTransicion(): void {
    if (!this.transicion || this.enTransicionId != null) return;
    const { id, accion } = this.transicion;
    const comentario = this.transicion.comentario.trim();
    if (accion !== 'confirmar' && !comentario) {
      this.errorTransicion = 'El comentario es obligatorio para esta operación';
      return;
    }
    this.enTransicionId = id;
    this.errorTransicion = '';
    const peticion =
      accion === 'confirmar'
        ? this.vinculacionService.confirmarCorrespondencia(id)
        : accion === 'rechazar'
          ? this.vinculacionService.rechazarCorrespondencia(id, comentario)
          : this.vinculacionService.desconfirmarCorrespondencia(id, comentario);
    peticion.subscribe({
      next: (actualizada) => {
        this.enTransicionId = null;
        this.transicion = null;
        this.errorTransicion = '';
        this.toast.success(this.mensajeExito(accion));
        this.aplicarRespuesta(actualizada);
      },
      error: (err) => {
        this.enTransicionId = null;
        this.errorTransicion = this.mensajeError(err, 'No se pudo completar la operación');
      },
    });
  }

  etiquetaEstado(estado: EstadoCorrespondencia): string {
    const etiquetas: Record<EstadoCorrespondencia, string> = {
      propuesta: 'Propuesta (pendiente de validación)',
      confirmada: 'Confirmada',
      rechazada: 'Rechazada',
    };
    return etiquetas[estado] ?? estado;
  }

  claseEstado(estado: EstadoCorrespondencia): string {
    return `badge-${estado}`;
  }

  etiquetaProcedencia(procedencia: string): string {
    return procedencia === 'derivada' ? 'Sugerida por el sistema (requiere validación)' : 'Captura manual';
  }

  etiquetaNivel(nivel: string): string {
    const etiquetas: Record<string, string> = {
      dimension: 'Dimensión del marco',
      estandar: 'Estándar del marco',
      indicador_marco: 'Indicador del marco',
      criterio: 'Criterio operativo',
      indicador: 'Indicador operativo',
    };
    return etiquetas[nivel] ?? nivel;
  }

  rutaOrigen(corr: Correspondencia): any[] | null {
    if (!corr.origen) return null;
    if (corr.origen.nivel === 'indicador') return ['/indicadores', corr.origen.id, 'detalle'];
    if (corr.origen.nivel === 'criterio' && this.permisos.puedeAccederRuta('/criterios')) return ['/criterios'];
    return null;
  }

  private aplicarRespuesta(actualizada: Correspondencia): void {
    if (!this.respuesta) return;
    if (this.estadoFiltro && actualizada.estado !== this.estadoFiltro) {
      this.cargar();
      return;
    }
    this.respuesta = {
      ...this.respuesta,
      results: this.respuesta.results.map((corr) => (corr.id === actualizada.id ? actualizada : corr)),
    };
  }

  private limpiarTransicion(): void {
    this.transicion = null;
    this.errorTransicion = '';
  }

  private mensajeExito(accion: AccionTransicion): string {
    if (accion === 'confirmar') return 'Correspondencia confirmada';
    if (accion === 'rechazar') return 'Correspondencia rechazada';
    return 'Correspondencia devuelta a propuesta';
  }

  private mensajeError(err: any, fallback: string): string {
    if (err?.status === 403) {
      return 'No tiene permisos para realizar esta operación';
    }
    const detalle = err?.error;
    if (typeof detalle === 'string' && detalle.trim()) {
      return detalle.length > 300 ? fallback : detalle;
    }
    if (detalle && typeof detalle === 'object') {
      const primera = Object.values(detalle)[0];
      if (Array.isArray(primera) && primera.length) return String(primera[0]);
      if (typeof primera === 'string' && primera) return primera;
      if (typeof detalle['detail'] === 'string') return detalle['detail'];
    }
    return fallback;
  }
}
