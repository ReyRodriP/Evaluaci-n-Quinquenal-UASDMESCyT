import { Component, Input } from '@angular/core';
import { RouterLink } from "@angular/router";

@Component({
  selector: 'app-navbar',
  imports: [],
  templateUrl: './navbar.html',
  styleUrls: ['./navbar.css', '../sidebar/sidebar.css'],
})
export class Navbar {
  @Input() sidebarOpen: boolean = false
}
