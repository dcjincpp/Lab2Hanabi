from hanabi import *
import util
import agent
import random

class InnerStatePlayer(agent.Agent):
    def __init__(self, name, pnr):
        self.name = name
        self.explanation = []

    def get_action(self, nr, hands, knowledge, trash, played, board, valid_actions, hints, hits, cards_left):
        my_knowledge = knowledge[nr]
        
        potential_discards = []
        for i,k in enumerate(my_knowledge):
            if util.is_playable(k, board):
                return Action(PLAY, card_index=i)
            if util.is_useless(k, board):    
                potential_discards.append(i)
                
        if potential_discards:
            return Action(DISCARD, card_index=random.choice(potential_discards))

        if hints > 0:
            for player,hand in enumerate(hands):
                if player != nr:
                    for card_index,card in enumerate(hand):
                        if card.is_playable(board):                              
                            if random.random() < 0.5:
                                return Action(HINT_COLOR, player=player, color=card.color)
                            return Action(HINT_RANK, player=player, rank=card.rank)

            hints = util.filter_actions(HINT_COLOR, valid_actions) + util.filter_actions(HINT_RANK, valid_actions)
            return random.choice(hints)

        return random.choice(util.filter_actions(DISCARD, valid_actions))
        
def format_hint(h):
    if h == HINT_COLOR:
        return "color"
    return "rank"
        
class OuterStatePlayer(agent.Agent):
    def __init__(self, name, pnr):
        self.name = name
        self.hints = {}
        self.pnr = pnr #player number
        self.explanation = []

    #utilize trash and played for process of elimination for more information of hand
    def get_action(self, nr, hands, knowledge, trash, played, board, valid_actions, hints, hits, cards_left):
        #def update_Knowledge(hands, played, discarded, my_knowledge, nr):

        def adjust_card_count(card_map, color, rank, delta):
            if color in card_map and rank in card_map[color]:
                card_map[color][rank] += delta
                # Ensure the count doesn't go below 0
                if card_map[color][rank] < 0:
                    card_map[color][rank] = 0
            else:
                raise ValueError("Invalid color or rank")
            
        card_map = {
            color: {rank: COUNTS[rank] for rank in range(len(COUNTS))}
            for color in range(len(ALL_COLORS))
        }

        for _,card in enumerate(trash):
            adjust_card_count(card_map, card.color, card.rank - 1, -1)
            print(card)
#################################################################
        # for _, card in enumerate(played):
        #     adjust_card_count(card_map, card.color, card.rank - 1, -1)

        # for i, hand in enumerate(hands):
        #         #if(i == nr):
        #             #continue
        #         for _, card in enumerate(hand):
        #             adjust_card_count(card_map, card.color, card.rank - 1, -1)
        
        # total_cards = 0
        # for color, ranks in card_map.items():
        #     # Sum up the counts for all ranks under this color
        #     total_cards += sum(ranks)
        # print("out cards", len(trash) + len(played))
        # print("Trash Cards:", [(card.color, card.rank) for card in trash])
        # print("Played Cards:", [(card.color, card.rank) for card in played])
        # print("Other Hands Cards:", [(card.color, card.rank) for hand in hands for card in hand if hand != hands[nr]])

        #print(card_map)
        #print("total cards", total_cards)
        #print("-----------------------------------")
        # print(trash)
#################################################################
        #hands of other players
        for player,hand in enumerate(hands):
            for card_index,card in enumerate(hand):
                #if the card in a players hand does not have any hints, create an empty set of hints for it
                if (player,card_index) not in self.hints:
                    self.hints[(player,card_index)] = set() #players hints about card at index card_index = set()
        known = [""]*5
        for h in self.hints:
            pnr, card_index = h 
            if pnr != nr: #if player number is not the current player
                known[card_index] = str(list(map(format_hint, self.hints[h])))
        self.explanation = [["hints received:"] + known]

        #your hand
        my_knowledge = knowledge[nr]
        print(card_map)

        for i,k in enumerate(my_knowledge):
            print(k)
            print("---------------------------", "\n")
            #for j,card in enumerate(my_knowledge[i]):
                # print(card, "\n")
                # print("---------------------------", "\n")

        #goes through your potential hand and checks if something can be played while also checking and adding useless cards into an array
        potential_discards = []
        for i,k in enumerate(my_knowledge):
            if util.is_playable(k, board):
                return Action(PLAY, card_index=i)
            if util.is_useless(k, board):    
                potential_discards.append(i)
        
        #discard one of the useless cards
        if potential_discards:
            return Action(DISCARD, card_index=random.choice(potential_discards))
         
        playables = []        
        for player,hand in enumerate(hands):
            if player != nr:
                for card_index,card in enumerate(hand):
                    if card.is_playable(board):                              
                        playables.append((player,card_index))
        
        #sorts the playables by rank in descending order (5,4,3,2,1)
        playables.sort(key=lambda which: -hands[which[0]][which[1]].rank)
        while playables and hints > 0:
            player,card_index = playables[0]
            knows_rank = True
            real_color = hands[player][card_index].color
            real_rank = hands[player][card_index].rank
            k = knowledge[player][card_index]
            
            hinttype = [HINT_COLOR, HINT_RANK]
            
            
            for h in self.hints[(player,card_index)]:
                hinttype.remove(h)
            
            t = None
            if hinttype:
                t = random.choice(hinttype)
            #tells player which cards are a rank
            if t == HINT_RANK:
                for i,card in enumerate(hands[player]):
                    if card.rank == hands[player][card_index].rank:
                        self.hints[(player,i)].add(HINT_RANK)
                return Action(HINT_RANK, player=player, rank=hands[player][card_index].rank)
            #tells player which cards are a color
            if t == HINT_COLOR:
                for i,card in enumerate(hands[player]):
                    if card.color == hands[player][card_index].color:
                        self.hints[(player,i)].add(HINT_COLOR)
                return Action(HINT_COLOR, player=player, color=hands[player][card_index].color)
            
            playables = playables[1:]
 
        if hints > 0:
            hints = util.filter_actions(HINT_COLOR, valid_actions) + util.filter_actions(HINT_RANK, valid_actions)
            hintgiven = random.choice(hints)
            if hintgiven.type == HINT_COLOR:
                for i,card in enumerate(hands[hintgiven.player]):
                    if card.color == hintgiven.color:
                        self.hints[(hintgiven.player,i)].add(HINT_COLOR)
            else:
                for i,card in enumerate(hands[hintgiven.player]):
                    if card.rank == hintgiven.rank:
                        self.hints[(hintgiven.player,i)].add(HINT_RANK)
                
            return hintgiven

        return random.choice(util.filter_actions(DISCARD, valid_actions))

    def inform(self, action, player):
        if action.type in [PLAY, DISCARD]:
            if (player,action.card_index) in self.hints:
                self.hints[(player,action.card_index)] = set()
            for i in range(5):
                if (player,action.card_index+i+1) in self.hints:
                    self.hints[(player,action.card_index+i)] = self.hints[(player,action.card_index+i+1)]
                    self.hints[(player,action.card_index+i+1)] = set()


agent.register("inner", "Inner State Player", InnerStatePlayer)
agent.register("outer", "Outer State Player", OuterStatePlayer)