
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
  @Input() title: string = '';
  @Input() newTitle: string = '';
  @Input() editTitle: string = '';
  @Input() fields: any[] = [];

  @Output() close = new EventEmitter<void>();
  @Output() save = new EventEmitter<any>();

  model: any = {};
  searchTexts: { [key: string]: string } = {};

  ngOnChanges(changes: SimpleChanges) {
    if (changes['fields'] || changes['data'] || (changes['open'] && this.open)) {
      this.model = this.buildModel();
    }

    if (changes['open'] && !this.open) {
      this.model = this.buildModel();
    }
  }

  buildModel(): any {
    const baseModel: any = {};
    if (Array.isArray(this.fields)) {
      this.fields.forEach(field => {
        baseModel[field.name] = field.defaultValue ?? '';
      });
    }

    if (this.data) {
      return { ...baseModel, ...this.data };
    }

    return baseModel;
  }

  getModalTitle(): string {
    if (this.data) {
      return this.editTitle || `Editar ${this.title}`;
    }
    return this.newTitle || `Nueva ${this.title}`;
  }

  getFilteredOptions(field: any): any[] {
    if (!field.searchable || !this.searchTexts[field.name]) {
      return field.options || [];
    }
    const term = this.searchTexts[field.name].toLowerCase().trim();
    return (field.options || []).filter((opt: any) =>
      (opt.label ?? opt).toLowerCase().includes(term)
    );
  }

  onCancel() {
    this.close.emit();
  }

  toggleCheckbox(fieldName: string, value: any) {
    if (!Array.isArray(this.model[fieldName])) {
      this.model[fieldName] = [];
    }

    const index = this.model[fieldName].indexOf(value);
    if (index === -1) {
      this.model[fieldName].push(value);
    } else {
      this.model[fieldName].splice(index, 1);
    }
  }

  selectAll(fieldName: string, options: any[]) {
    this.model[fieldName] = options.map(option => option?.value ?? option);
  }

  clearAll(fieldName: string) {
    this.model[fieldName] = [];
  }

  onSave() {
    this.save.emit(this.model);
  }
}
