pluginManagement {
    repositories {
        google {
            content {
                includeGroupByRegex("com\\.android.*")
                includeGroupByRegex("com\\.google.*")
                includeGroupByRegex("androidx.*")
            }
        }
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.name = "calculadoraIA"

// El módulo :core es Kotlin/JVM puro y se puede compilar/testear SIN el Android SDK.
// Para verificar solo la lógica en un entorno sin SDK (p. ej. CI ligera):
//     CORE_ONLY=true gradle :core:test
// Con esa variable no se incluye :app (que requiere AGP + Android SDK).
include(":core")
if (System.getenv("CORE_ONLY") != "true") {
    include(":app")
}
