import sys
parts=['p1_head.html','p2_machine.html','p3_e1.html','p4_observer.html','p5_e2a.html','p6_e2b.html','p7_e3a.html','p8_e3b.html','p9_tables.html','p10_build.html','p11_script.html']
html=''.join(open(p).read() for p in parts)
html=html.replace('/*__LSH__*/', open('lsh.json').read())
open('yggdrasil_blueprint.html','w').write(html)
def prev(extra, name):
    open(name,'w').write('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"></head><body>'+extra+html+'</body></html>')
prev('', 'preview.html')
prev('<style>header, #machine, #e1, #observer, #e2a, .box.warn:first-of-type{display:none !important}</style>', 'preview_b.html')
prev('<style>header, #machine, #e1, #observer, #e2a, #e2b, #e3a, #e3b, .box.warn:first-of-type{display:none !important}</style>', 'preview_c.html')
print(len(html))
