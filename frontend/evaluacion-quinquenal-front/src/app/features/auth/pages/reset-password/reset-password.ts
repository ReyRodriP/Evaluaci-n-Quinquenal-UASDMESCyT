import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { ToastrService } from 'ngx-toastr';
import { AuthService } from '../../services/auth-service';

@Component({
  selector: 'app-reset-password',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './reset-password.html',
  styleUrl: './reset-password.css',
})
export class ResetPassword {
  resetForm: FormGroup;
  uid: string | null = null;
  token: string | null = null;

  constructor(
    private fb: FormBuilder,
    private authService: AuthService,
    private route: ActivatedRoute,
    private router: Router,
    private toast: ToastrService,
  ) {
    this.resetForm = this.fb.group({
      new_password: ['', [Validators.required, Validators.minLength(6)]],
      confirm_password: ['', [Validators.required, Validators.minLength(6)]],
    });

    this.route.queryParamMap.subscribe((params) => {
      this.uid = params.get('uid');
      this.token = params.get('token');
    });
  }

  onSubmit(): void {
    if (this.resetForm.valid) {
      const { new_password, confirm_password } = this.resetForm.value;

      if (new_password !== confirm_password) {
        this.toast.error('Las contraseñas no coinciden.');
        return;
      }

      this.authService.resetPassword({ uid: this.uid, token: this.token, new_password }).subscribe({
        next: () => {
          this.toast.success('Contraseña restablecida correctamente.');
          setTimeout(() => this.router.navigate(['/auth/login']), 1200);
        },
        error: () => {
          this.toast.error('El enlace de recuperación no es válido o ha expirado.');
        },
      });
    }
  }
}
