// Actual UI controller with a minimal DOM; this is not browser-layout acceptance.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const crypto = require("node:crypto").webcrypto;
class Element {
  constructor(tag) {
    this.tag = tag;
    this.children = [];
    this.events = {};
    this.attrs = {};
    this.parent = null;
  }
  get isConnected() {
    return this.tag === "main" || !!this.parent?.isConnected;
  }
  append(...nodes) {
    for (const node of nodes) {
      node.parent = this;
      this.children.push(node);
    }
  }
  appendChild(node) {
    this.append(node);
    return node;
  }
  replaceChildren(...nodes) {
    for (const node of this.children) node.parent = null;
    this.children = [];
    this.append(...nodes);
  }
  setAttribute(key, value) {
    this.attrs[key] = value;
  }
  addEventListener(name, fn) {
    this.events[name] = fn;
  }
}
const all = (node) => [node, ...node.children.flatMap(all)];
async function settle(ui) {
  for (let i = 0; i < 50 && ui.busy; i++) await new Promise(setImmediate);
  assert.equal(ui.busy, false);
}
function environment(fetch) {
  const root = new Element("main");
  let denied = 0;
  const context = {
    window: {},
    document: { createElement: (tag) => new Element(tag) },
    crypto,
    AbortController,
    setTimeout,
    clearTimeout,
    fetch,
  };
  vm.runInNewContext(
    fs.readFileSync("app/miniapp/publications.js", "utf8"),
    context,
  );
  const ui = context.window.MiniAppPublications({
    tg: { initData: "private-signed-data" },
    back() {},
    denied() {
      denied++;
    },
  });
  ui.render(root, "en");
  return {
    root,
    ui,
    get denied() {
      return denied;
    },
  };
}
const identity = "b836d3f2-96e3-47bc-9a1c-655cad6963a9";
const review = {
  preview_url: `/miniapp/publication-preview/${identity}`,
  public_url: `https://example.invalid/p/${identity}`,
  terms: {
    en: "Exact test hosting terms",
    notice_en: "Exact public-data disclosure",
  },
  intent: {
    revision: 1,
    expected_active: null,
    expires_at: "2026-12-01T00:00:00Z",
    content_hash: "a".repeat(64),
    terms_hash: "b".repeat(64),
  },
  token: "same-review-proof",
  active: false,
};
const ok = (value) => ({ ok: true, status: 200, json: async () => value });
async function scenario(status) {
  const calls = [];
  let decisions = 0;
  const env = environment(async (url, options) => {
    const payload = JSON.parse(options.body);
    calls.push({ url, payload });
    assert.equal(payload.init_data, "private-signed-data");
    assert.equal(url.includes("private-signed-data"), false);
    if (url.endsWith("publication-consent")) {
      decisions++;
      return decisions === 1 ? { ok: false, status } : ok({ recorded: true });
    }
    return ok(
      payload.publication_id
        ? { review }
        : {
            pages: [{ id: identity, reference: "b836d3f2", state: "draft" }],
            more: false,
          },
    );
  });
  await env.ui.open();
  all(env.root)
    .find((node) => node.textContent === "Review page")
    .events.click();
  await settle(env.ui);
  let publish = all(env.root).find((node) => node.id === "publish-page");
  assert.equal(publish.disabled, true);
  const frame = all(env.root).find((node) => node.tag === "iframe");
  assert.equal(frame.attrs.sandbox, "");
  assert.equal(frame.attrs.referrerpolicy, "no-referrer");
  assert.equal(frame.src, review.preview_url);
  frame.events.load();
  const check = all(env.root).find((node) => node.id === "publication-consent");
  check.checked = true;
  check.events.change();
  assert.equal(publish.disabled, false);
  publish.events.click();
  await settle(env.ui);
  const requests = calls.filter((call) =>
    call.url.endsWith("publication-consent"),
  );
  assert.equal(requests.length, 1);
  assert.equal(requests[0].payload.token, review.token);
  assert.equal(requests[0].payload.accepted, true);
  assert.equal(requests[0].payload.intent.expires_at, review.intent.expires_at);
  if (status === 503) {
    const retry = all(env.root).find(
      (node) => node.textContent === "Retry the same decision",
    );
    assert.ok(retry);
    retry.events.click();
    await settle(env.ui);
    const decisions = calls.filter((call) =>
      call.url.endsWith("publication-consent"),
    );
    assert.deepEqual(decisions[0].payload, decisions[1].payload);
    assert.ok(
      all(env.root).some((node) =>
        node.textContent?.startsWith("Your consent was recorded"),
      ),
    );
  } else {
    assert.equal(
      all(env.root).some((node) => node.id === "publication-consent"),
      false,
    );
    assert.equal(
      all(env.root).some(
        (node) => node.textContent === "Retry the same decision",
      ),
      false,
    );
  }
  env.ui.clear();
  assert.equal(env.root.children.length, 0);
}
async function stop() {
  const calls = [];
  const current = {
    ...review,
    active: true,
    stop_token: "separate-stop-proof",
    intent: { ...review.intent, expected_active: 1 },
  };
  const env = environment(async (url, options) => {
    const payload = JSON.parse(options.body);
    calls.push(payload);
    return ok(
      payload.action
        ? { recorded: true, action: "suspend" }
        : payload.publication_id
          ? { review: current }
          : {
              pages: [
                { id: identity, reference: "reference", state: "published" },
              ],
            },
    );
  });
  await env.ui.open();
  all(env.root)
    .find((node) => node.textContent === "Review page")
    .events.click();
  await settle(env.ui);
  all(env.root)
    .find((node) => node.textContent === "Stop publication")
    .events.click();
  assert.equal(calls.length, 2);
  all(env.root)
    .find((node) => node.textContent === "Yes, stop public access")
    .events.click();
  await settle(env.ui);
  assert.equal(calls[2].token, current.stop_token);
  assert.equal(calls[2].action, "suspend");
  assert.ok(
    all(env.root).some((node) =>
      node.textContent?.startsWith("Publication stopped"),
    ),
  );
}
async function stale() {
  let finish;
  const env = environment(
    () =>
      new Promise((resolve) => {
        finish = resolve;
      }),
  );
  const open = env.ui.open();
  env.ui.clear();
  finish(
    ok({
      pages: [
        { id: identity, reference: "stale private reference", state: "draft" },
      ],
    }),
  );
  await open;
  assert.equal(env.root.children.length, 0);
}
async function denied() {
  const env = environment(async () => ({ ok: false, status: 401 }));
  await env.ui.open();
  assert.equal(env.denied, 1);
  assert.equal(env.root.children.length, 0);
}
(async () => {
  await scenario(503);
  await scenario(409);
  await stop();
  await stale();
  await denied();
  console.log(
    "Publication UI consent, sandbox, exact retry and stale-response checks PASS",
  );
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
