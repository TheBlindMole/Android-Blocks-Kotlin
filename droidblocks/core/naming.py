"""Funcoes de nomenclatura e escape usadas pelo gerador de codigo."""

import re
import unicodedata

# Palavras reservadas do Kotlin que nao podem ser usadas como identificadores.
KOTLIN_KEYWORDS = {
    "as", "break", "class", "continue", "do", "else", "false", "for", "fun", "if",
    "in", "interface", "is", "null", "object", "package", "return", "super", "this",
    "throw", "true", "try", "typealias", "typeof", "val", "var", "when", "while",
}


def strip_accents(text):
    """Remove acentos, mantendo apenas caracteres ASCII."""
    normalized = unicodedata.normalize("NFKD", text or "")
    return normalized.encode("ascii", "ignore").decode("ascii")


def words(text):
    """Quebra um texto em palavras alfanumericas, respeitando camelCase."""
    text = strip_accents(text)
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)
    return [w for w in re.split(r"[^A-Za-z0-9]+", text) if w]


def to_pascal(text, fallback="Item"):
    """Converte para PascalCase (nomes de classes)."""
    parts = words(text)
    if not parts:
        return fallback
    result = "".join(p[:1].upper() + p[1:] for p in parts)
    if result[0].isdigit():
        result = fallback + result
    return result


def to_camel(text, fallback="value"):
    """Converte para camelCase (nomes de propriedades e funcoes)."""
    pascal = to_pascal(text, fallback=fallback.capitalize())
    result = pascal[:1].lower() + pascal[1:]
    if result in KOTLIN_KEYWORDS:
        result += "Value"
    return result


def to_snake(text, fallback="item"):
    """Converte para snake_case (recursos Android e rotas)."""
    parts = words(text)
    if not parts:
        return fallback
    result = "_".join(p.lower() for p in parts)
    if result[0].isdigit():
        result = fallback + "_" + result
    return result


def to_package_segment(text):
    """Gera um segmento de pacote valido (minusculo, sem simbolos)."""
    seg = re.sub(r"[^a-z0-9]", "", strip_accents(text).lower())
    if not seg:
        seg = "app"
    if seg[0].isdigit():
        seg = "app" + seg
    if seg in KOTLIN_KEYWORDS or seg in {"java", "android"}:
        seg += "app"
    return seg


def is_valid_package(package):
    """Valida um applicationId Android (ex.: com.empresa.app)."""
    pattern = r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$"
    if not re.match(pattern, package or ""):
        return False
    return all(seg not in KOTLIN_KEYWORDS for seg in package.split("."))


def kotlin_string(text):
    """Escapa um texto para uso dentro de aspas duplas em Kotlin."""
    text = "" if text is None else str(text)
    text = text.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$")
    return text.replace("\n", "\\n").replace("\r", "").replace("\t", "\\t")


def kq(text):
    """Retorna o texto ja entre aspas como literal Kotlin."""
    return '"' + kotlin_string(text) + '"'


def xml_escape(text):
    """Escapa texto para atributos e conteudo XML."""
    text = "" if text is None else str(text)
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def android_string(text):
    """Escapa texto para o conteudo de um <string> do Android."""
    text = "" if text is None else str(text)
    text = text.replace("\\", "\\\\")
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = text.replace("'", "\\'").replace('"', '\\"').replace("\n", "\\n")
    if text.startswith("@") or text.startswith("?"):
        text = "\\" + text
    return text


def unique_name(base, used):
    """Garante um nome unico adicionando sufixo numerico quando necessario."""
    name = base
    index = 2
    while name in used:
        name = f"{base}{index}"
        index += 1
    used.add(name)
    return name


def indent(text, spaces):
    """Indenta todas as linhas nao vazias de um bloco de texto."""
    pad = " " * spaces
    return "\n".join(pad + line if line.strip() else line for line in text.split("\n"))
