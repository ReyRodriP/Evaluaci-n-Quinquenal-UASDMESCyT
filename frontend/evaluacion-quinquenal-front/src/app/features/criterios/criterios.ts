import { Component, OnInit } from '@angular/core';
import { CrudTable } from '../../shared/components/CRUD/crud-table/crud-table';
import { SearchBar } from '../../shared/components/CRUD/search-bar/search-bar';
import { Pagination } from '../../shared/components/CRUD/pagination/pagination';
import { Modal } from '../../shared/components/CRUD/modal/modal';
import { AuthService } from '../../core/services/auth.service';
import { ToastrService } from 'ngx-toastr';

@Component({
  selector: 'app-criterios',
  imports: [CrudTable, SearchBar, Pagination, Modal],
  templateUrl: './criterios.html',
  styleUrl: './criterios.css',
})
export class Criterios implements OnInit {
  columnas: string[] = ['Nombre', 'Descripción', 'Período', 'Estado', 'Indicadores'];

  datos: any[] = [];
  periodos: any[] = [];

  showModal: boolean = false;
  selectedItem: any = null;

  criterioFields: any[] = [
    { label: 'Nombre', name: 'nombre', type: 'text', placeholder: 'Ej. Criterio de calidad', defaultValue: '' },
    { label: 'Descripción', name: 'descripcion', type: 'textarea', placeholder: 'Descripción del criterio', defaultValue: '' },
    { label: 'Período', name: 'periodo', type: 'select', options: [], defaultValue: '' },
    { label: 'Estado', name: 'estado', type: 'select', options: ['Activo', 'Inactivo'], defaultValue: 'Activo' }
  ];

  constructor(
    private authService: AuthService,
    private toast: ToastrService
  ) {}

  ngOnInit() {
    this.loadPeriodos();
    this.loadCriterios();
  }

  openNew() {
    this.selectedItem = null;
    this.showModal = true;
  }

  openEdit(item: any) {
    this.selectedItem = {
      ...item,
      periodo: item.periodoId ?? item.periodo,
      estado: item.activo ? 'Activo' : 'Inactivo',
    };
    this.showModal = true;
  }

  loadPeriodos() {
    this.authService.listarPeriodos().subscribe({
      next: (data) => {
        this.periodos = data;
        this.criterioFields = this.criterioFields.map(field => {
          if (field.name !== 'periodo') {
            return field;
          }

          return {
            ...field,
            options: this.periodos.map((periodo: any) => ({ value: periodo.id, label: periodo.nombre }))
          };
        });
      },
      error: (err) => {
        console.error('Error cargando periodos', err);
        this.toast.error('No se pudieron cargar los periodos');
      }
    });
  }

  loadCriterios() {
    this.authService.listarCriterios().subscribe({
      next: (data) => {
        this.datos = data.map((item: any) => ({
          ...item,
          periodo: item.periodo_nombre || '',
          periodoId: item.periodo,
          estado: item.activo ? 'Activo' : 'Inactivo'
        }));
        console.log('Criterios cargados:', this.datos);
      },
      error: (err) => {
        console.error('Error cargando criterios', err);
        this.toast.error('No se pudieron cargar los criterios');
      }
    });
  }

  onModalClose() {
    this.showModal = false;
    this.selectedItem = null;
  }

  onModalSave(saved: any) {
    if (!saved.nombre || !saved.periodo) {
      this.toast.error('Complete todos los campos requeridos');
      return;
    }

    const payload = {
      nombre: saved.nombre,
      descripcion: saved.descripcion,
      periodo: saved.periodo,
      activo: saved.estado === 'Activo',
    };

    if (this.selectedItem && this.selectedItem.id) {
      this.authService.actualizarCriterio(this.selectedItem.id, payload).subscribe({
        next: () => {
          this.toast.success('Criterio actualizado correctamente');
          this.loadCriterios();
          this.onModalClose();
        },
        error: (err) => {
          console.error('Error actualizando criterio', err);
          this.toast.error('Error al actualizar el criterio');
        }
      });
    } else {
      this.authService.crearCriterio(payload).subscribe({
        next: () => {
          this.toast.success('Criterio creado exitosamente');
          this.loadCriterios();
          this.onModalClose();
        },
        error: (err) => {
          console.error('Error creando criterio', err);
          this.toast.error('Error al crear el criterio');
        }
      });
    }
  }

  onRemove(item: any) {
    if (!item.id) {
      return;
    }

    this.authService.eliminarCriterio(item.id).subscribe({
      next: () => {
        this.toast.success('Criterio eliminado');
        this.loadCriterios();
      },
      error: (err) => {
        console.error('Error eliminando criterio', err);
        this.toast.error('No se pudo eliminar el criterio');
      }
    });
  }

  onToggleEstado(item: any) {
    if (!item.id) {
      return;
    }

    const nuevoEstado = !item.activo;

    this.authService.patchCriterio(item.id, { activo: nuevoEstado }).subscribe({
      next: () => {
        this.toast.success(`Criterio ${nuevoEstado ? 'activado' : 'desactivado'} correctamente`);
        this.loadCriterios();
      },
      error: (err) => {
        console.error('Error cambiando estado de criterio', err);
        this.toast.error('No se pudo cambiar el estado del criterio');
      }
    });
  }
}
