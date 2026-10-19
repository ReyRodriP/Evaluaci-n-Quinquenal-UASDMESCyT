import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Dashboard } from './dashboard';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { ToastrModule } from 'ngx-toastr';
import { of, throwError } from 'rxjs';
import { SeguimientoResumenService } from '../../../../core/services/seguimiento-resumen.service';
import { FilaSeguimiento, ResultadoSeguimiento, calcularMetricas } from '../../../../core/models/seguimiento.model';

function filaSeguimiento(parcial: Partial<FilaSeguimiento> = {}): FilaSeguimiento {
  return {
    asignacionId: 1,
    periodoNombre: 'Período actual',
    unidadId: 7,
    unidadNombre: 'Facultad de Ciencias',
    indicadorId: 100,
    indicadorNombre: 'IND-01',
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

  const mostrar = () => {
    component.loading = false;
    fixture.detectChanges();
  };

  const seccionSeguimiento = () =>
    (fixture.nativeElement as HTMLElement).querySelector('.seguimiento-resumen');

  beforeEach(async () => {
    seguimientoService = jasmine.createSpyObj<SeguimientoResumenService>(
      'SeguimientoResumenService',
      ['cargar', 'recargarCorrespondencias', 'obtenerPaginas']
    );
    seguimientoService.cargar.and.returnValue(of(resultadoBase()));

    await TestBed.configureTestingModule({
      imports: [Dashboard, ToastrModule.forRoot(), RouterTestingModule],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: SeguimientoResumenService, useValue: seguimientoService },
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
});
