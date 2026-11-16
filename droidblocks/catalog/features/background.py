"""Funcionalidades de notificacoes, tarefas em segundo plano e tempo."""

from .base import Feature

CAT = "Notificacoes e segundo plano"

FEATURES = [
    Feature(
        key="notifications", name="Notificacoes locais", category=CAT,
        description="Canal de notificacao criado na inicializacao e funcao para exibir alertas. "
                    "Habilita a acao 'Notificar'.",
        permissions=["android.permission.POST_NOTIFICATIONS"],
        app_init=["NotificationHelper.createChannel(this)"],
        res={"drawable/ic_notification.xml": '''<?xml version="1.0" encoding="utf-8"?>
<!-- Icone monocromatico usado na barra de notificacoes. -->
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp"
    android:height="24dp"
    android:viewportWidth="24"
    android:viewportHeight="24">
    <path
        android:fillColor="#FFFFFFFF"
        android:pathData="M12,22c1.1,0 2,-0.9 2,-2h-4c0,1.1 0.89,2 2,2zM18,16v-5c0,-3.07 -1.64,-5.64 -4.5,-6.32V4c0,-0.83 -0.67,-1.5 -1.5,-1.5s-1.5,0.67 -1.5,1.5v0.68C7.63,5.36 6,7.92 6,11v5l-2,2v1h16v-1l-2,-2z" />
</vector>
'''},
        files={"features/NotificationHelper.kt": r'''package %PKG%.features

import android.Manifest
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.pm.PackageManager
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import androidx.core.content.ContextCompat
import %PKG%.R

/** Criacao de canal e exibicao de notificacoes locais. */
object NotificationHelper {

    const val CHANNEL_ID = "app_default"

    /** Cria o canal padrao (necessario no Android 8+). Chamado em App.onCreate. */
    fun createChannel(context: Context) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(CHANNEL_ID, "Geral", NotificationManager.IMPORTANCE_DEFAULT)
            channel.description = "Notificacoes do aplicativo"
            context.getSystemService(NotificationManager::class.java).createNotificationChannel(channel)
        }
    }

    fun canNotify(context: Context): Boolean =
        Build.VERSION.SDK_INT < Build.VERSION_CODES.TIRAMISU ||
            ContextCompat.checkSelfPermission(context, Manifest.permission.POST_NOTIFICATIONS) == PackageManager.PERMISSION_GRANTED

    /** Exibe uma notificacao que abre o app ao ser tocada. */
    fun show(context: Context, title: String, text: String, id: Int = (System.currentTimeMillis() % 100000).toInt()) {
        if (!canNotify(context)) return
        val launch = context.packageManager.getLaunchIntentForPackage(context.packageName)
        val pending = PendingIntent.getActivity(
            context, 0, launch, PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        val notification = NotificationCompat.Builder(context, CHANNEL_ID)
            .setSmallIcon(R.drawable.ic_notification)
            .setContentTitle(title)
            .setContentText(text)
            .setStyle(NotificationCompat.BigTextStyle().bigText(text))
            .setContentIntent(pending)
            .setAutoCancel(true)
            .setPriority(NotificationCompat.PRIORITY_DEFAULT)
            .build()
        try {
            NotificationManagerCompat.from(context).notify(id, notification)
        } catch (e: SecurityException) {
            // Permissao revogada entre a verificacao e o envio.
        }
    }
}
'''},
    ),
    Feature(
        key="work_manager", name="Tarefas periodicas (WorkManager)", category=CAT,
        description="Sincronizacao periodica em segundo plano a cada 15 minutos, com rede disponivel.",
        libs=["work"],
        app_init=["SyncScheduler.schedule(this)"],
        files={"features/SyncWorker.kt": r'''package %PKG%.features

import android.content.Context
import android.util.Log
import androidx.work.Constraints
import androidx.work.CoroutineWorker
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.NetworkType
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.WorkerParameters
import java.util.concurrent.TimeUnit

/** Tarefa executada periodicamente. Coloque aqui a sincronizacao com o servidor. */
class SyncWorker(context: Context, params: WorkerParameters) : CoroutineWorker(context, params) {

    override suspend fun doWork(): Result = try {
        Log.d("SyncWorker", "Sincronizacao executada")
        Result.success()
    } catch (e: Exception) {
        Result.retry()
    }
}

/** Agenda a tarefa periodica unica (nao duplica ao reabrir o app). */
object SyncScheduler {

    fun schedule(context: Context) {
        val constraints = Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build()
        val request = PeriodicWorkRequestBuilder<SyncWorker>(15, TimeUnit.MINUTES)
            .setConstraints(constraints)
            .build()
        WorkManager.getInstance(context)
            .enqueueUniquePeriodicWork("periodic_sync", ExistingPeriodicWorkPolicy.KEEP, request)
    }
}
'''},
    ),
    Feature(
        key="reminders", name="Lembretes agendados", category=CAT,
        description="Agenda notificacoes para daqui a X minutos usando WorkManager.",
        libs=["work"], requires=["notifications"],
        files={"features/ReminderScheduler.kt": r'''package %PKG%.features

import android.content.Context
import androidx.work.CoroutineWorker
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.WorkerParameters
import androidx.work.workDataOf
import java.util.concurrent.TimeUnit

/** Worker que exibe a notificacao do lembrete. */
class ReminderWorker(context: Context, params: WorkerParameters) : CoroutineWorker(context, params) {
    override suspend fun doWork(): Result {
        val title = inputData.getString("title") ?: "Lembrete"
        val text = inputData.getString("text").orEmpty()
        NotificationHelper.show(applicationContext, title, text)
        return Result.success()
    }
}

/** Agenda e cancela lembretes. */
object ReminderScheduler {

    fun schedule(context: Context, tag: String, title: String, text: String, delayMinutes: Long) {
        val request = OneTimeWorkRequestBuilder<ReminderWorker>()
            .setInitialDelay(delayMinutes, TimeUnit.MINUTES)
            .setInputData(workDataOf("title" to title, "text" to text))
            .addTag(tag)
            .build()
        WorkManager.getInstance(context).enqueue(request)
    }

    fun cancel(context: Context, tag: String) {
        WorkManager.getInstance(context).cancelAllWorkByTag(tag)
    }
}
'''},
    ),
    Feature(
        key="alarm", name="Alarmes (AlarmManager)", category=CAT,
        description="Agenda alarmes em horario especifico que disparam uma notificacao.",
        requires=["notifications"],
        manifest_app='''        <receiver
            android:name=".features.AlarmReceiver"
            android:exported="false" />''',
        files={"features/AlarmHelper.kt": r'''package %PKG%.features

import android.app.AlarmManager
import android.app.PendingIntent
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent

/** Agenda alarmes aproximados (nao exigem permissao especial). */
object AlarmHelper {

    fun schedule(context: Context, requestCode: Int, triggerAtMillis: Long, title: String, text: String) {
        val intent = Intent(context, AlarmReceiver::class.java)
            .putExtra("title", title)
            .putExtra("text", text)
        val pending = PendingIntent.getBroadcast(
            context, requestCode, intent, PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        val manager = context.getSystemService(Context.ALARM_SERVICE) as AlarmManager
        manager.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, triggerAtMillis, pending)
    }

    fun cancel(context: Context, requestCode: Int) {
        val pending = PendingIntent.getBroadcast(
            context, requestCode, Intent(context, AlarmReceiver::class.java),
            PendingIntent.FLAG_NO_CREATE or PendingIntent.FLAG_IMMUTABLE
        ) ?: return
        (context.getSystemService(Context.ALARM_SERVICE) as AlarmManager).cancel(pending)
    }
}

/** Recebe o alarme e mostra a notificacao. */
class AlarmReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        NotificationHelper.show(context, intent.getStringExtra("title") ?: "Alarme", intent.getStringExtra("text").orEmpty())
    }
}
'''},
    ),
    Feature(
        key="foreground_service", name="Servico em primeiro plano", category=CAT,
        description="Servico com notificacao fixa para tarefas longas (sincronizacao, upload).",
        requires=["notifications"],
        permissions=["android.permission.FOREGROUND_SERVICE", "android.permission.FOREGROUND_SERVICE_DATA_SYNC"],
        manifest_app='''        <service
            android:name=".features.ForegroundTaskService"
            android:exported="false"
            android:foregroundServiceType="dataSync" />''',
        files={"features/ForegroundTaskService.kt": r'''package %PKG%.features

import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.os.IBinder
import androidx.core.app.NotificationCompat
import androidx.core.app.ServiceCompat
import androidx.core.content.ContextCompat
import %PKG%.R
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

/** Servico de longa duracao com notificacao persistente. */
class ForegroundTaskService : Service() {

    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val notification = NotificationCompat.Builder(this, NotificationHelper.CHANNEL_ID)
            .setSmallIcon(R.drawable.ic_notification)
            .setContentTitle("Tarefa em andamento")
            .setContentText("Processando em segundo plano")
            .setOngoing(true)
            .build()
        ServiceCompat.startForeground(this, 7001, notification, ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC)
        scope.launch {
            // Substitua pelo trabalho real. Aqui apenas aguarda 10 segundos.
            delay(10_000)
            stopSelf()
        }
        return START_NOT_STICKY
    }

    override fun onDestroy() {
        scope.cancel()
        super.onDestroy()
    }

    companion object {
        fun start(context: Context) {
            ContextCompat.startForegroundService(context, Intent(context, ForegroundTaskService::class.java))
        }
    }
}
'''},
    ),
    Feature(
        key="boot_receiver", name="Executar ao ligar o aparelho", category=CAT,
        description="Recebe o evento de inicializacao do sistema para reagendar tarefas.",
        permissions=["android.permission.RECEIVE_BOOT_COMPLETED"],
        manifest_app='''        <receiver
            android:name=".features.BootReceiver"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.BOOT_COMPLETED" />
            </intent-filter>
        </receiver>''',
        files={"features/BootReceiver.kt": r'''package %PKG%.features

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log

/** Chamado quando o aparelho termina de ligar. Reagende alarmes aqui. */
class BootReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action == Intent.ACTION_BOOT_COMPLETED) {
            Log.d("BootReceiver", "Aparelho reiniciado")
        }
    }
}
'''},
    ),
    Feature(
        key="timer", name="Cronometro e temporizador", category=CAT,
        description="Cronometro e contagem regressiva com StateFlow. Usado pelo bloco 'Cronometro'.",
        files={"features/TickTimer.kt": r'''package %PKG%.features

import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch

/**
 * Cronometro (countdownSeconds = 0) ou contagem regressiva (countdownSeconds > 0).
 * O valor emitido e o tempo em segundos a exibir.
 */
class TickTimer(private val scope: CoroutineScope, private val countdownSeconds: Long = 0L) {

    private val _seconds = MutableStateFlow(countdownSeconds)
    val seconds: StateFlow<Long> = _seconds.asStateFlow()

    private val _running = MutableStateFlow(false)
    val running: StateFlow<Boolean> = _running.asStateFlow()

    private var job: Job? = null

    fun start() {
        if (job?.isActive == true) return
        _running.value = true
        job = scope.launch {
            while (isActive) {
                delay(1000)
                if (countdownSeconds > 0) {
                    _seconds.value = (_seconds.value - 1).coerceAtLeast(0)
                    if (_seconds.value == 0L) {
                        _running.value = false
                        break
                    }
                } else {
                    _seconds.value += 1
                }
            }
        }
    }

    fun pause() {
        job?.cancel()
        _running.value = false
    }

    fun toggle() = if (_running.value) pause() else start()

    fun reset() {
        pause()
        _seconds.value = countdownSeconds
    }

    companion object {
        /** Formata segundos como mm:ss ou hh:mm:ss. */
        fun format(totalSeconds: Long): String {
            val hours = totalSeconds / 3600
            val minutes = (totalSeconds % 3600) / 60
            val seconds = totalSeconds % 60
            return if (hours > 0) "%d:%02d:%02d".format(hours, minutes, seconds) else "%02d:%02d".format(minutes, seconds)
        }
    }
}
'''},
    ),
]
