def get_test_game() -> str:
    raw_hand = """0  Player Debajitb plays at seat 0 with 9.99
0  Player Debajitb with In Deal, Blind To Come Posted, Dirty and None
0  Player Andrhatya plays at seat 2 with 10.00
0  Player Andrhatya with In Deal, Blind To Come Posted, Dirty and None
0  Dealer change (Andrhatya Debajitb Andrhatya)
1  Player Andrhatya posts small blind 0.05 (Done automatically)
2  Player Debajitb posts big blind 0.10 (Done automatically)
2  Dealt to player Debajitb : 8 of clubs
2  Dealt to player Andrhatya : A of spades
2  Dealt to player Debajitb : 8 of spades
2  Dealt to player Andrhatya : 4 of diamonds
11  Player Andrhatya calls 0.05 to 0.10
19  Player Debajitb raises 6.70 to 6.80
21  Player Andrhatya calls 6.70 to 6.80
21  Card dealt to table: 9 of diamonds
21  Card dealt to table: 3 of hearts
21  Card dealt to table: J of diamonds
26  Player Debajitb checks
30  Player Andrhatya folds
30  Rake was taken 0.75
30  Rabbit Hunting pause start. Duration: 5 sec
30  Showdown begins
31  Player Andrhatya RabbitHuntingBuy 0.00
32  Player Debajitb wins, cards weren't shown (Done automatically)
32  Player Debajitb collects main pot 12.85
32  Player Debajitb won 12.85
38  Table is resumed
38  Player Debajitb take a prize 12.85 with rake 0.75"""
    return raw_hand
