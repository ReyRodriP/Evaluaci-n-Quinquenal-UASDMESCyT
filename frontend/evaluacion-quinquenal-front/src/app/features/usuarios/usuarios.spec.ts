import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Usuarios } from './usuarios';

describe('Usuarios', () => {
  let component: Usuarios;
  let fixture: ComponentFixture<Usuarios>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Usuarios]
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
