package com.pedroparra.calculadoraia.core.pricing

import com.pedroparra.calculadoraia.core.tokenizer.TokenEncoding

/**
 * Catálogo semilla de modelos con precios de referencia (USD / 1M tokens).
 *
 * ⚠️ Los precios cambian con frecuencia. Estos son valores de PARTIDA a fecha
 * [SEED_DATE]; la app permite editarlos y persiste los cambios. Verifica siempre
 * la web oficial de cada proveedor antes de tomar decisiones de coste.
 */
object ModelCatalog {

    const val SEED_DATE = "2026-07-01"

    val defaults: List<ModelPricing> = listOf(
        // --- OpenAI (conteo EXACTO con jtokkit) ---
        ModelPricing(
            id = "gpt-4o", displayName = "GPT-4o", provider = Provider.OPENAI,
            encoding = TokenEncoding.O200K_BASE,
            inputPricePerMTok = 2.50, outputPricePerMTok = 10.00,
            cachedInputPricePerMTok = 1.25, lastUpdated = SEED_DATE,
        ),
        ModelPricing(
            id = "gpt-4o-mini", displayName = "GPT-4o mini", provider = Provider.OPENAI,
            encoding = TokenEncoding.O200K_BASE,
            inputPricePerMTok = 0.15, outputPricePerMTok = 0.60,
            cachedInputPricePerMTok = 0.075, lastUpdated = SEED_DATE,
        ),
        ModelPricing(
            id = "gpt-4.1", displayName = "GPT-4.1", provider = Provider.OPENAI,
            encoding = TokenEncoding.O200K_BASE,
            inputPricePerMTok = 2.00, outputPricePerMTok = 8.00,
            cachedInputPricePerMTok = 0.50, lastUpdated = SEED_DATE,
        ),
        ModelPricing(
            id = "gpt-4.1-mini", displayName = "GPT-4.1 mini", provider = Provider.OPENAI,
            encoding = TokenEncoding.O200K_BASE,
            inputPricePerMTok = 0.40, outputPricePerMTok = 1.60, lastUpdated = SEED_DATE,
        ),
        ModelPricing(
            id = "gpt-3.5-turbo", displayName = "GPT-3.5 Turbo", provider = Provider.OPENAI,
            encoding = TokenEncoding.CL100K_BASE,
            inputPricePerMTok = 0.50, outputPricePerMTok = 1.50, lastUpdated = SEED_DATE,
        ),

        // --- Anthropic (aproximado: no hay BPE offline público) ---
        ModelPricing(
            id = "claude-sonnet-4", displayName = "Claude Sonnet 4", provider = Provider.ANTHROPIC,
            encoding = null, inputPricePerMTok = 3.00, outputPricePerMTok = 15.00,
            approxCharsPerToken = 3.6, lastUpdated = SEED_DATE,
        ),
        ModelPricing(
            id = "claude-haiku-3.5", displayName = "Claude Haiku 3.5", provider = Provider.ANTHROPIC,
            encoding = null, inputPricePerMTok = 0.80, outputPricePerMTok = 4.00,
            approxCharsPerToken = 3.6, lastUpdated = SEED_DATE,
        ),

        // --- Google (aproximado) ---
        ModelPricing(
            id = "gemini-2.5-pro", displayName = "Gemini 2.5 Pro", provider = Provider.GOOGLE,
            encoding = null, inputPricePerMTok = 1.25, outputPricePerMTok = 10.00,
            approxCharsPerToken = 4.0, lastUpdated = SEED_DATE,
        ),
        ModelPricing(
            id = "gemini-2.5-flash", displayName = "Gemini 2.5 Flash", provider = Provider.GOOGLE,
            encoding = null, inputPricePerMTok = 0.30, outputPricePerMTok = 2.50,
            approxCharsPerToken = 4.0, lastUpdated = SEED_DATE,
        ),
    )

    fun byId(id: String): ModelPricing? = defaults.firstOrNull { it.id == id }

    /** Modelo por defecto de la app. */
    val default: ModelPricing get() = defaults.first()
}
