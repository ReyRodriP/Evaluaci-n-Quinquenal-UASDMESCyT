import { Component, Input, OnInit, OnDestroy, HostListener, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from "@angular/router";
import { AuthService } from '../../../features/auth/services/auth-service';
import { Subject } from 'rxjs';
import { debounceTime, distinctUntilChanged } from 'rxjs/operators';

@Component({
  selector: 'app-navbar',
  imports: [CommonModule, FormsModule],
  templateUrl: './navbar.html',
  styleUrls: ['./navbar.css', '../sidebar/sidebar.css'],
})
export class Navbar implements OnInit, OnDestroy {
  @Input() sidebarOpen: boolean = false

  notificaciones: any[] = []
  dropdownOpen = false

  searchQuery = ''
  searchResults: any = {}
  searchOpen = false
  searching = false
  private searchTerms = new Subject<string>()
  private polling?: ReturnType<typeof setInterval>

  constructor(
    private authService: AuthService,
    private router: Router,
    private elementRef: ElementRef
  ) {}

  ngOnInit(): void {
    this.cargarNotificaciones()
    this.polling = setInterval(() => this.cargarNotificaciones(), 30000)
    this.searchTerms.pipe(debounceTime(300), distinctUntilChanged()).subscribe(q => this.ejecutarBusqueda(q))
  }

  ngOnDestroy(): void {
    if (this.polling) clearInterval(this.polling)
    this.searchTerms.complete()
  }

  @HostListener('document:click', ['$event'])
  onClickOutside(event: MouseEvent): void {
    if (!this.elementRef.nativeElement.contains(event.target)) {
      this.searchOpen = false
      this.dropdownOpen = false
    }
  }

  get gruposResultados(): { key: string; items: any[] }[] {
    return Object.entries(this.searchResults)
      .filter(([, arr]) => Array.isArray(arr) && arr.length > 0)
      .map(([key, arr]) => ({ key, items: arr as any[] }))
  }

  onSearchInput(value: string): void {
    this.searchQuery = value
    this.searchOpen = true
    if (value.trim().length >= 2) {
      this.searchTerms.next(value.trim())
    } else {
      this.searchResults = {}
      this.searching = false
    }
  }

  private ejecutarBusqueda(q: string): void {
    this.searching = true
    this.authService.buscar(q).subscribe({
      next: (data) => {
        this.searchResults = data
        this.searching = false
      },
      error: () => this.searching = false,
    })
  }

  get totalResultados(): number {
    return Object.values(this.searchResults).reduce((s: number, arr: any) => s + (Array.isArray(arr) ? arr.length : 0), 0)
  }

  irAResultado(item: any): void {
    this.searchOpen = false
    this.searchQuery = ''
    this.searchResults = {}
    const rutas: Record<string, string> = {
      Indicador: '/indicadores',
      Departamento: '/departamentos',
      Facultad: '/facultades',
      Criterio: '/criterios',
      Usuario: '/usuarios',
    }
    const ruta = rutas[item.tipo] || '/dashboard'
    this.router.navigate([ruta])
  }

  cerrarBusqueda(): void {
    this.searchOpen = false
  }

  cargarNotificaciones(): void {
    this.authService.listarNotificaciones().subscribe({
      next: (data) => this.notificaciones = data,
    })
  }

  get noLeidas(): number {
    return this.notificaciones.filter(n => !n.leida).length
  }

  get ultimas(): any[] {
    return this.notificaciones.slice(0, 5)
  }

  toggleDropdown(): void {
    this.dropdownOpen = !this.dropdownOpen
  }

  cerrarDropdown(): void {
    this.dropdownOpen = false
  }

  irATodas(): void {
    this.dropdownOpen = false
    this.router.navigate(['/notificaciones'])
  }

  marcarYcerrar(id: number): void {
    this.authService.marcarNotificacionLeida(id).subscribe({
      next: () => {
        const n = this.notificaciones.find(x => x.id === id)
        if (n) n.leida = true
      }
    })
  }
}