import { describe, it, mock, afterEach } from 'node:test';
import assert from 'node:assert';
import fs from 'fs';
import { GET } from './route.js';

describe('Warehouse API GET Error Handling', () => {
  afterEach(() => {
    mock.restoreAll();
  });

  it('should return 500 when fs.readdirSync throws an error', async () => {
    // Mock Response if not present globally
    if (!global.Response) {
      global.Response = class Response {
        static json(body, init) {
          return {
            status: init?.status || 200,
            json: async () => body
          };
        }
      };
    }

    mock.method(fs, 'existsSync', () => true);
    mock.method(fs, 'readdirSync', () => {
      throw new Error('Simulated read error');
    });

    const response = await GET();
    assert.strictEqual(response.status, 500);

    const body = await response.json();
    assert.strictEqual(body.success, false);
    assert.strictEqual(body.error, 'Simulated read error');
  });

  it('should return empty array if directory does not exist', async () => {
    if (!global.Response) {
      global.Response = class Response {
        static json(body, init) {
          return {
            status: init?.status || 200,
            json: async () => body
          };
        }
      };
    }

    mock.method(fs, 'existsSync', () => false);

    const response = await GET();
    assert.strictEqual(response.status, 200);
    const body = await response.json();
    assert.deepStrictEqual(body, []);
  });
});
