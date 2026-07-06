import { Component, Renderer2, ElementRef, Output, EventEmitter, OnInit, OnDestroy } from '@angular/core';
import { Router, RouterLink, NavigationEnd } from '@angular/router';
import { AuthService } from '../../../features/auth/services/auth-service';
import { filter, Subscription } from 'rxjs';

@Component({
  selector: 'app-sidebar',
  imports: [RouterLink],
  templateUrl: './sidebar.html',
  styleUrls: ['./sidebar.css', '../navbar/navbar.css'],
})
export class Sidebar implements OnInit, OnDestroy {
  darkMode: boolean = false
  open: boolean = false
  currentUser: any = null
  private routerSubscription?: Subscription

  @Output() openChange = new EventEmitter<boolean>()

  constructor(
    private renderer: Renderer2,
    private el: ElementRef,
    private authService: AuthService,
    private router: Router
  ){}

  ngOnInit(): void {
    this.loadUser();
    this.routerSubscription = this.router.events
      .pipe(filter(event => event instanceof NavigationEnd))
      .subscribe(() => this.loadUser());
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
