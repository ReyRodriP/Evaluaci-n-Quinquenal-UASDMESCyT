import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';
import { DocumentosAsignacion } from './documentos-asignacion';
import { DocumentosService } from '../../../core/services/documentos.service';

describe('DocumentosAsignacion', () => {
  let fixture: ComponentFixture<DocumentosAsignacion>;
  let component: DocumentosAsignacion;
  let service: jasmine.SpyObj<DocumentosService>;
  beforeEach(async () => {
    service = jasmine.createSpyObj('DocumentosService', ['contexto', 'listar', 'crear', 'subir', 'accion', 'aprobarGlobal', 'descargar']);
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

  it('abre el documento elegido desde el listado con historial y acciones del estilo de evidencia', () => {
    fixture.componentRef.setInput('solicitudId', 2); fixture.detectChanges();
    expect(component.solicitudActiva.id).toBe(2);
    expect(fixture.nativeElement.querySelector('.content-grid .versiones-card')).toBeTruthy();
    expect(fixture.nativeElement.querySelector('.content-grid .actions-card')).toBeTruthy();
    expect(texto(fixture)).toContain('b.pdf');
    expect(texto(fixture)).toContain('Enviar documento a revisión');
    expect(fixture.nativeElement.querySelector('article').textContent).not.toContain('a.pdf');
  });

  it('el revisor ve el archivo enviado y puede aprobar la versión del documento activo', () => {
    service.contexto.and.returnValue(of({ gestion_documental: true, puede_revisar: true, puede_aportar: false, total: 2, aprobadas: 0 }));
    service.listar.and.returnValue(of([{ id: 4, titulo: 'Acta', estado: 'en_revision', versiones: [{ id: 2, numero: 1, nombre_archivo: 'express.png', revisiones: [] }] }]));
    service.accion.and.returnValue(of({}));
    component.cargar(); fixture.detectChanges();
    expect(texto(fixture)).toContain('express.png');
    const boton = Array.from((fixture.nativeElement as HTMLElement).querySelectorAll('button')).find(b => b.textContent?.includes('Aprobar esta versión'));
    expect(boton).toBeTruthy(); boton?.click();
    expect(service.accion).toHaveBeenCalledWith(4, 'aprobar', 2, '');
  });

  it('muestra y libera la vista previa del archivo del documento elegido', () => {
    service.descargar.and.returnValue(of(new Blob(['imagen'], { type: 'image/png' })));
    const crear = spyOn(URL, 'createObjectURL').and.returnValue('blob:prueba');
    const liberar = spyOn(URL, 'revokeObjectURL');
    component.abrirPreview({ id: 4 }, { id: 2, nombre_archivo: 'express.png' }); fixture.detectChanges();
    expect(service.descargar).toHaveBeenCalledWith(4, 2);
    expect(crear).toHaveBeenCalled();
    expect(fixture.nativeElement.querySelector('.preview-imagen').getAttribute('src')).toBe('blob:prueba');
    component.cerrarPreview();
    expect(liberar).toHaveBeenCalledWith('blob:prueba');
  });

  it('identifica la versión exacta indicada por el reporte de observaciones', () => {
    fixture.componentRef.setInput('solicitudId', 2); fixture.componentRef.setInput('versionId', 22); fixture.detectChanges();
    const version = fixture.nativeElement.querySelector('#version-documento-22');
    expect(version.classList.contains('version-referenciada')).toBeTrue();
    expect(version.textContent).toContain('Versión vinculada a la observación');
    expect(component.solicitudActiva.id).toBe(2);
  });
});
