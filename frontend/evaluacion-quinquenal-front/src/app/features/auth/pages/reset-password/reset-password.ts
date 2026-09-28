import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormGroup, FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink, RouterModule, ActivatedRoute } from "@angular/router";
import { AuthService } from '../../services/auth-service';
import { ToastrService } from 'ngx-toastr';

@Component({
  selector: 'app-reset-password',
  standalone: true,
  imports: [RouterLink, CommonModule, ReactiveFormsModule, RouterModule],
  templateUrl: './reset-password.html',
  styleUrl: '../login/login.css',
})
export class ResetPassword implements OnInit {
  resetForm: FormGroup;
  uidb64: string = '';
  token: string = '';

  constructor(
    private fb: FormBuilder,
    private authService: AuthService,
    private router: Router,
    private route: ActivatedRoute,
    private toast: ToastrService
  ) {
    this.resetForm = this.fb.group({
      new_password: ['', [Validators.required, Validators.minLength(6)]],
      confirm_password: ['', [Validators.required, Validators.minLength(6)]],
    });
  }

  ngOnInit() {
    this.route.queryParams.subscribe(params => {
      this.uidb64 = params['uidb64'] || '';
      this.token = params['token'] || '';
      if (!this.uidb64 || !this.token) {
        this.toast.error('Enlace de recuperación inválido');
        this.router.navigate(['/auth/login']);
      }
    });
  }

  onSubmit() {
    if (this.resetForm.valid) {
      if (this.resetForm.value.new_password !== this.resetForm.value.confirm_password) {
        this.toast.error('Las contraseñas no coinciden');
        return;
      }

      this.authService.resetPassword({
        uidb64: this.uidb64,
        token: this.token,
        new_password: this.resetForm.value.new_password,
      }).subscribe({
        next:()=> {
          this.toast.success('Contraseña restablecida correctamente');
          setTimeout(()=> {
            this.router.navigate(['/auth/login']);
          }, 2000)
        },
        error:(err)=> {
          console.log(err);
          this.toast.error(err.error?.error || 'Error al restablecer la contraseña');
        }
      })
    }
  }
}