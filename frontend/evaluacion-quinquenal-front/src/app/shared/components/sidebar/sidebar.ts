<<<<<<< HEAD
import { Component, Renderer2, ElementRef, Output, EventEmitter, OnInit, OnDestroy } from '@angular/core';
import { Router, RouterLink, NavigationEnd } from '@angular/router';
import { AuthService } from '../../../features/auth/services/auth-service';
import { filter, Subscription } from 'rxjs';
=======
import { Component, Renderer2, ElementRef, Output, EventEmitter } from '@angular/core';
import { RouterLink, Router } from "@angular/router";
import { CommonModule } from '@angular/common';
import { AuthService } from '../../../features/auth/services/auth-service';
>>>>>>> Ramon_Paulino_Gil_100345706

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [RouterLink, CommonModule],
  templateUrl: './sidebar.html',
  styleUrls: ['./sidebar.css', '../navbar/navbar.css'],
})
export class Sidebar implements OnInit, OnDestroy {
  darkMode: boolean = false
  open: boolean = false
  currentUser: any = null
  private routerSubscription?: Subscription

  @Output() openChange = new EventEmitter<boolean>()

<<<<<<< HEAD
  constructor(
=======
  constructor (
>>>>>>> Ramon_Paulino_Gil_100345706
    private renderer: Renderer2,
    private el: ElementRef,
    private authService: AuthService,
    private router: Router
<<<<<<< HEAD
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
=======
  ) {}

  get user() {
    return this.authService.getCurrentUser();
>>>>>>> Ramon_Paulino_Gil_100345706
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

<<<<<<< HEAD
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
=======
  logout(): void {
    this.authService.logout();
    this.router.navigate(['/auth/login']);
>>>>>>> Ramon_Paulino_Gil_100345706
  }
}
