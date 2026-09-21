import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, forkJoin, map } from 'rxjs';

import { ArenaEvent } from '../../models/arena-event.model';
import { PostMortem } from '../../models/post-mortem.model';
import { Run, RunArtifact } from '../../models/run.model';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root',
})
export class ArenaService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = environment.apiBaseUrl;

  createRun(payload: {
    quest_id: string;
    agent_profile_id: string;
    workspace_files?: Record<string, string>;
  }): Observable<Run> {
    return this.http.post<Run>(`${this.baseUrl}/runs/`, payload);
  }

  getRun(runId: string): Observable<Run> {
    return this.http.get<Run>(`${this.baseUrl}/runs/${runId}`);
  }

  getReplay(runId: string): Observable<ArenaEvent[]> {
    return this.http.get<ArenaEvent[]>(`${this.baseUrl}/runs/${runId}/replay`);
  }

  getRunBundle(runId: string): Observable<{ run: Run; replay: ArenaEvent[]; postMortem: PostMortem }> {
    return forkJoin({
      run: this.getRun(runId),
      replay: this.getReplay(runId),
      postMortem: this.http.get<PostMortem>(`${this.baseUrl}/runs/${runId}/post-mortem`),
    }).pipe(map((bundle) => bundle));
  }

  listArtifacts(runId: string): Observable<RunArtifact[]> {
    return this.http.get<RunArtifact[]>(`${this.baseUrl}/runs/${runId}/artifacts`);
  }

  getArtifact(runId: string, artifactName: string): Observable<RunArtifact> {
    return this.http.get<RunArtifact>(`${this.baseUrl}/runs/${runId}/artifacts/${artifactName}`);
  }
}
