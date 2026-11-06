/*
 * Anomalon design system v1 — behaviour.
 * Load:  <script src="https://anomalon.com/ds/v1/anomalon.js" defer></script>
 * No dependencies. Safe to load twice.
 */
(function () {
  "use strict";
  if (window.Anomalon) return;
  var HOME = "https://anomalon.com";
  var MARK =
    '<svg viewBox="0 0 22 22" aria-hidden="true"><rect x="1" y="1" width="20" height="20" rx="4" fill="none" stroke="currentColor" stroke-width="1.6"/>' +
    '<path d="M6 15.5 11 6l5 9.5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/>' +
    '<circle cx="11" cy="12.6" r="1.7" fill="var(--an-accent)"/></svg>';

  function esc(s) { return String(s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); }

  function parseNav(spec) {
    if (!spec) return [];
    return spec.split(",").map(function (pair) {
      var i = pair.indexOf("=");
      return i < 0 ? null : { label: pair.slice(0, i).trim(), href: pair.slice(i + 1).trim() };
    }).filter(Boolean);
  }

  function isCurrent(href) {
    try {
      var u = new URL(href, location.href);
      if (u.origin !== location.origin) return false;
      var a = u.pathname.replace(/\/index\.html$/, "/").replace(/\.html$/, "");
      var b = location.pathname.replace(/\/index\.html$/, "/").replace(/\.html$/, "");
      return a === b && (!u.hash || u.hash === location.hash);
    } catch (e) { return false; }
  }

  function header(el) {
    var tool = el.getAttribute("data-tool");
    var home = el.getAttribute("data-home") || HOME + "/";
    var items = parseNav(el.getAttribute("data-nav"));
    if (!el.hasAttribute("data-no-all")) items.push({ label: tool ? "All tools" : "Tools", href: HOME + "/" });
    var nav = items.map(function (it) {
      return '<a href="' + esc(it.href) + '"' + (isCurrent(it.href) ? ' aria-current="page"' : "") + ">" + esc(it.label) + "</a>";
    }).join("");
    var id = "an-nav-" + Math.random().toString(36).slice(2, 8);
    el.outerHTML =
      '<header class="an-header"><div class="an-header__in">' +
      '<a class="an-brand" href="' + esc(home) + '">' + MARK + "Anomalon" + (tool ? ' <span class="an-brand__tool">/ ' + esc(tool) + "</span>" : "") + "</a>" +
      (nav ? '<button class="an-btn an-btn--ghost an-nav__toggle" aria-expanded="false" aria-controls="' + id + '">Menu</button>' +
        '<nav class="an-nav" id="' + id + '" aria-label="Main">' + nav + "</nav>" : "") +
      "</div></header>";
  }

  function footer(el) {
    var tool = el.getAttribute("data-tool");
    var src = el.getAttribute("data-source");
    var year = new Date().getFullYear();
    el.outerHTML =
      '<footer class="an-footer"><div class="an-footer__in">' +
      "<span>" + (tool ? "Anomalon · " + esc(tool) : "© " + year + " Anomalon") + "</span>" +
      (src ? '<a href="' + esc(src) + '">Source</a>' : "") +
      '<a href="' + HOME + '/about/">About</a><a href="' + HOME + '/contact/">Contact</a>' +
      "</div></footer>";
  }

  function copyText(text, btn) {
    var done = function () { var t = btn.textContent; btn.textContent = "Copied"; setTimeout(function () { btn.textContent = t; }, 1400); };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(done, function () { fallback(text); done(); });
    } else { fallback(text); done(); }
  }
  function fallback(text) {
    var ta = document.createElement("textarea"); ta.value = text; ta.setAttribute("readonly", "");
    ta.style.position = "fixed"; ta.style.opacity = "0"; document.body.appendChild(ta); ta.select();
    try { document.execCommand("copy"); } catch (e) {} document.body.removeChild(ta);
  }

  function init(root) {
    root = root || document;
    root.querySelectorAll("[data-an-header]").forEach(header);
    root.querySelectorAll("[data-an-footer]").forEach(footer);
  }

  document.addEventListener("click", function (ev) {
    var t = ev.target.closest && ev.target.closest(".an-nav__toggle");
    if (t) {
      var nav = document.getElementById(t.getAttribute("aria-controls"));
      var open = t.getAttribute("aria-expanded") !== "true";
      t.setAttribute("aria-expanded", String(open)); if (nav) nav.setAttribute("data-open", String(open));
      return;
    }
    var c = ev.target.closest && ev.target.closest("[data-an-copy]");
    if (c) {
      var sel = c.getAttribute("data-an-copy");
      var src = sel ? document.querySelector(sel) : c.parentElement.querySelector("pre, code");
      if (src) copyText(src.innerText, c);
    }
  });

  window.Anomalon = { init: init, version: "1.3.0" };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", function () { init(); });
  else init();
})();
