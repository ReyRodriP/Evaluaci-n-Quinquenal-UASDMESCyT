import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subscription } from 'rxjs';
import { CatalogoService } from '../../core/services/catalogo.service';

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
  imports: [CommonModule],
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

  constructor(private catalogoService: CatalogoService) {}

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
    if (this.nivelActual === 'indicadores') return;
    this.pila = [
      ...this.pila,
      { nivel: this.nivelActual, etiqueta: this.etiquetaDe(item), item },
    ];
    this.nivelActual = this.siguienteNivel(this.nivelActual);
    this.cargar();
  }

  volverAindice(indice: number): void {
    this.pila = this.pila.slice(0, indice + 1);
    this.nivelActual = this.pila[indice].nivel;
    this.cargar();
  }

  volverAInicio(): void {
    this.pila = [];
    this.nivelActual = 'versiones';
    this.cargar();
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
