import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ToastrService } from 'ngx-toastr';
import { AuthService } from '../auth/services/auth-service';

@Component({
  selector: 'app-perfil',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './perfil.html',
  styleUrl: './perfil.css',
})
export class Perfil implements OnInit {
  user: any = {};
  loading = false;
  showPasswordFields = false;
  passwordPayload = {
    old_password: '',
    new_password: ''
  };

  constructor(
    private authService: AuthService,
    private toast: ToastrService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.loadProfile();
  }

  loadProfile(): void {
    this.authService.me().subscribe({
      next: (user: any) => {
        this.user = {
          ...user,
          foto_perfil: user?.foto_perfil || ''
        };
        this.authService.saveUser(this.user);
      },
      error: () => {
        this.toast.error('No se pudo cargar tu perfil');
      }
    });
  }

  onSubmit(): void {
    if (this.loading) {
      return;
    }

    this.loading = true;

    const formData = new FormData();
    formData.append('username', this.user?.username ?? '');
    formData.append('email', this.user?.email ?? '');
    formData.append('first_name', this.user?.first_name ?? '');
    formData.append('last_name', this.user?.last_name ?? '');
    formData.append('telefono', this.user?.telefono ?? '');

    if (this.user?.foto_perfil instanceof File) {
      formData.append('foto_perfil', this.user.foto_perfil);
    }

    this.authService.updateProfile(formData).subscribe({
      next: (updatedUser) => {
        this.user = {
          ...this.user,
          ...updatedUser
        };
        this.authService.saveUser(this.user);
        this.toast.success('Perfil actualizado correctamente');
      },
      error: () => {
        this.toast.error('No se pudo actualizar el perfil');
      },
      complete: () => {
        this.loading = false;
      }
    });
  }

  togglePasswordFields(): void {
    this.showPasswordFields = !this.showPasswordFields;
    if (!this.showPasswordFields) {
      this.passwordPayload = { old_password: '', new_password: '' };
    }
  }

  changePassword(): void {
    if (!this.passwordPayload.old_password || !this.passwordPayload.new_password) {
      this.toast.error('Completa ambos campos de contraseña');
      return;
    }

    this.authService.changePassword(this.passwordPayload).subscribe({
      next: () => {
        this.toast.success('Contraseña actualizada correctamente');
        this.showPasswordFields = false;
        this.passwordPayload = { old_password: '', new_password: '' };
      },
      error: () => {
        this.toast.error('No se pudo cambiar la contraseña');
      }
    });
  }

  onPhotoSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];

    if (!file) {
      return;
    }

    const reader = new FileReader();
    this.user = {
      ...this.user,
      foto_perfil: file
    };
  }

  getPhotoUrl(): string {
    if (this.user?.foto_perfil instanceof File) {
      return URL.createObjectURL(this.user.foto_perfil);
    }

    if (typeof this.user?.foto_perfil === 'string' && this.user.foto_perfil) {
      return this.user.foto_perfil;
    }

    return 'img/noUser.png';
  }

  goBack(): void {
    this.router.navigate(['/dashboard']);
  }
}
