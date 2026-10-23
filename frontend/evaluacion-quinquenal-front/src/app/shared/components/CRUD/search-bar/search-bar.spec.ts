import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SearchBar } from './search-bar';

describe('SearchBar', () => {
  let component: SearchBar;
  let fixture: ComponentFixture<SearchBar>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SearchBar]
    })
    .compileComponents();

    fixture = TestBed.createComponent(SearchBar);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('conserva el texto predeterminado y permite personalizar el alta por pantalla', () => {
    expect(fixture.nativeElement.querySelector('button.btn-primary').textContent.trim()).toBe('+ Nuevo Registro');
    fixture.componentRef.setInput('createLabel', 'Asignar indicador del marco'); fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('button.btn-primary').textContent.trim()).toBe('Asignar indicador del marco');
    const crear = spyOn(component.create, 'emit');
    fixture.nativeElement.querySelector('button.btn-primary').click();
    expect(crear).toHaveBeenCalledTimes(1);
  });
});
