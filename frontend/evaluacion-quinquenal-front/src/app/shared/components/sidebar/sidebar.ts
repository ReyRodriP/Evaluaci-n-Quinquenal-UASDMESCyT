import { Component, Renderer2, ElementRef, Output, EventEmitter } from '@angular/core';
import { RouterLink, Router } from "@angular/router";
import { CommonModule } from '@angular/common';
import { AuthService } from '../../../features/auth/services/auth-service';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [RouterLink, CommonModule],
  templateUrl: './sidebar.html',
  styleUrls: ['./sidebar.css', '../navbar/navbar.css'],
})
export class Sidebar {
  darkMode: boolean = false
  open: boolean = false

  @Output() openChange = new EventEmitter<boolean>()

  constructor (
    private renderer: Renderer2,
    private el: ElementRef,
    private authService: AuthService,
    private router: Router
  ) {}

  get user() {
    return this.authService.getCurrentUser();
  }

  public toggleTheme(): void {
    const texto = this.el.nativeElement.querySelector('.mode-text')
    this.darkMode = !this.darkMode;

    if (this.darkMode) {
      this.renderer.addClass(document.body, 'dark')
      texto.innerText = 'Modo claro'
    } else {
      this.renderer.removeClass(document.body, 'dark')
      texto.innerText = 'Modo oscuro'
    }
  }

  public toggleSidebar(): void {
    this.open = !this.open
    this.openChange.emit(this.open)
  }

  logout(): void {
    this.authService.logout();
    this.router.navigate(['/auth/login']);
  }
}
