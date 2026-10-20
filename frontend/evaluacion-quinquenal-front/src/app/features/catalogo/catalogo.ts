import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { Subscription, forkJoin, of, catchError } from 'rxjs';
import { CatalogoService } from '../../core/services/catalogo.service';
import { VinculacionService } from '../../core/services/vinculacion.service';
import { EvaluacionService } from '../../core/services/evaluacion.service';
import { Correspondencia } from '../../core/models/vinculacion.model';

type Nivel =
  | 'versiones'
  | 'dimensiones'
  | 'componentes'
  | 'criterios'
  | 'estandares'
  | 'indicadores';

interface Paso {
  nivel: Nivel;
  etiqueta: string;
  item: any;
}

const TITULOS: Record<Nivel, string> = {
  versiones: 'Versiones del marco',
  dimensiones: 'Dimensiones',
  componentes: 'Componentes',
  criterios: 'Criterios',
  estandares: 'Estándares',
  indicadores: 'Indicadores',
};

@Component({
  selector: 'app-catalogo',
  imports: [CommonModule, RouterLink],
  templateUrl: './catalogo.html',
  styleUrl: './catalogo.css',
})
export class Catalogo implements OnInit {
  nivelActual: Nivel = 'versiones';
  pila: Paso[] = [];
  items: any[] = [];
  cargando = false;
  error: string | null = null;
  exportando = false;
  errorExport: string | null = null;
  private peticion?: Subscription;

  indicadorPanel: any | null = null;
  panelCargando = false;
  panelError = '';
  panelSinPermiso = false;
  correspondenciasConfirmadas: Correspondencia[] = [];
  correspondenciasPropuestas: Correspondencia[] = [];
  asignacionesPorOrigen = new Map<number, any[]>();
  asignacionesCargando = false;

  constructor(
    private catalogoService: CatalogoService,
    private vinculacionService: VinculacionService,
    private evaluacionService: EvaluacionService
  ) {}

  ngOnInit(): void {
    this.cargar();
  }

  get tituloNivel(): string {
    return TITULOS[this.nivelActual];
  }

  get versionInactiva(): boolean {
    const version = this.pila.find((p) => p.nivel === 'versiones');
    return !!version && version.item.activo === false;
  }

  cargar(): void {
    this.peticion?.unsubscribe();
    this.cargando = true;
    this.error = null;
    const ultimo = this.pila[this.pila.length - 1];
    let obs$;
    if (!ultimo) {
      obs$ = this.catalogoService.listarVersiones();
    } else {
      switch (ultimo.nivel) {
        case 'versiones':
          obs$ = this.catalogoService.listarDimensiones(ultimo.item.slug);
          break;
        case 'dimensiones':
          obs$ = this.catalogoService.listarComponentes(ultimo.item.id);
          break;
        case 'componentes':
          obs$ = this.catalogoService.listarCriterios(ultimo.item.id);
          break;
        case 'criterios':
          obs$ = this.catalogoService.listarEstandares(ultimo.item.id);
          break;
        case 'estandares':
          obs$ = this.catalogoService.listarIndicadores(ultimo.item.id);
          break;
        default:
          obs$ = undefined;
      }
    }
    if (!obs$) {
      this.cargando = false;
      return;
    }
    this.peticion = obs$.subscribe({
      next: (datos) => {
        this.items = datos;
        this.cargando = false;
      },
      error: () => {
        this.items = [];
        this.cargando = false;
        this.error = `No se pudo cargar ${TITULOS[this.nivelActual].toLowerCase()}. Verifique su conexión e inténtelo de nuevo.`;
      },
    });
  }

  seleccionar(item: any): void {
    if (this.nivelActual === 'indicadores') {
      this.abrirPanel(item);
      return;
    }
    this.cerrarPanel();
    this.pila = [
      ...this.pila,
      { nivel: this.nivelActual, etiqueta: this.etiquetaDe(item), item },
    ];
    this.nivelActual = this.siguienteNivel(this.nivelActual);
    this.cargar();
  }

  volverAindice(indice: number): void {
    this.cerrarPanel();
    this.pila = this.pila.slice(0, indice + 1);
    this.nivelActual = this.pila[indice].nivel;
    this.cargar();
  }

  volverAInicio(): void {
    this.cerrarPanel();
    this.pila = [];
    this.nivelActual = 'versiones';
    this.cargar();
  }

  abrirPanel(item: any): void {
    this.indicadorPanel = item;
    this.cargarPanel();
  }

  cerrarPanel(): void {
    this.indicadorPanel = null;
    this.correspondenciasConfirmadas = [];
    this.correspondenciasPropuestas = [];
    this.asignacionesPorOrigen = new Map();
    this.panelError = '';
    this.panelSinPermiso = false;
    this.panelCargando = false;
    this.asignacionesCargando = false;
  }

  cargarPanel(): void {
    const indicador = this.indicadorPanel;
    if (!indicador) return;
    this.panelCargando = true;
    this.panelError = '';
    this.panelSinPermiso = false;
    this.correspondenciasConfirmadas = [];
    this.correspondenciasPropuestas = [];
    this.asignacionesPorOrigen = new Map();
    forkJoin({
      confirmadas: this.vinculacionService
        .listarCorrespondencias({ estado: 'confirmada', indicador_marco: indicador.id })
        .pipe(catchError((err) => of({ __error: err }))),
      propuestas: this.vinculacionService
        .listarCorrespondencias({ estado: 'propuesta', indicador_marco: indicador.id })
        .pipe(catchError((err) => of({ __error: err }))),
    }).subscribe({
      next: ({ confirmadas, propuestas }: any) => {
        const error = confirmadas?.__error ?? propuestas?.__error;
        this.panelCargando = false;
        if (error) {
          if (error?.status === 403) {
            this.panelSinPermiso = true;
          } else {
            this.panelError = 'No se pudieron cargar las correspondencias del marco.';
          }
          return;
        }
        this.correspondenciasConfirmadas = confirmadas?.results ?? [];
        this.correspondenciasPropuestas = propuestas?.results ?? [];
        this.cargarAsignacionesOrigenes();
      },
      error: () => {
        this.panelCargando = false;
        this.panelError = 'No se pudieron cargar las correspondencias del marco.';
      },
    });
  }

  private cargarAsignacionesOrigenes(): void {
    const origenes = this.correspondenciasConfirmadas
      .map((c) => c.origen)
      .filter((origen) => !!origen && origen.nivel === 'indicador' && typeof origen.id === 'number');
    if (!origenes.length) return;
    this.asignacionesCargando = true;
    const peticiones = origenes.map((origen) =>
      this.evaluacionService.listarAsignacionesPorIndicador(origen!.id).pipe(catchError(() => of([] as any[])))
    );
    forkJoin(peticiones).subscribe((listas) => {
      const mapa = new Map<number, any[]>();
      origenes.forEach((origen, indice) => mapa.set(origen!.id, listas[indice] ?? []));
      this.asignacionesPorOrigen = mapa;
      this.asignacionesCargando = false;
    });
  }

  asignacionesDe(corr: Correspondencia): any[] {
    const id = corr.origen?.id;
    return typeof id === 'number' ? (this.asignacionesPorOrigen.get(id) ?? []) : [];
  }

  etiquetaOrigen(nivel: string): string {
    return nivel === 'indicador' ? 'Indicador operativo' : 'Criterio operativo';
  }

  get slugVersion(): string | null {
    const paso = this.pila.find((p) => p.nivel === 'versiones');
    return paso ? paso.item.slug : null;
  }

  exportar(): void {
    const slug = this.slugVersion;
    if (!slug || this.exportando) return;
    this.exportando = true;
    this.errorExport = null;
    this.catalogoService.exportarCsv(slug).subscribe({
      next: (blob) => {
        this.exportando = false;
        this.descargar(blob, `arbol_eq_sidaces_${slug}.csv`);
      },
      error: () => {
        this.exportando = false;
        this.errorExport =
          'No se pudo exportar el árbol. Verifique su conexión e inténtelo de nuevo.';
      },
    });
  }

  descargar(blob: Blob, nombre: string): void {
    const url = URL.createObjectURL(blob);
    const enlace = document.createElement('a');
    enlace.href = url;
    enlace.download = nombre;
    enlace.click();
    URL.revokeObjectURL(url);
  }

  etiquetaDe(item: any): string {
    const codigo = item.codigo || item.slug || '';
    const texto = item.nombre || item.redaccion || item.redaccion_oficial || '';
    const corto = texto.length > 60 ? texto.slice(0, 60) + '…' : texto;
    return codigo ? `${codigo} — ${corto}` : corto;
  }

  textoDe(item: any): string {
    return item.nombre || item.redaccion || item.redaccion_oficial || item.descripcion || '';
  }

  codigoDe(item: any): string {
    return item.codigo_completo || item.codigo || item.slug || '';
  }

  private siguienteNivel(nivel: Nivel): Nivel {
    const orden: Nivel[] = [
      'versiones',
      'dimensiones',
      'componentes',
      'criterios',
      'estandares',
      'indicadores',
    ];
    const i = orden.indexOf(nivel);
    return orden[Math.min(i + 1, orden.length - 1)];
  }
}
