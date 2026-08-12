import { POST } from './route';
import fs from 'fs';
import { exec } from 'child_process';

// Mock child_process and fs
jest.mock('child_process', () => ({
  exec: jest.fn(),
}));

jest.mock('fs', () => ({
  existsSync: jest.fn(),
  mkdirSync: jest.fn(),
  writeFileSync: jest.fn(),
  unlinkSync: jest.fn(),
}));

// Mock util.promisify to just return the mock function so we can mock execAsync directly
jest.mock('util', () => {
  const originalUtil = jest.requireActual('util');
  return {
    ...originalUtil,
    promisify: (fn) => fn,
  };
});

describe('Checkout API Route', () => {
  let request;

  beforeEach(() => {
    jest.clearAllMocks();

    request = {
      json: jest.fn().mockResolvedValue({ items: [{ id: 1 }] }),
    };

    // The route actually returns a Response.json, which we can mock by ensuring it's available in global Next.js test context
    global.Response = class Response {
      constructor(body, init) {
        this.body = body;
        this.init = init;
        this.status = init?.status || 200;
      }
      static json(body, init) {
        return new Response(body, init);
      }
    };

    // Silence console messages during tests
    jest.spyOn(console, 'log').mockImplementation(() => {});
    jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    delete global.Response;
    jest.restoreAllMocks();
  });

  it('should handle request JSON parsing error and return 500', async () => {
    request.json.mockRejectedValue(new Error('Invalid JSON'));

    const response = await POST(request);

    expect(response.status).toBe(500);
    expect(response.body).toEqual({
      success: false,
      error: 'Invalid JSON',
    });
  });

  it('should handle Python execution stderr correctly and return 500', async () => {
    fs.existsSync.mockReturnValue(true);

    exec.mockResolvedValue({
      stdout: '',
      stderr: 'Some python error occurred',
    });

    const response = await POST(request);

    expect(response.status).toBe(500);
    expect(response.body).toEqual({
      success: false,
      error: 'Some python error occurred',
    });
  });

  it('should handle Python execution missing order ID correctly and return 500', async () => {
    fs.existsSync.mockReturnValue(true);

    exec.mockResolvedValue({
      stdout: 'Some logs before error ERROR:Failed to process order',
      stderr: '',
    });

    const response = await POST(request);

    expect(response.status).toBe(500);
    expect(response.body).toEqual({
      success: false,
      error: 'Failed to process order',
    });
  });

  it('should handle successful python execution and return 200', async () => {
    fs.existsSync.mockReturnValue(true);

    exec.mockResolvedValue({
      stdout: 'Processing... SUCCESS_ORDER_ID:12345-ABCDE',
      stderr: '',
    });

    const response = await POST(request);

    expect(response.status).toBe(200);
    expect(response.body).toEqual({
      success: true,
      orderId: '12345-ABCDE',
    });
  });
});
