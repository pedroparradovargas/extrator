package com.pedroparra.calculadoraia.core.tokenizer

import kotlinx.serialization.Serializable

/**
 * Codificaciones BPE (tiktoken) soportadas de forma EXACTA y offline vía jtokkit.
 * Solo los modelos de OpenAI publican su tokenizador; para el resto se aproxima.
 */
@Serializable
enum class TokenEncoding {
    /** GPT-4, GPT-3.5-turbo, text-embedding-3-*. */
    CL100K_BASE,

    /** GPT-4o, GPT-4.1 y familia o-series. */
    O200K_BASE,
}
