/* Signalbox Panel logic
 * - Loads config.json to get layoutDB, then loads that JSON
 * - Injects the SVG inline so we can colour & toggle elements
 * - Connects to MQTT over WebSocket to same host as the web server
 * - Provides context menus on sections/signals/points/plungers
 */

(function(){
  // ---------- Global state ----------
  const state = {
    cfg: null,
    layout: null,
    svg: null,
    mqtt: null,
    mqttConnected: false,
    wsPortCandidates: [9001, 8083, 80], // tweak if needed
    contextMenu: null
  };

  // ---------- DOM helpers ----------
  const el  = (sel, root=document) => root.querySelector(sel);
  const els = (sel, root=document) => Array.from(root.querySelectorAll(sel));

  function groupById(id) {
    if (!state.svg) return null;
    if (state.svg.getElementById) return state.svg.getElementById(id);
    return null;
  }
  const isGroup = (node) => node && node.tagName && node.tagName.toLowerCase() === "g";

  function setFillOnNodeOrGroup(node, colour) {
    if (!node) return;
    if (isGroup(node)) {
      els("ellipse,circle,rect,path,polygon,polyline,line", node).forEach(n => {
        const tg = n.tagName.toLowerCase();
        if (tg === "path" || tg === "polyline" || tg === "line") n.setAttribute("stroke", colour);
        else n.setAttribute("fill", colour);
      });
    } else {
      node.setAttribute("fill", colour);
    }
  }
  function setOffOnNodeOrGroup(node) {
    if (!node) return;
    if (isGroup(node)) {
      els("ellipse,circle,rect,path,polygon,polyline,line", node).forEach(n => {
        const tg = n.tagName.toLowerCase();
        if (tg === "path" || tg === "polyline" || tg === "line") n.setAttribute("stroke", "#666");
        else n.setAttribute("fill", "#666");
      });
    } else {
      node.setAttribute("fill", "#666");
    }
  }

  // ---------- Popup + diagnostics ----------
  function showPopup(title, bodyHtml) {
    el("#popupTitle").textContent = title;
    el("#popupBody").innerHTML = bodyHtml;
    el("#popup").classList.remove("hidden");
  }
  function hidePopup() { el("#popup").classList.add("hidden"); }
  function mqttError(msg) { showPopup("MQTT_error", `<p>${msg}</p>`); }

  function pushError(topic, payload) {
    const row = document.createElement("div");
    row.className = "error-row";
    const now = new Date().toLocaleTimeString();
    row.innerHTML = `<div class="time">${now}</div><div class="topic">${topic}</div><div class="payload">${payload}</div>`;
    el("#errors").prepend(row);
  }

  // Close popup buttons
  document.addEventListener("DOMContentLoaded", () => {
    const c = el("#popupClose"); if (c) c.addEventListener("click", hidePopup);
    const ok = el("#popupOk");  if (ok) ok.addEventListener("click", hidePopup);
  });

  // ---------- Config + Layout ----------
  async function loadConfigAndLayout() {
    const cfgRes = await fetch("/api/config");
    if (!cfgRes.ok) throw new Error("/api/config failed " + cfgRes.status);
    const cfg = await cfgRes.json();
    state.cfg = cfg;
    const label = el("#layoutDbLabel");
    if (label) label.textContent = `Layout: ${cfg.layoutDB}`;

    const layoutRes = await fetch(`/api/layout?file=${encodeURIComponent(cfg.layoutDB)}`);
    if (!layoutRes.ok) {
      const t = await layoutRes.text();
      mqttError(`/api/layout failed: ${layoutRes.status}`);
      pushError("api/layout", t.slice(0,200));
      throw new Error("layout fetch failed");
    }
    state.layout = await layoutRes.json();
  }

  // ---------- Inject SVG ----------
  async function mountSvg() {
    const res = await fetch("/static/images/layout.svg");
    const svgText = await res.text();
    el("#svgMount").innerHTML = svgText;
    state.svg = el("#svgMount svg");
    if (!state.svg) { pushError("svg", "No <svg> found after injection"); return; }
    verifyIdsAndReport();
    refreshFromLayout();
  }

  // ---------- MQTT ----------
  function tryConnectMqtt() {
    // Support both Paho.Client and Paho.MQTT.Client builds
    const PahoRoot = (window.Paho && (window.Paho.MQTT || window.Paho)) || null;
    const ClientCtor = PahoRoot && PahoRoot.Client;
    if (!ClientCtor) {
      mqttError("Paho MQTT client not found (expected window.Paho.MQTT.Client or window.Paho.Client).");
      pushError("mqtt", "Missing Paho client script");
      return;
    }

    const host = window.location.hostname;
    const candidates = state.wsPortCandidates.slice();
    function next() {
      if (!candidates.length) {
        el("#mqttStatus").textContent = "MQTT: disconnected";
        mqttError("Could not connect to MQTT via WebSocket. Check broker WS listener/port.");
        return;
      }
      const port = candidates.shift();
      // Change to "/" if your broker uses root path (common for Mosquitto)
      const path = "/mqtt";
      const clientId = "panel-" + Math.random().toString(16).slice(2);
      const client = new ClientCtor(host, Number(port), path, clientId);

      client.onConnectionLost = () => {
        state.mqttConnected = false;
        el("#mqttStatus").textContent = "MQTT: connection lost";
      };
      client.onMessageArrived = onMqttMessage;

      client.connect({
        timeout: 4,
        useSSL: window.location.protocol === "https:",
        onSuccess: () => {
          state.mqtt = client;
          state.mqttConnected = true;
          el("#mqttStatus").textContent = `MQTT: connected (ws://${host}:${port}${path})`;
          subscribeTopics();
        },
        onFailure: () => { next(); }
      });
    }
    next();
  }

  function subscribeTopics() {
    try { state.mqtt.subscribe("status/#"); }
    catch(err) { pushError("status/#", "subscribe failed: " + err.message); }
  }

  function onMqttMessage(message) {
    const topic = message.destinationName;
    const payload = message.payloadString || "";
    try {
      const data = JSON.parse(payload);
      if (topic.startsWith("status/section/")) {
        const ref = topic.split("/").pop();
        if (state.layout.Sections?.[ref]) { Object.assign(state.layout.Sections[ref], data); paintSection(ref); }
      } else if (topic.startsWith("status/signal/")) {
        const ref = topic.split("/").pop();
        if (state.layout.Signals?.[ref]) { if (data.aspect !== undefined) state.layout.Signals[ref].aspect = data.aspect; paintSignal(ref); }
      } else if (topic.startsWith("status/point/")) {
        const ref = topic.split("/").pop();
        if (state.layout.Points?.[ref]) { Object.assign(state.layout.Points[ref], data); paintPoint(ref); }
      } else if (topic.startsWith("errors/")) {
        pushError(topic, payload);
      }
    } catch {
      if (/error/i.test(payload)) pushError(topic, payload);
    }
  }

  function publish(topic, obj) {
    if (!state.mqttConnected) { mqttError("Not connected to MQTT."); return; }
    const MessageCtor = (window.Paho && (window.Paho.MQTT?.Message || window.Paho.Message)) || null;
    if (!MessageCtor) { pushError("mqtt", "No Paho Message constructor"); return; }
    const msg = new MessageCtor(JSON.stringify(obj));
    msg.destinationName = topic;
    try { state.mqtt.send(msg); }
    catch(err) { pushError(topic, "publish failed: " + err.message); }
  }

  // ---------- Painting ----------
  function refreshFromLayout() {
    Object.keys(state.layout.Sections || {}).forEach(ref => paintSection(ref));
    Object.keys(state.layout.Signals  || {}).forEach(ref => paintSignal(ref));
    Object.keys(state.layout.Points   || {}).forEach(ref => paintPoint(ref));
    Object.keys(state.layout.Plungers || {}).forEach(ref => attachPlungerContext(ref));
    renderRoutes();
  }

  function paintSection(ref) {
    const s = state.layout.Sections[ref] || {};
    const g = groupById(`Section-${ref}`); if (!g) return;
    const red = "#ff2d2d", white = "#ffffff", idle = "#bdbdbd";
    const colour = s.occstatus ? red : (s.routestatus ? white : idle);
    // colour strokes/fills of primitives inside the section group
    els("line,path,polyline,polygon,rect", g).forEach(n => {
      const tg = n.tagName.toLowerCase();
      n.setAttribute("stroke", colour);
      if (tg === "rect" || tg === "polygon") n.setAttribute("fill", colour);
    });
    // tooltips
    g.onmousemove = (e) => showTooltip(e, tooltipHtmlForSection(s));
    g.onmouseleave = hideTooltip;
  }

  function normAspect(a) {
    if (Array.isArray(a)) return a.map(normAspect).flat();
    if (a == null) return [];
    const s = String(a).toLowerCase().replace(/\s+/g,"_");
    const map = {
      red:"danger", stop:"danger", danger:"danger",
      yellow:"caution", single_yellow:"caution", caution:"caution",
      double_yellow:"doublecaution", doublecaution:"doublecaution",
      green:"clear", proceed:"clear", clear:"clear",
      pl:"position_light", position:"position_light", position_light:"position_light",
      apl:"associated_position_light", associated_position_light:"associated_position_light"
    };
    return [ map[s] || s ];
  }

  function paintSignal(ref) {
    const sig = (state.layout.Signals && state.layout.Signals[ref]) || {};
    // In draw.io exports, these ids are usually on <g> elements
    const main  = groupById(`Signal-${ref}-mainAspect`);
    const pos   = groupById(`Signal-${ref}-positionLight`);
    const assoc = groupById(`Signal-${ref}-assocPosLight`);

    const off="#666", red="#ff2d2d", yellow="#ffe066", green="#2dff70", white="#ffffff";
    setOffOnNodeOrGroup(main); setOffOnNodeOrGroup(pos); setOffOnNodeOrGroup(assoc);

    const aspects = normAspect(sig.aspect);
    if (aspects.includes("danger")) setFillOnNodeOrGroup(main, red);
    if (aspects.includes("doublecaution")) setFillOnNodeOrGroup(main, yellow);
    if (aspects.includes("caution")) setFillOnNodeOrGroup(main, yellow);
    if (aspects.includes("clear")) setFillOnNodeOrGroup(main, green);
    if (aspects.includes("position_light")) setFillOnNodeOrGroup(pos, white);
    if (aspects.includes("associated_position_light")) setFillOnNodeOrGroup(assoc, white);
  }

  function paintPoint(ref) {
    const pt = state.layout.Points?.[ref] || {};
    const a = groupById(`Point-${ref}-normal`);
    const b = groupById(`Point-${ref}-reverse`);
    if (!a && !b) return;
    const dir = pt.set_direction || pt.direction || (pt.detection_status || "normal");
    const isDetected = !!pt.detection_boolean;

    if (a) a.style.display = (dir === "normal") ? "inline" : "none";
    if (b) b.style.display = (dir === "reverse") ? "inline" : "none";

    const flashEl = (dir === "normal") ? a : b;
    if (flashEl && dir && !isDetected) {
      flashEl.classList.add("flash");
      els("*", flashEl).forEach(n => n.classList.add("flash"));
    } else {
      [a,b].forEach(node => {
        if (!node) return;
        node.classList.remove("flash");
        els("*", node).forEach(n => n.classList.remove("flash"));
      });
    }
  }

  function attachPlungerContext(ref) {
    const hit = groupById(`Plunger-${ref}`);
    if (hit) hit.dataset.plungerRef = ref;
  }

  // ---------- Context menus via event delegation ----------
  function closeContextMenu(){ if (state.contextMenu) state.contextMenu.remove(); state.contextMenu=null; }
  document.addEventListener("click", closeContextMenu);

  document.addEventListener("contextmenu", (e) => {
    if (!state.svg || !state.svg.contains(e.target)) return;
    e.preventDefault();
    const g = e.target.closest("[id]");
    if (!g) return;
    const id = g.id;
    const {pageX:x, pageY:y} = e;
    if (id.startsWith("Section-")) { sectionContextMenu(x,y,id.replace(/^Section-/,"")); return; }
    if (id.startsWith("Signal-"))  { const m=id.match(/^Signal-([^-\s]+)/); if (m) signalContextMenu(x,y,m[1]); return; }
    if (id.startsWith("Point-"))   { const m=id.match(/^Point-([^-\s]+)/);  if (m) pointContextMenu(x,y,m[1]); return; }
    if (id.startsWith("Plunger-")) { plungerContextMenu(x,y,id.replace(/^Plunger-/,"")); return; }
  });

  function makeMenu(x, y, items) {
    closeContextMenu();
    const m = document.createElement("div");
    m.className = "context-menu";
    m.style.left = x + "px"; m.style.top = y + "px";
    items.forEach(([label, handler]) => {
      const b = document.createElement("button");
      b.textContent = label;
      b.onclick = () => { handler(); closeContextMenu(); };
      m.appendChild(b);
    });
    document.body.appendChild(m);
    state.contextMenu = m;
  }

  function sectionContextMenu(x, y, ref) {
    const items = [
      ["Clear route(s) through section", () => publish("set/route", {action:"clear_section", section:ref})],
      ["Reset axle counter", () => { if (confirm(`Reset axle counter for ${ref}?`)) publish("set/section",{action:"reset_axle", section:ref}); }]
    ];
    const routes = state.layout.Routes || {};
    Object.keys(routes).forEach(r => {
      const route = routes[r];
      const uses = JSON.stringify(route).includes(ref);
      if (uses) items.push([`Set route ${r}`, () => publish("set/route", {action:"set", route:r})]);
    });
    makeMenu(x,y,items);
  }

  function signalContextMenu(x, y, ref) {
    makeMenu(x, y, [
      ["Danger", () => publish("set/signal", {ref, aspect:"danger"})],
      ["Caution", () => publish("set/signal", {ref, aspect:"caution"})],
      ["Clear", () => publish("set/signal", {ref, aspect:"clear"})],
      ["Position Light", () => publish("set/signal", {ref, aspect:"position_light"})],
      ["Assoc. Position Light", () => publish("set/signal", {ref, aspect:"associated_position_light"})]
    ]);
  }

  function pointContextMenu(x, y, ref) {
    makeMenu(x, y, [
      ["Set Normal", () => publish("set/point", {ref, direction:"normal"})],
      ["Set Reverse", () => publish("set/point", {ref, direction:"reverse"})]
    ]);
  }

  function plungerContextMenu(x, y, ref) {
    makeMenu(x, y, [
      ["Operate Plunger", () => publish("set/plunger", {ref, action:"operate"})]
    ]);
  }

  // ---------- Routes list ----------
  function renderRoutes() {
    const tbl = el("#routesTable");
    if (!tbl) return;
    tbl.innerHTML = "";
    const routes = state.layout.Routes || {};
    Object.keys(routes).forEach(r => {
      const tr = document.createElement("tr");
      tr.innerHTML = `<td class="_btnCell"><button data-r="${r}" class="btn">Set</button> <button data-r="${r}" data-clear class="btn btn--ghost">Clear</button></td><td>${r}</td><td class="_desc">${routes[r].description || ""}</td>`;
      tbl.appendChild(tr);
    });
    tbl.onclick = (e) => {
      const b = e.target.closest("button"); if (!b) return;
      const r = b.getAttribute("data-r");
      if (b.hasAttribute("data-clear")) publish("set/route", {action:"clear", route:r});
      else publish("set/route", {action:"set", route:r});
    };
  }

  // ---------- Tooltips ----------
  let tooltipDiv;
  function tooltipHtmlForSection(s) {
    const axles = (typeof s.occstatus === "number") ? s.occstatus : (s.occstatus ? 1 : 0);
    const trains = s.trains || [];
    const trainLines = trains.map(t => `${t.headcode || "—"} ${(t.locos||[]).join("+")}`).join("<br/>") || "No train";
    return `<div>Axles: <b>${axles}</b></div><div>${trainLines}</div>`;
  }
  function showTooltip(e, html) {
    if (!tooltipDiv) { tooltipDiv = document.createElement("div"); tooltipDiv.className = "tooltip"; document.body.appendChild(tooltipDiv); }
    tooltipDiv.innerHTML = html;
    tooltipDiv.style.left = e.pageX + "px";
    tooltipDiv.style.top  = e.pageY + "px";
    tooltipDiv.style.display = "block";
  }
  function hideTooltip() { if (tooltipDiv) tooltipDiv.style.display = "none"; }

  // ---------- Verification ----------
  function verifyIdsAndReport() {
    const issues = [];
    let foundSections = 0, foundSignals = 0, foundPoints = 0;
    Object.keys(state.layout.Sections || {}).forEach(ref => {
      const g = groupById(`Section-${ref}`);
      if (g) { foundSections++; g.style.outline = "1px dashed rgba(255,255,255,.15)"; setTimeout(()=>g.style.outline="none", 1200); }
      else issues.push(`Missing in SVG: Section-${ref}`);
    });
    Object.keys(state.layout.Signals || {}).forEach(ref => {
      const m = groupById(`Signal-${ref}-mainAspect`);
      if (m) { foundSignals++; }
      else issues.push(`Missing in SVG: Signal-${ref}-mainAspect`);
    });
    Object.keys(state.layout.Points || {}).forEach(ref => {
      const a = groupById(`Point-${ref}-normal`), b=groupById(`Point-${ref}-reverse`);
      if (a || b) { foundPoints++; }
      else issues.push(`Missing in SVG: Point-${ref}-normal/-reverse`);
    });
    console.groupCollapsed("%cSVG verification","color:#9cf");
    console.log("Found:", {sections:foundSections, signals:foundSignals, points:foundPoints});
    if (issues.length) console.warn("Mismatches:", issues);
    console.groupEnd();
  }

  // ---------- ARS toggle ----------
  document.addEventListener("DOMContentLoaded", () => {
    const ars = el("#arsToggle");
    if (ars) ars.addEventListener("change", (e) => publish("set/ars", {enabled: e.target.checked}));
  });

  // ---------- Boot ----------
  (async function init(){
    await loadConfigAndLayout();
    await mountSvg();
    tryConnectMqtt();
  })();
})();
