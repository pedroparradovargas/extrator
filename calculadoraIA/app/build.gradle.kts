plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.compose.compiler)
    alias(libs.plugins.kotlin.serialization)
}

android {
    namespace = "com.pedroparra.calculadoraia"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.pedroparra.calculadoraia"
        minSdk = 26
        targetSdk = 36
        versionCode = 1
        versionName = "0.1.0"
    }

    buildTypes {
        release {
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro",
            )
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    buildFeatures {
        compose = true
    }

    packaging {
        resources {
            excludes += "/META-INF/{AL2.0,LGPL2.1}"
            // jtokkit incluye varios vocabularios; solo usamos cl100k_base y
            // o200k_base. Excluimos los legacy para ahorrar tamaño de APK.
            excludes += "com/knuddels/jtokkit/r50k_base.tiktoken"
            excludes += "com/knuddels/jtokkit/p50k_base.tiktoken"
            excludes += "com/knuddels/jtokkit/p50k_edit.tiktoken"
        }
    }
}

kotlin {
    compilerOptions {
        jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17)
    }
}

dependencies {
    implementation(project(":core"))

    implementation(platform(libs.compose.bom))
    implementation(libs.compose.ui)
    implementation(libs.compose.ui.graphics)
    implementation(libs.compose.ui.tooling.preview)
    implementation(libs.compose.material3)
    implementation(libs.androidx.activity.compose)
    implementation(libs.androidx.lifecycle.viewmodel.compose)
    implementation(libs.androidx.lifecycle.runtime.compose)
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.navigation.compose)

    // Persistencia de precios editados
    implementation(libs.datastore.preferences)
    implementation(libs.kotlinx.serialization.json)

    // OCR on-device (modelo empaquetado → offline)
    implementation(libs.mlkit.text.recognition)

    debugImplementation(libs.compose.ui.tooling)
}
