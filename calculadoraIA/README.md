# calculadoraIA

App móvil **nativa Android (Kotlin + Jetpack Compose)** que funciona como una
**calculadora de IA 100% offline**: cuenta tokens de un texto, estima el **coste y
el tráfico** de usarlo con **N personas**, y permite introducir el texto por
teclado, **OCR** (foto) o **voz** (dictado). No llama a ninguna API de LLM.

> Proyecto en construcción. El módulo de lógica `:core` ya está implementado y
> **verificado con tests**; la app Android (`:app`) se está montando por fases.

## ¿Qué calcula?

- **Tokens exactos** para modelos de OpenAI usando un tokenizador BPE real
  (tiktoken vía [jtokkit](https://github.com/knuddelsgmbh/jtokkit)) empaquetado en
  la app — sin conexión. Para Claude/Gemini usa una aproximación configurable.
- **Coste y tráfico escalado a N personas**: dado un texto (o nº de tokens de
  entrada/salida), un modelo, N personas y mensajes por persona/día, calcula el
  coste por **mensaje / persona / día / mes** y los **tokens totales**.

## Arquitectura

Proyecto Gradle multi-módulo:

| Módulo | Tipo | Contenido |
|--------|------|-----------|
| **`:core`** | Kotlin/JVM **puro** | Tokenizador (jtokkit + aproximado), catálogo de precios y calculadora de coste. **Testeable sin Android SDK ni emulador.** |
| **`:app`** | Android (Compose) | UI, ViewModels, navegación, OCR (ML Kit + CameraX), voz (SpeechRecognizer), historial (Room), ajustes (DataStore). |

```
core/src/main/kotlin/.../core/
  tokenizer/  Tokenizer · JtokkitTokenizer · ApproxTokenizer · TokenizerFactory
  pricing/    Provider · ModelPricing · ModelCatalog
  cost/       CostInput · CostResult · CostCalculator
```

## Compilar y ejecutar la app

Requiere **Android Studio** (con Android SDK). Abre la carpeta `calculadoraIA/`
como proyecto y ejecuta la configuración `app` en un emulador o dispositivo.

Desde línea de comandos (con el SDK instalado):

```bash
./gradlew :app:assembleDebug     # genera el APK de debug
```

## Verificar solo la lógica (`:core`) sin Android SDK

La lógica pura se puede testear en cualquier máquina con **JDK 17+**, sin SDK ni
emulador. La variable `CORE_ONLY` excluye el módulo `:app` de la build:

```bash
CORE_ONLY=true ./gradlew :core:test
```

## Stack

Kotlin 2.2.20 · Jetpack Compose (BOM 2026.06) · Material 3 · jtokkit 1.1.0 ·
ML Kit Text Recognition · CameraX · Room · DataStore · Koin. `minSdk 26`,
`targetSdk 36`. Toolchain conservadora **AGP 8.13 / Gradle 8.14.x** (ver
`gradle/libs.versions.toml`; si tu Android Studio soporta AGP 9, puedes subir el
bloque AGP/Gradle/Kotlin).

> ⚠️ **Precios editables**: el catálogo (`ModelCatalog`) trae precios de partida a
> fecha `SEED_DATE`. Los precios de los proveedores cambian; la app permite
> editarlos. Verifica siempre la web oficial de cada proveedor.

## Estado y hoja de ruta

- [x] Scaffold Gradle multi-módulo + version catalog
- [x] `:core`: tokenización (jtokkit), precios y cálculo de coste **+ tests (verde)**
- [x] `:app`: scaffold Android (Compose, tema claro/oscuro, ES/EN)
- [x] Pantalla Calculadora (MVP): texto → tokens + coste/tráfico para N personas
- [x] OCR (ML Kit + Photo Picker + cámara por intent)
- [x] Voz (RecognizerIntent del sistema)
- [x] Ajustes con **precios editables** (DataStore) + navegación
- [x] Comparador de coste entre modelos (integrado en la calculadora)
- [x] Exportar/compartir el resultado (share sheet)
- [ ] Historial de cálculos (Room)

> **Nota:** `:app` no se compila en este entorno de nube (sin Android SDK y sin
> acceso al Maven de Google). Ábrelo en **Android Studio** para sincronizar y
> ejecutar; si el IDE pide ajustar la versión de AGP/Gradle, acéptalo (una línea
> en `gradle/libs.versions.toml`).
