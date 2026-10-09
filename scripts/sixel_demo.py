"""Demonstration of SIXEL graphics protocol in Python.

SIXEL encodes a bitmap into 6-pixel horizontal bands represented as printable ASCII.
When printed to a SIXEL-capable terminal (WezTerm, Mintty, xterm, modern Windows Terminal),
it renders as a true pixel bitmap graphic right inside the text flow.
"""
import sys

def encode_sixel_circle(radius=20):
    """Generate a crisp colored graph node (circle) in SIXEL format."""
    size = radius * 2
    # Create pixel mask for a circle
    pixels = []
    for y in range(size):
        row = []
        for x in range(size):
            dx = x - radius
            dy = y - radius
            d2 = dx * dx + dy * dy
            if d2 <= (radius - 2) * (radius - 2):
                row.append(2)  # green fill
            elif d2 <= radius * radius:
                row.append(1)  # cyan border
            else:
                row.append(0)  # transparent background
        pixels.append(row)
    
    # SIXEL header
    out = ["\033Pq\"1;1"]
    # Color palette: #id;2;R%;G%;B%
    out.append("#0;2;0;0;0#1;2;0;80;100#2;2;10;90;40")
    
    # Render in 6-pixel vertical bands
    num_bands = (size + 5) // 6
    for b in range(num_bands):
        y_start = b * 6
        for color_idx in (1, 2):
            out.append(f"#{color_idx}")
            sixel_chars = []
            for x in range(size):
                sixel_byte = 0
                for bit in range(6):
                    y = y_start + bit
                    if y < size and pixels[y][x] == color_idx:
                        sixel_byte |= (1 << bit)
                sixel_chars.append(chr(63 + sixel_byte))
            out.append("".join(sixel_chars))
            out.append("$")  # carriage return to start of 6-pixel line
        out.append("-")      # newline to next 6-pixel band
        
    out.append("\033\\")     # SIXEL string terminator
    return "".join(out)

if __name__ == "__main__":
    print("--- [SIXEL DEMO STREAM START] ---")
    sixel_data = encode_sixel_circle(radius=16)
    # Output raw SIXEL sequence
    sys.stdout.write(sixel_data + "\n")
    print("--- [SIXEL DEMO STREAM END] ---")
    print(f"Total SIXEL bytes: {len(sixel_data)}")
    print(f"Header: {repr(sixel_data[:20])}")
    print(f"Footer: {repr(sixel_data[-10:])}")
