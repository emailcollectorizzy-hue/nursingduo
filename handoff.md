# Handoff — How Netlify Blobs progress-sync works (and how to wire a new master into it)

> Audience: an AI agent (Claudian) or future-me asked to make a **new-format quizpage master**
> sync its progress to the cloud. Read this top-to-bottom once; it is self-contained.
> Authoritative code lives beside this file: `netlify/functions/progress.js` (server),
> `index.html` (the hub), and the deployed `*- Master.html` pages.

---

## 0. TL;DR

- The whole sync system is **one Netlify Function** (`/api/progress`) backed by **Netlify Blobs**, plus a small **client shim** that each master page runs.
- Auth is **username + PIN** (no email, no OAuth). First use of a username+PIN *creates* that account.
- Each course's progress is one JSON blob keyed by the master's **`STORAGE_KEY`**. Conflicts resolve by **last-write-wins on a millisecond `updatedAt`**.
- A master page becomes cloud-synced by satisfying **two requirements** (a `STORAGE_KEY` constant + saving its state to `localStorage[STORAGE_KEY]`) and then **appending the cloud-sync shim** `<script>` (§4). That's the entire job.
- **The current PULSE masters (`template-v2`) DO NOT contain the shim** — only the hub (`index.html`) talks to the server, and only to *read*. So a freshly built master has **no working cloud sync** until you add the shim. This is the gap you're being asked to close. (Manual `QPv2:` paste codes still work offline — see §8.)

```
                         ┌─────────────────────────────┐
  Master page (browser)  │  localStorage[STORAGE_KEY]   │  ← single source of truth on-device
   = NS250 - Master.html └──────────────┬──────────────┘
        │  cloud-sync shim (§4)         │ hooks Storage.setItem → debounced push
        │  POST /api/progress           │ pull-on-load (reload if server newer)
        ▼                               ▼
  ┌───────────────────────── Netlify Function ─────────────────────────┐
  │  netlify/functions/progress.js   (path = /api/progress)            │
  │  actions: get · put · list · streak                               │
  └──────────────┬─────────────────────────────────────────────────────┘
                 ▼  @netlify/blobs  store "quizpage-progress"
   meta/<user>            {pinHash, created}
   data/<user>/<key>      {state, updatedAt}      ← one per course (key = STORAGE_KEY, sanitized)
   streak/<user>          {count, best, lastDay, freezes}
   activity/<user>        {days:{<epochDay>:1}}
                 ▲
   index.html (hub)  POST /api/progress {action:"list"} → reads ALL the user's course blobs
```

---

## 1. The server contract (`netlify/functions/progress.js`)

One function, `export const config = { path: "/api/progress" }`, **POST only**, JSON body.
Every request body MUST include `{ action, user, pin }`.

- `user` — `/^[a-z0-9_-]{2,32}$/i`
- `pin` — `/^\d{4,8}$/`  (stored only as a SHA-256 hash, never plaintext)

**Auth model (important & deliberate):** the *first* time a `(user, pin)` pair is seen, the
server creates `meta/<user> = {pinHash, created}` and accepts it. After that, a wrong PIN for an
existing user returns **401**. So "sign up" and "sign in" are the same call — there is no
registration step, and **anyone who picks an unused username owns it**. This is a low-stakes
personal study app; do not treat the PIN as real security.

### Actions

| action | extra body fields | returns | effect |
|---|---|---|---|
| `put` | `storageKey`, `state` (object), `updatedAt` (ms number) | `{ok:true, updatedAt, streak}` **or** `{ok:false, stale:true, server}` | Writes `data/<user>/<key> = {state, updatedAt}` **only if** incoming `updatedAt` ≥ stored. Also bumps streak + activity for today. |
| `get` | `storageKey` | `{state, updatedAt}` **or** `{empty:true}` | Reads one course blob. |
| `list` | — | `{courses:{<key>:{state,updatedAt}}, streak, activity}` | Reads **every** `data/<user>/*` blob + streak + activity. This is what the hub uses. |
| `streak` | — | `{streak}` | Streak only. |

**Conflict rule (last-write-wins):** `put` rejects with `{stale:true, server:<the newer blob>}`
when the server already has a strictly-newer `updatedAt`. The client is expected to treat the
returned `server` state as truth (the shim handles this by pulling-newer on load + reloading).
There is **no field-level merge** — a whole course's state object is replaced atomically. Keep all
of a course's progress inside that one object.

**Streak/activity** are derived automatically on every `put` (any save "counts" for today;
2-day gaps consume one `freeze`). You don't manage these from the client.

**Blob key sanitisation:** the server runs `storageKey` through
`replace(/[^a-z0-9:_-]/gi, "_")`. Your `STORAGE_KEY` may contain `:` (it does), but anything
exotic becomes `_`. Keep keys simple (`quizpage:<slug>`).

---

## 2. Deploy plumbing (already set up — just don't break it)

- `package.json` → `"@netlify/blobs": "^8.x"`, `"type": "module"`.
- `netlify.toml` → `functions = "netlify/functions"`, `publish = "."`, plus one `[[redirects]]`
  per master giving it a clean URL (`/ns250` → `/NS250MedSurg - Master.html`, status 200 = rewrite).
- Netlify Blobs needs **no config/keys** — `getStore("quizpage-progress")` just works on Netlify.
  (Locally it needs `netlify dev`; a bare `file://` open is fine because the shim no-ops off http.)
- The store name is `"quizpage-progress"`. Same store for all users/courses; isolation is by key prefix.

---

## 3. What makes a page "syncable" — the two requirements

The shim is **page-agnostic**. It works on ANY master/review page that satisfies:

1. **A global `STORAGE_KEY` string**, unique per course, of the form `quizpage:<slug>`.
   In `template-v2.html` this already exists: `const STORAGE_KEY = "quizpage:{{STORAGE_KEY}}";`
   (the `{{STORAGE_KEY}}` placeholder is filled at build time from the course slug).
2. **All progress is persisted to `localStorage[STORAGE_KEY]`** as one `JSON.stringify(state)`
   object. `template-v2` does this (`localStorage.setItem(STORAGE_KEY, JSON.stringify(state))`).

If both hold, you do **not** need to find every save site — the shim monkey-patches
`Storage.prototype.setItem` and fires whenever that key is written. A new format only needs to keep
these two invariants (one state object, one key) and it's automatically syncable.

> ⚠️ Per-chapter standalone pages use a *different* key and would orphan progress — that's why the
> skill folds chapters into ONE course master (one key) instead. Keep one key per course.

---

## 4. The cloud-sync shim — drop-in `<script>` (the actual fix)

This is the **proven** implementation (it lived in the pre-PULSE `template.html` and is what the hub's
`list` was built to read). To make a new-format master sync, **paste these two `<script>` blocks
immediately before `</body>`** (after the page's own init script, so `STORAGE_KEY` and `switchTab`
already exist). It is a **safe no-op on `file://`** and auto-activates on `http(s)://`.

```html
<!--
  ===== Cloud sync + Hub integration =====
  SAFE no-op offline / on file://. On nursingduo.netlify.app: username+PIN auth via
  Netlify Blobs, debounced push on save, pull-on-load with reload-if-newer.
  Storage key = STORAGE_KEY of this master. Keep verbatim across masters so the hub's
  `list` action sees them.
-->
<script>
/* ===== Cloud sync shim (Netlify Blobs) ===== */
(function cloudSync(){
  if (typeof STORAGE_KEY !== "string") return;          // requirement #1
  const CLOUD_URL = "/api/progress";
  const AUTH_KEY  = "quizpage:cloudauth";               // shared across hub + all masters (same origin)
  const META_KEY  = STORAGE_KEY + ":cloudmeta";         // per-course "last synced updatedAt"

  const getAuth = () => { try { return JSON.parse(localStorage.getItem(AUTH_KEY) || "null"); } catch { return null; } };
  const setAuth = (a) => { try { localStorage.setItem(AUTH_KEY, JSON.stringify(a)); } catch {} };
  const clearAuth = () => { try { localStorage.removeItem(AUTH_KEY); } catch {} };
  const localUpdatedAt = () => { try { return +(localStorage.getItem(META_KEY) || 0); } catch { return 0; } };
  const setLocalUpdatedAt = (t) => { try { localStorage.setItem(META_KEY, String(t)); } catch {} };

  async function api(action, extra) {
    const auth = getAuth(); if (!auth) return null;
    let res;
    try {
      res = await fetch(CLOUD_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action, user: auth.user, pin: auth.pin, storageKey: STORAGE_KEY, ...extra })
      });
    } catch { return null; }
    if (res.status === 401) { clearAuth(); promptAuth(true); return null; }
    if (!res.ok) return null;
    return res.json();
  }

  function promptAuth(wrong) {
    if (document.getElementById("cs_modal")) return;
    const m = document.createElement("div");
    m.id = "cs_modal";
    m.style.cssText = "position:fixed;inset:0;background:rgba(0,0,0,.78);z-index:99999;display:flex;align-items:center;justify-content:center;padding:20px;";
    m.innerHTML = `
      <div style="background:#1a1a1a;color:#fff;padding:24px;border-radius:14px;max-width:360px;width:100%;font:14px/1.5 system-ui,sans-serif;box-shadow:0 20px 60px rgba(0,0,0,.5);">
        <div style="font-size:18px;font-weight:600;margin-bottom:4px;">☁️ Cloud sync</div>
        <div style="opacity:.7;margin-bottom:16px;">${wrong ? "Wrong PIN. Try again." : "Sign in to sync progress across devices."}</div>
        <label style="display:block;margin-bottom:10px;">Username<br><input id="cs_u" autocomplete="username" autocapitalize="none" autocorrect="off" style="width:100%;padding:8px;margin-top:4px;background:#000;color:#fff;border:1px solid #444;border-radius:6px;font:inherit;box-sizing:border-box;"></label>
        <label style="display:block;margin-bottom:14px;">PIN (4–8 digits)<br><input id="cs_p" type="password" inputmode="numeric" pattern="\\d*" autocomplete="current-password" style="width:100%;padding:8px;margin-top:4px;background:#000;color:#fff;border:1px solid #444;border-radius:6px;font:inherit;box-sizing:border-box;"></label>
        <div style="display:flex;gap:8px;">
          <button id="cs_ok" style="flex:1;padding:10px;background:#3b82f6;color:#fff;border:0;border-radius:8px;font:inherit;font-weight:600;cursor:pointer;">Sign in</button>
          <button id="cs_skip" style="padding:10px 14px;background:transparent;color:#888;border:1px solid #444;border-radius:8px;font:inherit;cursor:pointer;">Skip</button>
        </div>
        <div style="font-size:12px;opacity:.55;margin-top:12px;">First time? Pick any username + PIN — that combo becomes your account.</div>
      </div>`;
    document.body.appendChild(m);
    const finish = (auth) => { m.remove(); if (auth) { setAuth(auth); pullThenStart(); } else { attachAutoPush(); } };
    m.querySelector("#cs_ok").onclick = () => {
      const u = m.querySelector("#cs_u").value.trim();
      const p = m.querySelector("#cs_p").value.trim();
      if (!/^[a-z0-9_-]{2,32}$/i.test(u)) return alert("Username: 2–32 chars (letters, numbers, _ or -)");
      if (!/^\d{4,8}$/.test(p)) return alert("PIN: 4–8 digits");
      finish({ user: u, pin: p });
    };
    m.querySelector("#cs_skip").onclick = () => finish(null);
    m.querySelector("#cs_p").addEventListener("keydown", e => { if (e.key === "Enter") m.querySelector("#cs_ok").click(); });
  }

  async function pullThenStart() {
    const res = await api("get", {});
    if (res && !res.empty && res.state && (res.updatedAt || 0) > localUpdatedAt()) {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(res.state));
        setLocalUpdatedAt(res.updatedAt);
        location.reload();                 // simplest correct merge: reload with server state
        return;
      } catch {}
    }
    attachAutoPush();
    if (res && res.empty) schedulePush();  // first device for this course → seed the cloud
  }

  let pushTimer = null;
  function schedulePush() { clearTimeout(pushTimer); pushTimer = setTimeout(doPush, 2000); }
  async function doPush() {
    if (!getAuth()) return;
    let raw; try { raw = localStorage.getItem(STORAGE_KEY); } catch { return; }
    if (!raw) return;
    let s; try { s = JSON.parse(raw); } catch { return; }
    const updatedAt = Date.now();
    const res = await api("put", { state: s, updatedAt });
    if (res && res.ok) setLocalUpdatedAt(updatedAt);
    // if res.stale: a newer device won; next load's pullThenStart() will reconcile.
  }

  function attachAutoPush() {
    const orig = Storage.prototype.setItem;
    Storage.prototype.setItem = function(k, v) {
      orig.call(this, k, v);
      if (k === STORAGE_KEY && getAuth()) schedulePush();   // every state save → debounced push
    };
    document.addEventListener("visibilitychange", () => { if (document.hidden) { clearTimeout(pushTimer); doPush(); } });
    window.addEventListener("pagehide", () => { clearTimeout(pushTimer); doPush(); });
  }

  window.cloudSync = {
    signOut: () => { clearAuth(); location.reload(); },
    status:  () => ({ auth: getAuth(), localUpdatedAt: localUpdatedAt() }),
  };

  function boot() {
    if (location.protocol !== "http:" && location.protocol !== "https:") return;   // file:// no-op
    if (getAuth()) pullThenStart();
    else promptAuth(false);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
</script>
<script>
/* ===== Hub integration: "← Hub" back button + #tab= hash router ===== */
(function hubLink(){
  if (location.protocol !== "http:" && location.protocol !== "https:") return;
  function addBackBtn() {
    if (document.getElementById("hub-back-btn")) return;
    const btn = document.createElement("a");
    btn.id = "hub-back-btn"; btn.href = "/"; btn.innerHTML = "← Hub"; btn.title = "Back to course select";
    btn.style.cssText = "font:600 12px/1 -apple-system,system-ui,sans-serif;text-decoration:none;color:#fff;background:rgba(20,20,28,.88);-webkit-backdrop-filter:blur(8px);backdrop-filter:blur(8px);padding:7px 11px;border-radius:10px;border:1px solid rgba(255,255,255,.14);box-shadow:0 2px 8px rgba(0,0,0,.25);";
    // adapt to your header; fall back to fixed top-right
    const slot = document.querySelector("header.app-header .header-quick") || document.querySelector("header.app-header .header-meta");
    if (slot) slot.insertBefore(btn, slot.firstChild);
    else { btn.style.cssText += "position:fixed;top:max(10px,env(safe-area-inset-top));right:max(10px,env(safe-area-inset-right));z-index:9998;"; document.body.appendChild(btn); }
  }
  function applyHash() {
    const h = location.hash.slice(1); if (!h) return;
    const tab = new URLSearchParams(h).get("tab");
    if (tab && typeof switchTab === "function") { try { switchTab(tab); } catch {} }
  }
  function boot() { addBackBtn(); setTimeout(applyHash, 120); }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
  window.addEventListener("hashchange", applyHash);
})();
</script>
```

> The hub-link script is optional polish (back button + deep-link `#tab=quiz`). If your new format
> has no `switchTab(name)` function or `header.app-header`, the back button still renders (fixed
> top-right) and the hash router simply no-ops. Adjust the `slot` selector to your layout.

### Where exactly to splice
- In `template-v2.html` and any master built from it: place both blocks **just before `</body>`**,
  after the last existing `<script>` (the page's init). The shim relies on `STORAGE_KEY`
  (and, for the hub script, optionally `switchTab`) being defined by then.
- Because masters are mirrored vault → repo (skill Step 5.5), add the shim to the **template** (so
  every future build has it) **and** to the already-deployed masters that lack it. The cleanest fix
  is to put it in `template-v2.html` once; then rebuilt masters carry it.

---

## 5. Registering a NEW course/master with the hub (`index.html`)

The shim makes a page *write* its blob; the hub makes it *visible*. To add a new master so it shows
on nursingduo.netlify.app and aggregates into stats/streak:

1. **Add a redirect** in `netlify.toml`:
   ```toml
   [[redirects]]
     from = "/ns2xx"
     to = "/<COURSE><Slug> - Master.html"
     status = 200
   ```
2. **Add a `COURSES` entry** in `index.html` (search `const COURSES = [`):
   ```js
   { id: "ns2xx", name: "Course Name", storageKey: "quizpage:<same-slug-as-master>",
     href: "/ns2xx", status: "live", icon: "🧪", accent: "#2563eb" },
   ```
   The **`storageKey` MUST equal the master's `STORAGE_KEY` exactly** — that string is the join key
   between the master's blob and the hub tile. If they differ, the tile shows 0 progress.
3. **Mirror the master file** into this repo root (skill Step 5.5 already does `vault → repo` copy)
   and commit. Netlify deploys on push.

The hub reads `state.xp` and `state.srs` from each course blob for its stats — keep those fields in
your state object if you want the hub's XP/level/Leitner stats to populate (a new format can carry
whatever else it likes alongside).

---

## 6. Mental model of a full round-trip (so you can debug it)

1. User opens master on phone → shim `boot()` → has auth? → `pullThenStart()`.
2. `get` returns the server blob; if `updatedAt` > local meta, **overwrite localStorage + reload**
   (the page re-renders from server truth). Else attach the auto-push hook.
3. User studies → page calls `localStorage.setItem(STORAGE_KEY, …)` → patched `setItem` →
   `schedulePush()` (2 s debounce) → `put {state, updatedAt: Date.now()}`.
4. Server stores it (if not stale), bumps streak/activity, returns `{ok, streak}`.
5. On tab-hide / pagehide, a final flush `doPush()` runs so nothing is lost.
6. Later, on the laptop, step 2 pulls the phone's newer blob → reload → identical state. LWW.

---

## 7. Gotchas / invariants (don't regress these)

- **Same-origin shared auth.** Hub and masters are all served from `nursingduo.netlify.app`, so they
  share `localStorage["quizpage:cloudauth"]`. Sign in once (anywhere) and every master is authed.
  This only works because everything is one site — keep all masters + hub on that one domain.
- **`file://` must stay a no-op.** The `location.protocol` guard is load-bearing: the same master
  file is opened offline from the vault and must not nag a sign-in modal there. Keep the guard.
- **One state object per course.** No partial/field merges server-side; a `put` replaces the whole
  course blob. Don't split a course's progress across keys.
- **`updatedAt` is the only clock.** Always `Date.now()` ms. Don't send seconds or a counter.
- **Don't rename `STORAGE_KEY` of a live master** — it points at a different blob and orphans
  existing progress. If you must, plan a migration (`get` old key → `put` new key once).
- **PIN is not security.** SHA-256, no rate-limit, first-claim-wins usernames. Fine for personal use;
  never store anything sensitive.
- The server's only persistence is Netlify Blobs in store `quizpage-progress`. There's no DB, no
  backup. A `put` with a future-clock `updatedAt` can wedge a course (nothing can overwrite it until
  real time passes it) — don't fake timestamps.

---

## 8. The offline fallback (manual `QPv2:` codes) — unrelated but don't confuse it

Independently of the cloud, every master can export/import a compact **`QPv2:<b64>.<checksum>`**
progress code (the "Sync" modal — `openSyncModal`/`packFlashSync`/`applyFlashSync` in
`template-v2.html`). That's a **manual, peer-to-peer, no-account** transfer (copy code on device A,
paste on device B; apply is non-regressive — it only ever *raises* progress). It uses **no server**
and is the offline/airgapped path. Cloud sync (this doc) and QPv2 codes coexist; don't conflate them.

---

## 9. Quick test checklist after wiring a new master

- [ ] Open the master from `file://` → **no** sign-in modal, page works (shim no-op).
- [ ] `netlify dev` (or deployed) → open master → sign-in modal appears.
- [ ] Sign in with a fresh username+PIN → no error; study a bit; wait ~2 s.
- [ ] DevTools → Network: a `POST /api/progress` with `action:"put"` returns `{ok:true}`.
- [ ] Reopen in a private window, same creds → progress pulls back (page reloads into it).
- [ ] Wrong PIN for that username → 401 → modal re-prompts "Wrong PIN".
- [ ] Hub (`/`) signed in with same creds → the new course tile shows its XP/level/streak.
- [ ] Confirm the master's `STORAGE_KEY` === the hub `COURSES[].storageKey` string (exact match).

---

_Source references in this repo: server `netlify/functions/progress.js`; hub
`index.html` (`COURSES`, `api()`, `boot()`); proven shim originally in the quizpage skill's
pre-PULSE `template.html`. Skill build/mirror steps: `~/.claude/skills/quizpage/SKILL.md`
Step 5.5 + the customization-splice note._
