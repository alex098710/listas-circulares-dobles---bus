// Talks to the Python code in one of two ways:
//  - local server (python server.py): normal HTTP requests to /api/...
//  - static hosting (Vercel, GitHub Pages): the same .py files run inside
//    the browser with Pyodide
const PYODIDE_URL = "https://cdn.jsdelivr.net/pyodide/v0.27.5/full/";
const PYTHON_FILES = document.currentScript.dataset.modules.split(" ");

async function hasLocalServer() {
  if (location.protocol === "file:" || new URLSearchParams(location.search).get("python") === "browser") {
    return false;
  }
  try {
    const response = await fetch("/api/state");
    return (response.headers.get("Content-Type") || "").includes("application/json");
  } catch {
    return false;
  }
}

function loadScript(src) {
  return new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = src;
    script.onload = resolve;
    script.onerror = () => reject(new Error(`No se pudo cargar ${src}`));
    document.head.appendChild(script);
  });
}

function showLoader() {
  const loader = document.createElement("div");
  loader.id = "py-loader";
  loader.innerHTML = `<div><div class="spinner"></div><p>Cargando Python en el navegador…</p><small>La primera vez puede tardar unos segundos</small></div>`;
  loader.style.cssText =
    "position:fixed;inset:0;display:grid;place-items:center;background:#000a;color:#fff;" +
    "font-family:system-ui,sans-serif;text-align:center;z-index:99";
  const style = document.createElement("style");
  style.textContent =
    "#py-loader .spinner{width:42px;height:42px;margin:0 auto 12px;border:4px solid #fff4;" +
    "border-top-color:#fff;border-radius:50%;animation:py-spin 1s linear infinite}" +
    "@keyframes py-spin{to{transform:rotate(360deg)}}";
  document.head.appendChild(style);
  document.body.appendChild(loader);
  return loader;
}

async function startPyodide() {
  const loader = showLoader();
  await loadScript(`${PYODIDE_URL}pyodide.js`);
  const pyodide = await loadPyodide({ indexURL: PYODIDE_URL });
  for (const file of PYTHON_FILES) {
    const source = await fetch(`../${file}`).then((r) => r.text());
    pyodide.FS.writeFile(file, source);
  }
  pyodide.runPython(`
import json, sys
sys.path.insert(0, ".")
import api

def call(action, body):
    payload, status = api.handle(action, json.loads(body))
    return json.dumps(payload, ensure_ascii=False)
`);
  const call = pyodide.globals.get("call");
  loader.remove();
  return (action, body) => JSON.parse(call(action, JSON.stringify(body)));
}

// resolves to a Python caller in Pyodide mode, or null when the local server answers
const pythonReady = hasLocalServer().then((server) => (server ? null : startPyodide()));

window.backend = {
  async state() {
    const python = await pythonReady;
    if (python) return python("state", {});
    return fetch("/api/state").then((r) => r.json());
  },
  async request(action, body = {}) {
    const python = await pythonReady;
    if (python) return python(action, body);
    const response = await fetch(`/api/${action}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    return response.json();
  },
};
