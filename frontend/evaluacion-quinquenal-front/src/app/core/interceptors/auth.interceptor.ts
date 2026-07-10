import { HttpInterceptorFn, HttpRequest, HttpHandlerFn } from '@angular/common/http';

export const authInterceptor: HttpInterceptorFn = (req: HttpRequest<unknown>, next: HttpHandlerFn) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    const cloned = req.clone({
      headers: req.headers.set('Authorization', `Token ${token}`)
    });
    return next(cloned);
  }
  return next(req);
};
