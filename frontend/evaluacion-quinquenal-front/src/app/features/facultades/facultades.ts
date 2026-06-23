import { Component } from '@angular/core';
import { CrudTable } from '../../shared/components/CRUD/crud-table/crud-table';
import { SearchBar } from '../../shared/components/CRUD/search-bar/search-bar';
import { Pagination } from '../../shared/components/CRUD/pagination/pagination';
import { Modal } from '../../shared/components/CRUD/modal/modal';
@Component({
  selector: 'app-facultades',
  imports: [CrudTable, SearchBar, Pagination, Modal],
  templateUrl: './facultades.html',
  styleUrls: ['./facultades.css'],
})
export class Facultades {
  columnas: string[] = ['Nombre', 'Descripción', 'Estado', 'Fecha de Creación'];

  datos: any[] = [
    { nombre: 'Facultad de Ciencias', descripcion: 'Facultad dedicada a las ciencias naturales y exactas', estado: 'Activa', fechaCreacion: '2020-01-01' },
    { nombre: 'Facultad de Ingeniería', descripcion: 'Facultad dedicada a la ingeniería y tecnología', estado: 'Activa', fechaCreacion: '2020-01-01' },
  ];

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

  onModalClose() {
    this.showModal = false;
    this.selectedItem = null;
  }

  onModalSave(saved: any) {
    // if editing existing item, update it; otherwise push new
    if (this.selectedItem) {
      const idx = this.datos.findIndex(d => d.nombre === this.selectedItem.nombre && d.fechaCreacion === this.selectedItem.fechaCreacion);
      if (idx > -1) this.datos[idx] = saved;
    } else {
      this.datos.push(saved);
    }
    this.onModalClose();
  }
}
