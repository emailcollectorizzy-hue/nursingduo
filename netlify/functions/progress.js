import { getStore } from "@netlify/blobs";
import crypto from "node:crypto";

const isValidUser = (u) => typeof u === "string" && /^[a-z0-9_-]{2,32}$/i.test(u);
const isValidPin  = (p) => typeof p === "string" && /^\d{4,8}$/.test(p);
const hash = (p) => crypto.createHash("sha256").update(String(p)).digest("hex");
const safeStorageKey = (k) => String(k).replace(/[^a-z0-9:_-]/gi, "_");
const epochDay = (ms) => Math.floor((ms || Date.now()) / 86400000);

// Streak: any PUT counts as activity for today. Streak increments on consecutive days.
async function touchStreak(store, user) {
  const key = `streak/${user}`;
  const cur = (await store.get(key, { type: "json" })) || { count: 0, best: 0, lastDay: 0, freezes: 1 };
  const today = epochDay();
  if (cur.lastDay === today) return cur;
  if (cur.lastDay === today - 1) {
    cur.count = (cur.count || 0) + 1;
  } else if (cur.lastDay === today - 2 && cur.freezes > 0) {
    cur.freezes -= 1;
    cur.count = (cur.count || 0) + 1;
  } else if (cur.lastDay && cur.lastDay < today - 1) {
    cur.count = 1;
  } else {
    cur.count = Math.max(1, cur.count | 0);
  }
  cur.best = Math.max(cur.best | 0, cur.count);
  cur.lastDay = today;
  await store.setJSON(key, cur);
  return cur;
}

// Activity: a single blob per user, an object {day: 1} marking each active day.
// Keeps recent 90 days only, prunes older entries.
async function touchActivity(store, user) {
  const key = `activity/${user}`;
  const cur = (await store.get(key, { type: "json" })) || { days: {} };
  const today = epochDay();
  cur.days[today] = 1;
  const cutoff = today - 90;
  for (const d in cur.days) { if (+d < cutoff) delete cur.days[d]; }
  await store.setJSON(key, cur);
  return cur;
}

export default async (req) => {
  if (req.method !== "POST") {
    return new Response("method not allowed", { status: 405 });
  }
  let body;
  try { body = await req.json(); }
  catch { return new Response("bad json", { status: 400 }); }

  const { action, user, pin } = body || {};
  if (!isValidUser(user) || !isValidPin(pin)) {
    return new Response("bad credentials format", { status: 400 });
  }

  const store = getStore("quizpage-progress");
  const metaKey = `meta/${user}`;
  let meta = await store.get(metaKey, { type: "json" });
  const ph = hash(pin);

  if (!meta) {
    meta = { pinHash: ph, created: Date.now() };
    await store.setJSON(metaKey, meta);
  } else if (meta.pinHash !== ph) {
    return new Response("unauthorized", { status: 401 });
  }

  if (action === "list") {
    const prefix = `data/${user}/`;
    const out = {};
    const { blobs } = await store.list({ prefix });
    for (const b of blobs) {
      const sk = b.key.slice(prefix.length);
      const v = await store.get(b.key, { type: "json" });
      if (v) out[sk] = v;
    }
    const streak = (await store.get(`streak/${user}`, { type: "json" })) || { count: 0, best: 0, freezes: 1, lastDay: 0 };
    const activity = (await store.get(`activity/${user}`, { type: "json" })) || { days: {} };
    return Response.json({ courses: out, streak, activity });
  }

  if (action === "streak") {
    const streak = (await store.get(`streak/${user}`, { type: "json" })) || { count: 0, best: 0, freezes: 1, lastDay: 0 };
    return Response.json({ streak });
  }

  const { storageKey } = body;
  if (typeof storageKey !== "string" || storageKey.length < 1 || storageKey.length > 128) {
    return new Response("bad storageKey", { status: 400 });
  }
  const safeKey = safeStorageKey(storageKey);
  const dataKey = `data/${user}/${safeKey}`;

  if (action === "get") {
    const data = await store.get(dataKey, { type: "json" });
    return Response.json(data || { empty: true });
  }

  if (action === "put") {
    const { state, updatedAt } = body;
    if (!state || typeof updatedAt !== "number") {
      return new Response("bad payload", { status: 400 });
    }
    const existing = await store.get(dataKey, { type: "json" });
    if (existing && existing.updatedAt > updatedAt) {
      return Response.json({ ok: false, stale: true, server: existing });
    }
    await store.setJSON(dataKey, { state, updatedAt });
    const streak = await touchStreak(store, user);
    await touchActivity(store, user);
    return Response.json({ ok: true, updatedAt, streak });
  }

  return new Response("bad action", { status: 400 });
};

export const config = { path: "/api/progress" };
