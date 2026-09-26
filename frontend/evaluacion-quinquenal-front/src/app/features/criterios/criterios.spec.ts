import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Criterios } from './criterios';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { ToastrModule } from 'ngx-toastr';

describe('Criterios', () => {
  let component: Criterios;
  let fixture: ComponentFixture<Criterios>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Criterios, ToastrModule.forRoot(), RouterTestingModule],
      providers: [provideHttpClient(), provideHttpClientTesting()]
    })
    .compileComponents();

    fixture = TestBed.createComponent(Criterios);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
