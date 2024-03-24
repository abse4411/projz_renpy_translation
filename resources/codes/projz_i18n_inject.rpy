# coding=utf8
# projz_renpy_translation, a translator for RenPy games
# Copyright (C) 2023  github.com/abse4411
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

###########################################################
# ________  ________  ________        ___  ________       #
# |\   __  \|\   __  \|\   __  \      |\  \|\_____  \     #
# \ \  \|\  \ \  \|\  \ \  \|\  \     \ \  \\|___/  /|    #
#  \ \   ____\ \   _  _\ \  \\\  \  __ \ \  \   /  / /    #
#   \ \  \___|\ \  \\  \\ \  \\\  \|\  \\_\  \ /  /_/__   #
#    \ \__\    \ \__\\ _\\ \_______\ \________\\________\ #
#     \|__|     \|__|\|__|\|_______|\|________|\|_______| #
#                                                         #
#  This rpy file is generated by the project:             #
#  https://github.com/abse4411/projz_renpy_translation)   #
###########################################################
# Note: Run after define statements of font in gui.rpy
init offset = 999
# # Enable developer console
# init python:
#     if {projz_enable_console_content}:
#         renpy.config.developer = True

# location of fotns
define projz_font_dir = "{projz_fonts_dir}"
# Names of gui font var for saving default font
define projz_gui_vars = ["projz_gui_text_font","projz_gui_name_text_font","projz_gui_interface_text_font","projz_gui_button_text_font","projz_gui_choice_button_text_font","projz_gui_system_font","projz_gui_main_font"]
# Names of gui font var for saving selected font
define projz_sgui_vars = ["projz_sgui_text_font","projz_sgui_name_text_font","projz_sgui_interface_text_font","projz_sgui_button_text_font","projz_sgui_choice_button_text_font","projz_sgui_system_font","projz_sgui_main_font"]
define projz_gui_names = ["Text Font","Name Text Font","Interface Text Font","Button Text Font","Choice Button Text Font","System Font","Main Font"]
# Names for saving current selected font by our setting
# define projz_gui_selected_font = "projz_gui_selected_font"
init python:
    from store import persistent
    def projz_dget(name, dvalue=None):
        if hasattr(persistent, name) and getattr(persistent, name) is not None:
            return getattr(persistent, name)
        sname = name.replace('projz_s', 'projz_')
        if hasattr(persistent, sname) and getattr(persistent, sname) is not None:
            return getattr(persistent, sname)
        return dvalue

    def projz_get(name, dvalue=None):
        if hasattr(persistent, name) and getattr(persistent, name) is not None:
            return getattr(persistent, name)
        return dvalue

    def projz_set(name, value):
        setattr(persistent, name, value)
        return value

    def projz_dset(name, dobj, dname, dvalue=None):
        if hasattr(persistent, name) and getattr(persistent, name) is not None:
            return getattr(persistent, name)
        if hasattr(dobj, dname):
            return projz_set(name, getattr(dobj, dname))
        return projz_set(name, dvalue)

    def projz_config_get(name, dvalue=None):
        return projz_get("projz_config_"+name, dvalue)

    def projz_config_set(name, value):
        projz_set("projz_config_"+name, value)
        setattr(renpy.config, name, value)

    if projz_config_get("developer") is not None:
        renpy.config.developer = projz_config_get("developer")
    else:
        projz_config_set("developer", {projz_enable_developer_content})

    if projz_config_get("console", None) is not None:
        renpy.config.console = projz_config_get("console")
    else:
        projz_config_set("console", {projz_enable_console_content})

    # save default fonts
    projz_dset(projz_gui_vars[0], gui, 'text_font')
    projz_dset(projz_gui_vars[1], gui, 'name_text_font')
    projz_dset(projz_gui_vars[2], gui, 'interface_text_font')
    projz_dset(projz_gui_vars[3], gui, 'button_text_font')
    projz_dset(projz_gui_vars[4], gui, 'choice_button_text_font')
    projz_dset(projz_gui_vars[5], gui, 'system_font')
    projz_dset(projz_gui_vars[6], gui, 'main_font')


################### Make font vars dynamic since Ren’Py 6.99.14 ###################
# define gui.text_font = gui.preference(projz_gui_vars[0], gui.text_font)
# define gui.name_text_font = gui.preference(projz_gui_vars[1], gui.name_text_font)
# define gui.interface_text_font = gui.preference(projz_gui_vars[2], gui.interface_text_font)
# define gui.button_text_font = gui.preference(projz_gui_vars[3], gui.button_text_font)
# define gui.choice_button_text_font = gui.preference(projz_gui_vars[4], gui.choice_button_text_font)
###################################################################################

################### Make font vars dynamic by our implementation ###################
define gui.text_font = projz_dget(projz_sgui_vars[0])
define gui.name_text_font = projz_dget(projz_sgui_vars[1])
define gui.interface_text_font = projz_dget(projz_sgui_vars[2])
define gui.button_text_font = projz_dget(projz_sgui_vars[3])
define gui.choice_button_text_font = projz_dget(projz_sgui_vars[4])
define gui.system_font = projz_dget(projz_sgui_vars[5])
define gui.main_font = projz_dget(projz_sgui_vars[6])
####################################################################################

# define projz_languages = {"korean": ("한국어", "SourceHanSansLite.ttf"), "japanese": ("日本語","SourceHanSansLite.ttf"), "french":("Русский","DejaVuSans.ttf"), "chinese": ("简体中文","SourceHanSansLite.ttf")}
define projz_languages = {{projz_lang_content}}
#define projz_fonts = ["DejaVuSans.ttf", "KMKDSP.ttf", "SourceHanSansLite.ttf"]
define projz_fonts = [{projz_font_content}]
# Note that: fonts should be placed in "game/projz_fonts"


init python:
    from store import persistent, Action, DictEquality
    class ProjzFontAction(Action, DictEquality):
        def __init__(self, name, value, rebuild=True):
            self.name = name
            self.value = value
            self.rebuild = rebuild

        def __call__(self):
            projz_set(self.name, self.value)

            if self.rebuild:
                gui.rebuild()

        def get_selected(self):
            return projz_get(self.name, None) == self.value

    class ProjzDefaultFontAction(Action, DictEquality):
        def __init__(self, name, rebuild=True):
            self.name = name
            self.rebuild = rebuild

        def __call__(self):
            projz_set(self.name, None)

            if self.rebuild:
                gui.rebuild()

        def get_selected(self):
            return projz_get(self.name, None) is None

    class ProjzAllFontAction(Action, DictEquality):
        def __init__(self, value, rebuild=True):
            self.value = value
            self.rebuild = rebuild

        def __call__(self):
            for name in projz_sgui_vars:
                projz_set(name, self.value)

            if self.rebuild:
                gui.rebuild()

        def get_selected(self):
            for i in range(len(projz_sgui_vars)):
                sfont = projz_get(projz_sgui_vars[i], None)
                if sfont is None or sfont != self.value:
                    return False
            return True

    class ProjzDefaultAllFontAction(Action, DictEquality):
        def __init__(self, rebuild=True):
            self.rebuild = rebuild

        def __call__(self):
            for name in projz_sgui_vars:
                projz_set(name, None)

            if self.rebuild:
                gui.rebuild()

        def get_selected(self):
            for name in projz_sgui_vars:
                if projz_get(name, None) is not None:
                    return False
            return True

    class ProjzConfigAction(Action, DictEquality):
        def __init__(self, name, value, rebuild=True):
            self.name = name
            self.value = value
            self.rebuild = rebuild

        def __call__(self):
            projz_config_set(self.name, self.value)

            if self.rebuild:
                gui.rebuild()

        def get_selected(self):
            if hasattr(renpy.config, self.name) and getattr(renpy.config, self.name) == self.value:
                return True
            return False

    def projz_set_font(font):
        for name in projz_sgui_vars:
            projz_set(name, font)
        gui.rebuild()

    def projz_show_i18n_settings():
        renpy.show_screen('projz_i18n_settings')

    def projz_reload_game():
        renpy.reload_script()

    config.underlay[0].keymap['projz_show_i18n_settings'] = projz_show_i18n_settings
    config.keymap['projz_show_i18n_settings'] = ['{projz_shortcut_key}']

screen projz_i18n_settings():
    default show_more = False
    tag menu
    use game_menu(_("I18n settings"), scroll="viewport"):
        vbox:
            hbox:
                box_wrap True
                vbox:
                    style_prefix "radio"
                    label _("Language")
                    textbutton _("Default") action [Function(projz_set_font, None), Language(None)]
                    for k,v in projz_languages.items():
                        textbutton v[0] text_font projz_font_dir+v[1] action [Function(projz_set_font, projz_font_dir+v[1]), Language(k)]
                ################### Make font vars dynamic by our implementation ###################
                vbox:
                    style_prefix "radio"
                    label _("Font")
                    textbutton _("Default") action ProjzDefaultAllFontAction()
                    for f in projz_fonts:
                        textbutton f:
                            text_font projz_font_dir+f
                            action ProjzAllFontAction(projz_font_dir+f)
                vbox:
                    style_prefix "radio"
                    label _("Other Font Settings")
                    textbutton _("Expand") action SetScreenVariable("show_more", True)
                    textbutton _("Collapse") action SetScreenVariable("show_more", False)
                showif show_more == True:
                    for sf,n in zip(projz_sgui_vars, projz_gui_names):
                        vbox:
                            style_prefix "radio"
                            label _(n)
                            textbutton _("Default") action ProjzDefaultFontAction(sf)
                            for f in projz_fonts:
                                textbutton f:
                                    text_font projz_font_dir+f
                                    action ProjzFontAction(sf, projz_font_dir+f)
                ####################################################################################

                ################### Make font vars dynamic since Ren’Py 6.99.14 ###################
                # vbox:
                #     style_prefix "radio"
                #     label _("Font")
                #     textbutton "Default" action [gui.SetPreference(projz_gui_vars[0], persistent.projz_gui_text_font, rebuild=False), gui.SetPreference(projz_gui_vars[1], persistent.projz_gui_name_text_font, rebuild=False), gui.SetPreference(projz_gui_vars[2], persistent.projz_gui_interface_text_font, rebuild=False), gui.SetPreference(projz_gui_vars[3], persistent.projz_gui_button_text_font, rebuild=False), gui.SetPreference(projz_gui_vars[4], persistent.projz_gui_choice_button_text_font, rebuild=True)]
                #     for f in projz_fonts:
                #         textbutton f:
                #             text_font f
                #             action [gui.SetPreference(projz_gui_vars[0], "projz_fonts/"+f, rebuild=False), gui.SetPreference(projz_gui_vars[1], "projz_fonts/"+f, rebuild=False), gui.SetPreference(projz_gui_vars[2], "projz_fonts/"+f, rebuild=False), gui.SetPreference(projz_gui_vars[3], "projz_fonts/"+f, rebuild=False), gui.SetPreference(projz_gui_vars[4], "projz_fonts/"+f, rebuild=True)]
                ###################################################################################
                null height 10
                hbox:
                    style_prefix "slider"
                    box_wrap True
                    vbox:
                        label _("Text Size Scaling")
                        bar value Preference("font size")
                        textbutton _("Reset") action Preference("font size", 1.0)
                    vbox:
                        label _("Line Spacing Scaling")
                        bar value Preference("font line spacing")
                        textbutton _("Reset") action Preference("font line spacing", 1.0)
                null height 10
                hbox:
                    vbox:
                        style_prefix "radio"
                        label _("Developer Mode")
                        textbutton "auto" action [ProjzConfigAction("developer", "auto")]
                        textbutton "True" action [ProjzConfigAction("developer", True)]
                        textbutton "False" action [ProjzConfigAction("developer", False)]
                        text _("Reload Required")
                    vbox:
                        style_prefix "radio"
                        label _("Console (Shift+O)")
                        textbutton "True" action [ProjzConfigAction("console", True)]
                        textbutton "False" action [ProjzConfigAction("console", False)]
                        text _("Reload Required")
                    vbox:
                        style_prefix "check"
                        label _("Reload Game (Shift+R)")
                        textbutton _("Reload") action[Function(projz_reload_game)]
            null height 10
            label _("Watch")
            grid 2 12:
                text _("Language")
                text "[_preferences.language]"
                text _("Developer Mode")
                text "[config.developer]"
                text _("Debug Console")
                text "[config.console]"
                text _("Text Font")
                text "[gui.text_font]"
                text _("Name Text Font")
                text "[gui.name_text_font]"
                text _("Interface Text Font")
                text "[gui.interface_text_font]"
                text _("Button Text Font")
                text "[gui.button_text_font]"
                text _("Choice Button Text Font")
                text "[gui.choice_button_text_font]"
                text _("System Font")
                text "[gui.system_font]"
                text _("Main Font")
                text "[gui.main_font]"
                text _("Text Size Scaling")
                text "[_preferences.font_size:.1]"
                text _("Line Spacing Scaling")
                text "[_preferences.font_line_spacing:.1]"

            null height 10
            label _("Note that")
            text _("If there exists the font configuration in game/tl/language/style.rpy, it will disable our font setting because of its higher priority. For more information, please see {a=https://www.renpy.org/doc/html/translation.html#style-translations}this{/a}.")
            null height 10
            text _("This plugin is injected by the {a=https://github.com/abse4411/projz_renpy_translation}projz_renpy_translation{/a} project under the {a=https://github.com/abse4411/projz_renpy_translation?tab=GPL-3.0-1-ov-file}GPL-3.0 license{/a}.") xalign 1.0
            null height 60