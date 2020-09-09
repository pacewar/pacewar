This file has been dedicated to the public domain, to the extent
possible under applicable law, via CC0. See
http://creativecommons.org/publicdomain/zero/1.0/ for more
information. This file is offered as-is, without any warranty.

========================================================================


PACEWAR

This was my entry for PyWeek 19. The theme of this PyWeek competition
was "one room". This game is a "one room" game on a technicality: only
one "room" is used internally. The fighting arena is also boxed in, so
that makes it kind of like a room.

The object of the game is simple: destroy the other team. Each time you
do this, you win the round and the meter at the top slides toward your
side. However, the further the meter is on your side, the more ships the 
other team will get.

If your ship gets destroyed, you are randomly given control of another
one of your team's ships.

HOW TO RUN

If you have downloaded a version of the game designated for a particular
system, simply run the executable.

To run the source code, you will need Python 3.6 or later
<https://www.python.org>. You will also need the dependencies listed in
requirements.txt, which you can install automatically by using the
following command:

    python3 -m pip install -r requirements.txt

Once you have installed the dependencies, you can start the game by
running pacewar.py. On most systems, this should be done by
double-clicking on it; if you are shown a dialog asking you if you want
to display or run the file, choose to run it.

HOW TO PLAY

Use the arrow keys and Enter to navigate the menu. By default, player 1
is controlled by the arrow keys and Space, and player 2 is controlled by
WASD and left Shift. You can configure the controls in the Controls
menu.

Other controls:
- Enter: Pause the game.
- F7: Toggle colorblind mode.
- F8: Take a screenshot.
- F11: Toggle fullscreen.
- Escape: Quit the game.
- Middle mouse button: Quit the game.

The middle mouse button quitting the game is meant to work around a bug
in SDL 1.2 (an indirect dependency) which sometimes locks up the
keyboard when toggling fullscreen or changing the window size.
