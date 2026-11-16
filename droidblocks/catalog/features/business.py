"""Funcionalidades de seguranca, comercio, social e produtividade."""

from .base import Feature

SEC = "Seguranca e autenticacao"
COM = "Comercio e pagamentos"
SOC = "Social e comunicacao"
PRO = "Produtividade e interface"

FEATURES = [
    # ----- Seguranca -----
    Feature(
        key="local_auth", name="Login e cadastro local", category=SEC,
        description="Cadastro e login offline com senha protegida por hash SHA-256 com salt. "
                    "Habilita as acoes 'Entrar', 'Cadastrar' e 'Sair'. Usa campos com chave "
                    "'email' e 'password' na tela.",
        requires=["datastore"],
        files={"features/AuthManager.kt": r'''package %PKG%.features

import android.content.Context
import %PKG%.data.local.PreferencesStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import java.security.MessageDigest
import java.security.SecureRandom

/** Autenticacao local: cadastro, login, sessao e logout. */
object AuthManager {

    private const val KEY_USERS = "auth_users"
    private const val KEY_SESSION = "auth_session"

    /** E-mail do usuario logado, ou vazio. */
    fun sessionFlow(context: Context): Flow<String> = PreferencesStore(context).getString(KEY_SESSION, "")

    suspend fun isLoggedIn(context: Context): Boolean = sessionFlow(context).first().isNotBlank()

    /** Cadastra um usuario. Retorna mensagem de erro ou null em caso de sucesso. */
    suspend fun register(context: Context, email: String, password: String): String? {
        val normalized = email.trim().lowercase()
        if (!normalized.contains("@")) return "E-mail invalido"
        if (password.length < 6) return "A senha deve ter pelo menos 6 caracteres"
        val store = PreferencesStore(context)
        val users = store.getStringSet(KEY_USERS).first()
        if (users.any { it.startsWith("$normalized|") }) return "E-mail ja cadastrado"
        val salt = randomSalt()
        store.putStringSet(KEY_USERS, users + "$normalized|$salt|${hash(password, salt)}")
        store.putString(KEY_SESSION, normalized)
        return null
    }

    /** Valida as credenciais e abre a sessao. Retorna mensagem de erro ou null. */
    suspend fun login(context: Context, email: String, password: String): String? {
        val normalized = email.trim().lowercase()
        val store = PreferencesStore(context)
        val record = store.getStringSet(KEY_USERS).first().firstOrNull { it.startsWith("$normalized|") }
            ?: return "Usuario nao encontrado"
        val parts = record.split("|")
        if (parts.size != 3 || hash(password, parts[1]) != parts[2]) return "Senha incorreta"
        store.putString(KEY_SESSION, normalized)
        return null
    }

    suspend fun logout(context: Context) {
        PreferencesStore(context).putString(KEY_SESSION, "")
    }

    private fun randomSalt(): String {
        val bytes = ByteArray(16)
        SecureRandom().nextBytes(bytes)
        return bytes.joinToString("") { "%02x".format(it) }
    }

    private fun hash(password: String, salt: String): String {
        val digest = MessageDigest.getInstance("SHA-256").digest((salt + password).toByteArray(Charsets.UTF_8))
        return digest.joinToString("") { "%02x".format(it) }
    }
}
'''},
    ),
    Feature(
        key="validators", name="Validacao de formularios", category=SEC,
        description="Valida e-mail, telefone, senha forte, CPF, CNPJ, NIF (PT), CEP e codigo postal PT. "
                    "Usado pela propriedade 'validacao' dos campos de texto.",
        files={"features/Validators.kt": r'''package %PKG%.features

/** Validacoes comuns de formularios. Cada funcao retorna true quando o valor e valido. */
object Validators {

    private val EMAIL = Regex("^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$")

    fun required(value: String) = value.isNotBlank()

    fun email(value: String) = EMAIL.matches(value.trim())

    /** Telefone com 8 a 15 digitos (aceita +, espacos, parenteses e tracos). */
    fun phone(value: String): Boolean {
        val digits = value.filter { it.isDigit() }
        return digits.length in 8..15
    }

    fun number(value: String) = value.replace(',', '.').toDoubleOrNull() != null

    /** Senha com 8+ caracteres, letra maiuscula, minuscula e numero. */
    fun strongPassword(value: String) = value.length >= 8 &&
        value.any { it.isUpperCase() } && value.any { it.isLowerCase() } && value.any { it.isDigit() }

    fun cpf(value: String): Boolean {
        val d = value.filter { it.isDigit() }.map { it - '0' }
        if (d.size != 11 || d.all { it == d[0] }) return false
        val first = (0 until 9).sumOf { d[it] * (10 - it) }.let { (it * 10 % 11) % 10 }
        val second = (0 until 10).sumOf { d[it] * (11 - it) }.let { (it * 10 % 11) % 10 }
        return first == d[9] && second == d[10]
    }

    fun cnpj(value: String): Boolean {
        val d = value.filter { it.isDigit() }.map { it - '0' }
        if (d.size != 14 || d.all { it == d[0] }) return false
        val w1 = intArrayOf(5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)
        val w2 = intArrayOf(6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)
        val r1 = (0 until 12).sumOf { d[it] * w1[it] } % 11
        val c1 = if (r1 < 2) 0 else 11 - r1
        val r2 = (0 until 13).sumOf { d[it] * w2[it] } % 11
        val c2 = if (r2 < 2) 0 else 11 - r2
        return c1 == d[12] && c2 == d[13]
    }

    /** NIF portugues (9 digitos com digito de controlo). */
    fun nif(value: String): Boolean {
        val d = value.filter { it.isDigit() }.map { it - '0' }
        if (d.size != 9 || d[0] == 0) return false
        val sum = (0 until 8).sumOf { d[it] * (9 - it) }
        val check = 11 - sum % 11
        return d[8] == if (check >= 10) 0 else check
    }

    fun cep(value: String) = value.filter { it.isDigit() }.length == 8

    fun postalCodePt(value: String) = Regex("^\\d{4}-\\d{3}$").matches(value.trim())

    /** Valida pelo nome da regra configurada no bloco. */
    fun validate(rule: String, value: String): Boolean = when (rule) {
        "required" -> required(value)
        "email" -> email(value)
        "phone" -> phone(value)
        "number" -> number(value)
        "password" -> strongPassword(value)
        "cpf" -> cpf(value)
        "cnpj" -> cnpj(value)
        "nif" -> nif(value)
        "cep" -> cep(value)
        "postal_pt" -> postalCodePt(value)
        else -> true
    }
}
'''},
    ),
    Feature(
        key="secure_screen", name="Bloquear capturas de tela", category=SEC,
        description="Impede screenshots e gravacao de tela (apps bancarios, saude).",
        requires=["window_control"], activity_init=["WindowHelper.setSecure(this, true)"],
    ),
    Feature(
        key="root_detection", name="Deteccao de root", category=SEC,
        description="Verificacao basica se o aparelho possui root.",
        files={"features/RootDetector.kt": r'''package %PKG%.features

import android.os.Build
import java.io.File

/** Heuristicas simples de deteccao de root. Nao e uma protecao definitiva. */
object RootDetector {

    private val SU_PATHS = listOf(
        "/system/app/Superuser.apk", "/sbin/su", "/system/bin/su", "/system/xbin/su",
        "/data/local/xbin/su", "/data/local/bin/su", "/system/sd/xbin/su", "/data/local/su"
    )

    fun isRooted(): Boolean {
        val testKeys = Build.TAGS?.contains("test-keys") == true
        val hasSu = SU_PATHS.any { File(it).exists() }
        return testKeys || hasSu
    }
}
'''},
    ),
    Feature(
        key="pin_lock", name="Bloqueio por PIN", category=SEC,
        description="Define e verifica um PIN numerico guardado com hash.",
        requires=["datastore"],
        files={"features/PinManager.kt": r'''package %PKG%.features

import android.content.Context
import %PKG%.data.local.PreferencesStore
import kotlinx.coroutines.flow.first
import java.security.MessageDigest

/** Gerencia um PIN de acesso ao app. */
object PinManager {

    private const val KEY = "app_pin_hash"

    suspend fun hasPin(context: Context) = PreferencesStore(context).getString(KEY).first().isNotBlank()

    suspend fun setPin(context: Context, pin: String) {
        PreferencesStore(context).putString(KEY, hash(pin))
    }

    suspend fun verify(context: Context, pin: String) = PreferencesStore(context).getString(KEY).first() == hash(pin)

    suspend fun clear(context: Context) = PreferencesStore(context).putString(KEY, "")

    private fun hash(pin: String) = MessageDigest.getInstance("SHA-256")
        .digest(pin.toByteArray()).joinToString("") { "%02x".format(it) }
}
'''},
    ),
    # ----- Comercio -----
    Feature(
        key="cart", name="Carrinho de compras", category=COM,
        description="Carrinho em memoria com quantidades e total. Habilita as acoes 'Adicionar ao "
                    "carrinho', 'Remover do carrinho', 'Finalizar compra' e a fonte de lista 'cart'.",
        files={"features/CartManager.kt": r'''package %PKG%.features

import %PKG%.data.model.ListItem
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update

/** Linha do carrinho: item e quantidade. */
data class CartLine(val item: ListItem, val quantity: Int) {
    val total: Double get() = (item.price ?: 0.0) * quantity
}

/** Carrinho compartilhado por todas as telas. */
object CartManager {

    private val _lines = MutableStateFlow<List<CartLine>>(emptyList())
    val lines: StateFlow<List<CartLine>> = _lines.asStateFlow()

    val total: Double get() = _lines.value.sumOf { it.total }
    val count: Int get() = _lines.value.sumOf { it.quantity }

    fun add(item: ListItem, quantity: Int = 1) {
        _lines.update { current ->
            val existing = current.find { it.item.id == item.id }
            if (existing == null) {
                current + CartLine(item, quantity)
            } else {
                current.map { if (it.item.id == item.id) it.copy(quantity = it.quantity + quantity) else it }
            }
        }
    }

    fun remove(itemId: String) {
        _lines.update { current ->
            current.mapNotNull { line ->
                when {
                    line.item.id != itemId -> line
                    line.quantity > 1 -> line.copy(quantity = line.quantity - 1)
                    else -> null
                }
            }
        }
    }

    fun clear() {
        _lines.value = emptyList()
    }

    /** Converte as linhas em itens de lista para exibicao. */
    fun asListItems(): List<ListItem> = _lines.value.map { line ->
        line.item.copy(
            subtitle = "Qtd: ${line.quantity}",
            price = line.total,
            badge = line.quantity.toString()
        )
    }
}
'''},
    ),
    Feature(
        key="favorites", name="Favoritos", category=COM,
        description="Marca itens como favoritos. Habilita a acao 'Favoritar' e a fonte de lista 'favorites'.",
        files={"features/FavoritesManager.kt": r'''package %PKG%.features

import %PKG%.data.model.ListItem
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update

/** Lista de favoritos compartilhada entre as telas. */
object FavoritesManager {

    private val _items = MutableStateFlow<List<ListItem>>(emptyList())
    val items: StateFlow<List<ListItem>> = _items.asStateFlow()

    fun isFavorite(id: String) = _items.value.any { it.id == id }

    fun remove(id: String) {
        _items.update { current -> current.filterNot { it.id == id } }
    }

    /** Alterna o item e retorna true se ele passou a ser favorito. */
    fun toggle(item: ListItem): Boolean {
        val added = !isFavorite(item.id)
        _items.update { current -> if (added) current + item else current.filterNot { it.id == item.id } }
        return added
    }
}
'''},
    ),
    Feature(
        key="checkout", name="Calculo de checkout (frete, cupom, taxas)", category=COM,
        description="Calcula subtotal, frete, desconto por cupom e total final.",
        files={"features/CheckoutCalculator.kt": r'''package %PKG%.features

/** Resumo de valores de um pedido. */
data class CheckoutSummary(
    val subtotal: Double,
    val shipping: Double,
    val discount: Double,
    val total: Double
)

/** Regras de calculo do checkout. Ajuste os valores conforme o negocio. */
object CheckoutCalculator {

    var freeShippingFrom = 150.0
    var shippingFee = 12.90

    private val coupons = mapOf(
        "BEMVINDO10" to 0.10,
        "PROMO20" to 0.20
    )

    fun calculate(subtotal: Double, coupon: String = ""): CheckoutSummary {
        val shipping = if (subtotal >= freeShippingFrom || subtotal == 0.0) 0.0 else shippingFee
        val rate = coupons[coupon.trim().uppercase()] ?: 0.0
        val discount = subtotal * rate
        return CheckoutSummary(subtotal, shipping, discount, (subtotal - discount + shipping).coerceAtLeast(0.0))
    }

    fun isValidCoupon(coupon: String) = coupons.containsKey(coupon.trim().uppercase())
}
'''},
    ),
    Feature(
        key="payments", name="Pagamentos (estrutura plugavel)", category=COM,
        description="Interface de pagamento com processador simulado offline. Troque pela integracao "
                    "real (Stripe, Mercado Pago, PagSeguro, Google Pay).",
        files={"features/PaymentProcessor.kt": r'''package %PKG%.features

import kotlinx.coroutines.delay
import java.util.UUID

/** Resultado de uma tentativa de pagamento. */
sealed class PaymentResult {
    data class Approved(val transactionId: String) : PaymentResult()
    data class Declined(val reason: String) : PaymentResult()
}

/** Contrato para qualquer gateway de pagamento. */
interface PaymentProcessor {
    suspend fun pay(amount: Double, method: String, description: String): PaymentResult
}

/** Implementacao simulada para testes e prototipos. Nao realiza cobrancas reais. */
class FakePaymentProcessor : PaymentProcessor {
    override suspend fun pay(amount: Double, method: String, description: String): PaymentResult {
        delay(1200)
        return if (amount <= 0.0) {
            PaymentResult.Declined("Valor invalido")
        } else {
            PaymentResult.Approved(UUID.randomUUID().toString().take(8).uppercase())
        }
    }
}
'''},
    ),
    Feature(
        key="order_tracking", name="Acompanhamento de pedido", category=COM,
        description="Maquina de estados de pedido (recebido, preparo, a caminho, entregue).",
        files={"features/OrderTracker.kt": r'''package %PKG%.features

import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

/** Etapas de um pedido. */
enum class OrderStatus(val label: String) {
    RECEIVED("Pedido recebido"),
    PREPARING("Em preparo"),
    ON_THE_WAY("A caminho"),
    DELIVERED("Entregue"),
    CANCELED("Cancelado")
}

/** Controla o avanco do status de um pedido. */
class OrderTracker(initial: OrderStatus = OrderStatus.RECEIVED) {

    private val _status = MutableStateFlow(initial)
    val status: StateFlow<OrderStatus> = _status.asStateFlow()

    fun advance() {
        _status.value = when (_status.value) {
            OrderStatus.RECEIVED -> OrderStatus.PREPARING
            OrderStatus.PREPARING -> OrderStatus.ON_THE_WAY
            OrderStatus.ON_THE_WAY -> OrderStatus.DELIVERED
            else -> _status.value
        }
    }

    fun cancel() {
        if (_status.value != OrderStatus.DELIVERED) _status.value = OrderStatus.CANCELED
    }

    /** Progresso de 0.0 a 1.0 para barras de progresso. */
    val progress: Float get() = when (_status.value) {
        OrderStatus.RECEIVED -> 0.25f
        OrderStatus.PREPARING -> 0.5f
        OrderStatus.ON_THE_WAY -> 0.75f
        OrderStatus.DELIVERED -> 1f
        OrderStatus.CANCELED -> 0f
    }
}
'''},
    ),
    Feature(
        key="formatters", name="Formatadores (moeda, data, numeros)", category=COM,
        description="Formata moeda, datas, tempo relativo e numeros compactos conforme o idioma.",
        files={"features/Formatters.kt": r'''package %PKG%.features

import java.text.NumberFormat
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.concurrent.TimeUnit

/** Formatacao de valores para exibicao. */
object Formatters {

    fun currency(value: Double, locale: Locale = Locale.getDefault()): String =
        NumberFormat.getCurrencyInstance(locale).format(value)

    fun number(value: Double, decimals: Int = 2): String =
        NumberFormat.getNumberInstance().apply {
            minimumFractionDigits = decimals
            maximumFractionDigits = decimals
        }.format(value)

    fun date(millis: Long, pattern: String = "dd/MM/yyyy"): String =
        SimpleDateFormat(pattern, Locale.getDefault()).format(Date(millis))

    fun dateTime(millis: Long): String = date(millis, "dd/MM/yyyy HH:mm")

    /** Ex.: "ha 5 min", "ha 2 h", "ha 3 dias". */
    fun relative(millis: Long, now: Long = System.currentTimeMillis()): String {
        val diff = (now - millis).coerceAtLeast(0)
        val minutes = TimeUnit.MILLISECONDS.toMinutes(diff)
        return when {
            minutes < 1 -> "agora"
            minutes < 60 -> "ha $minutes min"
            minutes < 1440 -> "ha ${minutes / 60} h"
            else -> "ha ${minutes / 1440} dias"
        }
    }

    /** Ex.: 1200 -> "1,2 mil", 3400000 -> "3,4 mi". */
    fun compact(value: Long): String = when {
        value >= 1_000_000 -> "%.1f mi".format(value / 1_000_000.0)
        value >= 1_000 -> "%.1f mil".format(value / 1_000.0)
        else -> value.toString()
    }
}
'''},
    ),
    Feature(
        key="loyalty", name="Programa de pontos", category=COM,
        description="Acumulo e resgate de pontos de fidelidade salvos no DataStore.",
        requires=["datastore"],
        files={"features/PointsManager.kt": r'''package %PKG%.features

import android.content.Context
import %PKG%.data.local.PreferencesStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first

/** Saldo de pontos do usuario. */
object PointsManager {

    private const val KEY = "loyalty_points"

    fun balance(context: Context): Flow<Int> = PreferencesStore(context).getInt(KEY, 0)

    suspend fun earn(context: Context, points: Int) {
        val store = PreferencesStore(context)
        store.putInt(KEY, store.getInt(KEY, 0).first() + points)
    }

    /** Resgata pontos. Retorna false se o saldo for insuficiente. */
    suspend fun redeem(context: Context, points: Int): Boolean {
        val store = PreferencesStore(context)
        val current = store.getInt(KEY, 0).first()
        if (current < points) return false
        store.putInt(KEY, current - points)
        return true
    }

    /** Regra padrao: 1 ponto a cada 1 unidade monetaria gasta. */
    fun pointsFor(amount: Double) = amount.toInt()
}
'''},
    ),
    # ----- Social -----
    Feature(
        key="chat", name="Chat local", category=SOC,
        description="Mensagens em tempo real em memoria com resposta automatica de exemplo. "
                    "Habilita a acao 'Enviar mensagem' (campo com chave 'message') e a fonte 'chat'.",
        files={"features/ChatRepository.kt": r'''package %PKG%.features

import %PKG%.data.model.ListItem
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/** Mensagem do chat. */
data class ChatMessage(val id: Long, val author: String, val text: String, val time: Long, val mine: Boolean)

/** Repositorio de mensagens. Substitua por WebSocket ou Firestore para chat real. */
object ChatRepository {

    private val _messages = MutableStateFlow(
        listOf(ChatMessage(1, "Suporte", "Ola! Como posso ajudar?", System.currentTimeMillis(), false))
    )
    val messages: StateFlow<List<ChatMessage>> = _messages.asStateFlow()

    fun send(text: String) {
        if (text.isBlank()) return
        val now = System.currentTimeMillis()
        _messages.update { it + ChatMessage(now, "Voce", text.trim(), now, true) }
        _messages.update { it + ChatMessage(now + 1, "Suporte", autoReply(text), now + 1, false) }
    }

    private fun autoReply(text: String): String = when {
        text.contains("preco", ignoreCase = true) -> "Os precos estao na tela de produtos."
        text.contains("obrigad", ignoreCase = true) -> "Por nada! Estamos a disposicao."
        else -> "Recebemos sua mensagem: \"$text\""
    }

    fun asListItems(): List<ListItem> {
        val format = SimpleDateFormat("HH:mm", Locale.getDefault())
        return _messages.value.map { message ->
            ListItem(
                id = message.id.toString(),
                title = message.text,
                subtitle = "${message.author} - ${format.format(Date(message.time))}",
                badge = if (message.mine) "eu" else ""
            )
        }
    }
}
'''},
    ),
    Feature(
        key="contacts", name="Ler contatos do aparelho", category=SOC,
        description="Lista contatos com nome e telefone. Habilita a fonte de lista 'contacts'.",
        permissions=["android.permission.READ_CONTACTS"],
        files={"features/ContactsHelper.kt": r'''package %PKG%.features

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.provider.ContactsContract
import androidx.core.content.ContextCompat
import %PKG%.data.model.ListItem
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

/** Leitura dos contatos do telefone. Retorna lista vazia sem permissao. */
object ContactsHelper {

    suspend fun read(context: Context, limit: Int = 500): List<ListItem> = withContext(Dispatchers.IO) {
        val granted = ContextCompat.checkSelfPermission(context, Manifest.permission.READ_CONTACTS) ==
            PackageManager.PERMISSION_GRANTED
        if (!granted) return@withContext emptyList()
        val result = mutableListOf<ListItem>()
        val projection = arrayOf(
            ContactsContract.CommonDataKinds.Phone.CONTACT_ID,
            ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME,
            ContactsContract.CommonDataKinds.Phone.NUMBER
        )
        context.contentResolver.query(
            ContactsContract.CommonDataKinds.Phone.CONTENT_URI, projection, null, null,
            ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME + " ASC"
        )?.use { cursor ->
            while (cursor.moveToNext() && result.size < limit) {
                result += ListItem(
                    id = "contact_" + cursor.getString(0) + "_" + result.size,
                    title = cursor.getString(1).orEmpty(),
                    subtitle = cursor.getString(2).orEmpty()
                )
            }
        }
        result
    }
}
'''},
    ),
    Feature(
        key="calendar_event", name="Adicionar evento ao calendario", category=SOC,
        description="Abre o calendario do aparelho com o evento preenchido (sem permissao).",
        files={"features/CalendarHelper.kt": r'''package %PKG%.features

import android.content.Context
import android.content.Intent
import android.provider.CalendarContract

/** Cria eventos no calendario usando o app padrao do aparelho. */
object CalendarHelper {

    fun addEvent(context: Context, title: String, startMillis: Long, endMillis: Long, location: String = "", description: String = "") {
        val intent = Intent(Intent.ACTION_INSERT)
            .setData(CalendarContract.Events.CONTENT_URI)
            .putExtra(CalendarContract.Events.TITLE, title)
            .putExtra(CalendarContract.EXTRA_EVENT_BEGIN_TIME, startMillis)
            .putExtra(CalendarContract.EXTRA_EVENT_END_TIME, endMillis)
            .putExtra(CalendarContract.Events.EVENT_LOCATION, location)
            .putExtra(CalendarContract.Events.DESCRIPTION, description)
            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        try {
            context.startActivity(intent)
        } catch (e: Exception) {
            // Nenhum app de calendario instalado.
        }
    }
}
'''},
    ),
    Feature(
        key="user_profile", name="Perfil do usuario", category=SOC,
        description="Nome, e-mail e biografia do usuario salvos no DataStore.",
        requires=["datastore"],
        files={"features/ProfileStore.kt": r'''package %PKG%.features

import android.content.Context
import %PKG%.data.local.PreferencesStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.combine

/** Dados de perfil do usuario. */
data class UserProfile(val name: String, val email: String, val bio: String)

object ProfileStore {

    fun profile(context: Context): Flow<UserProfile> {
        val store = PreferencesStore(context)
        return combine(
            store.getString("profile_name"),
            store.getString("profile_email"),
            store.getString("profile_bio")
        ) { name, email, bio -> UserProfile(name, email, bio) }
    }

    suspend fun save(context: Context, profile: UserProfile) {
        val store = PreferencesStore(context)
        store.putString("profile_name", profile.name)
        store.putString("profile_email", profile.email)
        store.putString("profile_bio", profile.bio)
    }
}
'''},
    ),
    # ----- Produtividade -----
    Feature(
        key="search_engine", name="Busca inteligente", category=PRO,
        description="Busca sem acentos, por multiplas palavras e com tolerancia a erros de digitacao. "
                    "Quando ativa, a barra de busca das telas passa a usa-la.",
        files={"features/SearchEngine.kt": r'''package %PKG%.features

import %PKG%.data.model.ListItem
import java.text.Normalizer

/** Filtragem e ordenacao de itens por relevancia. */
object SearchEngine {

    fun normalize(text: String): String =
        Normalizer.normalize(text.lowercase(), Normalizer.Form.NFD).replace(Regex("\\p{Mn}+"), "")

    fun filter(items: List<ListItem>, query: String): List<ListItem> {
        val terms = normalize(query).split(" ").filter { it.isNotBlank() }
        if (terms.isEmpty()) return items
        return items.map { item -> item to score(item, terms) }
            .filter { it.second > 0 }
            .sortedByDescending { it.second }
            .map { it.first }
    }

    // Soma a relevancia de cada termo. Se algum termo nao aparecer, o item e descartado (0).
    private fun score(item: ListItem, terms: List<String>): Int {
        val title = normalize(item.title)
        val rest = normalize(item.subtitle + " " + item.description)
        var total = 0
        for (term in terms) {
            val points = when {
                title.startsWith(term) -> 5
                title.contains(term) -> 3
                rest.contains(term) -> 1
                title.split(" ").any { levenshtein(it, term) <= 1 && term.length > 3 } -> 1
                else -> 0
            }
            if (points == 0) return 0
            total += points
        }
        return total
    }

    private fun levenshtein(a: String, b: String): Int {
        val dp = IntArray(b.length + 1) { it }
        for (i in 1..a.length) {
            var previous = dp[0]
            dp[0] = i
            for (j in 1..b.length) {
                val temp = dp[j]
                dp[j] = minOf(dp[j] + 1, dp[j - 1] + 1, previous + if (a[i - 1] == b[j - 1]) 0 else 1)
                previous = temp
            }
        }
        return dp[b.length]
    }
}
'''},
    ),
    Feature(
        key="charts", name="Graficos (barras, linhas, pizza)", category=PRO,
        description="Graficos desenhados nativamente, sem bibliotecas externas. Usado pelo bloco 'Grafico'.",
        files_compose={"ui/components/Charts.kt": r'''package %PKG%.ui.components

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.unit.dp

/** Grafico de barras simples. */
@Composable
fun BarChart(values: List<Float>, modifier: Modifier = Modifier.fillMaxWidth().height(180.dp)) {
    val color = MaterialTheme.colorScheme.primary
    Canvas(modifier = modifier) {
        if (values.isEmpty()) return@Canvas
        val max = (values.maxOrNull() ?: 1f).coerceAtLeast(1f)
        val slot = size.width / values.size
        val barWidth = slot * 0.6f
        values.forEachIndexed { index, value ->
            val barHeight = size.height * (value / max)
            drawRoundRect(
                color = color,
                topLeft = Offset(index * slot + (slot - barWidth) / 2, size.height - barHeight),
                size = Size(barWidth, barHeight),
                cornerRadius = CornerRadius(8f, 8f)
            )
        }
    }
}

/** Grafico de linha com pontos. */
@Composable
fun LineChart(values: List<Float>, modifier: Modifier = Modifier.fillMaxWidth().height(180.dp)) {
    val color = MaterialTheme.colorScheme.primary
    Canvas(modifier = modifier) {
        if (values.size < 2) return@Canvas
        val max = values.maxOrNull() ?: 1f
        val min = values.minOrNull() ?: 0f
        val range = (max - min).takeIf { it > 0f } ?: 1f
        val step = size.width / (values.size - 1)
        val path = Path()
        values.forEachIndexed { index, value ->
            val point = Offset(index * step, size.height - (value - min) / range * size.height)
            if (index == 0) path.moveTo(point.x, point.y) else path.lineTo(point.x, point.y)
            drawCircle(color, radius = 6f, center = point)
        }
        drawPath(path, color, style = Stroke(width = 5f))
    }
}

/** Grafico de pizza com cores alternadas. */
@Composable
fun PieChart(values: List<Float>, modifier: Modifier = Modifier.fillMaxWidth().height(200.dp)) {
    val palette = listOf(
        MaterialTheme.colorScheme.primary, MaterialTheme.colorScheme.secondary,
        MaterialTheme.colorScheme.tertiary, Color(0xFF90CAF9), Color(0xFF1565C0), Color(0xFF80DEEA)
    )
    Canvas(modifier = modifier) {
        val total = values.sum().takeIf { it > 0f } ?: return@Canvas
        val diameter = minOf(size.width, size.height)
        val topLeft = Offset((size.width - diameter) / 2, (size.height - diameter) / 2)
        var start = -90f
        values.forEachIndexed { index, value ->
            val sweep = value / total * 360f
            drawArc(palette[index % palette.size], start, sweep, true, topLeft, Size(diameter, diameter))
            start += sweep
        }
    }
}
'''},
        files_views={"ui/components/ChartView.kt": r'''package %PKG%.ui.components

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Path
import android.graphics.RectF
import android.util.AttributeSet
import android.view.View

/** View de grafico com tres estilos: "bar", "line" e "pie". */
class ChartView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null
) : View(context, attrs) {

    var values: List<Float> = emptyList()
        set(value) {
            field = value
            invalidate()
        }

    var style: String = "bar"
        set(value) {
            field = value
            invalidate()
        }

    var color: Int = Color.parseColor("#1E88E5")

    private val paint = Paint(Paint.ANTI_ALIAS_FLAG)
    private val palette = intArrayOf(
        Color.parseColor("#1E88E5"), Color.parseColor("#0D47A1"), Color.parseColor("#26C6DA"),
        Color.parseColor("#90CAF9"), Color.parseColor("#1565C0"), Color.parseColor("#80DEEA")
    )

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        if (values.isEmpty()) return
        when (style) {
            "line" -> drawLine(canvas)
            "pie" -> drawPie(canvas)
            else -> drawBars(canvas)
        }
    }

    private fun drawBars(canvas: Canvas) {
        paint.style = Paint.Style.FILL
        paint.color = color
        val max = (values.maxOrNull() ?: 1f).coerceAtLeast(1f)
        val slot = width.toFloat() / values.size
        val barWidth = slot * 0.6f
        values.forEachIndexed { index, value ->
            val left = index * slot + (slot - barWidth) / 2
            val top = height - height * (value / max)
            canvas.drawRoundRect(RectF(left, top, left + barWidth, height.toFloat()), 8f, 8f, paint)
        }
    }

    private fun drawLine(canvas: Canvas) {
        if (values.size < 2) return
        paint.color = color
        paint.strokeWidth = 5f
        val max = values.maxOrNull() ?: 1f
        val min = values.minOrNull() ?: 0f
        val range = (max - min).takeIf { it > 0f } ?: 1f
        val step = width.toFloat() / (values.size - 1)
        val path = Path()
        values.forEachIndexed { index, value ->
            val x = index * step
            val y = height - (value - min) / range * height
            if (index == 0) path.moveTo(x, y) else path.lineTo(x, y)
            paint.style = Paint.Style.FILL
            canvas.drawCircle(x, y, 6f, paint)
        }
        paint.style = Paint.Style.STROKE
        canvas.drawPath(path, paint)
    }

    private fun drawPie(canvas: Canvas) {
        val total = values.sum().takeIf { it > 0f } ?: return
        val diameter = minOf(width, height).toFloat()
        val left = (width - diameter) / 2
        val top = (height - diameter) / 2
        val oval = RectF(left, top, left + diameter, top + diameter)
        paint.style = Paint.Style.FILL
        var start = -90f
        values.forEachIndexed { index, value ->
            paint.color = palette[index % palette.size]
            val sweep = value / total * 360f
            canvas.drawArc(oval, start, sweep, true, paint)
            start += sweep
        }
    }
}
'''},
    ),
    Feature(
        key="calendar_view", name="Calendario mensal", category=PRO,
        description="Grade de calendario com selecao de dia. Usado pelo bloco 'Calendario'.",
        files_compose={"ui/components/MonthCalendar.kt": r'''package %PKG%.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import java.text.SimpleDateFormat
import java.util.Calendar
import java.util.Locale

/** Calendario de um mes com navegacao e dia selecionado. Devolve a data em dd/MM/yyyy. */
@Composable
fun MonthCalendar(onDateSelected: (String) -> Unit = {}) {
    var offset by remember { mutableIntStateOf(0) }
    var selected by remember { mutableStateOf<Int?>(null) }
    val calendar = Calendar.getInstance().apply {
        add(Calendar.MONTH, offset)
        set(Calendar.DAY_OF_MONTH, 1)
    }
    val month = calendar.get(Calendar.MONTH)
    val year = calendar.get(Calendar.YEAR)
    val firstWeekday = calendar.get(Calendar.DAY_OF_WEEK) - 1
    val days = calendar.getActualMaximum(Calendar.DAY_OF_MONTH)
    val title = SimpleDateFormat("MMMM yyyy", Locale.getDefault()).format(calendar.time)

    Column(modifier = Modifier.fillMaxWidth()) {
        Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.fillMaxWidth()) {
            TextButton(onClick = { offset--; selected = null }) { Text("<") }
            Text(title, style = MaterialTheme.typography.titleMedium, modifier = Modifier.weight(1f))
            TextButton(onClick = { offset++; selected = null }) { Text(">") }
        }
        Row(modifier = Modifier.fillMaxWidth()) {
            listOf("D", "S", "T", "Q", "Q", "S", "S").forEach {
                Text(it, modifier = Modifier.weight(1f), fontWeight = FontWeight.Bold)
            }
        }
        val cells = firstWeekday + days
        val rows = (cells + 6) / 7
        for (row in 0 until rows) {
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceEvenly) {
                for (column in 0 until 7) {
                    val day = row * 7 + column - firstWeekday + 1
                    Box(
                        contentAlignment = Alignment.Center,
                        modifier = Modifier
                            .weight(1f)
                            .aspectRatio(1f)
                            .background(
                                if (day == selected) MaterialTheme.colorScheme.primary else Color.Transparent,
                                CircleShape
                            )
                            .clickable(enabled = day in 1..days) {
                                selected = day
                                onDateSelected("%02d/%02d/%04d".format(day, month + 1, year))
                            }
                    ) {
                        if (day in 1..days) {
                            Text(
                                day.toString(),
                                color = if (day == selected) MaterialTheme.colorScheme.onPrimary
                                else MaterialTheme.colorScheme.onSurface
                            )
                        }
                    }
                }
            }
        }
    }
}
'''},
    ),
    Feature(
        key="pull_to_refresh", name="Puxar para atualizar", category=PRO,
        description="Gesto de arrastar para baixo que recarrega as listas da tela.",
        libs_views=["swiperefresh"], flags=["pull_refresh"],
    ),
    Feature(
        key="event_log", name="Registro de eventos local", category=PRO,
        description="Grava eventos de uso em arquivo local (analytics offline, sem servidores).",
        files={"features/EventLogger.kt": r'''package %PKG%.features

import android.content.Context
import java.io.File
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/** Registra eventos em um arquivo de texto na pasta privada do app. */
object EventLogger {

    private const val FILE = "events.log"
    private const val MAX_BYTES = 512 * 1024

    @Synchronized
    fun log(context: Context, event: String, detail: String = "") {
        val file = File(context.filesDir, FILE)
        if (file.length() > MAX_BYTES) file.delete()
        val time = SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.US).format(Date())
        file.appendText("$time\t$event\t$detail\n")
    }

    fun read(context: Context): List<String> =
        File(context.filesDir, FILE).takeIf { it.exists() }?.readLines() ?: emptyList()

    fun clear(context: Context) {
        File(context.filesDir, FILE).delete()
    }
}
'''},
    ),
    Feature(
        key="crash_logger", name="Registro de falhas local", category=PRO,
        description="Salva o stack trace de falhas em arquivo para analise posterior.",
        app_init=["CrashLogger.install(this)"],
        files={"features/CrashLogger.kt": r'''package %PKG%.features

import android.content.Context
import java.io.File
import java.io.PrintWriter
import java.io.StringWriter

/** Captura excecoes nao tratadas e grava em crash.log antes de encerrar o app. */
object CrashLogger {

    fun install(context: Context) {
        val appContext = context.applicationContext
        val previous = Thread.getDefaultUncaughtExceptionHandler()
        Thread.setDefaultUncaughtExceptionHandler { thread, error ->
            try {
                val writer = StringWriter()
                error.printStackTrace(PrintWriter(writer))
                File(appContext.filesDir, "crash.log").appendText(
                    "---- ${System.currentTimeMillis()} (${thread.name})\n$writer\n"
                )
            } catch (ignored: Exception) {
                // Nunca falhar dentro do tratador de falhas.
            }
            previous?.uncaughtException(thread, error)
        }
    }

    fun lastCrash(context: Context): String? =
        File(context.filesDir, "crash.log").takeIf { it.exists() }?.readText()?.takeLast(4000)
}
'''},
    ),
    Feature(
        key="timber", name="Logs com Timber", category=PRO,
        description="Logs organizados apenas em builds de debug.",
        libs=["timber"], app_init=["if (BuildConfig.DEBUG) timber.log.Timber.plant(timber.log.Timber.DebugTree())"],
    ),
    Feature(
        key="webview_bridge", name="Ponte JavaScript para WebView", category=PRO,
        description="Permite que paginas web dentro do app chamem funcoes Kotlin (window.App.*).",
        files={"features/JsBridge.kt": r'''package %PKG%.features

import android.content.Context
import android.webkit.JavascriptInterface
import android.widget.Toast

/** Funcoes expostas ao JavaScript como window.App. Use apenas com conteudo confiavel. */
class JsBridge(private val context: Context) {

    @JavascriptInterface
    fun toast(message: String) {
        Toast.makeText(context, message, Toast.LENGTH_SHORT).show()
    }

    @JavascriptInterface
    fun appVersion(): String = try {
        @Suppress("DEPRECATION")
        context.packageManager.getPackageInfo(context.packageName, 0).versionName ?: ""
    } catch (e: Exception) {
        ""
    }
}
'''},
    ),
    Feature(
        key="onboarding_state", name="Controle de onboarding", category=PRO,
        description="Lembra se o usuario ja viu a apresentacao inicial. Habilita a acao 'Concluir onboarding'.",
        requires=["datastore"],
        files={"features/OnboardingState.kt": r'''package %PKG%.features

import android.content.Context
import %PKG%.data.local.PreferencesStore
import kotlinx.coroutines.flow.first

/** Marca o onboarding como concluido. */
object OnboardingState {

    private const val KEY = "onboarding_done"

    suspend fun isDone(context: Context) = PreferencesStore(context).getBoolean(KEY).first()

    suspend fun complete(context: Context) = PreferencesStore(context).putBoolean(KEY, true)

    suspend fun reset(context: Context) = PreferencesStore(context).putBoolean(KEY, false)
}
'''},
    ),
    Feature(
        key="ui_tests", name="Testes instrumentados de interface", category=PRO,
        description="Gera um teste de interface que abre o app e verifica a tela inicial.",
        flags=["ui_tests"],
    ),
]
