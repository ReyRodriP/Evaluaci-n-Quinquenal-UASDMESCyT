import { Component, OnInit, AfterViewInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { catchError, forkJoin, of, throwError } from 'rxjs';
import { ToastrService } from 'ngx-toastr';
import { DashboardService } from '../../../../core/services/dashboard.service';
import { EvaluacionService } from '../../../../core/services/evaluacion.service';
import { OrganizacionService } from '../../../../core/services/organizacion.service';
import { PermisosService } from '../../../../core/services/permisos.service';
import ApexCharts from 'apexcharts';

@Component({
  selector: 'app-dashboard',
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.css',
})
export class Dashboard implements OnInit, AfterViewInit, OnDestroy {
  resumen: any = {}
  avance: any[] = []
  periodos: any[] = []
  unidades: any[] = []
  tiposUnidad: any[] = []
  criterios: any[] = []
  indicadores: any[] = []
  pendientes: any[] = []
  periodoSeleccionadoId = ''
  unidadSeleccionadaId = ''
  tipoSeleccionadoId = ''
  criterioSeleccionadoId = ''
  indicadorSeleccionadoId = ''
  estadoSeleccionado = ''
  filtrosAplicados: Record<string, string> = {}
  mostrarFiltrosExtras = false
  agrupamientoAvance = 'unidad'
  loading = true
  readonly estadosAsignacion = [
    { value: 'pendiente', label: 'Pendiente' },
    { value: 'en_progreso', label: 'En revisión' },
    { value: 'observada', label: 'Observada' },
    { value: 'aprobado', label: 'Aprobada' },
    { value: 'rechazado', label: 'Rechazada' },
    { value: 'completado', label: 'Completada' },
  ]
  readonly agrupamientos = [
    { value: 'unidad', label: 'Por unidad' },
    { value: 'criterio', label: 'Por criterio' },
    { value: 'estado', label: 'Por estado' },
  ]
  private graficos: ApexCharts[] = []
  private observer?: MutationObserver
  private resumenCargado = false
  private avanceCargado = false
  private renderEnCola = false

  constructor(
    private dashboardService: DashboardService,
    private evaluacionService: EvaluacionService,
    private organizacionService: OrganizacionService,
    private permisos: PermisosService,
    private route: ActivatedRoute,
    private router: Router,
    private toast: ToastrService
  ) {}

  ngOnInit(): void {
    this.cargarPeriodos()
    this.observarTema()
  }

  ngOnDestroy(): void {
    this.observer?.disconnect()
    this.destruirGraficos()
  }

  cargarDatos(): void {
    const filtros = this.construirFiltros()
    this.loading = true
    this.resumenCargado = false
    this.avanceCargado = false
    this.renderEnCola = false
    this.dashboardService.obtenerResumen(filtros).subscribe({
      next: (data) => {
        this.resumen = data
        this.loading = false
        this.resumenCargado = true
        this.marcarListo()
      },
      error: () => {
        this.loading = false
        this.resumenCargado = true
        this.toast.error('No se pudo cargar el tablero')
      },
    })
    this.cargarPendientes()
    this.cargarAvance()
  }

  private cargarPendientes(): void {
    this.dashboardService.obtenerPendientes(this.construirFiltros()).subscribe({
      next: (data) => this.pendientes = data,
      error: () => this.toast.error('No se pudieron cargar las acciones pendientes'),
    })
  }

  private cargarAvance(): void {
    this.dashboardService.obtenerAvance(this.construirFiltros(), this.agrupamientoAvance).subscribe({
      next: (data) => {
        this.avance = data
        this.avanceCargado = true
        this.marcarListo()
      },
      error: () => {
        this.avanceCargado = true
        this.toast.error('No se pudo cargar el avance')
      },
    })
  }

  private marcarListo(): void {
    if (this.resumenCargado && this.avanceCargado && !this.renderEnCola) {
      this.renderEnCola = true
      this.diferirGraficos()
    }
  }

  private cargarPeriodos(): void {
    forkJoin({
      periodos: this.evaluacionService.listarPeriodos().pipe(catchError(() => of([]))),
      activo: this.evaluacionService.periodoActivo().pipe(
        catchError((error) => error.status === 404 ? of(null) : throwError(() => error))
      ),
      unidades: this.organizacionService.listarUnidadesOrganizacionales().pipe(catchError(() => of([]))),
      tipos: this.organizacionService.listarTiposUnidad().pipe(catchError(() => of([]))),
      criterios: this.evaluacionService.listarCriterios().pipe(catchError(() => of([]))),
      indicadores: this.evaluacionService.listarIndicadores().pipe(catchError(() => of([]))),
    }).subscribe({
      next: ({ periodos, activo, unidades, tipos, criterios, indicadores }) => {
        this.periodos = periodos
        this.unidades = unidades
        this.tiposUnidad = tipos
        this.criterios = criterios
        this.indicadores = indicadores
        const periodoUrl = this.route.snapshot.queryParamMap.get('periodo')
        const solicitado = periodos.find((periodo: any) => String(periodo.id) === periodoUrl)
        const seleccionSolicitadaValida = periodoUrl && (solicitado || !periodos.length)
        this.periodoSeleccionadoId = String(seleccionSolicitadaValida ? periodoUrl : activo?.id ?? '')
        this.unidadSeleccionadaId = this.route.snapshot.queryParamMap.get('unidad') || ''
        this.tipoSeleccionadoId = this.route.snapshot.queryParamMap.get('tipo') || ''
        this.criterioSeleccionadoId = this.route.snapshot.queryParamMap.get('criterio') || ''
        this.indicadorSeleccionadoId = this.route.snapshot.queryParamMap.get('indicador') || ''
        this.estadoSeleccionado = this.route.snapshot.queryParamMap.get('estado') || ''
        if (activo && !this.periodos.some((periodo: any) => Number(periodo.id) === Number(activo.id))) {
          this.periodos = [...this.periodos, activo]
        }
        this.filtrosAplicados = { ...this.construirFiltros() }
        this.cargarDatos()
      },
      error: () => {
        this.toast.error('No se pudieron cargar los períodos')
        this.loading = false
      },
    })
  }

  onPeriodoChange(periodoId: string): void {
    this.periodoSeleccionadoId = periodoId
    this.criterioSeleccionadoId = ''
    this.indicadorSeleccionadoId = ''
    this.aplicarFiltros()
  }

  onCriterioChange(criterioId: string): void {
    this.criterioSeleccionadoId = criterioId
    this.indicadorSeleccionadoId = ''
  }

  aplicarFiltros(): void {
    this.filtrosAplicados = { ...this.construirFiltros() }
    this.mostrarFiltrosExtras = false
    this.actualizarFiltrosUrl()
    this.cargarDatos()
  }

  cancelarFiltros(): void {
    this.unidadSeleccionadaId = this.filtrosAplicados['unidad'] ?? ''
    this.tipoSeleccionadoId = this.filtrosAplicados['tipo'] ?? ''
    this.criterioSeleccionadoId = this.filtrosAplicados['criterio'] ?? ''
    this.indicadorSeleccionadoId = this.filtrosAplicados['indicador'] ?? ''
    this.estadoSeleccionado = this.filtrosAplicados['estado'] ?? ''
    this.mostrarFiltrosExtras = false
  }

  limpiarFiltros(): void {
    this.unidadSeleccionadaId = ''
    this.tipoSeleccionadoId = ''
    this.criterioSeleccionadoId = ''
    this.indicadorSeleccionadoId = ''
    this.estadoSeleccionado = ''
    this.aplicarFiltros()
  }

  cambiarAgrupamiento(agrupamiento: string): void {
    if (agrupamiento === this.agrupamientoAvance) return
    this.agrupamientoAvance = agrupamiento
    this.renderEnCola = false
    this.avanceCargado = false
    this.cargarAvance()
  }

  get filtrosModificados(): boolean {
    const actual = this.construirFiltros()
    const claves = new Set([...Object.keys(this.filtrosAplicados), ...Object.keys(actual)])
    return Array.from(claves).some((key) => (actual[key] ?? '') !== (this.filtrosAplicados[key] ?? ''))
  }

  get tieneFiltrosAplicados(): boolean {
    return Object.values(this.filtrosAplicados).some(Boolean)
  }

  private construirFiltros(): Record<string, string> {
    const filtros: Record<string, string> = {}
    const valores: Record<string, string> = {
      periodo: this.periodoSeleccionadoId,
      unidad: this.unidadSeleccionadaId,
      tipo: this.tipoSeleccionadoId,
      criterio: this.criterioSeleccionadoId,
      indicador: this.indicadorSeleccionadoId,
      estado: this.estadoSeleccionado,
    }
    Object.entries(valores).forEach(([key, value]) => {
      if (value) filtros[key] = value
    })
    return filtros
  }

  private actualizarFiltrosUrl(): void {
    void this.router.navigate([], {
      relativeTo: this.route,
      queryParams: {
        periodo: this.periodoSeleccionadoId || null,
        unidad: this.unidadSeleccionadaId || null,
        tipo: this.tipoSeleccionadoId || null,
        criterio: this.criterioSeleccionadoId || null,
        indicador: this.indicadorSeleccionadoId || null,
        estado: this.estadoSeleccionado || null,
      },
      queryParamsHandling: 'merge',
      replaceUrl: true,
    })
  }

  unitPath(unit: any): string {
    const names = [unit.nombre]
    let parentId = unit.unidad_padre
    while (parentId) {
      const parent = this.unidades.find((candidate) => Number(candidate.id) === Number(parentId))
      if (!parent) break
      names.unshift(parent.nombre)
      parentId = parent.unidad_padre
    }
    return names.join(' / ')
  }

  get rolDashboard(): string {
    if (this.permisos.esSuperuser || this.permisos.tieneGrupo('Administrador General')) return 'Vista institucional'
    if (this.permisos.tieneGrupo('Coordinador Quinquenal')) return 'Seguimiento institucional'
    if (this.permisos.tieneGrupo('Responsable Departamental')) return 'Seguimiento de mi unidad'
    if (this.permisos.tieneGrupo('Revisor Institucional')) return 'Revisión de mi ámbito'
    if (this.permisos.tieneGrupo('Evaluador Externo')) return 'Evaluación externa'
    return 'Resumen de consulta'
  }

  get tituloPendientes(): string {
    if (this.permisos.esSuperuser || this.permisos.tieneGrupo('Administrador General')) return 'Alertas y pendientes'
    if (this.permisos.tieneGrupo('Coordinador Quinquenal')) return 'Pendientes de la evaluación'
    if (this.permisos.tieneGrupo('Responsable Departamental')) return 'Mis pendientes'
    if (this.permisos.tieneGrupo('Revisor Institucional')) return 'Pendientes de revisión'
    if (this.permisos.tieneGrupo('Evaluador Externo')) return 'Elementos pendientes'
    return ''
  }

  get hayAlertas(): boolean {
    return Boolean(this.resumen?.observadas || this.resumen?.sin_evidencia || this.resumen?.pendientes)
  }

  claseEstado(estado: string): string {
    return (
      {
        pendiente: 'chip-pendiente',
        en_progreso: 'chip-en-progreso',
        observada: 'chip-observada',
        aprobado: 'chip-aprobado',
        rechazado: 'chip-rechazado',
        completado: 'chip-completado',
      }[estado] ?? 'chip-pendiente'
    )
  }

  get criteriosPeriodo(): any[] {
    return this.criterios.filter((criterio: any) =>
      !criterio.periodo || String(criterio.periodo) === this.periodoSeleccionadoId
    )
  }

  get indicadoresPeriodo(): any[] {
    const criteriosIds = new Set(this.criteriosPeriodo.map((criterio: any) => Number(criterio.id)))
    return this.indicadores.filter((indicador: any) => criteriosIds.has(Number(indicador.criterio)))
  }

  private diferirGraficos(): void {
    const idle = (window as any).requestIdleCallback
      ? (cb: () => void) => (window as any).requestIdleCallback(cb, { timeout: 2000 })
      : (cb: () => void) => window.setTimeout(cb, 200);
    idle(() => this.inicializarGraficos());
  }

  ngAfterViewInit(): void {
    if (!this.loading) this.inicializarGraficos()
  }

  private esOscuro(): boolean {
    return document.body.classList.contains('dark')
  }

  private observarTema(): void {
    this.observer = new MutationObserver(() => this.inicializarGraficos())
    this.observer.observe(document.body, { attributes: true, attributeFilter: ['class'] })
  }

  private inicializarGraficos(): void {
    this.destruirGraficos()
    const idle = (cb: () => void) =>
      window.requestIdleCallback
        ? window.requestIdleCallback(() => cb(), { timeout: 3000 })
        : window.setTimeout(() => cb(), 300)
    // Un grafico por callback para que ningun ciclo supere los 50ms de "long task".
    idle(() => this.graficoEstado())
    idle(() => this.graficoAvance())
  }

  private destruirGraficos(): void {
    this.graficos.forEach(g => g.destroy())
    this.graficos = []
  }

  private graficoEstado(): void {
    const el = document.getElementById('chart-estado')
    if (!el) return
    const dark = this.esOscuro()
    const filas = [
      { nombre: 'Pendientes', valor: this.resumen.pendientes || 0, color: '#f59e0b' },
      { nombre: 'En revisión', valor: this.resumen.en_progreso || 0, color: '#3b82f6' },
      { nombre: 'Observadas', valor: this.resumen.observadas || 0, color: '#a855f7' },
      { nombre: 'Aprobadas', valor: this.resumen.aprobadas || 0, color: '#22c55e' },
      { nombre: 'Rechazadas', valor: this.resumen.rechazadas || 0, color: '#ef4444' },
      { nombre: 'Completadas', valor: this.resumen.completadas || 0, color: '#0f766e' },
    ].filter((fila) => fila.valor > 0)
    const grafico = new ApexCharts(el, {
      chart: {
        type: 'bar',
        fontFamily: 'inherit',
        toolbar: { show: false },
        foreColor: dark ? '#cbd5e1' : '#475569',
        height: 250,
      },
      series: [{ name: 'Asignaciones', data: filas.map((fila) => fila.valor) }],
      colors: filas.map((fila) => fila.color),
      plotOptions: {
        bar: { borderRadius: 4, horizontal: true, distributed: true, barHeight: '55%' },
      },
      dataLabels: { enabled: true },
      xaxis: { categories: filas.map((fila) => fila.nombre) },
      legend: { show: false },
      tooltip: { y: { formatter: (v: number) => v + ' asignaciones' } },
    })
    grafico.render()
    this.graficos.push(grafico)
  }

  private graficoAvance(): void {
    const el = document.getElementById('chart-avance')
    if (!el || !this.avance.length) return
    const dark = this.esOscuro()
    const esEstado = this.agrupamientoAvance === 'estado'
    const ordenado = [...this.avance].sort((a, b) => b.porcentaje - a.porcentaje)
    const nombres = ordenado.map((a) => a.nombre)
    const valores = ordenado.map((a) => (esEstado ? a.asignaciones || 0 : a.porcentaje))
    const altura = Math.max(250, nombres.length * 42 + 60)
    const grafico = new ApexCharts(el, {
      chart: {
        type: 'bar',
        fontFamily: 'inherit',
        toolbar: { show: false },
        foreColor: dark ? '#cbd5e1' : '#475569',
        height: altura,
      },
      series: [{ name: esEstado ? 'Asignaciones' : 'Avance (%)', data: valores }],
      colors: ['#3b82f6'],
      plotOptions: { bar: { borderRadius: 4, horizontal: true } },
      dataLabels: {
        enabled: true,
        formatter: (v: number) => (esEstado ? String(v) : v + '%'),
        style: { colors: [dark ? '#e2e8f0' : '#0f172a'], fontSize: '11px' },
      },
      xaxis: esEstado
        ? { categories: nombres }
        : { categories: nombres, max: 100, labels: { formatter: (v: number) => v + '%' } },
      yaxis: { labels: { style: { fontSize: '11px' } } },
      tooltip: { y: { formatter: (v: number) => (esEstado ? v + ' asignaciones' : v + '%') } },
    })
    grafico.render()
    this.graficos.push(grafico)
  }
}