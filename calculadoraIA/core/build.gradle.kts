// Módulo :core — Kotlin/JVM PURO. Sin dependencias de Android.
// Aquí vive toda la lógica de negocio (tokenización, precios, cálculo de coste),
// lo que permite testearla con `gradle :core:test` sin emulador ni Android SDK.
plugins {
    alias(libs.plugins.kotlin.jvm)
    alias(libs.plugins.kotlin.serialization)
}

group = "com.pedroparra.calculadoraia"

java {
    sourceCompatibility = JavaVersion.VERSION_17
    targetCompatibility = JavaVersion.VERSION_17
}

kotlin {
    compilerOptions {
        // Bytecode Java 17: compatible con Android (AGP 8.x) y con el JDK del entorno.
        jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17)
    }
}

dependencies {
    implementation(libs.jtokkit)
    implementation(libs.kotlinx.serialization.json)
    testImplementation(kotlin("test"))
}

tasks.test {
    useJUnitPlatform()
}
