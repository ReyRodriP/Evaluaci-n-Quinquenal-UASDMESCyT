import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { firstValueFrom, of } from 'rxjs';

import { AuthService } from '../../features/auth/services/auth-service';
import { AuthGuard } from './auth.guard';

describe('AuthGuard', () => {
  let guard: AuthGuard;
  let authService: jasmine.SpyObj<AuthService>;
  let router: jasmine.SpyObj<Router>;

  beforeEach(() => {
    authService = jasmine.createSpyObj<AuthService>('AuthService', ['isLoggedIn', 'getUser', 'me', 'logout']);
    router = jasmine.createSpyObj<Router>('Router', ['parseUrl']);
    router.parseUrl.and.returnValue({} as any);

    TestBed.configureTestingModule({
      providers: [
        AuthGuard,
        { provide: AuthService, useValue: authService },
        { provide: Router, useValue: router },
      ],
    });
    guard = TestBed.inject(AuthGuard);
  });

  it('validates the session through /me when the access token is expired', async () => {
    authService.isLoggedIn.and.returnValue(false);
    authService.getUser.and.returnValue({ id: 12 });
    authService.me.and.returnValue(of({ id: 12 }));

    const result = await firstValueFrom(guard.canActivate() as ReturnType<AuthService['me']>);

    expect(result).toBeTrue();
    expect(authService.me).toHaveBeenCalled();
    expect(router.parseUrl).not.toHaveBeenCalled();
  });

  it('redirects to login when no local session exists', () => {
    authService.isLoggedIn.and.returnValue(false);
    authService.getUser.and.returnValue(null);

    guard.canActivate();

    expect(router.parseUrl).toHaveBeenCalledWith('/auth/login');
    expect(authService.me).not.toHaveBeenCalled();
  });
});
