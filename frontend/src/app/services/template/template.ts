import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { AgentTemplate } from '../../models/agent-template.model';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root',
})
export class TemplateService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = environment.apiUrl;

  listAgentTemplates(): Observable<AgentTemplate[]> {
    return this.http.get<AgentTemplate[]>(`${this.baseUrl}/templates/agents`, { withCredentials: true });
  }
}
