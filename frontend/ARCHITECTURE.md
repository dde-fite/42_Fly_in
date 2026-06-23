# Fly In Visualizer — Guía de la codebase del frontend

Documento de referencia para **entender, presentar y explicar** todo el frontend.
Está pensado para leerse de arriba abajo: primero el qué y el porqué, luego la
arquitectura, y al final una chuleta de presentación con los puntos clave.

---

## 1. ¿Qué es esta aplicación?

**Fly In Visualizer** es la interfaz web que **visualiza una simulación de drones**
sobre una red de estaciones (*hubs*) conectadas. Los drones viajan desde un hub
**origen** hasta un hub **destino** atravesando conexiones con capacidad limitada,
**turno a turno**.

La metáfora visual es la de una **red ferroviaria / control de tráfico**:

- Cada **hub** se dibuja como una **estación** con andenes y vías horizontales.
- Cada **conexión** entre dos hubs se dibuja como un haz de **vías** (una por
  unidad de capacidad).
- Cada **drone** es una etiqueta que **aparca** en una vía de estación o **se
  desliza** (animado) por una vía de conexión cuando cambia de hub entre turnos.

El usuario:

1. Sube un **mapa** (`.txt`) → se crea la simulación.
2. **Avanza turnos** manualmente o deja que se reproduzca solo (play / fast).
3. **Navega** el lienzo con pan y zoom, y **selecciona** estaciones o conexiones
   para ver sus detalles.

> El backend es un servicio aparte (FastAPI). El frontend solo consume su API REST.

---

## 2. Stack tecnológico

| Capa | Tecnología | Por qué |
|------|-----------|---------|
| UI | **React 18** + **TypeScript** | Componentes declarativos, tipado estricto. |
| Build / dev | **Vite 8** | Arranque y HMR rápidos. |
| Estado global | **Zustand** | Stores mínimos sin boilerplate (sin Redux). |
| Validación de datos | **Zod 4** | Esquemas que validan la respuesta del backend **y** generan los tipos TS. |
| Render del lienzo | **Konva** + **react-konva** | Grafo de escena 2D con pan/zoom/hit-testing sobre `<canvas>`. |
| Estilos | **Tailwind CSS 4** | Utilidades en el JSX, sin CSS a mano. |
| Iconos | **@tabler/icons-react** | Iconos de los controles de reproducción. |
| Lint / formato | **Biome** | Un solo binario para formatear y lintear (tabs, comillas dobles, ancho 80). |
| Tests | **Vitest** | Tests unitarios de la lógica pura (entorno `node`, sin DOM). |

---

## 3. Arquitectura en una imagen

Flujo de datos de extremo a extremo:

```
            +-------------+   sube .txt    +----------------------+
   Usuario -+   Header    +--------------->|   simulationStore    |
            | (menús,     |  newSimulation |  (Zustand)           |
            |  playback)  |  advanceSim    |  simulation, speed…  |
            +-------------+                +----------+-----------+
                                                       | llama
                                                       v
                                            +----------------------+
                                            |   services/api.ts    |
                                            |  fetch + Zod.parse   |
                                            +----------+-----------+
                                                       | HTTP REST
                                                       v
                                            +----------------------+
                                            |   Backend (FastAPI)  |
                                            +----------------------+

   simulation (objeto validado)
            |
            v
   +-------------------------+   construye "Scene"   +------------------------+
   |   SimulationCanvas      +---------------------->|  canvas/ (lógica pura) |
   |  (orquesta hooks +      |                       |  view, scene, geometry,|
   |   Konva Stage/Layer)    |<----------------------+  track, render/entity… |
   +-------------------------+   dibuja / hit-test   +------------------------+
```

Idea central: **el estado vive en los stores**, **los datos se validan en la capa
api**, y **el lienzo es una función del estado**. La carpeta `canvas/` es **lógica
pura** (sin React, sin Konva) que sabe convertir el modelo en píxeles; los
componentes Konva solo invocan esa lógica.

---

## 4. Estructura de carpetas

```
frontend/
+-- index.html              # Punto de entrada HTML (div#root)
+-- vite.config.ts          # Config de build/dev (React + Tailwind + env)
+-- vitest.config.ts        # Config de tests (entorno node, tests/**)
+-- biome.json              # Formato + lint
+-- package.json
+-- tests/                  # Tests unitarios de la lógica pura de canvas/
+-- src/
    +-- main.tsx            # Monta <App/> en #root
    +-- App.tsx             # Layout raíz: Header + canvas o "sube un mapa"
    +-- style.css           # Tailwind + estilos globales (rainbow, etc.)
    |
    +-- schemas/            # Esquemas Zod (fuente de verdad de los datos)
    |   +-- hub.ts  connection.ts  drone.ts  token.ts
    |   +-- simulation.ts   # Raw (del backend) y enriquecido (objetos completos)
    |
    +-- types/              # Tipos TS derivados de los esquemas (z.infer)
    |   +-- simulation.ts   # Hub, Connection, Drone, Simulation
    |   +-- api.ts          # Token
    |
    +-- services/
    |   +-- api.ts          # Todas las llamadas HTTP + validación Zod
    |
    +-- store/              # Estado global (Zustand)
    |   +-- sessionStore.ts     # token, isLoading, error
    |   +-- simulationStore.ts  # simulation, playbackSpeed, fitViewTrigger
    |
    +-- hooks/              # Lógica reutilizable (sin UI)
    |   +-- usePlayback.ts       # Bucle de auto-avance (play/fast)
    |   +-- useKeypress.ts       # Atajos de teclado
    |   +-- useCanvasView.ts     # Pan/zoom/resize/auto-fit del lienzo
    |   +-- useRainbowRedraw.ts  # Redibuja mientras haya hubs "rainbow"
    |   +-- useDroneAnimation.ts # Anima el deslizamiento de drones por turno
    |
    +-- canvas/             # LÓGICA PURA del lienzo (sin React/Konva)
    |   +-- view.ts         # Transformada modelo→píxel, zoom, auto-fit
    |   +-- scene.ts        # Tipos Scene y DroneMove
    |   +-- geometry.ts     # Tamaño de la caja de estación, vías, drones
    |   +-- track.ts        # Geometría de vías de estación y de conexión
    |   +-- moves.ts        # Calcula qué drones se movieron entre dos turnos
    |   +-- colors.ts       # Cache de color estable por drone
    |   +-- palette.ts      # Constantes de color + lógica "rainbow"
    |   +-- primitives.ts   # Dibujos base (vía, bloque, etiqueta de drone)
    |   +-- hitTest.ts      # Resolver clic → hub o conexión
    |   +-- render/
    |       +-- entity.ts   # Dibuja cada entidad (fondo, hub, conexión, drone)
    |
    +-- components/
        +-- Header.tsx              # Barra superior: título, menús, estado, playback
        +-- SimulationCanvas.tsx    # Orquesta el lienzo Konva
        +-- TokenDisplay.tsx        # Modal con el token de sesión
        +-- header/
        |   +-- AppMenuBar.tsx      # Menús desplegables (Archivo/Simulación/Vista)
        |   +-- menuTypes.ts        # Tipos Menu / MenuItem
        |   +-- NetworkStatus.tsx   # Contadores de hubs/conexiones/drones
        |   +-- PlaybackControls.tsx# Turno + botones pausa/play/fast
        +-- canvas/
            +-- CanvasToolbar.tsx       # Zoom +/- y "ajustar vista"
            +-- DetailPanel.tsx         # Carcasa flotante reutilizable + DetailRow
            +-- HubDetailPanel.tsx      # Detalle de una estación
            +-- ConnectionDetailPanel.tsx# Detalle de una conexión
            +-- panelStyles.ts          # Clases Tailwind compartidas de los paneles
            +-- konva/
                +-- SceneNodes.tsx      # Componentes Konva <Shape> que llaman a render/entity
```

**Regla de oro de la organización:** archivos pequeños, una responsabilidad cada
uno. `canvas/` no importa nada de React; `components/` no contiene matemáticas de
dibujo. Esa separación es lo que hace testeable la parte difícil.

---

## 5. Modelo de dominio (schemas + types)

La **fuente de verdad** son los esquemas Zod en `schemas/`. Los tipos de
`types/` se derivan con `z.infer`, así que **el tipo nunca puede desincronizarse
del validador**.

```ts
// schemas/hub.ts
HubSchema = { name, position:[x,y], access, color?, connections:uuid[], capacity, drones:uuid[] }
// schemas/connection.ts
ConnectionSchema = { name, hubs:[idA, idB], capacity }
// schemas/drone.ts
DroneSchema = { name, location:uuid, destination:uuid }
// schemas/token.ts
TokenSchema = z.base64url()   // el token de sesión es una cadena base64url
```

### Raw vs. enriquecido

El backend, al crear o avanzar la simulación, devuelve **solo listas de UUIDs**.
El frontend luego pide cada categoría completa y arma el objeto rico:

```ts
// schemas/simulation.ts
RawSimulationSchema  = { turn, hubs:uuid[], origin, destination, connections:uuid[], drones:uuid[] }
SimulationSchema     = { turn, hubs:Record<id,Hub>, origin, destination,
                         connections:Record<id,Connection>, drones:Record<id,Drone> }
```

`Hub`, `Connection`, `Drone`, `Simulation` (en `types/simulation.ts`) y `Token`
(en `types/api.ts`) son los tipos que circulan por toda la app.

**Concepto clave — `access`:** cada hub tiene un acceso (`"blocked"`,
`"priority"` u otro). Esto **colorea las vías** de las conexiones que tocan ese
hub (rojo si bloqueado, verde si prioritario, blanco si normal).

---

## 6. Estado global (Zustand)

Dos stores pequeños, cada uno con su responsabilidad.

### `sessionStore` — sesión y errores
```ts
{ token, isLoading, error, setError, setIsLoading, fetchToken }
```
- `fetchToken()` pide un token al backend al arrancar la app (`App.tsx`).
- `isLoading` y `error` son **transversales**: cualquier operación los actualiza.

### `simulationStore` — la simulación y la reproducción
```ts
{ simulation, fitViewTrigger, playbackSpeed,
  newSimulation, setSimulation, clearSimulation,
  advanceSimulation, requestFitView, setPlaybackSpeed }
```
- `newSimulation(file)` / `advanceSimulation(steps)` son las dos operaciones que
  cambian `simulation`. Ambas pasan por el helper **`loadSimulation`**, que
  centraliza `isLoading`/`error` (pone loading, captura excepciones, las vuelca a
  `error`). Patrón importante: **un único sitio para el manejo de carga/error**.
- `playbackSpeed` (0 pausa, 1 normal, 3 rápido) lo lee la animación del lienzo
  para que el deslizamiento del drone **acabe antes del siguiente turno**.
- `fitViewTrigger` es un **contador**: incrementarlo es la señal "ajusta la
  vista". El hook del lienzo observa los cambios de ese número. Es el patrón
  "evento como estado" sin un event bus.

---

## 7. Capa de API (`services/api.ts`)

Único punto de contacto con el backend. **Toda respuesta se valida con Zod**
antes de entrar en la app (si el backend miente, falla aquí y no más adentro).

- `API_BASE` se construye de `VITE_BACKEND_URL`; si falta, **se lanza al arrancar**
  (fallo temprano y claro).
- `generateToken()` → `GET /api/token` → `TokenSchema.parse`.
- `createSimulation(file)` → `POST /api/simulation` (multipart con el `.txt`) →
  `RawSimulationSchema.parse` → `enrichSimulation`.
- `advanceSimulation(steps)` → `POST /api/simulation/step?steps=N` → idem.
- `enrichSimulation(token, raw)` pide **en paralelo** (`Promise.all`) hubs,
  connections y drones (`fetchAll` con su esquema `z.record`), y arma el
  `SimulationSchema` completo.
- `requireToken()` lee el token del `sessionStore` y falla si es null.

El token viaja como **query param** (`?token=…`) en cada petición.

---

## 8. El corazón: el sistema de render del lienzo

Aquí está la parte más rica. Se divide en **lógica pura** (`canvas/`) y
**adaptadores Konva** (`components/canvas/konva/`).

### 8.1 La transformada de vista (`canvas/view.ts`)

```ts
View = { scale, panX, panY, canvasWidth, canvasHeight }
modelToCanvas(view, x, y) → [px, py]     // modelo (unidades) → píxel pantalla
```
- `scale` = píxeles por **unidad de modelo** (1 unidad = 1 celda de rejilla).
- `HUB_SPACING = 1.7`: separa las estaciones para que no se toquen y se vean las
  conexiones intermedias.
- `zoomAt(view, anchorX, anchorY, factor)`: zoom **hacia el cursor** (el punto
  bajo el ratón queda fijo). Limitado por `MIN_SCALE`/`MAX_SCALE`. Devuelve una
  vista nueva (inmutable).
- `computeAutoFit(hubs, w, h)`: calcula `scale`+`pan` para **encuadrar todas las
  estaciones**. Devuelve `null` si no hay hubs.

### 8.2 La "Scene" (`canvas/scene.ts`)

`Scene` es **todo lo que el dibujante necesita del estado**, independiente de la
vista (la transformada va aparte):

```ts
Scene = { hubs, drones, connections, origin, destination,
          selectedHubId, selectedConnectionId }
DroneMove = { fromId, toId, tA, tB, progress }   // un drone deslizándose
```

### 8.3 Geometría y vías (`geometry.ts`, `track.ts`)

- `getHubBox(name, scale, capacity)` → tamaño de la caja de estación, fuente,
  andenes y separación de vías (depende del nombre y la capacidad).
- `railMetrics(scale)`, `droneSizeFor(scale)` → grosores y tamaños que escalan
  con el zoom.
- `stationTrackY(centerY, box, t)` → Y de la vía `t` dentro de una estación.
- `trackOffsets(capA, capB, connCap)` → **centra** las vías de una conexión
  dentro del conjunto mayor de vías de cada estación, para que una vía "entre" al
  mismo andén relativo en los dos extremos.
- `connectionTrackLine(view, hubA, hubB, tA, tB)` → segmento `[a, b]` en píxeles
  de una vía concreta de la conexión.

### 8.4 Color (`palette.ts`, `colors.ts`)

- `palette.ts`: constantes de color (vía libre/ocupada/seleccionada, prioritaria,
  bloqueada, andén, fondo, ORIGIN/DEST) y la lógica **rainbow**:
  `isRainbow`, `resolveHubColor`, `rainbowColor()` (color que **cicla con el
  tiempo**), `rainbowColors(n)`.
- `colors.ts`: `createDroneColorCache()` da un **color estable por drone** (el
  mismo drone siempre del mismo color entre turnos).

### 8.5 Primitivas y dibujantes de entidad

- `primitives.ts`: dibujos base sobre un `CanvasRenderingContext2D` —
  `drawRail`, `drawBlockLine` (vía con "bloque" de drone), `drawDroneLabel`.
- `render/entity.ts`: un dibujante por entidad. **Es la lógica de píxeles que la
  app siempre tuvo**; Konva solo posee el grafo de escena. Funciones:
  - `drawBackground` (rejilla + marca de agua "CONTROL AREA").
  - `drawConnection` (las vías de una conexión; color según `access`, selección y
    ocupación) y `connectionTrackPoints` (los segmentos, compartidos con el
    hit-test).
  - `drawHub` (la estación: cuerpo, andenes, vías, número de vía, nombre, contador
    de drones, etiqueta ORIGIN/DEST, tinte de color/rainbow) y `hubHitBox`.
  - `drawHubDrones` (drones aparcados, repartidos por vías) y `parkedDronesByHub`.
  - `drawMovingDrone` (un drone deslizándose por su vía con un fragmento rojo
    "ocupado" debajo).

### 8.6 El puente con React: `SceneNodes.tsx`

Componentes Konva finos. Cada uno es un `<Shape listening={false}>` cuyo
`sceneFunc` **llama al dibujante puro** correspondiente:

- `Background`, `ConnectionShape`, `HubShape`, `DroneNodes`.
- Los nodos **no son interactivos** (`listening=false`): la selección **no** la
  resuelve Konva, sino el **hit-test manual** contra la misma geometría que se
  dibuja (ver 8.7). Esto mantiene el dibujo y la detección de clics en una sola
  fuente de verdad.
- `sceneFunc` es deliberadamente un closure nuevo en cada render: el padre solo
  re-renderiza al cambiar vista/selección/datos o en un frame de animación, y los
  rellenos temporales (rainbow, deslizamiento) deben redibujar cada frame.

### 8.7 Selección por hit-testing (`canvas/hitTest.ts`)

```ts
hitTestHub(view, hubs, x, y) → id | null          // (x,y) dentro de una caja
hitTestConnection(view, scene, x, y) → id | null  // (x,y) cerca de una vía
```
- Un clic en una **estación gana** sobre una conexión; un clic en vacío limpia.
- La tolerancia de la conexión escala con el zoom.
- Usa `hubHitBox` y `connectionTrackPoints` de `render/entity.ts`: **misma
  geometría que se dibuja**, por eso el clic siempre acierta.

### 8.8 Animación de drones (`hooks/useDroneAnimation.ts`)

- En cada **cambio real de turno** diffea el estado anterior y el nuevo con
  `computeDroneMoves` (`canvas/moves.ts`) → lista de drones que cambiaron de hub
  por una conexión real, cada uno con su fila de vía.
- Anima `progress` de 0→1 con suavizado (`requestAnimationFrame`), escribiendo
  cada frame en `movesRef` y disparando un **redibujo**.
- La duración del deslizamiento **se divide por `playbackSpeed`** para que
  siempre termine antes de que llegue el siguiente turno (< `TURN_DELAY`).
- Limpia el `rAF` al desmontar; solo un cambio de turno real cancela un
  deslizamiento en curso.

---

## 9. El componente `SimulationCanvas`

Es el **orquestador** del lienzo. Tras el refactor quedó delgado: combina datos +
selección + render, y delega lo demás a hooks.

Responsabilidades, en orden:

1. **Memoiza** los `Map` de hubs/drones/connections desde la `simulation`.
2. Estado de **selección** (`selectedHubId`, `selectedConnectionId`).
3. `useCanvasView(hubs, containerRef)` → `view` + manejadores de pan/zoom +
   `autoFit`/`zoomIn`/`zoomOut` + `wasDragging()`.
4. `useDroneAnimation(...)` → escribe frames en `movesRef`; `bumpRender`
   (un `useReducer`) fuerza el redibujo por frame.
5. `useRainbowRedraw(hubs, bumpRender)` → bucle de redibujo **solo** si hay algún
   hub rainbow (en reposo, el lienzo queda estático).
6. Construye el objeto **`Scene`** memoizado.
7. `handleStageClick` → hit-test → fija/limpia selección (se **salta** el clic que
   cierra un arrastre real, vía `wasDragging()`).
8. Render: `<Stage><Layer>` con `Background`, las `ConnectionShape`, las
   `HubShape` y `DroneNodes`, más `CanvasToolbar` y, si hay selección, el panel de
   detalle correspondiente.

**Por qué tanta memoización:** los redibujos por frame (deslizamiento/rainbow) no
deben **reasignar** arrays/objetos, o forzarían a todos los `Shape` de Konva a
recalcular. `scene` es estable salvo cambios de datos/selección; los drones que
animan viajan **aparte** (`moving`) hacia `DroneNodes`.

---

## 10. Componentes de UI (fuera del lienzo)

### `App.tsx`
Layout raíz. Al montar, `fetchToken()`. Muestra el error global si lo hay, y o
bien "**Upload a map file to begin**" o el `SimulationCanvas`.

### `Header.tsx`
La barra superior y el **centro de mando**:
- Define los menús **Archivo / Simulación / Vista** (subir mapa, cerrar, token,
  siguiente turno, avanzar 10, play/pausa, velocidad rápida, ajustar vista).
- `usePlayback(hasSimulation, advanceSimulation)` para el estado de reproducción.
- **Atajos de teclado** vía `useKeypress`: `Espacio` play/pausa, `→` siguiente
  turno (`Shift+→` = 10), `f` ajustar vista.
- Input de archivo oculto que solo acepta `.txt`.
- Modal de **token** (`TokenDisplay`).
- A la derecha, `NetworkStatus` (contadores) y `PlaybackControls`.

### `header/PlaybackControls.tsx`
Muestra el **turno** y tres radios (pausa/play/fast) con iconos de Tabler. Patrón
"radio oculto + label con `peer-checked`" de Tailwind.

### `header/AppMenuBar.tsx` + `menuTypes.ts`
Renderiza los menús desplegables desde una estructura de datos `Menu[]`
(declarativo: la lógica está en `Header`, el render en `AppMenuBar`).

### `header/NetworkStatus.tsx`
Contadores de hubs / conexiones / drones de la simulación actual.

### `components/canvas/CanvasToolbar.tsx`
Botonera flotante: zoom +, zoom −, ajustar vista, y el nivel de zoom actual.

### Paneles de detalle (`DetailPanel`, `HubDetailPanel`, `ConnectionDetailPanel`)
- `DetailPanel` es la **carcasa flotante reutilizable** (marco, cabecera con
  título + cerrar, cuerpo) y `DetailRow` (una línea etiqueta/valor).
  `panelStyles.ts` tiene las clases Tailwind compartidas.
- `HubDetailPanel`: posición, acceso, capacidad, nº de drones, conexiones y color
  (con animación rainbow si aplica). Tematiza la cabecera con el color del hub.
- `ConnectionDetailPanel`: origen, destino, capacidad y drones activos.
- Ambos se muestran en la **misma esquina superior derecha** (`right-4 top-4`) y
  la selección es **mutuamente excluyente**, así que nunca se solapan.

---

## 11. Hooks (referencia rápida)

| Hook | Responsabilidad |
|------|-----------------|
| `usePlayback` | Estado play/pausa/fast + bucle de auto-avance (`setTimeout` cada `TURN_DELAY/multiplier`). Publica el multiplicador en el store. |
| `useKeypress` | Suscribe un manejador a una tecla, con opción `preventDefault`. |
| `useCanvasView` | Viewport: estado `view`, pan (arrastre con umbral), zoom (rueda/botones), `ResizeObserver` del contenedor, auto-fit (inicial + `fitViewTrigger`). |
| `useRainbowRedraw` | Mientras exista un hub "rainbow", redibuja cada frame para ciclar su tono. |
| `useDroneAnimation` | Diffea turnos y anima el deslizamiento de los drones. |

Patrón recurrente: **refs para lo que no debe re-renderizar** (coordenadas de
arrastre, frames de animación, último `playbackSpeed`) y **un `useReducer` como
señal de redibujo** (su `dispatch` es estable).

---

## 12. Flujos clave narrados (para explicar en vivo)

**A. Arranque**
`main.tsx` monta `App` → `App` llama `fetchToken()` → `sessionStore.token` se
rellena. Sin simulación, se ve "Upload a map file to begin".

**B. Cargar un mapa**
Menú *Archivo → Nueva simulación* abre el file picker → `handleFileSelect` valida
`.txt` → `simulationStore.newSimulation(file)` → `api.createSimulation` (POST +
enriquecer en paralelo) → `simulation` se setea → `SimulationCanvas` aparece y
hace **auto-fit** la primera vez que hay hubs.

**C. Avanzar un turno**
`→` o el menú → `advanceSimulation(1)` → `api.advanceSimulation` → nueva
`simulation` → `useDroneAnimation` detecta los drones que cambiaron de hub y
**los desliza** por sus vías hasta que llegan.

**D. Reproducir**
`Espacio` → `usePlayback` pone PLAY → bucle que llama `advanceSimulation(1)` cada
segundo (o 1/3 en FAST) → cada turno dispara su animación, calibrada por
`playbackSpeed` para que termine a tiempo.

**E. Seleccionar**
Clic en el lienzo → `handleStageClick` → `hitTestHub` (gana) o
`hitTestConnection` → se abre el panel de detalle en la esquina derecha. Clic en
vacío → se cierra.

**F. Pan / zoom**
Arrastrar (más de 4 px) → pan; un clic con micro-temblor no panea y selecciona
limpio. Rueda → zoom hacia el cursor. Botones de la toolbar → zoom al centro.
`f` o el menú → encuadrar todo.

**G. Rainbow**
Si un hub tiene `color: "rainbow"`, `useRainbowRedraw` mantiene un bucle de
redibujo y su tinte cicla de color; sin hubs rainbow, el lienzo queda estático
(0 trabajo en reposo).

---

## 13. Tests

- Viven en `tests/` y corren con **Vitest** en entorno `node` (sin DOM ni JSX),
  porque cubren la **lógica pura** de `canvas/` + los esquemas.
- Cubiertos: `colors`, `geometry`, `moves`, `palette`, `track`, `view` y
  `schemas`. **34 tests.**
- Lo difícil de testear (el dibujo en `<canvas>` y la interacción Konva) se
  mantiene fuera de los tests **a propósito**; por eso la geometría y las
  transformadas se aislaron como funciones puras: para poder testearlas.
- Ejecutar: `npm test` (o `npm run test:watch`).

---

## 14. Build, configuración y entorno

- **Scripts** (`package.json`): `dev` (Vite), `build` (`tsc -b && vite build`),
  `preview`, `test`, `test:watch`, `clean`, `fclean`.
- **Variables de entorno** (Vite, prefijo `VITE_`):
  - `VITE_BACKEND_URL` — **obligatoria**; sin ella, `api.ts` lanza al arrancar.
  - `FRONTEND_URL`, `PORT` — usadas en `vite.config.ts` (puerto del dev server,
    por defecto 3000).
- **Calidad**: Biome formatea y lintea (tabs, comillas dobles, ancho 80,
  `attributePosition: multiline` → cada atributo JSX en su línea). El linter de
  hooks de React está activo (deps exhaustivas).

---

## 15. Chuleta de presentación (los 8 puntos que tienes que contar)

1. **Qué hace**: visualiza una simulación de drones sobre una red de estaciones,
   turno a turno, con metáfora ferroviaria.
2. **Forma de los datos**: el backend da UUIDs; el frontend **enriquece** a
   objetos completos y **valida todo con Zod** (los tipos salen del esquema).
3. **Estado**: dos stores Zustand pequeños — `session` (token/loading/error) y
   `simulation` (datos + velocidad + señal de fit). Carga/error centralizados en
   `loadSimulation`.
4. **API**: un solo archivo; valida cada respuesta; falla temprano si falta la
   URL del backend.
5. **El lienzo es lógica pura + Konva**: `canvas/` no sabe de React; Konva solo
   posee el grafo de escena, pan, zoom; el dibujo son funciones puras testeables.
6. **Selección sin Konva**: hit-testing manual contra **la misma geometría que se
   dibuja**, una sola fuente de verdad.
7. **Animación calibrada**: los drones se deslizan entre turnos y la duración se
   ajusta a la velocidad de reproducción para terminar a tiempo.
8. **Rendimiento**: memoización agresiva + refs para no re-renderizar, y el bucle
   de redibujo solo corre cuando hay animación o rainbow.

---

## 16. Cómo funciona Konva en profundidad

Konva es una librería de **canvas 2D en modo retenido** (*retained-mode*). En vez
de que tú llames a `ctx.fillRect(...)` y olvides (modo inmediato), Konva mantiene
en memoria un **grafo de escena**: un árbol de nodos que él pinta, vuelve a pintar
y consulta cuando hace falta.

### 16.1 La jerarquía: Stage → Layer → Shape

```
Stage   (un <div> con uno o más <canvas> dentro; el contenedor raíz)
+- Layer  (cada Layer = su PROPIO <canvas>; redibujar una no toca las otras)
   +- Background      (Shape)
   +- ConnectionShape (Shape) × N conexiones
   +- HubShape        (Shape) × N estaciones
   +- DroneNodes      (Shape, dibuja todos los drones)
```

- **Stage** es la raíz. Crea el/los `<canvas>` reales dentro de un `<div>` y
  capta los eventos de ratón/rueda. Aquí se le da `width`/`height` (del `view`).
- **Layer** es una capa de pintado independiente con su propio `<canvas>`. Konva
  puede redibujar una capa sin tocar las demás. Esta app usa **una sola Layer**:
  todo se redibuja junto, lo cual es simple y suficiente porque el padre controla
  cuándo re-renderizar.
- **Shape** es un nodo dibujable. Konva trae formas predefinidas (Rect, Circle,
  Line…), pero aquí se usa el `Shape` **genérico** con un `sceneFunc` propio.

### 16.2 react-konva: un reconciliador de React para Konva

`react-konva` es un **renderer custom de React**, igual que `react-dom` pero cuyo
"host" no es el DOM sino el grafo de escena de Konva. Cuando escribes:

```tsx
<Stage width={w} height={h}><Layer><Shape .../></Layer></Stage>
```

React **diffea** ese árbol de componentes y `react-konva` traduce los cambios a
**operaciones sobre nodos Konva** (crear/actualizar/quitar un `Konva.Shape`,
`Konva.Layer`, etc.). Tú escribes JSX declarativo; por debajo se mantiene un árbol
de objetos Konva imperativos. Es el mismo modelo mental que el DOM: describes el
estado final y el reconciliador aplica el diff.

### 16.3 El `Shape` genérico y `sceneFunc`

El `Shape` genérico delega **todo su dibujo** en una función que tú das:

```tsx
// components/canvas/konva/SceneNodes.tsx
<Shape listening={false} sceneFunc={ctx => drawHub(as2d(ctx), view, scene, hubId, hub)} />
```

- `sceneFunc(context, shape)` recibe el **`Context` de Konva** (un envoltorio sobre
  `CanvasRenderingContext2D`) y pinta lo que quieras con la API canvas estándar.
- Por eso `render/entity.ts` puede ser **lógica pura de canvas**: recibe un
  `CanvasRenderingContext2D` y dibuja. Konva solo aporta *cuándo* y *sobre qué
  canvas* se llama.

### 16.4 El cast `as2d` y por qué existe

```ts
const as2d = (ctx: Context) => ctx as unknown as CanvasRenderingContext2D
```

El `Context` de Konva **no es** un `CanvasRenderingContext2D` real: es un wrapper
que reenvía los métodos de dibujo (`fillRect`, `beginPath`, `stroke`, `measureText`…)
y, de paso, puede grabar las operaciones para construir el *hit graph*. Expone los
mismos métodos, así que el cast deja que los dibujantes queden **tipados contra el
contexto estándar** (más portables y testeables). **Regla:** los dibujantes nunca
deben tocar `ctx.canvas` — el de Konva no es un `HTMLCanvasElement`.

### 16.5 `listening={false}`: por qué la selección NO la hace Konva

Konva sabe resolver "¿qué shape hay bajo el cursor?" por sí mismo, manteniendo un
**segundo canvas oculto** (el *hit canvas*) donde cada shape se pinta de un color
único; al hacer clic, lee el píxel y sabe qué shape es. Esta app **lo desactiva**
con `listening={false}` en todos los nodos. Razones:

1. **Una sola fuente de verdad geométrica.** La selección se resuelve con
   `hitTest.ts`, que mide contra **la misma geometría que se dibuja**
   (`hubHitBox`, `connectionTrackPoints`). No hay riesgo de que el dibujo y la
   detección se desincronicen.
2. **Rendimiento.** Sin hit graph, Konva no mantiene ni repinta un hit canvas por
   shape en cada redibujo.
3. **Control fino.** "La estación gana a la conexión", la tolerancia que **escala
   con el zoom**, etc. son reglas propias triviales de expresar en código y
   difíciles de imponerle al hit testing de Konva.

El Stage sí escucha eventos a nivel global (`onMouseDown`, `onWheel`, `onClick`…)
y ofrece `getStage().getPointerPosition()` para obtener el punto en píxeles; con
ese punto se llama al hit-test manual.

### 16.6 El modelo de redibujo (y por qué hay tanto closure nuevo)

Por defecto Konva solo repinta una capa cuando algo cambia. Aquí el control del
redibujo se **delega a React**:

- Los `<Shape>` se **recrean** en cada render del componente padre, y su
  `sceneFunc` es un **closure nuevo** cada vez. Resultado: cuando el padre
  re-renderiza, Konva vuelve a pintar con los datos frescos.
- El padre (`SimulationCanvas`) re-renderiza **solo** cuando cambian vista,
  selección o datos, **o** cuando `bumpRender` dispara un frame de animación
  (deslizamiento de drones o ciclo rainbow).
- **En reposo no hay redibujo**: sin animación ni rainbow, el lienzo queda
  estático y no se quema CPU.

Esto explica la **memoización agresiva** de `SimulationCanvas`: `scene`,
`hubEntries`, `connEntries` se memoizan para que un bump de animación **no
reasigne** estructuras y fuerce trabajo extra; los drones que animan viajan
**aparte** (`moving`) para no invalidar `scene`.

### 16.7 Pan y zoom: transformada propia, no la nativa de Konva

Konva permite transformar el Stage (`stage.scale()`, `stage.position()`). Esta app
**no** lo usa. En su lugar, la transformada vive en el objeto **`View`** y se
aplica en `modelToCanvas` al dibujar y al hacer hit-test. Ventaja: **una única
transformada** gobierna dibujo *y* detección de clics, ambas en coordenadas de
modelo, y es **pura y testeable** (`view.test.ts` prueba `zoomAt`/`computeAutoFit`
sin montar nada). El Stage queda reducido a "superficie de pintado + captador de
eventos".

> **Coste de bundle:** `konva` + `react-konva` son la dependencia pesada (el grueso
> de los ~528 KB del build). El trade-off se acepta a cambio del grafo de escena,
> el manejo de input y el `getPointerPosition` listos para usar.

---

## 17. Cómo funciona Vitest en profundidad

**Vitest** es el *test runner*. Su rasgo definitorio: está construido **sobre
Vite**, así que **reutiliza el mismo pipeline de transformación** que la app.

### 17.1 Por qué encaja con este proyecto

- Los `.ts` de los tests se transpilan **al vuelo con esbuild** (vía Vite); **no
  hay un paso de compilación TS aparte** para testear (`tsc` solo se usa para el
  *typecheck* en `npm run build`).
- Mismo **resolutor de módulos, alias y plugins** que la app: lo que corre en los
  tests es equivalente a lo que corre en producción. Cero divergencia de config.
- Arranque y *watch* rápidos: Vite solo re-transforma los módulos afectados.

### 17.2 La configuración (`vitest.config.ts`)

```ts
export default defineConfig({
  test: {
    environment: "node",            // sin DOM
    include: ["tests/**/*.test.ts"] // dónde están los tests
  },
})
```

- **`environment: "node"`**: no se monta `jsdom`. Es deliberado: los tests cubren
  **lógica pura** (geometría, transformadas, diff de turnos, esquemas), que no
  necesita `window`, `document` ni `<canvas>`. Node = más rápido y sin mocks.
- **`include`**: solo `tests/**/*.test.ts`. Los tests se sacaron del árbol `src/`
  a una carpeta `tests/` dedicada.
- **Config separada** de `vite.config.ts` a propósito: así los plugins del build
  de la app (React, Tailwind) **no se arrastran** a los tests, que no los
  necesitan (ningún test transforma JSX).

### 17.3 La API: `describe` / `it` / `expect`

Se importan **explícitamente** (no hay *globals* configurados):

```ts
import { describe, expect, it } from "vitest"
```

- `describe("nombre", () => …)` agrupa casos relacionados.
- `it("hace X", () => …)` (alias `test`) define un caso.
- `expect(valor).matcher(...)` hace la aserción.

### 17.4 Los matchers usados aquí, y por qué cada uno

| Matcher | Dónde | Por qué |
|---------|-------|---------|
| `toBeCloseTo(v, d)` | `view.test.ts` (geometría) | Compara **floats** con tolerancia: evita falsos fallos por error de coma flotante. Ej.: `fit?.scale` ≈ `188.235`. |
| `toThrow()` | `schemas.test.ts` | Comprueba que un `parse` de Zod **rechaza** lo inválido (posición malformada, token con caracteres no base64url). |
| `toEqual(...)` | `moves.test.ts` | Igualdad **estructural profunda** de objetos/arrays (la lista de `DroneMove`). |
| `toMatchObject(...)` | `schemas.test.ts` | Igualdad **parcial**: solo verifica los campos clave del objeto parseado. |
| `toBe(...)` / `toBeNull()` | varios | Identidad estricta / `null` (p.ej. `computeAutoFit` sin hubs → `null`). |

### 17.5 Patrones de los tests

- **Factories / helpers de fixture.** Funciones como `hub()` y `sim()` construyen
  datos mínimos y legibles, parametrizando solo lo relevante:

  ```ts
  const hub = (capacity = 1): Hub => ({ name:"H", position:[0,0], access:"open",
    connections:[], capacity, drones:[] })
  // un test de movimiento solo varía dónde están los drones:
  computeDroneMoves(sim({ d1:"a" }), sim({ d1:"b" }), hubs, connections)
  ```

- **Determinismo.** Entradas fijas, sin reloj real ni red. `randomUUID()` solo se
  usa para generar ids **válidos** que los esquemas Zod aceptan, no para azar de
  lógica.
- **Casos normales + borde + fallo.** P.ej. `computeDroneMoves`: drone que se mueve
  (normal), drone que no se mueve (borde), movimiento sin vía que conecte (fallo),
  dos drones apilados en filas distintas (borde de capacidad).
- **Se testea el dominio difícil directamente.** Como la geometría, las
  transformadas y el diff son **funciones puras**, se prueban sin montar React ni
  `<canvas>`. Esto es exactamente la recompensa de separar `canvas/` (puro) de
  `components/` (UI): lo complejo es testeable en aislamiento.

### 17.6 Qué NO se testea (y por qué)

El dibujo real en `<canvas>`, la interacción de Konva y los componentes React
**quedan fuera a propósito**. Testearlos exigiría `jsdom` + mocks de `canvas`/Konva
y daría **poca señal** a cambio de mucho andamiaje. Esa superficie se cubre con
`tsc --noEmit` (tipos), `npm run build` (que compila de verdad) y revisión manual.

### 17.7 Ejecutar

- `npm test` → `vitest run`: una pasada, ideal para CI.
- `npm run test:watch` → `vitest`: re-ejecuta al guardar, re-corriendo **solo** lo
  afectado gracias al grafo de módulos de Vite.

Estado actual: **34 tests** en 7 archivos (`colors`, `geometry`, `moves`,
`palette`, `track`, `view`, `schemas`).

---

## Glosario rápido

| Término | Significado |
|---------|-------------|
| **Hub / estación** | Nodo de la red; se dibuja como estación con andenes y vías. |
| **Connection / vía** | Enlace entre dos hubs; se dibuja como un haz de vías (1 por capacidad). |
| **Drone** | Agente que va de origen a destino; aparca o se desliza por vías. |
| **Turn / turno** | Paso discreto de la simulación; cada avance puede mover drones. |
| **access** | Tipo de acceso de un hub (`blocked`/`priority`/…) que colorea sus vías. |
| **Scene** | Snapshot del estado que necesita el dibujante (independiente de la vista). |
| **View** | Transformada modelo→píxel (scale, panX, panY, tamaño del canvas). |
| **DroneMove** | Un drone en deslizamiento entre dos hubs con un `progress` 0→1. |
| **Hit-test** | Resolver qué entidad hay bajo el cursor sin usar eventos de Konva. |
```
