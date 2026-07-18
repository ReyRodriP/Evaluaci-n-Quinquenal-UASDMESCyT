import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { forkJoin } from 'rxjs';
import { ToastrService } from 'ngx-toastr';
import { AuthService } from '../../core/services/auth.service';
import { SearchBar } from '../../shared/components/CRUD/search-bar/search-bar';
import { CrudTable } from '../../shared/components/CRUD/crud-table/crud-table';
import { Modal } from '../../shared/components/CRUD/modal/modal';
import { PermisosService } from '../../core/services/permisos.service';

@Component({
  selector: 'app-evidencias',
  imports: [CommonModule, SearchBar, CrudTable, Modal],
  templateUrl: './evidencias.html',
  styleUrl: './evidencias.css',
})
export class Evidencias implements OnInit {
  rows: any[] = [];
  rowsFiltrados: any[] = [];
  searchTerm = '';
  loading = false;

  historialAbierto = false;
  historialCampos: any[] = [];
  historialData: any = null;

  get puedeSubir(): boolean {
    return this.permisos.tieneAlgunPermiso([
      'evidence.add_evidencia', 'evidence.add_versionevidencia',
      'evidencias.add_evidencia',
    ]);
  }

  get puedeCancelarReactivar(): boolean {
    return this.permisos.tieneAlgunPermiso([
      'evidence.change_evidencia', 'evidencias.change_evidencia',
    ]);
  }

  constructor(
    private authService: AuthService,
    private permisos: PermisosService,
    private toast: ToastrService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.loadData();
  }

  loadData(): void {
    this.loading = true;
    forkJoin({
      asignaciones: this.authService.listarAsignaciones(),
      evidencias: this.authService.listarEvidencias(),
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
        this.toast.error('No se pudieron cargar las asignaciones para evidencia');
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
      return;
    }
    this.rowsFiltrados = this.rows.filter((row) => {
      const campos = [
        row.indicador_nombre,
        row.departamento_nombre,
        row.periodo_nombre,
        row.archivoNombre,
        row.estado,
        row.observacionesTexto,
      ];
      return campos.some((c) => c && c.toLowerCase().includes(term));
    });
  }

  onEdit(row: any): void {
    if (!row.evidenciaId) {
      const payload = new FormData();
      payload.append('titulo', `Evidencia ${row.indicador_nombre || 'indicador'}`);
      payload.append('descripcion', 'Evidencia subida desde la gestión de evidencias');
      payload.append('asignacion', String(row.id));
      this.authService.crearEvidencia(payload).subscribe({
        next: (res) => {
          const id = res?.id_evidencia ?? res?.id;
          if (id) this.router.navigate(['/evidencias', id, 'detalle']);
          else this.toast.error('No se pudo crear la evidencia');
        },
        error: () => this.toast.error('No se pudo crear la evidencia'),
      });
      return;
    }
    this.router.navigate(['/evidencias', row.evidenciaId, 'detalle']);
  }

  openManage(row: any): void {
    if (!row.evidenciaId) {
      const payload = new FormData();
      payload.append('titulo', `Evidencia ${row.indicador_nombre || 'indicador'}`);
      payload.append('descripcion', 'Evidencia subida desde la gestión de evidencias');
      payload.append('asignacion', String(row.id));
      this.authService.crearEvidencia(payload).subscribe({
        next: (res) => {
          const id = res?.id_evidencia ?? res?.id;
          if (id) this.router.navigate(['/evidencias', id, 'detalle']);
          else this.toast.error('No se pudo crear la evidencia');
        },
        error: () => this.toast.error('No se pudo crear la evidencia'),
      });
      return;
    }
    this.router.navigate(['/evidencias', row.evidenciaId, 'detalle']);
  }

  cancelar(row: any): void {
    if (!row.evidenciaId) return;
    this.authService.actualizarEvidencia(row.evidenciaId, { estado: 'cancelada' }).subscribe({
      next: () => {
        this.toast.success('Evidencia cancelada');
        this.loadData();
      },
      error: () => this.toast.error('No se pudo cancelar la evidencia'),
    });
  }

  reactivar(row: any): void {
    if (!row.evidenciaId) return;
    this.authService.actualizarEvidencia(row.evidenciaId, { estado: 'activa' }).subscribe({
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
    this.authService.descargarVersion(v.id_version).subscribe({
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
    this.authService.obtenerHistorial(row.evidenciaId).subscribe({
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
