package com.pedroparra.calculadoraia.data

import com.pedroparra.calculadoraia.core.pricing.ModelPricing
import kotlinx.serialization.Serializable

/** Precios editados por el usuario para un modelo (USD / 1M tokens). */
@Serializable
data class PriceOverride(
    val inputPricePerMTok: Double,
    val outputPricePerMTok: Double,
    val cachedInputPricePerMTok: Double? = null,
) {
    /** Aplica el override sobre el modelo semilla. */
    fun applyTo(model: ModelPricing): ModelPricing = model.copy(
        inputPricePerMTok = inputPricePerMTok,
        outputPricePerMTok = outputPricePerMTok,
        cachedInputPricePerMTok = cachedInputPricePerMTok ?: model.cachedInputPricePerMTok,
    )
}
