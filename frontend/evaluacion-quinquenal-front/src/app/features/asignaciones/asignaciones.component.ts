import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';
import { Asignacion, Indicador, Periodo } from '../../core/models/evaluation.model';
import { Departamento } from '../../core/models/organization.model';
import { ToastrService } from 'ngx-toastr';

@Component({
  selector: 'app-asignaciones',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './asignaciones.component.html',
})
export class AsignacionesComponent implements OnInit {
  asignaciones: Asignacion[] = [];
  indicadores: Indicador[] = [];
  departamentos: Departamento[] = [];
  periodos: Periodo[] = [];
  showModal = false;
  editMode = false;
  form: Asignacion = { indicador: 0, departamento: 0, periodo: 0, estado: 'pendiente' };

  constructor(private api: ApiService, private toast: ToastrService) {}

  ngOnInit() {
    this.api.getAsignaciones().subscribe(data => this.asignaciones = data);
    this.api.getIndicadores().subscribe(data => this.indicadores = data);
    this.api.getDepartamentos().subscribe(data => this.departamentos = data);
    this.api.getPeriodos().subscribe(data => this.periodos = data);
  }

  getBadgeClass(estado: string): string {
    const map: Record<string, string> = {
      pendiente: 'badge-warning',
      en_progreso: 'badge-info',
      completado: 'badge-success',
      aprobado: 'badge-primary',
      rechazado: 'badge-danger'
    };
    return map[estado] || 'badge-secondary';
  }

  abrirModal(asignacion?: Asignacion) {
    if (asignacion) {
      this.form = { ...asignacion };
      this.editMode = true;
    } else {
      this.form = { indicador: 0, departamento: 0, periodo: 0, estado: 'pendiente' };
      this.editMode = false;
    }
    this.showModal = true;
  }

  guardar() {
    if (this.editMode) {
      this.api.updateAsignacion(this.form.id!, this.form).subscribe(() => {
        this.toast.success('Asignación actualizada');
        this.ngOnInit();
        this.showModal = false;
      });
    } else {
      this.api.createAsignacion(this.form).subscribe(() => {
        this.toast.success('Asignación creada');
        this.ngOnInit();
        this.showModal = false;
      });
    }
  }

  eliminar(id: number) {
    if (confirm('¿Eliminar esta asignación?')) {
      this.api.deleteAsignacion(id).subscribe(() => {
        this.toast.success('Asignación eliminada');
        this.ngOnInit();
      });
    }
  }
}
