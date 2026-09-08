"""
settings_panel.py: 간소화된 설정 대화상자 (Tahoe 뉴모피즘)
"""

import wx
import logging

from opencore_legacy_patcher import constants
from opencore_legacy_patcher.support import global_settings, analytics_handler
from x86.gui import theme

from . import strings


class SimplifiedSettingsDialog(wx.Dialog):
    """
    일반 사용자용 간소화 설정 패널.
    고급 설정은 X86_ADVANCED=1 환경의 SettingsFrame에서 접근합니다.
    """

    def __init__(self, parent: wx.Frame, global_constants: constants.Constants) -> None:
        super().__init__(parent, title=strings.SETTINGS_TITLE, size=(460, 320))
        theme.style_frame(self)
        self.SetMinSize((theme.DIALOG_MIN_WIDTH, 280))
        self.constants = global_constants
        self._build_ui()
        self.Centre()

    def _build_ui(self) -> None:
        root = wx.Panel(self)
        theme.style_panel(root, "page")
        outer = wx.BoxSizer(wx.VERTICAL)

        card, inner = theme.create_card(root, variant="elevated")
        sizer = wx.BoxSizer(wx.VERTICAL)

        heading = wx.StaticText(card, label=strings.SETTINGS_GENERAL)
        theme.style_static_heading(heading)
        heading.SetFont(theme.font_subheading())
        sizer.Add(heading, 0, wx.BOTTOM, theme.SPACE_MD)

        gs = global_settings.GlobalEnviromentSettings()
        analytics_default = gs.read_property("EnableCrashAndAnalyticsReporting")
        if analytics_default is None:
            analytics_default = True

        self.check_analytics = wx.CheckBox(card, label=strings.SETTINGS_ANALYTICS)
        self.check_analytics.SetValue(bool(analytics_default))
        self.check_analytics.SetFont(theme.font_body())
        self.check_analytics.SetForegroundColour(theme.colors().text_primary)
        if analytics_handler.ANALYTICS_SERVER or analytics_handler.SITE_KEY is not None:
            sizer.Add(self.check_analytics, 0, wx.BOTTOM, theme.SPACE_MD)

        note = wx.StaticText(
            card,
            label="고급 EFI·개발자 설정은 X86_ADVANCED=1 환경에서 고급 모드로 변경할 수 있습니다.",
        )
        theme.style_static_muted(note)
        theme.wrap_static_text(note, theme.DIALOG_MIN_WIDTH - theme.SPACE_XL * 2)
        sizer.Add(note, 0, wx.BOTTOM, theme.SPACE_LG)

        btn_row = wx.BoxSizer(wx.HORIZONTAL)
        cancel_btn = theme.NeumoButton(
            card,
            strings.SETTINGS_CANCEL,
            variant=theme.NeumoButton.VARIANT_GHOST,
            size=(100, 38),
        )
        save_btn = theme.NeumoButton(
            card,
            strings.SETTINGS_SAVE,
            variant=theme.NeumoButton.VARIANT_PRIMARY,
            size=(100, 38),
        )
        save_btn.SetDefault(True)
        cancel_btn.BindClick(lambda e: self.EndModal(wx.ID_CANCEL))
        save_btn.BindClick(self._on_save)
        btn_row.AddStretchSpacer()
        btn_row.Add(cancel_btn, 0, wx.RIGHT, theme.SPACE_SM)
        btn_row.Add(save_btn, 0)
        sizer.Add(btn_row, 0, wx.EXPAND)

        inner.Add(sizer, 1, wx.EXPAND | wx.ALL, theme.SPACE_LG)
        outer.Add(card, 1, wx.EXPAND | wx.ALL, theme.SPACE_MD)
        root.SetSizer(outer)

        dialog_sizer = wx.BoxSizer(wx.VERTICAL)
        dialog_sizer.Add(root, 1, wx.EXPAND)
        self.SetSizer(dialog_sizer)

    def _on_save(self, event: wx.Event = None) -> None:
        try:
            gs = global_settings.GlobalEnviromentSettings()
            if hasattr(self, "check_analytics"):
                gs.write_property(
                    "EnableCrashAndAnalyticsReporting",
                    self.check_analytics.GetValue(),
                )
            self.EndModal(wx.ID_OK)
        except Exception as exc:
            logging.error("설정 저장 실패: %s", exc)
            wx.MessageBox(
                "설정을 저장하지 못했습니다.",
                "오류",
                wx.OK | wx.ICON_ERROR,
            )
