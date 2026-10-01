import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { catchError, forkJoin, of, throwError } from 'rxjs';
import { ToastrService } from 'ngx-toastr';
import { EvidenciasService } from '../../core/services/evidencias.service';
import { EvaluacionService } from '../../core/services/evaluacion.service';
import { SearchBar } from '../../shared/components/CRUD/search-bar/search-bar';
import { CrudTable } from '../../shared/components/CRUD/crud-table/crud-table';
import { Modal } from '../../shared/components/CRUD/modal/modal';
import { Pagination } from '../../shared/components/CRUD/pagination/pagination';
import { PermisosService } from '../../core/services/permisos.service';

@Component({
  selector: 'app-evidencias',
  imports: [CommonModule, FormsModule, SearchBar, CrudTable, Modal, Pagination],
  templateUrl: './evidencias.html',
  styleUrl: './evidencias.css',
})
export class Evidencias implements OnInit {
  rows: any[] = [];
  rowsFiltrados: any[] = [];
  rowsPaginados: any[] = [];
  searchTerm = '';
  currentPage = 1;
  pageSize = 10;
  loading = false;
  descargandoMasivo = false;
  periodoActivo: any = null;
  periodos: any[] = [];
  periodoSeleccionadoId = '';
  readonly limiteDescargaMasiva = 100;
  seleccionadas = new Set<number>();

  historialAbierto = false;
  historialCampos: any[] = [];
  historialData: any = null;

  get puedeSubir(): boolean {
    return this.periodoSeleccionadoEsActivo && this.permisos.tieneAlgunPermiso([
      'evidence.add_evidencia', 'evidence.add_versionevidencia',
      'evidencias.add_evidencia',
    ]);
  }

  get puedeCancelarReactivar(): boolean {
    return this.periodoSeleccionadoEsActivo && this.permisos.tieneAlgunPermiso([
      'evidence.change_evidencia', 'evidencias.change_evidencia',
    ]);
  }

  get puedeDescargarMasivo(): boolean {
    return this.permisos.tieneAlgunPermiso(['evidence.view_evidencia', 'evidencias.view_evidencia']);
  }

  get seleccionablesPagina(): any[] {
    return this.rowsPaginados.filter((row) => row.evidenciaId);
  }

  get paginaCompletaSeleccionada(): boolean {
    return this.seleccionablesPagina.length > 0
      && this.seleccionablesPagina.every((row) => this.seleccionadas.has(row.evidenciaId));
  }

  constructor(
    private evidenciasService: EvidenciasService,
    private evaluacionService: EvaluacionService,
    private permisos: PermisosService,
    private toast: ToastrService,
    private route: ActivatedRoute,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.loadPeriodos();
  }

  get periodoSeleccionadoEsActivo(): boolean {
    return this.periodos.some((periodo) =>
      String(periodo.id) === this.periodoSeleccionadoId && periodo.activo
    );
  }

  private loadPeriodos(): void {
    this.loading = true;
    forkJoin({
      periodos: this.evaluacionService.listarPeriodos().pipe(catchError(() => of([]))),
      periodo: this.evaluacionService.periodoActivo().pipe(
        catchError((error) => error.status === 404 ? of(null) : throwError(() => error))
      ),
    }).subscribe({
      next: ({ periodos, periodo }) => {
        this.periodos = periodos;
        this.periodoActivo = periodo;
        const periodoUrl = this.route.snapshot.queryParamMap.get('periodo');
        const periodoSolicitado = periodos.find((item: any) => String(item.id) === periodoUrl);
        const seleccionSolicitadaValida = periodoUrl && (periodoSolicitado || !periodos.length);
        this.periodoSeleccionadoId = String(seleccionSolicitadaValida ? periodoUrl : periodo?.id ?? '');
        if (periodo && !this.periodos.some((item: any) => Number(item.id) === Number(periodo.id))) {
          this.periodos = [...this.periodos, periodo];
        }
        if (this.periodoSeleccionadoId !== periodoUrl) this.actualizarPeriodoUrl();
        this.loadData();
      },
      error: () => {
        this.toast.error('No se pudieron cargar los períodos');
        this.loading = false;
      },
    });
  }

  onPeriodoChange(periodoId: string): void {
    this.periodoSeleccionadoId = periodoId;
    this.seleccionadas = new Set<number>();
    this.actualizarPeriodoUrl();
    this.loadData();
  }

  private actualizarPeriodoUrl(): void {
    void this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { periodo: this.periodoSeleccionadoId || null },
      queryParamsHandling: 'merge',
      replaceUrl: true,
    });
  }

  loadData(): void {
    if (!this.periodoSeleccionadoId) {
      this.rows = [];
      this.applySearch();
      this.loading = false;
      return;
    }
    this.loading = true;
    forkJoin({
      asignaciones: this.evaluacionService.listarAsignaciones(this.periodoSeleccionadoId),
      evidencias: this.evidenciasService.listarEvidencias(this.periodoSeleccionadoId),
    }).subscribe({
      next: ({ asignaciones, evidencias }) => {
        this.rows = asignaciones.map((asignacion: any) => {
          const evidencia = (evidencias || []).find((item: any) => {
            const evidenciaAsignacion = typeof item.asignacion === 'number' ? item.asignacion : item.asignacion?.id ?? item.asignacion;
            return evidenciaAsignacion === asignacion.id;
          });

          const versiones = evidencia?.versiones || [];
          const ultimaVersion = versiones.length ? versiones[versiones.length - 1] : null;
          const obs = evidencia?.ultima_observacion;

          return {
            ...asignacion,
            unidad_responsable: asignacion.unidad_responsable_nombre || asignacion.departamento_nombre || asignacion.unidad_responsable,
            evidenciaId: evidencia?.id_evidencia ?? null,
            evidencia,
            estado: evidencia
              ? (evidencia.estado === 'cancelada' ? 'Cancelada' : (evidencia.asignacion_estado_display || 'Subida'))
              : 'Pendiente',
            estadoWorkflow: evidencia?.asignacion_estado,
            archivoNombre: ultimaVersion?.nombre_archivo || ultimaVersion?.archivo?.split('/').pop() || 'Sin archivo',
            ultimaVersion,
            observacionesTexto: obs ? obs.comentario : '',
            ultimaObsUsuario: obs ? obs.usuario_nombre : '',
          };
        });
        this.applySearch();
        this.loading = false;
      },
      error: () => {
        this.toast.error('No se pudieron cargar las evidencias del período');
        this.loading = false;
      },
    });
  }

  onSearch(term: string): void {
    this.searchTerm = term;
    this.applySearch();
  }

  applySearch(): void {
    const term = this.searchTerm.toLowerCase().trim();
    if (!term) {
      this.rowsFiltrados = [...this.rows];
    } else {
      this.rowsFiltrados = this.rows.filter((row) => {
        const campos = [
          row.indicador_nombre,
          row.unidad_responsable_nombre || row.departamento_nombre,
          row.periodo_nombre,
          row.archivoNombre,
          row.estado,
          row.observacionesTexto,
        ];
        return campos.some((c) => c && c.toLowerCase().includes(term));
      });
    }
    this.currentPage = 1;
    this.actualizarPagina();
  }

  onPageSizeChange(size: number): void {
    this.pageSize = size;
    this.currentPage = 1;
    this.actualizarPagina();
  }

  onPageChange(page: number): void {
    this.currentPage = page;
    this.actualizarPagina();
  }

  private actualizarPagina(): void {
    const start = (this.currentPage - 1) * this.pageSize;
    this.rowsPaginados = this.rowsFiltrados.slice(start, start + this.pageSize);
  }

  filaSeleccionada(row: any): boolean {
    return Boolean(row.evidenciaId && this.seleccionadas.has(row.evidenciaId));
  }

  cambiarSeleccionFila(row: any, event: Event): void {
    if (!row.evidenciaId) return;
    const checked = (event.target as HTMLInputElement).checked;
    const seleccion = new Set(this.seleccionadas);
    if (checked) seleccion.add(row.evidenciaId);
    else seleccion.delete(row.evidenciaId);
    this.seleccionadas = seleccion;
  }

  alternarSeleccionPagina(): void {
    const seleccion = new Set(this.seleccionadas);
    if (this.paginaCompletaSeleccionada) {
      this.seleccionablesPagina.forEach((row) => seleccion.delete(row.evidenciaId));
    } else {
      this.seleccionablesPagina.forEach((row) => seleccion.add(row.evidenciaId));
    }
    this.seleccionadas = seleccion;
  }

  descargarSeleccionadas(): void {
    const evidenciaIds = [...this.seleccionadas];
    if (!evidenciaIds.length) {
      this.toast.error('Seleccione evidencias para descargar');
      return;
    }
    if (evidenciaIds.length > this.limiteDescargaMasiva) {
      this.toast.error(`Seleccione como máximo ${this.limiteDescargaMasiva} evidencias por ZIP`);
      return;
    }

    this.descargandoMasivo = true;
    this.evidenciasService.descargarMasiva(evidenciaIds).subscribe({
      next: (blob) => {
        const url = window.URL.createObjectURL(blob);
        const enlace = document.createElement('a');
        enlace.href = url;
        enlace.download = 'evidencias_seleccionadas.zip';
        enlace.click();
        window.URL.revokeObjectURL(url);
        this.toast.success(`ZIP preparado con ${evidenciaIds.length} evidencias`);
        this.seleccionadas = new Set<number>();
        this.descargandoMasivo = false;
      },
      error: () => {
        this.toast.error('No se pudo preparar la descarga. Revise el tamaño y sus permisos.');
        this.descargandoMasivo = false;
      },
    });
  }

  onEdit(row: any): void {
    if (!row.evidenciaId) {
      const payload = new FormData();
      payload.append('titulo', `Evidencia ${row.indicador_nombre || 'indicador'}`);
      payload.append('descripcion', 'Evidencia subida desde la gestión de evidencias');
      payload.append('asignacion', String(row.id));
      this.evidenciasService.crearEvidencia(payload).subscribe({
        next: (res) => {
          const id = res?.id_evidencia ?? res?.id;
          if (id) this.irADetalle(id);
          else this.toast.error('No se pudo crear la evidencia');
        },
        error: () => this.toast.error('No se pudo crear la evidencia'),
      });
      return;
    }
    this.irADetalle(row.evidenciaId);
  }

  private irADetalle(evidenciaId: number): void {
    void this.router.navigate(['/evidencias', evidenciaId, 'detalle'], {
      queryParams: { periodo: this.periodoSeleccionadoId },
    });
  }

  openManage(row: any): void {
    if (!row.evidenciaId) {
      const payload = new FormData();
      payload.append('titulo', `Evidencia ${row.indicador_nombre || 'indicador'}`);
      payload.append('descripcion', 'Evidencia subida desde la gestión de evidencias');
      payload.append('asignacion', String(row.id));
      this.evidenciasService.crearEvidencia(payload).subscribe({
        next: (res) => {
          const id = res?.id_evidencia ?? res?.id;
          if (id) this.irADetalle(id);
          else this.toast.error('No se pudo crear la evidencia');
        },
        error: () => this.toast.error('No se pudo crear la evidencia'),
      });
      return;
    }
    this.irADetalle(row.evidenciaId);
  }

  cancelar(row: any): void {
    if (!row.evidenciaId) return;
    this.evidenciasService.actualizarEvidencia(row.evidenciaId, { estado: 'cancelada' }, this.periodoSeleccionadoId).subscribe({
      next: () => {
        this.toast.success('Evidencia cancelada');
        this.loadData();
      },
      error: () => this.toast.error('No se pudo cancelar la evidencia'),
    });
  }

  reactivar(row: any): void {
    if (!row.evidenciaId) return;
    this.evidenciasService.actualizarEvidencia(row.evidenciaId, { estado: 'activa' }, this.periodoSeleccionadoId).subscribe({
      next: () => {
        this.toast.success('Evidencia reactivada');
        this.loadData();
      },
      error: () => this.toast.error('No se pudo reactivar la evidencia'),
    });
  }

  descargarUltimoArchivo(row: any): void {
    const v = row.ultimaVersion;
    if (!v?.id_version) {
      this.toast.error('No hay archivo disponible para descargar');
      return;
    }
    this.evidenciasService.descargarVersion(v.id_version, this.periodoSeleccionadoId).subscribe({
      next: (blob) => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = v.nombre_archivo || 'archivo';
        a.click();
        window.URL.revokeObjectURL(url);
      },
      error: () => this.toast.error('No se pudo descargar el archivo'),
    });
  }

  verHistorial(row: any): void {
    if (!row.evidenciaId) return;
    this.evidenciasService.obtenerHistorial(row.evidenciaId, this.periodoSeleccionadoId).subscribe({
      next: (versiones: any[]) => {
        const items = versiones.map((v: any) =>
          `  v${v.version}  ${v.fecha_subida?.slice(0, 10) || ''}  —  ${v.comentario || 'Sin comentario'}`
        ).join('\n');
        this.historialData = { historial: items || 'No hay versiones registradas.' };
        this.historialCampos = [
          { name: 'historial', label: 'Historial de versiones', type: 'textarea', defaultValue: '' },
        ];
        this.historialAbierto = true;
      },
      error: () => this.toast.error('No se pudo cargar el historial'),
    });
  }

  cerrarHistorial(): void {
    this.historialAbierto = false;
    this.historialData = null;
  }
}
