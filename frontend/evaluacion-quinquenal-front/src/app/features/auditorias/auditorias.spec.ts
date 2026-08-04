import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Auditorias } from './auditorias';

describe('Auditorias', () => {
  let component: Auditorias;
  let fixture: ComponentFixture<Auditorias>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Auditorias]
    })
    .compileComponents();

    fixture = TestBed.createComponent(Auditorias);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
