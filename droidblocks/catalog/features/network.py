"""Funcionalidades de rede, APIs e servicos em nuvem."""

from .base import Feature

CAT = "Rede e APIs"
FB = "Firebase (nuvem)"

FIREBASE_NOTE = ("Requer o arquivo app/google-services.json baixado do console do Firebase. "
                 "Sem ele o build falha.")

FEATURES = [
    Feature(
        key="network", name="Cliente HTTP (Retrofit + OkHttp + Gson)", category=CAT,
        description="Base para consumir APIs REST. Ativada automaticamente ao adicionar uma API.",
        libs=["retrofit", "retrofit_gson", "okhttp", "gson"],
        permissions=["android.permission.INTERNET", "android.permission.ACCESS_NETWORK_STATE"],
    ),
    Feature(
        key="http_logging", name="Log de requisicoes HTTP", category=CAT,
        description="Mostra requisicoes e respostas no Logcat em builds de debug.",
        libs=["okhttp_logging"], requires=["network"], flags=["http_logging"],
    ),
    Feature(
        key="http_cache", name="Cache HTTP offline", category=CAT,
        description="Cache em disco de 10 MB para respostas HTTP, reduz consumo de dados.",
        requires=["network"], flags=["http_cache"],
    ),
    Feature(
        key="auth_token", name="Token de autenticacao (Bearer)", category=CAT,
        description="Guarda o token no DataStore e envia automaticamente no cabecalho Authorization.",
        requires=["network", "datastore"], flags=["auth_token"],
        app_init=["TokenStore.preload(this)"],
        files={"features/TokenStore.kt": r'''package %PKG%.features

import android.content.Context
import %PKG%.data.local.PreferencesStore
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch
import okhttp3.Interceptor
import okhttp3.Response

/** Armazena o token de acesso em memoria e no DataStore. */
object TokenStore {

    private const val KEY = "auth_token"

    @Volatile
    var token: String? = null
        private set

    /** Carrega o token salvo para a memoria ao iniciar o app. */
    fun preload(context: Context) {
        CoroutineScope(SupervisorJob() + Dispatchers.IO).launch {
            token = PreferencesStore(context).getString(KEY, "").first().ifBlank { null }
        }
    }

    suspend fun save(context: Context, value: String) {
        token = value
        PreferencesStore(context).putString(KEY, value)
    }

    suspend fun clear(context: Context) {
        token = null
        PreferencesStore(context).putString(KEY, "")
    }
}

/** Adiciona o cabecalho Authorization quando houver token. */
class AuthInterceptor : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val current = TokenStore.token
        val request = if (current.isNullOrBlank()) {
            chain.request()
        } else {
            chain.request().newBuilder().header("Authorization", "Bearer $current").build()
        }
        return chain.proceed(request)
    }
}
'''},
    ),
    Feature(
        key="download_manager", name="Download de arquivos", category=CAT,
        description="Baixa arquivos para a pasta Downloads usando o DownloadManager do sistema.",
        permissions=["android.permission.INTERNET"],
        files={"features/DownloadHelper.kt": r'''package %PKG%.features

import android.app.DownloadManager
import android.content.Context
import android.net.Uri
import android.os.Environment

/** Inicia downloads gerenciados pelo sistema, com notificacao de progresso. */
object DownloadHelper {

    /** Enfileira o download e retorna o id para acompanhamento. */
    fun enqueue(context: Context, url: String, fileName: String, title: String = fileName): Long {
        val request = DownloadManager.Request(Uri.parse(url))
            .setTitle(title)
            .setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED)
            .setDestinationInExternalPublicDir(Environment.DIRECTORY_DOWNLOADS, fileName)
            .setAllowedOverMetered(true)
        val manager = context.getSystemService(Context.DOWNLOAD_SERVICE) as DownloadManager
        return manager.enqueue(request)
    }
}
'''},
    ),
    Feature(
        key="websocket", name="WebSocket (tempo real)", category=CAT,
        description="Conexao WebSocket com OkHttp, recebendo mensagens como Flow.",
        libs=["okhttp"], permissions=["android.permission.INTERNET"],
        files={"features/WebSocketClient.kt": r'''package %PKG%.features

import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import okhttp3.WebSocket
import okhttp3.WebSocketListener

/** Cliente WebSocket simples. Use connect() para receber e send() para enviar. */
class WebSocketClient(
    private val url: String,
    private val client: OkHttpClient = OkHttpClient()
) {
    private var socket: WebSocket? = null

    fun connect(): Flow<String> = callbackFlow {
        val listener = object : WebSocketListener() {
            override fun onMessage(webSocket: WebSocket, text: String) {
                trySend(text)
            }

            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                close(t)
            }

            override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                close()
            }
        }
        socket = client.newWebSocket(Request.Builder().url(url).build(), listener)
        awaitClose { socket?.close(1000, null) }
    }

    fun send(text: String): Boolean = socket?.send(text) ?: false
}
'''},
    ),
    Feature(
        key="json_utils", name="Utilitarios JSON (Gson)", category=CAT,
        description="Serializa e desserializa objetos e listas genericas.",
        libs=["gson"],
        files={"features/JsonUtils.kt": r'''package %PKG%.features

import com.google.gson.Gson
import com.google.gson.GsonBuilder
import com.google.gson.reflect.TypeToken

/** Conversao entre objetos Kotlin e JSON. */
object JsonUtils {

    val gson: Gson = GsonBuilder().setPrettyPrinting().create()

    fun toJson(value: Any?): String = gson.toJson(value)

    inline fun <reified T> fromJson(json: String): T? = try {
        gson.fromJson<T>(json, object : TypeToken<T>() {}.type)
    } catch (e: Exception) {
        null
    }
}
'''},
    ),
    Feature(
        key="firebase_auth", name="Firebase Authentication", category=FB,
        description="Login com e-mail e senha usando Firebase Auth.",
        libs=["firebase_bom", "firebase_auth", "coroutines_play"], plugins=["google_services"],
        notes=FIREBASE_NOTE,
        files={"features/FirebaseAuthHelper.kt": r'''package %PKG%.features

import com.google.firebase.auth.FirebaseAuth
import com.google.firebase.auth.FirebaseUser
import kotlinx.coroutines.tasks.await

/** Operacoes de autenticacao com Firebase. */
object FirebaseAuthHelper {

    private val auth: FirebaseAuth get() = FirebaseAuth.getInstance()

    val currentUser: FirebaseUser? get() = auth.currentUser

    suspend fun signIn(email: String, password: String): Result<FirebaseUser?> = runCatching {
        auth.signInWithEmailAndPassword(email, password).await().user
    }

    suspend fun signUp(email: String, password: String): Result<FirebaseUser?> = runCatching {
        auth.createUserWithEmailAndPassword(email, password).await().user
    }

    suspend fun resetPassword(email: String): Result<Unit> = runCatching {
        auth.sendPasswordResetEmail(email).await()
        Unit
    }

    fun signOut() = auth.signOut()
}
'''},
    ),
    Feature(
        key="firebase_firestore", name="Cloud Firestore", category=FB,
        description="Banco NoSQL em nuvem com operacoes de CRUD genericas.",
        libs=["firebase_bom", "firebase_firestore", "coroutines_play"], plugins=["google_services"],
        notes=FIREBASE_NOTE,
        files={"features/FirestoreRepository.kt": r'''package %PKG%.features

import com.google.firebase.firestore.FirebaseFirestore
import kotlinx.coroutines.tasks.await

/** CRUD generico em uma colecao do Firestore. */
class FirestoreRepository(private val collection: String) {

    private val db: FirebaseFirestore get() = FirebaseFirestore.getInstance()

    suspend fun list(): List<Map<String, Any?>> =
        db.collection(collection).get().await().documents.map { doc ->
            (doc.data ?: emptyMap()) + ("id" to doc.id)
        }

    suspend fun add(data: Map<String, Any?>): String =
        db.collection(collection).add(data).await().id

    suspend fun update(id: String, data: Map<String, Any?>) {
        db.collection(collection).document(id).update(data).await()
    }

    suspend fun delete(id: String) {
        db.collection(collection).document(id).delete().await()
    }
}
'''},
    ),
    Feature(
        key="firebase_messaging", name="Notificacoes push (FCM)", category=FB,
        description="Recebe notificacoes push do Firebase Cloud Messaging e exibe no aparelho.",
        libs=["firebase_bom", "firebase_messaging"], plugins=["google_services"],
        requires=["notifications"], notes=FIREBASE_NOTE,
        manifest_app='''        <service
            android:name=".features.PushMessagingService"
            android:exported="false">
            <intent-filter>
                <action android:name="com.google.firebase.MESSAGING_EVENT" />
            </intent-filter>
        </service>''',
        files={"features/PushMessagingService.kt": r'''package %PKG%.features

import android.util.Log
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage

/** Recebe mensagens push e exibe como notificacao local. */
class PushMessagingService : FirebaseMessagingService() {

    override fun onMessageReceived(message: RemoteMessage) {
        val title = message.notification?.title ?: message.data["title"] ?: return
        val body = message.notification?.body ?: message.data["body"].orEmpty()
        NotificationHelper.show(this, title, body)
    }

    override fun onNewToken(token: String) {
        // Envie este token ao seu servidor para direcionar notificacoes a este aparelho.
        Log.d("PushMessagingService", "Novo token FCM: $token")
    }
}
'''},
    ),
    Feature(
        key="firebase_analytics", name="Firebase Analytics", category=FB,
        description="Registro de eventos de uso no Google Analytics for Firebase.",
        libs=["firebase_bom", "firebase_analytics"], plugins=["google_services"],
        notes=FIREBASE_NOTE,
        files={"features/AnalyticsHelper.kt": r'''package %PKG%.features

import android.content.Context
import android.os.Bundle
import com.google.firebase.analytics.FirebaseAnalytics

/** Envia eventos personalizados ao Firebase Analytics. */
object AnalyticsHelper {

    fun log(context: Context, event: String, params: Map<String, String> = emptyMap()) {
        val bundle = Bundle()
        params.forEach { (key, value) -> bundle.putString(key, value) }
        FirebaseAnalytics.getInstance(context).logEvent(event, bundle)
    }
}
'''},
    ),
    Feature(
        key="firebase_crashlytics", name="Firebase Crashlytics", category=FB,
        description="Relatorios de falhas automaticos no console do Firebase.",
        libs=["firebase_bom", "firebase_crashlytics"], plugins=["google_services", "crashlytics"],
        notes=FIREBASE_NOTE,
    ),
    Feature(
        key="admob", name="Anuncios (AdMob)", category=CAT,
        description="Banner de anuncios do Google AdMob. Vem configurado com IDs de TESTE oficiais.",
        libs=["ads"], permissions=["android.permission.INTERNET"],
        app_init=["AdsHelper.init(this)"],
        notes="Substitua os IDs de teste pelos IDs reais da sua conta AdMob antes de publicar.",
        manifest_app='''        <!-- ID de aplicativo de TESTE do AdMob. Troque pelo seu ID real. -->
        <meta-data
            android:name="com.google.android.gms.ads.APPLICATION_ID"
            android:value="ca-app-pub-3940256099942544~3347511713" />''',
        files={"features/AdsHelper.kt": r'''package %PKG%.features

import android.content.Context
import com.google.android.gms.ads.AdRequest
import com.google.android.gms.ads.AdSize
import com.google.android.gms.ads.AdView
import com.google.android.gms.ads.MobileAds

/** Inicializacao do AdMob e criacao de banners. */
object AdsHelper {

    // ID de bloco de anuncio de TESTE fornecido pelo Google.
    const val TEST_BANNER_ID = "ca-app-pub-3940256099942544/6300978111"

    fun init(context: Context) {
        MobileAds.initialize(context)
    }

    /** Cria um AdView de banner pronto para ser adicionado a um layout. */
    fun createBanner(context: Context, unitId: String = TEST_BANNER_ID): AdView =
        AdView(context).apply {
            setAdSize(AdSize.BANNER)
            adUnitId = unitId
            loadAd(AdRequest.Builder().build())
        }
}
'''},
    ),
    Feature(
        key="billing", name="Compras no app (Google Play Billing)", category=CAT,
        description="Estrutura para vender produtos e assinaturas pela Google Play.",
        libs=["billing"],
        notes="Configure os produtos no Google Play Console. Validacao no servidor e recomendada.",
        files={"features/BillingManager.kt": r'''package %PKG%.features

import android.app.Activity
import android.content.Context
import com.android.billingclient.api.BillingClient
import com.android.billingclient.api.BillingClientStateListener
import com.android.billingclient.api.BillingFlowParams
import com.android.billingclient.api.BillingResult
import com.android.billingclient.api.PendingPurchasesParams
import com.android.billingclient.api.ProductDetails
import com.android.billingclient.api.Purchase
import com.android.billingclient.api.QueryProductDetailsParams

/** Gerencia a conexao com a Google Play Billing e o fluxo de compra. */
class BillingManager(
    context: Context,
    private val onPurchase: (Purchase) -> Unit
) {
    private val client: BillingClient = BillingClient.newBuilder(context)
        .setListener { result, purchases ->
            if (result.responseCode == BillingClient.BillingResponseCode.OK) {
                purchases?.forEach(onPurchase)
            }
        }
        .enablePendingPurchases(PendingPurchasesParams.newBuilder().enableOneTimeProducts().build())
        .build()

    /** Conecta ao servico de cobranca. */
    fun connect(onReady: () -> Unit) {
        client.startConnection(object : BillingClientStateListener {
            override fun onBillingSetupFinished(result: BillingResult) {
                if (result.responseCode == BillingClient.BillingResponseCode.OK) onReady()
            }

            override fun onBillingServiceDisconnected() {
                // A reconexao pode ser feita chamando connect() novamente.
            }
        })
    }

    /** Busca os detalhes de produtos de compra unica pelos ids cadastrados no Play Console. */
    fun queryProducts(ids: List<String>, onResult: (List<ProductDetails>) -> Unit) {
        val products = ids.map {
            QueryProductDetailsParams.Product.newBuilder()
                .setProductId(it)
                .setProductType(BillingClient.ProductType.INAPP)
                .build()
        }
        val params = QueryProductDetailsParams.newBuilder().setProductList(products).build()
        client.queryProductDetailsAsync(params) { _, details -> onResult(details) }
    }

    /** Abre a tela de compra da Google Play. */
    fun launchPurchase(activity: Activity, details: ProductDetails) {
        val productParams = BillingFlowParams.ProductDetailsParams.newBuilder()
            .setProductDetails(details)
            .build()
        val flow = BillingFlowParams.newBuilder().setProductDetailsParamsList(listOf(productParams)).build()
        client.launchBillingFlow(activity, flow)
    }

    fun disconnect() = client.endConnection()
}
'''},
    ),
]
