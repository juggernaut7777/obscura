import { POST } from './route.js';
import fs from 'fs';
import { exec } from 'child_process';
import path from 'path';

// Mock the modules
jest.mock('fs');
jest.mock('child_process');

// Silence console logs and errors during tests
beforeAll(() => {
  jest.spyOn(console, 'log').mockImplementation(() => {});
  jest.spyOn(console, 'error').mockImplementation(() => {});
});

afterAll(() => {
  console.log.mockRestore();
  console.error.mockRestore();
});

describe('Checkout API route', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should handle fs errors during writeFileSync', async () => {
    const mockRequest = {
      json: jest.fn().mockResolvedValue({ cart: ['item1'] })
    };

    fs.existsSync.mockReturnValue(true);
    fs.writeFileSync.mockImplementation(() => {
      throw new Error('Disk full');
    });

    const response = await POST(mockRequest);
    const responseData = await response.json();

    expect(response.status).toBe(500);
    expect(responseData.success).toBe(false);
    expect(responseData.error).toBe('Disk full');
  });

  it('should handle fs errors during mkdirSync', async () => {
    const mockRequest = {
      json: jest.fn().mockResolvedValue({ cart: ['item2'] })
    };

    fs.existsSync.mockReturnValue(false);
    fs.mkdirSync.mockImplementation(() => {
      throw new Error('Permission denied');
    });

    const response = await POST(mockRequest);
    const responseData = await response.json();

    expect(response.status).toBe(500);
    expect(responseData.success).toBe(false);
    expect(responseData.error).toBe('Permission denied');
  });
});
