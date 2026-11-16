# -*- coding: utf-8 -*-
"""Cem modelos de aplicativos prontos, montados a partir de blocos.

Cada modelo define telas, funcionalidades, entidades de banco, APIs e dados de
exemplo. Ao escolher um modelo, o projeto e criado ja integrado e pode ser
editado livremente no construtor.
"""

import copy

from ..core.model import Project, Screen, Component, Entity, new_id
from ..core.naming import to_snake
from .components import default_props
from . import api_presets as AP

TEMPLATES = []


# ------------------------------------------------------------------ construtores

def C(ctype, **props):
    """Cria um bloco com as propriedades padrao sobrescritas."""
    values = default_props(ctype)
    values.update(props)
    return Component(type=ctype, props=values)


def S(name, title, comps, nav=False, icon="home", form=""):
    return Screen(name=name, title=title, components=list(comps), in_nav=nav, icon=icon, form_entity=form)


def E(name, spec):
    fields = []
    for part in spec.split(","):
        part = part.strip()
        if part:
            fname, ftype = part.split(":")
            fields.append([fname.strip(), ftype.strip()])
    return Entity(name=name, fields=fields)


def samples(prefix, rows):
    """Gera itens de exemplo: (titulo, subtitulo, preco ou None, descricao opcional)."""
    items = []
    for index, row in enumerate(rows):
        title, subtitle = row[0], row[1]
        price = row[2] if len(row) > 2 else None
        desc = row[3] if len(row) > 3 else f"{title}: {subtitle}."
        items.append({
            "title": title, "subtitle": subtitle, "description": desc, "price": price,
            "image": f"https://picsum.photos/seed/{to_snake(prefix)}{index}/600/400",
        })
    return items


def T(name, category, description, screens, features=(), entities=(), apis=(), sample_sets=None,
      nav="bottom", color="#1E88E5", start=None, glyph="APP"):
    TEMPLATES.append({
        "name": name, "category": category, "description": description, "screens": screens,
        "features": list(features), "entities": list(entities), "apis": list(apis),
        "samples": sample_sets or {}, "navigation": nav, "color": color,
        "start": start or (screens[0].name if screens else ""), "glyph": glyph,
    })


# ------------------------------------------------------------------ telas tipicas

def login_screens(next_screen):
    return [
        S("Login", "Entrar", [
            C("spacer", height=24),
            C("title", text="Bem-vindo", align="center"),
            C("text", text="Entre com seu e-mail e senha para continuar.", style="caption", align="center"),
            C("text_field", label="E-mail", key="email", input="email", validation="email"),
            C("text_field", label="Senha", key="password", input="password", validation="required"),
            C("button", text="Entrar", action=f"login:{next_screen}"),
            C("button", text="Criar conta", action="navigate:Cadastro", style="text"),
        ], icon="lock"),
        S("Cadastro", "Criar conta", [
            C("title", text="Crie sua conta", size="medium"),
            C("text_field", label="Nome", key="name", validation="required"),
            C("text_field", label="E-mail", key="email", input="email", validation="email"),
            C("text_field", label="Senha", key="password", input="password", validation="password"),
            C("checkbox", label="Aceito os termos de uso", key="terms"),
            C("button", text="Cadastrar", action=f"register:{next_screen}"),
        ], icon="person"),
    ]


def list_screen(name, title, source, detail="Detalhe", icon="list", nav=True, search=True, grid=False,
                price=False, header=None, chips=None, fab=None, item_action=None):
    comps = list(header or [])
    if search:
        comps.append(C("search_bar", hint=f"Buscar em {title.lower()}..."))
    if chips:
        comps.append(C("chips", key="filter", options=chips))
    action = item_action or (f"navigate:{detail}" if detail else "none")
    if grid:
        comps.append(C("grid", source=source, item_action=action, show_price=price))
    else:
        comps.append(C("list", source=source, item_action=action, show_price=price))
    if fab:
        comps.append(C("fab", icon="add", action=fab))
    return S(name, title, comps, nav=nav, icon=icon)


def detail_screen(name="Detalhe", title="Detalhes", buttons=(), price=False, extra=None):
    comps = [C("item_detail", show_price=price)]
    comps += list(extra or [])
    for text, action, *style in buttons:
        comps.append(C("button", text=text, action=action, style=style[0] if style else "filled"))
    return S(name, title, comps, icon="info")


def form_screen(name, title, fields, entity="", after="", button="Salvar", extra=None, icon="edit", nav=False):
    comps = [C("title", text=title, size="medium")]
    for f in fields:
        label, key = f[0], f[1]
        kind = f[2] if len(f) > 2 else "text"
        validation = f[3] if len(f) > 3 else "none"
        if kind in ("checkbox", "switch"):
            comps.append(C(kind, label=label, key=key))
        elif kind == "date":
            comps.append(C("date_picker", label=label, key=key))
        elif kind.startswith("dropdown"):
            comps.append(C("dropdown", label=label, key=key, options=kind.split("=", 1)[1]))
        elif kind == "rating":
            comps.append(C("rating", label=label, key=key))
        elif kind == "slider":
            comps.append(C("slider", label=label, key=key))
        elif kind == "stepper":
            comps.append(C("stepper", label=label, key=key))
        else:
            comps.append(C("text_field", label=label, key=key, input=kind, validation=validation))
    comps += list(extra or [])
    comps.append(C("button", text=button, action=f"submit:{after}"))
    return S(name, title, comps, form=entity, icon=icon, nav=nav)


def profile_screen(logout_to="", name="Perfil", extra=None):
    comps = [C("avatar", name="Usuário", subtitle="usuario@email.com"), C("divider")]
    comps += list(extra or [])
    comps += [
        C("card", title="Meus dados", body="Nome, e-mail e preferências da conta."),
        C("card", title="Ajuda", body="Fale com o suporte ou consulte as perguntas frequentes.",
          action="email:suporte@exemplo.com"),
    ]
    if logout_to:
        comps.append(C("button", text="Sair", action=f"logout:{logout_to}", style="outlined"))
    return S(name, "Perfil", comps, nav=True, icon="person")


def settings_screen(name="Ajustes", extra=None):
    comps = [
        C("switch", label="Notificações", key="notifications"),
        C("switch", label="Modo escuro", key="darkMode"),
        C("dropdown", label="Idioma", key="language", options="Português;English;Español"),
    ]
    comps += list(extra or [])
    comps += [C("divider"), C("button", text="Avaliar o app", action="toast:Obrigado pelo apoio!", style="text"),
              C("text", text="Versão 1.0.0", style="caption", align="center")]
    return S(name, "Ajustes", comps, nav=True, icon="settings")


def cart_screen(checkout_to="Pedido", name="Carrinho"):
    return S(name, "Carrinho", [
        C("list", source="cart", item_action="remove_cart", show_price=True,
          empty_text="Seu carrinho está vazio"),
        C("text", text="Toque em um item para remover uma unidade.", style="caption"),
        C("cart_summary", action=f"checkout:{checkout_to}", button="Finalizar pedido"),
    ], nav=True, icon="cart")


def done_screen(name, title, message, back_to):
    return S(name, title, [
        C("spacer", height=40),
        C("title", text=title, align="center"),
        C("text", text=message, align="center"),
        C("button", text="Voltar ao início", action=f"navigate:{back_to}"),
    ], icon="check")


def chat_screen(name="Chat", title="Mensagens", nav=True):
    return S(name, title, [
        C("list", source="chat", show_image=False, empty_text="Nenhuma mensagem"),
        C("text_field", label="Mensagem", key="message"),
        C("button", text="Enviar", action="send_message"),
    ], nav=nav, icon="email")


def dashboard_screen(name, title, stats, values="4,7,3,9,6,8", chart="bar", extra=None, nav=True, icon="home"):
    comps = [C("title", text=title, size="medium")]
    for label, value in stats:
        comps.append(C("stat_card", label=label, value=value))
    comps.append(C("chart", style=chart, values=values))
    comps += list(extra or [])
    return S(name, title, comps, nav=nav, icon=icon)


def about_screen(app, text):
    return S("Sobre", "Sobre", [
        C("title", text=app), C("text", text=text),
        C("button", text="Compartilhar o app", action=f"share:Conheça o app {app}!", style="outlined"),
    ], nav=True, icon="info")


def home_header(title, subtitle, banner=None):
    comps = [C("title", text=title), C("text", text=subtitle, style="caption")]
    if banner:
        comps.append(C("banner", title=banner[0], subtitle=banner[1]))
    return comps


# ------------------------------------------------------------------ dados de exemplo

RESTAURANTS = samples("rest", [
    ("Pizzaria Bella Napoli", "Italiana - 30-40 min", None), ("Sushi Kenzo", "Japonesa - 40-50 min", None),
    ("Burger House", "Lanches - 20-30 min", None), ("Cantina da Nonna", "Massas - 35 min", None),
    ("Taco Loco", "Mexicana - 25 min", None), ("Green Bowl", "Saudável - 20 min", None),
    ("Churrascaria Gaúcha", "Carnes - 45 min", None), ("Açaí da Praia", "Sobremesas - 15 min", None)])
DISHES = samples("dish", [
    ("Pizza Margherita", "Molho de tomate, mussarela e manjericão", 49.9),
    ("Combo Sushi 20 peças", "Salmão, atum e skin", 79.9), ("Cheeseburger duplo", "Pão brioche e cheddar", 34.5),
    ("Lasanha bolonhesa", "Porção individual", 42.0), ("Burrito de frango", "Com guacamole", 29.9),
    ("Salada Caesar", "Frango grelhado e croutons", 27.0), ("Picanha na brasa", "Arroz, farofa e vinagrete", 69.9),
    ("Açaí 500 ml", "Banana, granola e mel", 22.0)])
PRODUCTS = samples("prod", [
    ("Fone Bluetooth Pro", "Áudio - cancelamento de ruído", 299.9), ("Smartwatch Fit", "Vestíveis", 449.0),
    ("Camiseta Básica", "Moda - algodão", 59.9), ("Tênis Runner", "Calçados esportivos", 389.0),
    ("Mochila Urbana", "Acessórios - 20 L", 179.0), ("Garrafa Térmica", "Casa - 750 ml", 89.9),
    ("Luminária LED", "Decoração", 129.0), ("Teclado Mecânico", "Informática", 349.0),
    ("Cafeteira Italiana", "Cozinha", 149.0), ("Óculos de Sol", "Moda - proteção UV", 199.0)])
GROCERIES = samples("groc", [
    ("Arroz 5 kg", "Mercearia", 27.9), ("Feijão 1 kg", "Mercearia", 8.5), ("Leite 1 L", "Laticínios", 5.2),
    ("Banana prata (kg)", "Hortifrúti", 6.9), ("Café 500 g", "Mercearia", 18.9), ("Pão de forma", "Padaria", 9.5),
    ("Ovos (dúzia)", "Frescos", 12.0), ("Detergente", "Limpeza", 2.9)])
PROFESSIONALS = samples("pro", [
    ("Ana Souza", "Eletricista - 4,9 estrelas", 120.0), ("Carlos Lima", "Encanador - 4,8 estrelas", 100.0),
    ("Juliana Reis", "Diarista - 5,0 estrelas", 180.0), ("Pedro Alves", "Pintor - 4,7 estrelas", 250.0),
    ("Marina Costa", "Montadora de móveis - 4,9 estrelas", 90.0)])
COURSES = samples("course", [
    ("Kotlin do zero", "12 aulas - Iniciante", 0.0), ("Jetpack Compose", "18 aulas - Intermediário", 49.9),
    ("Inglês para viagem", "20 aulas", 39.9), ("Excel avançado", "15 aulas", 59.9),
    ("Fotografia com celular", "10 aulas", 29.9), ("Finanças pessoais", "8 aulas", 0.0)])
EVENTS = samples("event", [
    ("Festival de Música", "Sáb, 20h - Parque Central", 120.0), ("Feira de Tecnologia", "Dom, 10h - Centro de Convenções", 60.0),
    ("Peça: O Auto da Compadecida", "Sex, 21h - Teatro Municipal", 80.0), ("Corrida 10K", "Dom, 7h - Orla", 95.0),
    ("Stand-up Comedy", "Qui, 22h - Bar do Riso", 45.0)])
HOTELS = samples("hotel", [
    ("Hotel Mar Azul", "Praia - 4 estrelas", 420.0), ("Pousada da Serra", "Montanha - café incluso", 280.0),
    ("Hostel Centro", "Centro - quartos compartilhados", 90.0), ("Resort Sol Nascente", "All inclusive", 980.0),
    ("Hotel Executivo", "Próximo ao aeroporto", 350.0)])
PLACES = samples("place", [
    ("Museu de Arte", "Cultura - aberto até 18h"), ("Parque Ibirapuera", "Natureza - gratuito"),
    ("Mercado Municipal", "Gastronomia"), ("Mirante do Centro", "Vista panorâmica"),
    ("Catedral da Sé", "Histórico"), ("Rua das Artes", "Compras e cafés")])
PROPERTIES = samples("house", [
    ("Apartamento 2 quartos", "Centro - 68 m²", 2500.0), ("Casa com quintal", "Jardim América - 140 m²", 4200.0),
    ("Studio mobiliado", "Vila Nova - 32 m²", 1800.0), ("Cobertura duplex", "Beira-mar - 210 m²", 9800.0),
    ("Sala comercial", "Av. Paulista - 45 m²", 3100.0)])
CARS = samples("car", [
    ("Hatch econômico", "Manual - 5 lugares", 129.0), ("Sedan conforto", "Automático - ar-condicionado", 189.0),
    ("SUV familiar", "7 lugares", 289.0), ("Picape", "4x4 - cabine dupla", 320.0), ("Elétrico compacto", "Autonomia 300 km", 240.0)])
WORKOUTS = samples("workout", [
    ("Treino A - Peito e tríceps", "45 min - 6 exercícios"), ("Treino B - Costas e bíceps", "50 min - 7 exercícios"),
    ("Treino C - Pernas", "60 min - 8 exercícios"), ("HIIT 20 minutos", "Cardio intenso"),
    ("Alongamento matinal", "15 min"), ("Core e abdômen", "25 min")])
MEDITATIONS = samples("med", [
    ("Respiração 4-7-8", "5 min - ansiedade"), ("Escaneamento corporal", "12 min - relaxamento"),
    ("Foco no trabalho", "8 min - concentração"), ("Antes de dormir", "15 min - sono"), ("Gratidão", "6 min - bem-estar")])
SONGS = samples("song", [
    ("Noite Clara", "Banda Aurora - 3:42"), ("Caminhos", "Lia Mendes - 4:10"), ("Mar Aberto", "Trio Atlântico - 3:15"),
    ("Cidade Viva", "MC Horizonte - 2:58"), ("Saudade Leve", "Duo Brisa - 3:30")])
VIDEOS = samples("video", [
    ("Big Buck Bunny", "Animação - 10 min"), ("Tears of Steel", "Ficção científica - 12 min"),
    ("Sintel", "Aventura - 15 min"), ("Elephants Dream", "Animação - 11 min")])
QUESTIONS = samples("quiz", [
    ("Qual é a capital da Austrália?", "Geografia"), ("Quem pintou a Mona Lisa?", "Arte"),
    ("Quantos planetas há no Sistema Solar?", "Ciências"), ("Em que ano o homem pisou na Lua?", "História")])
CONTACTS = samples("contact", [
    ("Ana Beatriz", "(11) 98888-1111"), ("Bruno Carvalho", "(21) 97777-2222"), ("Camila Duarte", "(31) 96666-3333"),
    ("Diego Fernandes", "(41) 95555-4444"), ("Elisa Gomes", "(51) 94444-5555")])
NEWS = samples("news", [
    ("Nova linha de metrô é inaugurada", "Cidades - há 2 h"), ("Seleção vence amistoso", "Esportes - há 3 h"),
    ("Bolsa fecha em alta", "Economia - há 5 h"), ("Festival de cinema anuncia filmes", "Cultura - há 1 dia")])
PETS = samples("pet", [
    ("Ração Premium 10 kg", "Cães adultos", 189.9), ("Arranhador", "Gatos", 99.0), ("Banho e tosa", "Serviço", 70.0),
    ("Coleira com GPS", "Acessórios", 249.0), ("Petisco natural", "Snacks", 19.9)])
MEDS = samples("med2", [
    ("Dipirona 500 mg", "Analgésico - 10 comprimidos", 8.9), ("Vitamina C", "Suplemento - 30 cápsulas", 24.9),
    ("Protetor solar FPS 50", "Dermocosmético", 59.9), ("Álcool gel 70%", "Higiene", 9.9),
    ("Termômetro digital", "Equipamento", 29.9)])
COFFEE = samples("coffee", [
    ("Espresso", "Curto e intenso", 6.0), ("Cappuccino", "Com canela", 12.0), ("Latte gelado", "Leite e baunilha", 14.0),
    ("Pão de queijo", "Porção com 6", 10.0), ("Bolo de cenoura", "Fatia", 9.0)])
CLOTHES = samples("cloth", [
    ("Vestido midi", "Feminino - viscose", 159.9), ("Calça jeans slim", "Masculino", 179.9), ("Jaqueta corta-vento", "Unissex", 229.0),
    ("Camisa social", "Masculino - algodão", 139.0), ("Saia plissada", "Feminino", 119.0), ("Moletom canguru", "Unissex", 189.0)])
ELECTRONICS = samples("elec", [
    ("Smartphone X12", "128 GB - 5G", 2499.0), ("Notebook Air 14", "16 GB RAM - SSD 512 GB", 5299.0),
    ("Smart TV 50''", "4K - HDR", 2899.0), ("Caixa de som portátil", "À prova d'água", 399.0), ("Tablet 10''", "64 GB", 1499.0)])
DEALS = samples("deal", [
    ("50% em pizzas", "Válido até domingo"), ("Frete grátis", "Compras acima de R$ 99"),
    ("Leve 3 pague 2", "Linha de cosméticos"), ("Cashback de 10%", "Pagamentos via app")])
SERVICES = samples("service", [
    ("Corte masculino", "30 min", 45.0), ("Corte e escova", "60 min", 90.0), ("Manicure", "40 min", 35.0),
    ("Barba completa", "30 min", 35.0), ("Coloração", "90 min", 160.0)])
PODCASTS = samples("podcast", [
    ("Tecnologia em Foco", "Episódio 120 - IA no dia a dia"), ("Histórias do Brasil", "Episódio 45 - Império"),
    ("Mente Saudável", "Episódio 32 - Rotina e sono"), ("Negócios 360", "Episódio 87 - Startups")])
STATIONS = samples("radio", [
    ("Rádio Jazz Café", "Jazz - 24h"), ("Pop Hits", "Pop internacional"), ("MPB FM", "Música brasileira"),
    ("Notícias 24h", "Jornalismo"), ("Lo-fi Study", "Para estudar")])
LESSONS = samples("lesson", [
    ("Saudações", "Lição 1 - Básico"), ("Números", "Lição 2 - Básico"), ("No restaurante", "Lição 3 - Situações"),
    ("Pedindo direções", "Lição 4 - Viagem"), ("Verbos no passado", "Lição 5 - Gramática")])
FLASHCARDS = samples("card", [
    ("Mitocôndria", "Organela responsável pela respiração celular"), ("Fotossíntese", "Conversão de luz em energia química"),
    ("Teorema de Pitágoras", "a² = b² + c²"), ("Revolução Francesa", "1789 - fim do absolutismo")])
TRIPS = samples("trip", [
    ("São Paulo - Rio de Janeiro", "Ida 08:00 - 1 h", 289.0), ("Lisboa - Porto", "Ida 10:30 - 55 min", 79.0),
    ("Recife - Salvador", "Ida 14:15 - 1 h 20", 349.0), ("Brasília - Manaus", "Ida 06:40 - 3 h", 699.0)])
LINES = samples("line", [
    ("Linha 1 - Azul", "Tucuruvi - Jabaquara - a cada 4 min"), ("Linha 2 - Verde", "Vila Madalena - Vila Prudente"),
    ("Ônibus 875A", "Terminal Lapa - Centro - a cada 12 min"), ("Linha 4 - Amarela", "Luz - Vila Sônia")])
PARKING = samples("park", [
    ("Estacionamento Centro", "120 vagas - R$ 12/h", 12.0), ("Shopping Norte", "800 vagas - R$ 10/h", 10.0),
    ("Garagem Avenida", "60 vagas - R$ 15/h", 15.0)])
CHURCH = samples("club", [
    ("Assembleia geral", "Sábado, 15h"), ("Campanha do agasalho", "Doações até dia 30"),
    ("Torneio de futsal", "Inscrições abertas"), ("Reunião da diretoria", "Quinta, 19h")])
STOCK = samples("stock", [
    ("Parafuso 6 mm", "Estoque: 1.200 un", 0.15), ("Cabo HDMI 2 m", "Estoque: 48 un", 24.9),
    ("Papel A4 (resma)", "Estoque: 35 un", 29.9), ("Toner preto", "Estoque: 6 un", 189.0)])
LEADS = samples("lead", [
    ("Construtora Alfa", "Proposta enviada - R$ 45 mil"), ("Mercado Bom Preço", "Negociação - R$ 12 mil"),
    ("Clínica Vida", "Primeiro contato"), ("Escola Futuro", "Fechado - R$ 30 mil")])
ORDERS = samples("order", [
    ("OS 1024 - Notebook", "Troca de tela - em andamento"), ("OS 1025 - Impressora", "Aguardando peça"),
    ("OS 1026 - Celular", "Concluída"), ("OS 1027 - Ar-condicionado", "Agendada")])
DEFAULT = samples("item", [(f"Item {i}", f"Descrição do item {i}") for i in range(1, 9)])


# ================================================================== MODELOS
# ---------- Delivery e alimentacao
T("Delivery de comida", "Delivery e alimentação",
  "Restaurantes, cardápio, carrinho, checkout e acompanhamento do pedido.",
  login_screens("Inicio") + [
      list_screen("Inicio", "Restaurantes", "sample:restaurants", detail="Cardapio", icon="home",
                  header=home_header("O que vamos pedir hoje?", "Entrega rápida na sua região",
                                     ("Frete grátis", "Em pedidos acima de R$ 50")),
                  chips="Todos;Pizza;Japonesa;Lanches;Saudável"),
      S("Cardapio", "Cardápio", [C("item_detail"), C("title", text="Pratos", size="small"),
                                 C("list", source="sample:dishes", item_action="add_cart", show_price=True),
                                 C("text", text="Toque em um prato para adicionar ao carrinho.", style="caption")]),
      cart_screen("Pedido"),
      S("Pedido", "Acompanhar pedido", [C("title", text="Pedido confirmado!"), C("progress", style="linear", bind_loading=False),
                                        C("text", text="Seu pedido está sendo preparado e logo sai para entrega."),
                                        C("map_view", title="Restaurante"),
                                        C("button", text="Falar com o entregador", action="call:11999999999", style="outlined")],
        icon="place"),
      profile_screen("Login"),
  ], ["cart", "local_auth", "notifications", "favorites", "formatters", "order_tracking", "maps"],
  sample_sets={"restaurants": RESTAURANTS, "dishes": DISHES}, color="#E53935", start="Login", glyph="FOOD")

T("Delivery de mercado", "Delivery e alimentação", "Supermercado online com categorias, busca, carrinho e agendamento.", [
    list_screen("Inicio", "Mercado", "sample:groceries", grid=True, price=True, icon="home",
                header=home_header("Supermercado", "Receba em casa hoje"),
                chips="Todos;Hortifrúti;Mercearia;Laticínios;Limpeza"),
    detail_screen(buttons=[("Adicionar ao carrinho", "add_cart"), ("Favoritar", "favorite", "outlined")], price=True,
                  extra=[C("stepper", label="Quantidade", key="quantity")]),
    cart_screen("Entrega"),
    form_screen("Entrega", "Agendar entrega", [("Endereço", "address", "text", "required"), ("CEP", "cep", "number", "cep"),
                                              ("Data", "date", "date"), ("Período", "period", "dropdown=Manhã;Tarde;Noite")],
                after="Confirmado", button="Confirmar entrega"),
    done_screen("Confirmado", "Entrega agendada!", "Você receberá uma notificação quando o pedido sair.", "Inicio"),
    list_screen("Favoritos", "Favoritos", "favorites", icon="favorite", search=False, price=True),
], ["cart", "favorites", "validators", "notifications"], sample_sets={"groceries": GROCERIES}, color="#43A047", glyph="MKT")

T("Farmácia delivery", "Delivery e alimentação", "Medicamentos, receitas por foto, carrinho e lembrete de remédios.", [
    list_screen("Inicio", "Farmácia", "sample:meds", price=True, icon="home",
                header=home_header("Farmácia 24h", "Entrega em até 1 hora")),
    detail_screen(buttons=[("Adicionar ao carrinho", "add_cart")], price=True),
    S("Receita", "Enviar receita", [C("text", text="Tire uma foto da receita médica para o farmacêutico validar."),
                                    C("image", source="photo", height=220), C("button", text="Tirar foto", action="take_photo"),
                                    C("button", text="Escolher da galeria", action="pick_image", style="outlined")],
      nav=True, icon="edit"),
    cart_screen("Finalizado"),
    done_screen("Finalizado", "Pedido enviado!", "O farmacêutico vai revisar e confirmar seu pedido.", "Inicio"),
], ["cart", "camera_capture", "image_picker", "reminders"], sample_sets={"meds": MEDS}, color="#00897B", glyph="RX")

T("Cardápio digital", "Delivery e alimentação", "Cardápio para restaurante com QR Code na mesa e chamada do garçom.", [
    list_screen("Cardapio", "Cardápio", "sample:dishes", price=True, icon="list",
                header=home_header("Bem-vindo ao Restaurante", "Mesa 12"), chips="Entradas;Pratos;Bebidas;Sobremesas"),
    detail_screen(buttons=[("Adicionar ao pedido", "add_cart")], price=True),
    cart_screen("Enviado", name="Pedido"),
    done_screen("Enviado", "Pedido enviado à cozinha", "Em breve seu prato chega à mesa.", "Cardapio"),
    S("Mesa", "Mesa", [C("title", text="QR Code da mesa"), C("qr_code", text="https://restaurante.exemplo/mesa/12"),
                       C("button", text="Chamar garçom", action="notify:Garçom chamado para a mesa 12"),
                       C("button", text="Pedir a conta", action="toast:A conta está a caminho", style="outlined")],
      nav=True, icon="star"),
], ["cart", "qr_generator", "notifications"], sample_sets={"dishes": DISHES}, color="#6D4C41", glyph="MENU")

T("Reserva de mesas", "Delivery e alimentação", "Reserva em restaurantes com data, horário e número de pessoas.", [
    list_screen("Restaurantes", "Restaurantes", "sample:restaurants", detail="Reservar", icon="home"),
    S("Reservar", "Reservar mesa", [C("item_detail"), C("date_picker", label="Data", key="date"),
                                    C("dropdown", label="Horário", key="time", options="19:00;19:30;20:00;20:30;21:00"),
                                    C("stepper", label="Pessoas", key="people", max=20),
                                    C("text_field", label="Observações", key="notes", input="multiline"),
                                    C("button", text="Confirmar reserva", action="submit:Reservas")], form="Reservation"),
    list_screen("Reservas", "Minhas reservas", "entity:Reservation", detail=None, icon="date", search=False),
], ["notifications", "calendar_event"], [E("Reservation", "date:String, time:String, people:Int, notes:String")],
  sample_sets={"restaurants": RESTAURANTS}, color="#8E24AA", glyph="RSV")

T("Receitas culinárias", "Delivery e alimentação", "Receitas reais da API TheMealDB com favoritos.", [
    list_screen("Receitas", "Receitas", "api:MealDb.searchMeals", grid=True, icon="home"),
    detail_screen(buttons=[("Favoritar", "favorite"), ("Compartilhar", "share_item", "outlined")]),
    list_screen("Favoritos", "Favoritos", "favorites", icon="favorite", search=False),
], ["favorites", "network", "http_cache"], apis=[AP.themealdb()], color="#F4511E", glyph="CHEF")

T("Cafeteria com pedidos", "Delivery e alimentação", "Cardápio de cafeteria, pedido para retirada e programa de pontos.", [
    list_screen("Menu", "Menu", "sample:coffee", price=True, icon="home", grid=True,
                header=home_header("Bom dia!", "Peça e retire sem fila")),
    detail_screen(buttons=[("Adicionar", "add_cart")], price=True,
                  extra=[C("radio_group", label="Tamanho", key="size", options="Pequeno;Médio;Grande")]),
    cart_screen("Retirada"),
    done_screen("Retirada", "Pedido recebido", "Avisaremos quando estiver pronto para retirada.", "Menu"),
    S("Pontos", "Fidelidade", [C("stat_card", label="Seus pontos", value="320"),
                               C("text", text="A cada R$ 1 gasto, você ganha 1 ponto. 500 pontos = 1 café grátis."),
                               C("qr_code", text="CLIENTE-000123")], nav=True, icon="star"),
], ["cart", "loyalty", "qr_generator", "notifications"], sample_sets={"coffee": COFFEE}, color="#795548", glyph="CAFE")

T("Delivery de água e gás", "Delivery e alimentação", "Pedido rápido de botijão e galão com pagamento na entrega.", [
    S("Inicio", "Pedir", [C("title", text="Água e gás"), C("text", text="Entrega em até 40 minutos."),
                          C("radio_group", label="Produto", key="product", options="Botijão P13;Galão 20 L;Botijão + Galão"),
                          C("stepper", label="Quantidade", key="quantity"),
                          C("text_field", label="Endereço", key="address", validation="required"),
                          C("dropdown", label="Pagamento", key="payment", options="Dinheiro;Pix;Cartão na entrega"),
                          C("button", text="Pedir agora", action="submit:Pedidos")], nav=True, form="GasOrder"),
    list_screen("Pedidos", "Meus pedidos", "entity:GasOrder", detail=None, icon="list", search=False),
], ["validators", "notifications"], [E("GasOrder", "product:String, quantity:Int, address:String, payment:String")],
  color="#1565C0", glyph="GAS")

T("Pet shop", "Delivery e alimentação", "Produtos e serviços para pets com agendamento de banho e tosa.", [
    list_screen("Loja", "Pet shop", "sample:pets", grid=True, price=True, icon="home"),
    detail_screen(buttons=[("Adicionar ao carrinho", "add_cart")], price=True),
    cart_screen("Concluido"),
    form_screen("Agendar", "Banho e tosa", [("Nome do pet", "petName", "text", "required"),
                                            ("Porte", "size", "dropdown=Pequeno;Médio;Grande"), ("Data", "date", "date")],
                entity="Grooming", after="Loja", button="Agendar", nav=True, icon="date"),
    done_screen("Concluido", "Pedido feito!", "Obrigado por comprar conosco.", "Loja"),
], ["cart", "notifications"], [E("Grooming", "petName:String, size:String, date:String")],
  sample_sets={"pets": PETS}, color="#FB8C00", glyph="PET")

T("Food truck localizador", "Delivery e alimentação", "Mapa e lista de food trucks próximos.", [
    list_screen("Trucks", "Food trucks", "sample:restaurants", icon="home"),
    detail_screen(buttons=[("Como chegar", "open_url:https://maps.google.com/?q=-23.55,-46.63")],
                  extra=[C("map_view", title="Food truck")]),
    S("Mapa", "Mapa", [C("map_view", height=480), C("button", text="Minha localização", action="location")], nav=True, icon="place"),
], ["maps", "location"], sample_sets={"restaurants": RESTAURANTS}, color="#FDD835", glyph="TRK")

# ---------- Comercio
T("Loja online", "Comércio", "Loja com produtos reais da FakeStore API, carrinho e checkout.", [
    list_screen("Loja", "Loja", "api:FakeStore.getProducts", grid=True, price=True, icon="home",
                header=[C("banner", title="Semana de ofertas", subtitle="Descontos em toda a loja")]),
    detail_screen(buttons=[("Adicionar ao carrinho", "add_cart"), ("Favoritar", "favorite", "outlined"),
                           ("Compartilhar", "share_item", "text")], price=True),
    cart_screen("Checkout"),
    form_screen("Checkout", "Pagamento", [("Nome no cartão", "cardName", "text", "required"),
                                          ("Número do cartão", "cardNumber", "number", "required"),
                                          ("Cupom", "coupon")], after="Obrigado", button="Pagar"),
    done_screen("Obrigado", "Compra realizada!", "Você receberá o código de rastreio por e-mail.", "Loja"),
    list_screen("Favoritos", "Favoritos", "favorites", icon="favorite", search=False, price=True),
], ["cart", "favorites", "checkout", "payments", "network", "formatters"], apis=[AP.fakestore()],
  color="#3949AB", glyph="SHOP")

T("Marketplace", "Comércio", "Marketplace com vendedores, anúncios, chat e avaliações.", login_screens("Explorar") + [
    list_screen("Explorar", "Explorar", "api:DummyJson.getProducts", grid=True, price=True, icon="home"),
    detail_screen(buttons=[("Comprar", "add_cart"), ("Conversar com vendedor", "navigate:Chat", "outlined")], price=True,
                  extra=[C("rating", label="Avalie o vendedor", key="rating")]),
    cart_screen("Obrigado"),
    chat_screen(),
    done_screen("Obrigado", "Pedido realizado!", "O vendedor foi notificado.", "Explorar"),
    profile_screen("Login"),
], ["cart", "chat", "local_auth", "network"], apis=[AP.dummyjson(("products",))], color="#00ACC1", start="Login", glyph="MKP")

T("Loja de roupas", "Comércio", "Moda com filtros, tamanhos, lista de desejos e carrinho.", [
    list_screen("Vitrine", "Vitrine", "sample:clothes", grid=True, price=True, icon="home",
                chips="Feminino;Masculino;Unissex;Promoções"),
    detail_screen(buttons=[("Adicionar à sacola", "add_cart"), ("Lista de desejos", "favorite", "outlined")], price=True,
                  extra=[C("chips", key="size", options="PP;P;M;G;GG")]),
    cart_screen("Obrigado", name="Sacola"),
    list_screen("Desejos", "Desejos", "favorites", icon="favorite", search=False, price=True),
    done_screen("Obrigado", "Pedido confirmado", "Obrigado pela compra!", "Vitrine"),
], ["cart", "favorites", "checkout"], sample_sets={"clothes": CLOTHES}, color="#D81B60", glyph="MODA")

T("Loja de eletrônicos", "Comércio", "Eletrônicos com busca na API DummyJSON e parcelamento.", [
    list_screen("Produtos", "Produtos", "api:DummyJson.getProducts", price=True, icon="home"),
    detail_screen(buttons=[("Comprar", "add_cart"), ("Simular parcelamento", "toast:Em até 10x sem juros", "outlined")], price=True),
    cart_screen("Obrigado"),
    done_screen("Obrigado", "Compra realizada", "Acompanhe a entrega pelo app.", "Produtos"),
], ["cart", "network", "formatters"], apis=[AP.dummyjson(("products",))], color="#263238", glyph="TECH")

T("Catálogo offline", "Comércio", "Catálogo de produtos salvo no aparelho, com cadastro e edição.", [
    list_screen("Catalogo", "Catálogo", "entity:Product", price=True, icon="home", fab="navigate:NovoProduto"),
    detail_screen(price=True),
    form_screen("NovoProduto", "Novo produto", [("Nome", "name", "text", "required"), ("Preço", "price", "number", "number"),
                                                ("Categoria", "category"), ("URL da imagem", "imageUrl")],
                entity="Product", after="Catalogo"),
], ["csv_export"], [E("Product", "name:String, price:Double, category:String, imageUrl:String")], color="#5E35B1", glyph="CAT")

T("Leilão online", "Comércio", "Leilões com lances, contagem regressiva e notificações.", [
    list_screen("Leiloes", "Leilões", "sample:products", price=True, icon="home"),
    detail_screen(price=True, extra=[C("timer", mode="countdown", seconds=3600),
                                     C("text_field", label="Seu lance", key="bid", input="number", validation="number")],
                  buttons=[("Dar lance", "toast:Lance registrado!")]),
    list_screen("Acompanhando", "Acompanhando", "favorites", icon="favorite", search=False, price=True),
], ["timer", "favorites", "notifications"], sample_sets={"products": PRODUCTS}, color="#C62828", glyph="BID")

T("Classificados", "Comércio", "Anúncios de usados com fotos, categorias e contato direto.", [
    list_screen("Anuncios", "Anúncios", "entity:Ad", price=True, icon="home", fab="navigate:Anunciar",
                chips="Todos;Eletrônicos;Móveis;Veículos;Roupas"),
    detail_screen(price=True, buttons=[("Ligar", "call:11999999999"), ("WhatsApp", "open_url:https://wa.me/5511999999999", "outlined")]),
    form_screen("Anunciar", "Novo anúncio", [("Título", "title", "text", "required"), ("Preço", "price", "number", "number"),
                                             ("Descrição", "description", "multiline"), ("Telefone", "phone", "phone", "phone")],
                entity="Ad", after="Anuncios", button="Publicar",
                extra=[C("image", source="photo", height=160), C("button", text="Adicionar foto", action="take_photo", style="outlined")]),
], ["camera_capture", "validators"], [E("Ad", "title:String, price:Double, description:String, phone:String")],
  color="#F9A825", glyph="ADS")

T("Cupons e ofertas", "Comércio", "Ofertas próximas, cupons com QR Code e notificações.", [
    list_screen("Ofertas", "Ofertas", "sample:deals", icon="home"),
    detail_screen(extra=[C("qr_code", text="CUPOM-BEMVINDO10")], buttons=[("Salvar cupom", "favorite"),
                                                                          ("Compartilhar", "share_item", "outlined")]),
    list_screen("Salvos", "Meus cupons", "favorites", icon="star", search=False),
], ["favorites", "qr_generator", "notifications"], sample_sets={"deals": DEALS}, color="#EF6C00", glyph="CUP")

T("Lista de desejos", "Comércio", "Organize produtos que deseja comprar com preço e prioridade.", [
    list_screen("Desejos", "Desejos", "entity:Wish", price=True, icon="home", fab="navigate:NovoDesejo", detail=None),
    form_screen("NovoDesejo", "Novo desejo", [("Produto", "name", "text", "required"), ("Preço", "price", "number"),
                                              ("Link", "link"), ("Prioridade", "priority", "dropdown=Alta;Média;Baixa")],
                entity="Wish", after="Desejos"),
], [], [E("Wish", "name:String, price:Double, link:String, priority:String")], color="#AD1457", glyph="WISH")

T("Comparador de preços", "Comércio", "Compare preços de produtos com leitura de código de barras.", [
    list_screen("Produtos", "Produtos", "api:DummyJson.searchProducts", price=True, icon="home"),
    detail_screen(price=True, buttons=[("Ler código de barras", "scan_code")]),
    S("Scanner", "Escanear", [C("text", text="Aponte a câmera para o código de barras do produto."),
                              C("button", text="Escanear", action="scan_code")], nav=True, icon="search"),
], ["barcode_scanner", "network"], apis=[AP.dummyjson(("products",))], color="#00838F", glyph="CMP")

# ---------- Financas
T("Clima", "Finanças e informação", "Previsão do tempo real com a API Open-Meteo.", [
    S("Agora", "Clima agora", [C("title", text="Previsão do tempo"), C("progress", style="linear"),
                               C("list", source="api:OpenMeteo.getForecast", show_image=False),
                               C("button", text="Atualizar", action="refresh"),
                               C("button", text="Minha localização", action="location", style="outlined")],
      nav=True, icon="home"),
    about_screen("Clima", "Dados fornecidos pela API gratuita Open-Meteo."),
], ["network", "location", "http_cache"], apis=[AP.open_meteo()], color="#0288D1", glyph="SKY")

T("Notícias", "Finanças e informação", "Notícias reais da Spaceflight News API com leitura e compartilhamento.", [
    list_screen("Noticias", "Notícias", "api:SpaceNews.getArticles", icon="home"),
    detail_screen(buttons=[("Compartilhar", "share_item"), ("Salvar", "favorite", "outlined")]),
    list_screen("Salvas", "Salvas", "favorites", icon="favorite", search=False),
], ["network", "favorites", "pull_to_refresh", "http_cache"], apis=[AP.spaceflight_news()], color="#37474F", glyph="NEWS")

T("Conversor de moedas", "Finanças e informação", "Cotações reais do dólar para dezenas de moedas.", [
    S("Cotacoes", "Cotações", [C("title", text="1 USD vale:"), C("search_bar", hint="Buscar moeda (ex.: BRL, EUR)"),
                               C("list", source="api:ExchangeRates.getRates", show_image=False)], nav=True, icon="home"),
    S("Calculadora", "Converter", [C("text_field", label="Valor", key="amount", input="number"),
                                   C("dropdown", label="De", key="from", options="USD;BRL;EUR;GBP"),
                                   C("dropdown", label="Para", key="to", options="BRL;USD;EUR;GBP"),
                                   C("button", text="Converter", action="toast:Use as cotações da aba anterior")],
      nav=True, icon="build"),
], ["network", "formatters"], apis=[AP.exchange_rates()], color="#2E7D32", glyph="FX")

T("Criptomoedas", "Finanças e informação", "Cotações de criptomoedas em tempo real (CoinGecko).", [
    list_screen("Mercado", "Mercado", "api:CoinGecko.getMarkets", price=True, icon="home"),
    detail_screen(price=True, buttons=[("Acompanhar", "favorite")], extra=[C("chart", style="line", values="3,5,4,6,8,7,9")]),
    list_screen("Carteira", "Acompanhando", "favorites", icon="star", search=False, price=True),
], ["network", "favorites", "charts", "pull_to_refresh"], apis=[AP.coingecko()], color="#F57F17", glyph="BTC")

T("Controle de gastos", "Finanças e informação", "Registre despesas, veja totais por categoria e gráfico.", [
    dashboard_screen("Resumo", "Resumo do mês", [("Gasto no mês", "R$ 2.340"), ("Orçamento restante", "R$ 660")],
                     chart="pie", values="35,20,15,30"),
    list_screen("Despesas", "Despesas", "entity:Expense", price=True, icon="list", fab="navigate:NovaDespesa", detail=None),
    form_screen("NovaDespesa", "Nova despesa", [("Descrição", "title", "text", "required"), ("Valor", "amount", "number", "number"),
                                                ("Categoria", "category", "dropdown=Alimentação;Transporte;Moradia;Lazer;Saúde"),
                                                ("Data", "date", "date")], entity="Expense", after="Despesas"),
], ["charts", "csv_export", "formatters"], [E("Expense", "title:String, amount:Double, category:String, date:String")],
  color="#00695C", glyph="$$")

T("Orçamento pessoal", "Finanças e informação", "Receitas, despesas e metas mensais com indicadores.", [
    dashboard_screen("Painel", "Painel financeiro", [("Saldo", "R$ 1.250"), ("Receitas", "R$ 5.000"), ("Despesas", "R$ 3.750")]),
    list_screen("Lancamentos", "Lançamentos", "entity:Entry", price=True, icon="list", fab="navigate:NovoLancamento", detail=None),
    form_screen("NovoLancamento", "Novo lançamento", [("Descrição", "title", "text", "required"), ("Valor", "amount", "number"),
                                                      ("Tipo", "kind", "dropdown=Receita;Despesa"), ("Data", "date", "date")],
                entity="Entry", after="Lancamentos"),
    S("Metas", "Metas", [C("card", title="Reserva de emergência", body="R$ 3.200 de R$ 10.000"),
                         C("progress", style="linear", bind_loading=False),
                         C("card", title="Viagem de férias", body="R$ 1.100 de R$ 6.000")], nav=True, icon="star"),
], ["charts"], [E("Entry", "title:String, amount:Double, kind:String, date:String")], color="#1B5E20", glyph="BUD")

T("Calculadora de empréstimo", "Finanças e informação", "Simulação de financiamento Price e SAC.", [
    S("Simular", "Simular", [C("title", text="Simulador de financiamento"),
                             C("text_field", label="Valor (R$)", key="principal", input="number", validation="number"),
                             C("text_field", label="Juros ao mês (%)", key="rate", input="number", validation="number"),
                             C("slider", label="Parcelas", key="months", min=1.0, max=120.0),
                             C("radio_group", label="Sistema", key="system", options="Price;SAC"),
                             C("button", text="Calcular", action="submit:")], nav=True, icon="build"),
    about_screen("Simulador", "Cálculos baseados nas fórmulas da Tabela Price e do SAC (algoritmos inclusos)."),
], ["validators", "formatters"], color="#283593", glyph="LOAN")

T("Carteira digital", "Finanças e informação", "Saldo, transferências por QR Code e extrato.", login_screens("Carteira") + [
    dashboard_screen("Carteira", "Minha carteira", [("Saldo disponível", "R$ 842,30")], chart="line", values="3,4,3,5,6,5,7",
                     extra=[C("button", text="Pagar com QR Code", action="scan_code"),
                            C("button", text="Receber", action="navigate:Receber", style="outlined")]),
    S("Receber", "Receber", [C("qr_code", text="PIX-CHAVE-ALEATORIA-0001"), C("text", text="Mostre este código para receber.")]),
    list_screen("Extrato", "Extrato", "sample:deals", icon="list", detail=None),
    profile_screen("Login"),
], ["local_auth", "barcode_scanner", "qr_generator", "biometric", "secure_screen", "charts"], color="#4527A0", start="Login", glyph="PAY")

T("Investimentos", "Finanças e informação", "Acompanhe ativos, rentabilidade e alocação da carteira.", [
    dashboard_screen("Carteira", "Patrimônio", [("Total investido", "R$ 48.200"), ("Rentabilidade no ano", "+8,4%")],
                     chart="pie", values="40,25,20,15"),
    list_screen("Ativos", "Ativos", "entity:Asset", price=True, icon="list", fab="navigate:NovoAtivo", detail=None),
    form_screen("NovoAtivo", "Novo ativo", [("Nome", "name", "text", "required"), ("Valor", "value", "number"),
                                            ("Tipo", "kind", "dropdown=Renda fixa;Ações;FII;Cripto")], entity="Asset", after="Ativos"),
], ["charts", "formatters"], [E("Asset", "name:String, value:Double, kind:String")], color="#0D47A1", glyph="INV")

T("Divisão de contas", "Finanças e informação", "Divida a conta do restaurante com gorjeta.", [
    S("Dividir", "Dividir conta", [C("text_field", label="Valor total", key="total", input="number", validation="number"),
                                   C("stepper", label="Pessoas", key="people", max=50),
                                   C("slider", label="Gorjeta (%)", key="tip", min=0.0, max=20.0),
                                   C("button", text="Calcular", action="submit:"),
                                   C("button", text="Compartilhar resultado", action="share:Divisão feita pelo app", style="outlined")],
      nav=True, icon="build"),
    list_screen("Historico", "Histórico", "entity:Split", icon="list", search=False, detail=None),
], [], [E("Split", "total:Double, people:Int, tip:Double")], color="#6A1B9A", glyph="SPLIT")

# ---------- Saude e fitness
T("Treinos fitness", "Saúde e bem-estar", "Fichas de treino, cronômetro e histórico.", [
    list_screen("Treinos", "Treinos", "sample:workouts", icon="home"),
    detail_screen(extra=[C("timer", mode="stopwatch")], buttons=[("Concluir treino", "submit:Historico")]),
    list_screen("Historico", "Histórico", "entity:Session", icon="date", search=False, detail=None),
    dashboard_screen("Progresso", "Progresso", [("Treinos no mês", "14"), ("Minutos", "620")], icon="star"),
], ["timer", "charts", "keep_screen_on"], [E("Session", "workout:String, minutes:Int, date:String")],
  sample_sets={"workouts": WORKOUTS}, color="#D84315", glyph="GYM")

T("Contador de passos", "Saúde e bem-estar", "Passos do dia, distância e calorias com o sensor do aparelho.", [
    dashboard_screen("Hoje", "Hoje", [("Passos", "6.240"), ("Distância", "4,7 km"), ("Calorias", "218 kcal")]),
    S("Meta", "Meta", [C("slider", label="Meta diária de passos", key="goal", min=1000.0, max=20000.0),
                       C("button", text="Salvar meta", action="toast:Meta salva")], nav=True, icon="star"),
], ["step_counter", "charts", "notifications"], color="#2E7D32", glyph="STEP")

T("Controle de água", "Saúde e bem-estar", "Registre copos de água e receba lembretes.", [
    S("Hoje", "Hidratação", [C("stat_card", label="Consumido hoje", value="1,2 L de 2,5 L"),
                             C("progress", style="linear", bind_loading=False),
                             C("button", text="+ 250 ml", action="submit:"), C("button", text="Lembrar em 1 hora",
                                                                                   action="notify:Hora de beber água!", style="outlined")],
      nav=True, icon="home", form="Drink"),
    list_screen("Registro", "Registro", "entity:Drink", icon="list", search=False, detail=None),
], ["reminders", "notifications"], [E("Drink", "ml:Int, time:String")], color="#0277BD", glyph="H2O")

T("Dieta e calorias", "Saúde e bem-estar", "Diário alimentar com calorias e macronutrientes.", [
    dashboard_screen("Diario", "Diário de hoje", [("Calorias", "1.430 / 2.000 kcal"), ("Proteínas", "82 g")], chart="pie",
                     values="45,30,25"),
    list_screen("Refeicoes", "Refeições", "entity:Meal", icon="list", fab="navigate:NovaRefeicao", detail=None),
    form_screen("NovaRefeicao", "Nova refeição", [("Alimento", "food", "text", "required"), ("Calorias", "calories", "number"),
                                                  ("Refeição", "meal", "dropdown=Café da manhã;Almoço;Lanche;Jantar")],
                entity="Meal", after="Refeicoes"),
], ["charts", "barcode_scanner"], [E("Meal", "food:String, calories:Int, meal:String")], color="#558B2F", glyph="KCAL")

T("Lembrete de remédios", "Saúde e bem-estar", "Cadastre medicamentos com horário e receba alarmes.", [
    list_screen("Remedios", "Remédios", "entity:Medicine", icon="home", fab="navigate:NovoRemedio", detail=None),
    form_screen("NovoRemedio", "Novo remédio", [("Nome", "name", "text", "required"), ("Dose", "dose"),
                                                ("Horário", "time", "dropdown=06:00;08:00;12:00;18:00;20:00;22:00"),
                                                ("Uso contínuo", "continuous", "switch")], entity="Medicine", after="Remedios"),
    settings_screen(),
], ["alarm", "notifications", "boot_receiver"], [E("Medicine", "name:String, dose:String, time:String, continuous:Boolean")],
  color="#C2185B", glyph="MED")

T("Agendamento de consultas", "Saúde e bem-estar", "Médicos, especialidades e marcação de consultas.", login_screens("Medicos") + [
    list_screen("Medicos", "Médicos", "sample:pros", icon="home", chips="Clínico;Pediatria;Dermatologia;Cardiologia"),
    S("Detalhe", "Agendar", [C("item_detail", show_price=True), C("calendar", key="date"),
                             C("dropdown", label="Horário", key="time", options="08:00;09:00;10:00;14:00;15:00"),
                             C("button", text="Confirmar consulta", action="submit:Consultas")], form="Appointment"),
    list_screen("Consultas", "Consultas", "entity:Appointment", icon="date", search=False, detail=None),
    profile_screen("Login"),
], ["local_auth", "calendar_view", "notifications", "calendar_event"], [E("Appointment", "date:String, time:String")],
  sample_sets={"pros": PROFESSIONALS}, color="#00796B", start="Login", glyph="DOC")

T("Meditação", "Saúde e bem-estar", "Sessões guiadas com cronômetro e áudio.", [
    list_screen("Sessoes", "Sessões", "sample:meditations", icon="home", grid=True),
    detail_screen(extra=[C("timer", mode="countdown", seconds=300), C("lottie", height=160)],
                  buttons=[("Ouvir instrução", "speak:Inspire profundamente e solte o ar devagar")]),
    S("Respirar", "Respirar", [C("lottie", height=240), C("text", text="Inspire por 4 segundos, segure por 7 e solte em 8.",
                                                                       align="center")], nav=True, icon="face"),
], ["timer", "text_to_speech", "lottie", "keep_screen_on"], sample_sets={"meditations": MEDITATIONS}, color="#5C6BC0", glyph="ZEN")

T("Monitor de sono", "Saúde e bem-estar", "Registre horas de sono e qualidade com gráfico semanal.", [
    dashboard_screen("Semana", "Sono na semana", [("Média", "7h12"), ("Melhor noite", "8h30")], chart="line", values="6,7,7.5,6.5,8,8.5,7"),
    form_screen("Registrar", "Registrar noite", [("Horas dormidas", "hours", "number"), ("Qualidade", "quality", "rating"),
                                                 ("Data", "date", "date")], entity="Sleep", after="Semana", nav=True, icon="add"),
], ["charts", "reminders"], [E("Sleep", "hours:Double, quality:Int, date:String")], color="#311B92", glyph="ZZZ")

T("Diário de humor", "Saúde e bem-estar", "Registro diário de humor e anotações.", [
    list_screen("Diario", "Diário", "entity:Mood", icon="home", fab="navigate:NovoRegistro", detail=None),
    form_screen("NovoRegistro", "Como você está?", [("Humor", "mood", "rating"), ("Anotação", "note", "multiline"),
                                                    ("Data", "date", "date")], entity="Mood", after="Diario"),
    dashboard_screen("Graficos", "Tendência", [("Média do mês", "3,8")], chart="line", values="3,4,2,5,4,4,3", icon="star"),
], ["charts", "pin_lock"], [E("Mood", "mood:Int, note:String, date:String")], color="#7B1FA2", glyph="MOOD")

T("IMC e saúde", "Saúde e bem-estar", "Calculadora de IMC, metabolismo basal e hidratação.", [
    S("Calcular", "Calcular", [C("text_field", label="Peso (kg)", key="weight", input="number", validation="number"),
                               C("text_field", label="Altura (m)", key="height", input="number", validation="number"),
                               C("text_field", label="Idade", key="age", input="number"),
                               C("radio_group", label="Sexo", key="sex", options="Feminino;Masculino"),
                               C("button", text="Calcular", action="submit:")], nav=True, icon="build"),
    about_screen("IMC", "Os cálculos usam fórmulas de referência e não substituem avaliação médica."),
], ["validators"], color="#43A047", glyph="IMC")

# ---------- Produtividade
T("Lista de tarefas", "Produtividade", "Tarefas com prioridade, prazo e conclusão.", [
    list_screen("Tarefas", "Tarefas", "entity:Task", icon="home", fab="navigate:NovaTarefa", detail=None,
                chips="Todas;Hoje;Importantes"),
    form_screen("NovaTarefa", "Nova tarefa", [("Título", "title", "text", "required"), ("Descrição", "description", "multiline"),
                                              ("Prioridade", "priority", "dropdown=Alta;Média;Baixa"), ("Prazo", "dueDate", "date"),
                                              ("Concluída", "done", "checkbox")], entity="Task", after="Tarefas"),
    settings_screen(),
], ["reminders", "notifications"], [E("Task", "title:String, description:String, priority:String, dueDate:String, done:Boolean")],
  color="#1E88E5", glyph="TODO")

T("Bloco de notas", "Produtividade", "Notas com busca, cores e compartilhamento.", [
    list_screen("Notas", "Notas", "entity:Note", icon="home", fab="navigate:NovaNota", detail=None),
    form_screen("NovaNota", "Nova nota", [("Título", "title", "text", "required"), ("Conteúdo", "content", "multiline"),
                                          ("Cor", "color", "dropdown=Azul;Amarelo;Verde;Rosa")], entity="Note", after="Notas"),
], ["search_engine", "backup_json"], [E("Note", "title:String, content:String, color:String")], color="#FFB300", glyph="NOTE")

T("Pomodoro", "Produtividade", "Ciclos de foco de 25 minutos com pausas e estatísticas.", [
    S("Foco", "Foco", [C("title", text="Hora de focar", align="center"), C("timer", mode="countdown", seconds=1500),
                       C("chips", key="mode", options="Foco 25;Pausa 5;Pausa 15"),
                       C("button", text="Avisar ao terminar", action="notify:Ciclo concluído!", style="outlined")],
      nav=True, icon="home"),
    dashboard_screen("Estatisticas", "Estatísticas", [("Ciclos hoje", "6"), ("Horas focadas", "2h30")], icon="star"),
], ["timer", "notifications", "keep_screen_on", "vibration"], color="#E53935", glyph="POMO")

T("Agenda", "Produtividade", "Compromissos com calendário, feriados nacionais e lembretes.", [
    S("Calendario", "Calendário", [C("calendar", key="date"), C("list", source="entity:Event", show_image=False,
                                                                 empty_text="Nenhum compromisso"),
                                   C("fab", action="navigate:NovoEvento")], nav=True, icon="date"),
    form_screen("NovoEvento", "Novo compromisso", [("Título", "title", "text", "required"), ("Data", "date", "date"),
                                                   ("Hora", "time"), ("Local", "place")], entity="Event", after="Calendario"),
    list_screen("Feriados", "Feriados", "api:Holidays.getHolidays", icon="star", detail=None),
], ["calendar_view", "reminders", "calendar_event", "network"], [E("Event", "title:String, date:String, time:String, place:String")],
  apis=[AP.holidays()], color="#3949AB", glyph="CAL")

T("Hábitos", "Produtividade", "Acompanhe hábitos diários com sequência e gráficos.", [
    list_screen("Habitos", "Hábitos", "entity:Habit", icon="home", fab="navigate:NovoHabito", detail=None),
    form_screen("NovoHabito", "Novo hábito", [("Hábito", "name", "text", "required"),
                                              ("Frequência", "frequency", "dropdown=Diário;Semanal"), ("Lembrete", "reminder", "switch")],
                entity="Habit", after="Habitos"),
    dashboard_screen("Progresso", "Progresso", [("Sequência atual", "12 dias")], chart="bar", values="5,6,7,4,7,6,7", icon="star"),
], ["charts", "reminders"], [E("Habit", "name:String, frequency:String, reminder:Boolean")], color="#00897B", glyph="HAB")

T("Gerenciador de projetos", "Produtividade", "Projetos e tarefas por status com quadro estilo kanban.", [
    list_screen("Projetos", "Projetos", "entity:Project", icon="home", fab="navigate:NovoProjeto", detail=None),
    form_screen("NovoProjeto", "Novo projeto", [("Nome", "name", "text", "required"), ("Responsável", "owner"),
                                                ("Status", "status", "dropdown=A fazer;Em andamento;Concluído"), ("Entrega", "dueDate", "date")],
                entity="Project", after="Projetos"),
    S("Quadro", "Quadro", [C("tabs", key="column", options="A fazer;Em andamento;Concluído"),
                           C("list", source="entity:Project", show_image=False)], nav=True, icon="list"),
], ["charts"], [E("Project", "name:String, owner:String, status:String, dueDate:String")], color="#455A64", glyph="KAN")

T("Leitor de QR Code", "Produtividade", "Leia e gere QR Codes, com histórico.", [
    S("Ler", "Ler código", [C("title", text="Leitor de QR Code"), C("text", text="Toque no botão e aponte para o código."),
                            C("button", text="Escanear", action="scan_code")], nav=True, icon="search"),
    S("Gerar", "Gerar", [C("text_field", label="Texto ou link", key="content"), C("qr_code", text="https://example.com"),
                         C("button", text="Compartilhar", action="share:https://example.com", style="outlined")],
      nav=True, icon="add"),
], ["barcode_scanner", "qr_generator", "clipboard"], color="#212121", glyph="QR")

T("Scanner de documentos", "Produtividade", "Fotografe documentos, extraia o texto (OCR) e gere PDF.", [
    S("Digitalizar", "Digitalizar", [C("image", source="photo", height=260), C("button", text="Fotografar documento", action="take_photo"),
                                     C("button", text="Escolher imagem", action="pick_image", style="outlined"),
                                     C("text", text="O texto reconhecido aparece aqui após o processamento.", style="caption")],
      nav=True, icon="edit"),
    list_screen("Documentos", "Documentos", "entity:Document", icon="list", search=True, detail=None),
], ["camera_capture", "image_picker", "ocr", "pdf_generator", "file_provider"], [E("Document", "title:String, text:String")],
  color="#424242", glyph="SCAN")

T("Gravador de voz", "Produtividade", "Grave, ouça e compartilhe áudios.", [
    S("Gravar", "Gravar", [C("timer", mode="stopwatch"), C("button", text="Iniciar gravação", action="toast:Gravando..."),
                           C("text", text="As gravações ficam salvas no aparelho.", style="caption")], nav=True, icon="play"),
    list_screen("Gravacoes", "Gravações", "entity:Recording", icon="list", detail=None),
], ["audio_recorder", "audio_player", "timer", "file_provider"], [E("Recording", "name:String, seconds:Int")],
  color="#B71C1C", glyph="REC")

T("Lista de compras", "Produtividade", "Lista de mercado compartilhável com quantidades e preços.", [
    list_screen("Lista", "Lista de compras", "entity:ShoppingItem", price=True, icon="home", fab="navigate:NovoItem", detail=None),
    form_screen("NovoItem", "Novo item", [("Item", "name", "text", "required"), ("Quantidade", "quantity", "stepper"),
                                          ("Preço estimado", "price", "number")], entity="ShoppingItem", after="Lista"),
], ["csv_export", "speech_to_text"], [E("ShoppingItem", "name:String, quantity:Int, price:Double")], color="#7CB342", glyph="LIST")

# ---------- Social
T("Rede social", "Social e comunicação", "Feed de posts, perfil, curtidas e comentários.", login_screens("Feed") + [
    list_screen("Feed", "Feed", "api:DummyJson.getPosts", icon="home", fab="navigate:NovoPost"),
    detail_screen(buttons=[("Curtir", "favorite"), ("Compartilhar", "share_item", "outlined")]),
    form_screen("NovoPost", "Novo post", [("O que você está pensando?", "body", "multiline", "required")],
                after="Feed", button="Publicar", extra=[C("button", text="Adicionar foto", action="pick_image", style="outlined")]),
    list_screen("Pessoas", "Pessoas", "api:RandomUser.getPeople", icon="person", detail=None),
    profile_screen("Login"),
], ["local_auth", "favorites", "image_picker", "network", "notifications"],
  apis=[AP.dummyjson(("posts",)), AP.randomuser()], color="#1DA1F2", start="Login", glyph="SOC")

T("Chat / mensageiro", "Social e comunicação", "Conversas com lista de contatos e mensagens.", login_screens("Conversas") + [
    list_screen("Conversas", "Conversas", "sample:contacts", detail="Chat", icon="email"),
    chat_screen(nav=False),
    profile_screen("Login"),
], ["chat", "local_auth", "notifications"], sample_sets={"contacts": CONTACTS}, color="#25D366", start="Login", glyph="CHAT")

T("Fórum / comunidade", "Social e comunicação", "Tópicos, respostas e categorias de discussão.", [
    list_screen("Topicos", "Tópicos", "api:JsonPlaceholder.getPosts", icon="home", chips="Geral;Ajuda;Ideias"),
    S("Detalhe", "Tópico", [C("item_detail"), C("title", text="Respostas", size="small"),
                            C("list", source="api:JsonPlaceholder.getComments", show_image=False),
                            C("text_field", label="Sua resposta", key="reply", input="multiline"),
                            C("button", text="Responder", action="toast:Resposta publicada")]),
], ["network"], apis=[AP.jsonplaceholder(("posts", "comments"))], color="#FF7043", glyph="FOR")

T("Networking profissional", "Social e comunicação", "Perfis profissionais, conexões e vagas.", [
    list_screen("Pessoas", "Pessoas", "api:RandomUser.getPeople", icon="home"),
    detail_screen(buttons=[("Conectar", "favorite"), ("Enviar e-mail", "email:contato@exemplo.com", "outlined")]),
    list_screen("Conexoes", "Conexões", "favorites", icon="person", search=False),
    list_screen("Vagas", "Vagas", "sample:leads", icon="list", detail=None),
], ["favorites", "network"], apis=[AP.randomuser()], sample_sets={"leads": LEADS}, color="#0A66C2", glyph="NET")

T("Galeria de fotos", "Social e comunicação", "Galeria com fotos da câmera e da galeria do aparelho.", [
    list_screen("Galeria", "Galeria", "sample:default", grid=True, icon="home", search=False),
    detail_screen(buttons=[("Compartilhar", "share_item")]),
    S("Camera", "Câmera", [C("camera_preview", height=360), C("button", text="Tirar foto", action="take_photo")],
      nav=True, icon="add"),
], ["camerax_preview", "camera_capture", "gallery_save", "image_utils"], color="#6D4C41", glyph="PIC")

T("Blog", "Social e comunicação", "Blog com artigos da API JSONPlaceholder e comentários.", [
    list_screen("Artigos", "Artigos", "api:JsonPlaceholder.getPosts", icon="home"),
    detail_screen(buttons=[("Salvar", "favorite"), ("Compartilhar", "share_item", "outlined")]),
    list_screen("Salvos", "Salvos", "favorites", icon="favorite", search=False),
    about_screen("Blog", "Um blog de exemplo construído com blocos."),
], ["network", "favorites"], apis=[AP.jsonplaceholder(("posts",))], color="#5D4037", glyph="BLOG")

# ---------- Entretenimento
T("Podcasts", "Entretenimento", "Busca de podcasts reais (iTunes) e player.", [
    list_screen("Podcasts", "Podcasts", "api:ITunes.search", icon="home"),
    detail_screen(buttons=[("Seguir", "favorite"), ("Compartilhar", "share_item", "outlined")]),
    list_screen("Seguindo", "Seguindo", "favorites", icon="star", search=False),
], ["network", "favorites", "audio_player"], apis=[AP.itunes("podcast", "tecnologia")], color="#8E24AA", glyph="POD")

T("Player de música", "Entretenimento", "Músicas com prévia de áudio e playlists.", [
    list_screen("Musicas", "Músicas", "api:ITunes.search", icon="home"),
    detail_screen(buttons=[("Adicionar à playlist", "favorite")]),
    list_screen("Playlist", "Playlist", "favorites", icon="play", search=False),
], ["network", "favorites", "audio_player", "foreground_service"], apis=[AP.itunes("music", "bossa nova")],
  color="#1DB954", glyph="MUS")

T("Streaming de vídeo", "Entretenimento", "Catálogo de vídeos com player integrado.", [
    list_screen("Catalogo", "Catálogo", "sample:videos", grid=True, icon="home"),
    detail_screen(extra=[C("video_player")], buttons=[("Minha lista", "favorite")]),
    list_screen("MinhaLista", "Minha lista", "favorites", icon="star", search=False),
], ["video_player", "favorites"], sample_sets={"videos": VIDEOS}, color="#E50914", glyph="TV")

T("Rádio online", "Entretenimento", "Estações de rádio com player de áudio.", [
    list_screen("Radios", "Rádios", "sample:stations", icon="home"),
    detail_screen(buttons=[("Ouvir", "toast:Conectando à rádio..."), ("Favoritar", "favorite", "outlined")]),
    list_screen("Favoritas", "Favoritas", "favorites", icon="favorite", search=False),
], ["audio_player", "favorites"], sample_sets={"stations": STATIONS}, color="#FF6F00", glyph="FM")

T("Quiz", "Entretenimento", "Perguntas e respostas com pontuação.", [
    list_screen("Perguntas", "Perguntas", "sample:questions", detail="Responder", icon="home", search=False),
    S("Responder", "Responder", [C("item_detail"), C("radio_group", label="Resposta", key="answer",
                                                       options="Opção A;Opção B;Opção C;Opção D"),
                                 C("button", text="Confirmar", action="toast:Resposta registrada!")]),
    dashboard_screen("Placar", "Placar", [("Acertos", "8 de 10")], icon="star"),
], ["vibration", "sound_effects"], sample_sets={"questions": QUESTIONS}, color="#7E57C2", glyph="QUIZ")

T("Eventos e ingressos", "Entretenimento", "Agenda de eventos, compra de ingressos e QR Code de entrada.", [
    list_screen("Eventos", "Eventos", "sample:events", price=True, icon="home"),
    detail_screen(price=True, buttons=[("Comprar ingresso", "add_cart"), ("Adicionar à agenda", "toast:Evento salvo", "outlined")]),
    cart_screen("Ingresso"),
    S("Ingresso", "Seu ingresso", [C("title", text="Ingresso confirmado"), C("qr_code", text="INGRESSO-2026-000981"),
                                   C("text", text="Apresente este código na entrada.")], icon="star"),
], ["cart", "qr_generator", "calendar_event"], sample_sets={"events": EVENTS}, color="#AD1457", glyph="TIX")

# ---------- Educacao
T("Cursos online", "Educação", "Cursos, aulas em vídeo e progresso do aluno.", login_screens("Cursos") + [
    list_screen("Cursos", "Cursos", "sample:courses", price=True, icon="home"),
    detail_screen(price=True, extra=[C("video_player")], buttons=[("Matricular", "add_cart")]),
    dashboard_screen("Progresso", "Meu progresso", [("Cursos ativos", "3"), ("Aulas concluídas", "27")], icon="star"),
    profile_screen("Login"),
], ["local_auth", "video_player", "cart", "charts"], sample_sets={"courses": COURSES}, color="#3F51B5", start="Login", glyph="EDU")

T("Flashcards", "Educação", "Cartões de estudo com repetição.", [
    list_screen("Baralho", "Baralho", "entity:Flashcard", icon="home", fab="navigate:NovoCartao", detail=None),
    form_screen("NovoCartao", "Novo cartão", [("Frente", "front", "text", "required"), ("Verso", "back", "multiline")],
                entity="Flashcard", after="Baralho"),
    list_screen("Exemplos", "Exemplos", "sample:cards", icon="star"),
    detail_screen(),
], ["text_to_speech"], [E("Flashcard", "front:String, back:String")], sample_sets={"cards": FLASHCARDS}, color="#F06292", glyph="FLSH")

T("Dicionário", "Educação", "Definições em inglês via Free Dictionary API.", [
    S("Buscar", "Dicionário", [C("text_field", label="Palavra em inglês", key="word"),
                               C("button", text="Buscar", action="api:Dictionary.define"),
                               C("list", source="api:Dictionary.define", show_image=False, empty_text="Digite uma palavra")],
      nav=True, icon="search"),
], ["network", "text_to_speech"], apis=[AP.dictionary()], color="#455A64", glyph="DIC")

T("Tradutor", "Educação", "Tradução offline com ML Kit e leitura em voz alta.", [
    S("Traduzir", "Traduzir", [C("text_field", label="Texto em português", key="text", input="multiline"),
                               C("button", text="Traduzir para inglês", action="toast:Tradução em andamento"),
                               C("button", text="Ouvir", action="speak:Hello, how are you?", style="outlined"),
                               C("button", text="Falar", action="listen", style="text")], nav=True, icon="home"),
], ["translate", "text_to_speech", "speech_to_text", "language_id"], color="#1A73E8", glyph="TRAD")

T("Biblioteca de livros", "Educação", "Busca de livros na Open Library com lista de leitura.", [
    list_screen("Livros", "Livros", "api:OpenLibrary.searchBooks", icon="home"),
    detail_screen(buttons=[("Quero ler", "favorite")]),
    list_screen("Leitura", "Minha lista", "favorites", icon="star", search=False),
], ["network", "favorites"], apis=[AP.openlibrary()], color="#8D6E63", glyph="BOOK")

T("Portal do aluno", "Educação", "Notas, faltas, horários e avisos da escola.", login_screens("Painel") + [
    dashboard_screen("Painel", "Painel do aluno", [("Média geral", "8,4"), ("Frequência", "94%")]),
    list_screen("Avisos", "Avisos", "sample:news", icon="notifications"),
    detail_screen(),
    S("Horarios", "Horários", [C("tabs", key="day", options="Seg;Ter;Qua;Qui;Sex"),
                               C("list", source="sample:courses", show_image=False)], nav=True, icon="date"),
], ["local_auth", "notifications", "charts"], sample_sets={"news": NEWS, "courses": COURSES}, color="#0277BD",
  start="Login", glyph="ALU")

T("Matemática para crianças", "Educação", "Exercícios de tabuada com pontuação e sons.", [
    S("Jogar", "Tabuada", [C("title", text="Quanto é 7 x 8?", align="center"),
                           C("text_field", label="Resposta", key="answer", input="number"),
                           C("button", text="Responder", action="toast:Muito bem!"),
                           C("stat_card", label="Pontos", value="120")], nav=True, icon="star"),
], ["sound_effects", "vibration"], color="#FF7043", glyph="MATH")

T("Aprender idiomas", "Educação", "Lições, pronúncia com voz e reconhecimento de fala.", [
    list_screen("Licoes", "Lições", "sample:lessons", icon="home"),
    detail_screen(buttons=[("Ouvir pronúncia", "speak:Good morning"), ("Praticar fala", "listen", "outlined")]),
    dashboard_screen("Progresso", "Progresso", [("Sequência", "9 dias"), ("XP", "1.240")], icon="star"),
], ["text_to_speech", "speech_to_text", "charts"], sample_sets={"lessons": LESSONS}, color="#58CC02", glyph="LANG")

T("Calculadora", "Educação", "Calculadora com histórico de operações.", [
    S("Calcular", "Calculadora", [C("text_field", label="Número A", key="a", input="number"),
                                  C("text_field", label="Número B", key="b", input="number"),
                                  C("chips", key="op", options="+;-;x;/"),
                                  C("button", text="Calcular", action="submit:")], nav=True, icon="build", form="Calculation"),
    list_screen("Historico", "Histórico", "entity:Calculation", icon="list", search=False, detail=None),
], [], [E("Calculation", "a:Double, b:Double, op:String")], color="#546E7A", glyph="CALC")

# ---------- Viagem e transporte
T("Mobilidade / táxi", "Viagem e transporte", "Pedir corrida com origem, destino e acompanhamento no mapa.", login_screens("Corrida") + [
    S("Corrida", "Para onde?", [C("map_view", height=300), C("text_field", label="Destino", key="destination"),
                                C("radio_group", label="Categoria", key="category", options="Econômico;Conforto;Executivo"),
                                C("button", text="Pedir corrida", action="submit:Viagens"),
                                C("button", text="Usar minha localização", action="location", style="outlined")],
      nav=True, icon="place", form="Ride"),
    list_screen("Viagens", "Viagens", "entity:Ride", icon="list", search=False, detail=None),
    profile_screen("Login"),
], ["maps", "location", "local_auth", "location_updates"], [E("Ride", "destination:String, category:String")],
  color="#000000", start="Login", glyph="RIDE")

T("Aluguel de carros", "Viagem e transporte", "Frota, reserva por período e checkout.", [
    list_screen("Frota", "Frota", "sample:cars", price=True, icon="home", grid=True),
    S("Detalhe", "Reservar", [C("item_detail", show_price=True), C("date_picker", label="Retirada", key="pickup"),
                              C("date_picker", label="Devolução", key="dropoff"), C("switch", label="Seguro completo", key="insurance"),
                              C("button", text="Reservar", action="submit:Reservas")], form="CarRental"),
    list_screen("Reservas", "Reservas", "entity:CarRental", icon="date", search=False, detail=None),
], ["notifications"], [E("CarRental", "pickup:String, dropoff:String, insurance:Boolean")],
  sample_sets={"cars": CARS}, color="#2E7D32", glyph="CAR")

T("Reserva de hotéis", "Viagem e transporte", "Busca de hotéis, datas, hóspedes e favoritos.", [
    list_screen("Hoteis", "Hotéis", "sample:hotels", price=True, icon="home",
                header=[C("date_picker", label="Check-in", key="checkin"), C("date_picker", label="Check-out", key="checkout"),
                        C("stepper", label="Hóspedes", key="guests", max=10)]),
    detail_screen(price=True, extra=[C("map_view", title="Hotel")], buttons=[("Reservar", "toast:Reserva confirmada!"),
                                                                           ("Favoritar", "favorite", "outlined")]),
    list_screen("Favoritos", "Favoritos", "favorites", icon="favorite", search=False, price=True),
], ["maps", "favorites"], sample_sets={"hotels": HOTELS}, color="#003580", glyph="HTL")

T("Guia turístico", "Viagem e transporte", "Pontos turísticos, mapa e roteiros.", [
    list_screen("Lugares", "Lugares", "sample:places", icon="home", grid=True),
    detail_screen(extra=[C("map_view", title="Ponto turístico")], buttons=[("Salvar no roteiro", "favorite"),
                                                                          ("Ouvir descrição", "speak:Bem-vindo a este lugar", "outlined")]),
    list_screen("Roteiro", "Meu roteiro", "favorites", icon="place", search=False),
    list_screen("Paises", "Países", "api:Countries.getCountries", icon="star", detail=None),
], ["maps", "favorites", "text_to_speech", "network"], apis=[AP.restcountries()], sample_sets={"places": PLACES},
  color="#00897B", glyph="TOUR")

T("Passagens aéreas", "Viagem e transporte", "Busca de voos, seleção e cartão de embarque.", [
    S("Buscar", "Buscar voos", [C("text_field", label="Origem", key="origin"), C("text_field", label="Destino", key="destination"),
                                C("date_picker", label="Ida", key="departure"), C("stepper", label="Passageiros", key="passengers"),
                                C("button", text="Buscar", action="navigate:Voos")], nav=True, icon="search"),
    list_screen("Voos", "Voos disponíveis", "sample:trips", price=True, detail="Embarque", nav=False),
    S("Embarque", "Cartão de embarque", [C("item_detail", show_price=True), C("qr_code", text="BOARDING-PASS-AB1234")]),
], ["qr_generator"], sample_sets={"trips": TRIPS}, color="#0D47A1", glyph="FLY")

T("Estacionamento", "Viagem e transporte", "Encontre vagas, reserve e pague o estacionamento.", [
    list_screen("Vagas", "Estacionamentos", "sample:parking", price=True, icon="home"),
    detail_screen(price=True, extra=[C("map_view", title="Estacionamento"), C("timer", mode="stopwatch")],
                  buttons=[("Reservar vaga", "toast:Vaga reservada por 15 minutos")]),
    S("Mapa", "Mapa", [C("map_view", height=460)], nav=True, icon="place"),
], ["maps", "timer", "location"], sample_sets={"parking": PARKING}, color="#1565C0", glyph="PARK")

T("Transporte público", "Viagem e transporte", "Linhas, horários e alertas de transporte.", [
    list_screen("Linhas", "Linhas", "sample:lines", icon="home"),
    detail_screen(buttons=[("Avisar chegada", "notify:Seu ônibus chega em 3 minutos"), ("Favoritar", "favorite", "outlined")]),
    list_screen("Favoritas", "Favoritas", "favorites", icon="star", search=False),
    S("Mapa", "Mapa", [C("map_view", height=460), C("button", text="Onde estou", action="location")], nav=True, icon="place"),
], ["maps", "location", "notifications", "favorites"], sample_sets={"lines": LINES}, color="#0097A7", glyph="BUS")

T("Mapa de pontos de interesse", "Viagem e transporte", "Cadastre locais favoritos com coordenadas.", [
    S("Mapa", "Mapa", [C("map_view", height=420), C("button", text="Minha localização", action="location")], nav=True, icon="place"),
    list_screen("Locais", "Locais", "entity:Place", icon="list", fab="navigate:NovoLocal", detail=None),
    form_screen("NovoLocal", "Novo local", [("Nome", "name", "text", "required"), ("Latitude", "lat", "number"),
                                            ("Longitude", "lng", "number"), ("Categoria", "category")], entity="Place", after="Locais"),
], ["maps", "location", "geocoding"], [E("Place", "name:String, lat:Double, lng:Double, category:String")],
  color="#C62828", glyph="POI")

T("Diário de viagem", "Viagem e transporte", "Registre viagens com fotos, notas e localização.", [
    list_screen("Viagens", "Viagens", "entity:Trip", icon="home", fab="navigate:NovaViagem", detail=None, grid=True),
    form_screen("NovaViagem", "Nova viagem", [("Destino", "destination", "text", "required"), ("Data", "date", "date"),
                                              ("Notas", "notes", "multiline"), ("Avaliação", "rating", "rating")],
                entity="Trip", after="Viagens", extra=[C("image", source="photo", height=160),
                                                       C("button", text="Adicionar foto", action="pick_image", style="outlined")]),
], ["image_picker", "location"], [E("Trip", "destination:String, date:String, notes:String, rating:Int")],
  color="#00838F", glyph="TRIP")

T("Rastreamento de entregas", "Viagem e transporte", "Acompanhe encomendas e consulte endereços por CEP.", [
    list_screen("Encomendas", "Encomendas", "entity:Parcel", icon="home", fab="navigate:NovaEncomenda", detail=None),
    form_screen("NovaEncomenda", "Nova encomenda", [("Descrição", "name", "text", "required"), ("Código de rastreio", "code"),
                                                    ("Loja", "store")], entity="Parcel", after="Encomendas"),
    S("Cep", "Consultar CEP", [C("text_field", label="CEP", key="cep", input="number", validation="cep"),
                               C("button", text="Consultar", action="api:BrasilApi.lookupCep"),
                               C("list", source="api:BrasilApi.lookupCep", show_image=False, empty_text="Informe um CEP")],
      nav=True, icon="place"),
], ["network", "notifications", "barcode_scanner"], [E("Parcel", "name:String, code:String, store:String")],
  apis=[AP.brasil_cep()], color="#FFA000", glyph="TRK")

# ---------- Servicos
T("Agendamento de salão", "Serviços", "Serviços de beleza, profissionais e horários.", [
    list_screen("Servicos", "Serviços", "sample:services", price=True, icon="home"),
    S("Detalhe", "Agendar", [C("item_detail", show_price=True), C("calendar", key="date"),
                             C("chips", key="time", options="09:00;10:30;14:00;16:30"),
                             C("button", text="Agendar", action="submit:Agenda")], form="Booking"),
    list_screen("Agenda", "Meus horários", "entity:Booking", icon="date", search=False, detail=None),
], ["calendar_view", "reminders", "notifications"], [E("Booking", "date:String, time:String")],
  sample_sets={"services": SERVICES}, color="#EC407A", glyph="SALON")

T("Serviços domésticos", "Serviços", "Contrate eletricistas, encanadores e diaristas.", login_screens("Profissionais") + [
    list_screen("Profissionais", "Profissionais", "sample:pros", price=True, icon="home",
                chips="Eletricista;Encanador;Diarista;Pintor"),
    detail_screen(price=True, buttons=[("Solicitar orçamento", "navigate:Chat"), ("Ligar", "call:11988887777", "outlined")]),
    chat_screen(),
    profile_screen("Login"),
], ["chat", "local_auth", "location"], sample_sets={"pros": PROFESSIONALS}, color="#5E35B1", start="Login", glyph="FIX")

T("Academia - check-in", "Serviços", "Check-in por QR Code, aulas e plano do aluno.", login_screens("Inicio") + [
    dashboard_screen("Inicio", "Minha academia", [("Check-ins no mês", "16"), ("Plano", "Anual")],
                     extra=[C("qr_code", text="ALUNO-4521")]),
    list_screen("Aulas", "Aulas", "sample:workouts", icon="date"),
    detail_screen(buttons=[("Reservar vaga", "toast:Vaga reservada")]),
], ["local_auth", "qr_generator", "charts"], sample_sets={"workouts": WORKOUTS}, color="#FF5722", start="Login", glyph="FIT")

T("Imobiliária", "Serviços", "Imóveis para alugar e comprar com mapa e contato.", [
    list_screen("Imoveis", "Imóveis", "sample:properties", price=True, icon="home", chips="Alugar;Comprar;Lançamentos"),
    detail_screen(price=True, extra=[C("map_view", title="Imóvel")], buttons=[("Agendar visita", "toast:Visita solicitada"),
                                                                           ("Favoritar", "favorite", "outlined")]),
    list_screen("Favoritos", "Favoritos", "favorites", icon="favorite", search=False, price=True),
], ["maps", "favorites", "calendar_event"], sample_sets={"properties": PROPERTIES}, color="#00695C", glyph="CASA")

T("Condomínio", "Serviços", "Avisos, reservas de áreas comuns e portaria.", login_screens("Avisos") + [
    list_screen("Avisos", "Avisos", "sample:club", icon="notifications"),
    detail_screen(),
    form_screen("Reservas", "Reservar área", [("Área", "area", "dropdown=Salão de festas;Churrasqueira;Quadra"),
                                              ("Data", "date", "date")], entity="AreaBooking", after="Avisos", nav=True, icon="date"),
    S("Portaria", "Portaria", [C("button", text="Liberar visitante", action="toast:Visitante liberado"),
                               C("button", text="Ligar para portaria", action="call:1133334444", style="outlined"),
                               C("qr_code", text="ACESSO-APTO-101")], nav=True, icon="lock"),
], ["local_auth", "notifications", "qr_generator"], [E("AreaBooking", "area:String, date:String")],
  sample_sets={"club": CHURCH}, color="#37474F", start="Login", glyph="COND")

T("Associação / clube", "Serviços", "Avisos, eventos, carteirinha digital e mensalidade.", [
    list_screen("Mural", "Mural", "sample:club", icon="home"),
    detail_screen(),
    S("Carteirinha", "Carteirinha", [C("avatar", name="Sócio Exemplo", subtitle="Matrícula 0042"),
                                     C("qr_code", text="SOCIO-0042")], nav=True, icon="account"),
    list_screen("Eventos", "Eventos", "sample:events", icon="date", price=True),
], ["qr_generator", "notifications"], sample_sets={"club": CHURCH, "events": EVENTS}, color="#1565C0", glyph="CLUB")

T("Ordem de serviço", "Serviços", "Abertura e acompanhamento de ordens de serviço com assinatura e fotos.", [
    list_screen("Ordens", "Ordens", "entity:ServiceOrder", icon="home", fab="navigate:NovaOrdem", detail=None),
    form_screen("NovaOrdem", "Nova OS", [("Cliente", "client", "text", "required"), ("Equipamento", "equipment"),
                                         ("Defeito", "issue", "multiline"), ("Status", "status", "dropdown=Aberta;Em andamento;Concluída")],
                entity="ServiceOrder", after="Ordens", extra=[C("button", text="Foto do equipamento", action="take_photo", style="outlined")]),
], ["camera_capture", "pdf_generator", "file_provider"], [E("ServiceOrder", "client:String, equipment:String, issue:String, status:String")],
  color="#EF6C00", glyph="OS")

# ---------- Negocios
T("CRM de vendas", "Negócios", "Leads, funil de vendas e indicadores.", [
    dashboard_screen("Painel", "Funil de vendas", [("Leads ativos", "38"), ("Taxa de conversão", "22%")], chart="bar",
                     values="38,21,12,8"),
    list_screen("Leads", "Leads", "entity:Lead", icon="person", fab="navigate:NovoLead", detail=None),
    form_screen("NovoLead", "Novo lead", [("Empresa", "company", "text", "required"), ("Contato", "contact"),
                                          ("Telefone", "phone", "phone", "phone"), ("Etapa", "stage", "dropdown=Contato;Proposta;Negociação;Fechado")],
                entity="Lead", after="Leads"),
], ["charts", "csv_export", "validators"], [E("Lead", "company:String, contact:String, phone:String, stage:String")],
  color="#283593", glyph="CRM")

T("Ponto eletrônico", "Negócios", "Registro de entrada e saída com localização e biometria.", login_screens("Ponto") + [
    S("Ponto", "Registrar ponto", [C("timer", mode="stopwatch"), C("button", text="Registrar entrada", action="biometric:Registros"),
                                   C("button", text="Registrar saída", action="submit:Registros", style="outlined")],
      nav=True, icon="home", form="Punch"),
    list_screen("Registros", "Registros", "entity:Punch", icon="list", search=False, detail=None),
], ["local_auth", "biometric", "location", "timer"], [E("Punch", "kind:String, time:String")], color="#4E342E",
  start="Login", glyph="PONTO")

T("Gestão de estoque", "Negócios", "Produtos, quantidades, leitura de código de barras e exportação.", [
    list_screen("Estoque", "Estoque", "entity:StockItem", price=True, icon="home", fab="navigate:NovoProdutoEstoque", detail=None),
    form_screen("NovoProdutoEstoque", "Novo produto", [("Nome", "name", "text", "required"), ("Código", "code"),
                                                       ("Quantidade", "quantity", "stepper"), ("Custo", "price", "number")],
                entity="StockItem", after="Estoque", extra=[C("button", text="Ler código", action="scan_code", style="outlined")]),
    dashboard_screen("Relatorio", "Relatório", [("Itens", "412"), ("Valor em estoque", "R$ 38.900")], icon="star"),
], ["barcode_scanner", "csv_export", "charts"], [E("StockItem", "name:String, code:String, quantity:Int, price:Double")],
  sample_sets={"stock": STOCK}, color="#1B5E20", glyph="STK")

T("PDV (ponto de venda)", "Negócios", "Venda rápida com carrinho, troco e recibo em PDF.", [
    list_screen("Vender", "Vender", "sample:stock", price=True, icon="home", item_action="add_cart", detail=None),
    cart_screen("Recibo", name="Venda"),
    done_screen("Recibo", "Venda concluída", "O recibo foi gerado.", "Vender"),
], ["cart", "pdf_generator", "barcode_scanner", "formatters"], sample_sets={"stock": STOCK}, color="#00695C", glyph="PDV")

T("Pesquisa e formulários", "Negócios", "Coleta de respostas offline com exportação CSV.", [
    form_screen("Pesquisa", "Pesquisa de satisfação", [("Nome", "name"), ("Nota de 1 a 5", "score", "rating"),
                                                       ("Recomendaria?", "recommend", "switch"), ("Comentário", "comment", "multiline")],
                entity="SurveyAnswer", after="Respostas", button="Enviar", nav=True, icon="edit"),
    list_screen("Respostas", "Respostas", "entity:SurveyAnswer", icon="list", detail=None),
], ["csv_export"], [E("SurveyAnswer", "name:String, score:Int, recommend:Boolean, comment:String")], color="#6A1B9A", glyph="FORM")

T("Portfólio pessoal", "Negócios", "Apresente projetos, currículo e contato.", [
    S("Inicio", "Portfólio", [C("avatar", name="Seu Nome", subtitle="Desenvolvedor Android"),
                              C("text", text="Apaixonado por criar apps bonitos e rápidos."),
                              C("button", text="Entrar em contato", action="email:contato@exemplo.com")], nav=True, icon="home"),
    list_screen("Projetos", "Projetos", "sample:default", grid=True, icon="star"),
    detail_screen(buttons=[("Ver no GitHub", "open_url:https://github.com")]),
    S("Site", "Site", [C("web_view", url="https://developer.android.com")], nav=True, icon="info"),
], ["custom_tabs"], color="#212121", glyph="ME")

# ---------- Utilidades
T("Lanterna e utilidades", "Utilidades", "Lanterna, bateria, informações do aparelho e bússola.", [
    S("Lanterna", "Ferramentas", [C("title", text="Ferramentas", align="center"),
                                  C("button", text="Ligar/desligar lanterna", action="flashlight"),
                                  C("button", text="Ver bateria", action="battery", style="outlined"),
                                  C("button", text="Informações do aparelho", action="device_info", style="outlined")],
      nav=True, icon="home"),
], ["flashlight", "battery", "device_info", "compass"], color="#FFC107", glyph="UTIL")

T("Bússola", "Utilidades", "Bússola digital com localização atual.", [
    S("Bussola", "Bússola", [C("title", text="N", align="center"), C("text", text="Gire o aparelho para encontrar o norte.",
                                                                         align="center"),
                             C("button", text="Minha localização", action="location")], nav=True, icon="place"),
], ["compass", "location", "sensors"], color="#455A64", glyph="NSEW")

T("Cronômetro e timer", "Utilidades", "Cronômetro e temporizador com alerta.", [
    S("Cronometro", "Cronômetro", [C("timer", mode="stopwatch")], nav=True, icon="play"),
    S("Timer", "Timer", [C("timer", mode="countdown", seconds=300),
                         C("button", text="Avisar ao terminar", action="notify:Tempo esgotado!", style="outlined")],
      nav=True, icon="notifications"),
], ["timer", "notifications", "vibration", "keep_screen_on"], color="#3949AB", glyph="TIME")

T("Monitor do aparelho", "Utilidades", "Bateria, rede, sensores e armazenamento.", [
    S("Painel", "Painel", [C("stat_card", label="Bateria", value="--"), C("stat_card", label="Conexão", value="--"),
                           C("button", text="Atualizar bateria", action="battery"),
                           C("button", text="Detalhes do aparelho", action="device_info", style="outlined")], nav=True, icon="home"),
], ["battery", "device_info", "connectivity", "sensors"], color="#2E7D32", glyph="DEV")

T("Agenda de contatos", "Utilidades", "Contatos do aparelho com ligação, SMS e e-mail.", [
    list_screen("Contatos", "Contatos", "contacts", icon="home", detail="Detalhe"),
    detail_screen(buttons=[("Ligar", "call:"), ("Mensagem", "sms:", "outlined"), ("Copiar", "copy:", "text")]),
    list_screen("Favoritos", "Favoritos", "favorites", icon="star", search=False),
], ["contacts", "favorites", "clipboard"], color="#0288D1", glyph="CONT")

T("Clube de fidelidade", "Utilidades", "Pontos, recompensas e QR Code do cliente.", login_screens("Pontos") + [
    dashboard_screen("Pontos", "Meus pontos", [("Saldo", "1.250 pontos"), ("Nível", "Ouro")],
                     extra=[C("qr_code", text="FIDELIDADE-CLIENTE-77")]),
    list_screen("Recompensas", "Recompensas", "sample:deals", icon="star"),
    detail_screen(buttons=[("Resgatar", "toast:Recompensa resgatada!")]),
], ["local_auth", "loyalty", "qr_generator"], sample_sets={"deals": DEALS}, color="#F9A825", start="Login", glyph="VIP")

T("Doações / ONG", "Utilidades", "Campanhas, doações por Pix e voluntariado.", [
    list_screen("Campanhas", "Campanhas", "sample:club", icon="home"),
    detail_screen(extra=[C("progress", style="linear", bind_loading=False), C("qr_code", text="PIX-ONG-DOACAO")],
                  buttons=[("Copiar chave Pix", "copy:ong@exemplo.org"), ("Compartilhar", "share_item", "outlined")]),
    form_screen("Voluntario", "Seja voluntário", [("Nome", "name", "text", "required"), ("E-mail", "email", "email", "email"),
                                                  ("Disponibilidade", "availability", "dropdown=Manhã;Tarde;Noite;Fins de semana")],
                entity="Volunteer", after="Campanhas", nav=True, icon="person"),
], ["qr_generator", "clipboard", "validators"], [E("Volunteer", "name:String, email:String, availability:String")],
  sample_sets={"club": CHURCH}, color="#E91E63", glyph="ONG")

T("Resultados esportivos", "Entretenimento", "Notícias de esportes, tabela e times favoritos.", [
    list_screen("Noticias", "Notícias", "sample:news", icon="home"),
    detail_screen(buttons=[("Compartilhar", "share_item")]),
    S("Tabela", "Tabela", [C("tabs", key="league", options="Série A;Série B;Copa"),
                           C("list", source="sample:default", show_image=False)], nav=True, icon="list"),
    list_screen("Times", "Meus times", "favorites", icon="star", search=False),
], ["favorites", "notifications"], sample_sets={"news": NEWS}, color="#2E7D32", glyph="GOL")

T("Citações inspiradoras", "Entretenimento", "Frases da API DummyJSON com favoritos e compartilhamento.", [
    list_screen("Frases", "Frases", "api:DummyJson.getQuotes", icon="home"),
    detail_screen(buttons=[("Favoritar", "favorite"), ("Compartilhar", "share_item", "outlined"), ("Ouvir", "speak:Frase do dia", "text")]),
    list_screen("Favoritas", "Favoritas", "favorites", icon="favorite", search=False),
], ["network", "favorites", "text_to_speech", "home_widget"], apis=[AP.dummyjson(("quotes",))], color="#5C6BC0", glyph="QUOT")

T("Livro de receitas pessoal", "Delivery e alimentação", "Receitas próprias e da API DummyJSON.", [
    list_screen("Receitas", "Receitas", "api:DummyJson.getRecipes", grid=True, icon="home"),
    detail_screen(buttons=[("Favoritar", "favorite"), ("Ler em voz alta", "speak:Modo de preparo", "outlined")]),
    list_screen("Minhas", "Minhas receitas", "entity:MyRecipe", icon="edit", fab="navigate:NovaReceita", detail=None),
    form_screen("NovaReceita", "Nova receita", [("Nome", "name", "text", "required"), ("Ingredientes", "ingredients", "multiline"),
                                                ("Preparo", "steps", "multiline")], entity="MyRecipe", after="Minhas"),
], ["network", "favorites", "text_to_speech", "keep_screen_on"], [E("MyRecipe", "name:String, ingredients:String, steps:String")],
  apis=[AP.dummyjson(("recipes",))], color="#FF7043", glyph="COOK")

T("Tarefas na nuvem (API)", "Produtividade", "Tarefas sincronizadas com API REST (DummyJSON).", [
    list_screen("Tarefas", "Tarefas", "api:DummyJson.getTodos", icon="home", detail=None),
    S("Sincronizar", "Sincronizar", [C("text", text="As tarefas são carregadas da API e atualizadas periodicamente."),
                                     C("button", text="Sincronizar agora", action="refresh")], nav=True, icon="build"),
], ["network", "work_manager", "connectivity"], apis=[AP.dummyjson(("todos",))], color="#00796B", glyph="SYNC")

T("Diretório de equipe", "Negócios", "Lista de colaboradores com contato rápido.", [
    list_screen("Equipe", "Equipe", "api:DummyJson.getUsers", icon="home"),
    detail_screen(buttons=[("Ligar", "call:"), ("E-mail", "email:", "outlined")]),
], ["network"], apis=[AP.dummyjson(("users",))], color="#3949AB", glyph="TEAM")

T("Help desk", "Negócios", "Chamados de suporte com prioridade e chat.", login_screens("Chamados") + [
    list_screen("Chamados", "Chamados", "entity:Ticket", icon="home", fab="navigate:NovoChamado", detail=None),
    form_screen("NovoChamado", "Novo chamado", [("Assunto", "subject", "text", "required"), ("Descrição", "description", "multiline"),
                                                ("Prioridade", "priority", "dropdown=Baixa;Média;Alta;Urgente")],
                entity="Ticket", after="Chamados"),
    chat_screen(),
], ["local_auth", "chat", "notifications"], [E("Ticket", "subject:String, description:String, priority:String")],
  color="#C62828", start="Login", glyph="HELP")

T("Controle de frota", "Negócios", "Veículos, abastecimentos e manutenções.", [
    list_screen("Veiculos", "Veículos", "entity:Vehicle", icon="home", fab="navigate:NovoVeiculo", detail=None),
    form_screen("NovoVeiculo", "Novo veículo", [("Placa", "plate", "text", "required"), ("Modelo", "model"),
                                                ("Km atual", "km", "number")], entity="Vehicle", after="Veiculos"),
    form_screen("Abastecer", "Abastecimento", [("Placa", "plate"), ("Litros", "liters", "number"), ("Valor", "amount", "number")],
                entity="Refuel", after="Veiculos", nav=True, icon="add"),
    dashboard_screen("Custos", "Custos", [("Gasto no mês", "R$ 4.320"), ("Consumo médio", "11,2 km/l")], icon="star"),
], ["charts", "location"], [E("Vehicle", "plate:String, model:String, km:Int"), E("Refuel", "plate:String, liters:Double, amount:Double")],
  color="#424242", glyph="FROTA")

T("Checklist de inspeção", "Negócios", "Checklists de vistoria com fotos e relatório em PDF.", [
    form_screen("Checklist", "Inspeção", [("Local", "place", "text", "required"), ("Extintores OK", "extinguishers", "checkbox"),
                                          ("Saídas livres", "exits", "checkbox"), ("Iluminação OK", "lights", "checkbox"),
                                          ("Observações", "notes", "multiline")], entity="Inspection", after="Historico",
                nav=True, icon="check", extra=[C("button", text="Anexar foto", action="take_photo", style="outlined")]),
    list_screen("Historico", "Histórico", "entity:Inspection", icon="list", detail=None),
], ["camera_capture", "pdf_generator", "location"], [E("Inspection", "place:String, extinguishers:Boolean, exits:Boolean, lights:Boolean, notes:String")],
  color="#F57C00", glyph="CHK")

T("App de igreja / comunidade", "Serviços", "Programação, avisos, pedidos de oração e doações.", [
    list_screen("Agenda", "Programação", "sample:club", icon="home"),
    detail_screen(),
    form_screen("Pedidos", "Pedido de oração", [("Nome", "name"), ("Pedido", "request", "multiline", "required")],
                entity="PrayerRequest", after="Agenda", nav=True, icon="favorite"),
    S("Doar", "Contribuir", [C("qr_code", text="PIX-COMUNIDADE"), C("button", text="Copiar chave Pix", action="copy:comunidade@exemplo.org")],
      nav=True, icon="star"),
], ["qr_generator", "clipboard", "notifications"], [E("PrayerRequest", "name:String, request:String")],
  sample_sets={"club": CHURCH}, color="#6A1B9A", glyph="COM")

T("Catálogo de países", "Educação", "Países do mundo com bandeira, capital e população.", [
    list_screen("Paises", "Países", "api:Countries.getCountries", icon="home", grid=True),
    detail_screen(buttons=[("Favoritar", "favorite")]),
    list_screen("Favoritos", "Favoritos", "favorites", icon="star", search=False),
], ["network", "favorites"], apis=[AP.restcountries()], color="#00897B", glyph="WORLD")

T("Votação e enquetes", "Social e comunicação", "Crie enquetes e veja resultados em gráfico.", [
    list_screen("Enquetes", "Enquetes", "entity:Poll", icon="home", fab="navigate:NovaEnquete", detail=None),
    form_screen("NovaEnquete", "Nova enquete", [("Pergunta", "question", "text", "required"), ("Opções (separadas por ;)", "options")],
                entity="Poll", after="Enquetes"),
    dashboard_screen("Resultados", "Resultados", [("Votos", "214")], chart="pie", values="45,30,25", icon="star"),
], ["charts"], [E("Poll", "question:String, options:String")], color="#7B1FA2", glyph="VOTE")

T("Achados e perdidos", "Utilidades", "Publique e encontre objetos perdidos com foto e local.", [
    list_screen("Itens", "Itens", "entity:LostItem", icon="home", fab="navigate:NovoItemPerdido", detail=None),
    form_screen("NovoItemPerdido", "Publicar item", [("Objeto", "name", "text", "required"), ("Onde", "place"),
                                                     ("Contato", "contact", "phone")], entity="LostItem", after="Itens",
                extra=[C("button", text="Foto", action="take_photo", style="outlined")]),
    S("Mapa", "Mapa", [C("map_view", height=440)], nav=True, icon="place"),
], ["camera_capture", "maps", "location"], [E("LostItem", "name:String, place:String, contact:String")], color="#546E7A", glyph="LOST")

T("Coleta seletiva", "Utilidades", "Pontos de reciclagem, dicas e agenda de coleta.", [
    list_screen("Pontos", "Pontos de coleta", "sample:places", icon="home"),
    detail_screen(extra=[C("map_view", title="Ponto de coleta")]),
    S("Dicas", "Dicas", [C("card", title="Plástico", body="Lave as embalagens antes de descartar."),
                         C("card", title="Vidro", body="Embale cacos em jornal."),
                         C("card", title="Eletrônicos", body="Leve a pontos autorizados.")], nav=True, icon="info"),
], ["maps", "location", "reminders"], sample_sets={"places": PLACES}, color="#2E7D32", glyph="ECO")

T("Agenda escolar dos pais", "Educação", "Comunicados, cardápio e calendário escolar.", [
    list_screen("Comunicados", "Comunicados", "sample:news", icon="home"),
    detail_screen(),
    S("Cardapio", "Cardápio", [C("tabs", key="day", options="Seg;Ter;Qua;Qui;Sex"),
                               C("list", source="sample:dishes", show_image=True)], nav=True, icon="list"),
    S("Calendario", "Calendário", [C("calendar", key="date")], nav=True, icon="date"),
], ["calendar_view", "notifications"], sample_sets={"news": NEWS, "dishes": DISHES}, color="#29B6F6", glyph="ESC")

T("Controle de vacinas", "Saúde e bem-estar", "Carteira de vacinação da família com lembretes.", [
    list_screen("Vacinas", "Vacinas", "entity:Vaccine", icon="home", fab="navigate:NovaVacina", detail=None),
    form_screen("NovaVacina", "Registrar vacina", [("Vacina", "name", "text", "required"), ("Pessoa", "person"),
                                                   ("Data", "date", "date"), ("Próxima dose", "nextDose", "date")],
                entity="Vaccine", after="Vacinas"),
], ["reminders", "notifications"], [E("Vaccine", "name:String, person:String, date:String, nextDose:String")],
  color="#00897B", glyph="VAC")

T("Ciclo e bem-estar feminino", "Saúde e bem-estar", "Registro de ciclo, sintomas e previsões.", [
    S("Calendario", "Calendário", [C("calendar", key="date"), C("stat_card", label="Próximo ciclo", value="em 12 dias")],
      nav=True, icon="date"),
    form_screen("Registro", "Registro do dia", [("Fluxo", "flow", "dropdown=Nenhum;Leve;Moderado;Intenso"),
                                                ("Humor", "mood", "rating"), ("Sintomas", "symptoms", "multiline")],
                entity="CycleDay", after="Calendario", nav=True, icon="edit"),
], ["calendar_view", "pin_lock", "reminders"], [E("CycleDay", "flow:String, mood:Int, symptoms:String")],
  color="#EC407A", glyph="CYC")

T("Primeiros socorros", "Saúde e bem-estar", "Guias offline de emergência e ligação rápida.", [
    list_screen("Guias", "Guias", "sample:default", icon="home"),
    detail_screen(buttons=[("Ligar 192 (SAMU)", "call:192"), ("Ouvir instruções", "speak:Mantenha a calma", "outlined")]),
    S("Emergencia", "Emergência", [C("button", text="SAMU 192", action="call:192"), C("button", text="Bombeiros 193", action="call:193"),
                                   C("button", text="Polícia 190", action="call:190"),
                                   C("button", text="Enviar minha localização", action="location", style="outlined")],
      nav=True, icon="phone"),
], ["text_to_speech", "location"], color="#D32F2F", glyph="SOS")

T("Cartão de visitas digital", "Negócios", "Cartão de visitas com QR Code e compartilhamento.", [
    S("Cartao", "Meu cartão", [C("avatar", name="Seu Nome", subtitle="Cargo - Empresa"), C("qr_code", text="https://seusite.com"),
                               C("button", text="Compartilhar contato", action="share:Seu Nome - (11) 99999-0000"),
                               C("button", text="Ligar", action="call:11999990000", style="outlined")], nav=True, icon="account"),
    S("Ler", "Ler cartão", [C("button", text="Escanear QR Code", action="scan_code")], nav=True, icon="search"),
], ["qr_generator", "barcode_scanner"], color="#263238", glyph="CARD")

T("Onboarding + app base", "Utilidades", "Esqueleto completo: apresentação, login, início, perfil e ajustes.", [
    S("Boas", "Boas-vindas", [C("lottie", height=220), C("title", text="Bem-vindo!", align="center"),
                              C("text", text="Conheça o app em poucos passos.", align="center"),
                              C("button", text="Começar", action="finish_onboarding:Login")], icon="star"),
] + login_screens("Inicio") + [
    S("Inicio", "Início", home_header("Olá!", "Este é o seu novo app.", ("Novidade", "Explore os recursos")) +
      [C("list", source="sample:default", item_action="navigate:Detalhe")], nav=True, icon="home"),
    detail_screen(),
    profile_screen("Login"),
    settings_screen(extra=[C("button", text="Alternar tema", action="toggle_theme", style="outlined")]),
], ["onboarding_state", "local_auth", "lottie", "dark_mode_toggle", "splash_screen", "crash_logger"],
  color="#1E88E5", glyph="BASE")

T("Painel administrativo", "Negócios", "Dashboard com KPIs, gráficos e relatórios exportáveis.", [
    dashboard_screen("Painel", "Visão geral", [("Vendas hoje", "R$ 12.480"), ("Pedidos", "86"), ("Ticket médio", "R$ 145")],
                     values="12,15,9,18,22,17,25"),
    dashboard_screen("Vendas", "Vendas por canal", [("Online", "62%")], chart="pie", values="62,25,13", icon="star"),
    list_screen("Pedidos", "Pedidos", "sample:products", price=True, icon="list"),
    detail_screen(price=True),
], ["charts", "csv_export", "pdf_generator"], sample_sets={"products": PRODUCTS}, color="#1E3A8A", glyph="ADM")

T("App de fotos com IA", "Utilidades", "Reconhecimento de objetos, rostos e texto em fotos (offline).", [
    S("Analisar", "Analisar foto", [C("image", source="photo", height=260),
                                    C("button", text="Tirar foto", action="take_photo"),
                                    C("button", text="Escolher da galeria", action="pick_image", style="outlined"),
                                    C("text", text="Rótulos, rostos e texto são detectados no aparelho.", style="caption")],
      nav=True, icon="face"),
], ["camera_capture", "image_picker", "image_labeling", "face_detection", "ocr"], color="#6200EA", glyph="AI")


# ---------- Novos modelos (v1.1): usam carrossel, etapas, assinatura, preco e contatos
BARBERS = samples("barber", [
    ("Corte masculino", "40 min", 45.0), ("Barba completa", "30 min", 35.0), ("Corte + barba", "1 h", 70.0),
    ("Pigmentação", "45 min", 50.0), ("Sobrancelha", "15 min", 15.0)])
VET = samples("vet", [
    ("Consulta clínica", "Avaliação geral", 150.0), ("Vacina V10", "Cães", 90.0), ("Vacina antirrábica", "Cães e gatos", 60.0),
    ("Banho e tosa", "Porte médio", 80.0), ("Castração", "Agendamento prévio", 450.0)])
PACKAGES = samples("pack", [
    ("Fernando de Noronha", "5 noites - aéreo incluso", 5890.0), ("Gramado", "Fim de semana - café da manhã", 1290.0),
    ("Lisboa e Porto", "10 dias - roteiro guiado", 9990.0), ("Bonito", "4 dias - passeios inclusos", 2490.0),
    ("Cancún", "7 noites - all inclusive", 7490.0)])
COSMETICS = samples("cosm", [
    ("Sérum vitamina C", "Skincare - 30 ml", 89.9), ("Batom matte", "Maquiagem", 39.9), ("Protetor solar FPS 50", "Rosto", 64.9),
    ("Máscara capilar", "Cabelos - 250 g", 49.9), ("Perfume floral", "Fragrâncias - 50 ml", 189.0),
    ("Hidratante corporal", "Corpo - 400 ml", 34.9)])
FLOWERS = samples("flower", [
    ("Buquê de rosas", "12 rosas vermelhas", 149.0), ("Orquídea branca", "Vaso de cerâmica", 119.0),
    ("Girassóis", "Arranjo com 6 flores", 99.0), ("Cesta café da manhã", "Com flores do campo", 189.0),
    ("Suculentas", "Kit com 3 mini vasos", 59.0)])
BAKERY = samples("bake", [
    ("Pão de fermentação natural", "Sai às 7h", 22.0), ("Croissant de manteiga", "Unidade", 9.5),
    ("Bolo de cenoura", "Com cobertura de chocolate", 38.0), ("Pão de queijo", "Pacote com 10", 15.0),
    ("Torta de limão", "Fatia", 14.0), ("Sonho de creme", "Unidade", 7.0)])
CAR_SERVICES = samples("auto", [
    ("Troca de óleo", "Óleo sintético + filtro", 189.0), ("Alinhamento e balanceamento", "4 rodas", 120.0),
    ("Revisão completa", "Checklist com 40 itens", 450.0), ("Freios", "Pastilhas dianteiras", 260.0),
    ("Ar-condicionado", "Higienização", 150.0)])
LAUNDRY = samples("wash", [
    ("Lavar e passar", "Por kg", 18.0), ("Edredom casal", "Lavagem especial", 45.0), ("Terno", "Lavagem a seco", 60.0),
    ("Tênis", "Higienização", 40.0), ("Cortinas", "Por metro", 25.0)])
TRAINING = samples("train", [
    ("Treino A - Peito e tríceps", "45 min - intermediário"), ("Treino B - Costas e bíceps", "50 min - intermediário"),
    ("Treino C - Pernas", "60 min - avançado"), ("HIIT em casa", "20 min - sem equipamentos"),
    ("Mobilidade", "15 min - todos os níveis")])
MEALS = samples("meal", [
    ("Café da manhã", "Ovos mexidos, pão integral e fruta - 420 kcal"), ("Lanche", "Iogurte com granola - 220 kcal"),
    ("Almoço", "Frango, arroz integral e salada - 610 kcal"), ("Lanche da tarde", "Castanhas e maçã - 250 kcal"),
    ("Jantar", "Omelete com legumes - 380 kcal")])
SESSIONS = samples("session", [
    ("Sessão individual", "50 min - online ou presencial", 180.0), ("Terapia de casal", "80 min", 260.0),
    ("Avaliação inicial", "Primeira conversa", 0.0), ("Pacote mensal", "4 sessões", 640.0)])
LEGAL = samples("legal", [
    ("Direito do consumidor", "Cobranças indevidas e contratos"), ("Direito trabalhista", "Rescisões e acordos"),
    ("Família", "Divórcio, guarda e pensão"), ("Imobiliário", "Compra, venda e locação"),
    ("Empresarial", "Abertura de empresa e contratos")])
ACCOUNTING = samples("acc", [
    ("Guia DAS - março", "Vence em 20/04", 76.9), ("Pró-labore", "Recibo mensal", None), ("Folha de pagamento", "2 funcionários", None),
    ("Declaração IRPF", "Prazo até 31/05", None), ("Nota fiscal 1023", "Emitida para Cliente A", 1500.0)])
ROOMS = samples("room", [
    ("Estação compartilhada", "Diária - Wi-Fi e café", 49.0), ("Mesa fixa", "Mensal", 690.0),
    ("Sala de reunião 6 pessoas", "Por hora - TV e quadro", 80.0), ("Sala privativa", "Mensal - 4 lugares", 2400.0),
    ("Auditório", "Por período - 60 lugares", 900.0)])
TALKS = samples("talk", [
    ("Abertura", "09:00 - Auditório principal"), ("Kotlin no backend", "10:00 - Sala 1"),
    ("Design de apps acessíveis", "11:00 - Sala 2"), ("Painel: IA no dia a dia", "14:00 - Auditório"),
    ("Workshop de Compose", "15:30 - Laboratório"), ("Encerramento e sorteios", "17:30 - Auditório")])
MOVIES = samples("movie", [
    ("Aventura nas Estrelas", "Ficção - 2h10 - 12 anos", 32.0), ("O Último Verão", "Drama - 1h50 - 14 anos", 28.0),
    ("Risos em Família", "Comédia - 1h40 - Livre", 28.0), ("Sombras da Cidade", "Suspense - 2h - 16 anos", 32.0),
    ("Mundo Animado", "Animação - 1h35 - Livre", 24.0)])
CONTRACTS = samples("contract", [
    ("Prestação de serviços", "Cliente: Mercado Bom Preço"), ("Locação de equipamento", "Cliente: Studio Foto"),
    ("Manutenção mensal", "Cliente: Condomínio Jardim"), ("Termo de confidencialidade", "Fornecedor: TechSoft")])
DELIVERIES = samples("deliv", [
    ("Pedido 5821", "Rua das Flores, 120 - Centro"), ("Pedido 5822", "Av. Brasil, 900 - Jardim América"),
    ("Pedido 5823", "Rua 7 de Setembro, 45 - Vila Nova"), ("Pedido 5824", "Praça da Matriz, 10 - Centro")])
JOBS = samples("job", [
    ("Desenvolvedor Android", "Remoto - CLT", 9500.0), ("Designer UX/UI", "Híbrido - São Paulo", 7200.0),
    ("Analista de dados", "Remoto - PJ", 8800.0), ("Atendente", "Presencial - Campinas", 2100.0),
    ("Estágio em marketing", "Híbrido - Curitiba", 1600.0)])
ADOPTION = samples("adopt", [
    ("Thor", "Cão - 2 anos - porte médio"), ("Mia", "Gata - 1 ano - castrada"), ("Bolinha", "Cão - 4 meses - filhote"),
    ("Luna", "Gata - 3 anos - dócil"), ("Max", "Cão - 6 anos - companheiro")])

T("Barbearia", "Serviços", "Serviços com preços, agendamento de horário, fidelidade e contato pelo WhatsApp.", [
    S("Inicio", "Barbearia", home_header("Barbearia Navalha", "Agende seu horário em segundos") + [
        C("carousel", source="sample:barbers", item_action="navigate:Agendar"),
        C("price_tag", label="Corte + barba", value="R$ 70,00", old_value="R$ 80,00"),
        C("key_value", title="Funcionamento", rows="Seg a sex: 9h às 20h\nSábado: 8h às 18h\nDomingo: fechado"),
        C("social_links", whatsapp="5511999999999", instagram="barbearianavalha", website=""),
    ], nav=True, icon="home"),
    S("Agendar", "Agendar horário", [
        C("item_detail", show_price=True),
        C("date_picker", label="Data", key="date"),
        C("chips", key="time", options="09:00;10:00;11:00;14:00;15:00;16:00;17:00"),
        C("text_field", label="Seu nome", key="name", validation="required"),
        C("button", text="Confirmar horário", action="submit:Agenda && notify:Horário confirmado!"),
    ], form="Booking", icon="date"),
    list_screen("Agenda", "Meus horários", "entity:Booking", detail=None, icon="date", search=False),
    S("Fidelidade", "Fidelidade", [
        C("title", text="Cartão fidelidade", size="medium"),
        C("steps", options="1;2;3;4;5", current=3),
        C("alert", text="Faltam 2 cortes para ganhar um corte grátis.", kind="success"),
        C("qr_code", text="cliente-0001"),
    ], nav=True, icon="star"),
], ["notifications", "qr_generator", "skeleton_loading"], [E("Booking", "date:String, time:String, name:String")],
  sample_sets={"barbers": BARBERS}, color="#37474F", glyph="CUT")

T("Clínica veterinária", "Saúde e bem-estar", "Pets cadastrados, vacinas, agendamento de consulta e emergência.", [
    S("Inicio", "Clínica Vet", home_header("Clínica Patas & Cia", "Cuidado completo para seu pet",
                                           ("Vacinação em dia?", "Confira a carteira do seu pet")) + [
        C("h_list", source="sample:vet", item_action="navigate:Consulta", show_price=True),
        C("button_row", text1="Emergência", action1="call:1133334444", text2="Agendar", action2="navigate:Consulta"),
        C("key_value", title="Atendimento", rows="Clínica: 8h às 20h\nPlantão 24h: (11) 3333-4444"),
    ], nav=True, icon="home"),
    form_screen("Pet", "Cadastrar pet", [("Nome", "name", "text", "required"), ("Espécie", "species", "dropdown=Cão;Gato;Ave;Outro"),
                                         ("Raça", "breed"), ("Nascimento", "birth", "date")],
                entity="Pet", after="Pets", icon="face"),
    list_screen("Pets", "Meus pets", "entity:Pet", detail=None, icon="face", search=False, fab="navigate:Pet"),
    S("Consulta", "Agendar consulta", [
        C("item_detail", show_price=True),
        C("date_picker", label="Data", key="date"),
        C("dropdown", label="Período", key="period", options="Manhã;Tarde;Noite"),
        C("text_field", label="Sintomas ou observações", key="notes", input="multiline"),
        C("button", text="Agendar", action="submit:Inicio && toast:Consulta agendada!"),
    ], form="Appointment", icon="date"),
], ["notifications", "reminders"], [E("Pet", "name:String, species:String, breed:String, birth:String"),
                                    E("Appointment", "date:String, period:String, notes:String")],
  sample_sets={"vet": VET}, color="#26A69A", glyph="VET")

T("Agência de viagens", "Viagem e transporte", "Pacotes em destaque, detalhes com preço promocional e solicitação de orçamento.", [
    S("Inicio", "Viagens", home_header("Para onde vamos?", "Pacotes com tudo incluso") + [
        C("carousel", source="sample:packages", item_action="navigate:Pacote", height=200),
        C("title", text="Mais procurados", size="small"),
        C("list", source="sample:packages", item_action="navigate:Pacote", show_price=True),
    ], nav=True, icon="home"),
    S("Pacote", "Pacote", [
        C("item_detail", show_price=True),
        C("tags", options="Aéreo;Hotel;Traslado;Seguro"),
        C("expandable", title="O que está incluso", body="Passagens de ida e volta, hospedagem com café da manhã, traslados e seguro viagem."),
        C("expandable", title="Política de cancelamento", body="Cancelamento gratuito até 30 dias antes do embarque."),
        C("button_row", text1="Favoritar", action1="favorite", text2="Quero este", action2="navigate:Orcamento"),
    ], icon="place"),
    form_screen("Orcamento", "Pedir orçamento", [("Nome", "name", "text", "required"), ("E-mail", "email", "email", "email"),
                                                ("Data de ida", "date", "date"), ("Viajantes", "people", "stepper")],
                entity="Quote", after="Inicio", button="Enviar pedido"),
    list_screen("Favoritos", "Favoritos", "favorites", detail="Pacote", icon="favorite", search=False, price=True),
], ["favorites", "notifications", "image_share"], [E("Quote", "name:String, email:String, date:String, people:Int")],
  sample_sets={"packages": PACKAGES}, color="#0277BD", glyph="TRIP")

T("Loja de cosméticos", "Comércio", "Vitrine com carrossel, ofertas com preço antigo, carrinho e avaliações.", [
    S("Inicio", "Beleza", home_header("Beleza & Cuidado", "Frete grátis acima de R$ 150") + [
        C("carousel", source="sample:cosmetics", item_action="navigate:Detalhe"),
        C("tags", options="Skincare;Maquiagem;Cabelos;Perfumes"),
        C("grid", source="sample:cosmetics", item_action="navigate:Detalhe", show_price=True),
    ], nav=True, icon="home"),
    S("Detalhe", "Produto", [
        C("item_detail", show_price=True),
        C("price_tag", label="Leve 2 por", value="R$ 149,90", old_value="R$ 179,80"),
        C("rating", label="Avalie este produto", key="rating"),
        C("button", text="Adicionar ao carrinho", action="add_cart && toast:Adicionado!"),
        C("button", text="Favoritar", action="favorite", style="outlined"),
    ], icon="info"),
    cart_screen("Concluido"),
    done_screen("Concluido", "Pedido realizado!", "Você receberá o código de rastreio por e-mail.", "Inicio"),
    list_screen("Favoritos", "Favoritos", "favorites", icon="favorite", search=False, price=True),
], ["cart", "favorites", "skeleton_loading", "rate_prompt"], sample_sets={"cosmetics": COSMETICS},
  color="#D81B60", glyph="GLOW")

T("Floricultura", "Comércio", "Flores e presentes com mensagem no cartão, data de entrega e WhatsApp.", [
    list_screen("Inicio", "Flores", "sample:flowers", grid=True, price=True, icon="home",
                header=home_header("Floricultura Jardim", "Entrega no mesmo dia até 15h")),
    detail_screen(buttons=[("Presentear", "add_cart && navigate:Cartao")], price=True,
                  extra=[C("tags", options="Entrega hoje;Embalagem presente")]),
    S("Cartao", "Cartão e entrega", [
        C("text_field", label="Mensagem do cartão", key="message", input="multiline"),
        C("text_field", label="Nome de quem recebe", key="receiver", validation="required"),
        C("text_field", label="Endereço de entrega", key="address", validation="required"),
        C("date_picker", label="Data de entrega", key="date"),
        C("button", text="Ir para o carrinho", action="submit:Carrinho"),
    ], form="GiftCard", icon="edit"),
    cart_screen("Enviado"),
    done_screen("Enviado", "Presente a caminho!", "Avisaremos quando as flores forem entregues.", "Inicio"),
    S("Contato", "Contato", [C("social_links", whatsapp="5511988887777", instagram="floriculturajardim",
                                website="https://example.com"),
                             C("key_value", title="Loja", rows="Endereço: Rua das Hortênsias, 50\nHorário: 8h às 19h")],
      nav=True, icon="phone"),
], ["cart", "notifications"], [E("GiftCard", "message:String, receiver:String, address:String, date:String")],
  sample_sets={"flowers": FLOWERS}, color="#C2185B", glyph="FLOR")

T("Padaria artesanal", "Delivery e alimentação", "Encomendas com horário de retirada, fornadas do dia e fidelidade.", [
    S("Inicio", "Padaria", home_header("Padaria Fermento", "Fornadas fresquinhas todos os dias") + [
        C("alert", text="Pão de fermentação natural sai às 7h e às 16h.", kind="info"),
        C("h_list", source="sample:bakery", item_action="add_cart", show_price=True),
        C("title", text="Cardápio", size="small"),
        C("list", source="sample:bakery", item_action="add_cart", show_price=True),
    ], nav=True, icon="home"),
    cart_screen("Retirada"),
    form_screen("Retirada", "Horário de retirada", [("Nome", "name", "text", "required"),
                                                   ("Horário", "time", "dropdown=07:00;08:00;09:00;16:00;17:00")],
                entity="Pickup", after="Pronto", button="Confirmar encomenda"),
    done_screen("Pronto", "Encomenda confirmada!", "Seu pedido estará separado no horário escolhido.", "Inicio"),
    S("Fidelidade", "Fidelidade", [C("steps", options="1;2;3;4;5;6;7;8;9;10", current=6),
                                   C("text", text="A cada 10 compras, um café com bolo por nossa conta.", align="center"),
                                   C("qr_code", text="fidelidade-0001")], nav=True, icon="star"),
], ["cart", "qr_generator", "daily_reminder"], [E("Pickup", "name:String, time:String")],
  sample_sets={"bakery": BAKERY}, color="#8D6E63", glyph="PAO")

T("Oficina mecânica", "Serviços", "Serviços, orçamento com etapas do reparo, histórico do veículo e assinatura de aprovação.", [
    list_screen("Servicos", "Serviços", "sample:auto", price=True, icon="build", detail="Orcamento",
                header=home_header("Auto Center", "Orçamento sem compromisso")),
    S("Orcamento", "Orçamento", [
        C("item_detail", show_price=True),
        C("text_field", label="Placa do veículo", key="plate", validation="required"),
        C("text_field", label="Modelo", key="model"),
        C("signature", label="Assinatura de aprovação"),
        C("button", text="Aprovar orçamento", action="submit:Status"),
    ], form="ServiceOrder", icon="edit"),
    S("Status", "Andamento", [
        C("title", text="Seu veículo", size="medium"),
        C("steps", options="Recebido;Diagnóstico;Reparo;Pronto", current=2),
        C("alert", text="Estamos aguardando a chegada de uma peça.", kind="warning"),
        C("button_row", text1="Ligar", action1="call:1140004000", text2="WhatsApp", action2="whatsapp:5511940004000"),
    ], nav=True, icon="info"),
    list_screen("Historico", "Histórico", "entity:ServiceOrder", detail=None, icon="list", search=False),
], ["notifications", "csv_export"], [E("ServiceOrder", "plate:String, model:String")],
  sample_sets={"auto": CAR_SERVICES}, color="#455A64", glyph="AUTO")

T("Lavanderia", "Serviços", "Tabela de preços, coleta agendada e acompanhamento por etapas.", [
    S("Inicio", "Lavanderia", home_header("Lavanderia Bolha", "Coleta e entrega grátis") + [
        C("list", source="sample:laundry", show_price=True, item_action="add_cart"),
        C("cart_summary", action="checkout:Coleta", button="Agendar coleta"),
    ], nav=True, icon="home"),
    form_screen("Coleta", "Agendar coleta", [("Endereço", "address", "text", "required"), ("Data", "date", "date"),
                                            ("Período", "period", "dropdown=Manhã;Tarde")],
                entity="Pickup", after="Acompanhar", button="Confirmar coleta"),
    S("Acompanhar", "Acompanhar", [C("steps", options="Coletado;Lavando;Passando;Entrega", current=1),
                                   C("text", text="Avisaremos por notificação a cada etapa.", style="caption"),
                                   C("button", text="Falar com a loja", action="whatsapp:5511977776666", style="outlined")],
      nav=True, icon="check"),
], ["cart", "notifications"], [E("Pickup", "address:String, date:String, period:String")],
  sample_sets={"laundry": LAUNDRY}, color="#039BE5", glyph="WASH")

T("Personal trainer", "Saúde e bem-estar", "Treinos do aluno, cronômetro de descanso, registro e contato com o personal.", [
    S("Hoje", "Treino de hoje", [
        C("title", text="Bora treinar!"),
        C("stat_card", label="Sequência de dias", value="5"),
        C("carousel", source="sample:training", item_action="navigate:Treino", height=160),
        C("quote", text="Disciplina é fazer o que precisa ser feito, mesmo sem vontade.", author="Seu personal"),
    ], nav=True, icon="home"),
    S("Treino", "Treino", [C("item_detail", show_image=False), C("timer", mode="countdown", seconds=60),
                           C("checkbox", label="Treino concluído", key="done"),
                           C("button", text="Registrar", action="submit:Hoje && vibrate && toast:Mandou bem!")],
      form="WorkoutLog", icon="play"),
    list_screen("Historico", "Histórico", "entity:WorkoutLog", detail=None, icon="date", search=False),
    S("Contato", "Personal", [C("avatar", name="Rafa Personal", subtitle="CREF 000000-G/SP"),
                              C("social_links", whatsapp="5511966665555", instagram="rafapersonal", website="")],
      nav=True, icon="person"),
], ["timer", "vibration", "daily_reminder"], [E("WorkoutLog", "done:Boolean")],
  sample_sets={"training": TRAINING}, color="#F4511E", glyph="FIT")

T("Nutricionista", "Saúde e bem-estar", "Plano alimentar do paciente, metas de água e macros, e retorno agendado.", [
    S("Plano", "Plano alimentar", [
        C("title", text="Seu plano de hoje", size="medium"),
        C("key_value", title="Metas diárias", rows="Calorias: 1.900 kcal\nProteínas: 140 g\nÁgua: 2,5 L"),
        C("list", source="sample:meals", show_image=False),
        C("alert", text="Lembre-se de beber água a cada 2 horas.", kind="info"),
    ], nav=True, icon="list"),
    form_screen("Diario", "Diário alimentar", [("Refeição", "meal", "dropdown=Café;Almoço;Lanche;Jantar"),
                                              ("O que comeu", "food", "multiline"), ("Fome antes (0 a 10)", "hunger", "slider")],
                entity="FoodLog", after="Registros", icon="edit", nav=True),
    list_screen("Registros", "Registros", "entity:FoodLog", detail=None, icon="date", search=False),
    S("Retorno", "Retorno", [C("expandable", title="Como se preparar", body="Traga seus exames recentes e anote dúvidas."),
                             C("date_picker", label="Data do retorno", key="date"),
                             C("button", text="Solicitar retorno", action="whatsapp:5511955554444")],
      nav=True, icon="date"),
], ["daily_reminder", "notifications"], [E("FoodLog", "meal:String, food:String, hunger:Float")],
  sample_sets={"meals": MEALS}, color="#7CB342", glyph="NUTRI")

T("Psicólogo", "Saúde e bem-estar", "Agendamento discreto de sessões, diário de emoções e app protegido por biometria.", [
    S("Inicio", "Bem-estar", home_header("Olá! Como você está hoje?", "Seu espaço seguro") + [
        C("h_list", source="sample:sessions", item_action="navigate:Agendar", show_price=True),
        C("quote", text="Cuidar da mente é um ato de coragem.", author=""),
        C("button", text="Registrar como me sinto", action="navigate:Diario", style="tonal"),
    ], nav=True, icon="home"),
    S("Agendar", "Agendar sessão", [C("item_detail", show_price=True), C("date_picker", label="Data", key="date"),
                                    C("radio_group", label="Modalidade", key="mode", options="Online;Presencial"),
                                    C("button", text="Solicitar horário", action="submit:Inicio && toast:Pedido enviado!")],
      form="Session", icon="date"),
    form_screen("Diario", "Diário de emoções", [("Humor", "mood", "rating"), ("O que aconteceu hoje?", "text", "multiline")],
                entity="Mood", after="Historico", icon="face", nav=True),
    list_screen("Historico", "Histórico", "entity:Mood", detail=None, icon="list", search=False),
], ["app_lock", "secure_screen", "notifications"], [E("Session", "date:String, mode:String"),
                                                   E("Mood", "mood:Int, text:String")],
  sample_sets={"sessions": SESSIONS}, color="#5E35B1", glyph="PSI")

T("Escritório de advocacia", "Negócios", "Áreas de atuação, triagem do caso, envio de documentos e acompanhamento.", [
    S("Inicio", "Advocacia", home_header("Silva & Associados", "Atendimento jurídico humanizado") + [
        C("list", source="sample:legal", item_action="navigate:Consulta", show_image=False),
        C("social_links", whatsapp="5511944443333", instagram="", website="https://example.com"),
    ], nav=True, icon="home"),
    S("Consulta", "Triagem do caso", [
        C("item_detail", show_image=False),
        C("text_field", label="Descreva seu caso", key="description", input="multiline", validation="required"),
        C("button", text="Anexar documento (PDF)", action="pick_file", style="outlined"),
        C("checkbox", label="Concordo com a política de privacidade", key="privacy"),
        C("button", text="Enviar", action="submit:Processos"),
    ], form="LegalCase", icon="edit"),
    S("Processos", "Meus processos", [
        C("steps", options="Triagem;Análise;Protocolo;Decisão", current=2),
        C("list", source="entity:LegalCase", show_image=False, empty_text="Nenhum caso enviado"),
    ], nav=True, icon="list"),
], ["document_picker", "upload", "secure_prefs"], [E("LegalCase", "description:String, privacy:Boolean")],
  sample_sets={"legal": LEGAL}, color="#263238", glyph="LAW")

T("Contabilidade", "Negócios", "Guias e prazos do cliente, envio de notas, exportação e alertas de vencimento.", [
    S("Painel", "Painel", [
        C("title", text="Sua empresa em dia", size="medium"),
        C("alert", text="A guia DAS vence em 5 dias.", kind="warning"),
        C("stat_card", label="Faturamento do mês", value="R$ 18.400"),
        C("chart", style="bar", values="12,15,14,18,16,18"),
    ], nav=True, icon="home"),
    list_screen("Documentos", "Documentos", "sample:accounting", detail=None, icon="list", price=True,
                fab="pick_file"),
    S("Enviar", "Enviar nota", [C("text", text="Envie notas e comprovantes em PDF ou imagem."),
                                C("button_row", text1="Arquivo", action1="pick_file", text2="Foto", action2="take_photo"),
                                C("button", text="Exportar lista (CSV)", action="export_csv", style="outlined")],
      nav=True, icon="send"),
], ["document_picker", "camera_capture", "csv_export", "reminders"], sample_sets={"accounting": ACCOUNTING},
  color="#1565C0", glyph="CONT")

T("Coworking", "Negócios", "Reserva de estações e salas, check-in por QR Code e regras do espaço.", [
    list_screen("Espacos", "Espaços", "sample:rooms", detail="Reservar", price=True, icon="home",
                header=home_header("Cowork Central", "Wi-Fi rápido, café e boas conexões")),
    S("Reservar", "Reservar", [C("item_detail", show_price=True), C("date_picker", label="Data", key="date"),
                               C("chips", key="slot", options="Manhã;Tarde;Dia inteiro"),
                               C("button", text="Reservar", action="submit:Reservas && notify:Reserva confirmada")],
      form="Reservation", icon="date"),
    list_screen("Reservas", "Minhas reservas", "entity:Reservation", detail=None, icon="date", search=False),
    S("Checkin", "Check-in", [C("qr_code", text="cowork-membro-0001"),
                              C("expandable", title="Regras do espaço", body="Silêncio nas estações compartilhadas. "
                                                                              "Reuniões apenas nas salas."),
                              C("key_value", title="Wi-Fi", rows="Rede: Cowork\nSenha: conecte2024")],
      nav=True, icon="check"),
], ["qr_generator", "notifications", "offline_banner"], [E("Reservation", "date:String, slot:String")],
  sample_sets={"rooms": ROOMS}, color="#00897B", glyph="WORK")

T("Conferência / evento", "Entretenimento", "Programação, palestras, ingresso com QR Code, mapa e avaliação.", [
    S("Inicio", "Evento", home_header("DevConf 2026", "15 de outubro - Centro de Convenções",
                                      ("Faltam 30 dias", "Garanta seu ingresso")) + [
        C("carousel", source="sample:talks", item_action="navigate:Palestra", height=150),
        C("button", text="Ver programação completa", action="navigate:Agenda", style="tonal"),
    ], nav=True, icon="home"),
    list_screen("Agenda", "Programação", "sample:talks", detail="Palestra", icon="date",
                chips="Todas;Auditório;Sala 1;Sala 2"),
    S("Palestra", "Palestra", [C("item_detail", show_image=False),
                               C("button_row", text1="Favoritar", action1="favorite", text2="Avaliar", action2="navigate:Avaliar")],
      icon="info"),
    form_screen("Avaliar", "Avaliar palestra", [("Nota", "rating", "rating"), ("Comentário", "comment", "multiline")],
                entity="Feedback", after="Agenda", button="Enviar avaliação"),
    S("Ingresso", "Meu ingresso", [C("qr_code", text="DEVCONF-2026-000123"), C("tags", options="Acesso total;Workshop"),
                                   C("map_view", title="Centro de Convenções")], nav=True, icon="star"),
], ["favorites", "qr_generator", "maps", "whats_new"], [E("Feedback", "rating:Int, comment:String")],
  sample_sets={"talks": TALKS}, color="#3949AB", glyph="CONF")

T("Cinema", "Entretenimento", "Filmes em cartaz, sessões, escolha de assentos e combos com preço promocional.", [
    S("Cartaz", "Em cartaz", [C("carousel", source="sample:movies", item_action="navigate:Filme", height=220),
                              C("grid", source="sample:movies", item_action="navigate:Filme", show_price=True)],
      nav=True, icon="play"),
    S("Filme", "Filme", [C("item_detail", show_price=True), C("tags", options="Dublado;Legendado;3D"),
                         C("chips", key="session", options="14:00;16:30;19:00;21:30"),
                         C("stepper", label="Ingressos", key="tickets", max=10),
                         C("button", text="Comprar", action="add_cart && navigate:Combos")], icon="info"),
    S("Combos", "Combos", [C("price_tag", label="Pipoca grande + 2 refrigerantes", value="R$ 39,90", old_value="R$ 52,00"),
                           C("button_row", text1="Pular", action1="navigate:Carrinho", text2="Adicionar", action2="navigate:Carrinho")],
      icon="star"),
    cart_screen("Pronto"),
    done_screen("Pronto", "Ingressos garantidos!", "Apresente o QR Code na entrada da sala.", "Cartaz"),
], ["cart", "qr_generator", "skeleton_loading"], sample_sets={"movies": MOVIES}, color="#B71C1C", glyph="CINE")

T("Contratos com assinatura", "Negócios", "Contratos com cliente, resumo, assinatura na tela e compartilhamento.", [
    list_screen("Contratos", "Contratos", "sample:contracts", detail="Contrato", icon="list", fab="navigate:Novo"),
    S("Contrato", "Contrato", [C("item_detail", show_image=False),
                               C("key_value", title="Resumo", rows="Vigência: 12 meses\nValor mensal: R$ 1.200,00\nReajuste: IPCA"),
                               C("expandable", title="Cláusulas principais",
                                 body="O contratado prestará os serviços descritos com qualidade e no prazo acordado."),
                               C("signature", label="Assinatura do cliente", height=200),
                               C("button", text="Concluir e compartilhar", action="share_item && toast:Contrato assinado")],
      icon="edit"),
    form_screen("Novo", "Novo contrato", [("Título", "title", "text", "required"), ("Cliente", "client", "text", "required"),
                                         ("Valor", "value", "number"), ("Início", "start", "date")],
                entity="Contract", after="Contratos"),
], ["image_share", "secure_prefs"], [E("Contract", "title:String, client:String, value:Double, start:String")],
  sample_sets={"contracts": CONTRACTS}, color="#283593", glyph="SIGN")

T("Entregas com comprovante", "Viagem e transporte", "Rota do entregador, navegação, foto e assinatura do recebedor.", [
    list_screen("Entregas", "Entregas do dia", "sample:deliveries", detail="Entrega", icon="list",
                header=[C("steps", options="Separação;Em rota;Concluído", current=2)]),
    S("Entrega", "Entrega", [C("item_detail", show_image=False),
                             C("button_row", text1="Abrir no mapa", action1="open_map", text2="Ligar", action2="call:11999990000"),
                             C("image", source="photo", height=180),
                             C("button", text="Foto do pacote entregue", action="take_photo", style="outlined"),
                             C("text_field", label="Nome de quem recebeu", key="receiver", validation="required"),
                             C("signature", label="Assinatura do recebedor"),
                             C("button", text="Confirmar entrega", action="submit:Entregas && share_location")],
      form="Proof", icon="check"),
], ["camera_capture", "location", "offline_banner"], [E("Proof", "receiver:String")],
  sample_sets={"deliveries": DELIVERIES}, color="#EF6C00", glyph="POD", nav="stack")

T("Vagas de emprego", "Negócios", "Vagas com salário, filtros, candidatura com currículo em PDF e status.", [
    list_screen("Vagas", "Vagas", "sample:jobs", detail="Vaga", price=True, icon="home",
                chips="Todas;Remoto;Híbrido;Presencial"),
    S("Vaga", "Vaga", [C("item_detail", show_image=False, show_price=True), C("tags", options="Vale-refeição;Plano de saúde;Home office"),
                       C("expandable", title="Requisitos", body="Experiência na área, boa comunicação e vontade de aprender."),
                       C("button_row", text1="Salvar", action1="favorite", text2="Candidatar-se", action2="navigate:Candidatura")],
      icon="info"),
    S("Candidatura", "Candidatura", [C("text_field", label="Nome completo", key="name", validation="required"),
                                     C("text_field", label="E-mail", key="email", input="email", validation="email"),
                                     C("button", text="Anexar currículo (PDF)", action="pick_file", style="outlined"),
                                     C("button", text="Enviar candidatura", action="submit:Status")],
      form="Application", icon="send"),
    S("Status", "Minhas candidaturas", [C("steps", options="Enviada;Triagem;Entrevista;Proposta", current=1),
                                        C("list", source="entity:Application", show_image=False)], nav=True, icon="check"),
    list_screen("Salvas", "Vagas salvas", "favorites", detail="Vaga", icon="favorite", search=False, price=True),
], ["favorites", "document_picker", "upload"], [E("Application", "name:String, email:String")],
  sample_sets={"jobs": JOBS}, color="#00695C", glyph="JOBS")

T("Adoção de pets", "Social e comunicação", "Animais para adoção, ficha do pet, formulário de interesse e contato com a ONG.", [
    S("Inicio", "Adote", home_header("Adote um amigo", "Todos vacinados e castrados") + [
        C("carousel", source="sample:adoption", item_action="navigate:Pet"),
        C("grid", source="sample:adoption", item_action="navigate:Pet"),
    ], nav=True, icon="home"),
    S("Pet", "Conheça", [C("item_detail"), C("tags", options="Vacinado;Castrado;Vermifugado"),
                         C("button_row", text1="Favoritar", action1="favorite", text2="Quero adotar", action2="navigate:Interesse")],
      icon="face"),
    form_screen("Interesse", "Quero adotar", [("Nome", "name", "text", "required"), ("Telefone", "phone", "phone", "phone"),
                                             ("Tipo de moradia", "home", "dropdown=Casa;Apartamento;Sítio"),
                                             ("Tem outros pets?", "others", "switch")],
                entity="AdoptionRequest", after="Inicio", button="Enviar interesse"),
    S("Ong", "A ONG", [C("text", text="Somos voluntários dedicados a resgatar e encontrar lares para animais."),
                       C("social_links", whatsapp="5511933332222", instagram="adotepatinhas", website="https://example.com"),
                       C("button", text="Doar", action="open_url:https://example.com/doar")], nav=True, icon="favorite"),
], ["favorites", "image_share"], [E("AdoptionRequest", "name:String, phone:String, home:String, others:Boolean")],
  sample_sets={"adoption": ADOPTION}, color="#FF7043", glyph="ADOT")


# ------------------------------------------------------------------ API publica

def categories():
    result = []
    for t in TEMPLATES:
        if t["category"] not in result:
            result.append(t["category"])
    return result


def find(name):
    for t in TEMPLATES:
        if t["name"] == name:
            return t
    return None


def build_project(template, name=None, package=None):
    """Cria um Project independente a partir de um modelo."""
    t = copy.deepcopy(template)
    project = Project()
    project.name = name or t["name"]
    if package:
        project.package = package
    project.description = t["description"]
    project.template = t["name"]
    project.navigation = t["navigation"]
    project.primary_color = t["color"]
    project.features = list(dict.fromkeys(t["features"]))
    project.entities = t["entities"]
    project.apis = t["apis"]
    project.samples = dict(t["samples"])
    project.samples.setdefault("default", DEFAULT)
    for screen in t["screens"]:
        screen.id = new_id("s")
        for comp in screen.components:
            comp.id = new_id()
    # Remove telas duplicadas (mesmo nome) mantendo a primeira.
    seen, screens = set(), []
    for screen in t["screens"]:
        if screen.name not in seen:
            seen.add(screen.name)
            screens.append(screen)
    project.screens = screens
    project.start_screen = t["start"]
    return project
