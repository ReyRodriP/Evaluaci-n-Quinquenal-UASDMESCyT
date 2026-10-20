import { TestBed } from '@angular/core/testing';
import { PermisosService } from './permisos.service';
import { AuthService } from '../../features/auth/services/auth-service';

describe('PermisosService', () => {
  let usuario: any;
  let servicio: PermisosService;

  beforeEach(() => {
    usuario = { is_superuser: false, groups: [], permisos: [] };
    TestBed.configureTestingModule({
      providers: [PermisosService, { provide: AuthService, useValue: { getUser: () => usuario } }],
    });
    servicio = TestBed.inject(PermisosService);
  });

  it('incluye Vínculos EQ en el menú con los roles que poseen vista de correspondencias', () => {
    const item = servicio.menuItems.find((i) => i.path === '/vinculacion');
    expect(item).toBeTruthy();
    expect(item!.label).toBe('Vínculos EQ');
    expect(item!.grupos).toContain('Administrador General');
    expect(item!.grupos).toContain('Coordinador Quinquenal');
    expect(item!.grupos).toContain('Responsable Departamental');
    expect(item!.grupos).toContain('Revisor Institucional');
    expect(item!.grupos).toContain('Consulta');
    expect(item!.grupos).not.toContain('Evaluador Externo');
  });

  it('el guard de la ruta permite a los grupos autorizados y bloquea al evaluador externo', () => {
    usuario = { ...usuario, groups: ['Consulta'] };
    expect(servicio.puedeAccederRuta('/vinculacion')).toBeTrue();

    usuario = { ...usuario, groups: ['Responsable Departamental'] };
    expect(servicio.puedeAccederRuta('/vinculacion')).toBeTrue();

    usuario = { ...usuario, groups: ['Evaluador Externo'] };
    expect(servicio.puedeAccederRuta('/vinculacion')).toBeFalse();
  });

  it('el superusuario ve Vínculos EQ en el menú', () => {
    usuario = { ...usuario, is_superuser: true };
    expect(servicio.menuVisible().some((i) => i.path === '/vinculacion')).toBeTrue();
    expect(servicio.puedeAccederRuta('/vinculacion')).toBeTrue();
  });

  it('un usuario de Consulta ve Vínculos EQ en el menú y el externo no', () => {
    usuario = { ...usuario, groups: ['Consulta'] };
    expect(servicio.menuVisible().some((i) => i.path === '/vinculacion')).toBeTrue();

    usuario = { ...usuario, groups: ['Evaluador Externo'] };
    expect(servicio.menuVisible().some((i) => i.path === '/vinculacion')).toBeFalse();
  });
});
