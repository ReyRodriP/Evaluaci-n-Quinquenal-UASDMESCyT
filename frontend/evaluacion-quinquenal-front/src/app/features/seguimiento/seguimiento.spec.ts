import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { of, throwError } from 'rxjs';

import { EvaluacionService } from '../../core/services/evaluacion.service';
import { EvidenciasService } from '../../core/services/evidencias.service';
import { VinculacionService } from '../../core/services/vinculacion.service';
import { COLUMNAS_EXPORTACION, Seguimiento } from './seguimiento';

const pagina = (results: any[], count = results.length) => ({
  count,
  next: null as string | null,
  previous: null as string | null,
  results,
});

function baseData() {
  return {
    periodos: [
      { id: 10, nombre: 'Período actual', activo: true },
      { id: 11, nombre: 'Período anterior', activo: false },
    ],
    activo: { id: 10, nombre: 'Período actual' } as any,
    asignaciones: [
      {
        id: 1, indicador: 100, indicador_nombre: 'IND-01',
        unidad_responsable: 7, unidad_responsable_nombre: 'Facultad de Ciencias',
        periodo: 10, periodo_nombre: 'Período actual',
        estado: 'pendiente', estado_display: 'Pendiente',
      },
      {
        id: 2, indicador: 100, indicador_nombre: 'IND-01',
        unidad_responsable: 7, unidad_responsable_nombre: 'Facultad de Ciencias',
        periodo: 10, periodo_nombre: 'Período actual',
        estado: 'en_progreso', estado_display: 'En progreso',
      },
      {
        id: 3, indicador: 300, indicador_nombre: 'IND-03',
        unidad_responsable: 8, unidad_responsable_nombre: 'Instituto Tecnológico',
        periodo: 10, periodo_nombre: 'Período actual',
        estado: 'observada', estado_display: 'Observada',
      },
      {
        id: 4, indicador: 400, indicador_nombre: 'IND-04',
        unidad_responsable: 7, unidad_responsable_nombre: 'Facultad de Ciencias',
        periodo: 10, periodo_nombre: 'Período actual',
        estado: 'aprobado', estado_display: 'Aprobado',
      },
    ] as any[],
    asignacionesHistoricas: [
      {
        id: 9, indicador: 100, indicador_nombre: 'IND-01',
        unidad_responsable: 7, unidad_responsable_nombre: 'Facultad de Ciencias',
        periodo: 11, periodo_nombre: 'Período anterior',
        estado: 'aprobado', estado_display: 'Aprobado',
      },
    ] as any[],
    evidencias: [
      { id_evidencia: 501, asignacion: 2, estado: 'activa', versiones: [{ id_version: 1 }, { id_version: 2 }, { id_version: 3 }] },
      { id_evidencia: 502, asignacion: 3, estado: 'activa', versiones: [] },
      { id_evidencia: 503, asignacion: 4, estado: 'activa', versiones: [] },
    ] as any[],
    indicadores: [
      { id: 100, nombre: 'IND-01', criterio_nombre: 'Criterio A' },
      { id: 300, nombre: 'IND-03', criterio_nombre: 'Criterio C' },
      { id: 400, nombre: 'IND-04', criterio_nombre: 'Criterio D' },
    ] as any[],
    confirmadas: [
      {
        id: 1, estado: 'confirmada', indicador_op: 100,
        destino: { nivel: 'indicador_marco', id: 55, texto: '6.1.1.1-IND-01' },
        version_marco: { id: 1, nombre: 'Marco 2026', slug: 'marco-2026', activo: true },
      },
    ] as any[],
    propuestas: [
      {
        id: 2, estado: 'propuesta', indicador_op: 100,
        destino: { nivel: 'dimension', id: 3, texto: 'D1 Modelación' },
        version_marco: { id: 1, nombre: 'Marco 2026', slug: 'marco-2026', activo: true },
      },
      {
        id: 3, estado: 'propuesta', indicador_op: 300,
        destino: { nivel: 'estandar', id: 9, texto: 'E1.2' },
        version_marco: { id: 1, nombre: 'Marco 2026', slug: 'marco-2026', activo: true },
      },
    ] as any[],
  };
}

describe('Seguimiento', () => {
  let component: Seguimiento;
  let fixture: ComponentFixture<Seguimiento>;
  let data: ReturnType<typeof baseData>;
  let evaluacionService: jasmine.SpyObj<EvaluacionService>;
  let evidenciasService: jasmine.SpyObj<EvidenciasService>;
  let vinculacionService: jasmine.SpyObj<VinculacionService>;

  const exitoAsignaciones = (periodoId: any, page: number) =>
    of(pagina(Number(periodoId) === 11 ? data.asignacionesHistoricas : data.asignaciones));
  const exitoEvidencias = (periodoId: any, page: number) =>
    of(pagina(Number(periodoId) === 11 ? [] : data.evidencias));
  const exitoIndicadores = (page: number) => of(pagina(data.indicadores));
  const exitoCorrespondencias = (filtro: any) =>
    of(pagina(filtro?.estado === 'propuesta' ? data.propuestas : data.confirmadas));

  const recargar = () => {
    evaluacionService.listarAsignacionesPagina.and.callFake(exitoAsignaciones);
    evidenciasService.listarEvidenciasPagina.and.callFake(exitoEvidencias);
    evaluacionService.listarIndicadoresPagina.and.callFake(exitoIndicadores);
    vinculacionService.listarCorrespondencias.and.callFake(exitoCorrespondencias);
    component.cargarDatos();
    fixture.detectChanges();
  };

  beforeEach(async () => {
    data = baseData();
    evaluacionService = jasmine.createSpyObj<EvaluacionService>(
      'EvaluacionService',
      ['listarPeriodos', 'periodoActivo', 'listarAsignacionesPagina', 'listarIndicadoresPagina']
    );
    evidenciasService = jasmine.createSpyObj<EvidenciasService>('EvidenciasService', ['listarEvidenciasPagina']);
    vinculacionService = jasmine.createSpyObj<VinculacionService>('VinculacionService', ['listarCorrespondencias']);

    evaluacionService.listarPeriodos.and.callFake(() => of(data.periodos));
    evaluacionService.periodoActivo.and.callFake(() => of(data.activo));
    evaluacionService.listarAsignacionesPagina.and.callFake(exitoAsignaciones);
    evaluacionService.listarIndicadoresPagina.and.callFake(exitoIndicadores);
    evidenciasService.listarEvidenciasPagina.and.callFake(exitoEvidencias);
    vinculacionService.listarCorrespondencias.and.callFake(exitoCorrespondencias);

    await TestBed.configureTestingModule({
      imports: [Seguimiento, HttpClientTestingModule, RouterTestingModule],
      providers: [
        { provide: EvaluacionService, useValue: evaluacionService },
        { provide: EvidenciasService, useValue: evidenciasService },
        { provide: VinculacionService, useValue: vinculacionService },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(Seguimiento);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('crea el componente y selecciona el período activo', () => {
    expect(component).toBeTruthy();
    expect(component.periodoSeleccionadoId).toBe('10');
    expect(evaluacionService.listarAsignacionesPagina).toHaveBeenCalledWith('10', 1);
    expect(evidenciasService.listarEvidenciasPagina).toHaveBeenCalledWith('10', 1);
  });

  it('construye filas con criterio, evidencia y estado de correspondencia', () => {
    expect(component.filas.length).toBe(4);

    const sinEvidencia = component.filas.find((fila) => fila.asignacionId === 1)!;
    expect(sinEvidencia.evidenciaId).toBeNull();
    expect(sinEvidencia.correspondenciaEstado).toBe('confirmada');

    const enRevision = component.filas.find((fila) => fila.asignacionId === 2)!;
    expect(enRevision.evidenciaId).toBe(501);
    expect(enRevision.criterioNombre).toBe('Criterio A');
    expect(enRevision.claveRevision).toBe('en_revision');
    expect(enRevision.estadoRevision).toBe('Pendiente de revisión');

    expect(component.filas.find((fila) => fila.asignacionId === 3)!.correspondenciaEstado).toBe('pendiente');
    expect(component.filas.find((fila) => fila.asignacionId === 4)!.correspondenciaEstado).toBe('sin');
  });

  it('calcula las métricas sin duplicar por versiones de evidencia', () => {
    expect(component.metricas).toEqual({
      total: 4,
      conEvidencia: 3,
      sinEvidencia: 1,
      pendientesRevision: 1,
      observadas: 1,
      conConfirmada: 2,
      sinConfirmada: 2,
    });
  });

  it('la propuesta no cuenta como correspondencia confirmada y la confirmada prevalece', () => {
    const propuesta = component.filas.find((fila) => fila.indicadorId === 300)!;
    expect(propuesta.correspondenciaEstado).toBe('pendiente');

    const tambienPropuesta = component.filas.find((fila) => fila.asignacionId === 2)!;
    expect(tambienPropuesta.correspondenciaEstado).toBe('confirmada');

    expect(component.metricas.conConfirmada).toBe(2);
    expect(component.metricas.sinConfirmada).toBe(2);
  });

  it('deriva los estados de revisión para cada caso', () => {
    const claves = component.filas.map((fila) => fila.claveRevision);
    expect(claves).toEqual(['sin_evidencia', 'en_revision', 'observada', 'aprobada']);
    expect(component.filas.map((fila) => fila.estadoRevision)).toEqual([
      'Sin evidencia',
      'Pendiente de revisión',
      'Observada',
      'Aprobada internamente',
    ]);
  });

  it('una evidencia cancelada no cuenta como pendiente de revisión', () => {
    data.evidencias[0].estado = 'cancelada';
    component.cargarDatos();
    fixture.detectChanges();

    const fila = component.filas.find((item) => item.asignacionId === 2)!;
    expect(fila.claveRevision).toBe('cancelada');
    expect(fila.estadoRevision).toBe('Evidencia cancelada');
    expect(component.metricas.conEvidencia).toBe(3);
    expect(component.metricas.pendientesRevision).toBe(0);
  });

  it('combina los filtros con semántica AND y limpia', () => {
    component.cambiarFiltro('unidad', '7');
    expect(component.filasFiltradas.length).toBe(3);

    component.cambiarFiltro('estado', 'pendiente');
    expect(component.filasFiltradas.length).toBe(1);
    expect(component.metricas.total).toBe(1);

    component.cambiarFiltro('revision', 'en_revision');
    expect(component.filasFiltradas.length).toBe(0);
    expect(component.metricas.total).toBe(0);
    expect(component.filasPaginadas.length).toBe(0);

    component.limpiarFiltros();
    expect(component.filasFiltradas.length).toBe(4);
    expect(component.metricas.total).toBe(4);
  });

  it('filtra por estado de correspondencia', () => {
    component.cambiarFiltro('correspondencia', 'confirmada');
    expect(component.filasFiltradas.length).toBe(2);

    component.cambiarFiltro('correspondencia', 'pendiente');
    expect(component.filasFiltradas.length).toBe(1);

    component.cambiarFiltro('correspondencia', 'sin');
    expect(component.filasFiltradas.length).toBe(1);
  });

  it('ofrece opciones de filtro derivadas de los datos cargados', () => {
    expect(component.opcionesUnidades.map((opcion) => opcion.valor)).toEqual(['7', '8']);
    expect(component.opcionesEstados.length).toBe(4);
    expect(component.opcionesRevision.length).toBe(4);
    expect(component.opcionesCorrespondencia.length).toBe(3);
  });

  it('recarga los datos al cambiar de período', () => {
    component.onPeriodoChange('11');
    fixture.detectChanges();

    expect(evaluacionService.listarAsignacionesPagina).toHaveBeenCalledWith('11', 1);
    expect(component.filas.length).toBe(1);
    expect(component.filas[0].periodoNombre).toBe('Período anterior');
    expect(component.filas[0].claveRevision).toBe('sin_evidencia');
  });

  it('muestra estado vacío cuando no hay asignaciones', () => {
    data.asignaciones = [];
    data.evidencias = [];
    component.cargarDatos();
    fixture.detectChanges();

    expect(component.filas.length).toBe(0);
    expect(component.metricas.total).toBe(0);
    const texto = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(texto).toContain('No hay asignaciones registradas para el período seleccionado.');
  });

  it('muestra error recuperable cuando falla la carga principal', () => {
    spyOn(console, 'error');
    evaluacionService.listarAsignacionesPagina.and.returnValue(throwError(() => ({ status: 500 })));
    component.cargarDatos();
    fixture.detectChanges();

    expect(component.errorCarga).toContain('No se pudo cargar');
    expect(component.cargando).toBeFalse();

    recargar();
    expect(component.errorCarga).toBe('');
    expect(component.filas.length).toBe(4);
  });

  it('degrada las métricas de correspondencia si vinculación falla y permite reintentar', () => {
    spyOn(console, 'error');
    vinculacionService.listarCorrespondencias.and.returnValue(throwError(() => ({ status: 403 })));
    component.cargarDatos();
    fixture.detectChanges();

    expect(component.filas.length).toBe(4);
    expect(component.errorCorrespondencias).toBeTrue();
    expect(component.correspondenciasDisponibles).toBeFalse();
    expect(component.metricas.conConfirmada).toBeNull();
    expect(component.metricas.sinConfirmada).toBeNull();
    expect(component.filas.every((fila) => fila.correspondenciaEstado === 'desconocida')).toBeTrue();
    const texto = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(texto).toContain('No se pudo consultar el estado de correspondencias');

    vinculacionService.listarCorrespondencias.and.callFake(exitoCorrespondencias);
    component.reintentarCorrespondencias();
    fixture.detectChanges();

    expect(component.errorCorrespondencias).toBeFalse();
    expect(component.metricas.conConfirmada).toBe(2);
    expect(component.filas[0].correspondenciaEstado).toBe('confirmada');
  });

  it('pagina el listado filtrado en el cliente', () => {
    data.asignaciones = Array.from({ length: 25 }, (_, indice) => ({
      id: indice + 1,
      indicador: 100,
      indicador_nombre: 'IND-01',
      unidad_responsable: 7,
      unidad_responsable_nombre: 'Facultad de Ciencias',
      periodo: 10,
      periodo_nombre: 'Período actual',
      estado: 'pendiente',
      estado_display: 'Pendiente',
    }));
    data.evidencias = [];
    recargar();

    expect(component.filasFiltradas.length).toBe(25);
    expect(component.filasPaginadas.length).toBe(10);

    component.onPageChange(2);
    expect(component.filasPaginadas[0].asignacionId).toBe(11);

    component.onPageSizeChange(25);
    expect(component.currentPage).toBe(1);
    expect(component.filasPaginadas.length).toBe(25);
  });

  it('acota la lectura por páginas y marca el truncamiento', () => {
    const paginas = (page: number) =>
      of({
        count: 120,
        next: page < 3 ? `pagina-${page + 1}` : null,
        previous: null,
        results: Array.from({ length: 50 }, (_, indice) => ({ id: (page - 1) * 50 + indice })),
      });

    let corto: any = null;
    component.obtenerPaginas(paginas, 2).subscribe((resultado) => (corto = resultado));
    expect(corto.items.length).toBe(100);
    expect(corto.total).toBe(120);
    expect(corto.truncado).toBeTrue();

    let completo: any = null;
    component.obtenerPaginas(paginas, 20).subscribe((resultado) => (completo = resultado));
    expect(completo.items.length).toBe(120);
    expect(completo.truncado).toBeFalse();
  });

  it('avisa cuando las asignaciones superan el límite de lectura', () => {
    evaluacionService.listarAsignacionesPagina.and.callFake(() =>
      of({ count: 1500, next: 'siguiente', previous: null, results: data.asignaciones.slice(0, 4) })
    );
    component.cargarDatos();
    fixture.detectChanges();

    expect(component.avisosTruncado.length).toBe(1);
    expect(component.avisosTruncado[0]).toContain('Asignaciones');
  });

  it('renderiza enlaces a detalle de asignación, evidencia y correspondencias', () => {
    const hrefs = Array.from((fixture.nativeElement as HTMLElement).querySelectorAll('a[href]')).map(
      (ancla) => ancla.getAttribute('href') ?? ''
    );

    expect(hrefs.some((href) => href.includes('/asignaciones/1/detalle'))).toBeTrue();
    expect(hrefs.some((href) => href.includes('/evidencias/501/detalle') && href.includes('periodo=10'))).toBeTrue();
    expect(hrefs.some((href) => href.includes('/indicadores/300/detalle'))).toBeTrue();
    expect(hrefs.some((href) => href.includes('/evidencias/'))).toBeTrue();
    expect(hrefs.filter((href) => href.includes('/evidencias/')).length).toBe(3);
  });

  it('exporta solo los registros que coinciden con los filtros activos', () => {
    component.cambiarFiltro('unidad', '7');
    const spy = spyOn(component, 'descargar');
    component.exportarCsv();

    expect(spy).toHaveBeenCalledTimes(1);
    const [contenido, nombre] = spy.calls.mostRecent().args as [string, string];
    expect(contenido).toContain('Facultad de Ciencias');
    expect(contenido).not.toContain('Instituto Tecnológico');
    expect(contenido.replace('\uFEFF', '').split('\r\n').filter(Boolean).length).toBe(4);
    expect(nombre).toContain('Seguimiento_Periodo_actual');
    expect(nombre).not.toContain('limitado');
    expect(nombre).toMatch(/\.csv$/);

    fixture.detectChanges();
    const boton = (fixture.nativeElement as HTMLElement).querySelector('.btn-export');
    expect(boton?.textContent).toContain('3 registros');
  });

  it('exporta más de una página de resultados', () => {
    data.asignaciones = Array.from({ length: 25 }, (_, indice) => ({
      id: indice + 1,
      indicador: 100,
      indicador_nombre: `IND-${indice + 1}`,
      unidad_responsable: 7,
      unidad_responsable_nombre: 'Facultad de Ciencias',
      periodo: 10,
      periodo_nombre: 'Período actual',
      estado: 'pendiente',
      estado_display: 'Pendiente',
    }));
    data.evidencias = [];
    recargar();
    expect(component.filasPaginadas.length).toBe(10);

    const spy = spyOn(component, 'descargar');
    component.exportarCsv();
    const contenido = spy.calls.mostRecent().args[0] as string;
    const lineas = contenido.replace('\uFEFF', '').split('\r\n').filter(Boolean);
    expect(lineas.length).toBe(26);
    expect(contenido).toContain('IND-25');
  });

  it('no exporta cuando el conjunto filtrado está vacío', () => {
    component.cambiarFiltro('estado', 'rechazado');
    fixture.detectChanges();
    const boton = (fixture.nativeElement as HTMLElement).querySelector('.btn-export');
    expect(boton).toBeNull();

    const spy = spyOn(component, 'descargar');
    component.exportarCsv();
    expect(spy).not.toHaveBeenCalled();
    expect(component.exportando).toBeFalse();
  });

  it('escapa comas, comillas y saltos de línea en las celdas', () => {
    data.asignaciones[0].unidad_responsable_nombre = 'Facultad "Norte",\nSur';
    recargar();
    const spy = spyOn(component, 'descargar');
    component.exportarCsv();
    const contenido = spy.calls.mostRecent().args[0] as string;
    expect(contenido).toContain('"Facultad ""Norte"",\nSur"');
  });

  it('neutraliza fórmulas de hoja de cálculo sin alterar los datos de la pantalla', () => {
    data.asignaciones[0].indicador_nombre = '=1+1';
    data.asignaciones[1].unidad_responsable_nombre = '@comando';
    data.indicadores[0].criterio_nombre = '-Criterio';
    recargar();
    const spy = spyOn(component, 'descargar');
    component.exportarCsv();

    const contenido = spy.calls.mostRecent().args[0] as string;
    expect(contenido).toContain("'=1+1");
    expect(contenido).toContain("'@comando");
    expect(contenido).toContain("'-Criterio");
    expect(component.filas[0].indicadorNombre).toBe('=1+1');
  });

  it('informa y marca el archivo cuando los datos están limitados', () => {
    component.avisosTruncado = ['Asignaciones: se obtuvieron 20 de 30; las métricas reflejan solo esas filas.'];
    fixture.detectChanges();

    const aviso = (fixture.nativeElement as HTMLElement).querySelector('.export-aviso');
    expect(aviso?.textContent).toContain('limitada');

    const spy = spyOn(component, 'descargar');
    component.exportarCsv();
    const nombre = spy.calls.mostRecent().args[1] as string;
    expect(nombre).toContain('Seguimiento_Periodo_actual_limitado');
    expect(nombre).toMatch(/\.csv$/);
  });

  it('mantiene consistentes las columnas exportadas con los datos visibles', () => {
    const spy = spyOn(component, 'descargar');
    component.exportarCsv();
    const contenido = spy.calls.mostRecent().args[0] as string;
    expect(contenido.startsWith('\uFEFF')).toBeTrue();

    const lineas = contenido.replace('\uFEFF', '').split('\r\n').filter(Boolean);
    expect(lineas[0]).toBe(COLUMNAS_EXPORTACION.join(','));
    expect(lineas[1]).toContain('Sin evidencia');
    expect(lineas[1]).toContain('Confirmada');
    expect(lineas[1]).toContain('6.1.1.1-IND-01');
    expect(lineas[1]).toContain('Marco 2026');
    expect(lineas[3]).toContain('Pendiente de validación');
    expect(lineas[3]).toContain('E1.2');
    expect(lineas[1].split(',')[6]).toBe(component.filasFiltradas[0].estadoRevision);
    expect(lineas[1].split(',')[7]).toBe(
      component.etiquetaCorrespondencia(component.filasFiltradas[0].correspondenciaEstado)
    );
  });
});
