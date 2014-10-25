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

If you have obtained a frozen binary for your system, you can simply run
the executable, which should be called something like "pacewar".

Otherwise, you will need to run the game from source. To do this, you
will need the following dependencies:

- Python 2 (2.7 or later) or 3 (3.1 or later) <http://www.python.org>
- SGE Game Engine 0.13 or later <http://stellarengine.nongnu.org>

Once you have installed the dependencies, you can start Pacewar by
running pacewar.py. By default, it will use Python 3. To run it with
Python 2 instead, you can either change the shebang on line 1 from
"python3" to "python2", or explicitly run the Python 2 executable, e.g.:

    python2 pacewar.py

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
in Pygame 1.9.2a0 which sometimes locks up the keyboard when toggling
fullscreen or changing the window size. See this post on the SGE blog
for more information:

https://savannah.nongnu.org/forum/forum.php?forum_id=8113