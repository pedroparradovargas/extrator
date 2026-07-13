package com.pedroparra.calculadoraia.ui.common

import java.util.Locale

/** Formatea un coste en USD, ajustando decimales según la magnitud. */
fun formatUsd(value: Double): String = when {
    value <= 0.0 -> "$0.00"
    value < 0.01 -> String.format(Locale.US, "$%.5f", value)
    value < 1.0 -> String.format(Locale.US, "$%.4f", value)
    else -> String.format(Locale.US, "$%,.2f", value)
}

/** Formatea una cantidad de tokens (con separador de miles). */
fun formatTokens(value: Double): String = String.format(Locale.US, "%,.0f", value)

fun formatInt(value: Int): String = String.format(Locale.US, "%,d", value)
