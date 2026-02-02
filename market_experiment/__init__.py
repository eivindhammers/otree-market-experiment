from otree.api import *
import random

doc = """
Double Auction Market Experiment
Demonstrates how decentralized decisions with private information lead to market equilibrium.
"""


class C(BaseConstants):
    NAME_IN_URL = 'market'
    PLAYERS_PER_GROUP = None  # All players in one market
    NUM_ROUNDS = 3

    # Value/cost schedules - designed to create clear supply/demand curves
    # These create a theoretical equilibrium around 50-60
    BUYER_VALUES = [95, 90, 85, 80, 75, 70, 65, 60, 55, 50, 45, 40, 35, 30, 25, 20, 15, 10]
    SELLER_COSTS = [10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95]

    ENDOWMENT = 100  # Starting points for everyone


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    market_price = models.FloatField(initial=0)
    num_trades = models.IntegerField(initial=0)
    total_surplus = models.FloatField(initial=0)


class Player(BasePlayer):
    role_assigned = models.StringField()  # 'buyer' or 'seller'
    private_value = models.IntegerField()  # buyer's value or seller's cost
    bid_or_ask = models.IntegerField(
        min=0, max=100,
        label=""
    )
    traded = models.BooleanField(initial=False)
    trade_price = models.FloatField(initial=0)
    profit = models.FloatField(initial=0)


# FUNCTIONS
def creating_session(subsession: Subsession):
    """Assign roles and private values to all players"""
    players = subsession.get_players()
    n = len(players)

    # Shuffle players for random assignment
    random.shuffle(players)

    # Half buyers, half sellers
    n_buyers = n // 2
    n_sellers = n - n_buyers

    buyers = players[:n_buyers]
    sellers = players[n_buyers:]

    # Assign values to buyers (cycle through if more buyers than values)
    buyer_values = C.BUYER_VALUES.copy()
    random.shuffle(buyer_values)
    for i, p in enumerate(buyers):
        p.role_assigned = 'buyer'
        p.private_value = buyer_values[i % len(buyer_values)]

    # Assign costs to sellers (cycle through if more sellers than costs)
    seller_costs = C.SELLER_COSTS.copy()
    random.shuffle(seller_costs)
    for i, p in enumerate(sellers):
        p.role_assigned = 'seller'
        p.private_value = seller_costs[i % len(seller_costs)]


def calculate_market_outcome(group: Group):
    """
    Call market clearing mechanism:
    - Collect all bids (from buyers) and asks (from sellers)
    - Find market-clearing price
    - Execute trades
    """
    players = group.get_players()

    buyers = [p for p in players if p.role_assigned == 'buyer']
    sellers = [p for p in players if p.role_assigned == 'seller']

    # Sort buyers by bid (highest first) - these are demand
    buyers_sorted = sorted(buyers, key=lambda p: p.bid_or_ask, reverse=True)

    # Sort sellers by ask (lowest first) - these are supply
    sellers_sorted = sorted(sellers, key=lambda p: p.bid_or_ask)

    # Find market-clearing trades
    trades = []
    i, j = 0, 0
    while i < len(buyers_sorted) and j < len(sellers_sorted):
        buyer = buyers_sorted[i]
        seller = sellers_sorted[j]

        if buyer.bid_or_ask >= seller.bid_or_ask:
            # Trade occurs at average of bid and ask
            price = (buyer.bid_or_ask + seller.bid_or_ask) / 2
            trades.append({
                'buyer': buyer,
                'seller': seller,
                'price': price
            })
            i += 1
            j += 1
        else:
            break

    # Execute trades and calculate profits
    total_surplus = 0
    if trades:
        # Use uniform price (average of all trade prices)
        market_price = sum(t['price'] for t in trades) / len(trades)
        group.market_price = market_price
        group.num_trades = len(trades)

        for trade in trades:
            buyer = trade['buyer']
            seller = trade['seller']

            buyer.traded = True
            buyer.trade_price = market_price
            buyer.profit = buyer.private_value - market_price

            seller.traded = True
            seller.trade_price = market_price
            seller.profit = market_price - seller.private_value

            total_surplus += buyer.profit + seller.profit

    # Players who didn't trade get 0 profit
    for p in players:
        if not p.traded:
            p.profit = 0

    group.total_surplus = total_surplus


def get_supply_demand_data(group: Group):
    """Generate data for supply and demand curve visualization"""
    players = group.get_players()

    buyers = [p for p in players if p.role_assigned == 'buyer']
    sellers = [p for p in players if p.role_assigned == 'seller']

    # Demand curve: buyer values sorted descending
    demand_values = sorted([p.private_value for p in buyers], reverse=True)
    demand_curve = []
    for i, val in enumerate(demand_values):
        demand_curve.append({'q': i, 'p': val})
        demand_curve.append({'q': i + 1, 'p': val})

    # Supply curve: seller costs sorted ascending
    supply_costs = sorted([p.private_value for p in sellers])
    supply_curve = []
    for i, cost in enumerate(supply_costs):
        supply_curve.append({'q': i, 'p': cost})
        supply_curve.append({'q': i + 1, 'p': cost})

    # Submitted bids demand curve
    bids = sorted([p.bid_or_ask for p in buyers], reverse=True)
    bid_curve = []
    for i, bid in enumerate(bids):
        bid_curve.append({'q': i, 'p': bid})
        bid_curve.append({'q': i + 1, 'p': bid})

    # Submitted asks supply curve
    asks = sorted([p.bid_or_ask for p in sellers])
    ask_curve = []
    for i, ask in enumerate(asks):
        ask_curve.append({'q': i, 'p': ask})
        ask_curve.append({'q': i + 1, 'p': ask})

    return {
        'demand': demand_curve,
        'supply': supply_curve,
        'bids': bid_curve,
        'asks': ask_curve,
    }


# PAGES
class Instructions(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1


class RoleAssignment(Page):
    timeout_seconds = 60


class Trading(Page):
    form_model = 'player'
    form_fields = ['bid_or_ask']

    @staticmethod
    def vars_for_template(player: Player):
        if player.role_assigned == 'buyer':
            return {
                'role_description': 'BUYER',
                'value_label': 'Your private value for the good',
                'action_label': 'Enter your maximum bid (what you are willing to pay)',
                'hint': 'You profit if you buy at a price below your value.'
            }
        else:
            return {
                'role_description': 'SELLER',
                'value_label': 'Your private cost to produce the good',
                'action_label': 'Enter your minimum ask (what you need to receive)',
                'hint': 'You profit if you sell at a price above your cost.'
            }


class ResultsWaitPage(WaitPage):
    after_all_players_arrive = calculate_market_outcome


class Results(Page):
    @staticmethod
    def vars_for_template(player: Player):
        group = player.group
        return {
            'curves_data': get_supply_demand_data(group),
        }

    @staticmethod
    def js_vars(player: Player):
        group = player.group
        return {
            'curves_data': get_supply_demand_data(group),
            'market_price': group.market_price,
            'num_trades': group.num_trades,
        }


class FinalResults(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == C.NUM_ROUNDS

    @staticmethod
    def vars_for_template(player: Player):
        all_rounds = player.in_all_rounds()
        total_profit = sum(p.profit for p in all_rounds)
        return {
            'total_profit': total_profit,
            'rounds_data': all_rounds,
        }


page_sequence = [Instructions, RoleAssignment, Trading, ResultsWaitPage, Results, FinalResults]
