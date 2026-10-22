import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Periodos } from './periodos';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { HttpTestingController } from '@angular/common/http/testing';
import { environment } from '../../../environments/environment';
import { RouterTestingModule } from '@angular/router/testing';
import { ToastrModule } from 'ngx-toastr';

describe('Periodos', () => {
  let component: Periodos;
  let fixture: ComponentFixture<Periodos>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Periodos, ToastrModule.forRoot(), RouterTestingModule],
      providers: [provideHttpClient(), provideHttpClientTesting()]
    })
    .compileComponents();

    fixture = TestBed.createComponent(Periodos);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('permite seleccionar una versión globalmente inactiva y conserva su referencia en el guardado', () => {
    const http = TestBed.inject(HttpTestingController);
    http.expectOne(`${environment.apiUrl}/periodos/`).flush([]);
    http.expectOne(`${environment.apiUrl}/catalogo/versiones/`).flush({ results: [{ id: 1, nombre: 'Marco piloto', activo: false }], next: null });
    component.openNew();
    expect(component.periodoFields.find(c => c.name === 'version_marco')?.options[0].label).toContain('Inactiva globalmente');
    component.onModalSave({ nombre: 'P', fecha_inicio: '2026-01-01', fecha_fin: '2030-01-01', estado: 'Activo', version_marco: 1 });
    const alta = http.expectOne(`${environment.apiUrl}/periodos/`);
    expect(alta.request.body.version_marco).toBe(1); alta.flush({ id: 3 });
    http.expectOne(`${environment.apiUrl}/periodos/`).flush([]);
  });
});
