import { Component, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ToastrService } from 'ngx-toastr';
import { AuthService } from '../../core/services/auth.service';
import { CrudTable } from '../../shared/components/CRUD/crud-table/crud-table';
import { Pagination } from '../../shared/components/CRUD/pagination/pagination';

type Pestana =
  | 'general'
  | 'facultad'
  | 'departamento'
  | 'evidencias'
  | 'observaciones'
  | 'auditoria'
  | 'usuarios';

@Component({
  selector: 'app-reportes',
  imports: [CommonModule, FormsModule, CrudTable, Pagination],
  templateUrl: './reportes.html',
  styleUrl: './reportes.css',
})
export class Reportes implements OnInit, OnDestroy {
  pestanaActiva: Pestana = 'general';
  loading = false;
  pageSize = 10;

  periodos: any[] = [];
  facultades: any[] = [];
  departamentos: any[] = [];
  criterios: any[] = [];
  usuarios: any[] = [];
  roles: any[] = [];

  // Reporte 1: General del periodo
  genFiltros = { periodo: '' };
  genData: any = {};

  // Reporte 2: Por facultad
  facId = '';
  facData: any = { departamentos: [], pendientes: 0, aprobadas: 0 };
  facColumnas = ['Departamento', 'Total Asignaciones', 'Evidencias', 'Pendientes', 'Aprobadas'];

  // Reporte 3: Por departamento
  depId = '';
  depRows: any[] = [];
  depPage = 1;
  depTotal = 0;
  depColumnas = ['Indicador', 'Estado', 'Fecha Modificación', 'Responsable', 'Última Versión'];

  // Reporte 4: Evidencias
  evFiltros = { estado: '', departamento: '', periodo: '', criterio: '' };
  evRows: any[] = [];
  evPage = 1;
  evTotal = 0;
  evColumnas = ['Indicador', 'Evidencia', 'Departamento', 'Criterio', 'Periodo', 'Estado', 'Fecha'];

  // Reporte 5: Observaciones
  obsFiltros = { periodo: '', departamento: '', usuario: '' };
  obsRows: any[] = [];
  obsPage = 1;
  obsResumen = { total: 0, evidencias: 0 };
  obsColumnas = ['Evidencia', 'Indicador', 'Departamento', 'Periodo', 'Versión', 'Observador', 'Comentario', 'Fecha', 'N° Observaciones'];

  // Reporte 6: Auditoría
  audFiltros = { usuario: '', fecha_desde: '', fecha_hasta: '', modelo: '', accion: '' };
  audRows: any[] = [];
  audPage = 1;
  audTotal = 0;
  audColumnas = ['Usuario', 'Acción', 'Modelo', 'Registro ID', 'Descripción', 'Fecha'];

  // Reporte 7: Usuarios
  usrFiltros = { rol: '', departamento: '', estado: '' };
  usrRows: any[] = [];
  usrPage = 1;
  usrResumen = { total: 0, activos: 0, inactivos: 0 };
  usrColumnas = ['Usuario', 'Nombre', 'Correo', 'Rol', 'Departamento', 'Último Acceso', 'Estado'];

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

  cambiarPestana(pestana: Pestana): void {
    this.pestanaActiva = pestana;
    this.cargarReporteActual();
  }

  cargarReporteActual(): void {
    if (this.pestanaActiva === 'general') this.cargarGeneral();
    if (this.pestanaActiva === 'facultad' && this.facId) this.cargarFacultad();
    if (this.pestanaActiva === 'departamento' && this.depId) this.cargarDepartamento();
    if (this.pestanaActiva === 'evidencias') this.cargarEvidencias();
    if (this.pestanaActiva === 'observaciones') this.cargarObservaciones();
    if (this.pestanaActiva === 'auditoria') this.cargarAuditoria();
    if (this.pestanaActiva === 'usuarios') this.cargarUsuarios();
  }

  private loadSelectores(): void {
    this.authService.listarPeriodos().subscribe((data) => (this.periodos = data));
    this.authService.listarFacultades().subscribe((data) => (this.facultades = data));
    this.authService.listarDepartamentos().subscribe((data) => (this.departamentos = data));
    this.authService.listarCriterios().subscribe((data) => (this.criterios = data));
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

  // ===================== GENERAL =====================
  cargarGeneral(): void {
    this.loading = true;
    const params = this.limpiarParametros(this.genFiltros);
    this.authService.reporteGeneral(params).subscribe({
      next: (data) => {
        this.genData = data;
        this.loading = false;
      },
      error: () => {
        this.toast.error('No se pudo cargar el reporte general');
        this.loading = false;
      },
    });
  }

  limpiarFiltrosGeneral(): void {
    this.genFiltros = { periodo: '' };
    this.cargarGeneral();
  }

  // ===================== FACULTAD =====================
  cargarFacultad(): void {
    if (!this.facId) return;
    this.loading = true;
    this.authService.reporteFacultad(Number(this.facId)).subscribe({
      next: (data) => {
        this.facData = data;
        this.loading = false;
      },
      error: () => {
        this.toast.error('No se pudo cargar el reporte por facultad');
        this.loading = false;
      },
    });
  }

  // ===================== DEPARTAMENTO =====================
  cargarDepartamento(): void {
    if (!this.depId) return;
    this.loading = true;
    const params = { page: this.depPage, page_size: this.pageSize };
    this.authService.reporteDepartamento(Number(this.depId), params).subscribe({
      next: (data) => {
        this.depRows = data.rows;
        this.depTotal = data.total;
        this.loading = false;
      },
      error: () => {
        this.toast.error('No se pudo cargar el reporte por departamento');
        this.loading = false;
      },
    });
  }

  cambiarPaginaDepartamento(pagina: number): void {
    this.depPage = pagina;
    this.cargarDepartamento();
  }

  // ===================== EVIDENCIAS =====================
  cargarEvidencias(): void {
    this.loading = true;
    const params = { ...this.limpiarParametros(this.evFiltros), page: this.evPage, page_size: this.pageSize };
    this.authService.reporteEvidencias(params).subscribe({
      next: (data) => {
        this.evRows = data.rows;
        this.evTotal = data.total;
        this.loading = false;
      },
      error: () => {
        this.toast.error('No se pudo cargar el reporte de evidencias');
        this.loading = false;
      },
    });
  }

  limpiarFiltrosEvidencias(): void {
    this.evFiltros = { estado: '', departamento: '', periodo: '', criterio: '' };
    this.evPage = 1;
    this.cargarEvidencias();
  }

  cambiarPaginaEvidencias(pagina: number): void {
    this.evPage = pagina;
    this.cargarEvidencias();
  }

  // ===================== OBSERVACIONES =====================
  cargarObservaciones(): void {
    this.loading = true;
    const params = { ...this.limpiarParametros(this.obsFiltros), page: this.obsPage, page_size: this.pageSize };
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

  limpiarFiltrosObservaciones(): void {
    this.obsFiltros = { periodo: '', departamento: '', usuario: '' };
    this.obsPage = 1;
    this.cargarObservaciones();
  }

  cambiarPaginaObservaciones(pagina: number): void {
    this.obsPage = pagina;
    this.cargarObservaciones();
  }

  // ===================== AUDITORÍA =====================
  onTextoAuditoria(): void {
    if (this.debounceTimer) {
      clearTimeout(this.debounceTimer);
    }
    this.debounceTimer = setTimeout(() => this.cargarAuditoria(), 300);
  }

  cargarAuditoria(): void {
    this.loading = true;
    const params = { ...this.limpiarParametros(this.audFiltros), page: this.audPage, page_size: this.pageSize };
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

  limpiarFiltrosAuditoria(): void {
    this.audFiltros = { usuario: '', fecha_desde: '', fecha_hasta: '', modelo: '', accion: '' };
    this.audPage = 1;
    this.cargarAuditoria();
  }

  cambiarPaginaAuditoria(pagina: number): void {
    this.audPage = pagina;
    this.cargarAuditoria();
  }

  // ===================== USUARIOS =====================
  cargarUsuarios(): void {
    this.loading = true;
    const params = { ...this.limpiarParametros(this.usrFiltros), page: this.usrPage, page_size: this.pageSize };
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

  limpiarFiltrosUsuarios(): void {
    this.usrFiltros = { rol: '', departamento: '', estado: '' };
    this.usrPage = 1;
    this.cargarUsuarios();
  }

  cambiarPaginaUsuarios(pagina: number): void {
    this.usrPage = pagina;
    this.cargarUsuarios();
  }

  // ===================== EXPORTAR =====================
  exportar(formato: 'pdf' | 'xlsx'): void {
    let reporte: string;
    let filtros: any;
    let nombre: string;

    switch (this.pestanaActiva) {
      case 'general':
        reporte = 'general';
        filtros = this.limpiarParametros(this.genFiltros);
        nombre = 'reporte_general';
        break;
      case 'facultad':
        reporte = `facultad/${this.facId}`;
        filtros = {};
        nombre = `reporte_facultad_${this.facId}`;
        break;
      case 'departamento':
        reporte = `departamento/${this.depId}`;
        filtros = {};
        nombre = `reporte_departamento_${this.depId}`;
        break;
      case 'evidencias':
        reporte = 'evidencias';
        filtros = this.limpiarParametros(this.evFiltros);
        nombre = 'reporte_evidencias';
        break;
      case 'observaciones':
        reporte = 'observaciones';
        filtros = this.limpiarParametros(this.obsFiltros);
        nombre = 'reporte_observaciones';
        break;
      case 'auditoria':
        reporte = 'auditoria';
        filtros = this.limpiarParametros(this.audFiltros);
        nombre = 'reporte_auditoria';
        break;
      default:
        reporte = 'usuarios';
        filtros = this.limpiarParametros(this.usrFiltros);
        nombre = 'reporte_usuarios';
        break;
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
