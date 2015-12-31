#!/usr/bin/env python2

# Pacewar
# Copyright (C) 2014, 2015 Julian Marchant <onpon4@riseup.net>
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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

__version__ = "1.6.3"

import sys
import os
import math
import time
import random
import json

import sge

if getattr(sys, "frozen", False):
    __file__ = sys.executable

DATA = os.path.join(os.path.dirname(__file__), "data")
DATA_IMAGES = os.path.join(DATA, "images")
DATA_MUSIC = os.path.join(DATA, "music")
DATA_SOUNDS = os.path.join(DATA, "sounds")

VIEW_WIDTH = 1280
VIEW_HEIGHT = 720
ROOM_WIDTH = VIEW_WIDTH * 3
ROOM_HEIGHT = VIEW_HEIGHT * 3
SCALE = 0.75

JOYSTICK_THRESHOLD = 0.7

TEAM_SIZE = 8
ROUND_TICK = 2

TEAM_RED = 0
TEAM_GREEN = 1
START_X_RANGE = {TEAM_RED: [0, VIEW_WIDTH],
                 TEAM_GREEN: [ROOM_WIDTH - VIEW_WIDTH, ROOM_WIDTH]}
START_Y_RANGE = {TEAM_RED: [0, VIEW_HEIGHT],
                 TEAM_GREEN: [ROOM_HEIGHT - VIEW_HEIGHT, ROOM_HEIGHT]}

THRUST = 1.5
THRUST_MAX = 8
TURN = 1.25
TURN_MAX = 5
TURN_FRICTION = 0.5

SHOOT_WAIT = 15
BULLET_SPEED = 20
BULLET_LIFE = 15

DANGER_DISTANCE = BULLET_SPEED * BULLET_LIFE * 1.25
DANGER_ANGLE = 15

MENU_MAIN = 0
MENU_START = 6
MENU_CONTROLS = 1
MENU_KEYS_PLAYER1 = 2
MENU_KEYS_PLAYER2 = 3
MENU_JS_PLAYER1 = 4
MENU_JS_PLAYER2 = 5
MENU_ITEMS = {MENU_MAIN: ["1-player", "2-player", "Controls", "Quit"],
              MENU_START: ["1 point", "2 points", "3 points", "4 points",
                           "5 points", "6 points", "7 points", "8 points",
                           "Back"],
              MENU_CONTROLS: ["Player 1 (keyboard)", "Player 1 (joystick)",
                              "Player 2 (keyboard)", "Player 2 (joystick)",
                              "Back"],
              MENU_KEYS_PLAYER1: ["Thrust", "Left", "Right", "Shoot", "Back"],
              MENU_KEYS_PLAYER2: ["Thrust", "Left", "Right", "Shoot", "Back"],
              MENU_JS_PLAYER1: ["Thrust", "Left", "Right", "Shoot", "Back"],
              MENU_JS_PLAYER2: ["Thrust", "Left", "Right", "Shoot", "Back"],}
MENU_BORDER = 32
MENU_SPACING = 16

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".pacewar")

colorblind = False
points_to_win = 3

ships_lists = {TEAM_RED: [], TEAM_GREEN: []}
bullets_lists = {TEAM_RED: [], TEAM_GREEN: []}

player1_key_thrust = "up"
player1_key_left = "left"
player1_key_right = "right"
player1_key_shoot = "space"
player2_key_thrust = "w"
player2_key_left = "a"
player2_key_right = "d"
player2_key_shoot = "shift_left"
player1_js_thrust = (0, "button", 0)
player1_js_left = (0, "axis-", 0)
player1_js_right = (0, "axis+", 0)
player1_js_shoot = (0, "button", 1)
player2_js_thrust = (1, "button", 0)
player2_js_left = (1, "axis-", 0)
player2_js_right = (1, "axis+", 0)
player2_js_shoot = (1, "button", 1)


class Game(sge.Game):

    def event_step(self, time_passed, delta_mult):
        x = self.width / 2 - meter_sprite.width / 2
        y = 64
        self.project_sprite(meter_sprite, 0, x, y)

    def event_key_press(self, key, char):
        global colorblind

        if key == "f7":
            colorblind = not colorblind
            self.current_room.update_meter()
        elif key == "f8":
            fname = "screenshot-{}.bmp".format(round(time.time(), 3))
            sge.Sprite.from_screenshot().save(fname)
        elif key == "f11":
            if self.fullscreen:
                self.scale = SCALE
                self.fullscreen = False
                self.scale = None
            else:
                self.fullscreen = True

    def event_mouse_button_press(self, button):
        if button == "middle":
            self.event_close()

    def event_close(self):
        self.end()

    def event_paused_close(self):
        self.event_close()


class Room(sge.Room):

    def event_room_start(self):
        self.score = 0
        self.round_counter = 0
        self.started = False
        self.finished = False
        self.multiplayer = False
        self.menu = MENU_MAIN
        self.menu_selection = 0
        self.menu_sprite = None
        self.menu_axes = {}
        self.round_end()
        self.alarms["check_win"] = 5
        self.update_meter()

    def event_step(self, time_passed, delta_mult):
        if not self.started:
            sge.game.project_sprite(logo_sprite, 0, sge.game.width / 2, 96)

            if self.menu == MENU_KEYS_PLAYER1:
                menu_items = ["Thrust:  {}".format(player1_key_thrust),
                              "Left:    {}".format(player1_key_left),
                              "Right:   {}".format(player1_key_right),
                              "Shoot:   {}".format(player1_key_shoot),
                              "Back"]
            elif self.menu == MENU_KEYS_PLAYER2:
                menu_items = ["Thrust:  {}".format(player2_key_thrust),
                              "Left:    {}".format(player2_key_left),
                              "Right:   {}".format(player2_key_right),
                              "Shoot:   {}".format(player2_key_shoot),
                              "Back"]
            elif self.menu == MENU_JS_PLAYER1:
                thrust = "None"
                left = "None"
                right = "None"
                shoot = "None"
                if player1_js_thrust:
                    thrust = "Joystick {} {} {}".format(*player1_js_thrust)
                if player1_js_left:
                    left = "Joystick {} {} {}".format(*player1_js_left)
                if player1_js_right:
                    right = "Joystick {} {} {}".format(*player1_js_right)
                if player1_js_shoot:
                    shoot = "Joystick {} {} {}".format(*player1_js_shoot)

                menu_items = ["Thrust:  {}".format(thrust),
                              "Left:    {}".format(left),
                              "Right:   {}".format(right),
                              "Shoot:   {}".format(shoot),
                              "Back"]
            elif self.menu == MENU_JS_PLAYER2:
                thrust = "None"
                left = "None"
                right = "None"
                shoot = "None"
                if player2_js_thrust:
                    thrust = "Joystick {} {} {}".format(*player2_js_thrust)
                if player2_js_left:
                    left = "Joystick {} {} {}".format(*player2_js_left)
                if player2_js_right:
                    right = "Joystick {} {} {}".format(*player2_js_right)
                if player2_js_shoot:
                    shoot = "Joystick {} {} {}".format(*player2_js_shoot)

                menu_items = ["Thrust:  {}".format(thrust),
                              "Left:    {}".format(left),
                              "Right:   {}".format(right),
                              "Shoot:   {}".format(shoot),
                              "Back"]
            else:
                menu_items = MENU_ITEMS[self.menu]

            line_w = max([menu_font.get_width(x) for x in menu_items])
            line_h = max([menu_font.get_height(x) for x in menu_items])
            menu_w = line_w + MENU_BORDER * 2
            menu_h = (line_h * len(menu_items) + MENU_BORDER * 2 +
                      MENU_SPACING * (len(menu_items) - 1))

            if (self.menu_sprite is None or
                    (self.menu_sprite.width != menu_w or
                     self.menu_sprite.height != menu_h)):
                self.menu_sprite = sge.Sprite(width=menu_w, height=menu_h)

            self.menu_sprite.draw_lock()
            self.menu_sprite.draw_clear()

            for i in range(len(menu_items)):
                font = (selection_font if self.menu_selection == i else
                        menu_font)
                x = MENU_BORDER
                y = MENU_BORDER + (line_h + MENU_SPACING) * i
                self.menu_sprite.draw_text(font, menu_items[i], x, y,
                                           color=sge.Color("white"))

            self.menu_sprite.draw_unlock()
            sge.game.project_sprite(self.menu_sprite, 0,
                                    sge.game.width / 2 - menu_w / 2, 240)
        elif self.finished:
            if not music.playing:
                create_room().start()

    def event_alarm(self, alarm_id):
        if alarm_id == "check_win":
            red_alive = bool(ships_lists[TEAM_RED])
            green_alive = bool(ships_lists[TEAM_GREEN])

            if red_alive and green_alive:
                self.alarms["check_win"] = 5
            elif green_alive and not red_alive:
                self.score += 1
                self.update_meter()
                self.round_end()
            elif red_alive and not green_alive:
                self.score -= 1
                self.update_meter()
                self.round_end()
            else:
                self.round_end()
        elif alarm_id == "round_end":
            self.round_start()

    def event_key_press(self, key, char):
        global player1_key_thrust
        global player1_key_left
        global player1_key_right
        global player1_key_shoot
        global player2_key_thrust
        global player2_key_left
        global player2_key_right
        global player2_key_shoot
        global player1_js_thrust
        global player1_js_left
        global player1_js_right
        global player1_js_shoot
        global player2_js_thrust
        global player2_js_left
        global player2_js_right
        global player2_js_shoot
        global points_to_win

        if self.finished:
            if key == "enter":
                create_room().start()
        elif not self.started:
            if key == "up":
                self.menu_selection -= 1
                self.menu_selection %= len(MENU_ITEMS[self.menu])
                select_sound.play()
            elif key == "down":
                self.menu_selection += 1
                self.menu_selection %= len(MENU_ITEMS[self.menu])
                select_sound.play()
            elif key == "enter":
                if self.menu == MENU_MAIN:
                    if self.menu_selection == 0:
                        self.menu = MENU_START
                        self.menu_selection = points_to_win - 1
                    elif self.menu_selection == 1:
                        self.multiplayer = True
                        self.menu = MENU_START
                        self.menu_selection = points_to_win - 1
                    elif self.menu_selection == 2:
                        self.menu = MENU_CONTROLS
                        self.menu_selection = 0
                    elif self.menu_selection == 3:
                        sge.game.end()
                elif self.menu == MENU_START:
                    if self.menu_selection < 8:
                        points_to_win = self.menu_selection + 1
                        self.update_meter()
                        self.round_start()
                    else:
                        self.menu = MENU_MAIN
                        self.menu_selection = 1 if self.multiplayer else 0
                elif self.menu == MENU_CONTROLS:
                    self.menu = [MENU_KEYS_PLAYER1, MENU_JS_PLAYER1,
                                 MENU_KEYS_PLAYER2, MENU_JS_PLAYER2,
                                 MENU_MAIN][self.menu_selection]
                    self.menu_selection = 0
                elif self.menu == MENU_KEYS_PLAYER1:
                    if self.menu_selection == 0:
                        k = self.wait_key()
                        if k is not None:
                            player1_key_thrust = k
                    elif self.menu_selection == 1:
                        k = self.wait_key()
                        if k is not None:
                            player1_key_left = k
                    elif self.menu_selection == 2:
                        k = self.wait_key()
                        if k is not None:
                            player1_key_right = k
                    elif self.menu_selection == 3:
                        k = self.wait_key()
                        if k is not None:
                            player1_key_shoot = k
                    elif self.menu_selection == 4:
                        self.menu = MENU_CONTROLS
                        self.menu_selection = 0
                elif self.menu == MENU_KEYS_PLAYER2:
                    if self.menu_selection == 0:
                        k = self.wait_key()
                        if k is not None:
                            player2_key_thrust = k
                    elif self.menu_selection == 1:
                        k = self.wait_key()
                        if k is not None:
                            player2_key_left = k
                    elif self.menu_selection == 2:
                        k = self.wait_key()
                        if k is not None:
                            player2_key_right = k
                    elif self.menu_selection == 3:
                        k = self.wait_key()
                        if k is not None:
                            player2_key_shoot = k
                    elif self.menu_selection == 4:
                        self.menu = MENU_CONTROLS
                        self.menu_selection = 2
                elif self.menu == MENU_JS_PLAYER1:
                    if self.menu_selection == 0:
                        js = self.wait_js()
                        if js is not None:
                            player1_js_thrust = js
                    elif self.menu_selection == 1:
                        js = self.wait_js()
                        if js is not None:
                            player1_js_left = js
                    elif self.menu_selection == 2:
                        js = self.wait_js()
                        if js is not None:
                            player1_js_right = js
                    elif self.menu_selection == 3:
                        js = self.wait_js()
                        if js is not None:
                            player1_js_shoot = js
                    elif self.menu_selection == 4:
                        self.menu = MENU_CONTROLS
                        self.menu_selection = 1
                elif self.menu == MENU_JS_PLAYER2:
                    if self.menu_selection == 0:
                        js = self.wait_js()
                        if js is not None:
                            player2_js_thrust = js
                    elif self.menu_selection == 1:
                        js = self.wait_js()
                        if js is not None:
                            player2_js_left = js
                    elif self.menu_selection == 2:
                        js = self.wait_js()
                        if js is not None:
                            player2_js_right = js
                    elif self.menu_selection == 3:
                        js = self.wait_js()
                        if js is not None:
                            player2_js_shoot = js
                    elif self.menu_selection == 4:
                        self.menu = MENU_CONTROLS
                        self.menu_selection = 3
            elif key == "escape":
                if self.menu == MENU_MAIN:
                    sge.game.event_close()
                elif self.menu == MENU_START:
                    self.menu = MENU_MAIN
                    self.menu_selection = 1 if self.multiplayer else 0
                elif self.menu == MENU_CONTROLS:
                    self.menu = MENU_MAIN
                    self.menu_selection = 0
                elif self.menu == MENU_KEYS_PLAYER1:
                    self.menu = MENU_CONTROLS
                    self.menu_selection = 0
                elif self.menu == MENU_KEYS_PLAYER2:
                    self.menu = MENU_CONTROLS
                    self.menu_selection = 2
                elif self.menu == MENU_JS_PLAYER1:
                    self.menu = MENU_CONTROLS
                    self.menu_selection = 1
                elif self.menu == MENU_JS_PLAYER2:
                    self.menu = MENU_CONTROLS
                    self.menu_selection = 3
        else:
            if key == "escape":
                sge.Music.stop(fade_time=500)
                create_room().start("dissolve", 500)
            elif key == "enter":
                sge.Music.pause()
                select_sound.play()
                sge.game.pause()

    def event_joystick_axis_move(self, js_name, js_id, axis, value):
        if not self.started:
            if axis == 1:
                prev = self.menu_axes.get((js_id, axis), 0)
                self.menu_axes[(js_id, axis)] = value

                if prev <= JOYSTICK_THRESHOLD and value > JOYSTICK_THRESHOLD:
                    self.event_key_press("down", "")
                elif (prev >= -JOYSTICK_THRESHOLD and
                      value < -JOYSTICK_THRESHOLD):
                    self.event_key_press("up", "")

    def event_joystick_hat_move(self, js_name, js_id, hat, x, y):
        if not self.started:
            if x == 0:
                if y == 1:
                    self.event_key_press("down", "")
                elif y == -1:
                    self.event_key_press("up", "")

    def event_joystick_button_press(self, js_name, js_id, button):
        if not self.started:
            self.event_key_press("enter", "\n")

    def event_paused_key_press(self, key, char):
        if key == "enter":
            sge.Music.unpause()
            select_sound.play()
            sge.game.unpause()
        elif key == "escape":
            sge.Music.stop()
            create_room().start()

    def update_meter(self):
        global meter_sprite

        meter_w = (meter_left_sprite.width + meter_right_sprite.width +
                   meter_center_sprite.width +
                   meter_back_sprite.width * points_to_win * 2)
        if meter_sprite.width != meter_w:
            meter_sprite = sge.Sprite(width=meter_w, height=16)

        w = meter_back_sprite.width
        h = meter_back_sprite.height

        green_meter = sge.Sprite(width=(w * points_to_win), height=h)
        red_meter = sge.Sprite(width=green_meter.width, height=h)

        green_meter.draw_lock()
        red_meter.draw_lock()

        for i in range(points_to_win):
            green_meter.draw_sprite(meter_back_sprite, 0, w * i, 0)
            red_meter.draw_sprite(meter_back_sprite, 0, w * i, 0)

        if self.score > 0:
            for i in range(self.score):
                x = w * i
                green_meter.draw_sprite(meter_sprites[TEAM_GREEN], 0, x, 0)
                if colorblind:
                    green_meter.draw_sprite(colorblind_sprites[TEAM_GREEN], 0,
                                            x + w / 2 - 8, 0)
        elif self.score < 0:
            for i in range(abs(self.score)):
                x = red_meter.width - w * i
                red_meter.draw_sprite(meter_sprites[TEAM_RED], 0, x, 0)
                if colorblind:
                    red_meter.draw_sprite(colorblind_sprites[TEAM_RED], 0,
                                          x - w / 2 - 8, 0)

        green_meter.draw_unlock()
        red_meter.draw_unlock()

        x = 0
        meter_sprite.draw_lock()
        meter_sprite.draw_clear()
        for sprite in [meter_left_sprite, red_meter, meter_center_sprite,
                       green_meter, meter_right_sprite]:
            meter_sprite.draw_sprite(sprite, 0, x, 0)
            x += sprite.width
        meter_sprite.draw_unlock()

    def round_start(self):
        global player1
        global player2
        player1 = None
        player2 = None

        for ship in ships_lists[TEAM_RED] + ships_lists[TEAM_GREEN]:
            ship.destroy()
        for bullet in bullets_lists[TEAM_RED] + bullets_lists[TEAM_GREEN]:
            bullet.destroy()

        if not music.playing:
            music.play(loops=None)

        round_limit = points_to_win * 3 // 2
        if abs(self.round_counter) >= round_limit:
            penalty = int((self.round_counter -
                           math.copysign(round_limit, self.round_counter)) /
                          ROUND_TICK)
        else:
            penalty = 0

        for i in range(max(1, TEAM_SIZE - max(self.score, 0, penalty))):
            Ship.create(TEAM_GREEN)
        for i in range(max(1, TEAM_SIZE + min(self.score, 0, penalty))):
            Ship.create(TEAM_RED)

        if self.multiplayer:
            self.views = [sge.View(0, 0, width=(VIEW_WIDTH / 2),
                                   height=VIEW_HEIGHT),
                          sge.View(ROOM_WIDTH, ROOM_HEIGHT,
                                   xport=(VIEW_WIDTH / 2),
                                   width=(VIEW_WIDTH / 2), height=VIEW_HEIGHT)]

            p1ship = random.choice(ships_lists[TEAM_GREEN])
            player1 = Human.create(p1ship, 1,
                                   key_thrust=player1_key_thrust,
                                   key_left=player1_key_left,
                                   key_right=player1_key_right,
                                   key_shoot=player1_key_shoot,
                                   js_thrust=player1_js_thrust,
                                   js_left=player1_js_left,
                                   js_right=player1_js_right,
                                   js_shoot=player1_js_shoot)
            p1ship.controller.destroy()
            p1ship.controller = player1

            p2ship = random.choice(ships_lists[TEAM_RED])
            player2 = Human.create(p2ship, 0,
                                   key_thrust=player2_key_thrust,
                                   key_left=player2_key_left,
                                   key_right=player2_key_right,
                                   key_shoot=player2_key_shoot,
                                   js_thrust=player2_js_thrust,
                                   js_left=player2_js_left,
                                   js_right=player2_js_right,
                                   js_shoot=player2_js_shoot)
            p2ship.controller.destroy()
            p2ship.controller = player2
        else:
            self.views = [sge.View(ROOM_WIDTH, ROOM_HEIGHT,
                                   width=VIEW_WIDTH, height=VIEW_HEIGHT)]

            p1ship = random.choice(ships_lists[TEAM_GREEN])
            player1 = Human.create(p1ship, 0,
                                   key_thrust=player1_key_thrust,
                                   key_left=player1_key_left,
                                   key_right=player1_key_right,
                                   key_shoot=player1_key_shoot,
                                   js_thrust=player1_js_thrust,
                                   js_left=player1_js_left,
                                   js_right=player1_js_right,
                                   js_shoot=player1_js_shoot)
            p1ship.controller.destroy()
            p1ship.controller = player1

        self.started = True
        self.alarms["check_win"] = 5

    def round_end(self):
        if self.started:
            if self.score > 0:
                self.round_counter -= 1
            elif self.score < 0:
                self.round_counter += 1

            if abs(self.score) < points_to_win:
                self.alarms["round_end"] = 90
            else:
                self.finished = True
                sge.Music.stop(fade_time=5000)
        else:
            if self.score:
                loser = TEAM_RED if self.score > 0 else TEAM_GREEN
                self.score = 0
                self.update_meter()
                for i in range(TEAM_SIZE // 2):
                    Ship.create(loser)
            else:
                for i in range(TEAM_SIZE // 2):
                    Ship.create(TEAM_RED)
                    Ship.create(TEAM_GREEN)

            self.alarms["check_win"] = 5

    def wait_key(self):
        # Wait for a key press and return it.
        key = None
        while key is None:
            # Input events
            sge.game.pump_input()
            while sge.game.input_events:
                event = sge.game.input_events.pop(0)
                if isinstance(event, sge.input.KeyPress):
                    sge.game.pump_input()
                    sge.game.input_events = []
                    if event.key == "escape":
                        return None
                    else:
                        return event.key

            # Regulate speed
            sge.game.regulate_speed(fps=10)

            # Project text
            text = "Press the key you wish to use for this function, or Escape to cancel."
            sge.game.project_text(menu_font, text, sge.game.width / 2,
                                  sge.game.height / 2, width=sge.game.width,
                                  height=sge.game.height,
                                  color=sge.Color("white"),
                                  halign="center", valign="middle")

            # Refresh
            sge.game.refresh()

        sge.game.pump_input()
        sge.game.input_events = []
        return key

    def wait_js(self):
        # Wait for a joystick press and return it.
        while True:
            # Input events
            sge.game.pump_input()
            while sge.game.input_events:
                event = sge.game.input_events.pop(0)
                if isinstance(event, sge.input.KeyPress):
                    if event.key == "escape":
                        sge.game.pump_input()
                        sge.game.input_events = []
                        return None
                elif isinstance(event, sge.input.JoystickAxisMove):
                    if event.value > JOYSTICK_THRESHOLD:
                        sge.game.pump_input()
                        sge.game.input_events = []
                        return (event.js_id, "axis+", event.axis)
                    elif event.value < -JOYSTICK_THRESHOLD:
                        sge.game.pump_input()
                        sge.game.input_events = []
                        return (event.js_id, "axis-", event.axis)
                elif isinstance(event, sge.input.JoystickHatMove):
                    sge.game.pump_input()
                    sge.game.input_events = []
                    t = ("hatx+" if event.x > 0 else
                         "hatx-" if event.x < 0 else
                         "haty+" if event.y > 0 else
                         "haty-" if event.y < 0 else
                         "hatx0")
                    return (event.js_id, t, event.hat)
                elif isinstance(event, sge.input.JoystickButtonPress):
                    sge.game.pump_input()
                    sge.game.input_events = []
                    return (event.js_id, "button", event.button)

            # Regulate speed
            sge.game.regulate_speed(fps=10)

            # Project text
            text = "Press the joystick button, axis, or hat direction you wish to use for this function, or Escape to cancel."
            sge.game.project_text(menu_font, text, sge.game.width / 2,
                                  sge.game.height / 2, width=sge.game.width,
                                  height=sge.game.height,
                                  color=sge.Color("white"),
                                  halign="center", valign="middle")

            # Refresh
            sge.game.refresh()


class Ship(sge.Object):

    def __init__(self, team):
        super(Ship, self).__init__(random.randrange(*START_X_RANGE[team]),
                                   random.randrange(*START_Y_RANGE[team]),
                                   sprite=random.choice(ship_sprites[team]),
                                   checks_collisions=False,
                                   regulate_origin=True,
                                   collision_precise=True, image_xscale=0.2,
                                   image_yscale=0.2,
                                   image_rotation=random.randrange(360))
        self.team = team

    def event_create(self):
        global ships_lists
        self.controller = AI.create(self)
        self.thrust = False
        self.left = False
        self.right = False
        self.shoot = False
        self.can_shoot = True
        self.rvelocity = 0
        self.thrust_obj = None
        ships_lists[self.team].append(self)

    def event_update_position(self, delta_mult):
        if delta_mult:
            vi = self.rvelocity
            a = (self.left - self.right) * TURN
            self.rvelocity += a * delta_mult
            dc = -math.copysign(TURN_FRICTION * delta_mult, self.rvelocity)
            if abs(self.rvelocity) > abs(dc):
                a -= math.copysign(TURN_FRICTION, self.rvelocity)
                self.rvelocity += dc
            else:
                a -= self.rvelocity / delta_mult
                self.rvelocity = 0

            self.image_rotation += vi * delta_mult + 0.5 * a * (delta_mult ** 2)
            super(Ship, self).event_update_position(delta_mult)

    def event_step(self, time_passed, delta_mult):
        # Shoot
        if self.shoot:
            self.do_shoot()

        # Acceleration
        if self.thrust:
            direction = math.radians(self.image_rotation + 90)
            self.xacceleration = math.cos(direction) * THRUST
            self.yacceleration = -math.sin(direction) * THRUST
        else:
            self.xacceleration = 0
            self.yacceleration = 0

        self.speed = min(self.speed, THRUST_MAX)
        if abs(self.rvelocity) > TURN_MAX:
            self.rvelocity = math.copysign(TURN_MAX, self.rvelocity)

        # Bounce off edges
        if self.bbox_left < 0:
            self.bbox_left *= -1
            self.xvelocity = abs(self.xvelocity)
        elif self.bbox_right > ROOM_WIDTH:
            self.bbox_right = ROOM_WIDTH - (self.bbox_right - ROOM_WIDTH)
            self.xvelocity = -abs(self.xvelocity)
        if self.bbox_top < 0:
            self.bbox_top *= -1
            self.yvelocity = abs(self.yvelocity)
        elif self.bbox_bottom > ROOM_HEIGHT:
            self.bbox_bottom = ROOM_HEIGHT - (self.bbox_bottom - ROOM_HEIGHT)
            self.yvelocity = -abs(self.yvelocity)

        # Colorblind mode
        if colorblind:
            sprite = colorblind_sprites[self.team]
            sge.game.current_room.project_sprite(sprite, 0, self.x - 8,
                                                 self.y - 8, self.z + 1)

        # Display exhaust
        if self.thrust:
            if self.thrust_obj is None:
                self.thrust_obj = sge.Object.create(
                    self.x, self.y, -1,
                    sprite=exhaust_sprites[id(self.sprite)], tangible=False,
                    regulate_origin=True, image_xscale=self.image_xscale,
                    image_yscale=self.image_yscale,
                    image_rotation=self.image_rotation)
            else:
                self.thrust_obj.x = self.x
                self.thrust_obj.y = self.y
                self.thrust_obj.image_rotation = self.image_rotation
        else:
            if self.thrust_obj is not None:
                self.thrust_obj.destroy()
                self.thrust_obj = None

    def event_alarm(self, alarm_id):
        if alarm_id == "shoot":
            self.can_shoot = True

    def event_collision(self, other, xdirection, ydirection):
        if isinstance(other, Bullet) and other.team != self.team:
            self.destroy()
            Explosion.create(self.x, self.y, self.z, sprite=explosion_sprite,
                             regulate_origin=True, image_xscale=0.5,
                             image_yscale=0.5)

            in_range = False
            for view in sge.game.current_room.views:
                if (self.bbox_right >= view.x and
                        self.bbox_left <= view.x + view.width and
                        self.bbox_bottom >= view.y and
                        self.bbox_top <= view.y + view.height):
                    in_range = True
                    break

            if in_range:
                explode_sound.play()
            else:
                explode_sound.play(volume=50)

    def event_destroy(self):
        global ships_lists
        while self in ships_lists[self.team]:
            ships_lists[self.team].remove(self)

        if self.controller is not None:
            self.controller.destroy()
            self.controller = None

        if self.thrust_obj is not None:
            self.thrust_obj.destroy()
            self.thrust_obj = None

    def do_shoot(self):
        if self.can_shoot:
            bullet = Bullet.create(self.team, self.x, self.y, -5,
                                   sprite=bullet_sprites[self.team],
                                   collision_precise=True,
                                   image_rotation=self.image_rotation)
            bullet.speed = BULLET_SPEED
            bullet.move_direction = bullet.image_rotation + 90
            bullet.xvelocity += self.xvelocity
            bullet.yvelocity += self.yvelocity
            self.can_shoot = False
            self.alarms["shoot"] = SHOOT_WAIT

            in_range = False
            for view in sge.game.current_room.views:
                if (self.bbox_right >= view.x and
                        self.bbox_left <= view.x + view.width and
                        self.bbox_bottom >= view.y and
                        self.bbox_top <= view.y + view.height):
                    in_range = True
                    break

            if in_range:
                shoot_sound.play()
            else:
                shoot_sound.play(volume=50)


class Explosion(sge.Object):

    def event_animation_end(self):
        self.destroy()


class Bullet(sge.Object):

    def __init__(self, team, *args, **kwargs):
        super(Bullet, self).__init__(*args, **kwargs)
        self.team = team

    def event_create(self):
        global bullets_lists
        bullets_lists[self.team].append(self)
        self.alarms["death"] = BULLET_LIFE

    def event_destroy(self):
        global bullets_list
        while self in bullets_lists[self.team]:
            bullets_lists[self.team].remove(self)

    def event_alarm(self, alarm_id):
        if alarm_id == "death":
            self.destroy()

    def event_collision(self, other, xdirection, ydirection):
        if isinstance(other, Ship) and other.team != self.team:
            self.destroy()
        elif isinstance(other, Bullet):
            self.destroy()

            in_range = False
            for view in sge.game.current_room.views:
                if (self.bbox_right >= view.x and
                        self.bbox_left <= view.x + view.width and
                        self.bbox_bottom >= view.y and
                        self.bbox_top <= view.y + view.height):
                    in_range = True
                    break

            if in_range:
                dissipate_sound.play()


class Controller(sge.Object):

    def __init__(self, parent):
        super(Controller, self).__init__(0, 0, visible=False, tangible=False)
        self.parent = parent
        self.team = parent.team

    def event_destroy(self):
        self.parent = None


class Human(Controller):

    def __init__(self, parent, view, key_thrust="up", key_left="left",
                 key_right="right", key_shoot="space", js_thrust=None,
                 js_left=None, js_right=None, js_shoot=None):
        sge.Object.__init__(self, parent.x, parent.y, sprite=target_sprite,
                            tangible=False)
        self.parent = parent
        self.team = parent.team
        self.view = view
        self.key_thrust = key_thrust
        self.key_left = key_left
        self.key_right = key_right
        self.key_shoot = key_shoot
        self.js_thrust = js_thrust
        self.js_left = js_left
        self.js_right = js_right
        self.js_shoot = js_shoot

        # Set current key state
        self.parent.thrust = sge.keyboard.get_pressed(key_thrust)
        self.parent.left = sge.keyboard.get_pressed(key_left)
        self.parent.right = sge.keyboard.get_pressed(key_right)
        self.parent.shoot = sge.keyboard.get_pressed(key_shoot)

        # Add current joystick state
        js_controls = [js_thrust, js_left, js_right, js_shoot]
        js_states = [False, False, False, False]
        for i in range(len(js_controls)):
            if js_controls[i] is not None:
                j = js_controls[i][0]
                t = js_controls[i][1]
                c = js_controls[i][2]
                if t == "axis+":
                    js_states[i] = (sge.joystick.get_axis(j, c) >
                                    JOYSTICK_THRESHOLD)
                elif t == "axis-":
                    js_states[i] = (sge.joystick.get_axis(j, c) <
                                    -JOYSTICK_THRESHOLD)
                elif t == "axis0":
                    js_states[i] = (abs(sge.joystick.get_axis(j, c)) <=
                                    JOYSTICK_THRESHOLD)
                elif t == "hat":
                    js_states[i] = (sge.joystick.get_hat_x(j, c[0]) == c[1] and
                                    sge.joystick.get_hat_y(j, c[0]) == c[2])
                elif t == "button":
                    js_states[i] = sge.joystick.get_pressed(j, c)

        self.parent.thrust = self.parent.thrust or js_states[0]
        self.parent.left = self.parent.left or js_states[1]
        self.parent.right = self.parent.right or js_states[2]
        self.parent.shoot = self.parent.shoot or js_states[3]

    def event_end_step(self, time_passed, delta_mult):
        if (self.parent is not None and
                self.parent in sge.game.current_room.objects):
            self.x = self.parent.x
            self.y = self.parent.y
            view = sge.game.current_room.views[self.view]
            view.x = self.parent.x - view.width / 2
            view.y = self.parent.y - view.height / 2
        else:
            print("Warning: Ship is dead but controller (a human) is not!")
            self.destroy()

    def event_key_press(self, key, char):
        if (self.parent is not None and
                self.parent in sge.game.current_room.objects):
            if key == self.key_thrust:
                self.parent.thrust = True
            if key == self.key_left:
                self.parent.left = True
            if key == self.key_right:
                self.parent.right = True
            if key == self.key_shoot:
                self.parent.shoot = True
                self.parent.do_shoot()

    def event_key_release(self, key):
        if (self.parent is not None and
                self.parent in sge.game.current_room.objects):
            if key == self.key_thrust:
                self.parent.thrust = False
            if key == self.key_left:
                self.parent.left = False
            if key == self.key_right:
                self.parent.right = False
            if key == self.key_shoot:
                self.parent.shoot = False

    def event_joystick_axis_move(self, js_name, js_id, axis, value):
        if (self.parent is not None and
                self.parent in sge.game.current_room.objects):
            js_versions = [(js_id, "axis+", axis), (js_id, "axis-", axis)]
            if value > JOYSTICK_THRESHOLD:
                js = (js_id, "axis+", axis)
            elif value < -JOYSTICK_THRESHOLD:
                js = (js_id, "axis-", axis)
            else:
                js = (js_id, "axis0", axis)

            if js == self.js_thrust:
                self.parent.thrust = True
            elif self.js_thrust in js_versions:
                self.parent.thrust = False
            if js == self.js_left:
                self.parent.left = True
            elif self.js_left in js_versions:
                self.parent.left = False
            if js == self.js_right:
                self.parent.right = True
            elif self.js_right in js_versions:
                self.parent.right = False
            if js == self.js_shoot:
                self.parent.shoot = True
                self.parent.do_shoot()
            elif self.js_shoot in js_versions:
                self.parent.shoot = False

    def event_joystick_hat_move(self, js_name, js_id, hat, x, y):
        if (self.parent is not None and
                self.parent in sge.game.current_room.objects):
            js_versions = [(js_id, "hatx+", hat), (js_id, "hatx-", hat)]
            if x > 0:
                js = (js_id, "hatx+", hat)
            elif x < 0:
                js = (js_id, "hatx-", hat)
            else:
                js = (js_id, "hatx0", hat)

            if js == self.js_thrust:
                self.parent.thrust = True
            elif self.js_thrust in js_versions:
                self.parent.thrust = False
            if js == self.js_left:
                self.parent.left = True
            elif self.js_left in js_versions:
                self.parent.left = False
            if js == self.js_right:
                self.parent.right = True
            elif self.js_right in js_versions:
                self.parent.right = False
            if js == self.js_shoot:
                self.parent.shoot = True
                self.parent.do_shoot()
            elif self.js_shoot in js_versions:
                self.parent.shoot = False

            js_versions = [(js_id, "haty+", hat), (js_id, "haty-", hat)]
            if y > 0:
                js = (js_id, "haty+", hat)
            elif y < 0:
                js = (js_id, "haty-", hat)
            else:
                js = (js_id, "haty0", hat)

            if js == self.js_thrust:
                self.parent.thrust = True
            elif self.js_thrust in js_versions:
                self.parent.thrust = False
            if js == self.js_left:
                self.parent.left = True
            elif self.js_left in js_versions:
                self.parent.left = False
            if js == self.js_right:
                self.parent.right = True
            elif self.js_right in js_versions:
                self.parent.right = False
            if js == self.js_shoot:
                self.parent.shoot = True
                self.parent.do_shoot()
            elif self.js_shoot in js_versions:
                self.parent.shoot = False

    def event_joystick_button_press(self, js_name, js_id, button):
        if (self.parent is not None and
                self.parent in sge.game.current_room.objects):
            js = (js_id, "button", button)

            if js == self.js_thrust:
                self.parent.thrust = True
            if js == self.js_left:
                self.parent.left = True
            if js == self.js_right:
                self.parent.right = True
            if js == self.js_shoot:
                self.parent.shoot = True
                self.parent.do_shoot()

    def event_joystick_button_release(self, js_name, js_id, button):
        if (self.parent is not None and
                self.parent in sge.game.current_room.objects):
            js = (js_id, "button", button)

            if js == self.js_thrust:
                self.parent.thrust = False
            if js == self.js_left:
                self.parent.left = False
            if js == self.js_right:
                self.parent.right = False
            if js == self.js_shoot:
                self.parent.shoot = False

    def event_destroy(self):
        global player1
        global player2

        super(Human, self).event_destroy()

        friends = ships_lists[self.team]
        if friends:
            ship = random.choice(friends)

            if ship.controller is not None:
                ship.controller.destroy()
                ship.controller = None

            if self is player1:
                player1 = Human.create(ship, self.view,
                                       key_thrust=player1_key_thrust,
                                       key_left=player1_key_left,
                                       key_right=player1_key_right,
                                       key_shoot=player1_key_shoot,
                                       js_thrust=player1_js_thrust,
                                       js_left=player1_js_left,
                                       js_right=player1_js_right,
                                       js_shoot=player1_js_shoot)
                ship.controller = player1
            elif self is player2:
                player2 = Human.create(ship, self.view,
                                       key_thrust=player2_key_thrust,
                                       key_left=player2_key_left,
                                       key_right=player2_key_right,
                                       key_shoot=player2_key_shoot,
                                       js_thrust=player2_js_thrust,
                                       js_left=player2_js_left,
                                       js_right=player2_js_right,
                                       js_shoot=player2_js_shoot)
                ship.controller = player2
        else:
            if self is player1:
                player1 = None
            elif self is player2:
                player2 = None


class AI(Controller):

    def event_create(self):
        self.target = None
        self.threats = []
        self.alarms["select_target"] = random.randint(30, 90)
        self.alarms["check_threats"] = 5

    def event_step(self, time_passed, delta_mult):
        if self.parent in sge.game.current_room.objects:
            # Release all buttons
            self.parent.thrust = False
            self.parent.left = False
            self.parent.right = False
            self.parent.shoot = False

            if self.threats:
                # Get to safety
                thrust_ok = True
                left_ok = True
                right_ok = True

                direction = (self.parent.image_rotation + 90) % 360

                if self.parent.x <= DANGER_DISTANCE:
                    if 90 < direction < 180:
                        left_ok = False
                    elif 180 < direction < 270:
                        right_ok = False
                elif self.parent.x >= (sge.game.current_room.width -
                                       DANGER_DISTANCE):
                    if 0 < direction < 90:
                        right_ok = False
                    elif 270 < direction > 360:
                        left_ok = False

                if self.parent.y <= DANGER_DISTANCE:
                    if 0 < direction < 90:
                        left_ok = False
                    elif 90 < direction < 180:
                        right_ok = False
                elif self.parent.y >= (sge.game.current_room.height -
                                       DANGER_DISTANCE):
                    if 180 < direction < 270:
                        left_ok = False
                    elif 270 < direction < 360:
                        right_ok = False

                for threat in self.threats:
                    if thrust_ok or left_ok or right_ok:
                        threat_direction = math.degrees(math.atan2(
                            self.parent.y - threat.y,
                            threat.x - self.parent.x))
                        diff = (threat_direction - direction) % 360
                        if diff <= DANGER_ANGLE or diff >= 360 - DANGER_ANGLE:
                            thrust_ok = False
                            self.parent.do_shoot()
                        elif DANGER_ANGLE < diff <= 2 * DANGER_ANGLE:
                            left_ok = False
                        elif (360 - 2 * DANGER_ANGLE <= diff <
                              360 - DANGER_ANGLE):
                            right_ok = False

                if thrust_ok:
                    self.parent.thrust = True

                if left_ok:
                    self.parent.left = True
                elif right_ok:
                    self.parent.right = True
                else:
                    # Resort to just shooting.
                    self.parent.do_shoot()
            elif self.target is not None:
                if self.target in sge.game.current_room.objects:
                    # Persue target
                    dist = math.hypot(self.target.x - self.parent.x,
                                      self.target.y - self.parent.y)
                    target_angle = math.degrees(
                        math.atan2(self.parent.y - self.target.y,
                                   self.target.x - self.parent.x))
                    diff = (target_angle -
                            (self.parent.image_rotation + 90)) % 360
                    if 2 < diff < 180:
                        self.parent.left = True
                    elif 180 <= diff < 358:
                        self.parent.right = True

                    if diff <= 10 or diff >= 350:
                        if dist > BULLET_SPEED * BULLET_LIFE:
                            self.parent.thrust = True
                        else:
                            self.parent.do_shoot()
                elif self.alarms.get("select_target", 15) > 10:
                    self.alarms["select_target"] = 10

    def event_alarm(self, alarm_id):
        if self.parent in sge.game.current_room.objects:
            et = TEAM_GREEN if self.team == TEAM_RED else TEAM_RED
            if alarm_id == "select_target":
                self.target = None

                for ship in ships_lists[et]:
                    if (self.target is None or
                             (math.hypot(ship.x - self.parent.x,
                                         ship.y - self.parent.y) <
                              math.hypot(self.target.x - self.parent.x,
                                         self.target.y - self.parent.y))):
                        self.target = ship

                self.alarms["select_target"] = random.randint(90, 180)
            elif alarm_id == "check_threats":
                self.threats = []
                potential_threats = ships_lists[et] + bullets_lists[et]
                for pt in potential_threats:
                    dist = math.hypot(pt.x - self.parent.x,
                                      pt.y - self.parent.y)
                    direction = (pt.image_rotation + 90) % 360
                    pt_direction = math.degrees(math.atan2(
                        pt.y - self.parent.y, self.parent.x - pt.x)) % 360
                    diff = abs(pt_direction - direction)
                    if (dist <= DANGER_DISTANCE and
                            diff <= DANGER_ANGLE):
                        self.threats.append(pt)
                self.alarms["check_threats"] = random.randint(5, 10)


def create_nebula(num, z, scroll_rate):
    # Create a nebula background layer and return it.
    sprite = sge.Sprite(width=max(ROOM_WIDTH, ROOM_WIDTH * scroll_rate),
                        height=max(ROOM_HEIGHT, ROOM_HEIGHT * scroll_rate))
    layers = []
    for i in range(num):
        nebula_sprite = random.choice(nebula_sprites)
        x = random.randrange(max(1, int(sprite.width - nebula_sprite.width)))
        y = random.randrange(max(1, int(sprite.height - nebula_sprite.height)))
        sprite.draw_sprite(nebula_sprite, 0, x, y)

    return sge.BackgroundLayer(sprite, 0, 0, z, xscroll_rate=scroll_rate,
                               yscroll_rate=scroll_rate)


def create_room():
    views = [sge.View(ROOM_WIDTH // 2 - VIEW_WIDTH // 2,
                      ROOM_HEIGHT // 2 - VIEW_HEIGHT // 2, width=VIEW_WIDTH,
                      height=VIEW_HEIGHT)]
    return Room(width=ROOM_WIDTH, height=ROOM_HEIGHT, views=views,
                background=background, object_area_width=64,
                object_area_height=64)


# Create Game object
Game(width=1280, height=720, scale=SCALE, scale_smooth=True, fps=30,
     delta=True, delta_min=15, window_text="Pacewar",
     window_icon=os.path.join(DATA_IMAGES, "Spaceship15B.png"))

# Load sprites
r1_sprite = sge.Sprite("Spaceship14", DATA_IMAGES, origin_x=83, origin_y=154,
                       bbox_x=-17, bbox_y=-17, bbox_width=33, bbox_height=33)
g1_sprite = sge.Sprite("Spaceship14B", DATA_IMAGES, origin_x=83, origin_y=154,
                       bbox_x=-17, bbox_y=-17, bbox_width=33, bbox_height=33)
r2_sprite = sge.Sprite("Spaceship15", DATA_IMAGES, origin_x=80, origin_y=91,
                       bbox_x=-16, bbox_y=-16, bbox_width=32, bbox_height=32)
g2_sprite = sge.Sprite("Spaceship15B", DATA_IMAGES, origin_x=80, origin_y=91,
                       bbox_x=-16, bbox_y=-16, bbox_width=32, bbox_height=32)
r3_sprite = sge.Sprite("Spaceship16", DATA_IMAGES, origin_x=69, origin_y=92,
                       bbox_x=-14, bbox_y=-14, bbox_width=28, bbox_height=28)
g3_sprite = sge.Sprite("Spaceship16B", DATA_IMAGES, origin_x=69, origin_y=92,
                       bbox_x=-14, bbox_y=-14, bbox_width=28, bbox_height=28)
e1_sprite = sge.Sprite("Exhaust14", DATA_IMAGES, origin_x=31, origin_y=-65,
                       fps=60)
e2_sprite = sge.Sprite("Exhaust15", DATA_IMAGES, origin_x=35, origin_y=-44,
                       fps=60)
e3_sprite = sge.Sprite("Exhaust16", DATA_IMAGES, origin_x=14, origin_y=-48,
                       fps=60)

ship_sprites = {TEAM_RED: [r1_sprite, r2_sprite, r3_sprite],
                TEAM_GREEN: [g1_sprite, g2_sprite, g3_sprite]}
exhaust_sprites = {id(r1_sprite): e1_sprite, id(g1_sprite): e1_sprite,
                   id(r2_sprite): e2_sprite, id(g2_sprite): e2_sprite,
                   id(r3_sprite): e3_sprite, id(g3_sprite): e3_sprite}

explosion_sprite = sge.Sprite("explosion", DATA_IMAGES, origin_x=64,
                              origin_y=64, fps=30)
bullet_sprites = {TEAM_RED: sge.Sprite("bullet_red", DATA_IMAGES, origin_x=8,
                                       origin_y=16),
                  TEAM_GREEN: sge.Sprite("bullet_green", DATA_IMAGES,
                                         origin_x=8, origin_y=16)}
stars_sprite = sge.Sprite("Stars", DATA_IMAGES)
nebula_sprites = [sge.Sprite("Nebula1", DATA_IMAGES),
                  sge.Sprite("Nebula2", DATA_IMAGES),
                  sge.Sprite("Nebula3", DATA_IMAGES)]
target_sprite = sge.Sprite("target", DATA_IMAGES, width=80, height=80,
                           origin_x=40, origin_y=40)
logo_sprite = sge.Sprite("logo", DATA_IMAGES, origin_x=321)
colorblind_sprites = {TEAM_RED: sge.Sprite("colorblind_red", DATA_IMAGES),
                      TEAM_GREEN: sge.Sprite("colorblind_green", DATA_IMAGES)}
font_sprite = sge.Sprite("font", DATA_IMAGES)
font_selected_sprite = sge.Sprite("font_selected", DATA_IMAGES)
meter_left_sprite = sge.Sprite("meter_left", DATA_IMAGES)
meter_right_sprite = sge.Sprite("meter_right", DATA_IMAGES)
meter_center_sprite = sge.Sprite("meter_center", DATA_IMAGES)
meter_back_sprite = sge.Sprite("meter_back", DATA_IMAGES)
meter_sprites = {TEAM_RED: sge.Sprite("meter_red", DATA_IMAGES, origin_x=37),
                 TEAM_GREEN: sge.Sprite("meter_green", DATA_IMAGES)}
meter_w = (meter_left_sprite.width + meter_right_sprite.width +
           meter_center_sprite.width +
           meter_back_sprite.width * points_to_win * 2)
meter_sprite = sge.Sprite(width=meter_w, height=16)

# Load backgrounds
layers = []
layers.append(sge.BackgroundLayer(stars_sprite, 0, 0, -1000, xscroll_rate=0.05,
                                  yscroll_rate=0.01, repeat_left=True,
                                  repeat_right=True, repeat_up=True,
                                  repeat_down=True))
layers.append(create_nebula(15, -100, 0.1))
layers.append(create_nebula(30, -50, 0.5))
layers.append(create_nebula(5, 5, 1))

background = sge.Background(layers, sge.Color("black"))

# Load sounds
shoot_sound = sge.Sound(os.path.join(DATA_SOUNDS, "shoot.wav"))
explode_sound = sge.Sound(os.path.join(DATA_SOUNDS, "explode.wav"))
dissipate_sound = sge.Sound(os.path.join(DATA_SOUNDS, "dissipate.ogg"))
select_sound = sge.Sound(os.path.join(DATA_SOUNDS, "select.ogg"), volume=50)

# Load music
music = sge.Music(os.path.join(DATA_MUSIC, "DST-RailJet-LongSeamlessLoop.ogg"))

# Load fonts
chars = [' ', '!', '"', '#', '$', '%', '&', "'", '(', ')', '*', '+', ',',
         '-', '.', '/', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
         ':', ';', '<', '=', '>', '?', '@', 'A', 'B', 'C', 'D', 'E', 'F',
         'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S',
         'T', 'U', 'V', 'W', 'X', 'Y', 'Z', '[', '\\', ']', '^', '_', '`',
         'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
         'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
         '{', '|', '}', '~']
menu_font = sge.Font.from_sprite(font_sprite, chars, size=24)
selection_font = sge.Font.from_sprite(font_selected_sprite, chars, size=24)

# Create room
sge.game.start_room = create_room()

sge.game.scale = None
sge.game.mouse.visible = False

if not os.path.exists(CONFIG_DIR):
    os.makedirs(CONFIG_DIR)

try:
    with open(os.path.join(CONFIG_DIR, "keys.json"), 'r') as f:
        keys_cfg = json.load(f)
except (IOError, ValueError):
    pass
else:
    player1_key_thrust = keys_cfg.get("player1_thrust", player1_key_thrust)
    player1_key_left = keys_cfg.get("player1_left", player1_key_left)
    player1_key_right = keys_cfg.get("player1_right", player1_key_right)
    player1_key_shoot = keys_cfg.get("player1_shoot", player1_key_shoot)
    player2_key_thrust = keys_cfg.get("player2_thrust", player2_key_thrust)
    player2_key_left = keys_cfg.get("player2_left", player2_key_left)
    player2_key_right = keys_cfg.get("player2_right", player2_key_right)
    player2_key_shoot = keys_cfg.get("player2_shoot", player2_key_shoot)

try:
    with open(os.path.join(CONFIG_DIR, "joystick.json"), 'r') as f:
        js_cfg = json.load(f)
except (IOError, ValueError):
    pass
else:
    player1_js_thrust = tuple(js_cfg.get("player1_thrust",
                                         player1_js_thrust))
    player1_js_left = tuple(js_cfg.get("player1_left", player1_js_left))
    player1_js_right = tuple(js_cfg.get("player1_right", player1_js_right))
    player1_js_shoot = tuple(js_cfg.get("player1_shoot", player1_js_shoot))
    player2_js_thrust = tuple(js_cfg.get("player2_thrust",
                                         player2_js_thrust))
    player2_js_left = tuple(js_cfg.get("player2_left", player2_js_left))
    player2_js_right = tuple(js_cfg.get("player2_right", player2_js_right))
    player2_js_shoot = tuple(js_cfg.get("player2_shoot", player2_js_shoot))


if __name__ == '__main__':
    try:
        sge.game.start()
    finally:
        keys_cfg = {"player1_thrust": player1_key_thrust,
                    "player1_left": player1_key_left,
                    "player1_right": player1_key_right,
                    "player1_shoot": player1_key_shoot,
                    "player2_thrust": player2_key_thrust,
                    "player2_left": player2_key_left,
                    "player2_right": player2_key_right,
                    "player2_shoot": player2_key_shoot}
        js_cfg = {"player1_thrust": player1_js_thrust,
                  "player1_left": player1_js_left,
                  "player1_right": player1_js_right,
                  "player1_shoot": player1_js_shoot,
                  "player2_thrust": player2_js_thrust,
                  "player2_left": player2_js_left,
                  "player2_right": player2_js_right,
                  "player2_shoot": player2_js_shoot}

        with open(os.path.join(CONFIG_DIR, "keys.json"), 'w') as f:
            json.dump(keys_cfg, f)

        with open(os.path.join(CONFIG_DIR, "joystick.json"), 'w') as f:
            json.dump(js_cfg, f)
