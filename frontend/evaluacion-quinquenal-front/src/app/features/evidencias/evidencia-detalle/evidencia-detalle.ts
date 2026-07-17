import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ToastrService } from 'ngx-toastr';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-evidencia-detalle',
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './evidencia-detalle.html',
  styleUrl: './evidencia-detalle.css',
})
export class EvidenciaDetalle implements OnInit {
  evidencia: any = null;
  loading = false;
  error = '';

  subiendo = false;
  nuevoArchivo: File | null = null;
  comentarioVersion = '';

  comentarioRevision = '';
  estadoSeleccionado = '';
  guardandoRevision = false;

  constructor(
    private route: ActivatedRoute,
    private authService: AuthService,
    private toast: ToastrService
  ) {}

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.cargarDetalle(+id);
    }
  }

  cargarDetalle(id: number): void {
    this.loading = true;
    this.authService.detalleEvidencia(id).subscribe({
      next: (data) => {
        this.evidencia = data;
        this.loading = false;
      },
      error: () => {
        this.error = 'No se pudo cargar el detalle de la evidencia';
        this.loading = false;
      },
    });
  }

  onFileChange(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.nuevoArchivo = input.files?.[0] ?? null;
  }

  subirVersion(): void {
    if (!this.nuevoArchivo) {
      this.toast.error('Debe seleccionar un archivo');
      return;
    }
    this.subiendo = true;
    const payload = new FormData();
    payload.append('archivo', this.nuevoArchivo, this.nuevoArchivo.name);
    payload.append('comentario', this.comentarioVersion || 'Nueva versión');

    this.authService.subirVersionEvidencia(this.evidencia.id_evidencia, payload).subscribe({
      next: () => {
        this.toast.success('Versión subida correctamente');
        this.nuevoArchivo = null;
        this.comentarioVersion = '';
        this.cargarDetalle(this.evidencia.id_evidencia);
        this.subiendo = false;
      },
      error: () => {
        this.toast.error('No se pudo subir la versión');
        this.subiendo = false;
      },
    });
  }

  descargar(versionId: number, nombreArchivo: string): void {
    this.authService.descargarVersion(versionId).subscribe({
      next: (blob) => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = nombreArchivo;
        a.click();
        window.URL.revokeObjectURL(url);
      },
      error: () => this.toast.error('No se pudo descargar el archivo'),
    });
  }

  private getAsignacionId(): number | null {
    if (!this.evidencia) return null;
    return this.evidencia.asignacion_info?.id ?? this.evidencia.asignacion ?? null;
  }

  guardarRevision(): void {
    if (!this.estadoSeleccionado) {
      this.toast.error('Seleccione un estado (aprobar, rechazar o solicitar cambios)');
      return;
    }
    const asignacionId = this.getAsignacionId();
    if (!asignacionId) {
      this.toast.error('No se pudo identificar la asignación asociada');
      return;
    }
    this.guardandoRevision = true;

    const request$ = this.estadoSeleccionado === 'aprobado'
      ? this.authService.aprobarAsignacion(asignacionId, this.comentarioRevision || undefined)
      : this.estadoSeleccionado === 'rechazado'
        ? this.authService.rechazarAsignacion(asignacionId, this.comentarioRevision || undefined)
        : this.estadoSeleccionado === 'observada'
          ? this.authService.solicitarCambios(asignacionId, this.comentarioRevision || undefined)
          : null;

    if (!request$) {
      this.toast.error('Estado no válido');
      this.guardandoRevision = false;
      return;
    }

    request$.subscribe({
      next: () => {
        this.toast.success('Revisión guardada correctamente');
        this.comentarioRevision = '';
        this.estadoSeleccionado = '';
        this.cargarDetalle(this.evidencia.id_evidencia);
        this.guardandoRevision = false;
      },
      error: () => {
        this.toast.error('No se pudo guardar la revisión');
        this.guardandoRevision = false;
      },
    });
  }

  get versionesOrdenadas(): any[] {
    if (!this.evidencia?.versiones) return [];
    return [...this.evidencia.versiones].sort((a, b) => b.version - a.version);
  }
}
