import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { AgentProfile } from '../../models/agent-profile.model';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root',
})
export class AgentProfileService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = environment.apiUrl;

  list(): Observable<AgentProfile[]> {
    return this.http.get<AgentProfile[]>(`${this.baseUrl}/profiles/`);
  }

  create(profile: AgentProfile): Observable<AgentProfile> {
    return this.http.post<AgentProfile>(`${this.baseUrl}/profiles/`, profile);
  }

  listMine(): Observable<AgentProfile[]> {
    return this.http.get<AgentProfile[]>(`${this.baseUrl}/profiles/mine`, { withCredentials: true });
  }
}
