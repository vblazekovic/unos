
# ===================== HRVAČKI KLUB PODRAVKA — SEKCIJA 1 =====================
# Streamlit modul: Osnovni podaci o klubu
# Zalijepi u svoju postojeca.py i pozovi render_prvi_odjeljak() gdje želiš.

import streamlit as st
from io import BytesIO
import json
from datetime import datetime

# ---------- helpers ----------
BRAND = {
    "red": "#C81414",     # klupska crvena
    "gold": "#C8A94A",    # zlatna
    "white": "#FFFFFF",
    "bg": "#ffffff",
}

def _inject_brand_css():
    st.markdown(
        f"""
        <style>
            :root {{
                --brand-red: {BRAND["red"]};
                --brand-gold: {BRAND["gold"]};
                --brand-white: {BRAND["white"]};
            }}
            .brand-card {{
                border: 1px solid rgba(0,0,0,0.08);
                border-radius: 14px;
                padding: 14px 18px;
                background: var(--brand-white);
                box-shadow: 0 2px 16px rgba(0,0,0,0.04);
            }}
            .brand-header {{
                display:flex; align-items:center; gap:14px; margin-bottom:8px;
            }}
            .brand-badge {{
                background: var(--brand-gold);
                color: #111;
                font-weight: 700;
                padding: 2px 10px;
                border-radius: 999px;
                font-size: 12px;
                letter-spacing: .3px;
            }}
            .brand-title {{
                font-weight: 800; font-size: 22px; margin: 0;
            }}
            .brand-sub {{
                color:#555; font-size: 13px; margin-top:2px;
            }}
            .brand-hr {{
                border: none; height: 1px; background: rgba(0,0,0,.08); margin: 10px 0 12px 0;
            }}
            .save-row button[kind="secondary"] {{
                border-color: var(--brand-gold) !important;
            }}
            .stDownloadButton button, .stButton>button {{
                border-radius: 10px !important;
                font-weight: 700 !important;
            }}
            /* istakni obavezna polja vizualno */
            .required:after {{
                content:" *";
                color: var(--brand-red);
                font-weight: 900;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )

def _init_state():
    ss = st.session_state
    if "club_data" not in ss:
        ss.club_data = {
            "klub": "HRVAČKI KLUB PODRAVKA",
            "ulica": "Miklinovec 6a",
            "grad_postanski": "48000 Koprivnica",
            "iban": "HR6923860021100518154",
            "oib": "60911784858",
            "email": "hsk-podravka@gmail.com",
            "web": "https://hk-podravka.com",
            "social": {
                "instagram": "",
                "facebook": "",
                "tiktok": ""
            },
            # osobe
            "predsjednik": {"ime_prezime": "", "kontakt": "", "email": ""},
            "tajnik": {"ime_prezime": "", "kontakt": "", "email": ""},
            "predsjednistvo": [],   # list[dict]
            "nadzorni_odbor": [],   # list[dict]
            # dokumenti (pohranjujemo meta, ne datoteke trajno)
            "dokumenti": {
                "statut": None,
                "ostali": []   # list of {"name":..., "uploaded_at":...}
            },
            # logo meta
            "logo_path_hint": "assets/logo.png"
        }

def _download_json_button(data: dict, label: str, filename: str):
    buf = BytesIO()
    buf.write(json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"))
    st.download_button(label=label, data=buf.getvalue(), file_name=filename, mime="application/json")

def _upload_json_and_load(label: str, key: str):
    up = st.file_uploader(label, type=["json"], key=key)
    if up is not None:
        try:
            loaded = json.load(up)
            st.session_state.club_data = loaded
            st.success("✅ Učitani podaci su uspješno postavljeni.")
        except Exception as e:
            st.error(f"⚠️ Greška pri učitavanju JSON-a: {e}")

def _people_table_editor(title: str, list_key: str, help_text: str = ""):
    st.markdown(f"**{title}**")
    items = st.session_state.club_data.get(list_key, [])
    # Data editor
    edited = st.data_editor(
        items if items else [{"ime_prezime": "", "kontakt": "", "email": ""}],
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "ime_prezime": st.column_config.TextColumn("Ime i prezime", required=False),
            "kontakt": st.column_config.TextColumn("Kontakt broj", required=False),
            "email": st.column_config.TextColumn("E-mail adresa", required=False),
        },
        help=help_text
    )
    st.session_state.club_data[list_key] = edited

# ---------- main renderer ----------
def render_prvi_odjeljak():
    st.set_page_config(page_title="HK Podravka — Admin", page_icon="🥇", layout="wide")
    _inject_brand_css()
    _init_state()

    # HEADER
    with st.container():
        cols = st.columns([1, 3])
        with cols[0]:
            # Logo — pokušaj učitati iz putanje; fallback na uploader
            st.markdown('<div class="brand-badge">HK PODRAVKA</div>', unsafe_allow_html=True)
            logo_col1, logo_col2 = st.columns([1,1])
            with logo_col1:
                st.image(st.session_state.club_data.get("logo_path_hint", "assets/logo.png"), caption="Logo (putanja)", use_column_width=True)
            with logo_col2:
                new_logo = st.file_uploader("Promijeni logo (PNG/JPG)", type=["png","jpg","jpeg"], key="logo_upload")
                if new_logo:
                    st.image(new_logo, caption="Novi logo (nespremjeno u datoteke)", use_column_width=True)
                    st.info("Napomena: U ovoj fazi logo se ne sprema na disk. Path možeš promijeniti dolje u polju 'Putanja do loga'.")
        with cols[1]:
            st.markdown('<p class="brand-title">Administracija — Osnovni podaci o klubu</p>', unsafe_allow_html=True)
            st.markdown('<p class="brand-sub">Ova sekcija služi kao centralno mjesto za unos i uređivanje službenih podataka kluba te osoba u tijelima upravljanja. Dizajn je prilagođen za mobitele.</p>', unsafe_allow_html=True)

    st.markdown('<hr class="brand-hr" />', unsafe_allow_html=True)

    # OSNOVNI PODACI
    with st.container():
        st.markdown("### 🏛️ Osnovni podaci")
        bcol1, bcol2, bcol3 = st.columns([1.1,1,1])
        with bcol1:
            st.text_input("KLUB (IME)", key="cd_klub", value=st.session_state.club_data["klub"])
            st.text_input("ULICA I KUĆNI BROJ", key="cd_ulica", value=st.session_state.club_data["ulica"])
            st.text_input("GRAD I POŠTANSKI BROJ", key="cd_grad", value=st.session_state.club_data["grad_postanski"])
        with bcol2:
            st.text_input("IBAN RAČUN", key="cd_iban", value=st.session_state.club_data["iban"])
            st.text_input("OIB", key="cd_oib", value=st.session_state.club_data["oib"])
            st.text_input("E-mail", key="cd_email", value=st.session_state.club_data["email"])
        with bcol3:
            st.text_input("Web stranica", key="cd_web", value=st.session_state.club_data["web"])
            st.text_input("Putanja do loga", key="cd_logo_path", value=st.session_state.club_data.get("logo_path_hint","assets/logo.png"))
            st.markdown("&nbsp;")

    # DRUŠTVENE MREŽE
    st.markdown("### 🔗 Društvene mreže")
    s1, s2, s3 = st.columns(3)
    with s1:
        st.text_input("Instagram URL", key="cd_instagram", value=st.session_state.club_data["social"].get("instagram",""))
    with s2:
        st.text_input("Facebook URL", key="cd_facebook", value=st.session_state.club_data["social"].get("facebook",""))
    with s3:
        st.text_input("TikTok URL", key="cd_tiktok", value=st.session_state.club_data["social"].get("tiktok",""))

    st.markdown('<hr class="brand-hr" />', unsafe_allow_html=True)

    # OSOBE
    st.markdown("### 👥 Tijela kluba")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Predsjednik**")
        p_ime = st.text_input("Ime i prezime (predsjednik)", key="cd_preds_ime", value=st.session_state.club_data["predsjednik"]["ime_prezime"])
        p_kontakt = st.text_input("Kontakt broj (predsjednik)", key="cd_preds_kontakt", value=st.session_state.club_data["predsjednik"]["kontakt"])
        p_email = st.text_input("E-mail (predsjednik)", key="cd_preds_email", value=st.session_state.club_data["predsjednik"]["email"])
    with c2:
        st.markdown("**Tajnik**")
        t_ime = st.text_input("Ime i prezime (tajnik)", key="cd_taj_ime", value=st.session_state.club_data["tajnik"]["ime_prezime"])
        t_kontakt = st.text_input("Kontakt broj (tajnik)", key="cd_taj_kontakt", value=st.session_state.club_data["tajnik"]["kontakt"])
        t_email = st.text_input("E-mail (tajnik)", key="cd_taj_email", value=st.session_state.club_data["tajnik"]["email"])

    st.markdown("&nbsp;")
    _people_table_editor("Članovi predsjedništva", "predsjednistvo", help_text="Dodajte/uređujte članove. Po potrebi koristite +/- za redove.")
    _people_table_editor("Nadzorni odbor", "nadzorni_odbor", help_text="Dodajte/uređujte članove. Po potrebi koristite +/- za redove.")

    st.markdown('<hr class="brand-hr" />', unsafe_allow_html=True)

    # DOKUMENTI
    st.markdown("### 📄 Dokumenti")
    dcol1, dcol2 = st.columns([1,1])
    with dcol1:
        statut_file = st.file_uploader("Upload — Statut kluba (PDF/Doc)", type=["pdf","doc","docx"])
        if statut_file:
            st.session_state.club_data["dokumenti"]["statut"] = {
                "name": statut_file.name,
                "uploaded_at": datetime.now().isoformat(timespec="seconds")
            }
            st.success(f"Statut učitan: {statut_file.name}")
        # prikaz statusa
        current_statut = st.session_state.club_data["dokumenti"]["statut"]
        if current_statut:
            st.info(f"Trenutno postavljen Statut: **{current_statut['name']}** (upload: {current_statut['uploaded_at']})")
    with dcol2:
        other_files = st.file_uploader("Upload — Ostali dokumenti (više datoteka)", accept_multiple_files=True, type=["pdf","jpg","jpeg","png","doc","docx","xls","xlsx"])
        if other_files:
            for f in other_files:
                st.session_state.club_data["dokumenti"]["ostali"].append({
                    "name": f.name,
                    "uploaded_at": datetime.now().isoformat(timespec="seconds")
                })
            st.success(f"Učitano: {len(other_files)} dokumenata")

        if st.session_state.club_data["dokumenti"]["ostali"]:
            st.write("**Popis ostalih dokumenata:**")
            st.dataframe(st.session_state.club_data["dokumenti"]["ostali"], use_container_width=True)

    st.markdown('<hr class="brand-hr" />', unsafe_allow_html=True)

    # SPREMI / UVEZI
    st.markdown("### 💾 Spremanje / Uvoz podataka")
    with st.container():
        # sinkroniziraj state iz inputa
        st.session_state.club_data.update({
            "klub": st.session_state.cd_klub,
            "ulica": st.session_state.cd_ulica,
            "grad_postanski": st.session_state.cd_grad,
            "iban": st.session_state.cd_iban,
            "oib": st.session_state.cd_oib,
            "email": st.session_state.cd_email,
            "web": st.session_state.cd_web,
            "logo_path_hint": st.session_state.cd_logo_path,
            "social": {
                "instagram": st.session_state.cd_instagram,
                "facebook": st.session_state.cd_facebook,
                "tiktok": st.session_state.cd_tiktok,
            },
            "predsjednik": {
                "ime_prezime": p_ime,
                "kontakt": p_kontakt,
                "email": p_email,
            },
            "tajnik": {
                "ime_prezime": t_ime,
                "kontakt": t_kontakt,
                "email": t_email,
            },
        })

        sc1, sc2, sc3 = st.columns([1,1,1])
        with sc1:
            _download_json_button(st.session_state.club_data, "⬇️ Preuzmi JSON (sekcija 1)", "hk_podravka_osnovni_podaci.json")
        with sc2:
            _upload_json_and_load("⬆️ Uvezi JSON (sekcija 1)", key="json_upload_1")
        with sc3:
            if st.button("✅ Spremi u session (lokalno)"):
                st.success("Podaci su ažurirani u memoriji aplikacije.")

    st.markdown('<hr class="brand-hr" />', unsafe_allow_html=True)

    # FOOTER INFO
    with st.container():
        st.caption("© HK Podravka — Admin modul · Boje: crvena, bijela, zlatna · Sekcija 1/8")
# =================== / SEKCIJA 1 ===================
