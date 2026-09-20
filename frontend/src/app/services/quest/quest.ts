import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { Quest } from '../../models/quest.model';
import { StarterFile } from '../../models/starter-file.model';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root',
})
export class QuestService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = environment.apiUrl;

  list(): Observable<Quest[]> {
    return this.http.get<Quest[]>(`${this.baseUrl}/quests/`);
  }

  getById(id: string): Observable<Quest> {
    return this.http.get<Quest>(`${this.baseUrl}/quests/${id}`);
  }

  listStarterFiles(id: string): Observable<StarterFile[]> {
    return this.http.get<StarterFile[]>(`${this.baseUrl}/quests/${id}/starter-files`);
  }
}
