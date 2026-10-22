import { Component, EventEmitter, Input, OnChanges, OnDestroy, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
import { forkJoin, Observable, Subscription } from 'rxjs';
import { DocumentosService } from '../../../core/services/documentos.service';

@Component({
  selector: 'app-documentos-asignacion',
  imports: [CommonModule, FormsModule],
  templateUrl: './documentos-asignacion.html',
  styleUrls: ['../../evidencias/evidencia-detalle/evidencia-detalle.css', './documentos-asignacion.css'],
})
export class DocumentosAsignacion implements OnChanges, OnDestroy {
  @Input({ required: true }) asignacionId = 0;
  @Input() solicitudId = 0;
  @Output() actualizado = new EventEmitter<number>();
  contexto: any = null;
  solicitudes: any[] = [];
  cargando = false;
  ocupada = false;
  error = '';
  titulo = '';
  descripcion = '';
  editando: number | null = null;
  archivos: Record<number, File | undefined> = {};
  comentarios: Record<number, string> = {};
  seleccionadaId = 0;
  mostrarFormulario = false;
  readonly MAX_ARCHIVO_MB = 50;
  archivoErrores: Record<number, string> = {};
  previewAbierto = false;
  previewNombre = '';
  previewCargando = false;
  previewError = '';
  previewTipo = '';
  previewUrl: SafeResourceUrl | null = null;
  previewImagen = '';
  previewTexto = '';
  private previewBlobUrl = '';
  private previewConsulta?: Subscription;
  private consulta?: Subscription;
  private operacion?: Subscription;

  constructor(private documentos: DocumentosService, private sanitizer: DomSanitizer) {}
  ngOnChanges(): void { this.cargar(); }
  ngOnDestroy(): void { this.consulta?.unsubscribe(); this.operacion?.unsubscribe(); this.cerrarPreview(); }

  get solicitudActiva(): any { return this.solicitudes.find(s => s.id === this.seleccionadaId) ?? null; }

  seleccionarDocumento(id: number): void { this.seleccionadaId = id; this.cerrarPreview(); }

  cargar(): void {
    this.consulta?.unsubscribe();
    this.contexto = null;
    this.solicitudes = [];
    this.error = '';
    if (!this.asignacionId) return;
    this.cargando = true;
    this.consulta = forkJoin({ contexto: this.documentos.contexto(this.asignacionId), solicitudes: this.documentos.listar(this.asignacionId) }).subscribe({
      next: ({ contexto, solicitudes }) => {
        this.contexto = contexto; this.solicitudes = solicitudes; this.cargando = false;
        const preferida = this.solicitudId || this.seleccionadaId;
        this.seleccionadaId = solicitudes.find(s => s.id === preferida)?.id ?? solicitudes[0]?.id ?? 0;
      },
      error: () => { this.error = 'No se pudo consultar la documentación o perdió el acceso.'; this.cargando = false; },
    });
  }

  ejecutar(operacion: Observable<any>): void {
    if (this.ocupada) return;
    this.ocupada = true;
    this.error = '';
    this.operacion = operacion.subscribe({
      next: () => { this.ocupada = false; this.actualizado.emit(this.seleccionadaId); },
      error: (err) => {
        this.ocupada = false;
        this.error = typeof err.error === 'string' ? err.error : JSON.stringify(err.error ?? 'No se pudo realizar la operación.');
        if (err.status === 403 || err.status === 404) { this.contexto = null; this.solicitudes = []; }
      },
    });
  }

  guardar(): void {
    if (!this.titulo.trim() || !this.descripcion.trim()) return;
    this.ejecutar(this.editando
      ? this.documentos.editar(this.editando, this.titulo, this.descripcion)
      : this.documentos.crear(this.asignacionId, this.titulo, this.descripcion));
  }

  editar(solicitud: any): void { this.mostrarFormulario = true; this.editando = solicitud.id; this.titulo = solicitud.titulo; this.descripcion = solicitud.descripcion; }
  cancelarEdicion(): void { this.editando = null; this.titulo = ''; this.descripcion = ''; }
  eliminar(id: number): void { this.ejecutar(this.documentos.eliminar(id)); }
  seleccionar(id: number, event: Event): void {
    const archivo = (event.target as HTMLInputElement).files?.[0];
    this.archivoErrores[id] = archivo && archivo.size > this.MAX_ARCHIVO_MB * 1024 * 1024 ? `El archivo supera el tamaño máximo de ${this.MAX_ARCHIVO_MB} MB.` : '';
    this.archivos[id] = this.archivoErrores[id] ? undefined : archivo;
  }
  subir(id: number): void {
    const archivo = this.archivos[id];
    if (archivo) this.ejecutar(this.documentos.subir(id, archivo, this.comentarios[id] || ''));
  }
  enviar(id: number): void { this.ejecutar(this.documentos.accion(id, 'enviar')); }
  revisar(solicitud: any, accion: string): void {
    this.ejecutar(this.documentos.accion(solicitud.id, accion, solicitud.versiones[0]?.id, this.comentarios[solicitud.id] || ''));
  }
  aprobarGlobal(): void { this.ejecutar(this.documentos.aprobarGlobal(this.asignacionId)); }
  descargar(solicitud: any, version: any): void {
    this.operacion = this.documentos.descargar(solicitud.id, version.id).subscribe({
      next: (blob) => {
        const url = URL.createObjectURL(blob);
        const enlace = document.createElement('a');
        enlace.href = url; enlace.download = version.nombre_archivo; enlace.click();
        URL.revokeObjectURL(url);
      },
      error: () => { this.error = 'No se pudo descargar el documento.'; },
    });
  }

  abrirPreview(solicitud: any, version: any): void {
    this.cerrarPreview();
    this.previewAbierto = true; this.previewCargando = true; this.previewNombre = version.nombre_archivo;
    this.previewConsulta = this.documentos.descargar(solicitud.id, version.id).subscribe({
      next: async (blob) => {
        const extension = (version.nombre_archivo || '').split('.').pop()?.toLowerCase();
        this.previewTipo = extension === 'pdf' ? 'pdf' : ['png', 'jpg', 'jpeg', 'gif', 'webp'].includes(extension) ? 'imagen' : extension === 'txt' ? 'texto' : 'otro';
        if (this.previewTipo === 'texto') {
          const texto = await blob.text();
          if (!this.previewAbierto || this.previewNombre !== version.nombre_archivo) return;
          this.previewTexto = texto;
        } else if (this.previewTipo !== 'otro') {
          this.previewBlobUrl = URL.createObjectURL(blob);
          this.previewImagen = this.previewBlobUrl;
          this.previewUrl = this.sanitizer.bypassSecurityTrustResourceUrl(this.previewBlobUrl);
        }
        this.previewCargando = false;
      },
      error: () => { this.previewCargando = false; this.previewError = 'No se pudo cargar la vista previa.'; },
    });
  }

  cerrarPreview(): void {
    this.previewConsulta?.unsubscribe();
    if (this.previewBlobUrl) URL.revokeObjectURL(this.previewBlobUrl);
    this.previewBlobUrl = ''; this.previewUrl = null; this.previewImagen = ''; this.previewTexto = '';
    this.previewAbierto = false; this.previewError = ''; this.previewTipo = '';
  }
}
