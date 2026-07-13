package com.pedroparra.calculadoraia.core.pricing

import com.pedroparra.calculadoraia.core.tokenizer.TokenEncoding
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNotNull
import kotlin.test.assertNull
import kotlin.test.assertTrue

class ModelCatalogTest {

    @Test
    fun hasSeedModels() {
        assertTrue(ModelCatalog.defaults.isNotEmpty())
    }

    @Test
    fun openAiModelsHaveExactEncoding() {
        val gpt4o = requireNotNull(ModelCatalog.byId("gpt-4o"))
        assertEquals(TokenEncoding.O200K_BASE, gpt4o.encoding)
        assertEquals(false, gpt4o.isApproximate)
    }

    @Test
    fun anthropicModelsUseApproximation() {
        val claude = requireNotNull(ModelCatalog.byId("claude-sonnet-4"))
        assertNull(claude.encoding)
        assertNotNull(claude.approxCharsPerToken)
        assertTrue(claude.isApproximate)
    }

    @Test
    fun idsAreUnique() {
        val ids = ModelCatalog.defaults.map { it.id }
        assertEquals(ids.size, ids.toSet().size)
    }
}
