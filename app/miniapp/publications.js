"use strict";

window.MiniAppPublications = function ({ tg, back, denied }) {
  let root,
    lang = "ar",
    rows = [],
    more = false,
    review = null,
    identity = null;
  let busy = false,
    error = "",
    recorded = false,
    agreed = false,
    pending = null;
  let suspending = false,
    outcome = "saved";
  let generation = 0,
    controller = null;
  const words = {
    ar: {
      title: "صفحاتي",
      back: "العودة للحساب",
      list: "العودة للصفحات",
      loading: "جارٍ التحميل…",
      empty: "لا توجد صفحات جاهزة للمراجعة.",
      limit: "تظهر أحدث 20 صفحة فقط.",
      view: "مراجعة الصفحة",
      preview: "معاينة الصفحة كاملة",
      links: "مراجعة روابط التواصل",
      linkHint:
        "المعاينة معزولة للحماية. يمكنك اختبار روابط التواصل من هذه القائمة.",
      missing:
        "تعذّر عرض المعاينة. حدّث الحالة قبل الموافقة على النشر. يمكنك إيقاف النسخة المنشورة.",
      terms: "شروط الاستضافة والنشر",
      until: "الاستضافة حتى",
      agree: "راجعت الصفحة وبياناتها والشروط، وأوافق على نشر هذه النسخة للعامة",
      publish: "أوافق على النشر",
      active: "هذه النسخة منشورة",
      open: "فتح الصفحة العامة",
      saved: "سُجلت موافقتك. حدّث الحالة للتحقق من النسخة المنشورة.",
      previous: "النسخة السابقة ما زالت منشورة حتى توافق على هذه التعديلات.",
      stop: "إيقاف النشر",
      stopConfirm: "نعم، إيقاف ظهور الصفحة للعامة",
      keep: "العودة للمراجعة",
      stopped: "أُوقف النشر. حدّث الحالة للتحقق.",
      refresh: "تحديث الحالة",
      failure: "تعذر إكمال الطلب. أعد المحاولة.",
      changed: "تغيّرت المراجعة أو أصبحت غير متاحة. حدّث الحالة قبل المتابعة.",
      uncertain:
        "قد تكون الموافقة سُجلت. أعد المحاولة بنفس القرار أو حدّث الحالة.",
      retry: "إعادة المحاولة بنفس القرار",
      draft: "مسودة",
      changes: "تعديلات بانتظار النشر",
      published: "منشورة",
      suspended: "موقوفة",
      expired: "انتهت الاستضافة",
    },
    en: {
      title: "My pages",
      back: "Back to account",
      list: "Back to pages",
      loading: "Loading…",
      empty: "No pages are ready for review.",
      limit: "Only the latest 20 pages are shown.",
      view: "Review page",
      preview: "Complete page preview",
      links: "Review contact links",
      linkHint:
        "The preview is isolated for safety. Test contact links from this list.",
      missing:
        "Preview unavailable. Refresh before approving publication. You can still stop the published version.",
      terms: "Hosting and publication terms",
      until: "Hosting expires",
      agree:
        "I reviewed the page, its data and the terms, and consent to making this version public",
      publish: "Approve publication",
      active: "This version is published",
      open: "Open public page",
      saved:
        "Your consent was recorded. Refresh to check the published version.",
      previous:
        "The previous version stays public until you approve these changes.",
      stop: "Stop publication",
      stopConfirm: "Yes, stop public access",
      keep: "Return to review",
      stopped: "Publication stopped. Refresh to check its status.",
      refresh: "Refresh status",
      failure: "Could not complete the request. Try again.",
      changed:
        "The review changed or became unavailable. Refresh before continuing.",
      uncertain:
        "Consent may already be recorded. Retry the same decision or refresh status.",
      retry: "Retry the same decision",
      draft: "Draft",
      changes: "Changes awaiting publication",
      published: "Published",
      suspended: "Suspended",
      expired: "Hosting expired",
    },
  };
  const t = (key) => words[lang][key] || key;
  function el(tag, text, cls) {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = text;
    if (cls) node.className = cls;
    return node;
  }
  function button(key, action, cls = "secondary") {
    const node = el("button", t(key), cls);
    node.type = "button";
    node.disabled = busy;
    node.addEventListener("click", action);
    return node;
  }
  function draw() {
    if (!root?.isConnected) return;
    root.replaceChildren();
    root.setAttribute("aria-busy", String(busy));
    root.appendChild(
      button(
        review || identity ? "list" : "back",
        () => (review || identity ? request(null) : back()),
        "back-button",
      ),
    );
    const card = el("section", undefined, "card publication-review");
    const heading = el("h2", t("title"), "section-title");
    heading.tabIndex = -1;
    card.appendChild(heading);
    if (busy || error || recorded) {
      const status = el(
        "p",
        t(busy ? "loading" : error || outcome),
        "availability",
      );
      status.setAttribute("role", "status");
      card.appendChild(status);
    }
    if (review) {
      const expiry = el(
        "time",
        new Date(review.intent.expires_at).toLocaleString(
          lang === "ar" ? "ar-SA" : "en-GB",
          {
            calendar: "gregory",
            year: "numeric",
            month: "long",
            day: "numeric",
            hour: "2-digit",
            minute: "2-digit",
            timeZoneName: "short",
          },
        ),
        "publication-copy",
      );
      expiry.dateTime = review.intent.expires_at;
      card.append(el("h3", t("until")), expiry);
      card.append(el("p", review.terms["notice_" + lang], "availability"));
      const frame = el("iframe", undefined, "publication-preview");
      frame.setAttribute("sandbox", "");
      frame.setAttribute("referrerpolicy", "no-referrer");
      frame.title = t("preview");
      let loaded = false;
      const shown = review,
        version = generation;
      const label = el("label", undefined, "confirmation-consent");
      const check = el("input");
      check.type = "checkbox";
      check.id = "publication-consent";
      check.checked = agreed;
      check.disabled = true;
      const publish = button(
        "publish",
        () => {
          if (
            !loaded ||
            !review.token ||
            !agreed ||
            busy ||
            pending ||
            review.active
          )
            return;
          if (!globalThis.crypto?.randomUUID) {
            error = "failure";
            draw();
            return;
          }
          pending = {
            token: review.token,
            intent: review.intent,
            accepted: true,
            operation_id: crypto.randomUUID(),
          };
          request(identity, pending);
        },
        "primary",
      );
      publish.id = "publish-page";
      publish.disabled = true;
      check.addEventListener("change", () => {
        agreed = check.checked;
        publish.disabled = !loaded || !agreed || busy || !!pending;
      });
      frame.addEventListener("load", () => {
        if (version !== generation || shown !== review || !frame.isConnected)
          return;
        loaded = true;
        check.disabled = busy || !!pending || review.active;
        publish.disabled = busy || !!pending || review.active || !agreed;
      });
      if (review.preview_url) {
        frame.src = review.preview_url;
        card.appendChild(frame);
      } else card.appendChild(el("p", t("missing"), "availability"));
      card.append(
        el("h3", t("terms")),
        el("p", review.terms[lang], "publication-copy"),
      );
      if (Array.isArray(review.links) && review.links.length) {
        const links = el("details", undefined, "publication-links");
        links.append(el("summary", t("links")), el("p", t("linkHint"), "sub"));
        for (const item of review.links.slice(0, 6)) {
          if (typeof item.url !== "string" || !item.url.startsWith("https://"))
            continue;
          const link = el("a", `${item.label} — ${item.url}`, "secondary");
          link.href = item.url;
          link.target = "_blank";
          link.rel = "noopener noreferrer";
          links.appendChild(link);
        }
        card.appendChild(links);
      }
      if (review.active && review.preview_url) {
        card.appendChild(el("p", t("active"), "pill"));
        const link = el("a", t("open"), "secondary");
        link.href = review.public_url;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        card.appendChild(link);
      } else if (!review.active) {
        if (review.intent.expected_active !== null)
          card.appendChild(el("p", t("previous"), "availability"));
        label.append(check, el("span", t("agree")));
        card.append(label, publish);
      }
      if (review.stop_token && !pending) {
        if (!suspending)
          card.appendChild(
            button(
              "stop",
              () => {
                suspending = true;
                draw();
              },
              "text-button",
            ),
          );
        else {
          card.appendChild(
            button("stopConfirm", () => {
              if (busy || pending || !globalThis.crypto?.randomUUID) return;
              pending = {
                token: review.stop_token,
                intent: review.intent,
                accepted: true,
                action: "suspend",
                operation_id: crypto.randomUUID(),
              };
              request(identity, pending);
            }),
          );
          card.appendChild(
            button(
              "keep",
              () => {
                suspending = false;
                draw();
              },
              "text-button",
            ),
          );
        }
      }
    } else if (!identity && !busy && !recorded) {
      if (!rows.length) card.appendChild(el("p", t("empty")));
      for (const row of rows) {
        const item = el("section");
        item.append(
          el("h3", row.title || row.reference),
          el("bdi", row.reference),
          el("p", t(row.changes_pending ? "changes" : row.state)),
          button("view", () => request(row.id)),
        );
        card.appendChild(item);
      }
      if (more) card.appendChild(el("p", t("limit"), "sub"));
    }
    if (pending && error === "uncertain")
      card.appendChild(button("retry", () => request(identity, pending)));
    if (identity || error || recorded)
      card.appendChild(button("refresh", () => request(identity)));
    root.appendChild(card);
  }
  async function request(id, decision = null) {
    if (busy) return;
    identity = id;
    busy = true;
    error = "";
    agreed = false;
    suspending = false;
    if (!decision) {
      review = null;
      pending = null;
      recorded = false;
    }
    const version = ++generation;
    const requestController = new AbortController();
    controller = requestController;
    const timer = setTimeout(() => requestController.abort(), 20000);
    draw();
    try {
      const response = await fetch(
        decision
          ? "/miniapp/api/publication-consent"
          : "/miniapp/api/publications",
        {
          method: "POST",
          credentials: "same-origin",
          cache: "no-store",
          signal: requestController.signal,
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            init_data: tg.initData,
            ...(decision || { publication_id: id }),
          }),
        },
      );
      if (version !== generation) return;
      if ([401, 403].includes(response.status)) {
        clear();
        denied();
        return;
      }
      if (!response.ok) {
        if ([400, 404, 409].includes(response.status)) {
          review = null;
          pending = null;
          error = "changed";
        } else error = decision ? "uncertain" : "failure";
        return;
      }
      const result = await response.json();
      if (version !== generation) return;
      if (decision) {
        review = null;
        pending = null;
        recorded = result.recorded === true;
        outcome = result.action === "suspend" ? "stopped" : "saved";
      } else {
        recorded = false;
        pending = null;
        const candidate = result.review || null;
        if (
          candidate &&
          ((candidate.preview_url !== null &&
            !/^\/miniapp\/publication-preview\/[a-f0-9-]{36}$/.test(
              candidate.preview_url,
            )) ||
            !/^https:\/\//.test(candidate.public_url) ||
            !candidate.intent ||
            !candidate.terms ||
            (candidate.preview_url !== null
              ? typeof candidate.token !== "string"
              : candidate.token !== null))
        )
          throw Error("invalid review");
        review = candidate;
        rows = result.pages || [];
        more = result.more === true;
      }
    } catch (_) {
      if (version === generation) error = decision ? "uncertain" : "failure";
    } finally {
      clearTimeout(timer);
      if (version === generation) {
        busy = false;
        controller = null;
        draw();
      }
    }
  }
  function clear() {
    generation++;
    controller?.abort();
    controller = null;
    if (root) root.replaceChildren();
    root = null;
    rows = [];
    review = null;
    identity = null;
    pending = null;
    busy = false;
    error = "";
    recorded = false;
    agreed = false;
    more = false;
    suspending = false;
    outcome = "saved";
  }
  return {
    render(container, language) {
      root = container;
      lang = language;
      draw();
    },
    open() {
      return request(null);
    },
    goBack() {
      if (identity && !busy) return request(null);
      back();
    },
    clear,
    get busy() {
      return busy;
    },
  };
};
