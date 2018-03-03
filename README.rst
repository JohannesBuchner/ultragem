UltraGem - A Bejeweled/CandyCrush clone
======================================

    .. image:: https://raw.githubusercontent.com/JohannesBuchner/ultragem/master/screenshot.png
        :alt: UltraGem screenshot
        :align: center

How to Run UltraGem
--------------------

You need pygame and a few other libraries installed. Then simply run::

	$ python ultragem.py


Progress and TODO
--------------------

* Allow varying the number of gems (done)
* Allow explosions with earned special gems (column/row/9-square/all-of-color for 4-row,4-row,5-corner,5-row) (done)
* Disable some fields, two nearby explosions free them. (done)
* Implement a auto-playing bot with different strategies:
   * Select a random valid move (done)
   * Select the move giving immediately the highest score (most gems destroyed) (done)
   * Thinking two moves ahead, select the move destroying most gems (or producing gems needed for goal) (done)
* Generate and evaluate levels with different painting strategy (done)
   * Randomly choose filling of Nd disabled fields and Nw activation fields. Symmetric in x-axis.
   * Randomly choose number of gems.
   * Randomly choose game goal.
   * Let auto-playing bot play through: (done)
      * If strategy 1 succeeds >5/10 games -> trivial game.
      * If strategy 1 succeeds >1/10 games and strategy 2 succeeds >5/10 games -> easy game.
      * If strategy 2 succeeds >1/10 games and strategy 3 succeeds >1/10 games -> hard game.
      * If strategy 3 succeeds >1/10 games -> very hard game.
      * If strategy 3 succeeds >=1/50 games -> super hard game.
      * If strategy 3 succeeds <1/50 games -> impossible game
      * Drop trivial and impossible games.
* Define game score: (all done)
   * Reach score X with at most N moves
   * Destroy at least N gems of color X
   * Destroy Ni special gems
   * Bring 4 passive gems (rocks) to the bottom
   * Activate N pre-selected fields (have two explosions there)
* Define a level specification (done)
   * Level file: initial board size,state,number of colors and required goal
   * Journey: directory of levels, named in sequence
* Convert auto-generated and scored levels to levels (done)
   * Define goals based on bot performance
* Load/select journey on startup. Show current level number (done)
* If goal reached, player can advance to next level (done)


Open source (see LICENSE.rst)

Based on GemGem:
http://inventwithpython.com/blog/2011/06/24/new-game-source-code-gemgem-a-bejeweled-clone/

