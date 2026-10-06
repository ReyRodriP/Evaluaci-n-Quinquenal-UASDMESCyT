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
  readonly estadosAsignacion = [
    { value: 'pendiente', label: 'Pendiente' },
    { value: 'en_progreso', label: 'En revisión' },
    { value: 'observada', label: 'Observada' },
    { value: 'aprobado', label: 'Aprobada' },
    { value: 'rechazado', label: 'Rechazada' },
    { value: 'completado', label: 'Completada' },
  ]
  loading = true
  private graficos: ApexCharts[] = []
  private observer?: MutationObserver

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
    this.dashboardService.obtenerResumen(filtros).subscribe({
      next: (data) => {
        this.resumen = data
        this.loading = false
        this.diferirGraficos()
      },
      error: () => {
        this.loading = false
        this.toast.error('No se pudo cargar el tablero')
      },
    })
    this.dashboardService.obtenerAvance(filtros).subscribe({
      next: (data) => this.avance = data,
      error: () => this.toast.error('No se pudo cargar el avance'),
    })
    this.dashboardService.obtenerPendientes(filtros).subscribe({
      next: (data) => this.pendientes = data,
      error: () => this.toast.error('No se pudieron cargar las acciones pendientes'),
    })
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
        if (this.periodoSeleccionadoId !== periodoUrl) this.actualizarFiltrosUrl()
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
    this.onFiltrosChange()
  }

  onCriterioChange(criterioId: string): void {
    this.criterioSeleccionadoId = criterioId
    this.indicadorSeleccionadoId = ''
    this.onFiltrosChange()
  }

  onFiltrosChange(): void {
    this.loading = true
    this.actualizarFiltrosUrl()
    this.cargarDatos()
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

  get esRevisorInstitucional(): boolean {
    return this.permisos.tieneGrupo('Revisor Institucional')
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
    idle(() => this.graficoPastel())
    idle(() => this.graficoAvance())
  }

  private destruirGraficos(): void {
    this.graficos.forEach(g => g.destroy())
    this.graficos = []
  }

  private graficoPastel(): void {
    const el = document.getElementById('chart-pastel')
    if (!el) return
    const dark = this.esOscuro()
    const grafico = new ApexCharts(el, {
      chart: {
        type: 'donut',
        fontFamily: 'inherit',
        foreColor: dark ? '#cbd5e1' : '#475569',
      },
      labels: ['Pendientes', 'En progreso', 'Aprobadas', 'Observadas', 'Rechazadas'],
      series: [
        this.resumen.pendientes || 0,
        this.resumen.en_progreso || 0,
        this.resumen.aprobadas || 0,
        this.resumen.observadas || 0,
        this.resumen.rechazadas || 0,
      ],
      colors: ['#f59e0b', '#3b82f6', '#22c55e', '#a855f7', '#ef4444'],
      plotOptions: { pie: { donut: { size: '60%' } } },
      legend: { position: 'bottom' },
      responsive: [{ breakpoint: 480, options: { chart: { width: 300 }, legend: { position: 'bottom' } } }],
    })
    grafico.render()
    this.graficos.push(grafico)
  }

  private graficoAvance(): void {
    const el = document.getElementById('chart-avance')
    if (!el || !this.avance.length) return
    const dark = this.esOscuro()
    const ordenado = [...this.avance].sort((a, b) => b.porcentaje - a.porcentaje)
    const facultades = ordenado.map(a => a.facultad)
    const porcentajes = ordenado.map(a => Math.round(a.porcentaje * 100) / 100)
    const altura = Math.max(280, facultades.length * 42 + 60)
    const grafico = new ApexCharts(el, {
      chart: {
        type: 'bar',
        fontFamily: 'inherit',
        toolbar: { show: false },
        foreColor: dark ? '#cbd5e1' : '#475569',
        height: altura,
      },
      series: [{ name: 'Avance (%)', data: porcentajes }],
      colors: ['#3b82f6'],
      plotOptions: { bar: { borderRadius: 4, horizontal: true } },
      dataLabels: {
        enabled: true,
        formatter: (v: number) => v + '%',
        style: { colors: [dark ? '#e2e8f0' : '#0f172a'], fontSize: '11px' },
      },
      xaxis: { categories: facultades, max: 100, labels: { formatter: (v: number) => v + '%' } },
      yaxis: { labels: { style: { fontSize: '11px' } } },
      tooltip: { y: { formatter: (v: number) => v + '%' } },
    })
    grafico.render()
    this.graficos.push(grafico)
  }
}
