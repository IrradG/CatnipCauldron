# Catnip Cauldron — starter project

## What is included
- `index.html`: menu and garden screen structure.
- `css/style.css`: cozy layout and responsive styling.
- `js/main.js`: menu navigation and temporary garden demo interactions.
- `js/nyra.js`: Nyra expression selection and random blinking.
- `python/game_state.py`: first Python game-state lesson starter.
- `assets/`: put your own exported PNG files in the matching folders.

## Add your art
Move your PNG files into these folders without renaming them:
- Nyra sprites -> `assets/nyra/`
- plant sprites -> `assets/plants/`
- potion sprites -> `assets/potions/`
- backgrounds -> `assets/backgrounds/`
- buttons/UI -> `assets/ui/`

The code expects the background files to be named exactly:
- `CatnipCauldron(MainScreen).png`
- `CatnipCauldron(PlantingArea).png`

The Nyra mapping in `js/nyra.js` expects:
- `Nyra_Passive(1).png`, `Nyra_Passive(2).png`, `Nyra_Passive(3).png`, `Nyra_Passive(Blink).png`
- Same pattern for `Nyra_Happy` and `Nyra_Blush`.

If your actual files have different capitalization or spacing, update the path strings in the code. Some systems treat capitalization as important.

## Run the project
Because this project will load local files and Pyodide, run it through a local development server rather than double-clicking `index.html`.
One beginner-friendly option, if Python is installed:
1. Open a terminal in the `CatnipCauldron` folder.
2. Run: `python -m http.server 8000`
3. Open `http://localhost:8000` in your browser.

The first UI prototype does not require Python game logic yet. It currently uses JavaScript for a simple demonstration: select a plot, plant MoonCatnip, then use Harvest to advance it to grown and harvest it. This is temporary; real growth, plant selection, potions, and saving will be added in later steps.

## Note
The game is a work in progress. The image paths are wired for the expected filenames, but the asset folders are empty in this starter download because your original PNGs are on your computer and were not uploaded here.

## Where the rules live (Day 5)
- `python/game_state.py` is the game's brain. Planting, harvesting, removing, seeds, and the 5x5 garden grid are all Python.
  Each section is tagged with its lesson (Lesson 1 stack, Lesson 3 2D list, Lesson 12 resources).
- `js/main.js` only draws things and forwards clicks to Python through small bridge functions
  (`updateSeeds`, `drawPlot`, `setMessage`, `showDialogue`).
- Python loads through Pyodide, so open the game with a local server and an internet connection.
  The Play button says "Loading..." until Python is ready.
- `python/test_game_state.py` checks the rules: `python python/test_game_state.py`

## Step 1 of the 12-lesson plan (Day 9)
New in `python/game_state.py` (all tested in `python/test_game_state.py`):
- **Lesson 1** - `Plant` objects + the Undo history **stack** (Undo button, top-left).
- **Lesson 2** - the weather forecast **queue** (`deque`). "Skip Time" takes the front of the queue (the sky for the next time slot) and plants grow with it.
- **Lesson 6** - the backpack is a **hash table** (separate chaining + rehashing). Open the backpack and press "Peek inside" to see it.
- **Lesson 12** - coins (and seeds per plant) as resources.
- Plants no longer grow instantly: press Skip Time. Harvest gives the plant into the backpack (and a seed back until the Shop exists).

## Step 2 (Day 10): the Shop and sorting
- **Lesson 8** - five sorting algorithms written by hand in `python/game_state.py` (Bubble, Insertion, Selection, Merge, Quick). Each one counts its comparisons, so the Shop and the Backpack can show "Sorted by price with Bubble Sort (O(n^2)) - 9 comparisons".
- **Lesson 12** - coins: buy seeds, sell harvested plants. Open the Shop from the extra buttons (arrow tab) in the garden.
- Harvesting no longer gives a seed back - buy seeds in the Shop instead.
- Backpack has sort controls too (Name / Count, any algorithm, ascending or descending).
- Prices and grow days are in `PLANT_CATALOG` near the top of the Python file.

## Step 3 (Day 11): the Herbarium (Lessons 4, 5, 9) + renaming
- **MoonBloom is now MoonBell** (files and code).
- `python/herbarium_data.py` holds all the book text (quotes, appearance, habitat, Nyra's notes, potion recipes). Edit it freely.
- **Lesson 4** - the book's categories are a **tree**. "Depth-first" walks it with a stack, "Breadth-first" with a queue.
- **Lesson 5** - every entry sits in a **binary search tree**; the "A-Z" order is an in-order walk of it.
- **Lesson 9** - search by name with **Binary**, **BST** or **Linear** search. The book shows which entries each one looked at and how many steps it took.
- A plant's page unlocks the first time you harvest it (MoonCatnip starts unlocked). Potions unlock once the Cauldron exists.

## Code map
- `js/main.js` starts with a FILE MAP and numbered "SECTION n" banners.
- `css/style.css` starts with a FILE MAP too.
- `python/game_state.py` starts with a LESSON MAP; every part is tagged with its lesson and Big O notes.
- Run the Python checks with: `python python/test_game_state.py`

## Bug fix (after Day 11)
- Selling a plant or buying a seed now clears the Undo history (they can't be undone), so "harvest -> sell -> Undo" no longer gives a free plant. Undo-harvest also refuses if the plant is no longer in the backpack. 3 new checks were added (34 total).

## Step 4: the Map (Lesson 7)
- Open the **Map** from the extra buttons (arrow tab) in the garden. Its icon is my map drawing placed on YOUR `IconImage(Border)` art: `assets/ui/CatnipCauldron_IconImage(Map).png` - replace it with your own art any time (same name, 512x512).
- `python/game_state.py` -> "THE MAP": a **graph** stored as an adjacency list (`PlaceGraph`), 8 places and 9 paths (`MAP_PLACES`, `MAP_ROADS` - edit these to change the world).
- **Breadth-first** (a queue) scouts nearby places first. **Depth-first** (a stack) follows one trail as far as it goes. Press **Explore!** and Nyra discovers the next unseen place *in that walk's order*, so BFS and DFS find different places first.
- The Garden -> Woods -> Spring -> Pond -> Garden loop is on purpose: it shows why a walk must remember visited places.
- 7 new checks in `python/test_game_state.py` for this step.

## Step 5: routes on the Map (Lesson 10)
- The path **minutes** now matter. Nyra only plans through places she has **discovered**, so exploring improves her routes.
- **Cheapest way there** (Dijkstra, with a min-heap): pick a place on the map, press the button, and the cheapest route lights up in pink. It is compared with the fewest-stops route a breadth-first walk would take - to the Mountain they differ (9 min vs 11 min)! The "Dijkstra settled" line shows the order places were finalised.
- **Errand trip** (greedy): visit every discovered place and come home. Greedy always walks to the nearest unvisited stop. The game also tries every order (brute force, n!) so you can see when greedy gets fooled (34 min vs 29 min once everything is discovered; with fewer places it is often a tie).
- Path times changed slightly to make the lesson interesting: Garden-Pond 3, Woods-Mountain 8 (edit `MAP_ROADS`).
- 8 new checks (49 total), including one that proves Dijkstra equals trying every possible path.

## Step 6: the Cauldron (Lesson 11, dynamic programming)
- **Finding it:** the Cauldron is a place on the Map. Nyra has to **discover it** (press Explore on the Map) before the Cauldron button (new, in the extras tab) opens it.
- **Potions are objects** (`Potion`, `POTION_CATALOG`) with recipes. Brewing uses up plants from the backpack, adds a potion, and **unlocks its Herbarium page** the first time. Brewed potions appear in the Backpack's Potions tab and can be sold in the Shop (the Shop's second tab is now just "Sell").
- **Weather changes prices:** rain -> Purr-fect Potion x1.5, cold snap -> SunnySide Elixir x1.5, starry night -> Starlit Elixir x1.25 (`POTION_DEMAND`). So the best brew changes from day to day.
- **Ask Nyra** (`best_brewing_plan`): best(plants) = the larger of "sell every plant as it is" or "brew ONE potion + best(the plants left over)". The answer for each set of leftover plants is remembered (**memoization**), so every different situation is solved once. The window shows how many calls plain recursion would have needed vs. how many situations were solved/reused.
- **Greedy gets fooled again:** "always brew the priciest potion first" loses on a rainy day with one of each plant (80 coins vs. 84 for Purr-fect + SunnySide).
- **Brew Nyra's plan** brews the whole suggestion; you can also brew single potions by hand.
- Brewing, like buying/selling, clears the Undo history (used-up plants can't be put back).
- New art: `CatnipCauldron_IconImage(Cauldron).png` (your Cauldron sprite on your border) and `CatnipCauldron(Cauldron_Window).png` (a lighter 640px copy of the sprite for the window). Your originals are untouched.
- 9 new checks (58 total), including one that tries EVERY possible brew combination and proves the DP answer is the best.

## Still to do
- Water for Lesson 12 (watering plants; rain refills it; Map travel could cost energy).

## Step 7: day and night (Skip Time)
- **Next Day is now Skip Time.** Each press moves from Day to Night, and from Night to the next morning (the day number only goes up in the morning).
- **The queue now holds the sky for each coming time slot** (Clear, Cloudy, Rainy, Cold snap). A clear sky is **Sunny** by day and a **Starry night** at night; rain and cold snaps can happen at either time. Hover the top-left pill to see the forecast with each slot's time, e.g. "Cloudy (night), Rainy (day), ...".
- **Backgrounds** (your four planting-area pictures) crossfade: rain -> rain picture (day or night), clear night -> Starry Night, other nights -> Night, otherwise the day picture. See `scene_for` in `game_state.py` and `setScene` in `main.js`.
- **Plants now like a time of day** (`Plant.likes`, taken from your Herbarium text): MoonCatnip, MoonBell, Frostmint and StarBloom grow best at night; SunPetal and HeartBlossom grow best by day. In its favourite time a plant earns 2 points, otherwise 1; rain adds 1; a starry night adds 1 for Moon and Star plants; a cold snap stops everything except Frostmint (3 points). One ordinary day (Day + Night) still adds up to 3 points for every plant, so the old growth pace is kept (`growth_needed = grow_days x 3`).
- The Herbarium facts line and tapping a growing plant now tell you when it grows best.
- 7 new checks (65 total).

## Step 8: garden weather effects
- **Rain** falls whenever the rain picture is showing (day or night): 140 random drops, some bigger and faster so it feels like depth.
- **Fireflies** drift around, glow and blink on nights without rain (the Night and Starry Night pictures). Some are pink, like on the home screen.
- Both fade in and out with the background crossfade. They sit above the plants and Nyra, but below the dock, dialogue, top bar and windows, and never block clicks.
- The resting effect is paused, so it uses no power. With "reduce motion" turned on in the system settings the rain is hidden and the fireflies stay still.
- Code: `SECTION 16` in `js/main.js` (`buildWeatherEffects`, `setWeatherEffect`) and "Garden weather effects" in `css/style.css`. Numbers like the number of drops are easy to tweak there.

## Bug fix: potions in the Backpack
- Brewed potions were in the backpack but never showed in its **Potions** tab: `updateInventory` in `js/main.js` did not copy the `potions` list that Python sends. It does now.
- The sort line under the Potions tab used the seeds' comparison count; it now has its own (`potions_comparisons`).
- New check in `python/test_game_state.py` (66 total).

## Bucket list (ideas for later)
- (empty for now - the level system below was the last item!)

## Step 9 (Day 14): recipe book + Starlit wording
- **Lesson 6 (recipe lookup):** the Cauldron's recipes now live in `RecipeBook`, a **hash table with chaining** (same idea as the backpack: key = potion name, index = letter-code sum % slots). The Cauldron window and brewing both LOOK UP each recipe there, and each potion card shows "Recipe book lookup (hash table): slot 2, 1 compared".
- **Starlit Elixir** keeps its six-plant recipe for the Cauldron, but its card now explains why: "Nyra brews a Purr-fect Potion and a SunnySide Elixir along the way, so this uses all six plants." (`Potion.note`)
- 4 new checks (70 total), including one that forces every recipe into one slot to prove the chain works.

## Step 10: Nyra's reactions
- **Per-plant lines:** every plant has 3 lines for planting, 3 for harvesting and 3 for removing (`PLANT_REACTIONS` in `game_state.py`, 54 lines in all), each with its own personality and face (MoonCatnip makes her swoon, HeartBlossom makes her blush...). She never says the same line twice in a row. The special "new Herbarium page" line on a first harvest stays.
- **Clickable Nyra:** click her and she reacts (`nyra_poke`). By day, at night and in the rain she says different things, and **every third click she blushes** with her Blush sprite. A few lines hint at the cat ears squished under her hat.
- **Only her body counts:** `SECTION 17` in `main.js` checks the pixel under the mouse, so clicks on the empty space around her still reach the plots, and the cursor turns into a pointer over her. Keyboard players can Tab to an invisible "Say hi to Nyra" button.
- To add or change lines, edit `PLANT_REACTIONS` and `NYRA_POKES` (each line is `(text, face, mouth)`; faces: happy / passive / blush).
- 5 new checks (75 total).

## Step 11: levels and unlocking
- **XP** comes from: harvesting (`Plant.xp` = grow days x 3, so slow plants give more), brewing (`Potion.xp`: 10, 10 and 30), a **brand-new Herbarium page** (+10 bonus) and **finding a new place on the Map** (+4).
- **6 levels** (`LEVEL_XP = [0, 20, 50, 90, 140, 200]` = total XP needed to reach each one). A badge in the top bar shows "Lv N" and a progress bar (hover it for "12/30 XP"); it pops when you level up, and Nyra tells you what just unlocked.
- **Seeds** (Shop, Buy tab): MoonCatnip + SunPetal from level 1, Frostmint at 2, MoonBell + HeartBlossom at 3, StarBloom at 5. Locked seeds are greyed out with "Unlocks at level N" and can't be bought.
- **Recipes** (Cauldron): SunnySide Elixir at level 2, Purr-fect Potion at 3, Starlit Elixir at 5 (each opens together with its ingredients). Locked recipes are dark silhouettes with "Nyra learns this recipe at level N".
- **Nyra's dynamic programming advice only plans with recipes she has learned** (`best_brewing_plan(..., allowed)`).
- **Undo can't farm XP:** undoing a harvest takes its XP back (the Herbarium page and its bonus stay), and a level is never lost, so unlocked things stay unlocked.
- `PlayerLevel` (OOP, Lesson 1) holds XP and level. All the numbers are in tables: `LEVEL_XP`, each `Plant(... unlock_level=)` and `Potion(... unlock_level=, xp=)`.
- 12 new checks (87 total), including one that makes sure no recipe unlocks before the plants it needs.

## Step 12: a real start, level-up celebration and sound
- **Start small:** the player now starts with just **3 MoonCatnip seeds** (and 20 coins), so every other seed and recipe really has to be unlocked by leveling up. (The Backpack's hash table now grows its first rehash a little later, as more kinds of items arrive.)
- **Level-up celebration:** reaching a new level shows a "LEVEL UP!" card with golden rays, a burst of sparkles and chips for everything that just unlocked. Click it or press Esc to dismiss it (it also closes by itself after ~4.5 seconds). With "reduce motion" on, it just appears without the animation. Code: `levelUpFx` in `SECTION 18` of `main.js`; the look is under "Level-up celebration" in `style.css`.
- **Sound system** (`SECTION 19` in `main.js`): Python asks for effects with `playSound("name")` at the right moments (plant, harvest, remove, undo, coin, brew, new Herbarium page, new Map place, morning/night, Nyra clicks, level-up). A soft click plays for every button. **Music** follows the screen (home screen / garden + Shop) and **ambience** follows the weather picture (day, night, rain; only in the garden). Everything fades in and out.
- **Your sounds go in `assets/sounds/`** with the exact names listed in `assets/sounds/README.txt` (mp3 by default; change `SOUND_EXTENSION` for .ogg or .wav). **Every file is optional:** a missing file is just silent, so you can add them one at a time. Volumes and delays are in the `SOUNDS` table at the top of that section.
- **Press M** in the game to mute or unmute (remembered next time). When you build the Settings window, `setSoundEnabled(true/false)` is ready to be connected to a switch.
- Browsers only allow sound after the first click, so the home screen music starts when the player first clicks or presses a key.
- 2 new checks (89 total); the starting-pouch tests were updated (`sampler(g)` in the tests adds the old "one of each seed" when a test needs it).

## Step 13: the Cauldron scene (visual revamp)
- **Opening:** the garden blurs like it does for the Backpack, your big cauldron **rises from the bottom middle** (with a little overshoot), then the left panel (Nyra's advice) and the right panel (recipes) **slide in from the two sides**. Closing plays it backwards.
- **Brewing:** press Brew (or "Brew Nyra's plan") and the plants **fly in an arc into the cauldron**, one after another. Each one makes a splash ring and little drops, and the cauldron squashes and bounces. Then the finished potion **pops out** with its name.
- **Only the look changed:** all rules are still Python. The one new thing Python sends is `brewed` (which plants went into which potion, sent once), so the screen throws exactly the right plants. 3 new checks (92 total).
- Code: `SECTION 15` in `main.js` ("Cauldron scene: opening, closing and the throw animation"), and "Cauldron scene (revamp)" at the bottom of `style.css`. Your `Cauldron_Main` art is used (a trimmed copy `..._Trim.png` is made for speed); `Cauldron_Window.png` is no longer used.
- With "reduce motion" on, everything still works but the motion is skipped.

## Step 14: your sounds, volume sliders, Settings and Credits
- **Your files are wired in** (`SOUND_FILES` in `SECTION 19`, no renaming needed): swoosh on every screen change and window opening, the pop-up when Nyra's dialogue box appears, the pop when the mouse moves onto a button, the click when a button is pressed, the level-up sound, and the cauldron bubbling **while the Cauldron window is open** (it fades out as the cauldron sinks) plus a short burst when you brew. Sounds without a file yet (plant, harvest, coin ...) stay silent until you add a line to `SOUND_FILES`; see `assets/sounds/README.txt`.
- **Music:** "Remembering Something I Forgot" is the main theme and loops on the home screen. When you press Play it keeps going, and in the garden and Shop the three songs take turns (main theme -> Coffee Jelly -> Turtle Sandbox), the next one fading in a few seconds before the current one ends.
- **Settings window** (home screen button and the gear in the garden): separate **Music** and **Sound effects** sliders, a **Mute everything** switch (also the **M** key), and a "Now playing" line. Volumes are remembered in the browser. The garden plots do not pop when hovered (it would be too busy); everything else does.
- **Credits window** (home screen button, or Settings -> Credits): reads `assets/sounds/credits.json`. **Please fill in the authors, sources, URLs and licenses there**; empty fields show as "still to fill in". The authors of the effects were guessed from your file names.
- Built on top of your Day 18 Cauldron scene; the only change in your Cauldron code is two sound lines (`showCauldron` / `closeCauldron`). Code: `SECTION 19` (sound) and `SECTION 20` (Settings and Credits) in `main.js`.

## Step 15: more sounds (rain, owls, planting, picking, coins) and cleaner credits
- **Planting, picking and coins:** planting a seed, harvesting a plant and buying or selling in the Shop now have sounds. The planting file holds **5 little planting sounds**, so the game plays one random one each time (never the same twice in a row).
- **Garden ambience:** rain loops on any rainy day or night, and distant owls loop on nights without rain. The day has none yet. They only play in the garden (not in the Shop). The recordings are just 10 seconds long, so each loop **fades into its own start** and repeats without a click.
- **Loudness balanced:** every effect's volume was set by measuring its file, so the click is no longer much quieter than the pop-up, and the level-up is not too loud.
- **Credits:** the three songs are credited to **Purrple Cat**, and the sound effects list **only the creators' usernames**. The "still to fill in" notes are gone; `assets/sounds/credits.json` is now very simple (music artist + song titles, and a list of usernames). Please double-check the usernames were spelled like the sources' pages.
- Everything else (Settings, sliders, Cauldron scene) is unchanged. No Python changes, so the 92 checks are unchanged.

## Step 15: secret codes (cheat codes for showing the game off)
Open **Settings** and type a code in the **Secret code** box (capitals, spaces and dashes don't matter).

| Code | What it does |
|---|---|
| `LEVELUP` | one level up, with the full celebration |
| `MAXLEVEL` | straight to the top level (everything unlocked) |
| `RICH` | +500 coins |
| `SEEDS` | +5 seeds of every plant you have unlocked |
| `PLANTS` | +3 harvested plants of every unlocked kind (for the Cauldron) |
| `GROWALL` | every growing plant is ready to harvest |
| `EXPLORE` | reveals every place on the Map |
| `PAGES` | unlocks every Herbarium page |
| `SKIPTIME` | moves time forward one step |
| `CODES` | lists all the codes |

- **Lesson 6 again:** the codes are stored in a **hash table** (`CodeBook`, same idea as the recipe book). The answer shows "code book: slot 1, 2 compared".
- If a code makes you level up, Settings closes by itself so the celebration is visible.
- `codes_used` counts successful codes, so achievements can ignore them later.
- 11 new checks (103 total).

## Step 16: day ambience
- **Birds in the day:** `gammagool__birds-in-the-slovenian-forest.wav` now loops in the garden on sunny, cloudy and cold-snap **days** (`AMBIENCE_FILES.day`). So every look of the garden has its own sound: day = birds, night = owls, rain = rain (day or night). Moving between them fades the old loop out and the new one in.
- The recording is 63 seconds and fades in and out at its ends, so its loop is smooth. It is a little quieter than the rain and owls (about 4 dB below the rain); if it feels too soft, raise `LOOP_GAIN.ambience`.
- The file is 11 MB because it is an uncompressed .wav. That is fine locally, but if you put the game online, a smaller .mp3 version loads much faster (keep the original too).
- `gammagool` was added to the sound effect credits (please check the spelling on the source page).

## Step 17: the hidden easter egg (a rhythm-game boss fight)
- **How to find it:** type `ItsAllAHoax` in the Settings "Secret code" box (capitals, spaces and dashes do not matter). It is in the code book (hash table) but **not** in the list of codes, so the `CODES` command never shows it, it answers with no message, and it does not count as a used cheat code.
- **The sequence** (`SECTION 21` in `main.js`): Settings closes by itself, the screen slowly darkens while Nyra senses something is off, the lights flicker, her message is cut off mid-word, and everything goes **pitch black for 1.7 seconds of silence**; then the rhythm game fades in and starts. The garden's music and ambience fade out for the whole thing. Click or press Enter to speed through Nyra's lines.
- **After the fight** you always land on the **home screen, as if nothing happened**. If you **lose**, that's all. If you **win** (survive the song), **Nyra pops up on the home screen, glad you're back** (two lines, click to continue).
- **Nyra's words** come from Python (`EGG_INTRO`, `EGG_CUTOFF` and `EGG_WELCOME`, three versions of each, never the same one twice in a row). Edit them like her other reactions.
- **The game** is in `assets/easter_egg/` (your files; only the assets it uses were copied, and the editor/recorder tools stay in your own folder). I changed `game.js` only for a new **embedded mode** (`?embed=1`); opening it normally still plays exactly like before. In embedded mode it waits on black until our game says go, uses the music and effects volumes from Settings, leaves when you press Enter after the end screen (or by itself after a few seconds) instead of retrying, and has **Q to leave** on its pause screen (counts as a loss). If a browser blocks its music from starting by itself, it shows its title screen so you can press Enter.
- It is shown in a frame, and the two games talk through messages: `egg-ready`, `egg-go` and `egg-result` (win / lose).
- **Important when testing:** the song needs a web server that supports byte ranges (almost all do, e.g. VS Code Live Server, GitHub Pages). Python's built-in `http.server` does not, which only matters if you jump into the middle of the song with `?start=`.
- 6 new checks (109 total).

## Step 18: easter egg polish (glitch sound and a countdown)
- **Glitch sound:** `error-glitch.mp3` plays the moment Nyra's message is cut off. The glitch picture (Nyra and her box shake and flash colours, the dark flickers) now lasts as long as the sound (`EGG_GLITCH_MS = 1300` in `SECTION 21`, the file is 1.33 s), and then comes the pure black with silence (1.7 s). The sound is `egg_glitch` in `SOUND_FILES`/`SOUNDS`, so its volume follows the Sound effects slider.
- **Countdown:** the fight no longer starts straight away. After it fades in, the lanes slide in, a **"GET READY" 3 - 2 - 1 - GO!** appears over the arena (one number every 0.8 seconds, soft low thumps made by the browser, no file needed) and only then does the song start. In total that is about 4.2 seconds more before the first note. Settings for it are at the top of the "embedded count-down" block in `assets/easter_egg/game.js` (`COUNT_WAIT`, `COUNT_STEP`, `COUNT_LABELS`). Standalone play (opening the minigame directly) is unchanged.
- If you find sounds you like for the countdown, they can replace `beep()` in `game.js`.
- No Python changes, so the 109 checks are unchanged.

## Bug fix: one Nyra at a time in the easter egg
- Typing the code **in the garden** used to bring up a *second* Nyra and dialogue box on top of the garden's own. Now, in the garden, the egg uses **the garden's own Nyra and dialogue box** (same place, same talking animation and pop sound, `showDialogue`). The dark is a veil inside the garden that sits *under* Nyra (`#garden-veil`, z-index between the plots and Nyra), so she stays bright while the garden darkens, and the glitch shakes the garden's own Nyra and box.
- On the **home screen** there is no Nyra, so the overlay Nyra and box are still used there (and for the "welcome back" lines after a win).
- Code: `showEggLine(line, inGarden)` and `runEasterEgg` in `SECTION 21`; the `.garden-veil` and `.garden-screen.egg-glitch` rules in `style.css`.
