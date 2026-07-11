import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
<<<<<<< HEAD
import { forkJoin } from 'rxjs';
import { CrudTable } from '../../shared/components/CRUD/crud-table/crud-table';
import { SearchBar } from '../../shared/components/CRUD/search-bar/search-bar';
import { Pagination } from '../../shared/components/CRUD/pagination/pagination';
import { Modal } from '../../shared/components/CRUD/modal/modal';
import { AuthService } from '../auth/services/auth-service';
=======
import { ApiService } from '../../core/services/api.service';
import { Usuario } from '../../core/models/user.model';
>>>>>>> Ramon_Paulino_Gil_100345706
import { ToastrService } from 'ngx-toastr';

@Component({
  selector: 'app-usuarios',
<<<<<<< HEAD
  imports: [CommonModule, FormsModule, CrudTable, SearchBar, Pagination, Modal],
=======
  standalone: true,
  imports: [CommonModule, FormsModule],
>>>>>>> Ramon_Paulino_Gil_100345706
  templateUrl: './usuarios.html',
  styleUrl: './usuarios.css',
})
export class Usuarios implements OnInit {
<<<<<<< HEAD
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
    { label: 'Departamento', name: 'departamento', type: 'select', options: [], defaultValue: '' },
    { label: 'Rol', name: 'rol', type: 'select', options: ['Administrador', 'Consulta', 'Responsable', 'Coordinador'], defaultValue: 'Consulta' },
    { label: 'Estado', name: 'estado', type: 'select', options: ['Activo', 'Inactivo'], defaultValue: 'Activo' }
  ];

  constructor(
    private authService: AuthService,
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
    if (!departamento) {
      onSuccess();
      return;
    }

    this.authService.listarPerfiles().subscribe({
      next: (perfiles) => {
        const profile = perfiles.find((perfil: any) => perfil.usuario === userId || perfil.usuario?.id === userId);

        if (profile && profile.id) {
          this.authService.actualizarPerfil(profile.id, { departamento }).subscribe({
            next: () => onSuccess(),
            error: (err) => {
              console.error('Error actualizando perfil de usuario', err);
              onError(err);
            }
          });
        } else {
          this.authService.crearPerfil({ usuario: userId, departamento }).subscribe({
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
=======
  usuarios: Usuario[] = [];
  showModal = false;
  editMode = false;
  form: any = { username: '', email: '', first_name: '', last_name: '', telefono: '', password: '' };

  constructor(private api: ApiService, private toast: ToastrService) {}

  ngOnInit() {
    this.api.getUsuarios().subscribe(data => this.usuarios = data);
  }

  abrirModal(usuario?: Usuario) {
    if (usuario) {
      this.form = { ...usuario, password: '' };
      this.editMode = true;
    } else {
      this.form = { username: '', email: '', first_name: '', last_name: '', telefono: '', password: '' };
      this.editMode = false;
    }
    this.showModal = true;
  }

  guardar() {
    if (this.editMode) {
      const data: any = {
        username: this.form.username,
        email: this.form.email,
        first_name: this.form.first_name,
        last_name: this.form.last_name,
        telefono: this.form.telefono,
        is_active: this.form.is_active
      };
      this.api.updateUsuario(this.form.id, data).subscribe(() => {
        this.toast.success('Usuario actualizado');
        this.ngOnInit();
        this.showModal = false;
      });
    }
  }
>>>>>>> Ramon_Paulino_Gil_100345706
}
