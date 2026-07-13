package com.pedroparra.calculadoraia.ui.calculator

import androidx.lifecycle.ViewModel
import com.pedroparra.calculadoraia.core.cost.CostCalculator
import com.pedroparra.calculadoraia.core.cost.CostInput
import com.pedroparra.calculadoraia.core.pricing.ModelPricing
import com.pedroparra.calculadoraia.core.tokenizer.TokenizerFactory
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update

class CalculatorViewModel : ViewModel() {

    private val _ui = MutableStateFlow(CalculatorUiState())
    val ui: StateFlow<CalculatorUiState> = _ui.asStateFlow()

    init {
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
        val tokenCount = TokenizerFactory.forModel(s.model).count(s.text)
        val cost = CostCalculator.compute(
            CostInput(
                tokensIn = tokenCount.tokens,
                tokensOut = s.outputTokensInput.toIntOrNull() ?: 0,
                people = s.peopleInput.toIntOrNull() ?: 0,
                messagesPerPersonPerDay = s.messagesPerDayInput.toDoubleOrNull() ?: 0.0,
                days = 30,
                priceInPerMTok = s.model.inputPricePerMTok,
                priceOutPerMTok = s.model.outputPricePerMTok,
                cachedInputPricePerMTok = s.model.cachedInputPricePerMTok,
            ),
        )
        _ui.update { it.copy(tokenCount = tokenCount, cost = cost) }
    }
}

private fun String.digits(): String = filter { it.isDigit() }
private fun String.decimal(): String = filter { it.isDigit() || it == '.' }
