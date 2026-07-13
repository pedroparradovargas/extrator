package com.pedroparra.calculadoraia.core.tokenizer

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue

class JtokkitTokenizerTest {

    @Test
    fun emptyStringHasZeroTokens() {
        val c = JtokkitTokenizer(TokenEncoding.CL100K_BASE).count("")
        assertEquals(0, c.tokens)
        assertEquals(0, c.characters)
        assertEquals(0, c.words)
        assertFalse(c.approximate)
    }

    @Test
    fun cl100kCountsHelloWorld() {
        val c = JtokkitTokenizer(TokenEncoding.CL100K_BASE).count("hello world")
        assertEquals(2, c.tokens) // "hello" + " world"
        assertEquals(11, c.characters)
        assertEquals(2, c.words)
        assertFalse(c.approximate)
    }

    @Test
    fun o200kCountsHelloWorld() {
        val c = JtokkitTokenizer(TokenEncoding.O200K_BASE).count("hello world")
        assertEquals(2, c.tokens)
    }

    @Test
    fun countsAreExactNotApproximate() {
        val c = JtokkitTokenizer(TokenEncoding.O200K_BASE).count("El veloz murciélago")
        assertFalse(c.approximate)
        assertTrue(c.tokens > 0)
    }
}
