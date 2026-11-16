# DroidBlocks Studio

Construtor **no-code** de aplicativos Android em **Kotlin**, para Windows, macOS e Linux, que funciona **100% offline**.
Você monta as telas encaixando blocos, ativa funcionalidades com um clique e o DroidBlocks gera um projeto completo,
pronto para abrir no **Android Studio**.

## O que o projeto gerado contém

- Gradle em Kotlin DSL (`settings.gradle.kts`, `build.gradle.kts`, `app/build.gradle.kts`), catálogo de versões
  (`gradle/libs.versions.toml`), `gradle.properties`, wrapper do Gradle (`gradlew`, `gradlew.bat` e `.jar`) e regras do ProGuard.
- `REQUIREMENTS.md` e `requirements.txt` com todas as dependências, plugins, versões e permissões; `README.md` do app.
- `AndroidManifest.xml` com permissões, serviços, receivers e providers das funcionalidades ativas.
- Interface em **Jetpack Compose (Material 3)** ou **XML Views com ViewBinding**, à sua escolha.
- Arquitetura MVVM: um `ViewModel` com `StateFlow` por tela, repositório único e container de dependências.
- Banco local com **Room** (entidades, DAOs com CRUD, banco) e APIs REST com **Retrofit + OkHttp + Gson**.
- Navegação (pilha, barra inferior ou menu lateral), tema com a sua paleta (claro/escuro), ícone adaptativo,
  `strings.xml` com tradução, testes unitários e instrumentados.
- Todo o código é comentado em português, sem emojis.

## Versão 1.1

- 12 blocos novos: carrossel, lista horizontal, seção expansível, tabela rótulo/valor, etapas, aviso colorido,
  dois botões lado a lado, assinatura, citação, etiquetas, preço com desconto e links sociais.
- Ações encadeadas e 9 ações novas (excluir item, limpar formulário, exportar CSV, abrir no mapa, WhatsApp,
  enviar localização, abrir ajustes, escolher arquivo, relatar problema).
- 15 funcionalidades novas: bloqueio por biometria, listas offline, aviso de sem conexão, Material You,
  carregamento skeleton, upload multipart, seletor de documentos, relatar problema chacoalhando, lembrete diário,
  preferências criptografadas, configuração por JSON, novidades da versão, pedido de avaliação inteligente,
  acessibilidade e compartilhamento de imagens.
- 20 algoritmos novos (SM-2, Elo, geohash, ponto em polígono, Douglas-Peucker, NPS, pace, TDEE, estoque, ROI...).
- 20 modelos novos (barbearia, veterinária, agência de viagens, cinema, contratos com assinatura, vagas...).
- Prévia visual, mapa de navegação, biblioteca de telas prontas, atalhos de teclado e compilação do APK.

## Recursos do construtor

| Item | Quantidade |
|------|-----------|
| Blocos visuais (texto, botões, campos, listas, grades, carrossel, etapas, assinatura, mapas, QR Code, gráficos...) | 49 |
| Funcionalidades (câmera, GPS, notificações, login, carrinho, Firebase, ML Kit, biometria, modo offline...) | 123 |
| Algoritmos prontos em Kotlin, com testes (ordenação, grafos, Dijkstra, A*, finanças, saúde, geohash...) | 84 |
| Modelos de aplicativos (delivery, loja, clima, finanças, saúde, educação, transporte, serviços...) | 142 |
| APIs públicas prontas, sem chave (FakeStore, DummyJSON, Open-Meteo, CoinGecko...) | 22 |
| Ações para botões e listas (navegar, salvar, chamar API, carrinho, câmera, WhatsApp, CSV...) | 46 |
| Telas prontas para inserir (login, vitrine, planos, FAQ, contato, assinatura...) | 18 |

Outras ferramentas:

- **Assistente de novo projeto**: nome, pacote, Compose ou XML, navegação, SDK, paleta, tema, idiomas e recursos iniciais.
- **Montagem por blocos**: arraste da paleta para o celular, reordene arrastando, clique para editar propriedades.
- **Prévia visual**: alterne entre os blocos e uma prévia parecida com o app final (Ctrl+P).
- **Ações em sequência**: um botão pode executar várias ações em ordem (ex.: salvar, notificar e abrir outra tela).
- **Mapa de navegação** (Ctrl+M): mostra como as telas se ligam e destaca telas inacessíveis.
- **Telas prontas**: insira telas completas (login, vitrine, planos, FAQ, contato, termo com assinatura...).
- **Integração automática**: ao usar um bloco ou ação, as funcionalidades, bibliotecas e permissões necessárias são
  adicionadas sozinhas. O botão **Organizar** corrige referências, cria telas que faltam e ordena o projeto.
- **Editor de APIs**: endpoints, modelos, parâmetros e mapeamento para listas. Importa modelos a partir de um JSON de exemplo.
- **Editor de banco de dados**: entidades com campos tipados e geração automática de telas de lista e cadastro.
- **Diagnóstico** em tempo real, **pré-visualização do código** de cada tela e do projeto inteiro.
- Desfazer/refazer, copiar/colar blocos, salvamento automático e projetos recentes.
- **Compilar APK** e **Abrir no Android Studio** direto da janela de geração (detecta Android Studio, SDK e JDK).
- Linha de comando para gerar projetos sem abrir a interface.

## Requisitos

- **Python 3.9 ou superior** com **Tkinter** (não há outras dependências).
  - Windows: instalador oficial de https://www.python.org (já inclui Tkinter; marque "Add python.exe to PATH").
  - macOS: instalador oficial de https://www.python.org, ou `brew install python-tk`.
  - Linux: `sudo apt install python3 python3-tk` (Debian/Ubuntu), `sudo dnf install python3-tkinter` (Fedora).
- Para compilar os apps gerados: Android Studio (versão estável atual), que já traz o JDK.

## Instalação

| Sistema | Como instalar |
|---------|---------------|
| Windows | Dê duplo clique em `install.bat` |
| macOS | Dê duplo clique em `install.command` (ou rode `./install.sh` no Terminal) |
| Linux | Rode `./install.sh` |

O instalador gráfico copia o aplicativo, cria atalho no menu do sistema, na área de trabalho e o comando
`droidblocks` no terminal. Para desinstalar, use o botão **Desinstalar** do instalador ou rode `uninstall.py`
na pasta de instalação. Seus projetos `.dbp` são mantidos.

Instalação sem interface: `python installer/installer.py --silent [--dir PASTA] [--no-desktop]`.

Para usar sem instalar: `run.bat` (Windows) ou `./run.sh` (macOS/Linux), ou `python main.py`.

### Executável independente (opcional)

Para distribuir sem exigir Python, gere um executável em cada sistema com o PyInstaller:

```
pip install pyinstaller
python installer/build_executable.py
```

- Windows: `dist/DroidBlocksStudio.exe` e, se o Inno Setup 6 estiver instalado, `dist/DroidBlocksStudio-Setup.exe`
  (script em `installer/windows/setup.iss`).
- macOS: `dist/DroidBlocks Studio.app` e uma imagem `.dmg`.
- Linux: binário único, pacote `.tar.gz` e pacote `.deb` (se `dpkg-deb` existir).

## Uso rápido

1. Abra o DroidBlocks e siga o assistente (ou escolha um dos 142 modelos).
2. Arraste blocos para o celular, configure as propriedades e as ações à direita.
3. Ative funcionalidades e algoritmos na aba da esquerda; cadastre APIs e entidades nos botões da barra.
4. Clique em **Gerar projeto**. Abra a pasta gerada no Android Studio (**File > Open**) e execute.

## Linha de comando

```
python main.py --list-templates
python main.py --template "Loja online" --out ./saida --package com.minhaempresa.loja
python main.py --template "Clima" --out ./saida --views --zip
python main.py --generate meuapp.dbp --out ./saida
```

## Atalhos do editor

| Atalho | Ação |
|--------|------|
| Ctrl+N / Ctrl+O / Ctrl+S | Novo, abrir, salvar |
| Ctrl+Z / Ctrl+Y | Desfazer, refazer |
| Ctrl+D / Delete | Duplicar, excluir bloco |
| Ctrl+C / Ctrl+V | Copiar, colar bloco |
| Ctrl+G | Gerar projeto |
| Ctrl+P | Alternar blocos e prévia |
| Ctrl+M | Mapa de navegação |
| Setas para cima/baixo | Selecionar bloco anterior/seguinte |
| Alt+setas | Mover o bloco selecionado |
| F5 | Validar |

No macOS use Cmd no lugar de Ctrl.

## Observações sobre os projetos gerados

- A primeira sincronização do Gradle no Android Studio baixa as bibliotecas (exige internet uma vez).
- As versões padrão formam uma combinação testada (AGP 8.7.3, Kotlin 2.0.21, Compose BOM 2024.12.01).
  Podem ser alteradas em **Mais > Configurações e versões** ou depois no `libs.versions.toml`.
- Google Maps exige uma chave (`MAPS_API_KEY` em `local.properties`); funcionalidades Firebase exigem
  `app/google-services.json`. O diagnóstico avisa quando isso é necessário.

## Estrutura deste repositório

```
main.py                     Ponto de entrada (interface e linha de comando)
droidblocks/catalog/        Blocos, funcionalidades, algoritmos, modelos, APIs e versões
droidblocks/core/           Modelo do projeto, resolvedor de dependências e gerador de código
droidblocks/ui/             Interface Tkinter (tema preto e azul)
droidblocks/assets/         Wrapper do Gradle incluído nos projetos
installer/                  Instalador gráfico, build de executáveis e Inno Setup
tests/                      Testes do gerador
```


