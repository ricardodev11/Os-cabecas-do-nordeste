import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { BattleDetail, BattleReplayBundle, BattleResult, BattleStreamEvent } from '../../models/battle.model';
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

  /**
   * Abre o SSE stream de status da battle (contrato: `GET /battles/{id}/stream`).
   * Emite eventos `BattleStreamEvent` conforme o backend publica no bus e
   * completa quando a battle atinge um estado terminal (completed/failed) —
   * o próprio backend fecha o stream nesse momento.
   */
  stream(id: string): Observable<BattleStreamEvent> {
    const url = `${this.baseUrl}/battles/${id}/stream`;
    return new Observable<BattleStreamEvent>((subscriber) => {
      const controller = new AbortController();
      void fetch(url, { credentials: 'include', signal: controller.signal })
        .then((response) => {
          if (!response.ok) {
            throw new Error(`SSE HTTP ${response.status}`);
          }
          if (!response.body) {
            throw new Error('SSE response sem body');
          }
          const reader = response.body.getReader();
          const decoder = new TextDecoder('utf-8');
          let buffer = '';

          const drain = async () => {
            const { done, value } = await reader.read();
            if (done) {
              subscriber.complete();
              return;
            }
            buffer += decoder.decode(value, { stream: true });
            const blocks = buffer.split('\n\n');
            buffer = blocks.pop() ?? '';
            for (const block of blocks) {
              const dataLine = block
                .split('\n')
                .find((line) => line.startsWith('data:'));
              if (!dataLine) {
                continue;
              }
              const raw = dataLine.slice(5).trim();
              if (!raw) {
                continue;
              }
              subscriber.next(JSON.parse(raw) as BattleStreamEvent);
            }
            void drain();
          };
          return drain();
        })
        .catch((error: unknown) => {
          if (!controller.signal.aborted) {
            subscriber.error(error instanceof Error ? error : new Error(String(error)));
          }
        });

      return () => controller.abort();
    });
  }
}
