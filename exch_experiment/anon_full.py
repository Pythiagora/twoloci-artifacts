import re,json,glob,os
base="Exchangeability/DeFinetti"
golds=json.load(open("/tmp/exch_forms.json"))  # garde les golds
gmap={o['method']:o['gold'] for o in golds}
dirs={'Martingale':'ViaMartingale','L2':'ViaL2','Koopman':'ViaKoopman'}
KEEP=set("""theorem lemma def variable variables open namespace end by have let show fun match with at using from in do return if then else where mutual
exact apply refine intro intros rintro obtain rcases cases constructor simp simp_all simp_rw rw rewrite calc ring ring_nf linarith nlinarith
norm_num omega positivity gcongr aesop tauto decide field_simp convert congr ext funext subst this trivial rfl sorry set push_cast filter_upwards
And Or Iff Exists Not True False Type Prop Sort Nonempty noncomputable instance abbrev structure inductive class
Measure Measurable MeasurableSpace IsProbabilityMeasure StandardBorelSpace MemLp Integrable
Contractable ConditionallyIID Exchangeable deFinetti scoped BigOperators Topology Classical""".split())
def keep(t):
    if t in KEEP: return True
    if len(t)<=2: return True
    if re.fullmatch(r"h[A-Za-z0-9_]{0,3}",t): return True
    if re.fullmatch(r"[0-9].*",t): return True
    return False
IDENT=re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*'?")
out=[]
for m,d in dirs.items():
    files=[f"{base}/Theorem{ 'Via'+m }.lean"]+sorted(glob.glob(f"{base}/{d}/**/*.lean",recursive=True))
    src="\n".join(open(f).read() for f in files if os.path.exists(f))
    # strip docstrings /- ... -/ et commentaires --
    src=re.sub(r"/-.*?-/","",src,flags=re.DOTALL)
    src="\n".join(l for l in src.split("\n") if not l.strip().startswith("--"))
    src=re.sub(r"via(Martingale|L2|Koopman)","ViaX",src)
    rmap={}; cnt=[0]
    def rep(mt):
        t=mt.group(0); head=t.split(".")[0]
        if keep(t) or keep(head): return t
        if t not in rmap: cnt[0]+=1; rmap[t]=f"F{cnt[0]}"
        return rmap[t]
    anon=IDENT.sub(rep,src); anon=re.sub(r"\n{3,}","\n\n",anon).strip()
    out.append({"method":m,"gold":gmap[m],"script":anon,"nfiles":len(files),"nmask":cnt[0]})
json.dump(out,open("/tmp/exch_anon_full.json","w"),indent=1,ensure_ascii=False)
leak=["martingale","koopman","ergodic","directing","cesaro","cesàro","hilbert","blockaverage","reversemart","meanergodic","koopmanoperator"]
for o in out:
    f=[w for w in leak if w in o['script'].lower()]
    print(f"{o['method']}: {o['nfiles']} fichiers, {len(o['script'])} car, {o['nmask']} masqués | fuites={f or 'aucune'}")
