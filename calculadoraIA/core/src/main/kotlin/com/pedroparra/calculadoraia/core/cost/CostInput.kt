package com.pedroparra.calculadoraia.core.cost

/**
 * Entradas para el cálculo de coste/tráfico escalado a N personas.
 * Precios en USD por 1.000.000 de tokens.
 */
data class CostInput(
    /** Tokens de entrada por mensaje. */
    val tokensIn: Int,
    /** Tokens de salida por mensaje. */
    val tokensOut: Int,
    /** Número de personas (N). */
    val people: Int,
    /** Mensajes por persona y día. */
    val messagesPerPersonPerDay: Double,
    /** Días del periodo (por defecto 30 ≈ un mes). */
    val days: Int = 30,
    val priceInPerMTok: Double,
    val priceOutPerMTok: Double,
    /** Tarifa de entrada cacheada; si es null se usa [priceInPerMTok]. */
    val cachedInputPricePerMTok: Double? = null,
    /** Fracción (0..1) de [tokensIn] servida desde caché. */
    val cachedFraction: Double = 0.0,
)
