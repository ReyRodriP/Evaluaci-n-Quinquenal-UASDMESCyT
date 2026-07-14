import { Component, Input, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, Router } from "@angular/router";
import { AuthService } from '../../../features/auth/services/auth-service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-navbar',
  imports: [CommonModule],
  templateUrl: './navbar.html',
  styleUrls: ['./navbar.css', '../sidebar/sidebar.css'],
})
export class Navbar implements OnInit {
  @Input() sidebarOpen: boolean = false

  notificaciones: any[] = []
  dropdownOpen = false
  private polling?: ReturnType<typeof setInterval>

  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.cargarNotificaciones()
    this.polling = setInterval(() => this.cargarNotificaciones(), 30000)
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
