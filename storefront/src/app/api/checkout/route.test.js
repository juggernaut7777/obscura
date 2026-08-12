import fs from 'fs';

jest.mock('fs', () => ({
  existsSync: jest.fn(),
  mkdirSync: jest.fn(),
  writeFileSync: jest.fn(),
  unlinkSync: jest.fn()
}));

jest.mock('child_process', () => {
  const original = jest.requireActual('child_process');
  const mockExec = jest.fn();
  const { promisify } = require('util');
  mockExec[promisify.custom] = jest.fn();
  return {
    ...original,
    exec: mockExec
  };
});

// We need to provide the global Response since Next.js route handlers use it
global.Response = class Response {
  constructor(body, init) {
    this.body = body;
    this.status = init?.status || 200;
  }
  static json(data, init) {
    return new Response(data, init);
  }
};

describe('POST /api/checkout', () => {
  let mockRequest;
  let execAsyncMock;

  beforeEach(() => {
    jest.resetModules();

    mockRequest = {
      json: jest.fn().mockResolvedValue({ cart: ['item1', 'item2'] })
    };

    const { exec } = require('child_process');
    const { promisify } = require('util');
    execAsyncMock = exec[promisify.custom];
    execAsyncMock.mockReset();
  });

  it('should return 500 when request body fails to parse (simulating error handling test)', async () => {
    const { POST } = require('./route');
    mockRequest.json.mockRejectedValue(new Error('Invalid JSON'));

    const response = await POST(mockRequest);
    expect(response.status).toBe(500);
    expect(response.body).toEqual({ success: false, error: 'Invalid JSON' });
  });

  it('should return 200 with orderId on successful python execution', async () => {
    const { POST } = require('./route');
    fs.existsSync.mockReturnValue(true);
    // Note: The regex is /SUCCESS_ORDER_ID:(\S+)/. There was no space in the route, so match(/SUCCESS_ORDER_ID: 12345/) returns null.
    execAsyncMock.mockResolvedValue({ stdout: 'SUCCESS_ORDER_ID:12345\n', stderr: '' });

    const response = await POST(mockRequest);
    expect(response.status).toBe(200);
    expect(response.body).toEqual({ success: true, orderId: '12345' });
  });

  it('should return 500 when python execution encounters stderr without stdout', async () => {
    const { POST } = require('./route');
    fs.existsSync.mockReturnValue(true);
    execAsyncMock.mockResolvedValue({ stdout: '', stderr: 'Python crashed due to missing dependencies\n' });

    const response = await POST(mockRequest);
    expect(response.status).toBe(500);
    expect(response.body).toEqual({ success: false, error: 'Python crashed due to missing dependencies\n' });
  });

  it('should return 500 when python execution outputs ERROR without order id', async () => {
    const { POST } = require('./route');
    fs.existsSync.mockReturnValue(true);
    execAsyncMock.mockResolvedValue({ stdout: 'ERROR:Insufficient inventory\n', stderr: '' });

    const response = await POST(mockRequest);
    expect(response.status).toBe(500);
    expect(response.body).toEqual({ success: false, error: 'Insufficient inventory' });
  });

  it('should return 500 on python execution throw', async () => {
    const { POST } = require('./route');
    fs.existsSync.mockReturnValue(true);
    execAsyncMock.mockRejectedValue(new Error('Execution failed'));

    const response = await POST(mockRequest);
    expect(response.status).toBe(500);
    expect(response.body).toEqual({ success: false, error: 'Execution failed' });
  });
});
