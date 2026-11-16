"""Funcionalidades de sistema, dispositivo e integracao com o Android."""

from .base import Feature

CAT = "Sistema e dispositivo"

FEATURES = [
    Feature(
        key="intents", name="Intents comuns (compartilhar, ligar, e-mail, SMS, abrir link)",
        category=CAT, builtin=True,
        description="Ja incluido em todo projeto (util/IntentHelper.kt). Habilita as acoes "
                    "de compartilhar, ligar, enviar e-mail, SMS, abrir links e mapas.",
    ),
    Feature(
        key="vibration", name="Vibracao e feedback tatil", category=CAT,
        description="Vibracao simples e por padrao, compativel com todas as versoes do Android.",
        permissions=["android.permission.VIBRATE"],
        files={"features/VibrationHelper.kt": '''package %PKG%.features

import android.content.Context
import android.os.Build
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager

/** Utilitario para vibracao e feedback tatil. */
object VibrationHelper {

    /** Vibra o aparelho durante o tempo informado, em milissegundos. */
    fun vibrate(context: Context, durationMs: Long = 60L) {
        val vibrator = vibrator(context) ?: return
        if (!vibrator.hasVibrator()) return
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            vibrator.vibrate(VibrationEffect.createOneShot(durationMs, VibrationEffect.DEFAULT_AMPLITUDE))
        } else {
            @Suppress("DEPRECATION")
            vibrator.vibrate(durationMs)
        }
    }

    /** Executa um padrao de vibracao: pausa, vibra, pausa, vibra... */
    fun pattern(context: Context, timings: LongArray = longArrayOf(0, 80, 60, 80)) {
        val vibrator = vibrator(context) ?: return
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            vibrator.vibrate(VibrationEffect.createWaveform(timings, -1))
        } else {
            @Suppress("DEPRECATION")
            vibrator.vibrate(timings, -1)
        }
    }

    // Obtem o servico de vibracao conforme a versao do sistema.
    private fun vibrator(context: Context): Vibrator? =
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            (context.getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as? VibratorManager)?.defaultVibrator
        } else {
            @Suppress("DEPRECATION")
            context.getSystemService(Context.VIBRATOR_SERVICE) as? Vibrator
        }
}
'''},
    ),
    Feature(
        key="clipboard", name="Area de transferencia", category=CAT,
        description="Copiar e colar textos usando o ClipboardManager.",
        files={"features/ClipboardHelper.kt": '''package %PKG%.features

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context

/** Operacoes de copiar e colar texto. */
object ClipboardHelper {

    /** Copia o texto para a area de transferencia. */
    fun copy(context: Context, text: String, label: String = "texto") {
        val manager = context.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
        manager.setPrimaryClip(ClipData.newPlainText(label, text))
    }

    /** Retorna o texto atual da area de transferencia, ou vazio. */
    fun paste(context: Context): String {
        val manager = context.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
        val clip = manager.primaryClip ?: return ""
        if (clip.itemCount == 0) return ""
        return clip.getItemAt(0).coerceToText(context)?.toString().orEmpty()
    }
}
'''},
    ),
    Feature(
        key="custom_tabs", name="Abrir links em Custom Tabs", category=CAT,
        description="Abre paginas web dentro do app com a barra do navegador (Chrome Custom Tabs).",
        libs=["browser"],
        files={"features/CustomTabsHelper.kt": '''package %PKG%.features

import android.content.Context
import android.content.Intent
import android.net.Uri
import androidx.browser.customtabs.CustomTabColorSchemeParams
import androidx.browser.customtabs.CustomTabsIntent

/** Abre URLs usando Custom Tabs, com fallback para o navegador padrao. */
object CustomTabsHelper {

    fun open(context: Context, url: String, toolbarColor: Int? = null) {
        val builder = CustomTabsIntent.Builder().setShowTitle(true)
        if (toolbarColor != null) {
            val params = CustomTabColorSchemeParams.Builder().setToolbarColor(toolbarColor).build()
            builder.setDefaultColorSchemeParams(params)
        }
        val tabs = builder.build()
        tabs.intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        try {
            tabs.launchUrl(context, Uri.parse(url))
        } catch (e: Exception) {
            val fallback = Intent(Intent.ACTION_VIEW, Uri.parse(url)).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            context.startActivity(fallback)
        }
    }
}
'''},
    ),
    Feature(
        key="device_info", name="Informacoes do dispositivo", category=CAT,
        description="Fabricante, modelo, versao do Android, versao do app, tela e idioma.",
        files={"features/DeviceInfoHelper.kt": '''package %PKG%.features

import android.content.Context
import android.os.Build
import java.util.Locale

/** Dados basicos do aparelho e do aplicativo. */
data class DeviceInfo(
    val manufacturer: String,
    val model: String,
    val androidVersion: String,
    val sdkInt: Int,
    val appVersion: String,
    val screenWidthDp: Int,
    val screenHeightDp: Int,
    val locale: String
) {
    /** Resumo legivel em varias linhas. */
    fun summary(): String = listOf(
        "Aparelho: $manufacturer $model",
        "Android: $androidVersion (API $sdkInt)",
        "App: $appVersion",
        "Tela: ${screenWidthDp}x${screenHeightDp} dp",
        "Idioma: $locale"
    ).joinToString("\\n")
}

object DeviceInfoHelper {

    /** Le as informacoes atuais do dispositivo. */
    fun read(context: Context): DeviceInfo {
        val config = context.resources.configuration
        val appVersion = try {
            @Suppress("DEPRECATION")
            context.packageManager.getPackageInfo(context.packageName, 0).versionName ?: "?"
        } catch (e: Exception) {
            "?"
        }
        return DeviceInfo(
            manufacturer = Build.MANUFACTURER.replaceFirstChar { it.titlecase(Locale.getDefault()) },
            model = Build.MODEL,
            androidVersion = Build.VERSION.RELEASE,
            sdkInt = Build.VERSION.SDK_INT,
            appVersion = appVersion,
            screenWidthDp = config.screenWidthDp,
            screenHeightDp = config.screenHeightDp,
            locale = Locale.getDefault().toLanguageTag()
        )
    }
}
'''},
    ),
    Feature(
        key="battery", name="Bateria", category=CAT,
        description="Nivel de bateria e estado de carregamento.",
        files={"features/BatteryHelper.kt": '''package %PKG%.features

import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.BatteryManager

/** Consulta o nivel e o estado da bateria. */
object BatteryHelper {

    /** Percentual de carga (0 a 100). */
    fun level(context: Context): Int {
        val manager = context.getSystemService(Context.BATTERY_SERVICE) as BatteryManager
        return manager.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY)
    }

    /** Indica se o aparelho esta carregando ou com carga completa. */
    fun isCharging(context: Context): Boolean {
        val intent = context.registerReceiver(null, IntentFilter(Intent.ACTION_BATTERY_CHANGED))
        val status = intent?.getIntExtra(BatteryManager.EXTRA_STATUS, -1) ?: -1
        return status == BatteryManager.BATTERY_STATUS_CHARGING || status == BatteryManager.BATTERY_STATUS_FULL
    }

    /** Texto resumido para exibir ao usuario. */
    fun summary(context: Context): String {
        val state = if (isCharging(context)) "carregando" else "na bateria"
        return "Bateria: ${level(context)}% ($state)"
    }
}
'''},
    ),
    Feature(
        key="connectivity", name="Monitor de conexao", category=CAT,
        description="Verifica se ha internet e observa mudancas de rede em tempo real (Flow).",
        permissions=["android.permission.ACCESS_NETWORK_STATE"],
        files={"features/ConnectivityObserver.kt": '''package %PKG%.features

import android.content.Context
import android.net.ConnectivityManager
import android.net.Network
import android.net.NetworkCapabilities
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow
import kotlinx.coroutines.flow.distinctUntilChanged

/** Observa o estado da conexao com a internet. */
class ConnectivityObserver(context: Context) {

    private val manager = context.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager

    /** Retorna true quando ha uma rede ativa com acesso a internet. */
    fun isOnline(): Boolean {
        val capabilities = manager.getNetworkCapabilities(manager.activeNetwork) ?: return false
        return capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)
    }

    /** Indica se a conexao atual e via Wi-Fi. */
    fun isWifi(): Boolean {
        val capabilities = manager.getNetworkCapabilities(manager.activeNetwork) ?: return false
        return capabilities.hasTransport(NetworkCapabilities.TRANSPORT_WIFI)
    }

    /** Emite true/false sempre que a conectividade mudar. */
    fun observe(): Flow<Boolean> = callbackFlow {
        val callback = object : ConnectivityManager.NetworkCallback() {
            override fun onAvailable(network: Network) {
                trySend(true)
            }

            override fun onLost(network: Network) {
                trySend(isOnline())
            }
        }
        trySend(isOnline())
        manager.registerDefaultNetworkCallback(callback)
        awaitClose { manager.unregisterNetworkCallback(callback) }
    }.distinctUntilChanged()
}
'''},
    ),
    Feature(
        key="flashlight", name="Lanterna", category=CAT,
        description="Liga e desliga o flash da camera como lanterna (sem permissao extra).",
        files={"features/FlashlightHelper.kt": '''package %PKG%.features

import android.content.Context
import android.hardware.camera2.CameraAccessException
import android.hardware.camera2.CameraCharacteristics
import android.hardware.camera2.CameraManager

/** Controle da lanterna do aparelho. */
object FlashlightHelper {

    var isOn: Boolean = false
        private set

    /** Alterna o estado da lanterna e retorna o novo estado. */
    fun toggle(context: Context): Boolean {
        set(context, !isOn)
        return isOn
    }

    /** Define o estado da lanterna. */
    fun set(context: Context, on: Boolean) {
        val manager = context.getSystemService(Context.CAMERA_SERVICE) as CameraManager
        val cameraId = manager.cameraIdList.firstOrNull { id ->
            manager.getCameraCharacteristics(id).get(CameraCharacteristics.FLASH_INFO_AVAILABLE) == true
        } ?: return
        try {
            manager.setTorchMode(cameraId, on)
            isOn = on
        } catch (e: CameraAccessException) {
            isOn = false
        }
    }
}
'''},
    ),
    Feature(
        key="window_control", name="Controle de tela (brilho, manter ligada, orientacao)", category=CAT,
        description="Manter a tela ligada, ajustar brilho da janela e travar orientacao.",
        files={"features/WindowHelper.kt": '''package %PKG%.features

import android.app.Activity
import android.content.pm.ActivityInfo
import android.view.WindowManager

/** Ajustes da janela da Activity atual. */
object WindowHelper {

    /** Impede que a tela apague enquanto a Activity estiver visivel. */
    fun keepScreenOn(activity: Activity, on: Boolean) {
        if (on) {
            activity.window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        } else {
            activity.window.clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        }
    }

    /** Bloqueia capturas de tela e gravacao (FLAG_SECURE). */
    fun setSecure(activity: Activity, secure: Boolean) {
        if (secure) {
            activity.window.addFlags(WindowManager.LayoutParams.FLAG_SECURE)
        } else {
            activity.window.clearFlags(WindowManager.LayoutParams.FLAG_SECURE)
        }
    }

    /** Ajusta o brilho apenas desta janela (0.01 a 1.0). */
    fun setBrightness(activity: Activity, value: Float) {
        val params = activity.window.attributes
        params.screenBrightness = value.coerceIn(0.01f, 1f)
        activity.window.attributes = params
    }

    /** Trava a orientacao em retrato ou paisagem. */
    fun lockOrientation(activity: Activity, portrait: Boolean) {
        activity.requestedOrientation = if (portrait) {
            ActivityInfo.SCREEN_ORIENTATION_PORTRAIT
        } else {
            ActivityInfo.SCREEN_ORIENTATION_LANDSCAPE
        }
    }
}
'''},
    ),
    Feature(
        key="keep_screen_on", name="Manter tela sempre ligada", category=CAT,
        description="Aplica FLAG_KEEP_SCREEN_ON automaticamente na abertura do app.",
        requires=["window_control"],
        activity_init=["WindowHelper.keepScreenOn(this, true)"],
    ),
    Feature(
        key="dark_mode_toggle", name="Alternar tema claro/escuro", category=CAT,
        description="Preferencia de tema salva no DataStore e aplicada ao app inteiro. "
                    "Habilita a acao 'Alternar tema'.",
        requires=["datastore"],
        flags=["theme_toggle"],
        files={"features/ThemePreferences.kt": '''package %PKG%.features

import android.content.Context
import %PKG%.data.local.PreferencesStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first

/** Guarda a escolha de tema do usuario: "system", "light" ou "dark". */
object ThemePreferences {

    private const val KEY = "theme_mode"

    fun modeFlow(context: Context): Flow<String> = PreferencesStore(context).getString(KEY, "system")

    suspend fun setMode(context: Context, mode: String) {
        PreferencesStore(context).putString(KEY, mode)
    }

    /** Alterna entre claro e escuro. */
    suspend fun toggle(context: Context) {
        val current = modeFlow(context).first()
        setMode(context, if (current == "dark") "light" else "dark")
    }
}
'''},
    ),
    Feature(
        key="localization", name="Troca de idioma no app", category=CAT,
        description="Idioma por aplicativo (Android 13+) com locales_config.xml e fallback.",
        libs=["appcompat"],
        flags=["locale_config"],
        files={"features/LocaleHelper.kt": '''package %PKG%.features

import android.app.LocaleManager
import android.content.Context
import android.os.Build
import android.os.LocaleList
import androidx.appcompat.app.AppCompatDelegate
import androidx.core.os.LocaleListCompat

/** Define o idioma do aplicativo, independente do idioma do sistema. */
object LocaleHelper {

    /** Aplica o idioma informado (ex.: "pt-BR", "en"). Vazio volta ao padrao do sistema. */
    fun setLanguage(context: Context, languageTag: String) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            val manager = context.getSystemService(LocaleManager::class.java)
            manager.applicationLocales = if (languageTag.isBlank()) {
                LocaleList.getEmptyLocaleList()
            } else {
                LocaleList.forLanguageTags(languageTag)
            }
        } else {
            AppCompatDelegate.setApplicationLocales(LocaleListCompat.forLanguageTags(languageTag))
        }
    }

    /** Idioma atualmente aplicado ao app. */
    fun currentLanguage(): String = AppCompatDelegate.getApplicationLocales().toLanguageTags()
}
'''},
    ),
    Feature(
        key="deep_links", name="Deep links", category=CAT,
        description="Abre telas especificas a partir de links no formato app://tela?itemId=1.",
        flags=["deep_links"],
        files={"features/DeepLinkParser.kt": '''package %PKG%.features

import android.net.Uri

/** Converte um Uri de deep link em uma rota interna do app. */
object DeepLinkParser {

    /**
     * Exemplo: meuapp://detalhe?itemId=10 retorna "detalhe?itemId=10".
     * Retorna null se o Uri nao for valido.
     */
    fun routeFrom(uri: Uri?): String? {
        if (uri == null) return null
        val screen = uri.host?.takeIf { it.isNotBlank() } ?: return null
        val itemId = uri.getQueryParameter("itemId")
        return if (itemId.isNullOrBlank()) screen else "$screen?itemId=${Uri.encode(itemId)}"
    }
}
'''},
    ),
    Feature(
        key="app_shortcuts", name="Atalhos do icone (App Shortcuts)", category=CAT,
        description="Atalhos dinamicos ao pressionar o icone do app, apontando para deep links.",
        requires=["deep_links"],
        files={"features/ShortcutHelper.kt": '''package %PKG%.features

import android.content.Context
import android.content.Intent
import android.net.Uri
import androidx.core.content.pm.ShortcutInfoCompat
import androidx.core.content.pm.ShortcutManagerCompat
import androidx.core.graphics.drawable.IconCompat

/** Publica atalhos dinamicos no icone do aplicativo. */
object ShortcutHelper {

    /**
     * Cria um atalho que abre o deep link informado.
     * Exemplo: publish(context, "carrinho", "Carrinho", "meuapp://carrinho")
     */
    fun publish(context: Context, id: String, label: String, deepLink: String) {
        val intent = Intent(Intent.ACTION_VIEW, Uri.parse(deepLink)).setPackage(context.packageName)
        val shortcut = ShortcutInfoCompat.Builder(context, id)
            .setShortLabel(label)
            .setIcon(IconCompat.createWithResource(context, context.applicationInfo.icon))
            .setIntent(intent)
            .build()
        ShortcutManagerCompat.pushDynamicShortcut(context, shortcut)
    }

    fun removeAll(context: Context) {
        ShortcutManagerCompat.removeAllDynamicShortcuts(context)
    }
}
'''},
    ),
    Feature(
        key="in_app_review", name="Avaliacao no app (Play In-App Review)", category=CAT,
        description="Abre o fluxo oficial de avaliacao da Google Play sem sair do app. "
                    "Habilita a acao 'Avaliar app'.",
        libs=["play_review"],
        files={"features/ReviewHelper.kt": '''package %PKG%.features

import android.app.Activity
import com.google.android.play.core.review.ReviewManagerFactory

/** Solicita a avaliacao do app pela Google Play. */
object ReviewHelper {

    fun requestReview(activity: Activity) {
        val manager = ReviewManagerFactory.create(activity)
        manager.requestReviewFlow().addOnCompleteListener { task ->
            if (task.isSuccessful) {
                manager.launchReviewFlow(activity, task.result)
            }
        }
    }
}
'''},
    ),
    Feature(
        key="in_app_update", name="Atualizacao no app (Play In-App Update)", category=CAT,
        description="Verifica se ha versao nova na Google Play e oferece atualizacao flexivel.",
        libs=["play_update"],
        files={"features/UpdateHelper.kt": '''package %PKG%.features

import android.app.Activity
import com.google.android.play.core.appupdate.AppUpdateManagerFactory
import com.google.android.play.core.install.model.AppUpdateType
import com.google.android.play.core.install.model.UpdateAvailability

/** Verifica e inicia atualizacoes pela Google Play. */
object UpdateHelper {

    fun checkForUpdate(activity: Activity, requestCode: Int = 4201) {
        val manager = AppUpdateManagerFactory.create(activity)
        manager.appUpdateInfo.addOnSuccessListener { info ->
            val available = info.updateAvailability() == UpdateAvailability.UPDATE_AVAILABLE
            if (available && info.isUpdateTypeAllowed(AppUpdateType.FLEXIBLE)) {
                try {
                    @Suppress("DEPRECATION")
                    manager.startUpdateFlowForResult(info, AppUpdateType.FLEXIBLE, activity, requestCode)
                } catch (e: Exception) {
                    // Falha ao abrir o fluxo de atualizacao: ignorado com seguranca.
                }
            }
        }
    }
}
'''},
    ),
    Feature(
        key="splash_screen", name="Splash screen (API oficial)", category=CAT,
        description="Tela de abertura com a SplashScreen API (core-splashscreen), compativel desde o Android 6.",
        libs=["splashscreen"],
        flags=["splash"],
    ),
    Feature(
        key="sound_effects", name="Sons curtos (beep e tons)", category=CAT,
        description="Emite sons de confirmacao e alerta com ToneGenerator, sem arquivos de audio.",
        files={"features/SoundHelper.kt": '''package %PKG%.features

import android.media.AudioManager
import android.media.ToneGenerator

/** Sons curtos de feedback. */
object SoundHelper {

    private val generator: ToneGenerator? by lazy {
        try {
            ToneGenerator(AudioManager.STREAM_NOTIFICATION, 80)
        } catch (e: RuntimeException) {
            null
        }
    }

    fun beep() {
        generator?.startTone(ToneGenerator.TONE_PROP_BEEP, 150)
    }

    fun success() {
        generator?.startTone(ToneGenerator.TONE_PROP_ACK, 200)
    }

    fun error() {
        generator?.startTone(ToneGenerator.TONE_PROP_NACK, 300)
    }
}
'''},
    ),
    Feature(
        key="screenshot", name="Capturar view como imagem", category=CAT,
        description="Gera um Bitmap de qualquer View para salvar ou compartilhar.",
        files={"features/ViewCapture.kt": '''package %PKG%.features

import android.content.Context
import android.graphics.Bitmap
import android.view.View
import androidx.core.view.drawToBitmap
import java.io.File
import java.io.FileOutputStream

/** Captura o conteudo de uma View. */
object ViewCapture {

    fun capture(view: View): Bitmap = view.drawToBitmap()

    /** Salva o bitmap como PNG na pasta de cache e retorna o arquivo. */
    fun saveToCache(context: Context, bitmap: Bitmap, name: String = "captura.png"): File {
        val file = File(context.cacheDir, name)
        FileOutputStream(file).use { out -> bitmap.compress(Bitmap.CompressFormat.PNG, 100, out) }
        return file
    }
}
'''},
    ),
    Feature(
        key="home_widget", name="Widget na tela inicial", category=CAT,
        description="Widget classico (AppWidget) mostrando o nome do app e a hora da ultima atualizacao.",
        flags=["home_widget"],
        manifest_app='''        <receiver
            android:name=".features.AppWidget"
            android:exported="false">
            <intent-filter>
                <action android:name="android.appwidget.action.APPWIDGET_UPDATE" />
            </intent-filter>
            <meta-data
                android:name="android.appwidget.provider"
                android:resource="@xml/app_widget_info" />
        </receiver>''',
        res={
            "xml/app_widget_info.xml": '''<?xml version="1.0" encoding="utf-8"?>
<!-- Configuracao do widget da tela inicial. -->
<appwidget-provider xmlns:android="http://schemas.android.com/apk/res/android"
    android:initialLayout="@layout/widget_app"
    android:minWidth="180dp"
    android:minHeight="60dp"
    android:resizeMode="horizontal|vertical"
    android:updatePeriodMillis="1800000"
    android:widgetCategory="home_screen" />
''',
            "layout/widget_app.xml": '''<?xml version="1.0" encoding="utf-8"?>
<!-- Layout do widget: titulo e texto de atualizacao. -->
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:id="@+id/widget_root"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:background="@color/brand_primary"
    android:orientation="vertical"
    android:padding="12dp">

    <TextView
        android:id="@+id/widget_title"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="@string/app_name"
        android:textColor="#FFFFFF"
        android:textSize="16sp"
        android:textStyle="bold" />

    <TextView
        android:id="@+id/widget_text"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:textColor="#DDFFFFFF"
        android:textSize="13sp" />
</LinearLayout>
''',
        },
        files={"features/AppWidget.kt": '''package %PKG%.features

import android.app.PendingIntent
import android.appwidget.AppWidgetManager
import android.appwidget.AppWidgetProvider
import android.content.Context
import android.widget.RemoteViews
import %PKG%.R
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/** Widget da tela inicial que abre o app ao ser tocado. */
class AppWidget : AppWidgetProvider() {

    override fun onUpdate(context: Context, manager: AppWidgetManager, appWidgetIds: IntArray) {
        val time = SimpleDateFormat("HH:mm", Locale.getDefault()).format(Date())
        val launch = context.packageManager.getLaunchIntentForPackage(context.packageName)
        val pending = PendingIntent.getActivity(
            context, 0, launch, PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        appWidgetIds.forEach { id ->
            val views = RemoteViews(context.packageName, R.layout.widget_app)
            views.setTextViewText(R.id.widget_text, "Atualizado as $time")
            views.setOnClickPendingIntent(R.id.widget_root, pending)
            manager.updateAppWidget(id, views)
        }
    }
}
'''},
    ),
]
