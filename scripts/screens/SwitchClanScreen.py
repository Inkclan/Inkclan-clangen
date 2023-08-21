import logging
import os
import platform
import subprocess
import traceback

import pygame
import pygame_gui
import ujson

from scripts.cat.cats import Cat
from scripts.clan import Clan
from scripts.game_structure.discord_rpc import _DiscordRPC
from scripts.game_structure.game_essentials import game, screen, screen_x, screen_y, MANAGER
from scripts.game_structure.image_button import UIImageButton
from scripts.game_structure.windows import DeleteCheck, SaveError
from scripts.utility import get_text_box_theme, scale, quit  # pylint: disable=redefined-builtin
from .Screens import Screens
from ..housekeeping.datadir import get_data_dir
from ..housekeeping.version import get_version_info

logger = logging.getLogger(__name__)

class SwitchClanScreen(Screens):
    """
    TODO: DOCS
    """

    def handle_event(self, event):
        """
        TODO: DOCS
        """
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if game.switches['window_open']:
                pass
            elif event.ui_element == self.main_menu:
                self.change_screen('start screen')
            elif event.ui_element == self.next_page_button:
                self.page += 1
                self.update_page()
            elif event.ui_element == self.previous_page_button:
                self.page -= 1
                self.update_page()
            else:
                for page in self.delete_buttons:
                    if event.ui_element in page:
                        DeleteCheck(
                            self.change_screen,
                            self.clan_name[self.page][page.index(
                                event.ui_element)])

                        return

                for page in self.clan_buttons:
                    if event.ui_element in page:
                        Clan.switch_clans(
                            self.clan_name[self.page][page.index(
                                event.ui_element)])

        elif event.type == pygame.KEYDOWN and game.settings['keybinds']:
            if event.key == pygame.K_ESCAPE:
                self.change_screen('start screen')

    def exit_screen(self):
        """
        TODO: DOCS
        """
        self.main_menu.kill()
        del self.main_menu
        self.info.kill()
        del self.info
        self.current_clan.kill()
        del self.current_clan

        # del self.screen  # No need to keep that in memory.

        for page in self.clan_buttons:
            for button in page:
                button.kill()
                del button  # pylint: disable=modified-iterating-list

        for page in self.delete_buttons:
            for button in page:
                button.kill()
                del button  # pylint: disable=modified-iterating-list

        self.next_page_button.kill()
        del self.next_page_button
        self.previous_page_button.kill()
        del self.previous_page_button
        self.page_number.kill()
        del self.page_number

        self.clan_buttons = [[]]
        self.delete_buttons = [[]]
        self.clan_name = [[]]

    def screen_switches(self):
        """
        TODO: DOCS
        """
        self.screen = pygame.transform.scale(
            pygame.image.load(
                "resources/images/clan_saves_frame.png").convert_alpha(),
            (440 / 1600 * screen_x, 750 / 1400 * screen_y))
        self.main_menu = UIImageButton(scale(pygame.Rect((50, 50), (306, 60))),
                                       "",
                                       object_id="#main_menu_button",
                                       manager=MANAGER)
        self.info = pygame_gui.elements.UITextBox(
            'Note: This will close the game.\n When you open it next, it should have the new Clan.',
            # pylint: disable=line-too-long
            scale(pygame.Rect((200, 1200), (1200, 140))),
            object_id=get_text_box_theme("#text_box_30_horizcenter"),
            manager=MANAGER)

        self.current_clan = pygame_gui.elements.UITextBox(
            "",
            scale(pygame.Rect((200, 200), (1200, 140))),
            object_id=get_text_box_theme("#text_box_30_horizcenter"),
            manager=MANAGER)
        if game.clan:
            self.current_clan.set_text(
                f"The currently loaded Clan is {game.clan.name}Clan")
        else:
            self.current_clan.set_text("There is no Clan currently loaded.")

        self.clan_list = game.read_clans()

        self.clan_buttons = [[]]
        self.clan_name = [[]]
        self.delete_buttons = [[]]

        i = 0
        y_pos = 378
        for clan in self.clan_list[1:]:
            self.clan_name[-1].append(clan)
            self.clan_buttons[-1].append(
                pygame_gui.elements.UIButton(scale(
                    pygame.Rect((600, y_pos), (400, 78))),
                    clan + "Clan",
                    object_id="#saved_clan",
                    manager=MANAGER))
            self.delete_buttons[-1].append(
                UIImageButton(scale(pygame.Rect((940, y_pos + 17), (44, 44))),
                              "",
                              object_id="#exit_window_button",
                              manager=MANAGER,
                              starting_height=2))

            y_pos += 82
            i += 1
            if i >= 8:
                self.clan_buttons.append([])
                self.clan_name.append([])
                self.delete_buttons.append([])
                i = 0
                y_pos = 378

        self.next_page_button = UIImageButton(scale(
            pygame.Rect((912, 1080), (68, 68))),
            "",
            object_id="#arrow_right_button",
            manager=MANAGER)
        self.previous_page_button = UIImageButton(
            scale(pygame.Rect((620, 1080), (68, 68))),
            "",
            object_id="#arrow_left_button",
            manager=MANAGER)
        self.page_number = pygame_gui.elements.UITextBox(
            "",
            scale(pygame.Rect((680, 1080), (220, 60))),
            object_id=get_text_box_theme("#text_box_30_horizcenter"),
            manager=MANAGER)
        self.page = 0

        self.update_page()

        return super().screen_switches()

    def update_page(self):
        """
        TODO: DOCS
        """

        if self.page == 0:
            self.previous_page_button.disable()
        else:
            self.previous_page_button.enable()

        if self.page >= len(self.clan_buttons) - 1:
            self.next_page_button.disable()
        else:
            self.next_page_button.enable()

        self.page_number.set_text(
            f"Page {self.page + 1} of {len(self.clan_buttons)}")

        for page in self.clan_buttons:
            for button in page:
                button.hide()
        for page in self.delete_buttons:
            for button in page:
                button.hide()

        for button in self.clan_buttons[self.page]:
            button.show()

        for button in self.delete_buttons[self.page]:
            button.show()

    def on_use(self):
        """
        TODO: DOCS
        """
        screen.blit(self.screen,
                    (580 / 1600 * screen_x, 300 / 1400 * screen_y))


with open('resources/gamesettings.json', 'r', encoding='utf-8') as f:
    settings_dict = ujson.load(f)


class SettingsScreen(Screens):
    """
    TODO: DOCS
    """
    text_size = {
        '0': 'small',
        '1': 'medium',
        '2': 'big'
    }  # How text sizes will show up on the screen
    bool = {True: 'Yes', False: 'No', None: 'None'}
    sub_menu = 'general'

    # This is set to the current settings when the screen is opened.
    # All edits are made directly to game.settings, however, when you
    #  leave the screen,game.settings will be reverted based on this variable
    #   However, if settings are saved, edits will also be made to this variable.
    settings_at_open = {}

    # Have the settings been changed since the page was open or since settings were saved?
    settings_changed = False

    # Contains the checkboxes
    checkboxes = {}
    # Contains the text for the checkboxes.
    checkboxes_text = {}

    # contains the tooltips for contributors
    tooltip = {}

    info_text = ""
    tooltip_text = []
    with open('resources/credits_text.json', 'r', encoding='utf-8') as f:
        credits_text = ujson.load(f)
    for string in credits_text["text"]:
        if string == "{contrib}":
            for contributor in credits_text["contrib"]:
                info_text += contributor + "<br>"
                tooltip_text.append(credits_text["contrib"][contributor])
        else:
            info_text += string
            info_text += "<br>"

    def handle_event(self, event):
        """
        TODO: DOCS
        """
        if event.type == pygame_gui.UI_TEXT_BOX_LINK_CLICKED:
            if platform.system() == 'Darwin':
                subprocess.Popen(["open", "-u", event.link_target])
            elif platform.system() == 'Windows':
                os.system(f"start \"\" {event.link_target}")
            elif platform.system() == 'Linux':
                subprocess.Popen(['xdg-open', event.link_target])
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element == self.main_menu_button:
                self.change_screen('start screen')
                return
            if event.ui_element == self.fullscreen_toggle:
                game.switch_setting('fullscreen')
                quit(savesettings=True, clearevents=False)
            elif event.ui_element == self.open_data_directory_button:
                if platform.system() == 'Darwin':
                    subprocess.Popen(["open", "-R", get_data_dir()])
                elif platform.system() == 'Windows':
                    os.startfile(get_data_dir())  # pylint: disable=no-member
                elif platform.system() == 'Linux':
                    try:
                        subprocess.Popen(['xdg-open', get_data_dir()])
                    except OSError:
                        logger.exception("Failed to call to xdg-open.")
                return
            elif event.ui_element == self.save_settings_button:
                self.save_settings()
                try:
                    game.save_settings()
                except:
                    SaveError(traceback.format_exc())
                    self.change_screen("start screen")
                self.settings_changed = False
                self.update_save_button()
                return
            elif event.ui_element == self.relation_settings_button:
                self.open_relation_settings()
                return
            elif event.ui_element == self.general_settings_button:
                self.open_general_settings()
                return
            elif event.ui_element == self.info_button:
                self.open_info_screen()
                return
            elif event.ui_element == self.language_button:
                self.open_lang_settings()
            if self.sub_menu in ['general', 'relation', 'language']:
                self.handle_checkbox_events(event)

        elif event.type == pygame.KEYDOWN and game.settings['keybinds']:
            if event.key == pygame.K_ESCAPE:
                self.change_screen('start screen')
            elif event.key == pygame.K_RIGHT:
                if self.sub_menu == 'general':
                    self.open_relation_settings()
                elif self.sub_menu == 'relation':
                    self.open_info_screen()
                elif self.sub_menu == 'info':
                    self.open_lang_settings()
            elif event.key == pygame.K_LEFT:
                if self.sub_menu == 'relation':
                    self.open_general_settings()
                elif self.sub_menu == 'info':
                    self.open_relation_settings()
                elif self.sub_menu == 'language':
                    self.open_info_screen()

    def handle_checkbox_events(self, event):
        """
        TODO: DOCS
        """
        if event.ui_element in self.checkboxes.values():
            for key, value in self.checkboxes.items():
                if value == event.ui_element:
                    if self.sub_menu == 'language':
                        game.settings['language'] = key
                    else:
                        game.switch_setting(key)
                    self.settings_changed = True
                    self.update_save_button()
                    if self.sub_menu == 'general' and event.ui_element is self.checkboxes['discord']:
                        if game.settings['discord']:
                            print("Starting Discord RPC")
                            game.rpc = _DiscordRPC("1076277970060185701",
                                                   daemon=True)
                            game.rpc.start()
                            game.rpc.start_rpc.set()
                        else:
                            print("Stopping Discord RPC")
                            game.rpc.close()

                    opens = {
                        "general": self.open_general_settings,
                        "language": self.open_lang_settings,
                        "relation": self.open_relation_settings
                    }

                    scroll_pos = None
                    if "container_general" in self.checkboxes_text and \
                            self.checkboxes_text["container_general"].vert_scroll_bar:
                        scroll_pos = self.checkboxes_text["container_general"].vert_scroll_bar.start_percentage

                    if self.sub_menu in opens:
                        opens[self.sub_menu]()

                    if scroll_pos is not None:
                        self.checkboxes_text["container_general"].vert_scroll_bar.set_scroll_from_start_percentage(
                            scroll_pos)

                    break

    def screen_switches(self):
        """
        TODO: DOCS
        """
        self.settings_changed = False

        self.general_settings_button = UIImageButton(
            scale(pygame.Rect((200, 200), (300, 60))),
            "",
            object_id="#general_settings_button",
            manager=MANAGER)
        self.relation_settings_button = UIImageButton(
            scale(pygame.Rect((500, 200), (300, 60))),
            "",
            object_id="#relation_settings_button",
            manager=MANAGER)
        self.info_button = UIImageButton(scale(
            pygame.Rect((800, 200), (300, 60))),
            "",
            object_id="#info_settings_button",
            manager=MANAGER)
        self.language_button = UIImageButton(scale(
            pygame.Rect((1100, 200), (300, 60))),
            "",
            object_id="#lang_settings_button",
            manager=MANAGER)
        self.save_settings_button = UIImageButton(
            scale(pygame.Rect((654, 1100), (292, 60))),
            "",
            object_id="#save_settings_button",
            manager=MANAGER)

        if game.settings['fullscreen']:
            self.fullscreen_toggle = UIImageButton(
                scale(pygame.Rect((1234, 50), (316, 72))),
                "",
                object_id="#toggle_fullscreen_button",
                manager=MANAGER,
                tool_tip_text="This will close the game. "
                "When you reopen, the game"
                " will be windowed. ")
        else:
            self.fullscreen_toggle = UIImageButton(
                scale(pygame.Rect((1234, 50), (316, 72))),
                "",
                object_id="#toggle_fullscreen_button",
                manager=MANAGER,
                tool_tip_text="This will close the game. "
                "When you reopen, the game"
                " will be fullscreen. ")

        self.open_data_directory_button = UIImageButton(
            scale(pygame.Rect((50, 1290), (356, 60))),
            "",
            object_id="#open_data_directory_button",
            manager=MANAGER,
            tool_tip_text="Opens the data directory. "
                          "This is where save files "
                          "and logs are stored.")

        if get_version_info().is_sandboxed:
            self.open_data_directory_button.hide()

        self.update_save_button()
        self.main_menu_button = UIImageButton(scale(
            pygame.Rect((50, 50), (305, 60))),
            "",
            object_id="#main_menu_button",
            manager=MANAGER)
        self.sub_menu = 'general'
        self.open_general_settings()

        self.settings_at_open = game.settings.copy()

        self.refresh_checkboxes()

    def update_save_button(self):
        """
        Updates the disabled state the save button
        """
        if not self.settings_changed:
            self.save_settings_button.disable()
        else:
            self.save_settings_button.enable()

    def exit_screen(self):
        """
        TODO: DOCS
        """
        self.clear_sub_settings_buttons_and_text()
        self.general_settings_button.kill()
        del self.general_settings_button
        self.relation_settings_button.kill()
        del self.relation_settings_button
        self.info_button.kill()
        del self.info_button
        self.language_button.kill()
        del self.language_button
        self.save_settings_button.kill()
        del self.save_settings_button
        self.main_menu_button.kill()
        del self.main_menu_button
        self.fullscreen_toggle.kill()
        del self.fullscreen_toggle
        self.open_data_directory_button.kill()
        del self.open_data_directory_button

        game.settings = self.settings_at_open

    def save_settings(self):
        """Saves the settings, ensuring that they will be retained when the screen changes."""
        self.settings_at_open = game.settings.copy()

    def open_general_settings(self):
        """Opens and draws general_settings"""
        self.enable_all_menu_buttons()
        self.general_settings_button.disable()
        self.clear_sub_settings_buttons_and_text()
        self.sub_menu = 'general'
        self.save_settings_button.show()

        self.checkboxes_text[
            "container_general"] = pygame_gui.elements.UIScrollingContainer(
            scale(pygame.Rect((0, 440), (1400, 600))), manager=MANAGER)

        n = 0
        for code, desc in settings_dict['general'].items():
            self.checkboxes_text[code] = pygame_gui.elements.UITextBox(
                desc[0],
                scale(pygame.Rect((450, n * 78), (1000, 78))),
                container=self.checkboxes_text["container_general"],
                object_id=get_text_box_theme("#text_box_30_horizleft_pad_0_8"),
                manager=MANAGER)
            self.checkboxes_text[code].disable()
            n += 1

        self.checkboxes_text[
            "container_general"].set_scrollable_area_dimensions(
            (1360 / 1600 * screen_x, (n * 78 + 80) / 1400 * screen_y))

        self.checkboxes_text['instr'] = pygame_gui.elements.UITextBox(
            "Change the general settings of your game here",
            scale(pygame.Rect((200, 320), (1200, 100))),
            object_id=get_text_box_theme("#text_box_30_horizcenter"),
            manager=MANAGER)

        # This is where the actual checkboxes are created. I don't like
        #   how this is separated from the text boxes, but I've spent too much time to rewrite it.
        #   It has to separated because the checkboxes must be updated when settings are changed.
        #   Fix if you want. - keyraven
        self.refresh_checkboxes()

    def open_relation_settings(self):
        """Opens and draws relation_settings"""
        self.enable_all_menu_buttons()
        self.relation_settings_button.disable()
        self.clear_sub_settings_buttons_and_text()
        self.sub_menu = 'relation'
        self.save_settings_button.show()

        self.checkboxes_text[
            "container_relation"] = pygame_gui.elements.UIScrollingContainer(
            scale(pygame.Rect((0, 440), (1400, 600))), manager=MANAGER)

        n = 0
        for code, desc in settings_dict['relation'].items():
            self.checkboxes_text[code] = pygame_gui.elements.UITextBox(
                desc[0],
                scale(pygame.Rect((450, n * 78), (1000, 78))),
                container=self.checkboxes_text["container_relation"],
                object_id=get_text_box_theme("#text_box_30_horizleft_pad_0_8"),
                manager=MANAGER)
            self.checkboxes_text[code].disable()
            n += 1

        self.checkboxes_text['instr'] = pygame_gui.elements.UITextBox(
            "Change the relationship settings of your game here",
            scale(pygame.Rect((200, 320), (1200, 100))),
            object_id=get_text_box_theme("#text_box_30_horizcenter"),
            manager=MANAGER)

        self.refresh_checkboxes()

    def open_info_screen(self):
        """Open's info screen"""
        self.enable_all_menu_buttons()
        self.info_button.disable()
        self.clear_sub_settings_buttons_and_text()
        self.sub_menu = 'info'
        self.save_settings_button.hide()

        self.checkboxes_text["info_container"] = pygame_gui.elements.UIScrollingContainer(
            scale(pygame.Rect((200, 300), (1200, 1000))),
            manager=MANAGER
        )

        self.checkboxes_text['info_text_box'] = pygame_gui.elements.UITextBox(
            self.info_text,
            scale(pygame.Rect((0, 0), (1150, 8000))),
            object_id=get_text_box_theme("#text_box_30_horizcenter"),
            container=self.checkboxes_text["info_container"],
            manager=MANAGER)

        self.checkboxes_text['info_text_box'].disable()

        i = 0
        y_pos = 731
        for tooltip in self.tooltip_text:
            if not tooltip:
                self.tooltip[f'tip{i}'] = UIImageButton(
                    scale(pygame.Rect((400, i * 56 + y_pos), (400, 56))),
                    "",
                    object_id="#blank_button",
                    container=self.checkboxes_text["info_container"],
                    manager=MANAGER,
                    starting_height=2
                ),
            else:
                self.tooltip[f'tip{i}'] = UIImageButton(
                    scale(pygame.Rect((400, i * 56 + y_pos), (400, 56))),
                    "",
                    object_id="#blank_button",
                    container=self.checkboxes_text["info_container"],
                    manager=MANAGER,
                    tool_tip_text=tooltip,
                    starting_height=2
                ),

            i += 1
        self.checkboxes_text["info_container"].set_scrollable_area_dimensions(
            (1150 / 1600 * screen_x, (i * 56 + y_pos + 550) / 1400 * screen_y))

    def open_lang_settings(self):
        """Open Language Settings"""
        self.enable_all_menu_buttons()
        self.language_button.disable()
        self.clear_sub_settings_buttons_and_text()
        self.sub_menu = 'language'
        self.save_settings_button.show()

        self.checkboxes_text['instr'] = pygame_gui.elements.UITextBox(
            "Change the language of the game here. This has not been implemented yet.",
            scale(pygame.Rect((200, 320), (1200, 100))),
            object_id=get_text_box_theme("#text_box_30_horizcenter"),
            manager=MANAGER)

        self.refresh_checkboxes()

    def refresh_checkboxes(self):
        """
        TODO: DOCS
        """
        # Kill the checkboxes. No mercy here.
        for checkbox in self.checkboxes.values():
            checkbox.kill()
        self.checkboxes = {}

        # CHECKBOXES (ehhh) FOR LANGUAGES
        if self.sub_menu == 'language':
            self.checkboxes['english'] = UIImageButton(
                scale(pygame.Rect((620, 400), (360, 102))),
                "",
                object_id="#english_lang_button",
                manager=MANAGER)
            self.checkboxes['spanish'] = UIImageButton(
                scale(pygame.Rect((620, 502), (360, 74))),
                "",
                object_id="#spanish_lang_button",
                manager=MANAGER)
            self.checkboxes['german'] = UIImageButton(
                scale(pygame.Rect((620, 576), (360, 74))),
                "",
                object_id="#german_lang_button",
                manager=MANAGER)

            if game.settings['language'] == 'english':
                self.checkboxes['english'].disable()
            elif game.settings['language'] == 'spanish':
                self.checkboxes['spanish'].disable()
            elif game.settings['language'] == 'german':
                self.checkboxes['german'].disable()

        else:
            n = 0
            for code, desc in settings_dict[self.sub_menu].items():
                if game.settings[code]:
                    box_type = "#checked_checkbox"
                else:
                    box_type = "#unchecked_checkbox"
                self.checkboxes[code] = UIImageButton(
                    scale(pygame.Rect((340, n * 78), (68, 68))),
                    "",
                    object_id=box_type,
                    container=self.checkboxes_text["container_" +
                                                   self.sub_menu],
                    tool_tip_text=desc[1])
                n += 1

    def clear_sub_settings_buttons_and_text(self):
        """
        TODO: DOCS
        """
        for checkbox in self.checkboxes.values():
            checkbox.kill()
        self.checkboxes = {}
        for text in self.checkboxes_text.values():
            text.kill()
        self.checkboxes_text = {}

    def enable_all_menu_buttons(self):
        """
        TODO: DOCS
        """
        self.general_settings_button.enable()
        self.relation_settings_button.enable()
        self.info_button.enable()
        self.language_button.enable()

    def on_use(self):
        """
        TODO: DOCS
        """


class StatsScreen(Screens):
    """
    TODO: DOCS
    """

    def screen_switches(self):
        """
        TODO: DOCS
        """

        self.set_disabled_menu_buttons(["stats"])
        self.show_menu_buttons()
        self.update_heading_text(f'{game.clan.name}Clan')

        # Determine stats
        living_num = 0
        warriors_num = 0
        app_num = 0
        kit_num = 0
        elder_num = 0
        starclan_num = 0
        medcat_num = 0
        other_num = 0
        for cat in Cat.all_cats.values():
            if not cat.dead and not (cat.outside or cat.exiled):
                living_num += 1
                if cat.status == 'warrior':
                    warriors_num += 1
                elif cat.status in ['apprentice', 'medicine cat apprentice']:
                    app_num += 1
                elif cat.status in ['kitten', 'newborn']:
                    kit_num += 1
                elif cat.status == 'elder':
                    elder_num += 1
                elif cat.status == 'medicine cat':
                    medcat_num += 1
            elif (cat.status in ['kittypet', 'loner', 'rogue', 'former Clancat']
                  or cat.outside) and not cat.dead:
                other_num += 1
            else:
                starclan_num += 1

        stats_text = f"Number of Living Cats: {living_num}\n\n" + \
                     f"Number of Med. Cats: {medcat_num}\n\n" + \
                     f"Number of Warriors: {warriors_num}\n\n" + \
                     f"Number of Apprentices: {app_num}\n\n" + \
                     f"Number of Kits: {kit_num}\n\n" + \
                     f"Number of Elders: {elder_num}\n\n" + \
                     f"Number of Cats Outside the Clans: {other_num}\n\n" + \
                     f"Number of Dead Cats: {starclan_num}"

        self.stats_box = pygame_gui.elements.UITextBox(
            stats_text,
            scale(pygame.Rect((200, 300), (1200, 1000))),
            manager=MANAGER,
            object_id=get_text_box_theme("#text_box_30_horizcenter"))

    def exit_screen(self):
        """
        TODO: DOCS
        """
        self.stats_box.kill()
        del self.stats_box

    def handle_event(self, event):
        """
        TODO: DOCS
        """
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            self.menu_button_pressed(event)

    def on_use(self):
        """
        TODO: DOCS
        """