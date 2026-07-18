import { Component, OnInit } from '@angular/core';
import { CrudTable } from '../../shared/components/CRUD/crud-table/crud-table';
import { SearchBar } from '../../shared/components/CRUD/search-bar/search-bar';
import { Pagination } from '../../shared/components/CRUD/pagination/pagination';
import { Modal } from '../../shared/components/CRUD/modal/modal';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { AuthService } from '../auth/services/auth-service';
import { ToastrService } from 'ngx-toastr';
import { PermisosService } from '../../core/services/permisos.service';

@Component({
  selector: 'app-facultades',
  imports: [CrudTable, SearchBar, Pagination, Modal],
  templateUrl: './facultades.html',
  styleUrls: ['./facultades.css'],
})
export class Facultades implements OnInit {
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
      });
    }
  }

  //Manejo de ingreso de facultades

  facultadForm: FormGroup;

  get puedeCrear(): boolean {
    return this.permisos.tieneAlgunPermiso(['organization.add_facultad']);
  }

  get ocultarAcciones(): string[] {
    if (this.permisos.tieneAlgunPermiso(['organization.change_facultad', 'organization.delete_facultad'])) {
      return [];
    }
    const ocultas: string[] = [];
    if (!this.permisos.tienePermiso('organization.change_facultad')) ocultas.push('edit', 'toggle');
    if (!this.permisos.tienePermiso('organization.delete_facultad')) ocultas.push('remove');
    return ocultas;
  }

  constructor(
    private fb: FormBuilder,
    private authService: AuthService,
    private permisos: PermisosService,
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
  }
}
