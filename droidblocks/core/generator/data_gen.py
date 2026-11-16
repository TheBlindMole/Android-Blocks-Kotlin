"""Camada de dados: modelos, banco (Room), APIs (Retrofit), repositorio e injecao de dependencias."""

import re

from ...catalog.features import PERMISSIONS
from ..naming import to_pascal, to_camel, to_snake, kq, kotlin_string, unique_name
from ..resolver import iter_sources

PRIMITIVES = {"String": "String", "Int": "Int", "Long": "Long", "Double": "Double", "Float": "Float",
              "Boolean": "Boolean"}
DEFAULTS = {"String": '""', "Int": "0", "Long": "0L", "Double": "0.0", "Float": "0f", "Boolean": "false"}
RESERVED_CLASSES = {"Entity", "Dao", "Database", "Query", "Insert", "Update", "Delete", "ListItem", "Room",
                    "PrimaryKey", "String", "Int", "List", "Map", "App", "Flow", "Context"}
IMAGE_HINTS = ("image", "imagem", "foto", "photo", "picture", "thumb", "avatar", "url", "logo", "cover")
PRICE_HINTS = ("price", "preco", "valor", "amount", "value", "cost", "custo", "total")


# ----------------------------------------------------------------- utilitarios

def entity_class(entity):
    name = to_pascal(entity.name, "Item")
    return name + "Entity" if name in RESERVED_CLASSES else name


def entity_fields(entity):
    """Campos validos da entidade como (nomeKotlin, tipo), sem o id automatico."""
    result, used = [], {"id"}
    for raw_name, raw_type in entity.fields:
        name = to_camel(raw_name, "field")
        if name in used:
            continue
        used.add(name)
        result.append((name, raw_type if raw_type in PRIMITIVES else "String"))
    return result


def api_package_name(api):
    return to_snake(api.name, "api").replace("_", "")


def api_service_class(api):
    return to_pascal(api.name, "Api") + "Service"


def api_property(api):
    return to_camel(api.name, "api")


def model_class(name):
    cls = to_pascal(name, "Model")
    return cls + "Dto" if cls in RESERVED_CLASSES else cls


def kotlin_type(api, raw):
    """Converte o tipo declarado no editor para um tipo Kotlin anulavel."""
    raw = raw.replace(" ", "")
    models = {m.name for m in api.models}
    list_match = re.match(r"^List<(.+)>$", raw)
    map_match = re.match(r"^Map<String,(.+)>$", raw)
    if list_match:
        inner = list_match.group(1)
        inner_type = PRIMITIVES.get(inner) or (model_class(inner) if inner in models else "com.google.gson.JsonElement")
        return f"List<{inner_type}>?"
    if map_match:
        inner = map_match.group(1)
        inner_type = PRIMITIVES.get(inner) or (model_class(inner) if inner in models else "com.google.gson.JsonElement")
        return f"Map<String, {inner_type}>?"
    if raw in PRIMITIVES:
        return PRIMITIVES[raw] + "?"
    if raw in models:
        return model_class(raw) + "?"
    return "com.google.gson.JsonElement?"


def find_model(api, name):
    for m in api.models:
        if m.name == name:
            return m
    return None


def field_of(model, json_name):
    for f in model.fields:
        if f.name == json_name or to_camel(f.name) == json_name:
            return f
    return None


def path_expression(api, model, path, receiver="this"):
    """Converte 'a.b.c' em expressao Kotlin segura (a?.b?.c). Retorna None se invalido."""
    parts = path.split(".")
    current = model
    expr = receiver
    for index, part in enumerate(parts):
        if current is None:
            return None
        f = field_of(current, part)
        if f is None:
            return None
        name = to_camel(f.name, "field")
        expr = f"{expr}.{name}" if index == 0 else f"{expr}?.{name}"
        ftype = f.type.replace(" ", "")
        current = find_model(api, ftype)
    return expr


def mapping_expression(api, model, value, receiver="this"):
    """Expressao Kotlin que produz texto para um mapeamento (campo ou modelo '{campo}')."""
    if not value:
        return None
    if "{" in value:
        out = ['"']
        pos = 0
        for match in re.finditer(r"\{([^}]+)\}", value):
            out.append(kotlin_string(value[pos:match.start()]))
            expr = path_expression(api, model, match.group(1).strip(), receiver)
            out.append("${" + (expr + ".asText()" if expr else '""') + "}")
            pos = match.end()
        out.append(kotlin_string(value[pos:]))
        out.append('"')
        return "".join(out)
    expr = path_expression(api, model, value.strip(), receiver)
    return f"{expr}.asText()" if expr else None


def auto_mapping(model):
    """Mapeamento automatico quando o usuario nao definiu nenhum."""
    strings = [f.name for f in model.fields if f.type == "String"]
    mapping = {}
    for f in model.fields:
        lower = f.name.lower()
        if "image" not in mapping and f.type == "String" and any(h in lower for h in IMAGE_HINTS):
            mapping["image"] = f.name
        if "price" not in mapping and f.type in ("Double", "Float", "Int", "Long") and any(h in lower for h in PRICE_HINTS):
            mapping["price"] = f.name
        if lower == "id":
            mapping["id"] = f.name
    texts = [s for s in strings if s != mapping.get("image")]
    if texts:
        mapping["title"] = texts[0]
    if len(texts) > 1:
        mapping["subtitle"] = texts[1]
    if len(texts) > 2:
        mapping["description"] = texts[2]
    if "title" not in mapping and model.fields:
        mapping["title"] = model.fields[0].name
    return mapping


# ----------------------------------------------------------------- geracao

def generate(ctx):
    _model_files(ctx)
    _sample_data(ctx)
    if ctx.project.entities:
        _room(ctx)
    if ctx.project.apis:
        _network(ctx)
    _repository(ctx)
    _container_and_app(ctx)
    _utils(ctx)


def _model_files(ctx):
    ctx.add_kotlin("data/model/ListItem.kt", '''package %PKG%.data.model

/**
 * Item generico exibido em listas, grades e telas de detalhe.
 * Todas as fontes de dados (exemplo, banco, API, carrinho) sao convertidas para este formato.
 */
data class ListItem(
    val id: String,
    val title: String,
    val subtitle: String = "",
    val description: String = "",
    val imageUrl: String = "",
    val price: Double? = null,
    val badge: String = ""
)
''')
    search = (
        "SearchEngine.filter(base, query)" if ctx.resolved.has("search_engine") else
        "base.filter { item ->\n"
        "            val text = (item.title + \" \" + item.subtitle + \" \" + item.description).lowercase()\n"
        "            terms.all { text.contains(it) }\n"
        "        }")
    imports = "import %PKG%.features.SearchEngine\n" if ctx.resolved.has("search_engine") else ""
    terms = "" if ctx.resolved.has("search_engine") else \
        '        val terms = query.lowercase().split(" ").filter { it.isNotBlank() }\n'
    ctx.add_kotlin("data/model/Mappers.kt", f'''package %PKG%.data.model

{imports}
/** Converte qualquer valor em texto amigavel (listas viram texto separado por virgula). */
fun Any?.asText(): String = when (this) {{
    null -> ""
    is Double -> if (this % 1.0 == 0.0) this.toLong().toString() else this.toString()
    is Float -> if (this % 1f == 0f) this.toLong().toString() else this.toString()
    is Boolean -> if (this) "Sim" else "Nao"
    is List<*> -> this.joinToString(", ") {{ it.asText() }}
    else -> this.toString()
}}

/** Converte qualquer valor numerico ou texto em Double, quando possivel. */
fun Any?.asDouble(): Double? = when (this) {{
    is Number -> this.toDouble()
    is String -> this.replace(',', '.').toDoubleOrNull()
    else -> null
}}

/** Formata um preco usando a moeda do idioma do aparelho. */
fun Double?.asPrice(): String =
    if (this == null) "" else java.text.NumberFormat.getCurrencyInstance().format(this)

/** Filtros aplicados as listas: texto da busca e chip selecionado. */
object ItemFilters {{

    fun apply(items: List<ListItem>, query: String, filter: String = "", allLabel: String = ""): List<ListItem> {{
        val base = if (filter.isBlank() || filter == allLabel) {{
            items
        }} else {{
            items.filter {{ (it.title + " " + it.subtitle + " " + it.badge).contains(filter, ignoreCase = true) }}
        }}
        if (query.isBlank()) return base
{terms}        return {search}
    }}
}}
'''.replace("\n\n\n", "\n\n"))


def _sample_data(ctx):
    p = ctx.project
    used = {"default"}
    for _, _, source in iter_sources(p):
        if source.startswith("sample:"):
            used.add(source[7:])
    sets = []
    for name in sorted(used):
        rows = p.samples.get(name) or p.samples.get("default") or [
            {"title": f"Item {i}", "subtitle": f"Descricao do item {i}", "description": f"Detalhes do item {i}.",
             "price": None, "image": f"https://picsum.photos/seed/item{i}/600/400"} for i in range(1, 9)]
        items = []
        for index, row in enumerate(rows):
            price = row.get("price")
            price_code = "null" if price is None else f"{float(price)}"
            items.append(
                f"            ListItem(\n"
                f"                id = {kq(f'sample_{name}_{index}')},\n"
                f"                title = {kq(row.get('title', ''))},\n"
                f"                subtitle = {kq(row.get('subtitle', ''))},\n"
                f"                description = {kq(row.get('description', ''))},\n"
                f"                imageUrl = {kq(row.get('image', ''))},\n"
                f"                price = {price_code}\n"
                f"            )")
        sets.append(f"        {kq(name)} to listOf(\n" + ",\n".join(items) + "\n        )")
    ctx.add_kotlin("data/SampleData.kt", '''package %PKG%.data

import %PKG%.data.model.ListItem

/** Dados de exemplo usados enquanto o app nao tem banco ou API reais. */
object SampleData {

    private val sets: Map<String, List<ListItem>> = mapOf(
''' + ",\n".join(sets) + '''
    )

    /** Itens de um conjunto. Se o conjunto nao existir, devolve o conjunto padrao. */
    fun items(set: String): List<ListItem> = sets[set] ?: sets["default"].orEmpty()

    /** Todos os itens de todos os conjuntos. */
    fun all(): List<ListItem> = sets.values.flatten()
}
''')


def _room(ctx):
    p = ctx.project
    entity_names = []
    dao_lines = []
    for entity in p.entities:
        cls = entity_class(entity)
        entity_names.append(cls)
        table = to_snake(entity.name, "item") + "s"
        fields = entity_fields(entity)
        props = ["    @PrimaryKey(autoGenerate = true) val id: Long = 0"]
        for name, ftype in fields:
            props.append(f"    val {name}: {ftype} = {DEFAULTS[ftype]}")
        image = next((n for n, t in fields if t == "String" and any(h in n.lower() for h in IMAGE_HINTS)), None)
        price = next((n for n, t in fields if t in ("Double", "Float", "Int", "Long") and any(h in n.lower() for h in PRICE_HINTS)), None)
        texts = [n for n, t in fields if n not in (image, price)]
        title = texts[0] if texts else None
        subtitle_fields = texts[1:3]
        subtitle = " + \" - \" + ".join(f"{n}.asText()" for n in subtitle_fields) if subtitle_fields else '""'
        description = " + \"\\n\" + ".join(f'"{n}: " + {n}.asText()' for n, _ in fields) if fields else '""'
        form_args = []
        for name, ftype in fields:
            raw = f'values[{kq(name)}]'
            conv = {
                "String": f"{raw}.orEmpty()",
                "Int": f"{raw}?.replace(',', '.')?.toDoubleOrNull()?.toInt() ?: 0",
                "Long": f"{raw}?.replace(',', '.')?.toDoubleOrNull()?.toLong() ?: 0L",
                "Double": f"{raw}?.replace(',', '.')?.toDoubleOrNull() ?: 0.0",
                "Float": f"{raw}?.replace(',', '.')?.toFloatOrNull() ?: 0f",
                "Boolean": f"{raw}?.toBooleanStrictOrNull() ?: false",
            }[ftype]
            form_args.append(f"        {name} = {conv}")
        fn_from = to_camel(cls) + "FromForm"
        ctx.add_kotlin(f"data/local/{cls}.kt", f'''package %PKG%.data.local

import androidx.room.Entity
import androidx.room.PrimaryKey
import %PKG%.data.model.ListItem
import %PKG%.data.model.asText

/** Entidade {cls} persistida na tabela "{table}". */
@Entity(tableName = "{table}")
data class {cls}(
{(","+chr(10)).join(props)}
)

/** Converte o registro em item de lista para exibicao. */
fun {cls}.toListItem(): ListItem = ListItem(
    id = "{to_snake(cls)}_$id",
    title = {f"{title}.asText()" if title else '"' + cls + ' #$id"'},
    subtitle = {subtitle},
    description = {description},
    imageUrl = {f"{image}" if image else '""'}{",\n    price = " + price + ".toDouble()" if price else ""}
)

/** Cria um registro a partir dos valores de um formulario (chave do campo -> texto). */
fun {fn_from}(values: Map<String, String>): {cls} = {cls}(
{(","+chr(10)).join(form_args) if form_args else ""}
)
'''.replace(f"{cls}(\n\n)", f"{cls}()"))
        ctx.add_kotlin(f"data/local/{cls}Dao.kt", f'''package %PKG%.data.local

import androidx.room.Dao
import androidx.room.Delete
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update
import kotlinx.coroutines.flow.Flow

/** Operacoes de banco para {cls}. */
@Dao
interface {cls}Dao {{

    @Query("SELECT * FROM `{table}` ORDER BY id DESC")
    suspend fun getAll(): List<{cls}>

    @Query("SELECT * FROM `{table}` ORDER BY id DESC")
    fun observeAll(): Flow<List<{cls}>>

    @Query("SELECT * FROM `{table}` WHERE id = :id")
    suspend fun getById(id: Long): {cls}?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(item: {cls}): Long

    @Update
    suspend fun update(item: {cls})

    @Delete
    suspend fun delete(item: {cls})

    @Query("DELETE FROM `{table}` WHERE id = :id")
    suspend fun deleteById(id: Long)

    @Query("DELETE FROM `{table}`")
    suspend fun clear()
}}
''')
        dao_lines.append(f"    abstract fun {to_camel(cls)}Dao(): {cls}Dao")
    entities_list = ", ".join(f"{n}::class" for n in entity_names)
    ctx.add_kotlin("data/local/AppDatabase.kt", f'''package %PKG%.data.local

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase

/** Banco de dados local do aplicativo (SQLite via Room). */
@Database(entities = [{entities_list}], version = 1, exportSchema = false)
abstract class AppDatabase : RoomDatabase() {{

{chr(10).join(dao_lines)}

    companion object {{
        /** Cria o banco. Ao mudar a estrutura das entidades, aumente a versao acima. */
        fun create(context: Context): AppDatabase =
            Room.databaseBuilder(context.applicationContext, AppDatabase::class.java, "{to_snake(p.database_name or 'app_database')}.db")
                .fallbackToDestructiveMigration()
                .build()
    }}
}}
''')


def endpoint_info(api, endpoint):
    """Analisa um endpoint: modelo de resposta, modelo dos itens e tipo do wrapper."""
    response = find_model(api, endpoint.model)
    item_model = response
    wrapper_kind = None
    wrapper_name = None
    if endpoint.wrapper_field and response:
        wf = field_of(response, endpoint.wrapper_field)
        if wf:
            wrapper_name = to_camel(wf.name, "items")
            ftype = wf.type.replace(" ", "")
            if ftype.startswith("List<"):
                wrapper_kind = "list"
                item_model = find_model(api, ftype[5:-1])
            elif ftype.startswith("Map<"):
                wrapper_kind = "map"
                item_model = None
    return response, item_model, wrapper_kind, wrapper_name


def path_params(endpoint):
    return re.findall(r"\{(\w+)\}", endpoint.path or "")


def query_params(endpoint):
    result = []
    for part in (endpoint.query or "").split("&"):
        if not part.strip():
            continue
        key, _, value = part.partition("=")
        result.append((key.strip(), value.strip()))
    return result


def _network(ctx):
    p = ctx.project
    r = ctx.resolved
    services = []
    for api in p.apis:
        pkg = api_package_name(api)
        svc = api_service_class(api)
        # Modelos
        model_code = []
        for model in api.models:
            props = []
            used = set()
            for f in model.fields:
                name = unique_name(to_camel(f.name, "field"), used)
                props.append(f'    @SerializedName({kq(f.name)}) val {name}: {kotlin_type(api, f.type)} = null')
            if not props:
                props.append('    @SerializedName("value") val value: String? = null')
            model_code.append(f"/** Modelo {model.name} da API {api.name}. */\ndata class {model_class(model.name)}(\n"
                              + ",\n".join(props) + "\n)")
        ctx.add_kotlin(f"data/remote/{pkg}/{to_pascal(api.name)}Models.kt", f'''package %PKG%.data.remote.{pkg}

import com.google.gson.annotations.SerializedName

{(chr(10) + chr(10)).join(model_code)}
''')
        # Servico Retrofit
        methods = []
        mappers = []
        body_models = set()
        for ep in api.endpoints:
            method = (ep.method or "GET").upper()
            if method not in ("GET", "POST", "PUT", "PATCH", "DELETE"):
                method = "GET"
            path = (ep.path or "").lstrip("/")
            params, used = [], set()
            for name in path_params(ep):
                kname = unique_name(to_camel(name, "param"), used)
                params.append(f'@Path({kq(name)}) {kname}: String')
            for key, value in query_params(ep):
                kname = unique_name(to_camel(key, "param"), used)
                params.append(f'@Query({kq(key)}) {kname}: String = {kq(value)}')
            if method in ("POST", "PUT", "PATCH") and find_model(api, ep.body_model):
                params.append(f"@Body body: {model_class(ep.body_model)}")
                body_models.add(ep.body_model)
            response = find_model(api, ep.model)
            if response is None:
                ret = "com.google.gson.JsonElement"
            elif ep.returns_list:
                ret = f"List<{model_class(response.name)}>"
            else:
                ret = model_class(response.name)
            if method == "DELETE" and response is None:
                ret = "retrofit2.Response<Unit>"
            fname = to_camel(ep.name, "call")
            methods.append(f'''    /** {method} {path} */
    @{method}({kq(path)})
    suspend fun {fname}({", ".join(params)}): {ret}''')
            # Mapeador para ListItem
            _, item_model, wrapper_kind, _ = endpoint_info(api, ep)
            if item_model is not None:
                mapping = dict(ep.mapping) if ep.mapping else auto_mapping(item_model)
                cls = model_class(item_model.name)
                fields = {}
                for target in ("title", "subtitle", "description", "image"):
                    expr = mapping_expression(api, item_model, mapping.get(target, ""))
                    fields[target] = expr or '""'
                price_expr = path_expression(api, item_model, mapping.get("price", "")) if mapping.get("price") else None
                id_expr = mapping_expression(api, item_model, mapping.get("id", ""))
                id_code = f'{id_expr}.ifBlank {{ "{fname}_$index" }}' if id_expr else f'"{fname}_$index"'
                mappers.append(f'''/** Converte {cls} em item de lista (endpoint {ep.name}). */
fun {cls}.to{to_pascal(ep.name)}Item(index: Int): ListItem = ListItem(
    id = {id_code},
    title = {fields["title"]},
    subtitle = {fields["subtitle"]},
    description = {fields["description"]},
    imageUrl = {fields["image"]},
    price = {price_expr + ".asDouble()" if price_expr else "null"}
)''')
        for model_name in sorted(body_models):
            model = find_model(api, model_name)
            args, used = [], set()
            for f in model.fields:
                name = unique_name(to_camel(f.name, "field"), used)
                ftype = f.type.replace(" ", "")
                raw = f"values[{kq(name)}]"
                conv = {"String": raw, "Int": f"{raw}?.toIntOrNull()", "Long": f"{raw}?.toLongOrNull()",
                        "Double": f"{raw}?.replace(',', '.')?.toDoubleOrNull()",
                        "Float": f"{raw}?.replace(',', '.')?.toFloatOrNull()",
                        "Boolean": f"{raw}?.toBooleanStrictOrNull()"}.get(ftype, "null")
                args.append(f"    {name} = {conv}")
            mappers.append(f'''/** Monta o corpo {model_class(model_name)} a partir dos campos do formulario. */
fun {to_camel(model_class(model_name))}FromForm(values: Map<String, String>): {model_class(model_name)} = {model_class(model_name)}(
{(","+chr(10)).join(args)}
)''')
        ctx.add_kotlin(f"data/remote/{pkg}/{svc}.kt", f'''package %PKG%.data.remote.{pkg}

import retrofit2.http.Body
import retrofit2.http.DELETE
import retrofit2.http.GET
import retrofit2.http.PATCH
import retrofit2.http.POST
import retrofit2.http.PUT
import retrofit2.http.Path
import retrofit2.http.Query

/** Endpoints da API {api.name} ({api.base_url}). */
interface {svc} {{

{(chr(10) + chr(10)).join(methods)}
}}
''')
        if mappers:
            ctx.add_kotlin(f"data/remote/{pkg}/{to_pascal(api.name)}Mappers.kt", f'''package %PKG%.data.remote.{pkg}

import %PKG%.data.model.ListItem
import %PKG%.data.model.asDouble
import %PKG%.data.model.asText

{(chr(10) + chr(10)).join(mappers)}
''')
        services.append(api)

    # NetworkModule
    interceptors = []
    if r.has("http_logging"):
        interceptors.append('''            if (BuildConfig.DEBUG) {
                addInterceptor(HttpLoggingInterceptor().apply { level = HttpLoggingInterceptor.Level.BODY })
            }''')
    if r.has("auth_token"):
        interceptors.append("            addInterceptor(AuthInterceptor())")
    if r.has("http_cache"):
        interceptors.append('            cache(Cache(File(appContext.cacheDir, "http"), 10L * 1024 * 1024))')
    props = []
    for api in services:
        base = api.base_url.strip()
        if not base.endswith("/"):
            base += "/"
        prop = api_property(api)
        svc = api_service_class(api)
        if api.auth == "api_key":
            key = "API_KEY_" + to_snake(api.name).upper()
            props.append(f'''    /** Cliente da API {api.name} (envia a chave no cabecalho {api.api_key_header}). */
    val {prop}: {svc} by lazy {{
        val keyed = client.newBuilder().addInterceptor {{ chain ->
            chain.proceed(chain.request().newBuilder().header({kq(api.api_key_header)}, BuildConfig.{key}).build())
        }}.build()
        retrofit({kq(base)}, keyed).create({svc}::class.java)
    }}''')
        else:
            props.append(f'''    /** Cliente da API {api.name}. */
    val {prop}: {svc} by lazy {{ retrofit({kq(base)}).create({svc}::class.java) }}''')
    imports = ["import android.content.Context", "import %PKG%.BuildConfig", "import okhttp3.OkHttpClient",
               "import retrofit2.Retrofit", "import retrofit2.converter.gson.GsonConverterFactory",
               "import java.util.concurrent.TimeUnit"]
    if r.has("http_logging"):
        imports.append("import okhttp3.logging.HttpLoggingInterceptor")
    if r.has("auth_token"):
        imports.append("import %PKG%.features.AuthInterceptor")
    if r.has("http_cache"):
        imports += ["import okhttp3.Cache", "import java.io.File"]
    for api in services:
        imports.append(f"import %PKG%.data.remote.{api_package_name(api)}.{api_service_class(api)}")
    ctx.add_kotlin("data/remote/NetworkModule.kt", f'''package %PKG%.data.remote

{chr(10).join(sorted(set(imports)))}

/** Cria e guarda os clientes HTTP de todas as APIs do app. */
object NetworkModule {{

    private lateinit var appContext: Context

    /** Chamado uma vez em App.onCreate. */
    fun init(context: Context) {{
        appContext = context.applicationContext
    }}

    /** Cliente HTTP compartilhado com tempos limite e interceptadores. */
    val client: OkHttpClient by lazy {{
        OkHttpClient.Builder()
            .connectTimeout(20, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .apply {{
{chr(10).join(interceptors) if interceptors else "                // Adicione interceptadores aqui (log, autenticacao, cache)."}
            }}
            .build()
    }}

    private fun retrofit(baseUrl: String, httpClient: OkHttpClient = client): Retrofit =
        Retrofit.Builder()
            .baseUrl(baseUrl)
            .client(httpClient)
            .addConverterFactory(GsonConverterFactory.create())
            .build()

{(chr(10) + chr(10)).join(props)}
}}
'''.replace("%PKG%", ctx.pkg))


def _repository(ctx):
    p = ctx.project
    r = ctx.resolved
    branches = []
    imports = {"import android.content.Context", "import %PKG%.data.model.ListItem",
               "import java.util.concurrent.ConcurrentHashMap"}
    has_db = bool(p.entities)
    if has_db:
        imports.add("import %PKG%.data.local.*")
    for entity in p.entities:
        cls = entity_class(entity)
        branches.append(f'            "entity:{entity.name}" -> database.{to_camel(cls)}Dao().getAll().map {{ it.toListItem() }}')
    call_branches = []
    for api in p.apis:
        pkg = api_package_name(api)
        imports.add(f"import %PKG%.data.remote.{pkg}.*")
        imports.add("import %PKG%.data.remote.NetworkModule")
        prop = api_property(api)
        for ep in api.endpoints:
            fname = to_camel(ep.name, "call")
            response, item_model, wrapper_kind, wrapper_name = endpoint_info(api, ep)
            method = (ep.method or "GET").upper()
            args, guards = [], []
            for name in path_params(ep):
                kname = to_camel(name, "param")
                guards.append(f'val {kname} = values[{kq(kname)}].orEmpty().ifBlank {{ values["itemId"].orEmpty() }}')
                args.append(kname)
            has_body = method in ("POST", "PUT", "PATCH") and find_model(api, ep.body_model)
            if has_body:
                args.append(f"{to_camel(model_class(ep.body_model))}FromForm(values)")
            call = f"NetworkModule.{prop}.{fname}({', '.join(args)})"
            mapper = f"to{to_pascal(ep.name)}Item"
            key = f"{api.name}.{ep.name}"
            if response is None:
                items = f'listOf(ListItem(id = "{fname}", title = {call}.toString()))'
            elif wrapper_kind == "list" and item_model is not None:
                items = f"{call}.{wrapper_name}.orEmpty().mapIndexed {{ index, dto -> dto.{mapper}(index) }}"
            elif wrapper_kind == "map":
                items = (f"{call}.{wrapper_name}.orEmpty().map {{ (key, value) -> "
                         f'ListItem(id = "{fname}_$key", title = key, subtitle = value.asText()) }}')
                imports.add("import %PKG%.data.model.asText")
            elif ep.returns_list:
                items = f"{call}.mapIndexed {{ index, dto -> dto.{mapper}(index) }}"
            else:
                items = f"listOf({call}.{mapper}(0))"
            guard_code = ""
            if guards:
                checks = " || ".join(f"{to_camel(n, 'param')}.isBlank()" for n in path_params(ep))
                guard_code = "\n".join(f"                {g}" for g in guards) + \
                    f"\n                if ({checks}) emptyList() else "
            if method == "GET":
                if guard_code:
                    branches.append(f'            "api:{key}" -> {{\n{guard_code}{items}\n            }}')
                else:
                    branches.append(f'            "api:{key}" -> {items}')
            else:
                pre = "\n".join(f"                {g}" for g in guards)
                call_branches.append(f'''            "{key}" -> {{
{pre + chr(10) if pre else ""}                {call}
                "Enviado com sucesso"
            }}''')
    if r.has("cart"):
        imports.add("import %PKG%.features.CartManager")
        branches.append('            "cart" -> CartManager.asListItems()')
    if r.has("favorites"):
        imports.add("import %PKG%.features.FavoritesManager")
        branches.append('            "favorites" -> FavoritesManager.items.value')
    if r.has("chat"):
        imports.add("import %PKG%.features.ChatRepository")
        branches.append('            "chat" -> ChatRepository.asListItems()')
    if r.has("contacts"):
        imports.add("import %PKG%.features.ContactsHelper")
        branches.append('            "contacts" -> ContactsHelper.read(context)')
    imports.add("import %PKG%.data.SampleData")

    delete_lines = []
    entities_sorted = sorted(p.entities, key=lambda e: -len(to_snake(entity_class(e))))
    for entity in entities_sorted:
        cls = entity_class(entity)
        prefix = to_snake(cls) + "_"
        delete_lines.append(f'            id.startsWith("{prefix}") -> id.removePrefix("{prefix}").toLongOrNull()'
                            f'?.let {{ database.{to_camel(cls)}Dao().deleteById(it) }}')
    if r.has("favorites"):
        delete_lines.append("            FavoritesManager.isFavorite(id) -> FavoritesManager.remove(id)")
    if r.has("cart"):
        delete_lines.append("            CartManager.lines.value.any { it.item.id == id } -> CartManager.remove(id)")
    save_branches = []
    for entity in p.entities:
        cls = entity_class(entity)
        save_branches.append(
            f'            {kq(entity.name)} -> database.{to_camel(cls)}Dao().insert({to_camel(cls)}FromForm(values))')

    ctor = "private val context: Context"
    if has_db:
        ctor += ",\n    private val database: AppDatabase"
    save_body = ("        when (entity) {\n" + "\n".join(save_branches) +
                 '\n            else -> throw IllegalArgumentException("Entidade desconhecida: $entity")\n        }'
                 if save_branches else
                 '        // Nenhuma entidade de banco definida: os dados ficam apenas em memoria.\n'
                 '        memoryStore.getOrPut(entity) { mutableListOf() }.add(values)')
    memory = "" if save_branches else \
        "\n    private val memoryStore = mutableMapOf<String, MutableList<Map<String, String>>>()\n"
    call_body = ("        return when (endpoint) {\n" + "\n".join(call_branches) +
                 '\n            else -> "Dados atualizados"\n        }') if call_branches else \
        '        return "Dados atualizados"'
    unused = "@Suppress(\"UNUSED_PARAMETER\")\n    " if not call_branches else ""
    delete_body = ("        when {\n" + "\n".join(delete_lines) + "\n            else -> Unit\n        }"
                   if delete_lines else "        // Nenhuma origem permite exclusao (sem banco, carrinho ou favoritos).")
    when_block = ("when (source) {\n" + "\n".join(branches) +
                  '\n            else -> if (source.startsWith("sample:")) SampleData.items(source.removePrefix("sample:")) else emptyList()'
                  "\n        }")
    if r.has("offline_cache") and p.apis:
        imports.add("import %PKG%.features.OfflineStore")
        imports.add("import kotlin.coroutines.cancellation.CancellationException")
        body = when_block.replace("\n", "\n    ")
        load_items = f'''        val items: List<ListItem> = try {{
            {body}
        }} catch (e: Exception) {{
            if (e is CancellationException) throw e
            // Sem rede: usa a ultima resposta salva da API, se houver.
            if (source.startsWith("api:")) OfflineStore.load(context, source) ?: throw e else throw e
        }}
        if (source.startsWith("api:")) OfflineStore.save(context, source, items)'''
    else:
        load_items = f"        val items: List<ListItem> = {when_block}"
    ctx.add_kotlin("data/repository/AppRepository.kt", f'''package %PKG%.data.repository

{chr(10).join(sorted(imports))}

/**
 * Ponto unico de acesso aos dados do app. As telas pedem itens por "fonte":
 * sample:conjunto, entity:Entidade, api:Api.endpoint, cart, favorites, chat ou contacts.
 */
class AppRepository(
    {ctor}
) {{
    private val cache = ConcurrentHashMap<String, ListItem>()
{memory}
    /** Busca os itens de uma fonte. [values] traz os campos da tela (usados em parametros de API). */
    suspend fun getItems(source: String, values: Map<String, String> = emptyMap()): List<ListItem> {{
{load_items}
        items.forEach {{ cache[it.id] = it }}
        return items
    }}

    /** Encontra um item ja carregado (usado na tela de detalhe). */
    fun findItem(id: String): ListItem? = cache[id] ?: SampleData.all().firstOrNull {{ it.id == id }}

    /** Salva os valores de um formulario na entidade informada. */
    suspend fun save(entity: String, values: Map<String, String>) {{
{save_body}
    }}

    /** Exclui um item pela sua origem: banco local, favoritos ou carrinho. */
    suspend fun delete(id: String) {{
{delete_body}
        cache.remove(id)
    }}

    /** Executa um endpoint que envia dados (POST, PUT, PATCH, DELETE) e devolve uma mensagem. */
    {unused}suspend fun call(endpoint: String, values: Map<String, String>): String {{
{call_body}
    }}
}}
'''.replace("\n\n\n", "\n\n"))


def _container_and_app(ctx):
    p = ctx.project
    r = ctx.resolved
    has_db = bool(p.entities)
    db_line = "\n    /** Banco de dados local, criado sob demanda. */\n    val database: AppDatabase by lazy { AppDatabase.create(context) }\n" if has_db else ""
    repo_args = "context, database" if has_db else "context"
    ctx.add_kotlin("di/AppContainer.kt", f'''package %PKG%.di

import android.content.Context
{"import %PKG%.data.local.AppDatabase" + chr(10) if has_db else ""}import %PKG%.data.repository.AppRepository

/** Container simples de dependencias, criado uma vez na classe App. */
class AppContainer(private val context: Context) {{
{db_line}
    /** Repositorio unico usado por todas as telas. */
    val repository: AppRepository by lazy {{ AppRepository({repo_args}) }}
}}
''')
    init = []
    if p.apis:
        init.append("NetworkModule.init(this)")
    for feature in r.features:
        init.extend(feature.app_init)
    extra_imports = []
    if p.apis:
        extra_imports.append("import %PKG%.data.remote.NetworkModule")
    if not ctx.compose and "dynamic_color" in r.flags:
        init.append("DynamicColors.applyToActivitiesIfAvailable(this)")
        extra_imports.append("import com.google.android.material.color.DynamicColors")
    theme_views = not ctx.compose and "theme_toggle" in r.flags
    if theme_views:
        extra_imports += ["import androidx.appcompat.app.AppCompatDelegate", "import kotlinx.coroutines.CoroutineScope",
                          "import kotlinx.coroutines.Dispatchers", "import kotlinx.coroutines.launch"]
        init.append('''CoroutineScope(Dispatchers.Main).launch {
            ThemePreferences.modeFlow(this@App).collect { mode ->
                AppCompatDelegate.setDefaultNightMode(
                    when (mode) {
                        "dark" -> AppCompatDelegate.MODE_NIGHT_YES
                        "light" -> AppCompatDelegate.MODE_NIGHT_NO
                        else -> AppCompatDelegate.MODE_NIGHT_FOLLOW_SYSTEM
                    }
                )
            }
        }''')
    ctx._app_init = init
    ctx._app_imports = extra_imports


def finish_app(ctx):
    """Gera App.kt depois que os arquivos de funcionalidades existem (para os imports)."""
    init = getattr(ctx, "_app_init", [])
    imports = ["import android.app.Application", "import %PKG%.di.AppContainer"] + getattr(ctx, "_app_imports", [])
    feature_lines = [l for l in init if not l.startswith("NetworkModule")]
    if ctx.has_feature_files() and feature_lines:
        imports.append("import %PKG%.features.*")
    body = "\n".join("        " + line for line in init)
    ctx.add_kotlin("App.kt", f'''package %PKG%

{chr(10).join(sorted(set(imports)))}

/** Classe Application: ponto de partida do processo e dono do container de dependencias. */
class App : Application() {{

    lateinit var container: AppContainer
        private set

    override fun onCreate() {{
        super.onCreate()
        container = AppContainer(this)
{body if body else "        // Inicializacoes globais podem ser adicionadas aqui."}
    }}
}}
''')


def _utils(ctx):
    r = ctx.resolved
    p = ctx.project
    ctx.add_kotlin("util/IntentHelper.kt", '''package %PKG%.util

import android.content.ActivityNotFoundException
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.provider.Settings

/** Atalhos para abrir outros apps: compartilhar, ligar, e-mail, SMS, navegador e mapas. */
object IntentHelper {

    fun shareText(context: Context, text: String, title: String = "Compartilhar") {
        val intent = Intent(Intent.ACTION_SEND).apply {
            type = "text/plain"
            putExtra(Intent.EXTRA_TEXT, text)
        }
        start(context, Intent.createChooser(intent, title))
    }

    fun openUrl(context: Context, url: String): Boolean {
        val fixed = if (url.startsWith("http://") || url.startsWith("https://")) url else "https://$url"
        return start(context, Intent(Intent.ACTION_VIEW, Uri.parse(fixed)))
    }

    fun dial(context: Context, phone: String): Boolean =
        start(context, Intent(Intent.ACTION_DIAL, Uri.parse("tel:" + phone.filter { it.isDigit() || it == '+' })))

    fun email(context: Context, to: String, subject: String = "", body: String = ""): Boolean {
        val intent = Intent(Intent.ACTION_SENDTO, Uri.parse("mailto:")).apply {
            putExtra(Intent.EXTRA_EMAIL, arrayOf(to))
            putExtra(Intent.EXTRA_SUBJECT, subject)
            putExtra(Intent.EXTRA_TEXT, body)
        }
        return start(context, intent)
    }

    fun sms(context: Context, phone: String, body: String = ""): Boolean {
        val intent = Intent(Intent.ACTION_SENDTO, Uri.parse("smsto:" + phone.filter { it.isDigit() || it == '+' }))
            .putExtra("sms_body", body)
        return start(context, intent)
    }

    fun openMap(context: Context, latitude: Double, longitude: Double, label: String = ""): Boolean =
        start(context, Intent(Intent.ACTION_VIEW, Uri.parse("geo:$latitude,$longitude?q=$latitude,$longitude(${Uri.encode(label)})")))

    /** Abre o app de mapas pesquisando um endereco ou coordenadas ("lat,lng"). */
    fun openMapQuery(context: Context, query: String): Boolean =
        start(context, Intent(Intent.ACTION_VIEW, Uri.parse("geo:0,0?q=" + Uri.encode(query))))

    /** Abre uma conversa no WhatsApp (numero com codigo do pais, apenas digitos). */
    fun whatsapp(context: Context, phone: String, message: String = ""): Boolean {
        val digits = phone.filter { it.isDigit() }
        val url = "https://wa.me/$digits" + if (message.isBlank()) "" else "?text=" + Uri.encode(message)
        return start(context, Intent(Intent.ACTION_VIEW, Uri.parse(url)))
    }

    fun openAppSettings(context: Context): Boolean =
        start(context, Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS, Uri.fromParts("package", context.packageName, null)))

    // Inicia a Activity e evita falha quando nenhum app consegue abrir o Intent.
    private fun start(context: Context, intent: Intent): Boolean = try {
        context.startActivity(intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
        true
    } catch (e: ActivityNotFoundException) {
        false
    }
}
''')
    ctx.add_kotlin("util/ContextExt.kt", '''package %PKG%.util

import android.app.Activity
import android.content.Context
import android.content.ContextWrapper

/** Encontra a Activity por tras de um Context (util em Composables). */
fun Context.findActivity(): Activity? {
    var current: Context = this
    while (current is ContextWrapper) {
        if (current is Activity) return current
        current = current.baseContext
    }
    return null
}
''')
    dangerous = []
    for perm in r.permissions:
        meta = PERMISSIONS.get(perm, (False, None, None))
        if meta[0]:
            dangerous.append((perm, meta[1]))
    lines = []
    for perm, min_api in dangerous:
        if min_api:
            lines.append(f'        if (Build.VERSION.SDK_INT >= {min_api}) add("{perm}")')
        else:
            lines.append(f'        add("{perm}")')
    enabled = p.request_permissions_on_start
    ctx.add_kotlin("util/Permissions.kt", f'''package %PKG%.util

import android.content.Context
import android.content.pm.PackageManager
import android.os.Build
import androidx.core.content.ContextCompat

/** Verificacao de permissoes em tempo de execucao. */
object PermissionHelper {{

    fun isGranted(context: Context, permission: String): Boolean =
        ContextCompat.checkSelfPermission(context, permission) == PackageManager.PERMISSION_GRANTED

    fun missing(context: Context, permissions: List<String>): List<String> =
        permissions.filterNot {{ isGranted(context, it) }}
}}

/** Permissoes perigosas exigidas pelas funcionalidades ativas, pedidas na abertura do app. */
object StartupPermissions {{

    const val REQUEST_ON_START = {"true" if enabled else "false"}

    fun list(): List<String> = buildList {{
{chr(10).join(lines) if lines else "        // Nenhuma permissao perigosa e necessaria."}
    }}
}}
''')
