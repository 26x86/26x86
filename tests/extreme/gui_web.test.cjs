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
    let pickerState = 'idle';
    let pickerSelection = null;
    const pickerEntries = [
      {id:'macos', label:'macOS Golden Gate 27', kind:'macOS', target_major:27},
      {id:'recovery', label:'macOS Recovery · _default.ipsw', kind:'Recovery', target_major:27}
    ];
    const pickerSnapshot = () => ({ok:true, state:pickerState, delay_seconds:2,
      remaining_seconds: pickerState === 'armed' ? 1.5 : 0, alt_key:'Alt',
      picker_visible: pickerState === 'picker', selected_entry:pickerSelection,
      selection: pickerState === 'selected' ? pickerSelection : null,
      trigger: pickerSelection === 'recovery' ? 'alt-enter' : null, entries:pickerEntries});
    const report = () => ({ok: true, execution_mode: mode, efi_native: true,
      artifact_available: true, stageable: true, boot_verified: false,
      minimum_cpu: 'SSE4.1 + SSE4.2', supported_targets: [26, 27], blockers: ['원본 macOS 부팅 미검증']});
    const methods = {
      get_app_info: () => ({app_name:'26x86',version:'0.1.0',host_is_mac:true, status_ready:'준비됨', execution:{can_native_apply:true}}),
      get_steps: () => ['welcome','detect','build','patch','done'].map((id,i) => ({id,title:['개요','기기 확인','EFI 준비','설치 · 패치','완료'][i],heading:id,desc:''})),
      detect: () => ({ok:true,detect:{model:'MacPro4,1',marketing_name:'Mac Pro (2009)',host_is_mac:true}}),
      get_macos_choices: () => ({choices:[{label:'macOS Tahoe 26',kernel:25}],selected_kernel:25}),
      host_can_build: () => ({can_build:true}), get_status: () => ({build_completed:false}),
      get_sandbox_status: report, get_sandbox_plan: report,
      get_vmapple_status: () => ({ok:true, configured:true, machine_type:'iBoot(AArch64)', guest_os:'macOS', guest_os_policy:'macOS-only', recovery_scope:{protocol:'DFU/IPSW',default_image_name:'_default.ipsw'}, soc_profile:{schema:'26x86.vmapple-apple-silicon/1',profile_id:'vmapple-m1-macos',interrupt_controller:{sandbox_contract:'AIC',current_vmapple_qemu:'GICv3'},reference:{name:'qemu-t8030',machine_type:'t8030',guest_scope:'iPhone 11 / iOS'},device_topology:[{name:'AIC',status:'required-gap',current_vmapple_qemu:'GICv3 baseline'}]}, values:{
        qemu:'/opt/qemu-system-aarch64', qemu_img:'/usr/bin/qemu-img',
        firmware:'/assets/AVPBooter.bin', ibss:'/assets/iBSS.img4',
        ibec:'/assets/iBEC.img4', build_manifest:'/assets/BuildManifest.plist',
        tss_helper:'/assets/tss-request', original_ibss:'/assets/iBSS.im4p',
        original_ibec:'/assets/iBEC.im4p', aux:'/assets/aux.raw', root:'/assets/root.raw',
        output:'/tmp/26x86-vmapple-test'
      }}),
      inspect_vmapple_storage: () => ({ok:true, provisioning_status:'unverified',
        provisioned:null, installer_ui_possible:null, installer_ui_verified:false,
        blockers:[], markers:['NXSB'], base_images_read_only:true}),
      get_boot_picker_status: () => pickerSnapshot(),
      start_boot_picker: () => {pickerState='armed'; pickerSelection=null; return pickerSnapshot();},
      tick_boot_picker: () => pickerSnapshot(),
      boot_picker_key: key => {if (key === 'Alt' && pickerState === 'armed') pickerState='picker'; return pickerSnapshot();},
      select_boot_entry: id => {pickerSelection=id; pickerState='selected'; return pickerSnapshot();},
      launch_vmapple: config => ({ok:true, spawned:true, pid:42, target_major:config.target_major,
        machine_type:config.machine_type, guest_os:config.guest_os, recovery_protocol:config.recovery_protocol,
        display_backend:config.display, forced_transition:false, macos_boot_verified:false}),
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
    await page.locator('#vmapple-boot-start').click();
    await page.keyboard.press('Alt');
    await page.locator('[data-boot-entry="recovery"]').click();
    await page.getByText('Apple Silicon 장치 프로필', {exact:true}).waitFor();
    await page.getByText(/qemu-t8030의 t8030 장치 구성을/, {exact:false}).waitFor();
    await page.locator('#vmapple-storage-inspect').click();
    await page.getByText(/저장장치 읽기 검사 완료/, {exact:false}).waitFor();
    await page.locator('#vmapple-launch').click();
    await page.getByText(/VMApple GTK 창을 열었습니다/, {exact:false}).waitFor();
    await page.locator('#sandbox-prepare').click();
    await page.getByText('EFI 자체 검사 패키지 준비 완료 · macOS 부팅 미검증', {exact:true}).waitFor();
    const calls = await page.evaluate(() => window.testCalls);
    assert(calls.some(c => c[0] === 'prepare_sandbox' && c[1] === 27 && c[2] === 'C:/26x86-output'));
    assert(calls.some(c => c[0] === 'launch_vmapple' && c[1].target_major === 27 && c[1].research_only === true));
    assert(calls.some(c => c[0] === 'launch_vmapple' && c[1].machine_type === 'iBoot(AArch64)' && c[1].guest_os === 'macOS' && c[1].recovery_protocol === 'DFU/IPSW'));
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
