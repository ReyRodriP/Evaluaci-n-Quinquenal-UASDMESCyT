import { Component, Renderer2, ElementRef, Output, EventEmitter } from '@angular/core';
import { RouterLink } from "@angular/router";
import { Register } from '../../../features/auth/pages/register/register';

@Component({
  selector: 'app-sidebar',
  imports: [RouterLink],
  templateUrl: './sidebar.html',
  styleUrls: ['./sidebar.css', '../navbar/navbar.css'],
})
export class Sidebar {
  darkMode: boolean = false
  open: boolean = false

  @Output() openChange = new EventEmitter<boolean>()

  constructor (private renderer: Renderer2, private el: ElementRef){}

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
}
