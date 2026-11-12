/*
 * dc-lite: renders the design canvas's page templates in an ordinary browser.
 *
 * Each page carries its templates inline (written by tools/sync_from_canvas.py):
 *   <template id="dc-page">…</template>         the page's markup
 *   <script type="text/x-dc" data-for="page">   the page's Component class
 *   <template id="dc-Header">…</template>       one pair per child component
 *
 * Supported template syntax (the subset the canvas pages use):
 *   {{ a.b }} in text and attributes, <sc-for list as>, <sc-if value>,
 *   <dc-import name="X" prop="…">, and <helmet> (moved into <head>).
 */
(function () {
  "use strict";

  class DCLogic {
    constructor() { this.props = {}; this.state = {}; }
    setState(patch) { Object.assign(this.state, patch); }
    forceUpdate() {}
  }

  const HOLE = /\{\{\s*([^}]+?)\s*\}\}/g;
  const WHOLE = /^\s*\{\{\s*([^}]+?)\s*\}\}\s*$/;
  const classes = {};
  const seenHead = new Set();

  function lookup(path, scope) {
    path = path.trim();
    if (path === "true") return true;
    if (path === "false") return false;
    if (path === "null") return null;
    if (/^-?\d+(\.\d+)?$/.test(path)) return Number(path);
    if (/^(['"]).*\1$/.test(path)) return path.slice(1, -1);
    let value = scope;
    for (const part of path.split(".")) {
      if (value == null) return undefined;
      value = value[part];
    }
    return value;
  }

  function fill(text, scope) {
    return text.replace(HOLE, (_, path) => {
      const v = lookup(path, scope);
      return v == null ? "" : String(v);
    });
  }

  function componentClass(name) {
    if (classes[name]) return classes[name];
    const script = document.querySelector('script[type="text/x-dc"][data-for="' + name + '"]');
    if (!script) throw new Error("dc-lite: no logic for component " + name);
    const Cls = new Function("DCLogic", script.textContent + "\nreturn Component;")(DCLogic);
    let defaults = {};
    try {
      const declared = JSON.parse(script.getAttribute("data-props") || "{}");
      for (const key of Object.keys(declared)) {
        if (key[0] !== "$" && declared[key] && "default" in declared[key]) defaults[key] = declared[key].default;
      }
    } catch (e) { /* no declared props */ }
    classes[name] = { Cls, defaults };
    return classes[name];
  }

  function moveToHead(node) {
    const key = node.outerHTML;
    if (seenHead.has(key)) return;
    seenHead.add(key);
    document.head.appendChild(node);
  }

  function renderComponent(name, props) {
    const tpl = document.getElementById("dc-" + name);
    if (!tpl) throw new Error("dc-lite: no template for component " + name);
    const { Cls, defaults } = componentClass(name);
    const logic = new Cls();
    logic.props = Object.assign({}, defaults, props);
    const scope = logic.renderVals() || {};
    const out = document.createDocumentFragment();
    renderChildren(tpl.content, scope, out);
    return out;
  }

  function camel(attr) {
    return attr.replace(/-([a-z])/g, (_, c) => c.toUpperCase());
  }

  function renderChildren(source, scope, target) {
    for (const child of Array.from(source.childNodes)) renderNode(child, scope, target);
  }

  function renderNode(node, scope, target) {
    if (node.nodeType === Node.TEXT_NODE) {
      target.appendChild(document.createTextNode(fill(node.nodeValue, scope)));
      return;
    }
    if (node.nodeType !== Node.ELEMENT_NODE) return;
    const tag = node.localName;

    if (tag === "helmet") {
      for (const el of Array.from(node.children)) {
        if (el.localName === "link" || el.localName === "style") moveToHead(el.cloneNode(true));
      }
      return;
    }

    if (tag === "sc-for") {
      const m = WHOLE.exec(node.getAttribute("list") || "");
      const list = m ? lookup(m[1], scope) : null;
      const as = node.getAttribute("as") || "item";
      (Array.isArray(list) ? list : []).forEach((item, index) => {
        const inner = Object.create(scope);
        inner[as] = item;
        inner.$index = index;
        renderChildren(node, inner, target);
      });
      return;
    }

    if (tag === "sc-if") {
      const m = WHOLE.exec(node.getAttribute("value") || "");
      if (m && lookup(m[1], scope)) renderChildren(node, scope, target);
      return;
    }

    if (tag === "dc-import") {
      const props = {};
      for (const attr of Array.from(node.attributes)) {
        if (attr.name === "name" || attr.name.startsWith("hint-")) continue;
        const m = WHOLE.exec(attr.value);
        props[camel(attr.name)] = m ? lookup(m[1], scope) : fill(attr.value, scope);
      }
      target.appendChild(renderComponent(node.getAttribute("name"), props));
      return;
    }

    const el = node.namespaceURI === "http://www.w3.org/1999/xhtml"
      ? document.createElement(tag)
      : document.createElementNS(node.namespaceURI, node.tagName);
    for (const attr of Array.from(node.attributes)) {
      if (attr.name.startsWith("hint-")) continue;
      if (/^on[A-Z]/.test(attr.name)) continue; // canvas event bindings: not used on the site
      el.setAttribute(attr.name, fill(attr.value, scope));
    }
    if (tag === "template") {
      renderChildren(node.content, scope, el.content);
    } else {
      renderChildren(node, scope, el);
    }
    target.appendChild(el);
  }

  function boot() {
    try {
      document.body.prepend(renderComponent("page", {}));
    } catch (err) {
      console.error(err);
      const note = document.createElement("p");
      note.textContent = "This page could not be displayed. " + err.message;
      note.style.cssText = "padding:24px;font:16px system-ui;color:#b23a30";
      document.body.prepend(note);
    }
    const cloak = document.getElementById("dc-cloak");
    if (cloak) cloak.remove();
    if (location.hash) {
      const target = document.getElementById(location.hash.slice(1));
      if (target) target.scrollIntoView();
    }
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
