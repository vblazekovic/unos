
import io
import os
import json
import sqlite3
from datetime import datetime, date
from typing import List

import pandas as pd
import streamlit as st

st.set_page_config(page_title="HK Podravka — Sustav (prazno)", page_icon="🥇", layout="wide")

DB_PATH = "data/rezultati_knjiga1.sqlite"  # ostavljeno isto ime zbog kompatibilnosti
UPLOAD_ROOT = "data/uploads"  # slike natjecanja i fotografije članova

# -------------------- pomoćne liste --------------------
COMP_TYPES_DEFAULT = [
    "PRVENSTVO HRVATSKE",
    "REPREZENTATIVNI NASTUP",
    "MEĐUNARODNI TURNIR",
    "KUP",
    "LIGA",
    "REGIONALNO",
    "KVALIFIKACIJE",
    "ŠKOLSKO",
    "OSTALO",
]
STYLES = ["GR", "FS", "WW", "BW", "MODIFICIRANI"]
AGE_GROUPS = ["početnici", "početnice", "U11", "U13", "U15", "U17", "U20", "U23", "seniori", "seniorke"]

COUNTRIES = {
    "Albanija": "AL", "Austrija": "AT", "Belgija": "BE", "Bosna i Hercegovina": "BA",
    "Bugarska": "BG", "Crna Gora": "ME", "Češka": "CZ", "Danska": "DK", "Egipat": "EG",
    "Finska": "FI", "Francuska": "FR", "Grčka": "GR", "Hrvatska": "HR", "Irska": "IE",
    "Italija": "IT", "Kosovo": "XK", "Mađarska": "HU", "Makedonija": "MK", "Njemačka": "DE",
    "Nizozemska": "NL", "Norveška": "NO", "Poljska": "PL", "Portugal": "PT", "Rumunjska": "RO",
    "SAD": "US", "Srbija": "RS", "Slovačka": "SK", "Slovenija": "SI", "Španjolska": "ES",
    "Švedska": "SE", "Švicarska": "CH", "Turska": "TR", "Ujedinjeno Kraljevstvo": "GB",
}

# -------------------- DB utils --------------------
def ensure_dirs():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    os.makedirs(UPLOAD_ROOT, exist_ok=True)


def get_conn():
    ensure_dirs()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def df_from_sql(q: str, params: tuple = ()):  # helper za SELECT -> DataFrame
    conn = get_conn()
    df = pd.read_sql(q, conn, params=params)
    conn.close()
    return df


def exec_sql(q: str, params: tuple = ()):  # helper za INSERT/UPDATE jedno
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(q, params)
    conn.commit()
    lid = cur.lastrowid
    conn.close()
    return lid


def exec_many(q: str, rows: List[tuple]):  # helper za INSERT/UPDATE više
    conn = get_conn()
    cur = conn.cursor()
    cur.executemany(q, rows)
    conn.commit()
    conn.close()


def init_db():
    """Kreira *praznu* bazu (bez podataka)."""
    conn = get_conn()
    cur = conn.cursor()
    cur.executescript(
        """
        PRAGMA foreign_keys=ON;

        -- NATJECANJA
        CREATE TABLE IF NOT EXISTS competitions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            redni_broj INTEGER UNIQUE,
            godina INTEGER,
            datum TEXT,
            datum_kraj TEXT,
            natjecanje TEXT,
            ime_natjecanja TEXT,
            stil_hrvanja TEXT,
            mjesto TEXT,
            drzava TEXT,
            kratica_drzave TEXT,
            nastupilo_podravke INTEGER,
            ekipno TEXT,
            trener TEXT,
            napomena TEXT,
            link_rezultati TEXT,
            galerija_json TEXT,
            vijest TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        -- REZULTATI
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

        -- CLANOVI
        CREATE TABLE IF NOT EXISTS members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ime TEXT,
            prezime TEXT,
            datum_rodjenja TEXT,
            godina_rodjenja INTEGER,
            email_sportas TEXT,
            email_roditelj TEXT,
            telefon_sportas TEXT,
            telefon_roditelj TEXT,
            clanski_broj TEXT,
            oib TEXT,
            adresa TEXT,
            grupa_trening TEXT,
            foto_path TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        """
    )
    conn.commit()
    conn.close()


def next_redni_broj() -> int:
    try:
        d = df_from_sql("SELECT MAX(redni_broj) AS mx FROM competitions")
        if d.empty or d.iloc[0, 0] is None:
            return 1
        return int(d.iloc[0, 0]) + 1
    except Exception:
        return 1


def save_uploads(files, folder: str) -> list:
    """Spremi uploadane datoteke u podmapu; vrati listu putanja."""
    ensure_dirs()
    saved = []
    if not files:
        return saved
    dest_dir = os.path.join(UPLOAD_ROOT, folder)
    os.makedirs(dest_dir, exist_ok=True)
    for f in files:
        name = f.name.replace("/", "_").replace("\\", "_")
        path = os.path.join(dest_dir, name)
        with open(path, "wb") as out:
            out.write(f.read())
        saved.append(path)
    return saved


# Inicijalizacija *prazne* baze
init_db()

# -------------------- UI --------------------
st.title("🥇 HK Podravka — Sustav (prazan)")

page = st.sidebar.radio(
    "Navigacija",
    [
        "➕ Unos natjecanja",
        "🛠 Uredi natjecanje",
        "🧾 Unos rezultata",
        "📊 Pregled & izvoz",
        "👤 Članovi",
    ],
)

# ---------- helpers za UI ----------
def select_or_new(label: str, options: List[str], key: str) -> str:
    opts = sorted(list(set([o for o in options if o])))
    opts = ["➕ Upiši novo…"] + opts
    sel = st.selectbox(label, opts, key=key)
    if sel == "➕ Upiši novo…":
        return st.text_input(f"{label} (upiši)", key=f"{key}_new").strip()
    return sel


def name_select(label: str, names: List[str], key: str) -> str:
    opts = sorted(list(set([n for n in names if n])))
    opts = ["➕ Upiši novo ime/prezime…"] + opts
    sel = st.selectbox(label, opts, key=key)
    if sel.startswith("➕"):
        return st.text_input(f"{label} (upiši)", key=f"{key}_new").strip()
    return sel

# ----------------------- ➕ Unos natjecanja -----------------------
if page == "➕ Unos natjecanja":
    st.subheader("➕ Dodaj natjecanje")

    with st.form("frm_comp_add"):
        rb = next_redni_broj()
        st.write(f"Redni broj (auto): **{rb}**")

        col1, col2, col3 = st.columns(3)
        with col1:
            godina = st.number_input("Godina", min_value=1990, max_value=2100, value=datetime.now().year, step=1)
            datum = st.date_input("Datum (početak)")
            datum_kraj = st.date_input("Datum (kraj)", value=datum)
        with col2:
            natjecanje = select_or_new("Tip natjecanja", COMP_TYPES_DEFAULT, "comp_type")
            ime_natjecanja = st.text_input("Ime natjecanja (opcionalno)")
            stil = st.selectbox("Stil", STYLES, index=0)
        with col3:
            df_c = df_from_sql("SELECT DISTINCT mjesto FROM competitions WHERE mjesto IS NOT NULL AND mjesto<>''")
            grad_postojece = df_c["mjesto"].tolist() if not df_c.empty else []
            mjesto = select_or_new("Mjesto", grad_postojece, "grad_sel")

            drzave_opts = sorted(list(COUNTRIES.keys()))
            drzava = st.selectbox("Država", drzave_opts, index=drzave_opts.index("Hrvatska") if "Hrvatska" in drzave_opts else 0)
            kratica = st.text_input("Kratica države (auto, ali promjenjivo)", value=COUNTRIES.get(drzava, ""))

        col4, col5 = st.columns(2)
        with col4:
            nastupilo = st.number_input("Nastupilo hrvača Podravke", min_value=0, step=1, value=0)
            ekipno = st.text_input("Ekipno (npr. ekipni poredak)")
        with col5:
            trener = st.text_input("Trener")

        st.markdown("**Dodatno**")
        link_rez = st.text_input("Link na rezultate (URL)")
        napomena = st.text_area("Napomena", height=80)
        vijest = st.text_area("Tekst vijesti (za web objavu)", height=200)
        imgs = st.file_uploader("Slike s natjecanja (može više)", type=["png", "jpg", "jpeg", "webp"], accept_multiple_files=True)

        submit = st.form_submit_button("Spremi natjecanje")
        if submit:
            comp_id = exec_sql(
                """
                INSERT INTO competitions
                (redni_broj, godina, datum, datum_kraj, natjecanje, ime_natjecanja, stil_hrvanja,
                 mjesto, drzava, kratica_drzave, nastupilo_podravke, ekipno, trener,
                 napomena, link_rezultati, galerija_json, vijest)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rb, int(godina), str(datum), str(datum_kraj), natjecanje.strip(), ime_natjecanja.strip(),
                    stil.strip(), mjesto.strip(), drzava.strip(), kratica.strip(), int(nastupilo), ekipno.strip(),
                    trener.strip(), napomena.strip(), link_rez.strip(), None, vijest.strip()
                ),
            )
            paths = save_uploads(imgs, f"comp_{comp_id}") if imgs else []
            if paths:
                exec_sql("UPDATE competitions SET galerija_json=? WHERE id=?", (json.dumps(paths
            )
