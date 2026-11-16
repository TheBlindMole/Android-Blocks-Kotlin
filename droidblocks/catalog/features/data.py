"""Funcionalidades de armazenamento e dados locais."""

from .base import Feature

CAT = "Dados e armazenamento"

FEATURES = [
    Feature(
        key="room", name="Banco de dados local (Room)", category=CAT,
        description="Banco SQLite com Room. Ativado automaticamente ao criar entidades no editor de banco.",
        libs=["room_runtime", "room_ktx", "room_compiler"], plugins=["ksp"],
    ),
    Feature(
        key="datastore", name="Preferencias (DataStore)", category=CAT,
        description="Armazenamento chave-valor assincrono e seguro para threads.",
        libs=["datastore"],
        files={"data/local/PreferencesStore.kt": r'''package %PKG%.data.local

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.intPreferencesKey
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.core.stringSetPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

// Instancia unica do DataStore para todo o aplicativo.
private val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "app_preferences")

/** Acesso simplificado as preferencias do app. */
class PreferencesStore(private val context: Context) {

    fun getString(key: String, default: String = ""): Flow<String> =
        context.dataStore.data.map { it[stringPreferencesKey(key)] ?: default }

    suspend fun putString(key: String, value: String) {
        context.dataStore.edit { it[stringPreferencesKey(key)] = value }
    }

    fun getBoolean(key: String, default: Boolean = false): Flow<Boolean> =
        context.dataStore.data.map { it[booleanPreferencesKey(key)] ?: default }

    suspend fun putBoolean(key: String, value: Boolean) {
        context.dataStore.edit { it[booleanPreferencesKey(key)] = value }
    }

    fun getInt(key: String, default: Int = 0): Flow<Int> =
        context.dataStore.data.map { it[intPreferencesKey(key)] ?: default }

    suspend fun putInt(key: String, value: Int) {
        context.dataStore.edit { it[intPreferencesKey(key)] = value }
    }

    fun getStringSet(key: String): Flow<Set<String>> =
        context.dataStore.data.map { it[stringSetPreferencesKey(key)] ?: emptySet() }

    suspend fun putStringSet(key: String, value: Set<String>) {
        context.dataStore.edit { it[stringSetPreferencesKey(key)] = value }
    }

    suspend fun remove(key: String) {
        context.dataStore.edit { it.remove(stringPreferencesKey(key)) }
    }

    suspend fun clear() {
        context.dataStore.edit { it.clear() }
    }
}
'''},
    ),
    Feature(
        key="shared_prefs", name="SharedPreferences simples", category=CAT,
        description="Leitura e escrita sincrona de configuracoes simples.",
        files={"data/local/PrefsHelper.kt": r'''package %PKG%.data.local

import android.content.Context
import android.content.SharedPreferences
import androidx.core.content.edit

/** Wrapper simples sobre SharedPreferences. */
class PrefsHelper(context: Context, name: String = "app_prefs") {

    private val prefs: SharedPreferences = context.getSharedPreferences(name, Context.MODE_PRIVATE)

    fun getString(key: String, default: String = ""): String = prefs.getString(key, default) ?: default
    fun putString(key: String, value: String) = prefs.edit { putString(key, value) }
    fun getBoolean(key: String, default: Boolean = false): Boolean = prefs.getBoolean(key, default)
    fun putBoolean(key: String, value: Boolean) = prefs.edit { putBoolean(key, value) }
    fun getInt(key: String, default: Int = 0): Int = prefs.getInt(key, default)
    fun putInt(key: String, value: Int) = prefs.edit { putInt(key, value) }
    fun clear() = prefs.edit { clear() }
}
'''},
    ),
    Feature(
        key="file_storage", name="Arquivos internos", category=CAT,
        description="Ler, gravar, listar e apagar arquivos na area privada do app.",
        files={"data/local/FileStorage.kt": r'''package %PKG%.data.local

import android.content.Context
import java.io.File

/** Arquivos privados do aplicativo (nao exigem permissao). */
class FileStorage(private val context: Context) {

    private fun file(name: String) = File(context.filesDir, name)

    fun writeText(name: String, content: String) = file(name).writeText(content)

    fun appendText(name: String, content: String) = file(name).appendText(content)

    fun readText(name: String): String? = file(name).takeIf { it.exists() }?.readText()

    fun exists(name: String): Boolean = file(name).exists()

    fun delete(name: String): Boolean = file(name).delete()

    fun list(): List<String> = context.filesDir.listFiles()?.map { it.name }?.sorted() ?: emptyList()

    fun sizeBytes(name: String): Long = file(name).takeIf { it.exists() }?.length() ?: 0L
}
'''},
    ),
    Feature(
        key="file_provider", name="Compartilhar arquivos (FileProvider)", category=CAT,
        description="Gera URIs seguras (content://) para compartilhar arquivos com outros apps.",
        flags=["file_provider"],
        manifest_app='''        <provider
            android:name="androidx.core.content.FileProvider"
            android:authorities="${applicationId}.fileprovider"
            android:exported="false"
            android:grantUriPermissions="true">
            <meta-data
                android:name="android.support.FILE_PROVIDER_PATHS"
                android:resource="@xml/file_paths" />
        </provider>''',
        res={"xml/file_paths.xml": '''<?xml version="1.0" encoding="utf-8"?>
<!-- Pastas que podem ser compartilhadas via FileProvider. -->
<paths>
    <cache-path name="cache" path="." />
    <files-path name="files" path="." />
    <external-files-path name="external_files" path="." />
</paths>
'''},
        files={"features/FileShareHelper.kt": r'''package %PKG%.features

import android.content.Context
import android.content.Intent
import android.net.Uri
import androidx.core.content.FileProvider
import java.io.File

/** Gera URIs e compartilha arquivos com outros aplicativos. */
object FileShareHelper {

    fun uriFor(context: Context, file: File): Uri =
        FileProvider.getUriForFile(context, "${context.packageName}.fileprovider", file)

    fun share(context: Context, file: File, mimeType: String = "*/*") {
        val intent = Intent(Intent.ACTION_SEND).apply {
            type = mimeType
            putExtra(Intent.EXTRA_STREAM, uriFor(context, file))
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
        context.startActivity(Intent.createChooser(intent, "Compartilhar").addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
    }
}
'''},
    ),
    Feature(
        key="encryption", name="Criptografia (Android Keystore)", category=CAT,
        description="Criptografa textos com AES-256/GCM usando chave protegida pelo Keystore.",
        files={"features/CryptoHelper.kt": r'''package %PKG%.features

import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

/** Criptografia simetrica com chave guardada no Android Keystore. */
object CryptoHelper {

    private const val KEY_ALIAS = "app_secret_key"
    private const val TRANSFORMATION = "AES/GCM/NoPadding"
    private const val IV_SIZE = 12

    // Recupera a chave existente ou cria uma nova.
    private fun secretKey(): SecretKey {
        val keyStore = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
        (keyStore.getEntry(KEY_ALIAS, null) as? KeyStore.SecretKeyEntry)?.let { return it.secretKey }
        val generator = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore")
        val spec = KeyGenParameterSpec.Builder(
            KEY_ALIAS, KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT
        )
            .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
            .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
            .setKeySize(256)
            .build()
        generator.init(spec)
        return generator.generateKey()
    }

    /** Retorna o texto criptografado em Base64 (IV + dados). */
    fun encrypt(plain: String): String {
        val cipher = Cipher.getInstance(TRANSFORMATION)
        cipher.init(Cipher.ENCRYPT_MODE, secretKey())
        val encrypted = cipher.doFinal(plain.toByteArray(Charsets.UTF_8))
        return Base64.encodeToString(cipher.iv + encrypted, Base64.NO_WRAP)
    }

    /** Descriptografa um texto gerado por encrypt(). */
    fun decrypt(data: String): String {
        val bytes = Base64.decode(data, Base64.NO_WRAP)
        val iv = bytes.copyOfRange(0, IV_SIZE)
        val payload = bytes.copyOfRange(IV_SIZE, bytes.size)
        val cipher = Cipher.getInstance(TRANSFORMATION)
        cipher.init(Cipher.DECRYPT_MODE, secretKey(), GCMParameterSpec(128, iv))
        return String(cipher.doFinal(payload), Charsets.UTF_8)
    }
}
'''},
    ),
    Feature(
        key="csv_export", name="Exportar CSV", category=CAT,
        description="Gera arquivos CSV a partir de listas e compartilha com outros apps.",
        requires=["file_provider"],
        files={"features/CsvExporter.kt": r'''package %PKG%.features

import android.content.Context
import java.io.File

/** Gera arquivos CSV com escape correto de aspas, virgulas e quebras de linha. */
object CsvExporter {

    fun toCsv(header: List<String>, rows: List<List<String>>, separator: Char = ';'): String {
        val builder = StringBuilder()
        builder.appendLine(header.joinToString(separator.toString()) { escape(it, separator) })
        rows.forEach { row -> builder.appendLine(row.joinToString(separator.toString()) { escape(it, separator) }) }
        return builder.toString()
    }

    /** Grava o CSV no cache e abre o seletor de compartilhamento. */
    fun exportAndShare(context: Context, fileName: String, header: List<String>, rows: List<List<String>>) {
        val file = File(context.cacheDir, fileName)
        file.writeText("﻿" + toCsv(header, rows))
        FileShareHelper.share(context, file, "text/csv")
    }

    private fun escape(value: String, separator: Char): String {
        val needsQuotes = value.contains(separator) || value.contains('"') || value.contains('\n')
        val escaped = value.replace("\"", "\"\"")
        return if (needsQuotes) "\"$escaped\"" else escaped
    }
}
'''},
    ),
    Feature(
        key="backup_json", name="Backup em JSON", category=CAT,
        description="Exporta e importa listas de objetos para arquivos JSON.",
        libs=["gson"],
        files={"features/BackupHelper.kt": r'''package %PKG%.features

import android.content.Context
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import java.io.File

/** Backup simples de dados em arquivos JSON na pasta privada do app. */
object BackupHelper {

    val gson = Gson()

    fun <T> save(context: Context, name: String, items: List<T>): File {
        val file = File(context.filesDir, "$name.json")
        file.writeText(gson.toJson(items))
        return file
    }

    inline fun <reified T> restore(context: Context, name: String): List<T> {
        val file = File(context.filesDir, "$name.json")
        if (!file.exists()) return emptyList()
        val type = object : TypeToken<List<T>>() {}.type
        return gson.fromJson(file.readText(), type) ?: emptyList()
    }
}
'''},
    ),
    Feature(
        key="memory_cache", name="Cache em memoria com expiracao", category=CAT,
        description="Cache chave-valor com tempo de vida (TTL), seguro para threads.",
        files={"features/TimedCache.kt": r'''package %PKG%.features

/** Cache simples com expiracao por tempo. */
class TimedCache<K, V>(private val ttlMillis: Long = 5 * 60 * 1000L) {

    private data class Entry<V>(val value: V, val expiresAt: Long)

    private val entries = mutableMapOf<K, Entry<V>>()

    @Synchronized
    fun get(key: K): V? {
        val entry = entries[key] ?: return null
        if (System.currentTimeMillis() > entry.expiresAt) {
            entries.remove(key)
            return null
        }
        return entry.value
    }

    @Synchronized
    fun put(key: K, value: V) {
        entries[key] = Entry(value, System.currentTimeMillis() + ttlMillis)
    }

    /** Retorna do cache ou calcula, guarda e retorna o valor. */
    suspend fun getOrPut(key: K, loader: suspend () -> V): V {
        get(key)?.let { return it }
        val value = loader()
        put(key, value)
        return value
    }

    @Synchronized
    fun clear() = entries.clear()
}
'''},
    ),
]
