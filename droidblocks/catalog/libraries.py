"""Versoes e bibliotecas usadas nos projetos gerados.

As versoes padrao formam uma combinacao testada e compativel entre si. Todas podem
ser alteradas na tela de Configuracoes do DroidBlocks (aba Versoes) ou depois,
diretamente no arquivo gradle/libs.versions.toml do projeto gerado.
"""

from collections import namedtuple

DEFAULT_VERSIONS = {
    "agp": "8.7.3",
    "kotlin": "2.0.21",
    "ksp": "2.0.21-1.0.28",
    "gradle": "8.9",
    "coreKtx": "1.15.0",
    "lifecycle": "2.8.7",
    "activityCompose": "1.9.3",
    "composeBom": "2024.12.01",
    "navigationCompose": "2.8.5",
    "appcompat": "1.7.0",
    "material": "1.12.0",
    "constraintlayout": "2.2.0",
    "recyclerview": "1.3.2",
    "fragment": "1.8.5",
    "coroutines": "1.9.0",
    "room": "2.6.1",
    "retrofit": "2.11.0",
    "okhttp": "4.12.0",
    "gson": "2.11.0",
    "coil": "2.7.0",
    "datastore": "1.1.1",
    "work": "2.10.0",
    "media3": "1.5.0",
    "camerax": "1.4.1",
    "biometric": "1.1.0",
    "playLocation": "21.3.0",
    "playMaps": "19.0.0",
    "mapsCompose": "6.2.1",
    "codeScanner": "16.1.0",
    "mlkitText": "16.0.1",
    "mlkitFace": "16.1.7",
    "mlkitTranslate": "17.0.3",
    "mlkitLangId": "17.0.6",
    "mlkitLabeling": "17.0.9",
    "zxing": "3.5.3",
    "splashscreen": "1.0.1",
    "browser": "1.8.0",
    "playReview": "2.0.2",
    "playAppUpdate": "2.1.0",
    "firebaseBom": "33.7.0",
    "googleServices": "4.4.2",
    "crashlyticsPlugin": "3.0.2",
    "lottie": "6.6.2",
    "timber": "5.0.1",
    "billing": "7.1.1",
    "ads": "23.6.0",
    "swiperefresh": "1.1.0",
    "exif": "1.3.7",
    "junit": "4.13.2",
    "androidxJunit": "1.2.1",
    "espresso": "3.6.1",
}

# conf: impl, ksp, test, androidTest, debug
# bom: chave da BOM que gerencia a versao (sem versao propria)
Lib = namedtuple("Lib", "alias module version conf bom is_bom")


def _lib(alias, module, version=None, conf="impl", bom=None, is_bom=False):
    return Lib(alias, module, version, conf, bom, is_bom)


LIBRARIES = {
    # Base AndroidX
    "core_ktx": _lib("androidx-core-ktx", "androidx.core:core-ktx", "coreKtx"),
    "lifecycle_runtime": _lib("androidx-lifecycle-runtime-ktx", "androidx.lifecycle:lifecycle-runtime-ktx", "lifecycle"),
    "lifecycle_viewmodel": _lib("androidx-lifecycle-viewmodel-ktx", "androidx.lifecycle:lifecycle-viewmodel-ktx", "lifecycle"),
    "coroutines": _lib("kotlinx-coroutines-android", "org.jetbrains.kotlinx:kotlinx-coroutines-android", "coroutines"),
    "coroutines_play": _lib("kotlinx-coroutines-play-services", "org.jetbrains.kotlinx:kotlinx-coroutines-play-services", "coroutines"),
    # Compose
    "compose_bom": _lib("androidx-compose-bom", "androidx.compose:compose-bom", "composeBom", is_bom=True),
    "activity_compose": _lib("androidx-activity-compose", "androidx.activity:activity-compose", "activityCompose"),
    "compose_ui": _lib("androidx-compose-ui", "androidx.compose.ui:ui", bom="compose_bom"),
    "compose_graphics": _lib("androidx-compose-ui-graphics", "androidx.compose.ui:ui-graphics", bom="compose_bom"),
    "compose_preview": _lib("androidx-compose-ui-tooling-preview", "androidx.compose.ui:ui-tooling-preview", bom="compose_bom"),
    "compose_tooling": _lib("androidx-compose-ui-tooling", "androidx.compose.ui:ui-tooling", conf="debug", bom="compose_bom"),
    "compose_manifest": _lib("androidx-compose-ui-test-manifest", "androidx.compose.ui:ui-test-manifest", conf="debug", bom="compose_bom"),
    "compose_material3": _lib("androidx-compose-material3", "androidx.compose.material3:material3", bom="compose_bom"),
    "compose_icons": _lib("androidx-compose-material-icons-core", "androidx.compose.material:material-icons-core", bom="compose_bom"),
    "compose_ui_test": _lib("androidx-compose-ui-test-junit4", "androidx.compose.ui:ui-test-junit4", conf="androidTest", bom="compose_bom"),
    "lifecycle_vm_compose": _lib("androidx-lifecycle-viewmodel-compose", "androidx.lifecycle:lifecycle-viewmodel-compose", "lifecycle"),
    "lifecycle_rt_compose": _lib("androidx-lifecycle-runtime-compose", "androidx.lifecycle:lifecycle-runtime-compose", "lifecycle"),
    "navigation_compose": _lib("androidx-navigation-compose", "androidx.navigation:navigation-compose", "navigationCompose"),
    "coil_compose": _lib("coil-compose", "io.coil-kt:coil-compose", "coil"),
    # Views (XML)
    "appcompat": _lib("androidx-appcompat", "androidx.appcompat:appcompat", "appcompat"),
    "material": _lib("google-material", "com.google.android.material:material", "material"),
    "constraintlayout": _lib("androidx-constraintlayout", "androidx.constraintlayout:constraintlayout", "constraintlayout"),
    "recyclerview": _lib("androidx-recyclerview", "androidx.recyclerview:recyclerview", "recyclerview"),
    "activity_ktx": _lib("androidx-activity-ktx", "androidx.activity:activity-ktx", "activityCompose"),
    "fragment_ktx": _lib("androidx-fragment-ktx", "androidx.fragment:fragment-ktx", "fragment"),
    "coil_views": _lib("coil", "io.coil-kt:coil", "coil"),
    "swiperefresh": _lib("androidx-swiperefreshlayout", "androidx.swiperefreshlayout:swiperefreshlayout", "swiperefresh"),
    # Dados
    "room_runtime": _lib("androidx-room-runtime", "androidx.room:room-runtime", "room"),
    "room_ktx": _lib("androidx-room-ktx", "androidx.room:room-ktx", "room"),
    "room_compiler": _lib("androidx-room-compiler", "androidx.room:room-compiler", "room", conf="ksp"),
    "datastore": _lib("androidx-datastore-preferences", "androidx.datastore:datastore-preferences", "datastore"),
    "retrofit": _lib("retrofit", "com.squareup.retrofit2:retrofit", "retrofit"),
    "retrofit_gson": _lib("retrofit-converter-gson", "com.squareup.retrofit2:converter-gson", "retrofit"),
    "okhttp": _lib("okhttp", "com.squareup.okhttp3:okhttp", "okhttp"),
    "okhttp_logging": _lib("okhttp-logging", "com.squareup.okhttp3:logging-interceptor", "okhttp"),
    "gson": _lib("gson", "com.google.code.gson:gson", "gson"),
    # Background
    "work": _lib("androidx-work-runtime-ktx", "androidx.work:work-runtime-ktx", "work"),
    # Midia
    "media3_exoplayer": _lib("androidx-media3-exoplayer", "androidx.media3:media3-exoplayer", "media3"),
    "media3_ui": _lib("androidx-media3-ui", "androidx.media3:media3-ui", "media3"),
    "camerax_core": _lib("androidx-camera-core", "androidx.camera:camera-core", "camerax"),
    "camerax_camera2": _lib("androidx-camera-camera2", "androidx.camera:camera-camera2", "camerax"),
    "camerax_lifecycle": _lib("androidx-camera-lifecycle", "androidx.camera:camera-lifecycle", "camerax"),
    "camerax_view": _lib("androidx-camera-view", "androidx.camera:camera-view", "camerax"),
    "exif": _lib("androidx-exifinterface", "androidx.exifinterface:exifinterface", "exif"),
    "lottie_compose": _lib("lottie-compose", "com.airbnb.android:lottie-compose", "lottie"),
    "lottie_views": _lib("lottie", "com.airbnb.android:lottie", "lottie"),
    "zxing": _lib("zxing-core", "com.google.zxing:core", "zxing"),
    # Seguranca
    "biometric": _lib("androidx-biometric", "androidx.biometric:biometric", "biometric"),
    # Google Play Services
    "play_location": _lib("play-services-location", "com.google.android.gms:play-services-location", "playLocation"),
    "play_maps": _lib("play-services-maps", "com.google.android.gms:play-services-maps", "playMaps"),
    "maps_compose": _lib("maps-compose", "com.google.maps.android:maps-compose", "mapsCompose"),
    "code_scanner": _lib("play-services-code-scanner", "com.google.android.gms:play-services-code-scanner", "codeScanner"),
    "mlkit_text": _lib("mlkit-text-recognition", "com.google.mlkit:text-recognition", "mlkitText"),
    "mlkit_face": _lib("mlkit-face-detection", "com.google.mlkit:face-detection", "mlkitFace"),
    "mlkit_translate": _lib("mlkit-translate", "com.google.mlkit:translate", "mlkitTranslate"),
    "mlkit_langid": _lib("mlkit-language-id", "com.google.mlkit:language-id", "mlkitLangId"),
    "mlkit_labeling": _lib("mlkit-image-labeling", "com.google.mlkit:image-labeling", "mlkitLabeling"),
    "play_review": _lib("play-review-ktx", "com.google.android.play:review-ktx", "playReview"),
    "play_update": _lib("play-app-update-ktx", "com.google.android.play:app-update-ktx", "playAppUpdate"),
    "billing": _lib("billing-ktx", "com.android.billingclient:billing-ktx", "billing"),
    "ads": _lib("play-services-ads", "com.google.android.gms:play-services-ads", "ads"),
    # Firebase
    "firebase_bom": _lib("firebase-bom", "com.google.firebase:firebase-bom", "firebaseBom", is_bom=True),
    "firebase_auth": _lib("firebase-auth", "com.google.firebase:firebase-auth", bom="firebase_bom"),
    "firebase_firestore": _lib("firebase-firestore", "com.google.firebase:firebase-firestore", bom="firebase_bom"),
    "firebase_messaging": _lib("firebase-messaging", "com.google.firebase:firebase-messaging", bom="firebase_bom"),
    "firebase_analytics": _lib("firebase-analytics", "com.google.firebase:firebase-analytics", bom="firebase_bom"),
    "firebase_crashlytics": _lib("firebase-crashlytics", "com.google.firebase:firebase-crashlytics", bom="firebase_bom"),
    # Diversos
    "splashscreen": _lib("androidx-core-splashscreen", "androidx.core:core-splashscreen", "splashscreen"),
    "browser": _lib("androidx-browser", "androidx.browser:browser", "browser"),
    "timber": _lib("timber", "com.jakewharton.timber:timber", "timber"),
    # Testes
    "junit": _lib("junit", "junit:junit", "junit", conf="test"),
    "coroutines_test": _lib("kotlinx-coroutines-test", "org.jetbrains.kotlinx:kotlinx-coroutines-test", "coroutines", conf="test"),
    "androidx_junit": _lib("androidx-junit", "androidx.test.ext:junit", "androidxJunit", conf="androidTest"),
    "espresso": _lib("androidx-espresso-core", "androidx.test.espresso:espresso-core", "espresso", conf="androidTest"),
}

Plugin = namedtuple("Plugin", "alias plugin_id version")

PLUGINS = {
    "android_application": Plugin("android-application", "com.android.application", "agp"),
    "kotlin_android": Plugin("kotlin-android", "org.jetbrains.kotlin.android", "kotlin"),
    "kotlin_compose": Plugin("kotlin-compose", "org.jetbrains.kotlin.plugin.compose", "kotlin"),
    "ksp": Plugin("ksp", "com.google.devtools.ksp", "ksp"),
    "google_services": Plugin("google-services", "com.google.gms.google-services", "googleServices"),
    "crashlytics": Plugin("firebase-crashlytics", "com.google.firebase.crashlytics", "crashlyticsPlugin"),
}

BASE_LIBS_COMMON = ["core_ktx", "lifecycle_runtime", "lifecycle_viewmodel", "coroutines",
                    "junit", "coroutines_test", "androidx_junit", "espresso"]
BASE_LIBS_COMPOSE = ["compose_bom", "activity_compose", "compose_ui", "compose_graphics",
                     "compose_preview", "compose_tooling", "compose_manifest", "compose_material3",
                     "compose_icons", "lifecycle_vm_compose", "lifecycle_rt_compose",
                     "navigation_compose", "coil_compose", "compose_ui_test"]
BASE_LIBS_VIEWS = ["appcompat", "material", "constraintlayout", "recyclerview", "activity_ktx",
                   "coil_views"]


def accessor(alias):
    """Converte um alias do catalogo para o acessor usado no Gradle (libs.x.y)."""
    return "libs." + alias.replace("-", ".").replace("_", ".")
