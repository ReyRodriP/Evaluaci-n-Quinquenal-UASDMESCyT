import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { CrudTable } from '../../shared/components/CRUD/crud-table/crud-table';
import { SearchBar } from '../../shared/components/CRUD/search-bar/search-bar';
import { Modal } from '../../shared/components/CRUD/modal/modal';
import { AuthService } from '../auth/services/auth-service';
import { ToastrService } from 'ngx-toastr';

@Component({
  selector: 'app-roles',
  imports: [CommonModule, FormsModule, CrudTable, SearchBar, Modal],
  templateUrl: './roles.html',
  styleUrl: './roles.css',
})
export class Roles implements OnInit {
  columnas: string[] = ['Nombre', 'Permisos'];
  roles: any[] = [];
  rolesFiltrados: any[] = [];
  permisos: any[] = [];
  searchTerm = '';
  showModal = false;
  selectedItem: any = null;

  roleFields: any[] = [
    {
      label: 'Permisos',
      name: 'permission_ids',
      type: 'checkboxgroup',
      options: [],
      defaultValue: []
    }
  ];

  constructor(
    private authService: AuthService,
    private toast: ToastrService
  ) {}

  ngOnInit(): void {
    this.loadPermisos();
    this.loadRoles();
  }

  private normalizeListResponse(data: any): any[] {
    if (Array.isArray(data)) {
      return data;
    }
    if (data?.results && Array.isArray(data.results)) {
      return data.results;
    }
    if (data?.data && Array.isArray(data.data)) {
      return data.data;
    }
    return [];
  }

  loadPermisos(): void {
    this.authService.listarPermisos().subscribe({
      next: (data) => {
        const normalized = this.normalizeListResponse(data);
        this.permisos = normalized.map((perm: any) => ({ value: perm.id, label: perm.name }));
        this.roleFields = this.roleFields.map(field => {
          if (field.name !== 'permission_ids') {
            return field;
          }
          return {
            ...field,
            options: this.permisos
          };
        });
      },
      error: (err) => {
        console.error('Error cargando permisos', err);
        if (err?.status !== 403) {
          this.toast.error('No se pudieron cargar los permisos');
        }
      }
    });
  }

  loadRoles(): void {
    this.authService.listarRoles().subscribe({
      next: (data) => {
        const normalized = this.normalizeListResponse(data);
        this.roles = normalized.map((role: any) => ({
          ...role,
          id: role.id ?? role.pk,
          permisos: (role.permissions || []).map((perm: any) => perm.name).join(', '),
          permission_ids: (role.permissions || []).map((perm: any) => perm.id)
        }));
        this.applySearch();

        if (!this.roles.length) {
          this.toast.info('No se encontraron roles registrados en el sistema.');
        }
      },
      error: (err) => {
        console.error('Error cargando roles', err);
        this.toast.error('No se pudieron cargar los roles desde el servidor');
        this.roles = [];
        this.rolesFiltrados = [];
      }
    });
  }

  onSearch(term: string): void {
    this.searchTerm = term;
    this.applySearch();
  }

  applySearch(): void {
    const normalizedTerm = this.searchTerm.toLowerCase().trim();
    if (!normalizedTerm) {
      this.rolesFiltrados = [...this.roles];
      return;
    }

    this.rolesFiltrados = this.roles.filter((role: any) => {
      const nameMatch = (role.name || '').toLowerCase().includes(normalizedTerm);
      const permissionsMatch = (role.permisos || '').toLowerCase().includes(normalizedTerm);
      return nameMatch || permissionsMatch;
    });
  }

  openEdit(item: any): void {
    const roleId = item?.id ?? item?.pk;
    if (roleId == null) {
      this.toast.warning('No se puede editar este rol porque no tiene identificador válido.');
      return;
    }

    this.selectedItem = {
      ...item,
      id: roleId,
      permission_ids: item.permission_ids || []
    };
    this.showModal = true;
  }

  onModalClose(): void {
    this.showModal = false;
    this.selectedItem = null;
  }

  onModalSave(saved: any): void {
    if (!this.selectedItem || this.selectedItem.id == null) {
      this.toast.error('No se pudo identificar el rol seleccionado. Verifique que los roles carguen correctamente desde el servidor.');
      return;
    }

    const payload = {
      permission_ids: Array.isArray(saved.permission_ids) ? saved.permission_ids : []
    };

    this.authService.actualizarRol(this.selectedItem.id, payload).subscribe({
      next: () => {
        this.toast.success('Permisos del rol actualizados correctamente');
        this.loadRoles();
        this.onModalClose();
      },
      error: (err) => {
        console.error('Error actualizando permisos del rol', err);
        this.toast.error('No se pudo actualizar los permisos del rol');
      }
    });
  }
}
