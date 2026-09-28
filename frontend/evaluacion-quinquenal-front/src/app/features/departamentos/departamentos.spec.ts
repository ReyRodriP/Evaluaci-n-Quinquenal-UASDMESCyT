import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Departamentos } from './departamentos';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { ToastrModule } from 'ngx-toastr';

describe('Departamentos', () => {
  let component: Departamentos;
  let fixture: ComponentFixture<Departamentos>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Departamentos, ToastrModule.forRoot(), RouterTestingModule],
      providers: [provideHttpClient(), provideHttpClientTesting()]
    })
    .compileComponents();

    fixture = TestBed.createComponent(Departamentos);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
