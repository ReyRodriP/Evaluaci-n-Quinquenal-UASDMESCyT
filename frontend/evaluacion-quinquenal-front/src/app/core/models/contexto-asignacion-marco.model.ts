import { RutaMarcoAsignacion } from './asignacion-marco.model';

export interface ContextoAsignacionMarco {
  periodo: { id: number; nombre: string };
  version: { id: number; nombre: string; activo: boolean };
  unidades: { id: number; nombre: string; ruta: string; tipo: string }[];
  indicadores: { id: number; ruta: RutaMarcoAsignacion }[];
  encargados: { id: number; username: string; nombre: string }[];
  asignaciones_existentes: { id: number; indicador_marco: number }[];
}
