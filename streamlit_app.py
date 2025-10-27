# hk_podravka_app.py
# ---------------------------------------------
# Streamlit aplikacija za Hrvački klub Podravka
# Jedna .py datoteka, mobilno responzivna, s više odjeljaka.
# Autor: ChatGPT (za Vedrana)
# ---------------------------------------------

import streamlit as st
import pandas as pd
import io, os, base64
from datetime import datetime

st.set_page_config(
    page_title="HK Podravka - Admin",
    page_icon="🤼",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------
# Klupske boje i jednostavan stil
# -----------------------------
PRIMARY_RED = "#d60000"
WHITE = "#ffffff"
GOLD = "#c9a227"
BG_LIGHT = "#fff8f3"

CUSTOM_CSS = f"""
<style>
/* Global */
:root {{
  --club-red: {PRIMARY_RED};
  --club-gold: {GOLD};
  --club-white: {WHITE};
}}
/* Pozadina i kartice */
section.main > div {{
  background: {BG_LIGHT};
  border-radius: 18px;
  padding: 0.5rem 0.75rem;
}}
/* Naslovi */
h1, h2, h3, h4 {{
  color: var(--club-red);
}}
/* Dugmad */
.stButton>button {{
  background: var(--club-red);
  color: var(--club-white);
  border: none;
  border-radius: 12px;
  padding: 0.5rem 0.9rem;
}}
.stButton>button:hover {{
  background: #b00000;
}}
/* Info box */
div[data-baseweb="tag"] {{
  background: var(--club-gold) !important;
  color: black !important;
}}
/* Tab pločice (hint – Streamlit tabs su div-ovi) */
.stTabs [data-baseweb="tab-list"] {{
  gap: .25rem;
}}
.stTabs [data-baseweb="tab"] {{
  background: white;
  border: 1px solid #eee;
  border-bottom: 3px solid var(--club-gold);
  border-radius: 10px 10px 0 0;
  padding-top: .75rem;
  padding-bottom: .75rem;
}}
/* Tabele */
thead th {{
  background: var(--club-gold) !important;
  color: black !important;
}}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# -----------------------------
# Putanje za lokalnu pohranu (za produkciju / GitHub Actions možete zamijeniti npr. bazom)
# -----------------------------
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
MEMBERS_FILE = os.path.join(DATA_DIR, "clanovi.xlsx")
OFFICIALS_FILE = os.path.join(DATA_DIR, "duznosnici.xlsx")
DOCS_DIR = os.path.join(DATA_DIR, "dokumenti")
os.makedirs(DOCS_DIR, exist_ok=True)

# -----------------------------
# Pomoćne funkcije
# -----------------------------
MEMBER_COLUMNS = [
    "Ime", "Prezime", "Datum rođenja", "Spol (M/Ž)",
    "OIB", "Mjesto prebivališta",
    "Email sportaša", "Email roditelja/skrbnika",
    "Broj osobne iskaznice", "OI vrijedi do", "OI izdao",
    "Broj putovnice", "Putovnica vrijedi do", "Putovnicu izdao",
    "Status (Aktivni/Veteran/Ostalo)", "Plaća članarinu", "Iznos članarine (EUR)",
    "Grupa", "Slika (base64)",
    "Privola (da/ne)", "Pristupnica (da/ne)"
]

OFFICIALS_COLUMNS = [
    "Uloga (Predsjednik/Tajnik/Predsjedništvo/Nadzorni odbor)",
    "Ime i prezime", "Kontakt broj", "Email"
]

DEFAULT_GROUPS = ["Hrvači", "Hrvačice", "Veterani", "Ostalo"]

def init_state():
    if "club_info" not in st.session_state:
        st.session_state.club_info = {
            "Klub": "Hrvački klub Podravka",
            "Ulica i broj": "Miklinovec 6a",
            "Grad i poštanski broj": "48000 Koprivnica",
            "Email": "hsk-podravka@gmail.com",
            "OIB": "60911784858",
            "IBAN": "HR6923860021100518154",
            "Web": "https://hk-podravka.com",
            "Instagram": "",
            "Facebook": "",
            "TikTok": "",
        }
    if "logo_bytes" not in st.session_state:
        st.session_state.logo_bytes = None
    if "members_df" not in st.session_state:
        if os.path.exists(MEMBERS_FILE):
            try:
                st.session_state.members_df = pd.read_excel(MEMBERS_FILE)
            except Exception:
                st.session_state.members_df = pd.DataFrame(columns=MEMBER_COLUMNS)
        else:
            st.session_state.members_df = pd.DataFrame(columns=MEMBER_COLUMNS)
    if "officials_df" not in st.session_state:
        if os.path.exists(OFFICIALS_FILE):
            try:
                st.session_state.officials_df = pd.read_excel(OFFICIALS_FILE)
            except Exception:
                st.session_state.officials_df = pd.DataFrame(columns=OFFICIALS_COLUMNS)
        else:
            st.session_state.officials_df = pd.DataFrame(columns=OFFICIALS_COLUMNS)
    if "docs" not in st.session_state:
        st.session_state.docs = {}

def b64file(data_bytes, filename):
    b64 = base64.b64encode(data_bytes).decode()
    href = f'<a download="{filename}" href="data:file/octet-stream;base64,{b64}">Preuzmi {filename}</a>'
    return href

def save_all():
    st.session_state.members_df.to_excel(MEMBERS_FILE, index=False)
    st.session_state.officials_df.to_excel(OFFICIALS_FILE, index=False)

def excel_template_bytes():
    tmp = pd.DataFrame(columns=MEMBER_COLUMNS)
    bio = io.BytesIO()
    with pd.ExcelWriter(bio, engine="xlsxwriter") as writer:
        tmp.to_excel(writer, index=False, sheet_name="Clanovi")
        # Kratke upute
        guide = pd.DataFrame({
            "Polje": MEMBER_COLUMNS,
            "Napomena": [
                "Obavezno Ime", "Obavezno Prezime", "Format YYYY-MM-DD", "M ili Ž",
                "OIB (11 znamenki)", "Grad/naselje",
                "Email sportaša", "Email roditelja/skrbnika",
                "Osobna iskaznica broj", "YYYY-MM-DD", "Izdavatelj",
                "Broj putovnice", "YYYY-MM-DD", "Izdavatelj",
                "Jedno od: Aktivni/Veteran/Ostalo", "da/ne", "Broj (npr. 30)",
                "Hrvači/Hrvačice/Veterani/Ostalo", "base64 slika (opcionalno)",
                "da/ne", "da/ne"
            ]
        })
        guide.to_excel(writer, index=False, sheet_name="Upute")
    bio.seek(0)
    return bio.getvalue()

init_state()

# -----------------------------
# Sidebar – logo i brzi pristup
# -----------------------------
with st.sidebar:
    st.header("HK Podravka")
    logo = st.file_uploader("Učitaj logo kluba (PNG/JPG)", type=["png","jpg","jpeg"])
    if logo:
        st.session_state.logo_bytes = logo.read()
    if st.session_state.logo_bytes:
        st.image(st.session_state.logo_bytes, caption="Logo")

    st.markdown("**Brze radnje**")
    colA, colB = st.columns(2)
    with colA:
        if st.button("💾 Spremi podatke"):
            save_all()
            st.success("Podaci su spremljeni u /data folder.")
    with colB:
        if st.button("📥 Preuzmi Excel članova"):
            # kreiramo download odmah ispod kroz st.download_button
            pass

    st.divider()
    st.caption("Boje: crvena, bijela, zlatna. Aplikacija je responzivna za mobitele.")

# -----------------------------
# Zaglavlje
# -----------------------------
title_cols = st.columns([1,6])
with title_cols[0]:
    if st.session_state.logo_bytes:
        st.image(st.session_state.logo_bytes, use_column_width=True)
with title_cols[1]:
    st.title("Hrvački klub Podravka — Administracija")

# -----------------------------
# Glavni tabovi
# -----------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "🏟️ Osnovni podaci", "👥 Članovi", "📄 Dokumenti", "🛠️ Administracija"
])

# -----------------------------
# Tab 1: Osnovni podaci
# -----------------------------
with tab1:
    st.subheader("Podaci o klubu")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.session_state.club_info["Klub"] = st.text_input("KLUB (IME)", st.session_state.club_info["Klub"])
        st.session_state.club_info["Ulica i broj"] = st.text_input("ULICA I KUĆNI BROJ", st.session_state.club_info["Ulica i broj"])
        st.session_state.club_info["Grad i poštanski broj"] = st.text_input("GRAD I POŠTANSKI BROJ", st.session_state.club_info["Grad i poštanski broj"])
    with c2:
        st.session_state.club_info["Email"] = st.text_input("E-mail", st.session_state.club_info["Email"])
        st.session_state.club_info["OIB"] = st.text_input("OIB", st.session_state.club_info["OIB"])
        st.session_state.club_info["IBAN"] = st.text_input("IBAN RAČUN", st.session_state.club_info["IBAN"])
    with c3:
        st.session_state.club_info["Web"] = st.text_input("Web stranica", st.session_state.club_info["Web"])
        st.session_state.club_info["Instagram"] = st.text_input("Instagram (link) — mjesto za društvene mreže", st.session_state.club_info["Instagram"])
        st.session_state.club_info["Facebook"] = st.text_input("Facebook (link)", st.session_state.club_info["Facebook"])
        st.session_state.club_info["TikTok"] = st.text_input("TikTok (link)", st.session_state.club_info["TikTok"])

    st.markdown("---")
    st.subheader("Dužnosnici")
    st.caption("Dodaj: Predsjednik kluba, Tajnik, članovi Predsjedništva i Nadzorni odbor.")

    # Forma za unos dužnosnika
    with st.form("dodaj_duznosnika", clear_on_submit=True):
        role = st.selectbox("Uloga", ["Predsjednik", "Tajnik", "Predsjedništvo", "Nadzorni odbor"])
        fullname = st.text_input("Ime i prezime")
        phone = st.text_input("Kontakt broj")
        email = st.text_input("E-mail adresa")
        submitted = st.form_submit_button("➕ Dodaj dužnosnika")
        if submitted:
            new_row = {
                OFFICIALS_COLUMNS[0]: role,
                OFFICIALS_COLUMNS[1]: fullname,
                OFFICIALS_COLUMNS[2]: phone,
                OFFICIALS_COLUMNS[3]: email,
            }
            st.session_state.officials_df = pd.concat([st.session_state.officials_df, pd.DataFrame([new_row])], ignore_index=True)
            save_all()
            st.success("Dodano!")

    # Prikaz i uređivanje
    st.dataframe(st.session_state.officials_df, use_container_width=True)

    # Brisanje po indeksu
    with st.expander("🗑️ Brisanje dužnosnika"):
        idx = st.number_input("Indeks za brisanje (0-n)", min_value=0, step=1, value=0)
        if st.button("Obriši odabrani red"):
            if 0 <= idx < len(st.session_state.officials_df):
                st.session_state.officials_df = st.session_state.officials_df.drop(st.session_state.officials_df.index[idx]).reset_index(drop=True)
                save_all()
                st.warning("Obrisano.")

# -----------------------------
# Tab 2: Članovi
# -----------------------------
with tab2:
    st.subheader("Upravljanje članovima")

    # Predložak za Excel – download
    tmpl_bytes = None
    @st.cache_data
    def get_template_bytes():
        import pandas as pd, io
        from xlsxwriter import Workbook  # noqa: F401
        # generira isti template kao helper u glavnoj datoteci
        columns = [
            "Ime", "Prezime", "Datum rođenja", "Spol (M/Ž)",
            "OIB", "Mjesto prebivališta",
            "Email sportaša", "Email roditelja/skrbnika",
            "Broj osobne iskaznice", "OI vrijedi do", "OI izdao",
            "Broj putovnice", "Putovnica vrijedi do", "Putovnicu izdao",
            "Status (Aktivni/Veteran/Ostalo)", "Plaća članarinu", "Iznos članarine (EUR)",
            "Grupa", "Slika (base64)",
            "Privola (da/ne)", "Pristupnica (da/ne)"
        ]
        bio = io.BytesIO()
        with pd.ExcelWriter(bio, engine="xlsxwriter") as writer:
            pd.DataFrame(columns=columns).to_excel(writer, index=False, sheet_name="Clanovi")
            guide = pd.DataFrame({
                "Polje": columns,
                "Napomena": [
                    "Obavezno Ime", "Obavezno Prezime", "Format YYYY-MM-DD", "M ili Ž",
                    "OIB (11 znamenki)", "Grad/naselje",
                    "Email sportaša", "Email roditelja/skrbnika",
                    "Osobna iskaznica broj", "YYYY-MM-DD", "Izdavatelj",
                    "Broj putovnice", "YYYY-MM-DD", "Izdavatelj",
                    "Jedno od: Aktivni/Veteran/Ostalo", "da/ne", "Broj (npr. 30)",
                    "Hrvači/Hrvačice/Veterani/Ostalo", "base64 slika (opcionalno)",
                    "da/ne", "da/ne"
                ]
            })
            guide.to_excel(writer, index=False, sheet_name="Upute")
        bio.seek(0)
        return bio.getvalue()

    st.download_button("📄 Preuzmi predložak Excel tablice", data=get_template_bytes(),
                       file_name="predlozak_clanova.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    # Upload Excel-a s članovima
    up_file = st.file_uploader("📤 Učitaj članove putem Excel tablice (.xlsx)", type=["xlsx"])
    if up_file is not None:
        try:
            df = pd.read_excel(up_file)
            # osiguraj sve kolone
            for col in MEMBER_COLUMNS:
                if col not in df.columns:
                    df[col] = ""
            df = df[MEMBER_COLUMNS]
            st.session_state.members_df = pd.concat([st.session_state.members_df, df], ignore_index=True)
            save_all()
            st.success(f"Uvezeno članova: {len(df)}")
        except Exception as e:
            st.error(f"Greška pri učitavanju: {e}")

    st.markdown("---")
    st.subheader("Brzi unos novog člana (nije sve obavezno)")
    with st.form("novi_clan", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            ime = st.text_input("Ime")
            prezime = st.text_input("Prezime")
            datum = st.date_input("Datum rođenja", value=None, format="YYYY-MM-DD")
            spol = st.selectbox("Spol", ["", "M", "Ž"])
            oib = st.text_input("OIB")
            preb = st.text_input("Mjesto prebivališta")
        with c2:
            email_sportasa = st.text_input("Email sportaša")
            email_roditelja = st.text_input("Email roditelja/skrbnika")
            oi_broj = st.text_input("Broj osobne iskaznice")
            oi_do = st.date_input("OI vrijedi do", value=None, format="YYYY-MM-DD")
            oi_izdao = st.text_input("OI izdao")
            put_broj = st.text_input("Broj putovnice")
        with c3:
            put_do = st.date_input("Putovnica vrijedi do", value=None, format="YYYY-MM-DD")
            put_izdao = st.text_input("Putovnicu izdao")
            status = st.selectbox("Status", ["Aktivni", "Veteran", "Ostalo"])
            placanje = st.checkbox("Plaća članarinu", value=True if status=="Aktivni" else False)
            iznos = st.number_input("Iznos članarine (EUR)", min_value=0, max_value=1000, value=30 if placanje else 0, step=5)
            grupa = st.selectbox("Grupa", DEFAULT_GROUPS)
            slika = st.file_uploader("Slika člana (opcionalno)", type=["png","jpg","jpeg"])
            privola = st.checkbox("Privola dostavljena", value=False)
            pristupnica = st.checkbox("Pristupnica dostavljena", value=False)

        submitted = st.form_submit_button("➕ Dodaj člana")
        if submitted:
            # priprema vrijednosti
            def _dt(v):
                if v is None or v == "":
                    return ""
                return str(v)
            b64img = ""
            if slika:
                b64img = base64.b64encode(slika.read()).decode()
            new_row = {
                "Ime": ime, "Prezime": prezime, "Datum rođenja": _dt(datum),
                "Spol (M/Ž)": spol, "OIB": oib, "Mjesto prebivališta": preb,
                "Email sportaša": email_sportasa, "Email roditelja/skrbnika": email_roditelja,
                "Broj osobne iskaznice": oi_broj, "OI vrijedi do": _dt(oi_do), "OI izdao": oi_izdao,
                "Broj putovnice": put_broj, "Putovnica vrijedi do": _dt(put_do), "Putovnicu izdao": put_izdao,
                "Status (Aktivni/Veteran/Ostalo)": status, "Plaća članarinu": "da" if placanje else "ne",
                "Iznos članarine (EUR)": iznos, "Grupa": grupa, "Slika (base64)": b64img,
                "Privola (da/ne)": "da" if privola else "ne",
                "Pristupnica (da/ne)": "da" if pristupnica else "ne",
            }
            st.session_state.members_df = pd.concat([st.session_state.members_df, pd.DataFrame([new_row])], ignore_index=True)
            save_all()
            st.success("Član dodan!")

    st.markdown("### Popis članova")
    # Mini filteri
    fcol1, fcol2, fcol3 = st.columns(3)
    with fcol1:
        f_grupa = st.multiselect("Filtriraj po grupi", DEFAULT_GROUPS)
    with fcol2:
        f_status = st.multiselect("Filtriraj po statusu", ["Aktivni","Veteran","Ostalo"])
    with fcol3:
        f_potvrde = st.selectbox("Privola/Pristupnica", ["Svi", "Samo s obje potvrde", "Bez jedne ili obje"])

    df_show = st.session_state.members_df.copy()
    if f_grupa:
        df_show = df_show[df_show["Grupa"].isin(f_grupa)]
    if f_status:
        df_show = df_show[df_show["Status (Aktivni/Veteran/Ostalo)"].isin(f_status)]
    if f_potvrde == "Samo s obje potvrde":
        df_show = df_show[(df_show["Privola (da/ne)"]=="da") & (df_show["Pristupnica (da/ne)"]=="da")]
    elif f_potvrde == "Bez jedne ili obje":
        df_show = df_show[(df_show["Privola (da/ne)"]!="da") | (df_show["Pristupnica (da/ne)"]!="da")]

    st.dataframe(df_show.drop(columns=["Slika (base64)"]), use_container_width=True)
    # Prikaz slike za odabranog člana
    with st.expander("📸 Pregled fotografije člana (unesi indeks reda)"):
        idx = st.number_input("Indeks", min_value=0, step=1, value=0)
        if 0 <= idx < len(st.session_state.members_df):
            row = st.session_state.members_df.iloc[int(idx)]
            img_b64 = row.get("Slika (base64)", "")
            if isinstance(img_b64, str) and img_b64:
                st.image(base64.b64decode(img_b64))
            else:
                st.info("Nema slike za ovaj red.")

    # Download članova u Excel
    bio = io.BytesIO()
    with pd.ExcelWriter(bio, engine="xlsxwriter") as writer:
        st.session_state.members_df.to_excel(writer, index=False, sheet_name="Clanovi")
    bio.seek(0)
    st.download_button("📥 Preuzmi članove (Excel)", data=bio.getvalue(),
                       file_name="clanovi.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    # Brisanje po indeksu
    with st.expander("🗑️ Brisanje člana po indeksu"):
        idx2 = st.number_input("Indeks za brisanje (0-n)", min_value=0, step=1, value=0, key="del_idx")
        if st.button("Obriši člana"):
            if 0 <= idx2 < len(st.session_state.members_df):
                st.session_state.members_df = st.session_state.members_df.drop(st.session_state.members_df.index[int(idx2)]).reset_index(drop=True)
                save_all()
                st.warning("Član obrisan.")

# -----------------------------
# Tab 3: Dokumenti
# -----------------------------
with tab3:
    st.subheader("Upload klupskih dokumenata")
    st.caption("Npr. Statut kluba, pravilnici, zapisnici…")
    doc = st.file_uploader("📎 Učitaj dokument", type=["pdf","doc","docx","xls","xlsx","png","jpg","jpeg","txt"])
    doc_name = st.text_input("Naziv dokumenta (npr. Statut 2025)")
    if st.button("📤 Spremi dokument") and doc and doc_name:
        path = os.path.join(DOCS_DIR, f"{doc_name}_{doc.name}")
        with open(path, "wb") as f:
            f.write(doc.read())
        st.session_state.docs[doc_name] = path
        st.success(f"Spremljeno kao {path}")

    if st.session_state.docs:
        st.markdown("### Pohranjeni dokumenti")
        for k, v in st.session_state.docs.items():
            st.markdown(f"- **{k}** — `{v}`")

# -----------------------------
# Tab 4: Administracija (meta)
# -----------------------------
with tab4:
    st.subheader("Postavke i metapodaci")
    st.write("Ovdje su sažeti osnovni podaci za javnu stranicu:")
    st.json(st.session_state.club_info)

    st.info("Savjet: Ovu .py datoteku možete staviti na GitHub i pokrenuti preko Streamlit Cloud-a ili lokalno: `streamlit run hk_podravka_app.py`")

# -----------------------------
# Footer
# -----------------------------
st.markdown("---")
st.caption("© Hrvački klub Podravka | Miklinovec 6a, 48000 Koprivnica | OIB: 60911784858 | IBAN: HR6923860021100518154 | Kontakt: hsk-podravka@gmail.com")
