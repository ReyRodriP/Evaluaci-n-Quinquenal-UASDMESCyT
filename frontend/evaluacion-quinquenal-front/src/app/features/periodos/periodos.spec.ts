import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Periodos } from './periodos';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { ToastrModule } from 'ngx-toastr';

describe('Periodos', () => {
  let component: Periodos;
  let fixture: ComponentFixture<Periodos>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Periodos, ToastrModule.forRoot(), RouterTestingModule],
      providers: [provideHttpClient(), provideHttpClientTesting()]
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
