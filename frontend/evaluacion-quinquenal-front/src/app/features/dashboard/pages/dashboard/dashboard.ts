import { Component, OnInit, AfterViewInit } from '@angular/core';
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
export class Dashboard implements OnInit, AfterViewInit {
  resumen: any = {}
  avance: any[] = []
  loading = true

  constructor(private authService: AuthService) {}

  ngOnInit(): void {
    this.cargarDatos()
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

  private inicializarGraficos(): void {
    this.graficoPastel()
    this.graficoAvance()
  }

  private graficoPastel(): void {
    const el = document.getElementById('chart-pastel')
    if (!el) return
    new ApexCharts(el, {
      chart: { type: 'donut', fontFamily: 'inherit' },
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
    }).render()
  }

  private graficoAvance(): void {
    const el = document.getElementById('chart-avance')
    if (!el || !this.avance.length) return
    const facultades = this.avance.map(a => a.facultad)
    const porcentajes = this.avance.map(a => Math.round(a.porcentaje * 100) / 100)
    new ApexCharts(el, {
      chart: { type: 'bar', fontFamily: 'inherit', toolbar: { show: false } },
      series: [{ name: 'Avance (%)', data: porcentajes }],
      xaxis: { categories: facultades, labels: { rotate: -30 } },
      colors: ['#3b82f6'],
      plotOptions: { bar: { borderRadius: 4, horizontal: false } },
      dataLabels: { enabled: true, formatter: (v: number) => v + '%' },
      yaxis: { max: 100, labels: { formatter: (v: number) => v + '%' } },
      tooltip: { y: { formatter: (v: number) => v + '%' } },
    }).render()
  }
}
