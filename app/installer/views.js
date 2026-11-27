/* What the installer says: one plain screen for each situation. No ports, checksums or phases here; those go to the log, which
 * the page keeps closed. For the page and for node. */
"use strict";
(function (root) {
  const SCREENS = ["search", "ready", "work", "done", "resume", "trouble", "other"], STEPS = ["save", "install", "check"];
  const SAFE = "Your pedal is saved on this computer before anything changes.";
  const AMPS = "HyperRig keeps its presets where the original firmware keeps its amp models, its cabs and its presets. All of it is saved first and comes back when you restore the original firmware.";
  const INSTALL = { id: "install", label: "Install HyperRig", ask: { title: "Install HyperRig?", yes: "Install", text: "It takes about two minutes. " + AMPS } };
  const UPDATE = { id: "install", label: "Update HyperRig", ask: { title: "Update HyperRig?", yes: "Update", text: "It takes about two minutes. Your presets stay on the pedal." } };
  const RESTORE = { id: "restore", label: "Restore the original firmware", weight: "quiet", ask: { title: "Restore the original?", yes: "Restore",
    text: "It takes about two minutes and puts back the TANK-MINI firmware, its amp models, its cabs and its presets as they were when you installed HyperRig. HyperRig's presets go: export them in the editor first if you want them again." } };
  const EDITOR = { id: "editor", label: "Open the editor" }, AGAIN = { id: "again", label: "Try again" }, CONTINUE = { id: "continue", label: "Continue" };
  const LEAVE = { id: "leave", label: "Not now", weight: "quiet" }, SAVE = { id: "save", label: "Only save a copy", weight: "quiet" };

  function view(screen, title, text = "", more = {}) {
    if (!SCREENS.includes(screen)) throw new Error("unknown screen " + screen);
    const { over = "", pedal = "", actions = [], safe = "", step, progress } = more;
    const out = { screen, title, text, over, pedal, actions, safe };
    if (screen === "work") { out.step = STEPS.indexOf(step); out.progress = Math.min(1, Math.max(0, progress || 0)); }
    return out;
  }
  const search = () => view("search", "Plug in your TANK-MINI", "Connect it to this computer with a USB cable and switch it on. Use a port on the computer itself, not a hub.");
  const stock = version => view("ready", "Ready for HyperRig", "Your TANK-MINI has its original firmware.", { over: "TANK-MINI connected", pedal: "Original " + version, actions: [INSTALL, SAVE], safe: SAFE });
  const untried = version => view("other", "This version is not known yet", `Your TANK-MINI has the original firmware ${version}. HyperRig is installed from 011: put 011 on it with M-Upgrade, then come back.`, { over: "TANK-MINI connected", pedal: "Original " + version });
  function hyperrig(version, { newer = null, ahead = null, entry = true, backup = true } = {}) {
    const restore = entry && backup ? [RESTORE] : [];
    if (!entry) return view("ready", "HyperRig is on your pedal", "This build is older than this program can update. Use the installer it came with once; after that, this one does it.", { over: "TANK-MINI connected", pedal: "HyperRig " + version, actions: [EDITOR] });
    if (ahead) return view("ready", "Your pedal is ahead of this program", `Your pedal has HyperRig ${version}; this program has ${ahead}. Use the newest program.`, { over: "TANK-MINI connected", pedal: "HyperRig " + version, actions: [{ ...EDITOR, weight: "quiet" }, ...restore.map(r => ({ ...r, label: "Restore the original" }))] });
    if (newer) return view("ready", "An update is ready", newer === version ? `This program has another build of HyperRig ${version}.` : `Your pedal has HyperRig ${version}. Version ${newer} is here.`, { over: "TANK-MINI connected", pedal: "HyperRig " + version, actions: [UPDATE, { ...EDITOR, weight: "quiet" }, ...restore.map(r => ({ ...r, label: "Restore the original" }))] });
    return view("ready", "HyperRig is on your pedal", "Everything is up to date.", { over: "TANK-MINI connected", pedal: "HyperRig " + version, actions: [EDITOR, ...restore] });
  }
  const waiting = (backup = false) => view("ready", "Your pedal waits", "It is in update mode, with its firmware as it was.", { over: "TANK-MINI connected", actions: [INSTALL, ...(backup ? [RESTORE] : []), SAVE, LEAVE], safe: SAFE });
  const WORK = { install: { save: "Saving your pedal", install: "Writing HyperRig", check: "Checking every byte" }, restore: { save: "Saving your pedal", install: "Writing the original", check: "Checking every byte" },
    save: { save: "Saving your pedal", install: "Saving your pedal", check: "Starting your pedal" } };
  const working = (job, step, progress, title = null) => view("work", title || WORK[job][step], "", { over: { install: "Installing", restore: "Restoring", save: "Saving" }[job], step, progress });
  const saved = ({ came = true } = {}) => view("done", "Your pedal is saved", "The copy is whole and reads back from this computer. Open Details to see where it is." + (came ? "" : " The pedal did not come back by itself: switch it off and on."),
    { over: "Finished", actions: [{ id: "home", label: "Done" }] });
  /* first: HyperRig did not start the job (the original firmware did, or the loader, for one that was finished later): the editor
   * then adds the presets to start with, on a pedal that has no preset. */
  function done(job, version, { came = true, first = false } = {}) {
    const hint = came ? "" : " It did not come back by itself: switch it off and on.";
    if (job === "install") return view("done", "HyperRig is on your pedal", (first ? "Open the editor: on a pedal with no presets it adds three to start with, Clean, Crunch and Lead. Then plug in your guitar and play." : "Plug in your guitar and play.") + hint,
      { over: "Finished", pedal: "HyperRig " + version, actions: [first ? { ...EDITOR, id: "editor-first" } : EDITOR, { id: "home", label: "Done", weight: "quiet" }] });
    return view("done", "The original is back", "Your TANK-MINI is as it was, with its amp models." + hint, { over: "Finished", pedal: "Original " + version, actions: [{ id: "home", label: "Done" }] });
  }
  const resume = job => view("resume", "Let's finish the job", "The pedal was interrupted. Continue to " + (job === "restore" ? "finish restoring the original firmware." : "finish installing HyperRig."),
    { over: "TANK-MINI connected", actions: [CONTINUE], safe: "You can continue now or later: the pedal waits." });
  const TROUBLE = {
    unplugged: ["The pedal went away", "Plug it back in, straight into the computer, and it goes on from where it stopped."],
    busy: ["Something else is using it", "Close other programs that use the pedal, such as M-Upgrade or a music program, then try again."],
    refused: ["The pedal did not take it", "Its firmware did not accept the update. Switch the pedal off and on, then try again."],
    disk: ["No room for the backup", "Free about 10 MB on this computer, then try again."],
    mismatch: ["This copy did not match", "The pedal answered differently twice. Try another USB port or cable, then try again."],
    layout: ["This pedal is different", "Its memory is not laid out as the TANK-MINIs HyperRig knows. Please report it, with the Details."],
    backup: ["There is no backup here", "The original firmware of this pedal was not saved on this computer. Use the computer it was installed with."],
    elsewhere: ["Begun on another computer", "This pedal was being updated from another computer, which has its backup. Continue there."],
    noway: ["Not safe to continue", "The pedal would not come back by itself if its power went, so nothing is written. Please report it, with the Details."],
    damaged: ["This copy of HyperRig is damaged", "Please download it again."],
    failed: ["That did not work", "Try again; if it happens twice, open Details and report it."],
  };
  function trouble(kind, { changed = false, again = true } = {}) {
    const [title, text] = TROUBLE[kind] || TROUBLE.failed;
    return view("trouble", title, text, { over: "Stopped", actions: again ? [AGAIN] : [], safe: changed ? "The pedal waits in update mode, also when it is switched off and on. You can finish any time." : "Nothing was changed on the pedal." });
  }
  const updater = name => view("other", "M-Upgrade is at work", `The pedal answers as ${name}: an update of the original firmware is not finished. Finish it with M-Upgrade, then come back.`, { over: "Connected" });

  const api = { SCREENS, STEPS, TROUBLE, search, stock, untried, hyperrig, waiting, working, done, saved, resume, trouble, updater };
  if (typeof module === "object" && module.exports) module.exports = api; else root.HrViews = api;
})(typeof globalThis === "object" ? globalThis : this);
