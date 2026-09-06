"""
Subprocess wx runner for build/install/patch flows invoked from the HTML wizard.
"""

from __future__ import annotations

import logging
import sys

from x86.gui import bootstrap
from x86.gui.branding import window_title


def _run_app(frame_factory) -> int:
    from x86.mellow.integration import configuration
    configuration()[0].require_native_apply("Native wx wizard")
    global wx, HardwarePatchsetDetection, gui_build, gui_help, gui_install_oc
    global gui_main_menu, gui_model_change, gui_support, gui_sys_patch_display, gui_sys_patch_start
    import wx
    from opencore_legacy_patcher.sys_patch.patchsets import HardwarePatchsetDetection
    from opencore_legacy_patcher.wx_gui import (gui_build, gui_help, gui_install_oc,
        gui_main_menu, gui_model_change, gui_support, gui_sys_patch_display, gui_sys_patch_start)
    from x86.gui import theme
    bootstrap.ensure_repo_on_path()
    constants = bootstrap.get_constants(start_unpack=True)
    app = wx.App(False)
    app.SetAppName(constants.patcher_name)
    theme.apply_app_theme(app)

    title = window_title(constants.patcher_version)
    frame = frame_factory(constants, title)
    frame.Show()
    app.MainLoop()
    return 0


def _action_build(c, title):
    if not gui_support.CheckProperties(c).host_can_build():
        wx.MessageBox(
            "이 Mac에서는 EFI를 만들 수 없습니다.",
            "안내",
            wx.OK | wx.ICON_INFORMATION,
        )
        return wx.Frame(None)
    return gui_build.BuildFrame(None, title=title, global_constants=c, screen_location=None)


def _action_install(c, title):
    return gui_install_oc.InstallOCFrame(None, title=title, global_constants=c, screen_location=None)


def _action_patch(c, title):
    return gui_sys_patch_display.SysPatchDisplayFrame(
        None, title=title, global_constants=c, screen_location=None
    )


def _action_unpatch(c, title):
    frame = gui_sys_patch_start.SysPatchStartFrame(
        None,
        title=title,
        global_constants=c,
        screen_location=None,
        patches=HardwarePatchsetDetection(constants=c).device_properties,
    )
    wx.CallAfter(frame.revert_root_patching)
    return frame


def _action_model_change(c, title):
    return gui_model_change.ModelPickerFrame(None, title=title, global_constants=c)


def _action_advanced(c, title):
    return gui_main_menu.MainFrame(None, title=title, global_constants=c, screen_location=None)


def _action_help(c, title):
    return gui_help.HelpFrame(None, title=title, global_constants=c, screen_location=None)


ACTIONS = {
    "build": _action_build,
    "install": _action_install,
    "patch": _action_patch,
    "unpatch": _action_unpatch,
    "model_change": _action_model_change,
    "advanced": _action_advanced,
    "help": _action_help,
}


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        logging.error("Usage: python -m x86.gui.wx_runner <action>")
        return 2

    action = argv[0]
    factory = ACTIONS.get(action)
    if factory is None:
        logging.error("Unknown wx action: %s", action)
        return 2

    try:
        return _run_app(lambda c, title: factory(c, title))
    except Exception:
        logging.exception("wx_runner failed for action %s", action)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
