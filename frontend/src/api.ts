import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

export interface ChatResponse {
  response: string;
}

export interface IngestResponse {
  status: string;
}

export const api = {
  chat: async (message: string): Promise<ChatResponse> => {
    const response = await axios.post(`${API_BASE_URL}/chat`, { message });
    return response.data;
  },

  ingest: async (directory_path: string): Promise<IngestResponse> => {
    const response = await axios.post(`${API_BASE_URL}/ingest`, { directory_path });
    return response.data;
  }
};
