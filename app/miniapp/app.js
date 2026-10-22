"use strict";

(function () {
  const tg = window.Telegram && window.Telegram.WebApp;
  const screen = document.getElementById("screen");
  const notice = document.getElementById("notice");
  const tabs = document.getElementById("tabs");
  let data = null;
  let lang = "ar";
  let tab = "services";
  let category = "all";
  let selectedService = null;
  let noticeKey = "loading";

  const words = {
    ar: {
      eyebrow: "خدماتك الرقمية", heading: "مرحبًا بك", subtitle: "الخدمات والطلبات في مكان واحد",
      services: "الخدمات", orders: "طلباتي", account: "الحساب", all: "الكل",
      browse: "اختر نوع الخدمة", history: "آخر الطلبات", noOrders: "لا توجد طلبات بعد",
      noServices: "لا توجد خدمات متاحة حاليًا", trial: "رصيد تجريبي", available: "المتاح",
      reserved: "المحجوز", stars: "الدفع عبر نجوم تيليجرام", priceStars: "نجمة",
      sar: "ريال رصيد تجريبي", paused: "غير متاحة مؤقتًا",
      optionsPaused: "بعض الخيارات غير متاحة حاليًا", returnBot: "تابع الطلب في محادثة البوت",
      detail: "الطلب والدفع متاحان حاليًا من محادثة البوت. هذه النسخة للتصفح والمتابعة فقط.",
      loading: "جارٍ التحميل...", failure: "تعذر تحميل البيانات. أعد فتح التطبيق من تيليجرام.",
      outside: "افتح هذه الصفحة من داخل بوت تيليجرام لاستخدامها بأمان.",
      back: "العودة للخدمات", navigation: "التنقل", language: "تغيير اللغة إلى الإنجليزية",
      close: "العودة إلى البوت", status: "حالة الطلب", reference: "مرجع"
    },
    en: {
      eyebrow: "Digital services", heading: "Welcome", subtitle: "Services and orders in one place",
      services: "Services", orders: "My orders", account: "Account", all: "All",
      browse: "Choose a service category", history: "Recent orders", noOrders: "No orders yet",
      noServices: "No services are currently available", trial: "Test credit", available: "Available",
      reserved: "Reserved", stars: "Telegram Stars checkout", priceStars: "Stars",
      sar: "SAR test credit", paused: "Temporarily unavailable",
      optionsPaused: "Some options are unavailable", returnBot: "Continue in bot chat",
      detail: "Ordering and payment remain in the bot chat. This first version is read-only.",
      loading: "Loading...", failure: "Could not load data. Reopen from Telegram.",
      outside: "Open this page inside the Telegram bot to authenticate securely.",
      back: "Back to services", navigation: "Navigation", language: "Switch language to Arabic",
      close: "Return to bot", status: "Status", reference: "Ref."
    }
  };
  function t(key) { return words[lang][key]; }
  function element(tag, className, value) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (value !== undefined) node.textContent = value;
    return node;
  }
  function pane(title) {
    const card = element("section", "card");
    card.appendChild(element("h2", "", title));
    return card;
  }
  function updateChrome() {
    document.documentElement.lang = lang;
    document.documentElement.dir = lang === "ar" ? "rtl" : "ltr";
    document.getElementById("eyebrow").textContent = t("eyebrow");
    document.getElementById("heading").textContent = t("heading");
    document.getElementById("subtitle").textContent = t("subtitle");
    document.getElementById("lang").textContent = lang === "ar" ? "EN" : "عربي";
    document.getElementById("lang").setAttribute("aria-label", t("language"));
    tabs.setAttribute("aria-label", t("navigation"));
    notice.textContent = t(noticeKey);
    for (const button of tabs.querySelectorAll("button")) {
      button.textContent = t(button.dataset.tab);
      button.classList.toggle("active", button.dataset.tab === tab);
      if (button.dataset.tab === tab) button.setAttribute("aria-current", "page");
      else button.removeAttribute("aria-current");
    }
  }
  function botReturn(container) {
    container.appendChild(element("p", "sub", t("detail")));
    const button = element("button", "primary", t("close"));
    button.type = "button";
    button.addEventListener("click", function () { if (tg) tg.close(); });
    container.appendChild(button);
  }
  function renderServices() {
    const heading = pane(t("browse"));
    const filters = element("div", "filters");
    const categories = [{ key: "all", ar: "الكل", en: "All" }]
      .concat(data.categories.filter(function (item) {
        return data.services.some(function (service) { return service.category === item.key; });
      }));
    for (const group of categories) {
      const button = element("button", "filter" + (category === group.key ? " active" : ""),
        group[lang]);
      button.type = "button";
      button.setAttribute("aria-pressed", String(category === group.key));
      button.addEventListener("click", function () { category = group.key; render(); });
      filters.appendChild(button);
    }
    heading.appendChild(filters);
    screen.appendChild(heading);
    const list = element("div", "stack services");
    const selected = data.services.filter(function (service) {
      return category === "all" || service.category === category;
    });
    if (!selected.length) list.appendChild(element("div", "empty", t("noServices")));
    for (const service of selected) {
      const card = element("button", "card service");
      card.type = "button";
      card.dataset.service = service.slug;
      card.appendChild(element("h3", "", service["name_" + lang]));
      card.appendChild(element("p", "sub", service["description_" + lang]));
      card.appendChild(element("div", "price", String(service.price) + " " +
        (data.payment_mode === "stars" ? t("priceStars") : t("sar"))));
      if (service.ai_unavailable || service.ai_options_unavailable) {
        card.appendChild(element("span", "pill",
          t(service.ai_unavailable ? "paused" : "optionsPaused")));
      }
      card.addEventListener("click", function () {
        selectedService = service;
        render();
        document.getElementById("service-back").focus();
      });
      list.appendChild(card);
    }
    screen.appendChild(list);
    const info = pane(t("returnBot"));
    botReturn(info);
    screen.appendChild(info);
  }
  function backToServices() {
    if (!selectedService) return;
    const slug = selectedService.slug;
    selectedService = null;
    render();
    // Compare data directly; slugs are never interpolated into a CSS selector.
    const cards = screen.querySelectorAll("[data-service]");
    for (const card of cards) {
      if (card.dataset.service === slug) { card.focus(); break; }
    }
  }
  function renderServiceDetail() {
    const detail = pane(selectedService["name_" + lang]);
    const back = element("button", "filter", t("back"));
    back.id = "service-back";
    back.type = "button";
    back.addEventListener("click", backToServices);
    detail.prepend(back);
    detail.appendChild(element("p", "sub", selectedService["description_" + lang]));
    detail.appendChild(element("div", "price", String(selectedService.price) + " " +
      (data.payment_mode === "stars" ? t("priceStars") : t("sar"))));
    if (selectedService.ai_unavailable || selectedService.ai_options_unavailable) {
      detail.appendChild(element("span", "pill",
        t(selectedService.ai_unavailable ? "paused" : "optionsPaused")));
    }
    botReturn(detail);
    screen.appendChild(detail);
  }
  function renderOrders() {
    const list = element("div", "stack");
    list.appendChild(element("h2", "", t("history")));
    if (!data.orders.length) list.appendChild(element("div", "card empty", t("noOrders")));
    for (const order of data.orders) {
      const card = element("article", "card");
      card.appendChild(element("h3", "", order["name_" + lang]));
      card.appendChild(element("p", "sub", t("reference") + ": " + order.reference));
      card.appendChild(element("span", "pill", t("status") + ": " + order["status_" + lang]));
      list.appendChild(card);
    }
    screen.appendChild(list);
  }
  function renderAccount() {
    const card = pane(data.payment_mode === "stars" ? t("stars") : t("trial"));
    if (data.credit) {
      card.appendChild(element("p", "sub", t("available") + ": " +
        data.credit.available_sar + " SAR"));
      card.appendChild(element("p", "sub", t("reserved") + ": " +
        data.credit.reserved_sar + " SAR"));
    }
    botReturn(card);
    screen.appendChild(card);
  }
  function render() {
    updateChrome();
    if (!data) return;
    screen.replaceChildren();
    if (tg && tg.BackButton) {
      if (selectedService) tg.BackButton.show();
      else tg.BackButton.hide();
    }
    if (tab === "services") {
      if (selectedService) renderServiceDetail();
      else renderServices();
    }
    if (tab === "orders") renderOrders();
    if (tab === "account") renderAccount();
  }
  for (const button of tabs.querySelectorAll("button")) {
    button.addEventListener("click", function () {
      selectedService = null;
      tab = button.dataset.tab; render();
    });
  }
  document.getElementById("lang").addEventListener("click", function () {
    lang = lang === "ar" ? "en" : "ar"; render();
  });
  if (tg && tg.BackButton) {
    tg.BackButton.hide();
    tg.BackButton.onClick(backToServices);
  }
  async function boot() {
    if (tg) { tg.ready(); tg.expand(); }
    if (!tg || !tg.initData) { noticeKey = "outside"; updateChrome(); return; }
    try {
      const result = await fetch("/miniapp/api/overview", {
        method: "POST",
        credentials: "same-origin",
        cache: "no-store",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ init_data: tg.initData })
      });
      if (!result.ok) throw new Error("overview unavailable");
      data = await result.json();
      lang = data.language === "en" ? "en" : "ar";
      noticeKey = "detail";
      render();
    } catch (_) {
      noticeKey = "failure";
      updateChrome();
    }
  }
  updateChrome();
  notice.textContent = t("loading");
  boot();
})();
