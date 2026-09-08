const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const test = require('node:test');

// Run the production transport functions without starting the full DOM wizard.
const source = fs.readFileSync(path.join(__dirname, '../x86/gui/web/app.js'), 'utf8');
const end = source.indexOf('  function whenBridgeReady(');
assert.ok(end > 0);
const transportSource = source.slice(0, end) +
  'window.testTransport = { getBridgeApi, probeHttpBridge, connectQtWebChannel, api };})();';

function runtime(extra = {}) {
  const events = [];
  const window = { dispatchEvent(event) { events.push(event.type); } };
  const context = vm.createContext({
    window, document: { getElementById() { return null; } },
    Event: class { constructor(type) { this.type = type; } },
    fetch: async (url) => ({ ok: true, json: async () =>
      url === '/api/health' ? { ok: true } : { result: { title: 'NextCore' } } }),
    ...extra,
  });
  vm.runInContext(transportSource, context);
  return { window, api: window.testTransport, events };
}

test('HTTP browser transport works without creating a fake pywebview object', async () => {
  const { window, api, events } = runtime();
  assert.equal(await api.probeHttpBridge(), true);
  assert.equal(window.pywebview, undefined);
  assert.equal(api.getBridgeApi(), window.__x86HttpBridge);
  assert.equal((await api.api('get_app_info')).title, 'NextCore');
  assert.deepEqual(events, ['pywebviewready']);
});

test('HTTP readiness preserves native injection helpers before API creation', async () => {
  const { window, api } = runtime();
  const native = { stringify: JSON.stringify, _createApi() {} };
  window.pywebview = native;
  assert.equal(await api.probeHttpBridge(), true);
  assert.equal(window.pywebview, native);
  assert.equal(window.pywebview.stringify, JSON.stringify);
  assert.equal(typeof window.pywebview._createApi, 'function');
  assert.equal(api.getBridgeApi(), window.__x86HttpBridge);
});

test('native API appearing during an HTTP probe retains priority and identity', async () => {
  let finishHealth;
  const { window, api } = runtime({ fetch: () => new Promise(resolve => { finishHealth = resolve; }) });
  const pending = api.probeHttpBridge();
  const native = { api: { get_app_info: async () => 'native' }, stringify: JSON.stringify };
  window.pywebview = native;
  finishHealth({ ok: true, json: async () => ({ ok: true }) });
  assert.equal(await pending, true);
  assert.equal(window.pywebview, native);
  assert.equal(api.getBridgeApi(), native.api);
  assert.equal(await api.api('get_app_info'), 'native');
});

test('Qt callback transport preserves native helpers and wins over HTTP fallback', async () => {
  const bridge = { get_app_info(callback) { callback('qt'); } };
  const { window, api } = runtime({
    qt: { webChannelTransport: {} },
    QWebChannel: function (_transport, callback) { callback({ objects: { bridge } }); },
  });
  const native = { stringify: JSON.stringify, _createApi() {} };
  window.pywebview = native;
  api.connectQtWebChannel();
  window.__x86HttpBridge = { __httpWrapped: true };
  assert.equal(window.pywebview, native);
  assert.equal(api.getBridgeApi(), window.__x86QtBridge);
  assert.equal(await api.api('get_app_info'), 'qt');
  native.api = { get_app_info: async () => 'native' };
  assert.equal(await api.api('get_app_info'), 'native');
});
