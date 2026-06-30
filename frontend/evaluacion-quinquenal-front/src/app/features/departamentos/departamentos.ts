import { Component, OnInit } from '@angular/core';
import { CrudTable } from '../../shared/components/CRUD/crud-table/crud-table';
import { SearchBar } from '../../shared/components/CRUD/search-bar/search-bar';
import { Pagination } from '../../shared/components/CRUD/pagination/pagination';
import { Modal } from '../../shared/components/CRUD/modal/modal';
import { AuthService } from '../auth/services/auth-service';
import { ToastrService } from 'ngx-toastr';

@Component({
  selector: 'app-departamentos',
  imports: [CrudTable, SearchBar, Pagination, Modal],
  templateUrl: './departamentos.html',
  styleUrl: './departamentos.css',
})
export class Departamentos implements OnInit {
  columnas: string[] = ['Nombre', 'Descripción', 'Facultad', 'Estado', 'Fecha de Creación'];

  datos: any[] = [];
  datosFiltrados: any[] = [];
  facultades: any[] = [];
  searchTerm = '';
  selectedState = 'Todas';

  showModal: boolean = false;
  selectedItem: any = null;

  departamentoFields: any[] = [
    { label: 'Nombre', name: 'nombre', type: 'text', placeholder: 'Ej. Escuela de Informática', defaultValue: '' },
    { label: 'Descripción', name: 'descripcion', type: 'textarea', placeholder: 'Descripción del departamento', defaultValue: '' },
    { label: 'Facultad', name: 'facultad', type: 'select', options: [], defaultValue: '' },
    { label: 'Estado', name: 'estado', type: 'select', options: ['Activa', 'Inactiva'], defaultValue: 'Activa' }
  ];

  constructor(
    private authService: AuthService,
    private toast: ToastrService
  ) {}

  ngOnInit() {
    this.loadFacultades();
    this.loadDepartamentos();
  }

  openNew() {
    this.selectedItem = null;
    this.showModal = true;
  }

  openEdit(item: any) {
    this.selectedItem = {
      ...item,
      facultad: item.facultadId ?? item.facultad,
    };
    this.showModal = true;
  }

  loadFacultades() {
    this.authService.listarFacultades().subscribe({
      next: (data) => {
        this.facultades = data;
        this.departamentoFields = this.departamentoFields.map(field => {
          if (field.name !== 'facultad') {
            return field;
          }

          return {
            ...field,
            options: this.facultades.map((fac: any) => ({ value: fac.id, label: fac.nombre }))
          };
        });
      },
      error: (err) => {
        console.error('Error cargando facultades', err);
        this.toast.error('No se pudieron cargar las facultades');
      }
    });
  }

  loadDepartamentos() {
    this.authService.listarDepartamentos().subscribe({
      next: (data) => {
        this.datos = data.map((item: any) => ({
          ...item,
          estado: item.activo ? 'Activa' : 'Inactiva',
          fechaCreacion: item.fecha_creacion ? item.fecha_creacion.split('T')[0] : '',
          facultad: item.facultad_nombre || '',
          facultadId: item.facultad
        }));
        this.applySearch();
      },
      error: (err) => {
        console.error('Error cargando departamentos', err);
        this.toast.error('No se pudieron cargar los departamentos');
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
    if (!saved.facultad) {
      this.toast.error('Seleccione una facultad');
      return;
    }

    const payload = {
      nombre: saved.nombre,
      descripcion: saved.descripcion,
      facultad: saved.facultad,
      activo: saved.estado === 'Activa',
    };

    if (this.selectedItem && this.selectedItem.id) {
      this.authService.actualizarDepartamento(this.selectedItem.id, payload).subscribe({
        next: () => {
          this.toast.success('Departamento actualizado correctamente');
          this.loadDepartamentos();
          this.onModalClose();
        },
        error: (err) => {
          console.error('Error actualizando departamento', err);
          this.toast.error('Error al actualizar el departamento');
        }
      });
    } else {
      this.authService.crearDepartamento(payload).subscribe({
        next: () => {
          this.toast.success('Departamento creado exitosamente');
          this.loadDepartamentos();
          this.onModalClose();
        },
        error: (err) => {
          console.error('Error creando departamento', err);
          this.toast.error('Error al crear el departamento');
        }
      });
    }
  }

  onRemove(item: any) {
    if (!item.id) {
      return;
    }

    this.authService.eliminarDepartamento(item.id).subscribe({
      next: () => {
        this.toast.success('Departamento eliminado');
        this.loadDepartamentos();
      },
      error: (err) => {
        console.error('Error eliminando departamento', err);
        this.toast.error('No se pudo eliminar el departamento');
      }
    });
  }

  onToggleEstado(item: any) {
    if (!item.id) {
      return;
    }

    const nuevoEstado = !item.activo;

    this.authService.actualizarDepartamento(item.id, { activo: nuevoEstado }).subscribe({
      next: () => {
        this.toast.success(`Departamento ${nuevoEstado ? 'activado' : 'desactivado'} correctamente`);
        this.loadDepartamentos();
      },
      error: (err) => {
        console.error('Error cambiando estado de departamento', err);
        this.toast.error('No se pudo cambiar el estado del departamento');
      }
    });
  }
}
