from pprint import pprint
import random
import numpy
import bisect
from math import floor


# number of columns
NCOL = 8
# number of rows
NROW = 8

# number of colors
NCOLOR = 7



"""
shape3_flat: 4 variants

1: ** *
2: * **
3: rotate 1 clock-wisely 90 degree
4: rotate 2 clock-wisely 90 degree
"""

shape3_flat_x = (
  (0,0,0),
  (0,0,0),
  (0,1,3),
  (0,2,3))

shape3_flat_y = (
  (0,1,3),
  (0,2,3),
  (0,0,0),
  (0,0,0))

"""
shape3_zigzag: 4 variants
    *
1: * *
2: rotate 1 cw 90 deg
3: rotate 1 cw 180 deg
4: rotate 1 cw 270 deg
"""
shape3_zigzag_x = (
  (1,0,1),
  (0,1,2),
  (0,1,0),
  (0,1,2))

shape3_zigzag_y = (
  (0,1,2),
  (0,1,0),
  (0,1,2),
  (1,0,1))

"""
shape3_worm: 8 variants
     *
1: **
2: rotate 1 cw 90 deg
3: rotate 1 cw 180 deg
4: rotate 1 cw 270 deg
5: **
     *
6: rotate 5 cw 90 deg
7: rotate 5 cw 180 deg
8: rotate 5 cw 270 deg     
"""
shape3_worm_x = (
  (1,1,0),
  (0,1,2),
  (1,0,0),
  (0,1,2),
  (0,0,1),
  (0,1,2),
  (0,1,1),
  (0,1,2))

shape3_worm_y = (
  (0,1,2),
  (0,0,1),
  (0,1,2),
  (0,1,1),
  (0,1,2),
  (1,1,0),
  (0,1,2),
  (1,0,0))

def get_mat(shape=1, sub_shape=-1):
    if shape == 1:
        mat_dx = shape3_flat_x
        mat_dy = shape3_flat_y
    elif shape == 2:
        mat_dx = shape3_zigzag_x
        mat_dy = shape3_zigzag_y
    elif shape == 3:
        mat_dx = shape3_worm_x
        mat_dy = shape3_worm_y
    else:
        exit(1)
    if sub_shape == -1:
        return (mat_dx, mat_dy)
    return (mat_dx[sub_shape], mat_dy[sub_shape])

def draw_basic_shape(shape=1):
    mat_dx, mat_dy = get_mat(shape)
    nshapes = len(mat_dx)
    npts = len(mat_dx[0])
    for i in range(nshapes):
        mat = [[0]*NCOL for x in xrange(NROW)]
        for j in range(npts):
            dx = mat_dx[i][j]
            dy = mat_dy[i][j]
            mat[dx][dy] = 1
        pprint(mat)
    
def paitable_of_shape_at_pos(board, pos=(0,0), shape=1, sub_shape=0):
    dx, dy = get_mat(shape, sub_shape)
    npts = len(dx)
    x0,y0 = pos
    for i in range(npts):
        x1 = x0 + dx[i]
        y1 = y0 + dy[i]
        if x1 >= NROW or y1 >= NCOL or board[x1][y1] > 0: 
            return False
    return True

def paitable_of_shape_color_at_pos(board, pos=(0,0), shape=1, sub_shape=0, color=1):
    check_x = (
        (1,2),(-1,1),(-1,-2),
        (0,0),(0,0),(0,0))    
    check_y = (
        (0,0),(0,0),(0,0),
        (1,2),(-1,1),(-1,-2))
    ncheck = len(check_x)
    dx, dy = get_mat(shape, sub_shape)
    npts = len(dx)
    x0,y0 = pos
    #print 'origin', x0,y0, 'shape', shape, 'sub_shape', sub_shape
    for i in range(npts):
        
        x1 = x0 + dx[i]
        y1 = y0 + dy[i]
        #print 'to paint pos #%d, (%d,%d)' % (i, x1,y1), 'with color', color
        
        # room not taken yet
        if x1 >= NROW or y1 >= NCOL or board[x1][y1] > 0: 
            #print (x1,y1), 'out of border or spot taken'
            return False
        
        # NOT to form a 3-in-a-row/col with existing cells
        for j in range(ncheck):
            x2 = x1 + check_x[j][0]
            y2 = y1 + check_y[j][0]
            x3 = x1 + check_x[j][1]
            y3 = y1 + check_y[j][1]
            #print 'checking', (x2,y2), (x3,y3)
            if 0 <= x2 < NROW and 0 <= y2 < NCOL and \
               0 <= x3 < NROW and 0 <= y3 < NCOL and \
               board[x2][y2] == board[x3][y3] == color:
                #print 
                return False
            
        # NOT to form a 3-in-a-row/col with existing cell plus cells in its own shape
        # zigzag never falls in this condition
        if shape==2: continue
        flat_extra_check_pts = (
            ((0,2),(-1,0)),
            ((0,1),(0,4)),
            ((2,0),(-1,0)),
            ((1,0),(4,0)))
        
        nextra = 2
        worm_extra_check_pts = (
            ((1,2),(1,-1)),
            ((2,0),(-1,0)),
            ((0,0),(0,3)),
            ((0,1),(3,1)),
            ((0,2),(0,-1)),
            ((2,1),(-1,1)),
            ((1,0),(1,3)),
            ((0,0),(3,0)))
        if shape==1: 
            for j in range(nextra):
                x4 = x0 + flat_extra_check_pts[sub_shape][j][0]
                y4 = y0 + flat_extra_check_pts[sub_shape][j][1]
                if 0 <= x4 < NROW and 0 <= y4 < NCOL and board[x4][y4] == color:
                    return False
        elif shape == 3:
            for j in range(nextra):
                x4 = x0 + worm_extra_check_pts[sub_shape][j][0]
                y4 = y0 + worm_extra_check_pts[sub_shape][j][1]
                if 0 <= x4 < NROW and 0 <= y4 < NCOL and board[x4][y4] == color:
                    return False        
    return True

def paint_shape_at_pos_with_color(board, pos=(0,0), shape=1, sub_shape=0, color=9):
    dx, dy = get_mat(shape, sub_shape)
    npts = len(dx)
    x0,y0 = pos
    for i in range(npts):
        x1 = x0 + dx[i]
        y1 = y0 + dy[i]
        board[x1][y1] = color
  
"""unit tests"""
def unit_test_basic_shape():
    for i in range(3):
        print 'shape %d' % (i+1)        
        draw_basic_shape(i+1)
              
def unit_test_paitable(a):        
    a[3][3] = 1
    a[3][4] = 1 
    
    print paitable_of_shape_at_pos(a, (1,1), shape=1, sub_shape=0)
    paint_shape_at_pos_with_color(a, (1,1), shape=1, sub_shape=0, color=6)
    pprint(a)   
    
    print paitable_of_shape_at_pos(a, (3,0), shape=1, sub_shape=0)



def fill_all_non_colored_cells(board):
    #print 'begin: working on remaining non-colored cells'
    for i in range(0, NROW):
        for j in range(0, NCOL):
            if board[i][j] <= 0:
                #print 'pos', i, j
                fill_non_colored_cell_at_pos(board, (i,j))
                #pprint(board)
                
def fill_non_colored_cell_at_pos(board, pos):
    all_color = set()
    for i in range(1,NCOLOR+1):
        all_color.add(i)
    neighbor_4_x = (1,-1,0,0)
    neighbor_4_y = (0,0,1,-1)
    x0,y0 = pos
    for i in range(4):
        x1 = x0 + neighbor_4_x[i]
        y1 = y0 + neighbor_4_y[i]
        #print 'pos', pos, 'checking neighbor', (x1,y1)
        if 0 <= x1 < NROW and 0 <= y1 < NCOL and board[x1][y1] > 0 and board[x1][y1] in all_color:
            #print 'pos', pos,'removing color %d' % board[x1][y1]
            all_color.remove(board[x1][y1])
            
    #print 'pos', pos, 'choices left:' , list(all_color)
    chosen_color = random.choice(list(all_color))
    #print 'pos', pos, 'chosen color:', chosen_color
    board[x0][y0] = chosen_color

def unit_test_random_board(board, diff=0):
    color_real = [0]*(NCOLOR)
    color_hist = [floor(1.1*NROW*NCOL/NCOLOR)]*(NCOLOR)
    color_cumsum = numpy.cumsum(color_hist)
    basic_cnt = 0
    max_step = NROW*NCOL/4
    step_threshold = max_step * (9.0-diff)/9.0
    
    for i in range(4000):
        
        if basic_cnt >= step_threshold:
            break
        
        x0 = random.randint(0, NROW-1)
        y0 = random.randint(0, NCOL-1)
        
        #TODO need to balance different colors
        if color_cumsum[-1] == 0:
            #pprint(a)
            #print 'basic count', basic_cnt
            return
        
        rand_idx = random.randint(0,color_cumsum[-1]-1)
        color = bisect.bisect_right(color_cumsum, rand_idx)
        
        #color = random.randint(1,NCOLOR)
        shape = random.randint(1,3)
        if shape in (1,2):
            sub_shape = random.randint(0,3)
        else:
            sub_shape = random.randint(0,7)
        p = (x0, y0)
        
        
        if paitable_of_shape_color_at_pos(board, p, shape, sub_shape, color+1):
            #print '='*70, i, 'pre'
            #pprint(a)
            #pprint(color_hist)
            #pprint(color_cumsum)
            #print 'rand_idx = %d' % rand_idx
            #print 'color chosen %d' % (color+1)
            
            paint_shape_at_pos_with_color(board, p, shape, sub_shape, color+1)
            color_hist[color] -= 4
            color_hist[color] = max(0, color_hist[color])
            color_real[color] += 4
            color_cumsum = numpy.cumsum(color_hist)
            
            #print '='*70, i,'post'
            #pprint(color_hist)
            #pprint(color_cumsum)
            #pprint(color_real)
            #pprint(a)
            basic_cnt += 1
            #print 'number of non-colored cells: %d' % (NROW*NCOL-sum(color_real))
    #pprint(board)
    #print 'basic count', basic_cnt
    
def init_board(diff=0):
    diff = min(max(diff,0.0),9.0)
    print 'diff level: %d' % diff
    a = [[0]*NCOL for x in xrange(NROW)]
    print 'before random fill'
    unit_test_random_board(a,diff)
    
    pprint(a)
    fill_all_non_colored_cells(a)
    
    print 'after random fill'
    pprint(a)
    
    for i in range(0, NROW):
        for j in range(0, NCOL):
            a[i][j] -=1
    return a


if __name__ == '__main__':
    for r in range(100,200):
        print r
        random.seed(r)
        init_board(diff=5)



