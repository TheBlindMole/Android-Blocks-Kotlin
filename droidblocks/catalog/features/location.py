"""Funcionalidades de localizacao, mapas, sensores e hardware."""

from .base import Feature

CAT = "Localizacao e mapas"
HW = "Sensores e hardware"

LOCATION_PERMS = ["android.permission.ACCESS_FINE_LOCATION", "android.permission.ACCESS_COARSE_LOCATION"]

SENSOR_FLOW = r'''package %PKG%.features

import android.content.Context
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow

/** Expoe a leitura de qualquer sensor como Flow. */
object SensorHelper {

    fun isAvailable(context: Context, type: Int): Boolean =
        (context.getSystemService(Context.SENSOR_SERVICE) as SensorManager).getDefaultSensor(type) != null

    /** Exemplo: SensorHelper.observe(context, Sensor.TYPE_ACCELEROMETER) */
    fun observe(
        context: Context,
        type: Int,
        delay: Int = SensorManager.SENSOR_DELAY_UI
    ): Flow<FloatArray> = callbackFlow {
        val manager = context.getSystemService(Context.SENSOR_SERVICE) as SensorManager
        val sensor = manager.getDefaultSensor(type)
        if (sensor == null) {
            close()
            return@callbackFlow
        }
        val listener = object : SensorEventListener {
            override fun onSensorChanged(event: SensorEvent) {
                trySend(event.values.copyOf())
            }

            override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) = Unit
        }
        manager.registerListener(listener, sensor, delay)
        awaitClose { manager.unregisterListener(listener) }
    }
}
'''

FEATURES = [
    Feature(
        key="location", name="Localizacao atual (GPS)", category=CAT,
        description="Obtem a posicao atual com o Fused Location Provider. Habilita a acao 'Minha localizacao'.",
        libs=["play_location", "coroutines_play"], permissions=LOCATION_PERMS,
        files={"features/LocationHelper.kt": r'''package %PKG%.features

import android.Manifest
import android.annotation.SuppressLint
import android.content.Context
import android.content.pm.PackageManager
import android.location.Location
import androidx.core.content.ContextCompat
import com.google.android.gms.location.LocationServices
import com.google.android.gms.location.Priority
import com.google.android.gms.tasks.CancellationTokenSource
import kotlinx.coroutines.tasks.await

/** Localizacao atual do aparelho. Retorna null sem permissao ou sem sinal. */
object LocationHelper {

    fun hasPermission(context: Context): Boolean =
        ContextCompat.checkSelfPermission(context, Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED ||
            ContextCompat.checkSelfPermission(context, Manifest.permission.ACCESS_COARSE_LOCATION) == PackageManager.PERMISSION_GRANTED

    @SuppressLint("MissingPermission")
    suspend fun current(context: Context): Location? {
        if (!hasPermission(context)) return null
        val client = LocationServices.getFusedLocationProviderClient(context)
        return try {
            client.getCurrentLocation(Priority.PRIORITY_BALANCED_POWER_ACCURACY, CancellationTokenSource().token).await()
                ?: client.lastLocation.await()
        } catch (e: Exception) {
            null
        }
    }

    /** Texto amigavel com latitude e longitude. */
    fun format(location: Location?): String =
        if (location == null) "Localizacao indisponivel" else "Lat %.5f, Lng %.5f".format(location.latitude, location.longitude)
}
'''},
    ),
    Feature(
        key="location_updates", name="Rastreamento de localizacao", category=CAT,
        description="Recebe atualizacoes continuas de posicao como Flow (ex.: corrida, entregas).",
        libs=["play_location"], permissions=LOCATION_PERMS, requires=["location"],
        files={"features/LocationTracker.kt": r'''package %PKG%.features

import android.annotation.SuppressLint
import android.content.Context
import android.location.Location
import android.os.Looper
import com.google.android.gms.location.LocationCallback
import com.google.android.gms.location.LocationRequest
import com.google.android.gms.location.LocationResult
import com.google.android.gms.location.LocationServices
import com.google.android.gms.location.Priority
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow

/** Atualizacoes de localizacao em intervalo configuravel. */
object LocationTracker {

    @SuppressLint("MissingPermission")
    fun updates(context: Context, intervalMs: Long = 5_000L): Flow<Location> = callbackFlow {
        if (!LocationHelper.hasPermission(context)) {
            close()
            return@callbackFlow
        }
        val client = LocationServices.getFusedLocationProviderClient(context)
        val request = LocationRequest.Builder(Priority.PRIORITY_HIGH_ACCURACY, intervalMs).build()
        val callback = object : LocationCallback() {
            override fun onLocationResult(result: LocationResult) {
                result.lastLocation?.let { trySend(it) }
            }
        }
        client.requestLocationUpdates(request, callback, Looper.getMainLooper())
        awaitClose { client.removeLocationUpdates(callback) }
    }
}
'''},
    ),
    Feature(
        key="geocoding", name="Endereco a partir de coordenadas", category=CAT,
        description="Converte latitude/longitude em endereco e vice-versa (Geocoder).",
        files={"features/GeocoderHelper.kt": r'''package %PKG%.features

import android.content.Context
import android.location.Address
import android.location.Geocoder
import android.os.Build
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.withContext
import java.util.Locale
import kotlin.coroutines.resume

/** Geocodificacao direta e reversa. */
object GeocoderHelper {

    suspend fun addressFrom(context: Context, latitude: Double, longitude: Double): String? =
        withContext(Dispatchers.IO) {
            if (!Geocoder.isPresent()) return@withContext null
            val geocoder = Geocoder(context, Locale.getDefault())
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                suspendCancellableCoroutine { continuation ->
                    geocoder.getFromLocation(latitude, longitude, 1, object : Geocoder.GeocodeListener {
                        override fun onGeocode(addresses: MutableList<Address>) {
                            continuation.resume(addresses.firstOrNull()?.getAddressLine(0))
                        }

                        override fun onError(errorMessage: String?) {
                            continuation.resume(null)
                        }
                    })
                }
            } else {
                try {
                    @Suppress("DEPRECATION")
                    geocoder.getFromLocation(latitude, longitude, 1)?.firstOrNull()?.getAddressLine(0)
                } catch (e: Exception) {
                    null
                }
            }
        }

    suspend fun coordinatesFrom(context: Context, address: String): Pair<Double, Double>? =
        withContext(Dispatchers.IO) {
            if (!Geocoder.isPresent()) return@withContext null
            try {
                @Suppress("DEPRECATION")
                Geocoder(context, Locale.getDefault()).getFromLocationName(address, 1)
                    ?.firstOrNull()?.let { it.latitude to it.longitude }
            } catch (e: Exception) {
                null
            }
        }
}
'''},
    ),
    Feature(
        key="geofencing", name="Geofencing (cercas virtuais)", category=CAT,
        description="Dispara notificacao ao entrar ou sair de uma area. Exige localizacao em segundo plano.",
        libs=["play_location"], requires=["location", "notifications"],
        permissions=LOCATION_PERMS + ["android.permission.ACCESS_BACKGROUND_LOCATION"],
        notes="No Android 10+ o usuario precisa permitir localizacao 'o tempo todo' nas configuracoes.",
        manifest_app='''        <receiver
            android:name=".features.GeofenceReceiver"
            android:exported="false" />''',
        files={"features/GeofenceHelper.kt": r'''package %PKG%.features

import android.annotation.SuppressLint
import android.app.PendingIntent
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import com.google.android.gms.location.Geofence
import com.google.android.gms.location.GeofencingEvent
import com.google.android.gms.location.GeofencingRequest
import com.google.android.gms.location.LocationServices

/** Registra areas monitoradas. */
object GeofenceHelper {

    private fun pendingIntent(context: Context): PendingIntent =
        PendingIntent.getBroadcast(
            context, 0, Intent(context, GeofenceReceiver::class.java),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_MUTABLE
        )

    @SuppressLint("MissingPermission")
    fun add(context: Context, id: String, latitude: Double, longitude: Double, radiusMeters: Float = 150f) {
        val fence = Geofence.Builder()
            .setRequestId(id)
            .setCircularRegion(latitude, longitude, radiusMeters)
            .setExpirationDuration(Geofence.NEVER_EXPIRE)
            .setTransitionTypes(Geofence.GEOFENCE_TRANSITION_ENTER or Geofence.GEOFENCE_TRANSITION_EXIT)
            .build()
        val request = GeofencingRequest.Builder()
            .setInitialTrigger(GeofencingRequest.INITIAL_TRIGGER_ENTER)
            .addGeofence(fence)
            .build()
        LocationServices.getGeofencingClient(context).addGeofences(request, pendingIntent(context))
    }

    fun removeAll(context: Context) {
        LocationServices.getGeofencingClient(context).removeGeofences(pendingIntent(context))
    }
}

/** Recebe os eventos de entrada e saida das areas. */
class GeofenceReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        val event = GeofencingEvent.fromIntent(intent) ?: return
        if (event.hasError()) return
        val action = if (event.geofenceTransition == Geofence.GEOFENCE_TRANSITION_ENTER) "Entrou em" else "Saiu de"
        val ids = event.triggeringGeofences?.joinToString { it.requestId }.orEmpty()
        NotificationHelper.show(context, "Area monitorada", "$action: $ids")
    }
}
'''},
    ),
    Feature(
        key="maps", name="Google Maps", category=CAT,
        description="Mapa interativo com marcador. Usado pelo bloco 'Mapa'. Requer chave da API do Maps.",
        libs=["play_maps"], libs_compose=["maps_compose"], flags=["maps"],
        permissions=["android.permission.INTERNET"],
        notes="Crie a chave no Google Cloud Console e coloque MAPS_API_KEY=sua_chave no local.properties.",
        files_compose={"features/AppMap.kt": r'''package %PKG%.features

import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import com.google.android.gms.maps.model.CameraPosition
import com.google.android.gms.maps.model.LatLng
import com.google.maps.android.compose.GoogleMap
import com.google.maps.android.compose.Marker
import com.google.maps.android.compose.rememberCameraPositionState
import com.google.maps.android.compose.rememberMarkerState

/** Mapa centralizado em uma coordenada, com um marcador. */
@Composable
fun AppMap(latitude: Double, longitude: Double, title: String, modifier: Modifier = Modifier, zoom: Float = 14f) {
    val position = LatLng(latitude, longitude)
    val camera = rememberCameraPositionState {
        this.position = CameraPosition.fromLatLngZoom(position, zoom)
    }
    GoogleMap(modifier = modifier, cameraPositionState = camera) {
        Marker(state = rememberMarkerState(position = position), title = title)
    }
}
'''},
        files_views={"features/MapHelper.kt": r'''package %PKG%.features

import com.google.android.gms.maps.CameraUpdateFactory
import com.google.android.gms.maps.SupportMapFragment
import com.google.android.gms.maps.model.LatLng
import com.google.android.gms.maps.model.MarkerOptions

/** Configura um SupportMapFragment com marcador e zoom. */
object MapHelper {

    fun setup(fragment: SupportMapFragment, latitude: Double, longitude: Double, title: String, zoom: Float = 14f) {
        fragment.getMapAsync { map ->
            val position = LatLng(latitude, longitude)
            map.addMarker(MarkerOptions().position(position).title(title))
            map.moveCamera(CameraUpdateFactory.newLatLngZoom(position, zoom))
            map.uiSettings.isZoomControlsEnabled = true
        }
    }
}
'''},
    ),
    Feature(
        key="sensors", name="Sensores (acelerometro, giroscopio, luz...)", category=HW,
        description="Leitura de qualquer sensor do aparelho como Flow.",
        files={"features/SensorHelper.kt": SENSOR_FLOW},
    ),
    Feature(
        key="compass", name="Bussola", category=HW,
        description="Direcao em graus usando o sensor de vetor de rotacao.",
        requires=["sensors"],
        files={"features/CompassHelper.kt": r'''package %PKG%.features

import android.content.Context
import android.hardware.Sensor
import android.hardware.SensorManager
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

/** Direcao em graus (0 = norte, 90 = leste). */
object CompassHelper {

    fun azimuth(context: Context): Flow<Float> =
        SensorHelper.observe(context, Sensor.TYPE_ROTATION_VECTOR).map { values ->
            val rotation = FloatArray(9)
            val orientation = FloatArray(3)
            SensorManager.getRotationMatrixFromVector(rotation, values)
            SensorManager.getOrientation(rotation, orientation)
            ((Math.toDegrees(orientation[0].toDouble()) + 360.0) % 360.0).toFloat()
        }

    fun direction(degrees: Float): String {
        val names = listOf("N", "NE", "L", "SE", "S", "SO", "O", "NO")
        return names[(((degrees + 22.5f) % 360f) / 45f).toInt()]
    }
}
'''},
    ),
    Feature(
        key="step_counter", name="Contador de passos", category=HW,
        description="Passos desde a ultima reinicializacao do aparelho (sensor de passos).",
        requires=["sensors"], permissions=["android.permission.ACTIVITY_RECOGNITION"],
        files={"features/StepCounter.kt": r'''package %PKG%.features

import android.content.Context
import android.hardware.Sensor
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

/** Total de passos reportado pelo sensor TYPE_STEP_COUNTER. */
object StepCounter {

    fun isAvailable(context: Context) = SensorHelper.isAvailable(context, Sensor.TYPE_STEP_COUNTER)

    fun steps(context: Context): Flow<Int> =
        SensorHelper.observe(context, Sensor.TYPE_STEP_COUNTER).map { it[0].toInt() }

    /** Estimativa de distancia em km a partir dos passos. */
    fun distanceKm(steps: Int, stepLengthMeters: Double = 0.75): Double = steps * stepLengthMeters / 1000.0

    /** Estimativa de calorias gastas. */
    fun calories(steps: Int, weightKg: Double = 70.0): Double = steps * 0.0005 * weightKg
}
'''},
    ),
    Feature(
        key="shake_detector", name="Detector de chacoalhar", category=HW,
        description="Dispara um evento quando o usuario chacoalha o aparelho.",
        requires=["sensors"],
        files={"features/ShakeDetector.kt": r'''package %PKG%.features

import android.content.Context
import android.hardware.Sensor
import android.hardware.SensorManager
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.filter
import kotlinx.coroutines.flow.map
import kotlin.math.sqrt

/** Emite Unit a cada chacoalhada detectada. */
object ShakeDetector {

    fun shakes(context: Context, threshold: Float = 2.7f, cooldownMs: Long = 800L): Flow<Unit> {
        var last = 0L
        return SensorHelper.observe(context, Sensor.TYPE_ACCELEROMETER, SensorManager.SENSOR_DELAY_GAME)
            .filter { values ->
                val gX = values[0] / SensorManager.GRAVITY_EARTH
                val gY = values[1] / SensorManager.GRAVITY_EARTH
                val gZ = values[2] / SensorManager.GRAVITY_EARTH
                val force = sqrt(gX * gX + gY * gY + gZ * gZ)
                val now = System.currentTimeMillis()
                if (force > threshold && now - last > cooldownMs) {
                    last = now
                    true
                } else {
                    false
                }
            }
            .map { }
    }
}
'''},
    ),
    Feature(
        key="bluetooth_le", name="Bluetooth Low Energy (busca)", category=HW,
        description="Procura dispositivos BLE proximos e emite os resultados como Flow.",
        permissions=["android.permission.BLUETOOTH_SCAN", "android.permission.BLUETOOTH_CONNECT",
                     "android.permission.BLUETOOTH", "android.permission.BLUETOOTH_ADMIN",
                     "android.permission.ACCESS_FINE_LOCATION"],
        manifest_root='    <uses-feature android:name="android.hardware.bluetooth_le" android:required="false" />',
        files={"features/BleScanner.kt": r'''package %PKG%.features

import android.annotation.SuppressLint
import android.bluetooth.BluetoothManager
import android.bluetooth.le.ScanCallback
import android.bluetooth.le.ScanResult
import android.content.Context
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow

/** Dispositivo encontrado na busca. */
data class BleDevice(val address: String, val name: String, val rssi: Int)

/** Busca de dispositivos Bluetooth Low Energy. Requer permissoes concedidas. */
object BleScanner {

    @SuppressLint("MissingPermission")
    fun scan(context: Context): Flow<BleDevice> = callbackFlow {
        val manager = context.getSystemService(Context.BLUETOOTH_SERVICE) as BluetoothManager
        val scanner = manager.adapter?.bluetoothLeScanner
        if (scanner == null) {
            close()
            return@callbackFlow
        }
        val callback = object : ScanCallback() {
            override fun onScanResult(callbackType: Int, result: ScanResult) {
                val name = try {
                    result.device.name
                } catch (e: SecurityException) {
                    null
                }
                trySend(BleDevice(result.device.address, name ?: "Desconhecido", result.rssi))
            }
        }
        scanner.startScan(callback)
        awaitClose { scanner.stopScan(callback) }
    }
}
'''},
    ),
    Feature(
        key="nfc", name="Leitura NFC", category=HW,
        description="Le o identificador e o texto NDEF de etiquetas NFC.",
        permissions=["android.permission.NFC"],
        manifest_root='    <uses-feature android:name="android.hardware.nfc" android:required="false" />',
        files={"features/NfcHelper.kt": r'''package %PKG%.features

import android.app.Activity
import android.nfc.NdefRecord
import android.nfc.NfcAdapter
import android.nfc.Tag
import android.nfc.tech.Ndef

/** Leitura de etiquetas NFC usando o modo leitor. */
object NfcHelper {

    fun isAvailable(activity: Activity): Boolean = NfcAdapter.getDefaultAdapter(activity) != null

    /** Ative no onResume. O callback recebe o id da tag em hexadecimal e o texto, se houver. */
    fun enable(activity: Activity, onTag: (id: String, text: String?) -> Unit) {
        val adapter = NfcAdapter.getDefaultAdapter(activity) ?: return
        val flags = NfcAdapter.FLAG_READER_NFC_A or NfcAdapter.FLAG_READER_NFC_B or
            NfcAdapter.FLAG_READER_NFC_F or NfcAdapter.FLAG_READER_NFC_V
        adapter.enableReaderMode(activity, { tag: Tag ->
            val id = tag.id.joinToString("") { "%02X".format(it) }
            val text = readText(tag)
            activity.runOnUiThread { onTag(id, text) }
        }, flags, null)
    }

    /** Desative no onPause. */
    fun disable(activity: Activity) {
        NfcAdapter.getDefaultAdapter(activity)?.disableReaderMode(activity)
    }

    private fun readText(tag: Tag): String? {
        val ndef = Ndef.get(tag) ?: return null
        val message = ndef.cachedNdefMessage ?: return null
        val record = message.records.firstOrNull { it.tnf == NdefRecord.TNF_WELL_KNOWN } ?: return null
        val payload = record.payload
        if (payload.isEmpty()) return null
        val languageLength = payload[0].toInt() and 0x3F
        return String(payload, 1 + languageLength, payload.size - 1 - languageLength, Charsets.UTF_8)
    }
}
'''},
    ),
    Feature(
        key="biometric", name="Biometria (digital/rosto)", category="Seguranca e autenticacao",
        description="Autenticacao biometrica com BiometricPrompt. Habilita a acao 'Autenticar biometria'.",
        libs=["biometric"], libs_compose=["fragment_ktx"], flags=["fragment_activity"],
        files={"features/BiometricHelper.kt": r'''package %PKG%.features

import androidx.biometric.BiometricManager
import androidx.biometric.BiometricPrompt
import androidx.core.content.ContextCompat
import androidx.fragment.app.FragmentActivity

/** Autenticacao por biometria forte ou credencial do aparelho. */
object BiometricHelper {

    private const val AUTHENTICATORS = BiometricManager.Authenticators.BIOMETRIC_WEAK or
        BiometricManager.Authenticators.DEVICE_CREDENTIAL

    fun canAuthenticate(activity: FragmentActivity): Boolean =
        BiometricManager.from(activity).canAuthenticate(AUTHENTICATORS) == BiometricManager.BIOMETRIC_SUCCESS

    fun authenticate(
        activity: FragmentActivity,
        title: String = "Confirme sua identidade",
        onSuccess: () -> Unit,
        onError: (String) -> Unit = {}
    ) {
        if (!canAuthenticate(activity)) {
            onError("Biometria indisponivel neste aparelho")
            return
        }
        val prompt = BiometricPrompt(activity, ContextCompat.getMainExecutor(activity),
            object : BiometricPrompt.AuthenticationCallback() {
                override fun onAuthenticationSucceeded(result: BiometricPrompt.AuthenticationResult) {
                    onSuccess()
                }

                override fun onAuthenticationError(errorCode: Int, errString: CharSequence) {
                    onError(errString.toString())
                }
            })
        val info = BiometricPrompt.PromptInfo.Builder()
            .setTitle(title)
            .setAllowedAuthenticators(AUTHENTICATORS)
            .build()
        prompt.authenticate(info)
    }
}
'''},
    ),
]
