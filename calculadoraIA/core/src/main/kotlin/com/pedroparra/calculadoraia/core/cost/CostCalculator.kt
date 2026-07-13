package com.pedroparra.calculadoraia.core.cost

/**
 * Calculadora PURA de coste/tráfico. Sin dependencias de plataforma → testeable
 * en la JVM sin emulador.
 *
 * Fórmula base:
 *   costeMensaje    = tokensIn/1e6 * priceIn + tokensOut/1e6 * priceOut
 *   costePersonaMes = costeMensaje * mensajesPorDia * dias
 *   costeMesTotal   = costePersonaMes * N
 */
object CostCalculator {

    private const val MILLION = 1_000_000.0

    fun compute(input: CostInput): CostResult {
        val tIn = input.tokensIn.coerceAtLeast(0)
        val tOut = input.tokensOut.coerceAtLeast(0)
        val n = input.people.coerceAtLeast(0)
        val m = input.messagesPerPersonPerDay.coerceAtLeast(0.0)
        val d = input.days.coerceAtLeast(0)
        val f = input.cachedFraction.coerceIn(0.0, 1.0)

        val cachedPrice = input.cachedInputPricePerMTok ?: input.priceInPerMTok
        val inputCost =
            (tIn * (1.0 - f) / MILLION) * input.priceInPerMTok +
                (tIn * f / MILLION) * cachedPrice
        val outputCost = (tOut / MILLION) * input.priceOutPerMTok
        val costPerMessage = inputCost + outputCost

        val tokensPerMessage = tIn + tOut

        val costPerPersonPerDay = costPerMessage * m
        val costPerPersonPerPeriod = costPerPersonPerDay * d
        val tokensPerPersonPerDay = tokensPerMessage * m
        val tokensPerPersonPerPeriod = tokensPerPersonPerDay * d

        return CostResult(
            tokensPerMessage = tokensPerMessage,
            costPerMessage = costPerMessage,
            tokensPerPersonPerDay = tokensPerPersonPerDay,
            costPerPersonPerDay = costPerPersonPerDay,
            tokensPerPersonPerPeriod = tokensPerPersonPerPeriod,
            costPerPersonPerPeriod = costPerPersonPerPeriod,
            tokensTotalPerDay = tokensPerPersonPerDay * n,
            costTotalPerDay = costPerPersonPerDay * n,
            tokensTotalPerPeriod = tokensPerPersonPerPeriod * n,
            costTotalPerPeriod = costPerPersonPerPeriod * n,
            people = n,
            days = d,
        )
    }
}
