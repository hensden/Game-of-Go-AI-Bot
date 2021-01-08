'''
Authored by: Rohan Karnawat
Description: An alphabeta pruning enabled minimax algorithm for the Game of Go. 
			 Includes a few greedy optimizations. The bot is for only 5x5 go boards. 
CSCI 561 - 2102695224
'''
import os
from copy import deepcopy as dc
######################################################################################
##                                     UTILITIES                                    ##
######################################################################################
def writer(result):
    ans = ""
    if result[0] == "P":
    	ans = "PASS"
    else:
	    ans += str(result[0]) + ',' + str(result[1])

    f2 = open("output.txt", 'w')
    f2.write(ans)
    f2.close()

def reader():
    f1 = open("input.txt", 'r')
    boards = f1.readlines()
    f1.close()

    piece = int(boards[0].strip())

    pre = [[int(number) for number in row.rstrip('\n')] for row in boards[1:6]]
    board = [[int(number) for number in row.rstrip('\n')] for row in boards[6:11]]

    return piece, pre, board

def get_count(b, piece):
	cc = 0
	for i in range(5):
		for j in range(5):
			if b[i][j]==piece:
				cc+=1
	return cc


def get_empty_spaces(board):
	cc = 0
	for i in range(5):
		for j in range(5):
			if board[i][j] == 0:
				cc+=1
	return cc


def greedy(obj0, piece, x, y):
	obj = dc(obj0)
	obj.board[x][y] = piece
	deaths = obj.simulate_deaths(3-piece)
	if deaths:
		return len(deaths)
	return 0

og_board = None
######################################################################################
##                                MAIN SIMULATOR CLASS                              ##
######################################################################################
class GameOfGo:
	def __init__(self, pre, board):
		self.board = board
		self.pre = pre
		

	def get_neighbours(self, i, j):
		'''Get 4 neighbours'''
		n = []
		if i>0:
			n.append((i-1, j))
		if j>0:
			n.append((i, j-1))
		if i<4:
			n.append((i+1, j))
		if j<4:
			n.append((i, j+1))
		return n

	def get_friendly_neighbours(self, i, j):
		'''Get 4 neighbours that have same piece'''
		n = []
		if i>0 and self.board[i][j]==self.board[i-1][j]:
			n.append((i-1, j))
		if j>0 and self.board[i][j]==self.board[i][j-1]:
			n.append((i, j-1))
		if i<4 and self.board[i][j]==self.board[i+1][j]:
			n.append((i+1, j))
		if j<4 and self.board[i][j]==self.board[i][j+1]:
			n.append((i, j+1))
		return n

	def get_allied_component(self, i, j):
		'''Get a connected component/island of matching pieces'''
		st = []
		st.append((i,j))
		allies = []

		while len(st)>0:
			top = st.pop()
			allies.append(top)
			friends = self.get_friendly_neighbours(top[0],top[1])
			for friend in friends:
				if friend not in allies and friend not in st:
					st.append(friend)
		return allies

	def get_liberty_single(self, i, j):
		'''Get Liberty of one stone'''
		cc = 0
		free = False
		for pos in self.get_neighbours(i, j):
			if self.board[pos[0]][pos[1]] == 0:
				cc+=1
				free = True
		return free, cc
			
	def get_liberty_count(self, i, j):
		'''Get Liberty of one component'''
		allies = self.get_allied_component(i, j)
		cc = 0
		for pos in allies:
			neighbours = self.get_neighbours(pos[0], pos[1])
			for pos_pos in neighbours:
				if self.board[pos_pos[0]][pos_pos[1]] == 0:
					cc += 1
		return cc

	def get_liberty_bool(self, i, j):
		'''Check is position has any liberty'''
		allies = self.get_allied_component(i, j)
		for pos in allies:
			neighbours = self.get_neighbours(pos[0], pos[1])
			for pos_pos in neighbours:
				if self.board[pos_pos[0]][pos_pos[1]] == 0:
					return True
		return False

	
	def simulate_deaths(self, piece):
		'''Simulator for child branches of MMAB'''
		dying_locations = []
		for i in range(5):
			for j in range(5):
				if self.board[i][j] == piece:
					if not self.get_liberty_bool(i,j):
						dying_locations.append((i, j))
		if not dying_locations or len(dying_locations)==0:
			return None
		for pos in dying_locations:
			self.board[pos[0]][pos[1]] = 0
		return dying_locations


	def compare(self, a, b):
		'''Simply compare two board states'''
		for i in range(5):
			for j in range(5):
				if a[i][j]!=b[i][j]:
					return False
		return True


	def get_validity(self, i, j, piece):
		'''Validate a position'''
		if i<0 or j<0 or i>4 or j>4 or self.board[i][j] != 0:
			return False
		obj2 = dc(self)
		obj2.board[i][j] = piece
		# check for liberty 
		if obj2.get_liberty_bool(i, j):
			# print("if freedom", end=' ')
			return True
		tmp = obj2.simulate_deaths(3 - piece)
		if not obj2.get_liberty_bool(i, j):
			return False
		
		if tmp is not None and self.compare(self.pre, obj2.board):
			# print('KO violated', end=' ')
			return False

		return True

	def get_valid_locations(self, piece):
		'''Get valid positions'''
		valid = []
		for ico in range(5):
			for jco in range(5):
				if self.get_validity(ico, jco, piece):
					valid.append((ico,jco))
		return valid


	def set_piece(self, piece, i, j):
		'''Make a move'''
		self.pre = dc(self.board)
		self.board[i][j] = piece

	
	def is_winner(self, piece):
		'''Check is piece is winner'''
		me = 0
		op = 0
		if piece==1:
			op = 2.5
		else:
			me = 2.5
		for i in range(5):
			for j in range(5):
				if self.board[i][j]==piece:
					me += 1
				elif self.board[i][j]==3-piece:
					op += 1
		return me>op


######################################################################################
##                         DRIVER CODE / CORE IMPLEMENTATION                        ##
######################################################################################
def get_board_score(obj, piece, N):
	'''EVALUATION HEURISTIC'''
	global og_board
	cc = 0.0
	if N>15:
		if obj.is_winner(piece):
			cc += 1000
		else:
			cc -= 1000

	opponent = []
	me = []
	for i in range(5):
		for j in range(5):
			tmp1 = 0
			if obj.board[i][j] == piece:
				tmp1 += obj.get_liberty_count(i,j)
				me.append((i,j))
			elif obj.board[i][j] == 3-piece:
				opponent.append((i,j))
				lib_c = obj.get_liberty_count(i,j)
				tmp1 -= lib_c
				comp = obj.get_allied_component(i,j)
				if lib_c==0:
					lib_c=1
				cc += 1.5*len(comp)/float(lib_c)
			else:
				comp = obj.get_allied_component(i, j)
				surrounded = True
				if len(comp) > 1:
					for cell in comp:
						neighbours = obj.get_neighbours(cell[0],cell[1])
						for n in neighbours:
							if obj.board[n[0]][n[1]]==3-piece:
								surrounded = False
								break
						if not surrounded:
							break
				if surrounded:
					cc += 10*float(len(comp))

			cc += tmp1*4
			eye_members = obj.get_neighbours(i,j)
			outof4 = 0
			for mem in eye_members:
				if obj.board[mem[0]][mem[1]]==piece:
					outof4+=1
			tmp2 = [(0,0),(0,4),(4,4),(4,0)]
			if i>0 and i<4 and j>0 and j<4:
				cc += outof4*4
			elif (i,j) in tmp2:
				cc += outof4*2
			else:
				cc += outof4*3
				
	ikilled = 0
	for pos in opponent:
		if obj.board[pos[0]][pos[1]] != 3-piece:
			ikilled+=1
	murdered = 0
	for pos in me:
		if obj.board[pos[0]][pos[1]] != piece:
			murdered+=1
	cc += (ikilled - murdered)*5
	return cc

def alphabeta(obj0, piece, x, y, D, alpha, beta, maximizing_player, N):
	'''MINIMAX WITH A-B PRUNING'''
	if D==0 or N>24:
		if maximizing_player:
			return get_board_score(obj0, piece, N)
		return get_board_score(obj0, 3-piece, N)
			
	
	obj = dc(obj0)
	obj.set_piece(piece, x, y)
	
	next_valids = obj.get_valid_locations(3-piece)
	
	if maximizing_player:
		maxEval = -float('inf')
		for child in next_valids:
			val = alphabeta(obj, 3-piece,
				child[0], child[1], D-1,
				alpha, beta,
				False, N+1)
			if val is not None:
				maxEval = max(maxEval, val)
				alpha = max(alpha, val)
				if beta <= alpha:
					break
		return maxEval
	
	else:
		minEval = float('inf')
		for child in next_valids:
			val = alphabeta(obj, 3-piece,
				child[0], child[1], D-1,
				alpha, beta,
				True, N+1)
			if val is not None:
				minEval = min(minEval, val)
				beta = min(beta, val)
				if beta <= alpha:
					break
		return minEval
	return


def next_move(obj, piece, pre, board, move_number, depth):
	'''CORE CONTROLLER'''
	if move_number==1:
		return (2,1)
	if move_number==2:
		options = [(2,1), (2,2), (2,3), (1,2), (3,2), (1,1), (3,3)]
		for opt in options:
			if board[opt[0]][opt[1]]==0 and obj.get_liberty_single(opt[0],opt[1])[1]==4:
				return opt

	obj1 = dc(obj)
	available = obj1.get_valid_locations(piece)
	if len(available) == 0 or move_number>24:
		return "PASS"
	if depth==-100:
		# greedy 
		bestEval = -float('inf')
		for child in available:
			 val = greedy(obj1, piece, child[0], child[1])
			 if val > bestEval:
			 	bestEval = val
			 	best_child = child
	else:	
		best_child = available[0]
		best_immediate = available[0]
		maxEval = -float('inf')
		maxImm = -float('inf')
		for child in available:
			md = depth
			immediate_kills = greedy(obj1, piece, child[0], child[1])
			if immediate_kills > maxImm:
				maxImm = immediate_kills
				best_immediate = child
		if maxImm > 1:
			return best_immediate

		for child in available:
			md = depth
			val = alphabeta(obj1, piece,
				child[0], child[1], md,
				-float('inf'), float('inf'),
				True, move_number)
			if val > maxEval:
				best_child = child
				maxEval = val
			
	return best_child


def main():
	global og_board
	piece_type, previous_board, board = reader()
	og_board = dc(board)
	emp = get_empty_spaces(board)
	if emp==25:
		move_number = 1
	elif emp==24:
		move_number = 2
	else:
		with open('moves.txt', 'r') as f:
			move_number = int(f.read().strip())
			move_number += 2


	print("MOVE NUMBER : {}".format(move_number))
	with open('moves.txt', 'w') as f:
		f.write(str(move_number))
	if move_number < 11:
		max_depth = 2
	elif move_number < 19:
		max_depth = 3
	elif move_number < 21:
		max_depth = 4
	else:
		max_depth = -100

	if (max_depth<2 and max_depth>-10 and move_number>5) or move_number>=24:
		os.remove('moves.txt')


	simulator = GameOfGo(previous_board, board)
	action = next_move(
		simulator,
		piece_type,
		previous_board,
		board,
		move_number,
		max_depth)
	writer(action)

if __name__=="__main__":
	main()