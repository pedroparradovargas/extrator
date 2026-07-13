package com.pedroparra.calculadoraia.core.tokenizer

import kotlin.math.ceil

/**
 * Tokenizador APROXIMADO para modelos sin BPE offline público (Claude, Gemini).
 * Estima: tokens = ceil(caracteres / charsPerToken).
 */
class ApproxTokenizer(
    private val charsPerToken: Double = DEFAULT_CHARS_PER_TOKEN,
) : Tokenizer {

    init {
        require(charsPerToken > 0) { "charsPerToken debe ser > 0" }
    }

    override fun count(text: String): TokenCount =
        TokenCount(
            tokens = if (text.isEmpty()) 0 else ceil(text.length / charsPerToken).toInt(),
            characters = text.length,
            words = wordCount(text),
            approximate = true,
        )

    companion object {
        const val DEFAULT_CHARS_PER_TOKEN = 4.0
    }
}
