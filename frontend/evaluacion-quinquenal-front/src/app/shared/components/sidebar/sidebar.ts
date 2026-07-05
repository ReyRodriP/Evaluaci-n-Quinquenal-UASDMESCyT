import { Component, Renderer2, ElementRef, Output, EventEmitter } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../../features/auth/services/auth-service';

@Component({
  selector: 'app-sidebar',
  imports: [RouterLink],
  templateUrl: './sidebar.html',
  styleUrls: ['./sidebar.css', '../navbar/navbar.css'],
})
export class Sidebar {
  darkMode: boolean = false
  open: boolean = false
  currentUser: any = null

  @Output() openChange = new EventEmitter<boolean>()

  constructor(
    private renderer: Renderer2,
    private el: ElementRef,
    private authService: AuthService,
    private router: Router
  ){
    this.loadUser();
  }

  private loadUser(): void {
    const storedUser = this.authService.getUser();
    if (storedUser) {
      this.currentUser = storedUser;
      return;
    }

    this.authService.me().subscribe({
      next: (user) => {
        this.currentUser = user;
        this.authService.saveUser(user);
      },
      error: () => {
        this.currentUser = null;
      }
    });
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

  public onLogout(): void {
    this.authService.logoutApi().subscribe({
      next: () => {
        this.authService.logout();
        this.router.navigate(['/auth/login']);
      },
      error: () => {
        this.authService.logout();
        this.router.navigate(['/auth/login']);
      }
    });
  }
}
