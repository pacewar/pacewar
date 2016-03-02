Copyright (C) 2014-2016 onpon4 <onpon4@riseup.net>

Copying and distribution of this file, with or without modification,
are permitted in any medium without royalty provided the copyright
notice and this notice are preserved.  This file is offered as-is,
without any warranty.

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

To run Pacewar, you will need the following dependencies:

- Python 2 (2.7 or later) or 3 (3.1 or later) <http://www.python.org>
- Pygame 1.9.1 or later <http://pygame.org/download.shtml>

If you have downloaded a version of Pacewar designated for a particular
system, these dependencies can be found under the "deps" folder.  Please
see any "README" files in that folder for instructions and tips.

Once you have installed the dependencies, you can start Pacewar by
running pacewar.py. On most systems, this should be done by
double-clicking on it; if you are shown a dialog asking you if you want
to display or run the file, choose to run it.

Python 2 will be used by default. To run Pacewar with Python 3 instead,
you can either change the shebang on line 1 from "python2" to "python3",
or explicitly run the Python 3 executable, e.g. with
"python3 pacewar.py" (the exact command may be different depending on
your system).

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
in Pygame which sometimes locks up the keyboard when toggling fullscreen
or changing the window size. See this post on the SGE blog for more
information:

https://savannah.nongnu.org/forum/forum.php?forum_id=8113
