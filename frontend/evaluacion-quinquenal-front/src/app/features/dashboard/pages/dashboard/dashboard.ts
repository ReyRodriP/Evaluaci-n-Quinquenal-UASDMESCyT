import { Component, OnInit, AfterViewInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { AuthService } from '../../../../core/services/auth.service';
import ApexCharts from 'apexcharts';

@Component({
  selector: 'app-dashboard',
  imports: [CommonModule, RouterLink],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.css',
})
export class Dashboard implements OnInit, AfterViewInit, OnDestroy {
  resumen: any = {}
  avance: any[] = []
  loading = true
  private graficos: ApexCharts[] = []
  private observer?: MutationObserver

  constructor(private authService: AuthService) {}

  ngOnInit(): void {
    this.cargarDatos()
    this.observarTema()
  }

  ngOnDestroy(): void {
    this.observer?.disconnect()
    this.destruirGraficos()
  }

  cargarDatos(): void {
    this.authService.obtenerResumen().subscribe({
      next: (data) => {
        this.resumen = data
        this.loading = false
        setTimeout(() => this.inicializarGraficos(), 50)
      },
      error: () => this.loading = false,
    })
    this.authService.obtenerAvance().subscribe({
      next: (data) => this.avance = data,
    })
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
    this.graficoPastel()
    this.graficoAvance()
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
