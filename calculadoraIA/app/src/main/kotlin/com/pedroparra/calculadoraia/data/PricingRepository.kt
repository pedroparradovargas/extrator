package com.pedroparra.calculadoraia.data

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import com.pedroparra.calculadoraia.core.pricing.ModelCatalog
import com.pedroparra.calculadoraia.core.pricing.ModelPricing
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import kotlinx.serialization.decodeFromString
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json

private val Context.pricesDataStore: DataStore<Preferences> by preferencesDataStore(name = "prices")

/**
 * Fuente de verdad de los precios: el catálogo semilla ([ModelCatalog]) fusionado
 * con los overrides que el usuario haya guardado (persistidos en DataStore).
 */
class PricingRepository(context: Context) {

    private val dataStore = context.applicationContext.pricesDataStore
    private val json = Json { ignoreUnknownKeys = true }

    /** Modelos con los precios efectivos (semilla + ediciones del usuario). */
    val models: Flow<List<ModelPricing>> = dataStore.data.map { prefs ->
        val overrides = decode(prefs[OVERRIDES_KEY])
        ModelCatalog.defaults.map { model -> overrides[model.id]?.applyTo(model) ?: model }
    }

    suspend fun setOverride(id: String, override: PriceOverride) =
        mutate { it + (id to override) }

    suspend fun clearOverride(id: String) =
        mutate { it - id }

    private suspend fun mutate(transform: (Map<String, PriceOverride>) -> Map<String, PriceOverride>) {
        dataStore.edit { prefs ->
            val updated = transform(decode(prefs[OVERRIDES_KEY]))
            prefs[OVERRIDES_KEY] = json.encodeToString(updated)
        }
    }

    private fun decode(raw: String?): Map<String, PriceOverride> =
        if (raw.isNullOrBlank()) emptyMap()
        else runCatching { json.decodeFromString<Map<String, PriceOverride>>(raw) }.getOrDefault(emptyMap())

    companion object {
        private val OVERRIDES_KEY = stringPreferencesKey("price_overrides")
    }
}
