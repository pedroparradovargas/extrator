package com.pedroparra.calculadoraia.core.tokenizer

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class ApproxTokenizerTest {

    @Test
    fun approximatesByCharsPerToken() {
        val c = ApproxTokenizer(charsPerToken = 4.0).count("abcdefgh") // 8 → ceil(8/4)=2
        assertEquals(2, c.tokens)
        assertEquals(8, c.characters)
        assertTrue(c.approximate)
    }

    @Test
    fun roundsUp() {
        val c = ApproxTokenizer(charsPerToken = 4.0).count("abcdefghi") // 9 → ceil(2.25)=3
        assertEquals(3, c.tokens)
    }

    @Test
    fun emptyIsZero() {
        assertEquals(0, ApproxTokenizer().count("").tokens)
    }
}
