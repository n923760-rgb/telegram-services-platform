"use strict";

window.MiniAppResultReview = function ({ tg, back, denied, chat, orders }) {
  let container,
    lang = "ar",
    orderId = null,
    review = null,
    error = "",
    busy = false;
  let controller = null,
    generation = 0;
  let agreed = false,
    cancelling = false,
    attempted = false,
    retryDecision = null;
  let receipt = null,
    imageReady = false,
    imageFailed = false;
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
      agree: "راجعت الملخص والمعاينة المتاحة وأوافق على المتابعة",
      approvePrepared: "أوافق على إرسال الملفات",
      approveStructure: "أوافق على متابعة التنفيذ",
      nativeHint:
        "المبلغ محجوز مسبقًا لهذا الطلب. الموافقة تتابع الطلب الحالي، والنتائج تصل في البوت.",
      reject: "إلغاء هذا الطلب",
      cancelQuestion: "هل تريد إلغاء الطلب؟ لن تتم متابعة تنفيذه بعد الإلغاء.",
      confirmCancel: "نعم، إلغاء الطلب",
      keep: "العودة للمراجعة",
      approved: "سُجلت موافقتك",
      cancelled: "تم إلغاء الطلب",
      checking:
        "تحقق من الحالة في طلباتي، أو أعد المحاولة بالقرار نفسه. قد يكون القرار سُجل بالفعل.",
      orders: "متابعة طلباتي",
      openChat: "فتح محادثة البوت",
      receiptHint:
        "تابع حالة الطلب في طلباتي. الملفات النهائية تصل في محادثة البوت.",
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
      agree:
        "I reviewed the summary and available preview and agree to continue",
      approvePrepared: "Approve and send files",
      approveStructure: "Approve and continue processing",
      nativeHint:
        "Credit is already reserved for this request. Approval continues the existing order; results arrive in bot chat.",
      reject: "Cancel this request",
      cancelQuestion:
        "Cancel this request? Processing will not continue after cancellation.",
      confirmCancel: "Yes, cancel request",
      keep: "Return to review",
      approved: "Your approval was recorded",
      cancelled: "Request cancelled",
      checking:
        "Check My orders, or retry the same decision. It may already have been recorded.",
      orders: "Follow my orders",
      openChat: "Open bot chat",
      receiptHint:
        "Follow the request in My orders. Final files arrive in bot chat.",
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
    const title = el(
      "h2",
      "section-title",
      t(receipt ? (receipt.approved ? "approved" : "cancelled") : "title"),
    );
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
        /^data:image\/png;base64,[A-Za-z0-9+/=]+$/.test(image) &&
        !imageFailed
      ) {
        const figure = el("figure", "result-review-image");
        const picture = el("img");
        picture.src = image;
        picture.alt = t("image");
        const shown = review,
          version = generation;
        picture.addEventListener("load", () => {
          if (version === generation && review === shown && !imageReady) {
            imageReady = true;
            draw();
          }
        });
        picture.addEventListener("error", () => {
          if (version === generation && review === shown) {
            imageReady = false;
            imageFailed = true;
            draw();
          }
        });
        figure.append(picture, el("figcaption", "sub", t("scope")));
        card.appendChild(figure);
      } else if (review.image_unavailable || image)
        card.appendChild(el("p", "availability", t("missing")));
      if (review.decision) {
        const allowed =
          Boolean(text?.trim()) &&
          (!review.decision.prepared || imageReady) &&
          !imageFailed;
        if (cancelling) {
          card.appendChild(el("p", "availability", t("cancelQuestion")));
          const confirm = button(t("confirmCancel"), "secondary", () =>
            decide({
              token: review.decision.token,
              approved: false,
              accepted: true,
            }),
          );
          confirm.id = "confirm-review-cancel";
          confirm.disabled = busy || attempted;
          const keep = button(t("keep"), "text-button", () => {
            cancelling = false;
            draw();
          });
          keep.disabled = busy || attempted;
          card.append(confirm, keep);
        } else {
          const label = el("label", "confirmation-consent");
          const check = el("input");
          check.type = "checkbox";
          check.id = "review-consent";
          check.checked = agreed;
          check.disabled = busy || attempted || !allowed;
          const approve = button(
            t(
              review.decision.prepared ? "approvePrepared" : "approveStructure",
            ),
            "primary",
            () => {
              if (agreed && allowed && !busy && !attempted)
                decide({
                  token: review.decision.token,
                  approved: true,
                  accepted: true,
                });
            },
          );
          approve.id = "approve-review";
          approve.disabled = busy || attempted || !allowed || !agreed;
          check.addEventListener("change", () => {
            agreed = check.checked;
            approve.disabled = busy || attempted || !allowed || !agreed;
          });
          label.append(check, el("span", "", t("agree")));
          const reject = button(t("reject"), "text-button", () => {
            cancelling = true;
            draw();
          });
          reject.id = "reject-review";
          reject.disabled = busy || attempted;
          card.append(label, approve, reject);
        }
      }
    }
    if (receipt)
      card.append(
        el("p", "mini-label", t("reference")),
        el("bdi", "receipt-reference", receipt.reference),
        el("p", "pill", receipt["status_" + lang]),
      );
    if (error && error !== "changed") {
      const retry = button(t("retry"), "secondary", () =>
        retryDecision ? decide(retryDecision) : load(),
      );
      retry.disabled = busy;
      card.appendChild(retry);
    }
    card.appendChild(
      el(
        "p",
        "sub",
        t(
          attempted && !receipt
            ? "checking"
            : receipt
              ? "receiptHint"
              : review?.decision
                ? "nativeHint"
                : "hint",
        ),
      ),
    );
    if ((receipt || attempted) && orders)
      card.appendChild(button(t("orders"), "primary", orders));
    card.appendChild(
      button(
        t(review?.decision || receipt || attempted ? "openChat" : "chat"),
        "secondary",
        chat,
      ),
    );
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
      if (version === generation) {
        review = result.review;
        agreed = false;
        cancelling = false;
        attempted = false;
        retryDecision = null;
        imageReady = false;
        imageFailed = false;
      }
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
  async function decide(operation) {
    if (busy || !review) return;
    busy = true;
    attempted = true;
    error = "";
    retryDecision = { ...operation };
    const version = ++generation;
    const requestController = new AbortController();
    controller = requestController;
    const timer = setTimeout(() => requestController.abort(), 20000);
    draw();
    try {
      const response = await fetch("/miniapp/api/result-decision", {
        method: "POST",
        credentials: "same-origin",
        cache: "no-store",
        signal: requestController.signal,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ init_data: tg.initData, ...operation }),
      });
      if (version !== generation) return;
      if (response.status === 401 || response.status === 403) {
        denied();
        return;
      }
      if (!response.ok) {
        if ([400, 404, 409].includes(response.status)) {
          review = null;
          retryDecision = null;
          error = "changed";
        } else error = response.status === 429 ? "rate" : "failure";
        return;
      }
      const result = await response.json();
      if (version === generation) {
        receipt = result.receipt;
        review = null;
        retryDecision = null;
        agreed = false;
      }
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
      agreed = false;
      cancelling = false;
      attempted = false;
      retryDecision = null;
      receipt = null;
      imageReady = false;
      imageFailed = false;
      container?.removeAttribute("aria-busy");
      container = null;
    },
  };
};
