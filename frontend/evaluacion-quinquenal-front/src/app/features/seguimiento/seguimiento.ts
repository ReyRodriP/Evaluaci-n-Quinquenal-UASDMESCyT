import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { Observable, catchError, forkJoin, of } from 'rxjs';
import { Pagination } from '../../shared/components/CRUD/pagination/pagination';
import { EvaluacionService } from '../../core/services/evaluacion.service';
import { SeguimientoResumenService } from '../../core/services/seguimiento-resumen.service';
import { RespuestaPaginada } from '../../core/models/vinculacion.model';
import {
  ETIQUETAS_CORRESPONDENCIA,
  EstadoCorrespondenciaFila,
  FilaSeguimiento,
  Metricas,
  ResultadoPaginas,
  ResultadoSeguimiento,
  calcularMetricas,
} from '../../core/models/seguimiento.model';

export const COLUMNAS_EXPORTACION = [
  'Período',
  'Unidad responsable',
  'Criterio operativo',
  'Indicador operativo',
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

  constructor(
    private evaluacionService: EvaluacionService,
    private resumenService: SeguimientoResumenService,
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
    pagina$: (page: number) => Observable<RespuestaPaginada<T>>,
    maxPaginas: number,
    page = 1,
    acumulado: T[] = []
  ): Observable<ResultadoPaginas<T>> {
    return this.resumenService.obtenerPaginas(pagina$, maxPaginas, page, acumulado);
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
    this.metricas = calcularMetricas(this.filasFiltradas, this.correspondenciasDisponibles);
  }

  private aplicarResultado(resultado: ResultadoSeguimiento): void {
    this.filas = resultado.filas;
    this.avisosTruncado = resultado.avisosTruncado;
    this.avisoCorrespondenciaTruncada = resultado.avisoCorrespondenciaTruncada;
    this.errorCorrespondencias = !resultado.correspondenciasDisponibles;
    if (this.errorCorrespondencias) this.filtros.correspondencia = '';
    this.construirOpciones();
    this.aplicarFiltros();
  }

  private construirOpciones(): void {
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
        COLUMNAS_EXPORTACION,
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
      fila.evidenciaId != null ? 'Sí' : 'No',
      fila.estadoRevision,
      this.etiquetaCorrespondencia(fila.correspondenciaEstado),
      fila.codigoDestino,
      fila.versionMarco,
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

  private actualizarPeriodoUrl(): void {
    void this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { periodo: this.periodoSeleccionadoId || null },
      queryParamsHandling: 'merge',
      replaceUrl: true,
    });
  }
}
