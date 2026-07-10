import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';
import { Evidencia } from '../../core/models/evidencia.model';
import { Asignacion } from '../../core/models/evaluation.model';
import { ToastrService } from 'ngx-toastr';

@Component({
  selector: 'app-evidencias',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './evidencias.component.html',
})
export class EvidenciasComponent implements OnInit {
  evidencias: Evidencia[] = [];
  asignaciones: Asignacion[] = [];
  selectedFile: File | null = null;
  showModal = false;
  form: Evidencia = { asignacion: 0, nombre: '', descripcion: '', observaciones: '', archivo: '' };
  filtroAsignacion = '';

  constructor(private api: ApiService, private toast: ToastrService) {}

  ngOnInit() {
    this.cargarEvidencias();
    this.api.getAsignaciones().subscribe(data => this.asignaciones = data);
  }

  cargarEvidencias() {
    const id = this.filtroAsignacion ? Number(this.filtroAsignacion) : undefined;
    this.api.getEvidencias(id).subscribe(data => this.evidencias = data);
  }

  onFileSelected(event: any) {
    this.selectedFile = event.target.files[0] || null;
  }

  abrirModal() {
    this.form = { asignacion: 0, nombre: '', descripcion: '', observaciones: '', archivo: '' };
    this.selectedFile = null;
    this.showModal = true;
  }

  guardar() {
    if (!this.selectedFile) {
      this.toast.error('Debe seleccionar un archivo');
      return;
    }
    const fd = new FormData();
    fd.append('asignacion', String(this.form.asignacion));
    fd.append('nombre', this.form.nombre);
    fd.append('descripcion', this.form.descripcion);
    fd.append('observaciones', this.form.observaciones);
    fd.append('archivo', this.selectedFile);
    this.api.createEvidencia(fd).subscribe({
      next: () => {
        this.toast.success('Evidencia subida');
        this.cargarEvidencias();
        this.showModal = false;
      },
      error: (err) => {
        this.toast.error('Error al subir evidencia');
        console.error(err);
      }
    });
  }

  descargar(id: number, nombre: string) {
    this.api.descargarEvidencia(id).subscribe(blob => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = nombre;
      a.click();
      window.URL.revokeObjectURL(url);
    });
  }

  eliminar(id: number) {
    if (confirm('¿Eliminar esta evidencia?')) {
      this.api.deleteEvidencia(id).subscribe(() => {
        this.toast.success('Evidencia eliminada');
        this.cargarEvidencias();
      });
    }
  }

  formatSize(bytes: number): string {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1048576).toFixed(1) + ' MB';
  }
}
