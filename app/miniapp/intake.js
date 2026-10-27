"use strict";

window.MiniAppIntake = function ({ tg, exit, orders }) {
  let container,
    lang = "ar",
    draft = null,
    busy = false,
    error = "";
  let entered = "",
    retry = null;
  let receipt = null,
    agreed = false,
    confirmAttempted = false;
  const labels = {
    ar: {
      back: "العودة للخدمة",
      title: "بيانات طلبك",
      loading: "جارٍ حفظ مسودتك…",
      saved:
        "مسودة محفوظة لمدة ساعة من آخر تعديل. لم يبدأ التنفيذ ولم يُحجز رصيد.",
      next: "حفظ ومتابعة",
      skip: "تخطي هذا الحقل",
      upload: "اختر ملفًا",
      received: "ملفات مرفوعة",
      done: "اكتفيت بهذه الملفات",
      ready: "راجع بيانات طلبك",
      handoff: "المراجعة والتأكيد في البوت",
      edit: "تعديل البيانات",
      abort: "التراجع عن التعديل",
      retry: "إعادة المحاولة",
      refresh: "تحديث المسودة",
      bot: "العودة للبوت",
      fallback: "ارجع للمحادثة وأرسل /resume لاستكمال المسودة.",
      failure: "تعذر حفظ التعديل. يمكنك إعادة المحاولة بنفس العملية.",
      invalid: "راجع قيمة الحقل أو نوع الملف وحجمه، ثم حاول مجددًا.",
      expired: "أعد فتح التطبيق من قائمة البوت للمتابعة.",
      denied:
        "تعذر الوصول للحساب. افتح محادثة البوت وأرسل /start، أو تواصل مع الدعم.",
      conflict: "تغيّرت المسودة أو شروط الخدمة. حدّثها، أو استكملها في البوت.",
      rate: "طلبات كثيرة خلال وقت قصير. انتظر دقيقة ثم أعد المحاولة.",
      choose: "اختر إجابة واحدة",
      limit: "الحد الأقصى للملف",
      unavailable: "غير متاح مؤقتًا",
      reviewHint:
        "راجع بياناتك هنا، ثم انتقل للبوت لمراجعة السعر والتأكيد النهائي.",
      confirmHint:
        "راجع البيانات والسعر. عند التأكيد يُحجز المبلغ من رصيدك التجريبي ويبدأ الطلب.",
      agree: "راجعت البيانات والسعر وأوافق على حجز الرصيد التجريبي",
      confirm: "تأكيد الطلب وحجز الرصيد التجريبي",
      amount: "المبلغ من الرصيد التجريبي",
      submitted: "تم تسجيل طلبك",
      reference: "رقم الطلب",
      delivery: "تُرسل النتائج والملفات عبر محادثة البوت.",
      orders: "متابعة طلباتي",
      funds: "رصيدك التجريبي غير كافٍ لهذا الطلب.",
      paused: "الخدمة غير متاحة مؤقتًا. لم يبدأ طلب جديد.",
      concurrent: "لديك طلبات قيد التنفيذ. انتظر اكتمالها قبل طلب جديد.",
      checking:
        "تحقق من نتيجة التأكيد في طلباتي، أو أعد المحاولة لاستعادة الطلب نفسه.",
    },
    en: {
      back: "Back to service",
      title: "Your request details",
      loading: "Saving your draft…",
      saved:
        "Saved for one hour after the last edit. Processing and credit reservation have not started.",
      next: "Save and continue",
      skip: "Skip this field",
      upload: "Choose a file",
      received: "Uploaded files",
      done: "Done adding files",
      ready: "Review your request",
      handoff: "Review and confirm in bot",
      edit: "Edit details",
      abort: "Discard this edit",
      retry: "Try again",
      refresh: "Refresh draft",
      bot: "Return to bot",
      fallback: "Return to chat and send /resume to continue the draft.",
      failure: "Could not save the change. You can retry the same operation.",
      invalid: "Check the field value or file type and size, then try again.",
      expired: "Reopen the app from the bot menu to continue.",
      denied:
        "Cannot access this account. Open bot chat and send /start, or contact support.",
      conflict:
        "The draft or service terms changed. Refresh it or continue in bot chat.",
      rate: "Too many requests. Wait a minute before trying again.",
      choose: "Choose one answer",
      limit: "Maximum file size",
      unavailable: "Temporarily unavailable",
      reviewHint:
        "Review your details here, then check the price and confirm in bot chat.",
      confirmHint:
        "Review the details and price. Confirmation reserves this amount from your test credit and starts the request.",
      agree:
        "I reviewed the details and price and agree to reserve test credit",
      confirm: "Confirm and reserve test credit",
      amount: "Amount from test credit",
      submitted: "Your request is registered",
      reference: "Order reference",
      delivery: "Results and files are delivered through bot chat.",
      orders: "Follow my orders",
      funds: "Your test credit is insufficient for this request.",
      paused:
        "This service is temporarily unavailable. No new request has started.",
      concurrent:
        "You have requests in progress. Wait for them to finish before starting another.",
      checking: "Check My orders, or retry to recover the same request.",
    },
  };
  const t = (key) => labels[lang][key];
  function el(tag, cls, text) {
    const node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text !== undefined) node.textContent = text;
    return node;
  }
  function button(text, cls, action) {
    const node = el("button", cls, text);
    node.type = "button";
    node.disabled = busy;
    node.addEventListener("click", action);
    return node;
  }
  function draw() {
    if (!container || !container.isConnected) return;
    container.replaceChildren();
    container.setAttribute("aria-busy", String(busy));
    container.appendChild(button(t("back"), "back-button", exit));
    const card = el("section", "card intake-card");
    const title = el(
      "h2",
      "section-title",
      t(receipt ? "submitted" : draft && draft.ready ? "ready" : "title"),
    );
    title.id = "intake-title";
    title.tabIndex = -1;
    card.appendChild(title);
    if (draft) card.appendChild(el("p", "mini-label", draft["name_" + lang]));
    const status = el(
      "p",
      "availability",
      busy ? t("loading") : error ? t(error) : "",
    );
    status.hidden = !busy && !error;
    status.setAttribute("role", "status");
    card.appendChild(status);
    if (receipt) {
      card.append(
        el("p", "mini-label", t("reference")),
        el("bdi", "receipt-reference", receipt.reference),
        el("p", "pill", receipt["status_" + lang]),
        el("p", "sub", t("delivery")),
      );
      if (orders) card.appendChild(button(t("orders"), "primary", orders));
    }
    if (draft && !draft.ready && draft.field) {
      const field = draft.field;
      const prompt = el(
        field.choices.length ? "p" : "label",
        "intake-prompt",
        field.prompt[lang],
      );
      prompt.htmlFor = "intake-value";
      card.appendChild(prompt);
      if (field.choices.length) {
        const choices = el("div", "intake-choices");
        choices.setAttribute("role", "group");
        choices.setAttribute("aria-label", t("choose"));
        for (const choice of field.choices) {
          const option = button(
            choice[lang] + (choice.blocked ? " · " + t("unavailable") : ""),
            "secondary",
            () => mutate("answer", { value: choice.value }),
          );
          option.disabled = busy || choice.blocked;
          choices.appendChild(option);
        }
        card.appendChild(choices);
      } else if (field.kind === "text") {
        const input = el(
          field.single_line ? "input" : "textarea",
          "intake-value",
        );
        input.id = "intake-value";
        input.maxLength = field.max_length;
        input.dir = "auto";
        if (field.single_line) input.type = "text";
        else input.rows = 7;
        input.value = entered;
        input.disabled = busy;
        const count = el(
          "p",
          "sub intake-count",
          entered.length + " / " + field.max_length,
        );
        count.dir = "ltr";
        const next = button(t("next"), "primary", () =>
          mutate("answer", { value: entered }),
        );
        next.disabled = busy || !entered.trim();
        input.addEventListener("input", () => {
          entered = input.value;
          retry = null;
          next.disabled = busy || !entered.trim();
          count.textContent = entered.length + " / " + field.max_length;
        });
        card.append(input, count, next);
      } else {
        const input = el("input", "intake-file");
        input.id = "intake-value";
        input.type = "file";
        const images = "image/jpeg,image/png,image/webp";
        const audio = "audio/ogg,audio/mpeg,audio/wav";
        input.accept =
          field.kind === "image"
            ? images
            : field.kind === "audio"
              ? audio
              : images + "," + audio + ",application/pdf";
        input.disabled = busy;
        input.setAttribute("aria-label", t("upload"));
        input.addEventListener("change", () => {
          const file = input.files[0];
          if (!file) return;
          if (!file.size || file.size > field.max_bytes) {
            error = "invalid";
            draw();
            return;
          }
          mutate("answer", {}, file);
        });
        card.append(
          input,
          el(
            "p",
            "sub",
            t("limit") + ": " + Math.round(field.max_bytes / 1048576) + " MB",
          ),
        );
        if (field.multiple) {
          card.appendChild(
            el(
              "p",
              "sub",
              t("received") + ": " + field.received + " / " + field.max_items,
            ),
          );
          if (field.received)
            card.appendChild(
              button(t("done"), "primary", () => mutate("done")),
            );
        }
      }
      if (!field.required && !field.received && !field.skip_blocked)
        card.appendChild(
          button(field.skip[lang] || t("skip"), "text-button", () =>
            mutate("skip"),
          ),
        );
      if (draft.editing)
        card.appendChild(
          button(t("abort"), "text-button", () => mutate("abort")),
        );
    }
    if (draft && draft.ready) {
      card.append(
        el("p", "sub", t(draft.confirmation ? "confirmHint" : "reviewHint")),
        el("p", "intake-review", draft.review[lang]),
      );
      const url = draft.request_url;
      if (draft.confirmation) {
        card.appendChild(
          el(
            "p",
            "confirmation-amount",
            t("amount") +
              ": " +
              draft.confirmation.amount_sar +
              (lang === "ar" ? " ر.س" : " SAR"),
          ),
        );
        const label = el("label", "confirmation-consent");
        const check = el("input", "");
        check.type = "checkbox";
        check.id = "confirm-consent";
        check.checked = agreed;
        check.disabled = busy || confirmAttempted;
        const confirm = button(t("confirm"), "primary", () => {
          if (!agreed || busy || confirmAttempted) return;
          confirmAttempted = true;
          retry = {
            payload: {
              action: "confirm",
              token: draft.confirmation.token,
              accepted: true,
            },
          };
          send(retry);
        });
        confirm.id = "confirm-request";
        confirm.disabled = busy || !agreed || confirmAttempted;
        check.addEventListener("change", () => {
          agreed = check.checked;
          confirm.disabled = busy || !agreed || confirmAttempted;
        });
        label.append(check, el("span", "", t("agree")));
        card.append(label, confirm);
      } else if (
        typeof url === "string" &&
        /^https:\/\/t\.me\/[A-Za-z][A-Za-z0-9_]{1,28}bot\?start=request_[a-z][a-z0-9_]{0,39}$/i.test(
          url,
        ) &&
        tg &&
        typeof tg.openTelegramLink === "function"
      )
        card.appendChild(
          button(t("handoff"), "primary", () => tg.openTelegramLink(url)),
        );
      else
        card.append(
          button(t("bot"), "primary", () => tg && tg.close()),
          el("p", "sub", t("fallback")),
        );
      const edit = el("details", "intake-edit");
      edit.appendChild(el("summary", "", t("edit")));
      for (const field of draft.editable)
        edit.appendChild(
          button(field[lang], "secondary", () =>
            mutate("edit", { index: field.index }),
          ),
        );
      if (!confirmAttempted) card.appendChild(edit);
    }
    if (error) {
      if (retry)
        card.appendChild(button(t("retry"), "secondary", () => send(retry)));
      if (retry?.payload.action !== "confirm")
        card.appendChild(
          button(t("refresh"), "text-button", () =>
            send({ payload: { action: "view" } }),
          ),
        );
      card.append(
        button(t("bot"), "text-button", () => tg && tg.close()),
        el("p", "sub", t("fallback")),
      );
    }
    if (draft && !receipt)
      card.appendChild(
        el("p", "fine-print", t(confirmAttempted ? "checking" : "saved")),
      );
    container.appendChild(card);
  }
  async function send(operation) {
    if (busy) return;
    busy = true;
    error = "";
    draw();
    try {
      const payload = { init_data: tg.initData, ...operation.payload };
      const file = operation.file;
      const confirming = payload.action === "confirm";
      if (confirming) delete payload.action;
      const response = await fetch(
        confirming
          ? "/miniapp/api/confirm"
          : file
            ? "/miniapp/api/draft/upload"
            : "/miniapp/api/draft",
        {
          method: "POST",
          credentials: "same-origin",
          cache: "no-store",
          headers: file
            ? {
                "Content-Type":
                  file.type ||
                  {
                    pdf: "application/pdf",
                    png: "image/png",
                    jpg: "image/jpeg",
                    jpeg: "image/jpeg",
                    webp: "image/webp",
                    mp3: "audio/mpeg",
                    wav: "audio/wav",
                    ogg: "audio/ogg",
                  }[file.name.split(".").pop().toLowerCase()] ||
                  "application/octet-stream",
                "X-Telegram-Init-Data": tg.initData,
                "X-Draft-Revision": payload.revision,
                "X-Draft-Operation": payload.operation,
              }
            : { "Content-Type": "application/json" },
          body: file || JSON.stringify(payload),
        },
      );
      if (!response.ok) {
        if ([401, 403].includes(response.status)) {
          draft = null;
          receipt = null;
          agreed = false;
          entered = "";
          retry = null;
        }
        error =
          response.status === 429
            ? "rate"
            : response.status === 401
              ? "expired"
              : response.status === 403
                ? "denied"
                : response.status === 409
                  ? "conflict"
                  : [400, 413, 415].includes(response.status)
                    ? "invalid"
                    : "failure";
        if (response.status < 500) retry = null;
        if (confirming && response.status === 409) {
          const detail = (await response.json()).detail;
          // A definitive rejection permits correction; uncertain failures retain
          // the original confirmation operation for receipt recovery.
          confirmAttempted = false;
          agreed = false;
          error =
            {
              input_invalid: "invalid",
              insufficient: "funds",
              concurrent_limit: "concurrent",
              provider_config: "paused",
              service_ai_unavailable: "paused",
              cost_cap: "paused",
              user_cost_cap: "paused",
            }[detail] || "conflict";
        }
        return;
      }
      const result = await response.json();
      if (result.receipt) {
        receipt = result.receipt;
        draft = null;
        entered = "";
        agreed = false;
        retry = null;
        return;
      }
      if (result.draft?.confirmation?.token !== draft?.confirmation?.token)
        agreed = false;
      if (!result.draft || !draft || result.draft.revision !== draft.revision)
        entered = "";
      draft = result.draft;
      confirmAttempted = false;
      retry = null;
    } catch (_) {
      error = "failure";
    } finally {
      busy = false;
      draw();
      if (container && container.isConnected)
        document.getElementById("intake-title")?.focus();
    }
  }
  function mutate(action, extra = {}, file = null) {
    if (busy || !draft) return;
    const operation = {
      payload: {
        action,
        revision: draft.revision,
        operation: Array.from(
          crypto.getRandomValues(new Uint8Array(16)),
          (byte) => byte.toString(16).padStart(2, "0"),
        ).join(""),
        ...extra,
      },
      file,
    };
    retry = operation;
    return send(operation);
  }
  return {
    render(target, language) {
      container = target;
      lang = language;
      draw();
    },
    hide() {
      if (container) container.removeAttribute("aria-busy");
      container = null;
    },
    clear() {
      confirmAttempted = false;
      draft = null;
      receipt = null;
      agreed = false;
      entered = "";
      retry = null;
      if (container) container.removeAttribute("aria-busy");
      container = null;
    },
    open(slug) {
      if (busy) return;
      confirmAttempted = false;
      draft = null;
      receipt = null;
      agreed = false;
      entered = "";
      retry = null;
      return send({ payload: { action: "open", slug } });
    },
    get busy() {
      return busy;
    },
  };
};
