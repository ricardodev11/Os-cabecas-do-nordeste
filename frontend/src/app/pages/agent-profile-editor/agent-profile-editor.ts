import { CommonModule } from '@angular/common';
import { Component, inject, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

import { AgentProfile } from '../../models/agent-profile.model';
import { AgentProfileService } from '../../services/agent-profile/agent-profile';

@Component({
  selector: 'app-agent-profile-editor',
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './agent-profile-editor.html',
  styleUrl: './agent-profile-editor.css',
})
export class AgentProfileEditor implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly profileService = inject(AgentProfileService);

  isEdit = false;
  profileId = '';
  saving = false;
  error = '';
  success = '';

  readonly archetypes = ['builder', 'debugger', 'speedrunner', 'refiner'];

  form = {
    name: '',
    archetype: 'builder',
    planningStyle: '',
    stack: '',
    executor: '',
  };

  ngOnInit() {
    this.route.paramMap.subscribe((params) => {
      const id = params.get('id');
      if (id) {
        this.isEdit = true;
        this.profileId = id;
        this.profileService.get(id).subscribe({
          next: (p) => {
            this.form.name = p.name;
            this.form.archetype = p.archetype;
            this.form.planningStyle = p.planning_style;
            this.form.stack = (p.preferred_stack || []).join(', ');
            this.form.executor = p.executor || '';
          },
          error: () => {
            this.error = 'Perfil não encontrado.';
          },
        });
      }
    });
  }

  get title(): string {
    return this.isEdit ? 'Editar agente' : 'Novo agente';
  }

  save() {
    if (!this.form.name.trim()) {
      this.error = 'O nome é obrigatório.';
      return;
    }

    this.error = '';
    this.saving = true;
    const stack = this.form.stack
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean);

    const done = {
      next: () => {
        this.success = 'Salvo com sucesso!';
        setTimeout(() => this.router.navigate(['/profiles']), 800);
      },
      error: (err: unknown) => {
        this.saving = false;
        this.error = this.describeError(err);
      },
    };

    if (this.isEdit) {
      const patch: Partial<AgentProfile> = {
        name: this.form.name,
        planning_style: this.form.planningStyle,
        preferred_stack: stack,
      };
      this.profileService.update(this.profileId, patch).subscribe(done);
      return;
    }

    const payload = {
      id: `profile-${Date.now()}`,
      name: this.form.name,
      archetype: this.form.archetype,
      planning_style: this.form.planningStyle,
      preferred_stack: stack,
    } as AgentProfile;
    this.profileService.create(payload).subscribe(done);
  }

  private describeError(err: unknown): string {
    if (err && typeof err === 'object' && 'error' in err) {
      const body = (err as { error?: { detail?: string } }).error;
      if (body?.detail) {
        return String(body.detail);
      }
    }
    return 'Erro ao salvar. Tente novamente.';
  }
}