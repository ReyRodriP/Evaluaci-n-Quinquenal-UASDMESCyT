import { Component, OnInit } from '@angular/core';
import { CrudTable } from '../../shared/components/CRUD/crud-table/crud-table';
import { SearchBar } from '../../shared/components/CRUD/search-bar/search-bar';
import { Pagination } from '../../shared/components/CRUD/pagination/pagination';
import { Modal } from '../../shared/components/CRUD/modal/modal';
import { EvaluacionService } from '../../core/services/evaluacion.service';
import { ToastrService } from 'ngx-toastr';
import { PermisosService } from '../../core/services/permisos.service';
import { CatalogoService } from '../../core/services/catalogo.service';

@Component({
  selector: 'app-periodos',
  imports: [CrudTable, SearchBar, Pagination, Modal],
  templateUrl: './periodos.html',
  styleUrl: './periodos.css',
})
export class Periodos implements OnInit {
  columnas: string[] = ['Nombre', 'Fecha Inicio', 'Fecha Fin', 'Versión del marco', 'Estado'];
  versiones: any[] | null = null;

  datos: any[] = [];
  datosFiltrados: any[] = [];
  datosPaginados: any[] = [];
  searchTerm = '';
  selectedState = 'Todas';
  currentPage = 1;
  pageSize = 10;

  showModal: boolean = false;
  selectedItem: any = null;

  periodoFields: any[] = [
    { label: 'Nombre', name: 'nombre', type: 'text', placeholder: 'Ej. Período 2020-2025', defaultValue: '' },
    { label: 'Fecha Inicio', name: 'fecha_inicio', type: 'date', defaultValue: '' },
    { label: 'Fecha Fin', name: 'fecha_fin', type: 'date', defaultValue: '' },
    { label: 'Estado', name: 'estado', type: 'select', options: ['Activo', 'Inactivo'], defaultValue: 'Activo' }
  ];

  get puedeCrear(): boolean {
    return this.permisos.tieneAlgunPermiso(['evaluation.add_periodo']);
  }

  get ocultarAcciones(): string[] {
    if (this.permisos.tieneAlgunPermiso(['evaluation.change_periodo', 'evaluation.delete_periodo'])) {
      return [];
    }
    const ocultas: string[] = [];
    if (!this.permisos.tienePermiso('evaluation.change_periodo')) ocultas.push('edit', 'toggle');
    if (!this.permisos.tienePermiso('evaluation.delete_periodo')) ocultas.push('remove');
    return ocultas;
  }

  constructor(
    private evaluacionService: EvaluacionService,
    private permisos: PermisosService,
    private toast: ToastrService,
    private catalogo: CatalogoService
  ) {}

  ngOnInit() {
    this.loadPeriodos();
    this.catalogo.listarVersionesCompletas().subscribe({
      next: versiones => { this.versiones = versiones; if (!this.showModal) this.configurarVersiones(); },
      error: () => this.toast.error('No se pudieron consultar las versiones del marco; se conserva la selección existente de cada período'),
    });
  }

  private configurarVersiones(): void {
    if (this.versiones === null) return;
    this.periodoFields = this.periodoFields.filter(campo => campo.name !== 'version_marco');
    this.periodoFields.splice(3, 0, { label: 'Versión del marco', name: 'version_marco', type: 'select', allowClear: true,
      options: this.versiones.map(v => ({ value: v.id, label: `${v.nombre}${v.activo ? ' · Activa globalmente' : ' · Inactiva globalmente'}` })), defaultValue: null });
  }

  openNew() {
    this.configurarVersiones();
    this.selectedItem = null;
    this.showModal = true;
  }

  openEdit(item: any) {
    this.configurarVersiones();
    this.selectedItem = {
      ...item,
      estado: item.activo ? 'Activo' : 'Inactivo',
    };
    this.showModal = true;
  }

  loadPeriodos() {
    this.evaluacionService.listarPeriodos().subscribe({
      next: (data) => {
        this.datos = data.map((item: any) => ({
          ...item,
          estado: item.activo ? 'Activo' : 'Finalizado',
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
        || (this.selectedState === 'Finalizados' && !item.activo);
      return matchesSearch && matchesState;
    });
    this.currentPage = 1;
    this.actualizarPagina();
  }

  actualizarPagina(): void {
    const start = (this.currentPage - 1) * this.pageSize;
    this.datosPaginados = this.datosFiltrados.slice(start, start + this.pageSize);
  }

  onPageSizeChange(size: number): void {
    this.pageSize = size;
    this.currentPage = 1;
    this.actualizarPagina();
  }

  onPageChange(page: number): void {
    this.currentPage = page;
    this.actualizarPagina();
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
    if (saved.fecha_inicio >= saved.fecha_fin) {
      this.toast.error('La fecha de fin debe ser posterior a la fecha de inicio');
      return;
    }

    const payload = {
      nombre: saved.nombre,
      fecha_inicio: saved.fecha_inicio,
      fecha_fin: saved.fecha_fin,
      activo: saved.estado === 'Activo',
      ...(this.periodoFields.some(campo => campo.name === 'version_marco') && Object.prototype.hasOwnProperty.call(saved, 'version_marco')
        ? { version_marco: saved.version_marco ? Number(saved.version_marco) : null } : {}),
    };

    if (this.selectedItem && this.selectedItem.id) {
      this.evaluacionService.actualizarPeriodo(this.selectedItem.id, payload).subscribe({
        next: () => {
          this.toast.success('Período actualizado correctamente');
          this.loadPeriodos();
          this.onModalClose();
        },
        error: (err) => {
          console.error('Error actualizando período', err);
          this.toast.error(err?.error ? Object.values(err.error).flat().map(String).join(' ') : 'Error al actualizar el período');
        }
      });
    } else {
      this.evaluacionService.crearPeriodo(payload).subscribe({
        next: () => {
          this.toast.success('Período creado exitosamente');
          this.loadPeriodos();
          this.onModalClose();
        },
        error: (err) => {
          console.error('Error creando período', err);
          this.toast.error(err?.error ? Object.values(err.error).flat().map(String).join(' ') : 'Error al crear el período');
        }
      });
    }
  }

  onRemove(item: any) {
    if (!item.id) {
      return;
    }

    this.evaluacionService.eliminarPeriodo(item.id).subscribe({
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

    this.evaluacionService.patchPeriodo(item.id, { activo: nuevoEstado }).subscribe({
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
