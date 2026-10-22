import { TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';
import { SeguimientoResumenService } from './seguimiento-resumen.service';
import { EvaluacionService } from './evaluacion.service';
import { EvidenciasService } from './evidencias.service';
import { VinculacionService } from './vinculacion.service';
import { rutaCoincideConMarco } from '../models/asignacion-marco.model';

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

  it('distingue una asignación directa de la correspondencia de un indicador operativo con el mismo ID', () => {
    const ruta = {
      version: { id: 1, nombre: 'Marco técnico', slug: 'marco-tecnico', activo: false },
      dimension: { id: 5, codigo: 'VI', nombre: 'Personal académico' },
      componente: { id: 6, codigo: '6.1', nombre: 'Carrera académica' },
      criterio: { id: 11, codigo: '6.1.1', nombre: 'Criterio del marco' },
      estandar: { id: 20, codigo: '6.1.1.2', nombre: 'Estándar técnico' },
      indicador: { id: 7, codigo: '6.1.1.2-IND-01', nombre: 'Indicador del marco', orden: 1, codigo_sintetico: true },
    };
    const evaluacion = TestBed.inject(EvaluacionService) as jasmine.SpyObj<EvaluacionService>;
    const evidencias = TestBed.inject(EvidenciasService) as jasmine.SpyObj<EvidenciasService>;
    evaluacion.listarAsignacionesPagina.and.returnValue(of(pagina([
      { id: 1, indicador: 7, indicador_nombre: 'Operativo', periodo: 1, estado: 'pendiente' },
      { id: 2, indicador: null, indicador_marco: 7, tipo_origen: 'marco', indicador_nombre: 'Del marco', criterio_nombre: 'Criterio del marco', ruta_marco: ruta, periodo: 1, estado: 'pendiente' },
    ])));
    evaluacion.listarIndicadoresPagina.and.returnValue(of(pagina([{ id: 7, criterio: 11, criterio_nombre: 'Criterio operativo' }])));
    evidencias.listarEvidenciasPagina.and.returnValue(of(pagina([])));
    vinculacion.listarCorrespondencias.and.callFake(filtro => of(pagina(filtro?.estado === 'confirmada' ? [{ indicador_op: 7, destino: { texto: 'Destino operativo' } }] : [])));
    let resultado: any;
    service.cargar('1').subscribe(r => resultado = r);
    const [operativa, directa] = resultado.filas;
    expect(operativa.correspondenciaEstado).toBe('confirmada');
    expect(directa.correspondenciaEstado).toBe('directa');
    expect(directa.indicadorId).toBe('marco:7');
    expect(directa.criterioId).toBeNull();
    expect(directa.criterioNombre).toBe('Criterio del marco');
    expect(directa.codigoDestino).toBe(ruta.indicador.codigo);
    expect(resultado.metricas.conConfirmada).toBe(1);
    expect(resultado.metricas.sinConfirmada).toBe(0);
    expect(resultado.metricas.conAsignacionDirecta).toBe(1);
    expect(rutaCoincideConMarco(directa.rutaMarco, { dimension: '5', estandar: '20' })).toBeTrue();
    expect(rutaCoincideConMarco(directa.rutaMarco, { dimension: '5', estandar: '21' })).toBeFalse();
  });

  it('conserva el contexto directo aunque la consulta de correspondencias falle', () => {
    const evaluacion = TestBed.inject(EvaluacionService) as jasmine.SpyObj<EvaluacionService>;
    const evidencias = TestBed.inject(EvidenciasService) as jasmine.SpyObj<EvidenciasService>;
    evaluacion.listarAsignacionesPagina.and.returnValue(of(pagina([
      { id: 2, indicador: null, indicador_marco: 7, tipo_origen: 'marco', indicador_nombre: 'Del marco', ruta_marco: { version: { nombre: 'Marco técnico' }, indicador: { codigo: 'Interno' } } },
    ])));
    evaluacion.listarIndicadoresPagina.and.returnValue(of(pagina([])));
    evidencias.listarEvidenciasPagina.and.returnValue(of(pagina([])));
    vinculacion.listarCorrespondencias.and.returnValue(throwError(() => ({ status: 403 })));
    service.cargar('1').subscribe(resultado => {
      expect(resultado.filas[0].correspondenciaEstado).toBe('directa');
      expect(resultado.filas[0].versionMarco).toBe('Marco técnico');
      expect(resultado.metricas.conAsignacionDirecta).toBe(1);
      expect(resultado.metricas.conConfirmada).toBeNull();
    });
  });
});
