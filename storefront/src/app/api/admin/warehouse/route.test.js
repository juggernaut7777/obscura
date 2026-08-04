import test from 'node:test';
import assert from 'node:assert';
import fs from 'node:fs';
import path from 'node:path';
import { GET } from './route.js';

test('Warehouse API GET', async (t) => {
  await t.test('returns empty array if manualCurationPath does not exist', async (st) => {
    st.mock.method(fs, 'existsSync', () => false);
    const response = await GET();
    const data = await response.json();
    assert.deepStrictEqual(data, []);
  });

  await t.test('throws 500 when fs throws error', async (st) => {
    st.mock.method(fs, 'existsSync', () => true);
    st.mock.method(fs, 'readdirSync', () => { throw new Error('Mock fs error'); });

    // Silence console.error for this test to keep output clean
    st.mock.method(console, 'error', () => {});

    const response = await GET();
    const data = await response.json();

    assert.strictEqual(response.status, 500);
    assert.strictEqual(data.success, false);
    assert.strictEqual(data.error, 'Mock fs error');
  });

  await t.test('returns items correctly for happy path', async (st) => {
    st.mock.method(fs, 'existsSync', () => true);

    st.mock.method(fs, 'readdirSync', (p) => {
      const pStr = p.toString();
      if (pStr.includes('MANUAL_CURATION') && !pStr.includes('item1')) return ['item1'];
      return ['angle_1.png'];
    });

    st.mock.method(fs, 'statSync', () => ({
      isDirectory: () => true,
      mtime: new Date('2023-01-01T00:00:00Z')
    }));

    st.mock.method(fs, 'readFileSync', (p) => {
      const pStr = p.toString();
      if (pStr.endsWith('metadata.json')) return '{"foo": "bar"}';
      return Buffer.from('fake_image_data');
    });

    const response = await GET();
    const data = await response.json();

    assert.strictEqual(data.length, 1);
    assert.strictEqual(data[0].folderName, 'item1');
    assert.strictEqual(data[0].metadata.foo, 'bar');
    assert.strictEqual(data[0].thumbnail, 'data:image/png;base64,ZmFrZV9pbWFnZV9kYXRh');
  });
});
