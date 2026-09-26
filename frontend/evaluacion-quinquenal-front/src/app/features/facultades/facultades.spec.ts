import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Facultades } from './facultades';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { ToastrModule } from 'ngx-toastr';

describe('Facultades', () => {
  let component: Facultades;
  let fixture: ComponentFixture<Facultades>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Facultades, ToastrModule.forRoot(), RouterTestingModule],
      providers: [provideHttpClient(), provideHttpClientTesting()]
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
