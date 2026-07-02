import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { forkJoin } from 'rxjs';
import { ToastrService } from 'ngx-toastr';
import { AuthService } from '../../core/services/auth.service';

@Component({
  selector: 'app-evidencias',
  imports: [CommonModule, FormsModule],
  templateUrl: './evidencias.html',
  styleUrl: './evidencias.css',
})
export class Evidencias implements OnInit {
  rows: any[] = [];
  loading = false;
  submitting = false;
  showModal = false;
  selectedRow: any = null;
  mode: 'create' | 'edit' = 'create';

  form = {
    titulo: '',
    descripcion: '',
    archivo: null as File | null,
  };

  constructor(
    private authService: AuthService,
    private toast: ToastrService
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

          return {
            ...asignacion,
            evidenciaId: evidencia?.id_evidencia ?? null,
            evidencia,
            estado: evidencia?.estado === 'cancelada' ? 'Cancelada' : evidencia ? 'Subida' : 'Pendiente',
            archivoNombre: ultimaVersion?.archivo?.split('/').pop() || 'Sin archivo',
            archivos: versiones.map((version: any) => ({
              ...version,
              nombreArchivo: version.archivo?.split('/').pop() || 'Sin archivo',
            })),
          };
        });
        this.loading = false;
      },
      error: (err) => {
        console.error('Error cargando evidencias', err);
        this.toast.error('No se pudieron cargar las asignaciones para evidencia');
        this.loading = false;
      },
    });
  }

  openManage(row: any): void {
    this.selectedRow = row;
    this.mode = row.evidenciaId ? 'edit' : 'create';
    this.form = {
      titulo: row.evidencia?.titulo || `Evidencia ${row.indicador_nombre ?? 'indicador'}`,
      descripcion: row.evidencia?.descripcion || '',
      archivo: null,
    };
    this.showModal = true;
  }

  openCancel(row: any): void {
    this.selectedRow = row;
    this.showModal = false;
    this.cancelSubmission();
  }

  closeModal(): void {
    this.showModal = false;
    this.selectedRow = null;
    this.mode = 'create';
    this.form = {
      titulo: '',
      descripcion: '',
      archivo: null,
    };
  }

  onFileChange(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.form.archivo = input.files?.[0] ?? null;
  }

  submitEvidence(): void {
    if (!this.selectedRow) {
      return;
    }

    if (!this.form.archivo && this.mode === 'create') {
      this.toast.error('Debe adjuntar un archivo para subir la evidencia');
      return;
    }

    this.submitting = true;

    const evidenciaPayload = new FormData();
    evidenciaPayload.append('titulo', this.form.titulo || `Evidencia ${this.selectedRow.indicador_nombre ?? 'indicador'}`);
    evidenciaPayload.append('descripcion', this.form.descripcion || 'Evidencia subida desde la gestión de evidencias');
    evidenciaPayload.append('asignacion', String(this.selectedRow.id));

    const handleSuccess = () => {
      this.toast.success(this.selectedRow.evidenciaId ? 'Evidencia actualizada correctamente' : 'Evidencia creada y versión subida');
      this.closeModal();
      this.loadData();
      this.submitting = false;
    };

    const handleError = (err: any) => {
      console.error('Error procesando evidencia', err);
      this.toast.error('No se pudo procesar la evidencia');
      this.submitting = false;
    };

    if (!this.selectedRow.evidenciaId) {
      this.authService.crearEvidencia(evidenciaPayload).subscribe({
        next: (response) => {
          const evidenciaId = response?.id_evidencia ?? response?.id;
          if (!evidenciaId) {
            handleError(new Error('No se recibió el identificador de la evidencia'));
            return;
          }

          if (!this.form.archivo) {
            handleSuccess();
            return;
          }

          const versionPayload = new FormData();
          versionPayload.append('archivo', this.form.archivo, this.form.archivo.name);
          versionPayload.append('comentario', this.form.descripcion || 'Primera versión');

          this.authService.subirVersionEvidencia(evidenciaId, versionPayload).subscribe({
            next: handleSuccess,
            error: handleError,
          });
        },
        error: handleError,
      });
      return;
    }

    if (this.form.archivo) {
      const versionPayload = new FormData();
      versionPayload.append('archivo', this.form.archivo, this.form.archivo.name);
      versionPayload.append('comentario', this.form.descripcion || 'Versión actualizada');

      this.authService.subirVersionEvidencia(this.selectedRow.evidenciaId, versionPayload).subscribe({
        next: handleSuccess,
        error: handleError,
      });
      return;
    }

    handleSuccess();
  }

  editSubmission(): void {
    if (!this.selectedRow?.evidenciaId) {
      return;
    }

    this.submitting = true;

    this.authService.actualizarEvidencia(this.selectedRow.evidenciaId, {
      titulo: this.form.titulo || this.selectedRow.evidencia?.titulo,
      descripcion: this.form.descripcion || this.selectedRow.evidencia?.descripcion,
    }).subscribe({
      next: () => {
        this.toast.success('Envío editado correctamente');
        this.closeModal();
        this.loadData();
        this.submitting = false;
      },
      error: (err) => {
        console.error('Error editando evidencia', err);
        this.toast.error('No se pudo editar el envío');
        this.submitting = false;
      },
    });
  }

  cancelSubmission(): void {
    if (!this.selectedRow?.evidenciaId) {
      return;
    }

    this.submitting = true;

    this.authService.actualizarEvidencia(this.selectedRow.evidenciaId, { estado: 'cancelada' }).subscribe({
      next: () => {
        this.toast.success('Envío cancelado correctamente');
        this.closeModal();
        this.loadData();
        this.submitting = false;
      },
      error: (err) => {
        console.error('Error cancelando evidencia', err);
        this.toast.error('No se pudo cancelar el envío');
        this.submitting = false;
      },
    });
  }
}
