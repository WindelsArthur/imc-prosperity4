from typing import List, Dict, Any, Tuple
import json
import math
import jsonpickle
from datamodel import Listing, Observation, Order, OrderDepth, ProsperityEncoder, Symbol, Trade, TradingState


class Logger:
    # ... unchanged, keep your existing Logger class ...
    def __init__(self) -> None:
        self.logs = ""
        self.max_log_length = 3750
    def print(self, *objects, sep=" ", end="\n"):
        self.logs += sep.join(map(str, objects)) + end
    def flush(self, state, orders, conversions, trader_data):
        base_length = len(self.to_json([self.compress_state(state, ""), self.compress_orders(orders), conversions, "", ""]))
        max_item_length = (self.max_log_length - base_length) // 3
        print(self.to_json([
            self.compress_state(state, self.truncate(state.traderData, max_item_length)),
            self.compress_orders(orders), conversions,
            self.truncate(trader_data, max_item_length),
            self.truncate(self.logs, max_item_length),
        ]))
        self.logs = ""
    def compress_state(self, state, trader_data):
        return [state.timestamp, trader_data,
                self.compress_listings(state.listings),
                self.compress_order_depths(state.order_depths),
                self.compress_trades(state.own_trades),
                self.compress_trades(state.market_trades),
                state.position,
                self.compress_observations(state.observations)]
    def compress_listings(self, listings):
        return [[l.symbol, l.product, l.denomination] for l in listings.values()]
    def compress_order_depths(self, ods):
        return {s: [o.buy_orders, o.sell_orders] for s, o in ods.items()}
    def compress_trades(self, trades):
        return [[t.symbol, t.price, t.quantity, t.buyer, t.seller, t.timestamp]
                for arr in trades.values() for t in arr]
    def compress_observations(self, obs):
        co = {p: [o.bidPrice, o.askPrice, o.transportFees, o.exportTariff, o.importTariff, o.sugarPrice, o.sunlightIndex]
              for p, o in obs.conversionObservations.items()}
        return [obs.plainValueObservations, co]
    def compress_orders(self, orders):
        return [[o.symbol, o.price, o.quantity] for arr in orders.values() for o in arr]
    def to_json(self, value):
        return json.dumps(value, cls=ProsperityEncoder, separators=(",", ":"))
    def truncate(self, value, max_length):
        lo, hi = 0, min(len(value), max_length)
        out = ""
        while lo <= hi:
            mid = (lo + hi) // 2
            cand = value[:mid]
            if len(cand) < len(value):
                cand += "..."
            if len(json.dumps(cand)) <= max_length:
                out = cand
                lo = mid + 1
            else:
                hi = mid - 1
        return out

logger = Logger()


# ═══════════════════════════════════════════════════════════════════════════
# CONSTANTS 
# ═══════════════════════════════════════════════════════════════════════════
POSITION_LIMIT = 10

PEBBLES = ["PEBBLES_L", "PEBBLES_M", "PEBBLES_S", "PEBBLES_XL", "PEBBLES_XS"]
SNACKPACKS = ["SNACKPACK_CHOCOLATE", "SNACKPACK_PISTACHIO",
              "SNACKPACK_RASPBERRY", "SNACKPACK_STRAWBERRY", "SNACKPACK_VANILLA"]
MICROCHIPS = ["MICROCHIP_CIRCLE", "MICROCHIP_OVAL", "MICROCHIP_RECTANGLE",
              "MICROCHIP_SQUARE", "MICROCHIP_TRIANGLE"]
SLEEP_PODS = ["SLEEP_POD_COTTON", "SLEEP_POD_LAMB_WOOL", "SLEEP_POD_NYLON",
              "SLEEP_POD_POLYESTER", "SLEEP_POD_SUEDE"]
ROBOTS = ["ROBOT_DISHES", "ROBOT_IRONING", "ROBOT_LAUNDRY",
          "ROBOT_MOPPING", "ROBOT_VACUUMING"]
GALAXY = ["GALAXY_SOUNDS_BLACK_HOLES", "GALAXY_SOUNDS_DARK_MATTER",
          "GALAXY_SOUNDS_PLANETARY_RINGS", "GALAXY_SOUNDS_SOLAR_FLAMES",
          "GALAXY_SOUNDS_SOLAR_WINDS"]
OXYGEN = ["OXYGEN_SHAKE_CHOCOLATE", "OXYGEN_SHAKE_EVENING_BREATH",
          "OXYGEN_SHAKE_GARLIC", "OXYGEN_SHAKE_MINT", "OXYGEN_SHAKE_MORNING_BREATH"]
PANELS = ["PANEL_1X2", "PANEL_1X4", "PANEL_2X2", "PANEL_2X4", "PANEL_4X4"]
TRANSLATORS = ["TRANSLATOR_ASTRO_BLACK", "TRANSLATOR_ECLIPSE_CHARCOAL",
               "TRANSLATOR_GRAPHITE_MIST", "TRANSLATOR_SPACE_GRAY", "TRANSLATOR_VOID_BLUE"]
UV_VISORS = ["UV_VISOR_AMBER", "UV_VISOR_MAGENTA", "UV_VISOR_ORANGE",
             "UV_VISOR_RED", "UV_VISOR_YELLOW"]

ALL_PRODUCTS = (PEBBLES + SNACKPACKS + MICROCHIPS + SLEEP_PODS + ROBOTS
                + GALAXY + OXYGEN + PANELS + TRANSLATORS + UV_VISORS)

# Per-product stricter caps (round-2 Phase B bleeders + Phase H PEBBLES_L).
PROD_CAP = {
    "SLEEP_POD_LAMB_WOOL": 10,
    "UV_VISOR_MAGENTA": 4,
    "PANEL_1X2": 3,
    "TRANSLATOR_SPACE_GRAY": 4,
    "ROBOT_MOPPING": 2,
    "PANEL_4X4": 4,
    "GALAXY_SOUNDS_SOLAR_FLAMES": 4,
    "SNACKPACK_RASPBERRY": 10,
    "SNACKPACK_CHOCOLATE": 10,
    "PEBBLES_L": 4,
}

# Basket invariants.
PEBBLES_SUM_TARGET = 50000.0
SNACKPACK_SUM_TARGET = 50221.0
PEBBLES_SKEW_DIVISOR = 8.0
SNACKPACK_SKEW_DIVISOR = 5.0
PEBBLES_SKEW_CLIP = 5.0
SNACKPACK_SKEW_CLIP = 3.0
PEBBLES_BIG_SKEW = 3.5
SNACKPACK_BIG_SKEW = 3.5

# Cointegration pair tilt
PAIR_TILT_DIVISOR = 3.0  
PAIR_TILT_CLIP = 7.0

# Inventory + sizing.
INV_SKEW_BETA = 0.2
QUOTE_BASE_SIZE_CAP = 8
QUOTE_AGGRESSIVE_SIZE = 2

# 9 within-group cointegration pairs
COINT_PAIRS = [
    ("MICROCHIP_RECTANGLE", "MICROCHIP_SQUARE", -0.401, 14119.0),
    ("ROBOT_LAUNDRY", "ROBOT_VACUUMING", 0.334, 7072.0),
    ("SLEEP_POD_COTTON", "SLEEP_POD_POLYESTER", 0.519, 5144.0),
    ("GALAXY_SOUNDS_DARK_MATTER", "GALAXY_SOUNDS_PLANETARY_RINGS", 0.183, 8285.0),
    ("SNACKPACK_RASPBERRY", "SNACKPACK_VANILLA", 0.013, 9962.0),
    ("SNACKPACK_CHOCOLATE", "SNACKPACK_STRAWBERRY", -0.106, 11051.0),
    ("UV_VISOR_AMBER", "UV_VISOR_MAGENTA", -1.238, 21897.0),
    ("TRANSLATOR_ECLIPSE_CHARCOAL", "TRANSLATOR_VOID_BLUE", 0.456, 4954.0),
    ("SLEEP_POD_POLYESTER", "SLEEP_POD_SUEDE", 0.756, 2977.0),
]

# 30 cross-group cointegration pairs
CROSS_GROUP_PAIRS = [
    ("PEBBLES_XL", "PANEL_2X4", 2.4821, -14735.73),
    ("UV_VISOR_AMBER", "SNACKPACK_STRAWBERRY", -2.4501, 34143.94),
    ("PEBBLES_M", "OXYGEN_SHAKE_MORNING_BREATH", -0.9037, 19300.55),
    ("UV_VISOR_YELLOW", "GALAXY_SOUNDS_DARK_MATTER", 1.5837, -5238.83),
    ("OXYGEN_SHAKE_GARLIC", "PEBBLES_S", -1.0114, 20960.00),
    ("PANEL_2X4", "PEBBLES_XL", 0.3093, 7174.37),
    ("MICROCHIP_SQUARE", "SLEEP_POD_SUEDE", 1.8678, -7692.97),
    ("GALAXY_SOUNDS_BLACK_HOLES", "PEBBLES_S", -1.0180, 20559.94),
    ("PEBBLES_S", "GALAXY_SOUNDS_BLACK_HOLES", -0.7694, 17755.06),
    ("PEBBLES_S", "OXYGEN_SHAKE_GARLIC", -0.7727, 18147.25),
    ("SLEEP_POD_POLYESTER", "UV_VISOR_AMBER", -0.9226, 19139.77),
    ("GALAXY_SOUNDS_SOLAR_WINDS", "PANEL_1X4", -0.5377, 15490.30),
    ("PEBBLES_S", "PANEL_2X4", -1.1018, 21344.63),
    ("ROBOT_IRONING", "PEBBLES_M", -0.9154, 18096.05),
    ("PANEL_2X4", "OXYGEN_SHAKE_GARLIC", 0.5545, 4653.12),
    ("GALAXY_SOUNDS_DARK_MATTER", "UV_VISOR_YELLOW", 0.3725, 6144.99),
    ("UV_VISOR_AMBER", "SLEEP_POD_POLYESTER", -0.9595, 19272.87),
    ("PEBBLES_M", "ROBOT_IRONING", -0.7284, 16601.80),
    ("PANEL_2X4", "PEBBLES_S", -0.6242, 16840.75),
    ("SNACKPACK_STRAWBERRY", "SLEEP_POD_POLYESTER", 0.3255, 6852.82),
    ("SNACKPACK_CHOCOLATE", "PANEL_2X4", -0.2171, 12289.62),
    ("SLEEP_POD_SUEDE", "MICROCHIP_SQUARE", 0.4516, 5257.75),
    ("SNACKPACK_STRAWBERRY", "UV_VISOR_AMBER", -0.3259, 13284.98),
    ("TRANSLATOR_ECLIPSE_CHARCOAL", "SLEEP_POD_LAMB_WOOL", -0.5308, 15493.89),
    ("SNACKPACK_VANILLA", "PANEL_1X2", 0.1461, 8793.78),
    ("SNACKPACK_VANILLA", "PANEL_2X4", 0.1490, 8418.80),
    ("SLEEP_POD_LAMB_WOOL", "TRANSLATOR_ECLIPSE_CHARCOAL", -0.7159, 17727.49),
    ("SNACKPACK_PISTACHIO", "OXYGEN_SHAKE_GARLIC", -0.1488, 11269.91),
    ("SNACKPACK_PISTACHIO", "PEBBLES_XS", 0.0992, 8761.10),
    ("SNACKPACK_PISTACHIO", "MICROCHIP_OVAL", 0.0907, 8753.81),
]

ALL_PAIRS = [
    ("MICROCHIP_RECTANGLE", "MICROCHIP_SQUARE", -0.401, 14119.0),
    ("ROBOT_LAUNDRY", "ROBOT_VACUUMING", 0.334, 7072.0),
    ("SLEEP_POD_COTTON", "SLEEP_POD_POLYESTER", 0.519, 5144.0),
    ("GALAXY_SOUNDS_DARK_MATTER", "GALAXY_SOUNDS_PLANETARY_RINGS", 0.183, 8285.0),
    ("SNACKPACK_RASPBERRY", "SNACKPACK_VANILLA", 0.013, 9962.0),
    ("SNACKPACK_CHOCOLATE", "SNACKPACK_STRAWBERRY", -0.106, 11051.0),
    ("UV_VISOR_AMBER", "UV_VISOR_MAGENTA", -1.238, 21897.0),
    ("TRANSLATOR_ECLIPSE_CHARCOAL", "TRANSLATOR_VOID_BLUE", 0.456, 4954.0),
    ("SLEEP_POD_POLYESTER", "SLEEP_POD_SUEDE", 0.756, 2977.0),
    ("PEBBLES_XL", "PANEL_2X4", 2.482227230783029, -14736.627433039512),
    ("PEBBLES_XL", "PANEL_2X4", 2.4820760435062317, -14735.725533064964),
    ("PEBBLES_XL", "PANEL_2X4", 2.4836375314050287, -14734.160489337815),
    ("PEBBLES_XL", "PANEL_2X4", 2.4826780489833116, -14738.740593613664),
    ("PEBBLES_XL", "ROBOT_DISHES", 2.564397695004785, -12461.145043672),
    ("PEBBLES_XL", "ROBOT_DISHES", 2.580310373321849, -12603.173905101849),
    ("UV_VISOR_AMBER", "SNACKPACK_STRAWBERRY", -2.450106587117227, 34143.94273172769),
    ("UV_VISOR_AMBER", "SNACKPACK_STRAWBERRY", -2.4305786726880605, 33927.276302152575),
    ("MICROCHIP_SQUARE", "SLEEP_POD_SUEDE", 1.8491788283254749, -7466.61592831549),
    ("UV_VISOR_AMBER", "SNACKPACK_STRAWBERRY", -2.4491955648629253, 34133.843718037206),
    ("UV_VISOR_AMBER", "SNACKPACK_STRAWBERRY", -2.445794297399974, 34096.17794022894),
    ("PEBBLES_M", "OXYGEN_SHAKE_MORNING_BREATH", -0.9038574030984422, 19302.333841766544),
    ("PEBBLES_M", "OXYGEN_SHAKE_MORNING_BREATH", -0.9045190182030806, 19309.28714080616),
    ("PEBBLES_XL", "ROBOT_DISHES", 2.56069672636587, -12428.06846030326),
    ("PEBBLES_XL", "ROBOT_DISHES", 2.5614599343393354, -12434.873479647302),
    ("PEBBLES_M", "OXYGEN_SHAKE_MORNING_BREATH", -0.9071032460880762, 19337.10366530879),
    ("OXYGEN_SHAKE_GARLIC", "PEBBLES_S", -1.010483289589149, 20961.44090806879),
    ("UV_VISOR_YELLOW", "GALAXY_SOUNDS_DARK_MATTER", 1.5845185234667698, -5246.704444535159),
    ("PEBBLES_M", "OXYGEN_SHAKE_MORNING_BREATH", -0.9036874531311152, 19300.54973077501),
    ("UV_VISOR_YELLOW", "GALAXY_SOUNDS_DARK_MATTER", 1.5837356231428323, -5238.833960878167),
    ("PEBBLES_S", "PANEL_2X4", -1.1002206590772288, 21318.898591715264),
    ("PEBBLES_S", "GALAXY_SOUNDS_BLACK_HOLES", -0.76798793945877, 17729.4059141757),
    ("OXYGEN_SHAKE_GARLIC", "PEBBLES_S", -1.0113818820013512, 20960.12815840001),
    ("OXYGEN_SHAKE_GARLIC", "PEBBLES_S", -1.0114089992229085, 20959.999133310717),
    ("PANEL_2X4", "PEBBLES_XL", 0.309330121132573, 7174.371327549632),
    ("MICROCHIP_SQUARE", "SLEEP_POD_SUEDE", 1.8670373395927784, -7683.937480383369),
    ("MICROCHIP_SQUARE", "SLEEP_POD_SUEDE", 1.864258363987241, -7650.059386742636),
    ("OXYGEN_SHAKE_MORNING_BREATH", "PEBBLES_M", -0.8108942433400526, 18321.206456773343),
    ("OXYGEN_SHAKE_GARLIC", "PEBBLES_S", -1.0112450440377352, 20960.311151434107),
    ("MICROCHIP_SQUARE", "SLEEP_POD_SUEDE", 1.8677787000111792, -7692.96589523037),
    ("PEBBLES_S", "OXYGEN_SHAKE_GARLIC", -0.7727237760193734, 18145.83491576894),
    ("PANEL_2X4", "PEBBLES_XL", 0.3092340069776027, 7175.927154712559),
    ("ROBOT_IRONING", "PEBBLES_M", -0.915306293105909, 18089.46446260394),
    ("GALAXY_SOUNDS_BLACK_HOLES", "PEBBLES_S", -1.0181740113867237, 20561.95579944951),
    ("GALAXY_SOUNDS_BLACK_HOLES", "PEBBLES_S", -1.0179829712021022, 20559.937409828195),
    ("PEBBLES_S", "OXYGEN_SHAKE_GARLIC", -0.7727027691234808, 18147.2455211014),
    ("ROBOT_IRONING", "PEBBLES_M", -0.9153750089182504, 18096.00183821018),
    ("ROBOT_IRONING", "SNACKPACK_PISTACHIO", 3.1878405489502906, -21570.08361929973),
    ("PEBBLES_S", "OXYGEN_SHAKE_GARLIC", -0.7727200834350947, 18147.107658276203),
    ("ROBOT_IRONING", "SNACKPACK_PISTACHIO", 3.187580023317318, -21567.276068616477),
    ("ROBOT_IRONING", "PEBBLES_M", -0.915377205267104, 18095.13357057347),
    ("GALAXY_SOUNDS_BLACK_HOLES", "PEBBLES_S", -1.021242968917232, 20597.39085500036),
    ("PANEL_2X4", "PEBBLES_XL", 0.3075234552606712, 7205.10780576041),
    ("GALAXY_SOUNDS_SOLAR_WINDS", "PANEL_1X4", -0.5393360567523138, 15507.580615623154),
    ("PEBBLES_S", "OXYGEN_SHAKE_GARLIC", -0.7718228093270282, 18127.722946312624),
    ("OXYGEN_SHAKE_MORNING_BREATH", "PEBBLES_M", -0.8133370455047219, 18347.658580190815),
    ("GALAXY_SOUNDS_SOLAR_WINDS", "PANEL_1X4", -0.5376632969240946, 15490.29577772381),
    ("GALAXY_SOUNDS_BLACK_HOLES", "PEBBLES_S", -1.0189105238060594, 20569.713281920063),
    ("OXYGEN_SHAKE_MORNING_BREATH", "PEBBLES_M", -0.813961727499422, 18354.328611592795),
    ("PEBBLES_S", "PANEL_2X4", -1.1017757013394047, 21342.74453333796),
    ("TRANSLATOR_VOID_BLUE", "PEBBLES_XL", 0.2632096393312778, 7382.80711912763),
    ("PEBBLES_S", "PANEL_2X4", -1.1018141700156674, 21344.628762462107),
    ("PEBBLES_S", "PANEL_2X4", -1.1018323889513897, 21344.52984781118),
    ("ROBOT_IRONING", "SNACKPACK_PISTACHIO", 3.1891784028978445, -21584.091457267623),
    ("PANEL_2X4", "PEBBLES_XL", 0.3088604927086312, 7181.9109786943945),
    ("ROBOT_IRONING", "PEBBLES_M", -0.915357931373826, 18096.05464595134),
    ("GALAXY_SOUNDS_SOLAR_WINDS", "PANEL_1X4", -0.5379408297010201, 15493.192458673157),
    ("GALAXY_SOUNDS_SOLAR_WINDS", "PANEL_1X4", -0.5377188512714576, 15490.885614818251),
    ("OXYGEN_SHAKE_MORNING_BREATH", "PEBBLES_M", -0.8138433428288929, 18353.06299334476),
    ("PANEL_2X4", "PEBBLES_S", -0.6236562146290572, 16837.28630631082),
    ("PANEL_2X4", "OXYGEN_SHAKE_GARLIC", 0.5541264229945312, 4658.623237600704),
    ("PANEL_2X4", "OXYGEN_SHAKE_GARLIC", 0.5544637923840529, 4653.115945040127),
    ("PANEL_2X4", "OXYGEN_SHAKE_GARLIC", 0.5543780111137526, 4654.452549226243),
    ("UV_VISOR_AMBER", "PEBBLES_XS", 0.6548059629079153, 3053.6166388613683),
    ("PANEL_2X4", "PEBBLES_XS", -0.3717518232397583, 14018.355830906234),
    ("PANEL_2X4", "PEBBLES_XS", -0.37192066232626, 14019.370633428503),
    ("PEBBLES_M", "ROBOT_IRONING", -0.7289481998161417, 16609.41297806013),
    ("MICROCHIP_CIRCLE", "OXYGEN_SHAKE_CHOCOLATE", 0.7901625693229987, 1663.4791606526774),
    ("PEBBLES_M", "ROBOT_IRONING", -0.7284352781218678, 16601.803879151346),
    ("PEBBLES_M", "ROBOT_IRONING", -0.7284392640470874, 16601.955772478315),
    ("PANEL_2X4", "PEBBLES_S", -0.624170797571384, 16840.749405625695),
    ("PEBBLES_M", "ROBOT_IRONING", -0.728455173325091, 16602.54056515899),
    ("OXYGEN_SHAKE_CHOCOLATE", "MICROCHIP_CIRCLE", 0.8690837811006891, 1550.403811444466),
    ("PANEL_2X4", "PEBBLES_S", -0.6240537370367631, 16839.944282279965),
    ("PANEL_2X4", "PEBBLES_S", -0.623036339105657, 16836.65554768176),
    ("MICROCHIP_CIRCLE", "OXYGEN_SHAKE_CHOCOLATE", 0.7981102802401778, 1587.8057425343873),
    ("PANEL_2X4", "PEBBLES_XS", -0.368433368145386, 13999.24539348717),
    ("MICROCHIP_CIRCLE", "OXYGEN_SHAKE_CHOCOLATE", 0.7885667589069544, 1678.6708134586934),
    ("MICROCHIP_CIRCLE", "OXYGEN_SHAKE_CHOCOLATE", 0.7881501389699975, 1682.6338954266732),
    ("SLEEP_POD_LAMB_WOOL", "TRANSLATOR_ECLIPSE_CHARCOAL", -0.7149291554981798, 17717.704236984522),
    ("PANEL_2X4", "OXYGEN_SHAKE_GARLIC", 0.5528804744003539, 4679.627400194718),
    ("SLEEP_POD_SUEDE", "MICROCHIP_SQUARE", 0.4511103530416515, 5269.195933417363),
    ("SNACKPACK_CHOCOLATE", "PANEL_2X4", -0.2171488594154439, 12289.621446654111),
    ("SNACKPACK_CHOCOLATE", "PANEL_2X4", -0.2193158108161179, 12312.853098352913),
    ("SLEEP_POD_SUEDE", "MICROCHIP_SQUARE", 0.4516141237004989, 5258.074918911748),
    ("SNACKPACK_CHOCOLATE", "PANEL_2X4", -0.2175029414283099, 12293.357509223635),
    ("SLEEP_POD_SUEDE", "MICROCHIP_SQUARE", 0.4516242770887284, 5257.749218242207),
    ("SNACKPACK_CHOCOLATE", "PANEL_2X4", -0.2172128020810646, 12290.287714606307),
    ("SLEEP_POD_SUEDE", "MICROCHIP_SQUARE", 0.4515564561361945, 5259.570197700354),
    ("SNACKPACK_PISTACHIO", "OXYGEN_SHAKE_GARLIC", -0.147048651893191, 11246.923572730424),
    ("TRANSLATOR_ECLIPSE_CHARCOAL", "SLEEP_POD_LAMB_WOOL", -0.5339680362694506, 15527.80489753792),
    ("TRANSLATOR_ECLIPSE_CHARCOAL", "SLEEP_POD_LAMB_WOOL", -0.5307839844057307, 15493.887662403336),
    ("TRANSLATOR_ECLIPSE_CHARCOAL", "SLEEP_POD_LAMB_WOOL", -0.5435586605731771, 15629.520542705448),
    ("ROBOT_MOPPING", "PANEL_1X4", -0.8041442303919017, 18661.30374560096),
    ("GALAXY_SOUNDS_DARK_MATTER", "MICROCHIP_CIRCLE", -0.382383996399042, 13750.252348469883),
    ("SNACKPACK_VANILLA", "PANEL_1X2", 0.1461739394853733, 8793.067253636478),
    ("SNACKPACK_VANILLA", "PANEL_1X2", 0.1476297379597199, 8780.630463694833),
    ("SNACKPACK_VANILLA", "PANEL_1X2", 0.1465195284339851, 8790.086340762948),
    ("SNACKPACK_VANILLA", "PANEL_1X2", 0.1460910242046984, 8793.778855168383),
    ("GALAXY_SOUNDS_DARK_MATTER", "MICROCHIP_CIRCLE", -0.3822618721279026, 13749.153717392825),
    ("SNACKPACK_VANILLA", "PANEL_2X4", 0.1490704816817463, 8418.012472433675),
    ("GALAXY_SOUNDS_DARK_MATTER", "MICROCHIP_CIRCLE", -0.3830073662481682, 13755.889935135174),
    ("SNACKPACK_VANILLA", "PANEL_2X4", 0.1489969745294914, 8418.804623162),
    ("SLEEP_POD_LAMB_WOOL", "TRANSLATOR_ECLIPSE_CHARCOAL", -0.691788660586341, 17493.402899740624),
    ("SLEEP_POD_LAMB_WOOL", "TRANSLATOR_ECLIPSE_CHARCOAL", -0.7159367125345051, 17727.48533024148),
    ("SNACKPACK_PISTACHIO", "OXYGEN_SHAKE_GARLIC", -0.1484589103249383, 11265.790003553157),
    ("SNACKPACK_PISTACHIO", "OXYGEN_SHAKE_GARLIC", -0.1487624807481059, 11269.905145842196),
    ("SNACKPACK_PISTACHIO", "OXYGEN_SHAKE_GARLIC", -0.1486988048797005, 11269.04018668241),
    ("SNACKPACK_PISTACHIO", "PEBBLES_XS", 0.0992245921450982, 8761.100229781694),
    ("SNACKPACK_PISTACHIO", "PEBBLES_XS", 0.0990708884172029, 8761.845169065487),
    ("SNACKPACK_PISTACHIO", "PEBBLES_XS", 0.098254940173902, 8766.249843462334),
    ("SNACKPACK_VANILLA", "PANEL_2X4", 0.1494065264291233, 8414.356524737537),
    ("SNACKPACK_PISTACHIO", "PEBBLES_XS", 0.0991917004079643, 8761.259267734029),
    ("SNACKPACK_PISTACHIO", "ROBOT_IRONING", 0.1862776360787616, 7872.729885405478),
    ("SNACKPACK_VANILLA", "PANEL_2X4", 0.1512741548739461, 8393.873014805138),
    ("SNACKPACK_PISTACHIO", "ROBOT_IRONING", 0.1883702903240081, 7856.615093226784),
    ("SNACKPACK_PISTACHIO", "ROBOT_IRONING", 0.1880313338001796, 7859.236047065387),
    ("SNACKPACK_PISTACHIO", "ROBOT_IRONING", 0.1884660670142343, 7855.870910333828),
    ("SNACKPACK_PISTACHIO", "TRANSLATOR_ASTRO_BLACK", 0.2408654852833257, 7233.30954024455),
]
# ═══════════════════════════════════════════════════════════════════════════
# HELPERS 
# ═══════════════════════════════════════════════════════════════════════════
def _mid(od: OrderDepth):
    if not od or not od.buy_orders or not od.sell_orders:
        return None
    return (max(od.buy_orders) + min(od.sell_orders)) / 2.0


def _best_bid_ask(od: OrderDepth):
    bb = max(od.buy_orders) if (od and od.buy_orders) else None
    ba = min(od.sell_orders) if (od and od.sell_orders) else None
    return bb, ba


def _cap(prod: str) -> int:
    return PROD_CAP.get(prod, POSITION_LIMIT)


def _clip(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _compute_mids(state: TradingState) -> Dict[str, float]:
    mids = {}
    for p in ALL_PRODUCTS:
        m = _mid(state.order_depths.get(p))
        if m is not None:
            mids[p] = m
    return mids


def _basket_skew(prod: str, mids: Dict[str, float]) -> float:
    """PEBBLES Σ=50,000 and SNACKPACK Σ=50,221 invariant skew."""
    if prod in PEBBLES and all(p in mids for p in PEBBLES):
        resid = sum(mids[p] for p in PEBBLES) - PEBBLES_SUM_TARGET
        return _clip(-resid / PEBBLES_SKEW_DIVISOR, -PEBBLES_SKEW_CLIP, PEBBLES_SKEW_CLIP)
    if prod in SNACKPACKS and all(p in mids for p in SNACKPACKS):
        resid = sum(mids[p] for p in SNACKPACKS) - SNACKPACK_SUM_TARGET
        return _clip(-resid / SNACKPACK_SKEW_DIVISOR, -SNACKPACK_SKEW_CLIP, SNACKPACK_SKEW_CLIP)
    return 0.0


def _pair_skews_all(mids: Dict[str, float]) -> Dict[str, float]:
    """Sum cointegration tilts across all pairs into per-product skew."""
    out: Dict[str, float] = {}
    for a, b, slope, intercept in ALL_PAIRS:
        if a not in mids or b not in mids:
            continue
        spread_val = mids[a] - slope * mids[b] - intercept
        tilt = _clip(-spread_val / PAIR_TILT_DIVISOR, -PAIR_TILT_CLIP, PAIR_TILT_CLIP)
        out[a] = out.get(a, 0.0) + tilt
        out[b] = out.get(b, 0.0) - slope * tilt / max(abs(slope), 1.0)
    return out


def _is_aggressive(prod: str, basket_skew: float) -> Tuple[bool, bool]:
    """Big-cross flags: (long_aggressive, short_aggressive) on basket residual size."""
    if prod in PEBBLES:
        return basket_skew >= PEBBLES_BIG_SKEW, basket_skew <= -PEBBLES_BIG_SKEW
    if prod in SNACKPACKS:
        return basket_skew >= SNACKPACK_BIG_SKEW, basket_skew <= -SNACKPACK_BIG_SKEW
    return False, False


def _fair(prod: str, mids: Dict[str, float], pair_skews: Dict[str, float], pos: int) -> Tuple[float, float]:
    """Total fair value = mid + basket_skew + pair_skew + inv_skew.
    Returns (fair, basket_skew_only) so trade() can decide aggressive crossing."""
    if prod not in mids:
        return None, 0.0
    bsk = _basket_skew(prod, mids)
    psk = pair_skews.get(prod, 0.0)
    inv = -pos * INV_SKEW_BETA
    fair = mids[prod] + bsk + psk + inv
    return fair, bsk


# ═══════════════════════════════════════════════════════════════════════════
# Trader 
# ═══════════════════════════════════════════════════════════════════════════
class Trader:

    def takes(self, prod, od, fair, basket_skew, pos, lim, cap):
        """Aggressive crossing only when basket invariant is far. Returns
        (take_orders, bought, sold) — bought/sold consume cap inside trade()."""
        orders: List[Order] = []
        bought = 0
        sold = 0
        big_long, big_short = _is_aggressive(prod, basket_skew)
        bb, ba = _best_bid_ask(od)
        if bb is None or ba is None:
            return orders, bought, sold

        buy_left = min(lim - pos, cap - pos)
        sell_left = min(lim + pos, cap + pos)

        if big_long and buy_left > 0:
            size = min(QUOTE_AGGRESSIVE_SIZE, buy_left)
            orders.append(Order(prod, ba, size))
            bought += size
        if big_short and sell_left > 0:
            size = min(QUOTE_AGGRESSIVE_SIZE, sell_left)
            orders.append(Order(prod, bb, -size))
            sold += size
        return orders, bought, sold
    
    def clean_book_after_takes(self, od: OrderDepth, takes: List[Order]):
        for o in takes:
            if o.quantity > 0:  
                od.sell_orders[o.price] = od.sell_orders.get(o.price, 0) + o.quantity
                if od.sell_orders[o.price] >= 0:
                    del od.sell_orders[o.price]
            else:
                od.buy_orders[o.price] = od.buy_orders.get(o.price, 0) + o.quantity
                if od.buy_orders[o.price] <= 0:
                    del od.buy_orders[o.price]

    def make(self, prod, od, fair, buy_cap, sell_cap, pos):
        """Passive quotes inside the spread, gated on fair sanity."""
        bb, ba = _best_bid_ask(od)
        if bb is None or ba is None or ba - bb < 1:
            return []

        inside = ba - bb >= 2
        bid_px = bb + 1 if inside else bb
        ask_px = ba - 1 if inside else ba

        size_buy  = min(QUOTE_BASE_SIZE_CAP, max(buy_cap,  0))
        size_sell = min(QUOTE_BASE_SIZE_CAP, max(sell_cap, 0))

        orders = []
        if size_buy  and fair > bid_px - 0.25: orders.append(Order(prod, bid_px, size_buy))
        if size_sell and fair < ask_px + 0.25: orders.append(Order(prod, ask_px, -size_sell))
        return orders

    def trade(self, prod, state, mids, pair_skews):
        od = state.order_depths.get(prod)
        if od is None or not od.buy_orders or not od.sell_orders:
            return []

        pos = state.position.get(prod, 0)
        lim = POSITION_LIMIT
        cap = _cap(prod)

        fair, basket_skew = _fair(prod, mids, pair_skews, pos)
        if fair is None:
            return []

        # takes (aggressive cross on big basket residual)
        take_orders, bought, sold = self.takes(prod, od, fair, basket_skew, pos, lim, cap)

        # clean book so make() can see updated best bid/ask and avoid self-crossing
        self.clean_book_after_takes(od, take_orders)
        
        # make (passive inside-spread, accounting for whatever takes consumed)
        buy_cap = max(min(lim - pos, cap - pos) - bought, 0)
        sell_cap = max(min(lim + pos, cap + pos) - sold, 0)
        make_orders = self.make(prod, od, fair, buy_cap, sell_cap, pos)

        return take_orders + make_orders

    def run(self, state: TradingState):
        result: Dict[str, List[Order]] = {}
        td = jsonpickle.decode(state.traderData) if state.traderData else {}

        # Compute per-tick state ONCE for all products.
        mids = _compute_mids(state)
        pair_skews = _pair_skews_all(mids)

        for prod in ALL_PRODUCTS:
            orders = self.trade(prod, state, mids, pair_skews)
            if orders:
                result[prod] = orders

        trader_data = jsonpickle.encode(td)
        logger.flush(state, result, 0, trader_data)
        return result, 0, trader_data