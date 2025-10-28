import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime

# --------------- DB ---------------
def get_conn():
    conn = sqlite3.connect("club.db", check_same_thread=False)
    conn.execute("""CREATE TABLE IF NOT EXISTS coaches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS competitions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kind TEXT,
        custom_kind TEXT,
        name TEXT,
        date_from TEXT,
        date_to TEXT,
        place TEXT,
        style TEXT,
        age_group TEXT,
        country TEXT,
        country_code TEXT,
        team_rank TEXT,
        club_competitors INTEGER,
        total_competitors INTEGER,
        total_clubs INTEGER,
        total_countries INTEGER,
        coaches_text TEXT,
        notes TEXT,
        bulletin_link TEXT,
        results_link TEXT,
        gallery_link TEXT,
        bulletin_file TEXT,
        results_file TEXT
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS competition_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        competition_id INTEGER,
        member_id INTEGER,
        weight_category TEXT,
        style TEXT,
        result_text TEXT
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS competition_photos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        competition_id INTEGER,
        filename TEXT,
        path TEXT,
        uploaded_at TEXT
    )""")
    return conn

def iso3(country_name: str) -> str:
    try:
        import pycountry
        c = pycountry.countries.get(name=country_name)
        if c: return c.alpha_3
        # fuzzy
        from difflib import get_close_matches
        names = [x.name for x in pycountry.countries]
        m = get_close_matches(country_name, names, n=1, cutoff=0.7)
        if m:
            c = pycountry.countries.get(name=m[0])
            return c.alpha_3 if c else ""
    except Exception:
        pass
    return ""

def all_countries_list():
    try:
        import pycountry
        return sorted([c.name for c in pycountry.countries])
    except Exception:
        return []

KINDS = [
    "PRVENSTVO HRVATSKE","MEĐUNARODNI TURNIR","REPREZENTATIVNI NASTUP",
    "HRVAČKA LIGA ZA SENIORE","MEĐUNARODNA HRVAČKA LIGA ZA KADETE",
    "REGIONALNO PRVENSTVO","LIGA ZA DJEVOJČICE","OSTALO"
]
REP_SUB = ["PRVENSTVO EUROPE","PRVENSTVO SVIJETA","PRVENSTVO BALKANA","UWW TURNIR"]
STYLES = ["GR","FS","WW","BW","MODIFICIRANO"]
AGES = ["POČETNICI","U11","U13","U15","U17","U20","U23","SENIORI"]

st.set_page_config(page_title="Natjecanja", layout="wide")
st.title("Natjecanja i rezultati — minimalni modul")

conn = get_conn()

# --------------- Unos novog natjecanja ---------------
st.header("Unos natjecanja")

with st.form("comp_form"):
    kind = st.selectbox("Vrsta natjecanja", KINDS)
    rep_sub = st.selectbox("Podvrsta reprezentativnog nastupa", REP_SUB, disabled=(kind!="REPREZENTATIVNI NASTUP"))
    custom_kind = st.text_input("Upiši vrstu (ako 'OSTALO')", disabled=(kind!="OSTALO"))
    name = st.text_input("Ime natjecanja")
    c1, c2 = st.columns(2)
    date_from = c1.date_input("Datum od", value=date.today())
    date_to = c2.date_input("Datum do", value=date.today())
    place = st.text_input("Mjesto")
    countries = all_countries_list()
    c_country, c_iso = st.columns([3,1])
    with c_country:
        country = st.selectbox("Država (odaberi)", [""] + countries, index=0)
    with c_iso:
        auto_iso = iso3(country) if country else ""
        st.text_input("ISO3 kratica", value=auto_iso, disabled=True)

    style = st.selectbox("Hrvački stil", STYLES)
    age_group = st.selectbox("Uzrast", AGES)

    c3, c4, c5 = st.columns(3)
    team_rank = c3.text_input("Ekipni poredak (npr. 1., 5., 10.)")
    club_competitors = c4.number_input("Broj naših natjecatelja", min_value=0, step=1, value=0)
    total_competitors = c5.number_input("Ukupan broj natjecatelja", min_value=0, step=1, value=0)
    c6, c7 = st.columns(2)
    total_clubs = c6.number_input("Broj klubova", min_value=0, step=1, value=0)
    total_countries = c7.number_input("Broj zemalja", min_value=0, step=1, value=0)

    # Treneri: iz baze + dodatni
    coach_rows = conn.execute("SELECT full_name FROM coaches ORDER BY full_name").fetchall()
    coach_choices = [r[0] for r in coach_rows] if coach_rows else []
    c_coach_sel, c_coach_custom = st.columns([2,1])
    with c_coach_sel:
        coach_mult = st.multiselect("Trener(i) (iz baze)", coach_choices)
    with c_coach_custom:
        coach_custom = st.text_input("Dodatni trener (ime i prezime)")
    coach_all = coach_mult + ([coach_custom] if coach_custom else [])
    coach_text = ", ".join(coach_all)

    notes = st.text_area("Zapažanje trenera (za objave)")
    bulletin_link = st.text_input("Link na bilten/rezultate")
    results_link = st.text_input("Link na službene rezultate")
    gallery_link = st.text_input("Link na objavu na webu (galerija)")

    submit = st.form_submit_button("Spremi natjecanje")

if submit:
    conn.execute("""INSERT INTO competitions
        (kind,custom_kind,name,date_from,date_to,place,style,age_group,country,country_code,
         team_rank,club_competitors,total_competitors,total_clubs,total_countries,
         coaches_text,notes,bulletin_link,results_link,gallery_link, bulletin_file, results_file)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (kind, rep_sub if kind=="REPREZENTATIVNI NASTUP" else custom_kind, name,
         str(date_from), str(date_to), f"{place}, {country}", style, age_group, country, auto_iso,
         team_rank, int(club_competitors), int(total_competitors), int(total_clubs), int(total_countries),
         coach_text, notes, bulletin_link, results_link, gallery_link, "", ""))
    conn.commit()
    st.success("Natjecanje spremljeno.")

st.markdown("---")

# --------------- Uređivanje / brisanje / dupliranje ---------------
st.header("Uredi / briši / dupliciraj")

comp_rows = conn.execute("SELECT id, name, date_from, kind FROM competitions ORDER BY date_from DESC LIMIT 200").fetchall()
comp_options = [""] + [f"{r[0]} – {r[2]} – {r[1]} ({r[3]})" for r in comp_rows]
choice = st.selectbox("Odaberi natjecanje", comp_options)

if choice:
    edit_id = int(choice.split(" – ")[0])
    row = conn.execute("""SELECT id, kind, custom_kind, name, date_from, date_to, place, style, age_group,
                                 country, country_code, team_rank, club_competitors, total_competitors,
                                 total_clubs, total_countries, coaches_text, notes, bulletin_link, results_link, gallery_link
                          FROM competitions WHERE id=?""", (edit_id,)).fetchone()
    (cid, kind_e, custom_kind_e, name_e, df_e, dt_e, place_e, style_e, age_e,
     country_e, iso_e, team_rank_e, club_comp_e, total_comp_e, clubs_e, countries_e,
     coaches_e, notes_e, bull_e, res_e, gal_e) = row
    place_city = (place_e or "").split(",")[0].strip()

    with st.form("edit_comp_form"):
        kind = st.selectbox("Vrsta natjecanja", KINDS, index=KINDS.index(kind_e) if kind_e in KINDS else 0)
        rep_sub = st.selectbox("Podvrsta reprezentativnog nastupa", REP_SUB, disabled=(kind!="REPREZENTATIVNI NASTUP"))
        custom_kind = st.text_input("Upiši vrstu (ako 'OSTALO')", value=custom_kind_e or "", disabled=(kind!="OSTALO"))
        name = st.text_input("Ime natjecanja (ako postoji naziv)", value=name_e or "")
        c1, c2 = st.columns(2)
        date_from = c1.date_input("Datum od", value=pd.to_datetime(df_e).date() if df_e else date.today())
        date_to = c2.date_input("Datum do (ako 1 dan, ostavi isti)", value=pd.to_datetime(dt_e).date() if dt_e else date.today())
        place = st.text_input("Mjesto", value=place_city)

        countries = all_countries_list()
        c_country, c_iso = st.columns([3,1])
        with c_country:
            country = st.selectbox("Država (odaberi)", [""] + countries, index=([""]+countries).index(country_e) if country_e in countries else 0)
        with c_iso:
            auto_iso = iso3(country) if country else ""
            st.text_input("ISO3 kratica", value=auto_iso or (iso_e or ""), disabled=True, key=f"iso3_display_edit_{cid}")

        style = st.selectbox("Hrvački stil", STYLES, index=STYLES.index(style_e) if style_e in STYLES else 0)
        age_group = st.selectbox("Uzrast", AGES, index=AGES.index(age_e) if age_e in AGES else 0)

        c3, c4, c5 = st.columns(3)
        team_rank = c3.text_input("Ekipni poredak (npr. 1., 5., 10.)", value=team_rank_e or "")
        club_competitors = c4.number_input("Broj naših natjecatelja", min_value=0, step=1, value=int(club_comp_e or 0))
        total_competitors = c5.number_input("Ukupan broj natjecatelja", min_value=0, step=1, value=int(total_comp_e or 0))
        c6, c7 = st.columns(2)
        total_clubs = c6.number_input("Broj klubova", min_value=0, step=1, value=int(clubs_e or 0))
        total_countries = c7.number_input("Broj zemalja", min_value=0, step=1, value=int(countries_e or 0))

        coach_rows = conn.execute("SELECT full_name FROM coaches ORDER BY full_name").fetchall()
        coach_choices = [r[0] for r in coach_rows] if coach_rows else []
        preselected = [c for c in (coaches_e or "").split(", ") if c in coach_choices]
        c_coach_sel, c_coach_custom = st.columns([2,1])
        with c_coach_sel:
            coach_mult = st.multiselect("Trener(i) (iz baze)", coach_choices, default=preselected)
        with c_coach_custom:
            coach_custom = st.text_input("Dodatni trener (ime i prezime)", value="")
        coach_all = coach_mult + ([coach_custom] if coach_custom else [])
        coach_text = ", ".join(coach_all) if coach_all else (coaches_e or "")

        notes = st.text_area("Zapažanje trenera (za objave)", value=notes_e or "")
        bulletin_link = st.text_input("Link na bilten/rezultate", value=bull_e or "")
        results_link = st.text_input("Link na službene rezultate", value=res_e or "")
        gallery_link = st.text_input("Link na objavu na webu (galerija)", value=gal_e or "")

        submit_edit = st.form_submit_button("Spremi izmjene")

    if submit_edit:
        conn.execute("""UPDATE competitions SET
                            kind=?, custom_kind=?, name=?, date_from=?, date_to=?, place=?, style=?, age_group=?,
                            country=?, country_code=?, team_rank=?, club_competitors=?, total_competitors=?,
                            total_clubs=?, total_countries=?, coaches_text=?, notes=?, bulletin_link=?, results_link=?, gallery_link=?
                        WHERE id=?""",
                     (kind, rep_sub if kind=="REPREZENTATIVNI NASTUP" else custom_kind, name,
                      str(date_from), str(date_to), f"{place}, {country}", style, age_group,
                      country, auto_iso, team_rank, int(club_competitors), int(total_competitors),
                      int(total_clubs), int(total_countries), coach_text, notes, bulletin_link, results_link, gallery_link,
                      edit_id))
        conn.commit()
        st.success("Izmjene spremljene.")

        st.markdown("---")
        cdel, cdup = st.columns(2)
        with cdel:
            confirm_del = st.checkbox("Potvrdi brisanje", key=f"confirm_del_{edit_id}")
            if st.button("Obriši natjecanje", key=f"btn_delete_{edit_id}"):
                if confirm_del:
                    conn.execute("DELETE FROM competition_results WHERE competition_id=?", (edit_id,))
                    conn.execute("DELETE FROM competition_photos  WHERE competition_id=?", (edit_id,))
                    conn.execute("DELETE FROM competitions WHERE id=?", (edit_id,))
                    conn.commit()
                    st.success("Natjecanje obrisano.")
                else:
                    st.warning("Označi 'Potvrdi brisanje' prije brisanja.")
        with cdup:
            if st.button("Dupliciraj u novi zapis", key=f"btn_duplicate_{edit_id}"):
                conn.execute("""
                    INSERT INTO competitions
                    (kind, custom_kind, name, date_from, date_to, place, style, age_group, country, country_code,
                     team_rank, club_competitors, total_competitors, total_clubs, total_countries,
                     coaches_text, notes, bulletin_link, results_link, gallery_link, bulletin_file, results_file)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                \"\"\", (
                    kind, rep_sub if kind=="REPREZENTATIVNI NASTUP" else custom_kind, (name or "") + " (kopija)",
                    str(date_from), str(date_to), f"{place}, {country}", style, age_group, country, auto_iso,
                    team_rank, int(club_competitors), int(total_competitors), int(total_clubs), int(total_countries),
                    coach_text, notes, bulletin_link, results_link, gallery_link, "", ""
                ))
                conn.commit()
                new_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
                st.success(f"Kreirana kopija natjecanja (ID: {new_id}).")

st.markdown("---")

# --------------- Pregled i pretraga ---------------
st.header("Pregled i pretraga natjecanja")

colf = st.columns(6)
f_kind    = colf[0].selectbox("Vrsta natjecanja", [""] + KINDS, index=0)
with colf[1]:
    f_rep_sub = st.selectbox("Podvrsta (REP)", [""] + REP_SUB, index=0, disabled=(f_kind != "REPREZENTATIVNI NASTUP"))
f_year    = colf[2].text_input("Godina (npr. 2025)")
f_age     = colf[3].text_input("Uzrast (dio naziva)")
f_style   = colf[4].text_input("Stil (GR/FS/WW/BW/MOD)")
f_country = colf[5].text_input("Država (dio naziva)")

if st.button("Pretraži"):
    q = """
        SELECT id, name AS ime, kind AS vrsta, age_group AS uzrast, style AS stil,
               date_from AS od, date_to AS do, place AS mjesto, country AS država, country_code AS ISO3,
               club_competitors AS nastupili, coaches_text AS trener,
               team_rank AS ekipno, total_competitors AS natjecatelja,
               total_clubs AS klubova, total_countries AS zemalja
        FROM competitions WHERE 1=1
    """
    params = []
    if f_kind.strip():    q += " AND kind = ?";               params.append(f_kind)
    if f_year.strip():    q += " AND date_from LIKE ?";       params.append(f"{f_year}%")
    if f_age.strip():     q += " AND age_group LIKE ?";       params.append(f"%{f_age}%")
    if f_style.strip():   q += " AND style LIKE ?";           params.append(f"%{f_style}%")
    if f_country.strip(): q += " AND country LIKE ?";         params.append(f"%{f_country}%")
    if f_kind.strip() == "REPREZENTATIVNI NASTUP" and f_rep_sub.strip():
        q += " AND custom_kind = ?";                          params.append(f_rep_sub)
    q += " ORDER BY date_from DESC"
    cdf = pd.read_sql_query(q, conn, params=params)
else:
    cdf = pd.read_sql_query("""
        SELECT id, name AS ime, kind AS vrsta, age_group AS uzrast, style AS stil,
               date_from AS od, date_to AS do, place AS mjesto, country AS država, country_code AS ISO3,
               club_competitors AS nastupili, coaches_text AS trener
        FROM competitions ORDER BY date_from DESC
    """, conn)

# formatiranje
if 'od' in cdf.columns:
    try:
        cdf['od'] = pd.to_datetime(cdf['od']).dt.strftime('%d.%m.%Y.')
    except Exception:
        pass
if 'do' in cdf.columns:
    try:
        cdf['do'] = pd.to_datetime(cdf['do']).dt.strftime('%d.%m.%Y.')
    except Exception:
        pass
cdf.insert(0, 'R.br.', range(1, len(cdf)+1))
st.dataframe(cdf, use_container_width=True)
