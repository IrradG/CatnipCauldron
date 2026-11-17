CatnipCauldron sounds
=====================
Your files stay exactly where and how they are named. js/main.js (SECTION 19) says which file each
sound uses, in the SOUND_FILES table at the top of that section:

  click        Sound effects/vilkas_sound_button-click.mp3     any button is pressed
  hover        Sound effects/vilkas_sound__pop.mp3             the mouse moves onto a button
  transition   Sound effects/_kwahmah_02_swoosh.wav            changing screen, opening a window
  dialogue     Sound effects/marevnik__ui_pop_up.mp3           Nyra's dialogue box pops up
  levelup      Sound effects/qubodup__level-up.wav             a new level
  brew         Sound effects/odzta1__cauldronbubbling.wav      brewing a potion (cut after ~3 seconds)
  cauldron     Sound effects/odzta1__cauldronbubbling.wav      bubbling while the Cauldron window is open
  plant        Sound effects/wobesound__planting-sounds.wav    planting a seed (see below)
  harvest      Sound effects/f4ngy__picking-flower.wav         picking a plant
  coin         Sound effects/beezlefm__coins-medium-sound.wav  buying or selling in the Shop
  egg_glitch   Sound effects/error-glitch.mp3                     the hidden easter egg: Nyra's message is cut off (1.3 s)

The garden's background loops (AMBIENCE_FILES), which only play in the garden:
  rain             Sound effects/r0t0r-rain.mp3              any rainy day or night
  night / starry   Sound effects/ioan003-distant-owls.mp3    nights without rain
  day              Sound effects/gammagool__birds-in-the-slovenian-forest.wav   sunny, cloudy and cold days (63 s)
The loops fade into their own start (LOOP_CROSSFADE_SECONDS), so they repeat without a click even though
the rain and owls are only 10 seconds long.

The planting file holds 5 little planting sounds, one every second. SOUNDS.plant lists them as clips
([start second, length]) and the game plays one random clip each time, never the same one twice in a row.

Music (MUSIC_MAIN and MUSIC_PLAYLIST in the same section):
  BG Music/Remembering Something I Forgot.mp3    the main theme: loops on the home screen
  then, in the garden and Shop, the songs take turns with a crossfade:
  Remembering Something I Forgot -> Coffee Jelly -> Turtle Sandbox -> (back to the start)

Adding more sounds
------------------
Python already asks for these effects, but they have no file yet, so they are silent:
  remove, undo, page, discover, morning, night, nyra, nyra_blush
To give one a sound, copy your file into "Sound effects" and add one line to SOUND_FILES, for example:
  undo: "Sound effects/my_undo_sound.mp3",
To add a song to the garden rotation, add its path to MUSIC_PLAYLIST.

Volumes
-------
Players change Music and Sound effects separately in Settings (also the M key mutes everything).
Per-sound loudness is in the SOUNDS table (already balanced by measuring the files, so the click is not
quieter than the pop-up). The birds, rain and owl recordings are quite quiet by themselves: if you want them
louder, raise LOOP_GAIN or make the files louder in an audio editor.

Credits
-------
credits.json is shown in the game's Credits window (Settings -> Credits, or Credits on the home screen):
  music    the artist (Purrple Cat), the song titles, and optionally source / url / license
  effects  just the usernames of the sound effect creators, one per file
Add a username there whenever you add a sound from someone new.
