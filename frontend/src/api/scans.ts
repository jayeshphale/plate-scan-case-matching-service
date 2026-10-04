import { apiClient } from './client';
import { ScanCreatePayload, ScanIngestResponse } from '../types';

export const scansApi = {
  ingestScan: async (payload: ScanCreatePayload): Promise<ScanIngestResponse> => {
    // Note: scan endpoint does not require authorization header, but apiClient sends it if present
    const response = await apiClient.post<ScanIngestResponse>('/scans', payload);
    return response.data;
  },
};
