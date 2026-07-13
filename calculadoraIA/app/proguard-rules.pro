# jtokkit no usa reflexión, pero mantenemos sus clases y recursos por seguridad
# en builds minificados (los vocabularios .tiktoken viajan como recursos del jar).
-keep class com.knuddels.jtokkit.** { *; }

# kotlinx.serialization: mantener los serializadores generados.
-keepclassmembers class ** {
    *** Companion;
}
-keepclasseswithmembers class ** {
    kotlinx.serialization.KSerializer serializer(...);
}
