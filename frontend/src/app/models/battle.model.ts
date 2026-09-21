import { PostMortem } from './post-mortem.model';
import { Run } from './run.model';
import { User } from './user.model';
import { ArenaEvent } from './arena-event.model';

export interface BattleParticipant {
  id: string;
  battle_id: string;
  user_id: string;
  agent_profile_id: string;
  seat: 'left' | 'right';
  submission_status: string;
  workspace_files: Record<string, string>;
  run_id: string | null;
  joined_at: string;
}

export interface BattleResult {
  battle_id: string;
  winner_participant_id: string | null;
  score_left: number;
  score_right: number;
  tie_break_reason: string;
  summary: string;
  score_breakdown: BattleScoreBreakdown[];
}

export interface BattleScoreBreakdown {
  participant_id: string;
  seat: 'left' | 'right';
  technical_score: number;
  total_score: number;
  passed_tests: number;
  failed_tests: number;
  duration_ms: number | null;
  suites: BattleScoreSuiteBreakdown[];
}

export interface BattleScoreSuiteBreakdown {
  suite: string;
  passed: number;
  failed: number;
  duration_ms: number | null;
}

export interface Battle {
  id: string;
  quest_id: string;
  status: string;
  created_by_user_id: string;
  battle_type: string;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
}

export interface BattleDetail {
  battle: Battle;
  participants: BattleParticipant[];
  result: BattleResult | null;
}

/** Evento do SSE stream de status (`GET /battles/{id}/stream`). */
export interface BattleStreamEvent {
  battle_id: string;
  status: string;
  winner_participant_id?: string | null;
}

export interface BattleRunBundle {
  participant_id: string;
  run: Run;
  replay: ArenaEvent[];
  post_mortem: PostMortem;
}

export interface BattleReplayBundle {
  battle_id: string;
  runs: BattleRunBundle[];
}

export interface LeaderboardEntry {
  user_id: string;
  github_login: string;
  display_name: string;
  wins: number;
  losses: number;
  ties: number;
  best_score: number;
}
