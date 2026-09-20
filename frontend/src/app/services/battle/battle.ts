import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { BattleDetail, BattleReplayBundle, BattleResult } from '../../models/battle.model';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root',
})
export class BattleService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = environment.apiBaseUrl;

  list(): Observable<BattleDetail[]> {
    return this.http.get<BattleDetail[]>(`${this.baseUrl}/battles/`, { withCredentials: true });
  }

  create(payload: {
    quest_id: string;
    agent_profile_id: string;
    workspace_files?: Record<string, string>;
  }): Observable<BattleDetail> {
    return this.http.post<BattleDetail>(`${this.baseUrl}/battles/`, payload, { withCredentials: true });
  }

  getById(id: string): Observable<BattleDetail> {
    return this.http.get<BattleDetail>(`${this.baseUrl}/battles/${id}`, { withCredentials: true });
  }

  join(
    id: string,
    payload: { agent_profile_id: string; workspace_files?: Record<string, string> }
  ): Observable<BattleDetail> {
    return this.http.post<BattleDetail>(`${this.baseUrl}/battles/${id}/join`, payload, {
      withCredentials: true,
    });
  }

  submit(id: string, workspace_files: Record<string, string>): Observable<BattleDetail> {
    return this.http.post<BattleDetail>(
      `${this.baseUrl}/battles/${id}/submit`,
      { workspace_files },
      { withCredentials: true }
    );
  }

  start(id: string): Observable<BattleDetail> {
    return this.http.post<BattleDetail>(`${this.baseUrl}/battles/${id}/start`, {}, { withCredentials: true });
  }

  getResult(id: string): Observable<BattleResult> {
    return this.http.get<BattleResult>(`${this.baseUrl}/battles/${id}/result`, { withCredentials: true });
  }

  getReplay(id: string): Observable<BattleReplayBundle> {
    return this.http.get<BattleReplayBundle>(`${this.baseUrl}/battles/${id}/replay`, { withCredentials: true });
  }
}
