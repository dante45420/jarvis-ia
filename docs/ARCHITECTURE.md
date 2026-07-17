# Arquitectura — Jarvis

El *porqué* está en `VISION.md`. Acá va el *cómo*. Las decisiones concretas y su
justificación (incluyendo alternativas descartadas) están en `DECISIONS.md`.

## Stack

| Capa | Elección | Razón (resumen) |
|------|----------|-----------------|
| Lenguaje/API | Python 3.12+, FastAPI (async) | Ecosistema IA + async nativo. |
| Gestor de deps | `uv` | Rápido y reproducible. |
| Persistencia | PostgreSQL + `pgvector` | Relacional **y** vectorial en una sola base = menos servicios, menos costo. |
| LLM gateway | OpenRouter detrás del puerto `LLMProvider` | Ruteo al modelo más barato capaz. Nunca acoplado al SDK del proveedor. |
| Embeddings | OpenRouter (`baai/bge-m3`, 1024 dims) detrás de `EmbeddingProvider` | RAG barato y multilingüe; mismo gateway y key que el chat. |
| Caché / cola | Redis (se introduce cuando se necesite; hasta entonces, Postgres) | No sumar infra antes de tiempo. |
| Jobs async | Empezar con scheduler liviano; graduar a cola async cuando escale | Proactividad (recordatorios, podcast) desacoplada. |
| Frontend | React + TypeScript + Vite + Tailwind + shadcn/ui | UI limpia con colapsables; deploy barato (estático). |
| Observabilidad | Logging estructurado + telemetría de **tokens y costo** | El costo es un ciudadano de primera clase, se mide. |
| Calidad | pytest, ruff, mypy | Tests + lint + tipos como parte del flujo. |
| Empaque | Docker | Local reproducible; deploy a plataforma barata. |

> Proveedor de nube concreto (Supabase / Fly.io / Railway / Render u otro): decisión
> abierta, se fija en `DECISIONS.md` cuando se elija. Criterio: free tier generoso y
> Postgres administrado. No condiciona el código porque todo va detrás de puertos.

## Capas (hexagonal / puertos y adaptadores)

```
interfaces/     Entrada-salida: API web (FastAPI), adaptadores de canal (web, luego telegram)
application/    Casos de uso: orquestan el dominio. Sin detalle de infraestructura.
domain/         Núcleo puro: entidades, reglas, PUERTOS (interfaces). Sin dependencias externas.
adapters/       Implementaciones de puertos: OpenRouter, pgvector, embeddings, caché, canales.
platform/       Config, logging, telemetría, arranque.
```

Regla de dependencia: las flechas apuntan **hacia adentro**. `domain` no importa nada de
`adapters`. Cambiar un proveedor = escribir un adaptador nuevo, sin tocar dominio ni casos de uso.

### Puertos principales (interfaces del dominio)
- `LLMProvider` — completar/chat con selección de modelo y reporte de costo.
- `EmbeddingProvider` — texto → vector.
- `VectorStore` — guardar/buscar por similitud (impl: pgvector).
- `MemoryStore` — persistencia de memoria estructurada.
- `SemanticCache` — buscar/guardar respuestas por equivalencia de intención.
- `ChannelAdapter` — recibir/emitir mensajes por canal (web, telegram…).
- `ModelRouter` — dado un contexto, elige el modelo más barato capaz.
- `UsageMeter` — emite un `UsageRecord` por cada llamada de IA (o llamada evitada).

## Pipeline costo-primero (el corazón del sistema)

Todo mensaje entrante pasa por esta cadena. Cada paso intenta **cerrar el request antes**
de llegar al LLM. El LLM es el último eslabón, no el primero.

```
1. Canal recibe el mensaje (web / telegram) y lo normaliza.
2. Intento determinístico: reglas/regex/slot-filling resuelven intenciones obvias
   ("recuérdame X a las Y", "lista mis tareas") SIN LLM. Si resuelve → responde y termina.
3. Caché semántico: ¿hay una respuesta equivalente ya calculada? Si sí → responde y termina.
4. NLU/router barato: clasifica intención y elige el modelo más barato capaz (ModelRouter).
5. Ensamblado de contexto: RAG recupera solo memorias relevantes (top-k por embeddings)
   + resumen del historial. Se aplica un PRESUPUESTO de tokens estricto.
6. Llamada al LLM vía OpenRouter con function calling (salida estructurada).
7. Post-proceso determinístico + persistencia de memoria (extracción barata de hechos).
8. Se guarda en caché semántico y se registra costo/tokens en telemetría.
```

Cada paso que evita el paso 6 es dinero ahorrado. Optimizar aquí es optimizar el negocio.

## Sistema de memoria

La memoria hace a Jarvis "personal" y es el mayor riesgo de costo. Regla mental: **log ≠
memoria.** Ver decisión completa en `DECISIONS.md` (D-0008). Tres presupuestos separados:

| Presupuesto | ¿Cuesta tokens? | Estrategia |
|-------------|-----------------|------------|
| **Guardar** (log crudo de turnos) | No (SQL) | Fuente de verdad. Nunca se inyecta entero. |
| **Escribir memoria** (ascender del log) | Solo si usa IA | Escalera barata→cara; el LLM solo por lotes. |
| **Inyectar** (armar el prompt) | Siempre | Presupuesto fijo de tokens, recorte determinístico. |

### Escribir: escalera de lo barato a lo caro
1. **Señales explícitas** (regex, $0): "recuerda que…", "me llamo…", "prefiero…".
2. **Eventos estructurados** ($0): tareas, recordatorios, decisiones → tablas propias.
3. **Heurística de salience** ($0): nombres, fechas, afirmaciones sobre el usuario → candidatos.
4. **Extractor LLM** (último recurso): **por lotes, modelo barato, sobre una ventana** — nunca
   mensaje por mensaje. Resumen **rodante y jerárquico** (turnos nuevos + resumen anterior),
   así la entrada está acotada y el costo de escribir no crece sin límite.

Solo lo que se **asciende** a memoria recuperable se embebe (una vez, medido). Antes de escribir:
**dedup por similitud**. Cada memoria lleva `last_accessed`/`access_count` para **decaimiento**
(archivar lo viejo no usado ⇒ recuperación afilada y barata).

### Tipos de memoria
| Tipo | Qué guarda | Escritura | Lectura |
|------|-----------|-----------|---------|
| **Working** | Turnos recientes (~8 / ~1–2k tok) | Ventana deslizante | Directa |
| **Episodic** | Conversaciones pasadas resumidas + embebidas | Resumen batch, modelo barato | RAG por similitud |
| **Semantic** | Hechos durables del usuario | Determinística/barata | Estructurada + RAG |
| **Procedural** | Rutinas y "cómo hacer" | Explícita | Por intención |

### Hechos graph-ready
Los hechos durables se modelan como `sujeto–predicado–objeto + tiempo`, detrás del puerto
`MemoryStore`. Hoy en Postgres; mañana un adaptador de grafo temporal (Graphiti) se alimenta
del mismo pipeline de consolidación, sin reescritura. Es el sustrato del cerebro Córtex (D-0012).

### Inyectar: contexto con presupuesto fijo
Nunca "todo". Se arma por prioridad hasta llenar el tope de tokens; el recorte es determinístico
(contamos y cortamos, sin LLM) y la recuperación es SQL sobre pgvector (cero IA):
```
[ system ]  →  [ ficha usuario ~300 tok ]  →  [ working ~8 turnos ]
            →  [ RAG top-k (k=5, con umbral) ]  →  [ resumen episódico ]  →  [ mensaje ]
```

## Telemetría de costo y dashboard

El costo de IA es una métrica de primera clase: se mide en el punto de origen y se muestra.

**Registro base (`UsageRecord`).** Cada llamada que involucra un modelo (o que la evita)
emite un registro con las dimensiones que el dashboard necesita para desglosar:

| Campo | Uso |
|-------|-----|
| `occurred_at` | Agregación por día/hora. |
| `model` | Desglose por modelo. |
| `task` | Desglose por tarea/intención (ej. `chat`, `summarize_memory`, `route`, `podcast`). |
| `channel` | Web, telegram… |
| `tokens_in` / `tokens_out` | Insumo del costo y del análisis. |
| `cost` | Calculado desde el precio del modelo (tabla de precios versionada). |
| `outcome` | `llm_call` · `cache_hit` · `deterministic` (permite ver **cuánto se ahorró** evitando el LLM). |
| `request_id` | Traza y correlación. |

La emisión va detrás del puerto `UsageMeter`; el almacenamiento es Postgres. Las
agregaciones (por día/modelo/tarea) se resuelven en SQL —determinístico y barato—, no en la app.

**Dashboard (revelación progresiva).** La UI parte de lo mínimo y profundiza al hacer click:

```
Nivel 0  →  Gasto total (hoy / mes) + tendencia. Una sola cifra clara.
Nivel 1  →  click → desglose por día.
Nivel 2  →  click en un día → desglose por modelo.
Nivel 3  →  click en un modelo → desglose por tarea, y ahorro por caché/determinístico.
```

Cada nivel es una agregación SQL distinta sobre `UsageRecord`; la API expone un endpoint de
consulta con filtros (rango, modelo, tarea) y el frontend solo pinta.

## Módulos (arquitectura de producto)

El producto es "muchas apps en una". Cada capacidad es un **módulo** = un job-to-be-done con su
dominio de datos y su identidad de tabbar. Reglas de límites en `DECISIONS.md` (D-0009).

- Cada módulo es un **slice vertical**: dominio + casos de uso + adaptadores + API + UI.
- Cada módulo **expone sus capacidades como funciones tipadas** (tool-calling / MCP-ready), para
  que el cerebro Córtex (D-0012) las invoque sin trabajo extra.
- Nombres simples y épicos (una palabra): Oráculo (aprendizaje: podcast + noticiero), Bóveda
  (contabilidad de IA), Córtex (cerebro futuro).

**Piezas transversales (sistema, no módulos):**
- **Contabilidad de IA:** el dashboard de costo (misma data en web y mobile).
- **Bandeja de Jarvis (human-in-the-loop):** ítems que requieren aprobación/respuesta del
  usuario. Contrato común "ítem que requiere al usuario" que cualquier módulo —o Córtex— emite.
  Ordenable por módulo (luego por hora) o por hora de llegada; filtrable por ambos.

## Frontend web

- Revelación progresiva: se muestra lo esencial; el detalle vive en colapsables, paneles y menú
  hamburguesa. Se accede solo cuando se pide.
- **Nada bloquea la primera pintura:** shell instantáneo → skeletons → datos por streaming.
  Módulos con lazy loading. UI optimista + feedback inmediato; sin spinners que congelen.
- **Animación barata:** solo `transform`/`opacity` (GPU); librería `motion` + CSS. Nada que
  toque layout o cueste RAM.
- **Paleta:** base neutra + un acento, modo claro/oscuro. Presupuesto de rendimiento medido.
- Habla con el backend por una API estable; no conoce proveedores ni modelos. Desplegable estático.

## App mobile (Expo / React Native)

Personal, offline-first, modular. Comparte modelo mental y código con la web.

- **Hub central:** el ícono central del tabbar siempre vuelve al Hub; cada módulo reemplaza el
  tabbar por el suyo ⇒ se siente como app propia.
- **Offline-first:** cada módulo declara el mínimo que necesita sin señal (SQLite local) y
  sincroniza al volver la red. Degrada, nunca se cae.
- Mismos principios de rendimiento percibido y paleta que la web.

## Cerebro Córtex (futuro, ver D-0012)

Orquestador conversacional que llama a los módulos como herramientas y usa los hechos
graph-ready como memoria. Motor: modelo Claude potente vía OpenRouter, detrás de `LLMProvider`.
Se diseña desde ya (módulos MCP-ready, hechos graph-ready) para enchufarlo sin reescritura.

## Convenciones transversales
- Errores y logs con contexto suficiente para depurar sin reproducir.
- Telemetría de costo por request vía `UsageMeter` (ver sección dedicada). Es la métrica
  de salud del proyecto y el insumo del dashboard.
- Configuración por entorno (nada de secretos en el código).
