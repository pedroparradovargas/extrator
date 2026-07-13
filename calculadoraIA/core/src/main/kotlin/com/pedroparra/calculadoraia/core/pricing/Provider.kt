package com.pedroparra.calculadoraia.core.pricing

import kotlinx.serialization.Serializable

/** Proveedor del modelo de lenguaje. */
@Serializable
enum class Provider { OPENAI, ANTHROPIC, GOOGLE, OTHER }
