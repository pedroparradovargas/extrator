package com.pedroparra.calculadoraia.core.tokenizer

/** Cuenta los tokens de un texto según una codificación concreta. */
interface Tokenizer {
    fun count(text: String): TokenCount
}
