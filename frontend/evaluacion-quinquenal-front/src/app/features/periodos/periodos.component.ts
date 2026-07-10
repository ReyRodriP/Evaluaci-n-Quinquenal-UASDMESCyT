import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';
import { Periodo } from '../../core/models/evaluation.model';
import { ToastrService } from 'ngx-toastr';

@Component({
  selector: 'app-periodos',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './periodos.component.html',
})
export class PeriodosComponent implements OnInit {
  periodos: Periodo[] = [];
  showModal = false;
  editMode = false;
  form: Periodo = { nombre: '', fecha_inicio: '', fecha_fin: '', activo: true };

  constructor(private api: ApiService, private toast: ToastrService) {}

  ngOnInit() { this.cargar(); }

  cargar() {
    this.api.getPeriodos().subscribe(data => this.periodos = data);
  }

  abrirModal(periodo?: Periodo) {
    if (periodo) {
      this.form = { ...periodo };
      this.editMode = true;
    } else {
      this.form = { nombre: '', fecha_inicio: '', fecha_fin: '', activo: true };
      this.editMode = false;
    }
    this.showModal = true;
  }

  guardar() {
    if (this.editMode) {
      this.api.updatePeriodo(this.form.id!, this.form).subscribe(() => {
        this.toast.success('Período actualizado');
        this.cargar();
        this.showModal = false;
      });
    } else {
      this.api.createPeriodo(this.form).subscribe(() => {
        this.toast.success('Período creado');
        this.cargar();
        this.showModal = false;
      });
    }
  }

  eliminar(id: number) {
    if (confirm('¿Eliminar este período?')) {
      this.api.deletePeriodo(id).subscribe(() => {
        this.toast.success('Período eliminado');
        this.cargar();
      });
    }
  }
}
