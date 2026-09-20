export interface AgentProfile {
  id: string;
  name: string;
  archetype: string;
  planning_style: string;
  preferred_stack: string[];
  engineering_principles: string[];
  modules: string[];
  memory: {
    slots: string[];
  };
  constraints: {
    allow_dependency_install: boolean;
    allow_external_network: boolean;
    allow_schema_change: boolean;
    max_runtime_minutes: number;
  };
  limits: {
    max_files_edited: number;
    max_runs: number;
  };
  owner_user_id?: string | null;
  template_id?: string | null;
  visibility?: string;
  version?: number;
  executor?: string | null;
}
