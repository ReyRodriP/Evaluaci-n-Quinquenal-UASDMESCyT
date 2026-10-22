import { Injectable } from '@angular/core';
import { Observable, catchError, forkJoin, map, of } from 'rxjs';
import { switchMap } from 'rxjs/operators';
import { RespuestaPaginada } from '../models/vinculacion.model';
import {
  ETIQUETAS_REVISION,
  MAX_PAGINAS_CORRESPONDENCIAS,
  MAX_PAGINAS_LISTADO,
  EstadoCorrespondenciaFila,
  FilaSeguimiento,
  ResultadoPaginas,
  ResultadoSeguimiento,
  calcularMetricas,
} from '../models/seguimiento.model';
import { EvaluacionService } from './evaluacion.service';
import { EvidenciasService } from './evidencias.service';
import { VinculacionService } from './vinculacion.service';

interface CorrespondenciasPaginadas {
  confirmadas: ResultadoPaginas<any>;
  propuestas: ResultadoPaginas<any>;
}

interface ContextoCorrespondencias {
  confirmados: Set<number>;
  pendientes: Set<number>;
  preferidas: Map<number, { codigoDestino: string; versionMarco: string }>;
  correspondenciasDisponibles: boolean;
}

/**
 * @brief Carga acotada y construcción del resumen de seguimiento.
 * @details Implementación única de la obtención de datos y del cálculo de
 * métricas del seguimiento; la utilizan la pantalla de Seguimiento y el
 * Dashboard para evitar lógica duplicada.
 */
@Injectable({
  providedIn: 'root',
})
export class SeguimientoResumenService {
  private cache: {
    asignaciones: any[];
    evidencias: any[];
    indicadores: any[];
    avisosTruncado: string[];
  } | null = null;

  constructor(
    private evaluacionService: EvaluacionService,
    private evidenciasService: EvidenciasService,
    private vinculacionService: VinculacionService
  ) {}

  obtenerPaginas<T>(
    pagina$: (page: number) => Observable<RespuestaPaginada<T>>,
    maxPaginas: number,
    page = 1,
    acumulado: T[] = []
  ): Observable<ResultadoPaginas<T>> {
    return pagina$(page).pipe(
      switchMap((envoltura) => {
        const resultados = Array.isArray(envoltura?.results) ? envoltura.results : [];
        const total =
          typeof envoltura?.count === 'number' ? envoltura.count : acumulado.length + resultados.length;
        const cupo = Math.max(0, total - acumulado.length);
        const items = [...acumulado, ...resultados.slice(0, cupo)];
        const haySiguiente = Boolean(envoltura?.next);
        const completo = !haySiguiente || resultados.length === 0 || items.length >= total;
        if (completo || page >= maxPaginas) {
          return of({ items, total, truncado: total > items.length });
        }
        return this.obtenerPaginas(pagina$, maxPaginas, page + 1, items);
      })
    );
  }

  cargar(periodoId: string): Observable<ResultadoSeguimiento> {
    return forkJoin({
      asignaciones: this.obtenerPaginas(
        (page) => this.evaluacionService.listarAsignacionesPagina(periodoId, page),
        MAX_PAGINAS_LISTADO
      ),
      evidencias: this.obtenerPaginas(
        (page) => this.evidenciasService.listarEvidenciasPagina(periodoId, page),
        MAX_PAGINAS_LISTADO
      ),
      indicadores: this.obtenerPaginas(
        (page) => this.evaluacionService.listarIndicadoresPagina(page),
        MAX_PAGINAS_LISTADO
      ),
      correspondencias: this.cargarCorrespondencias(),
    }).pipe(
      map(({ asignaciones, evidencias, indicadores, correspondencias }) => {
        const avisosTruncado: string[] = [];
        if (asignaciones.truncado) {
          avisosTruncado.push(
            `Asignaciones: se obtuvieron ${asignaciones.items.length} de ${asignaciones.total}; las métricas reflejan solo esas filas.`
          );
        }
        if (evidencias.truncado) {
          avisosTruncado.push(
            `Evidencias: se obtuvieron ${evidencias.items.length} de ${evidencias.total}; algunas asignaciones pueden mostrarse sin evidencia.`
          );
        }
        if (indicadores.truncado) {
          avisosTruncado.push(
            `Indicadores: se obtuvieron ${indicadores.items.length} de ${indicadores.total}; el criterio operativo puede faltar en algunas filas.`
          );
        }
        this.cache = {
          asignaciones: asignaciones.items,
          evidencias: evidencias.items,
          indicadores: indicadores.items,
          avisosTruncado,
        };
        return this.construirResultado(correspondencias);
      })
    );
  }

  recargarCorrespondencias(): Observable<ResultadoSeguimiento | null> {
    if (!this.cache) return of(null);
    return this.cargarCorrespondencias().pipe(
      map((correspondencias) => this.construirResultado(correspondencias))
    );
  }

  /**
   * @brief Orígenes operativos con correspondencia confirmada para un filtro
   * de marco (dimensión, componente o estándar; subárbol según la API).
   */
  obtenerOrigenesMarco(filtro: { dimension?: number; componente?: number; estandar?: number }): Observable<{
    indicadores: Set<number>;
    criterios: Set<number>;
    truncado: boolean;
  }> {
    return this.obtenerPaginas(
      (page) => this.vinculacionService.listarCorrespondencias({ ...filtro, estado: 'confirmada', page }),
      MAX_PAGINAS_CORRESPONDENCIAS
    ).pipe(
      map((resultado) => {
        const indicadores = new Set<number>();
        const criterios = new Set<number>();
        for (const corr of resultado.items as any[]) {
          if (typeof corr?.indicador_op === 'number') indicadores.add(corr.indicador_op);
          if (typeof corr?.criterio_op === 'number') criterios.add(corr.criterio_op);
        }
        return { indicadores, criterios, truncado: resultado.truncado };
      })
    );
  }

  private cargarCorrespondencias(): Observable<CorrespondenciasPaginadas | null> {
    return forkJoin({
      confirmadas: this.obtenerPaginas(
        (page) => this.vinculacionService.listarCorrespondencias({ estado: 'confirmada', page }),
        MAX_PAGINAS_CORRESPONDENCIAS
      ),
      propuestas: this.obtenerPaginas(
        (page) => this.vinculacionService.listarCorrespondencias({ estado: 'propuesta', page }),
        MAX_PAGINAS_CORRESPONDENCIAS
      ),
    }).pipe(catchError(() => of(null)));
  }

  private construirResultado(correspondencias: CorrespondenciasPaginadas | null): ResultadoSeguimiento {
    const correspondenciasDisponibles = correspondencias !== null;
    const contexto: ContextoCorrespondencias = {
      confirmados: new Set<number>(),
      pendientes: new Set<number>(),
      preferidas: new Map<number, { codigoDestino: string; versionMarco: string }>(),
      correspondenciasDisponibles,
    };
    let avisoCorrespondenciaTruncada = false;

    if (correspondencias) {
      avisoCorrespondenciaTruncada = correspondencias.confirmadas.truncado || correspondencias.propuestas.truncado;
      const idsConfirmados = correspondencias.confirmadas.items
        .map((item: any) => item.indicador_op)
        .filter((id: any) => typeof id === 'number');
      const idsPropuestos = correspondencias.propuestas.items
        .map((item: any) => item.indicador_op)
        .filter((id: any) => typeof id === 'number');
      contexto.confirmados = new Set<number>(idsConfirmados);
      contexto.pendientes = new Set<number>(idsPropuestos.filter((id: number) => !contexto.confirmados.has(id)));
      const registrar = (items: any[]) => {
        for (const item of items) {
          const indicador = item?.indicador_op;
          if (typeof indicador !== 'number' || contexto.preferidas.has(indicador)) continue;
          contexto.preferidas.set(indicador, {
            codigoDestino: item?.destino?.texto ?? '',
            versionMarco: item?.version_marco?.nombre ?? '',
          });
        }
      };
      registrar(correspondencias.confirmadas.items);
      registrar(correspondencias.propuestas.items);
    }

    const filas = this.construirFilas(contexto);
    return {
      filas,
      metricas: calcularMetricas(filas, correspondenciasDisponibles),
      avisosTruncado: this.cache?.avisosTruncado ?? [],
      avisoCorrespondenciaTruncada,
      correspondenciasDisponibles,
    };
  }

  private construirFilas(contexto: ContextoCorrespondencias): FilaSeguimiento[] {
    const cache = this.cache;
    if (!cache) return [];

    const evPorAsignacion = new Map<number, any>();
    for (const evidencia of cache.evidencias) {
      const asignacionId =
        typeof evidencia.asignacion === 'number' ? evidencia.asignacion : evidencia.asignacion?.id;
      if (asignacionId != null) evPorAsignacion.set(asignacionId, evidencia);
    }
    const criterioPorIndicador = new Map<number, string>();
    const criterioIdPorIndicador = new Map<number, number | null>();
    for (const indicador of cache.indicadores) {
      criterioPorIndicador.set(indicador.id, indicador.criterio_nombre || '');
      criterioIdPorIndicador.set(indicador.id, typeof indicador.criterio === 'number' ? indicador.criterio : null);
    }

    return cache.asignaciones.map((asignacion: any) => {
      const evidencia = evPorAsignacion.get(asignacion.id) ?? null;
      const documental = asignacion.gestion_documental ? asignacion.documentos_resumen : null;
      const claveRevision = documental?.observados > 0 ? 'observada' : this.claveDeRevision(
        evidencia || (documental?.entregados > 0 ? { estado: 'activa' } : null), asignacion.estado);
      const esMarco = asignacion.tipo_origen === 'marco';
      const rutaMarco = asignacion.ruta_marco ?? undefined;
      const indicadorId = esMarco ? `marco:${asignacion.indicador_marco}` : asignacion.indicador;
      const vinculo = contexto.preferidas.get(indicadorId);
      let correspondenciaEstado: EstadoCorrespondenciaFila = 'desconocida';
      if (esMarco) {
        correspondenciaEstado = 'directa';
      } else if (contexto.correspondenciasDisponibles) {
        if (contexto.confirmados.has(indicadorId)) correspondenciaEstado = 'confirmada';
        else if (contexto.pendientes.has(indicadorId)) correspondenciaEstado = 'pendiente';
        else correspondenciaEstado = 'sin';
      }
      return {
        asignacionId: asignacion.id,
        periodoNombre: asignacion.periodo_nombre || '',
        unidadId: asignacion.unidad_responsable,
        unidadNombre: asignacion.unidad_responsable_nombre || '',
        indicadorId,
        indicadorNombre: asignacion.indicador_nombre || '',
        criterioId: esMarco ? null : criterioIdPorIndicador.get(indicadorId) ?? null,
        criterioNombre: esMarco ? (asignacion.criterio_nombre || rutaMarco?.criterio?.nombre || '—') : criterioPorIndicador.get(indicadorId) || '—',
        estado: asignacion.estado || '',
        estadoDisplay: asignacion.estado_display || asignacion.estado || '',
        evidenciaId: evidencia?.id_evidencia ?? null,
        claveRevision,
        estadoRevision: ETIQUETAS_REVISION[claveRevision],
        correspondenciaEstado,
        codigoDestino: esMarco ? (rutaMarco?.indicador?.codigo ?? '') : contexto.correspondenciasDisponibles ? (vinculo?.codigoDestino ?? '') : '',
        versionMarco: esMarco ? (rutaMarco?.version?.nombre ?? '') : contexto.correspondenciasDisponibles ? (vinculo?.versionMarco ?? '') : '',
        ...(esMarco ? { tipoOrigen: 'marco', indicadorMarcoId: asignacion.indicador_marco, rutaMarco } : {}),
        ...(documental ? { documentosResumen: documental } : {}),
      } as FilaSeguimiento;
    });
  }

  private claveDeRevision(evidencia: any, estadoAsignacion: string): FilaSeguimiento['claveRevision'] {
    if (!evidencia) return 'sin_evidencia';
    if (evidencia.estado === 'cancelada') return 'cancelada';
    switch (estadoAsignacion) {
      case 'en_progreso':
        return 'en_revision';
      case 'observada':
        return 'observada';
      case 'aprobado':
        return 'aprobada';
      case 'rechazado':
        return 'rechazada';
      case 'completado':
        return 'completada';
      default:
        return 'sin_enviar';
    }
  }
}
