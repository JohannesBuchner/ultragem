GemGem - A Bejeweled/CandyCrush clone
====================================

Original description:
http://inventwithpython.com/blog/2011/06/24/new-game-source-code-gemgem-a-bejeweled-clone/

    .. image:: https://raw.githubusercontent.com/JohannesBuchner/gemgem/master/screenshot.png
        :alt: GemGem screenshot
        :width: 100%
        :align: center

Run
--------

You need pygame installed. Then simply run::

	$ python gemgem.py


Wishlist
---------

 * Allow varying the number of gems
 * Allow explosions with earned special gems (column/row/9-square/all-of-color for 4-row,4-row,5-corner,5-row)
 * Disable some fields, two nearby explosions free them.
 * Allow new game goals:
   * Reach score X with at most N moves
   * Destroy at least N gems of color X
   * Destroy Ni special gems
   * Bring 4 passive gems (rocks) to the bottom
   * Activate N pre-selected fields (have two explosions there)
 * Implement a auto-playing bot with different strategies:
   * Select a random valid move
   * Select the move giving immediately the highest score (most gems destroyed)
   * Thinking two moves ahead, select the move destroying most gems (or producing gems needed for goal)
 * Generate and evaluate levels with different painting strategy
   * Randomly choose filling of Nd disabled fields and Nw activation fields. Symmetric in x-axis.
   * Randomly choose number of gems.
   * Randomly choose game goal.
   * Let auto-playing bot play through:
     * If strategy 1 succeeds >5/10 games -> trivial game.
     * If strategy 1 succeeds >1/10 games and strategy 2 succeeds >5/10 games -> easy game.
     * If strategy 2 succeeds >1/10 games and strategy 3 succeeds >1/10 games -> hard game.
     * If strategy 3 succeeds >1/10 games -> very hard game.
     * If strategy 3 succeeds >=1/50 games -> super hard game.
     * If strategy 3 succeeds <1/50 games -> impossible game
     * Drop trivial and impossible games.



Open source (see LICENSE.rst)


