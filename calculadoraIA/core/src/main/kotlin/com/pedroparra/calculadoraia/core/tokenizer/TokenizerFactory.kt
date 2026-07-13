package com.pedroparra.calculadoraia.core.tokenizer

import com.pedroparra.calculadoraia.core.pricing.ModelPricing

/** Elige el tokenizador adecuado según el modelo: exacto (OpenAI) o aproximado. */
object TokenizerFactory {

    fun forModel(model: ModelPricing): Tokenizer =
        model.encoding
            ?.let { JtokkitTokenizer(it) }
            ?: ApproxTokenizer(model.approxCharsPerToken ?: ApproxTokenizer.DEFAULT_CHARS_PER_TOKEN)
}
