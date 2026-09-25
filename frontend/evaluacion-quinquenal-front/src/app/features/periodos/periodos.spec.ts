import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Periodos } from './periodos';

describe('Periodos', () => {
  let component: Periodos;
  let fixture: ComponentFixture<Periodos>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Periodos]
    })
    .compileComponents();

    fixture = TestBed.createComponent(Periodos);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
