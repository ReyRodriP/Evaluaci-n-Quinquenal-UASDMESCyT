import { Component, Input } from '@angular/core';
import { RouterLink, Router } from "@angular/router";
import { AuthService } from '../../../features/auth/services/auth-service';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-navbar',
  imports: [CommonModule, RouterLink],
  templateUrl: './navbar.html',
  styleUrls: ['./navbar.css', '../sidebar/sidebar.css'],
})
export class Navbar {
  @Input() sidebarOpen: boolean = false;

  constructor(private authService: AuthService, private router: Router) {}

  get user() {
    return this.authService.getCurrentUser();
  }

  get isLoggedIn() {
    return this.authService.isLoggedIn();
  }

  logout() {
    this.authService.logout();
    this.router.navigate(['/auth/login']);
  }
}
