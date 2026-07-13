package com.pedroparra.calculadoraia.ui.calculator

import android.content.Context
import android.content.Intent
import com.pedroparra.calculadoraia.R
import com.pedroparra.calculadoraia.ui.common.formatInt
import com.pedroparra.calculadoraia.ui.common.formatTokens
import com.pedroparra.calculadoraia.ui.common.formatUsd

/** Comparte un resumen del resultado actual como texto plano (share sheet). */
fun shareResult(context: Context, state: CalculatorUiState) {
    val cost = state.cost ?: return
    val summary = buildString {
        appendLine("calculadoraIA — ${state.model.displayName}")
        appendLine("${context.getString(R.string.tokens_per_message)}: ${formatInt(cost.tokensPerMessage)}")
        appendLine("${context.getString(R.string.cost_per_message)}: ${formatUsd(cost.costPerMessage)}")
        appendLine("${context.getString(R.string.cost_per_person_month)}: ${formatUsd(cost.costPerPersonPerPeriod)}")
        appendLine(
            context.getString(R.string.section_total, cost.people) +
                " — ${context.getString(R.string.cost_total_month)}: ${formatUsd(cost.costTotalPerPeriod)}",
        )
        appendLine("${context.getString(R.string.tokens_total_month)}: ${formatTokens(cost.tokensTotalPerPeriod)}")
    }
    val intent = Intent(Intent.ACTION_SEND).apply {
        type = "text/plain"
        putExtra(Intent.EXTRA_TEXT, summary)
    }
    context.startActivity(Intent.createChooser(intent, context.getString(R.string.share)))
}
