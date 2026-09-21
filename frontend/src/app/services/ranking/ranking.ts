import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { LeaderboardEntry } from '../../models/battle.model';
import { RankingEntry } from '../../models/ranking-entry.model';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root',
})
export class RankingService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = environment.apiBaseUrl;

  listForQuest(questId: string): Observable<RankingEntry[]> {
    return this.http.get<RankingEntry[]>(`${this.baseUrl}/rankings/quests/${questId}`);
  }

  listLeaderboard(): Observable<LeaderboardEntry[]> {
    return this.http.get<LeaderboardEntry[]>(`${this.baseUrl}/leaderboard/`, { withCredentials: true });
  }
}
