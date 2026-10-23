/* Optional developer browser check. Uses Playwright and synthetic overview data only. */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { execFileSync } = require("node:child_process");
const { chromium } = require("playwright");

const root = path.resolve(__dirname, "..");
const snapshot = JSON.parse(
  execFileSync(
    "uv",
    [
      "run",
      "python",
      "-c",
      `
import json
from app.core.models import Service
from app.core.settings import config
from app.miniapp.api import visible_services
from app.services.registry import registry
from app.wallet.ledger import halalas
cfg = config()
cfg.miniapp_bot_username = "ExampleBot"
cfg.admin_ids = []
rows = [Service(slug=p.slug, name_ar=p.name_ar, name_en=p.name_en,
    description_ar=p.description_ar, price_halala=halalas(p.price_sar))
    for p in registry.types.values() if registry.can_request(p.slug)]
print(json.dumps({"language": "ar", "payment_mode": "test_credit", "categories": [],
    "services": visible_services(rows, user_id=4242, stars=False, ai_available=True),
    "orders": [{"reference": "demo0001", "name_ar": "مستند تجريبي", "name_en": "Demo document",
    "status": "completed", "payment_mode": "test_credit", "amount": "3.00",
    "status_ar": "مكتمل", "status_en": "Completed", "created_at": "2026-10-22T10:00:00Z"}],
    "bot_url": "https://t.me/ExampleBot", "orders_window": 8,
    "credit": {"available_sar": "12.00", "reserved_sar": "0.00"}}))
`,
    ],
    {
      cwd: root,
      encoding: "utf8",
      env: {
        ...process.env,
        APP_ENV: "test",
        AI_ENABLED: "false",
        BOT_TOKEN: "123456:TEST_TOKEN_ONLY",
        DATABASE_URL: "postgresql+asyncpg://test:test@127.0.0.1/services_test",
      },
    },
  ),
);

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
      colorScheme: "light",
    });
    const page = await context.newPage();
    const errors = [];
    const requests = [];
    let mode = "ok";
    let releaseFetch;
    page.on("pageerror", (error) => errors.push(error.message));
    await page.addInitScript(() => {
      window.uiTest = { links: [], closed: 0, backVisible: false };
      window.Telegram = {
        WebApp: {
          initData: "synthetic-init-data",
          colorScheme: "light",
          ready() {},
          expand() {},
          close() {
            window.uiTest.closed++;
          },
          openTelegramLink(url) {
            window.uiTest.links.push(url);
          },
          onEvent() {},
          BackButton: {
            show() {
              window.uiTest.backVisible = true;
            },
            hide() {
              window.uiTest.backVisible = false;
            },
            onClick(fn) {
              window.uiTest.back = fn;
            },
          },
        },
      };
    });
    await page.route("**/*", async (route) => {
      const url = new URL(route.request().url());
      const pathname = url.pathname;
      if (pathname === "/miniapp/api/overview") {
        requests.push({
          method: route.request().method(),
          body: route.request().postDataJSON(),
        });
        if (mode === "slow")
          await new Promise((resolve) => {
            releaseFetch = resolve;
          });
        if (["500", "401", "403"].includes(mode))
          return route.fulfill({
            status: Number(mode),
            contentType: "application/json",
            body: "{}",
          });
        const data = structuredClone(snapshot);
        if (mode.startsWith("tracking")) {
          data.orders = [
            "queued",
            "awaiting_payment",
            "waiting_confirmation",
            "processing",
            "delivering",
            "completed",
            "failed",
            "cancelled",
            "refunded",
            "__proto__",
          ].map((status, i) => ({
            reference: "track" + String(i + 1).padStart(3, "0"),
            name_ar: "طلب تجريبي " + (i + 1),
            name_en: "Demo request " + (i + 1),
            status:
              mode === "tracking-updated" && i === 2 ? "completed" : status,
            status_ar: "حالة تجريبية",
            status_en: "Sample status",
            payment_mode: i === 1 ? "stars" : "test_credit",
            amount: i === 1 ? 9 : "3.75",
            created_at: "2026-10-22T22:15:00Z",
          }));
          if (mode === "tracking-unsafe")
            data.bot_url = "https://evil.example/ExampleBot";
          if (mode === "tracking-finished")
            data.orders = data.orders.filter((o) => o.status === "completed");
        }
        if (mode === "empty") {
          data.services = [];
          data.orders = [];
        }
        if (mode === "stars") {
          data.payment_mode = "stars";
          data.credit = null;
          data.services.forEach((s) => {
            s.price = 8;
          });
        }
        if (mode === "paused")
          data.services.forEach((s) => {
            s.ai_unavailable = true;
            s.request_url = null;
          });
        if (mode === "direct")
          data.services.forEach((s) => {
            s.ai_options_unavailable = true;
          });
        if (mode === "unknown") data.services[0].category = "future-category";
        if (mode === "unsafe") {
          data.services[0].name_ar =
            '<img src=x onerror="window.uiUnsafe=true">';
          data.services[0].request_url =
            "https://evil.example/ExampleBot?start=request_csv_review";
          data.services[0].description_ar =
            "<script>window.uiUnsafe=true</script>";
        }
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(data),
        });
      }
      if (
        [
          "/miniapp",
          "/miniapp/app.js",
          "/miniapp/intake.js",
          "/miniapp/styles.css",
        ].includes(pathname)
      ) {
        assert.equal(route.request().method(), "GET");
        const file =
          pathname === "/miniapp" ? "index.html" : pathname.split("/").pop();
        return route.fulfill({
          contentType: file.endsWith(".js")
            ? "application/javascript"
            : file.endsWith(".css")
              ? "text/css"
              : "text/html",
          body: fs.readFileSync(path.join(root, "app/miniapp", file)),
        });
      }
      assert.equal(url.host, "telegram.org", "unexpected external request");
      return route.fulfill({ body: "" });
    });
    async function load() {
      await page.goto("https://miniapp.test/miniapp");
      await page.locator("#notice").waitFor({ state: "hidden" });
    }
    async function noOverflow() {
      assert.equal(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
        true,
      );
    }
    async function allServices() {
      await page
        .getByRole("button", { name: "جميع الخدمات", exact: true })
        .click();
    }

    if (process.env.MINIAPP_TEST_ORDERS === "1") {
      mode = "tracking";
      await load();
      await page.locator('[data-tab="orders"]').click();
      assert.equal(await page.locator(".order-card").count(), 10);
      assert.equal(
        await page.locator("#order-filter-active").innerText(),
        "الجارية · 5",
      );
      assert.equal(
        await page.locator("#order-filter-closed").innerText(),
        "المنتهية · 4",
      );
      const beforeFilter = requests.length;
      await page.locator("#order-filter-active").click();
      assert.equal(await page.locator(".order-card").count(), 5);
      assert.equal(
        await page
          .locator("#order-filter-active")
          .evaluate((el) => el === document.activeElement),
        true,
      );
      await page.locator("#lang").click();
      assert.equal(
        await page.locator("#order-filter-active").getAttribute("aria-pressed"),
        "true",
      );
      const payment = page
        .locator(".order-card")
        .filter({ hasText: "track002" });
      assert.match(
        await payment.locator(".order-amount").innerText(),
        /9 Stars/,
      );
      assert.doesNotMatch(
        await payment.locator(".order-amount").innerText(),
        /SAR|Test credit/,
      );
      assert.match(
        await page
          .locator(".order-card")
          .filter({ hasText: "track001" })
          .locator(".order-amount")
          .innerText(),
        /3.75 SAR · Test credit/,
      );
      await page
        .getByRole("button", { name: "Review result in bot", exact: true })
        .click();
      assert.deepEqual(await page.evaluate(() => window.uiTest.links), [
        "https://t.me/ExampleBot",
      ]);
      assert.equal(
        requests.length,
        beforeFilter,
        "filter, language and chat actions must not mutate or refresh",
      );
      mode = "tracking-updated";
      await page.locator("#refresh-orders").click();
      await page.waitForFunction(
        () =>
          document.getElementById("order-filter-active").textContent ===
          "In progress · 4",
      );
      assert.equal(await page.locator(".order-card").count(), 4);
      assert.equal(
        await page.locator("#order-filter-active").getAttribute("aria-pressed"),
        "true",
      );
      await page.locator("#order-filter-closed").click();
      assert.equal(await page.locator(".order-card").count(), 5);
      assert.match(
        await page
          .locator(".order-card")
          .filter({ hasText: "track007" })
          .locator(".order-next")
          .innerText(),
        /could not finish/,
      );
      await page.locator("#order-filter-all").click();
      assert.match(
        await page
          .locator(".order-card")
          .filter({ hasText: "track010" })
          .locator(".order-next")
          .innerText(),
        /Status unavailable/,
      );
      assert.equal(
        await page
          .locator(".order-card")
          .filter({ hasText: "track010" })
          .locator("button")
          .count(),
        0,
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
            await noOverflow();
            if (width === 390 && process.env.MINIAPP_SCREENSHOT_DIR) {
              fs.mkdirSync(process.env.MINIAPP_SCREENSHOT_DIR, {
                recursive: true,
              });
              await page.screenshot({
                path: path.join(
                  process.env.MINIAPP_SCREENSHOT_DIR,
                  `orders-${language}-${scheme}.png`,
                ),
                fullPage: true,
              });
            }
          }
        }
      }
      mode = "tracking-finished";
      await load();
      await page.locator('[data-tab="orders"]').click();
      await page.locator("#order-filter-active").click();
      assert.equal(await page.locator(".order-card").count(), 0);
      await page
        .getByText("لا توجد طلبات ضمن هذا التصنيف", { exact: true })
        .waitFor();
      mode = "tracking-unsafe";
      await load();
      await page.locator('[data-tab="orders"]').click();
      await page
        .getByRole("button", { name: "راجع النتيجة في البوت", exact: true })
        .click();
      assert.equal(await page.evaluate(() => window.uiTest.closed), 1);
      assert.deepEqual(await page.evaluate(() => window.uiTest.links), []);
      mode = "500";
      await page.locator("#refresh-orders").click();
      await page.locator("#notice.error").waitFor();
      assert.equal(await page.locator(".order-card").count(), 10);
      mode = "401";
      await page.locator("#refresh-orders").click();
      await page.waitForFunction(
        () => document.querySelectorAll(".order-card").length === 0,
      );
      assert.equal(await page.locator(".order-filter").count(), 0);
      assert.deepEqual(errors, []);
      assert.ok(
        requests.every(
          (r) =>
            r.method === "POST" &&
            JSON.stringify(r.body) === '{"init_data":"synthetic-init-data"}',
        ),
      );
      console.log(
        "PASS: synthetic order state filters, focus/language, historical payment, review/result chat-only actions, refreshed transitions, empty/unknown states, unsafe-link fallback, privacy, AR/EN accessibility and light/dark 320/390/768px layouts.",
      );
      return;
    }
    await load();
    assert.equal(await page.locator("[data-group]").count(), 4);
    assert.equal(await page.locator("[data-service]").count(), 0);
    assert.equal(await page.locator("#tabs button").count(), 3);
    assert.equal(await page.evaluate(() => window.uiTest.backVisible), false);
    const serviceCount = snapshot.services.length;
    await allServices();
    assert.equal(await page.locator("[data-service]").count(), serviceCount);
    assert.equal(requests.length, 1, "browsing should not refetch or mutate");
    await page.evaluate(() => window.uiTest.back());
    assert.equal(await page.locator("[data-group]").count(), 4);
    await page.locator('[data-group="files"]').click();
    assert.equal(
      await page.locator("[data-service]").count(),
      snapshot.services.filter((s) => ["documents", "pdf"].includes(s.category))
        .length,
    );
    await page.locator('[data-service="text_to_word_pdf"]').click();
    assert.equal(
      await page
        .locator("#service-back")
        .evaluate((el) => el === document.activeElement),
      true,
    );
    await page.locator("#lang").click();
    assert.equal(await page.locator("html").getAttribute("dir"), "ltr");
    await page
      .getByRole("heading", {
        name: snapshot.services.find((s) => s.slug === "text_to_word_pdf")
          .name_en,
        exact: true,
      })
      .waitFor();
    await page.locator("#service-request").click();
    assert.deepEqual(await page.evaluate(() => window.uiTest.links), [
      "https://t.me/ExampleBot?start=request_text_to_word_pdf",
    ]);
    assert.equal(await page.evaluate(() => window.uiTest.closed), 0);
    await page.evaluate(() => window.uiTest.back());
    assert.equal(
      await page
        .locator('[data-service="text_to_word_pdf"]')
        .evaluate((el) => el === document.activeElement),
      true,
    );
    await page.getByRole("button", { name: "Categories", exact: true }).click();
    assert.equal(
      await page
        .locator('[data-group="files"]')
        .evaluate((el) => el === document.activeElement),
      true,
    );
    await page.locator("#lang").click();
    await page.locator("#service-search").pressSequentially("انشاء");
    assert.equal(
      await page
        .locator("#service-search")
        .evaluate((el) => el === document.activeElement),
      true,
      "typing must keep the keyboard focused",
    );
    assert.ok(
      (await page.locator("[data-service]").count()) > 0,
      "Arabic alef/diacritic normalization",
    );
    await page.locator('[data-service="text_to_pdf"]').click();
    await page.locator("#service-back").click();
    assert.equal(await page.locator("#service-search").inputValue(), "انشاء");
    await page.getByRole("button", { name: "مسح البحث", exact: true }).click();
    await page.locator('[data-group="writing"]').click();
    await page.locator("#service-search").fill("csv");
    await page
      .getByRole("heading", { name: "لم نجد خدمة مطابقة", exact: true })
      .waitFor();
    await page
      .getByRole("button", { name: "البحث في جميع الخدمات", exact: true })
      .click();
    assert.equal(await page.locator("[data-service]").count(), 1);
    await page.locator('[data-service="csv_review"]').waitFor();
    assert.equal(requests.length, 1);
    await page.locator('[data-tab="orders"]').click();
    await page
      .locator(".order-reference")
      .getByText("demo0001", { exact: true })
      .waitFor();
    await page.locator("#lang").click();
    const beforeRefresh = requests.length;
    mode = "slow";
    await page.evaluate(() => {
      document.getElementById("refresh-orders").click();
      document.getElementById("refresh-orders").click();
    });
    await page.waitForFunction(
      () => document.getElementById("refresh-orders").disabled,
    );
    while (!releaseFetch)
      await new Promise((resolve) => setTimeout(resolve, 10));
    assert.equal(requests.length, beforeRefresh + 1);
    mode = "ok";
    releaseFetch();
    await page.locator("#refresh-orders").waitFor();
    await page.waitForFunction(
      () => !document.getElementById("refresh-orders").disabled,
    );
    assert.equal(
      await page.locator("html").getAttribute("lang"),
      "en",
      "refresh preserves chosen language",
    );
    mode = "500";
    await page.locator("#refresh-orders").click();
    await page.locator("#notice.error").waitFor();
    assert.equal(
      await page.locator(".order-reference").innerText(),
      "demo0001",
    );
    mode = "403";
    await page.locator("#refresh-orders").click();
    await page.waitForFunction(
      () => document.querySelectorAll(".order-reference").length === 0,
    );
    assert.equal(await page.locator("#screen").innerText(), "Try again");
    mode = "ok";
    await page.getByRole("button", { name: "Try again", exact: true }).click();
    await page.locator("#refresh-orders").waitFor();

    mode = "direct";
    await load();
    await allServices();
    await page.locator('[data-service="text_to_word_pdf"]').click();
    await page
      .getByText(
        "يمكنك استخدام الخيارات المباشرة. خيارات التحسين متوقفة مؤقتًا.",
        { exact: true },
      )
      .waitFor();
    assert.equal(await page.locator("#service-request").isEnabled(), true);
    mode = "paused";
    await load();
    await allServices();
    await page.locator('[data-service="text_summary"]').click();
    assert.equal(await page.locator("#service-request").count(), 0);
    assert.equal(
      await page
        .getByRole("button", { name: "غير متاحة مؤقتًا", exact: true })
        .isDisabled(),
      true,
    );
    mode = "unknown";
    await load();
    assert.equal(await page.locator('[data-group="other"]').count(), 1);
    mode = "unsafe";
    await load();
    await allServices();
    const unsafeSlug = snapshot.services[0].slug;
    await page.locator(`[data-service="${unsafeSlug}"]`).click();
    assert.equal(await page.locator("#screen img, #screen script").count(), 0);
    assert.equal(await page.evaluate(() => window.uiUnsafe), undefined);
    assert.equal(await page.locator("#service-request").count(), 0);
    mode = "empty";
    await load();
    assert.equal(await page.locator("[data-group]").count(), 0);
    await page.locator('[data-tab="orders"]').click();
    await page
      .getByRole("button", { name: "استكشف الخدمات", exact: true })
      .click();
    mode = "stars";
    await load();
    await allServices();
    await page.locator('[data-service="text_summary"]').click();
    assert.equal(
      await page.locator(".detail-price .price").innerText(),
      "8\nنجمة",
    );
    await page.locator('[data-tab="account"]').click();
    assert.equal(await page.locator(".balance-value").count(), 0);
    await page
      .getByRole("heading", { name: "الدفع بنجوم تيليجرام", exact: true })
      .waitFor();

    mode = "ok";
    for (const colorScheme of ["light", "dark"]) {
      await page.emulateMedia({ colorScheme });
      for (const width of [320, 390, 768]) {
        await page.setViewportSize({ width, height: 844 });
        await load();
        await noOverflow();
        if (width === 390 && process.env.MINIAPP_SCREENSHOT_DIR) {
          fs.mkdirSync(process.env.MINIAPP_SCREENSHOT_DIR, { recursive: true });
          await page.screenshot({
            path: path.join(
              process.env.MINIAPP_SCREENSHOT_DIR,
              `miniapp-home-${colorScheme}.png`,
            ),
            fullPage: true,
          });
        }
        await page.locator('[data-group="files"]').click();
        await noOverflow();
        await page.locator('[data-service="text_to_word_pdf"]').click();
        await noOverflow();
        if (width === 390 && process.env.MINIAPP_SCREENSHOT_DIR)
          await page.screenshot({
            path: path.join(
              process.env.MINIAPP_SCREENSHOT_DIR,
              `miniapp-detail-${colorScheme}.png`,
            ),
            fullPage: true,
          });
        await page.locator("#lang").click();
        await noOverflow();
        await page.locator('[data-tab="account"]').click();
        await noOverflow();
      }
    }
    await page.addInitScript(() => {
      delete window.Telegram;
    });
    const beforeOutside = requests.length;
    await page.goto("https://miniapp.test/miniapp");
    await page
      .getByText("افتح التطبيق من زر القائمة داخل بوت تيليجرام للمتابعة.", {
        exact: true,
      })
      .waitFor();
    await page.locator("#lang").click();
    await page
      .getByText(
        "Open the app from the menu button inside the Telegram bot to continue.",
        { exact: true },
      )
      .waitFor();
    assert.equal(requests.length, beforeOutside);
    assert.ok(
      requests.every(
        (r) =>
          r.method === "POST" &&
          JSON.stringify(r.body) === '{"init_data":"synthetic-init-data"}',
      ),
    );
    assert.deepEqual(errors, []);
    console.log(
      "PASS: browser catalog groups/search, focus/back/language, exact bot handoff, availability, refresh privacy/failure recovery, Stars/empty/unknown/untrusted data, AR/EN light/dark at 320/390/768px. Synthetic Telegram/API only.",
    );
  } finally {
    await browser.close();
  }
}
main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
