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
    const report = () => ({ok: true, execution_mode: mode, efi_native: true,
      artifact_available: true, stageable: true, boot_verified: false,
      minimum_cpu: 'SSE4.1 + SSE4.2', supported_targets: [26, 27], blockers: ['원본 macOS 부팅 미검증']});
    const methods = {
      get_app_info: () => ({app_name:'26x86',version:'0.1.0',host_is_mac:true, status_ready:'준비됨'}),
      get_steps: () => ['welcome','detect','build','patch','done'].map((id,i) => ({id,title:['개요','기기 확인','EFI 준비','설치 · 패치','완료'][i],heading:id,desc:''})),
      detect: () => ({ok:true,detect:{model:'MacPro4,1',marketing_name:'Mac Pro (2009)',host_is_mac:true}}),
      get_macos_choices: () => ({choices:[{label:'macOS Tahoe 26',kernel:25}],selected_kernel:25}),
      host_can_build: () => ({can_build:true}), get_status: () => ({build_completed:false}),
      get_sandbox_status: report, get_sandbox_plan: report,
      set_execution_mode: value => {mode=value;return {ok:true};},
      prepare_sandbox: (major, output) => ({ok:true,target_major:major,output_path:output,boot_verified:false}),
      launch_wx_action: () => ({ok:true}), get_patch_status: () => ({ok:true,summary:'패치 없음'}),
      set_hardware_profile: () => ({ok:true}), set_target_os: () => ({ok:true}),
      open_guide: () => {throw new Error('test guide failure');},
      reveal_log: () => ({ok:true}), get_settings: () => ({settings:{}}), save_settings: () => ({ok:true})
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
    await page.locator('#sandbox-prepare').waitFor({state:'visible'});
    await page.selectOption('#sandbox-target','27');
    await page.locator('#sandbox-output').fill('C:/26x86-output');
    await page.locator('#sandbox-prepare').click();
    await page.getByText('EFI 자체 검사 패키지 준비 완료 · macOS 부팅 미검증', {exact:true}).waitFor();
    const calls = await page.evaluate(() => window.testCalls);
    assert(calls.some(c => c[0] === 'prepare_sandbox' && c[1] === 27 && c[2] === 'C:/26x86-output'));
    assert(!calls.some(c => c[0] === 'launch_wx_action'), 'Sandbox must never dispatch native patch actions');
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
    await page.setViewportSize({width:390,height:844});
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'No narrow-window page overflow');
    assert.equal(errors.length, 0, errors.join('\n'));
    console.log('PASS: native/Sandbox dispatch isolation, target 27, receipt, no false completion, error handling, 390px layout');
  } finally { await browser.close(); }
})().catch(err => {console.error(err);process.exitCode=1;});
