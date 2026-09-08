// Run: NODE_PATH=<playwright package directory> node tests/extreme/gui_web.test.cjs
// A real browser exercises the production frontend against a deterministic bridge.
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const path = require('node:path');
const { pathToFileURL } = require('node:url');

(async () => {
  const browser = await chromium.launch({headless: true,
    ...(process.env.CHROMIUM_EXECUTABLE ? {executablePath: process.env.CHROMIUM_EXECUTABLE} : {})});
  const page = await browser.newPage({viewport: {width: 1100, height: 820}});
  const errors = [];
  page.on('pageerror', error => errors.push(String(error)));
  await page.addInitScript(() => {
    window.testCalls = [];
    let mode = 'native';
    const methods = {
      get_app_info: () => ({app_name:'NextCore',version:'0.1.0',host_is_mac:true, status_ready:'준비됨', execution:{can_native_apply:mode === 'native',is_sandbox:mode === 'sandbox'}}),
      get_steps: () => ['welcome','detect','build','patch','done'].map((id,i) => ({id,title:['개요','기기 확인','EFI 준비','설치 · 패치','완료'][i],heading:id,desc:''})),
      detect: () => ({ok:true,detect:{model:'MacPro4,1',marketing_name:'Mac Pro (2009)',host_is_mac:true}}),
      get_macos_choices: () => ({choices:[{label:'macOS Tahoe 26',kernel:25}],selected_kernel:25}),
      host_can_build: () => ({can_build:true}), get_status: () => ({build_completed:false}),
      set_execution_mode: value => {mode=value;return {ok:true};},
      launch_wx_action: () => ({ok:true}), get_patch_status: () => ({ok:true,summary:'패치 없음'}),
      set_target_os: () => ({ok:true}),
      open_guide: () => {throw new Error('test guide failure');},
      reveal_log: () => ({ok:true}), get_settings: () => ({settings:{}}), save_settings: settings => {mode=settings.execution_mode === 'apple-silicon-sandbox' ? 'sandbox' : 'native';return {ok:true};}
    };
    window.pywebview = {api: Object.fromEntries(Object.entries(methods).map(([name, fn]) =>
      [name, async (...args) => {window.testCalls.push([name, ...args]);return fn(...args);}]))};
  });
  try {
    await page.goto(pathToFileURL(path.resolve(__dirname, '../../x86/gui/web/index.html')).href);
    await page.locator('#mode-sandbox').waitFor();
    await page.screenshot({path: process.env.GUI_SCREENSHOT || path.resolve(__dirname, '../../gui-overview.png')});
    await page.locator('#mode-sandbox').click();
    await page.locator('[data-step="2"]').click();
    await page.getByRole('heading', {name:'ARM macOS EFI 준비'}).waitFor();
    const preparation = await page.locator('#step-content').innerText();
    assert(preparation.includes('macOS 27') && preparation.includes('x86_64 EFI'));
    assert.equal(await page.locator('#sandbox-prepare, #vmapple-launch, #action-silicon-demo').count(), 0);
    const calls = await page.evaluate(() => window.testCalls);
    assert(!calls.some(c => ['prepare_sandbox','launch_vmapple','get_silicon_sandbox_demo','start_boot_picker','get_vmapple_status'].includes(c[0])), 'App must not invoke removed testers');
    assert(!calls.some(c => c[0] === 'launch_wx_action'), 'ARM EFI mode must not dispatch native patch actions');
    await page.locator('[data-step="4"]').click();
    assert.equal(await page.locator('.done-check').count(), 0, 'Navigation is not completion proof');
    assert(await page.locator('#step-content').innerText().then(t => t.includes('미검증')));
    await page.locator('[data-step="0"]').click();
    await page.locator('#mode-native').click();
    await page.locator('[data-step="2"]').click();
    await page.locator('#action-build').click();
    assert(await page.evaluate(() => window.testCalls.some(c => c[0] === 'launch_wx_action' && c[1] === 'build')));
    await page.locator('[data-step="4"]').click();
    assert(await page.locator('#step-content').innerText().then(t => t.includes('완료 보고 없음')));
    await page.locator('[data-step="0"]').click();
    await page.locator('#action-guide').click();
    await page.getByText('도움말을 열 수 없습니다.', {exact:true}).waitFor();
    await page.locator('#btn-settings').click();
    await page.selectOption('#setting-mode','apple-silicon-sandbox');
    await page.locator('#settings-save').click();
    await page.locator('[data-step="2"]').click();
    await page.getByRole('heading', {name:'ARM macOS EFI 준비'}).waitFor();
    assert.equal(await page.locator('#action-build').count(), 0, 'Saved ARM mode must replace native actions');
    await page.setViewportSize({width:390,height:844});
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'No narrow-window page overflow');
    assert.equal(errors.length, 0, errors.join('\n'));
    console.log('PASS: ARM EFI preparation, retired testers absent, native dispatch, no false completion, error handling, 390px layout');
  } finally { await browser.close(); }
})().catch(err => {console.error(err);process.exitCode=1;});
