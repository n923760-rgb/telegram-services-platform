/* Synthetic, owner-authenticated review UI. No provider, Telegram or payment call. */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { execFileSync } = require("node:child_process");
const { chromium } = require("playwright");
const root = path.resolve(__dirname, "..");
const id = "12345678-0000-4000-8000-000000000001";
const native = process.env.MINIAPP_TEST_DECISION === "1";
const image =
  "data:image/png;base64," +
  execFileSync(
    "uv",
    [
      "run",
      "python",
      "-c",
      `
import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
p=Image.new("RGB",(480,680),"white")
d=ImageDraw.Draw(p)
d.text((36,40),"SYNTHETIC FIRST PAGE",font=ImageFont.load_default(size=25),fill="black")
d.text((36,100),"Reference 00123",font=ImageFont.load_default(size=22),fill="black")
d.text((36,150),"Amount 125.50",font=ImageFont.load_default(size=22),fill="black")
b=BytesIO(); p.save(b,format="PNG")
print(base64.b64encode(b.getvalue()).decode())
`,
    ],
    { cwd: root, encoding: "utf8" },
  ).trim();
async function main() {
  const browser = await chromium.launch({
    headless: true,
    ...(process.env.MINIAPP_CHROMIUM_PATH
      ? { executablePath: process.env.MINIAPP_CHROMIUM_PATH }
      : {}),
    args: process.env.MINIAPP_CHROMIUM_ARGS
      ? JSON.parse(process.env.MINIAPP_CHROMIUM_ARGS)
      : ["--no-sandbox", "--disable-dev-shm-usage"],
  });
  try {
    const context = await browser.newContext({
      viewport: { width: 390, height: 844 },
    });
    const page = await context.newPage();
    const errors = [],
      requests = [];
    let mode = "ok",
      release,
      releaseOverview;
    page.on("pageerror", (e) => errors.push(e.message));
    await page.addInitScript(() => {
      window.testResult = { links: [] };
      window.Telegram = {
        WebApp: {
          initData: "synthetic",
          ready() {},
          expand() {},
          close() {},
          onEvent() {},
          openTelegramLink(url) {
            window.testResult.links.push(url);
          },
          BackButton: {
            show() {
              window.testResult.backVisible = true;
            },
            hide() {
              window.testResult.backVisible = false;
            },
            onClick(fn) {
              window.testResult.back = fn;
            },
          },
        },
      };
    });
    await page.route("**/*", async (route) => {
      const url = new URL(route.request().url());
      if (url.pathname.startsWith("/miniapp/api/")) {
        const payload = route.request().postDataJSON();
        requests.push({ path: url.pathname, payload });
        const json = (data, status = 200) =>
          route.fulfill({
            status,
            contentType: "application/json",
            body: JSON.stringify(data),
          });
        if (url.pathname === "/miniapp/api/overview") {
          assert.deepEqual(payload, { init_data: "synthetic" });
          if (mode === "slow-overview")
            await new Promise((resolve) => {
              releaseOverview = resolve;
            });
          return json({
            language: "ar",
            intake_enabled: true,
            payment_mode: "test_credit",
            services: [],
            categories: [],
            bot_url: "https://t.me/ExampleBot",
            orders_window: 8,
            credit: { available_sar: "9.00", reserved_sar: "1.00" },
            orders: [
              {
                reference: "12345678",
                review_id: id,
                status: "waiting_confirmation",
                name_ar: "مستند تجريبي",
                name_en: "Demo document",
                status_ar: "بانتظار المراجعة",
                status_en: "Waiting for review",
                created_at: "2026-10-23T01:00:00Z",
                payment_mode: "test_credit",
                amount: "1.00",
              },
            ],
          });
        }
        if (native && url.pathname === "/miniapp/api/result-decision") {
          assert.deepEqual(Object.keys(payload).sort(), [
            "accepted",
            "approved",
            "init_data",
            "token",
          ]);
          assert.equal(payload.token, "synthetic-result-proof");
          assert.equal(payload.accepted, true);
          assert.equal(payload.init_data, "synthetic");
          if (["401", "403", "409", "500", "429"].includes(mode))
            return json({}, Number(mode));
          if (mode === "decision-slow")
            await new Promise((resolve) => {
              release = resolve;
            });
          return json({
            receipt: {
              reference: "12345678",
              approved: payload.approved,
              status_ar: payload.approved ? "قيد التنفيذ" : "ملغي",
              status_en: payload.approved ? "Queued" : "Cancelled",
            },
          });
        }
        assert.equal(
          url.pathname,
          "/miniapp/api/result-review",
          "review must never submit or decide an order",
        );
        assert.deepEqual(payload, { init_data: "synthetic", order_id: id });
        if (["401", "403", "409", "500", "429"].includes(mode))
          return json({}, Number(mode));
        const review = {
          reference: "12345678",
          name_ar: "مستند تجريبي",
          name_en: "Demo document",
          text_ar:
            "ملخص المراجعة الكامل\nالمرجع 00123 والمبلغ 125.50\nراجع البيانات قبل الموافقة في البوت.",
          text_en:
            "Full review summary\nReference 00123 and amount 125.50\n<img src=x onerror=window.unsafeResult=true>",
          image,
          image_unavailable: false,
          ...(native
            ? {
                decision: {
                  token: "synthetic-result-proof",
                  prepared: mode !== "structural",
                },
              }
            : {}),
        };
        if (mode === "missing") {
          review.image = null;
          review.image_unavailable = true;
        }
        if (mode === "structural") review.image = null;
        if (mode === "broken") review.image = "data:image/png;base64,AA==";
        if (mode === "empty") {
          review.text_ar = "";
          review.text_en = "";
        }
        if (mode === "unsafe")
          review.image = "https://evil.example/private.png";
        if (mode === "full")
          review.text_en = "A".repeat(49980) + "END OF REVIEW";
        if (mode === "slow") {
          review.text_en = "OLD RESPONSE MUST NOT RETURN";
          await new Promise((resolve) => {
            release = resolve;
          });
        }
        try {
          return await json({ review });
        } catch (error) {
          if (!route.request().failure()) throw error;
        }
        return;
      }
      if (url.hostname === "telegram.org") return route.fulfill({ body: "" });
      assert.equal(
        url.hostname,
        "miniapp.test",
        "no external preview requests",
      );
      const file =
        url.pathname === "/miniapp"
          ? "index.html"
          : url.pathname.split("/").pop();
      assert.ok(
        [
          "index.html",
          "app.js",
          "intake.js",
          "result-review.js",
          "styles.css",
        ].includes(file),
      );
      return route.fulfill({
        contentType: file.endsWith(".js")
          ? "application/javascript"
          : file.endsWith(".css")
            ? "text/css"
            : "text/html",
        body: fs.readFileSync(path.join(root, "app/miniapp", file)),
      });
    });
    async function load() {
      await page.goto("https://miniapp.test/miniapp");
      await page.locator("#notice").waitFor({ state: "hidden" });
      await page.locator('[data-tab="orders"]').click();
      await page.locator("#order-filter-active").click();
    }
    async function open() {
      await page.locator('[id^="review-order-"]').click();
    }
    async function ready() {
      await page.locator(".result-review-text").waitFor();
    }
    async function back() {
      await page.evaluate(() => window.testResult.back());
    }
    if (native) {
      const decisions = () =>
        requests.filter((r) => r.path.endsWith("/result-decision"));
      await load();
      await open();
      await ready();
      assert.equal(decisions().length, 0);
      assert.equal(await page.locator("#approve-review").isDisabled(), true);
      await page.locator("#review-consent").check();
      await page.locator("#lang").click();
      assert.equal(await page.locator("#review-consent").isChecked(), true);
      for (const width of [320, 390, 768]) {
        await page.setViewportSize({ width, height: 844 });
        assert.equal(
          await page.evaluate(
            () => document.documentElement.scrollWidth <= innerWidth,
          ),
          true,
        );
      }
      await page.setViewportSize({ width: 390, height: 844 });
      if (process.env.MINIAPP_SCREENSHOT_DIR) {
        fs.mkdirSync(process.env.MINIAPP_SCREENSHOT_DIR, { recursive: true });
        await page.screenshot({
          path: path.join(
            process.env.MINIAPP_SCREENSHOT_DIR,
            "native-review-en.png",
          ),
          fullPage: true,
        });
      }
      if (process.env.MINIAPP_AXE === "1") {
        const AxeBuilder = require("@axe-core/playwright").default;
        assert.deepEqual(
          (
            await new AxeBuilder({ page })
              .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
              .analyze()
          ).violations,
          [],
        );
      }
      await page.locator("#approve-review").click();
      await page
        .getByText("Your approval was recorded", { exact: true })
        .waitFor();
      assert.equal(decisions().length, 1);
      await page
        .getByRole("button", { name: "Follow my orders", exact: true })
        .click();
      await open();
      await ready();
      await page.locator("#reject-review").click();
      assert.equal(decisions().length, 1);
      await page.locator("#confirm-review-cancel").click();
      await page.getByText("Request cancelled", { exact: true }).waitFor();
      assert.equal(decisions().at(-1).payload.approved, false);
      for (const state of ["broken", "empty"]) {
        mode = state;
        await load();
        await open();
        await ready();
        await page.waitForTimeout(100);
        assert.equal(await page.locator("#approve-review").isDisabled(), true);
      }
      mode = "structural";
      await load();
      await open();
      await ready();
      await page.locator("#review-consent").check();
      mode = "500";
      await page.locator("#approve-review").click();
      await page
        .getByRole("button", { name: "إعادة المحاولة", exact: true })
        .waitFor();
      const frozen = decisions().at(-1).payload;
      assert.equal(await page.locator("#reject-review").isDisabled(), true);
      mode = "409";
      await page
        .getByRole("button", { name: "إعادة المحاولة", exact: true })
        .click();
      await page
        .getByText("تغيّرت حالة الطلب أو مراجعته. ارجع لطلباتي وحدّث الحالة.", {
          exact: true,
        })
        .waitFor();
      assert.deepEqual(decisions().at(-1).payload, frozen);
      assert.equal(await page.locator("#approve-review").count(), 0);
      mode = "structural";
      await load();
      await open();
      await ready();
      await page.locator("#review-consent").check();
      mode = "decision-slow";
      await page.locator("#approve-review").click();
      while (!release) await new Promise((resolve) => setTimeout(resolve, 10));
      await back();
      release();
      await page.waitForTimeout(100);
      assert.equal(await page.locator(".receipt-reference").count(), 0);
      mode = "structural";
      await open();
      await ready();
      await page.locator("#review-consent").check();
      mode = "403";
      await page.locator("#approve-review").click();
      await page
        .getByRole("button", { name: "إعادة المحاولة", exact: true })
        .waitFor();
      assert.equal(
        await page.locator(".result-review-card, .order-card").count(),
        0,
      );
      assert.deepEqual(errors, []);
      console.log(
        "PASS: native consent, prepared approval, two-step cancellation, AR/EN, accessibility, broken/empty preview, frozen ambiguous retry, stale proof, late response and auth privacy.",
      );
      return;
    }
    await load();
    await open();
    await ready();
    assert.equal(
      await page.evaluate(() => window.testResult.backVisible),
      true,
    );
    assert.equal(
      await page
        .locator("#result-review-title")
        .evaluate((el) => el === document.activeElement),
      true,
    );
    assert.equal(
      await page
        .locator(".result-review-image img")
        .evaluate((el) => el.complete && el.naturalWidth > 0),
      true,
    );
    const beforeLanguage = requests.length;
    await page.locator("#lang").click();
    assert.match(
      await page.locator(".result-review-text").innerText(),
      /Reference 00123 and amount 125.50/,
    );
    assert.equal(await page.locator(".result-review-text img").count(), 0);
    assert.equal(await page.evaluate(() => window.unsafeResult), undefined);
    assert.equal(
      requests.length,
      beforeLanguage,
      "language must not reload private content",
    );
    for (const scheme of ["light", "dark"]) {
      await page.emulateMedia({ colorScheme: scheme });
      for (const language of ["en", "ar"]) {
        if ((await page.locator("html").getAttribute("lang")) !== language)
          await page.locator("#lang").click();
        if (process.env.MINIAPP_AXE === "1") {
          const AxeBuilder = require("@axe-core/playwright").default;
          const result = await new AxeBuilder({ page })
            .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
            .analyze();
          assert.deepEqual(
            result.violations.map((v) => ({
              id: v.id,
              targets: v.nodes.map((n) => n.target),
            })),
            [],
          );
        }
        for (const width of [320, 390, 768]) {
          await page.setViewportSize({ width, height: 844 });
          assert.equal(
            await page.evaluate(
              () => document.documentElement.scrollWidth <= innerWidth,
            ),
            true,
          );
          if (width === 390 && process.env.MINIAPP_SCREENSHOT_DIR) {
            fs.mkdirSync(process.env.MINIAPP_SCREENSHOT_DIR, {
              recursive: true,
            });
            await page.screenshot({
              path: path.join(
                process.env.MINIAPP_SCREENSHOT_DIR,
                `review-${language}-${scheme}.png`,
              ),
              fullPage: true,
            });
          }
        }
      }
    }
    await page
      .getByRole("button", {
        name: "الموافقة أو الإلغاء في البوت",
        exact: true,
      })
      .click();
    assert.deepEqual(await page.evaluate(() => window.testResult.links), [
      "https://t.me/ExampleBot",
    ]);
    await back();
    assert.equal(
      await page.locator("#order-filter-active").getAttribute("aria-pressed"),
      "true",
    );
    assert.equal(
      await page
        .locator('[id^="review-order-"]')
        .evaluate((el) => el === document.activeElement),
      true,
    );
    for (const scenario of ["missing", "unsafe", "structural", "full"]) {
      mode = scenario;
      await open();
      await ready();
      if (scenario === "full") {
        await page.locator("#lang").click();
        assert.equal(
          (await page.locator(".result-review-text").innerText()).length,
          49993,
        );
        assert.match(
          await page.locator(".result-review-text").innerText(),
          /END OF REVIEW$/,
        );
        await page.locator("#lang").click();
      } else
        assert.equal(await page.locator(".result-review-image img").count(), 0);
      await back();
    }
    mode = "slow";
    await open();
    await page.getByText("جارٍ تحميل المراجعة…", { exact: true }).waitFor();
    while (!release) await new Promise((r) => setTimeout(r, 10));
    await back();
    mode = "ok";
    await open();
    await ready();
    release();
    await page.waitForTimeout(100);
    assert.doesNotMatch(
      await page.locator(".result-review-text").innerText(),
      /OLD RESPONSE/,
    );
    await back();
    mode = "500";
    await open();
    await page
      .getByRole("button", { name: "إعادة المحاولة", exact: true })
      .waitFor();
    mode = "ok";
    await page
      .getByRole("button", { name: "إعادة المحاولة", exact: true })
      .click();
    await ready();
    await back();
    mode = "409";
    await open();
    await page
      .getByText("تغيّرت حالة الطلب أو مراجعته. ارجع لطلباتي وحدّث الحالة.", {
        exact: true,
      })
      .waitFor();
    assert.equal(
      await page
        .locator(".result-review-image img, .result-review-text")
        .count(),
      0,
    );
    await back();
    mode = "slow-overview";
    await page.locator("#refresh-orders").click();
    while (!releaseOverview)
      await new Promise((resolve) => setTimeout(resolve, 10));
    mode = "401";
    await open();
    await page
      .getByRole("button", { name: "إعادة المحاولة", exact: true })
      .waitFor();
    releaseOverview();
    await page.waitForTimeout(100);
    assert.equal(
      await page.locator(".order-card, .result-review-card").count(),
      0,
      "a stale overview must never restore private data after review authentication fails",
    );
    mode = "ok";
    await load();
    for (const code of ["401", "403"]) {
      mode = code;
      await open();
      await page
        .getByRole("button", { name: "إعادة المحاولة", exact: true })
        .waitFor();
      assert.equal(
        await page
          .locator(".result-review-card, .order-card, .order-filter")
          .count(),
        0,
      );
      mode = "ok";
      await load();
    }
    assert.deepEqual(errors, []);
    console.log(
      "PASS: synthetic read-only review, owner payload, full text/PNG, AR/EN preservation, first-page scope, safe images, focus/back/filter restoration, aborted/late responses, retry/stale/auth privacy and responsive accessible themes. No decision/payment endpoint.",
    );
  } finally {
    await browser.close();
  }
}
main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
