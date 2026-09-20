import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { catchError, of } from 'rxjs';

import { AgentProfile } from '../../models/agent-profile.model';
import { AgentProfileService } from '../../services/agent-profile/agent-profile';

@Component({
  selector: 'app-agent-profile-list',
  imports: [CommonModule, RouterLink],
  templateUrl: './agent-profile-list.html',
  styleUrl: './agent-profile-list.css',
})
export class AgentProfileList {
  private readonly profileService = inject(AgentProfileService);

  readonly profiles$ = this.profileService.listMine().pipe(
    catchError(() => this.profileService.list())
  );
}