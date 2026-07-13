package com.pedroparra.calculadoraia.core.tokenizer

import com.knuddels.jtokkit.Encodings
import com.knuddels.jtokkit.api.Encoding
import com.knuddels.jtokkit.api.EncodingRegistry
import com.knuddels.jtokkit.api.EncodingType

/**
 * Tokenizador BPE EXACTO y offline para modelos de OpenAI, usando jtokkit.
 * Los vocabularios (cl100k_base / o200k_base) viajan dentro del jar → sin red.
 */
class JtokkitTokenizer(private val encoding: TokenEncoding) : Tokenizer {

    private val enc: Encoding = registry.getEncoding(encoding.toJtokkit())

    override fun count(text: String): TokenCount =
        TokenCount(
            tokens = if (text.isEmpty()) 0 else enc.countTokens(text),
            characters = text.length,
            words = wordCount(text),
            approximate = false,
        )

    private fun TokenEncoding.toJtokkit(): EncodingType = when (this) {
        TokenEncoding.CL100K_BASE -> EncodingType.CL100K_BASE
        TokenEncoding.O200K_BASE -> EncodingType.O200K_BASE
    }

    companion object {
        // Registro perezoso: solo carga el vocabulario que se pida realmente.
        private val registry: EncodingRegistry = Encodings.newLazyEncodingRegistry()
    }
}
