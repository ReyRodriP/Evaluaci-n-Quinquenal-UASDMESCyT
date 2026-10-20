import { TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';
import { SeguimientoResumenService } from './seguimiento-resumen.service';
import { EvaluacionService } from './evaluacion.service';
import { EvidenciasService } from './evidencias.service';
import { VinculacionService } from './vinculacion.service';

describe('SeguimientoResumenService', () => {
  let service: SeguimientoResumenService;
  let vinculacion: jasmine.SpyObj<VinculacionService>;

  const pagina = (results: any[], count = results.length, next: string | null = null) => ({
    count,
    next,
    previous: null,
    results,
  });

  beforeEach(() => {
    vinculacion = jasmine.createSpyObj<VinculacionService>('VinculacionService', ['listarCorrespondencias']);
    TestBed.configureTestingModule({
      providers: [
        SeguimientoResumenService,
        {
          provide: EvaluacionService,
          useValue: jasmine.createSpyObj<EvaluacionService>('EvaluacionService', [
            'listarAsignacionesPagina',
            'listarIndicadoresPagina',
          ]),
        },
        {
          provide: EvidenciasService,
          useValue: jasmine.createSpyObj<EvidenciasService>('EvidenciasService', ['listarEvidenciasPagina']),
        },
        { provide: VinculacionService, useValue: vinculacion },
      ],
    });
    service = TestBed.inject(SeguimientoResumenService);
  });

  it('obtenerOrigenesMarco consulta solo correspondencias confirmadas con el filtro del marco', () => {
    vinculacion.listarCorrespondencias.and.returnValue(
      of(
        pagina([
          { id: 1, estado: 'confirmada', indicador_op: 100, criterio_op: null },
          { id: 2, estado: 'confirmada', indicador_op: null, criterio_op: 33 },
        ])
      )
    );

    let origen: any = null;
    service.obtenerOrigenesMarco({ dimension: 5 }).subscribe((resultado) => (origen = resultado));

    expect(vinculacion.listarCorrespondencias).toHaveBeenCalledWith({
      dimension: 5,
      estado: 'confirmada',
      page: 1,
    });
    expect(origen.indicadores).toEqual(new Set([100]));
    expect(origen.criterios).toEqual(new Set([33]));
    expect(origen.truncado).toBeFalse();
  });

  it('obtenerOrigenesMarco usa el filtro de estandar y marca el truncamiento', () => {
    vinculacion.listarCorrespondencias.and.returnValue(of(pagina([], 100, 'siguiente')));

    let origen: any = null;
    service.obtenerOrigenesMarco({ estandar: 41 }).subscribe((resultado) => (origen = resultado));

    expect(vinculacion.listarCorrespondencias.calls.argsFor(0)[0]).toEqual({
      estandar: 41,
      estado: 'confirmada',
      page: 1,
    });
    expect(vinculacion.listarCorrespondencias).toHaveBeenCalledTimes(1);
    expect(origen.truncado).toBeTrue();
    expect(origen.indicadores.size).toBe(0);
  });

  it('obtenerOrigenesMarco propaga el error de la API sin filtrar datos', () => {
    vinculacion.listarCorrespondencias.and.returnValue(throwError(() => ({ status: 403 })));

    let error: any = null;
    service.obtenerOrigenesMarco({ componente: 11 }).subscribe({
      next: () => fail('no debe emitir'),
      error: (err) => (error = err),
    });

    expect(error?.status).toBe(403);
  });
});
