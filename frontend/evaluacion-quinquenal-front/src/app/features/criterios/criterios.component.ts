import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';
import { Criterio, Periodo } from '../../core/models/evaluation.model';
import { ToastrService } from 'ngx-toastr';

@Component({
  selector: 'app-criterios',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './criterios.component.html',
})
export class CriteriosComponent implements OnInit {
  criterios: Criterio[] = [];
  periodos: Periodo[] = [];
  showModal = false;
  editMode = false;
  form: Criterio = { nombre: '', descripcion: '', periodo: 0, activo: true };

  constructor(private api: ApiService, private toast: ToastrService) {}

  ngOnInit() {
    this.api.getCriterios().subscribe(data => this.criterios = data);
    this.api.getPeriodos().subscribe(data => this.periodos = data);
  }

  abrirModal(criterio?: Criterio) {
    if (criterio) {
      this.form = { ...criterio };
      this.editMode = true;
    } else {
      this.form = { nombre: '', descripcion: '', periodo: 0, activo: true };
      this.editMode = false;
    }
    this.showModal = true;
  }

  guardar() {
    if (this.editMode) {
      this.api.updateCriterio(this.form.id!, this.form).subscribe(() => {
        this.toast.success('Criterio actualizado');
        this.ngOnInit();
        this.showModal = false;
      });
    } else {
      this.api.createCriterio(this.form).subscribe(() => {
        this.toast.success('Criterio creado');
        this.ngOnInit();
        this.showModal = false;
      });
    }
  }

  eliminar(id: number) {
    if (confirm('¿Eliminar este criterio?')) {
      this.api.deleteCriterio(id).subscribe(() => {
        this.toast.success('Criterio eliminado');
        this.ngOnInit();
      });
    }
  }
}
