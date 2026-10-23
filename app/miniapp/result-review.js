"use strict";

window.MiniAppResultReview = function ({ tg, back, denied, chat }) {
  let container,
    lang = "ar",
    orderId = null,
    review = null,
    error = "",
    busy = false;
  let controller = null,
    generation = 0;
  const words = {
    ar: {
      back: "العودة لطلباتي",
      title: "مراجعة النتيجة",
      loading: "جارٍ تحميل المراجعة…",
      reference: "رقم الطلب",
      image: "معاينة الصفحة الأولى",
      scope: "الصورة تعرض الصفحة الأولى فقط، وليست معاينة لجميع صفحات الملف.",
      missing: "تعذر عرض الصورة هنا. استكمل مراجعة الطلب في محادثة البوت.",
      empty: "لا يوجد ملخص نصي لهذه المراجعة. استكملها في محادثة البوت.",
      hint: "الموافقة أو الإلغاء يتمان في البوت. فتح هذه المراجعة لا يغيّر طلبك أو رصيدك.",
      chat: "الموافقة أو الإلغاء في البوت",
      retry: "إعادة المحاولة",
      failure: "تعذر تحميل المراجعة. حاول مجددًا أو استكمل في البوت.",
      changed: "تغيّرت حالة الطلب أو مراجعته. ارجع لطلباتي وحدّث الحالة.",
      rate: "طلبات كثيرة. انتظر دقيقة ثم أعد المحاولة.",
    },
    en: {
      back: "Back to my orders",
      title: "Review result",
      loading: "Loading review…",
      reference: "Order reference",
      image: "First-page preview",
      scope: "The image shows the first page only, not every page of the file.",
      missing:
        "The image could not be displayed here. Continue the review in bot chat.",
      empty: "There is no text summary for this review. Continue in bot chat.",
      hint: "Approve or cancel in bot chat. Opening this review does not change your order or credit.",
      chat: "Approve or cancel in bot",
      retry: "Try again",
      failure: "Could not load the review. Retry or continue in bot chat.",
      changed:
        "The order or review changed. Return to My orders and refresh its status.",
      rate: "Too many requests. Wait a minute and try again.",
    },
  };
  const t = (key) => words[lang][key];
  function el(tag, cls, value) {
    const node = document.createElement(tag);
    if (cls) node.className = cls;
    if (value !== undefined) node.textContent = value;
    return node;
  }
  function button(text, cls, action) {
    const node = el("button", cls, text);
    node.type = "button";
    node.addEventListener("click", action);
    return node;
  }
  function draw() {
    if (!container || !container.isConnected) return;
    const focused = container.contains(document.activeElement);
    container.replaceChildren();
    container.setAttribute("aria-busy", String(busy));
    container.appendChild(button(t("back"), "back-button", back));
    const card = el("section", "card result-review-card");
    const title = el("h2", "section-title", t("title"));
    title.id = "result-review-title";
    title.tabIndex = -1;
    card.appendChild(title);
    if (busy || error) {
      const status = el("p", "availability", t(busy ? "loading" : error));
      status.setAttribute("role", "status");
      card.appendChild(status);
    }
    if (review) {
      card.append(
        el("h3", "", review["name_" + lang]),
        el("p", "mini-label", t("reference")),
        el("bdi", "order-reference", review.reference),
      );
      const text = review["text_" + lang];
      card.appendChild(el("p", "result-review-text", text || t("empty")));
      const image = review.image;
      if (
        typeof image === "string" &&
        image.length <= 4 * 1024 * 1024 + 22 &&
        /^data:image\/png;base64,[A-Za-z0-9+/=]+$/.test(image)
      ) {
        const figure = el("figure", "result-review-image");
        const picture = el("img");
        picture.src = image;
        picture.alt = t("image");
        picture.addEventListener("error", () => {
          figure.replaceChildren(el("figcaption", "sub", t("missing")));
        });
        figure.append(picture, el("figcaption", "sub", t("scope")));
        card.appendChild(figure);
      } else if (review.image_unavailable || image)
        card.appendChild(el("p", "availability", t("missing")));
    }
    if (error && error !== "changed") {
      const retry = button(t("retry"), "secondary", load);
      retry.disabled = busy;
      card.appendChild(retry);
    }
    card.append(el("p", "sub", t("hint")), button(t("chat"), "primary", chat));
    container.appendChild(card);
    if (focused) title.focus();
  }
  async function load() {
    if (busy || !orderId) return;
    busy = true;
    error = "";
    const version = ++generation;
    const requestController = new AbortController();
    controller = requestController;
    const timer = setTimeout(() => requestController.abort(), 20000);
    draw();
    try {
      const response = await fetch("/miniapp/api/result-review", {
        method: "POST",
        credentials: "same-origin",
        cache: "no-store",
        signal: requestController.signal,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ init_data: tg.initData, order_id: orderId }),
      });
      if (version !== generation) return;
      if (response.status === 401 || response.status === 403) {
        denied();
        return;
      }
      if (!response.ok) {
        error = [404, 409].includes(response.status)
          ? "changed"
          : response.status === 429
            ? "rate"
            : "failure";
        if (error === "changed") review = null;
        return;
      }
      const result = await response.json();
      if (version === generation) review = result.review;
    } catch (_) {
      if (version === generation) error = "failure";
    } finally {
      clearTimeout(timer);
      if (version === generation) {
        busy = false;
        controller = null;
        draw();
      }
    }
  }
  return {
    render(node, language) {
      container = node;
      lang = language;
      draw();
    },
    open(id) {
      this.clear();
      orderId = id;
      return load();
    },
    clear() {
      generation++;
      controller?.abort();
      controller = null;
      orderId = null;
      review = null;
      error = "";
      busy = false;
      container?.removeAttribute("aria-busy");
      container = null;
    },
  };
};
