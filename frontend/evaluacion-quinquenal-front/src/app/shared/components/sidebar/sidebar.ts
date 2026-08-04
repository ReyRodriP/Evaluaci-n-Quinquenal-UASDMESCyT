import { Component, Renderer2, ElementRef, Output, EventEmitter, OnInit, OnDestroy } from '@angular/core';
import { Router, RouterLink, NavigationEnd } from '@angular/router';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../../features/auth/services/auth-service';
import { PermisosService, MenuItem } from '../../../core/services/permisos.service';
import { filter, Subscription } from 'rxjs';

@Component({
  selector: 'app-sidebar',
  imports: [RouterLink, CommonModule],
  templateUrl: './sidebar.html',
  styleUrls: ['./sidebar.css', '../navbar/navbar.css'],
})
export class Sidebar implements OnInit, OnDestroy {
  darkMode: boolean = false
  open: boolean = false
  currentUser: any = null
  menuItems: MenuItem[] = []
  private routerSubscription?: Subscription

  @Output() openChange = new EventEmitter<boolean>()

  constructor(
    private renderer: Renderer2,
    private el: ElementRef,
    private authService: AuthService,
    private permisosService: PermisosService,
    private router: Router
  ){}

  ngOnInit(): void {
    this.loadUser();
    this.menuItems = this.permisosService.menuVisible();
    this.routerSubscription = this.router.events
      .pipe(filter(event => event instanceof NavigationEnd))
      .subscribe(() => {
        this.loadUser();
        this.menuItems = this.permisosService.menuVisible();
      });
  }

  ngOnDestroy(): void {
    this.routerSubscription?.unsubscribe();
  }

  private loadUser(): void {
    this.currentUser = this.authService.getUser();
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
