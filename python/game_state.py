"""Catnip Cauldron - the game's brain (Python).

HOW THIS FILE WORKS
-------------------
Python owns every game RULE: what can be planted, how plants grow, what is in
the backpack. JavaScript only DRAWS things (art, animations, clicks).

  JavaScript click  ->  Python rule function  ->  Python calls a JS "bridge"
                                                  function to update the screen

Bridge functions (provided by js/main.js before this file runs):

  drawPlot(position, plant, stage)      draw one garden plot (plant=None -> empty)
  updateInventory(json_text)            backpack contents + hash table details
  updateCoins(coins)                    coin counter
  updateDay(day, weather, symbol, forecast)   day / weather display
  updateUndo(count, label)              enable / disable the Undo button
  updateShop(json_text)                 what the Shop window lists
  updateHerbarium(json_text)            what the Herbarium book shows
  updateMap(json_text)                  what the Map window shows
  updateCauldron(json_text)             what the Cauldron window shows
  updateLevel(level, xp_in, xp_next, up)  the level badge in the top bar
  levelUpFx(level, unlocks_json)        the level-up celebration card
  playSound(name)                       play a sound effect (a missing sound file is simply silent)
  showCodeResult(text, worked)          the answer under the "Secret code" box in Settings
  startEasterEgg(lines_json)            the hidden easter egg: Nyra senses something, then the minigame starts
  showEggWelcome(lines_json)            Nyra welcomes the player back on the home screen after beating it
  setMessage(text)                      status message
  showDialogue(text, face, mouth)       Nyra speaks (face: happy / passive / blush)

LESSON MAP  (each section below is tagged with its lesson)
----------------------------------------------------------
  Lesson 1   OOP, Big O, Stacks ......... Plant class + the Undo history stack
  Lesson 2   Queues and Deques .......... the weather / sky queue (Skip Time: day <-> night)
  Lesson 3   2D lists ................... the 5x5 garden grid
  Lesson 4   Trees and traversals ....... Herbarium categories (DFS with a stack, BFS with a queue)
  Lesson 5   Binary search trees ........ the entry catalog (A-Z order)
  Lesson 6   Hash tables ................ the backpack (chaining + rehashing) and the Cauldron's recipe book
  Lesson 7   Graphs, BFS / DFS .......... the Map of places (scouting with a queue or a stack)
  Lesson 8   Sorting algorithms ......... Shop and Backpack sorting (5 algorithms)
  Lesson 9   Searching algorithms ....... Herbarium search (linear, binary, BST)
  Lesson 10  Dijkstra and greedy ........ the Map: cheapest route + errand trips
  Lesson 11  Dynamic programming ........ the Cauldron: Nyra suggests the most profitable brew
  Lesson 12  Resource management ........ coins, seeds, buying and selling

The words inside the Herbarium book are in herbarium_data.py (loaded first).
"""
import heapq
import itertools
import json
import random
from collections import deque


# =====================================================================
# LESSON 1: OOP - plants are objects
# Each kind of plant is an object that carries its own facts.
# =====================================================================
class Plant:
    """One kind of plant the player can grow."""

    def __init__(self, name, grow_days, coin_value, seed_cost, likes, unlock_level=1):
        self.name = name
        self.grow_days = grow_days      # about how many full days (day + night) it needs to grow
        self.coin_value = coin_value    # what a harvested plant sells for
        self.seed_cost = seed_cost      # what a seed costs to buy
        self.likes = likes              # the time of day it grows best in: "Day" or "Night"
        self.unlock_level = unlock_level    # the player level at which its seed appears in the Shop

    @property
    def xp(self):
        """XP for harvesting one: slower plants are worth more."""
        return self.grow_days * 3

    @property
    def growth_needed(self):
        """Growth points needed before it can be harvested (see GROWTH_PER_DAY)."""
        return self.grow_days * GROWTH_PER_DAY


GROWTH_PER_DAY = 3      # points a plant earns over one Day + one Night under an ordinary sky

PLANT_CATALOG = {          # "likes" follows the Herbarium: moon and star flowers open at night, SunPetal and HeartBlossom by day
    plant.name: plant
    for plant in [
        Plant("MoonCatnip", grow_days=2, coin_value=6, seed_cost=3, likes="Night", unlock_level=1),
        Plant("MoonBell", grow_days=3, coin_value=9, seed_cost=4, likes="Night", unlock_level=3),
        Plant("SunPetal", grow_days=2, coin_value=7, seed_cost=3, likes="Day", unlock_level=1),
        Plant("HeartBlossom", grow_days=3, coin_value=10, seed_cost=5, likes="Day", unlock_level=3),
        Plant("Frostmint", grow_days=2, coin_value=8, seed_cost=4, likes="Night", unlock_level=2),
        Plant("StarBloom", grow_days=4, coin_value=14, seed_cost=6, likes="Night", unlock_level=5),
    ]
}


# =====================================================================
# LESSON 12: Resource management - coins
# Seeds and harvested plants are resources too, but they live in the
# backpack hash table (Lesson 6) because there is one count PER plant.
# =====================================================================
class GardenResources:
    def __init__(self, coins):
        self.coins = coins

    def can_afford(self, cost):
        return self.coins >= cost

    def spend_coins(self, amount):
        self.coins -= amount            # O(1)

    def gain_coins(self, amount):
        self.coins += amount            # O(1)


resources = GardenResources(coins=20)


# =====================================================================
# LEVELS (progress): XP comes from harvesting, brewing, new Herbarium pages and new places on the Map.
# Each plant and potion has an unlock_level, so the Shop and the Cauldron open up as you play.
# Edit LEVEL_XP and the unlock_level numbers above to change the pacing.
# =====================================================================
LEVEL_XP = [0, 20, 50, 90, 140, 200]      # total XP needed to REACH level 1, 2, 3 ...
MAX_LEVEL = len(LEVEL_XP)
DISCOVERY_XP = 10                          # bonus for a brand-new Herbarium page
MAP_PLACE_XP = 4                           # for finding a new place on the Map


class PlayerLevel:
    def __init__(self):
        self.xp = 0
        self.level = 1

    def gain(self, amount):
        """Add XP. Returns the list of levels just reached (can be several at once)."""
        self.xp += amount
        reached = []
        while self.level < MAX_LEVEL and self.xp >= LEVEL_XP[self.level]:
            self.level += 1
            reached.append(self.level)
        return reached

    def take_back(self, amount):
        """Undo gives XP back, but never costs a level (so unlocked things stay unlocked)."""
        self.xp = max(self.xp - amount, LEVEL_XP[self.level - 1])

    def xp_into_level(self):
        return self.xp - LEVEL_XP[self.level - 1]

    def xp_for_next(self):
        """XP needed to finish this level, or 0 at the top level."""
        return 0 if self.level >= MAX_LEVEL else LEVEL_XP[self.level] - LEVEL_XP[self.level - 1]


player = PlayerLevel()


# =====================================================================
# LESSON 6: Hash tables - the backpack
# Key = item name like "seed:MoonCatnip", value = how many you own.
# index = (sum of letter codes) % table size.
# Collisions use SEPARATE CHAINING: every slot is a little list (a chain).
# When the table gets too full (load factor > 0.75) it grows to the next
# prime size and every item is hashed again (REHASHING).
# Big O: add / get / remove are O(1) on average (O(n) if one chain gets long).
# =====================================================================
def is_prime(number):
    if number < 2:
        return False
    divisor = 2
    while divisor * divisor <= number:
        if number % divisor == 0:
            return False
        divisor += 1
    return True


def next_prime(number):
    while not is_prime(number):
        number += 1
    return number


class InventoryHashTable:
    def __init__(self, size=5, max_load=0.75):
        self.size = size
        self.max_load = max_load
        self.count = 0              # how many different items are stored
        self.collisions = 0
        self.rehashes = 0
        self.events = []            # short history shown in "Peek inside"
        self.table = [[] for _ in range(size)]

    def hash_function(self, key):
        total = 0
        for letter in key.lower():
            total += ord(letter)
        return total % self.size

    def load_factor(self):
        return self.count / self.size

    def get(self, key):
        """How many of this item do we own? (0 if none)"""
        for item in self.table[self.hash_function(key)]:
            if item[0] == key:
                return item[1]
        return 0

    def add(self, key, amount=1):
        index = self.hash_function(key)
        for item in self.table[index]:
            if item[0] == key:
                item[1] += amount
                return
        if self.table[index]:                       # slot already used -> collision
            self.collisions += 1
            self.events.append(f"Collision! {key} and {self.table[index][0][0]} both hash to slot {index} (chained)")
        self.table[index].append([key, amount])
        self.count += 1
        if self.load_factor() > self.max_load:
            self.rehash()

    def remove(self, key, amount=1):
        """Take some away. Returns False (and changes nothing) if we don't have enough."""
        chain = self.table[self.hash_function(key)]
        for item in chain:
            if item[0] == key:
                if item[1] < amount:
                    return False
                item[1] -= amount
                if item[1] == 0:
                    chain.remove(item)
                    self.count -= 1
                return True
        return False

    def rehash(self):
        old_table, old_size, old_load = self.table, self.size, self.load_factor()
        self.size = next_prime(old_size * 2)
        self.table = [[] for _ in range(self.size)]
        for chain in old_table:                     # every item must be hashed AGAIN
            for item in chain:                      # because the size changed
                self.table[self.hash_function(item[0])].append(item)
        self.rehashes += 1
        self.events.append(f"Load factor {round(old_load, 2)} > {self.max_load}: REHASH {old_size} -> {self.size} slots")

    def items_with_prefix(self, prefix):
        """All (name, count) pairs whose key starts with prefix, e.g. "seed:"."""
        found = []
        for chain in self.table:
            for key, amount in chain:
                if key.startswith(prefix):
                    found.append((key[len(prefix):], amount))
        return found

    def details(self):
        return {
            "size": self.size,
            "count": self.count,
            "load_factor": round(self.load_factor(), 2),
            "max_load": self.max_load,
            "collisions": self.collisions,
            "rehashes": self.rehashes,
            "slots": [[f"{key} x{amount}" for key, amount in chain] for chain in self.table],
            "events": self.events[-6:],
        }


def seed_key(plant_name):
    return "seed:" + plant_name


def plant_key(plant_name):
    return "plant:" + plant_name


backpack = InventoryHashTable()
backpack.add(seed_key("MoonCatnip"), 3)      # the player starts with just three MoonCatnip seeds; the rest are unlocked by leveling up


# =====================================================================
# LESSON 8: Sorting algorithms - used by the Shop and the Backpack
# Every sorter gets a list of (key, item) pairs and returns the sorted pairs
# plus how many COMPARISONS it needed, so the game can show the difference.
#   Bubble / Insertion / Selection: O(n^2)     Merge / Quick: O(n log n)
# =====================================================================
def bubble_sort(pairs):
    """Swap neighbours that are out of order, again and again. O(n^2) (O(n) if already sorted)."""
    pairs = pairs[:]
    comparisons = 0
    for end in range(len(pairs) - 1, 0, -1):
        swapped = False
        for i in range(end):
            comparisons += 1
            if pairs[i][0] > pairs[i + 1][0]:
                pairs[i], pairs[i + 1] = pairs[i + 1], pairs[i]
                swapped = True
        if not swapped:
            break
    return pairs, comparisons


def insertion_sort(pairs):
    """Pick up each item and slide it into place among the sorted ones. O(n^2)."""
    pairs = pairs[:]
    comparisons = 0
    for i in range(1, len(pairs)):
        current = pairs[i]
        j = i - 1
        while j >= 0:
            comparisons += 1
            if pairs[j][0] > current[0]:
                pairs[j + 1] = pairs[j]
                j -= 1
            else:
                break
        pairs[j + 1] = current
    return pairs, comparisons


def selection_sort(pairs):
    """Find the smallest item left, put it next in line. O(n^2)."""
    pairs = pairs[:]
    comparisons = 0
    for i in range(len(pairs)):
        smallest = i
        for j in range(i + 1, len(pairs)):
            comparisons += 1
            if pairs[j][0] < pairs[smallest][0]:
                smallest = j
        pairs[i], pairs[smallest] = pairs[smallest], pairs[i]
    return pairs, comparisons


def merge_sort(pairs):
    """Split in half, sort each half, merge them back. O(n log n)."""
    if len(pairs) <= 1:
        return pairs[:], 0
    middle = len(pairs) // 2
    left, left_count = merge_sort(pairs[:middle])
    right, right_count = merge_sort(pairs[middle:])
    merged, i, j = [], 0, 0
    comparisons = left_count + right_count
    while i < len(left) and j < len(right):
        comparisons += 1
        if left[i][0] <= right[j][0]:
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1
    merged += left[i:]
    merged += right[j:]
    return merged, comparisons


def quick_sort(pairs):
    """Pick a pivot, put smaller items on one side and bigger on the other. O(n log n) on average."""
    if len(pairs) <= 1:
        return pairs[:], 0
    pivot = pairs[len(pairs) // 2][0]
    smaller, equal, bigger = [], [], []
    comparisons = 0
    for pair in pairs:
        comparisons += 1
        if pair[0] < pivot:
            smaller.append(pair)
        else:
            comparisons += 1
            if pair[0] > pivot:
                bigger.append(pair)
            else:
                equal.append(pair)
    sorted_smaller, smaller_count = quick_sort(smaller)
    sorted_bigger, bigger_count = quick_sort(bigger)
    return sorted_smaller + equal + sorted_bigger, comparisons + smaller_count + bigger_count


SORT_ALGORITHMS = {
    "Merge Sort": (merge_sort, "O(n log n)"),
    "Quick Sort": (quick_sort, "O(n log n) on average"),
    "Insertion Sort": (insertion_sort, "O(n²)"),
    "Selection Sort": (selection_sort, "O(n²)"),
    "Bubble Sort": (bubble_sort, "O(n²)"),
}


def sort_key(value):
    return value.lower() if isinstance(value, str) else value     # "apple" and "Apple" count the same


def sort_items(items, field, algorithm="Merge Sort", descending=False):
    """Sort a list of dictionaries by one field. Returns (sorted_list, comparisons)."""
    if algorithm not in SORT_ALGORITHMS:
        algorithm = "Merge Sort"
    sorter = SORT_ALGORITHMS[algorithm][0]
    pairs = [(sort_key(item[field]), item) for item in items]
    ordered, comparisons = sorter(pairs)
    result = [item for _, item in ordered]
    if descending:
        result.reverse()
    return result, comparisons


backpack_sort = {"field": "name", "algorithm": "Merge Sort", "descending": False}


def inventory_json():
    """Everything the backpack window needs, as text for JavaScript."""
    view = backpack_sort
    seeds, seed_comparisons = sort_items(
        [{"name": n, "count": c} for n, c in backpack.items_with_prefix("seed:")],
        view["field"], view["algorithm"], view["descending"])
    plants, plant_comparisons = sort_items(
        [{"name": n, "count": c} for n, c in backpack.items_with_prefix("plant:")],
        view["field"], view["algorithm"], view["descending"])
    potions, potion_comparisons = sort_items(
        [{"name": n, "count": c} for n, c in backpack.items_with_prefix("potion:")],
        view["field"], view["algorithm"], view["descending"])
    return json.dumps({
        "seeds": seeds,
        "plants": plants,
        "potions": potions,
        "table": backpack.details(),
        "sort": {**view, "big_o": SORT_ALGORITHMS[view["algorithm"]][1],
                 "seeds_comparisons": seed_comparisons, "plants_comparisons": plant_comparisons,
                 "potions_comparisons": potion_comparisons},
    })


# =====================================================================
# LESSON 2: Queues - the weather forecast
# A queue is "first in, first out": tomorrow's weather waits at the front.
# We use deque (double-ended queue) so removing from the front is O(1);
# a normal list would have to shift every item (O(n)).
# =====================================================================
WEATHER = {          # what the sky is like RIGHT NOW (a clear sky is "Sunny" by day and a "Starry night" at night)
    "Sunny":        {"symbol": "☀", "line": "A sunny sky! Sun plants soak it up."},
    "Cloudy":       {"symbol": "☁", "line": "A cloudy, calm sky."},
    "Rainy":        {"symbol": "☂", "line": "Rain! Every plant grows extra."},
    "Starry night": {"symbol": "★", "line": "A starry night! Moon and Star plants glow and grow extra."},
    "Cold snap":    {"symbol": "❄", "line": "A cold snap! Only Frostmint keeps growing."},
}
SKY_CHOICES = ["Clear", "Clear", "Cloudy", "Rainy", "Cold snap"]     # what can join the forecast queue (Clear is the likeliest)


def weather_name_for(sky, time_of_day):
    """The queue holds the SKY for each coming time slot. A clear sky looks different by day and by night."""
    if sky == "Clear":
        return "Sunny" if time_of_day == "Day" else "Starry night"
    return sky


def other_time(time_of_day):
    return "Night" if time_of_day == "Day" else "Day"


def scene_for(weather_name, time_of_day):
    """Which planting-area picture to show. Rain looks the same by day and by night."""
    if weather_name == "Rainy":
        return "rain"
    if time_of_day == "Night":
        return "starry" if weather_name == "Starry night" else "night"
    return "day"


def growth_for(weather_name, time_of_day, plant_name):
    """How many growth points this plant earns in ONE time slot (a Day or a Night)."""
    if weather_name == "Cold snap":
        return 3 if plant_name == "Frostmint" else 0              # only Frostmint loves the cold
    points = 2 if PLANT_CATALOG[plant_name].likes == time_of_day else 1     # grows best in its favourite time
    if weather_name == "Rainy":
        points += 1
    if weather_name == "Starry night" and ("Moon" in plant_name or "Star" in plant_name):
        points += 1
    return points


class ClimateQueue:
    def __init__(self):
        self.events = deque()

    def add_event(self, event):
        self.events.append(event)              # O(1) - join the back of the line

    def process_event(self):
        if self.events:
            return self.events.popleft()       # O(1) - leave from the front
        return None

    def upcoming(self, how_many):
        return list(self.events)[:how_many]


# The queue holds the sky for each COMING time slot (night, day, night, day ...), in order.
climate = ClimateQueue()
for _event in ["Cloudy", "Rainy", "Clear", "Clear", "Cloudy"]:
    climate.add_event(_event)

day = 1
time_of_day = "Day"            # "Day" or "Night": each press of Skip Time moves to the other one
today_weather = "Sunny"        # the sky right now (see weather_name_for)


# =====================================================================
# LESSON 1: Stacks - the Undo history
# A stack is "last in, first out": the newest action sits on top, so Undo
# always reverses the most recent thing. Big O: push, pop and peek are O(1).
# =====================================================================
class ActionHistoryStack:
    def __init__(self):
        self.stack = []

    def push_action(self, action):
        self.stack.append(action)              # O(1)

    def pop_action(self):
        return self.stack.pop() if self.stack else None     # O(1)

    def peek_action(self):
        return self.stack[-1] if self.stack else None       # O(1)

    def size(self):
        return len(self.stack)

    def clear(self):
        self.stack = []


history = ActionHistoryStack()


# =====================================================================
# LESSON 3: 2D lists - the 5x5 garden grid
# garden_grid[row][column] is None for an empty plot, or a dictionary like
# {"plant": "MoonCatnip", "stage": "early", "growth": 1} when growing.
# Big O: reading or writing one plot is O(1) - we jump straight to it.
# =====================================================================
GRID_SIZE = 5

garden_grid = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]


def position_to_cell(position):
    """Turn a plot number (0-24, left to right, top to bottom) into (row, column)."""
    return position // GRID_SIZE, position % GRID_SIZE


def has_plot(position):
    """True when the position is a real plot (the game sends -1 for 'none chosen')."""
    return position is not None and 0 <= position < GRID_SIZE * GRID_SIZE


def get_plot(position):
    row, column = position_to_cell(position)
    return garden_grid[row][column]


def set_plot(position, plot):
    row, column = position_to_cell(position)
    garden_grid[row][column] = plot


def redraw_plot(position):
    plot = get_plot(position)
    if plot is None:
        drawPlot(position, None, "empty")
    else:
        drawPlot(position, plot["plant"], plot["stage"])


# ---------- small helpers that keep the screen in sync ----------
def refresh_inventory_ui():
    updateInventory(inventory_json())


def refresh_coins_ui():
    updateCoins(resources.coins)


def forecast_text(how_many=3):
    """'Cloudy (night), Rainy (day), Starry night (night)' - the next time slots in order."""
    slots, time_slot = [], time_of_day
    for sky in climate.upcoming(how_many):
        time_slot = other_time(time_slot)
        slots.append(f"{weather_name_for(sky, time_slot)} ({time_slot.lower()})")
    return "Coming up: " + ", ".join(slots)


def refresh_day_ui():
    updateDay(day, today_weather, WEATHER[today_weather]["symbol"], forecast_text(),
              time_of_day, scene_for(today_weather, time_of_day))


def refresh_undo_ui():
    top = history.peek_action()
    updateUndo(history.size(), top["label"] if top else "")


# =====================================================================
# GAME RULES - these tie the lessons together.
# JavaScript calls these when the player clicks.
# =====================================================================
def start_game():
    """Called once when the game finishes loading."""
    refresh_inventory_ui()
    refresh_coins_ui()
    refresh_day_ui()
    refresh_undo_ui()
    refresh_herbarium_ui()
    refresh_map_ui()
    refresh_level_ui()


def inspect_plot(position):
    """The player selected a plot - say what is in it."""
    if not has_plot(position):
        return
    plot = get_plot(position)
    if plot is None:
        setMessage(f"Plot {position + 1} is ready for a seed.")
        return
    plant = PLANT_CATALOG[plot["plant"]]
    if plot["stage"] == "grown":
        setMessage(f"Plot {position + 1}: {plant.name} is ready to harvest!")
    else:
        setMessage(f"Plot {position + 1}: {plant.name} is growing ({plot['growth']}/{plant.growth_needed}). It grows best at {plant.likes.lower()}.")


def refresh_level_ui(leveled_up=False):
    updateLevel(player.level, player.xp_into_level(), player.xp_for_next(), leveled_up)


def unlocks_for_level(level):
    """What opens up at exactly this level, as readable names."""
    things = [f"{plant.name} seeds" for plant in PLANT_CATALOG.values() if plant.unlock_level == level]
    things += [f"the {potion.name} recipe" for potion in POTION_CATALOG.values() if potion.unlock_level == level]
    return things


def award_xp(amount):
    """Give XP; if that reaches a new level, celebrate and say what just opened up."""
    reached = player.gain(amount)
    refresh_level_ui(bool(reached))
    if not reached:
        return
    things = [thing for level in reached for thing in unlocks_for_level(level)]
    top = reached[-1]
    if things:
        text = f"Level {top}! New in the Shop and Cauldron: {', '.join(things)}."
    else:
        text = f"Level {top}! I feel stronger already!"
    setMessage(text)
    showDialogue(text, "happy", "open")
    levelUpFx(top, json.dumps(things))
    playSound("levelup")


# =====================================================================
# NYRA'S REACTIONS
# Every plant has its own little personality: 3 lines for planting it, harvesting it and
# pulling it out. Each line is (what she says, face, mouth). She never says the same line
# twice in a row. Clicking Nyra herself also makes her react (see nyra_poke).
# =====================================================================
PLANT_REACTIONS = {
    "MoonCatnip": {
        "plant": [
            ("MoonCatnip!! My tail is already swishing... sleep well, little one!", "happy", "open"),
            ("Mrrp~ Don't mind me, I'm just trying very hard not to roll in the soil.", "blush", "open"),
            ("Moon-kissed catnip, coming right up!", "happy", "open"),
        ],
        "harvest": [
            ("Fresh MoonCatnip! ...I'll only sniff it a LITTLE. Okay, maybe a lot.", "blush", "open"),
            ("Got it! My tail says this one is perfect.", "happy", "open"),
            ("So fluffy and fragrant! The Shop can wait... a minute.", "passive", "open"),
        ],
        "remove": [
            ("Back to the seed pouch, catnip. We'll try again, okay?", "passive", "closed"),
            ("Shhh, little MoonCatnip, go back to sleep.", "passive", "closed"),
            ("Mrr... I'll keep this seed safe in my pouch.", "passive", "closed"),
        ],
    },
    "MoonBell": {
        "plant": [
            ("Ding-a-ling! Grow tall and ring for the moon, little bell.", "happy", "open"),
            ("A MoonBell seed... so delicate. Sweet dreams!", "passive", "closed"),
            ("Planting a MoonBell! It likes the cool night air best.", "happy", "open"),
        ],
        "harvest": [
            ("It chimed when I picked it! ...or maybe I imagined that.", "happy", "open"),
            ("A MoonBell, glowing softly. So pretty!", "happy", "open"),
            ("Careful, careful... there. Not a single petal bent.", "passive", "open"),
        ],
        "remove": [
            ("Sorry, little bell, back in the pouch for now.", "passive", "closed"),
            ("Shh... the MoonBell will bloom another night.", "passive", "closed"),
            ("Tucking this bell seed in, safe and sound.", "passive", "closed"),
        ],
    },
    "SunPetal": {
        "plant": [
            ("SunPetal! Soak up all the sunshine, okay?", "happy", "open"),
            ("A little ray of sunshine, going into the soil!", "happy", "open"),
            ("Plant by day, grow by day. You'll be golden!", "happy", "open"),
        ],
        "harvest": [
            ("Warm and glowing like a tiny sun! Nice work, little petal!", "happy", "open"),
            ("Ooh, it's warm in my hands! I like it.", "happy", "open"),
            ("A SunPetal, picked at its brightest.", "passive", "open"),
        ],
        "remove": [
            ("Back in the pouch, sunshine. We'll find you a better spot.", "passive", "closed"),
            ("Aww, no sun for you today...", "passive", "closed"),
            ("Into the seed pouch, nice and cozy.", "passive", "closed"),
        ],
    },
    "HeartBlossom": {
        "plant": [
            ("A HeartBlossom! ...Why are my cheeks warm?", "blush", "open"),
            ("Plant it with love, grow it with love!", "happy", "open"),
            ("A little heart for our garden. Bloom nicely, okay?", "happy", "open"),
        ],
        "harvest": [
            ("A whole heart in my hands... I'm not blushing, YOU are!", "blush", "open"),
            ("So soft and so pink! HeartBlossoms are the best.", "happy", "open"),
            ("Picked with the gentlest paws. Not one petal torn!", "happy", "open"),
        ],
        "remove": [
            ("Sorry, HeartBlossom! I'll plant you somewhere lovely soon.", "passive", "closed"),
            ("Oh... back in the pouch, little heart.", "passive", "closed"),
            ("Don't be sad, you'll bloom later. I promise.", "passive", "closed"),
        ],
    },
    "Frostmint": {
        "plant": [
            ("Frostmint! Cool, calm, and very refreshing.", "happy", "open"),
            ("Brrr, even the seed feels chilly. Grow strong!", "happy", "open"),
            ("Planting something minty and cool... mrrp, my nose tingles!", "happy", "open"),
        ],
        "harvest": [
            ("Crisp and icy! My nose is tingling already.", "happy", "open"),
            ("A fresh Frostmint! It smells like a winter morning.", "happy", "open"),
            ("Brr! So cold on my fingertips, but so lovely.", "passive", "open"),
        ],
        "remove": [
            ("Back to the seed pouch you go, Frostmint. Stay cool!", "passive", "closed"),
            ("Into the pouch, nice and chilly.", "passive", "closed"),
            ("Pausing the frost. We'll plant you again soon!", "passive", "closed"),
        ],
    },
    "StarBloom": {
        "plant": [
            ("A StarBloom! It takes ages to grow, but it's so worth it.", "happy", "open"),
            ("Wishing on a star... and planting one too!", "happy", "open"),
            ("Take your time, little star. I'll wait patiently. Mostly.", "passive", "open"),
        ],
        "harvest": [
            ("Our StarBloom opened! I could stare at it all night.", "happy", "open"),
            ("A real star in my hands... this is a treasure!", "blush", "open"),
            ("Look how it shimmers! Perfect.", "happy", "open"),
        ],
        "remove": [
            ("Oh... my precious StarBloom seed, safe in the pouch.", "passive", "closed"),
            ("Back to dreaming among the stars, little one.", "passive", "closed"),
            ("I'll keep this seed extra safe. Stars take a long time!", "passive", "closed"),
        ],
    },
}

NYRA_POKES = {          # what she says when you click her; blush lines come on every third click
    "day": [
        ("Hm? Oh, hi! Did you need something?", "happy", "open"),
        ("Hehe, hello! The garden looks lovely today.", "happy", "open"),
        ("Yes? I'm busy being a very professional gardener.", "happy", "open"),
        ("Pat pat? Okay, I'll allow it.", "happy", "open"),
        ("Did you know my ears are squished under this hat? ...Don't tell anyone.", "happy", "open"),
    ],
    "night": [
        ("Mrr... it's so quiet at night. I like it.", "passive", "open"),
        ("The moon is out! ...and so are my ears, under this hat.", "passive", "open"),
        ("Yawn... five more minutes of moonlight, okay?", "passive", "open"),
        ("Night is the best time for MoonCatnip... and cat naps.", "happy", "open"),
    ],
    "rain": [
        ("Mrrow! I do NOT like getting wet.", "passive", "open"),
        ("Rain on the hat... plink plink. At least the plants are happy.", "happy", "open"),
        ("My tail is soaked... don't look!", "passive", "open"),
        ("Shhh, listen to the raindrops.", "passive", "closed"),
    ],
    "blush": [
        ("W-what was that for?! ...Do it again?", "blush", "open"),
        ("My ears! ...I mean, my hat! It's just my hat!", "blush", "open"),
        ("Mrrp! Don't tickle my tail!", "blush", "open"),
        ("Y-you're being very bold today...", "blush", "blush"),
        ("That's embarrassing... but kinda nice.", "blush", "blush"),
    ],
}
nyra_last_line = {}     # pool -> the line she said last, so she doesn't repeat herself
nyra_pokes = 0


def pick_reaction(pool, lines):
    """A random line from the list, but never the one she said last time for this pool."""
    options = [line for line in lines if line != nyra_last_line.get(pool)] or lines
    choice = random.choice(options)
    nyra_last_line[pool] = choice
    return choice


def nyra_says(line):
    text, face, mouth = line
    showDialogue(text, face, mouth)


def plant_reaction(plant_name, action):
    """action is "plant", "harvest" or "remove"."""
    nyra_says(pick_reaction((plant_name, action), PLANT_REACTIONS[plant_name][action]))


def nyra_poke():
    """The player clicked Nyra. Day, night and rain each have their own lines; every third click she blushes."""
    global nyra_pokes
    nyra_pokes += 1
    if nyra_pokes % 3 == 0:
        pool = "blush"
    elif today_weather == "Rainy":
        pool = "rain"
    else:
        pool = "night" if time_of_day == "Night" else "day"
    playSound("nyra_blush" if pool == "blush" else "nyra")
    nyra_says(pick_reaction(("poke", pool), NYRA_POKES[pool]))


def plant_seed(position, plant_name):
    """Plant the chosen plant in the chosen plot (uses one seed of that plant)."""
    if not has_plot(position):
        setMessage("Choose a plot first, little gardener!")
        return
    plant = PLANT_CATALOG.get(plant_name)
    if plant is None:
        setMessage("That plant isn't in the catalog yet.")
        return
    if backpack.get(seed_key(plant.name)) < 1:
        setMessage(f"You're out of {plant.name} seeds.")
        return
    if get_plot(position) is not None:
        setMessage("That plot already has a plant!")
        return

    set_plot(position, {"plant": plant.name, "stage": "early", "growth": 0})
    backpack.remove(seed_key(plant.name), 1)
    history.push_action({"kind": "plant", "position": position, "plant": plant.name,
                         "label": f"Planted {plant.name}"})
    refresh_inventory_ui()
    refresh_undo_ui()
    redraw_plot(position)
    setMessage(f"You planted {plant.name}!")
    playSound("plant")
    plant_reaction(plant.name, "plant")


def harvest_plant(position):
    """Harvest a fully grown plant. It goes into the backpack, ready to sell in the Shop."""
    if not has_plot(position):
        setMessage("Choose a plot first!")
        return
    plot = get_plot(position)
    if plot is None:
        setMessage("There's nothing to harvest here yet.")
        return
    if plot["stage"] != "grown":
        setMessage("That plant isn't ready yet. Press Skip Time to help it grow.")
        showDialogue("Not yet... let it grow a little more.", "passive", "closed")
        return

    name = plot["plant"]
    set_plot(position, None)
    backpack.add(plant_key(name), 1)
    new_entry = unlock_entry(name)          # first harvest adds the plant to the Herbarium
    harvest_xp = PLANT_CATALOG[name].xp
    playSound("harvest")
    history.push_action({"kind": "harvest", "position": position, "plant": name, "xp": harvest_xp,
                         "label": f"Harvested {name}"})
    refresh_inventory_ui()
    refresh_undo_ui()
    redraw_plot(position)
    if new_entry:
        refresh_herbarium_ui()
        setMessage(f"Harvested a {name}! New Herbarium entry unlocked. (+{harvest_xp + DISCOVERY_XP} XP)")
        showDialogue(f"A new page for the Herbarium: {name}! Let's go read about it.", "happy", "open")
    else:
        setMessage(f"Harvested! You got a {name}. (+{harvest_xp} XP)")
        plant_reaction(name, "harvest")
    award_xp(harvest_xp + (DISCOVERY_XP if new_entry else 0))


def remove_plant(position):
    """Pull a plant out. A living plant gives its seed back; a plant that has
    died (stage "dead", coming later) will not."""
    if not has_plot(position):
        setMessage("Choose a plot first!")
        return
    plot = get_plot(position)
    if plot is None:
        setMessage("There's nothing to remove here.")
        return

    name = plot["plant"]
    refund = plot["stage"] != "dead"
    set_plot(position, None)
    if refund:
        backpack.add(seed_key(name), 1)
    history.push_action({"kind": "remove", "position": position, "plot": dict(plot),
                         "refunded": refund, "label": f"Removed {name}"})
    refresh_inventory_ui()
    refresh_undo_ui()
    redraw_plot(position)
    playSound("remove")
    if refund:
        setMessage(f"{name} removed. You got your seed back.")
        plant_reaction(name, "remove")
    else:
        setMessage(f"{name} removed.")
        showDialogue(f"Bye-bye, little {name}...", "passive", "closed")


def skip_time():
    """Time moves on: Day becomes Night, and Night becomes the next Day. The next sky comes off the
    front of the queue, a new one joins the back, and every plant grows."""
    global day, time_of_day, today_weather
    if time_of_day == "Day":
        time_of_day = "Night"
    else:
        time_of_day = "Day"
        day += 1                                              # a new day starts every morning
    sky = climate.process_event()                             # Lesson 2: dequeue
    climate.add_event(random.choice(SKY_CHOICES))             # Lesson 2: enqueue
    today_weather = weather_name_for(sky, time_of_day)

    finished = 0
    for position in range(GRID_SIZE * GRID_SIZE):
        plot = get_plot(position)
        if plot is None or plot["stage"] != "early":
            continue
        plot["growth"] += growth_for(today_weather, time_of_day, plot["plant"])
        if plot["growth"] >= PLANT_CATALOG[plot["plant"]].growth_needed:
            plot["stage"] = "grown"
            finished += 1
        redraw_plot(position)

    history.clear()          # earlier actions can't be undone any more
    playSound("night" if time_of_day == "Night" else "morning")
    refresh_day_ui()
    refresh_undo_ui()
    when = f"Night of day {day}" if time_of_day == "Night" else f"Morning of day {day}"
    line = ("The sun has set. " if time_of_day == "Night" else "A new day begins! ") + WEATHER[today_weather]["line"]
    if finished:
        setMessage(f"{when}: {today_weather}. {finished} plant(s) finished growing!")
        showDialogue(f"{line} {finished} of our plants are ready!", "happy", "open")
    else:
        setMessage(f"{when}: {today_weather}. Nothing finished growing yet.")
        showDialogue(line, "passive", "open")


def undo_action():
    """Reverse the most recent action (the top of the history stack)."""
    action = history.pop_action()
    if action is None:
        setMessage("There's nothing to undo.")
        return

    position = action.get("position")
    playSound("undo")
    if action["kind"] == "plant":
        set_plot(position, None)
        backpack.add(seed_key(action["plant"]), 1)
    elif action["kind"] == "harvest":
        name = action["plant"]
        if not backpack.remove(plant_key(name), 1):     # the harvested plant is gone (sold?) -> can't undo
            refresh_undo_ui()
            setMessage(f"Can't undo: that {name} isn't in the backpack any more.")
            return
        set_plot(position, {"plant": name, "stage": "grown", "growth": PLANT_CATALOG[name].growth_needed})
        player.take_back(action.get("xp", 0))           # so harvest -> undo -> harvest can't farm XP
        refresh_level_ui()
    elif action["kind"] == "remove":
        set_plot(position, dict(action["plot"]))
        if action["refunded"]:
            backpack.remove(seed_key(action["plot"]["plant"]), 1)

    refresh_inventory_ui()
    refresh_undo_ui()
    redraw_plot(position)
    setMessage(f"Undid: {action['label']}.")
    showDialogue("Whoops, rewinding that!", "passive", "closed")


# =====================================================================
# THE HERBARIUM - Lessons 4, 5 and 9
# A collection book: an entry becomes "discovered" the first time you
# harvest that plant (potions will unlock when you brew them).
# =====================================================================
discovered = {"MoonCatnip"}            # the starter plant is already in the book


def normalize(text):
    """'Purr-fect Potion', 'purr fect potion' and 'PURRFECT potion' all become 'purrfectpotion'."""
    return "".join(letter for letter in text.lower() if letter.isalnum())


# ---------------------------------------------------------------------
# LESSON 4: Trees - the book's categories
# Herbarium -> Plants / Potions -> Herbs, Flowers, Basic, Rare -> entries
# Two ways to walk the same tree:
#   Depth-first   uses a STACK  (Lesson 1): go as deep as possible first
#   Breadth-first uses a QUEUE  (Lesson 2): visit one whole level at a time
# Big O: both visit every node once, so O(n).
# ---------------------------------------------------------------------
class TreeNode:
    def __init__(self, name, kind):
        self.name = name
        self.kind = kind                # "root", "category" or "entry"
        self.children = []

    def add_child(self, node):
        self.children.append(node)
        return node


def build_herbarium_tree():
    root = TreeNode("Herbarium", "root")
    for section_name, groups in HERBARIUM_TREE.items():
        section = root.add_child(TreeNode(section_name, "category"))
        for group_name, entry_names in groups.items():
            group = section.add_child(TreeNode(group_name, "category"))
            for entry_name in entry_names:
                group.add_child(TreeNode(entry_name, "entry"))
    return root


def depth_first_order(root):
    order = []
    stack = [(root, 0)]
    while stack:
        node, depth = stack.pop()
        order.append((node, depth))
        for child in reversed(node.children):      # reversed so the first child is visited first
            stack.append((child, depth + 1))
    return order


def breadth_first_order(root):
    order = []
    queue = deque([(root, 0)])
    while queue:
        node, depth = queue.popleft()
        order.append((node, depth))
        for child in node.children:
            queue.append((child, depth + 1))
    return order


herbarium_tree = build_herbarium_tree()
BOOK_ORDER = [node.name for node, _ in depth_first_order(herbarium_tree) if node.kind == "entry"]


def count_entries(node):
    """How many entries sit below this node, and how many of them are discovered."""
    if node.kind == "entry":
        return (1 if node.name in discovered else 0), 1
    found = total = 0
    for child in node.children:
        child_found, child_total = count_entries(child)
        found += child_found
        total += child_total
    return found, total


# ---------------------------------------------------------------------
# LESSON 5: Binary search trees - the entry catalog
# Every node has a smaller key on its LEFT and a bigger key on its RIGHT,
# so a search can throw away half of the tree at every step.
# Walking it "in order" (left, node, right) gives the entries A-Z.
# Big O: search / insert O(log n) when the tree is balanced.
# ---------------------------------------------------------------------
class BSTNode:
    def __init__(self, key, name):
        self.key = key
        self.name = name
        self.left = None
        self.right = None


class EntryBST:
    def __init__(self):
        self.root = None

    def insert(self, name):
        key = normalize(name)
        node = BSTNode(key, name)
        if self.root is None:
            self.root = node
            return
        current = self.root
        while True:
            if key < current.key:
                if current.left is None:
                    current.left = node
                    return
                current = current.left
            else:
                if current.right is None:
                    current.right = node
                    return
                current = current.right

    def search(self, key):
        """Returns (name or None, steps, path of names looked at)."""
        current, steps, path = self.root, 0, []
        while current is not None:
            steps += 1
            path.append(current.name)
            if key == current.key:
                return current.name, steps, path
            current = current.left if key < current.key else current.right
        return None, steps, path

    def in_order(self):
        names, stack, current = [], [], self.root
        while stack or current is not None:
            while current is not None:
                stack.append(current)
                current = current.left
            current = stack.pop()
            names.append(current.name)
            current = current.right
        return names


def build_entry_bst(names):
    """Insert the middle name first, then the halves, so the tree stays balanced."""
    tree = EntryBST()
    ordered = sorted(names, key=normalize)

    def add_middle_first(low, high):
        if low > high:
            return
        middle = (low + high) // 2
        tree.insert(ordered[middle])
        add_middle_first(low, middle - 1)
        add_middle_first(middle + 1, high)

    add_middle_first(0, len(ordered) - 1)
    return tree


entry_bst = build_entry_bst(BOOK_ORDER)
# the same names, sorted A-Z with OUR Lesson 8 sort, for binary search
SORTED_ENTRIES, _ = sort_items([{"key": normalize(n), "name": n} for n in BOOK_ORDER], "key", "Merge Sort")


# ---------------------------------------------------------------------
# LESSON 9: Searching - three ways to find an entry
# Each returns (name or None, steps, path of names looked at).
#   Linear search  O(n)      look at every entry in book order until it matches
#   Binary search  O(log n)  needs a SORTED list; check the middle, drop half
#   BST search     O(log n)  the same idea, walking down the tree from Lesson 5
# ---------------------------------------------------------------------
def linear_search(target):
    path = []
    for name in BOOK_ORDER:
        path.append(name)
        if normalize(name) == target:
            return name, len(path), path
    return None, len(path), path


def binary_search(target):
    low, high, path = 0, len(SORTED_ENTRIES) - 1, []
    while low <= high:
        middle = (low + high) // 2
        path.append(SORTED_ENTRIES[middle]["name"])
        if SORTED_ENTRIES[middle]["key"] == target:
            return SORTED_ENTRIES[middle]["name"], len(path), path
        if SORTED_ENTRIES[middle]["key"] < target:
            low = middle + 1
        else:
            high = middle - 1
    return None, len(path), path


def bst_search(target):
    return entry_bst.search(target)


SEARCH_METHODS = {
    "Binary Search": (binary_search, "O(log n)"),
    "BST Search": (bst_search, "O(log n)"),
    "Linear Search": (linear_search, "O(n)"),
}

herbarium_view = {"order": "dfs", "selected": None, "search": None}

TRAVERSAL_NOTES = {
    "dfs": "Depth-first: go as deep as possible before moving sideways (uses a stack).",
    "bfs": "Breadth-first: visit one whole level before going deeper (uses a queue).",
    "az": "A-Z: an in-order walk of a binary search tree (Lesson 5).",
}


def herbarium_json():
    order = herbarium_view["order"]
    rows = []
    if order == "az":
        for number, name in enumerate(entry_bst.in_order(), start=1):
            rows.append({"visit": number, "depth": 0, "kind": "entry", "name": name, "unlocked": name in discovered})
    else:
        walk = depth_first_order(herbarium_tree) if order == "dfs" else breadth_first_order(herbarium_tree)
        for number, (node, depth) in enumerate(walk):
            if node.kind == "root":
                continue
            row = {"visit": number, "depth": depth - 1, "kind": node.kind, "name": node.name}
            if node.kind == "entry":
                row["unlocked"] = node.name in discovered
            else:
                found, total = count_entries(node)
                row["progress"] = f"{found}/{total}"
            rows.append(row)

    selected, entry = herbarium_view["selected"], None
    if selected in HERBARIUM_ENTRIES and selected in discovered:
        data = HERBARIUM_ENTRIES[selected]
        entry = {"name": selected, "kind": data["kind"], "quote": data["quote"], "sections": data["sections"]}
        if data["kind"] == "plant":
            plant = PLANT_CATALOG[selected]
            entry["facts"] = f"Grows in about {plant.grow_days} days · grows best at {plant.likes.lower()} · sells for {plant.coin_value} coins"
    found_total, all_total = len(discovered), len(BOOK_ORDER)
    return json.dumps({
        "order": order, "rows": rows, "note": TRAVERSAL_NOTES[order],
        "selected": selected, "entry": entry, "search": herbarium_view["search"],
        "progress": {"found": found_total, "total": all_total},
    })


def refresh_herbarium_ui():
    updateHerbarium(herbarium_json())


def unlock_entry(name):
    """Add an entry to the book. Returns True if it was new."""
    if name in HERBARIUM_ENTRIES and name not in discovered:
        discovered.add(name)
        playSound("page")
        return True
    return False


def herbarium_open():
    refresh_herbarium_ui()


def herbarium_set_order(order):
    if order in TRAVERSAL_NOTES:
        herbarium_view["order"] = order
    refresh_herbarium_ui()


def herbarium_select(name):
    if name in HERBARIUM_ENTRIES and name in discovered:
        herbarium_view["selected"] = name
    refresh_herbarium_ui()


def herbarium_search(query, method):
    """Look an entry up by name using the chosen search algorithm."""
    if method not in SEARCH_METHODS:
        method = "Binary Search"
    searcher, big_o = SEARCH_METHODS[method]
    target = normalize(query)
    if not target:
        herbarium_view["search"] = {"message": "Type a name to search for.", "method": method, "big_o": big_o, "path": []}
        refresh_herbarium_ui()
        return
    name, steps, path = searcher(target)
    if name is None:
        message = f"Nothing is called \"{query.strip()}\". ({method}: {steps} step{'s' if steps != 1 else ''})"
    elif name not in discovered:
        message = f"There is an entry for that, but you haven't discovered it yet! ({method}: {steps} step{'s' if steps != 1 else ''})"
    else:
        herbarium_view["selected"] = name
        message = f"Found {name} with {method} in {steps} step{'s' if steps != 1 else ''}."
    herbarium_view["search"] = {"message": message, "method": method, "big_o": big_o, "path": path, "found": name is not None}
    refresh_herbarium_ui()


# =====================================================================
# THE MAP - Lesson 7 (graphs, BFS and DFS)
# A GRAPH is places (nodes) joined by paths (edges). Unlike a tree it may
# have loops: Garden -> Woods -> Spring -> Pond -> Garden is a circle, so a
# walk must remember which places it has VISITED or it would go round forever.
# We store it as an ADJACENCY LIST: place -> list of (neighbour, minutes).
# The minutes are ignored by BFS / DFS but are the COST that Lesson 10 (Dijkstra, greedy) uses.
#   Breadth-first  uses a QUEUE (Lesson 2): scout every nearby place first.
#   Depth-first    uses a STACK (Lesson 1): follow one trail as far as it goes.
# Big O: both visit each place and path once, so O(V + E).
# Exploring reveals ONE new place per press, in the order the chosen walk
# would visit them - so BFS and DFS really do discover different places first.
# =====================================================================
class PlaceGraph:
    def __init__(self):
        self.roads = {}                       # adjacency list: name -> [(neighbour, minutes), ...]

    def add_place(self, name):
        self.roads.setdefault(name, [])

    def add_road(self, first, second, minutes):
        self.add_place(first)
        self.add_place(second)
        self.roads[first].append((second, minutes))      # a path works both ways,
        self.roads[second].append((first, minutes))      # so it is stored twice

    def neighbours(self, name, allowed=None):
        """Neighbouring places. If allowed is given, only places in it are returned."""
        return [place for place, _ in self.roads[name] if allowed is None or place in allowed]


MAP_PLACES = {       # name: (x, y on the map from 0 to 100, what Nyra says about it)
    "Garden":    (50, 82, "Home sweet home! Twenty-five little plots and a lot of weeding."),
    "Herbarium": (22, 66, "Nyra's book of plants and potions lives here."),
    "Shop":      (80, 66, "Seeds go out, harvested plants come in."),
    "Cauldron":  (8, 40, "Where potions bubble. Nyra brews here, and a good brew earns more than plain plants!"),
    "Woods":     (62, 50, "Quiet clearings where moonlight reaches the ground. MoonCatnip likes it here."),
    "Pond":      (36, 46, "Cool, damp ground. MoonBell grows near the water."),
    "Spring":    (50, 28, "A cold spring bubbling out of the rock. Frostmint grows all around it."),
    "Mountain":  (76, 12, "High above every lantern. StarBloom hides up here."),
}
MAP_ROADS = [        # (place, place, minutes) - the ORDER here decides which neighbour a walk tries first
    ("Garden", "Herbarium", 1), ("Garden", "Shop", 2), ("Garden", "Woods", 3), ("Garden", "Pond", 3),
    ("Herbarium", "Cauldron", 2), ("Woods", "Spring", 3), ("Woods", "Mountain", 8),
    ("Pond", "Spring", 2), ("Spring", "Mountain", 4),
]

place_graph = PlaceGraph()
for _place in MAP_PLACES:
    place_graph.add_place(_place)
for _first, _second, _minutes in MAP_ROADS:
    place_graph.add_road(_first, _second, _minutes)

MAP_HOME = "Garden"
known_places = {"Garden", "Herbarium", "Shop"}       # the rest are found by exploring


def breadth_first_walk(graph, start, allowed=None):
    """Visit places nearest-first. Returns a list of steps; each step says who was visited,
    who led there, how many paths from the start, and who was still waiting in the QUEUE."""
    steps, seen = [], {start}
    queue = deque([(start, None, 0)])
    while queue:
        name, came_from, hops = queue.popleft()                  # O(1) - front of the line
        for neighbour in graph.neighbours(name, allowed):
            if neighbour not in seen:
                seen.add(neighbour)                              # mark when JOINING the queue
                queue.append((neighbour, name, hops + 1))
        steps.append({"name": name, "came_from": came_from, "hops": hops,
                      "waiting": [item[0] for item in queue]})
    return steps


def depth_first_walk(graph, start):
    """Follow one trail as deep as possible, then back up. Uses a STACK (a list, push/pop at the end)."""
    steps, visited = [], set()
    stack = [(start, None)]
    while stack:
        name, came_from = stack.pop()                            # O(1) - newest first
        if name in visited:                                      # the same place may be pushed twice
            continue
        visited.add(name)
        for neighbour in reversed(graph.neighbours(name)):       # reversed so the FIRST road is tried first
            if neighbour not in visited:
                stack.append((neighbour, name))
        steps.append({"name": name, "came_from": came_from,
                      "waiting": [item[0] for item in reversed(stack) if item[0] not in visited]})
    return steps


# ---------------------------------------------------------------------
# LESSON 10: Dijkstra and greedy - efficient routes on the Map
# Now the MINUTES on the paths matter. Nyra can only plan through places she
# has already discovered, so exploring makes her routes better.
#
#  Dijkstra: always settle the unsettled place with the SMALLEST total minutes so
#    far (a priority queue / min-heap). The first time a place is taken out, its
#    minutes are final. Always gives the cheapest route. O((V + E) log V).
#
#  Greedy: at every step take the choice that looks best RIGHT NOW. For an errand
#    trip that means "go to the nearest stop I still need". It is quick and simple,
#    but it can get fooled, so we also try EVERY order (brute force, O(n!)) to
#    show how good the greedy trip really was.
# ---------------------------------------------------------------------
def dijkstra(graph, start, allowed):
    """Cheapest minutes from start to every reachable place.
    Returns (minutes, came_from, settled) where settled lists places in the order they were finalised."""
    minutes = {start: 0}
    came_from = {start: None}
    settled = []
    heap = [(0, start)]                                   # (minutes so far, place) - smallest comes out first
    done = set()
    while heap:
        spent, place = heapq.heappop(heap)                # O(log n)
        if place in done:                                 # an older, more expensive entry - ignore it
            continue
        done.add(place)
        settled.append((place, spent))
        for neighbour, cost in graph.roads[place]:
            if neighbour not in allowed or neighbour in done:
                continue
            if spent + cost < minutes.get(neighbour, float("inf")):     # found a cheaper way in
                minutes[neighbour] = spent + cost
                came_from[neighbour] = place
                heapq.heappush(heap, (spent + cost, neighbour))
    return minutes, came_from, settled


def path_from(came_from, goal):
    path = []
    while goal is not None:
        path.append(goal)
        goal = came_from[goal]
    return path[::-1]


def road_minutes(graph, path):
    return sum(dict(graph.roads[a])[b] for a, b in zip(path, path[1:]))


def fewest_stops_route(graph, start, goal, allowed):
    """The route a breadth-first walk would take (fewest places, ignoring minutes)."""
    came_from = {step["name"]: step["came_from"] for step in breadth_first_walk(graph, start, allowed)}
    return path_from(came_from, goal) if goal in came_from else None


def greedy_errands(graph, start, stops, allowed):
    """Greedy: from where I stand, always walk to the NEAREST stop that is still left. Then go home."""
    total, here, left, order = 0, start, set(stops), []
    while left:
        minutes, _, _ = dijkstra(graph, here, allowed)
        nearest = min(sorted(left), key=lambda place: minutes[place])      # sorted() makes ties predictable
        total += minutes[nearest]
        order.append(nearest)
        left.remove(nearest)
        here = nearest
    minutes, _, _ = dijkstra(graph, here, allowed)
    return order, total + minutes[start]


def best_errands(graph, start, stops, allowed):
    """Brute force: try every possible order. Returns (best order, minutes, how many orders were tried)."""
    distance = {place: dijkstra(graph, place, allowed)[0] for place in [start, *stops]}
    best_order, best_total, tried = None, float("inf"), 0
    for order in itertools.permutations(sorted(stops)):               # n! orders
        tried += 1
        total, here = 0, start
        for place in order:
            total += distance[here][place]
            here = place
        total += distance[here][start]
        if total < best_total:
            best_order, best_total = list(order), total
    return best_order, best_total, tried


MAP_WALKS = {
    "bfs": (breadth_first_walk, "Breadth-first: scout every nearby place before going farther (uses a queue)."),
    "dfs": (depth_first_walk, "Depth-first: follow one trail as far as it goes before turning back (uses a stack)."),
}
map_view = {"mode": "bfs", "selected": MAP_HOME, "route": None, "trip": None,
            "message": "Press Explore and Nyra will go and find a new place!"}


def map_json():
    walk = MAP_WALKS[map_view["mode"]][0](place_graph, MAP_HOME)
    hops = {step["name"]: step["hops"] for step in breadth_first_walk(place_graph, MAP_HOME)}
    step_number = {step["name"]: number for number, step in enumerate(walk, start=1)}

    def shown(name):
        return name if name in known_places else "???"

    visible = {name for name in MAP_PLACES
               if name in known_places or any(n in known_places for n in place_graph.neighbours(name))}
    ids = {name: number for number, name in enumerate(MAP_PLACES)}     # roads and places are joined by id,
    places = [{"id": ids[name], "name": shown(name), "real": name if name in known_places else None,   # so "???" never leaks a name
               "x": MAP_PLACES[name][0], "y": MAP_PLACES[name][1],
               "known": name in known_places, "step": step_number[name]}
              for name in MAP_PLACES if name in visible]
    roads = [{"a": ids[a], "b": ids[b], "minutes": minutes, "known": a in known_places and b in known_places}
             for a, b, minutes in MAP_ROADS if a in visible and b in visible]
    steps = [{"number": number, "name": shown(step["name"]),
              "came_from": shown(step["came_from"]) if step["came_from"] else None,
              "waiting": [shown(n) for n in step["waiting"]]}
             for number, step in enumerate(walk, start=1)]

    selected, detail = map_view["selected"], None
    if selected in known_places:
        detail = {"name": selected, "blurb": MAP_PLACES[selected][2],
                  "hops": hops[selected],
                  "neighbours": [{"name": shown(place), "minutes": minutes}
                                 for place, minutes in place_graph.roads[selected]]}
    route = map_view["route"]
    if route:
        route = {**route, "ids": [ids[name] for name in route["cheapest"]["path"]]}
    return json.dumps({
        "route": route, "trip": map_view["trip"],
        "mode": map_view["mode"], "note": MAP_WALKS[map_view["mode"]][1],
        "structure": "queue" if map_view["mode"] == "bfs" else "stack",
        "home": MAP_HOME, "places": places, "roads": roads, "steps": steps,
        "selected": selected, "selected_id": ids.get(selected), "detail": detail, "message": map_view["message"],
        "progress": {"found": len(known_places), "total": len(MAP_PLACES)},
    })


def refresh_map_ui():
    updateMap(map_json())


def map_open():
    refresh_map_ui()


def map_set_mode(mode):
    if mode in MAP_WALKS:
        map_view["mode"] = mode
    refresh_map_ui()


def map_select(name):
    if name in known_places:
        map_view["selected"] = name
        map_view["route"] = None
    refresh_map_ui()


def map_explore():
    """Nyra walks the chosen way and finds the first place she has not seen yet."""
    mode = map_view["mode"]
    walk = MAP_WALKS[mode][0](place_graph, MAP_HOME)
    hops = {step["name"]: step["hops"] for step in breadth_first_walk(place_graph, MAP_HOME)}
    for number, step in enumerate(walk, start=1):
        if step["name"] not in known_places:
            name = step["name"]
            known_places.add(name)
            map_view["selected"], map_view["route"], map_view["trip"] = name, None, None     # old plans are out of date
            way = "breadth-first" if mode == "bfs" else "depth-first"
            map_view["message"] = f"Found {name}! It was stop {number} of the {way} walk ({hops[name]} path(s) from the {MAP_HOME})."
            refresh_map_ui()
            setMessage(f"Nyra found a new place: {name}! (+{MAP_PLACE_XP} XP)")
            playSound("discover")
            showDialogue(f"I found {name}! {MAP_PLACES[name][2]}", "happy", "open")
            award_xp(MAP_PLACE_XP)
            return
    map_view["message"] = "Every place is found! Switch the walk to see the OTHER visiting order."
    refresh_map_ui()
    showDialogue("We've found every place on the map. What a lovely little world!", "happy", "open")


def map_route():
    """Lesson 10 (Dijkstra): cheapest way from the Garden to the selected place - only through discovered places."""
    goal = map_view["selected"]
    if goal not in known_places or goal == MAP_HOME:
        map_view["message"] = "Pick a discovered place on the map first (not the Garden), then ask for the cheapest way."
        refresh_map_ui()
        return
    minutes, came_from, settled = dijkstra(place_graph, MAP_HOME, known_places)
    if goal not in minutes:
        map_view["message"] = f"No known path to {goal} yet. Explore more!"
        refresh_map_ui()
        return
    cheapest = path_from(came_from, goal)
    fewest = fewest_stops_route(place_graph, MAP_HOME, goal, known_places)
    fewest_minutes = road_minutes(place_graph, fewest)
    same = fewest_minutes == minutes[goal]
    map_view["route"] = {
        "goal": goal,
        "cheapest": {"path": cheapest, "minutes": minutes[goal]},
        "fewest": {"path": fewest, "minutes": fewest_minutes},
        "same": same,
        "settled": [{"name": place, "minutes": spent} for place, spent in settled],
    }
    if same:
        map_view["message"] = f"Cheapest way to {goal}: {minutes[goal]} min. (The fewest-stops route is just as cheap this time.)"
    else:
        map_view["message"] = f"Cheapest way to {goal}: {minutes[goal]} min - the fewest-stops route would take {fewest_minutes}!"
    refresh_map_ui()
    showDialogue(f"The cheapest way to {goal} is {' → '.join(cheapest)}.", "passive", "open")


def map_errands():
    """Lesson 10 (greedy): visit every discovered place and come home. Greedy picks the nearest next stop;
    brute force tries every order so we can see how good (or bad) greedy was."""
    stops = sorted(name for name in known_places if name != MAP_HOME)
    if len(stops) < 2:
        map_view["message"] = "An errand trip needs at least two discovered places besides the Garden."
        refresh_map_ui()
        return
    greedy_order, greedy_minutes = greedy_errands(place_graph, MAP_HOME, stops, known_places)
    best_order, best_minutes, tried = best_errands(place_graph, MAP_HOME, stops, known_places)
    map_view["trip"] = {
        "stops": stops,
        "greedy": {"order": greedy_order, "minutes": greedy_minutes},
        "best": {"order": best_order, "minutes": best_minutes},
        "tried": tried,
        "same": greedy_minutes == best_minutes,
    }
    if greedy_minutes == best_minutes:
        map_view["message"] = f"Errand trip: greedy found a best-possible trip this time ({greedy_minutes} min)."
    else:
        map_view["message"] = f"Errand trip: greedy takes {greedy_minutes} min, but the best order takes {best_minutes}. Greedy got fooled!"
    refresh_map_ui()


# =====================================================================
# THE CAULDRON - Lesson 11 (dynamic programming) + Lesson 1 (objects)
# Potions are objects with a recipe. Brewing uses up plants from the backpack.
# What a potion sells for changes with TODAY'S weather (people want a cosy
# potion on a rainy day), so "what should I brew?" has no fixed answer.
#
# Nyra's advice = the plan that earns the MOST coins from the plants in the
# backpack (brew potions, then sell whatever plants are left over).
#
#   best(plants) = the larger of:  sell every plant as it is,
#                  or  brew ONE potion + best(the plants that are left)
#
# Plain recursion solves the same "plants that are left" again and again
# (Purr-fect then SunnySide leaves the same plants as SunnySide then Purr-fect).
# DYNAMIC PROGRAMMING remembers each answer (memoization), so every different
# set of leftover plants is solved only once.
# Big O: plain recursion is exponential in the number of brews; memoized it is
# O(number of different leftover-plant sets x number of potions).
# =====================================================================
class Potion:
    def __init__(self, name, ingredients, base_price, note="", unlock_level=1, xp=10):
        self.name = name
        self.ingredients = ingredients      # {plant name: how many}
        self.base_price = base_price        # coins on a normal day
        self.note = note                    # a short extra explanation shown in the Cauldron window
        self.unlock_level = unlock_level    # the player level at which Nyra learns this recipe
        self.xp = xp                        # XP for brewing one


POTION_CATALOG = {
    potion.name: potion
    for potion in [
        Potion("Purr-fect Potion", {"MoonCatnip": 1, "MoonBell": 1}, 24, unlock_level=3, xp=10),
        Potion("SunnySide Elixir", {"SunPetal": 1, "Frostmint": 1}, 24, unlock_level=2, xp=10),
        # The Herbarium says Starlit Elixir is made from the two basic potions + HeartBlossom + StarBloom.
        # Here Nyra brews those two basic potions on the way, so the Cauldron counts the six plants instead.
        Potion("Starlit Elixir", {"MoonCatnip": 1, "MoonBell": 1, "SunPetal": 1, "Frostmint": 1,
                                  "HeartBlossom": 1, "StarBloom": 1}, 80, unlock_level=5, xp=30,
               note="Nyra brews a Purr-fect Potion and a SunnySide Elixir along the way, so this uses all six plants."),
    ]
}


# ---------------------------------------------------------------------
# LESSON 6 again: the recipe book is a HASH TABLE (with chaining)
# key = potion name, value = its recipe ({plant: how many}).
# index = (sum of letter codes) % number of slots, exactly like the backpack.
# Every time the Cauldron shows or uses a recipe, it LOOKS IT UP here.
# Big O: a lookup is O(1) on average - it goes straight to one slot and only
# compares the few recipes sharing that slot.
# ---------------------------------------------------------------------
class RecipeBook:
    def __init__(self, size=5):
        self.size = size
        self.table = [[] for _ in range(size)]      # each slot is a chain (a small list)
        self.collisions = 0

    def hash_function(self, name):
        total = 0
        for letter in name.lower():
            total += ord(letter)
        return total % self.size

    def put(self, name, recipe):
        slot = self.hash_function(name)
        if self.table[slot]:
            self.collisions += 1                    # another recipe already lives here: chain them
        self.table[slot].append([name, recipe])

    def lookup(self, name):
        """Returns (recipe or None, slot number, how many recipes were compared)."""
        slot = self.hash_function(name)
        compared = 0
        for stored_name, recipe in self.table[slot]:
            compared += 1
            if stored_name == name:
                return recipe, slot, compared
        return None, slot, compared


recipe_book = RecipeBook()
for _potion in POTION_CATALOG.values():
    recipe_book.put(_potion.name, _potion.ingredients)


POTION_DEMAND = {       # weather -> {potion: price multiplier}
    "Rainy": {"Purr-fect Potion": 1.5},
    "Cold snap": {"SunnySide Elixir": 1.5},
    "Starry night": {"Starlit Elixir": 1.25},
}
DEMAND_LINES = {
    "Rainy": "Rainy day: everyone wants a cosy Purr-fect Potion!",
    "Cold snap": "Cold snap: SunnySide Elixir is selling like warm bread!",
    "Starry night": "Starry night: Starlit Elixir sparkles extra bright!",
}
PLANT_ORDER = list(PLANT_CATALOG)                       # fixed order, so a set of plants becomes a tuple of counts
NEEDS = {name: tuple(potion.ingredients.get(plant, 0) for plant in PLANT_ORDER)
         for name, potion in POTION_CATALOG.items()}
NAIVE_CALL_LIMIT = 50000                                # stop counting plain-recursion calls after this many


def potion_key(potion_name):
    return "potion:" + potion_name


def potion_price(potion_name, weather_name=None):
    """What a potion sells for today (the base price times the weather's demand)."""
    weather_name = weather_name or today_weather
    multiplier = POTION_DEMAND.get(weather_name, {}).get(potion_name, 1)
    return round(POTION_CATALOG[potion_name].base_price * multiplier)


def current_plants():
    """The harvested plants in the backpack as a tuple of counts, in PLANT_ORDER."""
    return tuple(backpack.get(plant_key(plant)) for plant in PLANT_ORDER)


def can_make(plants, needs):
    return all(have >= need for have, need in zip(plants, needs))


def after_brewing(plants, needs):
    return tuple(have - need for have, need in zip(plants, needs))


def leftover_value(plants):
    """Coins we would get by selling these plants as they are."""
    return sum(count * PLANT_CATALOG[plant].coin_value for count, plant in zip(plants, PLANT_ORDER))


def learned_recipes(allowed=None):
    """The recipes Nyra can use: all of them, or only the ones in `allowed` (the unlocked ones)."""
    return {name: needs for name, needs in NEEDS.items() if allowed is None or name in allowed}


def unlocked_potions():
    return {name for name, potion in POTION_CATALOG.items() if potion.unlock_level <= player.level}


def count_plain_recursion_calls(plants, prices, allowed=None):
    """The SAME search without any memory. We only count how many calls it makes (and stop at a limit)."""
    calls = 0
    recipes = learned_recipes(allowed)

    def search(left):
        nonlocal calls
        calls += 1
        if calls > NAIVE_CALL_LIMIT:
            return 0
        best = leftover_value(left)
        for name, needs in recipes.items():
            if can_make(left, needs):
                best = max(best, prices[name] + search(after_brewing(left, needs)))
        return best

    search(plants)
    return min(calls, NAIVE_CALL_LIMIT), calls > NAIVE_CALL_LIMIT


def best_brewing_plan(plants, prices, allowed=None):
    """Dynamic programming (top-down, with a memo). Returns (coins, potions to brew in order, stats)."""
    memo = {}                                # plants left -> (best coins, the potion to brew first or None)
    stats = {"solved": 0, "reused": 0}
    recipes = learned_recipes(allowed)

    def solve(left):
        if left in memo:
            stats["reused"] += 1             # answered before - no work needed
            return memo[left][0]
        stats["solved"] += 1
        best, first = leftover_value(left), None             # option 1: sell everything as it is
        for name, needs in recipes.items():                  # option 2: brew one potion, then solve the rest
            if can_make(left, needs):
                coins = prices[name] + solve(after_brewing(left, needs))
                if coins > best:
                    best, first = coins, name
        memo[left] = (best, first)
        return best

    total = solve(plants)
    plan, left = [], plants                  # walk through the remembered choices to read out the plan
    while memo[left][1] is not None:
        plan.append(memo[left][1])
        left = after_brewing(left, NEEDS[memo[left][1]])
    return total, plan, stats


def greedy_brewing_plan(plants, prices, allowed=None):
    """Greedy for comparison: always brew the potion that sells for the most right now."""
    plan, left = [], plants
    recipes = learned_recipes(allowed)
    while True:
        choices = [name for name, needs in recipes.items() if can_make(left, needs)]
        if not choices:
            break
        name = max(choices, key=lambda choice: prices[choice])
        plan.append(name)
        left = after_brewing(left, NEEDS[name])
    return sum(prices[name] for name in plan) + leftover_value(left), plan


def counted(name, count):
    """'1 SunnySide Elixir', '3 Purr-fect Potions'"""
    return f"{count} {name}" + ("s" if count > 1 else "")


def group_plan(plan, prices):
    counts = {}
    for name in plan:
        counts[name] = counts.get(name, 0) + 1
    return [{"name": name, "count": count, "price": prices[name]} for name, count in counts.items()]


cauldron_view = {"advice": None, "message": "Press Ask Nyra and she will work out the most profitable brew!", "brewed": []}


def make_advice():
    plants = current_plants()
    prices = {name: potion_price(name) for name in POTION_CATALOG}
    allowed = unlocked_potions()                       # Nyra can only plan with recipes she has learned
    best, plan, stats = best_brewing_plan(plants, prices, allowed)
    greedy_coins, greedy_plan = greedy_brewing_plan(plants, prices, allowed)
    naive_calls, naive_stopped = count_plain_recursion_calls(plants, prices, allowed)
    baseline = leftover_value(plants)
    return {
        "best": best, "baseline": baseline, "gain": best - baseline,
        "plan": group_plan(plan, prices), "plan_order": plan,
        "greedy": {"coins": greedy_coins, "plan": group_plan(greedy_plan, prices)},
        "greedy_fooled": greedy_coins < best,
        "naive_calls": naive_calls, "naive_stopped": naive_stopped,
        "states": stats["solved"], "reused": stats["reused"],
        "have_plants": sum(plants),
    }


def advice_sentence(advice):
    if not advice["plan"]:
        if advice["have_plants"] == 0:
            return "We don't have any harvested plants yet. Let's grow some first!"
        return f"Nothing is worth brewing right now. Selling the plants as they are earns {advice['baseline']} coins."
    brews = " and ".join(counted(item["name"], item["count"]) for item in advice["plan"])
    return f"Brew {brews}! That earns {advice['best']} coins instead of {advice['baseline']}."


def cauldron_json():
    potions = []
    for name, potion in POTION_CATALOG.items():
        if potion.unlock_level > player.level:                     # not learned yet: show only a silhouette
            potions.append({"name": "???", "art": name, "locked": True, "unlock_level": potion.unlock_level,
                            "ingredients": [], "lookup": None, "note": "", "can_brew": False,
                            "price": 0, "base_price": 0, "plants_worth": 0, "owned": 0})
            continue
        recipe, slot, compared = recipe_book.lookup(name)          # Lesson 6: look the recipe up in the hash table
        ingredients = [{"name": plant, "need": need, "have": backpack.get(plant_key(plant))}
                       for plant, need in recipe.items()]
        potions.append({
            "name": name, "art": name, "locked": False, "unlock_level": potion.unlock_level, "ingredients": ingredients,
            "lookup": {"slot": slot, "compared": compared}, "note": potion.note,
            "can_brew": all(item["have"] >= item["need"] for item in ingredients),
            "price": potion_price(name), "base_price": potion.base_price,
            "plants_worth": sum(PLANT_CATALOG[plant].coin_value * need for plant, need in potion.ingredients.items()),
            "owned": backpack.get(potion_key(name)),
        })
    return json.dumps({
        "weather": today_weather, "symbol": WEATHER[today_weather]["symbol"], "time": time_of_day,
        "demand": DEMAND_LINES.get(today_weather, "Nothing is in special demand today."),
        "potions": potions, "advice": cauldron_view["advice"],
        "advice_text": advice_sentence(cauldron_view["advice"]) if cauldron_view["advice"] else None,
        "message": cauldron_view["message"], "opened": False,
        "book": {"slots": recipe_book.size, "collisions": recipe_book.collisions},
    })


def refresh_cauldron_ui(opened=False):
    data = json.loads(cauldron_json())
    data["opened"] = opened
    data["brewed"] = cauldron_view["brewed"]          # what was just brewed (the screen animates it once)
    cauldron_view["brewed"] = []
    updateCauldron(json.dumps(data))


def cauldron_open():
    """The player went to the Cauldron. Nyra has to have discovered it on the Map first."""
    if "Cauldron" not in known_places:
        setMessage("Nyra hasn't found the Cauldron yet. Explore the Map!")
        showDialogue("Where did I leave my Cauldron? Maybe the Map will help me find it.", "passive", "open")
        return
    cauldron_view["advice"] = None
    cauldron_view["message"] = "Press Ask Nyra and she will work out the most profitable brew!"
    refresh_cauldron_ui(opened=True)


def cauldron_ask():
    cauldron_view["advice"] = make_advice()
    advice = cauldron_view["advice"]
    cauldron_view["message"] = advice_sentence(advice)
    refresh_cauldron_ui()
    showDialogue(advice_sentence(advice), "happy" if advice["plan"] else "passive", "open")


def brew_one(potion_name):
    """Use up the ingredients and add one potion to the backpack. Returns True if it worked."""
    recipe, _slot, _compared = recipe_book.lookup(potion_name)     # Lesson 6: look the recipe up
    if POTION_CATALOG[potion_name].unlock_level > player.level:    # Nyra hasn't learned it yet
        return False
    if recipe is None or not can_make(current_plants(), NEEDS[potion_name]):
        return False
    for plant, need in recipe.items():
        backpack.remove(plant_key(plant), need)
    backpack.add(potion_key(potion_name), 1)
    # the screen throws exactly these plants into the cauldron (one entry per plant thrown)
    cauldron_view["brewed"].append({"potion": potion_name,
                                    "plants": [plant for plant, need in recipe.items() for _ in range(need)]})
    return True


def finish_brewing(new_entries):
    history.clear()                        # used-up plants can't be put back, so Undo can't reach past a brew
    cauldron_view["advice"] = None
    refresh_undo_ui()
    refresh_inventory_ui()
    if new_entries:
        refresh_herbarium_ui()
    refresh_cauldron_ui()


def cauldron_brew(potion_name):
    if potion_name not in POTION_CATALOG:
        return
    if POTION_CATALOG[potion_name].unlock_level > player.level:
        cauldron_view["message"] = f"Nyra hasn't learned that recipe yet. It unlocks at level {POTION_CATALOG[potion_name].unlock_level}."
        refresh_cauldron_ui()
        return
    if not brew_one(potion_name):
        cauldron_view["message"] = f"Not enough plants for a {potion_name} yet."
        refresh_cauldron_ui()
        return
    new_entry = unlock_entry(potion_name)
    earned = POTION_CATALOG[potion_name].xp + (DISCOVERY_XP if new_entry else 0)
    cauldron_view["message"] = f"Brewed a {potion_name}!" + (" New Herbarium entry unlocked." if new_entry else "") + f" (+{earned} XP)"
    finish_brewing([potion_name] if new_entry else [])
    setMessage(cauldron_view["message"])
    playSound("brew")
    if new_entry:
        showDialogue(f"My first {potion_name}! I should read its page in the Herbarium.", "happy", "open")
    else:
        showDialogue(f"Another {potion_name}, bubbling nicely!", "happy", "open")
    award_xp(earned)


def cauldron_brew_plan():
    """Brew everything Nyra's plan says, one potion after another."""
    advice = make_advice()
    if not advice["plan_order"]:
        cauldron_view["message"] = advice_sentence(advice)
        refresh_cauldron_ui()
        return
    new_entries, earned = [], 0
    for name in advice["plan_order"]:
        if brew_one(name):
            earned += POTION_CATALOG[name].xp
            if unlock_entry(name):
                new_entries.append(name)
                earned += DISCOVERY_XP
    brewed = " and ".join(counted(item["name"], item["count"]) for item in advice["plan"])
    cauldron_view["message"] = f"Brewed {brewed}! Together they are worth {advice['gain']} coins more than the plain plants (at today's prices). (+{earned} XP)"
    finish_brewing(new_entries)
    setMessage(cauldron_view["message"])
    playSound("brew")
    showDialogue("All brewed, just like my plan! The Shop should love these.", "happy", "open")
    award_xp(earned)


# =====================================================================
# THE SHOP - Lesson 12 (spending and earning coins) + Lesson 8 (sorting)
# "Buy" lists the seeds for sale; "Sell" lists the plants in your backpack.
# The player picks what to sort by and which algorithm to use.
# =====================================================================
shop_view = {"tab": "buy", "field": "name", "algorithm": "Merge Sort", "descending": False}


def shop_json():
    if shop_view["tab"] == "buy":
        rows = [{"name": plant.name, "price": plant.seed_cost, "owned": backpack.get(seed_key(plant.name)),
                 "affordable": resources.can_afford(plant.seed_cost),
                 "locked": plant.unlock_level > player.level, "unlock_level": plant.unlock_level}
                for plant in PLANT_CATALOG.values()]
    else:
        rows = [{"name": name, "price": PLANT_CATALOG[name].coin_value, "owned": count, "kind": "plant"}
                for name, count in backpack.items_with_prefix("plant:")]
        rows += [{"name": name, "price": potion_price(name), "owned": count, "kind": "potion",
                  "in_demand": potion_price(name) > POTION_CATALOG[name].base_price}
                 for name, count in backpack.items_with_prefix("potion:")]
    rows, comparisons = sort_items(rows, shop_view["field"], shop_view["algorithm"], shop_view["descending"])
    return json.dumps({**shop_view, "big_o": SORT_ALGORITHMS[shop_view["algorithm"]][1],
                       "comparisons": comparisons, "rows": rows})


def refresh_shop_ui():
    updateShop(shop_json())


def shop_open():
    """The player walked into the Shop."""
    refresh_shop_ui()
    refresh_coins_ui()


def shop_set_view(tab, field, algorithm, descending):
    """The player changed the tab, the sort field, the algorithm or the direction."""
    if tab in ("buy", "sell"):
        shop_view["tab"] = tab
    if field in ("name", "price", "owned"):
        shop_view["field"] = field
    if algorithm in SORT_ALGORITHMS:
        shop_view["algorithm"] = algorithm
    shop_view["descending"] = bool(descending)
    refresh_shop_ui()


def set_backpack_sort(field, algorithm, descending):
    """The player changed how the Backpack is sorted."""
    if field in ("name", "count"):
        backpack_sort["field"] = field
    if algorithm in SORT_ALGORITHMS:
        backpack_sort["algorithm"] = algorithm
    backpack_sort["descending"] = bool(descending)
    refresh_inventory_ui()


def buy_seed(plant_name):
    plant = PLANT_CATALOG.get(plant_name)
    if plant is None:
        setMessage("The shop doesn't sell that.")
        return
    if plant.unlock_level > player.level:
        setMessage(f"{plant.name} seeds unlock at level {plant.unlock_level}. Keep growing!")
        return
    if not resources.can_afford(plant.seed_cost):
        setMessage(f"A {plant.name} seed costs {plant.seed_cost} coins. You only have {resources.coins}.")
        return
    resources.spend_coins(plant.seed_cost)
    backpack.add(seed_key(plant.name), 1)
    history.clear()          # a purchase can't be undone, so older actions can't be either
    refresh_undo_ui()
    refresh_coins_ui()
    refresh_inventory_ui()
    refresh_shop_ui()
    setMessage(f"Bought a {plant.name} seed for {plant.seed_cost} coins.")
    playSound("coin")


def sell_plant(plant_name, amount=1):
    plant = PLANT_CATALOG.get(plant_name)
    if plant is None or not isinstance(amount, int) or amount < 1:
        setMessage("Nothing to sell there.")
        return
    if not backpack.remove(plant_key(plant.name), amount):
        setMessage(f"You don't have {amount} {plant.name} to sell.")
        return
    earned = plant.coin_value * amount
    resources.gain_coins(earned)
    history.clear()          # BUG FIX: otherwise Undo-ing a harvest after selling it gave a free plant
    refresh_undo_ui()
    refresh_coins_ui()
    refresh_inventory_ui()
    refresh_shop_ui()
    setMessage(f"Sold {amount} {plant.name} for {earned} coins.")
    playSound("coin")


def sell_potion(potion_name, amount=1):
    if potion_name not in POTION_CATALOG:
        setMessage("The shop doesn't buy that.")
        return
    if not backpack.remove(potion_key(potion_name), amount):
        setMessage(f"You don't have {amount} {potion_name} to sell.")
        return
    earned = potion_price(potion_name) * amount
    resources.gain_coins(earned)
    history.clear()
    refresh_undo_ui()
    refresh_coins_ui()
    refresh_inventory_ui()
    refresh_shop_ui()
    setMessage(f"Sold {amount} {potion_name} for {earned} coins.")
    playSound("coin")


# =====================================================================
# SECRET CODES ("cheat codes") - handy for showing the game off
# Type a code in the Settings window. LESSON 6 AGAIN: the codes live in a HASH TABLE
# (code -> the action it runs), looked up exactly like the Cauldron's recipes.
# Codes ignore capitals, spaces and dashes ("Level Up" = "LEVELUP").
# Every action returns (did it work?, what to tell the player).
# Big O: a lookup is O(1) on average, then the action does its own small job.
# =====================================================================
class CodeBook:
    def __init__(self, size=7):
        self.size = size
        self.table = [[] for _ in range(size)]      # each slot is a chain (a small list)
        self.collisions = 0

    def hash_function(self, code):
        total = 0
        for letter in code:
            total += ord(letter)
        return total % self.size

    def put(self, code, action):
        slot = self.hash_function(code)
        if self.table[slot]:
            self.collisions += 1
        self.table[slot].append([code, action])

    def lookup(self, code):
        """Returns (action or None, slot number, how many codes were compared)."""
        slot = self.hash_function(code)
        compared = 0
        for stored_code, action in self.table[slot]:
            compared += 1
            if stored_code == code:
                return action, slot, compared
        return None, slot, compared


def secret_level_up():
    if player.level >= MAX_LEVEL:
        return False, "You are already at the top level!"
    award_xp(LEVEL_XP[player.level] - player.xp)        # exactly the XP missing for the next level
    return True, f"Level up! You are now level {player.level}."


def secret_max_level():
    if player.level >= MAX_LEVEL:
        return False, "You are already at the top level!"
    award_xp(LEVEL_XP[-1] - player.xp)
    return True, f"Top level reached: level {player.level}. Everything is unlocked!"


def secret_rich():
    resources.gain_coins(500)
    refresh_coins_ui()
    refresh_shop_ui()
    playSound("coin")
    return True, f"+500 coins! You now have {resources.coins}."


def secret_seeds():
    for plant in PLANT_CATALOG.values():
        if plant.unlock_level <= player.level:           # only seeds that are unlocked
            backpack.add(seed_key(plant.name), 5)
    refresh_inventory_ui()
    refresh_shop_ui()
    playSound("coin")
    return True, "+5 seeds of every plant you have unlocked."


def secret_plants():
    for plant in PLANT_CATALOG.values():
        if plant.unlock_level <= player.level:
            backpack.add(plant_key(plant.name), 3)
    refresh_inventory_ui()
    refresh_shop_ui()
    refresh_cauldron_ui()
    playSound("harvest")
    return True, "+3 harvested plants of every kind you have unlocked. Time to brew!"


def secret_grow_all():
    grown = 0
    for position in range(GRID_SIZE * GRID_SIZE):
        plot = get_plot(position)
        if plot is not None and plot["stage"] == "early":
            plot["stage"] = "grown"
            plot["growth"] = PLANT_CATALOG[plot["plant"]].growth_needed
            redraw_plot(position)
            grown += 1
    if grown == 0:
        return False, "Nothing is growing in the garden right now."
    playSound("harvest")
    return True, f"{grown} plant(s) are ready to harvest!"


def secret_explore():
    unknown = [place for place in MAP_PLACES if place not in known_places]
    if not unknown:
        return False, "Every place on the Map is already found."
    known_places.update(MAP_PLACES)
    refresh_map_ui()
    playSound("discover")
    return True, f"Revealed {len(unknown)} place(s) on the Map."


def secret_pages():
    missing = [name for name in HERBARIUM_ENTRIES if name not in discovered]
    if not missing:
        return False, "Every Herbarium page is already unlocked."
    discovered.update(HERBARIUM_ENTRIES)
    refresh_herbarium_ui()
    playSound("page")
    return True, f"Unlocked {len(missing)} Herbarium page(s)."


def secret_skip_time():
    skip_time()
    return True, f"Time moved on: Day {day}, {time_of_day}."


def secret_list_codes():
    return True, "Codes: " + ", ".join(sorted(code.upper() for code in SECRET_CODES))


SECRET_CODES = {        # code (lowercase letters and digits only) -> action
    "levelup": secret_level_up,
    "maxlevel": secret_max_level,
    "rich": secret_rich,
    "seeds": secret_seeds,
    "plants": secret_plants,
    "growall": secret_grow_all,
    "explore": secret_explore,
    "pages": secret_pages,
    "skiptime": secret_skip_time,
    "codes": secret_list_codes,
}

code_book = CodeBook()
for _code, _action in SECRET_CODES.items():
    code_book.put(_code, _action)

codes_used = 0          # how many times a secret code worked (achievements will ignore these)


# =====================================================================
# THE EASTER EGG (hidden)
# Typing the secret word in Settings starts a rhythm-game boss fight (assets/easter_egg). The word is in
# the code book (Lesson 6) but NOT in SECRET_CODES, so the CODES command never lists it, and it answers
# with no message and does not count as a used code. The sequence itself (Nyra senses something is off,
# a cut-off message, black, the fight) is run by SECTION 21 in main.js; Python only picks Nyra's words and
# remembers how it went.
# =====================================================================
EGG_CODE = "itsallahoax"
EGG_INTRO = [           # Nyra feels that something is off (each line is (text, face, mouth), like all her lines)
    ("Huh...? Did the lanterns just flicker? It got really quiet all of a sudden.", "passive", "open"),
    ("Why is it so cold all of a sudden? My tail is standing straight up...", "passive", "open"),
    ("Something feels off. The crickets stopped. Did you notice that too?", "passive", "open"),
]
EGG_CUTOFF = [          # she tries to call out, and the message is cut off
    ("Hey, can you hear me? There's something behind the garden wa—", "passive", "open"),
    ("I don't like this. Please don't let go of the keyboa—", "passive", "open"),
    ("Someone is whispering my name. It sounds like it's comi—", "passive", "open"),
]
EGG_WELCOME = [         # if the player beat the fight: two lines on the home screen
    [("You're back! Oh, thank goodness... I had the strangest dream.", "happy", "open"),
     ("Everything's fine now. Come on, let's go play in the garden!", "happy", "open")],
    [("There you are! I kept calling for you... it was so dark.", "happy", "open"),
     ("Whatever that was, you beat it. My hero! ...Don't tell anyone I said that.", "blush", "open")],
    [("Welcome back! My ears are still buzzing under this hat...", "happy", "open"),
     ("You were amazing in there. Let's never speak of it again, okay? Hehe.", "blush", "open")],
]
egg = {"attempts": 0, "cleared": False}


def secret_egg():
    egg["attempts"] += 1
    intro = pick_reaction(("egg", "intro"), EGG_INTRO)
    cutoff = pick_reaction(("egg", "cutoff"), EGG_CUTOFF)
    startEasterEgg(json.dumps({"intro": list(intro), "cutoff": list(cutoff)}))
    return True, None            # None = a hidden code: no message, and it does not count as a used code


code_book.put(EGG_CODE, secret_egg)


def egg_result(result):
    """The minigame is over: result is "win" (survived the song) or "lose". Losing is silent, as if nothing happened."""
    if result != "win":
        return
    egg["cleared"] = True
    lines = pick_reaction(("egg", "welcome"), EGG_WELCOME)
    showEggWelcome(json.dumps([list(line) for line in lines]))


def apply_secret_code(text):
    """The player typed a code in Settings."""
    global codes_used
    code = normalize(text)
    if not code:
        showCodeResult("Type a code first.", False)
        return
    action, slot, compared = code_book.lookup(code)       # Lesson 6: look the code up in the hash table
    if action is None:
        showCodeResult("That code doesn't do anything... yet.", False)
        return
    worked, message = action()
    if message is None:                                   # a hidden code (the easter egg): stay silent
        return
    if worked:
        codes_used += 1
    showCodeResult(f"{message}  (code book: slot {slot}, {compared} compared)", worked)


# =====================================================================
# STILL TO DO (ideas):  a Water resource for Lesson 12 (watering plants, rain refills it,
# travelling on the Map could cost energy).
# =====================================================================
