import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';
import { DocumentosAsignacion } from './documentos-asignacion';
import { DocumentosService } from '../../../core/services/documentos.service';

describe('DocumentosAsignacion', () => {
  let fixture: ComponentFixture<DocumentosAsignacion>;
  let component: DocumentosAsignacion;
  let service: jasmine.SpyObj<DocumentosService>;
  beforeEach(async () => {
    service = jasmine.createSpyObj('DocumentosService', ['contexto', 'listar', 'crear', 'subir', 'accion', 'aprobarGlobal']);
    service.contexto.and.returnValue(of({ gestion_documental: true, puede_aportar: true, puede_definir: false, puede_revisar: false, puede_aprobar_global: false, total: 2, aprobadas: 1 }));
    service.listar.and.returnValue(of([
      { id: 1, titulo: 'Documento A', descripcion: 'Requisito A', estado: 'aprobada', versiones: [{ id: 11, numero: 1, nombre_archivo: 'a.pdf', revisiones: [] }] },
      { id: 2, titulo: 'Documento B', descripcion: 'Requisito B', estado: 'borrador', versiones: [{ id: 22, numero: 2, nombre_archivo: 'b.pdf', revisiones: [] }] },
    ]));
    await TestBed.configureTestingModule({ imports: [DocumentosAsignacion], providers: [{ provide: DocumentosService, useValue: service }] }).compileComponents();
    fixture = TestBed.createComponent(DocumentosAsignacion);
    component = fixture.componentInstance;
    fixture.componentRef.setInput('asignacionId', 26);
    fixture.detectChanges();
  });
  const texto = (f: ComponentFixture<DocumentosAsignacion>) => (f.nativeElement as HTMLElement).textContent || '';

  it('distingue documentos, versiones y aprobación global pendiente', () => {
    expect(texto(fixture)).toContain('1 de 2 documentos aprobados');
    expect(texto(fixture)).toContain('Documento A');
    expect(texto(fixture)).toContain('Versión 2');
    expect(texto(fixture)).not.toContain('Aprobar globalmente la asignación');
    expect(texto(fixture)).not.toContain('Nueva solicitud obligatoria');
  });
  it('envía la última versión de un documento específico para revisión', () => {
    service.accion.and.returnValue(of({}));
    spyOn(component.actualizado, 'emit');
    component.comentarios[2] = 'Corregir fecha';
    component.revisar(component.solicitudes[1], 'solicitar_cambios');
    expect(service.accion).toHaveBeenCalledWith(2, 'solicitar_cambios', 22, 'Corregir fecha');
    expect(component.actualizado.emit).toHaveBeenCalled();
  });
  it('muestra cierre global solo cuando el servidor lo autoriza', () => {
    service.contexto.and.returnValue(of({ gestion_documental: true, puede_aprobar_global: true, total: 2, aprobadas: 2 }));
    service.aprobarGlobal.and.returnValue(of({}));
    component.cargar(); fixture.detectChanges();
    expect(texto(fixture)).toContain('Falta la decisión global explícita');
    const button = Array.from((fixture.nativeElement as HTMLElement).querySelectorAll('button')).find(b => b.textContent?.includes('Aprobar globalmente'));
    button?.click();
    expect(service.aprobarGlobal).toHaveBeenCalledWith(26);
  });
  it('retira contenido y acciones si se pierde el ámbito al recargar', () => {
    service.contexto.and.returnValue(throwError(() => ({ status: 404 })));
    component.cargar(); fixture.detectChanges();
    expect(component.solicitudes).toEqual([]);
    expect(component.contexto).toBeNull();
    expect(texto(fixture)).not.toContain('Documento A');
    expect(texto(fixture)).toContain('perdió el acceso');
  });
  it('separa los archivos seleccionados para cada documento', () => {
    service.subir.and.returnValue(of({}));
    const a = new File(['a'], 'a.pdf'), b = new File(['b'], 'b.pdf');
    component.archivos = { 1: a, 2: b };
    component.subir(2);
    expect(service.subir).toHaveBeenCalledWith(2, b, '');
  });
});
