import { Component, OnInit, signal } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { AuthService } from './features/auth/services/auth-service';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App implements OnInit {
  protected readonly title = signal('evaluacion-quinquenal-front');

  constructor(private authService: AuthService) {}

  ngOnInit(): void {
    if (this.authService.isLoggedIn()) {
      this.authService.me().subscribe({
        next: (user) => this.authService.saveUser(user),
        error: (err: any) => {
          if (err?.status === 401) {
            this.authService.logout();
          }
        },
      });
    }
    this.bloquearCopia();
  }

  private bloquearCopia(): void {
    const esCampoDeEdicion = (e: Event): boolean => {
      const t = e.target as HTMLElement | null;
      return !!t?.closest?.('input, textarea, select, [contenteditable="true"]');
    };

    document.addEventListener('copy', (e) => { if (!esCampoDeEdicion(e)) e.preventDefault(); }, true);
    document.addEventListener('cut', (e) => { if (!esCampoDeEdicion(e)) e.preventDefault(); }, true);
    document.addEventListener('paste', (e) => { if (!esCampoDeEdicion(e)) e.preventDefault(); }, true);
    document.addEventListener('contextmenu', (e) => { if (!esCampoDeEdicion(e)) e.preventDefault(); }, true);
    document.addEventListener('dragstart', (e) => { if (!esCampoDeEdicion(e)) e.preventDefault(); }, true);
  }
}
