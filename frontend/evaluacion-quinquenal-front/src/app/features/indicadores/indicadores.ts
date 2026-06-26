import { Component, OnInit } from '@angular/core';
import { CrudTable } from '../../shared/components/CRUD/crud-table/crud-table';
import { SearchBar } from '../../shared/components/CRUD/search-bar/search-bar';
import { Pagination } from '../../shared/components/CRUD/pagination/pagination';
import { Modal } from '../../shared/components/CRUD/modal/modal';
import { AuthService } from '../../core/services/auth.service';
import { ToastrService } from 'ngx-toastr';

@Component({
  selector: 'app-indicadores',
  imports: [CrudTable, SearchBar, Pagination, Modal],
  templateUrl: './indicadores.html',
  styleUrl: './indicadores.css',
})
export class Indicadores implements OnInit {
  columnas: string[] = ['Nombre', 'Descripción', 'Criterio', 'Obligatorio', 'Estado'];

  datos: any[] = [];
  criterios: any[] = [];

  showModal: boolean = false;
  selectedItem: any = null;

  indicadorFields: any[] = [
    { label: 'Nombre', name: 'nombre', type: 'text', placeholder: 'Ej. Indicador 1', defaultValue: '' },
    { label: 'Descripción', name: 'descripcion', type: 'textarea', placeholder: 'Descripción del indicador', defaultValue: '' },
    { label: 'Criterio', name: 'criterio', type: 'select', options: [], defaultValue: '' },
    { label: 'Obligatorio', name: 'obligatorio', type: 'select', options: ['Si', 'No'], defaultValue: 'No' },
    { label: 'Estado', name: 'estado', type: 'select', options: ['Activo', 'Inactivo'], defaultValue: 'Activo' }
  ];

  constructor(
    private authService: AuthService,
    private toast: ToastrService
  ) {}

  ngOnInit() {
    this.loadCriterios();
    this.loadIndicadores();
  }

  openNew() {
    this.selectedItem = null;
    this.showModal = true;
  }

  openEdit(item: any) {
    this.selectedItem = {
      ...item,
      criterio: item.criterioId ?? item.criterio,
      obligatorio: item.obligatorio ? 'Si' : 'No',
      estado: item.activo ? 'Activo' : 'Inactivo',
    };
    this.showModal = true;
  }

  loadCriterios() {
    this.authService.listarCriterios().subscribe({
      next: (data) => {
        this.criterios = data;
        this.indicadorFields = this.indicadorFields.map(field => {
          if (field.name !== 'criterio') {
            return field;
          }

          return {
            ...field,
            options: this.criterios.map((criterio: any) => ({ value: criterio.id, label: criterio.nombre }))
          };
        });
      },
      error: (err) => {
        console.error('Error cargando criterios', err);
        this.toast.error('No se pudieron cargar los criterios');
      }
    });
  }

  loadIndicadores() {
    this.authService.listarIndicadores().subscribe({
      next: (data) => {
        this.datos = data.map((item: any) => ({
          ...item,
          estado: item.activo ? 'Activo' : 'Inactivo',
          criterio: item.criterio_nombre || '',
          criterioId: item.criterio,
          obligatorio: item.obligatorio ? 'Si' : 'No'
        }));
      },
      error: (err) => {
        console.error('Error cargando indicadores', err);
        this.toast.error('No se pudieron cargar los indicadores');
      }
    });
  }

  onModalClose() {
    this.showModal = false;
    this.selectedItem = null;
  }

  onModalSave(saved: any) {
    if (!saved.nombre || !saved.criterio) {
      this.toast.error('Complete todos los campos requeridos');
      return;
    }

    const payload = {
      nombre: saved.nombre,
      descripcion: saved.descripcion,
      criterio: saved.criterio,
      obligatorio: saved.obligatorio === 'Si',
      activo: saved.estado === 'Activo',
    };

    if (this.selectedItem && this.selectedItem.id) {
      this.authService.actualizarIndicador(this.selectedItem.id, payload).subscribe({
        next: () => {
          this.toast.success('Indicador actualizado correctamente');
          this.loadIndicadores();
          this.onModalClose();
        },
        error: (err) => {
          console.error('Error actualizando indicador', err);
          this.toast.error('Error al actualizar el indicador');
        }
      });
    } else {
      this.authService.crearIndicador(payload).subscribe({
        next: () => {
          this.toast.success('Indicador creado exitosamente');
          this.loadIndicadores();
          this.onModalClose();
        },
        error: (err) => {
          console.error('Error creando indicador', err);
          this.toast.error('Error al crear el indicador');
        }
      });
    }
  }

  onRemove(item: any) {
    if (!item.id) {
      return;
    }

    this.authService.eliminarIndicador(item.id).subscribe({
      next: () => {
        this.toast.success('Indicador eliminado');
        this.loadIndicadores();
      },
      error: (err) => {
        console.error('Error eliminando indicador', err);
        this.toast.error('No se pudo eliminar el indicador');
      }
    });
  }

  onToggleEstado(item: any) {
    if (!item.id) {
      return;
    }

    const nuevoEstado = !item.activo;

    this.authService.patchIndicador(item.id, { activo: nuevoEstado }).subscribe({
      next: () => {
        this.toast.success(`Indicador ${nuevoEstado ? 'activado' : 'desactivado'} correctamente`);
        this.loadIndicadores();
      },
      error: (err) => {
        console.error('Error cambiando estado de indicador', err);
        this.toast.error('No se pudo cambiar el estado del indicador');
      }
    });
  }
}
