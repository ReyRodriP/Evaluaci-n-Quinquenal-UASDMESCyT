import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Usuarios } from './usuarios';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { ToastrModule } from 'ngx-toastr';

describe('Usuarios', () => {
  let component: Usuarios;
  let fixture: ComponentFixture<Usuarios>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Usuarios, ToastrModule.forRoot(), RouterTestingModule],
      providers: [provideHttpClient(), provideHttpClientTesting()]
    })
    .compileComponents();

    fixture = TestBed.createComponent(Usuarios);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should define the main columns for the users table', () => {
    expect(component.columnas).toContain('Nombre');
    expect(component.columnas).toContain('Correo');
    expect(component.columnas).toContain('Departamento');
    expect(component.columnas).toContain('Rol');
    expect(component.columnas).toContain('Estado');
  });
});
