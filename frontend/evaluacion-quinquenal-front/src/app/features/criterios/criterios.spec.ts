import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Criterios } from './criterios';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { ToastrModule } from 'ngx-toastr';
import { AuthService } from '../../features/auth/services/auth-service';
import { environment } from '../../../environments/environment';

describe('Criterios', () => {
  let component: Criterios;
  let fixture: ComponentFixture<Criterios>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Criterios, ToastrModule.forRoot(), RouterTestingModule],
      providers: [provideHttpClient(), provideHttpClientTesting()]
    })
    .compileComponents();

    fixture = TestBed.createComponent(Criterios);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  function http(): HttpTestingController {
    return TestBed.inject(HttpTestingController);
  }

  function definirUsuario(usuario: any): void {
    const auth = TestBed.inject(AuthService);
    spyOn(auth, 'getUser').and.returnValue(usuario);
  }

  function resolverCargasIniciales(): void {
    const control = http();
    control
      .expectOne((r) => r.url === `${environment.apiUrl}/periodos/`)
      .flush({ count: 0, results: [] });
    control
      .expectOne((r) => r.url === `${environment.apiUrl}/criterios/` && !r.params.has('page'))
      .flush({
        count: 1,
        results: [{ id: 5, nombre: 'Criterio X', descripcion: 'Demo', periodo: 1, activo: true }],
      });
  }

  it('sin permisos de vinculación no aparece la acción Vincular', () => {
    definirUsuario({ is_superuser: false, groups: [], permisos: [] });
    resolverCargasIniciales();
    fixture.detectChanges();

    expect(fixture.nativeElement.querySelector('.accion-vincular')).toBeNull();
    expect(component.puedeVincular).toBeFalse();
  });

  it('con permiso permite proponer vínculo desde la fila con el origen correcto', () => {
    definirUsuario({
      is_superuser: false,
      groups: ['Administrador General'],
      permisos: ['vinculacion.add_correspondencia'],
    });
    resolverCargasIniciales();
    fixture.detectChanges();

    const vincular = fixture.nativeElement.querySelector('.accion-vincular') as HTMLButtonElement;
    expect(vincular).toBeTruthy();
    expect(component.puedeVincular).toBeTrue();

    vincular.click();
    fixture.detectChanges();

    expect(component.criterioVincular).toEqual({ nivel: 'criterio', id: 5, texto: 'Criterio X' });
    expect(fixture.nativeElement.querySelector('app-correspondencia-form')).toBeTruthy();
    expect(fixture.nativeElement.textContent).toContain('Criterio X');

    http()
      .expectOne((r) => r.url === `${environment.apiUrl}/catalogo/versiones/`)
      .flush({ count: 0, results: [] });
    fixture.detectChanges();
  });

  it('cancelar el formulario de vinculación cierra el panel', () => {
    definirUsuario({ is_superuser: true, groups: [], permisos: [] });
    resolverCargasIniciales();
    fixture.detectChanges();

    (fixture.nativeElement.querySelector('.accion-vincular') as HTMLButtonElement).click();
    fixture.detectChanges();
    http()
      .expectOne((r) => r.url === `${environment.apiUrl}/catalogo/versiones/`)
      .flush({ count: 0, results: [] });
    fixture.detectChanges();

    const cancelar = (Array.from(fixture.nativeElement.querySelectorAll('button')) as HTMLButtonElement[]).find(
      (b) => (b.textContent ?? '').includes('Cancelar')
    )!;
    cancelar.click();
    fixture.detectChanges();

    expect(component.criterioVincular).toBeNull();
    expect(fixture.nativeElement.querySelector('app-correspondencia-form')).toBeNull();
  });
});
