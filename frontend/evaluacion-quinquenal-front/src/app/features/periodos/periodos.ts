import { Component, OnInit } from '@angular/core';
import { CrudTable } from '../../shared/components/CRUD/crud-table/crud-table';
import { SearchBar } from '../../shared/components/CRUD/search-bar/search-bar';
import { Pagination } from '../../shared/components/CRUD/pagination/pagination';
import { Modal } from '../../shared/components/CRUD/modal/modal';
import { AuthService } from '../../core/services/auth.service';
import { ToastrService } from 'ngx-toastr';

@Component({
  selector: 'app-periodos',
  imports: [CrudTable, SearchBar, Pagination, Modal],
  templateUrl: './periodos.html',
  styleUrl: './periodos.css',
})
export class Periodos implements OnInit {
  columnas: string[] = ['Nombre', 'Fecha Inicio', 'Fecha Fin', 'Estado'];

  datos: any[] = [];
  datosFiltrados: any[] = [];
  searchTerm = '';
  selectedState = 'Todas';

  showModal: boolean = false;
  selectedItem: any = null;

  periodoFields: any[] = [
    { label: 'Nombre', name: 'nombre', type: 'text', placeholder: 'Ej. Período 2020-2025', defaultValue: '' },
    { label: 'Fecha Inicio', name: 'fecha_inicio', type: 'date', defaultValue: '' },
    { label: 'Fecha Fin', name: 'fecha_fin', type: 'date', defaultValue: '' },
    { label: 'Estado', name: 'estado', type: 'select', options: ['Activo', 'Inactivo'], defaultValue: 'Activo' }
  ];

  constructor(
    private authService: AuthService,
    private toast: ToastrService
  ) {}

  ngOnInit() {
    this.loadPeriodos();
  }

  openNew() {
    this.selectedItem = null;
    this.showModal = true;
  }

  openEdit(item: any) {
    this.selectedItem = {
      ...item,
    };
    this.showModal = true;
  }

  loadPeriodos() {
    this.authService.listarPeriodos().subscribe({
      next: (data) => {
        this.datos = data.map((item: any) => ({
          ...item,
          estado: item.activo ? 'Activo' : 'Inactivo',
          fecha_inicio: item.fecha_inicio ? item.fecha_inicio.split('T')[0] : '',
          fecha_fin: item.fecha_fin ? item.fecha_fin.split('T')[0] : '',
        }));
        this.applySearch();
      },
      error: (err) => {
        console.error('Error cargando periodos', err);
        this.toast.error('No se pudieron cargar los periodos');
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
        || (this.selectedState === 'Activos' && item.activo)
        || (this.selectedState === 'Inactivos' && !item.activo);
      return matchesSearch && matchesState;
    });
  }

  onModalClose() {
    this.showModal = false;
    this.selectedItem = null;
  }

  onModalSave(saved: any) {
    if (!saved.nombre || !saved.fecha_inicio || !saved.fecha_fin) {
      this.toast.error('Complete todos los campos requeridos');
      return;
    }

    const payload = {
      nombre: saved.nombre,
      fecha_inicio: saved.fecha_inicio,
      fecha_fin: saved.fecha_fin,
      activo: saved.estado === 'Activo',
    };

    if (this.selectedItem && this.selectedItem.id) {
      this.authService.actualizarPeriodo(this.selectedItem.id, payload).subscribe({
        next: () => {
          this.toast.success('Período actualizado correctamente');
          this.loadPeriodos();
          this.onModalClose();
        },
        error: (err) => {
          console.error('Error actualizando período', err);
          this.toast.error('Error al actualizar el período');
        }
      });
    } else {
      this.authService.crearPeriodo(payload).subscribe({
        next: () => {
          this.toast.success('Período creado exitosamente');
          this.loadPeriodos();
          this.onModalClose();
        },
        error: (err) => {
          console.error('Error creando período', err);
          this.toast.error('Error al crear el período');
        }
      });
    }
  }

  onRemove(item: any) {
    if (!item.id) {
      return;
    }

    this.authService.eliminarPeriodo(item.id).subscribe({
      next: () => {
        this.toast.success('Período eliminado');
        this.loadPeriodos();
      },
      error: (err) => {
        console.error('Error eliminando período', err);
        this.toast.error('No se pudo eliminar el período');
      }
    });
  }

  onToggleEstado(item: any) {
    if (!item.id) {
      return;
    }

    const nuevoEstado = !item.activo;

    this.authService.patchPeriodo(item.id, { activo: nuevoEstado }).subscribe({
      next: () => {
        this.toast.success(`Período ${nuevoEstado ? 'activado' : 'desactivado'} correctamente`);
        this.loadPeriodos();
      },
      error: (err) => {
        console.error('Error cambiando estado de período', err);
        this.toast.error('No se pudo cambiar el estado del período');
      }
    });
  }
}
