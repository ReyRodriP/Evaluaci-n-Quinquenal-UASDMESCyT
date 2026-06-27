import { Component, OnInit } from '@angular/core';
import { forkJoin } from 'rxjs';
import { CrudTable } from '../../shared/components/CRUD/crud-table/crud-table';
import { SearchBar } from '../../shared/components/CRUD/search-bar/search-bar';
import { Pagination } from '../../shared/components/CRUD/pagination/pagination';
import { Modal } from '../../shared/components/CRUD/modal/modal';
import { AuthService } from '../../core/services/auth.service';
import { ToastrService } from 'ngx-toastr';

@Component({
  selector: 'app-asignaciones',
  imports: [CrudTable, SearchBar, Pagination, Modal],
  templateUrl: './asignaciones.html',
  styleUrl: './asignaciones.css',
})
export class Asignaciones implements OnInit {
  columnas: string[] = ['Departamento', 'Indicadores', 'Período', 'Estado'];

  datos: any[] = [];
  indicadores: any[] = [];
  departamentos: any[] = [];
  periodos: any[] = [];

  showModal: boolean = false;
  selectedItem: any = null;

  asignacionFields: any[] = [
    { label: 'Departamento', name: 'departamento', type: 'select', options: [], defaultValue: '' },
    { label: 'Indicadores', name: 'indicador', type: 'checkboxgroup', options: [], defaultValue: [] },
    { label: 'Período', name: 'periodo', type: 'select', options: [], defaultValue: '' },
    { label: 'Estado', name: 'estado', type: 'select', options: [
      { value: 'pendiente', label: 'Pendiente' },
      { value: 'en_progreso', label: 'En progreso' },
      { value: 'completado', label: 'Completado' },
      { value: 'aprobado', label: 'Aprobado' },
      { value: 'rechazado', label: 'Rechazado' }
    ], defaultValue: 'pendiente' }
  ];

  constructor(
    private authService: AuthService,
    private toast: ToastrService
  ) {}

  ngOnInit() {
    this.loadIndicadores();
    this.loadDepartamentos();
    this.loadPeriodos();
    this.loadAsignaciones();
  }

  openNew() {
    this.selectedItem = null;
    this.showModal = true;
  }

  openEdit(item: any) {
    const indicadoresIds = Array.isArray(item.indicadores)
      ? item.indicadores.map((indicador: any) => indicador.id ?? indicador.value ?? indicador)
      : [item.indicadorId ?? item.indicador];

    this.selectedItem = {
      ...item,
      indicador: indicadoresIds,
      asignaciones: item.asignaciones ?? [],
      departamento: item.departamentoId ?? item.departamento,
      periodo: item.periodoId ?? item.periodo,
      estado: (item.estadoRaw ?? item.estado) || item.estado_display || 'pendiente',
    };
    this.showModal = true;
  }

  loadIndicadores() {
    this.authService.listarIndicadores().subscribe({
      next: (data) => {
        this.indicadores = data;
        this.asignacionFields = this.asignacionFields.map(field => {
          if (field.name !== 'indicador') {
            return field;
          }

          return {
            ...field,
            options: this.indicadores.map((indicador: any) => ({ value: indicador.id, label: indicador.nombre }))
          };
        });
      },
      error: (err) => {
        console.error('Error cargando indicadores', err);
        this.toast.error('No se pudieron cargar los indicadores');
      }
    });
  }

  loadDepartamentos() {
    this.authService.listarDepartamentos().subscribe({
      next: (data) => {
        this.departamentos = data;
        this.asignacionFields = this.asignacionFields.map(field => {
          if (field.name !== 'departamento') {
            return field;
          }

          return {
            ...field,
            options: this.departamentos.map((departamento: any) => ({ value: departamento.id, label: departamento.nombre }))
          };
        });
      },
      error: (err) => {
        console.error('Error cargando departamentos', err);
        this.toast.error('No se pudieron cargar los departamentos');
      }
    });
  }

  loadPeriodos() {
    this.authService.listarPeriodos().subscribe({
      next: (data) => {
        this.periodos = data;
        this.asignacionFields = this.asignacionFields.map(field => {
          if (field.name !== 'periodo') {
            return field;
          }

          return {
            ...field,
            options: this.periodos.map((periodo: any) => ({ value: periodo.id, label: periodo.nombre }))
          };
        });
      },
      error: (err) => {
        console.error('Error cargando periodos', err);
        this.toast.error('No se pudieron cargar los periodos');
      }
    });
  }

  loadAsignaciones() {
    this.authService.listarAsignaciones().subscribe({
      next: (data) => {
        const grouped = data.reduce((acc: any, item: any) => {
          const key = `${item.departamento}_${item.periodo}_${item.estado}`;
          const indicadorNombre = item.indicador_nombre || '';
          const indicadorId = item.indicador;

          if (!acc[key]) {
            acc[key] = {
              ids: [],
              asignaciones: [],
              id: item.id,
              departamento: item.departamento_nombre || '',
              departamentoId: item.departamento,
              periodo: item.periodo_nombre || '',
              periodo_nombre: item.periodo_nombre || '',
              periodoId: item.periodo,
              estado: item.estado_display || item.estado || '',
              estadoRaw: item.estado || 'pendiente',
              indicadores: [],
            };
          }

          acc[key].ids.push(item.id);
          acc[key].asignaciones.push({ id: item.id, indicador: indicadorId });
          acc[key].indicadores.push({ id: indicadorId, nombre: indicadorNombre });
          return acc;
        }, {} as Record<string, any>);

        this.datos = Object.values(grouped);
      },
      error: (err) => {
        console.error('Error cargando asignaciones', err);
        this.toast.error('No se pudieron cargar las asignaciones');
      }
    });
  }

  onModalClose() {
    this.showModal = false;
    this.selectedItem = null;
  }

  onModalSave(saved: any) {
    const selectedIndicadores = Array.isArray(saved.indicador) ? saved.indicador : [saved.indicador];
    if (!selectedIndicadores.length || !saved.departamento || !saved.periodo) {
      this.toast.error('Complete todos los campos requeridos');
      return;
    }

    const payloadBase = {
      departamento: saved.departamento,
      periodo: saved.periodo,
      estado: saved.estado,
    };

    const crearAsignaciones = (indicadores: any[]) => {
      const requests = indicadores.map((indicador: any) => this.authService.crearAsignacion({
        ...payloadBase,
        indicador,
      }));
      return forkJoin(requests);
    };

    if (this.selectedItem && Array.isArray(this.selectedItem.asignaciones) && this.selectedItem.asignaciones.length) {
      const existingAsignaciones = this.selectedItem.asignaciones;
      const existingIndicadores = existingAsignaciones.map((a: any) => a.indicador);
      const addedIndicadores = selectedIndicadores.filter((id: any) => !existingIndicadores.includes(id));
      const removedAsignaciones = existingAsignaciones.filter((a: any) => !selectedIndicadores.includes(a.indicador));
      const primaryIndicador = selectedIndicadores[0];
      const updatePayload = {
        ...payloadBase,
        indicador: primaryIndicador,
      };

      this.authService.actualizarAsignacion(existingAsignaciones[0].id, updatePayload).subscribe({
        next: () => {
          const requests: any[] = [];

          if (addedIndicadores.length) {
            addedIndicadores.forEach((indicador: any) => {
              requests.push(this.authService.crearAsignacion({ ...payloadBase, indicador }));
            });
          }

          if (removedAsignaciones.length) {
            removedAsignaciones.forEach((asignacion: any) => {
              requests.push(this.authService.eliminarAsignacion(asignacion.id));
            });
          }

          if (requests.length) {
            forkJoin(requests).subscribe({
              next: () => {
                this.toast.success('Asignación actualizada correctamente');
                this.loadAsignaciones();
                this.onModalClose();
              },
              error: (err) => {
                console.error('Error actualizando asignaciones', err);
                this.toast.error('Error al actualizar las asignaciones');
              }
            });
          } else {
            this.toast.success('Asignación actualizada correctamente');
            this.loadAsignaciones();
            this.onModalClose();
          }
        },
        error: (err) => {
          console.error('Error actualizando asignación', err);
          this.toast.error('Error al actualizar la asignación');
        }
      });
    } else {
      crearAsignaciones(selectedIndicadores).subscribe({
        next: () => {
          this.toast.success('Asignación(es) creada(s) exitosamente');
          this.loadAsignaciones();
          this.onModalClose();
        },
        error: (err) => {
          console.error('Error creando asignaciones', err);
          this.toast.error('Error al crear las asignaciones');
        }
      });
    }
  }

  onRemove(item: any) {
    if (!item.id) {
      return;
    }

    this.authService.eliminarAsignacion(item.id).subscribe({
      next: () => {
        this.toast.success('Asignación eliminada');
        this.loadAsignaciones();
      },
      error: (err) => {
        console.error('Error eliminando asignación', err);
        this.toast.error('No se pudo eliminar la asignación');
      }
    });
  }

  onToggleEstado(item: any) {
    if (!item.id) {
      return;
    }

    const nuevoEstado = item.estadoRaw === 'aprobado' ? 'pendiente' : 'aprobado';

    this.authService.patchAsignacion(item.id, { estado: nuevoEstado }).subscribe({
      next: () => {
        this.toast.success(`Asignación marcada como ${nuevoEstado}`);
        this.loadAsignaciones();
      },
      error: (err) => {
        console.error('Error cambiando estado de asignación', err);
        this.toast.error('No se pudo cambiar el estado de la asignación');
      }
    });
  }
}
