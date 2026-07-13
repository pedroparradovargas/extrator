package com.pedroparra.calculadoraia.core.cost

/** Resultado del cálculo de coste/tráfico. Costes en USD, tokens en unidades. */
data class CostResult(
    // Por un único mensaje
    val tokensPerMessage: Int,
    val costPerMessage: Double,

    // Por persona
    val tokensPerPersonPerDay: Double,
    val costPerPersonPerDay: Double,
    val tokensPerPersonPerPeriod: Double,
    val costPerPersonPerPeriod: Double,

    // Totales para las N personas
    val tokensTotalPerDay: Double,
    val costTotalPerDay: Double,
    val tokensTotalPerPeriod: Double,
    val costTotalPerPeriod: Double,

    val people: Int,
    val days: Int,
)
