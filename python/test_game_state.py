"""Quick checks for game_state.py.  Run with:  python test_game_state.py

The game's JavaScript functions don't exist outside the browser, so this file
gives game_state.py fake ones that just record what Python asked them to do."""
import json
from pathlib import Path


def fresh_game(level=None):
    """level=None starts at the top level (everything unlocked), so most checks ignore levels; pass level=1 to test them."""
    calls = []
    namespace = {
        "drawPlot": lambda pos, plant, stage: calls.append(("plot", pos, plant, stage)),
        "updateInventory": lambda text: calls.append(("inventory", json.loads(text))),
        "updateCoins": lambda coins: calls.append(("coins", coins)),
        "updateDay": lambda d, w, s, f, t, sc: calls.append(("day", d, w, s, f, t, sc)),
        "updateUndo": lambda count, label: calls.append(("undo", count, label)),
        "updateShop": lambda text: calls.append(("shop", json.loads(text))),
        "updateHerbarium": lambda text: calls.append(("herbarium", json.loads(text))),
        "updateMap": lambda text: calls.append(("map", json.loads(text))),
        "updateCauldron": lambda text: calls.append(("cauldron", json.loads(text))),
        "updateLevel": lambda level, xp_in, xp_next, up: calls.append(("level", level, xp_in, xp_next, up)),
        "levelUpFx": lambda level, text: calls.append(("levelup", level, json.loads(text))),
        "playSound": lambda name: calls.append(("sound", name)),
        "startEasterEgg": lambda text: calls.append(("egg_start", json.loads(text))),
        "showEggWelcome": lambda text: calls.append(("egg_welcome", json.loads(text))),
        "showCodeResult": lambda text, worked: calls.append(("code", text, worked)),
        "setMessage": lambda text: calls.append(("message", text)),
        "showDialogue": lambda text, face, mouth: calls.append(("dialogue", text, face, mouth)),
    }
    for filename in ["herbarium_data.py", "game_state.py"]:       # the book text loads first, like in the game
        exec(Path(__file__).with_name(filename).read_text(encoding="utf-8"), namespace)
    if level is None:
        namespace["player"].level = namespace["MAX_LEVEL"]
        namespace["player"].xp = namespace["LEVEL_XP"][-1]
    else:
        namespace["player"].level = level
        namespace["player"].xp = namespace["LEVEL_XP"][level - 1]
    return namespace, calls


def last(calls, kind):
    return [c for c in calls if c[0] == kind][-1]


def seeds(g, name):
    return g["backpack"].get("seed:" + name)


def sampler(g):
    """The game now starts with only 3 MoonCatnip seeds. Tests that need other seeds add one of each here."""
    for name in g["PLANT_CATALOG"]:
        if name != "MoonCatnip":
            g["backpack"].add("seed:" + name, 1)


# ---------- Lesson 6: hash table ----------
def test_hash_table_counts_and_removes():
    g, _ = fresh_game(); table = g["InventoryHashTable"]()
    table.add("seed:Rose", 2); table.add("seed:Rose", 1)
    assert table.get("seed:Rose") == 3
    assert table.remove("seed:Rose", 5) is False and table.get("seed:Rose") == 3
    assert table.remove("seed:Rose", 3) is True and table.get("seed:Rose") == 0 and table.count == 0


def test_hash_table_chains_collisions_and_rehashes():
    g, _ = fresh_game(); table = g["InventoryHashTable"](size=5)
    table.add("ab", 1); table.add("ba", 1)             # same letters -> same slot -> collision
    assert table.collisions == 1 and len(table.table[table.hash_function("ab")]) == 2
    for key in ["c", "d", "e", "f"]:
        table.add(key, 1)
    assert table.rehashes >= 1 and table.size == 11     # grew to the next prime >= 2x
    assert all(table.get(k) == 1 for k in ["ab", "ba", "c", "d", "e", "f"])   # nothing lost


def test_starting_backpack():
    g, _ = fresh_game()
    assert seeds(g, "MoonCatnip") == 3                    # just three MoonCatnip seeds; everything else is unlocked by leveling
    assert [name for name, _count in g["backpack"].items_with_prefix("seed:")] == ["MoonCatnip"]
    assert g["backpack"].rehashes == 0                    # one kind of item: the table has not needed to grow yet
    sampler(g)                                            # collecting more kinds of items makes the table grow (Lesson 6)
    assert g["backpack"].rehashes >= 1


# ---------- Lessons 3 / 12 / 6: planting ----------
def test_start_shows_everything():
    g, calls = fresh_game(); g["start_game"]()
    assert last(calls, "coins") == ("coins", 20)
    assert last(calls, "day")[1:3] == (1, "Sunny")
    assert last(calls, "undo") == ("undo", 0, "")
    assert {s["name"]: s["count"] for s in last(calls, "inventory")[1]["seeds"]}["MoonCatnip"] == 3


def test_plant_uses_a_seed_of_that_plant():
    g, calls = fresh_game(); sampler(g)
    g["plant_seed"](0, "MoonCatnip")
    assert seeds(g, "MoonCatnip") == 2 and seeds(g, "StarBloom") == 1
    assert g["garden_grid"][0][0] == {"plant": "MoonCatnip", "stage": "early", "growth": 0}
    assert last(calls, "plot") == ("plot", 0, "MoonCatnip", "early")


def test_cannot_plant_without_plot_seed_or_on_occupied():
    g, calls = fresh_game(); sampler(g)
    g["plant_seed"](-1, "MoonCatnip")
    assert last(calls, "message")[1] == "Choose a plot first, little gardener!"
    g["plant_seed"](3, "StarBloom"); g["plant_seed"](4, "StarBloom")
    assert last(calls, "message")[1] == "You're out of StarBloom seeds."
    g["plant_seed"](3, "MoonCatnip")
    assert last(calls, "message")[1] == "That plot already has a plant!"


# ---------- Lesson 2: weather queue and growth ----------
def test_queue_is_first_in_first_out():
    g, _ = fresh_game(); q = g["ClimateQueue"]()
    q.add_event("a"); q.add_event("b")
    assert q.process_event() == "a" and q.process_event() == "b" and q.process_event() is None


def test_skip_time_takes_the_front_of_the_forecast():
    g, calls = fresh_game()
    seen = []
    for _ in range(5):
        g["skip_time"](); seen.append(g["today_weather"])
    assert seen == ["Cloudy", "Rainy", "Starry night", "Sunny", "Cloudy"]     # night, day, night, day, night
    assert len(g["climate"].events) == 5                                       # forecast always refilled
    assert all(sky in g["SKY_CHOICES"] for sky in g["climate"].events)


def test_time_alternates_and_the_day_only_changes_in_the_morning():
    g, calls = fresh_game()
    assert (g["day"], g["time_of_day"]) == (1, "Day")
    g["skip_time"](); assert (g["day"], g["time_of_day"]) == (1, "Night")
    g["skip_time"](); assert (g["day"], g["time_of_day"]) == (2, "Day")
    g["skip_time"](); assert (g["day"], g["time_of_day"]) == (2, "Night")
    assert last(calls, "day")[5] == "Night" and "Night of day 2" in last(calls, "message")[1]
    g["skip_time"]()
    assert "Morning of day 3" in last(calls, "message")[1]


def test_a_clear_sky_is_sunny_by_day_and_starry_by_night():
    g, _ = fresh_game()
    assert g["weather_name_for"]("Clear", "Day") == "Sunny" and g["weather_name_for"]("Clear", "Night") == "Starry night"
    assert g["weather_name_for"]("Rainy", "Night") == "Rainy" and g["weather_name_for"]("Cold snap", "Day") == "Cold snap"


def test_forecast_says_which_time_slot_each_sky_is_for():
    g, calls = fresh_game(); g["start_game"]()
    assert last(calls, "day")[4] == "Coming up: Cloudy (night), Rainy (day), Starry night (night)"
    g["skip_time"]()
    assert last(calls, "day")[4].startswith("Coming up: Rainy (day), Starry night (night), Sunny (day)")


def test_background_scene_follows_time_and_weather():
    g, calls = fresh_game()
    scene = g["scene_for"]
    assert scene("Sunny", "Day") == "day" and scene("Cloudy", "Day") == "day" and scene("Cold snap", "Day") == "day"
    assert scene("Cloudy", "Night") == "night" and scene("Cold snap", "Night") == "night"
    assert scene("Starry night", "Night") == "starry"
    assert scene("Rainy", "Day") == "rain" and scene("Rainy", "Night") == "rain"      # rain looks the same day or night
    g["start_game"](); assert last(calls, "day")[6] == "day"
    g["skip_time"](); assert last(calls, "day")[6] == "night"                          # Cloudy night
    g["skip_time"](); assert last(calls, "day")[6] == "rain"                           # Rainy day
    g["skip_time"](); assert last(calls, "day")[6] == "starry"                         # clear night


def test_plants_grow_over_time_slots_and_then_can_be_harvested():
    g, calls = fresh_game()
    g["plant_seed"](7, "MoonCatnip")                              # a night plant: needs 2 days x 3 = 6 points
    g["harvest_plant"](7)
    assert last(calls, "message")[1].startswith("That plant isn't ready yet")
    g["skip_time"]()                                              # cloudy night: its favourite time +2
    assert g["get_plot"](7)["growth"] == 2 and g["get_plot"](7)["stage"] == "early"
    g["skip_time"]()                                              # rainy day: 1 + 1 rain = 2
    assert g["get_plot"](7)["growth"] == 4 and g["get_plot"](7)["stage"] == "early"
    g["skip_time"]()                                              # starry night: 2 + 1 star bonus = 3
    assert g["get_plot"](7)["stage"] == "grown"
    g["harvest_plant"](7)
    assert g["get_plot"](7) is None
    assert g["backpack"].get("plant:MoonCatnip") == 1 and seeds(g, "MoonCatnip") == 2   # no seed back any more


def test_weather_effects():
    g, _ = fresh_game()
    grow = g["growth_for"]
    assert grow("Sunny", "Day", "SunPetal") == 2 and grow("Sunny", "Night", "SunPetal") == 1           # likes the day
    assert grow("Cloudy", "Night", "MoonBell") == 2 and grow("Cloudy", "Day", "MoonBell") == 1         # likes the night
    assert grow("Rainy", "Day", "SunPetal") == 3 and grow("Rainy", "Night", "SunPetal") == 2           # rain adds 1
    assert grow("Starry night", "Night", "MoonBell") == 3 and grow("Starry night", "Night", "StarBloom") == 3
    assert grow("Starry night", "Night", "HeartBlossom") == 1                                          # no star bonus, not its time
    assert grow("Cold snap", "Night", "Frostmint") == 3 and grow("Cold snap", "Day", "Frostmint") == 3
    assert grow("Cold snap", "Day", "SunPetal") == 0 and grow("Cold snap", "Night", "MoonCatnip") == 0


def test_one_ordinary_day_adds_up_to_the_same_pace_for_every_plant():
    g, _ = fresh_game()
    for name, plant in g["PLANT_CATALOG"].items():
        full_day = g["growth_for"]("Cloudy", "Day", name) + g["growth_for"]("Cloudy", "Night", name)
        assert full_day == g["GROWTH_PER_DAY"] == 3, name
        assert plant.growth_needed == plant.grow_days * 3 and plant.likes in ("Day", "Night")


def test_plants_follow_the_herbarium_about_their_favourite_time():
    g, _ = fresh_game()
    likes = {name: plant.likes for name, plant in g["PLANT_CATALOG"].items()}
    assert likes == {"MoonCatnip": "Night", "MoonBell": "Night", "SunPetal": "Day", "HeartBlossom": "Day",
                     "Frostmint": "Night", "StarBloom": "Night"}


def test_inspecting_a_growing_plant_shows_progress_and_favourite_time():
    g, calls = fresh_game(); sampler(g)
    g["plant_seed"](0, "SunPetal"); g["inspect_plot"](0)
    assert last(calls, "message")[1] == "Plot 1: SunPetal is growing (0/6). It grows best at day."


# ---------- Lesson 1: stack and Undo ----------
def test_history_stack_is_last_in_first_out():
    g, _ = fresh_game(); h = g["ActionHistoryStack"]()
    h.push_action("a"); h.push_action("b")
    assert h.peek_action() == "b" and h.pop_action() == "b" and h.pop_action() == "a" and h.pop_action() is None


def test_undo_plant():
    g, calls = fresh_game()
    g["plant_seed"](0, "MoonCatnip"); g["undo_action"]()
    assert g["get_plot"](0) is None and seeds(g, "MoonCatnip") == 3
    assert last(calls, "undo") == ("undo", 0, "")


def test_undo_goes_newest_first():
    g, calls = fresh_game(); sampler(g)
    g["plant_seed"](0, "MoonCatnip"); g["plant_seed"](1, "MoonBell")
    assert last(calls, "undo") == ("undo", 2, "Planted MoonBell")
    g["undo_action"]()
    assert g["get_plot"](1) is None and g["get_plot"](0) is not None


def test_undo_remove_and_harvest():
    g, calls = fresh_game(); sampler(g)
    g["plant_seed"](2, "Frostmint"); g["remove_plant"](2)
    assert seeds(g, "Frostmint") == 1                              # refunded
    g["undo_action"]()
    assert g["get_plot"](2)["plant"] == "Frostmint" and seeds(g, "Frostmint") == 0
    g["get_plot"](2).update(stage="grown", growth=2)
    g["harvest_plant"](2)
    assert g["backpack"].get("plant:Frostmint") == 1
    g["undo_action"]()
    assert g["get_plot"](2)["stage"] == "grown" and g["backpack"].get("plant:Frostmint") == 0 and seeds(g, "Frostmint") == 0


def test_remove_does_not_refund_a_dead_plant():
    g, _ = fresh_game(); sampler(g)
    g["plant_seed"](2, "Frostmint"); g["get_plot"](2)["stage"] = "dead"
    g["remove_plant"](2)
    assert seeds(g, "Frostmint") == 0


def test_next_day_clears_undo():
    g, calls = fresh_game()
    g["plant_seed"](0, "MoonCatnip"); g["skip_time"]()
    assert last(calls, "undo") == ("undo", 0, "")
    g["undo_action"]()
    assert last(calls, "message")[1] == "There's nothing to undo."



# ---------- Lesson 8: sorting ----------
def test_every_sorting_algorithm_sorts_correctly():
    import random
    g, _ = fresh_game(); rng = random.Random(7)
    for name in g["SORT_ALGORITHMS"]:
        for size in [0, 1, 2, 9, 30]:
            items = [{"name": f"p{rng.randint(0, 20)}", "count": rng.randint(0, 9)} for _ in range(size)]
            result, comparisons = g["sort_items"](items, "count", name)
            assert [i["count"] for i in result] == sorted(i["count"] for i in items), name
            assert len(result) == len(items) and comparisons >= 0


def test_sort_by_name_ignores_capitals_and_can_go_descending():
    g, _ = fresh_game()
    items = [{"name": "banana"}, {"name": "Apple"}, {"name": "cherry"}]
    assert [i["name"] for i in g["sort_items"](items, "name")[0]] == ["Apple", "banana", "cherry"]
    assert [i["name"] for i in g["sort_items"](items, "name", descending=True)[0]] == ["cherry", "banana", "Apple"]


def test_big_o_shows_up_in_the_comparison_counts():
    g, _ = fresh_game()
    items = [{"n": 40 - i} for i in range(40)]            # worst case: in reverse order
    merge = g["sort_items"](items, "n", "Merge Sort")[1]
    bubble = g["sort_items"](items, "n", "Bubble Sort")[1]
    assert merge < 300 < bubble                            # n log n  vs  n^2
    already_sorted = [{"n": i} for i in range(40)]
    assert g["sort_items"](already_sorted, "n", "Bubble Sort")[1] == 39     # best case O(n)


def test_backpack_sort_setting():
    g, calls = fresh_game(); sampler(g)
    g["set_backpack_sort"]("count", "Quick Sort", True)
    data = last(calls, "inventory")[1]
    assert [s["name"] for s in data["seeds"]][0] == "MoonCatnip"              # 3 seeds, the most
    assert data["sort"]["algorithm"] == "Quick Sort" and data["sort"]["seeds_comparisons"] > 0


# ---------- Shop: Lessons 12 + 8 ----------
def test_buying_a_seed():
    g, calls = fresh_game()
    g["buy_seed"]("StarBloom")                              # costs 6 of our 20 coins (we have no StarBloom seeds yet)
    assert g["resources"].coins == 14 and seeds(g, "StarBloom") == 1
    assert last(calls, "coins") == ("coins", 14)
    g["resources"].coins = 2
    g["buy_seed"]("StarBloom")
    assert g["resources"].coins == 2 and "only have 2" in last(calls, "message")[1]


def test_selling_plants():
    g, calls = fresh_game()
    g["backpack"].add("plant:SunPetal", 3)
    g["sell_plant"]("SunPetal", 2)                          # 7 coins each
    assert g["resources"].coins == 34 and g["backpack"].get("plant:SunPetal") == 1
    g["sell_plant"]("SunPetal", 5)
    assert g["resources"].coins == 34 and "don't have" in last(calls, "message")[1]


def test_shop_lists_are_sorted_with_the_chosen_algorithm():
    g, calls = fresh_game()
    g["shop_set_view"]("buy", "price", "Insertion Sort", False)
    shop = last(calls, "shop")[1]
    prices = [r["price"] for r in shop["rows"]]
    assert prices == sorted(prices) and shop["algorithm"] == "Insertion Sort" and shop["comparisons"] > 0
    g["shop_set_view"]("buy", "price", "Insertion Sort", True)
    assert [r["price"] for r in last(calls, "shop")[1]["rows"]] == sorted(prices, reverse=True)
    g["shop_set_view"]("sell", "name", "Merge Sort", False)
    assert last(calls, "shop")[1]["rows"] == []              # nothing harvested yet



# ---------- Herbarium: Lessons 4, 5, 9 ----------
def names_in_walk(g, order):
    return [(n.name, d) for n, d in order if n.kind != "root"]


def test_depth_first_goes_deep_before_sideways():
    g, _ = fresh_game()
    walk = [name for name, _ in names_in_walk(g, g["depth_first_order"](g["herbarium_tree"]))]
    assert walk[:6] == ["Plants", "Herbs", "MoonCatnip", "Frostmint", "Flowers", "MoonBell"]
    assert len(walk) == 15      # 2 sections + 4 groups + 9 entries


def test_breadth_first_visits_one_level_at_a_time():
    g, _ = fresh_game()
    walk = names_in_walk(g, g["breadth_first_order"](g["herbarium_tree"]))
    assert [n for n, _ in walk[:6]] == ["Plants", "Potions", "Herbs", "Flowers", "Basic", "Rare"]
    depths = [d for _, d in walk]
    assert depths == sorted(depths)                     # levels never go back up
    assert len(walk) == 15      # 2 sections + 4 groups + 9 entries


def test_bst_in_order_is_alphabetical_and_balanced():
    g, _ = fresh_game()
    names = g["entry_bst"].in_order()
    assert names == sorted(names, key=g["normalize"]) and len(names) == 9
    assert g["entry_bst"].search(g["normalize"]("StarBloom"))[1] <= 4      # balanced: few steps


def test_all_three_searches_find_every_entry():
    g, _ = fresh_game()
    for name in g["BOOK_ORDER"]:
        target = g["normalize"](name)
        for method, (search, _) in g["SEARCH_METHODS"].items():
            found, steps, path = search(target)
            assert found == name and steps == len(path) and path[-1] == name, (method, name)
    assert all(search(g["normalize"]("nothing"))[0] is None for search, _ in g["SEARCH_METHODS"].values())


def test_linear_search_takes_more_steps_than_binary():
    g, _ = fresh_game()
    target = g["normalize"]("Starlit Elixir")                # last entry in the book
    assert g["linear_search"](target)[1] == 9
    assert g["binary_search"](target)[1] <= 4


def test_search_opens_discovered_entries_and_hides_undiscovered_ones():
    g, calls = fresh_game()
    g["herbarium_search"]("moon catnip", "Binary Search")           # spaces and capitals don't matter
    herb = last(calls, "herbarium")[1]
    assert herb["selected"] == "MoonCatnip" and herb["entry"]["name"] == "MoonCatnip"
    assert "Found MoonCatnip" in herb["search"]["message"]
    g["herbarium_search"]("StarBloom", "Linear Search")
    herb = last(calls, "herbarium")[1]
    assert "haven't discovered" in herb["search"]["message"] and herb["selected"] == "MoonCatnip"
    g["herbarium_search"]("pizza", "BST Search")
    assert "Nothing is called" in last(calls, "herbarium")[1]["search"]["message"]


def test_first_harvest_unlocks_a_page():
    g, calls = fresh_game(); sampler(g)
    assert "StarBloom" not in g["discovered"]
    g["herbarium_select"]("StarBloom")                              # locked: can't open it
    assert last(calls, "herbarium")[1]["entry"] is None
    g["plant_seed"](0, "StarBloom")
    for _ in range(4):
        g["skip_time"]()
        g["get_plot"](0)["growth"] = max(g["get_plot"](0)["growth"], 0)
    g["get_plot"](0).update(stage="grown")
    g["harvest_plant"](0)
    assert "StarBloom" in g["discovered"] and "New Herbarium entry" in [c for c in calls if c[0] == "message"][-1][1]
    g["herbarium_select"]("StarBloom")
    entry = last(calls, "herbarium")[1]["entry"]
    assert entry["name"] == "StarBloom" and entry["sections"][0][0] == "Appearance" and "grows in about 4 days" in entry["facts"].lower() and "at night" in entry["facts"]


def test_herbarium_orders_and_progress():
    g, calls = fresh_game()
    g["herbarium_set_order"]("az")
    rows = last(calls, "herbarium")[1]["rows"]
    assert [r["name"] for r in rows][:3] == ["Frostmint", "HeartBlossom", "MoonBell"]
    g["herbarium_set_order"]("dfs")
    herb = last(calls, "herbarium")[1]
    assert herb["progress"] == {"found": 1, "total": 9}
    assert [r["progress"] for r in herb["rows"] if r["name"] in ("Plants", "Potions")] == ["1/6", "0/3"]


def test_selling_a_harvest_closes_the_undo_history():
    """Regression: harvest -> sell -> Undo used to put the plant back AND keep the coins."""
    g, calls = fresh_game()
    g["plant_seed"](0, "MoonCatnip")
    g["get_plot"](0).update(stage="grown", growth=2)
    g["harvest_plant"](0)
    g["sell_plant"]("MoonCatnip", 1)
    coins = g["resources"].coins
    assert g["history"].size() == 0 and last(calls, "undo")[1] == 0
    g["undo_action"]()
    assert g["get_plot"](0) is None and g["resources"].coins == coins


def test_undo_harvest_refuses_when_plant_is_gone():
    g, calls = fresh_game()
    g["plant_seed"](0, "MoonCatnip")
    g["get_plot"](0).update(stage="grown", growth=2)
    g["harvest_plant"](0)
    g["backpack"].remove("plant:MoonCatnip", 1)          # simulate the plant leaving some other way
    g["undo_action"]()
    assert g["get_plot"](0) is None and "Can't undo" in last(calls, "message")[1]


def test_buying_a_seed_closes_the_undo_history():
    g, _ = fresh_game()
    g["plant_seed"](0, "MoonCatnip")
    g["buy_seed"]("MoonBell")
    assert g["history"].size() == 0


# ---------- Lesson 7: graphs, BFS and DFS ----------
def test_graph_paths_work_both_ways():
    g, _ = fresh_game(); graph = g["place_graph"]
    for place, roads in graph.roads.items():
        for neighbour, minutes in roads:
            assert (place, minutes) in graph.roads[neighbour]


def test_bfs_visits_nearest_first():
    g, _ = fresh_game()
    steps = g["breadth_first_walk"](g["place_graph"], "Garden")
    assert [s["name"] for s in steps] == ["Garden", "Herbarium", "Shop", "Woods", "Pond", "Cauldron", "Spring", "Mountain"]
    hops = {s["name"]: s["hops"] for s in steps}
    assert hops["Garden"] == 0 and hops["Pond"] == 1 and hops["Cauldron"] == 2 and hops["Mountain"] == 2


def test_dfs_follows_a_trail_deep_first():
    g, _ = fresh_game()
    steps = g["depth_first_walk"](g["place_graph"], "Garden")
    assert [s["name"] for s in steps] == ["Garden", "Herbarium", "Cauldron", "Shop", "Woods", "Spring", "Pond", "Mountain"]


def test_walks_visit_every_place_once_even_with_loops():
    g, _ = fresh_game()
    for walk in (g["breadth_first_walk"], g["depth_first_walk"]):
        names = [s["name"] for s in walk(g["place_graph"], "Garden")]
        assert len(names) == len(set(names)) == len(g["MAP_PLACES"])


def test_exploring_reveals_places_in_walk_order():
    g, calls = fresh_game()
    assert g["known_places"] == {"Garden", "Herbarium", "Shop"}
    g["map_explore"]()                                       # breadth-first: Woods is next unseen
    assert "Woods" in g["known_places"] and "Woods" in last(calls, "message")[1]
    g2, _ = fresh_game()
    g2["map_set_mode"]("dfs"); g2["map_explore"]()           # depth-first: the trail reaches Cauldron first
    assert "Cauldron" in g2["known_places"] and "Woods" not in g2["known_places"]


def test_map_hides_unknown_places_and_ends_politely():
    g, calls = fresh_game()
    g["map_open"]()
    data = last(calls, "map")[1]
    names = {p["name"] for p in data["places"]}
    assert "Mountain" not in [p["real"] for p in data["places"]] and "???" in names
    assert data["progress"] == {"found": 3, "total": 8}
    for _ in range(10):
        g["map_explore"]()
    assert len(g["known_places"]) == 8
    assert "Every place is found" in last(calls, "map")[1]["message"]


def test_map_select_only_opens_known_places():
    g, calls = fresh_game()
    g["map_open"]()
    g["map_select"]("Mountain")                              # not found yet -> ignored
    assert last(calls, "map")[1]["selected"] == "Garden"
    g["map_select"]("Shop")
    detail = last(calls, "map")[1]["detail"]
    assert detail["name"] == "Shop" and detail["hops"] == 1 and detail["neighbours"][0]["name"] == "Garden"


# ---------- Lesson 10: Dijkstra and greedy ----------
def all_places(g):
    return set(g["MAP_PLACES"])


def test_dijkstra_matches_trying_every_path():
    g, _ = fresh_game(); graph = g["place_graph"]

    def every_path_cost(here, goal, seen, spent):                  # slow, obviously-correct version
        if here == goal:
            return spent
        best = float("inf")
        for neighbour, cost in graph.roads[here]:
            if neighbour not in seen:
                best = min(best, every_path_cost(neighbour, goal, seen | {neighbour}, spent + cost))
        return best

    for start in all_places(g):
        minutes, _, _ = g["dijkstra"](graph, start, all_places(g))
        for goal in all_places(g):
            assert minutes[goal] == every_path_cost(start, goal, {start}, 0), (start, goal)


def test_dijkstra_settles_places_cheapest_first_and_builds_the_path():
    g, _ = fresh_game()
    minutes, came_from, settled = g["dijkstra"](g["place_graph"], "Garden", all_places(g))
    totals = [spent for _, spent in settled]
    assert totals == sorted(totals) and settled[0] == ("Garden", 0)
    assert g["path_from"](came_from, "Mountain") == ["Garden", "Pond", "Spring", "Mountain"] and minutes["Mountain"] == 9


def test_cheapest_route_can_differ_from_fewest_stops():
    g, calls = fresh_game()
    g["known_places"].update(["Pond", "Spring", "Woods", "Mountain"])
    g["map_select"]("Mountain"); g["map_route"]()
    route = last(calls, "map")[1]["route"]
    assert route["cheapest"]["path"] == ["Garden", "Pond", "Spring", "Mountain"] and route["cheapest"]["minutes"] == 9
    assert route["fewest"]["path"] == ["Garden", "Woods", "Mountain"] and route["fewest"]["minutes"] == 11
    assert route["same"] is False and len(route["ids"]) == 4


def test_routes_only_use_discovered_places():
    g, calls = fresh_game()
    g["known_places"].update(["Woods", "Spring", "Mountain"])          # Pond is still unknown
    g["map_select"]("Mountain"); g["map_route"]()
    route = last(calls, "map")[1]["route"]
    assert route["cheapest"]["path"] == ["Garden", "Woods", "Spring", "Mountain"] and route["cheapest"]["minutes"] == 10
    assert "Pond" not in route["cheapest"]["path"]                      # 9 min via the Pond, but Nyra doesn't know it yet


def test_route_needs_a_destination_and_is_cleared_by_new_choices():
    g, calls = fresh_game()
    g["map_route"]()                                                    # Garden selected -> nothing to plan
    assert last(calls, "map")[1]["route"] is None and "Pick a discovered place" in last(calls, "map")[1]["message"]
    g["map_select"]("Shop"); g["map_route"]()
    assert last(calls, "map")[1]["route"]["cheapest"]["path"] == ["Garden", "Shop"]
    g["map_select"]("Herbarium")
    assert last(calls, "map")[1]["route"] is None
    g["map_route"](); g["map_explore"]()                                # exploring makes old plans stale
    assert last(calls, "map")[1]["route"] is None


def test_greedy_is_fooled_but_never_beats_brute_force():
    g, _ = fresh_game(); graph = g["place_graph"]; everywhere = all_places(g)
    stops = sorted(everywhere - {"Garden"})
    greedy_order, greedy_minutes = g["greedy_errands"](graph, "Garden", stops, everywhere)
    best_order, best_minutes, tried = g["best_errands"](graph, "Garden", stops, everywhere)
    assert greedy_order[0] == "Herbarium" and greedy_minutes == 34      # always the nearest next stop
    assert best_minutes == 29 and tried == 5040                         # 7! orders tried
    for few in (["Shop", "Herbarium"], ["Pond", "Woods"], ["Pond", "Spring", "Mountain"]):
        assert g["greedy_errands"](graph, "Garden", few, everywhere)[1] >= g["best_errands"](graph, "Garden", few, everywhere)[1]


def test_errand_trip_button_reports_greedy_vs_best():
    g, calls = fresh_game()
    g["map_errands"]()                                                  # only Herbarium + Shop known: tied
    trip = last(calls, "map")[1]["trip"]
    assert trip["stops"] == ["Herbarium", "Shop"] and trip["same"] is True
    g["known_places"].update(["Pond", "Spring", "Woods", "Mountain", "Cauldron"])
    g["map_errands"]()
    trip = last(calls, "map")[1]["trip"]
    assert trip["greedy"]["minutes"] == 34 and trip["best"]["minutes"] == 29 and trip["same"] is False
    assert "fooled" in last(calls, "map")[1]["message"]


def test_errand_trip_needs_two_stops():
    g, calls = fresh_game()
    g["known_places"].intersection_update({"Garden", "Shop"})
    g["map_errands"]()
    assert last(calls, "map")[1]["trip"] is None


# ---------- Lesson 11: dynamic programming (the Cauldron) ----------
def give_plants(g, **plants):
    for name, amount in plants.items():
        g["backpack"].add("plant:" + name, amount)


def prices_for(g, weather):
    return {name: g["potion_price"](name, weather) for name in g["POTION_CATALOG"]}


def test_potion_prices_follow_the_weather():
    g, _ = fresh_game()
    assert g["potion_price"]("Purr-fect Potion", "Sunny") == 24 and g["potion_price"]("Purr-fect Potion", "Rainy") == 36
    assert g["potion_price"]("SunnySide Elixir", "Cold snap") == 36 and g["potion_price"]("Starlit Elixir", "Starry night") == 100
    assert g["potion_price"]("Starlit Elixir", "Rainy") == 80


def test_dp_plan_is_really_the_best_one():
    """Compare with the slow, obvious way: try EVERY number of each potion."""
    import itertools, random
    g, _ = fresh_game(); rng = random.Random(11)
    names = list(g["POTION_CATALOG"])
    for weather in ["Sunny", "Rainy", "Cold snap", "Starry night"]:
        prices = prices_for(g, weather)
        for _ in range(25):
            plants = tuple(rng.randint(0, 4) for _ in g["PLANT_ORDER"])
            best_by_force = 0
            for counts in itertools.product(range(5), repeat=len(names)):
                left, ok = plants, True
                for name, count in zip(names, counts):
                    for _ in range(count):
                        if not g["can_make"](left, g["NEEDS"][name]):
                            ok = False
                            break
                        left = g["after_brewing"](left, g["NEEDS"][name])
                    if not ok:
                        break
                if ok:
                    best_by_force = max(best_by_force, sum(prices[n] * c for n, c in zip(names, counts)) + g["leftover_value"](left))
            coins, plan, _stats = g["best_brewing_plan"](plants, prices)
            assert coins == best_by_force, (weather, plants)
            left = plants                                         # and the plan really is makeable and worth that much
            for name in plan:
                assert g["can_make"](left, g["NEEDS"][name])
                left = g["after_brewing"](left, g["NEEDS"][name])
            assert sum(prices[n] for n in plan) + g["leftover_value"](left) == coins


def test_greedy_brewing_gets_fooled_on_a_rainy_day():
    g, _ = fresh_game()
    one_of_each = (1, 1, 1, 1, 1, 1)
    sunny, rainy = prices_for(g, "Sunny"), prices_for(g, "Rainy")
    assert g["best_brewing_plan"](one_of_each, sunny)[:2] == (80, ["Starlit Elixir"])
    coins, plan, _ = g["best_brewing_plan"](one_of_each, rainy)
    assert coins == 84 and sorted(plan) == ["Purr-fect Potion", "SunnySide Elixir"]
    assert g["greedy_brewing_plan"](one_of_each, rainy)[0] == 80


def test_memoizing_does_far_less_work_than_plain_recursion():
    g, _ = fresh_game()
    plants, prices = (5, 5, 5, 5, 5, 5), prices_for(g, "Sunny")
    _, _, stats = g["best_brewing_plan"](plants, prices)
    calls, stopped = g["count_plain_recursion_calls"](plants, prices)
    assert stats["reused"] > 0 and stats["solved"] == 91 and calls == 4494 and not stopped
    assert g["count_plain_recursion_calls"]((12,) * 6, prices)[1] is True        # plain recursion is stopped at the limit


def test_cauldron_is_locked_until_it_is_found_on_the_map():
    g, calls = fresh_game()
    g["cauldron_open"]()
    assert not [c for c in calls if c[0] == "cauldron"] and "Cauldron" in last(calls, "message")[1]
    g["known_places"].add("Cauldron")
    g["cauldron_open"]()
    assert last(calls, "cauldron")[1]["opened"] is True and len(last(calls, "cauldron")[1]["potions"]) == 3


def test_brewing_uses_plants_adds_a_potion_and_unlocks_its_page():
    g, calls = fresh_game()
    g["known_places"].add("Cauldron")
    give_plants(g, MoonCatnip=2, MoonBell=1)
    g["plant_seed"](0, "MoonCatnip")                                    # something on the Undo stack
    g["cauldron_brew"]("Purr-fect Potion")
    assert g["backpack"].get("plant:MoonCatnip") == 1 and g["backpack"].get("plant:MoonBell") == 0
    assert g["backpack"].get("potion:Purr-fect Potion") == 1 and "Purr-fect Potion" in g["discovered"]
    assert g["history"].size() == 0
    assert last(calls, "inventory")[1]["potions"] == [{"name": "Purr-fect Potion", "count": 1}]
    g["cauldron_brew"]("Purr-fect Potion")                              # no MoonBell left
    assert g["backpack"].get("potion:Purr-fect Potion") == 1 and "Not enough" in last(calls, "cauldron")[1]["message"]


def test_ask_nyra_then_brew_her_plan():
    g, calls = fresh_game()
    g["known_places"].add("Cauldron"); g["today_weather"] = "Rainy"
    give_plants(g, MoonCatnip=1, MoonBell=1, SunPetal=1, Frostmint=1, HeartBlossom=1, StarBloom=1)
    g["cauldron_ask"]()
    advice = last(calls, "cauldron")[1]["advice"]
    assert advice["best"] == 84 and advice["baseline"] == 54 and advice["gain"] == 30 and advice["greedy_fooled"] is True
    assert {item["name"] for item in advice["plan"]} == {"Purr-fect Potion", "SunnySide Elixir"}
    g["cauldron_brew_plan"]()
    assert g["backpack"].get("potion:Purr-fect Potion") == 1 and g["backpack"].get("potion:SunnySide Elixir") == 1
    assert g["backpack"].get("plant:HeartBlossom") == 1                  # kept, to be sold as it is
    assert last(calls, "cauldron")[1]["advice"] is None                  # old advice is out of date after brewing


def test_nyra_says_so_when_there_is_nothing_to_brew():
    g, calls = fresh_game()
    g["known_places"].add("Cauldron")
    g["cauldron_ask"]()
    assert "harvested plants" in last(calls, "cauldron")[1]["advice_text"]
    give_plants(g, HeartBlossom=2)
    g["cauldron_ask"]()
    assert last(calls, "cauldron")[1]["advice"]["plan"] == [] and "Nothing is worth brewing" in last(calls, "cauldron")[1]["advice_text"]


def test_shop_buys_potions_at_todays_price():
    g, calls = fresh_game()
    g["backpack"].add("potion:Purr-fect Potion", 2)
    g["today_weather"] = "Rainy"
    g["shop_set_view"]("sell", "name", "Merge Sort", False)
    row = [r for r in last(calls, "shop")[1]["rows"] if r["kind"] == "potion"][0]
    assert row["price"] == 36 and row["in_demand"] is True
    coins = g["resources"].coins
    g["sell_potion"]("Purr-fect Potion", 2)
    assert g["resources"].coins == coins + 72 and g["backpack"].get("potion:Purr-fect Potion") == 0
    g["sell_potion"]("Purr-fect Potion", 1)                              # none left
    assert g["resources"].coins == coins + 72


def test_backpack_sends_potions_and_their_sort_count_to_the_screen():
    """Regression: potions were in the backpack but never reached the Backpack window."""
    g, calls = fresh_game()
    g["backpack"].add("potion:Starlit Elixir", 1); g["backpack"].add("potion:Purr-fect Potion", 3)
    g["refresh_inventory_ui"]()
    data = last(calls, "inventory")[1]
    assert data["potions"] == [{"name": "Purr-fect Potion", "count": 3}, {"name": "Starlit Elixir", "count": 1}]
    assert "potions_comparisons" in data["sort"] and data["sort"]["potions_comparisons"] > 0



# ---------- Cauldron recipe book (Lesson 6: hash table) ----------
def test_recipe_book_finds_every_recipe_and_nothing_else():
    g, _ = fresh_game(); book = g["recipe_book"]
    for name, potion in g["POTION_CATALOG"].items():
        recipe, slot, compared = book.lookup(name)
        assert recipe == potion.ingredients and 0 <= slot < book.size and compared >= 1
    assert book.lookup("Pizza Potion")[0] is None


def test_recipe_book_chains_recipes_that_share_a_slot():
    g, _ = fresh_game(); book = g["RecipeBook"](size=1)         # one slot: everything collides
    book.put("A", {"MoonCatnip": 1}); book.put("B", {"SunPetal": 1}); book.put("C", {"StarBloom": 1})
    assert book.collisions == 2
    recipe, slot, compared = book.lookup("C")
    assert recipe == {"StarBloom": 1} and slot == 0 and compared == 3     # had to walk the chain


def test_cauldron_window_shows_recipes_from_the_lookup_and_explains_starlit():
    g, calls = fresh_game()
    g["known_places"].add("Cauldron"); g["cauldron_open"]()
    data = [c for c in calls if c[0] == "cauldron"][-1][1]
    starlit = [p for p in data["potions"] if p["name"] == "Starlit Elixir"][0]
    assert "lookup" in starlit and starlit["lookup"]["compared"] >= 1
    assert "along the way" in starlit["note"] and len(starlit["ingredients"]) == 6
    assert data["book"]["slots"] == g["recipe_book"].size


def test_brewing_still_works_through_the_recipe_book():
    g, calls = fresh_game()
    for plant in ["MoonCatnip", "MoonBell"]:
        g["backpack"].add("plant:" + plant, 1)
    g["cauldron_brew"]("Purr-fect Potion")
    assert g["backpack"].get("potion:Purr-fect Potion") == 1 and g["backpack"].get("plant:MoonCatnip") == 0


# ---------- Nyra's reactions ----------
def said(calls):
    return [c for c in calls if c[0] == "dialogue"][-1]


def test_every_plant_has_three_lines_for_each_action():
    g, _ = fresh_game()
    assert set(g["PLANT_REACTIONS"]) == set(g["PLANT_CATALOG"])
    for plant, actions in g["PLANT_REACTIONS"].items():
        assert set(actions) == {"plant", "harvest", "remove"}, plant
        for action, lines in actions.items():
            assert len(lines) == 3 and len(set(lines)) == 3, (plant, action)
            for text, face, mouth in lines:
                assert text and face in ("happy", "passive", "blush") and mouth in ("closed", "open", "blush")


def test_planting_harvesting_and_removing_use_that_plants_lines():
    g, calls = fresh_game(); sampler(g)
    g["plant_seed"](0, "MoonCatnip")
    assert said(calls)[1:] in g["PLANT_REACTIONS"]["MoonCatnip"]["plant"]
    g["get_plot"](0).update(stage="grown", growth=6)
    g["discovered"].add("MoonCatnip")                       # not the first harvest, so no "new page" line
    g["harvest_plant"](0)
    assert said(calls)[1:] in g["PLANT_REACTIONS"]["MoonCatnip"]["harvest"]
    g["plant_seed"](1, "StarBloom")
    g["remove_plant"](1)
    assert said(calls)[1:] in g["PLANT_REACTIONS"]["StarBloom"]["remove"]


def test_nyra_never_says_the_same_plant_line_twice_in_a_row():
    g, calls = fresh_game()
    previous = None
    for _ in range(60):
        g["plant_reaction"]("HeartBlossom", "plant")
        text = said(calls)[1]
        assert text != previous
        previous = text


def test_clicking_nyra_follows_time_weather_and_blushes_every_third_time():
    g, calls = fresh_game()
    g["nyra_poke"](); first = said(calls)
    assert first[1:] in g["NYRA_POKES"]["day"] and first[2] != "blush"
    g["nyra_poke"]()
    assert said(calls)[1:] in g["NYRA_POKES"]["day"]
    g["nyra_poke"]()
    assert said(calls)[1:] in g["NYRA_POKES"]["blush"] and said(calls)[2] == "blush"
    g["time_of_day"] = "Night"; g["nyra_poke"]()                          # 4th click
    assert said(calls)[1:] in g["NYRA_POKES"]["night"]
    g["today_weather"] = "Rainy"; g["nyra_poke"]()                        # 5th click: rain beats night
    assert said(calls)[1:] in g["NYRA_POKES"]["rain"]
    g["nyra_poke"]()                                                      # 6th click: blush again
    assert said(calls)[2] == "blush"


def test_nyra_gives_different_lines_when_poked_a_lot():
    g, calls = fresh_game()
    texts = []
    for _ in range(30):
        g["nyra_poke"](); texts.append(said(calls)[1])
    assert len(set(texts)) >= 8 and all(a != b for a, b in zip(texts, texts[1:]))


# ---------- Levels and unlocking ----------
def grow_and_harvest(g, position, plant):
    g["backpack"].add("seed:" + plant, 1)
    g["plant_seed"](position, plant)
    g["get_plot"](position).update(stage="grown", growth=g["PLANT_CATALOG"][plant].growth_needed)
    g["harvest_plant"](position)


def test_xp_reaches_levels_and_stops_at_the_top():
    g, calls = fresh_game(level=1)
    player = g["player"]
    assert (player.level, player.xp, player.xp_for_next()) == (1, 0, 20)
    assert player.gain(19) == [] and player.level == 1
    assert player.gain(1) == [2] and player.level == 2 and player.xp_into_level() == 0 and player.xp_for_next() == 30
    assert player.gain(1000) == [3, 4, 5, 6] and player.level == g["MAX_LEVEL"] == 6          # several levels at once
    assert player.xp_for_next() == 0                                                         # nothing left to reach


def test_undo_takes_xp_back_but_never_a_level():
    g, _ = fresh_game(level=1)
    player = g["player"]; player.gain(25)                         # level 2, 5 XP into it
    player.take_back(100)
    assert player.level == 2 and player.xp == 20                  # stops at the start of level 2


def test_harvest_gives_xp_with_a_bonus_for_a_new_herbarium_page():
    g, calls = fresh_game(level=1)
    grow_and_harvest(g, 0, "SunPetal")                            # 6 XP + 10 for its new page
    assert g["player"].xp == 16 and "+16 XP" in [c for c in calls if c[0] == "message"][-1][1]
    assert last(calls, "level")[1:] == (1, 16, 20, False)
    grow_and_harvest(g, 1, "MoonCatnip")                          # the starter plant's page is already open: just 6 -> 22 XP, level 2
    assert g["player"].level == 2 and last(calls, "level")[1:] == (2, 2, 30, True)


def test_level_up_says_what_just_unlocked():
    g, calls = fresh_game(level=1)
    g["award_xp"](20)
    text = last(calls, "dialogue")[1]
    assert text.startswith("Level 2!") and "Frostmint seeds" in text and "SunnySide Elixir recipe" in text
    g["award_xp"](30)                                            # level 3
    assert "MoonBell seeds" in last(calls, "dialogue")[1] and "HeartBlossom seeds" in last(calls, "dialogue")[1]
    g["award_xp"](40)                                            # level 4 opens nothing new
    assert last(calls, "dialogue")[1] == "Level 4! I feel stronger already!"


def test_harvest_undo_harvest_cannot_farm_xp():
    g, _ = fresh_game(level=1)
    g["backpack"].add("seed:SunPetal", 1); g["plant_seed"](0, "SunPetal")
    g["get_plot"](0).update(stage="grown", growth=6)
    g["harvest_plant"](0)                                         # 6 XP + 10 page bonus
    assert g["player"].xp == 16
    for _ in range(5):
        g["undo_action"](); g["harvest_plant"](0)
    assert g["player"].xp == 16                                   # the page bonus stayed; the 6 XP never piled up


def test_locked_seeds_cannot_be_bought_until_their_level():
    g, calls = fresh_game(level=1)
    g["resources"].coins = 100
    start_bell, start_star = seeds(g, "MoonBell"), seeds(g, "StarBloom")      # both 0: the pouch only has MoonCatnip
    g["buy_seed"]("MoonBell")
    assert g["resources"].coins == 100 and seeds(g, "MoonBell") == start_bell
    assert "unlock at level 3" in last(calls, "message")[1]
    g["shop_set_view"]("buy", "name", "Merge Sort", False)
    rows = {r["name"]: r for r in last(calls, "shop")[1]["rows"]}
    assert [rows[n]["locked"] for n in ("MoonCatnip", "SunPetal", "Frostmint", "MoonBell", "StarBloom")] == [False, False, True, True, True]
    assert rows["StarBloom"]["unlock_level"] == 5
    g["player"].gain(200)                                         # up to level 5
    g["buy_seed"]("MoonBell"); g["buy_seed"]("StarBloom")
    assert seeds(g, "MoonBell") == start_bell + 1 and seeds(g, "StarBloom") == start_star + 1


def test_locked_recipes_show_only_a_silhouette():
    g, calls = fresh_game(level=1)
    g["known_places"].add("Cauldron"); g["cauldron_open"]()
    potions = last(calls, "cauldron")[1]["potions"]
    assert [p["locked"] for p in potions] == [True, True, True] and all(p["name"] == "???" and p["ingredients"] == [] for p in potions)
    assert {p["art"] for p in potions} == set(g["POTION_CATALOG"])
    g["player"].gain(20); g["refresh_cauldron_ui"]()              # level 2
    potions = {p["art"]: p for p in last(calls, "cauldron")[1]["potions"]}
    assert potions["SunnySide Elixir"]["locked"] is False and potions["SunnySide Elixir"]["name"] == "SunnySide Elixir"
    assert potions["Purr-fect Potion"]["locked"] is True and potions["Purr-fect Potion"]["unlock_level"] == 3


def test_brewing_a_locked_recipe_is_refused():
    g, calls = fresh_game(level=1)
    g["known_places"].add("Cauldron")
    for plant in ("SunPetal", "Frostmint"):
        g["backpack"].add("plant:" + plant, 1)
    g["cauldron_brew"]("SunnySide Elixir")
    assert g["backpack"].get("potion:SunnySide Elixir") == 0 and g["backpack"].get("plant:SunPetal") == 1
    assert "level 2" in last(calls, "cauldron")[1]["message"]
    assert g["brew_one"]("SunnySide Elixir") is False


def test_nyras_advice_only_uses_recipes_she_has_learned():
    g, calls = fresh_game(level=2)                                # only SunnySide Elixir is learned
    g["known_places"].add("Cauldron"); g["today_weather"] = "Sunny"
    for plant in g["PLANT_CATALOG"]:
        g["backpack"].add("plant:" + plant, 1)
    g["cauldron_ask"]()
    advice = last(calls, "cauldron")[1]["advice"]
    assert [item["name"] for item in advice["plan"]] == ["SunnySide Elixir"]
    g["player"].level = 5; g["cauldron_ask"]()                    # now Starlit Elixir is learned too
    assert "Starlit Elixir" in [item["name"] for item in last(calls, "cauldron")[1]["advice"]["plan"]]


def test_brewing_gives_xp_with_a_bonus_for_a_new_page():
    g, calls = fresh_game(level=5)
    g["known_places"].add("Cauldron")
    for plant in g["PLANT_CATALOG"]:
        g["backpack"].add("plant:" + plant, 2)
    before = g["player"].xp
    g["cauldron_brew"]("Starlit Elixir")                          # 30 XP + 10 new page
    assert g["player"].xp == before + 40
    g["cauldron_brew"]("Starlit Elixir")                          # page already known
    assert g["player"].xp == before + 70


def test_finding_a_new_place_gives_xp():
    g, _ = fresh_game(level=1)
    g["map_explore"]()
    assert g["player"].xp == g["MAP_PLACE_XP"] == 4


def test_unlock_levels_make_sense():
    g, _ = fresh_game()
    plants, potions = g["PLANT_CATALOG"], g["POTION_CATALOG"]
    assert plants["MoonCatnip"].unlock_level == 1                 # the starter seeds can be bought from the start
    for plant in plants.values():
        assert 1 <= plant.unlock_level <= g["MAX_LEVEL"] and plant.xp == plant.grow_days * 3
    for potion in potions.values():                               # nobody learns a recipe before they can get its plants
        assert 1 <= potion.unlock_level <= g["MAX_LEVEL"]
        assert potion.unlock_level >= max(plants[name].unlock_level for name in potion.ingredients), potion.name
    reachable = sum(len(g["unlocks_for_level"](level)) for level in range(1, g["MAX_LEVEL"] + 1))
    assert reachable == len(plants) + len(potions)                # everything unlocks at some level


# ---------- Sounds and the level-up celebration ----------
def new_sounds(calls, since):
    return [c[1] for c in calls[since:] if c[0] == "sound"]


def test_actions_ask_for_their_sounds():
    g, calls = fresh_game(level=1); sampler(g); g["known_places"].add("Cauldron")
    def after(action):
        since = len(calls); action(); return new_sounds(calls, since)
    assert after(lambda: g["plant_seed"](0, "SunPetal")) == ["plant"]
    g["get_plot"](0).update(stage="grown", growth=6)
    assert sorted(after(lambda: g["harvest_plant"](0))) == ["harvest", "page"]  # SunPetal's Herbarium page is new (the page chime is delayed in main.js)
    assert after(lambda: g["undo_action"]()) == ["undo"]
    g["harvest_plant"](0)
    g["plant_seed"](1, "MoonCatnip")
    assert after(lambda: g["remove_plant"](1)) == ["remove"]
    g["resources"].coins = 50
    assert after(lambda: g["buy_seed"]("MoonCatnip")) == ["coin"]
    assert after(lambda: g["sell_plant"]("SunPetal", 1)) == ["coin"]
    assert after(lambda: g["skip_time"]()) == ["night"]
    assert after(lambda: g["skip_time"]()) == ["morning"]
    assert after(lambda: g["map_explore"]()) == ["discover", "levelup"]          # the +4 XP happens to complete level 2 (16 + 4 = 20)
    g["player"].level = 5
    for plant in ("MoonCatnip", "MoonBell", "SunPetal", "Frostmint", "HeartBlossom", "StarBloom"):
        g["backpack"].add("plant:" + plant, 1)
    assert after(lambda: g["cauldron_brew"]("Starlit Elixir")) == ["page", "brew"]
    assert after(lambda: g["nyra_poke"]()) == ["nyra"]
    g["nyra_poke"]()
    assert after(lambda: g["nyra_poke"]()) == ["nyra_blush"]                    # every third click


def test_level_up_celebration_lists_what_unlocked_and_plays_a_sound():
    g, calls = fresh_game(level=1)
    since = len(calls); g["award_xp"](10)                                         # not enough for level 2
    assert not [c for c in calls[since:] if c[0] == "levelup"] and "levelup" not in new_sounds(calls, since)
    g["award_xp"](40)                                                             # 50 XP in total: levels 2 AND 3 at once
    level, unlocks = last(calls, "levelup")[1:]
    assert level == 3 and set(unlocks) == {"Frostmint seeds", "MoonBell seeds", "HeartBlossom seeds",
                                           "the SunnySide Elixir recipe", "the Purr-fect Potion recipe"}
    assert new_sounds(calls, since)[-1] == "levelup"
    g["award_xp"](40)                                                             # level 4 opens nothing new
    assert last(calls, "levelup")[1:] == (4, [])



# ---------- Cauldron animation report (what the screen throws into the cauldron) ----------
def test_brewing_reports_which_plants_were_thrown_in_exactly_once():
    g, calls = fresh_game()
    g["known_places"].add("Cauldron")                             # (the helper starts at the top level: every recipe is learned)
    for plant in ["MoonCatnip", "MoonBell"]:
        g["backpack"].add("plant:" + plant, 1)
    g["cauldron_brew"]("Purr-fect Potion")
    sent = [c[1] for c in calls if c[0] == "cauldron"]
    brewed = [d["brewed"] for d in sent if d["brewed"]]
    assert len(brewed) == 1 and brewed[0][0]["potion"] == "Purr-fect Potion"
    assert sorted(brewed[0][0]["plants"]) == ["MoonBell", "MoonCatnip"]
    g["cauldron_open"]()
    assert [c[1] for c in calls if c[0] == "cauldron"][-1]["brewed"] == []       # not repeated


def test_brewing_a_whole_plan_reports_every_potion():
    g, calls = fresh_game()
    g["known_places"].add("Cauldron")
    for plant in ["MoonCatnip", "MoonBell", "SunPetal", "Frostmint"]:
        g["backpack"].add("plant:" + plant, 1)
    g["cauldron_brew_plan"]()
    names = [item["potion"] for c in calls if c[0] == "cauldron" for item in c[1]["brewed"]]
    assert sorted(names) == ["Purr-fect Potion", "SunnySide Elixir"]


def test_a_recipe_nyra_has_not_learned_reports_nothing_to_throw():
    g, calls = fresh_game(level=1)
    g["known_places"].add("Cauldron")
    for plant in ["MoonCatnip", "MoonBell"]:
        g["backpack"].add("plant:" + plant, 1)
    g["cauldron_brew"]("Purr-fect Potion")                             # unlocks at level 3
    assert [item for c in calls if c[0] == "cauldron" for item in c[1]["brewed"]] == []
    assert g["backpack"].get("plant:MoonCatnip") == 1                  # nothing was used up



# ---------- Secret codes (cheat codes) ----------
def enter(g, text):
    g["apply_secret_code"](text)


def code_answer(calls):
    return [c for c in calls if c[0] == "code"][-1]


def test_code_book_finds_every_code_and_nothing_else():
    g, _ = fresh_game()
    for code, action in g["SECRET_CODES"].items():
        found, slot, compared = g["code_book"].lookup(code)
        assert found is action and 0 <= slot < g["code_book"].size and compared >= 1
    assert g["code_book"].lookup("pizza")[0] is None


def test_code_book_chains_codes_that_share_a_slot():
    g, _ = fresh_game(); book = g["CodeBook"](size=1)
    for name in ["a", "b", "c"]:
        book.put(name, name)
    assert book.collisions == 2 and book.lookup("c") == ("c", 0, 3)


def test_codes_ignore_capitals_spaces_and_dashes():
    g, calls = fresh_game(level=1)
    for typed in ["LEVELUP", "level up", "Level-Up", "  levelUP  "]:
        before = g["player"].level
        enter(g, typed)
        assert g["player"].level == before + 1 and code_answer(calls)[2] is True


def test_unknown_and_empty_codes_do_nothing():
    g, calls = fresh_game()
    enter(g, "pizza"); assert code_answer(calls)[1].startswith("That code doesn't do anything") and code_answer(calls)[2] is False
    enter(g, "   "); assert code_answer(calls)[1] == "Type a code first."
    assert g["codes_used"] == 0


def test_levelup_gives_exactly_one_level_and_a_celebration():
    g, calls = fresh_game(level=1)
    enter(g, "levelup")
    assert g["player"].level == 2 and g["player"].xp == g["LEVEL_XP"][1]
    assert any(c[0] == "levelup" and c[1] == 2 for c in calls)
    enter(g, "levelup"); assert g["player"].level == 3


def test_maxlevel_unlocks_everything_in_one_celebration():
    g, calls = fresh_game(level=1)
    enter(g, "maxlevel")
    assert g["player"].level == g["MAX_LEVEL"]
    assert len([c for c in calls if c[0] == "levelup"]) == 1
    enter(g, "maxlevel"); assert "already at the top level" in code_answer(calls)[1] and code_answer(calls)[2] is False
    enter(g, "levelup"); assert code_answer(calls)[2] is False


def test_rich_gives_500_coins():
    g, calls = fresh_game(); before = g["resources"].coins
    enter(g, "rich")
    assert g["resources"].coins == before + 500 and [c for c in calls if c[0] == "coins"][-1][1] == before + 500


def test_seeds_and_plants_only_cover_what_is_unlocked():
    g, _ = fresh_game(level=1)
    start = {name: g["backpack"].get("seed:" + name) for name in g["PLANT_CATALOG"]}
    enter(g, "seeds")
    for name, plant in g["PLANT_CATALOG"].items():
        gained = g["backpack"].get("seed:" + name) - start[name]
        assert gained == (5 if plant.unlock_level <= 1 else 0), name
    enter(g, "plants")
    assert g["backpack"].get("plant:MoonCatnip") == 3 and g["backpack"].get("plant:StarBloom") == 0


def test_growall_makes_every_growing_plant_ready():
    g, calls = fresh_game()
    enter(g, "growall"); assert code_answer(calls)[2] is False                   # nothing planted yet
    sampler(g)
    g["plant_seed"](0, "MoonCatnip"); g["plant_seed"](1, "SunPetal")
    enter(g, "growall")
    assert g["get_plot"](0)["stage"] == "grown" and g["get_plot"](1)["stage"] == "grown"
    g["harvest_plant"](0); assert g["backpack"].get("plant:MoonCatnip") == 1       # and they can really be harvested


def test_explore_and_pages_open_everything_once():
    g, calls = fresh_game()
    enter(g, "explore"); assert set(g["known_places"]) == set(g["MAP_PLACES"]) and code_answer(calls)[2] is True
    enter(g, "explore"); assert code_answer(calls)[2] is False
    enter(g, "pages"); assert set(g["discovered"]) == set(g["HERBARIUM_ENTRIES"])
    enter(g, "pages"); assert code_answer(calls)[2] is False


def test_skiptime_moves_the_clock_and_codes_are_counted():
    g, calls = fresh_game()
    before = (g["day"], g["time_of_day"])
    enter(g, "skiptime")
    assert (g["day"], g["time_of_day"]) != before and g["codes_used"] == 1
    enter(g, "codes"); assert "LEVELUP" in code_answer(calls)[1] and g["codes_used"] == 2
    enter(g, "pizza"); assert g["codes_used"] == 2                                # failures are not counted


# ---------- The easter egg ----------
def test_the_secret_word_starts_the_egg_silently():
    g, calls = fresh_game()
    for typed in ("ItsAllAHoax", "its all a hoax", "ITS-ALL-A-HOAX", "  itsallahoax!  "):
        since = len(calls); g["apply_secret_code"](typed)
        starts = [c for c in calls[since:] if c[0] == "egg_start"]
        assert len(starts) == 1, typed
        assert not [c for c in calls[since:] if c[0] == "code"]          # no message under the box
    assert g["egg"]["attempts"] == 4 and g["codes_used"] == 0                    # not counted as a cheat code


def test_the_egg_is_hidden_from_the_code_list():
    g, calls = fresh_game()
    assert "itsallahoax" not in g["SECRET_CODES"]
    g["apply_secret_code"]("codes")
    shown = [c for c in calls if c[0] == "code"][-1]
    assert "HOAX" not in shown[1].upper() and "ITSALLAHOAX" not in shown[1].upper().replace(" ", "")
    assert g["code_book"].lookup("itsallahoax")[0] is not None                  # but it IS in the code book


def test_the_egg_start_has_two_lines_from_nyra():
    g, calls = fresh_game()
    g["apply_secret_code"]("itsallahoax")
    data = [c for c in calls if c[0] == "egg_start"][-1][1]
    assert tuple(data["intro"]) in g["EGG_INTRO"] and tuple(data["cutoff"]) in g["EGG_CUTOFF"]
    assert data["cutoff"][0].endswith("—")                                       # cut off in the middle of a word
    for pool in (g["EGG_INTRO"], g["EGG_CUTOFF"]):
        assert len(pool) >= 3 and len(set(pool)) == len(pool)
        assert all(face in ("happy", "passive", "blush") and mouth in ("closed", "open", "blush") for _t, face, mouth in pool)


def test_the_egg_lines_change_between_tries():
    g, calls = fresh_game()
    intros = []
    for _ in range(12):
        g["apply_secret_code"]("itsallahoax"); intros.append([c for c in calls if c[0] == "egg_start"][-1][1]["intro"][0])
    assert len(set(intros)) >= 2 and all(a != b for a, b in zip(intros, intros[1:]))


def test_winning_the_egg_welcomes_the_player_back_and_losing_does_not():
    g, calls = fresh_game()
    g["egg_result"]("lose")
    assert not [c for c in calls if c[0] == "egg_welcome"] and g["egg"]["cleared"] is False      # as if nothing happened
    g["egg_result"]("win")
    welcome = [c for c in calls if c[0] == "egg_welcome"][-1][1]
    assert g["egg"]["cleared"] is True and len(welcome) == 2
    assert [tuple(line) for line in welcome] in [list(map(tuple, seq)) for seq in g["EGG_WELCOME"]]
    assert all(face in ("happy", "passive", "blush") for _text, face, _mouth in welcome)
    g["egg_result"]("lose")
    assert g["egg"]["cleared"] is True                                           # clearing it once is remembered


def test_ordinary_codes_still_work_and_unknown_ones_still_answer():
    g, calls = fresh_game(level=1)
    g["apply_secret_code"]("rich")
    assert [c for c in calls if c[0] == "code"][-1][1].startswith("+500 coins") and g["codes_used"] == 1
    g["apply_secret_code"]("itsnotahoax")
    assert "doesn't do anything" in [c for c in calls if c[0] == "code"][-1][1]


if __name__ == "__main__":
    tests = [f for name, f in sorted(globals().items()) if name.startswith("test_")]
    for t in tests:
        t(); print("ok  ", t.__name__)
    print(f"\nAll {len(tests)} checks passed!")
