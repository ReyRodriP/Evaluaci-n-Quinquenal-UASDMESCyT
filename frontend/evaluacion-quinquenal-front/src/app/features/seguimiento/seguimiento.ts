import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { Observable, catchError, forkJoin, of, switchMap } from 'rxjs';
import { Pagination } from '../../shared/components/CRUD/pagination/pagination';
import { EvaluacionService } from '../../core/services/evaluacion.service';
import { SeguimientoResumenService } from '../../core/services/seguimiento-resumen.service';
import { VinculacionService } from '../../core/services/vinculacion.service';
import { CatalogoService } from '../../core/services/catalogo.service';
import { rutaCoincideConMarco } from '../../core/models/asignacion-marco.model';
import { RespuestaPaginada } from '../../core/models/vinculacion.model';
import {
  ETIQUETAS_CORRESPONDENCIA,
  ETIQUETAS_REVISION,
  MAX_PAGINAS_CORRESPONDENCIAS,
  ClaveRevision,
  EstadoCorrespondenciaFila,
  FilaSeguimiento,
  Metricas,
  ResultadoPaginas,
  ResultadoSeguimiento,
  calcularMetricas,
  tieneEvidencia,
} from '../../core/models/seguimiento.model';

export const COLUMNAS_EXPORTACION = [
  'Período',
  'Unidad responsable',
  'Criterio',
  'Indicador',
  'Estado de asignación',
  'Existencia de evidencia',
  'Estado de revisión',
  'Estado de correspondencia',
  'Código del destino del marco',
  'Versión del marco',
];

export interface OpcionFiltro {
  valor: string;
  etiqueta: string;
}

@Component({
  selector: 'app-seguimiento',
  imports: [CommonModule, FormsModule, Pagination, RouterLink],
  templateUrl: './seguimiento.html',
  styleUrl: './seguimiento.css',
})
export class Seguimiento implements OnInit {
  tieneEvidencia = tieneEvidencia;

  get tieneDocumentos(): boolean { return this.filasFiltradas.some(fila => fila.documentosResumen); }
  periodos: any[] = [];
  periodoActivo: any = null;
  periodoSeleccionadoId = '';

  cargando = false;
  exportando = false;
  errorPeriodos = false;
  errorCarga = '';
  errorCorrespondencias = false;
  reintentandoCorrespondencias = false;
  avisosTruncado: string[] = [];
  avisoCorrespondenciaTruncada = false;

  dimensionesMarco: any[] = [];
  marcoCargando = false;
  marcoError = false;
  cargandoOrigenesMarco = false;
  marcoListo = false;
  marcoFiltroError = false;
  avisoMarcoTruncado = false;
  private marcoOrigenesIndicador = new Set<number>();
  private marcoOrigenesCriterio = new Set<number>();

  filas: FilaSeguimiento[] = [];
  filasFiltradas: FilaSeguimiento[] = [];
  filasPaginadas: FilaSeguimiento[] = [];

  filtros = { unidad: '', estado: '', revision: '', correspondencia: '', dimension: '', componente: '' };
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

  constructor(
    private evaluacionService: EvaluacionService,
    private resumenService: SeguimientoResumenService,
    private vinculacionService: VinculacionService,
    private catalogoService: CatalogoService,
    private route: ActivatedRoute,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.cargarPeriodos();
  }

  get correspondenciasDisponibles(): boolean {
    return !this.errorCorrespondencias;
  }

  get tieneAsignacionesDirectas(): boolean {
    return this.filas.some(fila => fila.tipoOrigen === 'marco');
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
        this.cargarMarcoEInicializar();
      },
      error: () => {
        this.errorPeriodos = true;
      },
    });
  }

  private cargarMarcoEInicializar(): void {
    this.marcoCargando = true;
    this.catalogoService
      .listarVersiones()
      .pipe(
        switchMap((versiones: any[]) => {
          const activa = versiones.find((item: any) => item.activo) ?? versiones[0];
          return activa ? this.catalogoService.listarDimensiones(activa.slug) : of([]);
        }),
        catchError(() => of(null))
      )
      .subscribe((dimensiones) => {
        this.marcoCargando = false;
        if (dimensiones === null) {
          this.marcoError = true;
          this.dimensionesMarco = [];
        } else {
          this.marcoError = false;
          this.dimensionesMarco = dimensiones;
        }
        this.leerFiltrosDesdeUrl();
        this.sincronizarUrl();
        this.cargarDatos();
        if (!this.marcoError && (this.filtros.dimension || this.filtros.componente)) {
          this.cargarOrigenesMarco();
        }
      });
  }

  get opcionesDimensiones(): OpcionFiltro[] {
    return this.dimensionesMarco.map((dimension) => ({
      valor: String(dimension.id),
      etiqueta: `${dimension.codigo} — ${dimension.nombre}`,
    }));
  }

  get opcionesComponentes(): OpcionFiltro[] {
    const dimension = this.dimensionesMarco.find((item) => String(item.id) === this.filtros.dimension);
    const componentes = dimension?.componentes ?? [];
    return componentes.map((componente: any) => ({
      valor: String(componente.id),
      etiqueta: `${componente.codigo_completo || componente.codigo} — ${componente.nombre}`,
    }));
  }

  get filtroMarcoActivo(): boolean {
    return Boolean(this.filtros.dimension || this.filtros.componente);
  }

  onDimensionMarcoChange(valor: string): void {
    this.filtros.dimension = valor;
    this.filtros.componente = '';
    this.currentPage = 1;
    this.marcoListo = false;
    this.marcoFiltroError = false;
    this.avisoMarcoTruncado = false;
    if (!valor) {
      this.limpiarOrigenesMarco();
      this.aplicarFiltros();
      return;
    }
    this.cargarOrigenesMarco();
  }

  onComponenteMarcoChange(valor: string): void {
    this.filtros.componente = valor;
    this.currentPage = 1;
    this.marcoListo = false;
    this.marcoFiltroError = false;
    this.avisoMarcoTruncado = false;
    if (!valor) {
      if (this.filtros.dimension) {
        this.cargarOrigenesMarco();
      } else {
        this.limpiarOrigenesMarco();
        this.aplicarFiltros();
      }
      return;
    }
    this.cargarOrigenesMarco();
  }

  private limpiarOrigenesMarco(): void {
    this.marcoOrigenesIndicador = new Set<number>();
    this.marcoOrigenesCriterio = new Set<number>();
    this.marcoListo = false;
  }

  private cargarOrigenesMarco(): void {
    if (!this.filtros.dimension && !this.filtros.componente) {
      this.limpiarOrigenesMarco();
      this.aplicarFiltros();
      return;
    }
    this.cargandoOrigenesMarco = true;
    this.marcoListo = false;
    const filtro: { estado: 'confirmada'; dimension?: number; componente?: number } = { estado: 'confirmada' };
    if (this.filtros.componente) {
      filtro.componente = Number(this.filtros.componente);
    } else if (this.filtros.dimension) {
      filtro.dimension = Number(this.filtros.dimension);
    }
    this.obtenerPaginas(
      (page) => this.vinculacionService.listarCorrespondencias({ ...filtro, page }),
      MAX_PAGINAS_CORRESPONDENCIAS
    ).subscribe({
      next: (resultado) => {
        const indicadores = new Set<number>();
        const criterios = new Set<number>();
        for (const corr of resultado.items) {
          if (typeof corr.indicador_op === 'number') indicadores.add(corr.indicador_op);
          if (typeof corr.criterio_op === 'number') criterios.add(corr.criterio_op);
        }
        this.marcoOrigenesIndicador = indicadores;
        this.marcoOrigenesCriterio = criterios;
        this.cargandoOrigenesMarco = false;
        this.marcoListo = true;
        this.avisoMarcoTruncado = resultado.truncado;
        this.aplicarFiltros();
      },
      error: () => {
        this.cargandoOrigenesMarco = false;
        this.marcoListo = false;
        this.marcoFiltroError = true;
        this.filtros.dimension = '';
        this.filtros.componente = '';
        this.aplicarFiltros();
      },
    });
  }

  private filaPerteneceAlMarco(fila: FilaSeguimiento): boolean {
    if (fila.tipoOrigen === 'marco') return rutaCoincideConMarco(fila.rutaMarco, this.filtros);
    if (this.marcoOrigenesIndicador.has(Number(fila.indicadorId))) return true;
    if (fila.criterioId != null && this.marcoOrigenesCriterio.has(Number(fila.criterioId))) return true;
    return false;
  }

  onPeriodoChange(periodoId: string): void {
    this.periodoSeleccionadoId = periodoId;
    this.sincronizarUrl();
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
    this.resumenService.cargar(this.periodoSeleccionadoId).subscribe({
      next: (resultado) => {
        this.aplicarResultado(resultado);
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
    this.resumenService.recargarCorrespondencias().subscribe((resultado) => {
      if (resultado) this.aplicarResultado(resultado);
      this.reintentandoCorrespondencias = false;
    });
  }

  cambiarFiltro(campo: 'unidad' | 'estado' | 'revision' | 'correspondencia', valor: string): void {
    this.filtros[campo] = valor;
    this.aplicarFiltros();
  }

  limpiarFiltros(): void {
    this.filtros = { unidad: '', estado: '', revision: '', correspondencia: '', dimension: '', componente: '' };
    this.limpiarOrigenesMarco();
    this.marcoFiltroError = false;
    this.avisoMarcoTruncado = false;
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
    pagina$: (page: number) => Observable<RespuestaPaginada<T>>,
    maxPaginas: number,
    page = 1,
    acumulado: T[] = []
  ): Observable<ResultadoPaginas<T>> {
    return this.resumenService.obtenerPaginas(pagina$, maxPaginas, page, acumulado);
  }

  aplicarFiltros(): void {
    const restringirPorMarco = this.filtroMarcoActivo && this.marcoListo;
    this.filasFiltradas = this.filas.filter(
      (fila) =>
        (!this.filtros.unidad || String(fila.unidadId) === this.filtros.unidad) &&
        (!this.filtros.estado || fila.estado === this.filtros.estado) &&
        (!this.filtros.revision || fila.claveRevision === this.filtros.revision) &&
        (!this.filtros.correspondencia || fila.correspondenciaEstado === this.filtros.correspondencia) &&
        (!restringirPorMarco || this.filaPerteneceAlMarco(fila))
    );
    this.currentPage = 1;
    this.calcularMetricas();
    this.actualizarPagina();
    this.sincronizarUrl();
  }

  private actualizarPagina(): void {
    const start = (this.currentPage - 1) * this.pageSize;
    this.filasPaginadas = this.filasFiltradas.slice(start, start + this.pageSize);
  }

  private calcularMetricas(): void {
    this.metricas = calcularMetricas(this.filasFiltradas, this.correspondenciasDisponibles);
  }

  private aplicarResultado(resultado: ResultadoSeguimiento): void {
    this.filas = resultado.filas;
    this.avisosTruncado = resultado.avisosTruncado;
    this.avisoCorrespondenciaTruncada = resultado.avisoCorrespondenciaTruncada;
    this.errorCorrespondencias = !resultado.correspondenciasDisponibles;
    if (this.errorCorrespondencias && this.filtros.correspondencia !== 'directa') this.filtros.correspondencia = '';
    this.construirOpciones();
    this.aplicarFiltros();
  }

  private construirOpciones(): void {
    this.opcionesCorrespondencia = this.opcionesCorrespondencia.filter(opcion => opcion.valor !== 'directa');
    if (this.tieneAsignacionesDirectas) {
      this.opcionesCorrespondencia.push({ valor: 'directa', etiqueta: 'Asignación directa al marco' });
    }
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
    if (this.filtros.revision && !this.opcionesRevision.some((opcion) => opcion.valor === this.filtros.revision)) {
      this.opcionesRevision.push({
        valor: this.filtros.revision,
        etiqueta: ETIQUETAS_REVISION[this.filtros.revision as ClaveRevision] ?? this.filtros.revision,
      });
    }
  }

  private aOpcionesOrdenadas(mapa: Map<string, string>): OpcionFiltro[] {
    return [...mapa.entries()]
      .map(([valor, etiqueta]) => ({ valor, etiqueta }))
      .sort((a, b) => a.etiqueta.localeCompare(b.etiqueta));
  }

  etiquetaCorrespondencia(estado: EstadoCorrespondenciaFila): string {
    return ETIQUETAS_CORRESPONDENCIA[estado];
  }

  valorPeriodo(periodo: any): string {
    return String(periodo?.id ?? '');
  }

  esExportacionLimitada(): boolean {
    return this.avisosTruncado.length > 0 || this.avisoCorrespondenciaTruncada;
  }

  exportarCsv(): void {
    if (this.exportando || !this.filasFiltradas.length) return;
    this.exportando = true;
    try {
      const filasCsv = [
        [...COLUMNAS_EXPORTACION, ...(this.tieneDocumentos ? ['Documentos solicitados', 'Documentos entregados', 'Documentos aprobados'] : [])],
        ...this.filasFiltradas.map((fila) => this.filaCsv(fila)),
      ];
      const contenido =
        '\uFEFF' +
        filasCsv.map((fila) => fila.map((celda) => this.escaparCelda(celda)).join(',')).join('\r\n') +
        '\r\n';
      this.descargar(contenido, this.nombreArchivo());
    } finally {
      this.exportando = false;
    }
  }

  descargar(contenido: string, nombre: string): void {
    const blob = new Blob([contenido], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const ancla = document.createElement('a');
    ancla.href = url;
    ancla.download = nombre;
    document.body.appendChild(ancla);
    ancla.click();
    ancla.remove();
    URL.revokeObjectURL(url);
  }

  escaparCelda(valor: string): string {
    let texto = String(valor ?? '');
    if (/^[=+\-@]/.test(texto)) texto = `'${texto}`;
    if (/["\r\n]/.test(texto)) return `"${texto.replace(/"/g, '""')}"`;
    return texto;
  }

  nombreArchivo(): string {
    const periodo = this.periodos.find((item: any) => String(item.id) === String(this.periodoSeleccionadoId));
    const partes = ['Seguimiento'];
    if (periodo?.nombre) partes.push(this.sanitizarNombre(String(periodo.nombre)));
    if (this.esExportacionLimitada()) partes.push('limitado');
    partes.push(new Date().toISOString().slice(0, 10));
    return `${partes.join('_')}.csv`;
  }

  private filaCsv(fila: FilaSeguimiento): string[] {
    return [
      fila.periodoNombre,
      fila.unidadNombre,
      fila.criterioNombre,
      fila.indicadorNombre,
      fila.estadoDisplay,
      tieneEvidencia(fila) ? 'Sí' : 'No',
      fila.estadoRevision,
      this.etiquetaCorrespondencia(fila.correspondenciaEstado),
      fila.codigoDestino,
      fila.versionMarco,
      ...(this.tieneDocumentos ? [fila.documentosResumen?.solicitados, fila.documentosResumen?.entregados, fila.documentosResumen?.aprobados].map(valor => valor == null ? '' : String(valor)) : []),
    ];
  }

  private sanitizarNombre(texto: string): string {
    const limpio = texto
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/[^A-Za-z0-9]+/g, '_')
      .replace(/^_+|_+$/g, '')
      .slice(0, 60);
    return limpio || 'periodo';
  }

  private limpiarTodo(): void {
    this.filas = [];
    this.avisosTruncado = [];
    this.avisoCorrespondenciaTruncada = false;
    this.errorCorrespondencias = false;
    this.errorCarga = '';
    this.aplicarFiltros();
  }

  private leerFiltrosDesdeUrl(): void {
    const parametros = this.route.snapshot.queryParamMap;
    const revision = parametros.get('revision') ?? '';
    const correspondencia = parametros.get('correspondencia') ?? '';
    const dimension = parametros.get('dimension') ?? '';
    const componente = parametros.get('componente') ?? '';
    const clavesRevision = Object.keys(ETIQUETAS_REVISION);
    this.filtros.revision = clavesRevision.includes(revision) ? revision : '';
    this.filtros.correspondencia = correspondencia === 'directa' || this.opcionesCorrespondencia.some(
      (opcion) => opcion.valor === correspondencia
    )
      ? correspondencia
      : '';
    this.filtros.dimension = this.opcionesDimensiones.some((opcion) => opcion.valor === dimension)
      ? dimension
      : '';
    this.filtros.componente = this.opcionesComponentes.some((opcion) => opcion.valor === componente)
      ? componente
      : '';
  }

  private sincronizarUrl(): void {
    void this.router.navigate([], {
      relativeTo: this.route,
      queryParams: {
        periodo: this.periodoSeleccionadoId || null,
        revision: this.filtros.revision || null,
        correspondencia: this.filtros.correspondencia || null,
        dimension: this.filtros.dimension || null,
        componente: this.filtros.componente || null,
      },
      queryParamsHandling: 'merge',
      replaceUrl: true,
    });
  }
}
