import urllib.parse

import dearpygui.dearpygui as dpg

from Code.loc import Localization as loc
from Code.app_vars import AppConfig


class GUIMetaTab:
    create_file: bool = False

    @staticmethod
    def create():
        with dpg.tab(
            label=loc.get_string("gui-meta-tab-label"),
            parent="main_tab_bar",
            tag="gui_meta_tab",
        ):
            dpg.add_checkbox(label="test", default_value=GUIMetaTab.create_file)

    @staticmethod
    def generate_github_issue_link(mod_id, metadata_xml):
        params = {
            "template": "add_metadata_config.yml",
            "mod-id": str(mod_id),
            "dependency": metadata_xml,
        }

        issue_url = (
            AppConfig.github_user_url
            + "/issues/new?"
            + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
        )

        return issue_url
