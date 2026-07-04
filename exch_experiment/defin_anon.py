import re,json
forms=json.load(open("/tmp/exch_forms.json"))
KEEP=set("""theorem lemma def variable variables open namespace end by have let show fun match with at using from in do return if then else
exact apply refine intro intros rintro obtain rcases cases constructor simp simp_all simp_rw rw rewrite calc ring ring_nf linarith nlinarith
norm_num omega positivity gcongr aesop tauto decide field_simp convert congr ext funext subst this trivial rfl sorry
And Or Iff Exists Not True False Type Prop Sort Nonempty
Measure Measurable MeasurableSpace IsProbabilityMeasure StandardBorelSpace MemLp Integrable
Contractable ConditionallyIID Exchangeable deFinetti
forall exists not""".split())
# on garde aussi : locaux courts (<=2 char), h-préfixés courts, lettres grecques/maths
def keep(tok):
    if tok in KEEP: return True
    if len(tok)<=2: return True
    if re.fullmatch(r"h[A-Za-z0-9_]{0,3}", tok): return True
    if re.fullmatch(r"[0-9].*", tok): return True
    return False
IDENT=re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*'?")
out=[]
for o in forms:
    s=o["script"]
    # neutralise les "viaX" et le nom du théorème principal
    s=re.sub(r"via(Martingale|L2|Koopman)","ViaX",s)
    rmap={}; cnt=[0]
    def rep(m):
        t=m.group(0)
        head=t.split(".")[0]
        if keep(t) or keep(head): 
            # garde les chemins génériques type Measure.xxx ? -> on masque le suffixe spécifique
            if "." in t and not keep(t):
                pass
            else:
                return t
        if t not in rmap:
            cnt[0]+=1; rmap[t]=f"F{cnt[0]}"
        return rmap[t]
    anon=IDENT.sub(rep,s)
    out.append({"method":o["method"],"gold":o["gold"],"script":anon})
json.dump(out,open("/tmp/exch_anon.json","w"),indent=1,ensure_ascii=False)
print("masqués par script:",{o['method']:sum(1 for _ in re.finditer(r'F[0-9]+',oo['script'])) for o,oo in zip(forms,out)})
# vérif : plus de mots révélateurs ?
leak=["martingale","koopman","ergodic","directing","cesaro","cesàro","meanergodic","reverseMart","Hilbert","blockaverage"]
for oo in out:
    found=[w for w in leak if w.lower() in oo['script'].lower()]
    print(f"{oo['method']}: fuites restantes = {found or 'aucune'}")
print("\n--- script Martingale anonymisé (tête) ---")
print(out[0]['script'][:600])
