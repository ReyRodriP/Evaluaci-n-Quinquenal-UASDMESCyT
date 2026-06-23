import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-crud-table',
  imports: [CommonModule],
  templateUrl: './crud-table.html',
  styleUrls: ['./crud-table.css'],
})
export class CrudTable {
  @Input() columnas: string[] = [];

  @Input() datos: any[] = [];
  @Output() edit = new EventEmitter<any>();
  @Output() remove = new EventEmitter<any>();
  @Output() toggleEstado = new EventEmitter<any>();

  onEdit(item: any) {
    this.edit.emit(item);
  }

  onRemove(item: any) {
    this.remove.emit(item);
  }

  onToggleEstado(item: any) {
    this.toggleEstado.emit(item);
  }

  getColumnKey(columnName: string): string {
    const mapping: { [key: string]: string } = {
      'nombre': 'nombre',
      'código': 'codigo',
      'descripción': 'descripcion',
      'estado': 'estado',
      'fecha de creación': 'fechaCreacion',
      'acciones': 'acciones'
    };
    return mapping[columnName.toLowerCase()] || columnName.toLowerCase();
  }

  getDataColumns(): string[] {
    return this.columnas.filter(col => col.toLowerCase() !== 'acciones');
  }
}
