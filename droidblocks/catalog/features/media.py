"""Funcionalidades de camera, imagem, audio, video e inteligencia artificial no aparelho."""

from .base import Feature

CAT = "Midia e camera"
AI = "Inteligencia artificial (ML Kit)"

CAMERA_FILES = r'''package %PKG%.features

import android.content.Context
import android.net.Uri
import androidx.core.content.FileProvider
import java.io.File

/** Cria arquivos temporarios para fotos e devolve Uris seguras (content://). */
object CameraFiles {

    fun newPhotoUri(context: Context): Uri {
        val dir = File(context.cacheDir, "camera").apply { mkdirs() }
        val file = File(dir, "foto_${System.currentTimeMillis()}.jpg")
        return FileProvider.getUriForFile(context, "${context.packageName}.fileprovider", file)
    }
}
'''

CAMERAX_HELPER = r'''package %PKG%.features

import android.content.Context
import android.net.Uri
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageCapture
import androidx.camera.core.ImageCaptureException
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.core.content.ContextCompat
import androidx.lifecycle.LifecycleOwner
import java.io.File

/** Inicia a pre-visualizacao da camera (CameraX) e captura fotos. */
object CameraXHelper {

    fun start(
        owner: LifecycleOwner,
        previewView: PreviewView,
        lensFacing: Int = CameraSelector.LENS_FACING_BACK,
        onReady: (ImageCapture) -> Unit = {}
    ) {
        val context = previewView.context
        val future = ProcessCameraProvider.getInstance(context)
        future.addListener({
            val provider = future.get()
            val preview = Preview.Builder().build()
            preview.setSurfaceProvider(previewView.surfaceProvider)
            val capture = ImageCapture.Builder().build()
            val selector = CameraSelector.Builder().requireLensFacing(lensFacing).build()
            try {
                provider.unbindAll()
                provider.bindToLifecycle(owner, selector, preview, capture)
                onReady(capture)
            } catch (e: Exception) {
                // Camera indisponivel ou permissao negada.
            }
        }, ContextCompat.getMainExecutor(context))
    }

    /** Captura uma foto para a pasta de cache e devolve a Uri do arquivo. */
    fun takePicture(context: Context, capture: ImageCapture, onSaved: (Uri?) -> Unit) {
        val file = File(context.cacheDir, "camerax_${System.currentTimeMillis()}.jpg")
        val options = ImageCapture.OutputFileOptions.Builder(file).build()
        capture.takePicture(options, ContextCompat.getMainExecutor(context),
            object : ImageCapture.OnImageSavedCallback {
                override fun onImageSaved(output: ImageCapture.OutputFileResults) {
                    onSaved(Uri.fromFile(file))
                }

                override fun onError(exception: ImageCaptureException) {
                    onSaved(null)
                }
            })
    }
}
'''

SPEECH_COMMON = r'''package %PKG%.features

import android.content.Intent
import android.speech.RecognizerIntent

/** Monta o Intent de reconhecimento de voz do sistema. */
object SpeechIntents {

    fun create(languageTag: String, prompt: String = "Fale agora"): Intent =
        Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, languageTag)
            putExtra(RecognizerIntent.EXTRA_PROMPT, prompt)
        }

    fun firstResult(data: Intent?): String? =
        data?.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS)?.firstOrNull()
}
'''


def _mlkit_image(name, lib, cls, body, imports, desc, key):
    """Cria uma feature de ML Kit que processa imagens a partir de uma Uri."""
    code = r'''package %PKG%.features

import android.content.Context
import android.net.Uri
import com.google.mlkit.vision.common.InputImage
''' + imports + r'''import kotlinx.coroutines.tasks.await

''' + body
    return Feature(key=key, name=name, category=AI, description=desc,
                   libs=[lib, "coroutines_play"], files={f"features/{cls}.kt": code})


FEATURES = [
    Feature(
        key="camera_capture", name="Tirar foto (camera do sistema)", category=CAT,
        description="Abre a camera padrao e devolve a foto. Habilita a acao 'Tirar foto'.",
        requires=["file_provider"],
        notes="Nao declare a permissao CAMERA junto com esta funcao, a menos que tambem use CameraX.",
        files={"features/CameraFiles.kt": CAMERA_FILES},
        files_compose={"features/CameraCapture.kt": r'''package %PKG%.features

import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.runtime.Composable
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.platform.LocalContext

/** Retorna uma funcao que abre a camera e entrega a Uri da foto, ou null se cancelado. */
@Composable
fun rememberCameraCapture(onResult: (Uri?) -> Unit): () -> Unit {
    val context = LocalContext.current
    val pending = rememberSaveable { mutableStateOf<Uri?>(null) }
    val launcher = rememberLauncherForActivityResult(ActivityResultContracts.TakePicture()) { success ->
        onResult(if (success) pending.value else null)
    }
    return {
        val uri = CameraFiles.newPhotoUri(context)
        pending.value = uri
        launcher.launch(uri)
    }
}
'''},
        files_views={"features/CameraCaptureHelper.kt": r'''package %PKG%.features

import android.net.Uri
import androidx.activity.ComponentActivity
import androidx.activity.result.contract.ActivityResultContracts

/** Deve ser criado como propriedade da Activity (antes do onStart). */
class CameraCaptureHelper(
    private val activity: ComponentActivity,
    private val onResult: (Uri?) -> Unit
) {
    private var pending: Uri? = null

    private val launcher = activity.registerForActivityResult(ActivityResultContracts.TakePicture()) { success ->
        onResult(if (success) pending else null)
    }

    fun launch() {
        val uri = CameraFiles.newPhotoUri(activity)
        pending = uri
        launcher.launch(uri)
    }
}
'''},
    ),
    Feature(
        key="image_picker", name="Escolher imagem da galeria", category=CAT,
        description="Seletor de fotos oficial do Android (Photo Picker). Habilita a acao 'Escolher imagem'.",
        files_compose={"features/ImagePicker.kt": r'''package %PKG%.features

import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.PickVisualMediaRequest
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.runtime.Composable

/** Retorna uma funcao que abre o seletor de fotos. */
@Composable
fun rememberImagePicker(onResult: (Uri?) -> Unit): () -> Unit {
    val launcher = rememberLauncherForActivityResult(ActivityResultContracts.PickVisualMedia()) { uri ->
        onResult(uri)
    }
    return { launcher.launch(PickVisualMediaRequest(ActivityResultContracts.PickVisualMedia.ImageOnly)) }
}
'''},
        files_views={"features/ImagePickerHelper.kt": r'''package %PKG%.features

import android.net.Uri
import androidx.activity.ComponentActivity
import androidx.activity.result.PickVisualMediaRequest
import androidx.activity.result.contract.ActivityResultContracts

/** Deve ser criado como propriedade da Activity (antes do onStart). */
class ImagePickerHelper(activity: ComponentActivity, onResult: (Uri?) -> Unit) {

    private val launcher = activity.registerForActivityResult(ActivityResultContracts.PickVisualMedia()) { uri ->
        onResult(uri)
    }

    fun launch() {
        launcher.launch(PickVisualMediaRequest(ActivityResultContracts.PickVisualMedia.ImageOnly))
    }
}
'''},
    ),
    Feature(
        key="camerax_preview", name="Camera personalizada (CameraX)", category=CAT,
        description="Pre-visualizacao ao vivo da camera dentro do app e captura de fotos.",
        libs=["camerax_core", "camerax_camera2", "camerax_lifecycle", "camerax_view"],
        permissions=["android.permission.CAMERA"],
        manifest_root='    <uses-feature android:name="android.hardware.camera.any" android:required="false" />',
        files={"features/CameraXHelper.kt": CAMERAX_HELPER},
        files_compose={"features/CameraPreview.kt": r'''package %PKG%.features

import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageCapture
import androidx.camera.view.PreviewView
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.viewinterop.AndroidView
import androidx.lifecycle.compose.LocalLifecycleOwner

/** Composable com a imagem ao vivo da camera. */
@Composable
fun CameraPreview(
    modifier: Modifier = Modifier,
    lensFacing: Int = CameraSelector.LENS_FACING_BACK,
    onReady: (ImageCapture) -> Unit = {}
) {
    val owner = LocalLifecycleOwner.current
    AndroidView(
        modifier = modifier,
        factory = { context ->
            PreviewView(context).also { view -> CameraXHelper.start(owner, view, lensFacing, onReady) }
        }
    )
}
'''},
    ),
    Feature(
        key="audio_player", name="Player de audio", category=CAT,
        description="Reproduz audios locais ou por URL com MediaPlayer.",
        permissions=["android.permission.INTERNET"],
        files={"features/AudioPlayer.kt": r'''package %PKG%.features

import android.media.AudioAttributes
import android.media.MediaPlayer

/** Player de audio simples para URLs ou arquivos. */
class AudioPlayer {

    private var player: MediaPlayer? = null

    val isPlaying: Boolean get() = player?.isPlaying == true

    /** Prepara e toca o audio de forma assincrona. */
    fun play(source: String, onCompleted: () -> Unit = {}) {
        stop()
        player = MediaPlayer().apply {
            setAudioAttributes(
                AudioAttributes.Builder()
                    .setContentType(AudioAttributes.CONTENT_TYPE_MUSIC)
                    .setUsage(AudioAttributes.USAGE_MEDIA)
                    .build()
            )
            setDataSource(source)
            setOnPreparedListener { it.start() }
            setOnCompletionListener { onCompleted() }
            prepareAsync()
        }
    }

    fun pause() {
        player?.takeIf { it.isPlaying }?.pause()
    }

    fun resume() {
        player?.start()
    }

    fun stop() {
        player?.release()
        player = null
    }
}
'''},
    ),
    Feature(
        key="audio_recorder", name="Gravador de audio", category=CAT,
        description="Grava audio do microfone em arquivo .m4a.",
        permissions=["android.permission.RECORD_AUDIO"],
        files={"features/AudioRecorder.kt": r'''package %PKG%.features

import android.content.Context
import android.media.MediaRecorder
import android.os.Build
import java.io.File

/** Gravacao de audio em AAC (.m4a). Requer permissao RECORD_AUDIO concedida. */
class AudioRecorder(private val context: Context) {

    private var recorder: MediaRecorder? = null
    var currentFile: File? = null
        private set

    val isRecording: Boolean get() = recorder != null

    fun start(): File {
        stop()
        val file = File(context.filesDir, "gravacao_${System.currentTimeMillis()}.m4a")
        val mediaRecorder = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            MediaRecorder(context)
        } else {
            @Suppress("DEPRECATION")
            MediaRecorder()
        }
        mediaRecorder.apply {
            setAudioSource(MediaRecorder.AudioSource.MIC)
            setOutputFormat(MediaRecorder.OutputFormat.MPEG_4)
            setAudioEncoder(MediaRecorder.AudioEncoder.AAC)
            setAudioEncodingBitRate(128_000)
            setAudioSamplingRate(44_100)
            setOutputFile(file.absolutePath)
            prepare()
            start()
        }
        recorder = mediaRecorder
        currentFile = file
        return file
    }

    fun stop(): File? {
        try {
            recorder?.stop()
        } catch (e: RuntimeException) {
            // Gravacao muito curta: o arquivo pode estar vazio.
        }
        recorder?.release()
        recorder = null
        return currentFile
    }
}
'''},
    ),
    Feature(
        key="video_player", name="Player de video (Media3/ExoPlayer)", category=CAT,
        description="Reproducao de videos por URL com controles. Usado pelo bloco 'Video'.",
        libs=["media3_exoplayer", "media3_ui"], permissions=["android.permission.INTERNET"],
        files_compose={"features/VideoPlayer.kt": r'''package %PKG%.features

import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.viewinterop.AndroidView
import androidx.media3.common.MediaItem
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.ui.PlayerView

/** Player de video com controles padrao, liberado automaticamente ao sair da tela. */
@Composable
fun VideoPlayer(url: String, modifier: Modifier = Modifier, autoPlay: Boolean = false) {
    val context = LocalContext.current
    val player = remember(url) {
        ExoPlayer.Builder(context).build().apply {
            setMediaItem(MediaItem.fromUri(url))
            playWhenReady = autoPlay
            prepare()
        }
    }
    DisposableEffect(player) {
        onDispose { player.release() }
    }
    AndroidView(modifier = modifier, factory = { PlayerView(it).apply { this.player = player } })
}
'''},
        files_views={"features/VideoPlayerHelper.kt": r'''package %PKG%.features

import androidx.media3.common.MediaItem
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.ui.PlayerView

/** Cria o ExoPlayer e conecta a um PlayerView. Lembre de chamar release() no onDestroy. */
object VideoPlayerHelper {

    fun attach(view: PlayerView, url: String, autoPlay: Boolean = false): ExoPlayer =
        ExoPlayer.Builder(view.context).build().also { player ->
            view.player = player
            player.setMediaItem(MediaItem.fromUri(url))
            player.playWhenReady = autoPlay
            player.prepare()
        }
}
'''},
    ),
    Feature(
        key="text_to_speech", name="Texto para fala (TTS)", category=CAT,
        description="Le textos em voz alta com o motor de voz do sistema. Habilita a acao 'Falar texto'.",
        queries=['        <intent>\n            <action android:name="android.intent.action.TTS_SERVICE" />\n        </intent>'],
        files={"features/TtsHelper.kt": r'''package %PKG%.features

import android.content.Context
import android.speech.tts.TextToSpeech
import java.util.Locale

/** Sintese de voz com inicializacao preguicosa. */
object TtsHelper : TextToSpeech.OnInitListener {

    private var tts: TextToSpeech? = null
    private var ready = false
    private var pending: String? = null
    private var locale: Locale = Locale.getDefault()

    fun speak(context: Context, text: String, language: Locale = Locale.getDefault()) {
        locale = language
        val engine = tts
        if (engine == null) {
            pending = text
            tts = TextToSpeech(context.applicationContext, this)
            return
        }
        if (ready) {
            engine.language = locale
            engine.speak(text, TextToSpeech.QUEUE_FLUSH, null, "utterance")
        } else {
            pending = text
        }
    }

    override fun onInit(status: Int) {
        ready = status == TextToSpeech.SUCCESS
        val text = pending
        pending = null
        if (ready && text != null) {
            tts?.language = locale
            tts?.speak(text, TextToSpeech.QUEUE_FLUSH, null, "utterance")
        }
    }

    fun stop() {
        tts?.stop()
    }

    fun shutdown() {
        tts?.shutdown()
        tts = null
        ready = false
    }
}
'''},
    ),
    Feature(
        key="speech_to_text", name="Reconhecimento de voz", category=CAT,
        description="Converte fala em texto com o reconhecedor do sistema. Habilita a acao 'Ouvir voz'.",
        queries=['        <intent>\n            <action android:name="android.speech.RecognitionService" />\n        </intent>'],
        files={"features/SpeechIntents.kt": SPEECH_COMMON},
        files_compose={"features/SpeechToText.kt": r'''package %PKG%.features

import android.content.ActivityNotFoundException
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.runtime.Composable
import java.util.Locale

/** Retorna uma funcao que abre o reconhecimento de voz e devolve o texto reconhecido. */
@Composable
fun rememberSpeechToText(
    languageTag: String = Locale.getDefault().toLanguageTag(),
    onResult: (String?) -> Unit
): () -> Unit {
    val launcher = rememberLauncherForActivityResult(ActivityResultContracts.StartActivityForResult()) { result ->
        onResult(SpeechIntents.firstResult(result.data))
    }
    return {
        try {
            launcher.launch(SpeechIntents.create(languageTag))
        } catch (e: ActivityNotFoundException) {
            onResult(null)
        }
    }
}
'''},
        files_views={"features/SpeechToTextHelper.kt": r'''package %PKG%.features

import android.content.ActivityNotFoundException
import androidx.activity.ComponentActivity
import androidx.activity.result.contract.ActivityResultContracts
import java.util.Locale

/** Deve ser criado como propriedade da Activity (antes do onStart). */
class SpeechToTextHelper(activity: ComponentActivity, private val onResult: (String?) -> Unit) {

    private val launcher = activity.registerForActivityResult(ActivityResultContracts.StartActivityForResult()) { result ->
        onResult(SpeechIntents.firstResult(result.data))
    }

    fun launch(languageTag: String = Locale.getDefault().toLanguageTag()) {
        try {
            launcher.launch(SpeechIntents.create(languageTag))
        } catch (e: ActivityNotFoundException) {
            onResult(null)
        }
    }
}
'''},
    ),
    Feature(
        key="image_utils", name="Processamento de imagens", category=CAT,
        description="Redimensionar, comprimir e corrigir rotacao (EXIF) de imagens.",
        libs=["exif"],
        files={"features/ImageUtils.kt": r'''package %PKG%.features

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Matrix
import android.net.Uri
import androidx.exifinterface.media.ExifInterface
import java.io.ByteArrayOutputStream

/** Operacoes comuns com imagens. */
object ImageUtils {

    /** Carrega uma imagem reduzida para caber em maxSize pixels no maior lado. */
    fun loadScaled(context: Context, uri: Uri, maxSize: Int = 1280): Bitmap? {
        val bounds = BitmapFactory.Options().apply { inJustDecodeBounds = true }
        context.contentResolver.openInputStream(uri)?.use { BitmapFactory.decodeStream(it, null, bounds) }
        var sample = 1
        while (bounds.outWidth / sample > maxSize || bounds.outHeight / sample > maxSize) sample *= 2
        val options = BitmapFactory.Options().apply { inSampleSize = sample }
        val bitmap = context.contentResolver.openInputStream(uri)?.use {
            BitmapFactory.decodeStream(it, null, options)
        } ?: return null
        return rotateByExif(context, uri, bitmap)
    }

    /** Corrige a rotacao da foto conforme o EXIF. */
    fun rotateByExif(context: Context, uri: Uri, bitmap: Bitmap): Bitmap {
        val orientation = context.contentResolver.openInputStream(uri)?.use {
            ExifInterface(it).getAttributeInt(ExifInterface.TAG_ORIENTATION, ExifInterface.ORIENTATION_NORMAL)
        } ?: ExifInterface.ORIENTATION_NORMAL
        val degrees = when (orientation) {
            ExifInterface.ORIENTATION_ROTATE_90 -> 90f
            ExifInterface.ORIENTATION_ROTATE_180 -> 180f
            ExifInterface.ORIENTATION_ROTATE_270 -> 270f
            else -> return bitmap
        }
        val matrix = Matrix().apply { postRotate(degrees) }
        return Bitmap.createBitmap(bitmap, 0, 0, bitmap.width, bitmap.height, matrix, true)
    }

    /** Comprime em JPEG e retorna os bytes. */
    fun compress(bitmap: Bitmap, quality: Int = 80): ByteArray {
        val output = ByteArrayOutputStream()
        bitmap.compress(Bitmap.CompressFormat.JPEG, quality.coerceIn(1, 100), output)
        return output.toByteArray()
    }

    /** Recorta a imagem em um quadrado central. */
    fun cropSquare(bitmap: Bitmap): Bitmap {
        val size = minOf(bitmap.width, bitmap.height)
        return Bitmap.createBitmap(bitmap, (bitmap.width - size) / 2, (bitmap.height - size) / 2, size, size)
    }
}
'''},
    ),
    Feature(
        key="gallery_save", name="Salvar imagem na galeria", category=CAT,
        description="Salva Bitmaps na galeria (MediaStore), compativel com Android 10+ e anteriores.",
        permissions=["android.permission.WRITE_EXTERNAL_STORAGE"],
        files={"features/GallerySaver.kt": r'''package %PKG%.features

import android.content.ContentValues
import android.content.Context
import android.graphics.Bitmap
import android.net.Uri
import android.os.Build
import android.os.Environment
import android.provider.MediaStore

/** Salva imagens na galeria do aparelho. */
object GallerySaver {

    fun save(context: Context, bitmap: Bitmap, displayName: String, album: String = "App"): Uri? {
        val values = ContentValues().apply {
            put(MediaStore.Images.Media.DISPLAY_NAME, "$displayName.jpg")
            put(MediaStore.Images.Media.MIME_TYPE, "image/jpeg")
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                put(MediaStore.Images.Media.RELATIVE_PATH, Environment.DIRECTORY_PICTURES + "/" + album)
                put(MediaStore.Images.Media.IS_PENDING, 1)
            }
        }
        val resolver = context.contentResolver
        val uri = resolver.insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, values) ?: return null
        resolver.openOutputStream(uri)?.use { bitmap.compress(Bitmap.CompressFormat.JPEG, 95, it) }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            values.clear()
            values.put(MediaStore.Images.Media.IS_PENDING, 0)
            resolver.update(uri, values, null, null)
        }
        return uri
    }
}
'''},
    ),
    Feature(
        key="pdf_viewer", name="Leitor de PDF", category=CAT,
        description="Renderiza paginas de PDF em imagens com PdfRenderer (nativo).",
        files={"features/PdfPageRenderer.kt": r'''package %PKG%.features

import android.content.Context
import android.graphics.Bitmap
import android.graphics.Color
import android.graphics.pdf.PdfRenderer
import android.net.Uri

/** Renderiza paginas de um PDF a partir de uma Uri. */
object PdfPageRenderer {

    fun pageCount(context: Context, uri: Uri): Int =
        context.contentResolver.openFileDescriptor(uri, "r")?.use { fd ->
            PdfRenderer(fd).use { it.pageCount }
        } ?: 0

    fun render(context: Context, uri: Uri, pageIndex: Int, width: Int = 1080): Bitmap? =
        context.contentResolver.openFileDescriptor(uri, "r")?.use { fd ->
            PdfRenderer(fd).use { renderer ->
                if (pageIndex !in 0 until renderer.pageCount) return@use null
                renderer.openPage(pageIndex).use { page ->
                    val height = (width.toFloat() / page.width * page.height).toInt()
                    val bitmap = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888)
                    bitmap.eraseColor(Color.WHITE)
                    page.render(bitmap, null, null, PdfRenderer.Page.RENDER_MODE_FOR_DISPLAY)
                    bitmap
                }
            }
        }
}
'''},
    ),
    Feature(
        key="pdf_generator", name="Gerar PDF", category=CAT,
        description="Cria documentos PDF com titulo e linhas de texto, com quebra de pagina.",
        files={"features/PdfGenerator.kt": r'''package %PKG%.features

import android.content.Context
import android.graphics.Paint
import android.graphics.Typeface
import android.graphics.pdf.PdfDocument
import java.io.File

/** Gera PDFs simples em tamanho A4. */
object PdfGenerator {

    private const val PAGE_WIDTH = 595
    private const val PAGE_HEIGHT = 842
    private const val MARGIN = 40f

    fun create(context: Context, fileName: String, title: String, lines: List<String>): File {
        val document = PdfDocument()
        val titlePaint = Paint().apply { textSize = 20f; typeface = Typeface.DEFAULT_BOLD }
        val textPaint = Paint().apply { textSize = 12f }
        var pageNumber = 1
        var page = document.startPage(PdfDocument.PageInfo.Builder(PAGE_WIDTH, PAGE_HEIGHT, pageNumber).create())
        var y = MARGIN + 20f
        page.canvas.drawText(title, MARGIN, y, titlePaint)
        y += 30f
        for (line in lines) {
            if (y > PAGE_HEIGHT - MARGIN) {
                document.finishPage(page)
                pageNumber++
                page = document.startPage(PdfDocument.PageInfo.Builder(PAGE_WIDTH, PAGE_HEIGHT, pageNumber).create())
                y = MARGIN + 12f
            }
            page.canvas.drawText(line, MARGIN, y, textPaint)
            y += 18f
        }
        document.finishPage(page)
        val file = File(context.cacheDir, fileName)
        file.outputStream().use { document.writeTo(it) }
        document.close()
        return file
    }
}
'''},
    ),
    Feature(
        key="qr_generator", name="Gerar QR Code", category=CAT,
        description="Gera imagens de QR Code offline (ZXing). Usado pelo bloco 'QR Code'.",
        libs=["zxing"],
        files={"features/QrCodeGenerator.kt": r'''package %PKG%.features

import android.graphics.Bitmap
import android.graphics.Color
import com.google.zxing.BarcodeFormat
import com.google.zxing.EncodeHintType
import com.google.zxing.qrcode.QRCodeWriter

/** Gera um Bitmap de QR Code a partir de um texto. */
object QrCodeGenerator {

    fun generate(text: String, size: Int = 512, foreground: Int = Color.BLACK, background: Int = Color.WHITE): Bitmap {
        val hints = mapOf(EncodeHintType.MARGIN to 1, EncodeHintType.CHARACTER_SET to "UTF-8")
        val matrix = QRCodeWriter().encode(text.ifEmpty { " " }, BarcodeFormat.QR_CODE, size, size, hints)
        val pixels = IntArray(size * size)
        for (y in 0 until size) {
            for (x in 0 until size) {
                pixels[y * size + x] = if (matrix[x, y]) foreground else background
            }
        }
        return Bitmap.createBitmap(pixels, size, size, Bitmap.Config.ARGB_8888)
    }
}
'''},
    ),
    Feature(
        key="barcode_scanner", name="Leitor de QR/codigo de barras", category=AI,
        description="Leitura de QR Code e codigos de barras com o Google Code Scanner, "
                    "sem precisar de permissao de camera. Habilita a acao 'Ler codigo'.",
        libs=["code_scanner"],
        files={"features/BarcodeScannerHelper.kt": r'''package %PKG%.features

import android.content.Context
import com.google.mlkit.vision.barcode.common.Barcode
import com.google.mlkit.vision.codescanner.GmsBarcodeScannerOptions
import com.google.mlkit.vision.codescanner.GmsBarcodeScanning
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlin.coroutines.resume

/** Abre o leitor de codigos do Google Play Services e devolve o valor lido. */
object BarcodeScannerHelper {

    suspend fun scan(context: Context): String? = suspendCancellableCoroutine { continuation ->
        val options = GmsBarcodeScannerOptions.Builder()
            .setBarcodeFormats(Barcode.FORMAT_ALL_FORMATS)
            .build()
        GmsBarcodeScanning.getClient(context, options).startScan()
            .addOnSuccessListener { barcode ->
                if (continuation.isActive) continuation.resume(barcode.rawValue)
            }
            .addOnCanceledListener {
                if (continuation.isActive) continuation.resume(null)
            }
            .addOnFailureListener {
                if (continuation.isActive) continuation.resume(null)
            }
    }
}
'''},
    ),
    _mlkit_image(
        "Reconhecimento de texto (OCR)", "mlkit_text", "TextRecognitionHelper",
        r'''/** Extrai texto de imagens, offline. */
object TextRecognitionHelper {

    suspend fun recognize(context: Context, uri: Uri): String {
        val image = InputImage.fromFilePath(context, uri)
        val recognizer = TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS)
        return recognizer.process(image).await().text
    }
}
''',
        "import com.google.mlkit.vision.text.TextRecognition\nimport com.google.mlkit.vision.text.latin.TextRecognizerOptions\n",
        "Le textos de fotos e documentos sem internet (alfabeto latino).", "ocr"),
    _mlkit_image(
        "Deteccao de rostos", "mlkit_face", "FaceDetectionHelper",
        r'''/** Conta rostos e informa se estao sorrindo. */
object FaceDetectionHelper {

    data class FaceResult(val count: Int, val smiling: Int)

    suspend fun detect(context: Context, uri: Uri): FaceResult {
        val options = FaceDetectorOptions.Builder()
            .setPerformanceMode(FaceDetectorOptions.PERFORMANCE_MODE_FAST)
            .setClassificationMode(FaceDetectorOptions.CLASSIFICATION_MODE_ALL)
            .build()
        val faces = FaceDetection.getClient(options).process(InputImage.fromFilePath(context, uri)).await()
        val smiling = faces.count { (it.smilingProbability ?: 0f) > 0.6f }
        return FaceResult(faces.size, smiling)
    }
}
''',
        "import com.google.mlkit.vision.face.FaceDetection\nimport com.google.mlkit.vision.face.FaceDetectorOptions\n",
        "Detecta rostos em fotos, offline.", "face_detection"),
    _mlkit_image(
        "Rotulagem de imagens", "mlkit_labeling", "ImageLabelingHelper",
        r'''/** Identifica objetos e cenas em uma imagem. */
object ImageLabelingHelper {

    suspend fun labels(context: Context, uri: Uri, minConfidence: Float = 0.6f): List<Pair<String, Float>> {
        val labeler = ImageLabeling.getClient(ImageLabelerOptions.DEFAULT_OPTIONS)
        return labeler.process(InputImage.fromFilePath(context, uri)).await()
            .filter { it.confidence >= minConfidence }
            .map { it.text to it.confidence }
    }
}
''',
        "import com.google.mlkit.vision.label.ImageLabeling\nimport com.google.mlkit.vision.label.defaults.ImageLabelerOptions\n",
        "Reconhece objetos (comida, animal, carro...) em fotos, offline.", "image_labeling"),
    Feature(
        key="translate", name="Tradutor no aparelho", category=AI,
        description="Traducao offline com ML Kit (o modelo e baixado na primeira utilizacao).",
        libs=["mlkit_translate", "coroutines_play"],
        files={"features/TranslatorHelper.kt": r'''package %PKG%.features

import com.google.mlkit.nl.translate.TranslateLanguage
import com.google.mlkit.nl.translate.Translation
import com.google.mlkit.nl.translate.TranslatorOptions
import kotlinx.coroutines.tasks.await

/** Traducao de textos entre idiomas suportados pelo ML Kit. */
object TranslatorHelper {

    suspend fun translate(
        text: String,
        source: String = TranslateLanguage.PORTUGUESE,
        target: String = TranslateLanguage.ENGLISH
    ): String {
        val options = TranslatorOptions.Builder().setSourceLanguage(source).setTargetLanguage(target).build()
        val translator = Translation.getClient(options)
        return try {
            translator.downloadModelIfNeeded().await()
            translator.translate(text).await()
        } finally {
            translator.close()
        }
    }
}
'''},
    ),
    Feature(
        key="language_id", name="Identificar idioma", category=AI,
        description="Descobre o idioma de um texto, offline.",
        libs=["mlkit_langid", "coroutines_play"],
        files={"features/LanguageIdHelper.kt": r'''package %PKG%.features

import com.google.mlkit.nl.languageid.LanguageIdentification
import kotlinx.coroutines.tasks.await

/** Identifica o idioma de um texto. Retorna "und" quando nao reconhece. */
object LanguageIdHelper {

    suspend fun identify(text: String): String =
        LanguageIdentification.getClient().identifyLanguage(text).await()
}
'''},
    ),
    Feature(
        key="lottie", name="Animacoes Lottie", category=CAT,
        description="Animacoes vetoriais Lottie a partir de URL ou da pasta assets.",
        files_compose={"features/LottieBox.kt": r'''package %PKG%.features

import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import com.airbnb.lottie.compose.LottieAnimation
import com.airbnb.lottie.compose.LottieCompositionSpec
import com.airbnb.lottie.compose.LottieConstants
import com.airbnb.lottie.compose.rememberLottieComposition

/** Exibe uma animacao Lottie em loop a partir de uma URL. */
@Composable
fun LottieBox(url: String, modifier: Modifier = Modifier) {
    val composition = rememberLottieComposition(LottieCompositionSpec.Url(url))
    LottieAnimation(
        composition = composition.value,
        iterations = LottieConstants.IterateForever,
        modifier = modifier
    )
}
'''},
        files_views={"features/LottieHelper.kt": r'''package %PKG%.features

import com.airbnb.lottie.LottieAnimationView
import com.airbnb.lottie.LottieDrawable

/** Carrega e inicia uma animacao Lottie em loop. */
object LottieHelper {

    fun play(view: LottieAnimationView, url: String) {
        view.setAnimationFromUrl(url)
        view.repeatCount = LottieDrawable.INFINITE
        view.playAnimation()
    }
}
'''},
    ),
]

# A biblioteca do Lottie depende do modo de interface (Compose ou Views).
for _f in FEATURES:
    if _f.key == "lottie":
        _f.libs_compose = ["lottie_compose"]
        _f.libs_views = ["lottie_views"]
