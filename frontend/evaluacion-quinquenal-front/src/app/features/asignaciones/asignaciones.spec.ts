import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Asignaciones } from './asignaciones';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { ToastrModule } from 'ngx-toastr';

describe('Asignaciones', () => {
  let component: Asignaciones;
  let fixture: ComponentFixture<Asignaciones>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Asignaciones, ToastrModule.forRoot(), RouterTestingModule],
      providers: [provideHttpClient(), provideHttpClientTesting()]
    })
    .compileComponents();

    fixture = TestBed.createComponent(Asignaciones);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
