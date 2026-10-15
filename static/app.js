const ROAD_RADIUS = 215;
const svg = document.getElementById("map");
const toast = document.getElementById("toast");
const originSelect = document.getElementById("in-origin");
const targetSelect = document.getElementById("in-target");
let state = null;
let plan = null;
let busAngle = null;
let busy = false;

const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

function polar(radius, degrees) {
  const rad = (degrees * Math.PI) / 180;
  return [radius * Math.cos(rad), radius * Math.sin(rad)];
}

function arcPath(radius, fromDeg, toDeg, clockwise) {
  const [x1, y1] = polar(radius, fromDeg);
  const [x2, y2] = polar(radius, toDeg);
  let span = clockwise ? toDeg - fromDeg : fromDeg - toDeg;
  span = ((span % 360) + 360) % 360;
  return `M ${x1} ${y1} A ${radius} ${radius} 0 ${span > 180 ? 1 : 0} ${clockwise ? 1 : 0} ${x2} ${y2}`;
}

function escapeHtml(text) {
  return String(text).replace(/[&<>"']/g, (c) => `&#${c.charCodeAt(0)};`);
}

function showToast(message, isError = false) {
  toast.textContent = message;
  toast.classList.toggle("error", isError);
  toast.classList.add("show");
  clearTimeout(showToast.timer);
  showToast.timer = setTimeout(() => toast.classList.remove("show"), 2600);
}

async function api(action, body = {}) {
  const response = await fetch(`/api/${action}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await response.json();
  if (data.error) showToast(data.error, true);
  return data;
}

// ------------------------------------------------------------------ geometry
function stationNames() {
  return state.stations.map((s) => s.name);
}

function angleOf(name) {
  const index = stationNames().indexOf(name);
  return -90 + (index * 360) / state.stations.length;
}

// ------------------------------------------------------------------ the bus
function drawBus(angle) {
  document.getElementById("bus").setAttribute("transform", `rotate(${angle}) translate(${ROAD_RADIUS} 0)`);
}

function placeBus(angle, direction = null) {
  if (busAngle === null) {
    busAngle = angle;
    return drawBus(angle);
  }
  let delta = (((angle - busAngle) % 360) + 360) % 360; // clockwise distance
  if (direction === "backward" && delta > 0) delta -= 360;
  else if (!direction && delta > 180) delta -= 360;

  const start = busAngle;
  const startTime = performance.now();
  busAngle += delta;
  const frame = (now) => {
    const t = Math.min((now - startTime) / 420, 1);
    const eased = t < 0.5 ? 2 * t * t : 1 - (-2 * t + 2) ** 2 / 2;
    drawBus(start + delta * eased);
    if (t < 1) requestAnimationFrame(frame);
  };
  requestAnimationFrame(frame);
}

async function driveAlong(path, direction) {
  for (const name of path.slice(1)) {
    placeBus(angleOf(name), direction);
    await wait(480);
  }
}

// ------------------------------------------------------------------ render
function renderMap() {
  const stations = state.stations;
  const count = stations.length;
  const layer = document.getElementById("layer");
  const step = 360 / Math.max(count, 1);
  const gap = Math.min(step / 2 - 1, 7);

  let markup = `
    <circle class="park" r="${ROAD_RADIUS - 17}"/>
    <circle class="road" r="${ROAD_RADIUS}"/>
    <circle class="road-line" r="${ROAD_RADIUS}"/>
    <text class="center-title" y="-8">Ruta Circular</text>
    <text class="center-sub" y="14">${count} estaciones enlazadas</text>`;

  if (count === 0) {
    layer.innerHTML = markup + `<text class="center-sub" y="40">Abre una estación para empezar</text>`;
    document.getElementById("bus").style.display = "none";
    return;
  }

  // highlighted shortest-route options
  if (plan && plan.forward_stops > 0) {
    const from = angleOf(plan.forward[0]);
    const to = angleOf(plan.forward.at(-1));
    markup += `<path class="route-forward" d="${arcPath(ROAD_RADIUS + 9, from, to, true)}"
      opacity="${plan.best === "forward" ? 1 : .35}"/>`;
    markup += `<path class="route-backward" d="${arcPath(ROAD_RADIUS - 9, from, to, false)}"
      opacity="${plan.best === "backward" ? 1 : .35}"/>`;
  }

  // next links (outside the road) and prev links (inside the road)
  if (count > 1) {
    stations.forEach((station, index) => {
      const from = -90 + index * step;
      const to = from + step;
      markup += `<path class="link-next" marker-end="url(#arrow-next)" d="${arcPath(ROAD_RADIUS + 30, from + gap, to - gap, true)}"/>`;
      markup += `<path class="link-prev" marker-end="url(#arrow-prev)" d="${arcPath(ROAD_RADIUS - 30, to - gap, from + gap, false)}"/>`;
    });
  }

  stations.forEach((station) => {
    const angle = angleOf(station.name);
    const [x, y] = polar(ROAD_RADIUS, angle);
    const [lx, ly] = polar(ROAD_RADIUS + 66, angle);
    const classes = ["station"];
    if (station.name === targetSelect.value && plan) classes.push("target");
    const labels = [];
    if (station.name === state.head) labels.push("PRIMERA");
    if (station.name === state.tail) labels.push("ÚLTIMA");
    markup += `
      <g class="${classes.join(" ")}" data-name="${escapeHtml(station.name)}">
        <title>Clic para elegir ${escapeHtml(station.name)} como destino</title>
        <circle cx="${x}" cy="${y}" r="11"/>
        <g transform="translate(${lx} ${ly})">
          ${labels.length ? `<text class="label" y="-20">${labels.join(" · ")}</text>` : ""}
          <text y="-4">${escapeHtml(station.name)}</text>
          <text class="waiting" y="12">👥 ${station.waiting}</text>
        </g>
      </g>`;
  });

  layer.innerHTML = markup;
  layer.querySelectorAll(".station").forEach((node) => {
    node.addEventListener("click", () => {
      targetSelect.value = node.dataset.name;
      requestPlan();
    });
  });
  document.getElementById("bus").style.display = "";
}

function fillSelect(select, options, keep) {
  const previous = select.value;
  select.innerHTML = options.map(([value, label]) => `<option value="${escapeHtml(value)}">${escapeHtml(label)}</option>`).join("");
  const values = options.map(([value]) => value);
  if (keep && values.includes(keep)) select.value = keep;
  else if (values.includes(previous)) select.value = previous;
}

function renderPanel() {
  const names = stationNames();
  document.getElementById("st-bus").textContent = state.bus ?? "—";
  document.getElementById("st-board").textContent = `${state.on_board}/${state.capacity}`;
  document.getElementById("st-delivered").textContent = state.delivered;
  document.getElementById("st-size").textContent = state.size;

  fillSelect(originSelect, names.map((n) => [n, n]), state.bus);
  fillSelect(targetSelect, names.map((n) => [n, n]));
  fillSelect(document.getElementById("in-after"),
    [["", "Al final (antes de la primera)"], ...names.map((n) => [n, `Después de ${n}`])]);
  fillSelect(document.getElementById("in-close"), names.map((n) => [n, n]));

  const loop = (list, arrow) =>
    list.length ? `${list.map(escapeHtml).join(` ${arrow} `)} ${arrow} <i>${escapeHtml(list[0])}…</i>` : "vacía";
  const reversed = names.length ? [names[0], ...names.slice(1).reverse()] : [];
  document.getElementById("trav-next").innerHTML = loop(names, "→");
  document.getElementById("trav-prev").innerHTML = loop(reversed, "←");

  document.getElementById("pointers").innerHTML = state.stations
    .map((s) => `<tr><td>${escapeHtml(s.prev)}</td><td><b>${escapeHtml(s.name)}</b></td><td>${escapeHtml(s.next)}</td><td>${s.waiting}</td></tr>`)
    .join("");
  document.getElementById("log").innerHTML = state.log.map((line) => `<li>${escapeHtml(line)}</li>`).join("");

  const planBox = document.getElementById("plan");
  if (!plan) {
    planBox.innerHTML = `<p class="hint">Elige origen y destino, o haz clic en una estación del mapa.</p>`;
  } else if (plan.forward_stops === 0) {
    planBox.innerHTML = `<p class="hint">El origen y el destino son la misma estación.</p>`;
  } else {
    const option = (key, title) => `
      <div class="option ${key} ${plan.best === key ? "best" : ""}">
        <b>${title}: ${plan[`${key}_stops`]} paradas ${plan.best === key ? "✔ más corta" : ""}</b>
        <span>${plan[key].map(escapeHtml).join(key === "forward" ? " → " : " ← ")}</span>
      </div>`;
    planBox.innerHTML = option("forward", "Por next ➡️") + option("backward", "Por prev ⬅️");
  }
}

function render(newState, { moveBus = true } = {}) {
  state = newState;
  if (plan && !(stationNames().includes(plan.forward[0]) && stationNames().includes(plan.forward.at(-1)))) {
    plan = null;
  }
  renderMap();
  renderPanel();
  if (moveBus && state.bus) placeBus(angleOf(state.bus));
}

// ------------------------------------------------------------------ actions
async function requestPlan() {
  if (!originSelect.value || !targetSelect.value) return;
  const data = await api("plan", { origin: originSelect.value, target: targetSelect.value });
  plan = data.result ?? null;
  render(data);
}

function setBusy(value) {
  busy = value;
  document.querySelectorAll("button").forEach((b) => (b.disabled = value));
}

async function drive(direction) {
  if (busy) return;
  const data = await api(direction);
  if (data.error) return render(data);
  plan = null;
  render(data, { moveBus: false });
  placeBus(angleOf(data.bus), direction);
}

document.querySelectorAll("[data-action]").forEach((button) => {
  button.addEventListener("click", async () => {
    const action = button.dataset.action;
    if (action === "forward" || action === "backward") return drive(action);
    render(await api(action));
  });
});

document.getElementById("btn-travel").addEventListener("click", async () => {
  if (busy || !targetSelect.value) return;
  const target = targetSelect.value;
  if (target === state.bus) return showToast("El bus ya está en esa estación");
  setBusy(true);
  const data = await api("travel", { target });
  if (data.error) {
    setBusy(false);
    return render(data);
  }
  plan = data.result;
  render(data, { moveBus: false });
  await driveAlong(plan[plan.best], plan.best);
  showToast(`🚌 Llegó a ${target} en ${plan[`${plan.best}_stops`]} paradas`);
  plan = null;
  render(data, { moveBus: false });
  setBusy(false);
});

originSelect.addEventListener("change", requestPlan);
targetSelect.addEventListener("change", requestPlan);

document.getElementById("form-add").addEventListener("submit", async (event) => {
  event.preventDefault();
  const name = document.getElementById("in-name").value;
  const waiting = document.getElementById("in-waiting").value;
  const after = document.getElementById("in-after").value;
  const data = await api("add", { name, waiting, after });
  render(data);
  if (!data.error) {
    document.getElementById("in-name").value = "";
    showToast(`Estación ${name} abierta`);
  }
});

document.getElementById("btn-close").addEventListener("click", async () => {
  const name = document.getElementById("in-close").value;
  if (name && confirm(`¿Cerrar la estación ${name}? Sus vecinas quedarán enlazadas entre sí.`)) {
    render(await api("close", { name }));
  }
});

document.getElementById("btn-reset").addEventListener("click", async () => {
  if (confirm("¿Borrar todas las estaciones?")) {
    plan = null;
    render(await api("reset"));
  }
});

// static SVG skeleton: markers, a layer that is redrawn, and the persistent bus
svg.innerHTML = `
  <defs>
    <marker id="arrow-next" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" fill="#1b998b"/>
    </marker>
    <marker id="arrow-prev" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" fill="#f46036"/>
    </marker>
  </defs>
  <g id="layer"></g>
  <g id="bus">
    <rect x="-13" y="-24" width="26" height="48" rx="6"/>
    <rect class="window" x="-9" y="-19" width="18" height="9" rx="2"/>
    <rect class="window" x="-9" y="-6" width="18" height="6" rx="1"/>
    <rect class="window" x="-9" y="3" width="18" height="6" rx="1"/>
    <circle class="wheel" cx="-14" cy="-14" r="4"/><circle class="wheel" cx="14" cy="-14" r="4"/>
    <circle class="wheel" cx="-14" cy="14" r="4"/><circle class="wheel" cx="14" cy="14" r="4"/>
  </g>`;

fetch("/api/state").then((r) => r.json()).then((data) => render(data));
