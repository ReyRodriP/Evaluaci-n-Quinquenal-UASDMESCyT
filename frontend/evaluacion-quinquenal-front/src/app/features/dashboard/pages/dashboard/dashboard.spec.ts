import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';

import { Dashboard } from './dashboard';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { ActivatedRoute, convertToParamMap } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';
import { ToastrModule } from 'ngx-toastr';
import { of, throwError } from 'rxjs';
import { SeguimientoResumenService } from '../../../../core/services/seguimiento-resumen.service';
import { CatalogoService } from '../../../../core/services/catalogo.service';
import { FilaSeguimiento, ResultadoSeguimiento, calcularMetricas } from '../../../../core/models/seguimiento.model';

const dimensionesMarcoPrueba: any[] = [
  {
    id: 1,
    codigo: 'I',
    nombre: 'Dimensión I',
    componentes: [
      { id: 11, codigo: '1.1', codigo_completo: '1.1', nombre: 'Componente 1' },
      { id: 12, codigo: '1.2', codigo_completo: '1.2', nombre: 'Componente 2' },
    ],
  },
  {
    id: 2,
    codigo: 'II',
    nombre: 'Dimensión II',
    componentes: [{ id: 21, codigo: '2.1', codigo_completo: '2.1', nombre: 'Componente 3' }],
  },
];

const estandaresPrueba: any[] = [{ id: 41, codigo_completo: '1.1.1.1', redaccion: 'Estándar 1' }];

function filaSeguimiento(parcial: Partial<FilaSeguimiento> = {}): FilaSeguimiento {
  return {
    asignacionId: 1,
    periodoNombre: 'Período actual',
    unidadId: 7,
    unidadNombre: 'Facultad de Ciencias',
    indicadorId: 100,
    indicadorNombre: 'IND-01',
    criterioId: null,
    criterioNombre: 'Criterio A',
    estado: 'en_progreso',
    estadoDisplay: 'En progreso',
    evidenciaId: 501,
    claveRevision: 'en_revision',
    estadoRevision: 'Pendiente de revisión',
    correspondenciaEstado: 'confirmada',
    codigoDestino: '6.1.1.1-IND-01',
    versionMarco: 'Marco 2026',
    ...parcial,
  };
}

function resultadoBase(correspondenciasDisponibles = true): ResultadoSeguimiento {
  const filas = [
    filaSeguimiento({
      asignacionId: 1,
      estado: 'pendiente',
      estadoDisplay: 'Pendiente',
      evidenciaId: null,
      claveRevision: 'sin_evidencia',
      estadoRevision: 'Sin evidencia',
    }),
    filaSeguimiento({ asignacionId: 2 }),
    filaSeguimiento({
      asignacionId: 3,
      estado: 'observada',
      estadoDisplay: 'Observada',
      claveRevision: 'observada',
      estadoRevision: 'Observada',
      correspondenciaEstado: 'pendiente',
    }),
    filaSeguimiento({
      asignacionId: 4,
      estado: 'aprobado',
      estadoDisplay: 'Aprobado',
      claveRevision: 'aprobada',
      estadoRevision: 'Aprobada internamente',
      correspondenciaEstado: 'sin',
    }),
  ];
  return {
    filas,
    metricas: calcularMetricas(filas, correspondenciasDisponibles),
    avisosTruncado: [],
    avisoCorrespondenciaTruncada: false,
    correspondenciasDisponibles,
  };
}

describe('Dashboard', () => {
  let component: Dashboard;
  let fixture: ComponentFixture<Dashboard>;
  let seguimientoService: jasmine.SpyObj<SeguimientoResumenService>;
  let catalogoService: jasmine.SpyObj<CatalogoService>;

  const mostrar = () => {
    component.loading = false;
    fixture.detectChanges();
  };

  const seccionSeguimiento = () =>
    (fixture.nativeElement as HTMLElement).querySelector('.seguimiento-resumen');

  const enlaceDeTarjeta = (etiqueta: string) => {
    const enlaces = Array.from(
      (fixture.nativeElement as HTMLElement).querySelectorAll<HTMLAnchorElement>('a.kpi-enlace')
    );
    return enlaces.find((enlace) => enlace.querySelector('.kpi-label')?.textContent?.trim() === etiqueta);
  };

  const hrefDe = (etiqueta: string) => enlaceDeTarjeta(etiqueta)?.getAttribute('href') ?? '';

  beforeEach(async () => {
    seguimientoService = jasmine.createSpyObj<SeguimientoResumenService>(
      'SeguimientoResumenService',
      ['cargar', 'recargarCorrespondencias', 'obtenerPaginas', 'obtenerOrigenesMarco']
    );
    seguimientoService.cargar.and.returnValue(of(resultadoBase()));
    seguimientoService.obtenerOrigenesMarco.and.returnValue(
      of({ indicadores: new Set<number>(), criterios: new Set<number>(), truncado: false })
    );

    catalogoService = jasmine.createSpyObj<CatalogoService>(
      'CatalogoService',
      ['listarVersiones', 'listarDimensiones', 'listarCriterios', 'listarEstandares']
    );
    catalogoService.listarVersiones.and.returnValue(of([{ id: 1, slug: 'marco-2026', activo: true }]));
    catalogoService.listarDimensiones.and.returnValue(of(dimensionesMarcoPrueba));
    catalogoService.listarCriterios.and.returnValue(of([{ id: 31, nombre: 'Criterio 1.1' }]));
    catalogoService.listarEstandares.and.returnValue(of(estandaresPrueba));

    await TestBed.configureTestingModule({
      imports: [Dashboard, ToastrModule.forRoot(), RouterTestingModule],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: SeguimientoResumenService, useValue: seguimientoService },
        { provide: CatalogoService, useValue: catalogoService },
      ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(Dashboard);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('renderiza las métricas de seguimiento con sus etiquetas', () => {
    component.periodoSeleccionadoId = '10';
    component.resultadoSeguimiento = resultadoBase();
    mostrar();

    const tarjetas = Array.from(seccionSeguimiento()!.querySelectorAll('.kpi-card'));
    const etiquetas = tarjetas.map((tarjeta) => tarjeta.querySelector('.kpi-label')?.textContent?.trim());
    const valores = tarjetas.map((tarjeta) => tarjeta.querySelector('.kpi-value')?.textContent?.trim());
    expect(etiquetas).toEqual([
      'Pendientes de revisión',
      'Observadas',
      'Con correspondencia confirmada',
      'Sin correspondencia confirmada',
    ]);
    expect(valores).toEqual(['1', '1', '2', '2']);
  });

  it('recarga el resumen al cambiar de período', () => {
    component.periodoSeleccionadoId = '10';

    component.onPeriodoChange('11');

    expect(seguimientoService.cargar).toHaveBeenCalledWith('11');
    expect(component.cargandoSeguimiento).toBeFalse();
    expect(component.resultadoSeguimiento).not.toBeNull();
  });

  it('no recarga el resumen al aplicar filtros que no cambian el período', () => {
    component.periodoSeleccionadoId = '10';
    component.unidadSeleccionadaId = '7';

    component.aplicarFiltros();

    expect(seguimientoService.cargar).not.toHaveBeenCalled();
  });

  it('muestra el estado de carga del resumen de seguimiento', () => {
    component.cargandoSeguimiento = true;
    mostrar();

    const texto = seccionSeguimiento()?.textContent ?? '';
    expect(texto).toContain('Cargando resumen de seguimiento...');
  });

  it('muestra error recuperable del resumen y permite reintentar', () => {
    seguimientoService.cargar.and.returnValue(throwError(() => ({ status: 500 })));
    component.periodoSeleccionadoId = '10';
    component.cargarResumenSeguimiento();
    mostrar();

    expect(component.errorSeguimiento).toContain('No se pudo cargar');
    const alerta = seccionSeguimiento()?.querySelector('.state-error');
    expect(alerta?.textContent).toContain('Reintentar');

    seguimientoService.cargar.and.returnValue(of(resultadoBase()));
    (alerta?.querySelector('button') as HTMLButtonElement).click();
    fixture.detectChanges();

    expect(component.errorSeguimiento).toBe('');
    expect(component.resultadoSeguimiento).not.toBeNull();
    expect(seccionSeguimiento()?.textContent).toContain('Pendientes de revisión');
  });

  it('avisa cuando el resumen se calcula sobre un subconjunto limitado', () => {
    const limitado = resultadoBase();
    limitado.avisosTruncado = [
      'Asignaciones: se obtuvieron 20 de 30; las métricas reflejan solo esas filas.',
    ];
    component.periodoSeleccionadoId = '10';
    component.resultadoSeguimiento = limitado;
    mostrar();

    const aviso = seccionSeguimiento()?.querySelector('.resumen-segu-avisos .aviso-warn');
    expect(aviso?.textContent).toContain('las métricas reflejan solo esas filas');
  });

  it('omite las métricas de correspondencia y señala EQ-SIDACES sin disponibilidad', () => {
    component.periodoSeleccionadoId = '10';
    component.resultadoSeguimiento = resultadoBase(false);
    mostrar();

    const seccion = seccionSeguimiento()!;
    const tarjetas = Array.from(seccion.querySelectorAll('.kpi-card'));
    expect(tarjetas.length).toBe(2);
    expect(tarjetas.map((tarjeta) => tarjeta.querySelector('.kpi-label')?.textContent?.trim())).toEqual([
      'Pendientes de revisión',
      'Observadas',
    ]);
    expect(tarjetas.map((tarjeta) => tarjeta.querySelector('.kpi-value')?.textContent?.trim())).toEqual([
      '1',
      '1',
    ]);
    expect(seccion.textContent).not.toContain('Con correspondencia confirmada');
    expect(seccion.textContent).toContain('EQ-SIDACES no está disponible');
  });

  it('no muestra métricas en cero cuando no hay período seleccionado', () => {
    component.periodoSeleccionadoId = '';
    component.resultadoSeguimiento = null;
    component.cargandoSeguimiento = false;
    component.errorSeguimiento = '';
    mostrar();

    const seccion = seccionSeguimiento()!;
    expect(seccion.querySelectorAll('.kpi-card').length).toBe(0);
    expect(seccion.textContent).toContain('Seleccione un período');
  });

  it('navega al seguimiento completo conservando el período', () => {
    component.periodoSeleccionadoId = '10';
    component.resultadoSeguimiento = resultadoBase();
    mostrar();

    const enlace = seccionSeguimiento()?.querySelector<HTMLAnchorElement>('.resumen-segu-enlace');
    expect(enlace?.getAttribute('href')).toBe('/seguimiento?periodo=10');
  });

  it('enlaza «Sin evidencia» a Seguimiento con período y filtro de revisión', () => {
    component.periodoSeleccionadoId = '10';
    mostrar();

    const href = hrefDe('Sin evidencia');
    expect(href).toContain('/seguimiento');
    expect(href).toContain('periodo=10');
    expect(href).toContain('revision=sin_evidencia');
  });

  it('enlaza «Pendientes de revisión» con su filtro de revisión', () => {
    component.periodoSeleccionadoId = '10';
    component.resultadoSeguimiento = resultadoBase();
    mostrar();

    const href = hrefDe('Pendientes de revisión');
    expect(href).toContain('periodo=10');
    expect(href).toContain('revision=en_revision');
  });

  it('enlaza «Observadas» con el filtro de revisión observada', () => {
    component.periodoSeleccionadoId = '10';
    component.resultadoSeguimiento = resultadoBase();
    mostrar();

    const href = hrefDe('Observadas');
    expect(href).toContain('periodo=10');
    expect(href).toContain('revision=observada');
  });

  it('enlaza las métricas de correspondencia con sus filtros', () => {
    component.periodoSeleccionadoId = '10';
    component.resultadoSeguimiento = resultadoBase();
    mostrar();

    const hrefCon = hrefDe('Con correspondencia confirmada');
    expect(hrefCon).toContain('periodo=10');
    expect(hrefCon).toContain('correspondencia=confirmada');

    const hrefSin = hrefDe('Sin correspondencia confirmada');
    expect(hrefSin).toContain('periodo=10');
    expect(hrefSin).toContain('correspondencia=sin');
  });

  it('conserva el período seleccionado en los accesos directos', () => {
    component.periodoSeleccionadoId = '11';
    component.resultadoSeguimiento = resultadoBase();
    mostrar();

    expect(hrefDe('Observadas')).toContain('periodo=11');
    expect(hrefDe('Sin evidencia')).toContain('periodo=11');
  });

  it('las métricas sin filtro compatible no se convierten en enlaces', () => {
    component.resumen = { asignaciones: 4, evidencias: 3, cobertura_porcentaje: 75 };
    mostrar();

    const etiquetas = Array.from(
      (fixture.nativeElement as HTMLElement).querySelectorAll('a.kpi-enlace')
    ).map((enlace) => enlace.querySelector('.kpi-label')?.textContent?.trim());
    expect(etiquetas).toEqual(['Sin evidencia']);
  });

  describe('filtros del marco EQ-SIDACES', () => {
    const resultadoMixto = (): ResultadoSeguimiento => {
      const filas = [
        filaSeguimiento({
          asignacionId: 1,
          estado: 'pendiente',
          estadoDisplay: 'Pendiente',
          evidenciaId: null,
          claveRevision: 'sin_evidencia',
          estadoRevision: 'Sin evidencia',
        }),
        filaSeguimiento({ asignacionId: 2 }),
        filaSeguimiento({
          asignacionId: 3,
          indicadorId: 300,
          criterioId: 33,
          estado: 'observada',
          estadoDisplay: 'Observada',
          claveRevision: 'observada',
          estadoRevision: 'Observada',
          correspondenciaEstado: 'pendiente',
        }),
        filaSeguimiento({
          asignacionId: 4,
          indicadorId: 400,
          criterioId: 44,
          estado: 'aprobado',
          estadoDisplay: 'Aprobado',
          claveRevision: 'aprobada',
          estadoRevision: 'Aprobada internamente',
          correspondenciaEstado: 'sin',
        }),
      ];
      return {
        filas,
        metricas: calcularMetricas(filas, true),
        avisosTruncado: [],
        avisoCorrespondenciaTruncada: false,
        correspondenciasDisponibles: true,
      };
    }

    const aplicarFiltroDeMarco = (dimension: string, componente = '', estandar = '') => {
      component.dimensionSeleccionadaId = dimension;
      component.componenteSeleccionadoId = componente;
      component.estandarSeleccionadoId = estandar;
      component.aplicarFiltros();
    };

    it('carga las dimensiones del marco vigente y ofrece sus opciones', () => {
      expect(catalogoService.listarVersiones).toHaveBeenCalled();
      expect(catalogoService.listarDimensiones).toHaveBeenCalledWith('marco-2026');
      expect(component.dimensionesMarco.length).toBe(2);
      expect(component.opcionesDimensiones).toEqual([
        { valor: '1', etiqueta: 'I — Dimensión I' },
        { valor: '2', etiqueta: 'II — Dimensión II' },
      ]);
    });

    it('la cascada de filtros limpia valores incompatibles y carga los estándares', () => {
      component.onDimensionMarcoChange('1');
      component.onComponenteMarcoChange('11');

      expect(catalogoService.listarCriterios).toHaveBeenCalledWith(11);
      expect(catalogoService.listarEstandares).toHaveBeenCalledWith(31);
      expect(component.opcionesEstandares).toEqual([
        { valor: '41', etiqueta: '1.1.1.1 — Estándar 1' },
      ]);

      component.estandarSeleccionadoId = '41';
      component.onDimensionMarcoChange('2');

      expect(component.componenteSeleccionadoId).toBe('');
      expect(component.estandarSeleccionadoId).toBe('');
      expect(component.estandaresComponente).toEqual([]);
      expect(component.opcionesComponentes).toEqual([
        { valor: '21', etiqueta: '2.1 — Componente 3' },
      ]);
    });

    it('al filtrar por dimensión recalcula las métricas con solo las filas vinculadas', () => {
      component.periodoSeleccionadoId = '10';
      component.resultadoSeguimiento = resultadoMixto();
      seguimientoService.obtenerOrigenesMarco.and.returnValue(
        of({ indicadores: new Set([100]), criterios: new Set<number>(), truncado: false })
      );

      aplicarFiltroDeMarco('1');

      expect(seguimientoService.obtenerOrigenesMarco).toHaveBeenCalledWith({ dimension: 1 });
      expect(component.marcoListo).toBeTrue();
      const res = component.resultadoVisible!;
      expect(res.filas.map((fila) => fila.asignacionId)).toEqual([1, 2]);
      expect(res.metricas.total).toBe(2);
      expect(res.metricas.sinEvidencia).toBe(1);

      mostrar();
      const tarjetas = Array.from(seccionSeguimiento()!.querySelectorAll('.kpi-card'));
      const etiquetas = tarjetas.map((tarjeta) => tarjeta.querySelector('.kpi-label')?.textContent?.trim());
      const valores = tarjetas.map((tarjeta) => tarjeta.querySelector('.kpi-value')?.textContent?.trim());
      expect(etiquetas).toContain('Asignaciones en el ámbito');
      expect(valores[etiquetas.indexOf('Asignaciones en el ámbito')]).toBe('2');
      expect(seccionSeguimiento()!.textContent).toContain('Ámbito del marco');
    });

    it('cuenta una sola vez una asignación con varias relaciones confirmadas', () => {
      component.periodoSeleccionadoId = '10';
      component.resultadoSeguimiento = resultadoMixto();
      seguimientoService.obtenerOrigenesMarco.and.returnValue(
        of({
          indicadores: new Set([100, 300]),
          criterios: new Set([33]),
          truncado: false,
        })
      );

      aplicarFiltroDeMarco('1');

      const res = component.resultadoVisible!;
      expect(res.filas.map((fila) => fila.asignacionId)).toEqual([1, 2, 3]);
      expect(res.metricas.total).toBe(3);
    });

    it('restaura los filtros del marco desde la URL y aplica el ámbito', () => {
      const route = TestBed.inject(ActivatedRoute);
      Object.defineProperty(route.snapshot, 'queryParamMap', {
        configurable: true,
        get: () => convertToParamMap({ dimension: '1', componente: '11', estandar: '41' }),
      });
      seguimientoService.obtenerOrigenesMarco.and.returnValue(
        of({ indicadores: new Set([100]), criterios: new Set<number>(), truncado: false })
      );

      const otro = TestBed.createComponent(Dashboard);
      otro.detectChanges();
      const instancia = otro.componentInstance;

      expect(instancia.dimensionSeleccionadaId).toBe('1');
      expect(instancia.componenteSeleccionadoId).toBe('11');
      expect(instancia.estandarSeleccionadoId).toBe('41');
      expect(seguimientoService.obtenerOrigenesMarco).toHaveBeenCalledWith({ estandar: 41 });
      expect(instancia.marcoListo).toBeTrue();
      expect(instancia.opcionesEstandares).toEqual([
        { valor: '41', etiqueta: '1.1.1.1 — Estándar 1' },
      ]);
    });

    it('ignora los parámetros de marco inválidos en la URL', () => {
      const route = TestBed.inject(ActivatedRoute);
      Object.defineProperty(route.snapshot, 'queryParamMap', {
        configurable: true,
        get: () => convertToParamMap({ dimension: '999', componente: '999' }),
      });

      const otro = TestBed.createComponent(Dashboard);
      otro.detectChanges();
      const instancia = otro.componentInstance;

      expect(instancia.dimensionSeleccionadaId).toBe('');
      expect(instancia.componenteSeleccionadoId).toBe('');
      expect(instancia.filtroMarcoActivo).toBeFalse();
      expect(seguimientoService.obtenerOrigenesMarco).not.toHaveBeenCalled();
    });

    it('si el filtro del marco falla se limpia y se avisa sin filtrar datos', () => {
      component.periodoSeleccionadoId = '10';
      component.resultadoSeguimiento = resultadoBase();
      seguimientoService.obtenerOrigenesMarco.and.returnValue(throwError(() => ({ status: 403 })));

      aplicarFiltroDeMarco('1');

      expect(component.marcoFiltroError).toBeTrue();
      expect(component.dimensionSeleccionadaId).toBe('');
      expect(component.filtroMarcoActivo).toBeFalse();
      expect(component.resultadoVisible).toBe(component.resultadoSeguimiento);
      mostrar();
      expect(seccionSeguimiento()!.textContent).toContain('el filtro se limpió');
    });

    it('indica cuando el ámbito filtrado no tiene resultados', () => {
      component.periodoSeleccionadoId = '10';
      component.resultadoSeguimiento = resultadoMixto();
      seguimientoService.obtenerOrigenesMarco.and.returnValue(
        of({ indicadores: new Set<number>(), criterios: new Set<number>(), truncado: false })
      );

      aplicarFiltroDeMarco('1');

      const res = component.resultadoVisible!;
      expect(res.filas.length).toBe(0);
      expect(res.metricas.total).toBe(0);
      mostrar();
      expect(seccionSeguimiento()!.textContent).toContain('No hay asignaciones en el ámbito del marco seleccionado');
    });

    it('avisa cuando los orígenes del marco se truncan', () => {
      component.periodoSeleccionadoId = '10';
      component.resultadoSeguimiento = resultadoMixto();
      seguimientoService.obtenerOrigenesMarco.and.returnValue(
        of({ indicadores: new Set([100]), criterios: new Set<number>(), truncado: true })
      );

      aplicarFiltroDeMarco('1');

      expect(component.avisoMarcoTruncado).toBeTrue();
      mostrar();
      expect(seccionSeguimiento()!.textContent).toContain('superan el límite de consulta');
    });

    it('mantiene la vista general completa sin filtro del marco', () => {
      component.periodoSeleccionadoId = '10';
      component.resultadoSeguimiento = resultadoMixto();

      expect(component.resultadoVisible).toBe(component.resultadoSeguimiento);
      expect(component.resultadoVisible!.metricas.total).toBe(4);
      mostrar();
      const etiquetas = Array.from(seccionSeguimiento()!.querySelectorAll('.kpi-card .kpi-label')).map(
        (etiqueta) => etiqueta.textContent?.trim()
      );
      expect(etiquetas).not.toContain('Asignaciones en el ámbito');
      expect(etiquetas).toEqual([
        'Pendientes de revisión',
        'Observadas',
        'Con correspondencia confirmada',
        'Sin correspondencia confirmada',
      ]);
    });

    it('enlaza las tarjetas del resumen a Seguimiento con el período y el marco', () => {
      component.periodoSeleccionadoId = '10';
      component.resultadoSeguimiento = resultadoMixto();
      seguimientoService.obtenerOrigenesMarco.and.returnValue(
        of({ indicadores: new Set([100]), criterios: new Set<number>(), truncado: false })
      );
      aplicarFiltroDeMarco('1', '11');
      mostrar();

      const href = hrefDe('Pendientes de revisión');
      expect(href).toContain('periodo=10');
      expect(href).toContain('revision=en_revision');
      expect(href).toContain('dimension=1');
      expect(href).toContain('componente=11');
    });

    it('señala que el filtro del marco no aplica al bloque KPI principal', () => {
      component.periodoSeleccionadoId = '10';
      component.resumen = { asignaciones: 4, evidencias: 3 };
      aplicarFiltroDeMarco('1');
      mostrar();

      const texto = (fixture.nativeElement as HTMLElement).textContent ?? '';
      expect(texto).toContain('no aplican a este bloque ni a los gráficos');
    });

    it('limpiar los filtros restablece la vista general', () => {
      component.periodoSeleccionadoId = '10';
      component.resultadoSeguimiento = resultadoMixto();
      seguimientoService.obtenerOrigenesMarco.and.returnValue(
        of({ indicadores: new Set([100]), criterios: new Set<number>(), truncado: false })
      );
      aplicarFiltroDeMarco('1');
      expect(component.resultadoVisible!.filas.length).toBe(2);

      component.limpiarFiltros();

      expect(component.filtroMarcoActivo).toBeFalse();
      expect(component.dimensionSeleccionadaId).toBe('');
      expect(component.resultadoVisible).toBe(component.resultadoSeguimiento);
      expect(component.resultadoVisible!.filas.length).toBe(4);
    });

    it('inhabilita los selects del marco si el catálogo no está disponible', fakeAsync(() => {
      component.marcoError = true;
      component.mostrarFiltrosExtras = true;
      mostrar();
      tick();
      fixture.detectChanges();

      const selects = (fixture.nativeElement as HTMLElement).querySelectorAll<HTMLSelectElement>('.filters-more select');
      const dimension = selects[0];
      expect(dimension.disabled).toBeTrue();
      expect((fixture.nativeElement as HTMLElement).textContent).toContain(
        'No se pudo consultar el catálogo del marco'
      );
    }));
  });
});
