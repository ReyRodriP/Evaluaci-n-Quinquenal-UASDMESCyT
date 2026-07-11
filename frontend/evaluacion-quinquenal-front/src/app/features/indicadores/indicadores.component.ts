import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';
import { Indicador, Criterio } from '../../core/models/evaluation.model';
import { ToastrService } from 'ngx-toastr';

@Component({
  selector: 'app-indicadores',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './indicadores.component.html',
})
export class IndicadoresComponent implements OnInit {
  indicadores: Indicador[] = [];
  criterios: Criterio[] = [];
  showModal = false;
  editMode = false;
  form: Indicador = { nombre: '', descripcion: '', criterio: 0, obligatorio: false, activo: true };

  constructor(private api: ApiService, private toast: ToastrService) {}

  ngOnInit() {
    this.api.getIndicadores().subscribe(data => this.indicadores = data);
    this.api.getCriterios().subscribe(data => this.criterios = data);
  }

  abrirModal(indicador?: Indicador) {
    if (indicador) {
      this.form = { ...indicador };
      this.editMode = true;
    } else {
      this.form = { nombre: '', descripcion: '', criterio: 0, obligatorio: false, activo: true };
      this.editMode = false;
    }
    this.showModal = true;
  }

  guardar() {
    if (this.editMode) {
      this.api.updateIndicador(this.form.id!, this.form).subscribe(() => {
        this.toast.success('Indicador actualizado');
        this.ngOnInit();
        this.showModal = false;
      });
    } else {
      this.api.createIndicador(this.form).subscribe(() => {
        this.toast.success('Indicador creado');
        this.ngOnInit();
        this.showModal = false;
      });
    }
  }

  eliminar(id: number) {
    if (confirm('¿Eliminar este indicador?')) {
      this.api.deleteIndicador(id).subscribe(() => {
        this.toast.success('Indicador eliminado');
        this.ngOnInit();
      });
    }
  }
}
