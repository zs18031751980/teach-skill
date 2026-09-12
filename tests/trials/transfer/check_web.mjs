// Exercise the actual code emitted in web.md with controlled input/network ordering.
// This verifies its sequencing logic, not browser compatibility or real HTTP behavior.
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';

const answer = readFileSync(new URL('./web.md', import.meta.url), 'utf8');
const code = answer.match(/```js\n([\s\S]*?)```/)[1];
const input = { value: '', addEventListener(_, callback) { this.change = callback; } };
const timers = new Map();
const requests = [];
let sequence = 0;
let rendered = null;
let status = '';
vm.runInNewContext(code, {
  document: { querySelector: () => input },
  setTimeout(callback) { timers.set(++sequence, callback); return sequence; },
  clearTimeout(id) { timers.delete(id); },
  fetch(url) {
    return new Promise((resolve, reject) => requests.push({ url, resolve, reject }));
  },
  renderResults(data) { rendered = Array.from(data); },
  showStatus(text) { status = text; },
  console: { error() {} },
});
function type(value) { input.value = value; input.change(); }
function fire() {
  assert.equal(timers.size, 1);
  const [id, callback] = timers.entries().next().value;
  timers.delete(id);
  return callback();
}
function respond(request, data) { request.resolve({ ok: true, json: async () => data }); }

// An old response must be invalid immediately on input, before the new debounce fires.
type('ca');
let oldTask = fire();
type('cat');
respond(requests[0], ['old']);
await oldTask;
assert.deepEqual(rendered, []);
let newTask = fire();
respond(requests[1], ['cat']);
await newTask;
assert.deepEqual(rendered, ['cat']);

// Reversed response order must keep the newest result.
type('d'); oldTask = fire();
type('dog'); newTask = fire();
respond(requests[3], ['dog']); await newTask;
respond(requests[2], ['d']); await oldTask;
assert.deepEqual(rendered, ['dog']);

// A stale failure must not overwrite current success or status.
type('b'); oldTask = fire();
type('bird'); newTask = fire();
respond(requests[5], ['bird']); await newTask;
requests[4].reject(new Error('old failure')); await oldTask;
assert.deepEqual(rendered, ['bird']);
assert.equal(status, '');

// Clearing the input invalidates requests already in flight without sending an empty query.
type('fish'); oldTask = fire();
type('');
respond(requests[6], ['fish']); await oldTask;
assert.deepEqual(rendered, []);
assert.equal(timers.size, 0);
assert.equal(requests.length, 7);
console.log('Verified emitted search code against four response-order scenarios.');
