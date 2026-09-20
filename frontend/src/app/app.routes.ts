import { Routes } from '@angular/router';

import { BattleRoom } from './pages/battle-room/battle-room';
import { Dashboard } from './pages/dashboard/dashboard';
import { LandingPage } from './pages/landing-page/landing-page';
import { Login } from './pages/login/login';
import { QuestQueue } from './pages/quest-queue/quest-queue';
import { QuestLobby } from './pages/quest-lobby/quest-lobby';
import { Ranking } from './pages/ranking/ranking';
import { Result } from './pages/result/result';
import { AgentProfileList } from './pages/agent-profile-list/agent-profile-list';
import { AgentProfileEditor } from './pages/agent-profile-editor/agent-profile-editor';

export const routes: Routes = [
  { path: '', component: LandingPage },
  { path: 'login', component: Login },
  { path: 'dashboard', component: Dashboard },
  { path: 'leaderboard', component: Ranking },
  { path: 'battles/:id', component: BattleRoom },
  { path: 'quests', component: QuestQueue },
  { path: 'quests/:id', component: QuestLobby },
  { path: 'runs/:id', component: Result },
  { path: 'profiles', component: AgentProfileList },
  { path: 'profiles/new', component: AgentProfileEditor },
  { path: 'profiles/:id/edit', component: AgentProfileEditor },
  { path: '**', redirectTo: '' },
];
