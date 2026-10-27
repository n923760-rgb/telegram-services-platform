// Exercise the actual intake controller with a minimal DOM and HTTP responses.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

class Element {
  constructor(tag) { this.tag = tag; this.children = []; this.events = {}; this.isConnected = true; }
  append(...nodes) { this.children.push(...nodes); }
  appendChild(node) { this.append(node); return node; }
  replaceChildren(...nodes) { this.children = nodes; }
  setAttribute() {}
  removeAttribute() {}
  addEventListener(name, fn) { this.events[name] = fn; }
  focus() {}
}
function all(node) { return [node, ...node.children.flatMap(all)]; }
async function settle(controller) {
  for (let i = 0; i < 50 && controller.busy; i++)
    await new Promise(resolve => setImmediate(resolve));
  assert.equal(controller.busy, false);
}

async function scenario(status, detail) {
  const root = new Element("main");
  const calls = [];
  const draft = {
    ready: true, name_en: "QR codes", revision: "revision",
    review: { en: "Review" }, editable: [{ index: 0, en: "Content" }],
    confirmation: { token: "same-owner-bound-token", amount_sar: "3.00" },
  };
  const context = {
    window: {}, Uint8Array, crypto: require("node:crypto").webcrypto,
    document: {
      createElement: tag => new Element(tag),
      getElementById: id => all(root).find(node => node.id === id),
    },
    fetch: async (url, options) => {
      calls.push({ url, body: JSON.parse(options.body) });
      if (url.endsWith("/confirm"))
        return { ok: false, status, json: async () => ({ detail }) };
      return { ok: true, json: async () => ({ draft }) };
    },
  };
  vm.runInNewContext(fs.readFileSync("app/miniapp/intake.js", "utf8"), context);
  const controller = context.window.MiniAppIntake({ tg: { initData: "signed" }, exit() {} });
  controller.render(root, "en");
  await controller.open("qr_codes");
  const consent = all(root).find(node => node.id === "confirm-consent");
  consent.checked = true;
  consent.events.change();
  all(root).find(node => node.id === "confirm-request").events.click();
  await settle(controller);
  assert.equal(calls.length, 2);
  const checkbox = all(root).find(node => node.id === "confirm-consent");
  if (status === 409) {
    assert.equal(checkbox.checked, false);
    assert.equal(checkbox.disabled, false);
    assert(all(root).some(node => node.textContent === "Edit details"));
    assert.equal(all(root).find(node => node.id === "confirm-request").disabled, true);
    const notice = all(root).find(node => node.className === "availability").textContent;
    assert.equal(notice, detail === "input_invalid"
      ? "Check the field value or file type and size, then try again."
      : "The draft or service terms changed. Refresh it or continue in bot chat.");
  } else {
    assert.equal(checkbox.disabled, true);
    assert(!all(root).some(node => node.textContent === "Edit details"));
    all(root).find(node => node.textContent === "Try again").events.click();
    await settle(controller);
    assert.deepEqual(calls[2], calls[1]);
  }
}
(async () => {
  await scenario(409, "input_invalid");
  await scenario(409, "stale_button");
  await scenario(503, "input_retry");
  console.log("Intake rejection correction and uncertain retry: PASS");
})().catch(error => { console.error(error); process.exitCode = 1; });
