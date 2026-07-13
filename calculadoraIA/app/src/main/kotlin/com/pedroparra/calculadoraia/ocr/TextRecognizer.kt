package com.pedroparra.calculadoraia.ocr

import android.content.Context
import android.graphics.Bitmap
import android.net.Uri
import com.google.mlkit.vision.common.InputImage
import com.google.mlkit.vision.text.TextRecognition
import com.google.mlkit.vision.text.latin.TextRecognizerOptions
import kotlin.coroutines.resume
import kotlin.coroutines.resumeWithException
import kotlinx.coroutines.suspendCancellableCoroutine

/**
 * Reconocimiento de texto (OCR) on-device con ML Kit (modelo empaquetado → offline).
 * Convierte una imagen (de galería o cámara) en texto.
 */
object TextRecognizer {

    private val client = TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS)

    /** OCR sobre una imagen seleccionada de la galería (por su Uri). */
    suspend fun fromUri(context: Context, uri: Uri): String =
        process(InputImage.fromFilePath(context, uri))

    /** OCR sobre un bitmap (p. ej. la miniatura devuelta por la cámara). */
    suspend fun fromBitmap(bitmap: Bitmap): String =
        process(InputImage.fromBitmap(bitmap, 0))

    private suspend fun process(image: InputImage): String =
        suspendCancellableCoroutine { cont ->
            client.process(image)
                .addOnSuccessListener { cont.resume(it.text) }
                .addOnFailureListener { cont.resumeWithException(it) }
        }
}
