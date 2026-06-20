import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormGroup, FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink, RouterModule } from "@angular/router";
import { AuthService } from '../../services/auth-service';
import { ToastrService } from 'ngx-toastr';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [RouterLink, CommonModule, ReactiveFormsModule, RouterModule],
  templateUrl: './login.html',
  styleUrl: './login.css',
})
export class Login {
  loginForm: FormGroup;

  constructor(private fb: FormBuilder, private authService: AuthService, private router: Router, private toast: ToastrService) {
    this.loginForm = this.fb.group({
      username: ['', [Validators.required]],
      password: ['', [Validators.required, Validators.minLength(6)]],
    });
  }

  onSubmit() {
    if(this.loginForm.valid) {
      console.log(this.loginForm.value);

      this.authService.login(this.loginForm.value).subscribe({
        next:(data)=> {
          this.toast.success('Login completado'); //Notificacion de exito

          setTimeout(()=> {
            this.router.navigate(['/dashboard']); //Redirecciona si el login es exitoso
          }, 1500)
        },
        error:(err)=> {
          console.log(err);
          this.toast.error('Error al iniciar sesión')
        }
      })
    }
  }
}
