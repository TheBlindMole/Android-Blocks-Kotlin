"""APIs publicas prontas (sem chave) para usar nos projetos e modelos.

Todas podem ser adicionadas pelo editor de APIs ("Adicionar API pronta").
"""

from ..core.model import Api, ApiModel, ApiField, Endpoint


def _m(name, spec):
    """Cria um modelo a partir de 'campo:Tipo, campo2:Tipo'."""
    fields = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        fname, ftype = part.split(":", 1) if ":" in part else (part, "String")
        fields.append(ApiField(fname.strip(), ftype.strip()))
    return ApiModel(name, fields)


def _e(name, path, model, returns_list=True, wrapper="", query="", method="GET", body="", **mapping):
    return Endpoint(name=name, method=method, path=path, model=model, returns_list=returns_list,
                    wrapper_field=wrapper, query=query, body_model=body, mapping=dict(mapping))


def fakestore():
    return Api("FakeStore", "https://fakestoreapi.com/", models=[
        _m("StoreProduct", "id:Long, title:String, price:Double, description:String, category:String, image:String"),
    ], endpoints=[
        _e("getProducts", "products", "StoreProduct", title="title", subtitle="category",
           image="image", price="price", description="description", id="id"),
        _e("getProduct", "products/{id}", "StoreProduct", returns_list=False, title="title",
           subtitle="category", image="image", price="price", description="description", id="id"),
    ])


def dummyjson(parts=("products",)):
    models, endpoints = [], []
    if "products" in parts:
        models += [_m("DummyProduct", "id:Long, title:String, description:String, price:Double, "
                                      "thumbnail:String, category:String, rating:Double, brand:String"),
                   _m("ProductsPage", "products:List<DummyProduct>, total:Int")]
        endpoints += [
            _e("getProducts", "products", "ProductsPage", False, "products", "limit=50",
               title="title", subtitle="{brand} - nota {rating}", image="thumbnail", price="price",
               description="description", id="id"),
            _e("searchProducts", "products/search", "ProductsPage", False, "products", "q=phone",
               title="title", subtitle="category", image="thumbnail", price="price", id="id"),
        ]
    if "recipes" in parts:
        models += [_m("Recipe", "id:Long, name:String, image:String, cuisine:String, difficulty:String, "
                                "caloriesPerServing:Int, rating:Double, prepTimeMinutes:Int"),
                   _m("RecipesPage", "recipes:List<Recipe>")]
        endpoints.append(_e("getRecipes", "recipes", "RecipesPage", False, "recipes", "limit=50",
                            title="name", subtitle="{cuisine} - {prepTimeMinutes} min - {caloriesPerServing} kcal",
                            image="image", description="Dificuldade: {difficulty}", id="id"))
    if "quotes" in parts:
        models += [_m("Quote", "id:Long, quote:String, author:String"), _m("QuotesPage", "quotes:List<Quote>")]
        endpoints.append(_e("getQuotes", "quotes", "QuotesPage", False, "quotes", "limit=50",
                            title="quote", subtitle="author", id="id"))
    if "todos" in parts:
        models += [_m("Todo", "id:Long, todo:String, completed:Boolean, userId:Int"), _m("TodosPage", "todos:List<Todo>")]
        endpoints.append(_e("getTodos", "todos", "TodosPage", False, "todos", "limit=30",
                            title="todo", subtitle="Concluida: {completed}", id="id"))
    if "users" in parts:
        models += [_m("DummyUser", "id:Long, firstName:String, lastName:String, email:String, phone:String, image:String"),
                   _m("UsersPage", "users:List<DummyUser>")]
        endpoints.append(_e("getUsers", "users", "UsersPage", False, "users", "limit=30",
                            title="{firstName} {lastName}", subtitle="email", image="image", id="id"))
    if "posts" in parts:
        models += [_m("DummyPost", "id:Long, title:String, body:String, views:Int"), _m("PostsPage", "posts:List<DummyPost>")]
        endpoints.append(_e("getPosts", "posts", "PostsPage", False, "posts", "limit=30",
                            title="title", subtitle="{views} visualizacoes", description="body", id="id"))
    return Api("DummyJson", "https://dummyjson.com/", models=models, endpoints=endpoints)


def jsonplaceholder(parts=("posts",)):
    models, endpoints = [], []
    if "posts" in parts:
        models.append(_m("Post", "userId:Int, id:Long, title:String, body:String"))
        endpoints += [
            _e("getPosts", "posts", "Post", title="title", subtitle="Autor {userId}", description="body", id="id"),
            _e("createPost", "posts", "Post", False, method="POST", body="Post", title="title", id="id"),
        ]
    if "users" in parts:
        models.append(_m("User", "id:Long, name:String, username:String, email:String, phone:String, website:String"))
        endpoints.append(_e("getUsers", "users", "User", title="name", subtitle="email", id="id"))
    if "comments" in parts:
        models.append(_m("Comment", "postId:Int, id:Long, name:String, email:String, body:String"))
        endpoints.append(_e("getComments", "comments", "Comment", query="postId=1",
                            title="name", subtitle="email", description="body", id="id"))
    if "todos" in parts:
        models.append(_m("TodoItem", "userId:Int, id:Long, title:String, completed:Boolean"))
        endpoints.append(_e("getTodos", "todos", "TodoItem", title="title", subtitle="Concluida: {completed}", id="id"))
    return Api("JsonPlaceholder", "https://jsonplaceholder.typicode.com/", models=models, endpoints=endpoints)


def open_meteo():
    return Api("OpenMeteo", "https://api.open-meteo.com/", models=[
        _m("CurrentWeather", "time:String, temperature_2m:Double, relative_humidity_2m:Int, "
                             "wind_speed_10m:Double, weather_code:Int"),
        _m("ForecastResponse", "latitude:Double, longitude:Double, timezone:String, current:CurrentWeather"),
    ], endpoints=[
        _e("getForecast", "v1/forecast", "ForecastResponse", False,
           query="latitude=-23.55&longitude=-46.63&current=temperature_2m,relative_humidity_2m,"
                 "wind_speed_10m,weather_code&timezone=auto",
           title="Agora: {current.temperature_2m} C",
           subtitle="Umidade {current.relative_humidity_2m}% - Vento {current.wind_speed_10m} km/h",
           description="Fuso: {timezone} - Atualizado: {current.time}"),
    ])


def spaceflight_news():
    return Api("SpaceNews", "https://api.spaceflightnewsapi.net/", models=[
        _m("Article", "id:Long, title:String, url:String, image_url:String, news_site:String, "
                      "summary:String, published_at:String"),
        _m("ArticlesPage", "count:Int, results:List<Article>"),
    ], endpoints=[
        _e("getArticles", "v4/articles/", "ArticlesPage", False, "results", "limit=30",
           title="title", subtitle="news_site", image="image_url", description="summary", id="id"),
    ])


def exchange_rates():
    return Api("ExchangeRates", "https://open.er-api.com/", models=[
        _m("RatesResponse", "result:String, base_code:String, rates:Map<String,Double>"),
    ], endpoints=[
        _e("getRates", "v6/latest/USD", "RatesResponse", False, "rates"),
    ])


def coingecko():
    return Api("CoinGecko", "https://api.coingecko.com/", models=[
        _m("Coin", "id:String, symbol:String, name:String, image:String, current_price:Double, "
                   "price_change_percentage_24h:Double, market_cap:Double"),
    ], endpoints=[
        _e("getMarkets", "api/v3/coins/markets", "Coin", query="vs_currency=usd&per_page=50",
           title="name", subtitle="{symbol} - 24h: {price_change_percentage_24h}%", image="image",
           price="current_price", id="id"),
    ])


def themealdb():
    return Api("MealDb", "https://www.themealdb.com/", models=[
        _m("Meal", "idMeal:String, strMeal:String, strCategory:String, strArea:String, "
                   "strInstructions:String, strMealThumb:String"),
        _m("MealsResponse", "meals:List<Meal>"),
    ], endpoints=[
        _e("searchMeals", "api/json/v1/1/search.php", "MealsResponse", False, "meals", "s=",
           title="strMeal", subtitle="{strCategory} - {strArea}", image="strMealThumb",
           description="strInstructions", id="idMeal"),
    ])


def openlibrary():
    return Api("OpenLibrary", "https://openlibrary.org/", models=[
        _m("Book", "key:String, title:String, author_name:List<String>, first_publish_year:Int, cover_i:Long"),
        _m("BookSearch", "numFound:Int, docs:List<Book>"),
    ], endpoints=[
        _e("searchBooks", "search.json", "BookSearch", False, "docs", "q=android&limit=30",
           title="title", subtitle="{author_name} ({first_publish_year})",
           image="https://covers.openlibrary.org/b/id/{cover_i}-M.jpg", id="key"),
    ])


def dictionary():
    return Api("Dictionary", "https://api.dictionaryapi.dev/", models=[
        _m("WordEntry", "word:String, phonetic:String, origin:String"),
    ], endpoints=[
        _e("define", "api/v2/entries/en/{word}", "WordEntry", title="word", subtitle="phonetic",
           description="origin"),
    ])


def restcountries():
    return Api("Countries", "https://restcountries.com/", models=[
        _m("CountryName", "common:String, official:String"),
        _m("CountryFlags", "png:String"),
        _m("Country", "name:CountryName, capital:List<String>, region:String, population:Long, flags:CountryFlags"),
    ], endpoints=[
        _e("getCountries", "v3.1/all", "Country", query="fields=name,capital,region,population,flags",
           title="name.common", subtitle="{capital} - {region}", image="flags.png",
           description="Populacao: {population}", id="name.common"),
    ])


def randomuser():
    return Api("RandomUser", "https://randomuser.me/", models=[
        _m("PersonName", "first:String, last:String"),
        _m("PersonPicture", "medium:String, large:String"),
        _m("Person", "name:PersonName, email:String, phone:String, cell:String, picture:PersonPicture"),
        _m("PeopleResponse", "results:List<Person>"),
    ], endpoints=[
        _e("getPeople", "api/", "PeopleResponse", False, "results", "results=30&nat=br",
           title="{name.first} {name.last}", subtitle="email", image="picture.large",
           description="Telefone: {phone}"),
    ])


def itunes(media="podcast", term="tecnologia"):
    return Api("ITunes", "https://itunes.apple.com/", models=[
        _m("MediaItem", "trackId:Long, collectionId:Long, trackName:String, collectionName:String, "
                        "artistName:String, artworkUrl100:String, previewUrl:String, trackPrice:Double"),
        _m("MediaSearch", "resultCount:Int, results:List<MediaItem>"),
    ], endpoints=[
        _e("search", "search", "MediaSearch", False, "results", f"term={term}&media={media}&limit=40",
           title="trackName", subtitle="artistName", image="artworkUrl100", description="collectionName",
           id="trackId"),
    ])


def brasil_cep():
    return Api("BrasilApi", "https://brasilapi.com.br/", models=[
        _m("CepResult", "cep:String, state:String, city:String, neighborhood:String, street:String"),
    ], endpoints=[
        _e("lookupCep", "api/cep/v1/{cep}", "CepResult", False,
           title="{street}", subtitle="{neighborhood} - {city}/{state}", description="CEP {cep}", id="cep"),
    ])


def holidays(country="BR", year=2026):
    return Api("Holidays", "https://date.nager.at/", models=[
        _m("Holiday", "date:String, localName:String, name:String"),
    ], endpoints=[
        _e("getHolidays", f"api/v3/PublicHolidays/{year}/{country}", "Holiday",
           title="localName", subtitle="date", description="name", id="date"),
    ])


PRESETS = {
    "FakeStore (loja ficticia)": fakestore,
    "DummyJSON - produtos": lambda: dummyjson(("products",)),
    "DummyJSON - receitas": lambda: dummyjson(("recipes",)),
    "DummyJSON - citacoes": lambda: dummyjson(("quotes",)),
    "DummyJSON - tarefas": lambda: dummyjson(("todos",)),
    "DummyJSON - usuarios": lambda: dummyjson(("users",)),
    "DummyJSON - posts": lambda: dummyjson(("posts",)),
    "JSONPlaceholder - posts e comentarios": lambda: jsonplaceholder(("posts", "comments")),
    "JSONPlaceholder - usuarios e tarefas": lambda: jsonplaceholder(("users", "todos")),
    "Open-Meteo (clima)": open_meteo,
    "Spaceflight News (noticias)": spaceflight_news,
    "Open ER API (cambio)": exchange_rates,
    "CoinGecko (criptomoedas)": coingecko,
    "TheMealDB (receitas)": themealdb,
    "Open Library (livros)": openlibrary,
    "Free Dictionary (dicionario)": dictionary,
    "REST Countries (paises)": restcountries,
    "RandomUser (pessoas)": randomuser,
    "iTunes (podcasts)": lambda: itunes("podcast", "tecnologia"),
    "iTunes (musicas)": lambda: itunes("music", "bossa nova"),
    "BrasilAPI (CEP)": brasil_cep,
    "Nager (feriados)": holidays,
}
