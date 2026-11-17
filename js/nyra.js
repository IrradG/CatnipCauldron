/* Nyra's expression and blinking system.
   IMPORTANT: the paths below use your original filenames. Keep those files in assets/nyra/.
   If your files are stored in a different folder, update NYRA_ASSETS here. */
const NYRA_ASSETS = {
  passive: {
    closed: "assets/nyra/Nyra_Passive(1).png",
    open: "assets/nyra/Nyra_Passive(2).png",
    blush: "assets/nyra/Nyra_Passive(3).png",
    blink: "assets/nyra/Nyra_Passive(Blink).png"
  },
  happy: {
    closed: "assets/nyra/Nyra_Happy(1).png",
    open: "assets/nyra/Nyra_Happy(2).png",
    blush: "assets/nyra/Nyra_Happy(3).png",
    blink: "assets/nyra/Nyra_Happy(Blink).png"
  },
  blush: {
    closed: "assets/nyra/Nyra_Blush(1).png",
    open: "assets/nyra/Nyra_Blush(2).png",
    blush: "assets/nyra/Nyra_Blush(3).png",
    blink: "assets/nyra/Nyra_Blush(Blink).png"
  }
};

let nyraExpression = "passive";
let nyraMouth = "closed";
let nyraBlinkTimer = null;
let nyraIsBlinking = false;
let nyraDialogueActive = false;
let nyraImageElement = null;

function getNyraSpritePath() {
  const set = NYRA_ASSETS[nyraExpression] || NYRA_ASSETS.passive;
  if (nyraIsBlinking) return set.blink;
  return set[nyraMouth] || set.closed;
}

function renderNyra() {
  if (!nyraImageElement) return;
  nyraImageElement.src = getNyraSpritePath();
  nyraImageElement.onerror = () => {
    nyraImageElement.alt = "Nyra's sprite could not load. Check the filename and assets/nyra folder.";
    console.warn("Could not load Nyra sprite:", nyraImageElement.src);
  };
}

function setNyraExpression(expression, mouth = "closed", dialogueActive = false) {
  if (!NYRA_ASSETS[expression]) expression = "passive";
  if (!["closed", "open", "blush"].includes(mouth)) mouth = "closed";
  nyraExpression = expression;
  nyraMouth = mouth;
  nyraDialogueActive = dialogueActive;
  nyraIsBlinking = false;
  window.clearTimeout(nyraBlinkTimer);
  renderNyra();
  if (!nyraDialogueActive) scheduleNyraBlink();
}

function scheduleNyraBlink() {
  window.clearTimeout(nyraBlinkTimer);
  if (nyraDialogueActive) return;
  // Random pause between blinks: 3.5 to 7 seconds.
  const delay = 3500 + Math.random() * 3500;
  nyraBlinkTimer = window.setTimeout(() => {
    nyraIsBlinking = true;
    renderNyra();
    // Briefly show closed eyes, then restore her current expression.
    window.setTimeout(() => {
      nyraIsBlinking = false;
      renderNyra();
      scheduleNyraBlink();
    }, 160);
  }, delay);
}

function initNyra() {
  nyraImageElement = document.getElementById("nyra-sprite");
  if (!nyraImageElement) return;
  renderNyra();
  scheduleNyraBlink();
}

document.addEventListener("DOMContentLoaded", initNyra);
