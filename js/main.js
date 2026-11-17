/* =============================================================================
   Catnip Cauldron - js/main.js  ("the face of the game")

   JavaScript only DRAWS things and listens for clicks. Every game RULE lives in
   Python (python/game_state.py) and runs in the browser through Pyodide:

       you click  ->  JS asks Python  ->  Python decides  ->  Python calls a
                                                              "bridge" function in
                                                              this file to update the screen

   FILE MAP  (search for "SECTION n" to jump to a part)
    1  Page elements and screen state
    2  Python connection (Pyodide) + the first loading screen
    3  Screen transitions (the loading cauldron between screens) + entrance animations
    4  Art lookup, screens, messages and Nyra's dialogue
    5  The garden grid on screen ................... shows Lesson 3
    6  Bridge functions: Python -> screen ........... coins, day, undo, backpack, plots
    7  Plant picker and the dock (side buttons)
    8  Backpack window ............................. shows Lessons 6 (hash table) and 8 (sorting)
    9  Button and keyboard wiring
   10  Sorting controls ............................ Lesson 8 (Backpack + Shop)
   11  Shop ........................................ Lessons 8 and 12
   12  Herbarium book .............................. Lessons 4, 5 and 9
   13  Main menu life (fireflies; its Settings and Credits buttons open SECTION 20)
   14  Map window .................................. Lessons 7 (graph, BFS, DFS) and 10 (Dijkstra, greedy)
   15  Cauldron window ............................ Lesson 11 (dynamic programming)
   16  Garden weather effects ...................... rain drops and night fireflies
   17  Clicking Nyra ............................... she reacts (Python picks what she says)
   18  Level badge and level-up celebration .......... XP bar in the top bar; the sparkle card; locked seeds and recipes
   19  Sound ....................................... effects, music rotation and volumes (your files are listed in SOUND_FILES)
   20  Settings and Credits windows ................ music / effects volume sliders, mute, secret codes, credits list
   21  The hidden easter egg ....................... the secret word runs a dark sequence, then the rhythm-game fight

   Where each lesson lives in python/game_state.py:
   L1 Plant class + Undo stack - L2 weather queue - L3 garden grid - L4 Herbarium tree
   L5 entry BST - L6 backpack hash table - L7 + L10 map graph and routes - L11 cauldron DP - L8 sorting - L9 Herbarium search - L12 coins
   ============================================================================= */
/* =========================================================================
   SECTION 1 - Page elements and screen state
   Grabs every button and label from index.html once, so the rest of the file can use them.
   ========================================================================= */
const screens = {
  menu: document.getElementById("main-menu"),
  garden: document.getElementById("garden-screen"),
  shop: document.getElementById("shop-screen")
};
const playButton = document.getElementById("play-button");
const gardenScreen = document.getElementById("garden-screen");
const gardenGrid = document.getElementById("garden-grid");
const borderButton = document.getElementById("border-button");
const equippedPlantImage = document.getElementById("equipped-plant");
const plantButton = document.getElementById("plant-button");
const harvestButton = document.getElementById("harvest-button");
const removeButton = document.getElementById("remove-button");
const dockTab = document.getElementById("dock-tab");
const extras = document.getElementById("extras");
const plantDrawer = document.getElementById("plant-drawer");
const menuButton = document.getElementById("menu-button");
const backpackButton = document.getElementById("backpack-button");
const inventoryLayer = document.getElementById("inventory");
const invScrim = document.getElementById("inv-scrim");
const invBag = document.getElementById("inv-bag");
const invBagHop = document.getElementById("inv-bag-hop");
const invPanel = document.getElementById("inv-panel");
const invClose = document.getElementById("inv-close");
const invGrid = document.getElementById("inv-grid");
const invHint = document.getElementById("inv-hint");
const plantList = document.getElementById("plant-list");
const seedCountLabel = document.getElementById("seed-count");
const seedLabel = document.getElementById("seed-label");
const coinCountLabel = document.getElementById("coin-count");
const dayLabel = document.getElementById("day-label");
const weatherLabel = document.getElementById("weather-label");
const dayIndicator = document.getElementById("day-indicator");
const skipTimeButton = document.getElementById("skip-time-button");
const timeIcon = document.getElementById("time-icon");
const undoButton = document.getElementById("undo-button");
const invPeek = document.getElementById("inv-peek");
const invPeekView = document.getElementById("inv-peek-view");
const messageLabel = document.getElementById("garden-message");
const dialoguePanel = document.getElementById("dialogue-panel");
const dialogueText = document.getElementById("dialogue-text");

let selectedPlot = null;          // which plot is highlighted (screen state only)
let selectedPlant = "MoonCatnip"; // which plant is equipped (screen state only)
const PLOT_COUNT = 25;

/* =========================================================================
   SECTION 2 - Python connection (Pyodide) + the first loading screen
   Downloads Python, hands it the bridge functions, loads herbarium_data.py then game_state.py.
   ========================================================================= */
/* ---------- Python connection (Pyodide) ----------
   py.* are the rule functions written in python/game_state.py. */
const py = {};
let pythonReady = false;

const loadingScreen = document.getElementById("loading-screen");
const loadFill = document.getElementById("load-fill");
const loadStageText = document.getElementById("load-stage-text");
const loadRetry = document.getElementById("load-retry");
const menuNote = document.getElementById("load-status");
const sleep = ms => new Promise(resolve => window.setTimeout(resolve, ms));

function setLoadProgress(percent, text) {
  loadFill.style.width = `${percent}%`;
  loadStageText.textContent = text;
}

async function initPython() {
  const startedAt = performance.now();
  loadRetry.hidden = true;
  setLoadProgress(8, "Warming the cauldron…");
  try {
    const pyodide = await loadPyodide();
    setLoadProgress(62, "Teaching Nyra the garden rules…");
    // Bridge: functions Python is allowed to call to change what the player sees.
    pyodide.globals.set("updateInventory", updateInventory);
    pyodide.globals.set("updateCoins", updateCoins);
    pyodide.globals.set("updateDay", updateDay);
    pyodide.globals.set("updateUndo", updateUndo);
    pyodide.globals.set("updateShop", updateShop);
    pyodide.globals.set("updateHerbarium", updateHerbarium);
    pyodide.globals.set("updateMap", updateMap);
    pyodide.globals.set("updateCauldron", updateCauldron);
    pyodide.globals.set("updateLevel", updateLevel);
    pyodide.globals.set("levelUpFx", levelUpFx);
    pyodide.globals.set("playSound", playSound);
    pyodide.globals.set("startEasterEgg", startEasterEgg);
    pyodide.globals.set("showEggWelcome", showEggWelcome);
    pyodide.globals.set("showCodeResult", showCodeResult);
    pyodide.globals.set("drawPlot", drawPlot);
    pyodide.globals.set("setMessage", setMessage);
    pyodide.globals.set("showDialogue", showDialogue);
    const bookText = await (await fetch("python/herbarium_data.py")).text();
    const source = await (await fetch("python/game_state.py")).text();
    setLoadProgress(84, "Almost ready…");
    await pyodide.runPythonAsync(bookText);   // the Herbarium words come first ...
    await pyodide.runPythonAsync(source);     // ... then the game rules that use them
    ["start_game", "inspect_plot", "plant_seed", "harvest_plant", "remove_plant", "skip_time", "undo_action",
      "shop_open", "shop_set_view", "buy_seed", "sell_plant", "set_backpack_sort",
      "herbarium_open", "herbarium_set_order", "herbarium_select", "herbarium_search",
      "map_open", "map_set_mode", "map_select", "map_explore", "map_route", "map_errands",
      "cauldron_open", "cauldron_ask", "cauldron_brew", "cauldron_brew_plan", "sell_potion", "nyra_poke", "apply_secret_code", "egg_result"].forEach(name => {
      py[name] = pyodide.globals.get(name);
    });
    py.start_game();
    pythonReady = true;
    playButton.disabled = false;
    setLoadProgress(100, "Nyra is awake!");
    // Keep the screen up a moment so it never just flashes by.
    await sleep(Math.max(500, 1500 - (performance.now() - startedAt)));
    setIntro("go");
    loadingScreen.classList.add("done");
    window.setTimeout(() => { loadingScreen.hidden = true; }, 650);
  } catch (error) {
    console.error("Python failed to load:", error);
    setLoadProgress(0, "Check your internet, open the game through a local server, then try again.");
    document.getElementById("load-title-text").textContent = "Nyra is still sleeping…";
    loadingScreen.classList.add("failed");
    loadRetry.hidden = false;
  }
}

/* =========================================================================
   SECTION 3 - Screen transitions + entrance animations
   Every big screen change (menu, garden, shop) fades in the cauldron loading screen first.
   ========================================================================= */
/* ---------- Screen transitions ----------
   A solid colour fades over the screen, the loading cauldron appears, the screens swap
   behind it, then it fades away. Use this for any big screen change (garden, menu, and the shop later). */
/* Entrance animations: each screen starts "waiting" (elements hidden) and is told to "go"
   the moment the loading cover starts fading, so the player actually sees them arrive. */
function setIntro(state) {
  document.querySelectorAll("[data-intro]").forEach(screen => { screen.dataset.intro = state; });
}

const TRANSITION_COVER_MS = 380;  // how long the colour takes to fill the screen
const TRANSITION_HOLD_MS = 900;   // how long the cauldron stays on screen
let transitionBusy = false;

async function runTransition({ title, sub, work }) {
  if (transitionBusy) return;
  transitionBusy = true;
  playSound("transition");                        // whoosh: the screen is changing
  setIntro("wait");
  document.getElementById("load-title-text").textContent = title;
  loadStageText.textContent = sub;
  loadFill.style.transition = "none";
  loadFill.style.width = "0%";
  loadingScreen.classList.remove("failed");
  loadingScreen.classList.add("solid", "done");
  loadingScreen.hidden = false;
  void loadingScreen.offsetWidth;                 // let the browser notice the starting state
  loadingScreen.classList.remove("done");         // fade the colour in
  await sleep(TRANSITION_COVER_MS);
  work();                                         // screen is fully covered, so swap it now
  void loadFill.offsetWidth;
  loadFill.style.transition = `width ${TRANSITION_HOLD_MS}ms ease-out`;
  loadFill.style.width = "100%";
  await sleep(TRANSITION_HOLD_MS);
  setIntro("go");                                 // new screen's elements slide / pop in
  loadingScreen.classList.add("done");            // fade everything away
  await sleep(650);
  loadingScreen.hidden = true;
  loadingScreen.classList.remove("solid");
  loadFill.style.transition = "";
  transitionBusy = false;
}

/* Runs a Python rule, or asks the player to wait if Python is still loading. */
function askPython(ruleName, ...args) {
  if (!pythonReady) {
    setMessage("Nyra is still waking up. One moment!");
    return;
  }
  py[ruleName](...args);
}

/* =========================================================================
   SECTION 4 - Art lookup, screens, messages and Nyra's dialogue
   plantAssets = which image belongs to which plant. showScreen() swaps screens.
   ========================================================================= */
const plantAssets = {
  MoonCatnip: { label: "MoonCatnip", early: "assets/plants/MoonCatnip%28Early%29_Trim.png", grown: "assets/plants/MoonCatnip%28Grown%29_Trim.png" },
  MoonBell: { label: "MoonBell", early: "assets/plants/MoonBell%28Early%29.png", grown: "assets/plants/MoonBell%28Grown%29.png" },
  SunPetal: { label: "SunPetal", early: "assets/plants/SunPetal%28Early%29.png", grown: "assets/plants/SunPetal%28Grown%29.png" },
  HeartBlossom: { label: "HeartBlossom", early: "assets/plants/HeartBlossom%28Early%29.png", grown: "assets/plants/HeartBlossom%28Grown%29.png" },
  Frostmint: { label: "Frostmint", early: "assets/plants/Frostmint%28Early%29.png", grown: "assets/plants/Frostmint%28Grown%29.png" },
  StarBloom: { label: "StarBloom", early: "assets/plants/StarBloom%28Early%29.png", grown: "assets/plants/StarBloom%28Grown%29.png" }
};

function showScreen(screenName) {
  screens.menu.hidden = screenName !== "menu";
  screens.garden.hidden = screenName !== "garden";
  screens.shop.hidden = screenName !== "shop";
  if (screenName !== "garden") hideDialogue();
  soundForScreen(screenName);
}

function setMessage(message) {
  messageLabel.textContent = message;
  if (!screens.shop.hidden) document.getElementById("shop-note").textContent = message;   // visible note inside the shop
}

function showDialogue(message, expression = "happy", mouth = "closed") {
  playSound("dialogue");                          // a little pop whenever Nyra speaks
  dialogueText.textContent = message;
  dialoguePanel.hidden = false;
  if (window.setNyraExpression) window.setNyraExpression(expression, mouth, true);
}

function hideDialogue() {
  dialoguePanel.hidden = true;
  if (window.setNyraExpression) window.setNyraExpression("passive", "closed", false);
}

/* =========================================================================
   SECTION 5 - The garden grid on screen  (shows Lesson 3)
   Builds the 5x5 buttons. The real grid (a 2D list) lives in Python; drawPlot() below paints it.
   ========================================================================= */
function createGardenPlots() {
  gardenGrid.replaceChildren();
  Array.from({ length: PLOT_COUNT }, (_, index) => index).forEach(index => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "plot";
    button.setAttribute("aria-label", `Plot ${index + 1}, empty`);
    button.textContent = "✧";
    button.style.zIndex = String(Math.floor(index / 5) + 1);
    button.style.setProperty("--wave", String(Math.floor(index / 5) + (index % 5)));  // diagonal pop-in order
    button.addEventListener("click", () => selectPlot(index, button));
    gardenGrid.appendChild(button);
  });
}

function selectPlot(index, button) {
  gardenGrid.querySelectorAll(".plot").forEach(plotButton => plotButton.classList.remove("selected"));
  selectedPlot = index;
  button.classList.add("selected");
  askPython("inspect_plot", index);
}

/* =========================================================================
   SECTION 6 - Bridge functions: Python -> screen
   Python calls these by name: updateInventory, updateCoins, updateDay, updateUndo,
   updateShop, updateHerbarium and drawPlot. They only draw; they never decide anything.
   ========================================================================= */
/* ---------- Bridge functions: Python calls these to update the screen ---------- */
const gameData = { seeds: [], plants: [], table: null };

function ownedSeeds(plantName) {
  const entry = gameData.seeds.find(item => item.name === plantName);
  return entry ? entry.count : 0;
}

/* The Seeds pill shows how many seeds of the EQUIPPED plant you have. */
function updateSeedPill() {
  const plant = plantAssets[selectedPlant];
  seedLabel.textContent = `${plant.label} seeds`;
  seedCountLabel.textContent = String(ownedSeeds(selectedPlant));
}

/* Small "x3" badges in the plant picker. */
function updatePickerCounts() {
  plantList.querySelectorAll(".plant-option").forEach(option => {
    const count = ownedSeeds(option.dataset.plant);
    option.querySelector(".plant-count").textContent = `x${count}`;
    option.classList.toggle("no-seeds", count === 0);
  });
}

function updateInventory(jsonText) {
  const data = JSON.parse(jsonText);
  gameData.seeds = data.seeds;
  gameData.plants = data.plants;
  gameData.potions = data.potions;     // brewed potions (the Potions tab)
  gameData.table = data.table;
  gameData.sort = data.sort;
  syncBackpackSortControls();
  updateSeedPill();
  updatePickerCounts();
  renderInventory();
}

function updateCoins(coins) {
  document.querySelectorAll(".coin-count").forEach(label => { label.textContent = String(coins); });
}

const TIME_NAMES = { Day: "Daytime", Night: "Nighttime" };
function updateDay(day, weather, symbol, forecast, timeOfDay, scene) {
  timeIcon.textContent = timeOfDay === "Night" ? "☾" : "☀";
  dayLabel.textContent = `Day ${day} · ${TIME_NAMES[timeOfDay]}`;
  weatherLabel.textContent = ` · ${symbol} ${weather}`;
  dayIndicator.title = forecast;
  const next = timeOfDay === "Day" ? "night" : "morning";
  skipTimeButton.title = `Skip to ${next}`;
  skipTimeButton.setAttribute("aria-label", `Skip time to ${next}`);
  setScene(scene);
}

/* The planting area has a picture for each look (day, night, starry night, rain). The new picture
   is put on top and fades in; the old one is only removed once it is fully covered. */
let currentScene = null;
let sceneLayer = 0;
function setScene(scene) {
  if (scene === currentScene) return;
  const layers = Array.from(document.querySelectorAll(".scene"));
  const next = layers.find(layer => layer.dataset.scene === scene);
  if (!next) return;
  const previous = layers.find(layer => layer.dataset.scene === currentScene);
  currentScene = scene;
  setWeatherEffect(scene);
  soundForScene(scene);
  sceneLayer += 1;
  next.style.zIndex = String(sceneLayer);
  next.classList.add("on");
  if (previous) {
    window.setTimeout(() => {
      if (currentScene !== previous.dataset.scene) previous.classList.remove("on");
    }, 1100);
  }
}

function updateUndo(count, label) {
  undoButton.disabled = count === 0;
  undoButton.title = count === 0 ? "Nothing to undo" : `Undo: ${label}`;
}

/* =========================================================================
   SECTION 7 - Plant picker and the dock (side buttons)
   The Border icon shows the equipped plant; the arrow tab reveals Shop, Backpack, Herbarium...
   ========================================================================= */
/* Builds the plant choices that live inside the pull-out drawer. */
function buildPlantList() {
  plantList.replaceChildren();
  Object.entries(plantAssets).forEach(([key, plant]) => {
    const option = document.createElement("button");
    option.type = "button";
    option.className = "plant-option" + (selectedPlant === key ? " selected" : "");
    option.setAttribute("aria-pressed", String(selectedPlant === key));
    option.dataset.plant = key;
    const image = document.createElement("img");
    image.src = plant.grown;
    image.alt = "";
    const name = document.createElement("span");
    name.textContent = plant.label;
    const count = document.createElement("small");
    count.className = "plant-count";
    option.append(image, name, count);
    option.addEventListener("click", () => {
      selectedPlant = key;
      plantList.querySelectorAll(".plant-option").forEach(item => {
        item.classList.remove("selected");
        item.setAttribute("aria-pressed", "false");
      });
      option.classList.add("selected");
      option.setAttribute("aria-pressed", "true");
      updateEquippedPlant();
      updateSeedPill();
      setMessage(`${plant.label} selected. Choose a plot, then press the Plant icon.`);
    });
    plantList.appendChild(option);
  });
}

/* The Border icon shows the grown version of whichever plant is equipped. */
function updateEquippedPlant() {
  const plant = plantAssets[selectedPlant];
  equippedPlantImage.src = plant.grown;
  borderButton.setAttribute("aria-label", `Equipped plant: ${plant.label}. Open plant menu`);
  borderButton.title = `Equipped: ${plant.label}`;
}

/* Both pop-ups only slide over the scene; the garden itself never moves. */
function setDrawerOpen(open) {
  gardenScreen.classList.toggle("drawer-open", open);
  borderButton.setAttribute("aria-expanded", String(open));
  plantDrawer.setAttribute("aria-hidden", String(!open));
}

function setExtrasOpen(open) {
  gardenScreen.classList.toggle("extras-open", open);
  dockTab.setAttribute("aria-expanded", String(open));
  dockTab.setAttribute("aria-label", open ? "Hide extra buttons" : "Show more buttons");
  extras.setAttribute("aria-hidden", String(!open));
}

function comingSoon(name) {
  setMessage(`${name} isn't ready yet.`);
  showDialogue(`The ${name} isn't ready yet, but soon!`, "passive", "open");
}

/* Bridge: Python calls this to draw one plot. plant is undefined for an empty plot. */
function drawPlot(index, plant, stage) {
  const button = gardenGrid.children[index];
  if (!button) return;
  button.replaceChildren();
  if (!plant) {
    button.textContent = "✧";
    button.setAttribute("aria-label", `Plot ${index + 1}, empty`);
    return;
  }
  const image = document.createElement("img");
  const art = plantAssets[plant];
  if (art) image.src = art[stage] || art.early;
  image.alt = plant;
  image.className = stage === "grown" ? "plant-grown" : "plant-early";
  button.appendChild(image);
  button.setAttribute("aria-label", `Plot ${index + 1}, ${plant}, ${stage}`);
}

/* The three action icons just ask Python. -1 means "no plot chosen yet". */
function plantSeed() { askPython("plant_seed", selectedPlot ?? -1, selectedPlant); }
function harvestPlant() { askPython("harvest_plant", selectedPlot ?? -1); }
function removePlant() { askPython("remove_plant", selectedPlot ?? -1); }

/* =========================================================================
   SECTION 8 - Backpack window  (shows Lessons 6 and 8)
   The items come from the hash table in Python. "Peek inside" draws that hash table.
   The bag-opening animation lives here too.
   ========================================================================= */
/* ---------- Backpack / inventory ----------
   Items are filled in later (seed counts come next). Each tab holds a list of
   { name, icon, count } objects; empty tabs just show empty slots. */
/* The lists come from Python (the backpack hash table). Seed art isn't drawn yet,
   so seeds borrow each plant's early sprite until it is. */
function currentItems() {
  if (inventoryTab === "seeds") {
    return gameData.seeds.map(item => ({ name: `${plantAssets[item.name].label} seed`, icon: plantAssets[item.name].early, count: item.count }));
  }
  if (inventoryTab === "plants") {
    return gameData.plants.map(item => ({ name: plantAssets[item.name].label, icon: plantAssets[item.name].grown, count: item.count }));
  }
  if (inventoryTab === "potions") {
    return (gameData.potions || []).map(item => ({ name: item.name, icon: potionAssets[item.name], count: item.count }));
  }
  return [];
}
const inventoryHints = {
  seeds: "Your seeds will show up here.",
  plants: "Harvested plants will show up here.",
  potions: "Brew potions in the Cauldron and they will show up here."
};
const INVENTORY_SLOTS = 40;
let inventoryTab = "seeds";
let inventoryState = "closed";   // closed | opening | open | closing
let inventoryWantsClose = false;

const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
const wait = ms => new Promise(resolve => window.setTimeout(resolve, reduceMotion.matches ? 0 : ms));
function play(element, keyframes, duration, easing = "ease") {
  const animation = element.animate(keyframes, { duration: reduceMotion.matches ? 1 : duration, easing, fill: "forwards" });
  return animation.finished.catch(() => {});
}

function renderInventory() {
  invGrid.replaceChildren();
  const items = currentItems();
  for (let i = 0; i < INVENTORY_SLOTS; i++) {
    const slot = document.createElement("div");
    slot.className = "inv-slot";
    slot.setAttribute("role", "listitem");
    const item = items[i];
    if (item) {
      slot.title = item.name;
      const image = document.createElement("img");
      image.src = item.icon;
      image.alt = item.name;
      slot.appendChild(image);
      const count = document.createElement("span");
      count.className = "inv-count";
      count.textContent = `x${item.count}`;
      slot.appendChild(count);
    }
    invGrid.appendChild(slot);
  }
  invHint.textContent = items.length ? backpackSortInfo() : inventoryHints[inventoryTab];
  renderPeek();
}

/* "Peek inside": shows how Python really stores the backpack (Lesson 6, hash table). */
let peekOn = false;
function renderPeek() {
  invGrid.hidden = peekOn;
  invPeekView.hidden = !peekOn;
  invPeek.setAttribute("aria-pressed", String(peekOn));
  invPeek.classList.toggle("selected", peekOn);
  if (!peekOn || !gameData.table) return;
  const t = gameData.table;
  const lines = [
    `<p class="peek-stats">Slots <b>${t.size}</b> · Items <b>${t.count}</b> · Load <b>${t.load_factor}</b> (rehash above ${t.max_load}) · Collisions <b>${t.collisions}</b> · Rehashes <b>${t.rehashes}</b></p>`,
    `<ol class="peek-slots" start="0">${t.slots.map(chain => `<li class="${chain.length > 1 ? "chained" : ""}">${chain.length ? chain.join(" → ") : "—"}</li>`).join("")}</ol>`,
    t.events.length ? `<ul class="peek-events">${t.events.map(e => `<li>${e}</li>`).join("")}</ul>` : ""
  ];
  invPeekView.innerHTML = lines.join("");
  invHint.textContent = "A hash table with chaining: item name → slot number → chain (Lesson 6).";
}
invPeek.addEventListener("click", () => { peekOn = !peekOn; renderInventory(); });

document.querySelectorAll(".inv-tab[data-tab]").forEach(tab => {
  tab.addEventListener("click", () => {
    inventoryTab = tab.dataset.tab;
    document.querySelectorAll(".inv-tab[data-tab]").forEach(other => {
      const active = other === tab;
      other.classList.toggle("selected", active);
      other.setAttribute("aria-selected", String(active));
    });
    renderInventory();
  });
});

const BAG_OFFSCREEN = "translate(-50%, calc(-55% + 95svh))";
const BAG_CENTER = "translate(-50%, -55%)";
const PANEL_IN_BAG = "translate(-50%, calc(-50% - 8svh)) scale(.15)";
const PANEL_SHOWN = "translate(-50%, -50%) scale(1)";

async function openInventory() {
  if (inventoryState !== "closed") return;
  inventoryState = "opening";
  playSound("transition");
  inventoryWantsClose = false;
  setDrawerOpen(false);
  renderInventory();
  [invScrim, invBag, invBagHop, invPanel].forEach(el => el.getAnimations().forEach(a => a.cancel()));
  invBagHop.classList.remove("is-open");
  inventoryLayer.hidden = false;
  invPanel.style.opacity = "0";
  invPanel.style.visibility = "hidden";

  play(invScrim, [{ opacity: 0 }, { opacity: 1 }], 300);
  // 1) the closed bag slides up from the bottom to the middle
  await play(invBag, [{ transform: BAG_OFFSCREEN }, { transform: BAG_CENTER }], 540, "cubic-bezier(.2, .9, .3, 1.08)");
  // 2) it hops open
  const hop = play(invBagHop, [
    { transform: "scale(1, 1)" }, { transform: "scale(1.06, .92)", offset: .3 },
    { transform: "scale(.97, 1.05)", offset: .65 }, { transform: "scale(1, 1)" }
  ], 300, "ease-out");
  await wait(110);
  invBagHop.classList.add("is-open");
  await wait(110);
  // 3) the panel rises out of the bag's opening
  invPanel.style.visibility = "visible";
  await Promise.all([hop, play(invPanel, [
    { transform: PANEL_IN_BAG, opacity: 0 }, { transform: PANEL_SHOWN, opacity: 1 }
  ], 440, "cubic-bezier(.2, .9, .3, 1.05)")]);

  inventoryState = "open";
  invClose.focus({ preventScroll: true });
  if (inventoryWantsClose) closeInventory();
}

async function closeInventory() {
  if (inventoryState === "opening") { inventoryWantsClose = true; return; }
  if (inventoryState !== "open") return;
  inventoryState = "closing";
  // panel shrinks back into the bag, the bag closes, then slides away
  await play(invPanel, [
    { transform: PANEL_SHOWN, opacity: 1 }, { transform: PANEL_IN_BAG, opacity: 0 }
  ], 300, "ease-in");
  invPanel.style.visibility = "hidden";
  invBagHop.classList.remove("is-open");
  play(invBagHop, [
    { transform: "scale(1, 1)" }, { transform: "scale(1.05, .93)", offset: .4 }, { transform: "scale(1, 1)" }
  ], 200, "ease-out");
  await wait(160);
  play(invScrim, [{ opacity: 1 }, { opacity: 0 }], 340);
  await play(invBag, [{ transform: BAG_CENTER }, { transform: BAG_OFFSCREEN }], 400, "cubic-bezier(.5, 0, .9, .5)");
  inventoryLayer.hidden = true;
  inventoryState = "closed";
  backpackButton.focus({ preventScroll: true });
}

/* Keep keyboard focus inside the backpack while it is open. */
function trapInventoryFocus(event) {
  if (event.key !== "Tab" || inventoryState === "closed") return;
  const focusable = Array.from(invPanel.querySelectorAll("button")).filter(el => el.offsetParent !== null);
  if (!focusable.length) return;
  const first = focusable[0], last = focusable[focusable.length - 1];
  if (!invPanel.contains(document.activeElement)) { event.preventDefault(); first.focus(); }
  else if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
  else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
}


/* =========================================================================
   SECTION 9 - Button and keyboard wiring
   Each button just asks Python to do something (plant, harvest, remove, next day, undo...).
   ========================================================================= */
playButton.addEventListener("click", () => runTransition({
  title: "Heading to the garden",
  sub: "Fluffing up the soil…",
  work: () => {
    showScreen("garden");
    if (window.setNyraExpression) window.setNyraExpression("passive", "closed", false);
  }
}));
plantButton.addEventListener("click", plantSeed);
skipTimeButton.addEventListener("click", () => askPython("skip_time"));
undoButton.addEventListener("click", () => askPython("undo_action"));
harvestButton.addEventListener("click", harvestPlant);
removeButton.addEventListener("click", removePlant);
borderButton.addEventListener("click", () => setDrawerOpen(!gardenScreen.classList.contains("drawer-open")));
dockTab.addEventListener("click", () => setExtrasOpen(!gardenScreen.classList.contains("extras-open")));
backpackButton.addEventListener("click", openInventory);
invClose.addEventListener("click", closeInventory);
invScrim.addEventListener("click", closeInventory);
document.getElementById("herbarium-button").addEventListener("click", openHerbarium);
document.getElementById("map-button").addEventListener("click", openMap);
document.getElementById("settings-button").addEventListener("click", () => openDialog("settings"));
menuButton.addEventListener("click", () => runTransition({
  title: "Heading home",
  sub: "Tidying up the garden…",
  work: () => {
    setDrawerOpen(false);
    setExtrasOpen(false);
    showScreen("menu");
  }
}));
document.addEventListener("keydown", event => {
  if (event.key === "Escape") {
    if (dialogOpen) {
      closeDialog();
      return;
    }
    if (!document.getElementById("levelup-layer").hidden) {
      hideLevelUp();
      return;
    }
    if (cauldronState !== "closed") {
      closeCauldron();
      return;
    }
    if (mapState !== "closed") {
      closeMap();
      return;
    }
    if (herbariumState !== "closed") {
      closeHerbarium();
      return;
    }
    if (inventoryState !== "closed") {
      closeInventory();
      return;
    }
    setDrawerOpen(false);
    setExtrasOpen(false);
  }
  trapInventoryFocus(event);
  trapHerbariumFocus(event);
  trapMapFocus(event);
  trapCauldronFocus(event);
});
dialoguePanel.addEventListener("click", hideDialogue);
dialoguePanel.addEventListener("keydown", event => {
  if (event.key === "Enter" || event.key === " ") {
    event.preventDefault();
    hideDialogue();
  }
});

createGardenPlots();
buildPlantList();
updateEquippedPlant();
updateSeedPill();

// Play stays disabled until Python has loaded, so the rules are always ready.
playButton.disabled = true;
loadRetry.addEventListener("click", () => window.location.reload());
initPython();

/* =========================================================================
   SECTION 10 - Sorting controls  (Lesson 8)
   Pick a field and an algorithm; Python sorts with its own Bubble/Insertion/Selection/Merge/Quick code.
   ========================================================================= */
/* ---------- Sorting controls (Lesson 8) shared by the Backpack and the Shop ---------- */
const SORT_METHODS = ["Merge Sort", "Quick Sort", "Insertion Sort", "Selection Sort", "Bubble Sort"];
document.querySelectorAll(".sort-algo").forEach(select => {
  SORT_METHODS.forEach(name => select.add(new Option(name, name)));
});

function setDirButton(button, descending) {
  button.textContent = descending ? "↓" : "↑";
  button.title = descending ? "Descending (biggest first)" : "Ascending (smallest first)";
  button.setAttribute("aria-label", descending ? "Sort descending" : "Sort ascending");
  button.dataset.descending = String(descending);
}

/* Backpack */
const invSortField = document.getElementById("inv-sort-field");
const invSortAlgo = document.getElementById("inv-sort-algo");
const invSortDir = document.getElementById("inv-sort-dir");

function syncBackpackSortControls() {
  const sort = gameData.sort;
  if (!sort) return;
  invSortField.value = sort.field;
  invSortAlgo.value = sort.algorithm;
  setDirButton(invSortDir, sort.descending);
}

function backpackSortInfo() {
  const sort = gameData.sort;
  if (!sort) return "";
  const comparisons = { seeds: sort.seeds_comparisons, plants: sort.plants_comparisons, potions: sort.potions_comparisons }[inventoryTab];
  return `Sorted by ${sort.field} with ${sort.algorithm} (${sort.big_o}) · ${comparisons} comparisons`;
}

function pushBackpackSort(flipDirection = false) {
  const descending = invSortDir.dataset.descending === "true";
  askPython("set_backpack_sort", invSortField.value, invSortAlgo.value, flipDirection ? !descending : descending);
}
invSortField.addEventListener("change", () => pushBackpackSort());
invSortAlgo.addEventListener("change", () => pushBackpackSort());
invSortDir.addEventListener("click", () => pushBackpackSort(true));

/* =========================================================================
   SECTION 11 - Shop  (Lessons 8 and 12)
   Buy seeds, sell plants. Python sorts the rows and counts the comparisons.
   ========================================================================= */
/* ---------- Shop ---------- */
const shopList = document.getElementById("shop-list");
const shopSortField = document.getElementById("shop-sort-field");
const shopSortAlgo = document.getElementById("shop-sort-algo");
const shopSortDir = document.getElementById("shop-sort-dir");
let shopTab = "buy";

function pushShopView(overrides = {}) {
  const descending = overrides.descending ?? (shopSortDir.dataset.descending === "true");
  askPython("shop_set_view", overrides.tab ?? shopTab, shopSortField.value, shopSortAlgo.value, descending);
}

/* Bridge: Python sends the sorted shop list; this draws it. */
function updateShop(jsonText) {
  const shop = JSON.parse(jsonText);
  shopTab = shop.tab;
  document.querySelectorAll("[data-shop-tab]").forEach(tab => {
    const active = tab.dataset.shopTab === shop.tab;
    tab.classList.toggle("selected", active);
    tab.setAttribute("aria-selected", String(active));
  });
  shopSortField.value = shop.field;
  shopSortAlgo.value = shop.algorithm;
  setDirButton(shopSortDir, shop.descending);
  document.getElementById("shop-sort-info").textContent =
    `Sorted by ${shop.field} with ${shop.algorithm} (${shop.big_o}) · ${shop.comparisons} comparisons`;

  shopList.replaceChildren();
  if (shop.rows.length === 0) {
    const empty = document.createElement("p");
    empty.className = "shop-empty";
    empty.textContent = "You have nothing to sell yet. Plant something, press Skip Time until it's grown, then harvest it!";
    shopList.appendChild(empty);
    return;
  }
  shop.rows.forEach(row => {
    const isPotion = row.kind === "potion";
    const art = isPotion ? null : plantAssets[row.name];
    const item = document.createElement("div");
    item.className = "shop-row";
    item.setAttribute("role", "listitem");

    const image = document.createElement("img");
    image.src = isPotion ? potionAssets[row.name] : (shop.tab === "buy" ? art.early : art.grown);   // seeds borrow the early sprite until seed art exists
    image.alt = "";

    const info = document.createElement("div");
    info.className = "shop-row-name";
    const name = document.createElement("strong");
    name.textContent = isPotion ? row.name : (shop.tab === "buy" ? `${art.label} seed` : art.label);
    const owned = document.createElement("small");
    owned.textContent = `You own ${row.owned}`;
    info.append(name, owned);

    const price = document.createElement("div");
    price.className = "shop-row-price";
    price.textContent = row.locked
      ? `🔒 Unlocks at level ${row.unlock_level}`
      : `${row.price} coins${shop.tab === "sell" ? " each" : ""}${row.in_demand ? " (in demand!)" : ""}`;
    if (row.locked) item.classList.add("locked");

    const actions = document.createElement("div");
    actions.className = "shop-row-actions";
    if (shop.tab === "buy") {
      actions.appendChild(shopButton(row.locked ? "Locked" : "Buy", () => askPython("buy_seed", row.name), row.locked || !row.affordable));
    } else {
      const sellCommand = isPotion ? "sell_potion" : "sell_plant";
      actions.appendChild(shopButton("Sell 1", () => askPython(sellCommand, row.name, 1)));
      if (row.owned > 1) actions.appendChild(shopButton("Sell all", () => askPython(sellCommand, row.name, row.owned)));
    }
    item.append(image, info, price, actions);
    shopList.appendChild(item);
  });
}

function shopButton(label, onClick, disabled = false) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "top-button shop-btn";
  button.textContent = label;
  button.disabled = disabled;
  button.addEventListener("click", onClick);
  return button;
}

document.querySelectorAll("[data-shop-tab]").forEach(tab => {
  tab.addEventListener("click", () => pushShopView({ tab: tab.dataset.shopTab }));
});
shopSortField.addEventListener("change", () => pushShopView());
shopSortAlgo.addEventListener("change", () => pushShopView());
shopSortDir.addEventListener("click", () => pushShopView({ descending: shopSortDir.dataset.descending !== "true" }));

/* Walking into and out of the shop uses the same loading transition as the menu. */
document.getElementById("shop-button").addEventListener("click", () => runTransition({
  title: "Heading to the shop",
  sub: "Dusting off the shelves…",
  work: () => {
    setDrawerOpen(false);
    setExtrasOpen(false);
    showScreen("shop");
    document.getElementById("shop-note").textContent = "";
    askPython("shop_open");
  }
}));
document.getElementById("shop-back-button").addEventListener("click", () => runTransition({
  title: "Back to the garden",
  sub: "Putting the gardening gloves back on…",
  work: () => showScreen("garden")
}));

/* =====================================================================
   SECTION 12 - HERBARIUM (Lessons 4, 5, 9) - the collection book
   Python decides what is in the book and in which order; this code just
   draws the two pages and sends clicks back to Python.
   ===================================================================== */
const potionAssets = {
  "Purr-fect Potion": "assets/potions/Purr-fect%20Potion.png",
  "SunnySide Elixir": "assets/potions/SunnySide%20Elixir.png",
  "Starlit Elixir": "assets/potions/Starlit%20Elixir.png"
};
const herbariumLayer = document.getElementById("herbarium");
const herbBook = document.getElementById("herb-book");
const herbScrim = document.getElementById("herb-scrim");
const herbList = document.getElementById("herb-list");
const herbDetail = document.getElementById("herb-detail");
const herbQuery = document.getElementById("herb-query");
const herbMethod = document.getElementById("herb-method");
const herbOrder = document.getElementById("herb-order");
let herbariumState = "closed";   // closed | opening | open | closing
let herbariumWantsClose = false;
let herbData = null;

["Binary Search", "BST Search", "Linear Search"].forEach(name => herbMethod.add(new Option(name, name)));

function entryArt(name) {
  return plantAssets[name] ? plantAssets[name].grown : potionAssets[name];
}

/* Bridge: Python sends the whole book; this draws it. */
function updateHerbarium(jsonText) {
  herbData = JSON.parse(jsonText);
  renderHerbarium();
}

function renderHerbarium() {
  if (!herbData) return;
  const data = herbData;
  document.getElementById("herb-progress").textContent = `${data.progress.found}/${data.progress.total} found`;
  herbOrder.value = data.order;
  document.getElementById("herb-note").textContent = data.note;

  // search result line
  const resultLine = document.getElementById("herb-search-result");
  if (data.search) {
    const path = data.search.path.length ? ` Looked at: ${data.search.path.join(" → ")}. (${data.search.big_o})` : "";
    resultLine.textContent = data.search.message + path;
  } else {
    resultLine.textContent = "";
  }

  // left page: the list in the order Python chose
  herbList.replaceChildren();
  data.rows.forEach(row => {
    const item = document.createElement(row.kind === "entry" ? "button" : "div");
    item.className = `herb-row ${row.kind}`;
    item.style.setProperty("--depth", row.depth);
    item.setAttribute("role", "listitem");
    const visit = document.createElement("span");
    visit.className = "herb-visit";
    visit.textContent = row.visit;
    visit.title = "Visit order";
    item.appendChild(visit);
    if (row.kind === "entry") {
      item.type = "button";
      const picture = document.createElement("span");
      picture.className = "herb-thumb";
      if (row.unlocked) {
        const image = document.createElement("img");
        image.src = entryArt(row.name);
        image.alt = "";
        picture.appendChild(image);
      } else {
        picture.textContent = "?";
      }
      const label = document.createElement("span");
      label.className = "herb-label";
      label.textContent = row.unlocked ? row.name : "???";
      item.append(picture, label);
      item.disabled = !row.unlocked;
      item.classList.toggle("locked", !row.unlocked);
      item.classList.toggle("selected", row.name === data.selected);
      if (row.unlocked) item.addEventListener("click", () => askPython("herbarium_select", row.name));
    } else {
      const label = document.createElement("span");
      label.className = "herb-label";
      label.textContent = row.name;
      const progress = document.createElement("small");
      progress.textContent = row.progress;
      item.append(label, progress);
    }
    herbList.appendChild(item);
  });
  const selectedRow = herbList.querySelector(".herb-row.selected");
  if (selectedRow) selectedRow.scrollIntoView({ block: "nearest" });

  // right page: the entry
  herbDetail.replaceChildren();
  const entry = data.entry;
  if (!entry) {
    const hint = document.createElement("p");
    hint.className = "herb-empty";
    hint.textContent = "Choose a page from the list to read about it. Entries marked ??? are still waiting to be discovered. Harvest a plant to add it to the book!";
    herbDetail.appendChild(hint);
    return;
  }
  const top = document.createElement("div");
  top.className = "herb-top";
  const image = document.createElement("img");
  image.src = entryArt(entry.name);
  image.alt = "";
  const titles = document.createElement("div");
  const title = document.createElement("h3");
  title.textContent = entry.name;
  const kind = document.createElement("span");
  kind.className = "herb-kind";
  kind.textContent = entry.kind === "plant" ? "Plant" : "Potion";
  titles.append(title, kind);
  top.append(image, titles);
  herbDetail.appendChild(top);
  if (entry.quote) {
    const quote = document.createElement("blockquote");
    quote.textContent = `“${entry.quote}”`;
    herbDetail.appendChild(quote);
  }
  if (entry.facts) {
    const facts = document.createElement("p");
    facts.className = "herb-facts";
    facts.textContent = entry.facts;
    herbDetail.appendChild(facts);
  }
  entry.sections.forEach(([heading, text]) => {
    const section = document.createElement("section");
    const h4 = document.createElement("h4");
    h4.textContent = heading;
    const p = document.createElement("p");
    p.textContent = text;
    if (heading.startsWith("Nyra")) section.className = "nyra-note";
    section.append(h4, p);
    herbDetail.appendChild(section);
  });
  herbDetail.scrollTop = 0;
}

function runHerbariumSearch() {
  askPython("herbarium_search", herbQuery.value, herbMethod.value);
}
document.getElementById("herb-go").addEventListener("click", runHerbariumSearch);
herbQuery.addEventListener("keydown", event => { if (event.key === "Enter") runHerbariumSearch(); });
herbOrder.addEventListener("change", () => askPython("herbarium_set_order", herbOrder.value));

const BOOK_AWAY = "translate(-50%, calc(-50% + 34svh)) scale(.78)";
const BOOK_SHOWN = "translate(-50%, -50%) scale(1)";

async function openHerbarium() {
  if (herbariumState !== "closed" || inventoryState !== "closed") return;
  if (!pythonReady) { askPython("herbarium_open"); return; }
  herbariumState = "opening";
  playSound("transition");
  herbariumWantsClose = false;
  setDrawerOpen(false);
  askPython("herbarium_open");
  [herbScrim, herbBook].forEach(el => el.getAnimations().forEach(a => a.cancel()));
  herbariumLayer.hidden = false;
  play(herbScrim, [{ opacity: 0 }, { opacity: 1 }], 280);
  await play(herbBook, [{ transform: BOOK_AWAY, opacity: 0 }, { transform: BOOK_SHOWN, opacity: 1 }], 520, "cubic-bezier(.2, .9, .3, 1.08)");
  herbariumState = "open";
  document.getElementById("herb-close").focus({ preventScroll: true });
  if (herbariumWantsClose) closeHerbarium();
}

async function closeHerbarium() {
  if (herbariumState === "opening") { herbariumWantsClose = true; return; }
  if (herbariumState !== "open") return;
  herbariumState = "closing";
  play(herbScrim, [{ opacity: 1 }, { opacity: 0 }], 300);
  await play(herbBook, [{ transform: BOOK_SHOWN, opacity: 1 }, { transform: BOOK_AWAY, opacity: 0 }], 320, "ease-in");
  herbariumLayer.hidden = true;
  herbariumState = "closed";
  document.getElementById("herbarium-button").focus({ preventScroll: true });
}
document.getElementById("herb-close").addEventListener("click", closeHerbarium);
herbScrim.addEventListener("click", closeHerbarium);

function trapHerbariumFocus(event) {
  if (event.key !== "Tab" || herbariumState === "closed") return;
  const focusable = Array.from(herbBook.querySelectorAll("button:not(:disabled), input, select")).filter(el => el.offsetParent !== null);
  if (!focusable.length) return;
  const first = focusable[0], last = focusable[focusable.length - 1];
  if (!herbBook.contains(document.activeElement)) { event.preventDefault(); first.focus(); }
  else if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
  else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
}


/* =========================================================================
   SECTION 13 - Main menu life
   Fireflies, and the Settings / Credits placeholders.
   ========================================================================= */
/* ---------- Main menu life ---------- */
// Drifting fireflies and sparkles. Positions and speeds are random so it never looks like a loop.
(function buildSparkles() {
  const layer = document.getElementById("menu-sparkles");
  for (let i = 0; i < 26; i++) {
    const spark = document.createElement("span");
    const pink = i % 5 === 0;
    spark.className = "spark" + (pink ? " pink" : "");
    spark.style.left = `${Math.random() * 100}%`;
    spark.style.bottom = `${-5 + Math.random() * 45}%`;
    spark.style.setProperty("--size", `${3 + Math.random() * 6}px`);
    spark.style.setProperty("--drift", `${(Math.random() - .5) * 90}px`);
    spark.style.animationDuration = `${9 + Math.random() * 12}s`;
    spark.style.animationDelay = `${-Math.random() * 20}s`;
    layer.appendChild(spark);
  }
})();

// Temporary menu buttons until Settings and Credits screens exist.
function menuNoteText(text) { menuNote.textContent = text; }
document.getElementById("settings-menu-button").addEventListener("click", () => openDialog("settings"));
document.getElementById("credits-menu-button").addEventListener("click", () => openDialog("credits"));

/* The grid position is tuned in css/style.css to match the supplied 1920x1080 background.
   If it looks slightly off on your monitor, we can adjust the percentage values together. */


/* =========================================================================
   SECTION 14 - Map window  (Lesson 7: graphs, BFS and DFS)
   Python owns the graph and the two walks; this code only draws the places,
   the paths and the visiting order, and sends clicks back to Python.
   ========================================================================= */
const mapLayer = document.getElementById("map-layer");
const mapPanel = document.getElementById("map-panel");
const mapSvg = document.getElementById("map-svg");
const mapModeSelect = document.getElementById("map-mode");
let mapState = "closed";   // closed | open
let mapData = null;

/* Bridge: Python sends everything the map needs as text. */
function updateMap(jsonText) {
  mapData = JSON.parse(jsonText);
  renderMap();
}

function svgEl(tag, attributes = {}, text) {
  const element = document.createElementNS("http://www.w3.org/2000/svg", tag);
  Object.entries(attributes).forEach(([name, value]) => element.setAttribute(name, value));
  if (text !== undefined) element.textContent = text;
  return element;
}

function renderMap() {
  if (!mapData) return;
  const data = mapData;
  document.getElementById("map-progress").textContent = `${data.progress.found}/${data.progress.total} places found`;
  mapModeSelect.value = data.mode;
  document.getElementById("map-note").textContent = data.note;
  document.getElementById("map-message").textContent = data.message;
  document.getElementById("map-structure").textContent = `(waiting ${data.structure})`;

  // the drawing: paths first, so places sit on top of them
  mapSvg.replaceChildren();
  const spot = {};
  data.places.forEach(place => { spot[place.id] = place; });
  const routeIds = data.route ? data.route.ids : [];
  const onRoute = (a, b) => routeIds.some((id, i) => i > 0 && ((routeIds[i - 1] === a && id === b) || (routeIds[i - 1] === b && id === a)));
  data.roads.forEach(road => {
    const a = spot[road.a], b = spot[road.b];
    const lineClass = `${road.known ? "map-road" : "map-road unknown"}${onRoute(road.a, road.b) ? " on-route" : ""}`;
    mapSvg.appendChild(svgEl("line", { x1: a.x, y1: a.y, x2: b.x, y2: b.y, class: lineClass }));
    if (road.known) {
      const t = 0.32;     // a bit closer to the first place, so the label stays clear of the place names
      mapSvg.appendChild(svgEl("text", { x: a.x + (b.x - a.x) * t, y: a.y + (b.y - a.y) * t + 1, class: "map-minutes" }, `${road.minutes}m`));
    }
  });
  data.places.forEach(place => {
    const group = svgEl("g", { class: `map-place${place.known ? "" : " unknown"}${place.id === data.selected_id ? " selected" : ""}${routeIds.includes(place.id) ? " on-route" : ""}` });
    if (place.known) {
      group.setAttribute("tabindex", "0");
      group.setAttribute("role", "button");
      group.setAttribute("aria-label", `${place.name}, stop ${place.step}`);
      const choose = () => askPython("map_select", place.real);
      group.addEventListener("click", choose);
      group.addEventListener("keydown", event => {
        if (event.key === "Enter" || event.key === " ") { event.preventDefault(); choose(); }
      });
    } else {
      group.setAttribute("aria-label", "An undiscovered place");
    }
    group.appendChild(svgEl("circle", { cx: place.x, cy: place.y, r: 5.4, class: "map-dot" }));
    group.appendChild(svgEl("text", { x: place.x, y: place.y + 1.9, class: "map-dot-text" }, place.known ? String(place.step) : "?"));
    group.appendChild(svgEl("text", { x: place.x, y: place.y + 10, class: "map-name" }, place.name));
    mapSvg.appendChild(group);
  });

  // the selected place
  const detail = document.getElementById("map-detail");
  detail.replaceChildren();
  if (data.detail) {
    const title = document.createElement("strong");
    title.textContent = data.detail.name;
    const blurb = document.createElement("p");
    blurb.textContent = data.detail.blurb;
    const facts = document.createElement("p");
    facts.className = "map-facts";
    const roads = data.detail.neighbours.map(n => `${n.name} (${n.minutes} min)`).join(", ");
    facts.textContent = `${data.detail.hops} path(s) from the ${data.home} · Paths lead to: ${roads}`;
    detail.append(title, blurb, facts);
  }

  // Lesson 10: the cheapest route (Dijkstra) and the errand trip (greedy)
  const routeBox = document.getElementById("map-route-result");
  routeBox.replaceChildren();
  if (data.route) {
    const route = data.route;
    addResultLine(routeBox, `Cheapest to ${route.goal} (Dijkstra): ${route.cheapest.path.join(" → ")} = ${route.cheapest.minutes} min`, "good");
    addResultLine(routeBox, `Fewest stops (breadth-first): ${route.fewest.path.join(" → ")} = ${route.fewest.minutes} min`, route.same ? "" : "bad");
    addResultLine(routeBox, `Dijkstra settled: ${route.settled.map(s => `${s.name} ${s.minutes}`).join(", ")}`, "small");
  }
  routeBox.hidden = !data.route;
  const tripBox = document.getElementById("map-trip-result");
  tripBox.replaceChildren();
  if (data.trip) {
    const trip = data.trip;
    addResultLine(tripBox, `Errands: ${trip.stops.join(", ")} (then home)`, "small");
    addResultLine(tripBox, `Greedy (nearest next): ${trip.greedy.order.join(" → ")} = ${trip.greedy.minutes} min`, trip.same ? "good" : "bad");
    addResultLine(tripBox, `Best order (tried ${trip.tried}): ${trip.best.order.join(" → ")} = ${trip.best.minutes} min`, "good");
  }
  tripBox.hidden = !data.trip;

  // the visiting order: who is visited, who led there, and who is still waiting
  const steps = document.getElementById("map-steps");
  steps.replaceChildren();
  data.steps.forEach(step => {
    const row = document.createElement("li");
    row.className = step.name === "???" ? "unknown" : "";
    const waiting = step.waiting.length ? step.waiting.join(", ") : "nobody";
    const from = step.came_from ? ` from ${step.came_from}` : " (start)";
    row.textContent = `${step.name}${from} — ${data.structure}: ${waiting}`;
    steps.appendChild(row);
  });
}

function addResultLine(box, text, tone) {
  const line = document.createElement("p");
  line.className = tone ? `map-line ${tone}` : "map-line";
  line.textContent = text;
  box.appendChild(line);
}

function openMap() {
  if (mapState !== "closed" || inventoryState !== "closed" || herbariumState !== "closed") return;
  askPython("map_open");
  setDrawerOpen(false);
  playSound("transition");
  mapState = "open";
  mapLayer.hidden = false;
  play(mapPanel, [{ transform: "translate(-50%, -46%) scale(.96)", opacity: 0 }, { transform: "translate(-50%, -50%) scale(1)", opacity: 1 }], 260, "ease-out");
  play(document.getElementById("map-scrim"), [{ opacity: 0 }, { opacity: 1 }], 220);
  document.getElementById("map-close").focus({ preventScroll: true });
}

function closeMap() {
  if (mapState !== "open") return;
  mapState = "closed";
  mapLayer.hidden = true;
  document.getElementById("map-button").focus({ preventScroll: true });
}

function trapMapFocus(event) {
  if (event.key !== "Tab" || mapState === "closed") return;
  const focusable = Array.from(mapPanel.querySelectorAll("button:not(:disabled), select, [tabindex='0']")).filter(el => el.getAttribute("tabindex") !== "-1");
  if (!focusable.length) return;
  const first = focusable[0], last = focusable[focusable.length - 1];
  if (!mapPanel.contains(document.activeElement)) { event.preventDefault(); first.focus(); }
  else if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
  else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
}

document.getElementById("map-close").addEventListener("click", closeMap);
document.getElementById("map-scrim").addEventListener("click", closeMap);
document.getElementById("map-explore").addEventListener("click", () => askPython("map_explore"));
document.getElementById("map-route").addEventListener("click", () => askPython("map_route"));
document.getElementById("map-errands").addEventListener("click", () => askPython("map_errands"));
mapModeSelect.addEventListener("change", () => askPython("map_set_mode", mapModeSelect.value));


/* =========================================================================
   SECTION 15 - Cauldron window  (Lesson 11: dynamic programming)
   Python owns the recipes, the prices and Nyra's dynamic-programming advice; this
   code draws the recipe cards and Nyra's answer, and sends button clicks back.
   ========================================================================= */
const cauldronLayer = document.getElementById("cauldron-layer");
const cauldronPanel = document.getElementById("cauldron-panel");
let cauldronState = "closed";   // closed | open

/* Bridge: Python sends everything the Cauldron needs as text. data.opened is true only when the
   player has just walked up to the Cauldron (Python checks that it was found on the Map first). */
function updateCauldron(jsonText) {
  const data = JSON.parse(jsonText);
  renderCauldron(data);
  if (data.opened) showCauldron();
  if (data.brewed && data.brewed.length) playBrew(data.brewed);
}

function chip(text, enough) {
  const element = document.createElement("span");
  element.className = `cauldron-chip ${enough ? "enough" : "missing"}`;
  element.textContent = text;
  return element;
}

function renderCauldron(data) {
  document.getElementById("cauldron-weather").textContent = `${data.time === "Night" ? "☾" : "☀"} ${TIME_NAMES[data.time]} · ${data.symbol} ${data.weather}`;
  document.getElementById("cauldron-demand").textContent = data.demand;
  document.getElementById("cauldron-message").textContent = data.message;
  document.getElementById("cauldron-plan").disabled = !(data.advice ? data.advice.plan.length : data.potions.some(potion => potion.can_brew));

  const recipes = document.getElementById("cauldron-recipes");
  recipes.replaceChildren();
  data.potions.forEach(potion => {
    const card = document.createElement("div");
    card.className = "cauldron-card";
    card.setAttribute("role", "listitem");

    const image = document.createElement("img");
    image.src = potionAssets[potion.art];       // art is always the real name, even while the recipe is still a secret
    image.alt = "";
    image.draggable = false;

    if (potion.locked) {                        // a recipe Nyra hasn't learned yet: only a dark silhouette
      card.classList.add("locked");
      image.classList.add("silhouette");
      const secret = document.createElement("div");
      secret.className = "cauldron-card-info";
      const secretName = document.createElement("strong");
      secretName.textContent = "???";
      const secretLevel = document.createElement("span");
      secretLevel.className = "cauldron-price";
      secretLevel.textContent = `🔒 Nyra learns this recipe at level ${potion.unlock_level}`;
      secret.append(secretName, secretLevel);
      const lockedBrew = document.createElement("button");
      lockedBrew.type = "button";
      lockedBrew.className = "top-button shop-btn";
      lockedBrew.textContent = "Locked";
      lockedBrew.disabled = true;
      card.append(image, secret, lockedBrew);
      recipes.appendChild(card);
      return;
    }

    const info = document.createElement("div");
    info.className = "cauldron-card-info";
    const name = document.createElement("strong");
    name.textContent = potion.name;
    const price = document.createElement("span");
    price.className = potion.price > potion.base_price ? "cauldron-price up" : "cauldron-price";
    price.textContent = potion.price > potion.base_price
      ? `Sells for ${potion.price} coins today (${potion.base_price} normally)`
      : `Sells for ${potion.price} coins`;
    const worth = document.createElement("small");
    worth.textContent = `The plants alone sell for ${potion.plants_worth} · You own ${potion.owned}`;
    const chips = document.createElement("div");
    chips.className = "cauldron-chips";
    potion.ingredients.forEach(item => {
      chips.appendChild(chip(`${plantAssets[item.name].label} ${item.have}/${item.need}`, item.have >= item.need));
    });
    const lookup = document.createElement("small");
    lookup.className = "cauldron-lookup";
    lookup.textContent = `Recipe book lookup (hash table): slot ${potion.lookup.slot}, ${potion.lookup.compared} compared`;
    info.append(name, price, worth, chips);
    if (potion.note) {
      const note = document.createElement("small");
      note.className = "cauldron-card-note";
      note.textContent = potion.note;
      info.appendChild(note);
    }
    info.appendChild(lookup);

    const brew = document.createElement("button");
    brew.type = "button";
    brew.className = "top-button shop-btn";
    brew.textContent = "Brew";
    brew.disabled = !potion.can_brew;
    brew.addEventListener("click", () => { rememberBrewSource(image); askPython("cauldron_brew", potion.name); });

    card.append(image, info, brew);
    recipes.appendChild(card);
  });

  // Nyra's answer: the best plan, how it compares, and how much work the memory saved
  const box = document.getElementById("cauldron-advice");
  box.replaceChildren();
  const advice = data.advice;
  if (advice) {
    addResultLine(box, `Selling the plants as they are: ${advice.baseline} coins`, "small");
    addResultLine(box, `Nyra's plan (dynamic programming): ${advice.best} coins`, "good");
    const greedyPlan = advice.greedy.plan.length ? advice.greedy.plan.map(item => `${item.count} ${item.name}${item.count > 1 ? "s" : ""}`).join(" + ") : "nothing";
    addResultLine(box, `Greedy, priciest potion first (${greedyPlan}): ${advice.greedy.coins} coins${advice.greedy_fooled ? " - fooled!" : ""}`, advice.greedy_fooled ? "bad" : "small");
    const plain = advice.naive_stopped ? `more than ${advice.naive_calls.toLocaleString()} calls (stopped counting)` : `${advice.naive_calls.toLocaleString()} calls`;
    addResultLine(box, `Plain recursion would need ${plain}. With a memory: ${advice.states} different situations solved, ${advice.reused} answers reused.`, "small");
  }
  box.hidden = !advice;
}

/* ---------- Cauldron scene: opening, closing and the "throw the plants in" animation ----------
   Only the LOOK lives here. What gets brewed is decided by Python; Python just tells us which
   plants went into which potion (data.brewed) so we can throw exactly those in. */
const potWrap = document.getElementById("pot-wrap");
const potArt = document.getElementById("pot-art");
const potResult = document.getElementById("pot-result");
const cauldronParts = () => ({
  scrim: document.getElementById("cauldron-scrim"),
  head: cauldronPanel.querySelector(".cauldron-head"),
  demand: document.getElementById("cauldron-demand"),
  left: cauldronPanel.querySelector(".cauldron-left"),
  right: cauldronPanel.querySelector(".cauldron-right")
});
let brewFromRect = null;     // where the plants start flying from (the button / potion picture that was clicked)

function rememberBrewSource(element) {
  brewFromRect = element.getBoundingClientRect();
}

function showCauldron() {
  if (cauldronState !== "closed" || mapState !== "closed" || inventoryState !== "closed" || herbariumState !== "closed") return;
  setDrawerOpen(false);
  cauldronState = "open";
  playSound("transition");
  soundForCauldron(true);                         // the cauldron bubbles while its window is open
  const parts = cauldronParts();
  [potWrap, potResult, ...Object.values(parts)].forEach(element => element.getAnimations().forEach(a => a.cancel()));
  cauldronLayer.hidden = false;
  potResult.hidden = true;
  play(parts.scrim, [{ opacity: 0 }, { opacity: 1 }], 320);
  // 1) the big cauldron rises from the bottom middle, with a little overshoot
  play(potWrap, [{ transform: "translateY(88svh)" }, { transform: "translateY(-2.5svh)", offset: .72 }, { transform: "translateY(0)" }], 820, "cubic-bezier(.2, .8, .3, 1)");
  // 2) then the panels slide in from the two sides
  play(parts.head, [{ transform: "translateY(-80px)", opacity: 0 }, { transform: "translateY(0)", opacity: 1 }], 480, "ease-out");
  play(parts.demand, [{ opacity: 0 }, { opacity: 1 }], 500, "ease-out");
  wait(380).then(() => {
    if (cauldronState !== "open") return;
    play(parts.left, [{ transform: "translateX(-115%)", opacity: 0 }, { transform: "translateX(0)", opacity: 1 }], 560, "cubic-bezier(.2, .9, .3, 1)");
    play(parts.right, [{ transform: "translateX(115%)", opacity: 0 }, { transform: "translateX(0)", opacity: 1 }], 560, "cubic-bezier(.2, .9, .3, 1)");
  });
  document.getElementById("cauldron-close").focus({ preventScroll: true });
}

function openCauldron() {
  if (cauldronState !== "closed" || mapState !== "closed" || inventoryState !== "closed" || herbariumState !== "closed") return;
  askPython("cauldron_open");     // Python opens the window by calling updateCauldron, if the Cauldron has been found
}

async function closeCauldron() {
  if (cauldronState !== "open") return;
  cauldronState = "closing";
  soundForCauldron(false);                        // the bubbling fades out as the cauldron sinks
  cauldronLayer.querySelectorAll(".fly-plant, .pot-splash, .pot-drop").forEach(element => element.remove());
  potResult.hidden = true;
  const parts = cauldronParts();
  play(parts.left, [{ transform: "translateX(0)", opacity: 1 }, { transform: "translateX(-115%)", opacity: 0 }], 300, "ease-in");
  play(parts.right, [{ transform: "translateX(0)", opacity: 1 }, { transform: "translateX(115%)", opacity: 0 }], 300, "ease-in");
  play(parts.head, [{ opacity: 1 }, { opacity: 0 }], 260);
  play(parts.demand, [{ opacity: 1 }, { opacity: 0 }], 260);
  play(parts.scrim, [{ opacity: 1 }, { opacity: 0 }], 420);
  play(potWrap, [{ transform: "translateY(0)" }, { transform: "translateY(90svh)" }], 440, "ease-in");
  await wait(460);                // wait by time, so closing never depends on how fast the screen is drawing
  cauldronLayer.hidden = true;
  cauldronState = "closed";
  document.getElementById("cauldron-button").focus({ preventScroll: true });
}

/* The mouth of the cauldron, in screen coordinates. */
function potMouth() {
  const box = potArt.getBoundingClientRect();
  return { x: box.left + box.width * 0.5, y: box.top + box.height * 0.44 };
}

/* A curved path from one point to another (a parabola), as animation frames. */
function arcFrames(from, to, lift) {
  const frames = [];
  const steps = 14;
  for (let i = 0; i <= steps; i++) {
    const t = i / steps;
    const x = from.x + (to.x - from.x) * t;
    const y = from.y + (to.y - from.y) * t - Math.sin(Math.PI * t) * lift;
    frames.push({ transform: `translate(${x}px, ${y}px) translate(-50%, -50%) scale(${1 - 0.5 * t}) rotate(${t * 300}deg)`, opacity: t > 0.9 ? 0.3 : 1, offset: t });
  }
  return frames;
}

function floatingPiece(className, point) {
  const element = document.createElement(className === "fly-plant" ? "img" : "span");
  element.className = className;
  element.style.left = `${point.x}px`;
  element.style.top = `${point.y}px`;
  cauldronLayer.appendChild(element);
  return element;
}

function splashAt(point) {
  const ring = floatingPiece("pot-splash", point);
  play(ring, [{ transform: "translate(-50%, -50%) scale(.3)", opacity: .95 }, { transform: "translate(-50%, -50%) scale(1.7)", opacity: 0 }], 600, "ease-out").then(() => ring.remove());
  for (let i = 0; i < 5; i++) {                       // little drops jump out of the cauldron
    const drop = floatingPiece("pot-drop", point);
    const dx = (Math.random() - 0.5) * 120, rise = 50 + Math.random() * 70;
    play(drop, [{ transform: "translate(-50%, -50%)", opacity: 1 }, { transform: `translate(calc(-50% + ${dx}px), calc(-50% - ${rise}px))`, opacity: 0 }], 520 + Math.random() * 200, "ease-out").then(() => drop.remove());
  }
  // the cauldron squashes and bounces
  play(potArt, [{ transform: "scale(1)" }, { transform: "scale(1.07, .92)", offset: .3 }, { transform: "scale(.97, 1.05)", offset: .65 }, { transform: "scale(1)" }], 420, "ease-out");
}

async function throwPlant(plantName, from, to) {
  const flyer = floatingPiece("fly-plant", { x: 0, y: 0 });
  flyer.style.left = "0";
  flyer.style.top = "0";
  flyer.src = plantAssets[plantName].grown;
  flyer.alt = "";
  await play(flyer, arcFrames(from, to, 140), 720, "linear");
  flyer.remove();
  if (cauldronState === "open") splashAt(to);
}

/* The finished potion pops out of the cauldron with its name. */
async function showPotionResult(potionName) {
  potResult.querySelector("img").src = potionAssets[potionName];
  potResult.querySelector("strong").textContent = potionName;
  potResult.querySelector("small").textContent = "Brewed!";
  potResult.hidden = false;
  await play(potResult, [
    { transform: "translate(-50%, 160%) scale(.3)", opacity: 0 },
    { transform: "translate(-50%, -12%) scale(1.15)", opacity: 1, offset: .6 },
    { transform: "translate(-50%, 0) scale(1)", opacity: 1 }
  ], 620, "ease-out");
  await wait(1200);
  if (cauldronState !== "open") return;
  await play(potResult, [{ opacity: 1 }, { opacity: 0 }], 320);
  potResult.hidden = true;
}

let brewAnimating = false;
async function playBrew(brewed) {
  if (cauldronState !== "open") return;
  brewAnimating = true;
  document.getElementById("cauldron-recipes").classList.add("busy");
  const to = potMouth();
  const start = brewFromRect
    ? { x: brewFromRect.left + brewFromRect.width / 2, y: brewFromRect.top + brewFromRect.height / 2 }
    : { x: window.innerWidth * 0.8, y: window.innerHeight * 0.3 };
  for (const entry of brewed) {
    if (cauldronState !== "open") break;
    await Promise.all(entry.plants.map((plant, i) => wait(i * 190).then(() => throwPlant(plant, start, to))));
    await wait(160);
    if (cauldronState === "open") await showPotionResult(entry.potion);
  }
  brewAnimating = false;
  document.getElementById("cauldron-recipes").classList.remove("busy");
}

function trapCauldronFocus(event) {
  if (event.key !== "Tab" || cauldronState === "closed") return;
  const focusable = Array.from(cauldronPanel.querySelectorAll("button:not(:disabled)"));
  if (!focusable.length) return;
  const first = focusable[0], last = focusable[focusable.length - 1];
  if (!cauldronPanel.contains(document.activeElement)) { event.preventDefault(); first.focus(); }
  else if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
  else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
}

document.getElementById("cauldron-button").addEventListener("click", openCauldron);
document.getElementById("cauldron-close").addEventListener("click", closeCauldron);
document.getElementById("cauldron-scrim").addEventListener("click", closeCauldron);
document.getElementById("cauldron-ask").addEventListener("click", () => askPython("cauldron_ask"));
document.getElementById("cauldron-plan").addEventListener("click", event => { rememberBrewSource(event.currentTarget); askPython("cauldron_brew_plan"); });


/* =========================================================================
   SECTION 16 - Garden weather effects
   Rain falls when the picture is the rain one (day or night). Fireflies drift around on
   nights without rain. Everything is random, so it never looks like a loop.
   ========================================================================= */
(function buildWeatherEffects() {
  const rain = document.getElementById("fx-rain");
  for (let i = 0; i < 140; i++) {
    const drop = document.createElement("span");
    drop.className = "drop";
    const near = Math.random() < 0.3;                         // bigger, faster drops look closer
    drop.style.left = `${Math.random() * 112 - 6}%`;
    drop.style.setProperty("--length", `${near ? 22 + Math.random() * 14 : 12 + Math.random() * 10}px`);
    drop.style.setProperty("--alpha", near ? 0.85 : 0.5 + Math.random() * 0.2);
    drop.style.animationDuration = `${near ? 0.55 + Math.random() * 0.25 : 0.85 + Math.random() * 0.45}s`;
    drop.style.animationDelay = `${-Math.random() * 1.5}s`;
    rain.appendChild(drop);
  }

  const fireflies = document.getElementById("fx-fireflies");
  const wander = () => `${Math.round((Math.random() - 0.5) * 220)}px`;
  for (let i = 0; i < 30; i++) {
    const fly = document.createElement("span");
    fly.className = "firefly" + (i % 6 === 0 ? " pink" : "");
    fly.style.left = `${Math.random() * 100}%`;
    fly.style.top = `${28 + Math.random() * 66}%`;
    fly.style.setProperty("--size", `${5 + Math.random() * 5}px`);
    ["x1", "y1", "x2", "y2", "x3", "y3"].forEach(name => fly.style.setProperty(`--${name}`, wander()));
    fly.style.animationDuration = `${14 + Math.random() * 14}s, ${2.2 + Math.random() * 3}s`;     // wandering, blinking
    fly.style.animationDelay = `${-Math.random() * 20}s, ${-Math.random() * 5}s`;
    fireflies.appendChild(fly);
  }
})();

/* Called by setScene: which effect belongs to the picture that is now showing. */
function setWeatherEffect(scene) {
  const effect = scene === "rain" ? "rain" : (scene === "night" || scene === "starry") ? "fireflies" : "none";
  document.getElementById("weather-fx").dataset.fx = effect;
}


/* =========================================================================
   SECTION 17 - Clicking Nyra
   Her picture is bigger than she is, and the empty space around her must still let clicks reach
   the plots. So we test the pixel under the mouse: only her body counts. Python decides what
   she says (nyra_poke); this code only notices the click and gives her a little hop.
   ========================================================================= */
const gardenScreenElement = document.getElementById("garden-screen");
const nyraBodyMasks = new Map();   // sprite file -> a small copy of its see-through pixels

function nyraMask(image) {
  if (!image.complete || !image.naturalWidth) return null;
  if (nyraBodyMasks.has(image.src)) return nyraBodyMasks.get(image.src);
  let mask = null;
  try {
    const width = 200, height = Math.round(width * image.naturalHeight / image.naturalWidth);
    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;
    const context = canvas.getContext("2d", { willReadFrequently: true });
    context.drawImage(image, 0, 0, width, height);
    mask = { width, height, pixels: context.getImageData(0, 0, width, height).data };
  } catch (error) {
    mask = null;      // the browser would not let us read the picture; we fall back to a rough box
  }
  nyraBodyMasks.set(image.src, mask);
  return mask;
}

function pointIsNyra(clientX, clientY) {
  const image = document.getElementById("nyra-sprite");
  const box = image.getBoundingClientRect();
  if (!image.naturalWidth || box.width === 0) return false;
  // the picture is drawn "contain" and stuck to the bottom of its box: find where it really is
  const scale = Math.min(box.width / image.naturalWidth, box.height / image.naturalHeight);
  const drawnWidth = image.naturalWidth * scale, drawnHeight = image.naturalHeight * scale;
  const across = (clientX - box.left - (box.width - drawnWidth) / 2) / drawnWidth;
  const down = (clientY - box.top - (box.height - drawnHeight)) / drawnHeight;
  if (across < 0 || across >= 1 || down < 0 || down >= 1) return false;
  const mask = nyraMask(image);
  if (!mask) return across > 0.2 && across < 0.8 && down > 0.1;
  const column = Math.floor(across * mask.width), row = Math.floor(down * mask.height);
  return mask.pixels[(row * mask.width + column) * 4 + 3] > 40;       // is this pixel solid, not see-through?
}

function pokeNyra() {
  askPython("nyra_poke");
  const image = document.getElementById("nyra-sprite");
  play(image, [
    { transform: "translateY(0) scale(1, 1)" },
    { transform: "translateY(-1.2%) scale(1.01, .99)" },
    { transform: "translateY(0) scale(1, 1)" },
  ], 320, "ease-out");
}

// A click on bare garden (not a plot, button or window) might be a click on Nyra.
gardenScreenElement.addEventListener("click", event => {
  if (event.target === gardenScreenElement && pointIsNyra(event.clientX, event.clientY)) pokeNyra();
});

let nyraHoverCheckPending = false;
gardenScreenElement.addEventListener("pointermove", event => {
  if (nyraHoverCheckPending) return;
  nyraHoverCheckPending = true;
  window.requestAnimationFrame(() => {
    nyraHoverCheckPending = false;
    gardenScreenElement.classList.toggle("over-nyra", event.target === gardenScreenElement && pointIsNyra(event.clientX, event.clientY));
  });
});

document.getElementById("nyra-pat").addEventListener("click", pokeNyra);


/* =========================================================================
   SECTION 18 - Level badge
   Python owns XP, levels and what each level unlocks; this only draws the badge in the top bar
   (Lv N and a progress bar) and gives it a little pop when a new level is reached.
   Locked seeds (Shop) and locked recipes (Cauldron) are drawn in SECTION 11 and SECTION 15.
   ========================================================================= */
const levelPill = document.getElementById("level-pill");
const levelLabel = document.getElementById("level-label");
const levelFill = document.getElementById("level-fill");

function updateLevel(level, xpInto, xpNext, leveledUp) {
  const maxed = xpNext === 0;
  levelLabel.textContent = maxed ? `Lv ${level} · MAX` : `Lv ${level}`;
  levelFill.style.width = `${Math.round((maxed ? 1 : Math.min(1, xpInto / xpNext)) * 100)}%`;
  const detail = maxed ? "Top level reached!" : `${xpInto}/${xpNext} XP to level ${level + 1}`;
  levelPill.title = detail;
  levelPill.setAttribute("aria-label", `Level ${level}. ${detail}`);
  if (leveledUp) {
    play(levelPill, [
      { transform: "scale(1)", boxShadow: "0 0 0 0 rgba(255, 226, 140, .9)" },
      { transform: "scale(1.2)", boxShadow: "0 0 0 10px rgba(255, 226, 140, 0)" },
      { transform: "scale(1)", boxShadow: "0 0 0 0 rgba(255, 226, 140, 0)" },
    ], 900, "ease-out");
  }
}


/* ---- Level-up celebration (part of SECTION 18) ---- */
const levelUpLayer = document.getElementById("levelup-layer");
const levelUpCard = document.getElementById("levelup-card");
const levelUpColours = ["#ffd36e", "#f48fa8", "#c9a7ff", "#fff3b8", "#ffb6d0"];
let levelUpTimer = null;

function levelUpFx(level, unlocksJson) {
  if (typeof dialogOpen !== "undefined" && dialogOpen) closeDialog();   // e.g. a secret code in Settings: let the celebration be seen
  const unlocks = JSON.parse(unlocksJson);
  document.getElementById("levelup-number").textContent = level;
  const list = document.getElementById("levelup-unlocks");
  list.replaceChildren();
  (unlocks.length ? unlocks : ["Nyra feels stronger!"]).forEach(text => {
    const chip = document.createElement("span");
    chip.className = "levelup-chip";
    chip.textContent = `✦ ${text}`;
    list.appendChild(chip);
  });
  levelUpLayer.hidden = false;
  levelUpLayer.style.opacity = "1";
  const calm = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (!calm) {
    play(levelUpCard, [
      { transform: "translate(-50%, -50%) scale(.4) rotate(-6deg)", opacity: 0 },
      { transform: "translate(-50%, -50%) scale(1.12) rotate(2deg)", opacity: 1, offset: .55 },
      { transform: "translate(-50%, -50%) scale(1) rotate(0deg)", opacity: 1 },
    ], 650, "cubic-bezier(.2, .8, .3, 1)");
    burstSparkles();
  }
  window.clearTimeout(levelUpTimer);
  levelUpTimer = window.setTimeout(hideLevelUp, 4500);
}

function burstSparkles() {
  const box = document.getElementById("levelup-particles");
  box.replaceChildren();
  const glyphs = ["✦", "✧", "❀", "•", "✿"];
  for (let i = 0; i < 40; i++) {
    const spark = document.createElement("span");
    spark.className = "levelup-spark";
    spark.textContent = glyphs[i % glyphs.length];
    spark.style.color = levelUpColours[i % levelUpColours.length];
    spark.style.fontSize = `${18 + Math.random() * 26}px`;
    box.appendChild(spark);
    const angle = Math.random() * Math.PI * 2;
    const distance = 120 + Math.random() * 260;
    const x = Math.cos(angle) * distance, y = Math.sin(angle) * distance * 0.8;
    play(spark, [
      { transform: "translate(-50%, -50%) scale(.2) rotate(0deg)", opacity: 1 },
      { transform: `translate(calc(-50% + ${x}px), calc(-50% + ${y}px)) scale(1) rotate(${Math.random() * 240 - 120}deg)`, opacity: 1, offset: .55 },
      { transform: `translate(calc(-50% + ${x * 1.15}px), calc(-50% + ${y + 90}px)) scale(.6) rotate(${Math.random() * 360 - 180}deg)`, opacity: 0 },
    ], 1500 + Math.random() * 900, "cubic-bezier(.15, .7, .3, 1)");
  }
}

function hideLevelUp() {
  if (levelUpLayer.hidden) return;
  window.clearTimeout(levelUpTimer);
  play(levelUpLayer, [{ opacity: 1 }, { opacity: 0 }], 350, "ease-in");
  window.setTimeout(() => { levelUpLayer.hidden = true; document.getElementById("levelup-particles").replaceChildren(); }, 340);
}

levelUpCard.addEventListener("click", hideLevelUp);


/* =========================================================================
   SECTION 19 - Sound
   The sound files are in assets/sounds. SOUND_FILES says which file each sound uses; Python asks
   for effects with playSound("name") at the right moments. Add a line to SOUND_FILES to give a
   sound a file (a name with no file is just silent). Music and effects have their own volume
   (set in the Settings window, see SECTION 20) and a mute switch (also the M key).
   ========================================================================= */
const SOUND_FOLDER = "assets/sounds/";
const SOUND_FILES = {
  click:      "Sound effects/vilkas_sound_button-click.mp3",   // any button is pressed
  hover:      "Sound effects/vilkas_sound__pop.mp3",           // the mouse moves onto a button
  transition: "Sound effects/_kwahmah_02_swoosh.wav",          // changing screen, opening a window
  dialogue:   "Sound effects/marevnik__ui_pop_up.mp3",         // Nyra's dialogue box pops up
  levelup:    "Sound effects/qubodup__level-up.wav",           // a new level
  brew:       "Sound effects/odzta1__cauldronbubbling.wav",    // brewing a potion
  cauldron:   "Sound effects/odzta1__cauldronbubbling.wav",    // bubbling while the Cauldron window is open
  plant:      "Sound effects/wobesound__planting-sounds.wav",  // planting a seed (5 little sounds in one file: see SOUNDS.plant)
  harvest:    "Sound effects/f4ngy__picking-flower.wav",       // picking a plant
  coin:       "Sound effects/beezlefm__coins-medium-sound.wav",// buying or selling in the Shop
  egg_glitch: "Sound effects/error-glitch.mp3",                // the easter egg: Nyra's message is cut off (1.3 seconds)
  // Python also asks for: remove, undo, page, discover, morning, night, nyra, nyra_blush.
  // They stay silent until you add a line here, for example:   undo: "Sound effects/my_undo_sound.mp3",
};
const SOUNDS = {                                   // per sound: volume 0..1 (balanced by measuring the files), spacing = least ms between two plays,
                                                   // maxMs = cut it short, clips = play one random piece of the file: [start second, length in seconds]
  click: { volume: 0.4 }, hover: { volume: 0.28, spacing: 70 }, transition: { volume: 0.85 },
  dialogue: { volume: 0.35, spacing: 120 }, levelup: { volume: 0.75 }, brew: { volume: 0.7, maxMs: 3200 },
  coin: { volume: 0.7 }, harvest: { volume: 0.6 }, egg_glitch: { volume: 0.6 },
  plant: { volume: 1, clips: [[0, 0.72], [1, 0.72], [2, 0.72], [3, 0.72], [4, 0.77]] },   // wobesound's file holds 5 planting sounds, one per second
};
const AMBIENCE_FILES = {                           // the loop for each look of the garden
  day: "Sound effects/gammagool__birds-in-the-slovenian-forest.wav",      // sunny, cloudy and cold days
  night: "Sound effects/ioan003-distant-owls.mp3", starry: "Sound effects/ioan003-distant-owls.mp3",
  rain: "Sound effects/r0t0r-rain.mp3",
};
const LOOP_GAIN = { ambience: 1, cauldron: 0.3 };  // how loud each background loop is, compared with the effects volume (the birds, rain and owl recordings are all quiet)
const LOOP_CROSSFADE_SECONDS = 1.5;                // a loop fades into its own start, so short recordings repeat without a click

const MUSIC_MAIN = "BG Music/Remembering Something I Forgot.mp3";     // the main theme: loops on the home screen
const MUSIC_PLAYLIST = [MUSIC_MAIN, "BG Music/Coffee Jelly.mp3", "BG Music/Turtle Sandbox.mp3"];   // played in turn in the garden
const CROSSFADE_SECONDS = 4;                       // the next song fades in this long before the current one ends
const MUSIC_MAX_VOLUME = 0.6;                      // the music slider at 100% means this volume

/* ---- the player's volumes (kept in the browser, so they are remembered) ---- */
const audioSettings = { music: 0.5, effects: 0.8, muted: false };
try {
  const saved = JSON.parse(window.localStorage.getItem("catnip-audio") || "{}");
  ["music", "effects"].forEach(key => { if (typeof saved[key] === "number") audioSettings[key] = Math.min(1, Math.max(0, saved[key])); });
  audioSettings.muted = saved.muted === true;
} catch (error) { /* private browsing or no saved settings: keep the defaults */ }

function saveAudioSettings() {
  try { window.localStorage.setItem("catnip-audio", JSON.stringify(audioSettings)); } catch (error) { /* ignore */ }
}
const musicLevel = () => (audioSettings.muted ? 0 : audioSettings.music * MUSIC_MAX_VOLUME);
const effectLevel = () => (audioSettings.muted ? 0 : audioSettings.effects);

/* ---- playing files ---- */
const soundMissing = new Set();                    // files that could not be loaded: skipped from then on
const soundBase = new Map();                       // file -> the loaded Audio; copied for each play so effects can overlap
const lastPlayed = {};
const soundUrl = file => encodeURI(SOUND_FOLDER + file);

function fadeVolume(audio, target, milliseconds, then) {
  if (audio._fade) window.clearInterval(audio._fade);
  const steps = Math.max(1, Math.round(milliseconds / 50));
  const change = (target - audio.volume) / steps;
  let count = 0;
  audio._fade = window.setInterval(() => {
    count += 1;
    audio.volume = Math.min(1, Math.max(0, audio.volume + change));
    if (count >= steps) {
      window.clearInterval(audio._fade);
      audio._fade = null;
      audio.volume = Math.min(1, Math.max(0, target));
      if (then) then();
    }
  }, 50);
}

function playSound(name) {
  const file = SOUND_FILES[name];
  if (!file || soundMissing.has(file)) return;
  const level = effectLevel();
  if (level <= 0) return;
  const config = SOUNDS[name] || {};
  const now = performance.now();
  if (config.spacing && now - (lastPlayed[name] ?? -1e9) < config.spacing) return;
  lastPlayed[name] = now;
  let source = soundBase.get(file);
  let copy;
  if (!source) {
    source = new Audio(soundUrl(file));
    source.addEventListener("error", () => soundMissing.add(file), { once: true });
    soundBase.set(file, source);
    copy = source;
  } else {
    copy = source.cloneNode();
  }
  copy.volume = Math.min(1, (config.volume ?? 0.7) * level);
  let stopAfter = config.maxMs || 0;
  if (config.clips) {                                            // one random piece of the file, never the same twice in a row
    const options = config.clips.filter((_clip, index) => index !== config.lastClip);
    const index = config.clips.indexOf(options[Math.floor(Math.random() * options.length)]);
    config.lastClip = index;
    const [start, length] = config.clips[index];
    const seek = () => { try { copy.currentTime = start; } catch (error) { /* the browser will start from 0 */ } };
    if (copy.readyState >= 1) seek(); else copy.addEventListener("loadedmetadata", seek, { once: true });
    stopAfter = length * 1000;
  }
  copy.play().catch(() => {});
  if (stopAfter) window.setTimeout(() => fadeVolume(copy, 0, config.clips ? 60 : 300, () => copy.pause()), stopAfter);
}

/* ---- background loops: the cauldron bubbling (and later, weather ambience) ---- */
const loopSlots = { ambience: { audio: null, file: null }, cauldron: { audio: null, file: null } };
const loopLevel = kind => effectLevel() * LOOP_GAIN[kind];

/* One background loop. Each layer plays the file once; near its end the next layer starts and fades in
   while this one fades out, so even a recording with an abrupt end repeats smoothly. */
function startLoopLayer(kind, file) {
  const slot = loopSlots[kind];
  const audio = new Audio(soundUrl(file));
  audio.loop = false;
  audio.volume = 0;
  const handOver = () => {
    if (audio._handedOver || slot.audio !== audio) return;
    audio._handedOver = true;
    startLoopLayer(kind, file);
    fadeVolume(audio, 0, LOOP_CROSSFADE_SECONDS * 1000, () => audio.pause());
  };
  audio.addEventListener("error", () => { soundMissing.add(file); if (slot.audio === audio) { slot.audio = null; slot.file = null; } }, { once: true });
  audio.addEventListener("timeupdate", () => { if (audio.duration && audio.duration - audio.currentTime < LOOP_CROSSFADE_SECONDS) handOver(); });
  audio.addEventListener("ended", handOver);
  slot.audio = audio;
  slot.file = file;
  audio.play().then(() => fadeVolume(audio, loopLevel(kind), LOOP_CROSSFADE_SECONDS * 1000))
    .catch(() => { if (slot.audio === audio) { slot.audio = null; slot.file = null; } });     // blocked until the first click: tried again then
}

function setLoop(kind, file) {
  const slot = loopSlots[kind];
  const wanted = effectLevel() > 0 ? (file || null) : null;
  if (slot.file === wanted && (!wanted || slot.audio)) return;
  const old = slot.audio;
  if (old) { old._handedOver = true; fadeVolume(old, 0, 700, () => old.pause()); }
  slot.audio = null;
  slot.file = null;
  if (!wanted || soundMissing.has(wanted)) return;
  startLoopLayer(kind, wanted);
}

/* ---- music: the main theme loops on the home screen; in the garden the songs take turns ---- */
const music = { audio: null, file: null };

function musicTitle() {
  return music.file ? music.file.replace(/^.*\//, "").replace(/\.[^.]+$/, "") : "";
}

function playMusic(file, loop) {
  const old = music.audio;
  if (old && music.file === file) { old.loop = loop; return; }       // already playing this song: only change whether it repeats
  if (old) fadeVolume(old, 0, CROSSFADE_SECONDS * 250, () => old.pause());
  music.audio = null;
  music.file = null;
  if (!file || audioSettings.muted || soundMissing.has(file)) { syncSettingsUi(); return; }
  const audio = new Audio(soundUrl(file));
  audio.loop = loop;
  audio.volume = 0;
  audio.addEventListener("error", () => { soundMissing.add(file); if (music.audio === audio) { music.audio = null; music.file = null; syncSettingsUi(); } }, { once: true });
  audio.addEventListener("timeupdate", () => {                       // near the end: start the next song so they overlap
    if (!audio.loop && music.audio === audio && audio.duration && audio.duration - audio.currentTime < CROSSFADE_SECONDS) nextSong(audio);
  });
  audio.addEventListener("ended", () => { if (!audio.loop && music.audio === audio) nextSong(audio); });
  music.audio = audio;
  music.file = file;
  audio.play().then(() => fadeVolume(audio, musicLevel(), 1500))
    .catch(() => { if (music.audio === audio) { music.audio = null; music.file = null; } });
  syncSettingsUi();
}

function nextSong(current) {
  if (music.audio !== current) return;
  const index = MUSIC_PLAYLIST.indexOf(music.file);
  playMusic(MUSIC_PLAYLIST[(index + 1) % MUSIC_PLAYLIST.length], false);
}

function refreshMusic() {
  if (audioSettings.muted) return;
  if (soundState.screen === "menu") {
    playMusic(MUSIC_MAIN, true);
  } else if (music.audio && MUSIC_PLAYLIST.includes(music.file)) {
    music.audio.loop = false;                                        // keep the current song; the playlist takes over when it ends
  } else {
    playMusic(MUSIC_PLAYLIST[0], false);
  }
}

/* ---- keeping everything in step with the screen, the weather picture and the Cauldron window ---- */
const soundState = { screen: "menu", scene: "day", cauldron: false, egg: false };

function refreshSound() {
  if (soundState.egg) {                            // the easter egg is running: the garden goes silent
    playMusic(null, false);
    setLoop("ambience", null);
    setLoop("cauldron", null);
    return;
  }
  refreshMusic();
  setLoop("ambience", soundState.screen === "garden" ? AMBIENCE_FILES[soundState.scene] : null);
  setLoop("cauldron", soundState.screen === "garden" && soundState.cauldron ? SOUND_FILES.cauldron : null);
}
function soundForScreen(screenName) { soundState.screen = screenName; refreshSound(); }
function soundForScene(scene) { soundState.scene = scene; refreshSound(); }
function soundForCauldron(open) { soundState.cauldron = open; refreshSound(); }
function soundForEgg(on) { soundState.egg = on; refreshSound(); }

function applyVolumes() {
  if (music.audio) { if (music.audio._fade) { window.clearInterval(music.audio._fade); music.audio._fade = null; } music.audio.volume = musicLevel(); }
  Object.entries(loopSlots).forEach(([kind, slot]) => {
    if (slot.audio) { if (slot.audio._fade) { window.clearInterval(slot.audio._fade); slot.audio._fade = null; } slot.audio.volume = loopLevel(kind); }
  });
}

function setMusicVolume(value) {
  audioSettings.music = Math.min(1, Math.max(0, value));
  saveAudioSettings();
  applyVolumes();
}
function setEffectsVolume(value) {
  audioSettings.effects = Math.min(1, Math.max(0, value));
  saveAudioSettings();
  refreshSound();
  applyVolumes();
}

function setSoundEnabled(on) {
  audioSettings.muted = !on;
  saveAudioSettings();
  if (audioSettings.muted) {
    if (music.audio) { const old = music.audio; fadeVolume(old, 0, 300, () => old.pause()); }
    music.audio = null;
    music.file = null;
    refreshSound();
  } else {
    refreshSound();
  }
  syncSettingsUi();
}

// Browsers only allow sound after the first click or key press, so try again then.
["pointerdown", "keydown"].forEach(type => document.addEventListener(type, () => refreshSound(), { once: true }));

// A pop when the mouse moves onto a button (not the garden plots, which would pop all the time), a click when it is pressed.
let hoveredButton = null;
document.addEventListener("pointerover", event => {
  if (event.pointerType !== "mouse") return;
  const button = event.target.closest ? event.target.closest("button:not(.plot), .icon-button, [role='button']") : null;
  if (button === hoveredButton) return;
  hoveredButton = button;
  if (button && !button.disabled) playSound("hover");
});
document.addEventListener("click", event => {
  if (event.target.closest && event.target.closest("button, .icon-button, [role='button']")) playSound("click");
});

// "M" mutes or unmutes everything.
document.addEventListener("keydown", event => {
  if ((event.key === "m" || event.key === "M") && !event.ctrlKey && !event.metaKey && !event.altKey
      && !/^(INPUT|SELECT|TEXTAREA)$/.test(document.activeElement ? document.activeElement.tagName : "")) {
    setSoundEnabled(audioSettings.muted);
    setMessage(audioSettings.muted ? "Sound off. Press M to turn it back on." : "Sound on.");
  }
});


/* =========================================================================
   SECTION 20 - Settings and Credits windows
   One window layer for both. Settings has the Music and Sound effects sliders and the mute
   switch; Credits lists who made the music and sounds (it reads assets/sounds/credits.json,
   which is the file to edit when you add or change sounds).
   ========================================================================= */
const dialogLayer = document.getElementById("dialog-layer");
const settingsPanel = document.getElementById("settings-panel");
const creditsPanel = document.getElementById("credits-panel");
const musicSlider = document.getElementById("music-volume");
const effectsSlider = document.getElementById("effects-volume");
const muteBox = document.getElementById("sound-mute");
let dialogOpen = null;            // null, "settings" or "credits"
let dialogReturnFocus = null;
let creditsLoaded = false;

function syncSettingsUi() {
  if (!musicSlider) return;
  musicSlider.value = Math.round(audioSettings.music * 100);
  effectsSlider.value = Math.round(audioSettings.effects * 100);
  document.getElementById("music-volume-out").textContent = `${musicSlider.value}%`;
  document.getElementById("effects-volume-out").textContent = `${effectsSlider.value}%`;
  muteBox.checked = audioSettings.muted;
  const title = musicTitle();
  document.getElementById("now-playing").textContent = audioSettings.muted ? "(sound is off)" : (title ? `♪ ${title}` : "—");
}

function openDialog(which) {
  if (dialogOpen === which) return;
  const wasClosed = dialogOpen === null;
  dialogOpen = which;
  dialogLayer.hidden = false;
  settingsPanel.hidden = which !== "settings";
  creditsPanel.hidden = which !== "credits";
  const panel = which === "settings" ? settingsPanel : creditsPanel;
  if (wasClosed) {
    dialogReturnFocus = document.activeElement;
    playSound("transition");
    play(panel, [{ transform: "translate(-50%, -46%) scale(.96)", opacity: 0 }, { transform: "translate(-50%, -50%) scale(1)", opacity: 1 }], 240, "ease-out");
  }
  if (which === "credits") loadCredits();
  syncSettingsUi();
  panel.querySelector(".inv-close").focus({ preventScroll: true });
}

function closeDialog() {
  if (!dialogOpen) return;
  dialogOpen = null;
  dialogLayer.hidden = true;
  if (dialogReturnFocus && dialogReturnFocus.focus) dialogReturnFocus.focus({ preventScroll: true });
}

function creditLine(text, className) {
  const line = document.createElement("p");
  line.className = className;
  line.textContent = text;
  return line;
}

function creditHeading(text) {
  return Object.assign(document.createElement("h3"), { className: "credit-heading", textContent: text });
}

async function loadCredits() {
  if (creditsLoaded) return;
  const list = document.getElementById("credits-list");
  try {
    const response = await fetch(`${SOUND_FOLDER}credits.json`);
    const data = await response.json();
    list.replaceChildren();

    const music = data.music || {};                          // one artist, several songs
    list.appendChild(creditHeading("Music"));
    const card = document.createElement("div");
    card.className = "credit-card";
    const artist = document.createElement("strong");
    artist.textContent = music.author || "";
    card.appendChild(artist);
    (music.tracks || []).forEach(title => card.appendChild(creditLine(`♪ ${title}`, "credit-line")));
    ["source", "license"].forEach(key => { if (music[key]) card.appendChild(creditLine(`${key === "source" ? "Source" : "License"}: ${music[key]}`, "credit-line small")); });
    if (/^https?:\/\//.test(music.url || "")) {
      const link = document.createElement("a");
      link.href = music.url;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      link.textContent = music.url;
      const line = creditLine("", "credit-line small");
      line.appendChild(link);
      card.appendChild(line);
    }
    list.appendChild(card);

    list.appendChild(creditHeading("Sound effects"));          // only the creators' usernames, to keep it clean
    const chips = document.createElement("div");
    chips.className = "credit-chips";
    (data.effects || []).forEach(name => chips.appendChild(Object.assign(document.createElement("span"), { className: "credit-chip", textContent: name })));
    list.appendChild(chips);
    creditsLoaded = true;
  } catch (error) {
    list.replaceChildren(creditLine("The credits could not be loaded (assets/sounds/credits.json).", "credit-line"));
  }
}

/* Secret codes: the text box in Settings. Python looks the code up (a hash table) and answers through showCodeResult. */
const secretInput = document.getElementById("secret-code");
const secretResult = document.getElementById("secret-result");

function showCodeResult(text, worked) {
  secretResult.textContent = text;
  secretResult.classList.toggle("worked", Boolean(worked));
  secretResult.classList.toggle("failed", !worked);
  if (!worked) {                                   // a little shake for a code that did nothing
    secretInput.classList.remove("shake");
    void secretInput.offsetWidth;
    secretInput.classList.add("shake");
  }
}

function sendSecretCode() {
  askPython("apply_secret_code", secretInput.value);
  secretInput.value = "";
  secretInput.focus({ preventScroll: true });
}
document.getElementById("secret-go").addEventListener("click", sendSecretCode);
secretInput.addEventListener("keydown", event => { if (event.key === "Enter") sendSecretCode(); });

function trapDialogFocus(event) {
  if (event.key !== "Tab" || !dialogOpen) return;
  const panel = dialogOpen === "settings" ? settingsPanel : creditsPanel;
  const focusable = Array.from(panel.querySelectorAll("button:not(:disabled), input, a[href]"));
  if (!focusable.length) return;
  const first = focusable[0], last = focusable[focusable.length - 1];
  if (!panel.contains(document.activeElement)) { event.preventDefault(); first.focus(); }
  else if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
  else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
}

musicSlider.addEventListener("input", () => { setMusicVolume(Number(musicSlider.value) / 100); syncSettingsUi(); });
effectsSlider.addEventListener("input", () => { setEffectsVolume(Number(effectsSlider.value) / 100); syncSettingsUi(); });
effectsSlider.addEventListener("change", () => playSound("dialogue"));      // a little preview at the new loudness
muteBox.addEventListener("change", () => setSoundEnabled(!muteBox.checked));
document.getElementById("settings-close").addEventListener("click", closeDialog);
document.getElementById("credits-close").addEventListener("click", closeDialog);
document.getElementById("dialog-scrim").addEventListener("click", closeDialog);
document.getElementById("open-credits").addEventListener("click", () => openDialog("credits"));
document.getElementById("credits-back").addEventListener("click", () => openDialog("settings"));
document.addEventListener("keydown", trapDialogFocus);
syncSettingsUi();
refreshSound();


/* =========================================================================
   SECTION 21 - The hidden easter egg
   Python decides when it starts (the secret word in Settings) and what Nyra says; this runs the
   sequence: Settings closes, the garden gets darker while Nyra senses something is off, her message
   is cut off, pure black, and the rhythm game (assets/easter_egg, shown in a frame) begins.
   The game tells us "win" or "lose" when it ends. Either way we return to the home screen as if
   nothing happened; after a win Nyra is glad to see the player again.
   ========================================================================= */
const eggLayer = document.getElementById("egg-layer");
const eggFrame = document.getElementById("egg-frame");
const eggVeil = document.getElementById("egg-veil");
const eggNyra = document.getElementById("egg-nyra");
const eggNyraSprite = document.getElementById("egg-nyra-sprite");
const eggDialogue = document.getElementById("egg-dialogue");
const eggDialogueText = document.getElementById("egg-dialogue-text");
const appRoot = document.getElementById("app");
const gardenVeil = document.getElementById("garden-veil");
let eggRunning = false;
let eggStage = "idle";                 // idle | intro | fight | done
let eggReady = false;                  // the fight has loaded and is waiting on black
let eggWelcomeLines = null;            // set by Python after a win

const EGG_GLITCH_MS = 1300;            // how long the glitch lasts: the length of error-glitch.mp3 (1.33 s)
const eggSleep = ms => new Promise(resolve => window.setTimeout(resolve, ms));
const eggCalm = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;

/* Wait for ms, but a click or Enter/Space (after minMs) moves on sooner. */
function eggWait(ms, minMs = 900) {
  return new Promise(resolve => {
    const started = performance.now();
    let finished = false;
    const finish = () => {
      if (finished) return;
      finished = true;
      window.clearTimeout(timer);
      eggLayer.removeEventListener("click", skip);
      document.removeEventListener("keydown", skipKey);
      resolve();
    };
    const skip = () => { if (performance.now() - started >= minMs) finish(); };
    const skipKey = event => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); skip(); } };
    const timer = window.setTimeout(finish, ms);
    eggLayer.addEventListener("click", skip);
    document.addEventListener("keydown", skipKey);
  });
}

function eggUntil(condition, timeoutMs) {
  return new Promise(resolve => {
    const started = performance.now();
    const check = () => { if (condition() || performance.now() - started > timeoutMs) resolve(); else window.setTimeout(check, 100); };
    check();
  });
}

/* Set an element's opacity, fading there over ms (0 = at once). */
function eggOpacity(element, to, ms) {
  const from = parseFloat(window.getComputedStyle(element).opacity);
  element.style.opacity = String(to);
  if (ms <= 0 || eggCalm() || from === to) return Promise.resolve();
  return element.animate([{ opacity: from }, { opacity: to }], { duration: ms, easing: "ease-in-out" }).finished.catch(() => {});
}

function eggVolumes() {                // the player's Settings, translated for the fight (50% music and 80% effects = the fight's own full volume)
  if (audioSettings.muted) return { mv: 0, sv: 0 };
  return { mv: Math.min(1, audioSettings.music / 0.5), sv: Math.min(1, audioSettings.effects / 0.8) };
}

function eggUrl() {
  const { mv, sv } = eggVolumes();
  return `assets/easter_egg/index.html?embed=1&mv=${mv.toFixed(2)}&sv=${sv.toFixed(2)}`;
}

/* Nyra speaks one line: [text, face, mouth]. In the garden she uses the garden's own Nyra and dialogue box
   (same place, same talking); on the home screen (no Nyra there) the overlay Nyra and box are used. */
function showEggLine(line, inGarden = false) {
  const [text, face, mouth] = line;
  if (inGarden) {
    eggNyra.hidden = true;
    showDialogue(text, face, mouth);                 // plays the dialogue pop itself
    return;
  }
  eggNyraSprite.src = NYRA_ASSETS[face][mouth];
  eggDialogueText.textContent = text;
  eggNyra.hidden = false;
  eggLayer.classList.remove("egg-glitch");
  eggDialogue.style.animation = "none";
  void eggDialogue.offsetWidth;                      // restart the little pop-in
  eggDialogue.style.animation = "";
  playSound("dialogue");
}

function eggGlitchOn(on, inGarden) {                 // the picture shakes: the garden's own Nyra, or the overlay one
  (inGarden ? gardenScreen : eggLayer).classList.toggle("egg-glitch", on);
}

function startEasterEgg(linesJson) {                 // called by Python when the secret word was typed
  if (eggRunning) return;
  eggRunning = true;
  eggStage = "intro";
  runEasterEgg(JSON.parse(linesJson)).catch(error => { console.error("Easter egg:", error); endEasterEgg(); });
}

async function runEasterEgg(lines) {
  // Settings closes by itself; the box is tidied so nothing gives the secret away
  closeDialog();
  secretInput.value = "";
  secretResult.textContent = "";
  appRoot.inert = true;                              // nothing underneath can be clicked or tabbed to
  eggLayer.hidden = false;
  eggVeil.style.opacity = "0";
  eggNyra.hidden = true;
  soundForEgg(true);                                 // music and ambience fade out
  eggReady = false;
  eggFrame.classList.remove("show");
  eggFrame.src = eggUrl();                           // the fight loads in the background while the screen darkens
  await eggWait(600, 600);

  // In the garden the dark is the garden's own veil (under Nyra) and she talks in her usual box;
  // on the home screen it is the overlay veil with the overlay Nyra.
  const inGarden = !screens.garden.hidden;
  const softVeil = inGarden ? gardenVeil : eggVeil;

  eggOpacity(softVeil, 0.5, 2400);                   // the screen slowly darkens...
  showEggLine(lines.intro, inGarden);                // ...while Nyra feels that something is off
  await eggWait(4200);

  if (!eggCalm()) {                                  // the lights flicker
    for (let i = 0; i < 3; i += 1) {
      await eggOpacity(softVeil, 0.9, 60);
      await eggOpacity(softVeil, 0.45, 110);
    }
  }
  showEggLine(lines.cutoff, inGarden);               // she tries to call out: the message is cut off
  await eggWait(3000, 1300);

  eggGlitchOn(true, inGarden);                       // the message is cut off: an error glitch (picture and sound), then pure black
  playSound("egg_glitch");
  const glitchEnds = performance.now() + EGG_GLITCH_MS;
  while (performance.now() < glitchEnds) {
    if (!eggCalm()) softVeil.style.opacity = String(0.5 + Math.random() * 0.45);      // the dark flickers
    await eggSleep(50 + Math.random() * 80);
  }
  eggNyra.hidden = true;
  if (inGarden) hideDialogue();
  eggGlitchOn(false, inGarden);
  await eggOpacity(eggVeil, 1, 0);
  gardenVeil.style.opacity = "0";
  await eggSleep(1700);                              // a moment of silence in the dark

  await eggUntil(() => eggReady, 9000);              // the fight is loaded
  eggStage = "fight";
  eggFrame.classList.add("show");
  eggFrame.contentWindow.postMessage({ type: "egg-go" }, window.location.origin);
  eggFrame.contentWindow.focus();
  await eggOpacity(eggVeil, 0, 1000);                // the fight fades in and starts
}

window.addEventListener("message", event => {        // the fight talks to us: it is ready, or it is over
  if (event.origin !== window.location.origin || event.source !== eggFrame.contentWindow) return;
  const data = event.data || {};
  if (data.type === "egg-ready") eggReady = true;
  else if (data.type === "egg-result" && eggRunning && eggStage === "fight") finishEasterEgg(data.result === "win" ? "win" : "lose");
});

async function finishEasterEgg(result) {
  eggStage = "done";
  await eggOpacity(eggVeil, 1, 900);                 // fade to black
  eggFrame.classList.remove("show");
  eggFrame.src = "about:blank";                      // the fight (and its music) stops
  setDrawerOpen(false);
  setExtrasOpen(false);
  showScreen("menu");                                // home screen, as if nothing happened
  eggWelcomeLines = null;
  askPython("egg_result", result);                   // after a win, Python answers with showEggWelcome(...)
  await eggSleep(400);
  soundForEgg(false);                                // the home screen music comes back
  await eggOpacity(eggVeil, 0, 1200);
  if (eggWelcomeLines) await playEggWelcome();
  endEasterEgg();
}

function showEggWelcome(linesJson) {                 // called by Python after a win
  eggWelcomeLines = JSON.parse(linesJson);
}

async function playEggWelcome() {                    // Nyra is glad the player is back (click to go on)
  for (const line of eggWelcomeLines) {
    showEggLine(line);
    await eggWait(6500, 700);
  }
  eggNyra.hidden = true;
  eggWelcomeLines = null;
}

function endEasterEgg() {                            // everything back to normal
  eggFrame.classList.remove("show");
  eggFrame.src = "about:blank";
  eggNyra.hidden = true;
  eggLayer.classList.remove("egg-glitch");
  gardenScreen.classList.remove("egg-glitch");
  gardenVeil.style.opacity = "0";
  eggLayer.hidden = true;
  eggVeil.style.opacity = "0";
  appRoot.inert = false;
  soundForEgg(false);
  eggRunning = false;
  eggStage = "idle";
  const play = document.getElementById("play-button");
  if (play && !screens.menu.hidden) play.focus({ preventScroll: true });
}

eggDialogue.addEventListener("keydown", event => { if (event.key === "Enter" || event.key === " ") event.preventDefault(); });
