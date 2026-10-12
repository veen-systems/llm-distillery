import re,sys
for f in sys.argv[1:]:
    L=open(f).read().split("\n"); print("=====",f,len("\n".join(L)))
    heads=[i for i,l in enumerate(L) if re.match(r"^#{2,3} ",l)]+[len(L)]
    for a,b in zip(heads,heads[1:]):
        t="\n".join(L[a:b]); ds=re.findall(r"2026-(\d\d)-(\d\d)",t); mx=max(ds) if ds else None
        v=t.count("verify:")
        print(f"{a+1:4d}-{b:4d} {len(t):6d} max={'-'.join(mx) if mx else '-----'} v={v} {L[a][:75]}")
