
# streamlit_app.py  — HK Podravka • Unos po shemi "Knjiga1.xlsx"
import os, io, sqlite3
from datetime import datetime
import pandas as pd
import streamlit as st

st.set_page_config(page_title="HK Podravka — Unos (Knjiga1)", page_icon="🥇", layout="wide")

DB_PATH = "data/rezultati_knjiga1.sqlite"

# ----------------------- DB utils -----------------------
def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn

def df_from_sql(q: str, params: tuple = ()):
    conn = get_conn()
    df = pd.read_sql(q, conn, params=params)
    conn.close()
    return df

def exec_sql(q: str, params: tuple = ()):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(q, params)
    conn.commit()
    last_id = cur.lastrowid
    conn.close()
    return last_id

def exec_many(q: str, rows: list[tuple]):
    conn = get_conn()
    cur = conn.cursor()
    cur.executemany(q, rows)
    conn.commit()
    conn.close()

def init_db():
    """Kreira tablice ako ne postoje (prvi run na cloudu)."""
    conn = get_conn()
    cur = conn.cursor()
    cur.executescript("""
    PRAGMA foreign_keys=ON;

    CREATE TABLE IF NOT EXISTS competitions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        redni_broj INTEGER UNIQUE,
        godina INTEGER,
        datum TEXT,
        datum_kraj TEXT,
        natjecanje TEXT,
        ime_natjecanja TEXT NOT NULL,
        stil_hrvanja TEXT,
        mjesto TEXT,
        drzava TEXT,
        kratica_drzave TEXT,
        nastupilo_podravke INTEGER,
        ekipno TEXT,
        trener TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        competition_id INTEGER NOT NULL REFERENCES competitions(id) ON DELETE CASCADE,
        ime_prezime TEXT,
        spol TEXT,
        plasman TEXT,
        kategorija TEXT,
        uzrast TEXT,
        borbi INTEGER,
        pobjeda INTEGER,
        izgubljenih INTEGER,
        created_at TEXT DEFAULT (datetime('now'))
    );
    """)
    conn.commit()
    conn.close()

def next_redni_broj() -> int:
    """Vraća sljedeći RB; otporno i kad tablica još ne postoji/prazna."""
    try:
        d = df_from_sql("SELECT MAX(redni_broj) AS mx FROM competitions")
        if d.empty or d.iloc[0, 0] is None:
            return 1
        return int(d.iloc[0, 0]) + 1
    except Exception:
        return 1

# obavezno inicijaliziraj bazu na startu
init_db()

# ----------------------- UI -----------------------
st.title("🥇 HK Podravka — Unos i analiza (po tvojoj tablici)")

page = st.sidebar.radio(
    "Navigacija",
    ["➕ Unos natjecanja", "🧾 Unos rezultata", "📊 Pregled", "⬆️ Uvoz (Knjiga1.xlsx)"]
)

# ----------------------- ➕ Unos natjecanja -----------------------
if page == "➕ Unos natjecanja":
    st.subheader("➕ Dodaj natjecanje")
    with st.form("frm_comp"):
        rb = next_redni_broj()
        st.write(f"Redni broj (auto): **{rb}**")

        col1, col2, col3 = st.columns(3)
        with col1:
            godina = st.number_input("GODINA", min_value=1990, max_value=2100,
                                     value=datetime.now().year, step=1)
            datum = st.date_input("DATUM (početak)")
            datum_kraj = st.date_input("DATUM (kraj)", value=datum)
        with col2:
            natjecanje = st.text_input("NATJECANJE (oznaka/tip, npr. PH, Kup…)")
            ime_natjecanja = st.text_input("IME NATJECANJA *")
            stil = st.text_input("stil hrvanja (GR/SL/Ž)")
        with col3:
            mjesto = st.text_input("MJESTO")
            drzava = st.text_input("DRŽAVA", value="Hrvatska")
            kratica = st.text_input("KRATICA DRŽAVE", value="HR")

        col4, col5 = st.columns(2)
        with col4:
            nastupilo = st.number_input("NASTUPILO HRVAČA PODRAVKE", min_value=0, step=1, value=0)
            ekipno = st.text_input("EKIPNO (npr. ekipni poredak)")
        with col5:
            trener = st.text_input("TRENER")

        submitted = st.form_submit_button("Spremi natjecanje")
        if submitted:
            if not ime_natjecanja.strip():
                st.error("IME NATJECANJA je obavezno.")
            else:
                exec_sql(
                    """
                    INSERT INTO competitions
                    (redni_broj, godina, datum, datum_kraj, natjecanje, ime_natjecanja,
                     stil_hrvanja, mjesto, drzava, kratica_drzave, nastupilo_podravke, ekipno, trener)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        rb, int(godina), str(datum), str(datum_kraj), natjecanje.strip(),
                        ime_natjecanja.strip(), stil.strip(), mjesto.strip(), drzava.strip(),
                        kratica.strip(), int(nastupilo), ekipno.strip(), trener.strip()
                    )
                )
                st.success(f"Natjecanje spremljeno. Redni broj: {rb}")

    st.divider()
    st.subheader("📋 Popis natjecanja")
    dfc = df_from_sql("""
        SELECT redni_broj, godina, datum, datum_kraj, ime_natjecanja, natjecanje,
               mjesto, drzava, stil_hrvanja
        FROM competitions
        ORDER BY godina DESC, datum DESC
    """)
    st.dataframe(dfc, use_container_width=True)

# ----------------------- 🧾 Unos rezultata -----------------------
elif page == "🧾 Unos rezultata":
    st.subheader("🧾 Unos rezultata za natjecanje")

    dfc = df_from_sql("SELECT id, redni_broj, datum, ime_natjecanja FROM competitions ORDER BY godina DESC, datum DESC")
    if dfc.empty:
        st.info("Prvo dodaj natjecanje u ➕ Unos natjecanja.")
        st.stop()

    labels = dfc.apply(lambda r: f"#{int(r['redni_broj'])} — {r['datum']} — {r['ime_natjecanja']}", axis=1).tolist()
    comp_map = {labels[i]: int(dfc.iloc[i]["id"]) for i in range(len(labels))}
    sel = st.selectbox("Odaberi natjecanje", labels)
    competition_id = comp_map[sel]

    with st.form("frm_res"):
        col1, col2, col3 = st.columns(3)
        with col1:
            ime_prezime = st.text_input("IME I PREZIME *")
            spol = st.selectbox("spol", ["M", "Ž"])
            kategorija = st.text_input("KATEGORIJA")
            uzrast = st.text_input("UZRAST (U13/U15/...)")
        with col2:
            borbi = st.number_input("BORBI", min_value=0, step=1, value=0)
            pobjeda = st.number_input("POBJEDA", min_value=0, step=1, value=0)
            izgubljenih = st.number_input("IZGUBLJENIH", min_value=0, step=1, value=0)
        with col3:
            plasman = st.text_input("PLASMAN (1/2/3/...)")

        submit = st.form_submit_button("Spremi rezultat")
        if submit:
            if not ime_prezime.strip():
                st.error("IME I PREZIME je obavezno.")
            else:
                exec_sql(
                    """
                    INSERT INTO results
                    (competition_id, ime_prezime, spol, plasman, kategorija, uzrast, borbi, pobjeda, izgubljenih)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        competition_id, ime_prezime.strip(), spol, plasman.strip(),
                        kategorija.strip(), uzrast.strip(),
                        int(borbi), int(pobjeda), int(izgubljenih)
                    )
                )
                st.success("Rezultat spremljen.")
                st.experimental_rerun()

    st.divider()
    st.subheader("📋 Zadnjih 200 rezultata")
    dfr = df_from_sql("""
        SELECT r.id,
               c.redni_broj, c.ime_natjecanja, c.datum,
               r.ime_prezime, r.spol, r.kategorija, r.uzrast,
               r.borbi, r.pobjeda, r.izgubljenih, r.plasman
        FROM results r
        JOIN competitions c ON c.id = r.competition_id
        ORDER BY r.id DESC
        LIMIT 200
    """)
    st.dataframe(dfr, use_container_width=True)

# ----------------------- 📊 Pregled -----------------------
elif page == "📊 Pregled":
    st.subheader("📊 Pregled i filtriranje")
    dfr = df_from_sql("""
        SELECT r.*, c.redni_broj, c.godina, c.ime_natjecanja, c.datum,
               c.mjesto, c.drzava, c.stil_hrvanja
        FROM results r
        JOIN competitions c ON c.id = r.competition_id
    """)

    if dfr.empty:
        st.info("Nema još rezultata.")
        st.stop()

    colA, colB, colC, colD = st.columns(4)
    with colA:
        god = sorted(dfr["godina"].dropna().astype(int).unique().tolist())
        sel_god = st.multiselect("Godina", god, default=god)
    with colB:
        nat = sorted(dfr["ime_natjecanja"].dropna().astype(str).unique().tolist())
        sel_nat = st.multiselect("Ime natjecanja", nat, default=[])
    with colC:
        kat = sorted(dfr["kategorija"].dropna().astype(str).unique().tolist())
        sel_kat = st.multiselect("Kategorija", kat, default=[])
    with colD:
        spol = sorted(dfr["spol"].dropna().astype(str).unique().tolist())
        sel_spol = st.multiselect("Spol", spol, default=[])

    f = dfr.copy()
    if sel_god:
        f = f[f["godina"].astype(int).isin(sel_god)]
    if sel_nat:
        f = f[f["ime_natjecanja"].astype(str).isin(sel_nat)]
    if sel_kat:
        f = f[f["kategorija"].astype(str).isin(sel_kat)]
    if sel_spol:
        f = f[f["spol"].astype(str).isin(sel_spol)]

    st.write(f"🔎 Zapisa: **{len(f)}**")
    st.dataframe(
        f[[
            "redni_broj","godina","datum","ime_natjecanja","ime_prezime","spol",
            "kategorija","uzrast","borbi","pobjeda","izgubljenih","plasman",
            "mjesto","drzava","stil_hrvanja"
        ]],
        use_container_width=True
    )

    with st.expander("📈 Brza statistika", expanded=False):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Natjecanja", df_from_sql("SELECT COUNT(*) AS n FROM competitions")["n"].iloc[0])
        c2.metric("Rezultata", len(f))
        c3.metric("Ukupno borbi", int(f["borbi"].fillna(0).sum()))
        c4.metric("Pobjede", int(f["pobjeda"].fillna(0).sum()))

# ----------------------- ⬆️ Uvoz (Knjiga1.xlsx) -----------------------
elif page == "⬆️ Uvoz (Knjiga1.xlsx)":
    st.subheader("⬆️ Uvoz iz Excela po tvojoj tablici")
    st.caption(
        "Prihvaća .xlsx sa zaglavljima: GODINA, REDNI BROJ, DATUM, DATUM.1, "
        "IME I PREZIME, spol, PLASMAN, KATEGORIJA, NATJECANJE, IME NATJECANJA, "
        "UZRAST, stil hrvanja, MJESTO, DRŽAVA, KRATICA DRŽAVE, NASTUPILO HRVAČA PODRAVKE, "
        "EKIPNO, BORBI, POBJEDA, IZGUBLJENIH, TRENER."
    )
    up = st.file_uploader("Excel (.xlsx)", type=["xlsx"])
    if up:
        xls = pd.ExcelFile(io.BytesIO(up.getvalue()))
        sheet = st.selectbox("Sheet", xls.sheet_names)
        df = xls.parse(sheet)
        st.dataframe(df.head(20), use_container_width=True)

        def col(df, name):
            """Pronalaženje kolone case-insensitive."""
            for c in df.columns:
                if c.strip().lower() == name.strip().lower():
                    return c
            return None

        need = [
            "GODINA","REDNI BROJ","DATUM","DATUM.1","IME I PREZIME","spol","PLASMAN",
            "KATEGORIJA","NATJECANJE","IME NATJECANJA","UZRAST","stil hrvanja",
            "MJESTO","DRŽAVA","KRATICA DRŽAVE","NASTUPILO HRVAČA PODRAVKE",
            "EKIPNO","BORBI","POBJEDA","IZGUBLJENIH","TRENER"
        ]
        mapping = {n: col(df, n) for n in need}
        missing = [k for k, v in mapping.items() if v is None]
        if missing:
            st.error("Nedostaju kolone: " + ", ".join(missing))
        else:
            if st.button("🚀 Uvezi sve redove"):
                # ---- competitions (po REDNI BROJ) ----
                exist = df_from_sql("SELECT redni_broj FROM competitions")
                existing_rb = set(exist["redni_broj"].tolist()) if not exist.empty else set()

                comp_rows = {}
                for rb in df[mapping["REDNI BROJ"]].dropna().unique().tolist():
                    r = df[df[mapping["REDNI BROJ"]] == rb].iloc[0]
                    comp_rows[int(rb)] = (
                        int(rb),
                        int(pd.to_numeric(r[mapping["GODINA"]], errors="coerce") or 0),
                        str(r[mapping["DATUM"]]) if pd.notna(r[mapping["DATUM"]]) else "",
                        str(r[mapping["DATUM.1"]]) if pd.notna(r[mapping["DATUM.1"]]) else "",
                        str(r[mapping["NATJECANJE"]] or ""),
                        str(r[mapping["IME NATJECANJA"]] or ""),
                        str(r[mapping["stil hrvanja"]] or ""),
                        str(r[mapping["MJESTO"]] or ""),
                        str(r[mapping["DRŽAVA"]] or ""),
                        str(r[mapping["KRATICA DRŽAVE"]] or ""),
                        int(pd.to_numeric(r[mapping["NASTUPILO HRVAČA PODRAVKE"]], errors="coerce") or 0),
                        str(r[mapping["EKIPNO"]] or ""),
                        str(r[mapping["TRENER"]] or "")
                    )

                # insert competitions if missing
                for rb, row in comp_rows.items():
                    if rb in existing_rb:
                        continue
                    exec_sql("""
                        INSERT INTO competitions
                        (redni_broj, godina, datum, datum_kraj, natjecanje, ime_natjecanja,
                         stil_hrvanja, mjesto, drzava, kratica_drzave, nastupilo_podravke,
                         ekipno, trener)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, row)

                # map redni_broj -> id
                dfc = df_from_sql("SELECT id, redni_broj FROM competitions")
                rb_to_id = {int(r["redni_broj"]): int(r["id"]) for _, r in dfc.iterrows()}

                # ---- results ----
                rows = []
                for _, r in df.iterrows():
                    rb = int(pd.to_numeric(r[mapping["REDNI BROJ"]], errors="coerce") or 0)
                    comp_id = rb_to_id.get(rb)
                    if not comp_id:
                        continue
                    rows.append((
                        comp_id,
                        str(r[mapping["IME I PREZIME"]] or ""),
                        str(r[mapping["spol"]] or ""),
                        str(r[mapping["PLASMAN"]] or ""),
                        str(r[mapping["KATEGORIJA"]] or ""),
                        str(r[mapping["UZRAST"]] or ""),
                        int(pd.to_numeric(r[mapping["BORBI"]], errors="coerce") or 0),
                        int(pd.to_numeric(r[mapping["POBJEDA"]], errors="coerce") or 0),
                        int(pd.to_numeric(r[mapping["IZGUBLJENIH"]], errors="coerce") or 0)
                    ))

                if rows:
                    exec_many("""
                        INSERT INTO results
                        (competition_id, ime_prezime, spol, plasman, kategorija, uzrast, borbi, pobjeda, izgubljenih)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, rows)

                st.success(f"Uvezeno natjecanja: {len(comp_rows)} • Uvezeno rezultata: {len(rows)}")

