import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
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
  confirmandoSubida = false;
  archivoError = '';

  readonly MAX_ARCHIVO_MB = 50;

  comentarioRevision = '';
  estadoSeleccionado = '';
  guardandoRevision = false;

  editandoInfo = false;
  infoEditada: any = {};
  guardandoInfo = false;

  editandoVersionId: number | null = null;
  versionEditComentario = '';
  versionEditFile: File | null = null;
  versionEditFileError = '';
  guardandoVersionEdit = false;

  previewAbierto = false;
  previewUrl: SafeResourceUrl | null = null;
  previewTipo: 'pdf' | 'imagen' | 'texto' | 'excel' | 'desconocido' = 'desconocido';
  previewNombre = '';
  previewCargando = false;
  previewError = '';
  previewTextoContenido = '';

  constructor(
    private route: ActivatedRoute,
    private authService: AuthService,
    private toast: ToastrService,
    private sanitizer: DomSanitizer
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

  private validarTamañoArchivo(file: File | null): string {
    if (!file) return '';
    const maxBytes = this.MAX_ARCHIVO_MB * 1024 * 1024;
    return file.size > maxBytes
      ? `El archivo supera el tamaño máximo permitido de ${this.MAX_ARCHIVO_MB} MB.`
      : '';
  }

  onFileChange(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0] ?? null;
    this.archivoError = this.validarTamañoArchivo(file);
    if (this.archivoError) {
      this.nuevoArchivo = null;
      input.value = '';
    } else {
      this.nuevoArchivo = file;
    }
  }

  confirmarSubida(): void {
    if (this.archivoError) {
      this.toast.error(this.archivoError);
      return;
    }
    if (!this.nuevoArchivo) {
      this.toast.error('Debe seleccionar un archivo');
      return;
    }
    this.confirmandoSubida = true;
  }

  cancelarConfirmacion(): void {
    this.confirmandoSubida = false;
  }

  subirVersion(): void {
    if (!this.nuevoArchivo) return;
    this.confirmandoSubida = false;
    this.subiendo = true;
    const archivo = this.nuevoArchivo;
    const payload = new FormData();
    payload.append('archivo', archivo, archivo.name);
    payload.append('comentario', this.comentarioVersion || 'Nueva versión');

    this.authService.subirVersionEvidencia(this.evidencia.id_evidencia, payload).subscribe({
      next: () => {
        this.toast.success('Versión subida correctamente');
        this.nuevoArchivo = null;
        this.comentarioVersion = '';
        this.archivoError = '';
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

  editarInfo(): void {
    this.infoEditada = {
      titulo: this.evidencia.titulo || '',
      descripcion: this.evidencia.descripcion || '',
    };
    this.editandoInfo = true;
  }

  cancelarEdicion(): void {
    this.editandoInfo = false;
    this.infoEditada = {};
  }

  guardarInfo(): void {
    if (!this.infoEditada.titulo?.trim()) {
      this.toast.error('El título es obligatorio');
      return;
    }
    this.guardandoInfo = true;
    this.authService.actualizarEvidencia(this.evidencia.id_evidencia, {
      titulo: this.infoEditada.titulo.trim(),
      descripcion: this.infoEditada.descripcion.trim(),
    }).subscribe({
      next: () => {
        this.toast.success('Información actualizada correctamente');
        this.editandoInfo = false;
        this.infoEditada = {};
        this.cargarDetalle(this.evidencia.id_evidencia);
        this.guardandoInfo = false;
      },
      error: () => {
        this.toast.error('No se pudo actualizar la información');
        this.guardandoInfo = false;
      },
    });
  }

  editarVersion(version: any): void {
    this.editandoVersionId = version.id_version;
    this.versionEditComentario = version.comentario || '';
    this.versionEditFile = null;
  }

  onVersionEditFileChange(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0] ?? null;
    this.versionEditFileError = this.validarTamañoArchivo(file);
    if (this.versionEditFileError) {
      this.versionEditFile = null;
      input.value = '';
    } else {
      this.versionEditFile = file;
    }
  }

  cancelarEdicionVersion(): void {
    this.editandoVersionId = null;
    this.versionEditComentario = '';
    this.versionEditFile = null;
  }

  abrirPreview(version: any): void {
    this.previewAbierto = true;
    this.previewCargando = true;
    this.previewError = '';
    this.previewTextoContenido = '';
    this.previewNombre = version.nombre_archivo || 'archivo';

    const ext = (version.nombre_archivo || '').split('.').pop()?.toLowerCase() || '';

    if (['pdf'].includes(ext)) {
      this.previewTipo = 'pdf';
      this.authService.previewVersion(version.id_version).subscribe({
        next: (blob) => {
          const url = window.URL.createObjectURL(blob);
          this.previewUrl = this.sanitizer.bypassSecurityTrustResourceUrl(url);
          this.previewCargando = false;
        },
        error: () => {
          this.previewError = 'No se pudo cargar la vista previa';
          this.previewCargando = false;
        },
      });
    } else if (['png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'svg'].includes(ext)) {
      this.previewTipo = 'imagen';
      this.authService.previewVersion(version.id_version).subscribe({
        next: (blob) => {
          const url = window.URL.createObjectURL(blob);
          this.previewUrl = this.sanitizer.bypassSecurityTrustResourceUrl(url);
          this.previewCargando = false;
        },
        error: () => {
          this.previewError = 'No se pudo cargar la vista previa';
          this.previewCargando = false;
        },
      });
    } else if (['txt', 'csv', 'json', 'xml', 'html', 'htm', 'md', 'log', 'py', 'js', 'ts', 'java', 'c', 'cpp', 'css'].includes(ext)) {
      this.previewTipo = 'texto';
      this.authService.previewVersion(version.id_version).subscribe({
        next: (blob) => {
          const reader = new FileReader();
          reader.onload = () => {
            this.previewTextoContenido = reader.result as string;
            this.previewCargando = false;
          };
          reader.onerror = () => {
            this.previewError = 'No se pudo leer el archivo';
            this.previewCargando = false;
          };
          reader.readAsText(blob);
        },
        error: () => {
          this.previewError = 'No se pudo cargar la vista previa';
          this.previewCargando = false;
        },
      });
    } else if (['xlsx', 'xls'].includes(ext)) {
      this.previewTipo = 'excel';
      this.previewCargando = false;
      this.previewError = '';
    } else {
      this.previewTipo = 'desconocido';
      this.previewCargando = false;
      this.previewError = 'Vista previa no disponible para este tipo de archivo';
    }
  }

  cerrarPreview(): void {
    this.previewAbierto = false;
    this.previewUrl = null;
    this.previewTipo = 'desconocido';
    this.previewNombre = '';
    this.previewError = '';
    this.previewTextoContenido = '';
  }

  guardarEdicionVersion(): void {
    const versionId = this.editandoVersionId;
    if (!versionId) return;

    if (this.versionEditFileError) {
      this.toast.error(this.versionEditFileError);
      return;
    }

    this.guardandoVersionEdit = true;
    const payload = new FormData();
    if (this.versionEditFile) {
      payload.append('archivo', this.versionEditFile, this.versionEditFile.name);
    }
    payload.append('comentario', this.versionEditComentario);

    this.authService.editarVersionEvidencia(this.evidencia.id_evidencia, payload).subscribe({
      next: () => {
        this.toast.success('Versión actualizada correctamente');
        this.cancelarEdicionVersion();
        this.cargarDetalle(this.evidencia.id_evidencia);
        this.guardandoVersionEdit = false;
      },
      error: () => {
        this.toast.error('No se pudo actualizar la versión');
        this.guardandoVersionEdit = false;
      },
    });
  }

  get versionesOrdenadas(): any[] {
    if (!this.evidencia?.versiones) return [];
    return [...this.evidencia.versiones].sort((a, b) => b.version - a.version);
  }
}
