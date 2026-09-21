import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ClipboardCheck, LucideAngularModule, RotateCw, Swords, Trophy, Users } from 'lucide-angular';
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';
import { InputTextModule } from 'primeng/inputtext';
import { MessageModule } from 'primeng/message';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { SelectModule } from 'primeng/select';
import { TagModule } from 'primeng/tag';
import { TextareaModule } from 'primeng/textarea';
import { catchError, combineLatest, concat, map, of, switchMap, tap, EMPTY, finalize } from 'rxjs';

import { AgentProfile } from '../../models/agent-profile.model';
import { AuthSession } from '../../models/auth-session.model';
import { BattleDetail, BattleReplayBundle } from '../../models/battle.model';
import { Auth } from '../../services/auth/auth';
import { AgentProfileService } from '../../services/agent-profile/agent-profile';
import { BattleService } from '../../services/battle/battle';

@Component({
  selector: 'app-battle-room',
  imports: [
    CommonModule,
    ReactiveFormsModule,
    RouterLink,
    LucideAngularModule,
    ButtonModule,
    CardModule,
    InputTextModule,
    MessageModule,
    ProgressSpinnerModule,
    SelectModule,
    TagModule,
    TextareaModule,
  ],
  templateUrl: './battle-room.html',
  styleUrl: './battle-room.css',
})
export class BattleRoom {
  private readonly route = inject(ActivatedRoute);
  private readonly authService = inject(Auth);
  private readonly battleService = inject(BattleService);
  private readonly profileService = inject(AgentProfileService);

  readonly joinProfileId = new FormControl('', { nonNullable: true });
  readonly overridePath = new FormControl('app/main.py', { nonNullable: true });
  readonly overrideContent = new FormControl('', { nonNullable: true });
  readonly errorMessage = signal('');
  readonly replayBundle = signal<BattleReplayBundle | null>(null);
  readonly battleIcon = Swords;
  readonly participantIcon = Users;
  readonly submitIcon = ClipboardCheck;
  readonly replayIcon = RotateCw;
  readonly resultIcon = Trophy;

  readonly me$ = this.authService.me().pipe(catchError(() => of({ authenticated: false, user: null } as AuthSession)));
  readonly myProfiles$ = this.profileService.listMine().pipe(catchError(() => of([] as AgentProfile[])));
  readonly battleId$ = this.route.paramMap.pipe(map((params) => params.get('id') ?? ''));
  /** true enquanto o SSE stream da battle estiver ativo/aberto. */
  readonly live = signal(false);
  readonly battle$ = this.battleId$.pipe(
    switchMap((battleId) =>
      concat(
        // 1) Carrega o detail inicial normalmente.
        this.battleService.getById(battleId).pipe(catchError(() => of(null))),
        // 2) SSE alimenta os refreshes seguintes. Se cair no meio, mantém o último detail (EMPTY).
        this.battleService.stream(battleId).pipe(
          tap(() => this.live.set(true)),
          switchMap(() => this.battleService.getById(battleId).pipe(catchError(() => of(null)))),
          catchError(() => EMPTY),
          finalize(() => this.live.set(false))
        )
      )
    )
  );
  readonly vm$ = combineLatest([this.me$, this.myProfiles$, this.battle$]).pipe(
    map(([session, profiles, detail]) => {
      if (!this.joinProfileId.value && profiles.length > 0) {
        this.joinProfileId.setValue(profiles[0].id);
      }
      return {
        session,
        profiles,
        profileOptions: profiles.map((profile) => ({
          label: `${profile.name} · ${profile.archetype}`,
          value: profile.id,
        })),
        detail,
      };
    })
  );

  joinBattle(detail: BattleDetail) {
    this.errorMessage.set('');
    const profileId = this.joinProfileId.value;
    const workspaceFiles =
      this.overrideContent.value.trim().length > 0
        ? { [this.overridePath.value]: this.overrideContent.value }
        : {};
    this.battleService.join(detail.battle.id, { agent_profile_id: profileId, workspace_files: workspaceFiles }).subscribe({
      next: () => {},
      error: () => this.errorMessage.set('Nao foi possivel entrar na battle.'),
    });
  }

  submitWorkspace(detail: BattleDetail) {
    this.errorMessage.set('');
    this.battleService.submit(detail.battle.id, { [this.overridePath.value]: this.overrideContent.value }).subscribe({
      next: () => {},
      error: () => this.errorMessage.set('Falha ao atualizar a submissao.'),
    });
  }

  startBattle(detail: BattleDetail) {
    this.errorMessage.set('');
    this.battleService.start(detail.battle.id).subscribe({
      next: () => {},
      error: () => this.errorMessage.set('Nao foi possivel iniciar a battle.'),
    });
  }

  loadReplay(detail: BattleDetail) {
    this.battleService.getReplay(detail.battle.id).subscribe({
      next: (bundle) => this.replayBundle.set(bundle),
      error: () => this.errorMessage.set('Replay ainda nao esta disponivel.'),
    });
  }

  isParticipant(detail: BattleDetail, session: AuthSession): boolean {
    const userId = session.user?.id;
    return !!userId && detail.participants.some((item) => item.user_id === userId);
  }

  canStart(detail: BattleDetail, session: AuthSession): boolean {
    return detail.battle.created_by_user_id === session.user?.id && detail.battle.status === 'ready';
  }

  statusSeverity(status: string): 'success' | 'info' | 'warn' | 'danger' | 'secondary' | 'contrast' {
    if (status === 'completed') {
      return 'success';
    }
    if (status === 'failed') {
      return 'danger';
    }
    if (status === 'queued' || status === 'running') {
      return 'warn';
    }
    if (status === 'ready') {
      return 'info';
    }
    return 'secondary';
  }

  statusLabel(status: string): string {
    const labels: Record<string, string> = {
      waiting_for_opponent: 'aguardando oponente',
      ready: 'pronta',
      queued: 'na fila',
      running: 'executando',
      completed: 'concluída',
      failed: 'falhou',
    };
    return labels[status] ?? status;
  }

  participantLabel(status: string): string {
    const labels: Record<string, string> = {
      joined: 'entrou',
      ready: 'submissão pronta',
      completed: 'run concluída',
    };
    return labels[status] ?? status;
  }
}
