"use strict";

(function () {
  const tg = window.Telegram && window.Telegram.WebApp;
  const screen = document.getElementById("screen");
  const notice = document.getElementById("notice");
  const tabs = document.getElementById("tabs");
  let data = null;
  let lang = "ar";
  let tab = "services";
  let category = null;
  let query = "";
  let selectedService = null;
  let noticeKey = "loading";
  let loading = false;
  let catalogScroll = 0;

  // Group registered categories for browsing; no hard-coded service membership.
  const groups = [
    { key: "files", categories: ["documents", "pdf"], icon: "files" },
    { key: "writing", categories: ["text"], icon: "writing" },
    { key: "images", categories: ["images"], icon: "images" },
    { key: "work", categories: ["professional", "data"], icon: "work" },
    { key: "other", categories: ["other"], icon: "services" },
  ];
  const paths = {
    files: [
      "M8 3h7l4 4v13H8z",
      "M15 3v5h4",
      "M5 7H3v14h12",
      "M11 12h5M11 16h5",
    ],
    writing: ["m15 4 5 5-10 10-6 1 1-6z", "m12 7 5 5", "M4 4h5M4 8h3"],
    images: ["M4 3h16v18H4z", "m4 16 5-5 4 4 3-3 4 4", "M15 7h1"],
    work: ["M3 7h18v14H3z", "M8 7V3h8v4", "M3 12c5 3 13 3 18 0", "M10 13h4"],
    services: ["M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z"],
    orders: ["M6 3h12v18l-3-2-3 2-3-2-3 2z", "M9 8h6M9 12h6"],
    account: ["M16 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0", "M4 21v-2a8 8 0 0 1 16 0v2"],
    search: ["M17 10a7 7 0 1 1-14 0 7 7 0 0 1 14 0", "m15 15 6 6"],
    arrow: ["m9 5 7 7-7 7"],
    chat: ["M3 3h18v14H9l-6 4z", "M7 8h10M7 12h6"],
    refresh: ["M20 7a9 9 0 1 0 1 8", "M20 2v6h-6"],
    close: ["m6 6 12 12M6 18 18 6"],
  };
  const words = {
    ar: {
      eyebrow: "خدماتك الرقمية",
      heading: "ماذا تريد أن تنجز؟",
      subtitle: "اختر الخدمة المناسبة، وابدأ بخطوة بسيطة.",
      services: "الخدمات",
      orders: "طلباتي",
      account: "حسابي",
      all: "جميع الخدمات",
      files: "مستندات وPDF",
      writing: "كتابة وترجمة",
      images: "صور ومسح ضوئي",
      work: "أعمال وبيانات",
      other: "خدمات أخرى",
      filesHint: "إنشاء المستندات وتحويل الملفات",
      writingHint: "تحرير النصوص وتلخيصها وترجمتها",
      imagesHint: "استخراج النص وتحسين وضوح الصور",
      workHint: "سيرة ذاتية واجتماعات وجداول",
      otherHint: "المزيد من الخدمات",
      browse: "اختر قسمًا لتبدأ",
      serviceCount: "خدمات",
      search: "ابحث عن خدمة…",
      searchWithin: "ابحث في هذا القسم…",
      clearSearch: "مسح البحث",
      searchResults: "نتائج البحث",
      noResults: "لم نجد خدمة مطابقة",
      trySearch: "جرّب كلمة أخرى، أو ابحث في جميع الأقسام.",
      searchAll: "البحث في جميع الخدمات",
      noServices: "لا توجد خدمات متاحة حاليًا",
      history: "آخر طلباتك",
      latestOrder: "آخر طلب",
      noOrders: "لم تبدأ طلبك الأول بعد",
      firstOrder: "اختر خدمة تناسبك، وستجد حالة طلبك هنا.",
      explore: "استكشف الخدمات",
      refresh: "تحديث الطلبات",
      available: "الرصيد المتاح",
      reserved: "قيد الحجز",
      trial: "رصيدك التجريبي",
      trialHint: "هذا رصيد للتجربة، وتُراجع تكلفة كل طلب قبل تأكيده.",
      stars: "الدفع بنجوم تيليجرام",
      starsHint: "يظهر مبلغ النجوم وشروط الدفع عند مراجعة الطلب في البوت.",
      priceStars: "نجمة",
      sar: "ر.س",
      trialLabel: "رصيد تجريبي",
      price: "سعر الخدمة",
      paused: "غير متاحة مؤقتًا",
      directAvailable: "الخيارات المباشرة متاحة",
      pausedHint: "هذه الخدمة متوقفة مؤقتًا. يمكنك العودة واختيار خدمة أخرى.",
      directHint:
        "يمكنك استخدام الخيارات المباشرة. خيارات التحسين متوقفة مؤقتًا.",
      back: "العودة للخدمات",
      backGroups: "الأقسام",
      how: "كيف يكتمل طلبك؟",
      step1: "أرسل المحتوى",
      step1Hint: "استكمل البيانات أو ارفع الملف في البوت.",
      step2: "راجع وأكّد",
      step2Hint: "راجع الخيارات والسعر قبل بدء التنفيذ.",
      step3: "استلم النتيجة",
      step3Hint: "نرسل النتيجة والملفات في محادثة البوت.",
      startRequest: "متابعة الطلب في البوت",
      handoff: "ستنتقل إلى محادثة البوت لاستكمال هذا الطلب.",
      fallback: "افتح الخدمات في محادثة البوت واختر هذه الخدمة للمتابعة.",
      close: "العودة إلى البوت",
      noCharge: "لا يبدأ التنفيذ أو حجز الرصيد بمجرد فتح الخدمة.",
      botRole: "المحادثة تكمل تجربتك",
      botRoleHint:
        "في البوت تستكمل بيانات الطلب، وتستلم النتائج والملفات، وتتواصل مع الدعم.",
      needHelp: "تحتاج مساعدة؟",
      helpHint: "ارجع إلى محادثة البوت واضغط «الدعم».",
      loading: "جارٍ تحميل خدماتك…",
      refreshing: "جارٍ تحديث البيانات…",
      failure:
        "تعذر تحديث البيانات. حاول مجددًا، أو أعد فتح التطبيق من تيليجرام.",
      outside: "افتح التطبيق من زر القائمة داخل بوت تيليجرام للمتابعة.",
      retry: "إعادة المحاولة",
      navigation: "التنقل",
      language: "تغيير اللغة إلى الإنجليزية",
      reference: "رقم الطلب",
    },
    en: {
      eyebrow: "Your digital services",
      heading: "What would you like to do?",
      subtitle: "Choose a service. Start with one simple step.",
      services: "Services",
      orders: "My orders",
      account: "Account",
      all: "All services",
      files: "Documents & PDF",
      writing: "Writing & translation",
      images: "Images & scanning",
      work: "Work & data",
      other: "More services",
      filesHint: "Create documents and convert files",
      writingHint: "Edit, summarize and translate text",
      imagesHint: "Extract text and improve image clarity",
      workHint: "CVs, meetings and spreadsheets",
      otherHint: "Explore more services",
      browse: "Choose a category",
      serviceCount: "services",
      search: "Search for a service…",
      searchWithin: "Search this category…",
      clearSearch: "Clear search",
      searchResults: "Search results",
      noResults: "No matching services",
      trySearch: "Try another word, or search every category.",
      searchAll: "Search all services",
      noServices: "No services are currently available",
      history: "Recent orders",
      latestOrder: "Latest order",
      noOrders: "Your first order starts here",
      firstOrder: "Choose a service and follow its progress here.",
      explore: "Explore services",
      refresh: "Refresh orders",
      available: "Available credit",
      reserved: "Reserved",
      trial: "Your test credit",
      trialHint:
        "This credit is for testing. Review the cost before confirming each order.",
      stars: "Pay with Telegram Stars",
      starsHint:
        "Review the Stars amount and payment terms in bot chat before paying.",
      priceStars: "Stars",
      sar: "SAR",
      trialLabel: "Test credit",
      price: "Service price",
      paused: "Temporarily unavailable",
      directAvailable: "Direct options available",
      pausedHint:
        "This service is temporarily paused. Go back to choose another service.",
      directHint:
        "Direct options are available. Improvement options are temporarily paused.",
      back: "Back to services",
      backGroups: "Categories",
      how: "How your order works",
      step1: "Send your content",
      step1Hint: "Enter the details or upload your file in bot chat.",
      step2: "Review and confirm",
      step2Hint: "Check the options and price before processing starts.",
      step3: "Receive your result",
      step3Hint: "Your result and files arrive in bot chat.",
      startRequest: "Continue order in bot",
      handoff: "Continue this request in the bot conversation.",
      fallback:
        "Open Services in bot chat and select this service to continue.",
      close: "Return to bot",
      noCharge:
        "Opening a service does not start processing or reserve credit.",
      botRole: "The conversation completes your experience",
      botRoleHint:
        "Use bot chat to complete order details, receive results and files, and contact support.",
      needHelp: "Need a hand?",
      helpHint: "Return to bot chat and choose Support.",
      loading: "Loading your services…",
      refreshing: "Refreshing your data…",
      failure:
        "Could not refresh data. Try again, or reopen the app from Telegram.",
      outside:
        "Open the app from the menu button inside the Telegram bot to continue.",
      retry: "Try again",
      navigation: "Navigation",
      language: "Switch language to Arabic",
      reference: "Order ref.",
    },
  };

  function t(key) {
    return words[lang][key];
  }
  function element(tag, className, value) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (value !== undefined) node.textContent = value;
    return node;
  }
  function icon(name, className) {
    const node = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    for (const entry of Object.entries({
      viewBox: "0 0 24 24",
      fill: "none",
      stroke: "currentColor",
      "stroke-width": "1.7",
      "stroke-linecap": "round",
      "stroke-linejoin": "round",
      "aria-hidden": "true",
      focusable: "false",
      class: "icon" + (className ? " " + className : ""),
    })) {
      node.setAttribute(entry[0], entry[1]);
    }
    for (const path of paths[name] || paths.services) {
      const line = document.createElementNS(
        "http://www.w3.org/2000/svg",
        "path",
      );
      line.setAttribute("d", path);
      node.appendChild(line);
    }
    return node;
  }
  function button(label, className, action) {
    const node = element("button", className, label);
    node.type = "button";
    node.addEventListener("click", action);
    return node;
  }
  function heading(title, id) {
    const node = element("h2", "section-title", title);
    if (id) {
      node.id = id;
      node.tabIndex = -1;
    }
    return node;
  }
  function groupFor(service) {
    return (
      groups.find(function (group) {
        return group.categories.includes(service.category);
      }) || groups[4]
    );
  }
  function normalize(value) {
    return String(value || "")
      .normalize("NFKD")
      .toLowerCase()
      .replace(/[\u064B-\u065F\u0670\u0640]/g, "")
      .replace(/ى/g, "ي")
      .trim();
  }
  function matchingServices() {
    const term = normalize(query);
    return data.services.filter(function (service) {
      return (
        (!category ||
          category === "all" ||
          groupFor(service).key === category) &&
        (!term ||
          normalize(
            [
              service.name_ar,
              service.name_en,
              service.description_ar,
              service.description_en,
              t(groupFor(service).key),
            ].join(" "),
          ).includes(term))
      );
    });
  }
  function focus(id) {
    const node = document.getElementById(id);
    if (node) node.focus();
  }
  function syncBack() {
    if (!tg || !tg.BackButton) return;
    if (tab === "services" && (selectedService || category || query))
      tg.BackButton.show();
    else tg.BackButton.hide();
  }
  function updateChrome() {
    document.documentElement.lang = lang;
    document.documentElement.dir = lang === "ar" ? "rtl" : "ltr";
    document.getElementById("eyebrow").textContent = t("eyebrow");
    document.getElementById("heading").textContent = t(
      tab === "services" ? "heading" : tab,
    );
    document.getElementById("subtitle").textContent = t(
      tab === "services"
        ? "subtitle"
        : tab === "orders"
          ? "step3Hint"
          : "botRoleHint",
    );
    document.getElementById("heading").hidden = Boolean(selectedService);
    document.getElementById("subtitle").hidden = Boolean(selectedService);
    document.getElementById("lang").textContent = lang === "ar" ? "EN" : "عربي";
    document.getElementById("lang").setAttribute("aria-label", t("language"));
    tabs.setAttribute("aria-label", t("navigation"));
    notice.hidden = !noticeKey;
    notice.textContent = noticeKey ? t(noticeKey) : "";
    notice.classList.toggle("error", noticeKey === "failure");
    for (const item of tabs.querySelectorAll("button")) {
      item.replaceChildren(
        icon(item.dataset.tab),
        element("span", "", t(item.dataset.tab)),
      );
      item.classList.toggle("active", item.dataset.tab === tab);
      if (item.dataset.tab === tab) item.setAttribute("aria-current", "page");
      else item.removeAttribute("aria-current");
    }
    syncBack();
  }
  function chooseTab(value) {
    tab = value;
    selectedService = null;
    render();
    window.scrollTo(0, 0);
    focus("section-title");
  }
  function closeToBot() {
    if (tg && typeof tg.close === "function") tg.close();
  }
  function groupHome() {
    const previous = category;
    category = null;
    query = "";
    render();
    const item = Array.from(screen.querySelectorAll("[data-group]")).find(
      function (node) {
        return node.dataset.group === previous;
      },
    );
    if (item) item.focus();
    else focus("service-search");
  }
  function back() {
    if (!selectedService) {
      groupHome();
      return;
    }
    const slug = selectedService.slug;
    selectedService = null;
    render();
    const item = Array.from(screen.querySelectorAll("[data-service]")).find(
      function (node) {
        return node.dataset.service === slug;
      },
    );
    if (item) item.focus();
    window.scrollTo(0, catalogScroll);
  }
  function price(service) {
    const node = element("div", "price");
    node.append(
      element("strong", "", String(service.price)),
      element(
        "span",
        "",
        t(data.payment_mode === "stars" ? "priceStars" : "sar"),
      ),
    );
    if (data.payment_mode !== "stars")
      node.appendChild(element("span", "credit-label", t("trialLabel")));
    return node;
  }
  function serviceCard(service) {
    const group = groupFor(service);
    const card = button("", "service-card", function () {
      catalogScroll = window.scrollY;
      selectedService = service;
      render();
      window.scrollTo(0, 0);
      focus("service-back");
    });
    card.dataset.service = service.slug;
    card.appendChild(icon(group.icon, "service-icon tone-" + group.key));
    const copy = element("div", "service-copy");
    copy.append(
      element("h3", "", service["name_" + lang]),
      element("p", "sub service-description", service["description_" + lang]),
      price(service),
    );
    if (service.ai_unavailable || service.ai_options_unavailable)
      copy.appendChild(
        element(
          "span",
          "pill" + (service.ai_unavailable ? " paused" : ""),
          t(service.ai_unavailable ? "paused" : "directAvailable"),
        ),
      );
    card.append(copy, icon("arrow", "forward"));
    return card;
  }
  function renderCatalog(content) {
    content.replaceChildren();
    syncBack();
    if (!category && !query) {
      const top = element("div", "section-head");
      top.append(
        heading(t("browse"), "section-title"),
        button(t("all"), "text-button", function () {
          category = "all";
          render();
          focus("section-title");
        }),
      );
      content.appendChild(top);
      const grid = element("div", "category-grid");
      for (const group of groups) {
        const count = data.services.filter(function (service) {
          return groupFor(service).key === group.key;
        }).length;
        if (!count) continue;
        const card = button("", "category-card tone-" + group.key, function () {
          category = group.key;
          render();
          focus("section-title");
        });
        card.dataset.group = group.key;
        card.append(
          icon(group.icon, "category-icon"),
          element("h3", "", t(group.key)),
          element("p", "sub", t(group.key + "Hint")),
          element("span", "category-count", count + " " + t("serviceCount")),
        );
        grid.appendChild(card);
      }
      content.appendChild(grid);
      if (!data.services.length)
        content.appendChild(element("p", "empty", t("noServices")));
      if (data.orders.length) {
        const order = data.orders[0];
        const recent = button("", "recent-order", function () {
          chooseTab("orders");
        });
        const copy = element("div", "");
        copy.append(
          element("span", "mini-label", t("latestOrder")),
          element("h3", "", order["name_" + lang]),
          element("span", "sub", order["status_" + lang]),
        );
        recent.append(icon("orders"), copy, icon("arrow", "forward"));
        content.appendChild(recent);
      }
      return;
    }
    const selected = matchingServices();
    const top = element("div", "section-head");
    top.append(
      heading(query ? t("searchResults") : t(category), "section-title"),
      element("span", "count", selected.length + " " + t("serviceCount")),
    );
    content.appendChild(top);
    const list = element("div", "service-list");
    for (const service of selected) list.appendChild(serviceCard(service));
    content.appendChild(list);
    if (!selected.length) {
      const empty = element("div", "card empty");
      empty.append(
        icon("search"),
        element("h3", "", t("noResults")),
        element("p", "sub", t("trySearch")),
      );
      if (category && category !== "all")
        empty.appendChild(
          button(t("searchAll"), "secondary", function () {
            category = "all";
            render();
            focus("service-search");
          }),
        );
      content.appendChild(empty);
    }
  }
  function renderServices() {
    if (category) {
      const control = button(t("backGroups"), "back-button", groupHome);
      control.prepend(icon("arrow", "back-arrow"));
      screen.appendChild(control);
    }
    const search = element("div", "search-box");
    const input = element("input", "");
    input.id = "service-search";
    input.type = "search";
    input.maxLength = 120;
    input.value = query;
    input.placeholder = t(
      category && category !== "all" ? "searchWithin" : "search",
    );
    input.setAttribute("aria-label", input.placeholder);
    input.autocomplete = "off";
    const content = element("div", "catalog-content");
    const clear = button("", "icon-button clear-search", function () {
      query = "";
      input.value = "";
      clear.hidden = true;
      renderCatalog(content);
      input.focus();
    });
    clear.appendChild(icon("close"));
    clear.setAttribute("aria-label", t("clearSearch"));
    clear.hidden = !query;
    input.addEventListener("input", function () {
      query = input.value.slice(0, 120);
      clear.hidden = !query;
      renderCatalog(content);
    });
    search.append(icon("search"), input, clear);
    screen.append(search, content);
    renderCatalog(content);
  }
  function renderServiceDetail() {
    const group = groupFor(selectedService);
    const control = button(t("back"), "back-button", back);
    control.id = "service-back";
    control.prepend(icon("arrow", "back-arrow"));
    const detail = element("section", "card detail-card");
    detail.append(
      icon(group.icon, "detail-icon tone-" + group.key),
      element("span", "mini-label", t(group.key)),
      heading(selectedService["name_" + lang], "section-title"),
      element(
        "p",
        "detail-description",
        selectedService["description_" + lang],
      ),
    );
    const cost = element("div", "detail-price");
    cost.append(
      element("span", "mini-label", t("price")),
      price(selectedService),
    );
    detail.appendChild(cost);
    if (
      selectedService.ai_unavailable ||
      selectedService.ai_options_unavailable
    )
      detail.appendChild(
        element(
          "p",
          "availability" + (selectedService.ai_unavailable ? " paused" : ""),
          t(selectedService.ai_unavailable ? "pausedHint" : "directHint"),
        ),
      );
    const steps = element("section", "card steps");
    steps.appendChild(heading(t("how")));
    const list = element("ol", "steps-list");
    for (let index = 1; index <= 3; index++) {
      const item = element("li", "");
      const copy = element("div", "");
      copy.append(
        element("h3", "", t("step" + index)),
        element("p", "sub", t("step" + index + "Hint")),
      );
      item.append(element("span", "step-number", index), copy);
      list.appendChild(item);
    }
    steps.appendChild(list);
    const action = element("div", "order-action");
    const url = selectedService.request_url;
    const valid =
      typeof url === "string" &&
      /^https:\/\/t\.me\/[A-Za-z][A-Za-z0-9_]{1,28}bot\?start=request_[a-z][a-z0-9_]{0,39}$/i.test(
        url,
      );
    if (selectedService.ai_unavailable) {
      const unavailable = button(t("paused"), "primary", function () {});
      unavailable.disabled = true;
      action.appendChild(unavailable);
    } else if (valid && tg && typeof tg.openTelegramLink === "function") {
      const request = button(t("startRequest"), "primary", function () {
        tg.openTelegramLink(url);
      });
      request.id = "service-request";
      request.prepend(icon("chat"));
      action.append(request, element("p", "action-hint", t("handoff")));
    } else
      action.append(
        button(t("close"), "primary", closeToBot),
        element("p", "action-hint", t("fallback")),
      );
    action.appendChild(element("p", "fine-print", t("noCharge")));
    detail.appendChild(action);
    screen.append(control, detail, steps);
  }
  function orderCard(order) {
    const card = element("article", "card order-card");
    const top = element("div", "order-card-top");
    top.append(
      icon("orders", "order-icon"),
      element("h3", "", order["name_" + lang]),
    );
    card.appendChild(top);
    const meta = element("div", "order-meta");
    const reference = element("span", "", t("reference") + " ");
    reference.appendChild(element("bdi", "order-reference", order.reference));
    meta.appendChild(reference);
    const date = new Date(order.created_at);
    if (order.created_at && !Number.isNaN(date.getTime()))
      meta.appendChild(
        element(
          "time",
          "",
          new Intl.DateTimeFormat(
            lang === "ar" ? "ar-SA-u-ca-gregory" : "en-GB",
            { day: "numeric", month: "short", timeZone: "Asia/Riyadh" },
          ).format(date),
        ),
      );
    card.append(
      meta,
      element("span", "pill order-status", order["status_" + lang]),
    );
    return card;
  }
  function renderOrders() {
    const top = element("div", "section-head");
    top.appendChild(heading(t("history"), "section-title"));
    const refresh = button("", "icon-button", boot);
    refresh.id = "refresh-orders";
    refresh.setAttribute("aria-label", t("refresh"));
    refresh.disabled = loading;
    refresh.appendChild(icon("refresh"));
    top.appendChild(refresh);
    screen.appendChild(top);
    if (!data.orders.length) {
      const empty = element("div", "card empty");
      empty.append(
        icon("orders", "empty-icon"),
        element("h3", "", t("noOrders")),
        element("p", "sub", t("firstOrder")),
        button(t("explore"), "primary", function () {
          chooseTab("services");
        }),
      );
      screen.appendChild(empty);
    } else {
      const list = element("div", "order-list");
      for (const order of data.orders) list.appendChild(orderCard(order));
      screen.appendChild(list);
    }
  }
  function renderAccount() {
    const credit = element("section", "card account-credit");
    credit.appendChild(
      heading(
        t(data.payment_mode === "stars" ? "stars" : "trial"),
        "section-title",
      ),
    );
    if (data.credit) {
      const values = element("div", "balance-grid");
      for (const item of [
        ["available", "available_sar"],
        ["reserved", "reserved_sar"],
      ]) {
        const value = element("div", "");
        value.append(
          element("span", "mini-label", t(item[0])),
          element("strong", "balance-value", data.credit[item[1]]),
          element("span", "mini-label", t("sar")),
        );
        values.appendChild(value);
      }
      credit.appendChild(values);
    }
    credit.appendChild(
      element(
        "p",
        "sub",
        t(data.payment_mode === "stars" ? "starsHint" : "trialHint"),
      ),
    );
    const help = element("section", "card help-card");
    help.append(
      icon("chat", "help-icon"),
      heading(t("botRole")),
      element("p", "sub", t("botRoleHint")),
      element("h3", "", t("needHelp")),
      element("p", "sub", t("helpHint")),
      button(t("close"), "secondary", closeToBot),
    );
    screen.append(credit, help);
  }
  function render() {
    updateChrome();
    screen.replaceChildren();
    if (!data) {
      if (loading) {
        const skeleton = element("div", "category-grid skeleton");
        skeleton.setAttribute("aria-hidden", "true");
        for (let index = 0; index < 4; index++)
          skeleton.appendChild(element("div", "category-card", ""));
        screen.appendChild(skeleton);
      }
      if (noticeKey === "failure")
        screen.appendChild(button(t("retry"), "secondary", boot));
      return;
    }
    if (tab === "services") {
      if (selectedService) renderServiceDetail();
      else renderServices();
    }
    if (tab === "orders") renderOrders();
    if (tab === "account") renderAccount();
  }
  for (const item of tabs.querySelectorAll("button"))
    item.addEventListener("click", function () {
      chooseTab(item.dataset.tab);
    });
  document.getElementById("lang").addEventListener("click", function () {
    lang = lang === "ar" ? "en" : "ar";
    render();
  });
  if (tg && tg.BackButton) {
    tg.BackButton.hide();
    tg.BackButton.onClick(back);
  }
  function theme() {
    if (tg && (tg.colorScheme === "dark" || tg.colorScheme === "light"))
      document.documentElement.style.colorScheme = tg.colorScheme;
  }
  if (tg && typeof tg.onEvent === "function") tg.onEvent("themeChanged", theme);
  theme();
  async function boot() {
    if (loading) return;
    if (!tg || !tg.initData) {
      noticeKey = "outside";
      render();
      return;
    }
    loading = true;
    noticeKey = data ? "refreshing" : "loading";
    render();
    try {
      const response = await fetch("/miniapp/api/overview", {
        method: "POST",
        credentials: "same-origin",
        cache: "no-store",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ init_data: tg.initData }),
      });
      if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
          data = null;
          selectedService = null;
        }
        throw new Error("overview unavailable");
      }
      const updated = await response.json();
      if (!data) lang = updated.language === "en" ? "en" : "ar";
      data = updated;
      if (selectedService)
        selectedService =
          data.services.find(function (service) {
            return service.slug === selectedService.slug;
          }) || null;
      noticeKey = null;
    } catch (_) {
      noticeKey = "failure";
    }
    loading = false;
    render();
  }
  if (tg) {
    tg.ready();
    tg.expand();
  }
  render();
  boot();
})();
