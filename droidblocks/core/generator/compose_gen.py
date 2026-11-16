"""Geracao da interface em Jetpack Compose (Material 3)."""

import re

from ...catalog.components import ICONS
from ..naming import kq, to_snake
from .context import collect_imports
from .resources import mix
from .screen_spec import ScreenSpec, action_code, viewmodel, options_of

IMPORTS = {
    "Toast": "android.widget.Toast",
    "Activity": "android.app.Activity",
    "Bundle": "android.os.Bundle",
    "ComponentActivity": "androidx.activity.ComponentActivity",
    "FragmentActivity": "androidx.fragment.app.FragmentActivity",
    "setContent": "androidx.activity.compose.setContent",
    "enableEdgeToEdge": "androidx.activity.enableEdgeToEdge",
    "ActivityResultContracts": "androidx.activity.result.contract.ActivityResultContracts",
    "installSplashScreen": "androidx.core.splashscreen.SplashScreen.Companion.installSplashScreen",
    "Composable": "androidx.compose.runtime.Composable",
    "LaunchedEffect": "androidx.compose.runtime.LaunchedEffect",
    "remember": "androidx.compose.runtime.remember",
    "mutableStateOf": "androidx.compose.runtime.mutableStateOf",
    "rememberCoroutineScope": "androidx.compose.runtime.rememberCoroutineScope",
    ".collectAsState": "androidx.compose.runtime.collectAsState",
    "staticCompositionLocalOf": "androidx.compose.runtime.staticCompositionLocalOf",
    "CompositionLocalProvider": "androidx.compose.runtime.CompositionLocalProvider",
    ".collectAsStateWithLifecycle": "androidx.lifecycle.compose.collectAsStateWithLifecycle",
    "viewModel": "androidx.lifecycle.viewmodel.compose.viewModel",
    "Modifier": "androidx.compose.ui.Modifier",
    "Alignment": "androidx.compose.ui.Alignment",
    "LocalContext": "androidx.compose.ui.platform.LocalContext",
    "stringResource": "androidx.compose.ui.res.stringResource",
    "TextAlign": "androidx.compose.ui.text.style.TextAlign",
    "FontWeight": "androidx.compose.ui.text.font.FontWeight",
    ".dp": "androidx.compose.ui.unit.dp",
    ".sp": "androidx.compose.ui.unit.sp",
    ".asImageBitmap": "androidx.compose.ui.graphics.asImageBitmap",
    "Image": "androidx.compose.foundation.Image",
    ".clickable": "androidx.compose.foundation.clickable",
    ".background": "androidx.compose.foundation.background",
    "LazyColumn": "androidx.compose.foundation.lazy.LazyColumn",
    "LazyRow": "androidx.compose.foundation.lazy.LazyRow",
    "items": "androidx.compose.foundation.lazy.items",
    "Arrangement": "androidx.compose.foundation.layout.Arrangement",
    "Box": "androidx.compose.foundation.layout.Box",
    "Column": "androidx.compose.foundation.layout.Column",
    "Row": "androidx.compose.foundation.layout.Row",
    "Spacer": "androidx.compose.foundation.layout.Spacer",
    "PaddingValues": "androidx.compose.foundation.layout.PaddingValues",
    ".fillMaxSize": "androidx.compose.foundation.layout.fillMaxSize",
    ".fillMaxWidth": "androidx.compose.foundation.layout.fillMaxWidth",
    ".height": "androidx.compose.foundation.layout.height",
    ".padding": "androidx.compose.foundation.layout.padding",
    ".size": "androidx.compose.foundation.layout.size",
    ".consumeWindowInsets": "androidx.compose.foundation.layout.consumeWindowInsets",
    "KeyboardOptions": "androidx.compose.foundation.text.KeyboardOptions",
    "KeyboardType": "androidx.compose.ui.text.input.KeyboardType",
    "PasswordVisualTransformation": "androidx.compose.ui.text.input.PasswordVisualTransformation",
    "Icons": "androidx.compose.material.icons.Icons",
    "Icon": "androidx.compose.material3.Icon",
    "IconButton": "androidx.compose.material3.IconButton",
    "Button": "androidx.compose.material3.Button",
    "OutlinedButton": "androidx.compose.material3.OutlinedButton",
    "FilledTonalButton": "androidx.compose.material3.FilledTonalButton",
    "TextButton": "androidx.compose.material3.TextButton",
    "Text": "androidx.compose.material3.Text",
    "OutlinedTextField": "androidx.compose.material3.OutlinedTextField",
    "Card": "androidx.compose.material3.Card",
    "HorizontalDivider": "androidx.compose.material3.HorizontalDivider",
    "LinearProgressIndicator": "androidx.compose.material3.LinearProgressIndicator",
    "CircularProgressIndicator": "androidx.compose.material3.CircularProgressIndicator",
    "MaterialTheme": "androidx.compose.material3.MaterialTheme",
    "Scaffold": "androidx.compose.material3.Scaffold",
    "TopAppBar": "androidx.compose.material3.TopAppBar",
    "TopAppBarDefaults": "androidx.compose.material3.TopAppBarDefaults",
    "FloatingActionButton": "androidx.compose.material3.FloatingActionButton",
    "ExperimentalMaterial3Api": "androidx.compose.material3.ExperimentalMaterial3Api",
    "PullToRefreshBox": "androidx.compose.material3.pulltorefresh.PullToRefreshBox",
    "NavigationBar": "androidx.compose.material3.NavigationBar",
    "NavigationBarItem": "androidx.compose.material3.NavigationBarItem",
    "ModalNavigationDrawer": "androidx.compose.material3.ModalNavigationDrawer",
    "ModalDrawerSheet": "androidx.compose.material3.ModalDrawerSheet",
    "NavigationDrawerItem": "androidx.compose.material3.NavigationDrawerItem",
    "DrawerValue": "androidx.compose.material3.DrawerValue",
    "rememberDrawerState": "androidx.compose.material3.rememberDrawerState",
    "AsyncImage": "coil.compose.AsyncImage",
    "ContentScale": "androidx.compose.ui.layout.ContentScale",
    ".clip": "androidx.compose.ui.draw.clip",
    "RoundedCornerShape": "androidx.compose.foundation.shape.RoundedCornerShape",
    "NavHost": "androidx.navigation.compose.NavHost",
    "composable": "androidx.navigation.compose.composable",
    "rememberNavController": "androidx.navigation.compose.rememberNavController",
    ".currentBackStackEntryAsState": "androidx.navigation.compose.currentBackStackEntryAsState",
    "navArgument": "androidx.navigation.navArgument",
    "NavType": "androidx.navigation.NavType",
    ".findStartDestination": "androidx.navigation.NavGraph.Companion.findStartDestination",
    "Uri": "android.net.Uri",
    ".launch": "kotlinx.coroutines.launch",
    "IntentHelper": "%PKG%.util.IntentHelper",
    ".findActivity": "%PKG%.util.findActivity",
    "PermissionHelper": "%PKG%.util.PermissionHelper",
    "StartupPermissions": "%PKG%.util.StartupPermissions",
    "R": "%PKG%.R",
    "Routes": "%PKG%.navigation.Routes",
    "AppTheme": "%PKG%.ui.theme.AppTheme",
    "AppNavigation": "%PKG%.navigation.AppNavigation",
    "ListItem": "%PKG%.data.model.ListItem",
    ".asPrice": "%PKG%.data.model.asPrice",
    "LocalDrawerOpener": "%PKG%.navigation.LocalDrawerOpener",
}

UI_COMPONENTS = ["ItemRow", "GridCard", "DetailCard", "StatCard", "BannerCard", "AvatarHeader", "EmptyState",
                 "DropdownField", "RadioGroupField", "ChipsField", "TabsField", "LabeledCheckbox",
                 "LabeledSwitch", "SliderField", "RatingField", "QuantityStepper", "DatePickerField",
                 "WebViewBox", "CartSummary", "TimerBlock", "QrImage", "PhotoBox", "BarChart", "LineChart",
                 "PieChart", "MonthCalendar"]


def generate(ctx):
    _theme(ctx)
    _common(ctx)
    specs = [ScreenSpec(ctx, s) for s in ctx.project.screens]
    for spec in specs:
        ctx.add_kotlin(f"{ctx.screen_dir(spec.screen)}/{spec.cls}ViewModel.kt", viewmodel(ctx, spec))
        ctx.add_kotlin(f"{ctx.screen_dir(spec.screen)}/{spec.cls}Screen.kt", _screen(ctx, spec))
    _navigation(ctx, specs)
    _main_activity(ctx)


def finalize(ctx, body, package, extra_imports=(), header=""):
    imports = collect_imports(body, IMPORTS, extra_imports)
    if ctx.has_feature_files() and ".features." not in package:
        imports.append("%PKG%.features.*")
    imports = sorted({i.replace("%PKG%", ctx.pkg) for i in imports
                      if i.replace("%PKG%", ctx.pkg).rsplit(".", 1)[0] != package})
    lines = [header] if header else []
    lines.append(f"package {package}")
    lines.append("")
    lines += [f"import {i}" for i in imports]
    lines.append("")
    lines.append(body.strip("\n"))
    return "\n".join(lines) + "\n"


# ----------------------------------------------------------------- tema

def _theme(ctx):
    p = ctx.project
    light = (p.primary_color, p.secondary_color, p.tertiary_color)
    dark = tuple(mix(c, "#FFFFFF", 0.35) for c in light)

    def c(hexv):
        return "Color(0xFF" + hexv.lstrip("#").upper() + ")"

    ctx.add_kotlin("ui/theme/Color.kt", f'''package %PKG%.ui.theme

import androidx.compose.ui.graphics.Color

// Paleta definida no DroidBlocks (tons claros e versoes para o modo escuro).
val Primary = {c(light[0])}
val Secondary = {c(light[1])}
val Tertiary = {c(light[2])}
val PrimaryDark = {c(dark[0])}
val SecondaryDark = {c(dark[1])}
val TertiaryDark = {c(dark[2])}
''')
    ctx.add_kotlin("ui/theme/Type.kt", '''package %PKG%.ui.theme

import androidx.compose.material3.Typography

/** Tipografia padrao do Material 3. Personalize fontes e tamanhos aqui. */
val AppTypography = Typography()
''')
    default_dark = {"light": "false", "dark": "true"}.get(p.theme_mode, "isSystemInDarkTheme()")
    dynamic = "dynamic_color" in ctx.resolved.flags
    dyn_param = "dynamicColor: Boolean = true, " if dynamic else ""
    dyn_body = ('''    // Material You: no Android 12+ as cores vem do papel de parede do usuario.
    val context = LocalContext.current
    val colors = when {
        dynamicColor && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S ->
            if (darkTheme) dynamicDarkColorScheme(context) else dynamicLightColorScheme(context)
        darkTheme -> DarkColors
        else -> LightColors
    }
''' if dynamic else "")
    scheme = "colors" if dynamic else "if (darkTheme) DarkColors else LightColors"
    dyn_imports = ("import android.os.Build\nimport androidx.compose.material3.dynamicDarkColorScheme\n"
                   "import androidx.compose.material3.dynamicLightColorScheme\n"
                   "import androidx.compose.ui.platform.LocalContext\n") if dynamic else ""
    ctx.add_kotlin("ui/theme/Theme.kt", f'''package %PKG%.ui.theme

{dyn_imports}import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val LightColors = lightColorScheme(
    primary = Primary,
    onPrimary = Color.White,
    secondary = Secondary,
    onSecondary = Color.White,
    tertiary = Tertiary
)

private val DarkColors = darkColorScheme(
    primary = PrimaryDark,
    onPrimary = Color.Black,
    secondary = SecondaryDark,
    tertiary = TertiaryDark
)

/** Tema do aplicativo. darkTheme segue o sistema, a menos que o projeto force um modo. */
@Composable
fun AppTheme(darkTheme: Boolean = {default_dark}, {dyn_param}content: @Composable () -> Unit) {{
{dyn_body}    MaterialTheme(
        colorScheme = {scheme},
        typography = AppTypography,
        content = content
    )
}}
''')


# ----------------------------------------------------------------- componentes comuns

def _common(ctx):
    r = ctx.resolved
    parts = [COMMON_BASE, COMMON_EXTRA]
    if r.has("cart"):
        parts.append(COMMON_CART)
    if r.has("timer"):
        parts.append(COMMON_TIMER)
    if r.has("qr_generator"):
        parts.append(COMMON_QR)
    bridge = r.has("webview_bridge")
    body = "\n\n".join(parts)
    body = body.replace("BRIDGE_SETUP", 'addJavascriptInterface(JsBridge(context), "App")' if bridge else
                        "// Ative a funcionalidade 'Ponte JavaScript' para expor funcoes ao site.")
    imports = """import android.annotation.SuppressLint
import android.app.DatePickerDialog
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Surface
import androidx.compose.material3.TextButton
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.style.TextDecoration
import %PKG%.util.IntentHelper
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowDropDown
import androidx.compose.material.icons.filled.DateRange
import androidx.compose.material.icons.filled.Star
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Checkbox
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilterChip
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Slider
import androidx.compose.material3.Switch
import androidx.compose.material3.Tab
import androidx.compose.material3.TabRow
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import coil.compose.AsyncImage
import %PKG%.data.model.ListItem
import %PKG%.data.model.asPrice
import java.util.Calendar"""
    if r.has("cart"):
        imports += "\nimport %PKG%.features.CartManager\nimport androidx.lifecycle.compose.collectAsStateWithLifecycle"
    if r.has("timer"):
        imports += ("\nimport %PKG%.features.TickTimer\nimport androidx.compose.runtime.rememberCoroutineScope"
                    "\nimport androidx.compose.runtime.DisposableEffect")
    if r.has("qr_generator"):
        imports += "\nimport %PKG%.features.QrCodeGenerator"
    if bridge:
        imports += "\nimport %PKG%.features.JsBridge"
    imports = "\n".join(sorted(set(imports.split("\n"))))
    ctx.add_kotlin("ui/components/Common.kt", "@file:OptIn(ExperimentalMaterial3Api::class)\n\n"
                   "package %PKG%.ui.components\n\n" + imports + "\n\n" + body)


COMMON_BASE = r'''// Componentes visuais reutilizados por todas as telas geradas.

/** Imagem do item ou, na falta dela, um circulo com a inicial do titulo. */
@Composable
fun ItemImage(item: ListItem, size: Int = 56) {
    if (item.imageUrl.isNotBlank()) {
        AsyncImage(
            model = item.imageUrl,
            contentDescription = item.title,
            contentScale = ContentScale.Crop,
            modifier = Modifier.size(size.dp).clip(RoundedCornerShape(12.dp))
        )
    } else {
        Box(
            contentAlignment = Alignment.Center,
            modifier = Modifier
                .size(size.dp)
                .clip(CircleShape)
                .background(MaterialTheme.colorScheme.primaryContainer)
        ) {
            Text(
                item.title.take(1).uppercase(),
                color = MaterialTheme.colorScheme.onPrimaryContainer,
                fontWeight = FontWeight.Bold
            )
        }
    }
}

/** Linha de lista com imagem, titulo, subtitulo e preco opcional. */
@Composable
fun ItemRow(item: ListItem, showImage: Boolean = true, showPrice: Boolean = false, onClick: (() -> Unit)? = null) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .then(if (onClick != null) Modifier.clickable { onClick() } else Modifier)
    ) {
        Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.padding(12.dp)) {
            if (showImage) {
                ItemImage(item)
                Spacer(Modifier.width(12.dp))
            }
            Column(modifier = Modifier.weight(1f)) {
                Text(item.title, style = MaterialTheme.typography.titleMedium, maxLines = 2, overflow = TextOverflow.Ellipsis)
                if (item.subtitle.isNotBlank()) {
                    Text(
                        item.subtitle,
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        maxLines = 2,
                        overflow = TextOverflow.Ellipsis
                    )
                }
            }
            if (showPrice && item.price != null) {
                Text(item.price.asPrice(), style = MaterialTheme.typography.titleSmall, color = MaterialTheme.colorScheme.primary)
            }
        }
    }
}

/** Cartao de grade com imagem grande. */
@Composable
fun GridCard(item: ListItem, showPrice: Boolean, modifier: Modifier = Modifier, onClick: (() -> Unit)? = null) {
    Card(modifier = modifier.then(if (onClick != null) Modifier.clickable { onClick() } else Modifier)) {
        Column {
            if (item.imageUrl.isNotBlank()) {
                AsyncImage(
                    model = item.imageUrl,
                    contentDescription = item.title,
                    contentScale = ContentScale.Crop,
                    modifier = Modifier.fillMaxWidth().height(120.dp)
                )
            } else {
                Box(
                    contentAlignment = Alignment.Center,
                    modifier = Modifier.fillMaxWidth().height(120.dp).background(MaterialTheme.colorScheme.primaryContainer)
                ) {
                    Text(item.title.take(1).uppercase(), style = MaterialTheme.typography.headlineMedium)
                }
            }
            Column(modifier = Modifier.padding(10.dp)) {
                Text(item.title, style = MaterialTheme.typography.titleSmall, maxLines = 2, overflow = TextOverflow.Ellipsis)
                if (showPrice && item.price != null) {
                    Text(item.price.asPrice(), color = MaterialTheme.colorScheme.primary, fontWeight = FontWeight.Bold)
                } else if (item.subtitle.isNotBlank()) {
                    Text(item.subtitle, style = MaterialTheme.typography.bodySmall, maxLines = 1, overflow = TextOverflow.Ellipsis)
                }
            }
        }
    }
}

/** Detalhes completos do item selecionado. */
@Composable
fun DetailCard(item: ListItem?, showImage: Boolean = true, showPrice: Boolean = false) {
    if (item == null) {
        EmptyState("Nenhum item selecionado")
        return
    }
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        if (showImage && item.imageUrl.isNotBlank()) {
            AsyncImage(
                model = item.imageUrl,
                contentDescription = item.title,
                contentScale = ContentScale.Crop,
                modifier = Modifier.fillMaxWidth().height(220.dp).clip(RoundedCornerShape(16.dp))
            )
        }
        Text(item.title, style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
        if (item.subtitle.isNotBlank()) {
            Text(item.subtitle, style = MaterialTheme.typography.titleSmall, color = MaterialTheme.colorScheme.primary)
        }
        if (showPrice && item.price != null) {
            Text(item.price.asPrice(), style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
        }
        if (item.description.isNotBlank()) {
            Text(item.description, style = MaterialTheme.typography.bodyLarge)
        }
    }
}

/** Indicador numerico com rotulo. */
@Composable
fun StatCard(label: String, value: String) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(label, style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.onPrimaryContainer)
            Text(value, style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.onPrimaryContainer)
        }
    }
}

/** Banner com degrade nas cores do tema. */
@Composable
fun BannerCard(title: String, subtitle: String, onClick: (() -> Unit)? = null) {
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(16.dp))
            .background(Brush.horizontalGradient(listOf(MaterialTheme.colorScheme.primary, MaterialTheme.colorScheme.secondary)))
            .then(if (onClick != null) Modifier.clickable { onClick() } else Modifier)
            .padding(20.dp)
    ) {
        Column {
            Text(title, style = MaterialTheme.typography.titleLarge, color = Color.White, fontWeight = FontWeight.Bold)
            Text(subtitle, style = MaterialTheme.typography.bodyMedium, color = Color.White)
        }
    }
}

/** Cabecalho de perfil com iniciais. */
@Composable
fun AvatarHeader(name: String, subtitle: String) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Box(
            contentAlignment = Alignment.Center,
            modifier = Modifier.size(64.dp).clip(CircleShape).background(MaterialTheme.colorScheme.primary)
        ) {
            val initials = name.split(" ").filter { it.isNotBlank() }.take(2).joinToString("") { it.take(1).uppercase() }
            Text(initials, color = MaterialTheme.colorScheme.onPrimary, style = MaterialTheme.typography.titleLarge)
        }
        Spacer(Modifier.width(16.dp))
        Column {
            Text(name, style = MaterialTheme.typography.titleLarge)
            Text(subtitle, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}

/** Mensagem exibida quando uma lista esta vazia. */
@Composable
fun EmptyState(text: String) {
    Box(contentAlignment = Alignment.Center, modifier = Modifier.fillMaxWidth().padding(32.dp)) {
        Text(text, color = MaterialTheme.colorScheme.onSurfaceVariant)
    }
}

/** Campo com lista suspensa de opcoes. */
@Composable
fun DropdownField(label: String, value: String, options: List<String>, onSelect: (String) -> Unit) {
    var expanded by remember { mutableStateOf(false) }
    Box(modifier = Modifier.fillMaxWidth()) {
        OutlinedTextField(
            value = value,
            onValueChange = {},
            readOnly = true,
            label = { Text(label) },
            trailingIcon = { Icon(Icons.Filled.ArrowDropDown, contentDescription = null) },
            modifier = Modifier.fillMaxWidth()
        )
        Box(modifier = Modifier.matchParentSize().clickable { expanded = true })
        DropdownMenu(expanded = expanded, onDismissRequest = { expanded = false }) {
            options.forEach { option ->
                DropdownMenuItem(text = { Text(option) }, onClick = {
                    onSelect(option)
                    expanded = false
                })
            }
        }
    }
}

/** Grupo de opcoes unicas (radio). */
@Composable
fun RadioGroupField(label: String, value: String, options: List<String>, onSelect: (String) -> Unit) {
    Column {
        Text(label, style = MaterialTheme.typography.titleSmall)
        options.forEach { option ->
            Row(
                verticalAlignment = Alignment.CenterVertically,
                modifier = Modifier.fillMaxWidth().clickable { onSelect(option) }
            ) {
                RadioButton(selected = value == option, onClick = { onSelect(option) })
                Text(option)
            }
        }
    }
}

/** Chips de selecao rapida com rolagem horizontal. */
@Composable
fun ChipsField(value: String, options: List<String>, onSelect: (String) -> Unit) {
    Row(
        horizontalArrangement = Arrangement.spacedBy(8.dp),
        modifier = Modifier.fillMaxWidth().horizontalScroll(rememberScrollState())
    ) {
        options.forEach { option ->
            FilterChip(selected = value == option, onClick = { onSelect(option) }, label = { Text(option) })
        }
    }
}

/** Barra de abas. */
@Composable
fun TabsField(value: String, options: List<String>, onSelect: (String) -> Unit) {
    val index = options.indexOf(value).coerceAtLeast(0)
    TabRow(selectedTabIndex = index) {
        options.forEachIndexed { i, option ->
            Tab(selected = i == index, onClick = { onSelect(option) }, text = { Text(option) })
        }
    }
}

/** Caixa de selecao com rotulo clicavel. */
@Composable
fun LabeledCheckbox(label: String, checked: Boolean, onChange: (Boolean) -> Unit) {
    Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.fillMaxWidth().clickable { onChange(!checked) }) {
        Checkbox(checked = checked, onCheckedChange = onChange)
        Text(label)
    }
}

/** Interruptor com rotulo. */
@Composable
fun LabeledSwitch(label: String, checked: Boolean, onChange: (Boolean) -> Unit) {
    Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.fillMaxWidth()) {
        Text(label, modifier = Modifier.weight(1f))
        Switch(checked = checked, onCheckedChange = onChange)
    }
}

/** Controle deslizante com o valor atual. */
@Composable
fun SliderField(label: String, value: Float, min: Float, max: Float, onChange: (Float) -> Unit) {
    Column {
        Text("$label: ${value.toInt()}", style = MaterialTheme.typography.titleSmall)
        Slider(value = value.coerceIn(min, max), onValueChange = onChange, valueRange = min..max)
    }
}

/** Avaliacao por estrelas. */
@Composable
fun RatingField(label: String, value: Int, max: Int, onChange: (Int) -> Unit) {
    Column {
        Text(label, style = MaterialTheme.typography.titleSmall)
        Row {
            for (star in 1..max) {
                IconButton(onClick = { onChange(star) }) {
                    Icon(
                        Icons.Filled.Star,
                        contentDescription = "$star",
                        tint = if (star <= value) Color(0xFFFFC107) else MaterialTheme.colorScheme.outlineVariant
                    )
                }
            }
        }
    }
}

/** Contador com botoes de menos e mais. */
@Composable
fun QuantityStepper(label: String, value: Int, max: Int, onChange: (Int) -> Unit) {
    Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.fillMaxWidth()) {
        Text(label, modifier = Modifier.weight(1f), style = MaterialTheme.typography.titleSmall)
        OutlinedButton(onClick = { onChange((value - 1).coerceAtLeast(0)) }) { Text("-") }
        Text(value.toString(), modifier = Modifier.padding(horizontal = 16.dp), style = MaterialTheme.typography.titleMedium)
        OutlinedButton(onClick = { onChange((value + 1).coerceAtMost(max)) }) { Text("+") }
    }
}

/** Campo que abre o seletor de data do sistema. */
@Composable
fun DatePickerField(label: String, value: String, onSelect: (String) -> Unit) {
    val context = LocalContext.current
    OutlinedButton(
        onClick = {
            val now = Calendar.getInstance()
            DatePickerDialog(context, { _, year, month, day ->
                onSelect("%02d/%02d/%04d".format(day, month + 1, year))
            }, now.get(Calendar.YEAR), now.get(Calendar.MONTH), now.get(Calendar.DAY_OF_MONTH)).show()
        },
        modifier = Modifier.fillMaxWidth()
    ) {
        Icon(Icons.Filled.DateRange, contentDescription = null)
        Spacer(Modifier.width(8.dp))
        Text(if (value.isBlank()) label else "$label: $value")
    }
}

/** Foto escolhida/tirada ou um espaco reservado. */
@Composable
fun PhotoBox(uri: String, height: Int) {
    if (uri.isNotBlank()) {
        AsyncImage(
            model = uri,
            contentDescription = "Foto",
            contentScale = ContentScale.Crop,
            modifier = Modifier.fillMaxWidth().height(height.dp).clip(RoundedCornerShape(12.dp))
        )
    } else {
        Box(
            contentAlignment = Alignment.Center,
            modifier = Modifier
                .fillMaxWidth()
                .height(height.dp)
                .clip(RoundedCornerShape(12.dp))
                .background(MaterialTheme.colorScheme.surfaceVariant)
        ) {
            Text("Nenhuma imagem", color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}

/** Pagina web incorporada. */
@SuppressLint("SetJavaScriptEnabled")
@Composable
fun WebViewBox(url: String, height: Int) {
    AndroidView(
        modifier = Modifier.fillMaxWidth().height(height.dp),
        factory = { context ->
            WebView(context).apply {
                settings.javaScriptEnabled = true
                webViewClient = WebViewClient()
                BRIDGE_SETUP
                loadUrl(url)
            }
        }
    )
}'''

COMMON_EXTRA = r'''/** Cartao grande de carrossel com imagem e titulo sobreposto. */
@Composable
fun CarouselCard(item: ListItem, height: Int, onClick: (() -> Unit)? = null) {
    Card(
        modifier = Modifier
            .width(300.dp)
            .height(height.dp)
            .then(if (onClick != null) Modifier.clickable { onClick() } else Modifier)
    ) {
        Box(modifier = Modifier.fillMaxSize()) {
            if (item.imageUrl.isNotBlank()) {
                AsyncImage(
                    model = item.imageUrl,
                    contentDescription = item.title,
                    contentScale = ContentScale.Crop,
                    modifier = Modifier.fillMaxSize()
                )
            } else {
                Box(modifier = Modifier.fillMaxSize().background(MaterialTheme.colorScheme.primary))
            }
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .background(Brush.verticalGradient(listOf(Color.Transparent, Color(0xCC000000))))
            )
            Column(modifier = Modifier.align(Alignment.BottomStart).padding(14.dp)) {
                Text(item.title, color = Color.White, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold,
                    maxLines = 1, overflow = TextOverflow.Ellipsis)
                if (item.subtitle.isNotBlank()) {
                    Text(item.subtitle, color = Color.White, style = MaterialTheme.typography.bodySmall, maxLines = 1)
                }
            }
        }
    }
}

/** Cartao pequeno para listas horizontais. */
@Composable
fun HCard(item: ListItem, showPrice: Boolean, onClick: (() -> Unit)? = null) {
    GridCard(item, showPrice, Modifier.width(150.dp), onClick)
}

/** Secao que abre e fecha ao tocar. */
@Composable
fun ExpandableCard(title: String, body: String) {
    var open by remember { mutableStateOf(false) }
    Card(modifier = Modifier.fillMaxWidth().clickable { open = !open }) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(title, style = MaterialTheme.typography.titleMedium, modifier = Modifier.weight(1f))
                Text(if (open) "-" else "+", style = MaterialTheme.typography.titleLarge, color = MaterialTheme.colorScheme.primary)
            }
            AnimatedVisibility(visible = open) {
                Text(body, style = MaterialTheme.typography.bodyMedium, modifier = Modifier.padding(top = 8.dp))
            }
        }
    }
}

/** Tabela de pares rotulo e valor. */
@Composable
fun KeyValueCard(title: String, rows: List<Pair<String, String>>) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            if (title.isNotBlank()) Text(title, style = MaterialTheme.typography.titleMedium)
            rows.forEach { (label, value) ->
                Row {
                    Text(label, modifier = Modifier.weight(1f), color = MaterialTheme.colorScheme.onSurfaceVariant)
                    Text(value, fontWeight = FontWeight.Medium)
                }
            }
        }
    }
}

/** Indicador de etapas numeradas; as etapas ate [current] ficam destacadas. */
@Composable
fun StepsIndicator(steps: List<String>, current: Int) {
    Row(modifier = Modifier.fillMaxWidth()) {
        steps.forEachIndexed { index, label ->
            val done = index < current
            Column(horizontalAlignment = Alignment.CenterHorizontally, modifier = Modifier.weight(1f)) {
                Box(
                    contentAlignment = Alignment.Center,
                    modifier = Modifier
                        .size(32.dp)
                        .clip(CircleShape)
                        .background(if (done) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.surfaceVariant)
                ) {
                    Text(
                        (index + 1).toString(),
                        color = if (done) MaterialTheme.colorScheme.onPrimary else MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
                Text(label, style = MaterialTheme.typography.labelSmall, maxLines = 2, modifier = Modifier.padding(top = 4.dp))
            }
        }
    }
}

/** Caixa de aviso colorida: info, success, warning ou error. */
@Composable
fun AlertBox(text: String, kind: String) {
    val (background, foreground) = when (kind) {
        "success" -> Color(0xFFE8F5E9) to Color(0xFF1B5E20)
        "warning" -> Color(0xFFFFF8E1) to Color(0xFF7A5900)
        "error" -> MaterialTheme.colorScheme.errorContainer to MaterialTheme.colorScheme.onErrorContainer
        else -> MaterialTheme.colorScheme.primaryContainer to MaterialTheme.colorScheme.onPrimaryContainer
    }
    Surface(color = background, shape = RoundedCornerShape(12.dp), modifier = Modifier.fillMaxWidth()) {
        Text(text, color = foreground, modifier = Modifier.padding(14.dp))
    }
}

/** Area para assinar ou desenhar com o dedo. */
@Composable
fun SignaturePad(label: String, height: Int) {
    val strokes = remember { mutableStateListOf<List<Offset>>() }
    var current by remember { mutableStateOf<List<Offset>>(emptyList()) }
    val ink = MaterialTheme.colorScheme.onSurface
    Column {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text(label, style = MaterialTheme.typography.titleSmall, modifier = Modifier.weight(1f))
            TextButton(onClick = {
                strokes.clear()
                current = emptyList()
            }) { Text("Limpar") }
        }
        Canvas(
            modifier = Modifier
                .fillMaxWidth()
                .height(height.dp)
                .clip(RoundedCornerShape(12.dp))
                .background(MaterialTheme.colorScheme.surfaceVariant)
                .pointerInput(Unit) {
                    detectDragGestures(
                        onDragStart = { current = listOf(it) },
                        onDragEnd = {
                            strokes.add(current)
                            current = emptyList()
                        },
                        onDrag = { change, _ -> current = current + change.position }
                    )
                }
        ) {
            (strokes + listOf(current)).forEach { points ->
                for (i in 1 until points.size) {
                    drawLine(ink, points[i - 1], points[i], strokeWidth = 6f, cap = StrokeCap.Round)
                }
            }
        }
    }
}

/** Citacao ou depoimento em destaque. */
@Composable
fun QuoteCard(text: String, author: String) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text("\u201C$text\u201D", style = MaterialTheme.typography.bodyLarge, fontStyle = FontStyle.Italic)
            if (author.isNotBlank()) {
                Text("- $author", style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.primary,
                    modifier = Modifier.padding(top = 8.dp))
            }
        }
    }
}

/** Etiquetas informativas. */
@Composable
fun TagsRow(tags: List<String>) {
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.horizontalScroll(rememberScrollState())) {
        tags.forEach { tag ->
            Surface(color = MaterialTheme.colorScheme.secondaryContainer, shape = RoundedCornerShape(50)) {
                Text(tag, style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.onSecondaryContainer,
                    modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp))
            }
        }
    }
}

/** Preco grande com valor antigo riscado. */
@Composable
fun PriceTag(label: String, value: String, oldValue: String) {
    Column {
        Text(label, style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.onSurfaceVariant)
        Row(verticalAlignment = Alignment.Bottom) {
            Text(value, style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.primary)
            if (oldValue.isNotBlank()) {
                Text(oldValue, textDecoration = TextDecoration.LineThrough, color = MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.padding(start = 8.dp, bottom = 4.dp))
            }
        }
    }
}

/** Botoes de contato: WhatsApp, Instagram e site (os vazios sao ocultados). */
@Composable
fun SocialLinks(whatsapp: String, instagram: String, website: String) {
    val context = LocalContext.current
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxWidth()) {
        if (whatsapp.isNotBlank()) {
            OutlinedButton(onClick = { IntentHelper.whatsapp(context, whatsapp) }, modifier = Modifier.weight(1f)) { Text("WhatsApp") }
        }
        if (instagram.isNotBlank()) {
            OutlinedButton(onClick = { IntentHelper.openUrl(context, "https://instagram.com/" + instagram.removePrefix("@")) },
                modifier = Modifier.weight(1f)) { Text("Instagram") }
        }
        if (website.isNotBlank()) {
            OutlinedButton(onClick = { IntentHelper.openUrl(context, website) }, modifier = Modifier.weight(1f)) { Text("Site") }
        }
    }
}'''

COMMON_CART = r'''/** Total do carrinho com botao de finalizar. */
@Composable
fun CartSummary(buttonText: String, onCheckout: () -> Unit) {
    val lines by CartManager.lines.collectAsStateWithLifecycle()
    val total = lines.sumOf { it.total }
    val count = lines.sumOf { it.quantity }
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Row {
                Text("$count itens", modifier = Modifier.weight(1f))
                Text(total.asPrice(), fontWeight = FontWeight.Bold, style = MaterialTheme.typography.titleMedium)
            }
            Button(onClick = onCheckout, enabled = count > 0, modifier = Modifier.fillMaxWidth()) { Text(buttonText) }
        }
    }
}'''

COMMON_TIMER = r'''/** Cronometro ou contagem regressiva com controles. */
@Composable
fun TimerBlock(countdownSeconds: Long = 0L) {
    val scope = rememberCoroutineScope()
    val timer = remember { TickTimer(scope, countdownSeconds) }
    val seconds by timer.seconds.collectAsStateWithLifecycle()
    val running by timer.running.collectAsStateWithLifecycle()
    DisposableEffect(timer) { onDispose { timer.pause() } }
    Column(horizontalAlignment = Alignment.CenterHorizontally, modifier = Modifier.fillMaxWidth()) {
        Text(TickTimer.format(seconds), style = MaterialTheme.typography.displayMedium, fontWeight = FontWeight.Bold)
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            Button(onClick = { timer.toggle() }) { Text(if (running) "Pausar" else "Iniciar") }
            OutlinedButton(onClick = { timer.reset() }) { Text("Zerar") }
        }
    }
}'''

COMMON_QR = r'''/** Imagem de QR Code gerada localmente. */
@Composable
fun QrImage(text: String, size: Int) {
    val bitmap = remember(text) { QrCodeGenerator.generate(text, 512) }
    Box(contentAlignment = Alignment.Center, modifier = Modifier.fillMaxWidth()) {
        Image(bitmap = bitmap.asImageBitmap(), contentDescription = "QR Code", modifier = Modifier.size(size.dp))
    }
}'''


# ----------------------------------------------------------------- telas

def _num(value, default, cast=int):
    try:
        return cast(value)
    except (TypeError, ValueError):
        return default


def _float_lit(value, default=0.0):
    return f"{_num(value, default, float)}f"


def _component(ctx, spec, comp, index):
    """Codigo Compose de um bloco. Retorna (codigo dentro de item{}, codigo de items) ou None."""
    t = comp.type
    pr = comp.props
    sid = f"{to_snake(spec.screen.name)}_{index}"

    def s(hint, text):
        return f"stringResource(R.string.{ctx.string(f'{sid}_{hint}', text)})"

    def act(prop="action", item=None):
        return action_code(ctx, spec, pr.get(prop, "none"), item)

    field = spec.input_by_comp.get(comp.id)
    if t == "title":
        style = {"large": "headlineMedium", "medium": "titleLarge", "small": "titleMedium"}.get(pr.get("size"), "headlineMedium")
        align = ", textAlign = TextAlign.Center, modifier = Modifier.fillMaxWidth()" if pr.get("align") == "center" else ""
        return f"Text({s('title', pr.get('text', ''))}, style = MaterialTheme.typography.{style}, fontWeight = FontWeight.Bold{align})"
    if t == "text":
        style = {"caption": "bodySmall", "emphasis": "titleSmall"}.get(pr.get("style"), "bodyLarge")
        color = ", color = MaterialTheme.colorScheme.onSurfaceVariant" if pr.get("style") == "caption" else ""
        align = ", textAlign = TextAlign.Center, modifier = Modifier.fillMaxWidth()" if pr.get("align") == "center" else ""
        return f"Text({s('text', pr.get('text', ''))}, style = MaterialTheme.typography.{style}{color}{align})"
    if t == "button":
        widget = {"outlined": "OutlinedButton", "tonal": "FilledTonalButton", "text": "TextButton"}.get(pr.get("style"), "Button")
        return f"{widget}(onClick = {{ {act()} }}, modifier = Modifier.fillMaxWidth()) {{ Text({s('button', pr.get('text', ''))}) }}"
    if t == "image":
        height = _num(pr.get("height"), 180)
        if pr.get("source") == "photo":
            return f"PhotoBox(state.photoUri, {height})"
        return (f"AsyncImage(model = {kq(pr.get('url', ''))}, contentDescription = {kq(pr.get('description', 'Imagem'))}, "
                f"contentScale = ContentScale.Crop, modifier = Modifier.fillMaxWidth().height({height}.dp)"
                ".clip(RoundedCornerShape(12.dp)))")
    if t == "card":
        code = act()
        click = f".clickable {{ {code} }}" if code else ""
        return (f"Card(modifier = Modifier.fillMaxWidth(){click}) {{\n"
                f"    Column(modifier = Modifier.padding(16.dp)) {{\n"
                f"        Text({s('card_title', pr.get('title', ''))}, style = MaterialTheme.typography.titleMedium)\n"
                f"        Text({s('card_body', pr.get('body', ''))}, style = MaterialTheme.typography.bodyMedium)\n"
                f"    }}\n}}")
    if t == "banner":
        code = act()
        click = f", onClick = {{ {code} }}" if code else ""
        return f"BannerCard({s('banner_title', pr.get('title', ''))}, {s('banner_subtitle', pr.get('subtitle', ''))}{click})"
    if t == "text_field" and field:
        kind = pr.get("input", "text")
        extras = []
        keyboard = {"email": "Email", "number": "Decimal", "phone": "Phone", "password": "Password"}.get(kind)
        if keyboard:
            extras.append(f"keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.{keyboard})")
        if kind == "password":
            extras.append("visualTransformation = PasswordVisualTransformation()")
        if kind == "multiline":
            extras.append("minLines = 3")
        else:
            extras.append("singleLine = true")
        extras.append(f'isError = "{field.key}" in state.errors')
        extras.append(f'supportingText = if ("{field.key}" in state.errors) {{ {{ Text("Valor invalido") }} }} else null')
        extra = ",\n    ".join(extras)
        return (f"OutlinedTextField(\n    value = state.{field.key},\n    onValueChange = viewModel::{field.setter},\n"
                f"    label = {{ Text({s('label', pr.get('label', ''))}) }},\n    {extra},\n"
                f"    modifier = Modifier.fillMaxWidth()\n)")
    if t == "checkbox" and field:
        return f"LabeledCheckbox({s('label', pr.get('label', ''))}, state.{field.key}, viewModel::{field.setter})"
    if t == "switch" and field:
        return f"LabeledSwitch({s('label', pr.get('label', ''))}, state.{field.key}, viewModel::{field.setter})"
    if t == "slider" and field:
        return (f"SliderField({s('label', pr.get('label', ''))}, state.{field.key}, {_float_lit(pr.get('min'), 0)}, "
                f"{_float_lit(pr.get('max'), 100)}, viewModel::{field.setter})")
    opts = "listOf(" + ", ".join(kq(o) for o in options_of(comp)) + ")"
    if t == "radio_group" and field:
        return f"RadioGroupField({s('label', pr.get('label', ''))}, state.{field.key}, {opts}, viewModel::{field.setter})"
    if t == "dropdown" and field:
        return f"DropdownField({s('label', pr.get('label', ''))}, state.{field.key}, {opts}, viewModel::{field.setter})"
    if t == "chips" and field:
        return f"ChipsField(state.{field.key}, {opts}, viewModel::{field.setter})"
    if t == "tabs" and field:
        return f"TabsField(state.{field.key}, {opts}, viewModel::{field.setter})"
    if t == "date_picker" and field:
        return f"DatePickerField({s('label', pr.get('label', ''))}, state.{field.key}, viewModel::{field.setter})"
    if t == "rating" and field:
        return f"RatingField({s('label', pr.get('label', ''))}, state.{field.key}, {_num(pr.get('max'), 5)}, viewModel::{field.setter})"
    if t == "stepper" and field:
        return f"QuantityStepper({s('label', pr.get('label', ''))}, state.{field.key}, {_num(pr.get('max'), 99)}, viewModel::{field.setter})"
    if t == "calendar" and field:
        return f"MonthCalendar(onDateSelected = viewModel::{field.setter})"
    if t == "search_bar":
        return (f"OutlinedTextField(\n    value = state.query,\n    onValueChange = viewModel::onQueryChange,\n"
                f"    placeholder = {{ Text({s('hint', pr.get('hint', ''))}) }},\n"
                f"    leadingIcon = {{ Icon(Icons.Filled.Search, contentDescription = null) }},\n"
                f"    singleLine = true,\n    modifier = Modifier.fillMaxWidth()\n)")
    if t == "item_detail":
        return f"DetailCard(state.selectedItem, showImage = {str(bool(pr.get('show_image', True))).lower()}, showPrice = {str(bool(pr.get('show_price'))).lower()})"
    if t == "stat_card":
        return f"StatCard({s('stat_label', pr.get('label', ''))}, {s('stat_value', pr.get('value', ''))})"
    if t == "chart":
        values = []
        for v in str(pr.get("values", "")).split(","):
            try:
                values.append(f"{float(v.strip())}f")
            except ValueError:
                pass
        chart = {"line": "LineChart", "pie": "PieChart"}.get(pr.get("style"), "BarChart")
        return f"{chart}(listOf({', '.join(values) or '1f'}))"
    if t == "cart_summary":
        return f"CartSummary({s('button', pr.get('button', 'Finalizar'))}, onCheckout = {{ {act()} }})"
    if t == "avatar":
        return f"AvatarHeader({kq(pr.get('name', ''))}, {kq(pr.get('subtitle', ''))})"
    if t == "divider":
        return "HorizontalDivider()"
    if t == "spacer":
        return f"Spacer(Modifier.height({_num(pr.get('height'), 16)}.dp))"
    if t == "progress":
        bound = bool(pr.get("bind_loading", True))
        if pr.get("style") == "circular":
            widget = "Box(contentAlignment = Alignment.Center, modifier = Modifier.fillMaxWidth()) { CircularProgressIndicator() }"
        else:
            widget = ("LinearProgressIndicator(modifier = Modifier.fillMaxWidth())" if bound else
                      "LinearProgressIndicator(progress = { 0.5f }, modifier = Modifier.fillMaxWidth())")
        return f"if (state.isLoading) {{\n    {widget}\n}}" if bound else widget
    if t == "web_view":
        return f"WebViewBox({kq(pr.get('url', ''))}, {_num(pr.get('height'), 420)})"
    if t == "map_view":
        return (f"AppMap({_num(pr.get('lat'), -23.55, float)}, {_num(pr.get('lng'), -46.63, float)}, "
                f"{kq(pr.get('title', ''))}, Modifier.fillMaxWidth().height({_num(pr.get('height'), 260)}.dp))")
    if t == "video_player":
        return f"VideoPlayer({kq(pr.get('url', ''))}, Modifier.fillMaxWidth().height({_num(pr.get('height'), 220)}.dp))"
    if t == "qr_code":
        return f"QrImage({kq(pr.get('text', ''))}, {_num(pr.get('size'), 200)})"
    if t == "timer":
        seconds = _num(pr.get("seconds"), 1500) if pr.get("mode") == "countdown" else 0
        return f"TimerBlock({seconds}L)"
    if t == "camera_preview":
        return f"CameraPreview(Modifier.fillMaxWidth().height({_num(pr.get('height'), 320)}.dp))"
    if t == "expandable":
        return f"ExpandableCard({s('exp_title', pr.get('title', ''))}, {s('exp_body', pr.get('body', ''))})"
    if t == "key_value":
        pairs = []
        for line in str(pr.get("rows", "")).splitlines():
            if line.strip():
                label, _, value = line.partition(":")
                pairs.append(f"{kq(label.strip())} to {kq(value.strip())}")
        return f"KeyValueCard({s('kv_title', pr.get('title', ''))}, listOf({', '.join(pairs)}))"
    if t == "steps":
        steps = ", ".join(kq(o) for o in options_of(comp))
        return f"StepsIndicator(listOf({steps}), {_num(pr.get('current'), 1)})"
    if t == "alert":
        return f"AlertBox({s('alert', pr.get('text', ''))}, {kq(pr.get('kind', 'info'))})"
    if t == "button_row":
        a1 = action_code(ctx, spec, pr.get("action1", "none"))
        a2 = action_code(ctx, spec, pr.get("action2", "none"))
        return (f"Row(horizontalArrangement = Arrangement.spacedBy(12.dp), modifier = Modifier.fillMaxWidth()) {{\n"
                f"    OutlinedButton(onClick = {{ {a1} }}, modifier = Modifier.weight(1f)) {{ Text({s('button1', pr.get('text1', ''))}) }}\n"
                f"    Button(onClick = {{ {a2} }}, modifier = Modifier.weight(1f)) {{ Text({s('button2', pr.get('text2', ''))}) }}\n}}")
    if t == "signature":
        return f"SignaturePad({s('label', pr.get('label', ''))}, {_num(pr.get('height'), 180)})"
    if t == "quote":
        return f"QuoteCard({s('quote', pr.get('text', ''))}, {kq(pr.get('author', ''))})"
    if t == "tags":
        return "TagsRow(listOf(" + ", ".join(kq(o) for o in options_of(comp)) + "))"
    if t == "price_tag":
        return (f"PriceTag({s('price_label', pr.get('label', ''))}, {kq(pr.get('value', ''))}, "
                f"{kq(pr.get('old_value', ''))})")
    if t == "social_links":
        return (f"SocialLinks({kq(pr.get('whatsapp', ''))}, {kq(pr.get('instagram', ''))}, "
                f"{kq(pr.get('website', ''))})")
    if t == "lottie":
        return f"LottieBox({kq(pr.get('url', ''))}, Modifier.fillMaxWidth().height({_num(pr.get('height'), 200)}.dp))"
    return None


def _list_items(ctx, spec, lb):
    comp = lb.comp
    pr = comp.props
    code = action_code(ctx, spec, pr.get("item_action", "none"), "item")
    click = f"onClick = {{ {code} }}" if code else "onClick = null"
    empty = kq(pr.get("empty_text", "Nenhum item encontrado"))
    price = str(bool(pr.get("show_price"))).lower()
    skeleton = "skeleton" in ctx.resolved.flags
    if comp.type in ("carousel", "h_list"):
        if comp.type == "carousel":
            card = f"CarouselCard(item, {_num(pr.get('height'), 180)}, {click})"
        else:
            card = f"HCard(item, {price}, {click})"
        return "\n".join([
            "item {",
            *([f"    if (state.{lb.visible}.isEmpty() && state.isLoading) {{",
               "        SkeletonList(rows = 1)",
               f"    }} else if (state.{lb.visible}.isEmpty()) {{"] if skeleton else
              [f"    if (state.{lb.visible}.isEmpty() && !state.isLoading) {{"]),
            f"        EmptyState({empty})",
            "    } else {",
            "        LazyRow(horizontalArrangement = Arrangement.spacedBy(12.dp)) {",
            f"            items(state.{lb.visible}) {{ item -> {card} }}",
            "        }",
            "    }",
            "}"])
    lines = [f"if (state.{lb.visible}.isEmpty() && !state.isLoading) {{",
             f"    item {{ EmptyState({empty}) }}", "}"]
    if skeleton:
        lines += [f"if (state.{lb.visible}.isEmpty() && state.isLoading) {{",
                  "    item { SkeletonList() }", "}"]
    if comp.type == "grid":
        cols = max(1, min(4, _num(pr.get("columns"), 2)))
        lines.append(f"items(state.{lb.visible}.chunked({cols})) {{ row ->")
        lines.append("    Row(horizontalArrangement = Arrangement.spacedBy(12.dp), modifier = Modifier.fillMaxWidth()) {")
        lines.append(f"        row.forEach {{ item -> GridCard(item, {price}, Modifier.weight(1f), {click}) }}")
        lines.append(f"        repeat({cols} - row.size) {{ Spacer(Modifier.weight(1f)) }}")
        lines.append("    }")
        lines.append("}")
    else:
        image = str(bool(pr.get("show_image", True))).lower()
        lines.append(f"items(state.{lb.visible}) {{ item ->")
        lines.append(f"    ItemRow(item, showImage = {image}, showPrice = {price}, {click})")
        lines.append("}")
    return "\n".join(lines)


def _indent(code, n):
    pad = " " * n
    return "\n".join(pad + line if line.strip() else line for line in code.split("\n"))


def _screen(ctx, spec):
    r = ctx.resolved
    p = ctx.project
    screen = spec.screen
    title_res = ctx.string(f"screen_{spec.route}", screen.title or screen.name)
    body_items = []
    list_by_comp = {lb.comp.id: lb for lb in spec.lists}
    for index, comp in enumerate(spec.components):
        if comp.type == "fab":
            continue
        if comp.id in list_by_comp:
            body_items.append(_list_items(ctx, spec, list_by_comp[comp.id]))
            continue
        code = _component(ctx, spec, comp, index)
        if code:
            body_items.append("item {\n" + _indent(code, 4) + "\n}")
    lazy_body = _indent("\n".join(body_items), 12) if body_items else "            item { EmptyState(\"Tela vazia: adicione blocos no DroidBlocks\") }"

    fab = ""
    if spec.fab:
        icon = ICONS.get(spec.fab.props.get("icon", "add"), ICONS["add"])[0]
        fab_code = action_code(ctx, spec, spec.fab.props.get("action", "none"))
        fab = (f",\n        floatingActionButton = {{\n            FloatingActionButton(onClick = {{ {fab_code} }}) "
               f"{{ Icon({icon}, contentDescription = null) }}\n        }}")

    nav_icon = ""
    if not spec.is_top_level:
        nav_icon = ("navigationIcon = {\n                    IconButton(onClick = onBack) { "
                    "Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = \"Voltar\") }\n                },\n                ")
    elif p.navigation == "drawer":
        nav_icon = ("navigationIcon = {\n                    LocalDrawerOpener.current?.let { open ->\n"
                    "                        IconButton(onClick = open) { Icon(Icons.Filled.Menu, contentDescription = \"Menu\") }\n"
                    "                    }\n                },\n                ")

    preamble = ["val state by viewModel.uiState.collectAsStateWithLifecycle()", "val context = LocalContext.current"]
    full = lazy_body + fab
    if "scope." in full:
        preamble.append("val scope = rememberCoroutineScope()")
    if "activity" in full:
        preamble.append("val activity = context.findActivity()")
    if "takePhoto()" in full:
        preamble.append("val takePhoto = rememberCameraCapture { uri -> viewModel.onPhotoSelected(uri?.toString()) }")
    if "pickImage()" in full:
        preamble.append("val pickImage = rememberImagePicker { uri -> viewModel.onPhotoSelected(uri?.toString()) }")
    if "pickFile()" in full:
        preamble.append("val pickFile = rememberDocumentPicker { uri -> viewModel.onFilePicked(uri?.toString()) }")
    if "listen()" in full:
        preamble.append("val listen = rememberSpeechToText { text -> viewModel.onSpeechResult(text) }")
    preamble += [
        "",
        "// Recarrega os dados sempre que a tela aparece.",
        "LaunchedEffect(Unit) { viewModel.refresh() }",
        "// Exibe as mensagens do ViewModel.",
        "LaunchedEffect(viewModel) {",
        "    viewModel.messages.collect { Toast.makeText(context, it, Toast.LENGTH_SHORT).show() }",
        "}",
    ]
    content = f'''        LazyColumn(
            modifier = Modifier.fillMaxSize(){"" if r.has("pull_to_refresh") and spec.lists else ".padding(padding)"},
            contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {{
{lazy_body}
        }}'''
    if r.has("pull_to_refresh") and spec.lists:
        content = (f"        PullToRefreshBox(\n            isRefreshing = state.isLoading,\n"
                   f"            onRefresh = viewModel::refresh,\n            modifier = Modifier.fillMaxSize().padding(padding)\n"
                   f"        ) {{\n{_indent(content, 4)}\n        }}")

    body = f'''/**
 * Tela "{screen.title or screen.name}" gerada pelo DroidBlocks.
 * Cada bloco configurado no construtor vira um item da LazyColumn abaixo.
 */
@Composable
fun {spec.cls}Screen(
    onNavigate: (route: String, itemId: String?) -> Unit,
    onNavigateRoot: (route: String) -> Unit,
    onBack: () -> Unit,
    viewModel: {spec.cls}ViewModel = viewModel(factory = {spec.cls}ViewModel.Factory)
) {{
{_indent(chr(10).join(preamble), 4)}

    Scaffold(
        topBar = {{
            TopAppBar(
                title = {{ Text(stringResource(R.string.{title_res})) }},
                {nav_icon}colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primary,
                    titleContentColor = MaterialTheme.colorScheme.onPrimary,
                    navigationIconContentColor = MaterialTheme.colorScheme.onPrimary
                )
            )
        }}{fab}
    ) {{ padding ->
{content}
    }}
}}
'''
    # Simbolos que nao estao no mapa geral de imports
    extra = ["androidx.compose.material3.ExperimentalMaterial3Api", "%PKG%.ui.components.*"]
    used_icons = {name for name in ("ArrowBack", "Menu", "Search") if f"Filled.{name}" in body}
    for icon_name, _ in ICONS.values():
        if icon_name in body:
            used_icons.add(icon_name.split(".")[-1])
    for name in used_icons:
        auto = name in ("ArrowBack", "List", "Send") and f"AutoMirrored.Filled.{name}" in body
        extra.append(f"androidx.compose.material.icons.{'automirrored.' if auto else ''}filled.{name}")
    if "FragmentActivity" in body:
        extra.append("androidx.fragment.app.FragmentActivity")
    return finalize(ctx, body, spec.package, extra, "@file:OptIn(ExperimentalMaterial3Api::class)\n")


# ----------------------------------------------------------------- navegacao

def _navigation(ctx, specs):
    p = ctx.project
    start = p.get_start_screen()
    consts = "\n".join(f'    const val {ctx.route_const(s.screen.name)} = "{s.route}"' for s in specs)
    composables = []
    for s in specs:
        composables.append(f'''        composable(
            route = pattern(Routes.{ctx.route_const(s.screen.name)}),
            arguments = listOf(navArgument("itemId") {{
                type = NavType.StringType
                nullable = true
                defaultValue = null
            }})
        ) {{
            {s.cls}Screen(onNavigate = navigate, onNavigateRoot = navigateRoot, onBack = back)
        }}''')
    nav = [s for s in specs if s.screen.in_nav]
    if p.navigation == "bottom":
        nav = nav[:5]
    nav_items = []
    for s in nav:
        icon = ICONS.get(s.screen.icon, ICONS["info"])[0]
        label = ctx.string(f"nav_{s.screen.name}", s.screen.title or s.screen.name)
        nav_items.append(f"    NavItem(Routes.{ctx.route_const(s.screen.name)}, R.string.{label}, {icon})")
    imports_screens = [f"{s.package}.{s.cls}Screen" for s in specs]
    icons = set()
    for s in nav:
        icon = ICONS.get(s.screen.icon, ICONS["info"])[0]
        auto = icon.startswith("Icons.AutoMirrored")
        icons.add(f"androidx.compose.material.icons.{'automirrored.' if auto else ''}filled.{icon.split('.')[-1]}")

    graph = f'''        NavHost(
            navController = navController,
            startDestination = pattern(Routes.{ctx.route_const(start.name)}),
            modifier = modifier
        ) {{
{_indent(chr(10).join(composables), 4)}
        }}'''
    use_nav = p.navigation in ("bottom", "drawer") and nav
    if p.navigation == "bottom" and use_nav:
        shell = f'''    Scaffold(
        bottomBar = {{
            if (currentRoute in topLevelRoutes) {{
                NavigationBar {{
                    navItems.forEach {{ item ->
                        NavigationBarItem(
                            selected = currentRoute == item.route,
                            onClick = {{ navigateTopLevel(item.route) }},
                            icon = {{ Icon(item.icon, contentDescription = null) }},
                            label = {{ Text(stringResource(item.label)) }}
                        )
                    }}
                }}
            }}
        }}
    ) {{ innerPadding ->
        val modifier = Modifier.padding(innerPadding).consumeWindowInsets(innerPadding)
{graph}
    }}'''
    elif p.navigation == "drawer" and use_nav:
        shell = f'''    val drawerState = rememberDrawerState(DrawerValue.Closed)
    val scope = rememberCoroutineScope()
    ModalNavigationDrawer(
        drawerState = drawerState,
        drawerContent = {{
            ModalDrawerSheet {{
                Text(
                    stringResource(R.string.app_name),
                    style = MaterialTheme.typography.titleLarge,
                    modifier = Modifier.padding(24.dp)
                )
                navItems.forEach {{ item ->
                    NavigationDrawerItem(
                        label = {{ Text(stringResource(item.label)) }},
                        icon = {{ Icon(item.icon, contentDescription = null) }},
                        selected = currentRoute == item.route,
                        onClick = {{
                            scope.launch {{ drawerState.close() }}
                            navigateTopLevel(item.route)
                        }},
                        modifier = Modifier.padding(horizontal = 12.dp)
                    )
                }}
            }}
        }}
    ) {{
        CompositionLocalProvider(LocalDrawerOpener provides {{ scope.launch {{ drawerState.open() }} }}) {{
            val modifier = Modifier
{_indent(graph, 4)}
        }}
    }}'''
    else:
        shell = f'''    val modifier = Modifier
{graph}'''

    body = f'''/** Rotas de todas as telas do app. */
object Routes {{
{consts}
}}

/** Padrao de rota com o parametro opcional itemId (usado para abrir detalhes). */
fun pattern(route: String) = "$route?itemId={{itemId}}"

/** Item do menu principal. */
data class NavItem(val route: String, val label: Int, val icon: ImageVector)

/** Abre o menu lateral a partir de qualquer tela (nulo quando nao ha menu lateral). */
val LocalDrawerOpener = staticCompositionLocalOf<(() -> Unit)?> {{ null }}

private val navItems = listOf(
{("," + chr(10)).join(nav_items)}
)

/**
 * Grafo de navegacao do app.
 * [initialRoute] permite abrir uma tela especifica (por exemplo, a partir de um deep link).
 */
@Composable
fun AppNavigation(initialRoute: String? = null) {{
    val navController = rememberNavController()
    val backStackEntry by navController.currentBackStackEntryAsState()
    val currentRoute = backStackEntry?.destination?.route?.substringBefore("?")
    val topLevelRoutes = navItems.map {{ it.route }}

    val navigate: (String, String?) -> Unit = {{ route, itemId ->
        val target = if (itemId != null) "$route?itemId=${{Uri.encode(itemId)}}" else route
        navController.navigate(target) {{ launchSingleTop = true }}
    }}
    val navigateRoot: (String) -> Unit = {{ route ->
        navController.navigate(route) {{
            popUpTo(navController.graph.id) {{ inclusive = true }}
            launchSingleTop = true
        }}
    }}
    val navigateTopLevel: (String) -> Unit = {{ route ->
        navController.navigate(route) {{
            popUpTo(navController.graph.findStartDestination().id) {{ saveState = true }}
            launchSingleTop = true
            restoreState = true
        }}
    }}
    val back: () -> Unit = {{ navController.popBackStack() }}

    LaunchedEffect(initialRoute) {{
        if (initialRoute != null) navController.navigate(initialRoute)
    }}

{shell}
}}
'''
    if not use_nav:
        # Sem menu principal: remove as variaveis usadas apenas pela barra/menu.
        body = re.sub(r"    val backStackEntry by .*\n", "", body)
        body = re.sub(r"    val currentRoute = .*\n", "", body)
        body = re.sub(r"    val topLevelRoutes = .*\n", "", body)
        body = re.sub(r"    val navigateTopLevel: .*?\n    }\n", "", body, flags=re.S)
    if not nav_items:
        body = body.replace("private val navItems = listOf(\n\n)", "private val navItems = emptyList<NavItem>()")
    extra = imports_screens + sorted(icons) + ["androidx.compose.ui.graphics.vector.ImageVector"]
    ctx.add_kotlin("navigation/AppNavigation.kt", finalize(ctx, body, f"{ctx.pkg}.navigation", extra))


def _main_activity(ctx):
    r = ctx.resolved
    base = "FragmentActivity" if "fragment_activity" in r.flags else "ComponentActivity"
    splash = "        installSplashScreen()\n" if "splash" in r.flags else ""
    init = "\n".join("        " + line for line in
                     [line for f in r.features for line in f.activity_init])
    deep = "DeepLinkParser.routeFrom(intent?.data)" if "deep_links" in r.flags else "null"
    deep_decl = "val initialRoute: String? = " + deep
    theme_toggle = "theme_toggle" in r.flags
    if theme_toggle:
        content = '''            val mode by ThemePreferences.modeFlow(this).collectAsState(initial = "system")
            val dark = when (mode) {
                "dark" -> true
                "light" -> false
                else -> isSystemInDarkTheme()
            }
            AppTheme(darkTheme = dark) {
                AppNavigation(initialRoute = initialRoute)
            }'''
    else:
        content = '''            AppTheme {
                AppNavigation(initialRoute = initialRoute)
            }'''
    body = f'''/** Activity unica do app. Toda a interface e desenhada em Compose. */
class MainActivity : {base}() {{

    // Pedido de permissoes perigosas necessarias pelas funcionalidades ativas.
    private val permissionLauncher =
        registerForActivityResult(ActivityResultContracts.RequestMultiplePermissions()) {{ }}

    override fun onCreate(savedInstanceState: Bundle?) {{
{splash}        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
{init + chr(10) if init else ""}        requestStartupPermissions()
        {deep_decl}
        setContent {{
{content}
        }}
    }}

    private fun requestStartupPermissions() {{
        if (!StartupPermissions.REQUEST_ON_START) return
        val missing = PermissionHelper.missing(this, StartupPermissions.list())
        if (missing.isNotEmpty()) permissionLauncher.launch(missing.toTypedArray())
    }}
}}
'''
    extra = []
    if theme_toggle:
        extra.append("androidx.compose.foundation.isSystemInDarkTheme")
    ctx.add_kotlin("MainActivity.kt", finalize(ctx, body, ctx.pkg, extra))
