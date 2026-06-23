import { Component, Input, Output, EventEmitter } from '@angular/core';

@Component({
  selector: 'app-search-bar',
  templateUrl: './search-bar.html',
  styleUrls: ['./search-bar.css'],
})
export class SearchBar {
  @Input() titulo: string = '';

  @Output() create = new EventEmitter<void>();

  onCreate() {
    this.create.emit();
  }
}
