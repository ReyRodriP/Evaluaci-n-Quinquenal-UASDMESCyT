import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { catchError, forkJoin, of, throwError } from 'rxjs';
import { CrudTable } from '../../shared/components/CRUD/crud-table/crud-table';
import { SearchBar } from '../../shared/components/CRUD/search-bar/search-bar';
import { Pagination } from '../../shared/components/CRUD/pagination/pagination';
import { Modal } from '../../shared/components/CRUD/modal/modal';
import { EvaluacionService } from '../../core/services/evaluacion.service';
import { OrganizacionService } from '../../core/services/organizacion.service';
import { ToastrService } from 'ngx-toastr';
import { PermisosService } from '../../core/services/permisos.service';
import { NuevaAsignacionMarco } from './nueva-asignacion-marco/nueva-asignacion-marco';

@Component({
  selector: 'app-asignaciones',
  imports: [CommonModule, FormsModule, CrudTable, SearchBar, Pagination, Modal, RouterLink, NuevaAsignacionMarco],
  templateUrl: './asignaciones.html',
  styleUrl: './asignaciones.css',
})
export class Asignaciones implements OnInit {
  columnas: string[] = ['Unidad responsable', 'Indicadores', 'Período', 'Estado'];

  datos: any[] = [];
  datosFiltrados: any[] = [];
  datosPaginados: any[] = [];
  searchTerm = '';
  selectedState = 'Todos';
  currentPage = 1;
  pageSize = 10;
  unidades: any[] = [];
  periodos: any[] = [];
  periodoActivo: any = null;
  periodoSeleccionadoId = '';

  showModal: boolean = false;
  showMarco = false;
  selectedItem: any = null;

  asignacionFields: any[] = [
    { label: 'Unidad responsable', name: 'unidad_responsable', type: 'select', options: [], defaultValue: '' },
    { label: 'Período', name: 'periodo', type: 'select', options: [], defaultValue: '' },
    { label: 'Estado', name: 'estado', type: 'select', options: [
      { value: 'pendiente', label: 'Pendiente' },
      { value: 'en_progreso', label: 'En progreso' },
      { value: 'completado', label: 'Completado' },
      { value: 'aprobado', label: 'Aprobado' },
      { value: 'rechazado', label: 'Rechazado' }
    ], defaultValue: 'pendiente' }
  ];

  get puedeCrear(): boolean {
    return this.periodoSeleccionadoEsActivo && this.permisos.tieneAlgunPermiso(['evaluation.add_asignacion']);
  }

  get puedeCrearMarco(): boolean {
    return this.puedeCrear && (this.permisos.esSuperuser || this.permisos.tieneGrupo('Administrador General') || this.permisos.tieneGrupo('Coordinador Quinquenal'));
  }

  abrirMarco(): void { if (this.puedeCrearMarco) { this.selectedItem = null; this.showModal = false; this.showMarco = true; } }

  asignacionMarcoCreada(asignacion: any): void {
    this.showMarco = false;
    this.toast.success('Asignación del marco creada correctamente');
    void this.router.navigate(['/asignaciones', asignacion.id, 'detalle'], { queryParams: { periodo: asignacion.periodo } });
  }

  get ocultarAcciones(): string[] {
    if (!this.periodoSeleccionadoEsActivo) return ['edit', 'toggle', 'remove'];
    const ocultas = ['toggle'];
    if (!this.permisos.tieneAlgunPermiso(['evaluation.change_asignacion'])) ocultas.push('edit');
    if (!this.permisos.tieneAlgunPermiso(['evaluation.delete_asignacion'])) ocultas.push('remove');
    return ocultas;
  }

  constructor(
    private evaluacionService: EvaluacionService,
    private organizacionService: OrganizacionService,
    private permisos: PermisosService,
    private toast: ToastrService,
    private route: ActivatedRoute,
    private router: Router
  ) {}

  ngOnInit() {
    this.loadUnidades();
    this.loadPeriodos();
  }

  get periodoSeleccionadoEsActivo(): boolean {
    return this.periodos.some((periodo) =>
      String(periodo.id) === this.periodoSeleccionadoId && periodo.activo
    );
  }

  openNew() {
    this.abrirMarco();
  }

  openEdit(item: any) {
    if (item.tipo_origen === 'marco') {
      void this.router.navigate(['/asignaciones', item.id, 'detalle'], { queryParams: { periodo: this.periodoSeleccionadoId } });
      return;
    }
    if (!item.id || !this.periodoSeleccionadoEsActivo || !this.permisos.tieneAlgunPermiso(['evaluation.change_asignacion'])) return;
    this.showMarco = false;
    const indicadoresIds = Array.isArray(item.indicadores)
      ? item.indicadores.map((indicador: any) => indicador.id ?? indicador.value ?? indicador)
      : [item.indicadorId ?? item.indicador];

    this.selectedItem = {
      ...item,
      indicador: indicadoresIds,
      asignaciones: item.asignaciones?.length ? item.asignaciones : [{ id: item.id, indicador: item.indicadorId ?? item.indicador }],
      unidad_responsable: item.unidadResponsableId ?? item.unidad_responsable,
      periodo: item.periodoId ?? item.periodo,
      estado: (item.estadoRaw ?? item.estado) || item.estado_display || 'pendiente',
    };
    this.showModal = true;
  }

  loadUnidades() {
    this.organizacionService.listarUnidadesOrganizacionales().subscribe({
      next: (data) => {
        this.unidades = data;
        this.asignacionFields = this.asignacionFields.map(field => {
          if (field.name !== 'unidad_responsable') {
            return field;
          }

          return {
            ...field,
            options: this.unidades.map((unidad: any) => ({ value: unidad.id, label: `${this.unitPath(unidad)} · ${unidad.tipo_nombre}` }))
          };
        });
      },
      error: (err) => {
        console.error('Error cargando unidades organizacionales', err);
        this.toast.error('No se pudieron cargar las unidades organizacionales');
      }
    });
  }

  private unitPath(unit: any): string {
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

  loadPeriodos() {
    forkJoin({
      periodos: this.evaluacionService.listarPeriodos().pipe(catchError(() => of([]))),
      activo: this.evaluacionService.periodoActivo().pipe(
        catchError((error) => error.status === 404 ? of(null) : throwError(() => error))
      ),
    }).subscribe({
      next: ({ periodos, activo }) => {
        this.periodos = periodos;
        this.periodoActivo = activo;
        const periodoUrl = this.route.snapshot.queryParamMap.get('periodo');
        const solicitado = periodos.find((item: any) => String(item.id) === periodoUrl);
        const seleccionSolicitadaValida = periodoUrl && (solicitado || !periodos.length);
        this.periodoSeleccionadoId = String(seleccionSolicitadaValida ? periodoUrl : activo?.id ?? '');
        if (activo && !this.periodos.some((item: any) => Number(item.id) === Number(activo.id))) {
          this.periodos = [...this.periodos, activo];
        }
        if (this.periodoSeleccionadoId !== periodoUrl) this.actualizarPeriodoUrl();
        this.asignacionFields = this.asignacionFields.map(field => {
          if (field.name !== 'periodo') {
            return field;
          }

          return {
            ...field,
            options: this.periodos.filter((periodo: any) => periodo.activo)
              .map((periodo: any) => ({ value: periodo.id, label: periodo.nombre }))
          };
        });
        this.loadAsignaciones();
      },
      error: (err) => {
        console.error('Error cargando períodos', err);
        this.toast.error('No se pudieron cargar los períodos');
      }
    });
  }

  loadAsignaciones() {
    if (!this.periodoSeleccionadoId) {
      this.datos = [];
      this.applySearch();
      return;
    }
    this.evaluacionService.listarAsignaciones(this.periodoSeleccionadoId).subscribe({
      next: (data) => {
        const grouped = data.reduce((acc: any, item: any) => {
          const tipoOrigen = item.tipo_origen ?? 'operativo';
          const key = `${tipoOrigen}_${item.unidad_responsable}_${item.periodo}_${item.estado}${tipoOrigen === 'marco' ? '_' + item.id : ''}`;
          const indicadorNombre = item.indicador_nombre || '';
          const indicadorId = item.indicador;

          if (!acc[key]) {
            acc[key] = {
              ids: [],
              asignaciones: [],
              id: item.id,
              tipo_origen: tipoOrigen,
              unidad_responsable: item.unidad_responsable_nombre || '',
              unidadResponsableId: item.unidad_responsable,
              periodo: item.periodo_nombre || '',
              periodo_nombre: item.periodo_nombre || '',
              periodoId: item.periodo,
              estado: item.estado_display || item.estado || '',
              estadoRaw: item.estado || 'pendiente',
              indicadores: [],
            };
          }

          acc[key].ids.push(item.id);
          acc[key].asignaciones.push({ id: item.id, indicador: indicadorId, indicador_marco: item.indicador_marco ?? null });
          acc[key].indicadores.push({ id: indicadorId, indicador_marco: item.indicador_marco ?? null, nombre: indicadorNombre });
          return acc;
        }, {} as Record<string, any>);

        this.datos = Object.values(grouped);
        this.applySearch();
      },
      error: (err) => {
        console.error('Error cargando asignaciones', err);
        this.toast.error('No se pudieron cargar las asignaciones');
      }
    });
  }

  onPeriodoChange(periodoId: string): void {
    this.showMarco = false;
    this.showModal = false;
    this.periodoSeleccionadoId = periodoId;
    this.actualizarPeriodoUrl();
    this.loadAsignaciones();
  }

  private actualizarPeriodoUrl(): void {
    void this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { periodo: this.periodoSeleccionadoId || null },
      queryParamsHandling: 'merge',
      replaceUrl: true,
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
      const hayCoincidencia = (item.unidad_responsable ?? '').toLowerCase().includes(normalizedTerm)
        || (item.periodo ?? '').toLowerCase().includes(normalizedTerm)
        || (item.indicadores ?? []).some((indicador: any) => `${indicador.nombre ?? ''}`.toLowerCase().includes(normalizedTerm));
      const matchesSearch = !normalizedTerm || hayCoincidencia;
      const matchesState = this.selectedState === 'Todos'
        || (this.selectedState === item.estadoRaw)
        || (this.selectedState === item.estado);
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
    if (!this.selectedItem?.id || this.selectedItem.tipo_origen === 'marco'
      || !this.permisos.tieneAlgunPermiso(['evaluation.change_asignacion'])) return;
    if (!this.periodoSeleccionadoEsActivo) {
      this.toast.error('No se pueden modificar asignaciones de un período finalizado');
      return;
    }
    const asignaciones = this.selectedItem.asignaciones;
    if (!Array.isArray(asignaciones) || !asignaciones.length || asignaciones.some((a: any) => !a.id || !a.indicador)) return;
    if (!saved.unidad_responsable || !saved.periodo) {
      this.toast.error('Complete todos los campos requeridos');
      return;
    }

    const payloadBase = {
      unidad_responsable: saved.unidad_responsable,
      periodo: saved.periodo,
      estado: saved.estado,
    };

    forkJoin(asignaciones.map((asignacion: any) => this.evaluacionService.actualizarAsignacion(asignacion.id, {
      ...payloadBase, indicador: asignacion.indicador,
    }))).subscribe({
      next: () => {
        this.toast.success('Asignaciones existentes actualizadas correctamente');
        this.loadAsignaciones();
        this.onModalClose();
      },
      error: (err) => {
        console.error('Error actualizando asignaciones', err);
        this.toast.error('No se pudieron actualizar todas las asignaciones existentes');
        this.loadAsignaciones();
      },
    });
  }

  onRemove(item: any) {
    if (!item.id) {
      return;
    }

    this.evaluacionService.eliminarAsignacion(item.id).subscribe({
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
}
