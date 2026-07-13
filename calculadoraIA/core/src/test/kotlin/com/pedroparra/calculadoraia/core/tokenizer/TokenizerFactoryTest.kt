package com.pedroparra.calculadoraia.core.tokenizer

import com.pedroparra.calculadoraia.core.pricing.ModelCatalog
import kotlin.test.Test
import kotlin.test.assertFalse
import kotlin.test.assertTrue

class TokenizerFactoryTest {

    @Test
    fun openAiModelUsesExactTokenizer() {
        val model = requireNotNull(ModelCatalog.byId("gpt-4o"))
        assertFalse(TokenizerFactory.forModel(model).count("hello world").approximate)
    }

    @Test
    fun claudeModelUsesApproxTokenizer() {
        val model = requireNotNull(ModelCatalog.byId("claude-sonnet-4"))
        assertTrue(TokenizerFactory.forModel(model).count("hello world").approximate)
    }
}
