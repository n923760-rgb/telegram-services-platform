/* Developer browser qualification with synthetic Telegram and intake responses. */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { chromium } = require("playwright");
const root = path.resolve(__dirname, "..");
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
    async function review(name) {
      if (process.env.MINIAPP_SCREENSHOT_DIR) {
        fs.mkdirSync(process.env.MINIAPP_SCREENSHOT_DIR, { recursive: true });
        await page.screenshot({
          path: path.join(process.env.MINIAPP_SCREENSHOT_DIR, name + ".png"),
          fullPage: true,
        });
      }
      if (process.env.MINIAPP_AXE === "1") {
        const AxeBuilder = require("@axe-core/playwright").default;
        const result = await new AxeBuilder({ page })
          .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
          .analyze();
        assert.deepEqual(
          result.violations.map((v) => ({
            id: v.id,
            nodes: v.nodes.map((n) => n.target),
          })),
          [],
          name,
        );
      }
    }
    const errors = [];
    page.on("pageerror", (error) => errors.push(error.message));
    await page.addInitScript(() => {
      window.testLinks = [];
      window.Telegram = {
        WebApp: {
          initData: "synthetic",
          ready() {},
          expand() {},
          close() {},
          onEvent() {},
          openTelegramLink(url) {
            window.testLinks.push(url);
          },
          BackButton: {
            show() {},
            hide() {},
            onClick(fn) {
              window.testBack = fn;
            },
          },
        },
      };
    });
    let stage = 0,
      count = 0,
      failAfterSave = true,
      reject = false;
    const nativeConfirm = process.env.MINIAPP_TEST_CONFIRM === "1";
    let registered = false,
      confirmationCalls = 0;
    const seen = new Map(),
      requests = [];
    const service = {
      slug: "text_to_word_pdf",
      category: "documents",
      name_ar: "مستند تجريبي",
      name_en: "Demo document",
      description_ar: "وصف الخدمة",
      description_en: "Service description",
      price: "3.00",
      request_url: "https://t.me/ExampleBot?start=request_text_to_word_pdf",
    };
    const overview = {
      language: "ar",
      intake_enabled: true,
      confirmation_enabled: nativeConfirm,
      payment_mode: "test_credit",
      services: [service],
      orders: [],
      credit: { available_sar: "10.00", reserved_sar: "0.00" },
    };
    function view() {
      const field = {
        index: stage,
        kind: stage === 2 ? "image" : "text",
        required: true,
        multiple: stage === 2,
        max_items: 5,
        received: count,
        max_bytes: 1024,
        max_length: 1000,
        single_line: false,
        choices: [],
        skip: { ar: "تخطي", en: "Skip" },
        prompt: { ar: "أدخل بيانات الطلب", en: "Enter request details" },
      };
      if (stage === 1)
        field.choices = [
          {
            value: "yes",
            ar: "موافق على الخيار",
            en: "Choose this option",
            blocked: false,
          },
          {
            value: "blocked",
            ar: "خيار متوقف",
            en: "Paused option",
            blocked: true,
          },
        ];
      return {
        slug: service.slug,
        name_ar: service.name_ar,
        name_en: service.name_en,
        revision: String(stage * 10 + count + 1).padStart(64, "0"),
        ready: stage === 3,
        confirmation:
          stage === 3 && nativeConfirm
            ? { token: "synthetic-review", amount_sar: "3.00" }
            : null,
        editing: false,
        field: stage === 3 ? null : field,
        review:
          stage === 3
            ? {
                ar: "ملخص الطلب\nالسعر التجريبي 3.00 ر.س",
                en: "Request summary\nTest price SAR 3.00",
              }
            : null,
        editable: stage === 3 ? [{ index: 0, ar: "النص", en: "Text" }] : [],
        request_url: service.request_url,
      };
    }
    await page.route("**/*", async (route) => {
      const url = new URL(route.request().url());
      const json = (data, status = 200) =>
        route.fulfill({
          status,
          contentType: "application/json",
          body: JSON.stringify(data),
        });
      if (url.pathname === "/miniapp/api/overview") return json(overview);
      if (url.pathname === "/miniapp/api/confirm") {
        const payload = route.request().postDataJSON();
        assert.deepEqual(payload, {
          init_data: "synthetic",
          token: "synthetic-review",
          accepted: true,
        });
        confirmationCalls++;
        if (!registered) {
          registered = true;
          overview.orders = [
            {
              reference: "demo0002",
              name_ar: service.name_ar,
              name_en: service.name_en,
              status_ar: "في الانتظار",
              status_en: "Queued",
              created_at: "2026-10-23T01:00:00Z",
            },
          ];
          return json({}, 503);
        }
        return json({
          receipt: {
            reference: "demo0002",
            status: "queued",
            status_ar: "في الانتظار",
            status_en: "Queued",
            price_sar: "3.00",
            payment_mode: "test_credit",
          },
        });
      }
      if (url.pathname.startsWith("/miniapp/api/draft")) {
        if (reject) return json({ detail: "not_allowed" }, 403);
        const upload = url.pathname.endsWith("/upload");
        const payload = upload
          ? {
              action: "answer",
              operation: route.request().headers()["x-draft-operation"],
              revision: route.request().headers()["x-draft-revision"],
            }
          : route.request().postDataJSON();
        requests.push({ payload, upload });
        if (upload) {
          assert.equal(
            route.request().headers()["x-telegram-init-data"],
            "synthetic",
          );
          assert.equal(route.request().headers()["content-type"], "image/png");
        } else assert.equal(payload.init_data, "synthetic");
        if (payload.action === "open" || payload.action === "view")
          return json({ draft: view() });
        if (seen.has(payload.operation))
          return json(seen.get(payload.operation));
        assert.equal(payload.revision, view().revision);
        if (payload.action === "edit") {
          stage = payload.index;
          count = 0;
        } else if (payload.action === "done") {
          assert.equal(count, 1);
          stage = 3;
        } else if (stage === 0) {
          assert.equal(payload.value, "Private <script>markup</script>");
          stage = 1;
        } else if (stage === 1) {
          assert.equal(payload.value, "yes");
          stage = 2;
        } else if (stage === 2 && upload) {
          count++;
        } else throw Error("Unexpected write");
        const result = { draft: view() };
        seen.set(payload.operation, result);
        if (failAfterSave) {
          failAfterSave = false;
          return json({}, 503);
        }
        return json(result);
      }
      if (url.host === "telegram.org") return route.fulfill({ body: "" });
      const asset =
        url.pathname === "/miniapp"
          ? "index.html"
          : url.pathname.split("/").pop();
      assert.ok(
        [
          "index.html",
          "app.js",
          "styles.css",
          "intake.js",
          "result-review.js",
        ].includes(asset),
      );
      return route.fulfill({
        contentType: asset.endsWith(".js")
          ? "application/javascript"
          : asset.endsWith(".css")
            ? "text/css"
            : "text/html",
        body: fs.readFileSync(path.join(root, "app/miniapp", asset)),
      });
    });
    await page.goto("https://miniapp.test/miniapp");
    await page.locator('[data-group="files"]').click();
    await page.locator('[data-service="text_to_word_pdf"]').click();
    await page.locator("#service-start").click();
    const input = page.locator("#intake-value");
    await input.fill("Private <script>markup</script>");
    await review("intake-text-ar");
    await page.locator("#lang").click();
    assert.equal(await input.inputValue(), "Private <script>markup</script>");
    await page
      .getByRole("button", { name: "Save and continue", exact: true })
      .click();
    await page
      .getByRole("button", { name: "Try again", exact: true })
      .waitFor();
    await page.getByRole("button", { name: "Try again", exact: true }).click();
    await page
      .getByRole("button", { name: "Choose this option", exact: true })
      .waitFor();
    const mutations = requests.filter((r) => r.payload.action === "answer");
    await review("intake-choice-en");
    assert.equal(
      mutations[0].payload.operation,
      mutations[1].payload.operation,
      "retry must reuse the same operation",
    );
    assert.equal(
      await page.getByRole("button", { name: /Paused option/ }).isDisabled(),
      true,
    );
    await page
      .getByRole("button", { name: "Choose this option", exact: true })
      .click();
    await input.setInputFiles({
      name: "input.png",
      mimeType: "image/png",
      buffer: Buffer.from("synthetic-image-bytes"),
    });
    await page.getByText("Uploaded files: 1 / 5", { exact: true }).waitFor();
    await review("intake-file-en");
    await page
      .getByRole("button", { name: "Done adding files", exact: true })
      .click();
    if (nativeConfirm) {
      await page.locator("#confirm-request").waitFor();
      assert.equal(confirmationCalls, 0, "opening a review must not submit");
      assert.equal(await page.locator("#confirm-request").isDisabled(), true);
      await page.locator("#confirm-consent").check();
      await review("confirmation-consent");
      await page.locator("#lang").click();
      assert.equal(await page.locator("#confirm-consent").isChecked(), true);
      await page.locator("#lang").click();
      await page.locator("#confirm-request").click();
      await page
        .getByRole("button", { name: "Try again", exact: true })
        .waitFor();
      assert.equal(await page.locator("#confirm-request").isDisabled(), true);
      assert.equal(await page.locator(".intake-edit").count(), 0);
      assert.equal(
        (await page.locator(".fine-print").innerText()).includes(
          "have not started",
        ),
        false,
        "uncertain confirmation cannot claim no reservation",
      );
      await page
        .getByRole("button", { name: "Try again", exact: true })
        .click();
      await page
        .getByRole("heading", {
          name: "Your request is registered",
          exact: true,
        })
        .waitFor();
      assert.equal(confirmationCalls, 2);
      assert.equal(
        await page.locator(".receipt-reference").innerText(),
        "demo0002",
      );
      assert.equal(await page.locator("#confirm-request").count(), 0);
      assert.deepEqual(await page.evaluate(() => window.testLinks), []);
      for (const scheme of ["light", "dark"]) {
        await page.emulateMedia({ colorScheme: scheme });
        await review("confirmation-receipt-" + scheme);
        for (const width of [320, 390, 768]) {
          await page.setViewportSize({ width, height: 844 });
          assert.equal(
            await page.evaluate(
              () => document.documentElement.scrollWidth <= innerWidth,
            ),
            true,
          );
        }
      }
      await page
        .getByRole("button", { name: "Follow my orders", exact: true })
        .click();
      await page
        .locator(".order-reference")
        .getByText("demo0002", { exact: true })
        .waitFor();
      assert.deepEqual(errors, []);
      console.log(
        "PASS: synthetic explicit test-credit consent, no purchase on review, exact confirmation payload, ambiguous-success retry, receipt/Orders, AR/EN preservation and light/dark responsive receipt.",
      );
      return;
    }
    await page
      .getByRole("button", { name: "Review and confirm in bot", exact: true })
      .click();
    assert.deepEqual(await page.evaluate(() => window.testLinks), [
      service.request_url,
    ]);
    assert.equal(await page.locator("#screen script").count(), 0);
    for (const scheme of ["light", "dark"]) {
      await page.emulateMedia({ colorScheme: scheme });
      await review("intake-review-" + scheme);
      for (const width of [320, 390, 768]) {
        await page.setViewportSize({ width, height: 844 });
        assert.equal(
          await page.evaluate(
            () => document.documentElement.scrollWidth <= innerWidth,
          ),
          true,
        );
      }
    }
    await page.locator(".intake-edit summary").click();
    await page.getByRole("button", { name: "Text", exact: true }).click();
    await input.fill("Private <script>markup</script>");
    reject = true;
    await page
      .getByRole("button", { name: "Save and continue", exact: true })
      .click();
    await page
      .getByText(
        "Cannot access this account. Open bot chat and send /start, or contact support.",
        {
          exact: true,
        },
      )
      .waitFor();
    assert.equal(
      await page.locator("#intake-value").count(),
      0,
      "authentication rejection must remove private input",
    );
    await page.locator("#lang").click();
    await page
      .getByText(
        "تعذر الوصول للحساب. افتح محادثة البوت وأرسل /start، أو تواصل مع الدعم.",
        { exact: true },
      )
      .waitFor();
    assert.deepEqual(errors, []);
    assert.ok(
      requests.every((r) =>
        ["view", "open", "answer", "done", "edit"].includes(r.payload.action),
      ),
    );
    console.log(
      "PASS: synthetic intake text/language, idempotent retry, blocked choices, upload/count/done, review/edit, exact bot link, private-data removal, AR/EN and 320/390/768px light/dark overflow. No purchase endpoint.",
    );
  } finally {
    await browser.close();
  }
}
main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
