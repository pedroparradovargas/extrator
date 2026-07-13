package com.pedroparra.calculadoraia.ui.settings

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.pedroparra.calculadoraia.core.pricing.ModelCatalog
import com.pedroparra.calculadoraia.core.pricing.ModelPricing
import com.pedroparra.calculadoraia.data.PriceOverride
import com.pedroparra.calculadoraia.data.PricingRepository
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

class SettingsViewModel(application: Application) : AndroidViewModel(application) {

    private val repository = PricingRepository(application)

    val models: StateFlow<List<ModelPricing>> = repository.models
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), ModelCatalog.defaults)

    fun save(id: String, input: Double, output: Double, cached: Double?) {
        viewModelScope.launch {
            repository.setOverride(id, PriceOverride(input, output, cached))
        }
    }

    fun reset(id: String) {
        viewModelScope.launch { repository.clearOverride(id) }
    }
}
