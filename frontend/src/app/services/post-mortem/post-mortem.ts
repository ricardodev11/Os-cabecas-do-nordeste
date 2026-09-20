import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { PostMortem } from '../../models/post-mortem.model';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root',
})
export class PostMortemService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = environment.apiUrl;

  getForRun(runId: string): Observable<PostMortem> {
    return this.http.get<PostMortem>(`${this.baseUrl}/runs/${runId}/post-mortem`);
  }
}
