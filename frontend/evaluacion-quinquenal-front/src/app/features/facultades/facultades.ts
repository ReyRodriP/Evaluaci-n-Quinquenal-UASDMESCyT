import { Component, OnInit } from '@angular/core';
import { CrudTable } from '../../shared/components/CRUD/crud-table/crud-table';
import { SearchBar } from '../../shared/components/CRUD/search-bar/search-bar';
import { Pagination } from '../../shared/components/CRUD/pagination/pagination';
import { Modal } from '../../shared/components/CRUD/modal/modal';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { AuthService } from '../auth/services/auth-service';
import { ToastrService } from 'ngx-toastr';

@Component({
  selector: 'app-facultades',
  imports: [CrudTable, SearchBar, Pagination, Modal],
  templateUrl: './facultades.html',
  styleUrls: ['./facultades.css'],
})
export class Facultades implements OnInit {
  columnas: string[] = ['Nombre', 'Descripción', 'Estado', 'Fecha de Creación'];

  datos: any[] = [];

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
      },
      error: (err) => {
        console.error('Error cargando facultades', err);
        this.toast.error('No se pudieron cargar las facultades');
      }
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
  }
}
