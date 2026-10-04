export type CaseStatus = 'pending_claim' | 'active' | 'closed';

export interface User {
  id: string;
  username: string;
  email?: string;
  role: 'staff' | 'admin';
  tenant_id: string;
  tenant_name?: string;
  is_active: boolean;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: {
    id: string;
    username: string;
    tenant_id: string;
    tenant_name?: string;
    role: string;
  };
}

export interface Case {
  id: string;
  vin: string;
  origin_tenant_id?: string;
  origin_tenant_name?: string;
  tenant_id?: string;
  tenant_name?: string;
  assigned_user_id?: string;
  assigned_user_name?: string;
  status: CaseStatus;
  created_at: string;
  updated_at: string;
  claimed_at?: string;
  closed_at?: string;
}

export interface CaseListResponse {
  items: Case[];
  total: number;
  page: number;
  page_size: number;
}

export interface Scan {
  id: string;
  camera_id: string;
  plate: string;
  vin: string;
  latitude: number;
  longitude: number;
  scanned_at: string;
  image_url?: string;
  created_at: string;
}

export interface ScanCreatePayload {
  camera_id: string;
  plate: string;
  vin: string;
  latitude: number;
  longitude: number;
  scanned_at: string;
  image_url?: string;
}

export interface ScanIngestResponse {
  scan_id: string;
  tenant_id: string;
  vin: string;
  matched_existing_case: boolean;
  created_new_case: boolean;
  case_id?: string;
  case_status?: string;
  message: string;
}
