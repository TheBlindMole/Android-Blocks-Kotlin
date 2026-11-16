"""Funcionalidades adicionadas na versao 1.1.

Ficam em um modulo proprio para facilitar a leitura, mas cada uma usa as
mesmas categorias das demais e aparece misturada a elas no catalogo.
"""

from .base import Feature

SYS = "Sistema e dispositivo"
NET = "Rede e APIs"
DATA = "Dados e armazenamento"
MEDIA = "Midia e camera"
BG = "Notificacoes e segundo plano"
SEC = "Seguranca e autenticacao"
UI = "Produtividade e interface"


DOCUMENT_INFO = r'''package %PKG%.features

import android.content.Context
import android.content.Intent
import android.net.Uri
import android.provider.OpenableColumns

/** Informacoes e leitura de arquivos escolhidos pelo usuario (Uri content://). */
object DocumentInfo {

    /** Nome do arquivo como aparece para o usuario. */
    fun displayName(context: Context, uri: Uri): String {
        context.contentResolver.query(uri, arrayOf(OpenableColumns.DISPLAY_NAME), null, null, null)?.use { cursor ->
            if (cursor.moveToFirst()) {
                val index = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME)
                if (index >= 0) return cursor.getString(index) ?: "arquivo"
            }
        }
        return uri.lastPathSegment ?: "arquivo"
    }

    /** Tamanho em bytes, ou -1 quando o provedor nao informa. */
    fun sizeBytes(context: Context, uri: Uri): Long {
        context.contentResolver.query(uri, arrayOf(OpenableColumns.SIZE), null, null, null)?.use { cursor ->
            if (cursor.moveToFirst()) {
                val index = cursor.getColumnIndex(OpenableColumns.SIZE)
                if (index >= 0 && !cursor.isNull(index)) return cursor.getLong(index)
            }
        }
        return -1L
    }

    /** Le o conteudo como texto (use apenas para arquivos pequenos). */
    fun readText(context: Context, uri: Uri): String =
        context.contentResolver.openInputStream(uri)?.bufferedReader()?.use { it.readText() }.orEmpty()

    /** Mantem a permissao de leitura depois que o app reiniciar. */
    fun keepAccess(context: Context, uri: Uri) {
        try {
            context.contentResolver.takePersistableUriPermission(uri, Intent.FLAG_GRANT_READ_URI_PERMISSION)
        } catch (e: SecurityException) {
            // Alguns provedores nao oferecem permissao persistente; o acesso vale ate o app fechar.
        }
    }
}
'''


BUG_REPORTER = r'''package %PKG%.features

import android.app.Activity
import android.app.AlertDialog
import android.content.Context
import android.os.Build
import androidx.activity.ComponentActivity
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import kotlinx.coroutines.launch
import %PKG%.util.IntentHelper

/**
 * Relato de problemas: abre o app de e-mail ja preenchido com dados do aparelho.
 * Tambem pode ser disparado chacoalhando o celular (enableShake).
 */
object BugReporter {

    /** Endereco que recebe os relatos. Troque pelo e-mail da sua equipe. */
    var supportEmail: String = "suporte@exemplo.com"

    /** Resumo do aparelho e da versao do app, anexado ao final do e-mail. */
    fun deviceInfo(context: Context): String {
        val version = try {
            context.packageManager.getPackageInfo(context.packageName, 0).versionName ?: "?"
        } catch (e: Exception) {
            "?"
        }
        return buildString {
            appendLine("App: ${context.packageName} $version")
            appendLine("Aparelho: ${Build.MANUFACTURER} ${Build.MODEL}")
            appendLine("Android: ${Build.VERSION.RELEASE} (API ${Build.VERSION.SDK_INT})")
        }
    }

    /** Abre o e-mail de relato. */
    fun send(context: Context) {
        val body = "Descreva o que aconteceu:\n\n\n--- Informacoes tecnicas ---\n" + deviceInfo(context)
        IntentHelper.email(context, supportEmail, "Relato de problema", body)
    }

    /** Pergunta se o usuario quer relatar um problema sempre que o aparelho for chacoalhado. */
    fun enableShake(activity: ComponentActivity) {
        activity.lifecycleScope.launch {
            activity.repeatOnLifecycle(Lifecycle.State.RESUMED) {
                ShakeDetector.shakes(activity).collect { confirm(activity) }
            }
        }
    }

    private fun confirm(activity: Activity) {
        if (activity.isFinishing) return
        AlertDialog.Builder(activity)
            .setTitle("Relatar um problema?")
            .setMessage("Voce chacoalhou o aparelho. Deseja enviar um relato para a equipe do app?")
            .setPositiveButton("Relatar") { _, _ -> send(activity) }
            .setNegativeButton("Cancelar", null)
            .show()
    }
}
'''


SECURE_PREFS = r'''package %PKG%.features

import android.content.Context
import android.content.SharedPreferences

/**
 * Preferencias com valores criptografados pelo Android Keystore.
 * Use para tokens, PINs e outros dados sensiveis pequenos.
 */
class SecurePrefs(context: Context, name: String = "secure_prefs") {

    private val prefs: SharedPreferences = context.getSharedPreferences(name, Context.MODE_PRIVATE)

    fun putString(key: String, value: String) {
        prefs.edit().putString(key, CryptoHelper.encrypt(value)).apply()
    }

    /** Devolve [default] se a chave nao existir ou nao puder ser lida. */
    fun getString(key: String, default: String = ""): String {
        val stored = prefs.getString(key, null) ?: return default
        return try {
            CryptoHelper.decrypt(stored)
        } catch (e: Exception) {
            default
        }
    }

    fun putBoolean(key: String, value: Boolean) = putString(key, value.toString())

    fun getBoolean(key: String, default: Boolean = false): Boolean =
        getString(key, default.toString()).toBooleanStrictOrNull() ?: default

    fun contains(key: String): Boolean = prefs.contains(key)

    fun remove(key: String) {
        prefs.edit().remove(key).apply()
    }

    fun clear() {
        prefs.edit().clear().apply()
    }
}
'''


APP_LOCK = r'''package %PKG%.features

import android.os.SystemClock
import androidx.fragment.app.FragmentActivity
import androidx.lifecycle.DefaultLifecycleObserver
import androidx.lifecycle.LifecycleOwner

/**
 * Bloqueio do app: pede biometria (ou PIN do aparelho) ao abrir e ao voltar
 * do segundo plano depois de [timeoutMs]. Se o usuario cancelar, o app fecha.
 */
object AppLock {

    /** Tempo em segundo plano depois do qual o app volta a ser bloqueado. */
    var timeoutMs: Long = 30_000L

    /** Permite desligar o bloqueio, por exemplo por uma opcao nas configuracoes. */
    var enabled: Boolean = true

    private var startedActivities = 0
    private var backgroundAt = 0L
    private var unlocked = false
    private var authenticating = false

    /** Deve ser chamado no onCreate de cada Activity. */
    fun protect(activity: FragmentActivity) {
        activity.lifecycle.addObserver(object : DefaultLifecycleObserver {
            override fun onStart(owner: LifecycleOwner) {
                startedActivities++
                val away = SystemClock.elapsedRealtime() - backgroundAt
                if (startedActivities == 1 && unlocked && away > timeoutMs) unlocked = false
                if (enabled && !unlocked && !authenticating) {
                    activity.window.decorView.post { ask(activity) }
                }
            }

            override fun onStop(owner: LifecycleOwner) {
                startedActivities = (startedActivities - 1).coerceAtLeast(0)
                if (startedActivities == 0) backgroundAt = SystemClock.elapsedRealtime()
            }
        })
    }

    private fun ask(activity: FragmentActivity) {
        if (unlocked || authenticating || activity.isFinishing) return
        if (!BiometricHelper.canAuthenticate(activity)) {
            // Sem biometria nem bloqueio de tela configurado: nao ha como confirmar a identidade.
            unlocked = true
            return
        }
        authenticating = true
        BiometricHelper.authenticate(
            activity,
            title = "Desbloquear o app",
            onSuccess = {
                authenticating = false
                unlocked = true
            },
            onError = {
                authenticating = false
                activity.finishAffinity()
            }
        )
    }

    /** Bloqueia imediatamente (por exemplo, apos o logout). */
    fun lockNow() {
        unlocked = false
    }
}
'''


RATE_PROMPT = r'''package %PKG%.features

import android.app.Activity
import android.content.Context

/**
 * Pede a avaliacao do app no momento certo: so depois de [minLaunches] aberturas
 * e [minDays] dias de uso, e no maximo uma vez.
 */
object RatePrompt {

    var minLaunches = 5
    var minDays = 3

    private const val PREFS = "rate_prompt"
    private const val DAY_MS = 24L * 60 * 60 * 1000
    private var askedThisSession = false

    /** Regra pura, separada para facilitar testes. */
    fun shouldAsk(launches: Int, firstLaunchMs: Long, nowMs: Long, alreadyAsked: Boolean): Boolean {
        if (alreadyAsked || firstLaunchMs <= 0L) return false
        val days = (nowMs - firstLaunchMs) / DAY_MS
        return launches >= minLaunches && days >= minDays
    }

    /** Conta uma abertura do app. Chamado uma vez por processo na classe App. */
    fun countLaunch(context: Context) {
        val prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        val editor = prefs.edit().putInt("launches", prefs.getInt("launches", 0) + 1)
        if (prefs.getLong("first", 0L) == 0L) editor.putLong("first", System.currentTimeMillis())
        editor.apply()
    }

    /** Mostra o pedido de avaliacao se as condicoes forem atendidas. */
    fun maybeAsk(activity: Activity) {
        if (askedThisSession) return
        val prefs = activity.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        val ask = shouldAsk(
            prefs.getInt("launches", 0), prefs.getLong("first", 0L),
            System.currentTimeMillis(), prefs.getBoolean("asked", false)
        )
        if (!ask) return
        askedThisSession = true
        prefs.edit().putBoolean("asked", true).apply()
        activity.window.decorView.postDelayed({
            if (!activity.isFinishing) ReviewHelper.requestReview(activity)
        }, 2_000L)
    }
}
'''


WHATS_NEW = r'''package %PKG%.features

import android.app.Activity
import android.app.AlertDialog
import android.content.Context
import androidx.core.content.pm.PackageInfoCompat

/** Mostra as novidades uma unica vez depois de cada atualizacao do app. */
object WhatsNew {

    /** Novidades da versao atual. Atualize esta lista a cada lancamento. */
    val NOTES = listOf(
        "Visual renovado e mais rapido",
        "Novas opcoes nas configuracoes",
        "Correcoes de problemas relatados"
    )

    private var checked = false

    fun showIfUpdated(activity: Activity) {
        if (checked) return
        checked = true
        val prefs = activity.getSharedPreferences("whats_new", Context.MODE_PRIVATE)
        val current = try {
            PackageInfoCompat.getLongVersionCode(activity.packageManager.getPackageInfo(activity.packageName, 0))
        } catch (e: Exception) {
            return
        }
        val last = prefs.getLong("last_version", -1L)
        prefs.edit().putLong("last_version", current).apply()
        // Na primeira instalacao nao ha novidades a mostrar.
        if (last == -1L || last == current) return
        AlertDialog.Builder(activity)
            .setTitle("Novidades")
            .setMessage(NOTES.joinToString("\n") { "- $it" })
            .setPositiveButton("Entendi", null)
            .show()
    }
}
'''


APP_CONFIG = r'''package %PKG%.features

import android.content.Context
import org.json.JSONObject

/**
 * Configuracao do app lida de assets/app_config.json. Permite ligar e desligar
 * recursos e trocar textos sem mexer no codigo. [override] aceita um JSON
 * baixado de um servidor para sobrescrever os valores locais.
 */
object AppConfig {

    private var values = JSONObject()

    fun load(context: Context, fileName: String = "app_config.json") {
        values = try {
            JSONObject(context.assets.open(fileName).bufferedReader().use { it.readText() })
        } catch (e: Exception) {
            JSONObject()
        }
    }

    /** Mescla valores vindos de outra fonte (ex.: servidor) sobre os atuais. */
    fun override(json: String) {
        val extra = try {
            JSONObject(json)
        } catch (e: Exception) {
            return
        }
        extra.keys().forEach { key -> values.put(key, extra.get(key)) }
    }

    fun string(key: String, default: String = ""): String = values.optString(key, default)

    fun bool(key: String, default: Boolean = false): Boolean = values.optBoolean(key, default)

    fun int(key: String, default: Int = 0): Int = values.optInt(key, default)

    fun double(key: String, default: Double = 0.0): Double = values.optDouble(key, default)

    /** Le um interruptor do bloco "features" do JSON. */
    fun isEnabled(feature: String): Boolean = values.optJSONObject("features")?.optBoolean(feature, false) ?: false
}
'''

APP_CONFIG_JSON = '''{
  "support_email": "suporte@exemplo.com",
  "welcome_message": "Bem-vindo!",
  "maintenance": false,
  "min_version": 1,
  "features": {
    "novo_checkout": true,
    "modo_beta": false
  }
}
'''


A11Y = r'''package %PKG%.features

import android.content.Context
import android.provider.Settings
import android.view.View
import android.view.accessibility.AccessibilityManager
import androidx.core.graphics.ColorUtils

/** Atalhos de acessibilidade: leitor de tela, tamanho de fonte, animacoes e contraste. */
object A11y {

    /** True quando o TalkBack (ou outro leitor de tela) esta ativo. */
    fun isScreenReaderOn(context: Context): Boolean {
        val manager = context.getSystemService(Context.ACCESSIBILITY_SERVICE) as? AccessibilityManager ?: return false
        return manager.isEnabled && manager.isTouchExplorationEnabled
    }

    /** Escala de fonte escolhida pelo usuario (1.0 = padrao). */
    fun fontScale(context: Context): Float = context.resources.configuration.fontScale

    fun isLargeFont(context: Context): Boolean = fontScale(context) >= 1.3f

    /** True quando o usuario desligou as animacoes do sistema. */
    fun animationsDisabled(context: Context): Boolean =
        Settings.Global.getFloat(context.contentResolver, Settings.Global.ANIMATOR_DURATION_SCALE, 1f) == 0f

    /** Le um texto em voz alta pelo leitor de tela. */
    fun announce(view: View, text: String) {
        @Suppress("DEPRECATION")
        view.announceForAccessibility(text)
    }

    /** Razao de contraste entre duas cores (o WCAG recomenda no minimo 4.5 para texto). */
    fun contrastRatio(foreground: Int, background: Int): Double = ColorUtils.calculateContrast(foreground, background)
}
'''


UPLOADER = r'''package %PKG%.features

import android.content.Context
import android.net.Uri
import android.provider.OpenableColumns
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import java.util.concurrent.TimeUnit

/** Envia arquivos (fotos, PDFs, etc.) para um servidor em multipart/form-data. */
object FileUploader {

    private val client by lazy {
        OkHttpClient.Builder()
            .connectTimeout(30, TimeUnit.SECONDS)
            .writeTimeout(120, TimeUnit.SECONDS)
            .readTimeout(60, TimeUnit.SECONDS)
            .build()
    }

    /**
     * Envia o arquivo [uri] no campo [field]. [fields] sao campos de texto extras.
     * Devolve o corpo da resposta ou a falha.
     */
    suspend fun upload(
        context: Context,
        url: String,
        uri: Uri,
        field: String = "file",
        fields: Map<String, String> = emptyMap(),
        headers: Map<String, String> = emptyMap()
    ): Result<String> = withContext(Dispatchers.IO) {
        runCatching {
            val resolver = context.contentResolver
            val mime = resolver.getType(uri) ?: "application/octet-stream"
            val bytes = resolver.openInputStream(uri)?.use { it.readBytes() } ?: error("Arquivo nao encontrado")
            val body = MultipartBody.Builder().setType(MultipartBody.FORM).apply {
                fields.forEach { (key, value) -> addFormDataPart(key, value) }
                addFormDataPart(field, fileName(context, uri), bytes.toRequestBody(mime.toMediaTypeOrNull()))
            }.build()
            val request = Request.Builder().url(url).post(body).apply {
                headers.forEach { (key, value) -> header(key, value) }
            }.build()
            client.newCall(request).execute().use { response ->
                if (!response.isSuccessful) error("Falha no envio: HTTP ${response.code}")
                response.body?.string().orEmpty()
            }
        }
    }

    private fun fileName(context: Context, uri: Uri): String {
        context.contentResolver.query(uri, arrayOf(OpenableColumns.DISPLAY_NAME), null, null, null)?.use { cursor ->
            if (cursor.moveToFirst()) return cursor.getString(0) ?: "arquivo"
        }
        return uri.lastPathSegment ?: "arquivo"
    }
}
'''


SKELETON_COMPOSE = r'''package %PKG%.features

import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.unit.dp

/** Linhas cinzas pulsando enquanto a lista carrega (efeito "skeleton"). */
@Composable
fun SkeletonList(rows: Int = 4) {
    val transition = rememberInfiniteTransition(label = "skeleton")
    val alpha by transition.animateFloat(
        initialValue = 0.35f,
        targetValue = 0.9f,
        animationSpec = infiniteRepeatable(tween(800), RepeatMode.Reverse),
        label = "alpha"
    )
    val color = MaterialTheme.colorScheme.surfaceVariant
    Column(verticalArrangement = Arrangement.spacedBy(12.dp), modifier = Modifier.fillMaxWidth().alpha(alpha)) {
        repeat(rows) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Box(modifier = Modifier.size(56.dp).clip(RoundedCornerShape(12.dp)).background(color))
                Column(verticalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.weight(1f).padding(start = 12.dp)) {
                    Box(modifier = Modifier.fillMaxWidth(0.7f).height(14.dp).clip(RoundedCornerShape(4.dp)).background(color))
                    Box(modifier = Modifier.fillMaxWidth(0.4f).height(12.dp).clip(RoundedCornerShape(4.dp)).background(color))
                }
            }
        }
    }
}
'''


SKELETON_VIEWS = r'''package %PKG%.features

import android.animation.ValueAnimator
import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.RectF
import android.util.AttributeSet
import android.view.View

/** View com linhas cinzas pulsando enquanto a lista carrega (efeito "skeleton"). */
class SkeletonView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null
) : View(context, attrs) {

    var rows: Int = 4

    private val density = resources.displayMetrics.density
    private val paint = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = Color.rgb(220, 226, 233) }
    private val rect = RectF()
    private val animator = ValueAnimator.ofFloat(0.35f, 0.9f).apply {
        duration = 800
        repeatMode = ValueAnimator.REVERSE
        repeatCount = ValueAnimator.INFINITE
        addUpdateListener { alpha = it.animatedValue as Float }
    }

    override fun onMeasure(widthMeasureSpec: Int, heightMeasureSpec: Int) {
        val height = (rows * 68 * density).toInt()
        setMeasuredDimension(MeasureSpec.getSize(widthMeasureSpec), resolveSize(height, heightMeasureSpec))
    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        val radius = 8 * density
        for (row in 0 until rows) {
            val top = row * 68 * density
            rect.set(0f, top, 56 * density, top + 56 * density)
            canvas.drawRoundRect(rect, radius, radius, paint)
            val left = 68 * density
            rect.set(left, top + 10 * density, left + (width - left) * 0.7f, top + 24 * density)
            canvas.drawRoundRect(rect, radius / 2, radius / 2, paint)
            rect.set(left, top + 34 * density, left + (width - left) * 0.4f, top + 46 * density)
            canvas.drawRoundRect(rect, radius / 2, radius / 2, paint)
        }
    }

    override fun onAttachedToWindow() {
        super.onAttachedToWindow()
        animator.start()
    }

    override fun onDetachedFromWindow() {
        animator.cancel()
        super.onDetachedFromWindow()
    }
}
'''


IMAGE_SHARE = r'''package %PKG%.features

import android.content.ContentValues
import android.content.Context
import android.graphics.Bitmap
import android.os.Build
import android.os.Environment
import android.provider.MediaStore
import android.view.View
import androidx.core.view.drawToBitmap
import java.io.File

/** Compartilha e salva imagens: bitmaps, ou o "print" de qualquer View. */
object ImageShare {

    /** Compartilha um bitmap como PNG. */
    fun shareBitmap(context: Context, bitmap: Bitmap, fileName: String = "imagem.png") {
        val dir = File(context.cacheDir, "shared").apply { mkdirs() }
        val file = File(dir, fileName)
        file.outputStream().use { bitmap.compress(Bitmap.CompressFormat.PNG, 100, it) }
        FileShareHelper.share(context, file, "image/png")
    }

    /** Compartilha a imagem de uma View (por exemplo, um comprovante na tela). */
    fun shareView(view: View, fileName: String = "captura.png") {
        shareBitmap(view.context, view.drawToBitmap(), fileName)
    }

    /** Salva o bitmap na galeria (pasta Pictures do aparelho). Retorna true se deu certo. */
    fun saveToGallery(context: Context, bitmap: Bitmap, title: String = "imagem_${System.currentTimeMillis()}"): Boolean {
        return try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                val values = ContentValues().apply {
                    put(MediaStore.Images.Media.DISPLAY_NAME, "$title.png")
                    put(MediaStore.Images.Media.MIME_TYPE, "image/png")
                    put(MediaStore.Images.Media.RELATIVE_PATH, Environment.DIRECTORY_PICTURES)
                }
                val uri = context.contentResolver.insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, values) ?: return false
                context.contentResolver.openOutputStream(uri)?.use { bitmap.compress(Bitmap.CompressFormat.PNG, 100, it) }
                true
            } else {
                @Suppress("DEPRECATION")
                MediaStore.Images.Media.insertImage(context.contentResolver, bitmap, title, null) != null
            }
        } catch (e: Exception) {
            false
        }
    }
}
'''


DAILY_REMINDER = r'''package %PKG%.features

import android.content.Context
import androidx.work.CoroutineWorker
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.WorkerParameters
import androidx.work.workDataOf
import java.util.Calendar
import java.util.concurrent.TimeUnit

/** Worker que mostra a notificacao diaria. */
class DailyReminderWorker(context: Context, params: WorkerParameters) : CoroutineWorker(context, params) {
    override suspend fun doWork(): Result {
        NotificationHelper.show(
            applicationContext,
            inputData.getString("title") ?: "Lembrete",
            inputData.getString("text").orEmpty()
        )
        return Result.success()
    }
}

/** Lembrete diario em horario fixo (ex.: beber agua, estudar, tomar remedio). */
object DailyReminder {

    private const val WORK_NAME = "daily_reminder"

    /** Milissegundos de [nowMs] ate o proximo [hour]:[minute] (hoje ou amanha). */
    fun millisUntil(hour: Int, minute: Int, nowMs: Long = System.currentTimeMillis()): Long {
        val now = Calendar.getInstance().apply { timeInMillis = nowMs }
        val next = (now.clone() as Calendar).apply {
            set(Calendar.HOUR_OF_DAY, hour)
            set(Calendar.MINUTE, minute)
            set(Calendar.SECOND, 0)
            set(Calendar.MILLISECOND, 0)
            if (!after(now)) add(Calendar.DAY_OF_MONTH, 1)
        }
        return next.timeInMillis - nowMs
    }

    fun schedule(context: Context, hour: Int, minute: Int, title: String, text: String) {
        val request = PeriodicWorkRequestBuilder<DailyReminderWorker>(24, TimeUnit.HOURS)
            .setInitialDelay(millisUntil(hour, minute), TimeUnit.MILLISECONDS)
            .setInputData(workDataOf("title" to title, "text" to text))
            .build()
        WorkManager.getInstance(context).enqueueUniquePeriodicWork(WORK_NAME, ExistingPeriodicWorkPolicy.UPDATE, request)
    }

    fun cancel(context: Context) {
        WorkManager.getInstance(context).cancelUniqueWork(WORK_NAME)
    }
}
'''


OFFLINE_BANNER = r'''package %PKG%.features

import android.graphics.Color
import android.view.Gravity
import android.view.ViewGroup
import android.widget.FrameLayout
import android.widget.TextView
import androidx.activity.ComponentActivity
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.isVisible
import androidx.core.view.updatePadding
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import kotlinx.coroutines.launch

/** Faixa "Sem conexao" exibida automaticamente na parte de baixo de qualquer tela. */
object OfflineBanner {

    private const val TAG = "offline_banner"

    /** Texto exibido na faixa. */
    var message: String = "Sem conexao com a internet"

    fun attach(activity: ComponentActivity) {
        activity.lifecycleScope.launch {
            activity.repeatOnLifecycle(Lifecycle.State.STARTED) {
                ConnectivityObserver(activity).observe().collect { online ->
                    bannerFor(activity)?.isVisible = !online
                }
            }
        }
    }

    private fun bannerFor(activity: ComponentActivity): TextView? {
        val root = activity.findViewById<ViewGroup>(android.R.id.content) as? FrameLayout ?: return null
        root.findViewWithTag<TextView>(TAG)?.let { return it }
        val density = activity.resources.displayMetrics.density
        val pad = (8 * density).toInt()
        val banner = TextView(activity).apply {
            tag = TAG
            text = message
            gravity = Gravity.CENTER
            setTextColor(Color.WHITE)
            setBackgroundColor(Color.rgb(179, 38, 30))
            setPadding(pad, pad, pad, pad)
            elevation = 8 * density
            isVisible = false
        }
        root.addView(banner, FrameLayout.LayoutParams(
            FrameLayout.LayoutParams.MATCH_PARENT, FrameLayout.LayoutParams.WRAP_CONTENT, Gravity.BOTTOM))
        ViewCompat.setOnApplyWindowInsetsListener(banner) { view, insets ->
            val bars = insets.getInsets(WindowInsetsCompat.Type.systemBars())
            view.updatePadding(bottom = pad + bars.bottom)
            insets
        }
        ViewCompat.requestApplyInsets(banner)
        return banner
    }
}
'''


OFFLINE_STORE = r'''package %PKG%.features

import android.content.Context
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import %PKG%.data.model.ListItem
import java.io.File

/**
 * Guarda a ultima resposta de cada fonte de API em disco. O repositorio usa estes
 * dados quando a rede falha, entao as listas continuam aparecendo offline.
 */
object OfflineStore {

    private val gson = Gson()

    private fun file(context: Context, source: String): File {
        val dir = File(context.filesDir, "offline").apply { mkdirs() }
        return File(dir, source.replace(Regex("[^A-Za-z0-9_.-]"), "_") + ".json")
    }

    fun save(context: Context, source: String, items: List<ListItem>) {
        try {
            file(context, source).writeText(gson.toJson(items))
        } catch (e: Exception) {
            // Falha ao gravar o cache nao deve interromper o app.
        }
    }

    /** Ultimos itens salvos, ou null se nunca houve resposta com sucesso. */
    fun load(context: Context, source: String): List<ListItem>? {
        val target = file(context, source)
        if (!target.exists()) return null
        return try {
            val type = object : TypeToken<List<ListItem>>() {}.type
            gson.fromJson<List<ListItem>>(target.readText(), type)
        } catch (e: Exception) {
            null
        }
    }

    fun clear(context: Context) {
        File(context.filesDir, "offline").deleteRecursively()
    }
}
'''


FEATURES = [
    Feature(
        key="document_picker", name="Escolher arquivo (PDF, documentos)", category=MEDIA,
        description="Seletor de arquivos do sistema (Storage Access Framework), sem permissoes. "
                    "Habilita a acao 'Escolher arquivo'.",
        files={"features/DocumentInfo.kt": DOCUMENT_INFO},
        files_compose={"features/DocumentPicker.kt": r'''package %PKG%.features

import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.runtime.Composable
import androidx.compose.ui.platform.LocalContext

/** Retorna uma funcao que abre o seletor de arquivos. [mimeTypes] filtra os tipos aceitos. */
@Composable
fun rememberDocumentPicker(mimeTypes: Array<String> = arrayOf("*/*"), onResult: (Uri?) -> Unit): () -> Unit {
    val context = LocalContext.current
    val launcher = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
        if (uri != null) DocumentInfo.keepAccess(context, uri)
        onResult(uri)
    }
    return { launcher.launch(mimeTypes) }
}
'''},
        files_views={"features/DocumentPickerHelper.kt": r'''package %PKG%.features

import android.net.Uri
import androidx.activity.ComponentActivity
import androidx.activity.result.contract.ActivityResultContracts

/** Deve ser criado como propriedade da Activity (antes do onStart). */
class DocumentPickerHelper(
    private val activity: ComponentActivity,
    private val mimeTypes: Array<String> = arrayOf("*/*"),
    onResult: (Uri?) -> Unit
) {
    private val launcher = activity.registerForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
        if (uri != null) DocumentInfo.keepAccess(activity, uri)
        onResult(uri)
    }

    fun launch() {
        launcher.launch(mimeTypes)
    }
}
'''},
    ),
    Feature(
        key="bug_report", name="Relatar problema (chacoalhar ou botao)", category=SYS,
        description="Abre um e-mail de suporte com dados do aparelho. Chacoalhar o celular "
                    "tambem oferece o relato. Habilita a acao 'Relatar problema'.",
        requires=["shake_detector"],
        activity_init=["BugReporter.enableShake(this)"],
        files={"features/BugReporter.kt": BUG_REPORTER},
        notes="Troque BugReporter.supportEmail pelo e-mail da sua equipe.",
    ),
    Feature(
        key="secure_prefs", name="Preferencias criptografadas", category=SEC,
        description="Guarda tokens, PINs e dados sensiveis criptografados com o Android Keystore.",
        requires=["encryption"],
        files={"features/SecurePrefs.kt": SECURE_PREFS},
    ),
    Feature(
        key="app_lock", name="Bloqueio do app com biometria", category=SEC,
        description="Pede digital, rosto ou PIN ao abrir o app e ao voltar do segundo plano.",
        requires=["biometric"],
        activity_init=["AppLock.protect(this)"],
        files={"features/AppLock.kt": APP_LOCK},
        notes="O tempo de tolerancia fica em AppLock.timeoutMs (30 s por padrao).",
    ),
    Feature(
        key="rate_prompt", name="Pedir avaliacao no momento certo", category=SYS,
        description="Conta aberturas e dias de uso e so entao pede a avaliacao na Play Store, uma unica vez.",
        requires=["in_app_review"],
        app_init=["RatePrompt.countLaunch(this)"],
        activity_init=["RatePrompt.maybeAsk(this)"],
        files={"features/RatePrompt.kt": RATE_PROMPT},
    ),
    Feature(
        key="whats_new", name="Tela de novidades da versao", category=UI,
        description="Mostra uma janela com as novidades uma unica vez apos cada atualizacao.",
        activity_init=["WhatsNew.showIfUpdated(this)"],
        files={"features/WhatsNew.kt": WHATS_NEW},
        notes="Edite a lista WhatsNew.NOTES a cada lancamento.",
    ),
    Feature(
        key="app_config", name="Configuracao por JSON (assets)", category=DATA,
        description="Le assets/app_config.json para ligar recursos e trocar textos sem recompilar o codigo.",
        app_init=["AppConfig.load(this)"],
        files={"features/AppConfig.kt": APP_CONFIG},
        assets={"app_config.json": APP_CONFIG_JSON},
    ),
    Feature(
        key="accessibility", name="Acessibilidade (leitor de tela, fonte, contraste)", category=UI,
        description="Detecta TalkBack, fonte grande e animacoes desligadas; calcula contraste de cores.",
        files={"features/A11y.kt": A11Y},
    ),
    Feature(
        key="upload", name="Envio de arquivos (upload multipart)", category=NET,
        description="Envia fotos e documentos para um servidor com OkHttp (multipart/form-data).",
        requires=["network"],
        files={"features/FileUploader.kt": UPLOADER},
    ),
    Feature(
        key="skeleton_loading", name="Carregamento com skeleton", category=UI,
        description="Mostra linhas cinzas animadas no lugar das listas enquanto os dados carregam.",
        flags=["skeleton"],
        files_compose={"features/Skeleton.kt": SKELETON_COMPOSE},
        files_views={"features/SkeletonView.kt": SKELETON_VIEWS},
    ),
    Feature(
        key="image_share", name="Compartilhar e salvar imagens", category=MEDIA,
        description="Compartilha bitmaps ou o print de uma tela e salva imagens na galeria.",
        requires=["file_provider"],
        permissions=["android.permission.WRITE_EXTERNAL_STORAGE"],
        files={"features/ImageShare.kt": IMAGE_SHARE},
    ),
    Feature(
        key="material_you", name="Cores dinamicas (Material You)", category=UI,
        description="No Android 12 ou superior o app usa as cores do papel de parede do usuario.",
        flags=["dynamic_color"],
        notes="Em aparelhos mais antigos a paleta do projeto continua sendo usada.",
    ),
    Feature(
        key="daily_reminder", name="Lembrete diario em horario fixo", category=BG,
        description="Notificacao todos os dias no mesmo horario (WorkManager), mesmo com o app fechado.",
        libs=["work"], requires=["notifications"],
        files={"features/DailyReminder.kt": DAILY_REMINDER},
    ),
    Feature(
        key="offline_banner", name="Aviso de sem conexao", category=NET,
        description="Exibe uma faixa 'Sem conexao' em todas as telas quando a internet cai.",
        requires=["connectivity"],
        activity_init=["OfflineBanner.attach(this)"],
        files={"features/OfflineBanner.kt": OFFLINE_BANNER},
    ),
    Feature(
        key="offline_cache", name="Listas offline (ultima resposta da API)", category=DATA,
        description="Salva a ultima resposta de cada API e a usa quando nao houver internet.",
        requires=["network"], flags=["offline_cache"],
        files={"features/OfflineStore.kt": OFFLINE_STORE},
        notes="Atua nas listas com fonte 'api:'; cadastre uma API para aproveitar o cache offline.",
    ),
]
