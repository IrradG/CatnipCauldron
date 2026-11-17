"""Catnip Cauldron - Herbarium TEXT (data only, no game rules).

All the words in the Herbarium book live here, so they are easy to edit.
game_state.py reads these two things:

  HERBARIUM_TREE     which categories exist and which entries belong in them
  HERBARIUM_ENTRIES  the quote and the sections shown on the right-hand page

Each entry:  "kind" ("plant" or "potion"), "quote" (None = no quote), and
"sections" = a list of [title, text] pairs shown in order.
"""

# ---------------------------------------------------------------------
# The shape of the book (this becomes a TREE in game_state.py - Lesson 4)
# ---------------------------------------------------------------------
HERBARIUM_TREE = {
    "Plants": {
        "Herbs": ["MoonCatnip", "Frostmint"],
        "Flowers": ["MoonBell", "SunPetal", "HeartBlossom", "StarBloom"],
    },
    "Potions": {
        "Basic": ["Purr-fect Potion", "SunnySide Elixir"],
        "Rare": ["Starlit Elixir"],
    },
}

# ---------------------------------------------------------------------
# The pages
# ---------------------------------------------------------------------
HERBARIUM_ENTRIES = {
    # ----------------------------- PLANTS -----------------------------
    "MoonCatnip": {
        "kind": "plant",
        "quote": "A rather curious little plant. I wonder if cats are naturally drawn to it, or if it simply likes their company?",
        "sections": [
            ["Appearance", "A small leafy plant with soft green foliage and tiny purple flowers resembling cat ears. Its petals give off a faint glow under moonlight."],
            ["Habitat", "Usually found in quiet woodland clearings, beneath old trees, and near places where moonlight reaches the ground."],
            ["Growth & Blooming", "MoonCatnip grows throughout the day but becomes most active at night. Its little flowers open under the moonlight, releasing a gentle, sweet fragrance."],
            ["Nyra's Notes", "Cats seem particularly fond of this plant. I've even caught a few sleeping beside it! Perhaps I should plant some near the garden entrance."],
        ],
    },
    "MoonBell": {
        "kind": "plant",
        "quote": "They look like tiny bells hanging from the night sky. If only they could actually ring!",
        "sections": [
            ["Appearance", "Delicate lavender flowers shaped like little hanging bells. Their petals have a soft silvery sheen, especially at night."],
            ["Habitat", "Commonly grows near ponds, shaded forest paths, and damp patches of soil protected from direct sunlight."],
            ["Growth & Blooming", "MoonBell prefers cool surroundings. Its flowers remain closed during most of the day and slowly open as evening approaches, blooming brightest under a clear night sky."],
            ["Nyra's Notes", "The flowers seem to sway even when there's no breeze. I wonder if they're responding to the moonlight?"],
        ],
    },
    "SunPetal": {
        "kind": "plant",
        "quote": "A cheerful flower that seems to enjoy sunny mornings as much as I do!",
        "sections": [
            ["Appearance", "Bright golden-orange petals arranged like little rays of sunlight around its center. Its leaves are broad and sturdy."],
            ["Habitat", "Grows mainly in open fields, sunny hillsides, and garden patches with plenty of direct sunlight."],
            ["Growth & Blooming", "SunPetal thrives during the daytime. Its petals gradually open as sunlight reaches them, allowing it to absorb warmth and light. The flowers begin closing as the sun sets."],
            ["Nyra's Notes", "These flowers seem to lean toward the brightest part of the garden. Make sure they aren't planted beneath large trees!"],
        ],
    },
    "Frostmint": {
        "kind": "plant",
        "quote": "Brr! Even touching its leaves feels like holding a tiny piece of winter.",
        "sections": [
            ["Appearance", "A low-growing herb with cool teal leaves and tiny crystal-like formations along its edges. A thin layer of frost sometimes gathers around its stems."],
            ["Habitat", "Usually found in cool mountain valleys, shaded caves, and areas near cold springs."],
            ["Growth & Blooming", "Frostmint prefers cold environments and grows best away from intense sunlight. Its leaves develop a stronger crystalline coating during particularly chilly nights."],
            ["Nyra's Notes", "Handle this one carefully! Its leaves are surprisingly cold. I once placed a freshly picked leaf beside my tea. The tea was cold before I could even take a sip!"],
        ],
    },
    "HeartBlossom": {
        "kind": "plant",
        "quote": None,      # no quote written yet
        "sections": [
            ["Appearance", "A beautiful pink flower with heart-shaped petals surrounding a small glowing center. Its leaves are rounded and soft."],
            ["Habitat", "Found in peaceful meadows, secluded gardens, and forest clearings where the soil is rich and healthy."],
            ["Growth & Blooming", "HeartBlossom grows best in mild weather. Its flowers usually bloom during the morning and remain open until late afternoon. They are especially vibrant after gentle rainfall."],
            ["Nyra's Notes", "The petals are quite delicate, so avoid picking them roughly. I prefer to collect only the flowers that have fully bloomed."],
        ],
    },
    "StarBloom": {
        "kind": "plant",
        "quote": "A flower that only reveals its true beauty when the stars come out. How magical!",
        "sections": [
            ["Appearance", "A violet flower with several pointed, star-shaped petals. Tiny specks of light can occasionally be seen floating around its center."],
            ["Habitat", "Grows in secluded mountain gardens, high-altitude meadows, and places with a clear view of the night sky."],
            ["Growth & Blooming", "StarBloom grows slowly and requires plenty of time to mature. Its flowers remain closed during daylight and open only after dusk. Their glow becomes brighter when the night sky is filled with stars."],
            ["Nyra's Notes", "These flowers are rather difficult to find. I've heard that they are more common in places untouched by artificial light. I should definitely investigate!"],
        ],
    },

    # ----------------------------- POTIONS -----------------------------
    "Purr-fect Potion": {
        "kind": "potion",
        "quote": "A little bottle of peace and comfort. My feline friends seem to approve!",
        "sections": [
            ["Appearance", "A small glass bottle filled with a lovely lavender-colored liquid. Tiny bubbles float inside, while its stopper resembles a pair of adorable cat ears."],
            ["Ingredients", "MoonCatnip and MoonBell."],
            ["Brewing Notes", "When both ingredients are mixed, the liquid gradually turns lavender. A gentle, sweet fragrance appears as the potion finishes brewing."],
            ["Effects", "Produces a soothing and relaxing effect, helping ease tension and calm restless minds."],
            ["Nyra's Notes", "A favorite among my little visitors! Just don't leave the bottle unattended around curious cats. I've learned that lesson already!"],
        ],
    },
    "SunnySide Elixir": {
        "kind": "potion",
        "quote": "A bottle of sunshine! Perfect for those gloomy and sluggish days.",
        "sections": [
            ["Appearance", "A bright golden-orange elixir contained in a rounded glass bottle. Its stopper resembles a little sun, with warm sparkles occasionally dancing around the liquid."],
            ["Ingredients", "SunPetal and Frostmint."],
            ["Brewing Notes", "The mixture begins with a cool, minty hue before gradually becoming golden as the ingredients combine. A warm glow signals that the brewing process is complete."],
            ["Effects", "Provides a refreshing burst of energy and helps restore one's vitality."],
            ["Nyra's Notes", "Quite useful when working in the garden all day! Though I must remember not to drink too much before bedtime. Hehehe!"],
        ],
    },
    "Starlit Elixir": {
        "kind": "potion",
        "quote": "A little wonder captured beneath the stars. Definitely one of my proudest creations!",
        "sections": [
            ["Appearance", "A beautiful pink-purple potion with shimmering golden particles suspended inside. Its stopper is decorated with a tiny star, and the liquid seems to glow softly even in darkness."],
            ["Ingredients", "Purr-fect Potion, SunnySide Elixir, HeartBlossom, and StarBloom."],
            ["Brewing Notes", "Combining the two basic potions creates a swirling mixture. Adding HeartBlossom and StarBloom slowly transforms it into a luminous pink-purple elixir. The final golden sparkles indicate a successful brew."],
            ["Effects", "A rare and powerful elixir that combines the soothing properties of Purr-fect Potion with the revitalizing qualities of SunnySide Elixir. Its additional magical properties are still being studied."],
            ["Nyra's Notes", "This recipe took me quite a while to perfect! The StarBloom is especially important, so make sure to use a fully matured flower. I wouldn't want another failed experiment!"],
        ],
    },
}
