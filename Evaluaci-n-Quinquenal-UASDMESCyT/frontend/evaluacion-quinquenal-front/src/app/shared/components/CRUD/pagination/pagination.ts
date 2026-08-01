import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-pagination',
  imports: [CommonModule],
  templateUrl: './pagination.html',
  styleUrl: './pagination.css',
})
export class Pagination {
  @Input() total = 0;
  @Input() page = 1;
  @Input() pageSize = 10;

  @Output() pageChange = new EventEmitter<number>();

  get totalPages(): number {
    return this.total > 0 ? Math.ceil(this.total / this.pageSize) : 1;
  }

  get startItem(): number {
    return this.total === 0 ? 0 : (this.page - 1) * this.pageSize + 1;
  }

  get endItem(): number {
    return Math.min(this.page * this.pageSize, this.total);
  }

  get pages(): number[] {
    const total = this.totalPages;
    const current = this.page;

    if (total <= 7) {
      return Array.from({ length: total }, (_, i) => i + 1);
    }

    let inicio = Math.max(1, current - 2);
    let fin = Math.min(total, inicio + 4);
    inicio = Math.max(1, fin - 4);

    const pages: number[] = [];
    for (let i = inicio; i <= fin; i++) {
      pages.push(i);
    }
    return pages;
  }

  ir(pagina: number): void {
    if (pagina < 1 || pagina > this.totalPages || pagina === this.page) {
      return;
    }
    this.pageChange.emit(pagina);
  }
}
