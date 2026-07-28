import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-espera',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './espera.html',
  styleUrl: './espera.css',
})
export class Espera {
}
