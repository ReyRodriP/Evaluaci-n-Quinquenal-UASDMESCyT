import { Component, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ToastrService } from 'ngx-toastr';
import { AuthService } from '../../core/services/auth.service';
import { CrudTable } from '../../shared/components/CRUD/crud-table/crud-table';

type Pestana = 'observaciones' | 'auditoria' | 'usuarios';

@Component({
  selector: 'app-reportes',
  imports: [CommonModule, FormsModule, CrudTable],
  templateUrl: './reportes.html',
  styleUrl: './reportes.css',
})
export class Reportes implements OnInit, OnDestroy {
  pestanaActiva: Pestana = 'observaciones';
  loading = false;

  periodos: any[] = [];
  departamentos: any[] = [];
  usuarios: any[] = [];
  roles: any[] = [];

  // Reporte de Observaciones
  obsFiltros = { periodo: '', departamento: '', usuario: '' };
  obsRows: any[] = [];
  obsResumen = { total: 0, evidencias: 0 };
  obsColumnas = ['Evidencia', 'Indicador', 'Departamento', 'Periodo', 'Versión', 'Observador', 'Comentario', 'Fecha', 'N° Observaciones'];

  // Reporte de Auditoría
  audFiltros = { usuario: '', fecha_desde: '', fecha_hasta: '', modelo: '', accion: '' };
  audRows: any[] = [];
  audTotal = 0;
  audColumnas = ['Usuario', 'Acción', 'Modelo', 'Registro ID', 'Descripción', 'Fecha'];

  // Reporte de Usuarios
  usrFiltros = { rol: '', departamento: '', estado: '' };
  usrRows: any[] = [];
  usrResumen = { total: 0, activos: 0, inactivos: 0 };
  usrColumnas = ['Usuario', 'Nombre', 'Correo', 'Rol', 'Departamento', 'Último acceso', 'Estado'];

  constructor(
    private authService: AuthService,
    private toast: ToastrService
  ) {}

  private debounceTimer: any;

  ngOnInit(): void {
    this.loadSelectores();
    this.cargarReporteActual();
  }

  ngOnDestroy(): void {
    if (this.debounceTimer) {
      clearTimeout(this.debounceTimer);
    }
  }

  onTextoAuditoria(): void {
    if (this.debounceTimer) {
      clearTimeout(this.debounceTimer);
    }
    this.debounceTimer = setTimeout(() => this.cargarAuditoria(), 300);
  }

  cambiarPestana(pestana: Pestana): void {
    this.pestanaActiva = pestana;
    this.cargarReporteActual();
  }

  cargarReporteActual(): void {
    if (this.pestanaActiva === 'observaciones') this.cargarObservaciones();
    if (this.pestanaActiva === 'auditoria') this.cargarAuditoria();
    if (this.pestanaActiva === 'usuarios') this.cargarUsuarios();
  }

  private loadSelectores(): void {
    this.authService.listarPeriodos().subscribe((data) => (this.periodos = data));
    this.authService.listarDepartamentos().subscribe((data) => (this.departamentos = data));
    this.authService.listarUsuarios().subscribe((data) => (this.usuarios = data));
    this.authService.listarRoles().subscribe((data) => (this.roles = data));
  }

  private limpiarParametros(filtros: any): any {
    const params: any = {};
    Object.entries(filtros).forEach(([clave, valor]) => {
      if (valor !== '' && valor !== null && valor !== undefined) {
        params[clave] = String(valor);
      }
    });
    return params;
  }

  limpiarFiltrosObservaciones(): void {
    this.obsFiltros = { periodo: '', departamento: '', usuario: '' };
    this.cargarObservaciones();
  }

  limpiarFiltrosAuditoria(): void {
    this.audFiltros = { usuario: '', fecha_desde: '', fecha_hasta: '', modelo: '', accion: '' };
    this.cargarAuditoria();
  }

  limpiarFiltrosUsuarios(): void {
    this.usrFiltros = { rol: '', departamento: '', estado: '' };
    this.cargarUsuarios();
  }

  cargarObservaciones(): void {
    this.loading = true;
    const params = this.limpiarParametros(this.obsFiltros);
    this.authService.reporteObservaciones(params).subscribe({
      next: (data) => {
        this.obsRows = data.rows;
        this.obsResumen = { total: data.total_observaciones, evidencias: data.evidencias_observadas };
        this.loading = false;
      },
      error: () => {
        this.toast.error('No se pudo cargar el reporte de observaciones');
        this.loading = false;
      },
    });
  }

  cargarAuditoria(): void {
    this.loading = true;
    const params = this.limpiarParametros(this.audFiltros);
    this.authService.reporteAuditoria(params).subscribe({
      next: (data) => {
        this.audRows = data.rows;
        this.audTotal = data.total;
        this.loading = false;
      },
      error: () => {
        this.toast.error('No se pudo cargar el reporte de auditoría');
        this.loading = false;
      },
    });
  }

  cargarUsuarios(): void {
    this.loading = true;
    const params = this.limpiarParametros(this.usrFiltros);
    this.authService.reporteUsuarios(params).subscribe({
      next: (data) => {
        this.usrRows = data.rows;
        this.usrResumen = { total: data.total, activos: data.activos, inactivos: data.inactivos };
        this.loading = false;
      },
      error: () => {
        this.toast.error('No se pudo cargar el reporte de usuarios');
        this.loading = false;
      },
    });
  }

  exportar(formato: 'pdf' | 'xlsx'): void {
    let reporte: string;
    let filtros: any;
    let nombre: string;

    if (this.pestanaActiva === 'observaciones') {
      reporte = 'observaciones';
      filtros = this.limpiarParametros(this.obsFiltros);
      nombre = 'reporte_observaciones';
    } else if (this.pestanaActiva === 'auditoria') {
      reporte = 'auditoria';
      filtros = this.limpiarParametros(this.audFiltros);
      nombre = 'reporte_auditoria';
    } else {
      reporte = 'usuarios';
      filtros = this.limpiarParametros(this.usrFiltros);
      nombre = 'reporte_usuarios';
    }

    this.authService.exportarReporte(reporte, formato, filtros).subscribe({
      next: (blob) => {
        this.descargarBlob(blob, `${nombre}.${formato}`);
        this.toast.success(`Reporte exportado en ${formato.toUpperCase()}`);
      },
      error: () => this.toast.error('No se pudo exportar el reporte'),
    });
  }

  private descargarBlob(blob: Blob, nombreArchivo: string): void {
    const url = window.URL.createObjectURL(blob);
    const enlace = document.createElement('a');
    enlace.href = url;
    enlace.download = nombreArchivo;
    document.body.appendChild(enlace);
    enlace.click();
    document.body.removeChild(enlace);
    window.URL.revokeObjectURL(url);
  }
}
