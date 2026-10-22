export interface NodoRutaMarco {
  id: number;
  codigo: string;
  nombre: string;
}

export interface RutaMarcoAsignacion {
  version: { id: number; nombre: string; slug: string; activo: boolean };
  dimension: NodoRutaMarco;
  componente: NodoRutaMarco;
  criterio: NodoRutaMarco;
  estandar: NodoRutaMarco;
  indicador: NodoRutaMarco & { orden: number; codigo_sintetico: boolean };
}

export function rutaCoincideConMarco(
  ruta: RutaMarcoAsignacion | undefined,
  filtros: { dimension?: string; componente?: string; estandar?: string }
): boolean {
  if (!ruta) return false;
  return (!filtros.dimension || String(ruta.dimension.id) === filtros.dimension)
    && (!filtros.componente || String(ruta.componente.id) === filtros.componente)
    && (!filtros.estandar || String(ruta.estandar.id) === filtros.estandar);
}
