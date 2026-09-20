import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { BehaviorSubject, catchError, combineLatest, map, of, switchMap } from 'rxjs';

import { BattleDetail, BattleReplayBundle } from '../../models/battle.model';
import { BattleService } from '../../services/battle/battle';

@Component({
  selector: 'app-replays',
  imports: [CommonModule, RouterLink],
  templateUrl: './replays.html',
  styleUrl: './replays.css',
})
export class Replays {
  private readonly route = inject(ActivatedRoute);
  private readonly battleService = inject(BattleService);

  private readonly battleId$ = this.route.paramMap.pipe(map((params) => params.get('battleId')));

  readonly battles$ = this.battleId$.pipe(
    switchMap((battleId) =>
      battleId
        ? of([] as BattleDetail[])
        : this.battleService.list().pipe(
            catchError(() => of([] as BattleDetail[])),
            map((battles) =>
              [...battles].sort(
                (a, b) =>
                  new Date(b.battle.created_at).getTime() - new Date(a.battle.created_at).getTime()
              )
            )
          )
    )
  );

  readonly detailView$ = this.battleId$.pipe(
    switchMap((battleId) =>
      battleId
        ? combineLatest([
            this.battleService.getById(battleId).pipe(catchError(() => of(null as BattleDetail | null))),
            this.battleService
              .getReplay(battleId)
              .pipe(catchError(() => of(null as BattleReplayBundle | null))),
          ]).pipe(map(([battle, replay]) => ({ battle, replay })))
        : of(null)
    )
  );

  statusLabel(status: string): string {
    const labels: Record<string, string> = {
      waiting_for_opponent: 'Aguardando oponente',
      running: 'Em andamento',
      completed: 'Concluída',
      failed: 'Falhou',
    };
    return labels[status] ?? status;
  }

  seatLabel(battle: BattleDetail, participantId: string): string {
    const seat = battle.participants.find((p) => p.id === participantId)?.seat;
    return seat === 'left' ? 'Esquerda' : seat === 'right' ? 'Direita' : 'Não definida';
  }
}