import { Component, EventEmitter, Input, OnDestroy, OnInit, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subject } from 'rxjs';
import { debounceTime, takeUntil } from 'rxjs/operators';
import { Correspondencia, CorrespondenciaCreacion } from '../../../core/models/vinculacion.model';
import { VinculacionService } from '../../../core/services/vinculacion.service';
import { CatalogoService } from '../../../core/services/catalogo.service';
import { EvaluacionService } from '../../../core/services/evaluacion.service';
import { PermisosService } from '../../../core/services/permisos.service';

export type NivelDestinoForm = 'dimension' | 'estandar' | 'indicador_marco';
export type NivelOrigenForm = 'criterio' | 'indicador';

export interface DestinoFijo {
  nivel: NivelDestinoForm;
  id: number;
  version: number;
  codigo?: string;
  texto: string;
  /** Ruta jerárquica (incluye el propio nodo) armada por el explorador. */
  ruta?: string[];
}

export interface OrigenFijo {
  nivel: NivelOrigenForm;
  id: number;
  texto: string;
}

/**
 * @brief Formulario compartido de propuestas de correspondencia.
 * @details Soporta dos modos: destino fijo (nodo del marco elegido en el
 * explorador EQ-SIDACES + selector de origen operativo, con el destino
 * editable mediante la cascada jerárquica) y origen fijo (elemento
 * operativo + cascada de destino en el marco). No usa permisos de
 * escritura del backend por sí mismo: la creación la ejecuta la API y
 * cualquier error (incluido 403) se muestra inline.
 *
 * Destino admitido por el backend: exactamente uno de dimension,
 * estandar o indicador_marco (nunca componente ni criterio del marco).
 * Origen admitido: exactamente uno de criterio_op o indicador_op.
 */
@Component({
  selector: 'app-correspondencia-form',
  imports: [CommonModule, FormsModule],
  templateUrl: './correspondencia-form.html',
  styleUrl: './correspondencia-form.css',
})
export class CorrespondenciaForm implements OnInit, OnDestroy {
  @Input() destinoFijo: DestinoFijo | null = null;
  @Input() origenFijo: OrigenFijo | null = null;
  @Output() creada = new EventEmitter<Correspondencia>();
  @Output() cancelada = new EventEmitter<void>();

  tipoOrigen: NivelOrigenForm = 'indicador';
  origenes: any[] = [];
  origenesCargando = false;
  origenesTruncado = false;
  origenTotal = 0;
  filtroOrigen = '';
  origenSeleccionado = '';
  errorOrigen = '';

  editandoDestino = false;

  versiones: any[] = [];
  versionSeleccionada = '';
  nivelDestino: NivelDestinoForm = 'estandar';
  dimensiones: any[] = [];
  componentes: any[] = [];
  criteriosMarco: any[] = [];
  estandares: any[] = [];
  indicadoresMarco: any[] = [];
  dimensionSeleccionada = '';
  componenteSeleccionado = '';
  criterioSeleccionado = '';
  estandarSeleccionado = '';
  indicadorMarcoSeleccionado = '';

  comentario = '';
  creando = false;
  exito = false;
  errorCreacion = '';
  errorCarga = '';

  private busqueda$ = new Subject<string>();
  private destroy$ = new Subject<void>();

  constructor(
    private vinculacionService: VinculacionService,
    private catalogoService: CatalogoService,
    private evaluacionService: EvaluacionService,
    private permisos: PermisosService
  ) {}

  ngOnInit(): void {
    this.busqueda$
      .pipe(debounceTime(300), takeUntil(this.destroy$))
      .subscribe((termino) => {
        if (termino !== this.filtroOrigen.trim()) return;
        this.recargarOrigenes(termino);
      });
    if (!this.puedeCrear) return;
    if (this.modo === 'destino') this.cargarOrigenes();
    if (this.modo === 'origen') this.cargarVersiones();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  get modo(): 'destino' | 'origen' | null {
    if (this.destinoFijo && !this.origenFijo) return 'destino';
    if (this.origenFijo && !this.destinoFijo) return 'origen';
    return null;
  }

  get puedeCrear(): boolean {
    const rolEscritura =
      this.permisos.tieneGrupo('Administrador General') || this.permisos.tieneGrupo('Coordinador Quinquenal');
    return this.permisos.esSuperuser || (this.permisos.tienePermiso('vinculacion.add_correspondencia') && rolEscritura);
  }

  get mostrarCascada(): boolean {
    return this.modo === 'origen' || (this.modo === 'destino' && this.editandoDestino);
  }

  get listo(): boolean {
    if (this.modo === 'destino') {
      return !!this.origenSeleccionado && (!this.editandoDestino || this.destinoListo);
    }
    return this.destinoListo;
  }

  get destinoListo(): boolean {
    if (!this.versionSeleccionada) return false;
    if (this.nivelDestino === 'dimension') return !!this.dimensionSeleccionada;
    if (this.nivelDestino === 'estandar') return !!this.estandarSeleccionado;
    return !!this.indicadorMarcoSeleccionado;
  }

  get origenesVisibles(): any[] {
    const termino = this.filtroOrigen.toLowerCase().trim();
    if (!termino) return this.origenes;
    return this.origenes.filter((origen) =>
      `${origen?.nombre ?? ''} ${origen?.codigo ?? ''}`.toLowerCase().includes(termino)
    );
  }

  get mostrarFiltroOrigen(): boolean {
    return this.origenTotal > 12;
  }

  /** Ruta jerárquica del destino (fijo o en edición) para mostrar antes de enviar. */
  get rutaDestino(): string[] {
    if (this.modo === 'destino' && !this.editandoDestino) return this.destinoFijo?.ruta ?? [];
    if (!this.mostrarCascada) return [];
    const porId = (lista: any[], valor: string) => lista.find((x) => String(x.id) === valor);
    const partes: string[] = [];
    const dim = porId(this.dimensiones, this.dimensionSeleccionada);
    if (dim) partes.push(this.etiquetaDimension(dim));
    const comp = porId(this.componentes, this.componenteSeleccionado);
    if (comp) partes.push(this.etiquetaRama(comp));
    const crit = porId(this.criteriosMarco, this.criterioSeleccionado);
    if (crit) partes.push(this.etiquetaRama(crit));
    if (this.nivelDestino === 'estandar') {
      const est = porId(this.estandares, this.estandarSeleccionado);
      if (est) partes.push(this.etiquetaEstandar(est));
    }
    if (this.nivelDestino === 'indicador_marco') {
      const ind = porId(this.indicadoresMarco, this.indicadorMarcoSeleccionado);
      if (ind) partes.push(this.etiquetaIndicadorMarco(ind));
    }
    return partes;
  }

  cargarOrigenes(): void {
    this.filtroOrigen = '';
    this.origenSeleccionado = '';
    this.recargarOrigenes('');
  }

  onFiltroOrigenChange(): void {
    this.busqueda$.next(this.filtroOrigen.trim());
  }

  private recargarOrigenes(termino: string): void {
    this.origenesCargando = true;
    this.origenesTruncado = false;
    this.errorOrigen = '';
    const pagina$ =
      this.tipoOrigen === 'criterio'
        ? (page: number) => this.evaluacionService.listarCriteriosPagina(page, termino || undefined)
        : (page: number) => this.evaluacionService.listarIndicadoresPagina(page, termino || undefined);
    pagina$(1).subscribe({
      next: (resultado) => {
        this.origenes = resultado.results ?? [];
        this.origenTotal = resultado.count ?? this.origenes.length;
        this.origenesTruncado = this.origenTotal > this.origenes.length;
        this.origenesCargando = false;
        if (this.origenSeleccionado && !this.origenes.some((o) => String(o.id) === this.origenSeleccionado)) {
          this.origenSeleccionado = '';
        }
      },
      error: () => {
        this.origenes = [];
        this.origenTotal = 0;
        this.origenesCargando = false;
        this.errorOrigen =
          this.tipoOrigen === 'criterio'
            ? 'No se pudieron cargar los criterios operativos'
            : 'No se pudieron cargar los indicadores operativos';
      },
    });
  }

  etiquetaOrigen(item: any): string {
    const codigo = item?.codigo ?? '';
    const nombre = item?.nombre ?? '';
    return codigo ? `${codigo} — ${nombre}` : nombre;
  }

  cargarVersiones(): void {
    this.catalogoService.listarVersiones().subscribe({
      next: (versiones) => (this.versiones = versiones),
      error: () => (this.errorCarga = 'No se pudieron cargar las versiones del marco'),
    });
  }

  iniciarCambioDestino(): void {
    if (!this.destinoFijo || this.modo !== 'destino') return;
    this.editandoDestino = true;
    this.errorCarga = '';
    this.versionSeleccionada = String(this.destinoFijo.version);
    this.nivelDestino = this.destinoFijo.nivel;
    this.reiniciarCascada();
    if (this.nivelDestino === 'dimension') this.dimensionSeleccionada = String(this.destinoFijo!.id);
    this.cargarDimensiones();
  }

  restaurarDestino(): void {
    this.editandoDestino = false;
    this.errorCarga = '';
    this.reiniciarCascada();
    this.versionSeleccionada = '';
  }

  onVersionChange(): void {
    this.errorCarga = '';
    this.reiniciarCascada();
    if (!this.versionSeleccionada) return;
    this.cargarDimensiones();
  }

  onNivelChange(): void {
    this.errorCarga = '';
    this.reiniciarCascada();
    if (this.nivelDestino === 'dimension' || !this.versionSeleccionada) return;
    this.cargarDimensiones();
  }

  onDimensionChange(): void {
    this.errorCarga = '';
    this.componentes = [];
    this.criteriosMarco = [];
    this.estandares = [];
    this.indicadoresMarco = [];
    this.componenteSeleccionado = '';
    this.criterioSeleccionado = '';
    this.estandarSeleccionado = '';
    this.indicadorMarcoSeleccionado = '';
    if (!this.dimensionSeleccionada || this.nivelDestino === 'dimension') return;
    this.catalogoService.listarComponentes(+this.dimensionSeleccionada).subscribe({
      next: (componentes) => (this.componentes = componentes),
      error: () => (this.errorCarga = 'No se pudieron cargar los componentes'),
    });
  }

  onComponenteChange(): void {
    this.errorCarga = '';
    this.criteriosMarco = [];
    this.estandares = [];
    this.indicadoresMarco = [];
    this.criterioSeleccionado = '';
    this.estandarSeleccionado = '';
    this.indicadorMarcoSeleccionado = '';
    if (!this.componenteSeleccionado) return;
    this.catalogoService.listarCriterios(+this.componenteSeleccionado).subscribe({
      next: (criterios) => (this.criteriosMarco = criterios),
      error: () => (this.errorCarga = 'No se pudieron cargar los criterios del marco'),
    });
  }

  onCriterioChange(): void {
    this.errorCarga = '';
    this.estandares = [];
    this.indicadoresMarco = [];
    this.estandarSeleccionado = '';
    this.indicadorMarcoSeleccionado = '';
    if (!this.criterioSeleccionado) return;
    this.catalogoService.listarEstandares(+this.criterioSeleccionado).subscribe({
      next: (estandares) => (this.estandares = estandares),
      error: () => (this.errorCarga = 'No se pudieron cargar los estándares'),
    });
  }

  onEstandarChange(): void {
    this.errorCarga = '';
    this.indicadoresMarco = [];
    this.indicadorMarcoSeleccionado = '';
    if (!this.estandarSeleccionado || this.nivelDestino !== 'indicador_marco') return;
    this.catalogoService.listarIndicadores(+this.estandarSeleccionado).subscribe({
      next: (indicadores) => (this.indicadoresMarco = indicadores),
      error: () => (this.errorCarga = 'No se pudieron cargar los indicadores del marco'),
    });
  }

  private cargarDimensiones(): void {
    if (!this.versionSeleccionada) return;
    this.catalogoService.listarDimensiones(this.versionSeleccionada).subscribe({
      next: (dimensiones) => (this.dimensiones = dimensiones),
      error: () => (this.errorCarga = 'No se pudieron cargar las dimensiones del marco'),
    });
  }

  etiquetaDimension(item: any): string {
    return `${item.codigo} — ${item.nombre}`;
  }

  etiquetaRama(item: any): string {
    return `${item.codigo_completo} — ${item.nombre ?? ''}`.replace(/ — $/, '');
  }

  etiquetaEstandar(item: any): string {
    return item.codigo_completo ?? String(item.id);
  }

  etiquetaIndicadorMarco(item: any): string {
    return item.codigo_completo ?? String(item.id);
  }

  etiquetaNivelDestino(nivel: string): string {
    const etiquetas: Record<string, string> = {
      dimension: 'Dimensión del marco',
      estandar: 'Estándar del marco',
      indicador_marco: 'Indicador del marco',
    };
    return etiquetas[nivel] ?? nivel;
  }

  etiquetaNivelOrigen(nivel: string): string {
    const etiquetas: Record<string, string> = {
      criterio: 'Criterio operativo',
      indicador: 'Indicador operativo',
    };
    return etiquetas[nivel] ?? nivel;
  }

  crear(): void {
    if (this.creando || !this.listo || !this.puedeCrear) return;
    this.creando = true;
    this.errorCreacion = '';
    const payload: CorrespondenciaCreacion = {
      version_marco: 0,
      comentario: this.comentario.trim(),
    };
    if (this.modo === 'destino') {
      if (this.tipoOrigen === 'criterio') payload.criterio_op = +this.origenSeleccionado;
      else payload.indicador_op = +this.origenSeleccionado;
      if (this.editandoDestino) {
        this.aplicarDestinoEnEdicion(payload);
      } else {
        payload.version_marco = this.destinoFijo!.version;
        payload[this.destinoFijo!.nivel] = this.destinoFijo!.id;
      }
    } else {
      if (this.origenFijo!.nivel === 'criterio') payload.criterio_op = this.origenFijo!.id;
      else payload.indicador_op = this.origenFijo!.id;
      this.aplicarDestinoEnEdicion(payload);
    }
    this.vinculacionService.crearCorrespondencia(payload).subscribe({
      next: (correspondencia) => {
        this.creando = false;
        this.exito = true;
        this.creada.emit(correspondencia);
      },
      error: (err) => {
        this.errorCreacion = this.mensajeError(err, 'No se pudo crear la propuesta de correspondencia');
        this.creando = false;
      },
    });
  }

  cerrar(): void {
    if (this.creando) return;
    this.cancelada.emit();
  }

  private aplicarDestinoEnEdicion(payload: CorrespondenciaCreacion): void {
    payload.version_marco = +this.versionSeleccionada;
    if (this.nivelDestino === 'dimension') payload.dimension = +this.dimensionSeleccionada;
    if (this.nivelDestino === 'estandar') payload.estandar = +this.estandarSeleccionado;
    if (this.nivelDestino === 'indicador_marco') payload.indicador_marco = +this.indicadorMarcoSeleccionado;
  }

  private reiniciarCascada(): void {
    this.dimensiones = [];
    this.componentes = [];
    this.criteriosMarco = [];
    this.estandares = [];
    this.indicadoresMarco = [];
    this.dimensionSeleccionada = '';
    this.componenteSeleccionado = '';
    this.criterioSeleccionado = '';
    this.estandarSeleccionado = '';
    this.indicadorMarcoSeleccionado = '';
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
