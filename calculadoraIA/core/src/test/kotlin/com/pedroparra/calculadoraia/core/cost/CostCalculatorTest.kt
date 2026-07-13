package com.pedroparra.calculadoraia.core.cost

import kotlin.test.Test
import kotlin.test.assertEquals

class CostCalculatorTest {

    private val delta = 1e-9

    @Test
    fun scalesCostForNPeople() {
        val r = CostCalculator.compute(
            CostInput(
                tokensIn = 1000, tokensOut = 1000,
                people = 10, messagesPerPersonPerDay = 5.0, days = 30,
                priceInPerMTok = 2.50, priceOutPerMTok = 10.00,
            ),
        )
        assertEquals(2000, r.tokensPerMessage)
        assertEquals(0.0125, r.costPerMessage, delta)        // 1000/1e6*2.5 + 1000/1e6*10
        assertEquals(0.0625, r.costPerPersonPerDay, delta)   // *5
        assertEquals(1.875, r.costPerPersonPerPeriod, delta) // *30
        assertEquals(0.625, r.costTotalPerDay, delta)        // *10 personas
        assertEquals(18.75, r.costTotalPerPeriod, delta)     // *10 personas
        assertEquals(3_000_000.0, r.tokensTotalPerPeriod, delta) // 2000*5*30*10
    }

    @Test
    fun appliesCacheDiscount() {
        val r = CostCalculator.compute(
            CostInput(
                tokensIn = 1000, tokensOut = 0,
                people = 1, messagesPerPersonPerDay = 1.0, days = 1,
                priceInPerMTok = 2.50, priceOutPerMTok = 10.00,
                cachedInputPricePerMTok = 1.25, cachedFraction = 0.5,
            ),
        )
        // 500 tok @2.5/M + 500 tok @1.25/M = 0.00125 + 0.000625
        assertEquals(0.001875, r.costPerMessage, delta)
    }

    @Test
    fun negativeInputsAreCoercedToZero() {
        val r = CostCalculator.compute(
            CostInput(
                tokensIn = -5, tokensOut = -5, people = -1,
                messagesPerPersonPerDay = -1.0, days = -1,
                priceInPerMTok = 2.5, priceOutPerMTok = 10.0,
            ),
        )
        assertEquals(0.0, r.costTotalPerPeriod, delta)
        assertEquals(0, r.people)
    }
}
