
import { Component, Input, Output, EventEmitter, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-modal',
  imports: [CommonModule, FormsModule],
  templateUrl: './modal.html',
  styleUrls: ['./modal.css'],
})
export class Modal implements OnChanges {
  @Input() open: boolean = false;
  @Input() data: any = null;

  @Output() close = new EventEmitter<void>();
  @Output() save = new EventEmitter<any>();

  model: any = { nombre: '', descripcion: '', estado: 'Activa' };

  ngOnChanges(changes: SimpleChanges) {
    if (changes['data']) {
      if (this.data) {
        this.model = { ...this.data };
      } else if (this.open) {
        this.model = { nombre: '', descripcion: '', estado: 'Activa' };
      }
    }
    if (changes['open'] && !this.open) {
      // reset model when modal closes
      this.model = { nombre: '', descripcion: '', estado: 'Activa' };
    }
  }

  onCancel() {
    this.close.emit();
  }

  onSave() {
    this.save.emit(this.model);
  }
}
