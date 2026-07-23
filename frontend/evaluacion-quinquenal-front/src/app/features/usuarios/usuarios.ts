import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { forkJoin } from 'rxjs';
import { CrudTable } from '../../shared/components/CRUD/crud-table/crud-table';
import { SearchBar } from '../../shared/components/CRUD/search-bar/search-bar';
import { Pagination } from '../../shared/components/CRUD/pagination/pagination';
import { Modal } from '../../shared/components/CRUD/modal/modal';
import { AuthService } from '../auth/services/auth-service';
import { ToastrService } from 'ngx-toastr';
import { PermisosService } from '../../core/services/permisos.service';

@Component({
  selector: 'app-usuarios',
  imports: [CommonModule, FormsModule, CrudTable, SearchBar, Pagination, Modal],
  templateUrl: './usuarios.html',
  styleUrl: './usuarios.css',
})
export class Usuarios implements OnInit {
  columnas: string[] = ['Nombre de usuario','Nombre', 'Correo', 'Departamento', 'Rol', 'Estado'];

  datos: any[] = [];
  datosFiltrados: any[] = [];
  departamentos: any[] = [];
  roles: any[] = [];
  searchTerm = '';
  selectedState = 'Todos';

  showModal = false;
  selectedItem: any = null;

  usuarioFields: any[] = [
    { label: 'Nombre de usuario', name: 'username', type: 'text', placeholder: 'Username', defaultValue: ''},
    { label: 'Contraseña', name: 'password', type: 'password', placeholder: 'Dejar en blanco para no cambiar', defaultValue: '' },
    { label: 'Nombre', name: 'first_name', type: 'text', placeholder: 'Nombre del usuario', defaultValue: '' },
    { label: 'Correo', name: 'email', type: 'email', placeholder: 'correo@dominio.com', defaultValue: '' },
    { label: 'Departamento', name: 'departamento', type: 'select', options: [], defaultValue: '', allowClear: true, searchable: true },
    { label: 'Rol', name: 'rol', type: 'select', options: ['Administrador', 'Consulta', 'Responsable', 'Coordinador'], defaultValue: 'Consulta' },
    { label: 'Estado', name: 'estado', type: 'select', options: ['Activo', 'Inactivo'], defaultValue: 'Activo' }
  ];

  get puedeCrear(): boolean {
    return this.permisos.tieneAlgunPermiso(['auth.add_user']);
  }

  get ocultarAcciones(): string[] {
    if (this.permisos.tieneAlgunPermiso(['auth.change_user', 'auth.delete_user'])) {
      return [];
    }
    const ocultas: string[] = [];
    if (!this.permisos.tienePermiso('auth.change_user')) ocultas.push('edit', 'toggle');
    if (!this.permisos.tienePermiso('auth.delete_user')) ocultas.push('remove');
    return ocultas;
  }

  constructor(
    private authService: AuthService,
    private permisos: PermisosService,
    private toast: ToastrService
  ) {}

  ngOnInit(): void {
    this.loadUsuarios();
    this.loadDepartamentos();
    this.loadRoles();
  }

  openNew(): void {
    this.selectedItem = null;
    this.showModal = true;
  }

  openEdit(item: any): void {
    this.selectedItem = {
      ...item,
      username: item.username ?? '',
      first_name: item.first_name ?? item.username ?? '',
      departamento: item.departamentoId ?? item.departamento ?? '',
      rol: item.rol ?? 'Consulta',
      estado: item.is_active ? 'Activo' : 'Inactivo'
    };
    this.showModal = true;
  }

  loadUsuarios(): void {
    forkJoin([
      this.authService.listarUsuarios(),
      this.authService.listarPerfiles()
    ]).subscribe({
      next: ([usuarios, perfiles]) => {
        const profilesMap = new Map<number, any>();
        perfiles.forEach((perfil: any) => {
          if (perfil?.usuario !== undefined) {
            profilesMap.set(perfil.usuario, perfil);
          }
        });

        this.datos = usuarios.map((item: any) => {
          const profile = profilesMap.get(item.id);
          const departamentoId = profile?.departamento ?? item.departamento ?? '';

          return {
            ...item,
            username: item.username || '',
            first_name: item.first_name || item.username || '',
            departamento: profile?.departamento_nombre || item.departamento_nombre || item.departamento || '',
            departamentoId,
            rol: item.rol || 'Consulta',
            is_active: item.is_active ?? true,
            estado: item.is_active ? 'Activo' : 'Inactivo'
          };
        });
        this.applySearch();
      },
      error: (err) => {
        console.error('Error cargando usuarios', err);
        this.toast.error('No se pudieron cargar los usuarios');
      }
    });
  }

  loadDepartamentos(): void {
    this.authService.listarDepartamentos().subscribe({
      next: (data) => {
        this.departamentos = data;
        this.usuarioFields = this.usuarioFields.map(field => {
          if (field.name !== 'departamento') {
            return field;
          }

          return {
            ...field,
            options: this.departamentos.map((dep: any) => ({ value: dep.id, label: dep.nombre }))
          };
        });
      },
      error: (err) => {
        console.error('Error cargando departamentos', err);
      }
    });
  }

  loadRoles(): void {
    this.authService.listarRoles().subscribe({
      next: (data) => {
        this.roles = data.map((role: any) => ({
          value: role.name,
          label: role.name,
          id: role.id ?? role.pk
        }));
        this.usuarioFields = this.usuarioFields.map(field => {
          if (field.name !== 'rol') {
            return field;
          }

          return {
            ...field,
            options: this.roles
          };
        });
      },
      error: (err) => {
        console.error('Error cargando roles', err);
        this.roles = [
          { value: 'Administrador', label: 'Administrador', id: null },
          { value: 'Consulta', label: 'Consulta', id: null },
          { value: 'Responsable', label: 'Responsable', id: null },
          { value: 'Coordinador', label: 'Coordinador', id: null }
        ];
      }
    });
  }

  onSearch(term: string): void {
    this.searchTerm = term;
    this.applySearch();
  }

  onStateChange(state: string): void {
    this.selectedState = state;
    this.applySearch();
  }

  private applySearch(): void {
    const normalizedTerm = this.searchTerm.toLowerCase().trim();

    this.datosFiltrados = this.datos.filter((item: any) => {
      const searchable = `${item.first_name ?? ''} ${item.username ?? ''} ${item.email ?? ''} ${item.departamento ?? ''} ${item.rol ?? ''}`.toLowerCase();
      const matchesSearch = !normalizedTerm || searchable.includes(normalizedTerm);
      const matchesState = this.selectedState === 'Todos'
        || (this.selectedState === 'Activos' && item.is_active)
        || (this.selectedState === 'Inactivos' && !item.is_active);

      return matchesSearch && matchesState;
    });
  }

  onModalClose(): void {
    this.showModal = false;
    this.selectedItem = null;
  }

  private syncPerfilUsuario(userId: any, departamento: any, onSuccess: () => void, onError: (err: any) => void): void {
    this.authService.listarPerfiles().subscribe({
      next: (perfiles) => {
        const profile = perfiles.find((perfil: any) => perfil.usuario === userId || perfil.usuario?.id === userId);

        if (profile && profile.id) {
          this.authService.actualizarPerfil(profile.id, { departamento: departamento || null }).subscribe({
            next: () => onSuccess(),
            error: (err) => {
              console.error('Error actualizando perfil de usuario', err);
              onError(err);
            }
          });
        } else {
          this.authService.crearPerfil({ usuario: userId, departamento: departamento || null }).subscribe({
            next: () => onSuccess(),
            error: (err) => {
              console.error('Error creando perfil de usuario', err);
              onError(err);
            }
          });
        }
      },
      error: (err) => {
        console.error('Error cargando perfiles', err);
        onError(err);
      }
    });
  }

  onModalSave(saved: any): void {
    const selectedRole = this.roles.find(role => role.value === saved.rol);
    const payload: any = {
      username: saved.username,
      first_name: saved.first_name,
      email: saved.email,
      is_active: saved.estado === 'Activo'
    };

    if (saved.password) {
      payload.password = saved.password;
    }

    if (selectedRole && selectedRole.id !== null) {
      payload.group_ids = [selectedRole.id];
    }

    if (this.selectedItem && this.selectedItem.id) {
      this.authService.actualizarUsuario(this.selectedItem.id, payload).subscribe({
        next: () => {
          this.syncPerfilUsuario(this.selectedItem.id, saved.departamento, () => {
            this.toast.success('Usuario actualizado correctamente');
            this.loadUsuarios();
            this.onModalClose();
          }, (err) => {
            this.toast.error('Error al guardar el departamento del usuario');
          });
        },
        error: (err) => {
          console.error('Error actualizando usuario', err);
          this.toast.error('No se pudo actualizar el usuario');
        }
      });
    } else {
      this.authService.crearUsuario(payload).subscribe({
        next: (createdUser: any) => {
          const finishCreation = () => {
            this.toast.success('Usuario creado correctamente');
            this.loadUsuarios();
            this.onModalClose();
          };

          if (createdUser?.id && saved.departamento) {
            this.authService.crearPerfil({ usuario: createdUser.id, departamento: saved.departamento }).subscribe({
              next: () => finishCreation(),
              error: (err) => {
                console.error('Error creando perfil de usuario', err);
                this.toast.error('Usuario creado, pero falló asignar el departamento');
                finishCreation();
              }
            });
          } else {
            finishCreation();
          }
        },
        error: (err) => {
          console.error('Error creando usuario', err);
          this.toast.error('No se pudo crear el usuario');
        }
      });
    }
  }

  onRemove(item: any): void {
    if (!item.id) {
      return;
    }

    this.authService.eliminarUsuario(item.id).subscribe({
      next: () => {
        this.toast.success('Usuario eliminado');
        this.loadUsuarios();
      },
      error: (err) => {
        console.error('Error eliminando usuario', err);
        this.toast.error('No se pudo eliminar el usuario');
      }
    });
  }

  onToggleEstado(item: any): void {
    if (!item.id) {
      return;
    }

    const nuevoEstado = !item.is_active;

    this.authService.actualizarUsuario(item.id, { is_active: nuevoEstado }).subscribe({
      next: () => {
        item.is_active = nuevoEstado;
        item.estado = nuevoEstado ? 'Activo' : 'Inactivo';
        this.toast.success(`Usuario ${nuevoEstado ? 'activado' : 'desactivado'} correctamente`);
        this.applySearch();
      },
      error: (err) => {
        console.error('Error cambiando estado de usuario', err);
        this.toast.error('No se pudo cambiar el estado del usuario');
      }
    });
  }
}
