# Stretchy Head

A Super Mario 64-style interactive 3D head for a web page: grab the face, it stretches, let go and it springs back. Small pulls hold as poses; big pulls snap everything back. The head follows the pointer with its eyes, reacts when it is yanked too hard, dances when ignored and falls asleep when left alone.

One `index.html`, no frameworks, no build step, no server. Runs in any modern browser, phones included.

This repository is a **template**. It ships with a generic placeholder head so it runs as-is. The point is to replace that head with your own, and the guide below is how it was done the first time, by a non-programmer directing Claude. The live original: [hannarodgers.com](https://hannarodgers.com).

## Run it

Open the folder with any static server (browsers block `fetch` from `file://`):

```
python3 -m http.server 8000
```

then visit `http://localhost:8000/`. Or publish the folder to GitHub Pages, Cloudflare Pages or Netlify.

To publish it as a **Claude Artifact** (which does not serve `.glb` files), add a base64 copy of the head next to the page: `base64 -w0 head.glb > head.glb.b64.txt`. The page falls back to that file automatically.

## What is in the folder

| File | What it is |
| --- | --- |
| `index.html` | the whole page: WebGL renderer, shaders, stretch physics, character behaviour, sound effects |
| `head.glb` | the placeholder head: mesh, per-vertex weights, `MouthOpen` and `Surprise` shape keys, texture embedded |
| `head.json` | the numbers the page needs for that head (jaw hinge, eye openings, skin colour, split lines) |
| `basecolor.jpg` | the same texture as a separate file (used only if the GLB has none) |
| `glove-*.png` | cursor hand poses: open, ready, pinch |
| `ASSET-SPEC.md` | the exact contract for `head.glb` and `head.json` |
| `tools/gen_head.py` | the script that generated the placeholder; a worked example of the spec |

**To replace the head:** produce a new `head.glb` and `head.json` that follow `ASSET-SPEC.md` and drop them in. Nothing in `index.html` needs to change for a head that keeps the same scale.

**To add music:** put a track you have the rights to in the folder and set `musicFile`, `musicLen` (seconds, exact track length for a seamless loop) and `bpm` in `CFG` near the top of the script. The Music button appears when `musicFile` is set. No track ships with the template.

**To replace the cursor:** draw the hand poses (open, ready, pinch) and save them as 320 × 319 PNGs with transparency, then set each pose's hotspot (the pixel that sits under the pointer, usually a fingertip) in `HOT` near the cursor code. The ghost demo uses the same images.

**Keys for testing:** R spin · D dizzy · A dance · Z sleep · N "no" · E/W scoots · T tilt · I intro · 1/2/3 faces · B blink · L light · C clay · O hold mouth open · S sound · M music. `window.__state()` prints what the head is doing.

---

# Build your own: a step-by-step guide

Written for someone who is not a programmer but is comfortable directing one. Each phase has what you need ready, what to ask Claude for, and what to check before moving on. Follow the phases in order. Paragraphs marked **Your call** are where your project can reasonably diverge; everything else is a known-good path. Expect several weeks of part-time work: the model (phases 1–3) is the slow part, behaviour and polish move fast once the model is approved.

**Who this is for.** This is the route that works when you cannot model, rig or code: a generated mesh, one procedural expression, code-drawn eyes, and a renderer written for this one page. It is not the route a CG artist would choose. If you can sculpt or model, three forks give a better result for about a day's work each; they are marked **CG fork**.

## Before you start

| Need | Why |
| --- | --- |
| Claude (Pro or above) with a Project, Artifacts and a connected folder | the Project keeps a status file across chats; Artifacts host each build at a stable link; the connected folder is how files reach your disk |
| A 3D model generator with GLB export (Tripo was used; Meshy also works) | the head comes from here. Export is usually a paid feature even when generation is free |
| An image generator (Gemini was used) | concept art, the three-view turnaround that feeds the 3D generator, cursor art |
| Photos of yourself: front, both sides, back, plus any signature item | the generator has to know your face and your props |
| A music track you have the rights to, one that loops cleanly | optional. Do not use game music |

**Set up the Project first.** Make a Claude Project for the head and keep every chat inside it. In the first chat, ask Claude to create and maintain a status file that records the current build link, what changed in each version, exact tuning values and what is left. Start each new chat with: *"Read the project status file first, then continue from where it says we are."* This is what lets the project survive dozens of chats.

**Skills you need:** none technical. You need to look at a build, say in plain words what feels wrong, and hold the line on what you want. Claude turns "feels too slow" and "the emotion is surprise at being stretched" into numbers.

## Phase 1 — Design your head

Decide the character before you generate anything: how stylized, which features and props carry your identity, and what it should feel like when it stretches. We went cartoon; a more realistic head is a legitimate choice and changes nothing downstream.

1. **Collect reference.** Photograph yourself front, left, right and back in even light, neutral face, mouth closed. Photograph any identity item from every side.
2. **Make a character sheet** in an image generator from your photos. Iterate until it is you.
3. **Make a three-view turnaround:** front, side and back of the settled character in matching style, lighting and pose on a plain background. This is the most important deliverable of the phase. 3D generators guess the sides they cannot see and guess badly; feeding all three views costs more credits and gives a far better model.
4. **Keep it legal.** Reference a game if you like, but ship nothing of theirs: no logos, no character, no music. The interaction is the homage.

**Check:** the turnaround reads as one character from all three angles; the mouth is closed and the face neutral; any prop sits the same way in every view.

> **Your call:** style, props, whether the head is you at all. What does not change: neutral face, closed mouth, three matching views.

## Phase 2 — Make the 3D model

Generate the head from your turnaround, export a GLB, and let Claude do all mesh work by script.

1. **Generate** with multi-view input. Target roughly 5,000–12,000 triangles (the original is about 10,400 in quad topology; the placeholder is 15,000). Use the highest texture resolution offered; the texture sells the face. Generate a few candidates and pick the one whose face and prop read correctly, not the smoothest.
2. **Export** GLB, textures embedded, vertex colours off. If you only get OBJ, Claude can convert it.
3. **Ask for an inspection before anything else:** *"Inspect the GLB and report triangle count, whether it is quads, texture size, whether it is one connected mesh or many pieces, and whether it is symmetrical. Do not change anything yet."* A head split into hundreds of pieces along texture seams will crack when stretched; Claude can weld it, but find out now.
4. **Ask for the four structural changes, in order, each as its own build you approve:**
   1. **Mouth cut.** *"Cut the mouth along the mesh's existing edge loop at the lip line, not along the painted lips. Add an inner mouth cavity."* Cutting on painted lines produced thin triangle slivers at the corners that four rounds of fixes could not clean; cutting on the loop the generator already made solved it in one.
   2. **Eyes.** Replace painted eyes with eyes drawn in code so they can look around and blink. Ask for large irises with little white above or below, and ask Claude to research stylized-character gaze: aiming both eyes at one 3D point makes a cartoon look cross-eyed, so the eyes converge less than physics says.
   3. **Prop cleanup.** Supply clean source images for any logo or detail the generator painted badly; do not ask Claude to redraw them.
   4. **One expression shape.** An exaggerated "surprise at being stretched" face (brows up, cheeks, nose, mouth) computed as a shape the shader can blend, driven by how far the face is pulled. Every later face is carved out of this one in code.
5. **Lighting:** soft and flat, close to the generator's own preview.
6. **Lock it.** Say so in writing, have Claude publish the model as its own artifact labelled approved, and never edit that artifact again. Every later build starts from a copy. Also have Claude export the GLB and `head.json` per `ASSET-SPEC.md` to your folder.

**Check:** open it at full size; look at rest, mid-blink, mouth open, from the side and from below.

> **Your call:** which generator, how stylized, which props. What does not change: cut on edge loops, code-drawn eyes, one baked expression shape, a locked approved model.

> **CG fork 1 — retopologize before you lock.** Generated edge loops are generic, which is why mouth corners and socket rims stay slightly wrong forever. If you can retopo, rebuild the face with proper loops around the eyes and mouth and denser lips, bake the texture onto it, and hand Claude that mesh.

> **CG fork 2 — sculpt real shape keys and real eyes.** Instead of one procedural surprise shape, sculpt 6–8 blend shapes on the locked mesh (jaw open, brows per side, smile, O, blink) with a modelled mouth interior and teeth, plus eyeball and lid geometry. Export them as shape keys and tell Claude to drive those. This removes the painted-teeth limit and gives a real wink and a real O.

**Skip these:** stock heads (none will be you and bone rigs do not help); learning to sculpt the head by hand first (two weeks got the original project a cube); decimating a million-face mesh (export at a sane count instead); vertex painting followed by decimation (it smears the paint).

## Phase 3 — Get the model into a web page

This template is that page. Ask Claude for: *"Build a self-contained WebGL page that loads head.glb and head.json per ASSET-SPEC.md. No frameworks, no build step. It must run on phones."* Stretch, expression and eye lookups are computed from each vertex's rest position so seam copies always move together and the texture never cracks. Republish to the same artifact URL every round so the link never changes, and keep the approved-model artifact untouched as the fallback. Ask for keyboard test hooks for every scripted state and a `window.__state()` readout.

> **CG fork 3 — ask for three.js, not a one-off renderer.** This page uses hand-written WebGL. It runs anywhere, but the stretch, eyes, hair spring and lighting exist only as code. If you want the head in a normal pipeline, tell Claude up front: *"Build it on three.js with GLTFLoader; keep the deformation in a custom vertex shader on a standard material."* Everything in phases 4–8 still applies.

## Phase 4 — Grab, stretch, snap back

This is the product. Get it right first and protect it from every later change. A fix that makes the snap-back less satisfying is not a fix.

1. **The grab.** The grabbed point follows the pointer exactly, with no lag; vertices within a radius move with it, falling off smoothly; pulling further gets harder (soft taper), not a hard stop.
2. **The release.** Spring physics with overshoot. Values here: stiffness 235, damping 12.5 minus 4.2 × pull amount (bigger pulls wobble longer). Sparkles, a small shake and a "sproing" on big releases.
3. **Hold or snap.** Small pulls (under half of maximum stretch at release) stay as a pose. Big pulls snap back and reset every held pose. Grabbing near a held point picks it up; a tap releases it.
4. **Up to 8 simultaneous pulls.**
5. **Mouth and expression on stretch.** The mouth opens as the face is pulled (the stretch is the slider; there is no UI control), with a random delay and amount per grab.
6. **Tap to boop.** A dip-in wobble and sometimes a surprised or grinning face.
7. **Turn and lean.** Dragging the background turns the head; the head leans toward the pointer and the eyes follow it. On phones the turn rate scales with screen width.

**Three rules:** never release a held pose on a timer or because there are too many (poses clear only on a bigger event); never add distortion the visitor did not make; never trade away the snap to fix something else.

**Check on a phone:** a small tug holds and a big tug snaps everything back; the grabbed point sits under your finger; nothing cracks at the seams; a hard yank from the side does not pull the mouth inside out.

## Phase 5 — Bring it to life

Add behaviour in short rounds, one system per round, and play every build on a phone before asking for the next. Build in this order.

1. **Idle life:** breathing mouth, slow rock and bob, hair spring, blinks, eye darts.
2. **Eye contact:** a dart to look straight at the viewer, used at the start of the intro and after every reaction. Most "the reaction feels off" notes were fixed by where the eyes went.
3. **Faces:** split the one expression shape into regions in code (brows per side; mouth centre vs corners) and compose wow, grin, skeptic, effort, annoyed, shut, dazed, yawn, sleepy. Expressions ease in and out; distortions never do. A real "O" or anything that hides painted teeth needs a sculpted shape (CG fork 2).
4. **Idle rotation:** 2–3 s after the last touch, then every 3–5 s: a scoot back with a glance, a quick face, a bouncy tilt.
5. **Reactions to rough handling:** a heat meter over the last 10 s. At 3.5 a skeptic look and "hm?"; at 6 an annoyed "no" head shake, which is the warning. One more big pull within 8 s triggers the payoff. Then a 15 s cooldown. The warning is what makes the payoff feel earned.
6. **Two payoffs, each with its own cause:** yanking (the heat route) ends in a KO dizzy; piling up held distortion (more than 4 held pulls or total held stretch over 1.4) triggers the spin, which carries exactly the visitor's distortion through three turns and snaps back at landing. Whirling the head by the background also gives the dizzy.
7. **Acting notes:** in a real head shake the eyes stay locked on the target and the person blinks on the first turn. A floating head's dizzy must happen in the screen plane (roll, drift, nod), not toward the camera.
8. **Dance:** after 10 s untouched, two 8-beat phrases at the music's tempo, holding your gaze.
9. **Sleep:** after 18 s untouched with the pointer still for 5 s: yawn, lids close, head sinks, breathing loop with snores and floating z's. Any pointer movement wakes it with a jerk, wide eyes, a snort, a look at you, then it shakes off held poses.
10. **Intro:** grows from a point with a sparkle pop, rocks, settles and grins, about 1.6 s.

**The 20-second rule.** Most visitors leave within about 20 s of interaction. Every timer above was cut by half or more once that was accepted. An idle visitor should see intro, an idle move, the dance, then sleep, inside 20 s.

**Check on a phone, by hand not by key:** pose a face until it spins; yank until it says "no" and then KO; whirl it dizzy; leave it until it sleeps and wake it. If you cannot reach one of them in a minute of play, its trigger is wrong.

> **Your call:** which faces, which payoffs, what it does when ignored. What does not change: eye contact after every reaction, warn before you punish, one cause per payoff, timers sized to 20 s.

## Phase 6 — Sound and music

All effects are synthesized in code; only the music is a file. Two switches: Sound (on by default; browsers start it on the first click) and Music (off by default). A single combined switch was tried and reverted.

- **Effects:** a rubbery tone rising with the stretch, audible whenever the pointer moves; a "plip" when a small pull sets; a "sproing" on a big snap; "hm?" and a rattle for the "no"; a "tweety" for dizzy; yawn, snore, exhale whistle and wake snort. Keep everything between 150 Hz and 3 kHz so phone speakers play it.
- **No reward sounds.** No melodic chimes on the spin or landing. Melody competes with the music and the visitor has not achieved anything.
- **Music:** your own licensed track; pick one that loops cleanly on an exact beat count. Hand Claude the WAV and ask it to measure tempo and loudness, encode an MP3, and set loop points to the track's exact length after detecting where the audio really starts in the decoded file (MP3 decoders add silence at the front, which otherwise clicks on every loop).
- **Mix:** one gentle compressor; music at about 17 % of the effects level, ducking further while pulling, during the spin and while asleep.
- **iPhone silent mode** mutes Web Audio. Set the audio session type to playback before creating the audio context, after the visitor has chosen sound.

Claude cannot hear its own output; it sets levels by arithmetic. You are the only ear.

## Phase 7 — Optional polish

- **Custom cursor (desktop):** hand poses with identical angle and lighting (open, ready, pinch), rendered on a solid background and cut out by Claude; the system cursor is hidden over the head and the hand eases between poses. The template ships a set of line-art hands.
- **Ghost demo tug:** if nobody has grabbed the face 2.5 s after the intro, a translucent hand floats in, pinches a cheek, pulls, lets go with a snap, and floats off. Once more 8 s later. This replaced a text hint and is the most effective onboarding found.
- **Boot card / music choice:** a short title card with Music on / Music off, auto-dismissed after about 8 s. A required choice is also what lets the browser start audio.
- **Phone turning:** only a clearly sideways swipe turns the head; vertical swipes scroll the page.

## Phase 8 — Put it on your website

The head lives as its own page in a subfolder, embedded in an iframe with a photo fallback for browsers without WebGL. Prototype the homepage in an artifact with a layout switch first. Strip the test keys or hide them behind a query parameter. Have Claude copy files into the site with a dated backup and a changelog entry every time, and verify size and content on disk after each copy. Ship it yourself; do not have Claude run git on your working folder. Test on real devices: your phone with the ring switch both ways, a desktop at full size, and a second visit in the same session.

Three things learned the hard way: anything placed relative to the head's on-screen position must read that position once when the head has settled and hold it; anything measured from text must re-measure after web fonts load; physics must step in fixed sub-steps per frame (this template does) or slow devices and screen recorders see slow motion.

## How to work with Claude on this

- **One system per round.** Ask for one change, play it, write what you felt, ask for the next. Feel words are enough.
- **Diagnose before building.** *"Make sure you understand the problem before changing anything. Tell me what you think is causing it and what you propose, then wait."*
- **Set the bar for done.** *"Fixed means you checked it in the real page, at full size, in motion: at rest, mid-blink, mouth open, from the side and from below. Report no console errors every round."* Claude can run the page headless and screenshot it; it will not do this thoroughly unless required.
- **Ask if it is confident** when a diagnosis follows a failed fix. **Ask for disagreement:** "If this is a weak idea, say so."
- **Keep the status file current** and start a new chat whenever one gets long.
- **Keep the approved model sacred.** Every build starts from a copy of it.
- **Expect reversals.** Changing your mind is normal; say so and move on.

## Credits and licence

Code: MIT (see LICENSE). The placeholder head, its texture and the hand cursor images are released to the public domain (CC0); replace them with your own. If you build one, a link back to the guide is appreciated but not required. The original project, its head and its artwork belong to Hanna Rodgers and are not included here.
