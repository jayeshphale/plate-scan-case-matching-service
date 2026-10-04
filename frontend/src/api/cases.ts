import { apiClient } from './client';
import { Case, CaseListResponse, Scan } from '../types';

export const casesApi = {
  getCases: async (params?: {
    status?: string;
    vin?: string;
    page?: number;
    page_size?: number;
  }): Promise<CaseListResponse> => {
    const response = await apiClient.get<CaseListResponse>('/cases', { params });
    return response.data;
  },

  getCase: async (caseId: string): Promise<Case> => {
    const response = await apiClient.get<Case>(`/cases/${caseId}`);
    return response.data;
  },

  claimCase: async (caseId: string): Promise<Case> => {
    const response = await apiClient.post<Case>(`/cases/${caseId}/claim`);
    return response.data;
  },

  getCaseScans: async (caseId: string): Promise<Scan[]> => {
    const response = await apiClient.get<Scan[]>(`/cases/${caseId}/scans`);
    return response.data;
  },
};
