import { Component, EventEmitter, Input, OnChanges, OnDestroy, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { forkJoin, Observable, Subscription } from 'rxjs';
import { DocumentosService } from '../../../core/services/documentos.service';

@Component({
  selector: 'app-documentos-asignacion',
  imports: [CommonModule, FormsModule],
  templateUrl: './documentos-asignacion.html',
  styles: `
    section { margin-block: 1rem; padding: 1rem; border: 1px solid #d1d5db; border-radius: .5rem; }
    article { border-top: 1px solid #d1d5db; padding-block: 1rem; overflow-wrap: anywhere; }
    label { display: block; margin-block: .5rem; } input:not([type=file]), textarea { display: block; width: 100%; max-width: 45rem; }
    button { margin: .3rem; } .error { color: #b91c1c; } li { margin-block: .5rem; }
  `,
})
export class DocumentosAsignacion implements OnChanges, OnDestroy {
  @Input({ required: true }) asignacionId = 0;
  @Output() actualizado = new EventEmitter<void>();
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
  private consulta?: Subscription;
  private operacion?: Subscription;

  constructor(private documentos: DocumentosService) {}
  ngOnChanges(): void { this.cargar(); }
  ngOnDestroy(): void { this.consulta?.unsubscribe(); this.operacion?.unsubscribe(); }

  cargar(): void {
    this.consulta?.unsubscribe();
    this.contexto = null;
    this.solicitudes = [];
    this.error = '';
    if (!this.asignacionId) return;
    this.cargando = true;
    this.consulta = forkJoin({ contexto: this.documentos.contexto(this.asignacionId), solicitudes: this.documentos.listar(this.asignacionId) }).subscribe({
      next: ({ contexto, solicitudes }) => { this.contexto = contexto; this.solicitudes = solicitudes; this.cargando = false; },
      error: () => { this.error = 'No se pudo consultar la documentación o perdió el acceso.'; this.cargando = false; },
    });
  }

  ejecutar(operacion: Observable<any>): void {
    if (this.ocupada) return;
    this.ocupada = true;
    this.error = '';
    this.operacion = operacion.subscribe({
      next: () => { this.ocupada = false; this.actualizado.emit(); },
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

  editar(solicitud: any): void { this.editando = solicitud.id; this.titulo = solicitud.titulo; this.descripcion = solicitud.descripcion; }
  cancelarEdicion(): void { this.editando = null; this.titulo = ''; this.descripcion = ''; }
  eliminar(id: number): void { this.ejecutar(this.documentos.eliminar(id)); }
  seleccionar(id: number, event: Event): void { this.archivos[id] = (event.target as HTMLInputElement).files?.[0]; }
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
}
