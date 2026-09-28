import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Indicadores } from './indicadores';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { ToastrModule } from 'ngx-toastr';

describe('Indicadores', () => {
  let component: Indicadores;
  let fixture: ComponentFixture<Indicadores>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Indicadores, ToastrModule.forRoot(), RouterTestingModule],
      providers: [provideHttpClient(), provideHttpClientTesting()]
    })
    .compileComponents();

    fixture = TestBed.createComponent(Indicadores);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
