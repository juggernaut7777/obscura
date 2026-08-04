const fs = require('fs');
const util = require('util');

jest.mock('fs');

const route = require('./route.js');
const GET = route.GET;

// Mock Response.json for testing if it's not defined
if (typeof Response === 'undefined') {
  global.Response = {
    json: jest.fn((data, options) => {
      return {
        status: options?.status || 200,
        json: async () => data
      };
    })
  };
}

describe('Orders API', () => {
  let consoleErrorSpy;
  let originalResponseJson;

  beforeEach(() => {
    jest.clearAllMocks();
    consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
    if (global.Response && global.Response.json) {
       originalResponseJson = global.Response.json;
       global.Response.json = jest.fn((data, options) => {
         return {
           status: options?.status || 200,
           json: async () => data
         };
       });
    }
  });

  afterEach(() => {
    consoleErrorSpy.mockRestore();
    if (originalResponseJson) {
        global.Response.json = originalResponseJson;
    }
  });

  describe('GET', () => {
    it('returns empty array when file does not exist', async () => {
      fs.existsSync.mockReturnValue(false);
      const res = await GET();
      const data = await res.json();
      expect(data).toEqual([]);
      expect(res.status).toBe(200);
    });

    it('returns sorted orders when file exists', async () => {
      fs.existsSync.mockReturnValue(true);
      const mockOrders = [
        { id: 1, created_at: '2024-01-01T10:00:00Z' },
        { id: 2, created_at: '2024-01-02T10:00:00Z' },
        { id: 3, created_at: '2024-01-01T15:00:00Z' },
      ];
      fs.readFileSync.mockReturnValue(JSON.stringify(mockOrders));

      const res = await GET();
      const data = await res.json();

      expect(data).toEqual([
        { id: 2, created_at: '2024-01-02T10:00:00Z' },
        { id: 3, created_at: '2024-01-01T15:00:00Z' },
        { id: 1, created_at: '2024-01-01T10:00:00Z' }
      ]);
      expect(res.status).toBe(200);
    });

    it('returns 500 error on file read error', async () => {
      fs.existsSync.mockReturnValue(true);
      fs.readFileSync.mockImplementation(() => { throw new Error('File read failed'); });
      const res = await GET();
      const data = await res.json();
      expect(res.status).toBe(500);
      expect(data).toEqual({ success: false, error: 'File read failed' });
      expect(consoleErrorSpy).toHaveBeenCalled();
    });
  });
});
