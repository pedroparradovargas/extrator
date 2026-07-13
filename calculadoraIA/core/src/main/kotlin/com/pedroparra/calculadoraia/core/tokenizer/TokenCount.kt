package com.pedroparra.calculadoraia.core.tokenizer

/** Resultado de contar un texto: tokens, caracteres, palabras y si es aproximado. */
data class TokenCount(
    val tokens: Int,
    val characters: Int,
    val words: Int,
    /** true si el conteo es una estimación (modelos sin BPE offline: Claude/Gemini). */
    val approximate: Boolean,
)
