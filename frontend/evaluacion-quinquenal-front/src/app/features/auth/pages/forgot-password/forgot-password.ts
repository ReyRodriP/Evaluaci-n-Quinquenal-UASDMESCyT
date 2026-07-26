import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormGroup, FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink, RouterModule } from "@angular/router";
import { AuthService } from '../../services/auth-service';
import { ToastrService } from 'ngx-toastr';

@Component({
  selector: 'app-forgot-password',
  standalone: true,
  imports: [RouterLink, CommonModule, ReactiveFormsModule, RouterModule],
  templateUrl: './forgot-password.html',
  styleUrl: '../login/login.css',
})
export class ForgotPassword {
  forgotForm: FormGroup;

  constructor(private fb: FormBuilder, private authService: AuthService, private router: Router, private toast: ToastrService) {
    this.forgotForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
    });
  }

  onSubmit() {
    if(this.forgotForm.valid) {
      this.authService.forgotPassword(this.forgotForm.value.email).subscribe({
        next:()=> {
          this.toast.success('Revisa tu correo para las instrucciones');
          setTimeout(()=> {
            this.router.navigate(['/auth/login']);
          }, 2000)
        },
        error:(err)=> {
          console.log(err);
          this.toast.error(err.error?.email?.[0] || 'Error al enviar el correo');
        }
      })
    }
  }
}