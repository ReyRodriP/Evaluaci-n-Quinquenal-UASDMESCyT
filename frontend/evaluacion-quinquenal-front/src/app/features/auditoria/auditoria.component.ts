import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../core/services/api.service';
import { AuditoriaEntry } from '../../core/models/evidencia.model';

@Component({
  selector: 'app-auditoria',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './auditoria.component.html',
})
export class AuditoriaComponent implements OnInit {
  entries: AuditoriaEntry[] = [];

  constructor(private api: ApiService) {}

  ngOnInit() {
    this.api.getAuditoria().subscribe(data => this.entries = data);
  }
}
