import { Component } from '@angular/core';
import { RouterLink } from "@angular/router";
import { Navbar } from "../navbar/navbar";
import { Register } from '../../../features/auth/pages/register/register';

@Component({
  selector: 'app-sidebar',
  imports: [RouterLink, Navbar],
  templateUrl: './sidebar.html',
  styleUrl: './sidebar.css',
})
export class Sidebar {

}
