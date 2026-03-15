import { describe, it, expect, vi } from 'vitest';
import { api } from './api';
import axios from 'axios';

// Mock axios completely
vi.mock('axios', () => {
  return {
    default: {
      create: vi.fn(() => ({
        post: vi.fn(),
        get: vi.fn(),
      }))
    }
  }
});

describe('API Client', () => {
  it('analyzeStock calls correct endpoint', async () => {
    // Get the mocked instance 
    const mockedAxiosCreate = vi.mocked(axios.create);
    const mockInstance = mockedAxiosCreate.mock.results[0].value;
    
    // Mock the post method response
    mockInstance.post.mockResolvedValueOnce({
      data: { analysis_type: 'single', stocks: [], recommendation: 'HOLD', reasoning: 'Test reason' }
    });

    const res = await api.analyzeStock({ stock: 'AAPL' });
    expect(res.recommendation).toBe('HOLD');
    expect(res.reasoning).toBe('Test reason');
    expect(mockInstance.post).toHaveBeenCalledWith('/analyze_stock', { stock: 'AAPL' });
  });

  it('chat calls correct endpoint', async () => {
    const mockedAxiosCreate = vi.mocked(axios.create);
    const mockInstance = mockedAxiosCreate.mock.results[0].value;
    
    mockInstance.post.mockResolvedValueOnce({
      data: { analysis_type: 'chat', stocks: [], recommendation: 'BUY', reasoning: 'Strong buy' }
    });

    const res = await api.chat({ query: 'Should I buy?' });
    expect(res.recommendation).toBe('BUY');
    expect(res.reasoning).toBe('Strong buy');
    expect(mockInstance.post).toHaveBeenCalledWith('/chat', { query: 'Should I buy?' });
  });
});
