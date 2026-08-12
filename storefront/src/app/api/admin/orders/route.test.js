import { GET, POST } from './route';
import fs from 'fs';
import { exec } from 'child_process';

jest.mock('fs');
jest.mock('child_process', () => ({
  exec: jest.fn(),
}));

// Mock global Response for Next.js API routes in Node environment
global.Response = class {
  constructor(body, init) {
    this.body = body;
    this.init = init || {};
  }
  static json(data, init) {
    return new Response(JSON.stringify(data), init);
  }
};

describe('Admin Orders API', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    console.error = jest.fn();
    console.log = jest.fn();
  });

  describe('GET', () => {
    it('returns empty array when file does not exist', async () => {
      fs.existsSync.mockReturnValue(false);
      const response = await GET();
      expect(response.body).toBe('[]');
    });

    it('returns sorted orders when file exists', async () => {
      fs.existsSync.mockReturnValue(true);
      const mockOrders = [
        { id: 1, created_at: '2023-01-01' },
        { id: 2, created_at: '2023-01-03' },
        { id: 3, created_at: '2023-01-02' },
      ];
      fs.readFileSync.mockReturnValue(JSON.stringify(mockOrders));
      const response = await GET();
      const body = JSON.parse(response.body);
      expect(body[0].id).toBe(2);
      expect(body[1].id).toBe(3);
      expect(body[2].id).toBe(1);
    });

    it('returns 500 on error', async () => {
      fs.existsSync.mockReturnValue(true);
      fs.readFileSync.mockImplementation(() => {
        throw new Error('File read error');
      });
      const response = await GET();
      expect(response.init.status).toBe(500);
      expect(JSON.parse(response.body).success).toBe(false);
    });
  });

  describe('POST', () => {
    it('returns 400 when orderId is missing', async () => {
      const request = { json: jest.fn().mockResolvedValue({ action: 'mark-paid' }) };
      const response = await POST(request);
      expect(response.init.status).toBe(400);
    });

    it('returns 400 on invalid action', async () => {
      const request = { json: jest.fn().mockResolvedValue({ orderId: '123', action: 'invalid' }) };
      const response = await POST(request);
      expect(response.init.status).toBe(400);
    });

    it('executes python script for mark-paid', async () => {
      const request = { json: jest.fn().mockResolvedValue({ orderId: '123', action: 'mark-paid' }) };
      exec.mockImplementation((cmd, opts, cb) => cb(null, { stdout: 'success', stderr: '' }));
      const response = await POST(request);
      expect(exec).toHaveBeenCalledWith(
        'python order_fulfillment.py --mark-paid "123"',
        expect.any(Object),
        expect.any(Function)
      );
      expect(JSON.parse(response.body).success).toBe(true);
    });

    it('executes python script for mark-combining', async () => {
      const request = { json: jest.fn().mockResolvedValue({ orderId: '123', action: 'mark-combining' }) };
      exec.mockImplementation((cmd, opts, cb) => cb(null, { stdout: 'success', stderr: '' }));
      const response = await POST(request);
      expect(exec).toHaveBeenCalledWith(
        'python order_fulfillment.py --mark-combining "123"',
        expect.any(Object),
        expect.any(Function)
      );
      expect(JSON.parse(response.body).success).toBe(true);
    });

    it('executes python script for mark-shipped', async () => {
      const request = {
        json: jest.fn().mockResolvedValue({ orderId: '123', action: 'mark-shipped', tracking: 'T123', pipeline: 'P1' })
      };
      exec.mockImplementation((cmd, opts, cb) => cb(null, { stdout: 'success', stderr: '' }));
      const response = await POST(request);
      expect(exec).toHaveBeenCalledWith(
        'python order_fulfillment.py --mark-shipped "123" "T123" "P1"',
        expect.any(Object),
        expect.any(Function)
      );
    });

    it('returns 400 when missing tracking or pipeline for mark-shipped', async () => {
      const request = {
        json: jest.fn().mockResolvedValue({ orderId: '123', action: 'mark-shipped' })
      };
      const response = await POST(request);
      expect(response.init.status).toBe(400);
      expect(JSON.parse(response.body).error).toBe("Missing tracking or pipeline info for shipping");
    });

    it('returns 500 on execution error', async () => {
       const request = { json: jest.fn().mockResolvedValue({ orderId: '123', action: 'mark-paid' }) };
       exec.mockImplementation((cmd, opts, cb) => {
         throw new Error('Exec error');
       });
       const response = await POST(request);
       expect(response.init.status).toBe(500);
    });
  });
});
