import {
  HttpErrorResponse,
  HttpEvent,
  HttpHandler,
  HttpRequest,
  HttpResponse,
} from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { of, throwError } from 'rxjs';

import { AuthService } from '../../features/auth/services/auth-service';
import { AuthInterceptor } from './auth.interceptor';

describe('AuthInterceptor', () => {
  let interceptor: AuthInterceptor;
  let authService: jasmine.SpyObj<AuthService>;
  let router: jasmine.SpyObj<Router>;

  beforeEach(() => {
    authService = jasmine.createSpyObj<AuthService>(
      'AuthService',
      ['getToken', 'getUser', 'refreshViaCookie', 'saveToken', 'logout'],
    );
    router = jasmine.createSpyObj<Router>('Router', ['navigate']);

    TestBed.configureTestingModule({
      providers: [
        AuthInterceptor,
        { provide: AuthService, useValue: authService },
        { provide: Router, useValue: router },
      ],
    });

    interceptor = TestBed.inject(AuthInterceptor);
  });

  it('refreshes when the access cookie expired but the local user still exists', () => {
    authService.getToken.and.returnValue(null);
    authService.getUser.and.returnValue({ id: 7 });
    authService.refreshViaCookie.and.returnValue(of({ access: 'renewed-access-token' }));

    const handler = jasmine.createSpyObj<HttpHandler>('HttpHandler', ['handle']);
    handler.handle.and.returnValues(
      throwError(() => new HttpErrorResponse({ status: 401 })),
      of(new HttpResponse({ status: 200, body: { results: [] } })),
    );

    let response: HttpEvent<unknown> | undefined;
    interceptor.intercept(new HttpRequest('GET', '/api/notificaciones/'), handler)
      .subscribe((value) => response = value);

    expect(authService.refreshViaCookie).toHaveBeenCalledTimes(1);
    expect(authService.saveToken).toHaveBeenCalledWith('renewed-access-token');
    expect(handler.handle).toHaveBeenCalledTimes(2);
    expect(response instanceof HttpResponse).toBeTrue();
  });

  it('clears the local session and routes to login when refresh is rejected', () => {
    authService.getToken.and.returnValue(null);
    authService.getUser.and.returnValue({ id: 7 });
    authService.refreshViaCookie.and.returnValue(throwError(() => new HttpErrorResponse({ status: 401 })));

    const handler = jasmine.createSpyObj<HttpHandler>('HttpHandler', ['handle']);
    handler.handle.and.returnValue(throwError(() => new HttpErrorResponse({ status: 401 })));

    interceptor.intercept(new HttpRequest('GET', '/api/notificaciones/'), handler).subscribe({ error: () => {} });

    expect(authService.logout).toHaveBeenCalled();
    expect(router.navigate).toHaveBeenCalledWith(['/auth/login']);
  });
});
