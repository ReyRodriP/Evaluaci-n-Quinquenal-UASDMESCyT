import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';
import { Usuario } from '../../core/models/user.model';
import { ToastrService } from 'ngx-toastr';

@Component({
  selector: 'app-usuarios',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './usuarios.html',
  styleUrl: './usuarios.css',
})
export class Usuarios implements OnInit {
  usuarios: Usuario[] = [];
  showModal = false;
  editMode = false;
  form: any = { username: '', email: '', first_name: '', last_name: '', telefono: '', password: '' };

  constructor(private api: ApiService, private toast: ToastrService) {}

  ngOnInit() {
    this.api.getUsuarios().subscribe(data => this.usuarios = data);
  }

  abrirModal(usuario?: Usuario) {
    if (usuario) {
      this.form = { ...usuario, password: '' };
      this.editMode = true;
    } else {
      this.form = { username: '', email: '', first_name: '', last_name: '', telefono: '', password: '' };
      this.editMode = false;
    }
    this.showModal = true;
  }

  guardar() {
    if (this.editMode) {
      const data: any = {
        username: this.form.username,
        email: this.form.email,
        first_name: this.form.first_name,
        last_name: this.form.last_name,
        telefono: this.form.telefono,
        is_active: this.form.is_active
      };
      this.api.updateUsuario(this.form.id, data).subscribe(() => {
        this.toast.success('Usuario actualizado');
        this.ngOnInit();
        this.showModal = false;
      });
    }
  }
}
