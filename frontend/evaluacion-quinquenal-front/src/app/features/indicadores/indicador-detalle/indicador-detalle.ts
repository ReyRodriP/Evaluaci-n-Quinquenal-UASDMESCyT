import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ToastrService } from 'ngx-toastr';
import { VinculacionService } from '../../../core/services/vinculacion.service';
import { CatalogoService } from '../../../core/services/catalogo.service';
import { EvaluacionService } from '../../../core/services/evaluacion.service';
import { PermisosService } from '../../../core/services/permisos.service';
import { Correspondencia, EstadoCorrespondencia } from '../../../core/models/vinculacion.model';

type NivelDestino = 'dimension' | 'estandar' | 'indicador_marco';
type AccionTransicion = 'rechazar' | 'desconfirmar';

@Component({
  selector: 'app-indicador-detalle',
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './indicador-detalle.html',
  styleUrl: './indicador-detalle.css',
})
export class IndicadorDetalle implements OnInit {
  indicadorId = 0;
  indicador: any = null;
  correspondencias: Correspondencia[] = [];
  cargando = false;
  errorCarga = '';

  mostrandoFormCreacion = false;
  creando = false;
  versiones: any[] = [];
  versionSeleccionada = '';
  nivelDestino: NivelDestino = 'estandar';
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
  comentarioCreacion = '';
  errorCreacion = '';

  formTransicion: { id: number; accion: AccionTransicion; comentario: string } | null = null;
  enTransicionId: number | null = null;
  errorTransicion = '';

  constructor(
    private route: ActivatedRoute,
    private vinculacionService: VinculacionService,
    private catalogoService: CatalogoService,
    private evaluacionService: EvaluacionService,
    private permisos: PermisosService,
    private toast: ToastrService
  ) {}

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    this.indicadorId = id ? +id : 0;
    if (!this.indicadorId) {
      this.errorCarga = 'Identificador de indicador no válido';
      return;
    }
    this.cargarTodo();
  }

  cargarTodo(): void {
    this.cargando = true;
    this.errorCarga = '';
    this.evaluacionService.obtenerIndicador(this.indicadorId).subscribe({
      next: (indicador) => {
        this.indicador = indicador;
        this.cargarContexto();
      },
      error: () => {
        this.errorCarga = 'No se pudo cargar el indicador';
        this.cargando = false;
      },
    });
  }

  cargarContexto(): void {
    this.vinculacionService.contextoIndicador(this.indicadorId).subscribe({
      next: (contexto) => {
        this.correspondencias = contexto.correspondencias ?? [];
        this.cargando = false;
      },
      error: (err) => {
        this.errorCarga = this.mensajeError(err, 'No se pudieron cargar las correspondencias del indicador');
        this.cargando = false;
      },
    });
  }

  get esRolEscritura(): boolean {
    return this.permisos.tieneGrupo('Administrador General') || this.permisos.tieneGrupo('Coordinador Quinquenal');
  }

  get puedeCrear(): boolean {
    return this.permisos.esSuperuser || (this.permisos.tienePermiso('vinculacion.add_correspondencia') && this.esRolEscritura);
  }

  get puedeTransicionar(): boolean {
    return (
      this.permisos.esSuperuser ||
      (this.permisos.tienePermiso('vinculacion.change_correspondencia') && this.esRolEscritura)
    );
  }

  get destinoListo(): boolean {
    if (!this.versionSeleccionada) return false;
    if (this.nivelDestino === 'dimension') return !!this.dimensionSeleccionada;
    if (this.nivelDestino === 'estandar') return !!this.estandarSeleccionado;
    return !!this.indicadorMarcoSeleccionado;
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

  abrirFormCreacion(): void {
    this.mostrandoFormCreacion = true;
    this.errorCreacion = '';
    this.comentarioCreacion = '';
    this.reiniciarSeleccion();
    this.catalogoService.listarVersiones().subscribe({
      next: (versiones) => (this.versiones = versiones),
      error: () => this.toast.error('No se pudieron cargar las versiones del marco'),
    });
  }

  cancelarFormCreacion(): void {
    if (this.creando) return;
    this.mostrandoFormCreacion = false;
    this.errorCreacion = '';
  }

  onVersionChange(): void {
    this.reiniciarCascada();
    if (!this.versionSeleccionada) return;
    this.catalogoService.listarDimensiones(this.versionSeleccionada).subscribe({
      next: (dimensiones) => (this.dimensiones = dimensiones),
      error: () => this.toast.error('No se pudieron cargar las dimensiones del marco'),
    });
  }

  onNivelChange(): void {
    this.reiniciarCascada();
    if (this.nivelDestino === 'dimension' || !this.versionSeleccionada) return;
    this.catalogoService.listarDimensiones(this.versionSeleccionada).subscribe({
      next: (dimensiones) => (this.dimensiones = dimensiones),
      error: () => this.toast.error('No se pudieron cargar las dimensiones del marco'),
    });
  }

  onDimensionChange(): void {
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
      error: () => this.toast.error('No se pudieron cargar los componentes'),
    });
  }

  onComponenteChange(): void {
    this.criteriosMarco = [];
    this.estandares = [];
    this.indicadoresMarco = [];
    this.criterioSeleccionado = '';
    this.estandarSeleccionado = '';
    this.indicadorMarcoSeleccionado = '';
    if (!this.componenteSeleccionado) return;
    this.catalogoService.listarCriterios(+this.componenteSeleccionado).subscribe({
      next: (criterios) => (this.criteriosMarco = criterios),
      error: () => this.toast.error('No se pudieron cargar los criterios del marco'),
    });
  }

  onCriterioChange(): void {
    this.estandares = [];
    this.indicadoresMarco = [];
    this.estandarSeleccionado = '';
    this.indicadorMarcoSeleccionado = '';
    if (!this.criterioSeleccionado) return;
    this.catalogoService.listarEstandares(+this.criterioSeleccionado).subscribe({
      next: (estandares) => (this.estandares = estandares),
      error: () => this.toast.error('No se pudieron cargar los estándares'),
    });
  }

  onEstandarChange(): void {
    this.indicadoresMarco = [];
    this.indicadorMarcoSeleccionado = '';
    if (!this.estandarSeleccionado || this.nivelDestino !== 'indicador_marco') return;
    this.catalogoService.listarIndicadores(+this.estandarSeleccionado).subscribe({
      next: (indicadores) => (this.indicadoresMarco = indicadores),
      error: () => this.toast.error('No se pudieron cargar los indicadores del marco'),
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

  crear(): void {
    if (!this.destinoListo || this.creando) return;
    this.creando = true;
    this.errorCreacion = '';
    const payload: any = {
      version_marco: +this.versionSeleccionada,
      indicador_op: this.indicadorId,
      comentario: this.comentarioCreacion || '',
    };
    if (this.nivelDestino === 'dimension') payload.dimension = +this.dimensionSeleccionada;
    if (this.nivelDestino === 'estandar') payload.estandar = +this.estandarSeleccionado;
    if (this.nivelDestino === 'indicador_marco') payload.indicador_marco = +this.indicadorMarcoSeleccionado;

    this.vinculacionService.crearCorrespondencia(payload).subscribe({
      next: () => {
        this.toast.success('Propuesta de correspondencia creada');
        this.creando = false;
        this.mostrandoFormCreacion = false;
        this.cargarContexto();
      },
      error: (err) => {
        this.errorCreacion = this.mensajeError(err, 'No se pudo crear la propuesta de correspondencia');
        this.creando = false;
      },
    });
  }

  iniciarTransicion(corr: Correspondencia, accion: AccionTransicion): void {
    this.errorTransicion = '';
    this.formTransicion = { id: corr.id, accion, comentario: '' };
  }

  cancelarTransicion(): void {
    if (this.enTransicionId != null) return;
    this.formTransicion = null;
    this.errorTransicion = '';
  }

  confirmar(corr: Correspondencia): void {
    if (this.enTransicionId != null) return;
    this.enTransicionId = corr.id;
    this.errorTransicion = '';
    this.vinculacionService.confirmarCorrespondencia(corr.id).subscribe({
      next: () => {
        this.toast.success('Correspondencia confirmada');
        this.enTransicionId = null;
        this.cargarContexto();
      },
      error: (err) => {
        this.errorTransicion = this.mensajeError(err, 'No se pudo confirmar la correspondencia');
        this.enTransicionId = null;
      },
    });
  }

  ejecutarTransicion(): void {
    if (!this.formTransicion || this.enTransicionId != null) return;
    const comentario = this.formTransicion.comentario.trim();
    if (!comentario) {
      this.errorTransicion = 'El comentario es obligatorio para esta operación';
      return;
    }
    const { id, accion } = this.formTransicion;
    this.enTransicionId = id;
    this.errorTransicion = '';
    const peticion =
      accion === 'rechazar'
        ? this.vinculacionService.rechazarCorrespondencia(id, comentario)
        : this.vinculacionService.desconfirmarCorrespondencia(id, comentario);
    peticion.subscribe({
      next: () => {
        this.toast.success(accion === 'rechazar' ? 'Correspondencia rechazada' : 'Correspondencia devuelta a propuesta');
        this.enTransicionId = null;
        this.formTransicion = null;
        this.cargarContexto();
      },
      error: (err) => {
        this.errorTransicion = this.mensajeError(err, 'No se pudo completar la operación');
        this.enTransicionId = null;
      },
    });
  }

  private reiniciarSeleccion(): void {
    this.versionSeleccionada = '';
    this.nivelDestino = 'estandar';
    this.reiniciarCascada();
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
