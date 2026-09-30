import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { forkJoin } from 'rxjs';
import { ToastrService } from 'ngx-toastr';
import { OrganizacionService } from '../../core/services/organizacion.service';

interface UnitTreeNode {
  unit: any;
  depth: number;
  children: UnitTreeNode[];
}

@Component({
  selector: 'app-organizacion',
  imports: [CommonModule, FormsModule],
  templateUrl: './organizacion.html',
  styleUrl: './organizacion.css',
})
export class Organizacion implements OnInit {
  activeTab: 'estructura' | 'tipos' = 'estructura';
  tipos: any[] = [];
  unidades: any[] = [];
  selectedUnit: any = null;
  expandedIds = new Set<number>();
  searchTerm = '';
  loading = false;
  saving = false;
  editingType: any = null;
  unitForm = this.emptyUnitForm();
  typeForm = this.emptyTypeForm();

  constructor(
    private organizacionService: OrganizacionService,
    private toast: ToastrService,
  ) {}

  ngOnInit(): void {
    this.loadData();
  }

  get unitTree(): UnitTreeNode[] {
    const roots = this.buildNodes(null, 0);
    const term = this.searchTerm.trim().toLocaleLowerCase();
    return term ? this.filterNodes(roots, term) : roots;
  }

  get parentOptions(): any[] {
    if (!this.selectedUnit) return this.unidades;
    const excluded = new Set<number>([this.selectedUnit.id]);
    let previousSize = -1;
    while (excluded.size !== previousSize) {
      previousSize = excluded.size;
      this.unidades.forEach(unit => {
        if (excluded.has(unit.unidad_padre)) excluded.add(unit.id);
      });
    }
    return this.unidades.filter(unit => !excluded.has(unit.id));
  }

  countByType(typeId: number): number {
    return this.unidades.filter(unit => unit.tipo === typeId).length;
  }

  loadData(): void {
    this.loading = true;
    forkJoin({
      tipos: this.organizacionService.listarTiposUnidad(),
      unidades: this.organizacionService.listarUnidadesOrganizacionales(),
    }).subscribe({
      next: ({ tipos, unidades }) => {
        this.tipos = tipos;
        this.unidades = unidades;
        this.expandedIds = new Set(unidades.map(unit => unit.id));
        if (this.selectedUnit) {
          this.selectedUnit = unidades.find(unit => unit.id === this.selectedUnit.id) ?? null;
          if (this.selectedUnit) this.setUnitForm(this.selectedUnit);
        }
        this.loading = false;
      },
      error: () => {
        this.loading = false;
        this.toast.error('No se pudo cargar la estructura organizacional');
      },
    });
  }

  private buildNodes(parentId: number | null, depth: number): UnitTreeNode[] {
    return this.unidades
      .filter(unit => (unit.unidad_padre ?? null) === parentId)
      .sort((left, right) => left.nombre.localeCompare(right.nombre, 'es'))
      .map(unit => ({
        unit,
        depth,
        children: this.buildNodes(unit.id, depth + 1),
      }));
  }

  private filterNodes(nodes: UnitTreeNode[], term: string): UnitTreeNode[] {
    return nodes.reduce((matches: UnitTreeNode[], node) => {
      const children = this.filterNodes(node.children, term);
      const label = `${node.unit.nombre} ${node.unit.tipo_nombre}`.toLocaleLowerCase();
      if (label.includes(term) || children.length) matches.push({ ...node, children });
      return matches;
    }, []);
  }

  trackByUnit(_index: number, node: UnitTreeNode): number {
    return node.unit.id;
  }

  isExpanded(node: UnitTreeNode): boolean {
    return !!this.searchTerm.trim() || this.expandedIds.has(node.unit.id);
  }

  toggleExpanded(id: number): void {
    const expanded = new Set(this.expandedIds);
    if (expanded.has(id)) expanded.delete(id);
    else expanded.add(id);
    this.expandedIds = expanded;
  }

  selectUnit(unit: any): void {
    this.selectedUnit = unit;
    this.setUnitForm(unit);
  }

  newUnit(): void {
    this.selectedUnit = null;
    this.unitForm = this.emptyUnitForm();
  }

  addChild(): void {
    if (!this.selectedUnit) return this.newUnit();
    const parent = this.selectedUnit;
    this.selectedUnit = null;
    this.unitForm = this.emptyUnitForm();
    this.unitForm.unidad_padre = parent.id;
  }

  saveUnit(): void {
    if (!this.unitForm.nombre.trim() || !this.unitForm.tipo) {
      this.toast.error('Indica el nombre y tipo de la unidad');
      return;
    }

    const payload = {
      nombre: this.unitForm.nombre.trim(),
      descripcion: this.unitForm.descripcion.trim(),
      tipo: Number(this.unitForm.tipo),
      unidad_padre: this.unitForm.unidad_padre || null,
      activa: this.unitForm.activa,
    };
    this.saving = true;
    const request = this.selectedUnit
      ? this.organizacionService.actualizarUnidadOrganizacional(this.selectedUnit.id, payload)
      : this.organizacionService.crearUnidadOrganizacional(payload);

    request.subscribe({
      next: (unit: any) => {
        this.toast.success(this.selectedUnit ? 'Unidad actualizada' : 'Unidad creada');
        this.selectedUnit = unit;
        this.saving = false;
        this.loadData();
      },
      error: (err) => {
        this.saving = false;
        const detail = err?.error?.unidad_padre?.[0] || err?.error?.detail;
        this.toast.error(detail || 'No se pudo guardar la unidad');
      },
    });
  }

  toggleUnitActive(): void {
    if (!this.selectedUnit) return;
    this.unitForm.activa = !this.unitForm.activa;
    this.saveUnit();
  }

  newType(): void {
    this.editingType = null;
    this.typeForm = this.emptyTypeForm();
  }

  editType(type: any): void {
    this.editingType = type;
    this.typeForm = {
      nombre: type.nombre,
      descripcion: type.descripcion ?? '',
      activo: type.activo,
    };
  }

  saveType(): void {
    if (!this.typeForm.nombre.trim()) {
      this.toast.error('Indica el nombre del tipo de unidad');
      return;
    }
    const payload = {
      nombre: this.typeForm.nombre.trim(),
      descripcion: this.typeForm.descripcion.trim(),
      activo: this.typeForm.activo,
    };
    this.saving = true;
    const request = this.editingType
      ? this.organizacionService.actualizarTipoUnidad(this.editingType.id, payload)
      : this.organizacionService.crearTipoUnidad(payload);
    request.subscribe({
      next: () => {
        this.toast.success(this.editingType ? 'Tipo actualizado' : 'Tipo creado');
        this.saving = false;
        this.newType();
        this.loadData();
      },
      error: () => {
        this.saving = false;
        this.toast.error('No se pudo guardar el tipo de unidad');
      },
    });
  }

  deleteType(type: any): void {
    if (this.unidades.some(unit => unit.tipo === type.id)) {
      this.toast.error('No se puede eliminar un tipo que ya tiene unidades');
      return;
    }
    if (!window.confirm(`¿Eliminar el tipo "${type.nombre}"?`)) return;
    this.organizacionService.eliminarTipoUnidad(type.id).subscribe({
      next: () => {
        this.toast.success('Tipo eliminado');
        this.loadData();
      },
      error: () => this.toast.error('No se pudo eliminar el tipo de unidad'),
    });
  }

  unitPath(unit: any): string {
    const path = [unit.nombre];
    let parentId = unit.unidad_padre;
    while (parentId) {
      const parent = this.unidades.find(candidate => candidate.id === parentId);
      if (!parent) break;
      path.unshift(parent.nombre);
      parentId = parent.unidad_padre;
    }
    return path.join(' / ');
  }

  private setUnitForm(unit: any): void {
    this.unitForm = {
      nombre: unit.nombre,
      descripcion: unit.descripcion ?? '',
      tipo: unit.tipo,
      unidad_padre: unit.unidad_padre,
      activa: unit.activa,
    };
  }

  private emptyUnitForm(): any {
    return { nombre: '', descripcion: '', tipo: '', unidad_padre: null, activa: true };
  }

  private emptyTypeForm(): any {
    return { nombre: '', descripcion: '', activo: true };
  }
}