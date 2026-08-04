import { POST } from './route.js';
import fs from 'fs';
import { exec } from 'child_process';

jest.mock('fs');
jest.mock('child_process', () => ({
  exec: jest.fn(),
}));

describe('POST /api/checkout', () => {
  let mockRequest;

  beforeEach(() => {
    mockRequest = {
      json: jest.fn().mockResolvedValue({ cart: [] }),
    };
    jest.clearAllMocks();

    // Polyfill Response for Node environment if it doesn't exist
    if (typeof global.Response === 'undefined') {
      class MockResponse {
        constructor(body, init) {
          this.body = body;
          this.status = init?.status || 200;
        }
        async json() {
          return JSON.parse(this.body);
        }
        static json(data, init) {
          return new MockResponse(JSON.stringify(data), init);
        }
      }
      global.Response = MockResponse;
    } else {
      jest.spyOn(global.Response, 'json').mockImplementation((data, init) => {
        return {
          status: init?.status || 200,
          json: async () => data
        };
      });
    }

    jest.spyOn(console, 'error').mockImplementation(() => {});
    jest.spyOn(console, 'log').mockImplementation(() => {});

    fs.existsSync.mockReturnValue(true);
    fs.writeFileSync.mockImplementation(() => {}); // Clear throw from other tests
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('should return 200 and order ID on successful execution', async () => {
    exec.mockImplementation((cmd, opts, callback) => {
      // route.js uses promisify(exec) and execAsync(command, { cwd })
      // When promisify is used, if 2 arguments are passed, it maps to exec(cmd, opts, callback)
      if (typeof opts === 'function') {
        opts(null, { stdout: 'SUCCESS_ORDER_ID:12345', stderr: '' });
      } else {
        callback(null, { stdout: 'SUCCESS_ORDER_ID:12345', stderr: '' });
      }
    });

    const response = await POST(mockRequest);
    const responseBody = await response.json();

    expect(response.status).toBe(200);
    expect(responseBody).toEqual({ success: true, orderId: '12345' });
  });

  it('should return 500 when fs module throws an error', async () => {
    fs.writeFileSync.mockImplementation(() => {
      throw new Error('Mocked file system error');
    });

    const response = await POST(mockRequest);
    const responseBody = await response.json();

    expect(response.status).toBe(500);
    expect(responseBody).toEqual({
      success: false,
      error: 'Mocked file system error'
    });

    expect(console.error).toHaveBeenCalledWith(
      '[API CHECKOUT] Route handler error:',
      expect.any(Error)
    );
  });

  it('should return 500 when python script writes to stderr without stdout', async () => {
    exec.mockImplementation((cmd, opts, callback) => {
      if (typeof opts === 'function') {
        opts(null, { stdout: '', stderr: 'Python exception' });
      } else {
        callback(null, { stdout: '', stderr: 'Python exception' });
      }
    });

    const response = await POST(mockRequest);
    const responseBody = await response.json();

    expect(response.status).toBe(500);
    expect(responseBody).toEqual({
      success: false,
      error: 'Python exception'
    });
  });

  it('should return 500 with custom error when python outputs ERROR:msg', async () => {
    exec.mockImplementation((cmd, opts, callback) => {
      if (typeof opts === 'function') {
        opts(null, { stdout: 'ERROR:Out of stock', stderr: '' });
      } else {
        callback(null, { stdout: 'ERROR:Out of stock', stderr: '' });
      }
    });

    const response = await POST(mockRequest);
    const responseBody = await response.json();

    expect(response.status).toBe(500);
    expect(responseBody).toEqual({
      success: false,
      error: 'Out of stock'
    });
  });

  it('should handle JSON parse errors from request', async () => {
    mockRequest.json.mockRejectedValue(new Error('Invalid JSON'));

    const response = await POST(mockRequest);
    const responseBody = await response.json();

    expect(response.status).toBe(500);
    expect(responseBody).toEqual({
      success: false,
      error: 'Invalid JSON'
    });
  });
});
