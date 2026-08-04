import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Facultades } from './facultades';

describe('Facultades', () => {
  let component: Facultades;
  let fixture: ComponentFixture<Facultades>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Facultades]
    })
    .compileComponents();

    fixture = TestBed.createComponent(Facultades);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
