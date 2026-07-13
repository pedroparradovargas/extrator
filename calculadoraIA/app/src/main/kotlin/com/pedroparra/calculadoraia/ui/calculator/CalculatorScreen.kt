package com.pedroparra.calculadoraia.ui.calculator

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.ExposedDropdownMenuBox
import androidx.compose.material3.ExposedDropdownMenuDefaults
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.MenuAnchorType
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
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
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalInspectionMode
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import com.pedroparra.calculadoraia.R
import com.pedroparra.calculadoraia.core.cost.CostCalculator
import com.pedroparra.calculadoraia.core.cost.CostInput
import com.pedroparra.calculadoraia.core.pricing.ModelCatalog
import com.pedroparra.calculadoraia.core.pricing.ModelPricing
import com.pedroparra.calculadoraia.core.tokenizer.TokenCount
import com.pedroparra.calculadoraia.ui.common.formatInt
import com.pedroparra.calculadoraia.ui.common.formatTokens
import com.pedroparra.calculadoraia.ui.common.formatUsd
import com.pedroparra.calculadoraia.ui.theme.CalculadoraIaTheme

@Composable
fun CalculatorScreen(
    onOpenSettings: () -> Unit = {},
    viewModel: CalculatorViewModel = viewModel(),
) {
    val state by viewModel.ui.collectAsStateWithLifecycle()
    CalculatorContent(
        state = state,
        onTextChange = viewModel::onTextChange,
        onModelChange = viewModel::onModelChange,
        onOutputTokensChange = viewModel::onOutputTokensChange,
        onPeopleChange = viewModel::onPeopleChange,
        onMessagesPerDayChange = viewModel::onMessagesPerDayChange,
        onRecognizedText = viewModel::setExternalText,
        onOpenSettings = onOpenSettings,
    )
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CalculatorContent(
    state: CalculatorUiState,
    onTextChange: (String) -> Unit,
    onModelChange: (ModelPricing) -> Unit,
    onOutputTokensChange: (String) -> Unit,
    onPeopleChange: (String) -> Unit,
    onMessagesPerDayChange: (String) -> Unit,
    onRecognizedText: (String) -> Unit,
    onOpenSettings: () -> Unit,
) {
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(stringResource(R.string.calc_title)) },
                actions = {
                    TextButton(onClick = onOpenSettings) {
                        Text(stringResource(R.string.settings))
                    }
                },
            )
        },
    ) { padding ->
        Column(
            modifier = Modifier
                .padding(padding)
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 16.dp, vertical = 12.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            OutlinedTextField(
                value = state.text,
                onValueChange = onTextChange,
                label = { Text(stringResource(R.string.prompt_label)) },
                placeholder = { Text(stringResource(R.string.prompt_placeholder)) },
                minLines = 3,
                modifier = Modifier.fillMaxWidth(),
            )

            // OCR (galería/cámara) y voz. Se omite en el preview del IDE.
            if (!LocalInspectionMode.current) {
                InputActions(onRecognizedText = onRecognizedText)
            }

            ModelSelector(
                selected = state.model,
                models = state.availableModels,
                onModelChange = onModelChange,
            )

            OutlinedTextField(
                value = state.outputTokensInput,
                onValueChange = onOutputTokensChange,
                label = { Text(stringResource(R.string.output_tokens_label)) },
                singleLine = true,
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                modifier = Modifier.fillMaxWidth(),
            )

            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                OutlinedTextField(
                    value = state.peopleInput,
                    onValueChange = onPeopleChange,
                    label = { Text(stringResource(R.string.people_label)) },
                    singleLine = true,
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                    modifier = Modifier.weight(1f),
                )
                OutlinedTextField(
                    value = state.messagesPerDayInput,
                    onValueChange = onMessagesPerDayChange,
                    label = { Text(stringResource(R.string.messages_per_day_label)) },
                    singleLine = true,
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                    modifier = Modifier.weight(1f),
                )
            }

            ResultCard(state = state)
            ComparisonCard(state = state)
            Spacer(Modifier.height(8.dp))
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun ModelSelector(
    selected: ModelPricing,
    models: List<ModelPricing>,
    onModelChange: (ModelPricing) -> Unit,
) {
    var expanded by remember { mutableStateOf(false) }
    ExposedDropdownMenuBox(
        expanded = expanded,
        onExpandedChange = { expanded = it },
    ) {
        OutlinedTextField(
            value = selected.displayName,
            onValueChange = {},
            readOnly = true,
            label = { Text(stringResource(R.string.model_label)) },
            trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = expanded) },
            modifier = Modifier
                .menuAnchor(MenuAnchorType.PrimaryNotEditable)
                .fillMaxWidth(),
        )
        androidx.compose.material3.ExposedDropdownMenu(
            expanded = expanded,
            onDismissRequest = { expanded = false },
        ) {
            models.forEach { model ->
                DropdownMenuItem(
                    text = { Text(model.displayName) },
                    onClick = {
                        onModelChange(model)
                        expanded = false
                    },
                )
            }
        }
    }
}

@Composable
private fun ResultCard(state: CalculatorUiState) {
    val tokenCount = state.tokenCount ?: return
    val cost = state.cost ?: return
    val context = LocalContext.current

    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.elevatedCardColors(),
        elevation = CardDefaults.elevatedCardElevation(),
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text(
                    text = stringResource(R.string.results_title),
                    style = MaterialTheme.typography.titleMedium,
                    modifier = Modifier.weight(1f),
                )
                if (state.model.isApproximate) {
                    Text(
                        text = stringResource(R.string.approx_badge),
                        style = MaterialTheme.typography.labelMedium,
                        color = MaterialTheme.colorScheme.tertiary,
                    )
                }
            }

            Row(modifier = Modifier.fillMaxWidth()) {
                StatCell(formatInt(tokenCount.tokens), stringResource(R.string.stat_tokens), Modifier.weight(1f))
                StatCell(formatInt(tokenCount.characters), stringResource(R.string.stat_chars), Modifier.weight(1f))
                StatCell(formatInt(tokenCount.words), stringResource(R.string.stat_words), Modifier.weight(1f))
            }

            HorizontalDivider()
            SectionHeader(stringResource(R.string.section_message))
            ResultRow(stringResource(R.string.tokens_per_message), formatInt(cost.tokensPerMessage))
            ResultRow(stringResource(R.string.cost_per_message), formatUsd(cost.costPerMessage))

            HorizontalDivider()
            SectionHeader(stringResource(R.string.section_person))
            ResultRow(stringResource(R.string.cost_per_person_day), formatUsd(cost.costPerPersonPerDay))
            ResultRow(stringResource(R.string.cost_per_person_month), formatUsd(cost.costPerPersonPerPeriod))

            HorizontalDivider()
            SectionHeader(stringResource(R.string.section_total, cost.people))
            ResultRow(stringResource(R.string.cost_total_day), formatUsd(cost.costTotalPerDay))
            ResultRow(stringResource(R.string.cost_total_month), formatUsd(cost.costTotalPerPeriod), emphasize = true)
            ResultRow(stringResource(R.string.tokens_total_month), formatTokens(cost.tokensTotalPerPeriod))

            Text(
                text = stringResource(R.string.price_note, state.model.lastUpdated),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )

            TextButton(
                onClick = { shareResult(context, state) },
                modifier = Modifier.align(Alignment.End),
            ) { Text(stringResource(R.string.share)) }
        }
    }
}

@Composable
private fun ComparisonCard(state: CalculatorUiState) {
    if (state.comparison.isEmpty()) return
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.elevatedCardColors(),
        elevation = CardDefaults.elevatedCardElevation(),
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Text(
                text = stringResource(R.string.comparison_title),
                style = MaterialTheme.typography.titleMedium,
            )
            state.comparison.forEachIndexed { index, summary ->
                val cheapest = index == 0
                Row(modifier = Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        text = summary.model.displayName + if (summary.approximate) " ≈" else "",
                        style = MaterialTheme.typography.bodyMedium,
                        fontWeight = if (cheapest) FontWeight.Bold else FontWeight.Normal,
                        modifier = Modifier.weight(1f),
                    )
                    Text(
                        text = formatUsd(summary.monthlyTotal),
                        style = MaterialTheme.typography.bodyLarge,
                        fontWeight = if (cheapest) FontWeight.Bold else FontWeight.Normal,
                        color = if (cheapest) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurface,
                    )
                }
            }
        }
    }
}

@Composable
private fun StatCell(value: String, label: String, modifier: Modifier = Modifier) {
    Column(modifier = modifier, horizontalAlignment = Alignment.CenterHorizontally) {
        Text(text = value, style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.SemiBold)
        Text(text = label, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
    }
}

@Composable
private fun SectionHeader(text: String) {
    Text(
        text = text,
        style = MaterialTheme.typography.labelLarge,
        color = MaterialTheme.colorScheme.primary,
    )
}

@Composable
private fun ResultRow(label: String, value: String, emphasize: Boolean = false) {
    Row(modifier = Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
        Text(text = label, style = MaterialTheme.typography.bodyMedium, modifier = Modifier.weight(1f))
        Text(
            text = value,
            style = if (emphasize) MaterialTheme.typography.titleMedium else MaterialTheme.typography.bodyLarge,
            fontWeight = if (emphasize) FontWeight.Bold else FontWeight.Normal,
        )
    }
}

private val previewState: CalculatorUiState = run {
    val model = ModelCatalog.default
    CalculatorUiState(
        text = "Explain quantum computing in simple terms.",
        model = model,
        tokenCount = TokenCount(tokens = 8, characters = 42, words = 6, approximate = false),
        cost = CostCalculator.compute(
            CostInput(
                tokensIn = 8, tokensOut = 300, people = 10,
                messagesPerPersonPerDay = 5.0, days = 30,
                priceInPerMTok = model.inputPricePerMTok,
                priceOutPerMTok = model.outputPricePerMTok,
                cachedInputPricePerMTok = model.cachedInputPricePerMTok,
            ),
        ),
    )
}

@Preview(showBackground = true)
@Composable
private fun CalculatorPreview() {
    CalculadoraIaTheme {
        Surface {
            CalculatorContent(
                state = previewState,
                onTextChange = {},
                onModelChange = {},
                onOutputTokensChange = {},
                onPeopleChange = {},
                onMessagesPerDayChange = {},
                onRecognizedText = {},
                onOpenSettings = {},
            )
        }
    }
}
