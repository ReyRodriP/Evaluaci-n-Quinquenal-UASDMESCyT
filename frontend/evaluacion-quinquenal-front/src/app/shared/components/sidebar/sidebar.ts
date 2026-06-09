import { Component } from '@angular/core';
import { RouterLink } from "@angular/router";
import { Dashboard } from '../../../layouts/admin-layout/dashboard/dashboard';
import { Usuarios } from '../../../layouts/admin-layout/usuarios/usuarios';
import { Navbar } from "../navbar/navbar";

@Component({
  selector: 'app-sidebar',
  imports: [RouterLink, Navbar],
  templateUrl: './sidebar.html',
  styleUrl: './sidebar.css',
})
export class Sidebar {

}
