"""Biblioteca de telas prontas para inserir em qualquer projeto.

Cada item gera telas novas (com blocos ja configurados). As acoes apontam para
nomes de tela comuns; o botao Organizar cria as telas que faltarem.
"""

from .templates import (C, S, login_screens, list_screen, detail_screen, form_screen, profile_screen,
                        settings_screen, cart_screen, done_screen, chat_screen, dashboard_screen, about_screen,
                        home_header)


def _faq():
    return [S("Ajuda", "Perguntas frequentes", [
        C("title", text="Como podemos ajudar?", size="medium"),
        C("expandable", title="Como faço um pedido?", body="Escolha os itens, adicione ao carrinho e finalize."),
        C("expandable", title="Quais as formas de pagamento?", body="Cartão, Pix e dinheiro na entrega."),
        C("expandable", title="Posso cancelar?", body="Sim, enquanto o pedido não tiver saído para entrega."),
        C("button", text="Falar com o suporte", action="email:suporte@exemplo.com", style="outlined"),
    ], icon="info")]


def _contact():
    return [S("Contato", "Contato", [
        C("title", text="Fale conosco", size="medium"),
        C("key_value", title="Atendimento", rows="Segunda a sexta: 9h às 18h\nSábado: 9h às 13h"),
        C("social_links", whatsapp="5511999999999", instagram="seuperfil", website="https://example.com"),
        C("button_row", text1="Ligar", action1="call:11999999999", text2="Como chegar", action2="open_map:Avenida Paulista, 1000"),
    ], nav=True, icon="phone")]


def _tracking():
    return [S("Acompanhar", "Acompanhar pedido", [
        C("steps", options="Recebido;Preparando;A caminho;Entregue", current=2),
        C("alert", text="Seu pedido saiu para entrega.", kind="success"),
        C("key_value", title="Resumo", rows="Pedido: #1024\nPrevisão: 30 min\nPagamento: Pix"),
        C("button", text="Falar com o entregador", action="whatsapp:5511999999999", style="outlined"),
    ], icon="place")]


def _plans():
    return [S("Planos", "Planos", [
        C("title", text="Escolha seu plano", size="medium"),
        C("card", title="Básico", body="Recursos essenciais para começar."),
        C("price_tag", label="Por mês", value="R$ 19,90", old_value=""),
        C("card", title="Premium", body="Tudo liberado, sem anúncios e com suporte prioritário."),
        C("price_tag", label="Por mês", value="R$ 39,90", old_value="R$ 49,90"),
        C("button", text="Assinar o Premium", action="navigate:Pagamento"),
    ], icon="star")]


def _showcase():
    return [S("Vitrine", "Vitrine", home_header("Destaques", "Novidades da semana") + [
        C("carousel", source="sample:default", item_action="navigate:Detalhe"),
        C("title", text="Mais vendidos", size="small"),
        C("h_list", source="sample:default", item_action="navigate:Detalhe", show_price=True),
        C("title", text="Para você", size="small"),
        C("grid", source="sample:default", item_action="navigate:Detalhe", show_price=True),
    ], nav=True, icon="home")]


def _signature():
    return [S("Assinatura", "Termo e assinatura", [
        C("expandable", title="Termo de responsabilidade", body="Declaro que li e concordo com as condições."),
        C("checkbox", label="Li e concordo", key="agree"),
        C("text_field", label="Nome completo", key="name", validation="required"),
        C("signature", label="Assine abaixo"),
        C("button", text="Confirmar", action="submit: && toast:Assinatura registrada"),
    ], icon="edit")]


def _onboarding():
    return [S("Boas-vindas", "Bem-vindo", [
        C("spacer", height=24),
        C("image", url="https://picsum.photos/seed/welcome/600/400", height=200),
        C("title", text="Tudo o que você precisa em um só lugar", align="center"),
        C("text", text="Organize, acompanhe e receba avisos no momento certo.", align="center", style="caption"),
        C("steps", options="Conheça;Personalize;Comece", current=1),
        C("button", text="Começar", action="finish_onboarding:Inicio"),
    ], icon="star")]


def _reviews():
    return [S("Avaliacoes", "Avaliações", [
        C("stat_card", label="Nota média", value="4,8"),
        C("quote", text="Atendimento excelente e entrega super rápida!", author="Mariana"),
        C("quote", text="Uso todos os dias, recomendo.", author="João"),
        C("rating", label="Sua avaliação", key="rating"),
        C("text_field", label="Comentário", key="comment", input="multiline"),
        C("button", text="Enviar avaliação", action="submit: && toast:Obrigado pela avaliação!"),
    ], icon="star")]


# (nome, descricao, funcao que devolve as telas)
PRESETS = [
    ("Login e cadastro", "Entrar com e-mail e senha, e criar conta.", lambda: login_screens("Inicio")),
    ("Boas-vindas", "Tela de apresentação com etapas e botão Começar.", _onboarding),
    ("Vitrine com carrossel", "Carrossel de destaques, lista horizontal e grade.", _showcase),
    ("Lista com busca", "Busca, filtros e lista que abre o detalhe.",
     lambda: [list_screen("Lista", "Itens", "sample:default", chips="Todos;Novos;Promoções")]),
    ("Detalhe do item", "Imagem, título, preço e botões de ação.",
     lambda: [detail_screen(buttons=[("Adicionar ao carrinho", "add_cart"), ("Favoritar", "favorite", "outlined")],
                            price=True)]),
    ("Formulário de contato", "Nome, e-mail e mensagem com validação.",
     lambda: [form_screen("Mensagem", "Envie uma mensagem", [("Nome", "name", "text", "required"),
                                                             ("E-mail", "email", "email", "email"),
                                                             ("Mensagem", "message", "multiline", "required")],
                          button="Enviar")]),
    ("Carrinho e confirmação", "Carrinho com total e tela de pedido concluído.",
     lambda: [cart_screen("Concluido"), done_screen("Concluido", "Pedido realizado!", "Obrigado pela compra.", "Inicio")]),
    ("Acompanhar pedido", "Etapas do pedido, aviso e resumo.", _tracking),
    ("Planos e preços", "Cartões de planos com preço promocional.", _plans),
    ("Perguntas frequentes", "Seções expansíveis e contato com o suporte.", _faq),
    ("Contato e redes sociais", "Horário, WhatsApp, Instagram e mapa.", _contact),
    ("Termo com assinatura", "Aceite de termo e assinatura na tela.", _signature),
    ("Avaliações", "Nota média, depoimentos e formulário de avaliação.", _reviews),
    ("Perfil", "Avatar, dados da conta e sair.", lambda: [profile_screen("Login")]),
    ("Ajustes", "Notificações, tema e idioma.", lambda: [settings_screen()]),
    ("Chat", "Mensagens com campo de envio.", lambda: [chat_screen()]),
    ("Painel com gráfico", "Indicadores e gráfico de barras.",
     lambda: [dashboard_screen("Painel", "Resumo", [("Vendas hoje", "R$ 1.250"), ("Pedidos", "18")])]),
    ("Sobre o app", "Descrição e botão de compartilhar.", lambda: [about_screen("Meu App", "Feito com DroidBlocks.")]),
]
