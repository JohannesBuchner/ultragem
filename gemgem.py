# Gemgem (A Bejeweled Clone)
# http://inventwithpython.com/blog
# By Al Sweigart al@inventwithpython.com

# This code is meant to be a simple tutorial for Pygame and programming in
# general. As such, the code is simple (there is no object-oriented programming,
# list comprehensions, or other advanced concepts). This is intentional to make
# the code as readable as possible.


# This program has "gem data structures", which are basically dictionaries
# with the following keys:
#   'x' and 'y' - The location of the gem on the board. 0,0 is the top left.
#                 There is also a ROWABOVEBOARD row that 'y' can be set to,
#                 to indicate that it is above the board.
#   'direction' - one of the four constant variables UP, DOWN, LEFT, RIGHT.
#                 This is the direction the gem is moving. (Not always used.)
#   'imageNum' - The integer index into GEMIMAGES to denote which image this
#                gem uses.


import random
import time
import pygame
import sys
import copy
from pygame.locals import *
from bej import *

FPS = 25 # frames per second to update the screen
WINDOWWIDTH = 800  # width of the program's window, in pixels
WINDOWHEIGHT = 600 # height in pixels

BOARDWIDTH = 8 # how many columns in the board
BOARDHEIGHT = 8 # how many rows in the board
GEMIMAGESIZE = 64 # width & height of each space in pixels

# NUMGEMIMAGES is the number of gem types. You will need .png image files named
# gem0.png, gem1.png, etc. up to gem(N-1).png.
NUMGEMIMAGES = 7

# NUMMATCHSOUNDS is the number of different sounds to choose from when a match
# is made. The .wav files are named match0.wav, match1.wav, etc.
NUMMATCHSOUNDS = 6

MOVERATE = 25 # 1 to 100, larger num means faster animations
DEDUCTSPEED = 999999 # reduces score by 1 point every DEDUCTSPEED seconds.

HIGHLIGHTCOLOR = (255, 0, 255) # color of the selected gem's border
BGCOLOR = (170, 190, 255) # background color on the screen
GRIDCOLOR = (0, 0, 255) # color of the game board
GAMEOVERCOLOR = (255, 100, 100) # color of the "Game over" text.
GAMEOVERBGCOLOR = (0, 0, 0) # background color of the "Game over" text.
SCORECOLOR = (85, 65, 0)

# The amount of space to the sides of the board to the edge of the window is
# used several times, so calculate it once here and store in variables.
XMARGIN = int((WINDOWWIDTH - GEMIMAGESIZE * BOARDWIDTH) / 2)
YMARGIN = int((WINDOWHEIGHT - GEMIMAGESIZE * BOARDHEIGHT) / 2)

# Constants for the different directions. The numbers correspond to the
# keyboard's keypad, but they could be any arbitrary value.
UP = 8
RIGHT = 6
DOWN = 2
LEFT = 4

EMPTY_SPACE = -1 # an arbitrary, nonnegative value
ROWABOVEBOARD = 'row above board' # an arbitrary, noninteger value

score = 0 # global variable for the score

def main():
    global FPSCLOCK, WINDOWSURF, GEMIMAGES, GAMESOUNDS, BASICFONT, BOARDRECTS, score

    # Initial set up.
    assert NUMGEMIMAGES > 4
    pygame.init()
    FPSCLOCK = pygame.time.Clock()
    WINDOWSURF = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT))
    pygame.display.set_caption('Gemgem')
    BASICFONT = pygame.font.Font('freesansbold.ttf', 36)

    # Load the images
    GEMIMAGES = []
    for i in range(1,NUMGEMIMAGES+1):
        gemImage = pygame.image.load('gem%s.png' % i)
        if gemImage.get_size() != (GEMIMAGESIZE, GEMIMAGESIZE):
            gemImage = pygame.transform.smoothscale(gemImage, (GEMIMAGESIZE, GEMIMAGESIZE))
        GEMIMAGES.append(gemImage)

    # Load the sounds.
    GAMESOUNDS = {}
    GAMESOUNDS['bad swap'] = pygame.mixer.Sound('badswap.wav')
    GAMESOUNDS['match'] = []
    for i in range(NUMMATCHSOUNDS):
        GAMESOUNDS['match'].append(pygame.mixer.Sound('match%s.wav' % i))

    BOARDRECTS = []
    for x in range(BOARDWIDTH):
        BOARDRECTS.append([])
        for y in range(BOARDHEIGHT):
            r = pygame.Rect((XMARGIN + (x * GEMIMAGESIZE),
                             YMARGIN + (y * GEMIMAGESIZE),
                             GEMIMAGESIZE,
                             GEMIMAGESIZE))
            BOARDRECTS[x].append(r)

    while True:
        runGame()
        score = 0


def runGame():
    global score
    
    if 0:
        mainBoard = getBlankBoard()
        # Drop the initial gems.
        fillBoardAndAnimate(mainBoard, [])
    else:
        from bej import init_board
        print 'calling my init board'
        mainBoard = init_board(5)

    firstSelectedGem = None
    lastMouseDownX = None
    lastMouseDownY = None
    isGameOver = False
    lastScoreDeduction = time.time()
    clickContinueTextSurf = None
    while True:
        clickedSpace = None
        for event in pygame.event.get():
            if event.type == QUIT:
                terminate()

            if event.type == KEYUP:
                if event.key == K_ESCAPE:
                    terminate()
                elif event.key == K_BACKSPACE:
                    return

            if event.type == MOUSEBUTTONUP:
                if isGameOver:
                    return

                if event.pos == (lastMouseDownX, lastMouseDownY):
                    # This is a mouse click.
                    clickedSpace = checkForGemClick(event.pos)
                else:
                    # This is the end of a mouse drag, and the first gem has already been selected.
                    firstSelectedGem = checkForGemClick((lastMouseDownX, lastMouseDownY))
                    mouseOverSpace = checkForGemClick(event.pos)
                    if mouseOverSpace and (mouseOverSpace[0] == firstSelectedGem[0] + 1 or \
                                       mouseOverSpace[0] == firstSelectedGem[0] - 1 or \
                                       mouseOverSpace[1] == firstSelectedGem[1] + 1 or \
                                       mouseOverSpace[1] == firstSelectedGem[1] - 1):
                        clickedSpace = mouseOverSpace

                    if not firstSelectedGem or not mouseOverSpace:
                        # If this MOUSEBUTTONUP was not part of a valid drag, deselect both.
                        firstSelectedGem = None
                        mouseOverSpace = None
            if event.type == MOUSEBUTTONDOWN:
                lastMouseDownX, lastMouseDownY = event.pos

        # Check if this is the first or second gem to be clicked.
        if clickedSpace and not firstSelectedGem:
            firstSelectedGem = clickedSpace
        elif clickedSpace and firstSelectedGem:
            # Two gems have been selected. Swap the gems.
            firstSwappingGem, secondSwappingGem = getSwappingGems(mainBoard, firstSelectedGem, clickedSpace)
            if firstSwappingGem == None and secondSwappingGem == None:
                firstSelectedGem = None # Deselect the first gem.
                continue

            # Show the swap animation on the screen.
            boardCopy = getBoardCopyMinusGems(mainBoard, (firstSwappingGem, secondSwappingGem))
            animateMovingGems(boardCopy, [firstSwappingGem, secondSwappingGem], [])

            # Swap the gems in the board data structure.
            mainBoard[firstSwappingGem['x']][firstSwappingGem['y']] = secondSwappingGem['imageNum']
            mainBoard[secondSwappingGem['x']][secondSwappingGem['y']] = firstSwappingGem['imageNum']

            # See if this is a matching move.
            matchedGems = findMatchingGems(mainBoard)
            if matchedGems == []:
                # Not a matching move: swap the gems back
                GAMESOUNDS['bad swap'].play()
                animateMovingGems(boardCopy, [firstSwappingGem, secondSwappingGem], [])
                mainBoard[firstSwappingGem['x']][firstSwappingGem['y']] = firstSwappingGem['imageNum']
                mainBoard[secondSwappingGem['x']][secondSwappingGem['y']] = secondSwappingGem['imageNum']
            else:
                # This was a matching move.
                scoreAdd = 0
                while matchedGems != []:
                    # The matched gems need to be removed, then pull down the board.
                    points = []
                    for gemSet in matchedGems:
                        scoreAdd += (10 + (len(gemSet) - 3) * 10)
                        for gem in gemSet:
                            mainBoard[gem[0]][gem[1]] = EMPTY_SPACE
                        points.append({'points': scoreAdd,
                                       'x': gem[0] * GEMIMAGESIZE + XMARGIN,
                                       'y': gem[1] * GEMIMAGESIZE + YMARGIN})
                    random.choice(GAMESOUNDS['match']).play()
                    score += scoreAdd

                    # Drop the new gems.
                    fillBoardAndAnimate(mainBoard, points)

                    # Check if there are any new matches.
                    matchedGems = findMatchingGems(mainBoard)
            firstSelectedGem = None

            if not canMakeMove(mainBoard):
                isGameOver = True

        # Draw the board.
        WINDOWSURF.fill(BGCOLOR)
        drawBoard(mainBoard)
        if firstSelectedGem != None:
            highlightSpace(firstSelectedGem[0], firstSelectedGem[1])
        if isGameOver:
            if clickContinueTextSurf == None:
                clickContinueTextSurf = BASICFONT.render('Final Score: %s (Click to continue)' % (score), 1, GAMEOVERCOLOR, GAMEOVERBGCOLOR)
                clickContinueTextRect = clickContinueTextSurf.get_rect()
                clickContinueTextRect.center = int(WINDOWWIDTH / 2), int(WINDOWHEIGHT / 2)
            WINDOWSURF.blit(clickContinueTextSurf, clickContinueTextRect)
        elif score > 0 and time.time() - lastScoreDeduction > DEDUCTSPEED:
            score -= 1
            lastScoreDeduction = time.time()
        drawScore()
        pygame.display.update()
        FPSCLOCK.tick(FPS)


def getSwappingGems(board, firstXY, secondXY):
    firstGem = {'imageNum': board[firstXY[0]][firstXY[1]],
                'x': firstXY[0],
                'y': firstXY[1]}
    secondGem = {'imageNum': board[secondXY[0]][secondXY[1]],
                 'x': secondXY[0],
                 'y': secondXY[1]}
    highlightedGem = None
    if firstGem['x'] == secondGem['x'] + 1 and firstGem['y'] == secondGem['y']:
        firstGem['direction'] = LEFT
        secondGem['direction'] = RIGHT
    elif firstGem['x'] == secondGem['x'] - 1 and firstGem['y'] == secondGem['y']:
        firstGem['direction'] = RIGHT
        secondGem['direction'] = LEFT
    elif firstGem['y'] == secondGem['y'] + 1 and firstGem['x'] == secondGem['x']:
        firstGem['direction'] = UP
        secondGem['direction'] = DOWN
    elif firstGem['y'] == secondGem['y'] - 1 and firstGem['x'] == secondGem['x']:
        firstGem['direction'] = DOWN
        secondGem['direction'] = UP
    else:
        # These gems are not adjacent and can't be swapped.
        return None, None
    return firstGem, secondGem


def getBlankBoard():
    board = []
    for x in range(BOARDWIDTH):
        board.append([EMPTY_SPACE] * BOARDHEIGHT)
    return board


def canMakeMove(board):
    """Return True if the board is in a state where a matching move can be
    made on it. Otherwise return False."""
    for x in range(BOARDWIDTH):
        for y in range(BOARDHEIGHT):
            oneOffPatterns = (((0,1), (1,0), (2,0)),
                              ((0,1), (1,1), (2,0)),
                              ((0,0), (1,1), (2,0)),
                              ((0,1), (1,0), (2,1)),
                              ((0,0), (1,0), (2,1)),
                              ((0,1), (1,1), (2,0)),
                              ((0,0), (0,2), (0,3)),
                              ((0,0), (0,1), (0,3)))
            for pat in oneOffPatterns:
                if (getGemAt(board, x+pat[0][0], y+pat[0][1]) == \
                    getGemAt(board, x+pat[1][0], y+pat[1][1]) == \
                    getGemAt(board, x+pat[2][0], y+pat[2][1]) != None) or \
                   (getGemAt(board, x+pat[0][1], y+pat[0][0]) == \
                    getGemAt(board, x+pat[1][1], y+pat[1][0]) == \
                    getGemAt(board, x+pat[2][1], y+pat[2][0]) != None):
                    return True
    return False


def drawMovingGem(gem, progress):
    movex = 0
    movey = 0
    progress *= 0.01

    if gem['direction'] == UP:
        movey = -int(progress * GEMIMAGESIZE)
    elif gem['direction'] == DOWN:
        movey = int(progress * GEMIMAGESIZE)
    elif gem['direction'] == RIGHT:
        movex = int(progress * GEMIMAGESIZE)
    elif gem['direction'] == LEFT:
        movex = -int(progress * GEMIMAGESIZE)

    basex = gem['x']
    basey = gem['y']
    if basey == ROWABOVEBOARD:
        basey = -1

    pixelx = XMARGIN + (basex * GEMIMAGESIZE)
    pixely = YMARGIN + (basey * GEMIMAGESIZE)
    r = pygame.Rect( (pixelx + movex, pixely + movey, GEMIMAGESIZE, GEMIMAGESIZE) )
    WINDOWSURF.blit(GEMIMAGES[gem['imageNum']], r)


def swapGems(board, x, y, direction):
    if y == ROWABOVEBOARD:
        board[x][y] = EMPTY_SPACE
    else:
        if direction == UP:
            board[x][y], board[x][y-1] = board[x][y-1], board[x][y]
        elif direction == RIGHT:
            board[x][y], board[x+1][y] = board[x+1][y], board[x][y]
        elif direction == DOWN:
            board[x][y], board[x][y+1] = board[x][y+1], board[x][y]
        elif direction == LEFT:
            board[x][y], board[x-1][y] = board[x-1][y], board[x][y]


def pullDownAllGems(board):
    # pulls down all the gems on the board to the bottom to fill in any gaps
    for x in range(BOARDWIDTH):
        gemsInColumn = []
        for y in range(BOARDHEIGHT):
            if board[x][y] != EMPTY_SPACE:
                gemsInColumn.append(board[x][y])
        board[x] = ([EMPTY_SPACE] * (BOARDHEIGHT - len(gemsInColumn))) + gemsInColumn


def getGemAt(board, x, y):
    if x < 0 or y < 0 or x >= BOARDWIDTH or y >= BOARDHEIGHT:
        return None
    else:
        return board[x][y]


def getDropSlots(board):
    # Creates a "drop slot" for each column and fills the slot with a number
    # of gems that that column is lacking.
    # This function assumes that the gems have been gravity dropped already.
    boardCopy = copy.deepcopy(board)
    pullDownAllGems(boardCopy)

    dropSlots = []
    for i in range(BOARDWIDTH):
        dropSlots.append([])

    for x in range(BOARDWIDTH):
        for y in range(BOARDHEIGHT-1, -1, -1):
            if boardCopy[x][y] == EMPTY_SPACE:
                possibleGems = list(range(len(GEMIMAGES)))
                for offsetX, offsetY in ((0, -1), (1, 0), (0, 1), (-1, 0)):
                    # Narrow down the possible gems we should put in the blank
                    # space so we don't end up putting an two of the same gems
                    # next to each other when they drop.
                    neighborGem = getGemAt(boardCopy, x + offsetX, y + offsetY)
                    if neighborGem != None and neighborGem in possibleGems:
                        possibleGems.remove(neighborGem)

                newGem = random.choice(possibleGems)
                boardCopy[x][y] = newGem
                dropSlots[x].append(newGem)
    return dropSlots


def findMatchingGems(board):
    gemsToRemove = []
    boardCopy = copy.deepcopy(board)

    # loop through each space on the board, checking for 3 adjacent gems of the same type
    for x in range(BOARDWIDTH):
        for y in range(BOARDHEIGHT):
            # look for horizontal matches
            if getGemAt(boardCopy, x, y) == getGemAt(boardCopy, x + 1, y) == getGemAt(boardCopy, x + 2, y) and getGemAt(boardCopy, x, y) != EMPTY_SPACE:
                targetGem = boardCopy[x][y]
                offset = 0
                removeSet = []
                while getGemAt(boardCopy, x + offset, y) == targetGem:
                    # keep checking for matching gems, in case there's more than 3 gems in a row
                    removeSet.append((x + offset, y))
                    boardCopy[x + offset][y] = EMPTY_SPACE
                    offset += 1
                gemsToRemove.append(removeSet)

            # look for vertical matches
            if getGemAt(boardCopy, x, y) == getGemAt(boardCopy, x, y + 1) == getGemAt(boardCopy, x, y + 2) and getGemAt(boardCopy, x, y) != EMPTY_SPACE:
                targetGem = boardCopy[x][y]
                offset = 0
                removeSet = []
                while getGemAt(boardCopy, x, y + offset) == targetGem:
                    # keep checking for matching gems, in case there's more than 3 gems in a row
                    removeSet.append((x, y + offset))
                    boardCopy[x][y + offset] = EMPTY_SPACE
                    offset += 1
                gemsToRemove.append(removeSet)

    return gemsToRemove


def highlightSpace(x, y):
    pygame.draw.rect(WINDOWSURF, HIGHLIGHTCOLOR, BOARDRECTS[x][y], 4)


def getDroppingGems(board):
    # Find all the gems that have an empty space below them
    boardCopy = copy.deepcopy(board)
    droppingGems = []
    for x in range(BOARDWIDTH):
        for y in range(BOARDHEIGHT - 2, -1, -1):
            if boardCopy[x][y + 1] == EMPTY_SPACE and boardCopy[x][y] != EMPTY_SPACE:
                # This space drops if it is not empty but the space below it is empty
                droppingGems.append( {'imageNum': boardCopy[x][y], 'x': x, 'y': y, 'direction': DOWN} )
                boardCopy[x][y] = EMPTY_SPACE # this space will become empty if it drops.
    return droppingGems


def animateMovingGems(board, gems, pointsText):
    progress = 0 # progress at 0 represents beginning, progress at 100 represents finish.
    while progress < 100:
        WINDOWSURF.fill(BGCOLOR)
        drawBoard(board)
        # Draw each gem.
        for gem in gems:
            drawMovingGem(gem, progress)
        drawScore()
        for pointText in pointsText:
            pointsSurf = BASICFONT.render(str(pointText['points']), 1, SCORECOLOR)
            pointsRect = pointsSurf.get_rect()
            pointsRect.center = (pointText['x'], pointText['y'])
            WINDOWSURF.blit(pointsSurf, pointsRect)

        pygame.display.update()
        FPSCLOCK.tick(FPS)
        progress += MOVERATE


def moveGems(board, movingGems):
    # movingGems is a list of dicts with keys 'x', 'y', 'direction', and 'imageNum'
    for gem in movingGems:
        if gem['y'] != ROWABOVEBOARD:
            board[gem['x']][gem['y']] = EMPTY_SPACE
            movex = 0
            movey = 0
            if gem['direction'] == LEFT:
                movex = -1
            elif gem['direction'] == RIGHT:
                movex = 1
            elif gem['direction'] == DOWN:
                movey = 1
            elif gem['direction'] == UP:
                movey = -1
            board[gem['x'] + movex][gem['y'] + movey] = gem['imageNum']
        else:
            board[gem['x']][0] = gem['imageNum'] # ignore 'direction', just move to top row


def fillBoardAndAnimate(board, points=None):
    dropSlots = getDropSlots(board)
    while dropSlots != [[]] * BOARDWIDTH:
        # Go through the dropping animation as long as the board isn't full.
        movingGems = getDroppingGems(board)
        for x in range(len(dropSlots)):
            if len(dropSlots[x]) != 0:
                movingGems.append({'imageNum': dropSlots[x][0], 'x': x, 'y': ROWABOVEBOARD, 'direction': DOWN})

        boardCopy = getBoardCopyMinusGems(board, movingGems)
        animateMovingGems(boardCopy, movingGems, points)
        moveGems(board, movingGems)

        # Take the next group of gems from the drop slots.
        for x in range(len(dropSlots)):
            if len(dropSlots[x]) == 0:
                continue
            board[x][0] = dropSlots[x][0]
            del dropSlots[x][0]


def terminate():
    pygame.quit()
    sys.exit()


def checkForGemClick(pos):
    # See if the mouse click was on the board
    for x in range(BOARDWIDTH):
        for y in range(BOARDHEIGHT):
            if BOARDRECTS[x][y].collidepoint(pos[0], pos[1]):
                return (x, y) # Return board x and y where the click occurred.
    return None # Click was not on the board.


def drawBoard(board):
    pygame.draw.rect(WINDOWSURF, BGCOLOR, (XMARGIN, YMARGIN - GEMIMAGESIZE, GEMIMAGESIZE * BOARDWIDTH, GEMIMAGESIZE * (BOARDHEIGHT+1)), 0)
    for x in range(BOARDWIDTH):
        for y in range(BOARDHEIGHT):
            pygame.draw.rect(WINDOWSURF, GRIDCOLOR, BOARDRECTS[x][y], 1)
            gemToDraw = board[x][y]
            if gemToDraw != EMPTY_SPACE:
                WINDOWSURF.blit(GEMIMAGES[gemToDraw], BOARDRECTS[x][y])


def getBoardCopyMinusGems(board, gems):
    # Gems is a list of dicts, with keys 'imageNum', 'x', 'y', 'direction'.
    boardCopy = copy.deepcopy(board)

    # Remove some of the gems from this board data structure copy.
    for gem in gems:
        if gem['y'] != ROWABOVEBOARD:
            boardCopy[gem['x']][gem['y']] = EMPTY_SPACE
    return boardCopy


def drawScore():
    scoreImg = BASICFONT.render(str(score), 1, SCORECOLOR) # score is a global variable
    scoreRect = scoreImg.get_rect()
    scoreRect.bottomleft = (10, WINDOWHEIGHT - 10)
    WINDOWSURF.blit(scoreImg, scoreRect)


if __name__ == '__main__':
    main()
