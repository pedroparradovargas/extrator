package com.pedroparra.calculadoraia.core.tokenizer

private val WHITESPACE = Regex("\\s+")

/** Cuenta palabras separadas por espacios en blanco. Cadena vacía → 0. */
internal fun wordCount(text: String): Int {
    val trimmed = text.trim()
    if (trimmed.isEmpty()) return 0
    return trimmed.split(WHITESPACE).count { it.isNotEmpty() }
}
