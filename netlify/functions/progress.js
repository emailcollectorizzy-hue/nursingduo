import { getStore } from "@netlify/blobs";
import crypto from "node:crypto";

const isValidUser = (u) => typeof u === "string" && /^[a-z0-9_-]{2,32}$/i.test(u);
const isValidPin  = (p) => typeof p === "string" && /^\d{4,8}$/.test(p);
const hash = (p) => crypto.createHash("sha256").update(String(p)).digest("hex");

export default async (req) => {
  if (req.method !== "POST") {
    return new Response("method not allowed", { status: 405 });
  }
  let body;
  try { body = await req.json(); }
  catch { return new Response("bad json", { status: 400 }); }

  const { action, user, pin, storageKey } = body || {};
  if (!isValidUser(user) || !isValidPin(pin)) {
    return new Response("bad credentials format", { status: 400 });
  }
  if (typeof storageKey !== "string" || storageKey.length < 1 || storageKey.length > 128) {
    return new Response("bad storageKey", { status: 400 });
  }
  const safeKey = storageKey.replace(/[^a-z0-9:_-]/gi, "_");

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
    return Response.json({ ok: true, updatedAt });
  }

  return new Response("bad action", { status: 400 });
};

export const config = { path: "/api/progress" };
