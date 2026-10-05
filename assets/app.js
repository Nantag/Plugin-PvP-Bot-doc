/* PvpBot Wiki - theme, mobile menu, search, copy buttons and the "on this page" highlight. No dependencies. */
(function () {
  "use strict";

  function store(key, value) {
    try {
      if (value === undefined) return localStorage.getItem(key);
      if (value === null) localStorage.removeItem(key); else localStorage.setItem(key, value);
    } catch (e) { return null; }
  }

  // ---- theme ----------------------------------------------------------------------------------
  var root = document.documentElement;
  var toggle = document.getElementById("theme");
  function effectiveDark() {
    var t = root.getAttribute("data-theme");
    if (t) return t === "dark";
    return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
  }
  // The button holds a moon and a sun icon; the stylesheet shows the one for the theme you would switch to.
  function paint() { root.classList.toggle("is-dark", effectiveDark()); }
  if (toggle) {
    toggle.addEventListener("click", function () {
      var next = effectiveDark() ? "light" : "dark";
      root.setAttribute("data-theme", next);
      store("pvpbot-theme", next);
      paint();
    });
  }
  paint();

  // ---- mobile menu ----------------------------------------------------------------------------
  var menu = document.getElementById("menu");
  if (menu) {
    menu.addEventListener("click", function () { document.body.classList.toggle("nav-open"); });
    document.addEventListener("click", function (e) {
      if (document.body.classList.contains("nav-open") && !e.target.closest(".sidebar") && e.target !== menu) {
        document.body.classList.remove("nav-open");
      }
    });
  }

  // ---- copy buttons ---------------------------------------------------------------------------
  document.querySelectorAll("pre").forEach(function (pre) {
    var b = document.createElement("button");
    b.className = "copy";
    b.type = "button";
    b.textContent = "Copy";
    b.addEventListener("click", function () {
      var text = pre.querySelector("code") ? pre.querySelector("code").innerText : pre.innerText;
      var done = function () { b.textContent = "Copied!"; setTimeout(function () { b.textContent = "Copy"; }, 1200); };
      if (navigator.clipboard) navigator.clipboard.writeText(text).then(done, function () {});
    });
    pre.appendChild(b);
  });

  // ---- search ---------------------------------------------------------------------------------
  var input = document.getElementById("q");
  var box = document.getElementById("results");
  var index = window.PVPBOT_INDEX || [];
  var selected = -1;

  function norm(s) { return (s || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, ""); }
  function esc(s) { return s.replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function mark(text, terms) {
    var out = esc(text);
    terms.forEach(function (t) {
      if (t.length < 2) return;
      out = out.replace(new RegExp("(" + t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + ")", "ig"), "<mark>$1</mark>");
    });
    return out;
  }
  function snippet(text, terms) {
    var n = norm(text), at = -1;
    for (var i = 0; i < terms.length && at < 0; i++) at = n.indexOf(terms[i]);
    if (at < 0) return text.slice(0, 120);
    var from = Math.max(0, at - 50);
    return (from > 0 ? "…" : "") + text.slice(from, from + 140) + "…";
  }
  function search(q) {
    var terms = norm(q).split(/\s+/).filter(Boolean);
    if (!terms.length) return [];
    var hits = [];
    index.forEach(function (e) {
      var title = norm(e.title), page = norm(e.page), body = norm(e.text);
      var score = 0;
      for (var i = 0; i < terms.length; i++) {
        var t = terms[i], s = 0;
        if (title.indexOf(t) >= 0) s += title.indexOf(t) === 0 ? 12 : 8;
        if (page.indexOf(t) >= 0) s += 3;
        if (body.indexOf(t) >= 0) s += 2;
        if (!s) return; // every term must match somewhere
        score += s;
      }
      hits.push({ e: e, score: score });
    });
    hits.sort(function (a, b) { return b.score - a.score; });
    return hits.slice(0, 12).map(function (h) { return h.e; });
  }
  function render(q) {
    var terms = norm(q).split(/\s+/).filter(Boolean);
    var hits = search(q);
    selected = -1;
    if (!q.trim()) { box.classList.remove("open"); box.innerHTML = ""; return; }
    if (!hits.length) {
      box.innerHTML = '<div class="empty">No results for “' + esc(q) + '”</div>';
    } else {
      box.innerHTML = hits.map(function (e) {
        return '<a href="' + e.url + '"><span class="r-title">' + mark(e.title, terms) + '</span> <span class="r-page">· ' + esc(e.page) +
          '</span><span class="r-snip">' + mark(snippet(e.text, terms), terms) + "</span></a>";
      }).join("");
    }
    box.classList.add("open");
  }
  function move(d) {
    var items = box.querySelectorAll("a");
    if (!items.length) return;
    selected = (selected + d + items.length) % items.length;
    items.forEach(function (a, i) { a.classList.toggle("active", i === selected); });
    items[selected].scrollIntoView({ block: "nearest" });
  }
  if (input && box) {
    input.addEventListener("input", function () { render(input.value); });
    input.addEventListener("focus", function () { if (input.value) render(input.value); });
    input.addEventListener("keydown", function (e) {
      if (e.key === "ArrowDown") { e.preventDefault(); move(1); }
      else if (e.key === "ArrowUp") { e.preventDefault(); move(-1); }
      else if (e.key === "Enter") {
        var items = box.querySelectorAll("a");
        var go = items[selected >= 0 ? selected : 0];
        if (go) window.location.href = go.getAttribute("href");
      } else if (e.key === "Escape") { box.classList.remove("open"); input.blur(); }
    });
    document.addEventListener("click", function (e) { if (!e.target.closest(".search")) box.classList.remove("open"); });
    document.addEventListener("keydown", function (e) {
      if (e.key === "/" && document.activeElement !== input && !/input|textarea/i.test(document.activeElement.tagName)) {
        e.preventDefault();
        input.focus();
      }
    });
  }

  // ---- "on this page" -------------------------------------------------------------------------
  var tocLinks = Array.prototype.slice.call(document.querySelectorAll(".toc a"));
  if (tocLinks.length && "IntersectionObserver" in window) {
    var byId = {};
    tocLinks.forEach(function (a) { byId[a.getAttribute("href").slice(1)] = a; });
    var visible = {};
    var obs = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { visible[en.target.id] = en.isIntersecting; });
      var first = null;
      document.querySelectorAll("article h2[id], article h3[id]").forEach(function (h) {
        if (!first && visible[h.id]) first = h.id;
      });
      if (first) tocLinks.forEach(function (a) { a.classList.toggle("active", a === byId[first]); });
    }, { rootMargin: "-70px 0px -65% 0px" });
    document.querySelectorAll("article h2[id], article h3[id]").forEach(function (h) { obs.observe(h); });
  }
})();
