# 🚌 Ruta Circular de Bus: Lista Circular Doble

Taller de Estructuras de Datos. Caso de estudio: **una ruta de bus circular** (como las rutas alimentadoras o el circuito de un campus).

La ruta **no tiene fin**: después de la última estación el bus vuelve a la primera. Además, el bus puede ir **hacia adelante** (`next`) o **hacia atrás** (`prev`), así que para llegar a un destino puede **elegir el sentido más corto**. Eso solo es posible con una **lista circular doble**.

```
          ┌──────────── next ────────────┐
          ▼                              │
     [Terminal] ⇄ [Universidad] ⇄ ... ⇄ [Mercado]
          │                              ▲
          └──────────── prev ────────────┘
```

## 🌐 Ver en línea

**https://alex098710.github.io/listas-circulares-dobles---bus/**

En GitHub Pages el mismo código Python corre dentro del navegador con [Pyodide](https://pyodide.org). La primera carga tarda unos segundos.

## ▶️ Cómo ejecutarlo en tu computador

Solo necesitas Python 3.9 o superior (no hay que instalar librerías).

```bash
python server.py
```

Se abre el navegador en **http://localhost:5051**.

Para abrirlo desde un celular conectado al mismo WiFi: `python server.py --lan`.

Pruebas unitarias:

```bash
python -m unittest -v
```

## 🧱 Estructura del código (en inglés)

| Archivo | Contenido |
|---|---|
| `bus_route.py` | Clase `Station` (nodo) y clase `CircularRoute` (lista circular doble) |
| `api.py` | Acciones que puede pedir la página (las usa el servidor y la versión en línea) |
| `server.py` | Servidor web local (librería estándar de Python) |
| `index.html` | Entrada para GitHub Pages |
| `static/` | Interfaz en español (HTML, CSS y JavaScript) |
| `test_bus_route.py` | Pruebas unitarias |

### Clase `Station` (nodo)
| Atributo | Significado |
|---|---|
| `name` | Nombre de la estación |
| `waiting` | Pasajeros esperando |
| `next` | Estación siguiente |
| `prev` | Estación anterior |

### Clase `CircularRoute` (lista circular doble)
| Método | Operación de lista | En la ruta |
|---|---|---|
| `add_station(name, waiting, after)` | Insertar al final o después de un nodo | Abrir una estación |
| `close_station(name)` | Eliminar un nodo y re-enlazar a sus vecinos | Cerrar una estación |
| `find_station(name)` | Búsqueda | Buscar una estación |
| `traverse(start, direction)` | Recorrido en ambos sentidos | Ver el orden de la ruta |
| `move_forward()` / `move_backward()` | Avanzar por `next` / `prev` | Conducir el bus |
| `path_between(a, b, direction)` | Recorrido parcial entre dos nodos | Paradas entre dos estaciones |
| `shortest_direction(a, b)` | Comparar los dos recorridos | Ruta más corta |
| `travel_to(name)` | Recorrer por el sentido más corto | Llevar el bus a un destino |

### Casos especiales que maneja
- **Una sola estación:** su `next` y su `prev` apuntan a ella misma.
- **Cerrar la primera (`head`):** `head` pasa a la siguiente.
- **Cerrar la estación donde está el bus:** el bus avanza a la siguiente.
- **Cerrar la única estación:** la ruta queda vacía.
- **Recorrido sin ciclo infinito:** se para al volver al nodo de inicio, porque nunca aparece `None`.

## 🖥️ Interfaz
- Mapa circular con la vía, las estaciones (nodos) y el bus animado.
- Flechas **next** (verdes, por fuera) y **prev** (naranjas, punteadas, por dentro).
- Etiquetas **PRIMERA** y **ÚLTIMA**.
- Planeador de viaje: muestra las dos rutas posibles y marca la más corta.
- Formularios para abrir (insertar) y cerrar (eliminar) estaciones.
- Contadores de pasajeros a bordo y entregados, tabla de punteros y bitácora.

## 📝 Preguntas del taller
1. ¿Por qué una ruta de bus circular se modela mejor con una lista circular **doble**?
2. ¿Qué estación apunta a la primera con su `next`? ¿Y qué estación es el `prev` de la primera?
3. ¿Cuántos punteros cambian al abrir una estación entre otras dos? ¿Y al cerrarla?
4. ¿Qué pasa con `head` y con el bus si se cierra la estación donde está parado?
5. Explica cómo `shortest_direction` decide el sentido. ¿Qué pasa si los dos caminos tienen la misma cantidad de paradas?
6. ¿Por qué `path_between` nunca entra en un ciclo infinito si las dos estaciones existen?
7. ¿Cuál es la complejidad de `add_station`, `close_station` y `shortest_direction`?
8. Propón una mejora (por ejemplo, un segundo bus o estaciones expresas) y explica qué cambiaría en los nodos.
