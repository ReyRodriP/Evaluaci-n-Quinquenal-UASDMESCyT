import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { AuthService } from '../../services/auth-service';
import { Router } from '@angular/router';
import { ToastrService } from 'ngx-toastr';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule], //Reactive form porque incluye validaciones
  templateUrl: './register.html',
  styleUrl: './register.css',
})
export class Register {
  registerForm: FormGroup;

  constructor(
    private fb:FormBuilder, 
    private authService:AuthService, 
    private router:Router,
    private toast:ToastrService
  ) {
    this.registerForm = this.fb.group({
      username:["", Validators.required],
      email: ["", [Validators.required, Validators.email]],
      first_name: ["", [Validators.required, Validators.minLength(3), Validators.maxLength(20)]],
      last_name: ["", [Validators.required, Validators.minLength(3), Validators.maxLength(40)]],
      telefono: ["", [Validators.required, Validators.maxLength(10)]],
      password: ["", [Validators.required, Validators.minLength(6)]],
      passwordConfirmation: ["", [Validators.required, Validators.minLength(6)]]
    })
  }
  

  onSubmit() {
    if(this.registerForm.valid) {
      console.log(this.registerForm.value);

      this.authService.register(this.registerForm.value).subscribe({
        next:(data)=> {
          this.toast.success('Registro completado'); //Notificacion de exito

          setTimeout(()=> {
            this.router.navigate(['/auth/login']); //Redirecciona si el registro es exitoso
          }, 1500)
        },
        error:(err)=> {
          console.log(err);
          this.toast.error('Error al registrar')
        }
      })
    }
  }
}