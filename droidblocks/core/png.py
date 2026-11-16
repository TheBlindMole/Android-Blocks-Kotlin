"""Escritor de PNG em Python puro (sem dependencias) para gerar icones.

Desenha o icone padrao do app: fundo arredondado na cor principal com um
simbolo de blocos empilhados. Tambem gera arquivos .ico e .icns para o
instalador do DroidBlocks.
"""

import functools
import struct
import zlib


def hex_to_rgb(value):
    value = (value or "#1E88E5").lstrip("#")
    if len(value) == 3:
        value = "".join(c * 2 for c in value)
    try:
        return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return (30, 136, 229)


def encode_png(width, height, pixels):
    """pixels: lista de linhas, cada linha lista de tuplas RGBA."""
    raw = bytearray()
    for row in pixels:
        raw.append(0)
        for r, g, b, a in row:
            raw.extend((r, g, b, a))

    def chunk(kind, data):
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

    header = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) +
            chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b""))


def _inside_round_rect(x, y, x0, y0, x1, y1, radius):
    if x < x0 or x > x1 or y < y0 or y > y1:
        return False
    cx = min(max(x, x0 + radius), x1 - radius)
    cy = min(max(y, y0 + radius), y1 - radius)
    return (x - cx) ** 2 + (y - cy) ** 2 <= radius ** 2


@functools.lru_cache(maxsize=64)
def render_icon(size, color="#1E88E5", round_shape=False, background=None):
    """Desenha o icone com supersampling 3x3 para bordas suaves."""
    base = hex_to_rgb(color)
    accent = (255, 255, 255)
    bg = hex_to_rgb(background) if background else None
    samples = 3
    pixels = []
    s = float(size)
    blocks = [  # tres blocos empilhados em escada (proporcoes do icone)
        (0.24, 0.56, 0.76, 0.74),
        (0.30, 0.38, 0.70, 0.54),
        (0.36, 0.22, 0.64, 0.36),
    ]
    for py in range(size):
        row = []
        for px in range(size):
            acc = [0.0, 0.0, 0.0, 0.0]
            for sy in range(samples):
                for sx in range(samples):
                    x = (px + (sx + 0.5) / samples) / s
                    y = (py + (sy + 0.5) / samples) / s
                    if round_shape:
                        inside = (x - 0.5) ** 2 + (y - 0.5) ** 2 <= 0.47 ** 2
                    else:
                        inside = _inside_round_rect(x, y, 0.04, 0.04, 0.96, 0.96, 0.2)
                    if not inside:
                        if bg:
                            acc[0] += bg[0]; acc[1] += bg[1]; acc[2] += bg[2]; acc[3] += 255
                        continue
                    pixel = base
                    for bx0, by0, bx1, by1 in blocks:
                        if _inside_round_rect(x, y, bx0, by0, bx1, by1, 0.03):
                            pixel = accent
                            break
                    acc[0] += pixel[0]; acc[1] += pixel[1]; acc[2] += pixel[2]; acc[3] += 255
            n = samples * samples
            alpha = acc[3] / n
            if alpha <= 0:
                row.append((0, 0, 0, 0))
            else:
                row.append((int(acc[0] / n * 255 / alpha), int(acc[1] / n * 255 / alpha),
                            int(acc[2] / n * 255 / alpha), int(alpha)))
        pixels.append(row)
    return encode_png(size, size, pixels)


def build_ico(png_by_size):
    """Monta um .ico contendo PNGs (suportado a partir do Windows Vista)."""
    sizes = sorted(png_by_size)
    header = struct.pack("<HHH", 0, 1, len(sizes))
    offset = 6 + 16 * len(sizes)
    entries, data = b"", b""
    for size in sizes:
        png = png_by_size[size]
        dim = 0 if size >= 256 else size
        entries += struct.pack("<BBBBHHII", dim, dim, 0, 0, 1, 32, len(png), offset + len(data))
        data += png
    return header + entries + data


def build_icns(png_by_size):
    """Monta um .icns com PNGs (formato aceito pelo macOS 10.7+)."""
    types = {16: b"icp4", 32: b"icp5", 64: b"icp6", 128: b"ic07", 256: b"ic08", 512: b"ic09"}
    body = b""
    for size, kind in types.items():
        if size in png_by_size:
            png = png_by_size[size]
            body += kind + struct.pack(">I", len(png) + 8) + png
    return b"icns" + struct.pack(">I", len(body) + 8) + body
