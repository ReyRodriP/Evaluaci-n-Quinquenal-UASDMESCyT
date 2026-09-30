import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { ToastrService } from 'ngx-toastr';
import { Organizacion } from './organizacion';
import { OrganizacionService } from '../../core/services/organizacion.service';

describe('Organizacion', () => {
  let component: Organizacion;
  let fixture: ComponentFixture<Organizacion>;

  beforeEach(async () => {
    const organizacionService = {
      listarTiposUnidad: () => of([{ id: 1, nombre: 'Universidad' }, { id: 2, nombre: 'Recinto' }]),
      listarUnidadesOrganizacionales: () => of([
        { id: 1, nombre: 'UASD', tipo: 1, tipo_nombre: 'Universidad', unidad_padre: null, activa: true },
        { id: 2, nombre: 'Recinto Barahona', tipo: 2, tipo_nombre: 'Recinto', unidad_padre: 1, activa: true },
      ]),
    };

    await TestBed.configureTestingModule({
      imports: [Organizacion],
      providers: [
        { provide: OrganizacionService, useValue: organizacionService },
        { provide: ToastrService, useValue: { success: () => {}, error: () => {} } },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(Organizacion);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('construye el árbol organizacional con sus niveles', () => {
    expect(component.unitTree.length).toBe(1);
    expect(component.unitTree[0].unit.nombre).toBe('UASD');
    expect(component.unitTree[0].children[0].unit.nombre).toBe('Recinto Barahona');
  });

  it('cuenta unidades por tipo', () => {
    expect(component.countByType(2)).toBe(1);
  });
});