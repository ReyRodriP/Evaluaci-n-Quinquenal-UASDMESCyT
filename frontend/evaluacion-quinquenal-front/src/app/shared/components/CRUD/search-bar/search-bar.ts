import { CommonModule } from '@angular/common';
import { Component, Input, Output, EventEmitter } from '@angular/core';

@Component({
  selector: 'app-search-bar',
  imports: [CommonModule],
  templateUrl: './search-bar.html',
  styleUrls: ['./search-bar.css'],
})
export class SearchBar {
  @Input() titulo: string = '';
  @Input() placeholder: string = 'Buscar...';
  @Input() value: string = '';
  @Input() stateOptions: string[] = ['Todas', 'Activas', 'Inactivas'];
  @Input() stateLabel: string = 'Estado';

  @Output() create = new EventEmitter<void>();
  @Output() search = new EventEmitter<string>();
  @Output() stateChange = new EventEmitter<string>();

  onCreate() {
    this.create.emit();
  }

  onSearch(event: Event) {
    const target = event.target as HTMLInputElement;
    const term = target.value.trim();
    this.value = term;
    this.search.emit(term);
  }

  onStateChange(event: Event) {
    const target = event.target as HTMLSelectElement;
    this.stateChange.emit(target.value);
  }
}
