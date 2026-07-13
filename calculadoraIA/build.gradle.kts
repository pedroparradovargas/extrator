// Build raíz.
//
// A propósito NO declaramos aquí un bloque `plugins { ... apply false }`: eso
// obligaría a Gradle a RESOLVER el artefacto de AGP incluso para tareas que no lo
// usan, impidiendo verificar el módulo :core (Kotlin/JVM puro) sin el Android SDK.
//
// Cada módulo aplica sus propios plugins vía el version catalog (gradle/libs.versions.toml):
//   - :core  → kotlin("jvm") + serialization        (puro JVM, testeable sin SDK)
//   - :app   → com.android.application + kotlin-android + compose + ksp
