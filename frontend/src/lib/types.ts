export interface UserRule {
  id?: number;
  user_id?: number;
  label: string;
  pattern: string;
  match_type: string;
  field: string;
  priority: number;
  confidence: number;
  version: number;
  provenance: string;
  updated_at: string;
}

