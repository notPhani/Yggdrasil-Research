"""Generates a forensic network graph and converts it directly into SIXEL graphics format."""
import io
import sys
from pathlib import Path
from PIL import Image
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def generate_graph_image(out_png: Path) -> Image.Image:
    """Draw a dark-mode forensic graph of the Jan 27 2025 DeepSeek shock."""
    fig, ax = plt.subplots(figsize=(10, 6), dpi=100)
    fig.patch.set_facecolor("#0d1117")
    ax.set_facecolor("#0d1117")

    # Define nodes: (x, y, label, color, size)
    nodes = {
        "BOT": (0.50, 0.88, "● [ROOT] BOT\n(Baseline Market)", "#bc8cff", 1800),
        "DEEPSEEK": (0.32, 0.58, "▲ DeepSeek R1\n(Cost: 1.39 nats | 6.75:1 Odds)", "#58a6ff", 2200),
        "TARIFFS": (0.72, 0.58, "○ Tech Tariffs (Rival)\n(Cost: 2.45 nats)", "#d29922", 1600),
        "ABSTAIN": (0.86, 0.30, "✕ Abstention Baseline\n(Cost: 3.30 nats - Defeated)", "#f85149", 1400),
        "NVDA": (0.16, 0.22, "■ NVDA\n(-8.1%, 15x Vol)", "#3fb950", 1800),
        "TSM": (0.32, 0.15, "■ TSM\n(-4.1%)", "#3fb950", 1500),
        "ASML": (0.48, 0.22, "■ ASML.AS\n(-7.0%)", "#3fb950", 1500),
        "POWER": (0.68, 0.22, "■ AI Power (CEG, VST)\n(-3.8%)", "#e3b341", 1500),
    }

    # Edges: (from, to, color, width, style, label)
    edges = [
        ("BOT", "DEEPSEEK", "#58a6ff", 3.0, "-", "p=1.00 (Best Trunk)"),
        ("BOT", "TARIFFS", "#d29922", 1.8, "--", "p=0.22 (Rival)"),
        ("BOT", "ABSTAIN", "#f85149", 1.2, ":", "p=0.05"),
        ("DEEPSEEK", "NVDA", "#3fb950", 2.5, "-", "p=0.455"),
        ("DEEPSEEK", "TSM", "#3fb950", 2.0, "-", "p=0.312"),
        ("DEEPSEEK", "ASML", "#3fb950", 2.0, "-", "p=0.280"),
        ("TARIFFS", "POWER", "#e3b341", 1.8, "--", "p=0.150"),
    ]

    # Draw edges
    for frm, to, col, w, ls, elbl in edges:
        x1, y1 = nodes[frm][0], nodes[frm][1]
        x2, y2 = nodes[to][0], nodes[to][1]
        ax.annotate(
            "", xy=(x2, y2), xytext=(x1, y1),
            arrowprops=dict(arrowstyle="-|>", color=col, lw=w, linestyle=ls,
                            mutation_scale=14, shrinkA=18, shrinkB=18)
        )
        # Edge label
        mx, my = (x1 + x2) / 2.0, (y1 + y2) / 2.0
        ax.text(mx, my, elbl, color=col, fontsize=8, ha="center", va="center",
                bbox=dict(boxstyle="round,pad=0.2", facecolor="#161b22", edgecolor="none", alpha=0.8))

    # Draw nodes
    for k, (x, y, label, col, sz) in nodes.items():
        ax.scatter([x], [y], s=sz, color=col, zorder=5, edgecolors="#ffffff", linewidths=1.5, alpha=0.9)
        ax.text(x, y - 0.08, label, color="#c9d1d9", fontsize=8.5, fontweight="bold",
                ha="center", va="top", zorder=6,
                bbox=dict(boxstyle="round,pad=0.25", facecolor="#161b22", edgecolor="#30363d", alpha=0.9))

    ax.set_xlim(0.05, 0.98)
    ax.set_ylim(0.05, 1.02)
    ax.axis("off")
    plt.title("YGGDRASIL MARKET EVENT FORENSICS: STEINER TREE ARBORESCENCE (2025-01-27)",
              color="#58a6ff", fontsize=11, fontweight="bold", pad=15)
    plt.tight_layout()

    out_png.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_png, facecolor=fig.get_facecolor(), edgecolor="none", dpi=100)
    plt.close()

    return Image.open(out_png)


def image_to_sixel(im: Image.Image, max_colors: int = 64) -> str:
    """Converts a PIL Image to a standard SIXEL escape sequence string."""
    im = im.convert("RGB")
    # Resize down slightly to fit standard terminal height (e.g. 360px tall)
    w, h = im.size
    target_h = min(h, 360)
    target_w = int(w * (target_h / float(h)))
    im = im.resize((target_w, target_h), Image.Resampling.LANCZOS)
    
    # Quantize to limited palette
    im_pal = im.quantize(colors=max_colors)
    palette = im_pal.getpalette()[:max_colors * 3]
    pixels = np.array(im_pal)
    
    width, height = im_pal.size
    
    # SIXEL header
    out = ["\033Pq\"1;1"]
    
    # Output color table: #id;2;R%;G%;B%
    for i in range(len(palette) // 3):
        r = int(palette[i * 3 + 0] * 100 / 255.0)
        g = int(palette[i * 3 + 1] * 100 / 255.0)
        b = int(palette[i * 3 + 2] * 100 / 255.0)
        out.append(f"#{i};2;{r};{g};{b}")
        
    num_bands = (height + 5) // 6
    
    for band in range(num_bands):
        y_start = band * 6
        band_h = min(6, height - y_start)
        
        # Collect pixel colors in this 6-row band
        sub_pixels = pixels[y_start:y_start + band_h, :]
        active_colors = np.unique(sub_pixels)
        
        for c in active_colors:
            out.append(f"#{c}")
            chars = []
            run_char = ""
            run_count = 0
            
            for x in range(width):
                sixel_byte = 0
                for bit in range(band_h):
                    if sub_pixels[bit, x] == c:
                        sixel_byte |= (1 << bit)
                ch = chr(63 + sixel_byte)
                
                # Run-length compression (!count char)
                if ch == run_char:
                    run_count += 1
                else:
                    if run_count > 3:
                        chars.append(f"!{run_count}{run_char}")
                    elif run_count > 0:
                        chars.append(run_char * run_count)
                    run_char = ch
                    run_count = 1
                    
            if run_count > 3:
                chars.append(f"!{run_count}{run_char}")
            elif run_count > 0:
                chars.append(run_char * run_count)
                
            out.append("".join(chars) + "$")
            
        out.append("-")
        
    out.append("\033\\")
    return "".join(out)


def main():
    png_path = Path("data/sixel_graph.png")
    sixel_path = Path("data/sixel_graph.sixel")

    im = generate_graph_image(png_path)
    sixel_str = image_to_sixel(im, max_colors=48)
    
    sixel_path.write_text(sixel_str, encoding="ascii")
    
    # Write to stdout so SIXEL terminals can render it directly
    sys.stdout.write(sixel_str + "\n")
    sys.stdout.flush()

    print(f"\n[INFO] Generated PNG:   {png_path.resolve()} ({png_path.stat().st_size} bytes)")
    print(f"[INFO] Generated SIXEL: {sixel_path.resolve()} ({sixel_path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
