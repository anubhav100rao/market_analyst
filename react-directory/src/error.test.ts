import axios, { AxiosError } from 'axios';
import { describe, expect, it } from 'vitest';
import { getErrorMessage } from './error';

describe('getErrorMessage', () => {
  it('prefers backend detail from axios errors', () => {
    const error = new AxiosError('Request failed');
    error.response = {
      data: { detail: 'Backend validation failed' },
      status: 400,
      statusText: 'Bad Request',
      headers: {},
      config: {
        headers: axios.AxiosHeaders.from({}),
      },
    };

    expect(getErrorMessage(error, 'Fallback')).toBe('Backend validation failed');
  });

  it('falls back to standard Error message', () => {
    expect(getErrorMessage(new Error('Network down'), 'Fallback')).toBe('Network down');
  });

  it('uses fallback for unknown values', () => {
    expect(getErrorMessage('unexpected', 'Fallback')).toBe('Fallback');
  });
});
