import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';
import { Facultad, Departamento } from '../../core/models/organization.model';
import { ToastrService } from 'ngx-toastr';

@Component({
  selector: 'app-facultades',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './facultades.html',
  styleUrl: './facultades.css',
})
export class Facultades implements OnInit {
  facultades: Facultad[] = [];
  departamentos: Departamento[] = [];
  selectedFacultad: number | null = null;
  showFacultadModal = false;
  showDeptModal = false;
  editFacultadMode = false;
  editDeptMode = false;
  facForm: Facultad = { nombre: '', descripcion: '', activo: true };
  deptForm: Departamento = { nombre: '', descripcion: '', facultad: 0, activo: true };

  constructor(private api: ApiService, private toast: ToastrService) {}

  ngOnInit() {
    this.api.getFacultades().subscribe(data => this.facultades = data);
    this.api.getDepartamentos().subscribe(data => this.departamentos = data);
  }

  getDeptosByFacultad(facultadId: number): Departamento[] {
    return this.departamentos.filter(d => d.facultad === facultadId);
  }

  /* Facultad modal */
  abrirFacultadModal(facultad?: Facultad) {
    if (facultad) {
      this.facForm = { ...facultad };
      this.editFacultadMode = true;
    } else {
      this.facForm = { nombre: '', descripcion: '', activo: true };
      this.editFacultadMode = false;
    }
    this.showFacultadModal = true;
  }

  guardarFacultad() {
    if (this.editFacultadMode) {
      this.api.updateFacultad(this.facForm.id!, this.facForm).subscribe(() => {
        this.toast.success('Facultad actualizada');
        this.ngOnInit();
        this.showFacultadModal = false;
      });
    } else {
      this.api.createFacultad(this.facForm).subscribe(() => {
        this.toast.success('Facultad creada');
        this.ngOnInit();
        this.showFacultadModal = false;
      });
    }
  }

  eliminarFacultad(id: number) {
    if (confirm('¿Eliminar esta facultad?')) {
      this.api.deleteFacultad(id).subscribe(() => {
        this.toast.success('Facultad eliminada');
        this.ngOnInit();
      });
    }
  }

  /* Departamento modal */
  abrirDeptModal(departamento?: Departamento, facultadId?: number) {
    if (departamento) {
      this.deptForm = { ...departamento };
      this.editDeptMode = true;
    } else {
      this.deptForm = { nombre: '', descripcion: '', facultad: facultadId || 0, activo: true };
      this.editDeptMode = false;
    }
    this.showDeptModal = true;
  }

  guardarDepartamento() {
    if (this.editDeptMode) {
      this.api.updateDepartamento(this.deptForm.id!, this.deptForm).subscribe(() => {
        this.toast.success('Departamento actualizado');
        this.ngOnInit();
        this.showDeptModal = false;
      });
    } else {
      this.api.createDepartamento(this.deptForm).subscribe(() => {
        this.toast.success('Departamento creado');
        this.ngOnInit();
        this.showDeptModal = false;
      });
    }
  }

  eliminarDepartamento(id: number) {
    if (confirm('¿Eliminar este departamento?')) {
      this.api.deleteDepartamento(id).subscribe(() => {
        this.toast.success('Departamento eliminado');
        this.ngOnInit();
      });
    }
  }
}
