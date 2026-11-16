"""Geracao da interface classica com Activities, layouts XML e ViewBinding."""

from ...catalog.components import ICONS
from ..naming import kq, to_snake, xml_escape, to_pascal
from .context import collect_imports
from .screen_spec import ScreenSpec, action_code, viewmodel, options_of

IMPORTS = {
    "Activity": "android.app.Activity",
    "Bundle": "android.os.Bundle",
    "Context": "android.content.Context",
    "Intent": "android.content.Intent",
    "Toast": "android.widget.Toast",
    "DatePickerDialog": "android.app.DatePickerDialog",
    "Calendar": "java.util.Calendar",
    "SuppressLint": "android.annotation.SuppressLint",
    "WebViewClient": "android.webkit.WebViewClient",
    "AppCompatActivity": "androidx.appcompat.app.AppCompatActivity",
    "FragmentActivity": "androidx.fragment.app.FragmentActivity",
    "viewModels": "androidx.activity.viewModels",
    "ActivityResultContracts": "androidx.activity.result.contract.ActivityResultContracts",
    "installSplashScreen": "androidx.core.splashscreen.SplashScreen.Companion.installSplashScreen",
    "Lifecycle": "androidx.lifecycle.Lifecycle",
    ".lifecycleScope": "androidx.lifecycle.lifecycleScope",
    "lifecycleScope": "androidx.lifecycle.lifecycleScope",
    "repeatOnLifecycle": "androidx.lifecycle.repeatOnLifecycle",
    "launch": "kotlinx.coroutines.launch",
    ".launch": "kotlinx.coroutines.launch",
    ".doAfterTextChanged": "androidx.core.widget.doAfterTextChanged",
    ".isVisible": "androidx.core.view.isVisible",
    ".load": "coil.load",
    "LinearLayoutManager": "androidx.recyclerview.widget.LinearLayoutManager",
    "GridLayoutManager": "androidx.recyclerview.widget.GridLayoutManager",
    "Chip": "com.google.android.material.chip.Chip",
    "TabLayout": "com.google.android.material.tabs.TabLayout",
    "SupportMapFragment": "com.google.android.gms.maps.SupportMapFragment",
    "ExoPlayer": "androidx.media3.exoplayer.ExoPlayer",
    "R": "%PKG%.R",
    "Routes": "%PKG%.navigation.Routes",
    "Navigator": "%PKG%.navigation.Navigator",
    "BaseActivity": "%PKG%.ui.BaseActivity",
    "ListItemAdapter": "%PKG%.ui.components.ListItemAdapter",
    "ChartView": "%PKG%.ui.components.ChartView",
    "SignatureView": "%PKG%.ui.components.SignatureView",
    "Paint": "android.graphics.Paint",
    "IntentHelper": "%PKG%.util.IntentHelper",
    "PermissionHelper": "%PKG%.util.PermissionHelper",
    "StartupPermissions": "%PKG%.util.StartupPermissions",
    ".asPrice": "%PKG%.data.model.asPrice",
    "ListItem": "%PKG%.data.model.ListItem",
}


def generate(ctx):
    specs = [ScreenSpec(ctx, s) for s in ctx.project.screens]
    _base(ctx)
    _adapter(ctx)
    _navigator(ctx, specs)
    for spec in specs:
        ctx.add_kotlin(f"{ctx.screen_dir(spec.screen)}/{spec.cls}ViewModel.kt", viewmodel(ctx, spec))
        layout_name, layout_xml, wiring = _layout(ctx, spec)
        ctx.add_res(f"layout/{layout_name}.xml", layout_xml)
        ctx.add_kotlin(f"{ctx.screen_dir(spec.screen)}/{spec.cls}Activity.kt", _activity(ctx, spec, layout_name, wiring))


def finalize(ctx, body, package, extra=()):
    imports = collect_imports(body, IMPORTS, extra)
    if ctx.has_feature_files() and ".features." not in package:
        imports.append("%PKG%.features.*")
    imports = sorted({i.replace("%PKG%", ctx.pkg) for i in imports
                      if i.replace("%PKG%", ctx.pkg).rsplit(".", 1)[0] != package})
    imports = [i for i in imports if not i.endswith("getValue") and not i.endswith("setValue")]
    return f"package {package}\n\n" + "\n".join(f"import {i}" for i in imports) + "\n\n" + body.strip("\n") + "\n"


# ----------------------------------------------------------------- base

def _base(ctx):
    init = [line for f in ctx.resolved.features for line in f.activity_init]
    lines = "\n".join("        " + l for l in init) or "        // Configuracoes comuns a todas as telas podem ser adicionadas aqui."
    body = f'''/** Activity base de todas as telas: aplica configuracoes globais de janela. */
abstract class BaseActivity : AppCompatActivity() {{

    override fun onCreate(savedInstanceState: Bundle?) {{
        super.onCreate(savedInstanceState)
{lines}
    }}
}}
'''
    ctx.add_kotlin("ui/BaseActivity.kt", finalize(ctx, body, f"{ctx.pkg}.ui"))


def _adapter(ctx):
    ctx.add_kotlin("ui/components/ListItemAdapter.kt", '''package %PKG%.ui.components

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.ImageView
import android.widget.TextView
import androidx.core.view.isVisible
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import coil.load
import %PKG%.R
import %PKG%.data.model.ListItem
import %PKG%.data.model.asPrice

/**
 * Adapter generico para listas, grades e carrosseis de ListItem.
 * [layoutRes] escolhe o visual do item; [widthDp] e [heightDp] (quando maiores que zero)
 * fixam o tamanho do item, util em listas horizontais.
 */
class ListItemAdapter(
    private val layoutRes: Int,
    private val showImage: Boolean,
    private val showPrice: Boolean,
    private val onClick: ((ListItem) -> Unit)?,
    private val widthDp: Int = 0,
    private val heightDp: Int = 0
) : ListAdapter<ListItem, ListItemAdapter.Holder>(Diff) {

    class Holder(view: View) : RecyclerView.ViewHolder(view) {
        val image: ImageView = view.findViewById(R.id.item_image)
        val initial: TextView = view.findViewById(R.id.item_initial)
        val title: TextView = view.findViewById(R.id.item_title)
        val subtitle: TextView = view.findViewById(R.id.item_subtitle)
        val price: TextView = view.findViewById(R.id.item_price)
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): Holder {
        val view = LayoutInflater.from(parent.context).inflate(layoutRes, parent, false)
        val density = parent.resources.displayMetrics.density
        if (widthDp > 0) view.layoutParams.width = (widthDp * density).toInt()
        if (heightDp > 0) view.layoutParams.height = (heightDp * density).toInt()
        return Holder(view)
    }

    override fun onBindViewHolder(holder: Holder, position: Int) {
        val item = getItem(position)
        holder.title.text = item.title
        holder.subtitle.text = item.subtitle
        holder.subtitle.isVisible = item.subtitle.isNotBlank()
        holder.price.text = item.price.asPrice()
        holder.price.isVisible = showPrice && item.price != null
        val hasImage = showImage && item.imageUrl.isNotBlank()
        holder.image.isVisible = hasImage
        holder.initial.isVisible = showImage && !hasImage
        holder.initial.text = item.title.take(1).uppercase()
        if (hasImage) holder.image.load(item.imageUrl) { crossfade(true) }
        holder.itemView.setOnClickListener(onClick?.let { callback -> View.OnClickListener { callback(item) } })
    }

    private object Diff : DiffUtil.ItemCallback<ListItem>() {
        override fun areItemsTheSame(oldItem: ListItem, newItem: ListItem) = oldItem.id == newItem.id
        override fun areContentsTheSame(oldItem: ListItem, newItem: ListItem) = oldItem == newItem
    }
}
''')
    ctx.add_res("layout/item_list_row.xml", '''<?xml version="1.0" encoding="utf-8"?>
<!-- Linha de lista: imagem (ou inicial), titulo, subtitulo e preco. -->
<com.google.android.material.card.MaterialCardView xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:layout_marginBottom="8dp">

    <LinearLayout
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:gravity="center_vertical"
        android:orientation="horizontal"
        android:padding="12dp">

        <FrameLayout
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:layout_marginEnd="12dp">

            <ImageView
                android:id="@+id/item_image"
                android:layout_width="56dp"
                android:layout_height="56dp"
                android:contentDescription="@null"
                android:scaleType="centerCrop" />

            <TextView
                android:id="@+id/item_initial"
                android:layout_width="56dp"
                android:layout_height="56dp"
                android:background="@drawable/bg_avatar"
                android:gravity="center"
                android:textColor="@color/white"
                android:textSize="20sp"
                android:textStyle="bold" />
        </FrameLayout>

        <LinearLayout
            android:layout_width="0dp"
            android:layout_height="wrap_content"
            android:layout_weight="1"
            android:orientation="vertical">

            <TextView
                android:id="@+id/item_title"
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:maxLines="2"
                android:textAppearance="?attr/textAppearanceTitleMedium" />

            <TextView
                android:id="@+id/item_subtitle"
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:maxLines="2"
                android:textAppearance="?attr/textAppearanceBodySmall" />
        </LinearLayout>

        <TextView
            android:id="@+id/item_price"
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:textAppearance="?attr/textAppearanceTitleSmall"
            android:textColor="?attr/colorPrimary" />
    </LinearLayout>
</com.google.android.material.card.MaterialCardView>''')
    ctx.add_res("layout/item_grid_card.xml", '''<?xml version="1.0" encoding="utf-8"?>
<!-- Cartao de grade: imagem grande, titulo, subtitulo e preco. -->
<com.google.android.material.card.MaterialCardView xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:layout_margin="4dp">

    <LinearLayout
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:orientation="vertical">

        <FrameLayout
            android:layout_width="match_parent"
            android:layout_height="120dp">

            <ImageView
                android:id="@+id/item_image"
                android:layout_width="match_parent"
                android:layout_height="match_parent"
                android:contentDescription="@null"
                android:scaleType="centerCrop" />

            <TextView
                android:id="@+id/item_initial"
                android:layout_width="match_parent"
                android:layout_height="match_parent"
                android:background="?attr/colorPrimaryContainer"
                android:gravity="center"
                android:textSize="28sp"
                android:textStyle="bold" />
        </FrameLayout>

        <TextView
            android:id="@+id/item_title"
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:maxLines="2"
            android:paddingStart="10dp"
            android:paddingEnd="10dp"
            android:paddingTop="8dp"
            android:textAppearance="?attr/textAppearanceTitleSmall" />

        <TextView
            android:id="@+id/item_subtitle"
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:maxLines="1"
            android:paddingStart="10dp"
            android:paddingEnd="10dp"
            android:textAppearance="?attr/textAppearanceBodySmall" />

        <TextView
            android:id="@+id/item_price"
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:paddingStart="10dp"
            android:paddingEnd="10dp"
            android:paddingBottom="8dp"
            android:textColor="?attr/colorPrimary"
            android:textStyle="bold" />
    </LinearLayout>
</com.google.android.material.card.MaterialCardView>''')
    ctx.add_res("layout/item_carousel.xml", '''<?xml version="1.0" encoding="utf-8"?>
<!-- Cartao de carrossel: imagem de fundo com titulo sobreposto. -->
<com.google.android.material.card.MaterialCardView xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="300dp"
    android:layout_height="180dp"
    android:layout_marginEnd="12dp">

    <FrameLayout
        android:layout_width="match_parent"
        android:layout_height="match_parent">

        <ImageView
            android:id="@+id/item_image"
            android:layout_width="match_parent"
            android:layout_height="match_parent"
            android:contentDescription="@null"
            android:scaleType="centerCrop" />

        <TextView
            android:id="@+id/item_initial"
            android:layout_width="match_parent"
            android:layout_height="match_parent"
            android:background="?attr/colorPrimary"
            android:gravity="center"
            android:textColor="?attr/colorOnPrimary"
            android:textSize="40sp"
            android:textStyle="bold" />

        <LinearLayout
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:layout_gravity="bottom"
            android:background="@drawable/bg_scrim"
            android:orientation="vertical"
            android:padding="14dp">

            <TextView
                android:id="@+id/item_title"
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:maxLines="1"
                android:textColor="#FFFFFF"
                android:textAppearance="?attr/textAppearanceTitleMedium"
                android:textStyle="bold" />

            <TextView
                android:id="@+id/item_subtitle"
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:maxLines="1"
                android:textColor="#FFFFFF"
                android:textAppearance="?attr/textAppearanceBodySmall" />

            <TextView
                android:id="@+id/item_price"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:textColor="#FFFFFF"
                android:textStyle="bold" />
        </LinearLayout>
    </FrameLayout>
</com.google.android.material.card.MaterialCardView>
''')
    if any(c.type == "signature" for sc in ctx.project.screens for c in sc.components):
        ctx.add_kotlin("ui/components/SignatureView.kt", SIGNATURE_VIEW)



def _navigator(ctx, specs):
    p = ctx.project
    consts = "\n".join(f'    const val {ctx.route_const(s.screen.name)} = "{s.route}"' for s in specs)
    branches = "\n".join(f"        Routes.{ctx.route_const(s.screen.name)} -> {s.cls}Activity::class.java" for s in specs)
    nav = []
    if p.navigation in ("bottom", "drawer"):
        nav = [s for s in specs if s.screen.in_nav]
        if p.navigation == "bottom":
            nav = nav[:5]
    menu_fn = ""
    if nav:
        to_route = "\n".join(f"        R.id.nav_{s.route} -> Routes.{ctx.route_const(s.screen.name)}" for s in nav)
        to_menu = "\n".join(f"        Routes.{ctx.route_const(s.screen.name)} -> R.id.nav_{s.route}" for s in nav)
        menu_fn = f'''
    /** Rota correspondente a um item do menu principal. */
    fun routeForMenu(menuId: Int): String? = when (menuId) {{
{to_route}
        else -> null
    }}

    /** Id do item de menu de uma rota (ou 0 se a rota nao estiver no menu). */
    fun menuIdFor(route: String): Int = when (route) {{
{to_menu}
        else -> 0
    }}
'''
    body = f'''/** Rotas de todas as telas do app. */
object Routes {{
{consts}
}}

/** Navegacao entre Activities. O parametro itemId chega ao ViewModel pelo SavedStateHandle. */
object Navigator {{

    private fun activityFor(route: String): Class<out Activity>? = when (route) {{
{branches}
        else -> null
    }}

    /** Abre uma tela, opcionalmente com o id de um item. */
    fun open(activity: Activity, route: String, itemId: String? = null) {{
        val target = activityFor(route) ?: return
        val intent = Intent(activity, target)
        if (itemId != null) intent.putExtra("itemId", itemId)
        activity.startActivity(intent)
    }}

    /** Abre uma tela limpando o historico (login, logout, onboarding). */
    fun openRoot(activity: Activity, route: String) {{
        val target = activityFor(route) ?: return
        activity.startActivity(Intent(activity, target).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK))
    }}

    /** Troca entre telas do menu principal reaproveitando as ja abertas. */
    fun openTopLevel(activity: Activity, route: String) {{
        val target = activityFor(route) ?: return
        activity.startActivity(
            Intent(activity, target).addFlags(Intent.FLAG_ACTIVITY_REORDER_TO_FRONT or Intent.FLAG_ACTIVITY_NO_ANIMATION)
        )
    }}
{menu_fn}}}
'''
    extra = [f"{s.package}.{s.cls}Activity" for s in specs]
    ctx.add_kotlin("navigation/Navigator.kt", finalize(ctx, body, f"{ctx.pkg}.navigation", extra))


# ----------------------------------------------------------------- layouts

def _num(value, default, cast=int):
    try:
        return cast(value)
    except (TypeError, ValueError):
        return default


class Wiring:
    """Trechos de codigo Kotlin acumulados para a Activity."""

    def __init__(self):
        self.props = []
        self.setup = []
        self.render = []
        self.observe = []
        self.destroy = []
        self.imports = set()


def _layout(ctx, spec):
    p = ctx.project
    r = ctx.resolved
    w = Wiring()
    name = f"activity_{spec.route}"
    views = []
    sid = to_snake(spec.screen.name)
    list_by_comp = {lb.comp.id: lb for lb in spec.lists}

    def s(hint, text, index):
        return "@string/" + ctx.string(f"{sid}_{index}_{hint}", text)

    for index, comp in enumerate(spec.components):
        if comp.type == "fab":
            continue
        cid = f"c{index}"
        x = _component_xml(ctx, spec, comp, index, cid, s, w, list_by_comp)
        if x:
            views.append(x)

    content = "\n\n".join(_indent(v, 20) for v in views)
    refresh = r.has("pull_to_refresh") and spec.lists
    scroll = f'''            <androidx.core.widget.NestedScrollView
                android:id="@+id/scroll"
                android:layout_width="match_parent"
                android:layout_height="match_parent"
                android:fillViewport="true">

                <LinearLayout
                    android:id="@+id/content"
                    android:layout_width="match_parent"
                    android:layout_height="wrap_content"
                    android:orientation="vertical"
                    android:padding="16dp">

{content}
                </LinearLayout>
            </androidx.core.widget.NestedScrollView>'''
    if refresh:
        scroll = ('            <androidx.swiperefreshlayout.widget.SwipeRefreshLayout\n'
                  '                android:id="@+id/swipe_refresh"\n'
                  '                android:layout_width="match_parent"\n'
                  '                android:layout_height="match_parent">\n\n' + _indent(scroll, 4) +
                  '\n            </androidx.swiperefreshlayout.widget.SwipeRefreshLayout>')
        w.setup.append("binding.swipeRefresh.setOnRefreshListener { viewModel.refresh() }")
        w.render.append("binding.swipeRefresh.isRefreshing = state.isLoading")
    fab = ""
    if spec.fab:
        icon = spec.fab.props.get("icon", "add")
        fab = f'''

            <com.google.android.material.floatingactionbutton.FloatingActionButton
                android:id="@+id/fab"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_gravity="bottom|end"
                android:layout_margin="16dp"
                android:contentDescription="@null"
                app:srcCompat="@drawable/ic_nav_{icon if icon in ICONS else 'add'}" />'''
        code = action_code(ctx, spec, spec.fab.props.get("action", "none"))
        if code:
            w.setup.append(f"binding.fab.setOnClickListener {{ {code} }}")
    nav_screens = [sc for sc in p.screens if sc.in_nav][: 5 if p.navigation == "bottom" else 99]
    bottom = ""
    if p.navigation == "bottom" and spec.screen in nav_screens:
        bottom = '''

        <com.google.android.material.bottomnavigation.BottomNavigationView
            android:id="@+id/bottom_nav"
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            app:menu="@menu/bottom_nav" />'''
    main = f'''    <LinearLayout
        android:layout_width="match_parent"
        android:layout_height="match_parent"
        android:fitsSystemWindows="true"
        android:orientation="vertical">

        <com.google.android.material.appbar.MaterialToolbar
            android:id="@+id/toolbar"
            android:layout_width="match_parent"
            android:layout_height="?attr/actionBarSize"
            android:background="?attr/colorPrimary"
            app:titleTextColor="?attr/colorOnPrimary" />

        <FrameLayout
            android:layout_width="match_parent"
            android:layout_height="0dp"
            android:layout_weight="1">

{scroll}{fab}
        </FrameLayout>{bottom}
    </LinearLayout>'''
    drawer = p.navigation == "drawer" and spec.screen in nav_screens and nav_screens
    header = '<?xml version="1.0" encoding="utf-8"?>\n' \
             f'<!-- Layout da tela "{xml_escape(spec.screen.title or spec.screen.name)}" gerado pelo DroidBlocks. -->\n'
    ns = ('xmlns:android="http://schemas.android.com/apk/res/android"\n'
          '    xmlns:app="http://schemas.android.com/apk/res-auto"')
    if drawer:
        xml = (header + f'<androidx.drawerlayout.widget.DrawerLayout {ns}\n    android:id="@+id/drawer_layout"\n'
               '    android:layout_width="match_parent"\n    android:layout_height="match_parent"\n'
               '    android:fitsSystemWindows="true">\n\n' + main + '''

    <com.google.android.material.navigation.NavigationView
        android:id="@+id/nav_view"
        android:layout_width="wrap_content"
        android:layout_height="match_parent"
        android:layout_gravity="start"
        app:menu="@menu/drawer_nav" />
</androidx.drawerlayout.widget.DrawerLayout>''')
    else:
        xml = header + f'<FrameLayout {ns}\n    android:layout_width="match_parent"\n    android:layout_height="match_parent">\n\n' + main + "\n</FrameLayout>"
    w.drawer = bool(drawer)
    w.bottom = bool(bottom)
    return name, xml, w


def _indent(text, n):
    pad = " " * n
    return "\n".join(pad + line if line.strip() else line for line in text.split("\n"))


def _tv(cid, text, appearance, extra=""):
    return f'''<TextView
    android:id="@+id/{cid}"
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:layout_marginBottom="12dp"
    android:text="{text}"
    android:textAppearance="?attr/{appearance}"{extra} />'''


def _component_xml(ctx, spec, comp, index, cid, s, w, list_by_comp):
    t = comp.type
    pr = comp.props
    field = spec.input_by_comp.get(comp.id)
    b = "binding." + _bind(cid)

    def act(prop="action"):
        return action_code(ctx, spec, pr.get(prop, "none"))

    if t == "title":
        app = {"large": "textAppearanceHeadlineSmall", "medium": "textAppearanceTitleLarge"}.get(pr.get("size"), "textAppearanceTitleMedium")
        extra = '\n    android:gravity="center"' if pr.get("align") == "center" else ""
        return _tv(cid, s("title", pr.get("text", ""), index), app, extra + '\n    android:textStyle="bold"')
    if t == "text":
        app = {"caption": "textAppearanceBodySmall", "emphasis": "textAppearanceTitleSmall"}.get(pr.get("style"), "textAppearanceBodyLarge")
        extra = '\n    android:gravity="center"' if pr.get("align") == "center" else ""
        return _tv(cid, s("text", pr.get("text", ""), index), app, extra)
    if t == "button":
        style = {"outlined": "\n    style=\"@style/Widget.Material3.Button.OutlinedButton\"",
                 "tonal": "\n    style=\"@style/Widget.Material3.Button.TonalButton\"",
                 "text": "\n    style=\"@style/Widget.Material3.Button.TextButton\""}.get(pr.get("style"), "")
        code = act()
        if code:
            w.setup.append(f"{b}.setOnClickListener {{ {code} }}")
        return f'''<com.google.android.material.button.MaterialButton
    android:id="@+id/{cid}"{style}
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:layout_marginBottom="8dp"
    android:text="{s("button", pr.get("text", ""), index)}" />'''
    if t == "image":
        height = _num(pr.get("height"), 180)
        if pr.get("source") == "photo":
            w.render.append(f"if (state.photoUri.isNotBlank()) {b}.load(state.photoUri)")
        else:
            w.setup.append(f"{b}.load({kq(pr.get('url', ''))})")
        return f'''<ImageView
    android:id="@+id/{cid}"
    android:layout_width="match_parent"
    android:layout_height="{height}dp"
    android:layout_marginBottom="12dp"
    android:background="?attr/colorSurfaceVariant"
    android:contentDescription="{xml_escape(pr.get("description", "Imagem"))}"
    android:scaleType="centerCrop" />'''
    if t in ("card", "stat_card"):
        if t == "card":
            title, body = s("card_title", pr.get("title", ""), index), s("card_body", pr.get("body", ""), index)
            app1, app2, bg = "textAppearanceTitleMedium", "textAppearanceBodyMedium", ""
            code = act()
            if code:
                w.setup.append(f"{b}.setOnClickListener {{ {code} }}")
        else:
            title, body = s("stat_label", pr.get("label", ""), index), s("stat_value", pr.get("value", ""), index)
            app1, app2 = "textAppearanceLabelLarge", "textAppearanceHeadlineMedium"
            bg = '\n    app:cardBackgroundColor="?attr/colorPrimaryContainer"'
        return f'''<com.google.android.material.card.MaterialCardView
    android:id="@+id/{cid}"
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:layout_marginBottom="12dp"{bg}>

    <LinearLayout
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:orientation="vertical"
        android:padding="16dp">

        <TextView
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:text="{title}"
            android:textAppearance="?attr/{app1}" />

        <TextView
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:text="{body}"
            android:textAppearance="?attr/{app2}" />
    </LinearLayout>
</com.google.android.material.card.MaterialCardView>'''
    if t == "banner":
        code = act()
        if code:
            w.setup.append(f"{b}.setOnClickListener {{ {code} }}")
        return f'''<LinearLayout
    android:id="@+id/{cid}"
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:layout_marginBottom="12dp"
    android:background="@drawable/bg_banner"
    android:orientation="vertical"
    android:padding="20dp">

    <TextView
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:text="{s("banner_title", pr.get("title", ""), index)}"
        android:textColor="@color/white"
        android:textSize="20sp"
        android:textStyle="bold" />

    <TextView
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:text="{s("banner_subtitle", pr.get("subtitle", ""), index)}"
        android:textColor="@color/white" />
</LinearLayout>'''
    if t in ("text_field", "search_bar"):
        kind = pr.get("input", "text") if t == "text_field" else "text"
        input_type = {"email": "textEmailAddress", "number": "numberDecimal|numberSigned", "phone": "phone",
                      "password": "textPassword", "multiline": "textMultiLine|textCapSentences"}.get(kind, "text")
        extra = '\n    app:endIconMode="password_toggle"' if kind == "password" else ""
        if t == "search_bar":
            extra = '\n    app:startIconDrawable="@android:drawable/ic_menu_search"'
            hint = s("hint", pr.get("hint", ""), index)
            w.setup.append(f"{b}Input.doAfterTextChanged {{ viewModel.onQueryChange(it?.toString().orEmpty()) }}")
            w.render.append(f"if ({b}Input.text?.toString() != state.query) {b}Input.setText(state.query)")
        else:
            hint = s("label", pr.get("label", ""), index)
            if field:
                w.setup.append(f"{b}Input.doAfterTextChanged {{ viewModel.{field.setter}(it?.toString().orEmpty()) }}")
                w.render.append(f"if ({b}Input.text?.toString() != state.{field.key}) {b}Input.setText(state.{field.key})")
                w.render.append(f'{b}.error = if ("{field.key}" in state.errors) "Valor invalido" else null')
        lines = '\n        android:minLines="3"\n        android:gravity="top"' if kind == "multiline" else ""
        return f'''<com.google.android.material.textfield.TextInputLayout
    android:id="@+id/{cid}"
    style="@style/Widget.Material3.TextInputLayout.OutlinedBox"
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:layout_marginBottom="12dp"
    android:hint="{hint}"{extra}>

    <com.google.android.material.textfield.TextInputEditText
        android:id="@+id/{cid}_input"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:inputType="{input_type}"{lines} />
</com.google.android.material.textfield.TextInputLayout>'''
    if t in ("checkbox", "switch") and field:
        widget = "com.google.android.material.checkbox.MaterialCheckBox" if t == "checkbox" else \
            "com.google.android.material.materialswitch.MaterialSwitch"
        w.setup.append(f"{b}.setOnCheckedChangeListener {{ _, checked -> viewModel.{field.setter}(checked) }}")
        return f'''<{widget}
    android:id="@+id/{cid}"
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:layout_marginBottom="8dp"
    android:text="{s("label", pr.get("label", ""), index)}" />'''
    if t == "slider" and field:
        low, high = _num(pr.get("min"), 0.0, float), _num(pr.get("max"), 100.0, float)
        if high <= low:
            high = low + 1
        label = pr.get("label", "")
        w.setup.append(f"{b}.addOnChangeListener {{ _, value, _ -> viewModel.{field.setter}(value) }}")
        w.render.append(f'{b}Label.text = {kq(label + ": ")} + state.{field.key}.toInt()')
        return f'''<TextView
    android:id="@+id/{cid}_label"
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:textAppearance="?attr/textAppearanceTitleSmall" />

<com.google.android.material.slider.Slider
    android:id="@+id/{cid}"
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:layout_marginBottom="8dp"
    android:valueFrom="{low}"
    android:valueTo="{high}" />'''
    if t == "radio_group" and field:
        opts = options_of(comp)
        buttons = "\n\n".join(f'''    <RadioButton
        android:id="@+id/{cid}_o{i}"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:text="{xml_escape(o)}" />''' for i, o in enumerate(opts))
        branches = "; ".join(f"R.id.{cid}_o{i} -> {kq(o)}" for i, o in enumerate(opts))
        w.setup.append(f"{b}.setOnCheckedChangeListener {{ _, checkedId -> viewModel.{field.setter}(when (checkedId) {{ {branches}; else -> \"\" }}) }}")
        checked = f'\n    android:checkedButton="@+id/{cid}_o0"' if opts else ""
        return f'''<TextView
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:text="{s("label", pr.get("label", ""), index)}"
    android:textAppearance="?attr/textAppearanceTitleSmall" />

<RadioGroup
    android:id="@+id/{cid}"
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:layout_marginBottom="12dp"{checked}>

{buttons}
</RadioGroup>'''
    if t == "dropdown" and field:
        opts = options_of(comp)
        arr = "arrayOf(" + ", ".join(kq(o) for o in opts) + ")"
        w.setup.append(f"{b}Input.setSimpleItems({arr})")
        if opts:
            w.setup.append(f"{b}Input.setText({kq(opts[0])}, false)")
        w.setup.append(f"{b}Input.setOnItemClickListener {{ _, _, position, _ -> viewModel.{field.setter}({arr}[position]) }}")
        return f'''<com.google.android.material.textfield.TextInputLayout
    android:id="@+id/{cid}"
    style="@style/Widget.Material3.TextInputLayout.OutlinedBox.ExposedDropdownMenu"
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:layout_marginBottom="12dp"
    android:hint="{s("label", pr.get("label", ""), index)}">

    <com.google.android.material.textfield.MaterialAutoCompleteTextView
        android:id="@+id/{cid}_input"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:inputType="none" />
</com.google.android.material.textfield.TextInputLayout>'''
    if t == "chips" and field:
        opts = options_of(comp)
        chips = "\n\n".join(f'''        <com.google.android.material.chip.Chip
            android:id="@+id/{cid}_o{i}"
            style="@style/Widget.Material3.Chip.Filter"
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:checked="{"true" if i == 0 else "false"}"
            android:text="{xml_escape(o)}" />''' for i, o in enumerate(opts))
        w.setup.append(f"{b}.setOnCheckedStateChangeListener {{ group, ids -> "
                       f"viewModel.{field.setter}(ids.firstOrNull()?.let {{ group.findViewById<Chip>(it).text.toString() }} ?: \"\") }}")
        return f'''<HorizontalScrollView
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:layout_marginBottom="8dp"
    android:scrollbars="none">

    <com.google.android.material.chip.ChipGroup
        android:id="@+id/{cid}"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        app:selectionRequired="true"
        app:singleLine="true"
        app:singleSelection="true">

{chips}
    </com.google.android.material.chip.ChipGroup>
</HorizontalScrollView>'''
    if t == "tabs" and field:
        opts = options_of(comp)
        items = "\n\n".join(f'''    <com.google.android.material.tabs.TabItem
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="{xml_escape(o)}" />''' for o in opts)
        w.setup.append(f'''{b}.addOnTabSelectedListener(object : TabLayout.OnTabSelectedListener {{
    override fun onTabSelected(tab: TabLayout.Tab) {{
        viewModel.{field.setter}(tab.text?.toString().orEmpty())
    }}

    override fun onTabUnselected(tab: TabLayout.Tab) = Unit

    override fun onTabReselected(tab: TabLayout.Tab) = Unit
}})''')
        return f'''<com.google.android.material.tabs.TabLayout
    android:id="@+id/{cid}"
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:layout_marginBottom="12dp"
    app:tabMode="scrollable">

{items}
</com.google.android.material.tabs.TabLayout>'''
    if t == "date_picker" and field:
        label = pr.get("label", "")
        w.setup.append(f'''{b}.setOnClickListener {{
    val now = Calendar.getInstance()
    DatePickerDialog(this, {{ _, year, month, day ->
        viewModel.{field.setter}("%02d/%02d/%04d".format(day, month + 1, year))
    }}, now.get(Calendar.YEAR), now.get(Calendar.MONTH), now.get(Calendar.DAY_OF_MONTH)).show()
}}''')
        w.render.append(f'{b}.text = if (state.{field.key}.isBlank()) {kq(label)} else {kq(label + ": ")} + state.{field.key}')
        return f'''<com.google.android.material.button.MaterialButton
    android:id="@+id/{cid}"
    style="@style/Widget.Material3.Button.OutlinedButton"
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:layout_marginBottom="8dp"
    android:text="{s("label", label, index)}" />'''
    if t == "rating" and field:
        w.setup.append(f"{b}.setOnRatingBarChangeListener {{ _, rating, _ -> viewModel.{field.setter}(rating.toInt()) }}")
        return f'''<TextView
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:text="{s("label", pr.get("label", ""), index)}"
    android:textAppearance="?attr/textAppearanceTitleSmall" />

<RatingBar
    android:id="@+id/{cid}"
    android:layout_width="wrap_content"
    android:layout_height="wrap_content"
    android:layout_marginBottom="12dp"
    android:numStars="{_num(pr.get("max"), 5)}"
    android:stepSize="1" />'''
    if t == "stepper" and field:
        mx = _num(pr.get("max"), 99)
        w.setup.append(f"{b}Minus.setOnClickListener {{ viewModel.{field.setter}((viewModel.uiState.value.{field.key} - 1).coerceAtLeast(0)) }}")
        w.setup.append(f"{b}Plus.setOnClickListener {{ viewModel.{field.setter}((viewModel.uiState.value.{field.key} + 1).coerceAtMost({mx})) }}")
        w.render.append(f"{b}Value.text = state.{field.key}.toString()")
        return f'''<LinearLayout
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:layout_marginBottom="12dp"
    android:gravity="center_vertical"
    android:orientation="horizontal">

    <TextView
        android:layout_width="0dp"
        android:layout_height="wrap_content"
        android:layout_weight="1"
        android:text="{s("label", pr.get("label", ""), index)}"
        android:textAppearance="?attr/textAppearanceTitleSmall" />

    <com.google.android.material.button.MaterialButton
        android:id="@+id/{cid}_minus"
        style="@style/Widget.Material3.Button.OutlinedButton"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="-" />

    <TextView
        android:id="@+id/{cid}_value"
        android:layout_width="48dp"
        android:layout_height="wrap_content"
        android:gravity="center"
        android:textAppearance="?attr/textAppearanceTitleMedium" />

    <com.google.android.material.button.MaterialButton
        android:id="@+id/{cid}_plus"
        style="@style/Widget.Material3.Button.OutlinedButton"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="+" />
</LinearLayout>'''
    if t == "calendar" and field:
        w.setup.append(f'{b}.setOnDateChangeListener {{ _, year, month, day -> viewModel.{field.setter}("%02d/%02d/%04d".format(day, month + 1, year)) }}')
        return f'''<CalendarView
    android:id="@+id/{cid}"
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:layout_marginBottom="12dp" />'''
    if t == "expandable":
        w.setup.append(f"""{b}Header.setOnClickListener {{
    {b}Body.isVisible = !{b}Body.isVisible
    {b}Sign.text = if ({b}Body.isVisible) "-" else "+"
}}""")
        return f'''<com.google.android.material.card.MaterialCardView
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:layout_marginBottom="12dp">

    <LinearLayout
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:orientation="vertical"
        android:padding="16dp">

        <LinearLayout
            android:id="@+id/{cid}_header"
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:gravity="center_vertical"
            android:orientation="horizontal">

            <TextView
                android:layout_width="0dp"
                android:layout_height="wrap_content"
                android:layout_weight="1"
                android:text="{s("exp_title", pr.get("title", ""), index)}"
                android:textAppearance="?attr/textAppearanceTitleMedium" />

            <TextView
                android:id="@+id/{cid}_sign"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:text="+"
                android:textAppearance="?attr/textAppearanceTitleLarge"
                android:textColor="?attr/colorPrimary" />
        </LinearLayout>

        <TextView
            android:id="@+id/{cid}_body"
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:paddingTop="8dp"
            android:text="{s("exp_body", pr.get("body", ""), index)}"
            android:textAppearance="?attr/textAppearanceBodyMedium"
            android:visibility="gone" />
    </LinearLayout>
</com.google.android.material.card.MaterialCardView>'''
    if t == "key_value":
        rows = []
        for line in str(pr.get("rows", "")).splitlines():
            if not line.strip():
                continue
            label, _, value = line.partition(":")
            rows.append(f'''        <LinearLayout
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:orientation="horizontal"
            android:paddingTop="6dp">

            <TextView
                android:layout_width="0dp"
                android:layout_height="wrap_content"
                android:layout_weight="1"
                android:text="{xml_escape(label.strip())}"
                android:textColor="?attr/colorOnSurfaceVariant" />

            <TextView
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:text="{xml_escape(value.strip())}"
                android:textStyle="bold" />
        </LinearLayout>''')
        title = pr.get("title", "")
        head = (f'''        <TextView
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:text="{s("kv_title", title, index)}"
            android:textAppearance="?attr/textAppearanceTitleMedium" />\n\n''' if title else "")
        return f'''<com.google.android.material.card.MaterialCardView
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:layout_marginBottom="12dp">

    <LinearLayout
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:orientation="vertical"
        android:padding="16dp">

{head}{chr(10).join(rows)}
    </LinearLayout>
</com.google.android.material.card.MaterialCardView>'''
    if t == "steps":
        current = _num(pr.get("current"), 1)
        items = []
        for i, label in enumerate(options_of(comp)):
            on = i < current
            items.append(f'''    <LinearLayout
        android:layout_width="0dp"
        android:layout_height="wrap_content"
        android:layout_weight="1"
        android:gravity="center_horizontal"
        android:orientation="vertical">

        <TextView
            android:layout_width="32dp"
            android:layout_height="32dp"
            android:background="@drawable/{"bg_step_on" if on else "bg_step_off"}"
            android:gravity="center"
            android:text="{i + 1}"
            android:textColor="?attr/{"colorOnPrimary" if on else "colorOnSurfaceVariant"}" />

        <TextView
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:gravity="center"
            android:maxLines="2"
            android:paddingTop="4dp"
            android:text="{xml_escape(label)}"
            android:textAppearance="?attr/textAppearanceLabelSmall" />
    </LinearLayout>''')
        return f'''<LinearLayout
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:layout_marginBottom="12dp"
    android:orientation="horizontal">

{chr(10).join(items)}
</LinearLayout>'''
    if t == "alert":
        kind = pr.get("kind", "info") if pr.get("kind") in ("info", "success", "warning", "error") else "info"
        color = {"info": "#0D3B66", "success": "#1B5E20", "warning": "#7A5900", "error": "#8C1D18"}[kind]
        return f'''<TextView
    android:id="@+id/{cid}"
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:layout_marginBottom="12dp"
    android:background="@drawable/bg_alert_{kind}"
    android:padding="14dp"
    android:text="{s("alert", pr.get("text", ""), index)}"
    android:textColor="{color}" />'''
    if t == "button_row":
        for n in ("1", "2"):
            code = act("action" + n)
            if code:
                w.setup.append(f"{b}B{n}.setOnClickListener {{ {code} }}")
        return f'''<LinearLayout
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:layout_marginBottom="8dp"
    android:orientation="horizontal">

    <com.google.android.material.button.MaterialButton
        android:id="@+id/{cid}_b1"
        style="@style/Widget.Material3.Button.OutlinedButton"
        android:layout_width="0dp"
        android:layout_height="wrap_content"
        android:layout_marginEnd="6dp"
        android:layout_weight="1"
        android:text="{s("button1", pr.get("text1", ""), index)}" />

    <com.google.android.material.button.MaterialButton
        android:id="@+id/{cid}_b2"
        android:layout_width="0dp"
        android:layout_height="wrap_content"
        android:layout_marginStart="6dp"
        android:layout_weight="1"
        android:text="{s("button2", pr.get("text2", ""), index)}" />
</LinearLayout>'''
    if t == "signature":
        w.setup.append(f"{b}Clear.setOnClickListener {{ {b}.clear() }}")
        return f'''<LinearLayout
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:gravity="center_vertical"
    android:orientation="horizontal">

    <TextView
        android:layout_width="0dp"
        android:layout_height="wrap_content"
        android:layout_weight="1"
        android:text="{s("label", pr.get("label", ""), index)}"
        android:textAppearance="?attr/textAppearanceTitleSmall" />

    <com.google.android.material.button.MaterialButton
        android:id="@+id/{cid}_clear"
        style="@style/Widget.Material3.Button.TextButton"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="Limpar" />
</LinearLayout>

<{ctx.pkg}.ui.components.SignatureView
    android:id="@+id/{cid}"
    android:layout_width="match_parent"
    android:layout_height="{_num(pr.get("height"), 180)}dp"
    android:layout_marginBottom="12dp"
    android:background="?attr/colorSurfaceVariant" />'''
    if t == "quote":
        author = pr.get("author", "")
        author_xml = (f'''

        <TextView
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:paddingTop="8dp"
            android:text="- {xml_escape(author)}"
            android:textColor="?attr/colorPrimary" />''' if author else "")
        return f'''<com.google.android.material.card.MaterialCardView
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:layout_marginBottom="12dp">

    <LinearLayout
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:orientation="vertical"
        android:padding="16dp">

        <TextView
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:text="{s("quote", pr.get("text", ""), index)}"
            android:textAppearance="?attr/textAppearanceBodyLarge"
            android:textStyle="italic" />{author_xml}
    </LinearLayout>
</com.google.android.material.card.MaterialCardView>'''
    if t == "tags":
        chips = "\n\n".join(f'''        <com.google.android.material.chip.Chip
            style="@style/Widget.Material3.Chip.Assist"
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:checkable="false"
            android:clickable="false"
            android:text="{xml_escape(o)}" />''' for o in options_of(comp))
        return f'''<HorizontalScrollView
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:layout_marginBottom="8dp"
    android:scrollbars="none">

    <com.google.android.material.chip.ChipGroup
        android:id="@+id/{cid}"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        app:singleLine="true">

{chips}
    </com.google.android.material.chip.ChipGroup>
</HorizontalScrollView>'''
    if t == "price_tag":
        old_value = pr.get("old_value", "")
        old_xml = ""
        if old_value:
            w.setup.append(f"{b}Old.paintFlags = {b}Old.paintFlags or Paint.STRIKE_THRU_TEXT_FLAG")
            old_xml = f'''

        <TextView
            android:id="@+id/{cid}_old"
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:paddingStart="8dp"
            android:text="{xml_escape(old_value)}"
            android:textColor="?attr/colorOnSurfaceVariant" />'''
        return f'''<LinearLayout
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:layout_marginBottom="12dp"
    android:orientation="vertical">

    <TextView
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="{s("price_label", pr.get("label", ""), index)}"
        android:textColor="?attr/colorOnSurfaceVariant" />

    <LinearLayout
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:gravity="bottom"
        android:orientation="horizontal">

        <TextView
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:text="{xml_escape(pr.get("value", ""))}"
            android:textAppearance="?attr/textAppearanceHeadlineMedium"
            android:textColor="?attr/colorPrimary"
            android:textStyle="bold" />{old_xml}
    </LinearLayout>
</LinearLayout>'''
    if t == "social_links":
        links = [("whatsapp", "WhatsApp", lambda v: f"IntentHelper.whatsapp(this, {kq(v)})"),
                 ("instagram", "Instagram",
                  lambda v: f"IntentHelper.openUrl(this, {kq('https://instagram.com/' + v.lstrip('@'))})"),
                 ("website", "Site", lambda v: f"IntentHelper.openUrl(this, {kq(v)})")]
        buttons = []
        for key, label, code in links:
            value = str(pr.get(key, "")).strip()
            if not value:
                continue
            w.setup.append(f"{b}{key.capitalize()}.setOnClickListener {{ {code(value)} }}")
            buttons.append(f'''    <com.google.android.material.button.MaterialButton
        android:id="@+id/{cid}_{key}"
        style="@style/Widget.Material3.Button.OutlinedButton"
        android:layout_width="0dp"
        android:layout_height="wrap_content"
        android:layout_marginEnd="4dp"
        android:layout_weight="1"
        android:text="{label}" />''')
        if not buttons:
            return None
        return f'''<LinearLayout
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:layout_marginBottom="8dp"
    android:orientation="horizontal">

{chr(10).join(buttons)}
</LinearLayout>'''
    if comp.id in list_by_comp:
        lb = list_by_comp[comp.id]
        grid = t == "grid"
        cols = max(1, min(4, _num(pr.get("columns"), 2)))
        code = action_code(ctx, spec, pr.get("item_action", "none"), "item")
        click = f"{{ item -> {code} }}" if code else "null"
        image = "true" if (t != "list" or pr.get("show_image", True)) else "false"
        price = "true" if pr.get("show_price") else "false"
        size = ""
        if t == "carousel":
            layout = "R.layout.item_carousel"
            size = f", widthDp = 300, heightDp = {_num(pr.get('height'), 180)}"
        elif t == "h_list":
            layout = "R.layout.item_grid_card"
            size = ", widthDp = 150"
        else:
            layout = "R.layout.item_grid_card" if grid else "R.layout.item_list_row"
        w.props.append(f"private val list{lb.index}Adapter = ListItemAdapter({layout}, "
                       f"showImage = {image}, showPrice = {price}, onClick = {click}{size})")
        if t in ("carousel", "h_list"):
            manager = "LinearLayoutManager(this, LinearLayoutManager.HORIZONTAL, false)"
        else:
            manager = f"GridLayoutManager(this, {cols})" if grid else "LinearLayoutManager(this)"
        w.setup.append(f"{b}.layoutManager = {manager}")
        w.setup.append(f"{b}.adapter = list{lb.index}Adapter")
        w.render.append(f"list{lb.index}Adapter.submitList(state.{lb.visible})")
        w.render.append(f"{b}Empty.isVisible = state.{lb.visible}.isEmpty() && !state.isLoading")
        skeleton = ""
        if "skeleton" in ctx.resolved.flags:
            w.render.append(f"{b}Skeleton.isVisible = state.{lb.visible}.isEmpty() && state.isLoading")
            rows = 1 if t in ("carousel", "h_list") else 4
            w.setup.append(f"{b}Skeleton.rows = {rows}")
            skeleton = f'''<{ctx.pkg}.features.SkeletonView
    android:id="@+id/{cid}_skeleton"
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:layout_marginBottom="12dp"
    android:visibility="gone" />

'''
        return skeleton + f'''<TextView
    android:id="@+id/{cid}_empty"
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:gravity="center"
    android:padding="24dp"
    android:text="{xml_escape(pr.get("empty_text", "Nenhum item encontrado"))}"
    android:visibility="gone" />

<androidx.recyclerview.widget.RecyclerView
    android:id="@+id/{cid}"
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:layout_marginBottom="12dp"
    android:nestedScrollingEnabled="false" />'''
    if t == "item_detail":
        show_image = bool(pr.get("show_image", True))
        show_price = bool(pr.get("show_price"))
        w.render.append(f'''state.selectedItem.let {{ item ->
    {b}Title.text = item?.title ?: "Nenhum item selecionado"
    {b}Subtitle.text = item?.subtitle.orEmpty()
    {b}Description.text = item?.description.orEmpty()
    {b}Price.isVisible = {str(show_price).lower()} && item?.price != null
    {b}Price.text = item?.price.asPrice()
    {b}Image.isVisible = {str(show_image).lower()} && !item?.imageUrl.isNullOrBlank()
    if (!item?.imageUrl.isNullOrBlank()) {b}Image.load(item?.imageUrl)
}}''')
        return f'''<LinearLayout
    android:id="@+id/{cid}"
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:layout_marginBottom="12dp"
    android:orientation="vertical">

    <ImageView
        android:id="@+id/{cid}_image"
        android:layout_width="match_parent"
        android:layout_height="220dp"
        android:layout_marginBottom="12dp"
        android:contentDescription="@null"
        android:scaleType="centerCrop" />

    <TextView
        android:id="@+id/{cid}_title"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:textAppearance="?attr/textAppearanceHeadlineSmall"
        android:textStyle="bold" />

    <TextView
        android:id="@+id/{cid}_subtitle"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:textAppearance="?attr/textAppearanceTitleSmall"
        android:textColor="?attr/colorPrimary" />

    <TextView
        android:id="@+id/{cid}_price"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:textAppearance="?attr/textAppearanceTitleLarge"
        android:textStyle="bold" />

    <TextView
        android:id="@+id/{cid}_description"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:layout_marginTop="8dp"
        android:textAppearance="?attr/textAppearanceBodyLarge" />
</LinearLayout>'''
    if t == "chart":
        values = []
        for v in str(pr.get("values", "")).split(","):
            try:
                values.append(f"{float(v.strip())}f")
            except ValueError:
                pass
        w.setup.append(f'{b}.style = {kq(pr.get("style", "bar"))}')
        w.setup.append(f"{b}.values = listOf({', '.join(values) or '1f'})")
        return f'''<{ctx.pkg}.ui.components.ChartView
    android:id="@+id/{cid}"
    android:layout_width="match_parent"
    android:layout_height="180dp"
    android:layout_marginBottom="12dp" />'''
    if t == "cart_summary":
        code = act()
        w.setup.append(f"{b}Button.setOnClickListener {{ {code} }}")
        w.observe.append(f'''launch {{
    CartManager.lines.collect {{ lines ->
        {b}Count.text = lines.sumOf {{ it.quantity }}.toString() + " itens"
        {b}Total.text = lines.sumOf {{ it.total }}.asPrice()
        {b}Button.isEnabled = lines.isNotEmpty()
    }}
}}''')
        return f'''<com.google.android.material.card.MaterialCardView
    android:id="@+id/{cid}"
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:layout_marginBottom="12dp">

    <LinearLayout
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:orientation="vertical"
        android:padding="16dp">

        <LinearLayout
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:orientation="horizontal">

            <TextView
                android:id="@+id/{cid}_count"
                android:layout_width="0dp"
                android:layout_height="wrap_content"
                android:layout_weight="1" />

            <TextView
                android:id="@+id/{cid}_total"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:textAppearance="?attr/textAppearanceTitleMedium"
                android:textStyle="bold" />
        </LinearLayout>

        <com.google.android.material.button.MaterialButton
            android:id="@+id/{cid}_button"
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:layout_marginTop="8dp"
            android:text="{s("button", pr.get("button", "Finalizar"), index)}" />
    </LinearLayout>
</com.google.android.material.card.MaterialCardView>'''
    if t == "avatar":
        name = pr.get("name", "")
        initials = "".join(part[:1].upper() for part in name.split()[:2])
        return f'''<LinearLayout
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:layout_marginBottom="12dp"
    android:gravity="center_vertical"
    android:orientation="horizontal">

    <TextView
        android:layout_width="64dp"
        android:layout_height="64dp"
        android:layout_marginEnd="16dp"
        android:background="@drawable/bg_avatar"
        android:gravity="center"
        android:text="{xml_escape(initials)}"
        android:textColor="@color/white"
        android:textSize="22sp" />

    <LinearLayout
        android:layout_width="0dp"
        android:layout_height="wrap_content"
        android:layout_weight="1"
        android:orientation="vertical">

        <TextView
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:text="{s("avatar_name", name, index)}"
            android:textAppearance="?attr/textAppearanceTitleLarge" />

        <TextView
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:text="{s("avatar_subtitle", pr.get("subtitle", ""), index)}"
            android:textAppearance="?attr/textAppearanceBodyMedium" />
    </LinearLayout>
</LinearLayout>'''
    if t == "divider":
        return '''<com.google.android.material.divider.MaterialDivider
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:layout_marginTop="8dp"
    android:layout_marginBottom="8dp" />'''
    if t == "spacer":
        return f'''<Space
    android:layout_width="match_parent"
    android:layout_height="{_num(pr.get("height"), 16)}dp" />'''
    if t == "progress":
        bound = bool(pr.get("bind_loading", True))
        if bound:
            w.render.append(f"{b}.isVisible = state.isLoading")
        if pr.get("style") == "circular":
            return f'''<com.google.android.material.progressindicator.CircularProgressIndicator
    android:id="@+id/{cid}"
    android:layout_width="wrap_content"
    android:layout_height="wrap_content"
    android:layout_gravity="center_horizontal"
    android:layout_marginBottom="12dp"
    android:indeterminate="true" />'''
        extra = 'android:indeterminate="true"' if bound else 'android:progress="50"'
        return f'''<com.google.android.material.progressindicator.LinearProgressIndicator
    android:id="@+id/{cid}"
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:layout_marginBottom="12dp"
    {extra} />'''
    if t == "web_view":
        w.setup.append(f"{b}.settings.javaScriptEnabled = true")
        w.setup.append(f"{b}.webViewClient = WebViewClient()")
        if ctx.resolved.has("webview_bridge"):
            w.setup.append(f'{b}.addJavascriptInterface(JsBridge(this), "App")')
        w.setup.append(f"{b}.loadUrl({kq(pr.get('url', ''))})")
        w.suppress_js = True
        return f'''<WebView
    android:id="@+id/{cid}"
    android:layout_width="match_parent"
    android:layout_height="{_num(pr.get("height"), 420)}dp"
    android:layout_marginBottom="12dp" />'''
    if t == "map_view":
        w.setup.append(f"(supportFragmentManager.findFragmentById(R.id.{cid}) as? SupportMapFragment)?.let {{ "
                       f"MapHelper.setup(it, {_num(pr.get('lat'), -23.55, float)}, {_num(pr.get('lng'), -46.63, float)}, "
                       f"{kq(pr.get('title', ''))}) }}")
        return f'''<androidx.fragment.app.FragmentContainerView
    android:id="@+id/{cid}"
    android:name="com.google.android.gms.maps.SupportMapFragment"
    android:layout_width="match_parent"
    android:layout_height="{_num(pr.get("height"), 260)}dp"
    android:layout_marginBottom="12dp" />'''
    if t == "video_player":
        w.props.append(f"private var player{index}: ExoPlayer? = null")
        w.setup.append(f"player{index} = VideoPlayerHelper.attach({b}, {kq(pr.get('url', ''))})")
        w.destroy.append(f"player{index}?.release()")
        return f'''<androidx.media3.ui.PlayerView
    android:id="@+id/{cid}"
    android:layout_width="match_parent"
    android:layout_height="{_num(pr.get("height"), 220)}dp"
    android:layout_marginBottom="12dp" />'''
    if t == "qr_code":
        size = _num(pr.get("size"), 200)
        w.setup.append(f"{b}.setImageBitmap(QrCodeGenerator.generate({kq(pr.get('text', ''))}, 512))")
        return f'''<ImageView
    android:id="@+id/{cid}"
    android:layout_width="{size}dp"
    android:layout_height="{size}dp"
    android:layout_gravity="center_horizontal"
    android:layout_marginBottom="12dp"
    android:contentDescription="QR Code" />'''
    if t == "timer":
        seconds = _num(pr.get("seconds"), 1500) if pr.get("mode") == "countdown" else 0
        w.props.append(f"private val timer{index} by lazy {{ TickTimer(lifecycleScope, {seconds}L) }}")
        w.setup.append(f"{b}Toggle.setOnClickListener {{ timer{index}.toggle() }}")
        w.setup.append(f"{b}Reset.setOnClickListener {{ timer{index}.reset() }}")
        w.observe.append(f"launch {{ timer{index}.seconds.collect {{ {b}Time.text = TickTimer.format(it) }} }}")
        w.observe.append(f'launch {{ timer{index}.running.collect {{ {b}Toggle.text = if (it) "Pausar" else "Iniciar" }} }}')
        return f'''<LinearLayout
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:layout_marginBottom="12dp"
    android:gravity="center_horizontal"
    android:orientation="vertical">

    <TextView
        android:id="@+id/{cid}_time"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:textAppearance="?attr/textAppearanceDisplayMedium"
        android:textStyle="bold" />

    <LinearLayout
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:orientation="horizontal">

        <com.google.android.material.button.MaterialButton
            android:id="@+id/{cid}_toggle"
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:layout_marginEnd="12dp"
            android:text="Iniciar" />

        <com.google.android.material.button.MaterialButton
            android:id="@+id/{cid}_reset"
            style="@style/Widget.Material3.Button.OutlinedButton"
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:text="Zerar" />
    </LinearLayout>
</LinearLayout>'''
    if t == "camera_preview":
        w.setup.append(f"CameraXHelper.start(this, {b})")
        return f'''<androidx.camera.view.PreviewView
    android:id="@+id/{cid}"
    android:layout_width="match_parent"
    android:layout_height="{_num(pr.get("height"), 320)}dp"
    android:layout_marginBottom="12dp" />'''
    if t == "lottie":
        w.setup.append(f"LottieHelper.play({b}, {kq(pr.get('url', ''))})")
        return f'''<com.airbnb.lottie.LottieAnimationView
    android:id="@+id/{cid}"
    android:layout_width="match_parent"
    android:layout_height="{_num(pr.get("height"), 200)}dp"
    android:layout_marginBottom="12dp" />'''
    return None


def _bind(view_id):
    """Nome do campo gerado pelo ViewBinding para um id snake_case."""
    parts = view_id.split("_")
    return parts[0] + "".join(p[:1].upper() + p[1:] for p in parts[1:])


# ----------------------------------------------------------------- activity

def _activity(ctx, spec, layout_name, w):
    p = ctx.project
    r = ctx.resolved
    start = p.get_start_screen()
    is_start = spec.screen is start
    binding_cls = to_pascal(layout_name) + "Binding"
    title_res = ctx.string(f"screen_{spec.route}", spec.screen.title or spec.screen.name)
    all_code = "\n".join(w.setup + w.render + w.observe + w.props)

    props = list(w.props)
    helpers = []
    if "context" in all_code:
        helpers.append("private val context: Context get() = this")
    if "scope." in all_code:
        helpers.append("private val scope get() = lifecycleScope")
    if "activity" in all_code.replace("Activity", ""):
        helpers.append("private val activity: Activity? get() = this")
    if "takePhoto()" in all_code:
        props.append("private val cameraCapture = CameraCaptureHelper(this) { uri -> viewModel.onPhotoSelected(uri?.toString()) }")
        helpers.append("private fun takePhoto() = cameraCapture.launch()")
    if "pickImage()" in all_code:
        props.append("private val imagePicker = ImagePickerHelper(this) { uri -> viewModel.onPhotoSelected(uri?.toString()) }")
        helpers.append("private fun pickImage() = imagePicker.launch()")
    if "pickFile()" in all_code:
        props.append("private val documentPicker = DocumentPickerHelper(this) { uri -> viewModel.onFilePicked(uri?.toString()) }")
        helpers.append("private fun pickFile() = documentPicker.launch()")
    if "listen()" in all_code:
        props.append("private val speech = SpeechToTextHelper(this) { text -> viewModel.onSpeechResult(text) }")
        helpers.append("private fun listen() = speech.launch()")
    if "onNavigate(" in all_code:
        helpers.append("private fun onNavigate(route: String, itemId: String?) = Navigator.open(this, route, itemId)")
    if "onNavigateRoot(" in all_code:
        helpers.append("private fun onNavigateRoot(route: String) = Navigator.openRoot(this, route)")
    if "onBack()" in all_code:
        helpers.append("private fun onBack() = finish()")
    if is_start:
        props.append("private val permissionLauncher =\n        registerForActivityResult(ActivityResultContracts.RequestMultiplePermissions()) { }")

    toolbar = [f"binding.toolbar.title = getString(R.string.{title_res})"]
    if not spec.is_top_level:
        toolbar += ["binding.toolbar.setNavigationIcon(R.drawable.ic_arrow_back)",
                    "binding.toolbar.setNavigationOnClickListener { finish() }"]
    if w.drawer:
        toolbar += ["binding.toolbar.setNavigationIcon(R.drawable.ic_menu)",
                    "binding.toolbar.setNavigationOnClickListener { binding.drawerLayout.open() }",
                    "binding.navView.setNavigationItemSelectedListener { item ->",
                    "    binding.drawerLayout.close()",
                    "    Navigator.routeForMenu(item.itemId)?.let { route ->",
                    f"        if (route != Routes.{ctx.route_const(spec.screen.name)}) Navigator.openTopLevel(this, route)",
                    "    }",
                    "    true",
                    "}"]
    if w.bottom:
        toolbar += [f"binding.bottomNav.selectedItemId = Navigator.menuIdFor(Routes.{ctx.route_const(spec.screen.name)})",
                    "binding.bottomNav.setOnItemSelectedListener { item ->",
                    "    Navigator.routeForMenu(item.itemId)?.let { route ->",
                    f"        if (route != Routes.{ctx.route_const(spec.screen.name)}) Navigator.openTopLevel(this, route)",
                    "    }",
                    "    true",
                    "}"]

    on_create = []
    if is_start and "splash" in r.flags:
        on_create.append("installSplashScreen()")
    on_create += ["super.onCreate(savedInstanceState)",
                  f"binding = {binding_cls}.inflate(layoutInflater)",
                  "setContentView(binding.root)",
                  "setupToolbar()", "setupViews()", "observeState()"]
    if is_start:
        on_create.append("requestStartupPermissions()")
        if "deep_links" in r.flags:
            on_create += ["DeepLinkParser.routeFrom(intent?.data)?.let { route ->",
                          '    Navigator.open(this, route.substringBefore("?"), intent?.data?.getQueryParameter("itemId"))',
                          "}"]

    def block(lines, n=8):
        return "\n".join(_indent(l, n) for l in lines) if lines else " " * n + "// Nada a configurar."

    observe_extra = "\n".join(_indent(o, 16) for o in w.observe)
    render = block(w.render)
    destroy = ""
    if w.destroy:
        destroy = "\n\n    override fun onDestroy() {\n" + block(w.destroy) + "\n        super.onDestroy()\n    }"
    permissions = ""
    if is_start:
        permissions = '''

    private fun requestStartupPermissions() {
        if (!StartupPermissions.REQUEST_ON_START) return
        val missing = PermissionHelper.missing(this, StartupPermissions.list())
        if (missing.isNotEmpty()) permissionLauncher.launch(missing.toTypedArray())
    }'''
    suppress = '@SuppressLint("SetJavaScriptEnabled")\n' if getattr(w, "suppress_js", False) else ""
    state_unused = "" if w.render else "@Suppress(\"UNUSED_PARAMETER\")\n    "
    body = f'''/**
 * Tela "{spec.screen.title or spec.screen.name}" gerada pelo DroidBlocks.
 * Os blocos ficam no layout {layout_name}.xml e sao ligados ao ViewModel aqui.
 */
{suppress}class {spec.cls}Activity : BaseActivity() {{

    private lateinit var binding: {binding_cls}
    private val viewModel: {spec.cls}ViewModel by viewModels {{ {spec.cls}ViewModel.Factory }}
{chr(10).join("    " + pp for pp in props)}
{chr(10).join("    " + h for h in helpers)}

    override fun onCreate(savedInstanceState: Bundle?) {{
{block(on_create)}
    }}

    override fun onResume() {{
        super.onResume()
        // Recarrega os dados sempre que a tela volta a ficar visivel.
        viewModel.refresh()
    }}

    private fun setupToolbar() {{
{block(toolbar)}
    }}

    private fun setupViews() {{
{block(w.setup)}
    }}

    private fun observeState() {{
        lifecycleScope.launch {{
            repeatOnLifecycle(Lifecycle.State.STARTED) {{
                launch {{ viewModel.uiState.collect {{ render(it) }} }}
                launch {{
                    viewModel.messages.collect {{ Toast.makeText(this@{spec.cls}Activity, it, Toast.LENGTH_SHORT).show() }}
                }}
{observe_extra}
            }}
        }}
    }}

    // Atualiza a tela a partir do estado do ViewModel.
    {state_unused}private fun render(state: {spec.cls}UiState) {{
{render}
    }}{destroy}{permissions}
}}
'''
    body = body.replace("\n\n\n", "\n\n").replace("    \n", "\n")
    extra = [f"{ctx.pkg}.databinding.{binding_cls}"]
    if "FragmentActivity" in body:
        extra.append("androidx.fragment.app.FragmentActivity")
    if "repeatOnLifecycle" in body:
        extra.append("androidx.lifecycle.repeatOnLifecycle")
    return finalize(ctx, body, spec.package, extra)


SIGNATURE_VIEW = r'''package %PKG%.ui.components

import android.content.Context
import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Path
import android.util.AttributeSet
import android.view.MotionEvent
import android.view.View

/** Area de assinatura: desenha tracos com o dedo e exporta o resultado como Bitmap. */
class SignatureView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null
) : View(context, attrs) {

    private val path = Path()
    private val paint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.BLACK
        style = Paint.Style.STROKE
        strokeWidth = 6f * resources.displayMetrics.density / 2f
        strokeCap = Paint.Cap.ROUND
        strokeJoin = Paint.Join.ROUND
    }

    /** Indica se algo ja foi desenhado. */
    var isEmpty: Boolean = true
        private set

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        canvas.drawPath(path, paint)
    }

    override fun onTouchEvent(event: MotionEvent): Boolean {
        when (event.action) {
            MotionEvent.ACTION_DOWN -> {
                parent?.requestDisallowInterceptTouchEvent(true)
                path.moveTo(event.x, event.y)
                isEmpty = false
            }
            MotionEvent.ACTION_MOVE -> path.lineTo(event.x, event.y)
            MotionEvent.ACTION_UP -> performClick()
        }
        invalidate()
        return true
    }

    override fun performClick(): Boolean {
        super.performClick()
        return true
    }

    /** Apaga a assinatura. */
    fun clear() {
        path.reset()
        isEmpty = true
        invalidate()
    }

    /** Gera uma imagem com a assinatura atual sobre fundo branco. */
    fun toBitmap(): Bitmap {
        val bitmap = Bitmap.createBitmap(width.coerceAtLeast(1), height.coerceAtLeast(1), Bitmap.Config.ARGB_8888)
        val canvas = Canvas(bitmap)
        canvas.drawColor(Color.WHITE)
        canvas.drawPath(path, paint)
        return bitmap
    }
}
'''
