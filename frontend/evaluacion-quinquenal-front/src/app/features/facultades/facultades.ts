import { Component, OnInit } from '@angular/core';
<<<<<<< HEAD
import { CrudTable } from '../../shared/components/CRUD/crud-table/crud-table';
import { SearchBar } from '../../shared/components/CRUD/search-bar/search-bar';
import { Pagination } from '../../shared/components/CRUD/pagination/pagination';
import { Modal } from '../../shared/components/CRUD/modal/modal';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { AuthService } from '../auth/services/auth-service';
=======
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';
import { Facultad, Departamento } from '../../core/models/organization.model';
>>>>>>> Ramon_Paulino_Gil_100345706
import { ToastrService } from 'ngx-toastr';

@Component({
  selector: 'app-facultades',
<<<<<<< HEAD
  imports: [CrudTable, SearchBar, Pagination, Modal],
=======
  standalone: true,
  imports: [CommonModule, FormsModule],
>>>>>>> Ramon_Paulino_Gil_100345706
  templateUrl: './facultades.html',
  styleUrls: ['./facultades.css'],
})
export class Facultades implements OnInit {
<<<<<<< HEAD
  columnas: string[] = ['Nombre', 'Descripción', 'Estado', 'Fecha de Creación'];

  datos: any[] = [];
  datosFiltrados: any[] = [];
  searchTerm = '';
  selectedState = 'Todas';

  showModal: boolean = false;
  selectedItem: any = null;

  openNew() {
    this.selectedItem = null;
    this.showModal = true;
  }

  openEdit(item: any) {
    this.selectedItem = { ...item };
    this.showModal = true;
  }

  facultadFields = [
    { label: 'Nombre', name: 'nombre', type: 'text', placeholder: 'Ej. Facultad de Ciencias', defaultValue: '' },
    { label: 'Descripción', name: 'descripcion', type: 'textarea', placeholder: 'Descripción de la facultad', defaultValue: '' },
    { label: 'Estado', name: 'estado', type: 'select', options: ['Activa', 'Inactiva'], defaultValue: 'Activa' }
  ];

  ngOnInit() {
    this.loadFacultades();
  }

  loadFacultades() {
    this.authService.listarFacultades().subscribe({
      next: (data) => {
        this.datos = data.map((item: any) => ({
          ...item,
          estado: item.activo ? 'Activa' : 'Inactiva',
          fechaCreacion: item.fecha_creacion ? item.fecha_creacion.split('T')[0] : '',
        }));
        this.applySearch();
      },
      error: (err) => {
        console.error('Error cargando facultades', err);
        this.toast.error('No se pudieron cargar las facultades');
      }
    });
  }

  onSearch(term: string) {
    this.searchTerm = term;
    this.applySearch();
  }

  onStateChange(state: string) {
    this.selectedState = state;
    this.applySearch();
  }

  private applySearch() {
    const normalizedTerm = this.searchTerm.toLowerCase().trim();
    this.datosFiltrados = this.datos.filter((item: any) => {
      const nombre = `${item.nombre ?? ''}`.toLowerCase();
      const matchesSearch = !normalizedTerm || nombre.includes(normalizedTerm);
      const matchesState = this.selectedState === 'Todas'
        || (this.selectedState === 'Activas' && item.activo)
        || (this.selectedState === 'Inactivas' && !item.activo);
      return matchesSearch && matchesState;
    });
  }

  onModalClose() {
    this.showModal = false;
    this.selectedItem = null;
  }

  onModalSave(saved: any) {
    const payload = {
      nombre: saved.nombre,
      descripcion: saved.descripcion,
      activo: saved.estado === 'Activa',
    };

    if (this.selectedItem && this.selectedItem.id) {
      this.authService.actualizarFacultad(this.selectedItem.id, payload).subscribe({
        next: () => {
          this.toast.success('Facultad actualizada correctamente');
          this.loadFacultades();
          this.onModalClose();
        },
        error: (err) => {
          console.error('Error actualizando facultad', err);
          this.toast.error('Error al actualizar la facultad');
        }
      });
    } else {
      this.authService.crearFacultades(payload).subscribe({
        next: () => {
          this.toast.success('Facultad creada exitosamente');
          this.loadFacultades();
          this.onModalClose();
        },
        error: (err) => {
          console.error('Error creando facultad', err);
          this.toast.error('Error al crear la facultad');
        }
=======
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
>>>>>>> Ramon_Paulino_Gil_100345706
      });
    }
  }

<<<<<<< HEAD
  //Manejo de ingreso de facultades

  facultadForm: FormGroup;

  constructor(
    private fb: FormBuilder,
    private authService: AuthService,
    private toast: ToastrService
  ) {
    this.facultadForm = this.fb.group({
      nombre: ['', Validators.required],
      descripcion: ['', [Validators.required, Validators.minLength(6)]],
      estado: ['', Validators.required]
    });
  }

  onSubmit() {
    if(this.facultadForm.valid) {
      this.authService.crearFacultades(this.facultadForm.value).subscribe({
        next:(data)=> {
          this.toast.success('Facultad creada exitosamente');
          this.loadFacultades();
        },
        error:(err)=> {
          console.log(err);
          this.toast.error('Error al crear la facultad');
        }
      });
    }
  }

  onRemove(item: any) {
    if (!item.id) {
      return;
    }

    this.authService.eliminarFacultad(item.id).subscribe({
      next: () => {
        this.toast.success('Facultad eliminada');
        this.loadFacultades();
      },
      error: (err) => {
        console.error('Error eliminando facultad', err);
        this.toast.error('No se pudo eliminar la facultad');
      }
    });
  }

  onToggleEstado(item: any) {
    if (!item.id) {
      return;
    }

    const nuevoEstado = !item.activo;

    this.authService.actualizarFacultad(item.id, { activo: nuevoEstado }).subscribe({
      next: () => {
        this.toast.success(`Facultad ${nuevoEstado ? 'activada' : 'desactivada'} correctamente`);
        this.loadFacultades();
      },
      error: (err) => {
        console.error('Error cambiando estado de facultad', err);
        this.toast.error('No se pudo cambiar el estado de la facultad');
      }
    });
=======
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
>>>>>>> Ramon_Paulino_Gil_100345706
  }
}
