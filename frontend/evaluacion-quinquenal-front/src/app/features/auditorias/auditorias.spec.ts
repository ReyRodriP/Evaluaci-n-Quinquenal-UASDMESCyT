import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Auditorias } from './auditorias';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { ToastrModule } from 'ngx-toastr';

describe('Auditorias', () => {
  let component: Auditorias;
  let fixture: ComponentFixture<Auditorias>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Auditorias, ToastrModule.forRoot(), RouterTestingModule],
      providers: [provideHttpClient(), provideHttpClientTesting()]
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
