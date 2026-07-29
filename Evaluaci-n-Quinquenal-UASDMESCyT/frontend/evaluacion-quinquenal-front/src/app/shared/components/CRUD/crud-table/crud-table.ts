import { Component, Input, Output, EventEmitter, ContentChild, TemplateRef } from '@angular/core';
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
  @Input() ocultarAcciones: string[] = [];

  @Output() edit = new EventEmitter<any>();
  @Output() remove = new EventEmitter<any>();
  @Output() toggleEstado = new EventEmitter<any>();

  @ContentChild('acciones') accionesTemplate?: TemplateRef<any>;

  onEdit(item: any) {
    this.edit.emit(item);
  }

  onRemove(item: any) {
    this.remove.emit(item);
  }

  onToggleEstado(item: any) {
    this.toggleEstado.emit(item);
  }

  get showAccionesColumn(): boolean {
    return this.accionesTemplate != null || ['edit', 'toggle', 'remove'].some(a => !this.ocultarAcciones.includes(a));
  }

  mostrarBoton(nombre: string): boolean {
    return !this.ocultarAcciones.includes(nombre);
  }

  getColumnKey(columnName: string): string {
    const mapping: { [key: string]: string } = {
      'nombre de usuario': 'username',
      'nombre': 'nombre',
      'código': 'codigo',
      'descripción': 'descripcion',
      'criterio': 'criterio_nombre',
      'periodo': 'periodo_nombre',
      'período': 'periodo_nombre',
      'indicadores': 'indicadores',
      'obligatorio': 'obligatorio',
      'estado': 'estado',
      'fecha de creación': 'fechaCreacion',
      'fecha inicio': 'fecha_inicio',
      'fecha fin': 'fecha_fin',
      'acciones': 'acciones',
      'departamento': 'departamento_nombre',
      'indicador': 'indicador_nombre',
      'archivo': 'archivoNombre',
      'observaciones': 'observacionesTexto',
      'usuario': 'usuario_nombre',
      'acción': 'accion',
      'modelo': 'modelo',
      'fecha': 'fecha',
    };
    return mapping[columnName.toLowerCase()] || columnName.toLowerCase();
  }

  getCellValue(item: any, columnName: string): any {
    const key = this.getColumnKey(columnName);
    const directValue = item?.[key];

    if (directValue !== undefined && directValue !== null && directValue !== '') {
      return directValue;
    }

    const aliases = this.getColumnAliases(columnName);
    for (const alias of aliases) {
      const aliasValue = item?.[alias];
      if (aliasValue !== undefined && aliasValue !== null && aliasValue !== '') {
        return aliasValue;
      }
    }

    return '';
  }

  private getColumnAliases(columnName: string): string[] {
    const normalized = columnName.toLowerCase();

    switch (normalized) {
      case 'nombre':
        return ['first_name', 'name', 'username', 'nombre'];
      case 'correo':
        return ['email', 'correo'];
      case 'departamento':
        return ['departamento_nombre', 'nombre_departamento', 'departamento', 'nombre'];
      case 'rol':
        return ['rol', 'role', 'nombre_rol'];
      case 'estado':
        return ['estado', 'is_active'];
      default:
        return [];
    }
  }

  getDataColumns(): string[] {
    return this.columnas.filter(col => col.toLowerCase() !== 'acciones');
  }
}
