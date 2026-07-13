package com.pedroparra.calculadoraia.core.pricing

import com.pedroparra.calculadoraia.core.tokenizer.TokenEncoding
import kotlinx.serialization.Serializable

/**
 * Precios de un modelo, en USD por 1.000.000 de tokens.
 *
 * Editable por el usuario: los precios de los proveedores cambian con frecuencia;
 * `lastUpdated` refleja la fecha de la última revisión y se muestra en la UI.
 */
@Serializable
data class ModelPricing(
    val id: String,
    val displayName: String,
    val provider: Provider,
    /** Codificación BPE exacta (OpenAI). null → se usa aproximación (Claude/Gemini). */
    val encoding: TokenEncoding? = null,
    val inputPricePerMTok: Double,
    val outputPricePerMTok: Double,
    /** Tarifa de entrada cacheada, si el proveedor la ofrece. */
    val cachedInputPricePerMTok: Double? = null,
    /** Solo para modelos sin BPE offline: caracteres por token para aproximar. */
    val approxCharsPerToken: Double? = null,
    val lastUpdated: String,
) {
    /** true si el conteo de tokens de este modelo es aproximado. */
    val isApproximate: Boolean get() = encoding == null
}
