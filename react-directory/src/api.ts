import axios from 'axios';
import type {
  AnalysisResponse,
  AnalyzeStockRequest,
  CompareStocksRequest,
  IntentResponse,
  PortfolioRequest,
  ChatRequest
} from './types';

const API_BASE_URL = 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const api = {
  analyzeStock: async (request: AnalyzeStockRequest): Promise<AnalysisResponse> => {
    const response = await apiClient.post<AnalysisResponse>('/analyze_stock', request);
    return response.data;
  },

  compareStocks: async (request: CompareStocksRequest): Promise<AnalysisResponse> => {
    const response = await apiClient.post<AnalysisResponse>('/compare_stocks', request);
    return response.data;
  },

  portfolioAnalysis: async (request: PortfolioRequest): Promise<AnalysisResponse> => {
    const response = await apiClient.post<AnalysisResponse>('/portfolio_analysis', request);
    return response.data;
  },

  chat: async (request: ChatRequest): Promise<AnalysisResponse> => {
    const response = await apiClient.post<AnalysisResponse>('/chat', request);
    return response.data;
  },

  parseIntent: async (request: ChatRequest): Promise<IntentResponse> => {
    const response = await apiClient.post<IntentResponse>('/parse_intent', request);
    return response.data;
  },
};
