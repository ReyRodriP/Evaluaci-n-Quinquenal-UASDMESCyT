import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ToastrService } from 'ngx-toastr';
import { AuthService } from '../auth/services/auth-service';
import { SearchBar } from '../../shared/components/CRUD/search-bar/search-bar';
import { CrudTable } from '../../shared/components/CRUD/crud-table/crud-table';

@Component({
  selector: 'app-auditorias',
  imports: [CommonModule, SearchBar, CrudTable],
  templateUrl: './auditorias.html',
  styleUrl: './auditorias.css',
})
export class Auditorias implements OnInit {
  allRows: any[] = [];
  filteredRows: any[] = [];
  searchTerm = '';
  loading = false;

  stats = {
    totalHoy: 0,
    usuariosActivos: 0,
    aprobaciones: 0,
    observaciones: 0,
  };

  constructor(
    private authService: AuthService,
    private toast: ToastrService
  ) {}

  ngOnInit(): void {
    this.loadData();
  }

  loadData(): void {
    this.loading = true;
    this.authService.listarAuditorias().subscribe({
      next: (data) => {
        this.allRows = data;
        this.computeStats();
        this.applySearch();
        this.loading = false;
      },
      error: () => {
        this.toast.error('No se pudieron cargar los registros de auditoría');
        this.loading = false;
      },
    });
  }

  computeStats(): void {
    const hoy = new Date();
    const hoyStr = hoy.toISOString().slice(0, 10);

    const hoyEntries = this.allRows.filter((r) => {
      const f = (r.fecha || '').slice(0, 10);
      return f === hoyStr;
    });

    this.stats.totalHoy = hoyEntries.length;
    this.stats.usuariosActivos = new Set(hoyEntries.map((r) => r.usuario_nombre)).size;
    this.stats.aprobaciones = this.allRows.filter((r) =>
      (r.accion || '').toLowerCase().includes('aprob')
    ).length;
    this.stats.observaciones = this.allRows.filter((r) =>
      (r.accion || '').toLowerCase().includes('observ')
    ).length;
  }

  onSearch(term: string): void {
    this.searchTerm = term;
    this.applySearch();
  }

  applySearch(): void {
    const term = this.searchTerm.toLowerCase().trim();
    if (!term) {
      this.filteredRows = [...this.allRows];
      return;
    }
    this.filteredRows = this.allRows.filter((r) =>
      [r.usuario_nombre, r.accion, r.modelo, r.descripcion, r.fecha]
        .some((v) => v && v.toLowerCase().includes(term))
    );
  }
}
