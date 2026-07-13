package com.pedroparra.calculadoraia.ui.settings

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Card
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import com.pedroparra.calculadoraia.R
import com.pedroparra.calculadoraia.core.pricing.ModelPricing
import com.pedroparra.calculadoraia.ui.common.formatUsd

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen(
    onBack: () -> Unit,
    viewModel: SettingsViewModel = viewModel(),
) {
    val models by viewModel.models.collectAsStateWithLifecycle()
    var editing by remember { mutableStateOf<ModelPricing?>(null) }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(stringResource(R.string.settings_title)) },
                navigationIcon = {
                    TextButton(onClick = onBack) { Text(stringResource(R.string.back)) }
                },
            )
        },
    ) { padding ->
        LazyColumn(
            modifier = Modifier
                .padding(padding)
                .fillMaxSize(),
            contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            item {
                Text(
                    text = stringResource(R.string.settings_subtitle),
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            items(models, key = { it.id }) { model ->
                ModelPriceCard(model = model, onEdit = { editing = model })
            }
        }
    }

    editing?.let { model ->
        EditPriceDialog(
            model = model,
            onDismiss = { editing = null },
            onSave = { input, output, cached ->
                viewModel.save(model.id, input, output, cached)
                editing = null
            },
            onReset = {
                viewModel.reset(model.id)
                editing = null
            },
        )
    }
}

@Composable
private fun ModelPriceCard(model: ModelPricing, onEdit: () -> Unit) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Row(
            modifier = Modifier
                .padding(16.dp)
                .fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(text = model.displayName, style = MaterialTheme.typography.titleSmall)
                Text(
                    text = stringResource(
                        R.string.price_in_out,
                        formatUsd(model.inputPricePerMTok),
                        formatUsd(model.outputPricePerMTok),
                    ),
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            OutlinedButton(onClick = onEdit) { Text(stringResource(R.string.edit)) }
        }
    }
}

@Composable
private fun EditPriceDialog(
    model: ModelPricing,
    onDismiss: () -> Unit,
    onSave: (input: Double, output: Double, cached: Double?) -> Unit,
    onReset: () -> Unit,
) {
    var input by remember { mutableStateOf(model.inputPricePerMTok.toString()) }
    var output by remember { mutableStateOf(model.outputPricePerMTok.toString()) }
    var cached by remember { mutableStateOf(model.cachedInputPricePerMTok?.toString() ?: "") }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(model.displayName) },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                PriceField(input, { input = it }, stringResource(R.string.price_input))
                PriceField(output, { output = it }, stringResource(R.string.price_output))
                PriceField(cached, { cached = it }, stringResource(R.string.price_cached))
            }
        },
        confirmButton = {
            TextButton(onClick = {
                onSave(
                    input.toDoubleOrNull() ?: model.inputPricePerMTok,
                    output.toDoubleOrNull() ?: model.outputPricePerMTok,
                    cached.toDoubleOrNull(),
                )
            }) { Text(stringResource(R.string.save)) }
        },
        dismissButton = {
            TextButton(onClick = onReset) { Text(stringResource(R.string.reset)) }
        },
    )
}

@Composable
private fun PriceField(value: String, onValueChange: (String) -> Unit, label: String) {
    OutlinedTextField(
        value = value,
        onValueChange = { onValueChange(it.filter { c -> c.isDigit() || c == '.' }) },
        label = { Text(label) },
        singleLine = true,
        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
        modifier = Modifier.fillMaxWidth(),
    )
}
