import { GET, POST } from './route';

const mockSelect = jest.fn();
const mockOrder = jest.fn();
const mockUpdate = jest.fn();
const mockEq = jest.fn();
const mockFrom = jest.fn();

// Mock Next.js Server
jest.mock('next/server', () => ({
  NextResponse: {
    json: jest.fn((body, init) => {
      return {
        json: async () => body,
        status: init?.status || 200,
      };
    })
  }
}));

// Mock the util file
jest.mock('../../../../../../src/utils/supabase', () => ({
  supabase: {
    from: (...args) => mockFrom(...args)
  }
}), { virtual: true });

// Mock @supabase/supabase-js to prevent fetch error from original file
jest.mock('@supabase/supabase-js', () => ({
    createClient: jest.fn(() => ({
        from: (...args) => mockFrom(...args)
    }))
}));

// Mock global fetch if postgrest-js tries to look for it at import time
global.fetch = jest.fn();

describe('Admin Orders API', () => {
  beforeEach(() => {
    jest.clearAllMocks();

    mockSelect.mockReturnValue({ order: mockOrder });
    mockUpdate.mockReturnValue({ eq: mockEq });
    mockEq.mockReturnValue({ select: mockSelect });

    mockFrom.mockReturnValue({
      select: mockSelect,
      update: mockUpdate
    });
  });

  describe('GET', () => {
    it('returns empty array if no orders exist', async () => {
      mockOrder.mockResolvedValue({ data: [], error: null });
      const res = await GET();
      expect(await res.json()).toEqual([]);
      expect(res.status).toBe(200);
      expect(mockFrom).toHaveBeenCalledWith('orders');
      expect(mockSelect).toHaveBeenCalledWith('*');
      expect(mockOrder).toHaveBeenCalledWith('created_at', { ascending: false });
    });

    it('returns orders when they exist', async () => {
      const mockOrders = [
        { id: 2, created_at: '2023-01-02T00:00:00.000Z' },
        { id: 1, created_at: '2023-01-01T00:00:00.000Z' }
      ];
      mockOrder.mockResolvedValue({ data: mockOrders, error: null });

      const res = await GET();
      const data = await res.json();

      expect(data).toEqual(mockOrders);
      expect(res.status).toBe(200);
    });

    it('returns 500 on supabase error', async () => {
      mockOrder.mockResolvedValue({ data: null, error: { message: 'supabase error' } });
      const res = await GET();
      expect(res.status).toBe(500);
      expect(await res.json()).toEqual({ success: false, error: 'supabase error' });
    });

    it('returns 500 on unexpected error', async () => {
      mockFrom.mockImplementation(() => { throw new Error('unexpected error'); });
      const res = await GET();
      expect(res.status).toBe(500);
      expect(await res.json()).toEqual({ success: false, error: 'unexpected error' });
    });
  });

  describe('POST', () => {
    const createRequest = (body) => ({
      json: async () => body,
    });

    it('returns 400 for missing orderId', async () => {
      const req = createRequest({ action: 'mark-paid' });
      const res = await POST(req);
      expect(res.status).toBe(400);
      expect(await res.json()).toEqual({ success: false, error: 'Missing orderId or action' });
    });

    it('executes mark-paid command', async () => {
      mockSelect.mockResolvedValue({ data: [{ id: '123', status: 'paid' }], error: null });

      const req = createRequest({ orderId: '123', action: 'mark-paid' });
      const res = await POST(req);

      expect(res.status).toBe(200);
      expect(await res.json()).toEqual({ success: true, data: [{ id: '123', status: 'paid' }] });
      expect(mockFrom).toHaveBeenCalledWith('orders');
      expect(mockUpdate).toHaveBeenCalledWith({ status: 'paid' });
      expect(mockEq).toHaveBeenCalledWith('id', '123');
    });

    it('executes mark-combining command', async () => {
      mockSelect.mockResolvedValue({ data: [{ id: '123', status: 'combining' }], error: null });

      const req = createRequest({ orderId: '123', action: 'mark-combining' });
      const res = await POST(req);

      expect(res.status).toBe(200);
      expect(mockUpdate).toHaveBeenCalledWith({ status: 'combining' });
    });

    it('executes mark-shipped command', async () => {
      mockSelect.mockResolvedValue({ data: [{ id: '123', status: 'shipped', tracking: 'TRK123', pipeline: 'USPS' }], error: null });

      const req = createRequest({ orderId: '123', action: 'mark-shipped', tracking: 'TRK123', pipeline: 'USPS' });
      const res = await POST(req);

      expect(res.status).toBe(200);
      expect(mockUpdate).toHaveBeenCalledWith({ status: 'shipped', tracking: 'TRK123', pipeline: 'USPS' });
    });

    it('returns 400 for mark-shipped without tracking', async () => {
      const req = createRequest({ orderId: '123', action: 'mark-shipped', pipeline: 'USPS' });
      const res = await POST(req);
      expect(res.status).toBe(400);
    });

    it('returns 400 for invalid action', async () => {
      const req = createRequest({ orderId: '123', action: 'invalid-action' });
      const res = await POST(req);
      expect(res.status).toBe(400);
    });

    it('returns 500 on supabase error', async () => {
      mockSelect.mockResolvedValue({ data: null, error: { message: 'update failed' } });

      const req = createRequest({ orderId: '123', action: 'mark-paid' });
      const res = await POST(req);

      expect(res.status).toBe(500);
      expect(await res.json()).toEqual({ success: false, error: 'update failed' });
    });

    it('returns 500 on unexpected error', async () => {
      mockFrom.mockImplementation(() => { throw new Error('unexpected error'); });

      const req = createRequest({ orderId: '123', action: 'mark-paid' });
      const res = await POST(req);

      expect(res.status).toBe(500);
      expect(await res.json()).toEqual({ success: false, error: 'unexpected error' });
    });
  });
});
