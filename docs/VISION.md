# Visión — Jarvis

## Norte

Un asistente virtual personal que le hace la vida más fácil a su dueño, en lo
cotidiano y en lo laboral, operando al **costo más bajo posible** y construido
para **escalar sin reescribirse**. Todo lo que existe hoy es el 0.0001% de lo que
será: cada decisión se toma pensando en ese futuro, no en el alcance de esta semana.

## Los dos principios que gobiernan todo

### 1. Costo mínimo (prioridad #1)
El ahorro de tokens y de plata no es una optimización tardía: es un requisito de
diseño desde la primera línea.

- **Determinístico primero, IA al final.** Si un programa puede resolverlo (parsear,
  clasificar por reglas, buscar, agendar, formatear), lo resuelve el programa. La IA
  entra solo cuando no hay forma determinística de hacerlo bien.
- **El modelo más barato que sirve.** Vía OpenRouter, cada tarea usa el modelo más
  económico que entregue un resultado correcto y confiable para *ese* contexto. No hay
  un "modelo por defecto caro".
- **Contexto mínimo.** Nunca se manda todo el historial. Se recupera solo lo relevante
  (RAG con embeddings) y lo viejo se comprime en resúmenes. Presupuesto de tokens por request.
- **No pagar dos veces.** Caché semántico: respuestas y clasificaciones se reutilizan
  cuando la intención es equivalente.
- **Visibilidad total del gasto.** Cada llamada a IA se registra con dimensiones (modelo,
  tarea, día). El ahorro se mide y se muestra en un dashboard de costo, no se asume.

### 2. Escalabilidad (prioridad #2, igual de importante)
Se asume que cada componente crecerá en orden de magnitud. Por eso:

- Arquitectura hexagonal: el dominio es puro y no conoce infraestructura.
- Bajo acoplamiento / alta cohesión: cada proveedor externo vive detrás de un puerto.
  Cambiar OpenRouter, la base de datos o sumar un canal nuevo no toca el núcleo.
- Tests, documentación y decisiones registradas como parte del trabajo, no como extra.
- Empezamos como monolito modular (barato de operar) diseñado para partirse en servicios
  cuando —y solo cuando— la escala lo exija.

## Cómo se usa

- **Canal principal: app web.** Dashboard limpio con revelación progresiva (colapsables,
  menú hamburguesa): se muestra lo importante, el detalle se accede si se pide. Chat integrado.
- **App mobile personal (Expo/React Native).** "Muchas apps en una": un Hub central y módulos
  que se sienten como apps propias (tabbar que cambia por módulo). Offline-first. Solo la usa Dante.
- **Canales como adaptadores.** Telegram u otros entran después como un *adaptador de canal*
  más, sin tocar la lógica del asistente. Cada canal puede tener sus propias políticas
  (ej. Telegram con contexto más acotado por la fricción de retomar hilos largos).

El producto se organiza en **módulos** (un job-to-be-done cada uno) sobre un núcleo común, más
dos piezas transversales de sistema: la **contabilidad de IA** y la **Bandeja de Jarvis**
(donde cae todo lo que requiere tu aprobación o respuesta). Reglas de módulos en `DECISIONS.md`.
El norte último es el cerebro **Córtex**: una secretaria virtual con la que conversas y que
decide qué módulo activar. Se diseña desde ya para que enchufe natural, se implementa a futuro.

## Alcance por capacidades (el "qué hace")

El asistente se construye por músculos independientes sobre un núcleo común:

1. **Núcleo conversacional + memoria** — chat general con memoria persistente sobre el
   usuario (perfil, preferencias, hechos, historial) usando embeddings/RAG. *Se construye primero.*
2. **Tareas y recordatorios** — gestión de pendientes y disparo proactivo.
3. **Podcast automatizado** — generación automatizada de un podcast (se especifica más adelante).
4. **Integraciones** — correo, calendario y otros, sumados como adaptadores cuando corresponda.

Además, como capacidad transversal (no un músculo aparte):

- **Dashboard de costo de IA** — vista del gasto en IA con revelación progresiva: primero un
  total simple, y al hacer click se despliega el desglose por día, por modelo y por tarea.
  Es la cara visible de la Prioridad #1 y una herramienta para decidir dónde recortar.

El orden y detalle vivo están en `docs/ROADMAP.md`.

## Mejora continua

Parte del encargo es proponer mejoras que el dueño no pediría por no conocerlas, siempre
al servicio de estos dos principios. Toda mejora estructural se registra en `docs/DECISIONS.md`.

## No-objetivos (por ahora)
- No es una plataforma multiusuario ni un producto para terceros: es personal. La
  arquitectura no lo impide a futuro, pero no se construye para eso hoy.
- No se persiguen features llamativas que disparen costo sin retorno claro en utilidad.
