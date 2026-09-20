import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { EMPTY, Observable, switchMap } from 'rxjs';

import { AuthSession } from '../../models/auth-session.model';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root',
})
export class Auth {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = environment.apiUrl;
  private readonly origin = new URL(environment.apiUrl).origin;

  validateInvite(code: string, githubLogin: string): Observable<{ valid: boolean; status: string }> {
    return this.http.get<{ valid: boolean; status: string }>(`${this.baseUrl}/invites/validate`, {
      params: { code, github_login: githubLogin },
      withCredentials: true,
    });
  }

  login(githubLogin: string, inviteCode: string): Observable<AuthSession> {
    return this.http
      .post<{ state: string; authorization_url: string }>(
        `${this.baseUrl}/auth/github/start`,
        { github_login: githubLogin, invite_code: inviteCode },
        { withCredentials: true }
      )
      .pipe(
        switchMap((start) => {
          if (start.authorization_url.startsWith('http')) {
            window.location.assign(start.authorization_url);
            return EMPTY;
          }
          return this.http.get<AuthSession>(`${this.origin}${start.authorization_url}`, {
            withCredentials: true,
          });
        })
      );
  }

  me(): Observable<AuthSession> {
    return this.http.get<AuthSession>(`${this.baseUrl}/me`, { withCredentials: true });
  }
}
