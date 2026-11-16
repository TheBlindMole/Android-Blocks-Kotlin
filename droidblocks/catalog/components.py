"""Blocos visuais (componentes) que podem ser empilhados nas telas.

Cada bloco declara suas propriedades editaveis. A geracao de codigo para
Compose e para Views (XML) fica em core/generator.
"""

from collections import namedtuple

Prop = namedtuple("Prop", "key label kind default options")
Comp = namedtuple("Comp", "type label category glyph props requires description")


def P(key, label, kind="text", default="", options=None):
    return Prop(key, label, kind, default, options or [])


INPUT_TYPES = ["text", "email", "number", "phone", "password", "multiline"]
VALIDATIONS = ["none", "required", "email", "phone", "number", "password", "cpf", "cnpj",
               "nif", "cep", "postal_pt"]

BASIC = "Basicos"
INPUT = "Entrada de dados"
DATA = "Listas e dados"
MEDIA = "Midia e mapas"
LAYOUT = "Layout"

COMPONENT_LIST = [
    Comp("title", "Titulo", BASIC, "T", [
        P("text", "Texto", default="Título"),
        P("size", "Tamanho", "choice", "large", ["large", "medium", "small"]),
        P("align", "Alinhamento", "choice", "start", ["start", "center"]),
    ], [], "Texto de destaque para cabecalhos."),
    Comp("text", "Texto", BASIC, "Aa", [
        P("text", "Texto", "multiline", "Digite aqui o seu texto."),
        P("style", "Estilo", "choice", "body", ["body", "caption", "emphasis"]),
        P("align", "Alinhamento", "choice", "start", ["start", "center"]),
    ], [], "Paragrafo de texto."),
    Comp("button", "Botao", BASIC, "[ ]", [
        P("text", "Texto", default="Continuar"),
        P("action", "Acao", "action", "toast:Botão pressionado"),
        P("style", "Estilo", "choice", "filled", ["filled", "outlined", "tonal", "text"]),
    ], [], "Botao que executa uma acao."),
    Comp("image", "Imagem", MEDIA, "IMG", [
        P("url", "URL da imagem", default="https://picsum.photos/800/400"),
        P("source", "Origem", "choice", "url", ["url", "photo"]),
        P("height", "Altura (dp)", "int", 180),
        P("description", "Descricao (acessibilidade)", default="Imagem"),
    ], [], "Imagem por URL ou foto tirada/escolhida na tela."),
    Comp("card", "Cartao", LAYOUT, "[=]", [
        P("title", "Titulo", default="Cartão"),
        P("body", "Conteudo", "multiline", "Descrição do cartão."),
        P("action", "Acao ao tocar", "action", "none"),
    ], [], "Cartao com titulo e texto, opcionalmente clicavel."),
    Comp("banner", "Banner promocional", LAYOUT, "!!", [
        P("title", "Titulo", default="Oferta especial"),
        P("subtitle", "Subtitulo", default="Até 30% de desconto hoje"),
        P("action", "Acao ao tocar", "action", "none"),
    ], [], "Faixa colorida de destaque."),
    Comp("text_field", "Campo de texto", INPUT, "___", [
        P("label", "Rotulo", default="Nome"),
        P("key", "Chave do campo", default="name"),
        P("input", "Tipo de entrada", "choice", "text", INPUT_TYPES),
        P("validation", "Validacao", "choice", "none", VALIDATIONS),
    ], [], "Campo de digitacao. A chave liga o campo ao formulario e ao banco."),
    Comp("checkbox", "Caixa de selecao", INPUT, "[x]", [
        P("label", "Rotulo", default="Aceito os termos"),
        P("key", "Chave do campo", default="accepted"),
    ], [], "Opcao marcavel."),
    Comp("switch", "Interruptor", INPUT, "(o-)", [
        P("label", "Rotulo", default="Receber notificações"),
        P("key", "Chave do campo", default="enabled"),
    ], [], "Liga/desliga."),
    Comp("slider", "Controle deslizante", INPUT, "-o-", [
        P("label", "Rotulo", default="Valor"),
        P("key", "Chave do campo", default="amount"),
        P("min", "Minimo", "float", 0.0),
        P("max", "Maximo", "float", 100.0),
    ], [], "Seleciona um numero em um intervalo."),
    Comp("radio_group", "Opcoes unicas", INPUT, "(*)", [
        P("label", "Rotulo", default="Escolha uma opção"),
        P("key", "Chave do campo", default="option"),
        P("options", "Opcoes (separadas por ;)", default="Opção A;Opção B;Opção C"),
    ], [], "Grupo de botoes de radio."),
    Comp("dropdown", "Lista suspensa", INPUT, "[v]", [
        P("label", "Rotulo", default="Categoria"),
        P("key", "Chave do campo", default="category"),
        P("options", "Opcoes (separadas por ;)", default="Geral;Trabalho;Pessoal"),
    ], [], "Menu de selecao."),
    Comp("chips", "Chips de filtro", INPUT, "(a)(b)", [
        P("key", "Chave do campo", default="filter"),
        P("options", "Opcoes (separadas por ;)", default="Todos;Novos;Populares"),
    ], [], "Selecao rapida em forma de etiquetas."),
    Comp("tabs", "Abas", INPUT, "|a|b|", [
        P("key", "Chave do campo", default="tab"),
        P("options", "Abas (separadas por ;)", default="Resumo;Detalhes;Avaliações"),
    ], [], "Barra de abas; o valor selecionado fica no estado da tela."),
    Comp("date_picker", "Seletor de data", INPUT, "[d]", [
        P("label", "Rotulo", default="Selecionar data"),
        P("key", "Chave do campo", default="date"),
    ], [], "Abre um calendario e guarda a data escolhida."),
    Comp("rating", "Avaliacao (estrelas)", INPUT, "***", [
        P("label", "Rotulo", default="Sua avaliação"),
        P("key", "Chave do campo", default="rating"),
        P("max", "Estrelas", "int", 5),
    ], [], "Nota de 1 a N estrelas."),
    Comp("stepper", "Quantidade (+/-)", INPUT, "-1+", [
        P("label", "Rotulo", default="Quantidade"),
        P("key", "Chave do campo", default="quantity"),
        P("max", "Maximo", "int", 99),
    ], [], "Contador com botoes de mais e menos."),
    Comp("search_bar", "Barra de busca", DATA, "(?)", [
        P("hint", "Texto de ajuda", default="Buscar..."),
    ], [], "Filtra automaticamente as listas da mesma tela."),
    Comp("list", "Lista", DATA, "=", [
        P("source", "Fonte de dados", "source", "sample:default"),
        P("item_action", "Acao ao tocar no item", "action", "none"),
        P("show_image", "Mostrar imagem", "bool", True),
        P("show_price", "Mostrar preco", "bool", False),
        P("empty_text", "Texto quando vazia", default="Nenhum item encontrado"),
    ], [], "Lista de itens de dados de exemplo, banco, API, carrinho ou favoritos."),
    Comp("grid", "Grade", DATA, "::", [
        P("source", "Fonte de dados", "source", "sample:default"),
        P("item_action", "Acao ao tocar no item", "action", "none"),
        P("columns", "Colunas", "int", 2),
        P("show_price", "Mostrar preco", "bool", False),
    ], [], "Itens em grade (produtos, galeria)."),
    Comp("item_detail", "Detalhe do item", DATA, "[i]", [
        P("show_image", "Mostrar imagem", "bool", True),
        P("show_price", "Mostrar preco", "bool", False),
    ], [], "Mostra o item recebido ao navegar a partir de uma lista."),
    Comp("stat_card", "Indicador (KPI)", DATA, "#", [
        P("label", "Rotulo", default="Total"),
        P("value", "Valor", default="128"),
    ], [], "Numero de destaque com rotulo."),
    Comp("chart", "Grafico", DATA, "|||", [
        P("style", "Tipo", "choice", "bar", ["bar", "line", "pie"]),
        P("values", "Valores (separados por virgula)", default="4,7,3,9,6,8"),
    ], ["charts"], "Grafico de barras, linhas ou pizza."),
    Comp("cart_summary", "Resumo do carrinho", DATA, "$", [
        P("action", "Acao do botao", "action", "checkout:"),
        P("button", "Texto do botao", default="Finalizar compra"),
    ], ["cart"], "Total e quantidade de itens do carrinho, com botao."),
    Comp("avatar", "Avatar / perfil", BASIC, "(@)", [
        P("name", "Nome", default="Maria Silva"),
        P("subtitle", "Subtitulo", default="maria@email.com"),
    ], [], "Circulo com iniciais, nome e subtitulo."),
    Comp("divider", "Divisor", LAYOUT, "--", [], [], "Linha separadora."),
    Comp("spacer", "Espaco", LAYOUT, "  ", [P("height", "Altura (dp)", "int", 16)], [], "Espaco vertical."),
    Comp("progress", "Progresso", LAYOUT, "...", [
        P("style", "Tipo", "choice", "linear", ["linear", "circular"]),
        P("bind_loading", "Mostrar so carregando", "bool", True),
    ], [], "Indicador de carregamento."),
    Comp("web_view", "Pagina web", MEDIA, "www", [
        P("url", "URL", default="https://developer.android.com"),
        P("height", "Altura (dp)", "int", 420),
    ], [], "Exibe um site dentro do app."),
    Comp("map_view", "Mapa", MEDIA, "MAP", [
        P("lat", "Latitude", "float", -23.5505),
        P("lng", "Longitude", "float", -46.6333),
        P("title", "Titulo do marcador", default="Local"),
        P("height", "Altura (dp)", "int", 260),
    ], ["maps"], "Google Maps com marcador."),
    Comp("video_player", "Video", MEDIA, "|>", [
        P("url", "URL do video", default="https://storage.googleapis.com/exoplayer-test-media-0/BigBuckBunny_320x180.mp4"),
        P("height", "Altura (dp)", "int", 220),
    ], ["video_player"], "Player de video com controles."),
    Comp("qr_code", "QR Code", MEDIA, "QR", [
        P("text", "Conteudo", default="https://example.com"),
        P("size", "Tamanho (dp)", "int", 200),
    ], ["qr_generator"], "Gera e exibe um QR Code."),
    Comp("timer", "Cronometro", MEDIA, "00:00", [
        P("mode", "Modo", "choice", "stopwatch", ["stopwatch", "countdown"]),
        P("seconds", "Segundos (contagem regressiva)", "int", 1500),
    ], ["timer"], "Cronometro ou contagem regressiva com iniciar/pausar/zerar."),
    Comp("calendar", "Calendario", INPUT, "[31]", [
        P("key", "Chave do campo", default="selectedDate"),
    ], ["calendar_view"], "Calendario mensal com selecao de dia."),
    Comp("camera_preview", "Camera ao vivo", MEDIA, "CAM", [
        P("height", "Altura (dp)", "int", 320),
    ], ["camerax_preview"], "Imagem ao vivo da camera (CameraX)."),
    Comp("lottie", "Animacao Lottie", MEDIA, "~", [
        P("url", "URL do JSON", default="https://assets2.lottiefiles.com/packages/lf20_jcikwtux.json"),
        P("height", "Altura (dp)", "int", 200),
    ], ["lottie"], "Animacao vetorial em loop."),
    Comp("carousel", "Carrossel", DATA, "<=>", [
        P("source", "Fonte de dados", "source", "sample:default"),
        P("item_action", "Acao ao tocar no item", "action", "none"),
        P("height", "Altura (dp)", "int", 180),
    ], [], "Imagens grandes que deslizam na horizontal (destaques, banners)."),
    Comp("h_list", "Lista horizontal", DATA, "|||>", [
        P("source", "Fonte de dados", "source", "sample:default"),
        P("item_action", "Acao ao tocar no item", "action", "none"),
        P("show_price", "Mostrar preco", "bool", False),
    ], [], "Cartoes pequenos em uma linha rolavel (categorias, recomendados)."),
    Comp("expandable", "Secao expansivel", LAYOUT, "[+]", [
        P("title", "Titulo", default="Pergunta frequente"),
        P("body", "Conteudo", "multiline", "Resposta detalhada que aparece ao tocar."),
    ], [], "Bloco que abre e fecha ao tocar (FAQ, detalhes)."),
    Comp("key_value", "Tabela de informacoes", DATA, "k:v", [
        P("title", "Titulo", default="Informações"),
        P("rows", "Linhas (Rotulo: valor, uma por linha)", "multiline", "Horário: 08h às 18h\nTelefone: (11) 4000-0000\nEndereço: Rua Central, 100"),
    ], [], "Lista de pares rotulo e valor."),
    Comp("steps", "Etapas (progresso)", DATA, "1-2-3", [
        P("options", "Etapas (separadas por ;)", default="Recebido;Em preparo;A caminho;Entregue"),
        P("current", "Etapa atual (1, 2, 3...)", "int", 2),
    ], [], "Indicador de etapas, como o andamento de um pedido."),
    Comp("alert", "Aviso", LAYOUT, "(!)", [
        P("text", "Mensagem", "multiline", "Atenção: horário especial neste feriado."),
        P("kind", "Tipo", "choice", "info", ["info", "success", "warning", "error"]),
    ], [], "Caixa colorida de informacao, sucesso, alerta ou erro."),
    Comp("button_row", "Dois botoes lado a lado", BASIC, "[ ][ ]", [
        P("text1", "Texto do botao 1", default="Cancelar"),
        P("action1", "Acao do botao 1", "action", "back"),
        P("text2", "Texto do botao 2", default="Confirmar"),
        P("action2", "Acao do botao 2", "action", "toast:Confirmado"),
    ], [], "Par de botoes na mesma linha (secundario e principal)."),
    Comp("signature", "Assinatura / desenho", INPUT, "~~", [
        P("label", "Rotulo", default="Assine abaixo"),
        P("height", "Altura (dp)", "int", 180),
    ], [], "Area para assinar ou desenhar com o dedo, com botao para limpar."),
    Comp("quote", "Citacao / depoimento", BASIC, "\"\"", [
        P("text", "Texto", "multiline", "Excelente atendimento, recomendo a todos!"),
        P("author", "Autor", default="Cliente satisfeito"),
    ], [], "Frase em destaque com autor."),
    Comp("tags", "Etiquetas", BASIC, "#tag", [
        P("options", "Etiquetas (separadas por ;)", default="Novo;Frete grátis;Mais vendido"),
    ], [], "Etiquetas informativas (nao clicaveis)."),
    Comp("price_tag", "Preco em destaque", DATA, "R$", [
        P("label", "Rotulo", default="Plano mensal"),
        P("value", "Preco", default="R$ 49,90"),
        P("old_value", "Preco antigo (opcional)", default="R$ 69,90"),
    ], [], "Preco grande com valor antigo riscado."),
    Comp("social_links", "Redes sociais e contato", BASIC, "@->", [
        P("whatsapp", "WhatsApp (numero com DDI)", default="5511999999999"),
        P("instagram", "Instagram (usuario)", default="minhaempresa"),
        P("website", "Site", default="https://example.com"),
    ], [], "Botoes para WhatsApp, Instagram e site."),
    Comp("fab", "Botao flutuante", BASIC, "(+)", [
        P("icon", "Icone", "icon", "add"),
        P("action", "Acao", "action", "toast:Novo item"),
    ], [], "Botao circular no canto da tela (um por tela)."),
]

COMPONENTS = {c.type: c for c in COMPONENT_LIST}

INPUT_COMPONENTS = {"text_field", "checkbox", "switch", "slider", "radio_group", "dropdown",
                    "chips", "tabs", "date_picker", "rating", "stepper", "calendar"}

# Blocos que exibem itens de uma fonte de dados (viram listas no ViewModel).
LIST_COMPONENTS = {"list", "grid", "carousel", "h_list"}


def default_props(ctype):
    comp = COMPONENTS[ctype]
    return {p.key: p.default for p in comp.props}


def by_category():
    groups = {}
    for c in COMPONENT_LIST:
        groups.setdefault(c.category, []).append(c)
    return groups


# ---------------------------------------------------------------- acoes
# arg: none | screen | text | endpoint | url
Action = namedtuple("Action", "key label arg feature needs_item")

ACTION_LIST = [
    Action("none", "Nenhuma", "none", None, False),
    Action("navigate", "Navegar para tela", "screen", None, False),
    Action("back", "Voltar", "none", None, False),
    Action("toast", "Mostrar mensagem", "text", None, False),
    Action("submit", "Enviar formulario (valida e salva)", "screen", None, False),
    Action("api", "Chamar API", "endpoint", "network", False),
    Action("refresh", "Recarregar dados", "none", None, False),
    Action("open_url", "Abrir link", "url", None, False),
    Action("share", "Compartilhar texto", "text", None, False),
    Action("share_item", "Compartilhar item", "none", None, True),
    Action("call", "Ligar para numero", "text", None, False),
    Action("email", "Enviar e-mail", "text", None, False),
    Action("sms", "Enviar SMS", "text", None, False),
    Action("copy", "Copiar texto", "text", "clipboard", False),
    Action("login", "Entrar (login local)", "screen", "local_auth", False),
    Action("register", "Cadastrar (login local)", "screen", "local_auth", False),
    Action("logout", "Sair da conta", "screen", "local_auth", False),
    Action("add_cart", "Adicionar ao carrinho", "none", "cart", True),
    Action("remove_cart", "Remover do carrinho", "none", "cart", True),
    Action("checkout", "Finalizar compra", "screen", "cart", False),
    Action("favorite", "Favoritar item", "none", "favorites", True),
    Action("send_message", "Enviar mensagem (chat)", "none", "chat", False),
    Action("vibrate", "Vibrar", "none", "vibration", False),
    Action("notify", "Notificar", "text", "notifications", False),
    Action("speak", "Falar texto", "text", "text_to_speech", False),
    Action("listen", "Ouvir voz (preenche a busca)", "none", "speech_to_text", False),
    Action("flashlight", "Lanterna liga/desliga", "none", "flashlight", False),
    Action("location", "Mostrar minha localizacao", "none", "location", False),
    Action("scan_code", "Ler QR/codigo de barras", "none", "barcode_scanner", False),
    Action("take_photo", "Tirar foto", "none", "camera_capture", False),
    Action("pick_image", "Escolher imagem", "none", "image_picker", False),
    Action("biometric", "Autenticar biometria e navegar", "screen", "biometric", False),
    Action("rate_app", "Avaliar app", "none", "in_app_review", False),
    Action("toggle_theme", "Alternar tema", "none", "dark_mode_toggle", False),
    Action("finish_onboarding", "Concluir onboarding e navegar", "screen", "onboarding_state", False),
    Action("device_info", "Mostrar info do aparelho", "none", "device_info", False),
    Action("battery", "Mostrar bateria", "none", "battery", False),
    Action("delete_item", "Excluir item", "none", None, True),
    Action("clear_form", "Limpar formulario", "none", None, False),
    Action("export_csv", "Exportar lista em CSV", "none", "csv_export", False),
    Action("open_map", "Abrir no mapa (endereco ou lat,lng)", "text", None, False),
    Action("whatsapp", "Abrir conversa no WhatsApp", "text", None, False),
    Action("share_location", "Compartilhar minha localizacao", "none", "location", False),
    Action("open_settings", "Abrir configuracoes do app", "none", None, False),
    Action("pick_file", "Escolher arquivo", "none", "document_picker", False),
    Action("report_bug", "Relatar problema", "none", "bug_report", False),
]

ACTIONS = {a.key: a for a in ACTION_LIST}


ACTION_SEPARATOR = " && "


def split_actions(value):
    """Separa uma sequencia de acoes ('a:x && b && c:y') em itens individuais."""
    parts = [p.strip() for p in str(value or "none").split("&&")]
    parts = [p for p in parts if p and p != "none"]
    return parts or ["none"]


def join_actions(items):
    items = [i for i in items if i and i != "none"]
    return ACTION_SEPARATOR.join(items) if items else "none"


def parse_action(value):
    """Separa 'chave:argumento' em (chave, argumento)."""
    value = (value or "none").strip()
    if ":" in value:
        key, arg = value.split(":", 1)
    else:
        key, arg = value, ""
    if key not in ACTIONS:
        return "none", ""
    return key, arg


# ---------------------------------------------------------------- icones
# nome -> (icone Compose, caminho vetorial Android 24x24)
ICONS = {
    "home": ("Icons.Filled.Home", "M10,20v-6h4v6h5v-8h3L12,3 2,12h3v8z"),
    "list": ("Icons.AutoMirrored.Filled.List", "M3,13h2v-2H3v2zM3,17h2v-2H3v2zM3,9h2V7H3v2zM7,13h14v-2H7v2zM7,17h14v-2H7v2zM7,7v2h14V7H7z"),
    "person": ("Icons.Filled.Person", "M12,12c2.21,0 4,-1.79 4,-4s-1.79,-4 -4,-4 -4,1.79 -4,4 1.79,4 4,4zM12,14c-2.67,0 -8,1.34 -8,4v2h16v-2c0,-2.66 -5.33,-4 -8,-4z"),
    "settings": ("Icons.Filled.Settings", "M19.14,12.94c0.04,-0.3 0.06,-0.61 0.06,-0.94c0,-0.32 -0.02,-0.64 -0.07,-0.94l2.03,-1.58c0.18,-0.14 0.23,-0.41 0.12,-0.61l-1.92,-3.32c-0.12,-0.22 -0.37,-0.29 -0.59,-0.22l-2.39,0.96c-0.5,-0.38 -1.03,-0.7 -1.62,-0.94L14.4,2.81c-0.04,-0.24 -0.24,-0.41 -0.48,-0.41h-3.84c-0.24,0 -0.43,0.17 -0.47,0.41L9.25,5.35C8.66,5.59 8.12,5.92 7.63,6.29L5.24,5.33c-0.22,-0.08 -0.47,0 -0.59,0.22L2.74,8.87C2.62,9.08 2.66,9.34 2.86,9.48l2.03,1.58C4.84,11.36 4.8,11.69 4.8,12s0.02,0.64 0.07,0.94l-2.03,1.58c-0.18,0.14 -0.23,0.41 -0.12,0.61l1.92,3.32c0.12,0.22 0.37,0.29 0.59,0.22l2.39,-0.96c0.5,0.38 1.03,0.7 1.62,0.94l0.36,2.54c0.05,0.24 0.24,0.41 0.48,0.41h3.84c0.24,0 0.44,-0.17 0.47,-0.41l0.36,-2.54c0.59,-0.24 1.13,-0.56 1.62,-0.94l2.39,0.96c0.22,0.08 0.47,0 0.59,-0.22l1.92,-3.32c0.12,-0.22 0.07,-0.47 -0.12,-0.61L19.14,12.94zM12,15.6c-1.98,0 -3.6,-1.62 -3.6,-3.6s1.62,-3.6 3.6,-3.6s3.6,1.62 3.6,3.6S13.98,15.6 12,15.6z"),
    "cart": ("Icons.Filled.ShoppingCart", "M7,18c-1.1,0 -1.99,0.9 -1.99,2S5.9,22 7,22s2,-0.9 2,-2 -0.9,-2 -2,-2zM1,2v2h2l3.6,7.59 -1.35,2.45c-0.16,0.28 -0.25,0.61 -0.25,0.96 0,1.1 0.9,2 2,2h12v-2H7.42c-0.14,0 -0.25,-0.11 -0.25,-0.25l0.03,-0.12 0.9,-1.63h7.45c0.75,0 1.41,-0.41 1.75,-1.03l3.58,-6.49c0.08,-0.14 0.12,-0.31 0.12,-0.48 0,-0.55 -0.45,-1 -1,-1H5.21l-0.94,-2H1zM17,18c-1.1,0 -1.99,0.9 -1.99,2s0.89,2 1.99,2 2,-0.9 2,-2 -0.9,-2 -2,-2z"),
    "favorite": ("Icons.Filled.Favorite", "M12,21.35l-1.45,-1.32C5.4,15.36 2,12.28 2,8.5 2,5.42 4.42,3 7.5,3c1.74,0 3.41,0.81 4.5,2.09C13.09,3.81 14.76,3 16.5,3 19.58,3 22,5.42 22,8.5c0,3.78 -3.4,6.86 -8.55,11.54L12,21.35z"),
    "search": ("Icons.Filled.Search", "M15.5,14h-0.79l-0.28,-0.27C15.41,12.59 16,11.11 16,9.5 16,5.91 13.09,3 9.5,3S3,5.91 3,9.5 5.91,16 9.5,16c1.61,0 3.09,-0.59 4.23,-1.57l0.27,0.28v0.79l5,4.99L20.49,19l-4.99,-5zM9.5,14C7.01,14 5,11.99 5,9.5S7.01,5 9.5,5 14,7.01 14,9.5 11.99,14 9.5,14z"),
    "info": ("Icons.Filled.Info", "M12,2C6.48,2 2,6.48 2,12s4.48,10 10,10 10,-4.48 10,-10S17.52,2 12,2zM13,17h-2v-6h2v6zM13,9h-2V7h2v2z"),
    "notifications": ("Icons.Filled.Notifications", "M12,22c1.1,0 2,-0.9 2,-2h-4c0,1.1 0.89,2 2,2zM18,16v-5c0,-3.07 -1.64,-5.64 -4.5,-6.32V4c0,-0.83 -0.67,-1.5 -1.5,-1.5s-1.5,0.67 -1.5,1.5v0.68C7.63,5.36 6,7.92 6,11v5l-2,2v1h16v-1l-2,-2z"),
    "place": ("Icons.Filled.Place", "M12,2C8.13,2 5,5.13 5,9c0,5.25 7,13 7,13s7,-7.75 7,-13c0,-3.87 -3.13,-7 -7,-7zM12,11.5c-1.38,0 -2.5,-1.12 -2.5,-2.5s1.12,-2.5 2.5,-2.5 2.5,1.12 2.5,2.5 -1.12,2.5 -2.5,2.5z"),
    "star": ("Icons.Filled.Star", "M12,17.27L18.18,21l-1.64,-7.03L22,9.24l-7.19,-0.61L12,2 9.19,8.63 2,9.24l5.46,4.73L5.82,21z"),
    "email": ("Icons.Filled.Email", "M20,4H4c-1.1,0 -1.99,0.9 -1.99,2L2,18c0,1.1 0.9,2 2,2h16c1.1,0 2,-0.9 2,-2V6c0,-1.1 -0.9,-2 -2,-2zM20,8l-8,5 -8,-5V6l8,5 8,-5v2z"),
    "date": ("Icons.Filled.DateRange", "M9,11H7v2h2v-2zM13,11h-2v2h2v-2zM17,11h-2v2h2v-2zM19,4h-1V2h-2v2H8V2H6v2H5c-1.11,0 -1.99,0.9 -1.99,2L3,20c0,1.1 0.89,2 2,2h14c1.1,0 2,-0.9 2,-2V6c0,-1.1 -0.9,-2 -2,-2zM19,20H5V9h14v11z"),
    "phone": ("Icons.Filled.Phone", "M6.62,10.79c1.44,2.83 3.76,5.14 6.59,6.59l2.2,-2.2c0.27,-0.27 0.67,-0.36 1.02,-0.24 1.12,0.37 2.33,0.57 3.57,0.57 0.55,0 1,0.45 1,1V20c0,0.55 -0.45,1 -1,1 -9.39,0 -17,-7.61 -17,-17 0,-0.55 0.45,-1 1,-1h3.5c0.55,0 1,0.45 1,1 0,1.25 0.2,2.45 0.57,3.57 0.11,0.35 0.03,0.74 -0.25,1.02l-2.2,2.2z"),
    "play": ("Icons.Filled.PlayArrow", "M8,5v14l11,-7z"),
    "add": ("Icons.Filled.Add", "M19,13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"),
    "check": ("Icons.Filled.Check", "M9,16.17L4.83,12l-1.42,1.41L9,19 21,7l-1.41,-1.41z"),
    "account": ("Icons.Filled.AccountCircle", "M12,2C6.48,2 2,6.48 2,12s4.48,10 10,10 10,-4.48 10,-10S17.52,2 12,2zM12,5c1.66,0 3,1.34 3,3s-1.34,3 -3,3 -3,-1.34 -3,-3 1.34,-3 3,-3zM12,19.2c-2.5,0 -4.71,-1.28 -6,-3.22 0.03,-1.99 4,-3.08 6,-3.08 1.99,0 5.97,1.09 6,3.08 -1.29,1.94 -3.5,3.22 -6,3.22z"),
    "build": ("Icons.Filled.Build", "M22.7,19l-9.1,-9.1c0.9,-2.3 0.4,-5 -1.5,-6.9 -2,-2 -5,-2.4 -7.4,-1.3L9,6 6,9 1.6,4.7C0.4,7.1 0.9,10.1 2.9,12.1c1.9,1.9 4.6,2.4 6.9,1.5l9.1,9.1c0.4,0.4 1,0.4 1.4,0l2.3,-2.3c0.5,-0.4 0.5,-1.1 0.1,-1.4z"),
    "lock": ("Icons.Filled.Lock", "M18,8h-1V6c0,-2.76 -2.24,-5 -5,-5S7,3.24 7,6v2H6c-1.1,0 -2,0.9 -2,2v10c0,1.1 0.9,2 2,2h12c1.1,0 2,-0.9 2,-2V10c0,-1.1 -0.9,-2 -2,-2zM12,17c-1.1,0 -2,-0.9 -2,-2s0.9,-2 2,-2 2,0.9 2,2 -0.9,2 -2,2zM15.1,8H8.9V6c0,-1.71 1.39,-3.1 3.1,-3.1 1.71,0 3.1,1.39 3.1,3.1v2z"),
    "edit": ("Icons.Filled.Edit", "M3,17.25V21h3.75L17.81,9.94l-3.75,-3.75L3,17.25zM20.71,7.04c0.39,-0.39 0.39,-1.02 0,-1.41l-2.34,-2.34c-0.39,-0.39 -1.02,-0.39 -1.41,0l-1.83,1.83 3.75,3.75 1.83,-1.83z"),
    "send": ("Icons.AutoMirrored.Filled.Send", "M2.01,21L23,12 2.01,3 2,10l15,2 -15,2z"),
    "face": ("Icons.Filled.Face", "M9,11.75c-0.69,0 -1.25,0.56 -1.25,1.25s0.56,1.25 1.25,1.25 1.25,-0.56 1.25,-1.25 -0.56,-1.25 -1.25,-1.25zM15,11.75c-0.69,0 -1.25,0.56 -1.25,1.25s0.56,1.25 1.25,1.25 1.25,-0.56 1.25,-1.25 -0.56,-1.25 -1.25,-1.25zM12,2C6.48,2 2,6.48 2,12s4.48,10 10,10 10,-4.48 10,-10S17.52,2 12,2zM12,20c-4.41,0 -8,-3.59 -8,-8 0,-0.29 0.02,-0.58 0.05,-0.86 2.36,-1.05 4.23,-2.98 5.21,-5.37C11.07,8.33 14.05,10 17.42,10c0.78,0 1.53,-0.09 2.25,-0.26 0.21,0.71 0.33,1.47 0.33,2.26 0,4.41 -3.59,8 -8,8z"),
    "thumb": ("Icons.Filled.ThumbUp", "M1,21h4L5,9L1,9v12zM23,10c0,-1.1 -0.9,-2 -2,-2h-6.31l0.95,-4.57 0.03,-0.32c0,-0.41 -0.17,-0.79 -0.44,-1.06L14.17,1 7.59,7.59C7.22,7.95 7,8.45 7,9v10c0,1.1 0.9,2 2,2h9c0.83,0 1.54,-0.5 1.84,-1.22l3.02,-7.05c0.09,-0.23 0.14,-0.47 0.14,-0.73v-2z"),
}

ICON_NAMES = list(ICONS.keys())
