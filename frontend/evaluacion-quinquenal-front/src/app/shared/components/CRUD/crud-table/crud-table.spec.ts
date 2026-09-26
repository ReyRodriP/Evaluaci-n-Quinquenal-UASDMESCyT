import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CrudTable } from './crud-table';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { ToastrModule } from 'ngx-toastr';

describe('CrudTable', () => {
  let component: CrudTable;
  let fixture: ComponentFixture<CrudTable>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CrudTable, ToastrModule.forRoot(), RouterTestingModule],
      providers: [provideHttpClient(), provideHttpClientTesting()]
    })
    .compileComponents();

    fixture = TestBed.createComponent(CrudTable);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should map user table columns to the expected data properties', () => {
    expect(component.getColumnKey('Nombre')).toBe('nombre');
    expect(component.getColumnKey('Correo')).toBe('correo');
    expect(component.getColumnKey('Departamento')).toBe('departamento_nombre');
  });

  it('should resolve common user values from aliases', () => {
    const item = {
      first_name: 'Ana',
      email: 'ana@example.com',
      departamento: 'Tecnología'
    };

    expect(component.getCellValue(item, 'Nombre')).toBe('Ana');
    expect(component.getCellValue(item, 'Correo')).toBe('ana@example.com');
    expect(component.getCellValue(item, 'Departamento')).toBe('Tecnología');
  });
});
