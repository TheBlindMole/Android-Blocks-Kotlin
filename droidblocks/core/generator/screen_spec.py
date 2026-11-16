"""Analise de telas e geracao dos ViewModels (comuns a Compose e Views)."""

from ...catalog.components import COMPONENTS, parse_action, INPUT_COMPONENTS, LIST_COMPONENTS, split_actions
from ..naming import to_camel, to_pascal, kq

ALL_WORDS = {"todos", "todas", "tudo", "all", "geral"}
STRING_INPUTS = {"text_field", "radio_group", "dropdown", "chips", "tabs", "date_picker", "calendar"}


def options_of(comp):
    return [o.strip() for o in str(comp.props.get("options", "")).split(";") if o.strip()]


class InputField:
    def __init__(self, key, ctype, kotlin_type, default):
        self.key = key
        self.ctype = ctype
        self.type = kotlin_type
        self.default = default

    @property
    def setter(self):
        return "on" + self.key[:1].upper() + self.key[1:] + "Change"


class ListBinding:
    def __init__(self, comp, index, source):
        self.comp = comp
        self.index = index
        self.source = source
        self.items = f"list{index}Items"
        self.visible = f"list{index}Visible"


class ScreenSpec:
    """Tudo o que o gerador precisa saber sobre uma tela."""

    def __init__(self, ctx, screen):
        self.ctx = ctx
        self.screen = screen
        self.cls = ctx.screen_class(screen)
        self.route = ctx.screen_route(screen)
        self.package = ctx.screen_package(screen)
        self.components = ctx.valid_components(screen)
        self.inputs = {}
        self.input_by_comp = {}
        self.lists = []
        self.actions = set()
        self.validations = []
        self.chip_filter = None
        self.has_search = any(c.type == "search_bar" for c in self.components)
        self.fab = next((c for c in self.components if c.type == "fab"), None)
        self._analyze()

    def _analyze(self):
        used_types = {}
        list_index = 0
        for comp in self.components:
            if comp.type in INPUT_COMPONENTS:
                key = to_camel(comp.props.get("key", ""), "field")
                if key in ("query", "isLoading", "errors", "selectedItem", "photoUri", "fileUri"):
                    key += "Field"
                ktype, default = self._type_for(comp)
                if key in used_types and used_types[key] != ktype:
                    key = key + to_pascal(comp.type)
                used_types[key] = ktype
                if key not in self.inputs:
                    self.inputs[key] = InputField(key, comp.type, ktype, default)
                self.input_by_comp[comp.id] = self.inputs[key]
                if comp.type == "text_field" and comp.props.get("validation", "none") != "none":
                    self.validations.append((key, comp.props.get("validation")))
                if comp.type == "chips" and self.chip_filter is None:
                    opts = options_of(comp)
                    if opts and opts[0].lower() in ALL_WORDS:
                        self.chip_filter = (key, opts[0])
            if comp.type in LIST_COMPONENTS:
                list_index += 1
                self.lists.append(ListBinding(comp, list_index, comp.props.get("source", "sample:default")))
            spec = COMPONENTS[comp.type]
            for prop in spec.props:
                if prop.kind == "action":
                    for part in split_actions(comp.props.get(prop.key, "")):
                        self.actions.add(parse_action(part)[0])
        self.has_file = "pick_file" in self.actions
        self.has_photo = bool({"take_photo", "pick_image"} & self.actions) or any(
            c.type == "image" and c.props.get("source") == "photo" for c in self.components)

    @staticmethod
    def _type_for(comp):
        t = comp.type
        if t in STRING_INPUTS:
            opts = options_of(comp)
            if t in ("radio_group", "dropdown", "chips", "tabs") and opts:
                return "String", kq(opts[0])
            return "String", '""'
        if t in ("checkbox", "switch"):
            return "Boolean", "false"
        if t == "slider":
            try:
                low = float(comp.props.get("min", 0))
            except (TypeError, ValueError):
                low = 0.0
            return "Float", f"{low}f"
        if t == "rating":
            return "Int", "0"
        if t == "stepper":
            return "Int", "1"
        return "String", '""'

    @property
    def is_top_level(self):
        start = self.ctx.project.get_start_screen()
        return self.screen is start or self.screen.in_nav

    @property
    def needs_query(self):
        return self.has_search or "listen" in self.actions or "scan_code" in self.actions


# ----------------------------------------------------------------- acoes

ASYNC_THEN = {"submit", "login", "register", "logout", "biometric", "finish_onboarding", "location",
              "scan_code", "share_location"}


def action_code(ctx, spec, value, item_var=None):
    """Gera o codigo Kotlin de uma acao ou de uma sequencia de acoes ('a && b && c').

    Acoes assincronas (salvar, login, biometria...) executam as seguintes somente em caso de sucesso.
    """
    code = ""
    for part in reversed(split_actions(value)):
        code = _single_action(ctx, spec, part, item_var, code)
    return code


def _join(code, then):
    if not then:
        return code
    if not code:
        return then
    return f"{code}; {then}"


def _single_action(ctx, spec, value, item_var, then=""):
    """Codigo de uma unica acao; 'then' e o codigo das acoes seguintes."""
    key, _ = parse_action(value)
    if key in ASYNC_THEN:
        return _action_body(ctx, spec, value, item_var, then)
    return _join(_action_body(ctx, spec, value, item_var, ""), then)


def _action_body(ctx, spec, value, item_var=None, then=""):
    r = ctx.resolved
    key, arg = parse_action(value)
    p = ctx.project
    def route(name):
        screen = p.screen_by_name(name)
        return f"Routes.{ctx.route_const(screen.name)}" if screen else None

    def with_item(code):
        if item_var:
            return code.replace("ITEM", item_var)
        return ("viewModel.uiState.value.selectedItem?.let { item -> " + code.replace("ITEM", "item") +
                ' } ?: viewModel.showMessage("Nenhum item selecionado")')

    if key == "none":
        return ""
    if key == "navigate":
        target = route(arg)
        if not target:
            return f'viewModel.showMessage({kq("Tela nao encontrada: " + arg)})'
        return f"onNavigate({target}, {item_var + '.id' if item_var else 'null'})"
    if key == "back":
        return "onBack()"
    if key == "toast":
        return f"viewModel.showMessage({kq(arg or 'Pronto')})"
    if key == "refresh":
        return "viewModel.refresh()"
    if key == "submit":
        target = route(arg)
        inner = _join(f"onNavigate({target}, null)" if target else "", then)
        return f"viewModel.submit {{ {inner} }}"
    if key == "api":
        return f"viewModel.callApi({kq(arg)})"
    if key == "open_url":
        helper = "CustomTabsHelper.open" if r.has("custom_tabs") else "IntentHelper.openUrl"
        if arg:
            return f"{helper}(context, {kq(arg)})"
        return with_item(f"{helper}(context, ITEM.imageUrl)")
    if key == "share":
        return f"IntentHelper.shareText(context, {kq(arg or p.name)})"
    if key == "share_item":
        return with_item('IntentHelper.shareText(context, ITEM.title + "\\n" + ITEM.description)')
    if key in ("call", "email", "sms"):
        fn = {"call": "dial", "email": "email", "sms": "sms"}[key]
        if arg:
            return f"IntentHelper.{fn}(context, {kq(arg)})"
        return with_item(f"IntentHelper.{fn}(context, ITEM.subtitle)")
    if key == "copy":
        if arg:
            return f'ClipboardHelper.copy(context, {kq(arg)}); viewModel.showMessage("Copiado")'
        return with_item('ClipboardHelper.copy(context, ITEM.subtitle); viewModel.showMessage("Copiado")')
    if key in ("login", "register"):
        target = route(arg)
        nav = _join(f"onNavigateRoot({target})" if target else "", then)
        return f"viewModel.{key} {{ {nav} }}"
    if key == "logout":
        target = route(arg)
        nav = _join(f"onNavigateRoot({target})" if target else "", then)
        return f"viewModel.logout {{ {nav} }}"
    if key == "add_cart":
        return with_item('CartManager.add(ITEM); viewModel.showMessage("Adicionado ao carrinho")')
    if key == "remove_cart":
        return with_item("CartManager.remove(ITEM.id); viewModel.refresh()")
    if key == "checkout":
        target = route(arg)
        nav = f"; onNavigate({target}, null)" if target else ""
        return ('if (CartManager.count == 0) viewModel.showMessage("Carrinho vazio") else { '
                f'CartManager.clear(); viewModel.showMessage("Pedido realizado com sucesso"){nav} }}')
    if key == "favorite":
        return with_item('run { val added = FavoritesManager.toggle(ITEM); viewModel.showMessage(if (added) '
                         '"Adicionado aos favoritos" else "Removido dos favoritos") }')
    if key == "send_message":
        return "viewModel.sendMessage()"
    if key == "vibrate":
        return "VibrationHelper.vibrate(context)"
    if key == "notify":
        return f"NotificationHelper.show(context, context.getString(R.string.app_name), {kq(arg or 'Notificacao')})"
    if key == "speak":
        if arg:
            return f"TtsHelper.speak(context, {kq(arg)})"
        return with_item('TtsHelper.speak(context, ITEM.title + ". " + ITEM.description)')
    if key == "listen":
        return "listen()"
    if key == "flashlight":
        return ('run { val on = FlashlightHelper.toggle(context); viewModel.showMessage(if (on) "Lanterna ligada" '
                'else "Lanterna desligada") }')
    if key == "location":
        return "scope.launch { " + _join("viewModel.showMessage(LocationHelper.format(LocationHelper.current(context)))", then) + " }"
    if key == "scan_code":
        return "scope.launch { " + _join("viewModel.onScanResult(BarcodeScannerHelper.scan(context))", then) + " }"
    if key == "take_photo":
        return "takePhoto()"
    if key == "pick_image":
        return "pickImage()"
    if key == "biometric":
        target = route(arg)
        success = _join(f"onNavigate({target}, null)" if target else 'viewModel.showMessage("Autenticado")', then)
        return ("(activity as? FragmentActivity)?.let { BiometricHelper.authenticate(it, onSuccess = { "
                f"{success} }}, onError = {{ message -> viewModel.showMessage(message) }}) }}")
    if key == "rate_app":
        return "activity?.let { ReviewHelper.requestReview(it) }"
    if key == "toggle_theme":
        return "scope.launch { ThemePreferences.toggle(context) }"
    if key == "finish_onboarding":
        target = route(arg)
        nav = f"onNavigateRoot({target})" if target else ""
        return f"scope.launch {{ OnboardingState.complete(context); {_join(nav, then)} }}"
    if key == "device_info":
        return "viewModel.showMessage(DeviceInfoHelper.read(context).summary())"
    if key == "battery":
        return "viewModel.showMessage(BatteryHelper.summary(context))"
    if key == "delete_item":
        return with_item("viewModel.deleteItem(ITEM)")
    if key == "clear_form":
        return "viewModel.clearForm()"
    if key == "export_csv":
        return ('CsvExporter.exportAndShare(context, "dados.csv", listOf("Titulo", "Subtitulo", "Descricao", "Preco"), '
                'viewModel.exportRows())')
    if key == "open_map":
        if arg:
            return f"IntentHelper.openMapQuery(context, {kq(arg)})"
        return with_item('IntentHelper.openMapQuery(context, ITEM.title + " " + ITEM.subtitle)')
    if key == "whatsapp":
        if arg:
            return f"IntentHelper.whatsapp(context, {kq(arg)})"
        return with_item("IntentHelper.whatsapp(context, ITEM.subtitle)")
    if key == "share_location":
        share = ('IntentHelper.shareText(context, "Estou aqui: https://maps.google.com/?q=" + '
                 'location.latitude + "," + location.longitude)')
        return ("scope.launch { val location = LocationHelper.current(context); if (location == null) "
                f'viewModel.showMessage("Localizacao indisponivel") else {{ {_join(share, then)} }} }}')
    if key == "open_settings":
        return "IntentHelper.openAppSettings(context)"
    if key == "pick_file":
        return "pickFile()"
    if key == "report_bug":
        return "BugReporter.send(context)"
    return ""


def uses(spec, ctx, *needles):
    """Verifica se alguma acao gerada da tela usa determinados identificadores."""
    for comp in spec.components:
        for prop in COMPONENTS[comp.type].props:
            if prop.kind == "action":
                code = action_code(ctx, spec, comp.props.get(prop.key, ""), "item")
                if any(n in code for n in needles):
                    return True
    return False


# ----------------------------------------------------------------- ViewModel

def viewmodel(ctx, spec):
    p = ctx.project
    cls = spec.cls
    fields = ["    val isLoading: Boolean = false", "    val errors: Set<String> = emptySet()",
              "    val selectedItem: ListItem? = null"]
    if spec.has_photo:
        fields.append('    val photoUri: String = ""')
    if spec.has_file:
        fields.append('    val fileUri: String = ""')
    if spec.needs_query:
        fields.append('    val query: String = ""')
    for f in spec.inputs.values():
        fields.append(f"    val {f.key}: {f.type} = {f.default}")
    for lb in spec.lists:
        fields.append(f"    val {lb.items}: List<ListItem> = emptyList()")
    computed = []
    query = "query" if spec.needs_query else '""'
    filt = (spec.chip_filter[0], kq(spec.chip_filter[1])) if spec.chip_filter else ('""', '""')
    for lb in spec.lists:
        computed.append(f'''    /** Itens visiveis da lista {lb.index}, apos busca e filtro. */
    val {lb.visible}: List<ListItem>
        get() = ItemFilters.apply({lb.items}, {query}, {filt[0]}, {filt[1]})''')

    setters = []
    for f in spec.inputs.values():
        setters.append(f'''    fun {f.setter}(value: {f.type}) {{
        _uiState.update {{ it.copy({f.key} = value, errors = it.errors - "{f.key}") }}
    }}''')
    if spec.needs_query:
        setters.append('''    fun onQueryChange(value: String) {
        _uiState.update { it.copy(query = value) }
    }''')

    loads = []
    assigns = []
    for lb in spec.lists:
        loads.append(f'            val list{lb.index} = load({kq(lb.source)}, values)')
        assigns.append(f"{lb.items} = list{lb.index}")
    refresh_body = (
        "        viewModelScope.launch {\n"
        "            _uiState.update { it.copy(isLoading = true) }\n"
        "            val values = formValues()\n" + "\n".join(loads) + ("\n" if loads else "") +
        f"            _uiState.update {{ it.copy(isLoading = false{', ' + ', '.join(assigns) if assigns else ''}) }}\n"
        "        }")

    form_puts = []
    for f in spec.inputs.values():
        value = f"s.{f.key}" if f.type == "String" else f"s.{f.key}.toString()"
        form_puts.append(f'            put("{f.key}", {value})')

    checks = []
    for key, rule in spec.validations:
        checks.append(f'        if (!Validators.validate("{rule}", s.{key})) errors += "{key}"')
    validate = f'''    /** Valida os campos marcados com regra de validacao. */
    private fun validate(): Boolean {{
        val s = _uiState.value
        val errors = mutableSetOf<String>()
{chr(10).join(checks) if checks else "        // Nenhum campo com validacao nesta tela."}
        _uiState.update {{ it.copy(errors = errors) }}
        if (errors.isNotEmpty()) showMessage("Verifique os campos destacados")
        return errors.isEmpty()
    }}'''
    if not checks:
        validate = validate.replace("        val s = _uiState.value\n", "")

    entity = p.entity_by_name(spec.screen.form_entity) if spec.screen.form_entity else None
    if entity:
        save = f'''                repository.save({kq(entity.name)}, formValues())
                showMessage("Salvo com sucesso")'''
    else:
        save = '''                showMessage("Enviado com sucesso")'''

    extra = []
    if "login" in spec.actions or "register" in spec.actions:
        email = "email" if "email" in spec.inputs else None
        password = "password" if "password" in spec.inputs else None
        if email and password:
            for kind in ("login", "register"):
                if kind in spec.actions:
                    extra.append(f'''    /** {"Autentica o usuario" if kind == "login" else "Cadastra o usuario"} com e-mail e senha. */
    fun {kind}(onSuccess: () -> Unit) {{
        if (!validate()) return
        val s = _uiState.value
        viewModelScope.launch {{
            val error = AuthManager.{kind}(appContext, s.email, s.password)
            if (error == null) onSuccess() else showMessage(error)
        }}
    }}''')
        else:
            for kind in ("login", "register"):
                if kind in spec.actions:
                    extra.append(f'''    /** Esta tela precisa de campos com chave "email" e "password" para {kind}. */
    fun {kind}(onSuccess: () -> Unit) {{
        showMessage("Adicione campos com chave email e password")
    }}''')
    if "logout" in spec.actions:
        extra.append('''    /** Encerra a sessao e executa a navegacao informada. */
    fun logout(onDone: () -> Unit) {
        viewModelScope.launch {
            AuthManager.logout(appContext)
            onDone()
        }
    }''')
    if "send_message" in spec.actions:
        if "message" in spec.inputs:
            extra.append('''    /** Envia a mensagem digitada para o chat e limpa o campo. */
    fun sendMessage() {
        val text = _uiState.value.message
        if (text.isBlank()) return
        ChatRepository.send(text)
        _uiState.update { it.copy(message = "") }
        refresh()
    }''')
        else:
            extra.append('''    fun sendMessage() {
        showMessage("Adicione um campo com chave message")
    }''')
    if "delete_item" in spec.actions:
        extra.append('''    /** Exclui o item da sua origem (banco, carrinho ou favoritos) e recarrega. */
    fun deleteItem(item: ListItem) {
        viewModelScope.launch {
            try {
                repository.delete(item.id)
                showMessage("Item excluido")
            } catch (e: Exception) {
                showMessage("Erro ao excluir: " + (e.message ?: "falha"))
            }
            refresh()
        }
    }''')
    if "clear_form" in spec.actions:
        resets = ", ".join(f"{f.key} = {f.default}" for f in spec.inputs.values())
        extra.append(f'''    /** Volta todos os campos da tela para o valor inicial. */
    fun clearForm() {{
        _uiState.update {{ it.copy({resets + ", " if resets else ""}errors = emptySet()) }}
    }}''')
    if "export_csv" in spec.actions:
        visible = " + ".join(f"s.{lb.visible}" for lb in spec.lists) or "emptyList<ListItem>()"
        extra.append(f'''    /** Linhas das listas visiveis, usadas na exportacao CSV. */
    fun exportRows(): List<List<String>> {{
        val s = _uiState.value
        return ({visible}).map {{ listOf(it.title, it.subtitle, it.description, it.price?.toString().orEmpty()) }}
    }}''')
    if spec.has_file:
        extra.append('''    /** Recebe o arquivo escolhido pelo usuario. */
    fun onFilePicked(uri: String?) {
        if (uri.isNullOrBlank()) {
            showMessage("Nenhum arquivo selecionado")
        } else {
            _uiState.update { it.copy(fileUri = uri) }
            showMessage("Arquivo selecionado")
        }
    }''')
    if spec.has_photo:
        extra.append('''    /** Recebe a foto tirada ou escolhida. */
    fun onPhotoSelected(uri: String?) {
        if (uri.isNullOrBlank()) {
            showMessage("Nenhuma imagem selecionada")
        } else {
            _uiState.update { it.copy(photoUri = uri) }
        }
    }''')
    if "scan_code" in spec.actions:
        extra.append('''    /** Recebe o valor lido pelo leitor de codigos. */
    fun onScanResult(value: String?) {
        if (value.isNullOrBlank()) {
            showMessage("Leitura cancelada")
        } else {
            _uiState.update { it.copy(query = value) }
            showMessage("Codigo: $value")
        }
    }''')
    if "listen" in spec.actions:
        extra.append('''    /** Recebe o texto reconhecido por voz e usa como busca. */
    fun onSpeechResult(text: String?) {
        if (text.isNullOrBlank()) {
            showMessage("Nao foi possivel reconhecer a fala")
        } else {
            _uiState.update { it.copy(query = text) }
        }
    }''')

    body = "\n\n".join(setters + extra)
    feature_import = "import %PKG%.features.*\n" if ctx.has_feature_files() else ""
    validators_import = ""
    code = f'''package {spec.package}

import android.content.Context
import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.createSavedStateHandle
import androidx.lifecycle.viewModelScope
import androidx.lifecycle.viewmodel.initializer
import androidx.lifecycle.viewmodel.viewModelFactory
import %PKG%.App
import %PKG%.data.model.ItemFilters
import %PKG%.data.model.ListItem
import %PKG%.data.repository.AppRepository
{feature_import}{validators_import}import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

/** Estado da tela "{spec.screen.title or spec.screen.name}". */
data class {cls}UiState(
{("," + chr(10)).join(fields)}
){" {" + chr(10) + (chr(10) + chr(10)).join(computed) + chr(10) + "}" if computed else ""}

/** Logica da tela "{spec.screen.title or spec.screen.name}": estado, validacao e acesso aos dados. */
class {cls}ViewModel(
    private val repository: AppRepository,
    private val savedStateHandle: SavedStateHandle,
    private val appContext: Context
) : ViewModel() {{

    private val _uiState = MutableStateFlow({cls}UiState())
    val uiState: StateFlow<{cls}UiState> = _uiState.asStateFlow()

    private val _messages = MutableSharedFlow<String>(extraBufferCapacity = 8)

    /** Mensagens curtas para o usuario (exibidas como Toast pela tela). */
    val messages: SharedFlow<String> = _messages.asSharedFlow()

    init {{
        loadSelectedItem()
    }}

    fun showMessage(text: String) {{
        _messages.tryEmit(text)
    }}

{body + chr(10) + chr(10) if body else ""}    /** Recarrega todas as listas da tela. */
    fun refresh() {{
{refresh_body}
    }}

    // Carrega uma fonte de dados sem derrubar a tela em caso de erro.
    private suspend fun load(source: String, values: Map<String, String>): List<ListItem> = try {{
        repository.getItems(source, values)
    }} catch (e: Exception) {{
        showMessage("Falha ao carregar dados: " + (e.message ?: "erro desconhecido"))
        emptyList()
    }}

    // Carrega o item recebido pela navegacao (parametro itemId).
    private fun loadSelectedItem() {{
        val id = savedStateHandle.get<String>("itemId") ?: return
        _uiState.update {{ it.copy(selectedItem = repository.findItem(id)) }}
    }}

    /** Valores atuais do formulario, usados ao salvar e ao chamar APIs. */
    fun formValues(): Map<String, String> {{
        val s = _uiState.value
        return buildMap {{
{chr(10).join(form_puts)}
            s.selectedItem?.let {{ put("itemId", it.id) }}
        }}
    }}

{validate}

    /** Valida, salva e executa [onSuccess] quando tudo der certo. */
    fun submit(onSuccess: () -> Unit) {{
        if (!validate()) return
        viewModelScope.launch {{
            try {{
{save}
                onSuccess()
            }} catch (e: Exception) {{
                showMessage("Erro: " + (e.message ?: "falha ao salvar"))
            }}
        }}
    }}

    /** Chama um endpoint de API. GET recarrega as listas; os demais enviam os campos da tela. */
    fun callApi(endpoint: String) {{
        if (!validate()) return
        viewModelScope.launch {{
            try {{
                val message = repository.call(endpoint, formValues())
                showMessage(message)
            }} catch (e: Exception) {{
                showMessage("Erro na API: " + (e.message ?: "falha de conexao"))
            }}
            refresh()
        }}
    }}

    companion object {{
        /** Fabrica que injeta o repositorio do AppContainer e o SavedStateHandle. */
        val Factory: ViewModelProvider.Factory = viewModelFactory {{
            initializer {{
                val app = this[ViewModelProvider.AndroidViewModelFactory.APPLICATION_KEY] as App
                {cls}ViewModel(app.container.repository, createSavedStateHandle(), app)
            }}
        }}
    }}
}}
'''
    return code
