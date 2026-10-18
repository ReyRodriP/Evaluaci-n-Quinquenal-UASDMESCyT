import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { Observable, catchError, forkJoin, of } from 'rxjs';
import { switchMap } from 'rxjs/operators';
import { Pagination } from '../../shared/components/CRUD/pagination/pagination';
import { EvaluacionService } from '../../core/services/evaluacion.service';
import { EvidenciasService } from '../../core/services/evidencias.service';
import { VinculacionService } from '../../core/services/vinculacion.service';

export const MAX_PAGINAS_LISTADO = 20;
export const MAX_PAGINAS_CORRESPONDENCIAS = 10;

export type ClaveRevision =
  | 'sin_evidencia'
  | 'cancelada'
  | 'en_revision'
  | 'observada'
  | 'aprobada'
  | 'rechazada'
  | 'sin_enviar'
  | 'completada';

export type EstadoCorrespondenciaFila = 'confirmada' | 'pendiente' | 'sin' | 'desconocida';

export interface FilaSeguimiento {
  asignacionId: number;
  periodoNombre: string;
  unidadId: number | string;
  unidadNombre: string;
  indicadorId: number | string;
  indicadorNombre: string;
  criterioNombre: string;
  estado: string;
  estadoDisplay: string;
  evidenciaId: number | null;
  claveRevision: ClaveRevision;
  estadoRevision: string;
  correspondenciaEstado: EstadoCorrespondenciaFila;
}

export interface Metricas {
  total: number;
  conEvidencia: number;
  sinEvidencia: number;
  pendientesRevision: number;
  observadas: number;
  conConfirmada: number | null;
  sinConfirmada: number | null;
}

export interface OpcionFiltro {
  valor: string;
  etiqueta: string;
}

interface EnvolturaPaginada<T> {
  count: number;
  next: string | null;
  results: T[];
}

export interface ResultadoPaginas<T> {
  items: T[];
  total: number;
  truncado: boolean;
}

interface ResultadoCorrespondencias {
  confirmadas: ResultadoPaginas<any>;
  propuestas: ResultadoPaginas<any>;
}

const ETIQUETAS_REVISION: Record<ClaveRevision, string> = {
  sin_evidencia: 'Sin evidencia',
  cancelada: 'Evidencia cancelada',
  en_revision: 'Pendiente de revisión',
  observada: 'Observada',
  aprobada: 'Aprobada internamente',
  rechazada: 'Rechazada',
  sin_enviar: 'Sin enviar a revisión',
  completada: 'Completada',
};

const ETIQUETAS_CORRESPONDENCIA: Record<EstadoCorrespondenciaFila, string> = {
  confirmada: 'Confirmada',
  pendiente: 'Pendiente de validación',
  sin: 'Sin correspondencia confirmada',
  desconocida: 'No disponible',
};

@Component({
  selector: 'app-seguimiento',
  imports: [CommonModule, FormsModule, Pagination, RouterLink],
  templateUrl: './seguimiento.html',
  styleUrl: './seguimiento.css',
})
export class Seguimiento implements OnInit {
  periodos: any[] = [];
  periodoActivo: any = null;
  periodoSeleccionadoId = '';

  cargando = false;
  errorPeriodos = false;
  errorCarga = '';
  errorCorrespondencias = false;
  reintentandoCorrespondencias = false;
  avisosTruncado: string[] = [];
  avisoCorrespondenciaTruncada = false;

  filas: FilaSeguimiento[] = [];
  filasFiltradas: FilaSeguimiento[] = [];
  filasPaginadas: FilaSeguimiento[] = [];

  filtros = { unidad: '', estado: '', revision: '', correspondencia: '' };
  opcionesUnidades: OpcionFiltro[] = [];
  opcionesEstados: OpcionFiltro[] = [];
  opcionesRevision: OpcionFiltro[] = [];
  opcionesCorrespondencia: OpcionFiltro[] = [
    { valor: 'confirmada', etiqueta: 'Confirmada' },
    { valor: 'pendiente', etiqueta: 'Pendiente de validación' },
    { valor: 'sin', etiqueta: 'Sin correspondencia confirmada' },
  ];

  metricas: Metricas = {
    total: 0,
    conEvidencia: 0,
    sinEvidencia: 0,
    pendientesRevision: 0,
    observadas: 0,
    conConfirmada: null,
    sinConfirmada: null,
  };

  currentPage = 1;
  pageSize = 10;

  private asignacionesCargadas: any[] = [];
  private evidenciasCargadas: any[] = [];
  private indicadoresCargados: any[] = [];
  private confirmados = new Set<number>();
  private pendientes = new Set<number>();

  constructor(
    private evaluacionService: EvaluacionService,
    private evidenciasService: EvidenciasService,
    private vinculacionService: VinculacionService,
    private route: ActivatedRoute,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.cargarPeriodos();
  }

  get correspondenciasDisponibles(): boolean {
    return !this.errorCorrespondencias;
  }

  cargarPeriodos(): void {
    this.errorPeriodos = false;
    forkJoin({
      periodos: this.evaluacionService.listarPeriodos(),
      activo: this.evaluacionService.periodoActivo().pipe(catchError(() => of(null))),
    }).subscribe({
      next: ({ periodos, activo }) => {
        this.periodos = Array.isArray(periodos) ? periodos : [];
        this.periodoActivo = activo;
        const periodoUrl = this.route.snapshot.queryParamMap.get('periodo');
        const solicitado = this.periodos.find((item: any) => String(item.id) === periodoUrl);
        const seleccionSolicitadaValida = Boolean(periodoUrl) && (solicitado || !this.periodos.length);
        this.periodoSeleccionadoId = String(seleccionSolicitadaValida ? periodoUrl : activo?.id ?? '');
        if (activo && !this.periodos.some((item: any) => Number(item.id) === Number(activo.id))) {
          this.periodos = [...this.periodos, activo];
        }
        if (this.periodoSeleccionadoId !== periodoUrl) this.actualizarPeriodoUrl();
        this.cargarDatos();
      },
      error: () => {
        this.errorPeriodos = true;
      },
    });
  }

  onPeriodoChange(periodoId: string): void {
    this.periodoSeleccionadoId = periodoId;
    this.actualizarPeriodoUrl();
    this.cargarDatos();
  }

  reintentar(): void {
    if (this.errorPeriodos) {
      this.cargarPeriodos();
      return;
    }
    this.cargarDatos();
  }

  cargarDatos(): void {
    if (!this.periodoSeleccionadoId) {
      this.limpiarTodo();
      return;
    }
    this.cargando = true;
    this.errorCarga = '';
    this.avisosTruncado = [];
    forkJoin({
      asignaciones: this.obtenerPaginas(
        (page) => this.evaluacionService.listarAsignacionesPagina(this.periodoSeleccionadoId, page),
        MAX_PAGINAS_LISTADO
      ),
      evidencias: this.obtenerPaginas(
        (page) => this.evidenciasService.listarEvidenciasPagina(this.periodoSeleccionadoId, page),
        MAX_PAGINAS_LISTADO
      ),
      indicadores: this.obtenerPaginas(
        (page) => this.evaluacionService.listarIndicadoresPagina(page),
        MAX_PAGINAS_LISTADO
      ),
      correspondencias: this.cargarCorrespondencias(),
    }).subscribe({
      next: ({ asignaciones, evidencias, indicadores, correspondencias }) => {
        this.asignacionesCargadas = asignaciones.items;
        this.evidenciasCargadas = evidencias.items;
        this.indicadoresCargados = indicadores.items;
        if (asignaciones.truncado) {
          this.avisosTruncado.push(
            `Asignaciones: se obtuvieron ${asignaciones.items.length} de ${asignaciones.total}; las métricas reflejan solo esas filas.`
          );
        }
        if (evidencias.truncado) {
          this.avisosTruncado.push(
            `Evidencias: se obtuvieron ${evidencias.items.length} de ${evidencias.total}; algunas asignaciones pueden mostrarse sin evidencia.`
          );
        }
        if (indicadores.truncado) {
          this.avisosTruncado.push(
            `Indicadores: se obtuvieron ${indicadores.items.length} de ${indicadores.total}; el criterio operativo puede faltar en algunas filas.`
          );
        }
        this.aplicarCorrespondencias(correspondencias);
        this.construirFilas();
        this.aplicarFiltros();
        this.cargando = false;
      },
      error: (err) => {
        console.error('Error cargando el seguimiento', err);
        this.errorCarga = 'No se pudo cargar la información del seguimiento.';
        this.cargando = false;
      },
    });
  }

  reintentarCorrespondencias(): void {
    this.reintentandoCorrespondencias = true;
    this.cargarCorrespondencias().subscribe((resultado) => {
      this.aplicarCorrespondencias(resultado);
      this.construirFilas();
      this.aplicarFiltros();
      this.reintentandoCorrespondencias = false;
    });
  }

  cambiarFiltro(campo: 'unidad' | 'estado' | 'revision' | 'correspondencia', valor: string): void {
    this.filtros[campo] = valor;
    this.aplicarFiltros();
  }

  limpiarFiltros(): void {
    this.filtros = { unidad: '', estado: '', revision: '', correspondencia: '' };
    this.aplicarFiltros();
  }

  onPageChange(page: number): void {
    this.currentPage = page;
    this.actualizarPagina();
  }

  onPageSizeChange(size: number): void {
    this.pageSize = size;
    this.currentPage = 1;
    this.actualizarPagina();
  }

  obtenerPaginas<T>(
    pagina$: (page: number) => Observable<EnvolturaPaginada<T>>,
    maxPaginas: number,
    page = 1,
    acumulado: T[] = []
  ): Observable<ResultadoPaginas<T>> {
    return pagina$(page).pipe(
      switchMap((envoltura) => {
        const resultados = Array.isArray(envoltura?.results) ? envoltura.results : [];
        const total =
          typeof envoltura?.count === 'number' ? envoltura.count : acumulado.length + resultados.length;
        const cupo = Math.max(0, total - acumulado.length);
        const items = [...acumulado, ...resultados.slice(0, cupo)];
        const haySiguiente = Boolean(envoltura?.next);
        const completo = !haySiguiente || resultados.length === 0 || items.length >= total;
        if (completo || page >= maxPaginas) {
          return of({ items, total, truncado: total > items.length });
        }
        return this.obtenerPaginas(pagina$, maxPaginas, page + 1, items);
      })
    );
  }

  aplicarFiltros(): void {
    this.filasFiltradas = this.filas.filter(
      (fila) =>
        (!this.filtros.unidad || String(fila.unidadId) === this.filtros.unidad) &&
        (!this.filtros.estado || fila.estado === this.filtros.estado) &&
        (!this.filtros.revision || fila.claveRevision === this.filtros.revision) &&
        (!this.filtros.correspondencia || fila.correspondenciaEstado === this.filtros.correspondencia)
    );
    this.currentPage = 1;
    this.calcularMetricas();
    this.actualizarPagina();
  }

  private actualizarPagina(): void {
    const start = (this.currentPage - 1) * this.pageSize;
    this.filasPaginadas = this.filasFiltradas.slice(start, start + this.pageSize);
  }

  private calcularMetricas(): void {
    const filas = this.filasFiltradas;
    const total = filas.length;
    const conEvidencia = filas.filter((fila) => fila.evidenciaId != null).length;
    const pendientesRevision = filas.filter((fila) => fila.claveRevision === 'en_revision').length;
    const observadas = filas.filter((fila) => fila.claveRevision === 'observada').length;
    if (!this.correspondenciasDisponibles) {
      this.metricas = {
        total,
        conEvidencia,
        sinEvidencia: total - conEvidencia,
        pendientesRevision,
        observadas,
        conConfirmada: null,
        sinConfirmada: null,
      };
      return;
    }
    const conConfirmada = filas.filter((fila) => fila.correspondenciaEstado === 'confirmada').length;
    this.metricas = {
      total,
      conEvidencia,
      sinEvidencia: total - conEvidencia,
      pendientesRevision,
      observadas,
      conConfirmada,
      sinConfirmada: total - conConfirmada,
    };
  }

  private cargarCorrespondencias(): Observable<ResultadoCorrespondencias | null> {
    return forkJoin({
      confirmadas: this.obtenerPaginas(
        (page) => this.vinculacionService.listarCorrespondencias({ estado: 'confirmada', page }),
        MAX_PAGINAS_CORRESPONDENCIAS
      ),
      propuestas: this.obtenerPaginas(
        (page) => this.vinculacionService.listarCorrespondencias({ estado: 'propuesta', page }),
        MAX_PAGINAS_CORRESPONDENCIAS
      ),
    }).pipe(catchError(() => of(null)));
  }

  private aplicarCorrespondencias(resultado: ResultadoCorrespondencias | null): void {
    if (!resultado) {
      this.errorCorrespondencias = true;
      this.avisoCorrespondenciaTruncada = false;
      this.filtros.correspondencia = '';
      this.confirmados = new Set<number>();
      this.pendientes = new Set<number>();
      return;
    }
    this.errorCorrespondencias = false;
    this.avisoCorrespondenciaTruncada = resultado.confirmadas.truncado || resultado.propuestas.truncado;
    const idsConfirmados = resultado.confirmadas.items
      .map((item: any) => item.indicador_op)
      .filter((id: any) => typeof id === 'number');
    const idsPropuestos = resultado.propuestas.items
      .map((item: any) => item.indicador_op)
      .filter((id: any) => typeof id === 'number');
    this.confirmados = new Set<number>(idsConfirmados);
    this.pendientes = new Set<number>(idsPropuestos.filter((id: number) => !this.confirmados.has(id)));
  }

  private construirFilas(): void {
    const evPorAsignacion = new Map<number, any>();
    for (const evidencia of this.evidenciasCargadas) {
      const asignacionId =
        typeof evidencia.asignacion === 'number' ? evidencia.asignacion : evidencia.asignacion?.id;
      if (asignacionId != null) evPorAsignacion.set(asignacionId, evidencia);
    }
    const criterioPorIndicador = new Map<number, string>();
    for (const indicador of this.indicadoresCargados) {
      criterioPorIndicador.set(indicador.id, indicador.criterio_nombre || '');
    }

    this.filas = this.asignacionesCargadas.map((asignacion: any) => {
      const evidencia = evPorAsignacion.get(asignacion.id) ?? null;
      const claveRevision = this.claveDeRevision(evidencia, asignacion.estado);
      const indicadorId = asignacion.indicador;
      let correspondenciaEstado: EstadoCorrespondenciaFila = 'desconocida';
      if (this.correspondenciasDisponibles) {
        if (this.confirmados.has(indicadorId)) correspondenciaEstado = 'confirmada';
        else if (this.pendientes.has(indicadorId)) correspondenciaEstado = 'pendiente';
        else correspondenciaEstado = 'sin';
      }
      return {
        asignacionId: asignacion.id,
        periodoNombre: asignacion.periodo_nombre || '',
        unidadId: asignacion.unidad_responsable,
        unidadNombre: asignacion.unidad_responsable_nombre || '',
        indicadorId,
        indicadorNombre: asignacion.indicador_nombre || '',
        criterioNombre: criterioPorIndicador.get(indicadorId) || '—',
        estado: asignacion.estado || '',
        estadoDisplay: asignacion.estado_display || asignacion.estado || '',
        evidenciaId: evidencia?.id_evidencia ?? null,
        claveRevision,
        estadoRevision: ETIQUETAS_REVISION[claveRevision],
        correspondenciaEstado,
      } as FilaSeguimiento;
    });

    const unidades = new Map<string, string>();
    const estados = new Map<string, string>();
    const revisiones = new Map<string, string>();
    for (const fila of this.filas) {
      unidades.set(String(fila.unidadId), fila.unidadNombre);
      if (!estados.has(fila.estado)) estados.set(fila.estado, fila.estadoDisplay);
      if (!revisiones.has(fila.claveRevision)) revisiones.set(fila.claveRevision, fila.estadoRevision);
    }
    this.opcionesUnidades = this.aOpcionesOrdenadas(unidades);
    this.opcionesEstados = this.aOpcionesOrdenadas(estados);
    this.opcionesRevision = this.aOpcionesOrdenadas(revisiones);
  }

  private aOpcionesOrdenadas(mapa: Map<string, string>): OpcionFiltro[] {
    return [...mapa.entries()]
      .map(([valor, etiqueta]) => ({ valor, etiqueta }))
      .sort((a, b) => a.etiqueta.localeCompare(b.etiqueta));
  }

  private claveDeRevision(evidencia: any, estadoAsignacion: string): ClaveRevision {
    if (!evidencia) return 'sin_evidencia';
    if (evidencia.estado === 'cancelada') return 'cancelada';
    switch (estadoAsignacion) {
      case 'en_progreso':
        return 'en_revision';
      case 'observada':
        return 'observada';
      case 'aprobado':
        return 'aprobada';
      case 'rechazado':
        return 'rechazada';
      case 'completado':
        return 'completada';
      default:
        return 'sin_enviar';
    }
  }

  etiquetaCorrespondencia(estado: EstadoCorrespondenciaFila): string {
    return ETIQUETAS_CORRESPONDENCIA[estado];
  }

  valorPeriodo(periodo: any): string {
    return String(periodo?.id ?? '');
  }

  private limpiarTodo(): void {
    this.asignacionesCargadas = [];
    this.evidenciasCargadas = [];
    this.indicadoresCargados = [];
    this.filas = [];
    this.avisosTruncado = [];
    this.avisoCorrespondenciaTruncada = false;
    this.errorCorrespondencias = false;
    this.errorCarga = '';
    this.aplicarFiltros();
  }

  private actualizarPeriodoUrl(): void {
    void this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { periodo: this.periodoSeleccionadoId || null },
      queryParamsHandling: 'merge',
      replaceUrl: true,
    });
  }
}
