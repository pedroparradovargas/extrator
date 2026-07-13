package com.pedroparra.calculadoraia.ui.calculator

import com.pedroparra.calculadoraia.core.cost.CostResult
import com.pedroparra.calculadoraia.core.pricing.ModelCatalog
import com.pedroparra.calculadoraia.core.pricing.ModelPricing
import com.pedroparra.calculadoraia.core.tokenizer.TokenCount

/** Coste mensual total de un modelo para el texto/parámetros actuales (comparativa). */
data class ModelCostSummary(
    val model: ModelPricing,
    val tokensIn: Int,
    val monthlyTotal: Double,
    val approximate: Boolean,
)

/** Estado de la pantalla de la calculadora. Las entradas numéricas se guardan como
 *  texto para permitir edición libre; se parsean al calcular. */
data class CalculatorUiState(
    val text: String = "",
    val model: ModelPricing = ModelCatalog.default,
    val outputTokensInput: String = "300",
    val peopleInput: String = "10",
    val messagesPerDayInput: String = "5",
    val availableModels: List<ModelPricing> = ModelCatalog.defaults,
    val tokenCount: TokenCount? = null,
    val cost: CostResult? = null,
    val comparison: List<ModelCostSummary> = emptyList(),
)
