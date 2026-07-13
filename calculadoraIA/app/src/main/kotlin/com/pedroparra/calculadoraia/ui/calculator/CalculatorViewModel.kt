package com.pedroparra.calculadoraia.ui.calculator

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.pedroparra.calculadoraia.core.cost.CostCalculator
import com.pedroparra.calculadoraia.core.cost.CostInput
import com.pedroparra.calculadoraia.core.cost.CostResult
import com.pedroparra.calculadoraia.core.pricing.ModelPricing
import com.pedroparra.calculadoraia.core.tokenizer.TokenizerFactory
import com.pedroparra.calculadoraia.data.PricingRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

class CalculatorViewModel(application: Application) : AndroidViewModel(application) {

    private val pricingRepository = PricingRepository(application)

    private val _ui = MutableStateFlow(CalculatorUiState())
    val ui: StateFlow<CalculatorUiState> = _ui.asStateFlow()

    init {
        // Mantiene el catálogo (y el modelo seleccionado) en sincronía con los
        // precios que el usuario edite en Ajustes.
        viewModelScope.launch {
            pricingRepository.models.collect { models ->
                _ui.update { state ->
                    val selected = models.firstOrNull { it.id == state.model.id } ?: models.first()
                    state.copy(availableModels = models, model = selected)
                }
                recompute()
            }
        }
        recompute()
    }

    fun onTextChange(value: String) = mutate { it.copy(text = value) }
    fun onModelChange(model: ModelPricing) = mutate { it.copy(model = model) }
    fun onOutputTokensChange(value: String) = mutate { it.copy(outputTokensInput = value.digits()) }
    fun onPeopleChange(value: String) = mutate { it.copy(peopleInput = value.digits()) }
    fun onMessagesPerDayChange(value: String) = mutate { it.copy(messagesPerDayInput = value.decimal()) }

    /** Reemplaza el texto (usado por OCR/voz para inyectar lo reconocido). */
    fun setExternalText(value: String) = mutate { it.copy(text = value) }
    fun clearText() = mutate { it.copy(text = "") }

    private inline fun mutate(block: (CalculatorUiState) -> CalculatorUiState) {
        _ui.update(block)
        recompute()
    }

    private fun recompute() {
        val s = _ui.value
        val outTokens = s.outputTokensInput.toIntOrNull() ?: 0
        val people = s.peopleInput.toIntOrNull() ?: 0
        val msgs = s.messagesPerDayInput.toDoubleOrNull() ?: 0.0

        fun costFor(m: ModelPricing, tokensIn: Int): CostResult = CostCalculator.compute(
            CostInput(
                tokensIn = tokensIn,
                tokensOut = outTokens,
                people = people,
                messagesPerPersonPerDay = msgs,
                days = 30,
                priceInPerMTok = m.inputPricePerMTok,
                priceOutPerMTok = m.outputPricePerMTok,
                cachedInputPricePerMTok = m.cachedInputPricePerMTok,
            ),
        )

        val tokenCount = TokenizerFactory.forModel(s.model).count(s.text)
        val cost = costFor(s.model, tokenCount.tokens)

        // Comparativa: coste mensual total de cada modelo para el mismo texto.
        val comparison = s.availableModels.map { m ->
            val tokensIn = if (m.id == s.model.id) tokenCount.tokens
            else TokenizerFactory.forModel(m).count(s.text).tokens
            ModelCostSummary(
                model = m,
                tokensIn = tokensIn,
                monthlyTotal = costFor(m, tokensIn).costTotalPerPeriod,
                approximate = m.isApproximate,
            )
        }.sortedBy { it.monthlyTotal }

        _ui.update { it.copy(tokenCount = tokenCount, cost = cost, comparison = comparison) }
    }
}

private fun String.digits(): String = filter { it.isDigit() }
private fun String.decimal(): String = filter { it.isDigit() || it == '.' }
