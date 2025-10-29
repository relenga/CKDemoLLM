import apiClient from './api';

export interface GraphProcessRequest {
  input: string;
  options?: {
    temperature?: number;
    max_tokens?: number;
    stream?: boolean;
  };
}

export interface GraphProcessResponse {
  result: string;
  status: string;
  processing_time?: number;
  metadata?: {
    nodes_processed?: number;
    edges_traversed?: number;
  };
}

export const graphService = {
  processInput: async (request: GraphProcessRequest): Promise<GraphProcessResponse> => {
    const response = await apiClient.post('/api/graph/process', request);
    return response.data;
  },

  getStatus: async (): Promise<{ status: string; version: string }> => {
    const response = await apiClient.get('/api/status');
    return response.data;
  },

  getGraphInfo: async (): Promise<any> => {
    const response = await apiClient.get('/api/graph/info');
    return response.data;
  },
};