import streamlit as st
from datetime import datetime
import pandas as pd
import os
import sys
import altair as alt
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch

# S'assurer que le répertoire principal est importable
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)

# Import des fonctions (météo, saints, horoscope, blague)
try:
    from requete_page1 import (
        get_weather_data,
        get_saints_data,
        get_horoscope_data,
        get_blague_data
    )
    from styles import GLOBAL_STYLE
    from recommendations_generator import generate_recommendations, format_recommendations_for_display
except ImportError as e:
    st.error(f"Erreur d'importation des fonctions : {e}")
    st.stop()

# Appliquer le style global
st.markdown(GLOBAL_STYLE, unsafe_allow_html=True)

# ---------- Helpers ----------
def _safe_df(df_like):
    try:
        return pd.DataFrame(df_like)
    except Exception:
        return pd.DataFrame()

def _fmt(value, decimals=1, unit=""):
    try:
        v = float(value)
        s = f"{v:.{decimals}f}" if decimals > 0 else f"{v:.0f}"
        return f"{s}{unit}"
    except Exception:
        return "N/A"

def _deg_to_cardinal(deg):
    try:
        d = float(deg) % 360
    except Exception:
        return None
    dirs = ["N","NNE","NE","ENE","E","ESE","SE","SSE",
            "S","SSW","SW","WSW","W","WNW","NW","NNW"]
    idx = int((d + 11.25) // 22.5) % 16
    return dirs[idx]

def _wind_arrow_inline(deg, size=20):
    """Flèche + libellé en ligne, taille forcée."""
    try:
        d = float(deg) % 360
        d_txt = f"{d:.0f}"
        card = _deg_to_cardinal(d) or "—"
    except Exception:
        return '<span style="opacity:.75;">—</span>'
    return f"""
    <span style="display:inline-flex;align-items:center;gap:.45rem;">
      <svg style="width:{size}px;height:{size}px;flex:0 0 auto;"
           viewBox="0 0 28 28" xmlns="http://www.w3.org/2000/svg" aria-label="Direction du vent">
        <g transform="rotate({d}, 14, 14)">
          <line x1="14" y1="22" x2="14" y2="6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          <polygon points="14,3 17,8 11,8" fill="currentColor"/>
        </g>
        <circle cx="14" cy="14" r="12" fill="none" stroke="currentColor" stroke-opacity=".25" stroke-width="1"/>
      </svg>
      <span style="font-size:.95rem;opacity:.8;">{card} ({d_txt}°)</span>
    </span>
    """

def _uv_risk_label(uvi):
    try:
        u = float(uvi)
    except Exception:
        return "—"
    if u < 3: return "Faible"
    if u < 6: return "Modéré"
    if u < 8: return "Élevé"
    if u < 11: return "Très élevé"
    return "Extrême"

def _sec_to_hm(sec):
    try:
        s = int(round(float(sec)))
        h, r = divmod(s, 3600)
        m = r // 60
        return f"{h}h{m:02d}"
    except Exception:
        return "—"

def _fmt_hhmm(ts):
    try:
        return pd.to_datetime(ts).strftime("%H:%M")
    except Exception:
        return "—"

SIGNE_OPTIONS = [
    ("aries", "♈ Bélier"), ("taurus", "♉ Taureau"), ("gemini", "♊ Gémeaux"),
    ("cancer", "♋ Cancer"), ("leo", "♌ Lion"), ("virgo", "♍ Vierge"),
    ("libra", "♎ Balance"), ("scorpio", "♏ Scorpion"), ("sagittarius", "♐ Sagittaire"),
    ("capricorn", "♑ Capricorne"), ("aquarius", "♒ Verseau"), ("pisces", "♓ Poissons"),
]
SIGNE_KEYS = [k for k, _ in SIGNE_OPTIONS]
SIGNE_LABELS = {k: lbl for k, lbl in SIGNE_OPTIONS}

def _line_chart(df: pd.DataFrame, x_col: str, y_col: str, y_title: str):
    if df.empty or x_col not in df or y_col not in df:
        st.info("Aucune donnée graphique disponible.")
        return
    chart = (
        alt.Chart(df)
        .mark_line(point=True)
        .encode(
            x=alt.X(x_col, title="Heure"),
            y=alt.Y(y_col, title=y_title),
            tooltip=[x_col, y_col],
        )
        .properties(height=240)
        .interactive()
    )
    st.altair_chart(chart, use_container_width=True)

def _line_chart_temp_duo(df: pd.DataFrame, x_col: str, temp_col: str, felt_col: str):
    if df.empty or any(c not in df for c in [x_col, temp_col, felt_col]):
        st.info("Aucune donnée graphique disponible.")
        return
    df = df.copy()
    df["idx"] = range(len(df))
    long_df = df.melt(id_vars=[x_col, "idx"], value_vars=[temp_col, felt_col],
                      var_name="Série", value_name="Valeur")
    color_scale = alt.Scale(domain=[temp_col, felt_col], range=["#E4572E", "#2E6BE4"])
    base = (
        alt.Chart(long_df)
        .mark_line(point=True)
        .encode(
            x=alt.X(x_col, title="Heure"),
            y=alt.Y("Valeur:Q", title="°C"),
            color=alt.Color("Série:N", scale=color_scale, legend=None),
            tooltip=[x_col, "Série", "Valeur"]
        ).properties(height=240).interactive()
    )
    labels = (
        alt.Chart(long_df)
        .transform_joinaggregate(max_idx="max(idx)", groupby=["Série"])
        .transform_filter("datum.idx == datum.max_idx")
        .mark_text(align="left", dx=6, dy=-6, fontSize=12)
        .encode(x=alt.X(x_col), y=alt.Y("Valeur:Q"), text=alt.Text("Série"),
                color=alt.Color("Série:N", scale=color_scale, legend=None))
    )
    st.altair_chart(base + labels, use_container_width=True)

def _chart_7days(df: pd.DataFrame):
    if df.empty: return
    
    # Base commune
    base = alt.Chart(df).encode(x=alt.X("Jour:N", sort=None, title=None))
    
    # Barre pour la pluie
    bar = base.mark_bar(opacity=0.3, color="#4A90E2").encode(
        y=alt.Y("Pluie (mm):Q", title="Précipitations (mm)"),
        tooltip=["Jour", "Pluie (mm)", "Proba (%)"]
    )
    
    # Lignes pour Temp Max et Min
    line_max = base.mark_line(color="#E4572E", point=True).encode(
        y=alt.Y("Max (°C):Q", title="Température (°C)"),
        tooltip=["Jour", "Max (°C)"]
    )
    line_min = base.mark_line(color="#2E6BE4", point=True).encode(
        y=alt.Y("Min (°C):Q"),
        tooltip=["Jour", "Min (°C)"]
    )
    
    # On combine le tout
    chart = alt.layer(bar, line_max + line_min).resolve_scale(y='independent').properties(height=350)
    st.altair_chart(chart, use_container_width=True)

# --- Helper pour les emojis météo ---
def _get_weather_emoji(code):
    try:
        c = int(code)
    except:
        return "🤷"
        
    if c == 0: return "☀️"             # Ciel dégagé
    if c in [1, 2, 3]: return "⛅"     # Partiellement nuageux
    if c in [45, 48]: return "🌫️"     # Brouillard
    if c in [51, 53, 55]: return "🌦️" # Bruine
    if c in [61, 63, 65]: return "🌧️" # Pluie
    if c in [71, 73, 75]: return "❄️" # Neige
    if c in [80, 81, 82]: return "🌦️" # Averses
    if c in [95, 96, 99]: return "⛈️" # Orage
    return "🤷"

# --- Etat ---
def _ensure_state():
    st.session_state.setdefault("signe_sel", "leo")
    st.session_state.setdefault("refresh_horoscope", False)
    st.session_state.setdefault("horoscope_sign_key", None)

    st.session_state.setdefault("weather_data", None)
    st.session_state.setdefault("saints_data", None)
    st.session_state.setdefault("horoscope_data", None)
    st.session_state.setdefault("blague_data", None)

    st.session_state.setdefault("bootstrapped", False)
    st.session_state.setdefault("bootstrapped_for", None)

def _trigger_horo_refresh():
    st.session_state.refresh_horoscope = True

def _current_place_id():
    ville = st.session_state.get("ville_selectionnee", "")
    lat = st.session_state.get("latitude", "")
    lon = st.session_state.get("longitude", "")
    return f"{ville}|{lat}|{lon}"

def _fetch_all():
    progress_bar = st.progress(0)
    status = st.empty()
    try:
        status.info("🌤️ Récupération des données météo…")
        progress_bar.progress(25)
        st.session_state.weather_data = get_weather_data(st.session_state.latitude, st.session_state.longitude)

        status.info("📿 Récupération des saints du jour…")
        progress_bar.progress(50)
        st.session_state.saints_data = get_saints_data()

        status.info("🔮 Récupération de l'horoscope…")
        progress_bar.progress(75)
        st.session_state.horoscope_data = get_horoscope_data(st.session_state.signe_sel)
        st.session_state.horoscope_sign_key = st.session_state.signe_sel
        st.session_state.refresh_horoscope = False

        status.info("😄 Récupération de la blague du jour…")
        progress_bar.progress(95)
        st.session_state.blague_data = get_blague_data()

        progress_bar.progress(100)
        status.success("✅ Toutes les données ont été récupérées !")
        st.toast("Mise à jour terminée 🎉", icon="✅")
    except Exception as e:
        status.empty()
        progress_bar.empty()
        st.error("❌ Erreur lors de la récupération des données.")
        st.exception(e)

def show_data_page():
    _ensure_state()

    if "latitude" not in st.session_state or "longitude" not in st.session_state:
        st.error("❌ Aucune ville sélectionnée. Redirection vers l'accueil...")
        st.info("📍 Veuillez sélectionner une ville sur la page d'accueil.")
        
        # Redirection automatique après 2 secondes
        import time
        time.sleep(1)
        st.switch_page("Accueil.py")
        return

    # Auto-récupération à l’ouverture / changement de ville
    current_id = _current_place_id()
    if st.session_state.bootstrapped_for != current_id:
        st.session_state.bootstrapped = False
        st.session_state.bootstrapped_for = current_id
    if not st.session_state.bootstrapped:
        _fetch_all()
        st.session_state.bootstrapped = True

    # En-tête
    st.title(f"📊 Données pour {st.session_state.ville_selectionnee}")
    st.caption(f"📍 {st.session_state.latitude:.4f}, {st.session_state.longitude:.4f} • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    top_left, top_right = st.columns([1, 1])
    with top_left:
        if st.button("🏠 Retour à l'accueil"):
            st.session_state.page = "accueil"
            st.rerun()
    with top_right:
        st.write("")
        if st.button("🔄 Actualiser maintenant", type="primary"):
            _fetch_all()

    # --- ONGLETS ---
    tab_actuel, tab_prevision, tab_stats, tab_vent, tab_precip, tab_soleil, tab_confort, tab_jour_nuit, tab_reco = st.tabs([
        "🌤️ Météo actuelle", 
        "📅 Prévisions 7 jours",
        "📊 Statistiques",
        "💨 Vent & Pression",
        "💧 Précipitations",
        "☀️ Ensoleillement & UV",
        "🌡️ Confort",
        "🌙 Jour vs Nuit",
        "🎯 Recommandations"
    ])

    # --- ONGLET 1 ---
    with tab_actuel:
        # Deux colonnes
        col_left, col_right = st.columns(2)

        # ============ GAUCHE ============
        with col_left:
            weather_data = st.session_state.get("weather_data")

            # Météo actuelle
            with st.expander("🌤️ Données Météo", expanded=True):
                with st.container(border=True):
                    st.markdown("<div class='card-title'>🌡️ Météo actuelle</div>", unsafe_allow_html=True)

                    if weather_data and "current" in weather_data:
                        current = weather_data["current"]
                        c1, c2, c3 = st.columns([1, 1, 1])

                        # Température
                        with c1:
                            temp_txt = _fmt(current.get("temperature_2m"), 1, " °C")
                            ressenti_txt = _fmt(current.get("apparent_temperature"), 1, " °C")
                            st.markdown("<p class='metric-label'>Température</p>", unsafe_allow_html=True)
                            st.markdown(f"<p class='metric-value'>{temp_txt}</p>", unsafe_allow_html=True)
                            st.markdown(f"<p class='metric-sub'>Ressenti : {ressenti_txt}</p>", unsafe_allow_html=True)

                        # Humidité
                        with c2:
                            hum_txt = _fmt(current.get("relative_humidity_2m"), 0, " %")
                            st.markdown("<p class='metric-label'>Humidité</p>", unsafe_allow_html=True)
                            st.markdown(f"<p class='metric-value'>{hum_txt}</p>", unsafe_allow_html=True)

                        # Vent (vitesse + flèche inline)
                        with c3:
                            ws = _fmt(current.get("wind_speed_10m"), 1, "")
                            wind_dir_deg = None
                            for k in ["wind_direction_10m","winddirection_10m","wind_direction"]:
                                if k in current:
                                    wind_dir_deg = current.get(k); break
                            st.markdown("<p class='metric-label'>Vent</p>", unsafe_allow_html=True)
                            st.markdown(
                                f"<p class='metric-value'>{ws}<span class='metric-unit'>&nbsp;km/h</span> {_wind_arrow_inline(wind_dir_deg, size=20)}</p>",
                                unsafe_allow_html=True
                            )

                        # Prochaine pluie
                        if weather_data and "hourly" in weather_data and weather_data["hourly"]:
                            df_p = _safe_df(weather_data["hourly"][:24]).copy()
                            if "precipitation_probability" in df_p and "date" in df_p:
                                try:
                                    df_p["Heure"] = pd.to_datetime(df_p["date"]).dt.strftime("%d-%m %Hh")
                                    thr = 50
                                    mask = pd.to_numeric(df_p["precipitation_probability"], errors="coerce") >= thr
                                    idxs = df_p.index[mask]
                                    if len(idxs) > 0:
                                        h = df_p.loc[idxs[0], "Heure"]
                                        p = float(df_p.loc[idxs[0], "precipitation_probability"])
                                        st.warning(f"🌧️ Prochaine pluie probable (≥ {thr}%) : **{h}** (~{p:.0f}%)")
                                    else:
                                        st.success("🌞 Pas de pluie prévue (> 50%) dans les prochaines 24 h.")
                                except Exception:
                                    pass
                    else:
                        st.caption("— En attente d'actualisation —")

            # Prévisions (graphiques)
            if weather_data and "hourly" in weather_data and len(weather_data["hourly"]) > 0:
                with st.container(border=True):
                    st.markdown("<div class='card-title'>⏰ Prévisions horaires (24 h)</div>", unsafe_allow_html=True)
                    hourly_df = _safe_df(weather_data["hourly"][:24]).copy()

                    if "date" in hourly_df.columns:
                        try:
                            hourly_df["dt"] = pd.to_datetime(hourly_df["date"])
                            hourly_df["Heure"] = hourly_df["dt"].dt.strftime("%d-%m %Hh")
                        except Exception:
                            hourly_df["Heure"] = hourly_df["date"].astype(str)

                        # Température + Ressenti
                        if {"temperature_2m", "apparent_temperature"}.issubset(hourly_df.columns):
                            df_temp = hourly_df.rename(columns={
                                "temperature_2m": "Température (°C)",
                                "apparent_temperature": "Ressenti (°C)"
                            })[["Heure", "Température (°C)", "Ressenti (°C)"]]
                            _line_chart_temp_duo(df_temp, x_col="Heure",
                                                 temp_col="Température (°C)", felt_col="Ressenti (°C)")

                        # Pluie (%)
                        if "precipitation_probability" in hourly_df.columns:
                            df_rain = hourly_df.rename(columns={"precipitation_probability": "Pluie (%)"})
                            _line_chart(df_rain, x_col="Heure", y_col="Pluie (%)", y_title="Probabilité de pluie (%)")
                    else:
                        st.info("Structure des prévisions inattendue.")

            # Soleil & UV
            with st.expander("☀️ Soleil & UV (aujourd'hui)", expanded=True):
                with st.container(border=True):
                    st.markdown("<div class='card-title'>☀️ Soleil & UV</div>", unsafe_allow_html=True)
                    daily_list = weather_data.get("daily") if weather_data else []
                    daily_today = daily_list[0] if daily_list else {}
                    sunrise = _fmt_hhmm(daily_today.get("sunrise"))
                    sunset  = _fmt_hhmm(daily_today.get("sunset"))
                    daylight = daily_today.get("daylight_duration")
                    sunshine = daily_today.get("sunshine_duration")

                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Lever", sunset)
                    c2.metric("Coucher", sunrise)
                    c3.metric("Jour", _sec_to_hm(daylight))
                    c4.metric("Ensoleillement", _sec_to_hm(sunshine))

                    try:
                        sr_raw = (weather_data.get("daily") or [{}])[0].get("sunrise")
                        ss_raw = (weather_data.get("daily") or [{}])[0].get("sunset")
                        now = pd.Timestamp.utcnow()
                        sr = pd.to_datetime(sr_raw) if sr_raw else None
                        ss = pd.to_datetime(ss_raw) if ss_raw else None
                        if sr is not None and ss is not None and sr < ss:
                            pct = max(0.0, min(1.0, (now - sr) / (ss - sr)))
                            st.progress(float(pct), text=f"Progression du jour : {int(pct*100)}%")
                    except Exception:
                        pass

                    if weather_data and "hourly" in weather_data and weather_data["hourly"]:
                        df_u = _safe_df(weather_data["hourly"][:24]).copy()
                        if "uv_index" in df_u and "date" in df_u:
                            try:
                                df_u["Heure"] = pd.to_datetime(df_u["date"]).dt.strftime("%d-%m %Hh")
                                df_u["uv_index"] = pd.to_numeric(df_u["uv_index"], errors="coerce")
                                idx = df_u["uv_index"].idxmax()
                                if pd.notna(idx):
                                    uv_max = float(df_u.loc[idx, "uv_index"])
                                    uv_time = df_u.loc[idx, "Heure"]
                                    k1, k2 = st.columns(2)
                                    with k1:
                                        st.metric("Pic UV (24h)", f"{uv_max:.0f}", _uv_risk_label(uv_max))
                                    with k2:
                                        st.caption(f"Heure du pic : **{uv_time}**")
                                if df_u["uv_index"].notna().sum() > 1:
                                    _line_chart(df_u.rename(columns={"uv_index":"UV"}), "Heure", "UV", "Indice UV")
                            except Exception:
                                st.caption("UV non disponibles.")
                        else:
                            st.caption("UV non disponibles.")
                    else:
                        st.caption("UV non disponibles.")

            # Visibilité & Nuages
            with st.expander("🌫️ Visibilité & Nuages (24 h)", expanded=False):
                with st.container(border=True):
                    st.markdown("<div class='card-title'>🌫️ Visibilité & Nuages</div>", unsafe_allow_html=True)
                    if weather_data and "hourly" in weather_data and weather_data["hourly"]:
                        df_v = _safe_df(weather_data["hourly"][:24]).copy()
                        if "date" in df_v:
                            df_v["Heure"] = pd.to_datetime(df_v["date"]).dt.strftime("%d-%m %Hh")

                            if "visibility" in df_v:
                                vis = df_v[["Heure","visibility"]].copy()
                                try:
                                    vis["visibility"] = pd.to_numeric(vis["visibility"], errors="coerce")/1000.0
                                except Exception:
                                    pass
                                vis = vis.rename(columns={"visibility":"Visibilité (km)"})
                                _line_chart(vis, "Heure", "Visibilité (km)", "Visibilité (km)")

                            if "cloud_cover" in df_v:
                                cl = df_v[["Heure","cloud_cover"]].rename(columns={"cloud_cover":"Nébulosité (%)"})
                                _line_chart(cl, "Heure", "Nébulosité (%)", "Couverture nuageuse (%)")
                        else:
                            st.caption("Données non disponibles.")
                    else:
                        st.caption("Données non disponibles.")

            # Tableau complet en bas
            if weather_data and "hourly" in weather_data and len(weather_data["hourly"]) > 0:
                with st.expander("📋 Données horaires (tableau complet)", expanded=False):
                    with st.container(border=True):
                        hourly_full = _safe_df(weather_data["hourly"][:24]).copy()
                        if "date" in hourly_full.columns:
                            try:
                                hourly_full["dt"] = pd.to_datetime(hourly_full["date"])
                                hourly_full["Heure"] = hourly_full["dt"].dt.strftime("%d-%m %Hh")
                            except Exception:
                                hourly_full["Heure"] = hourly_full["date"].astype(str)
                        cols = ["Heure"]

                        def add_col(src, tgt, decimals=None, transform=None):
                            if src in hourly_full.columns:
                                s = pd.to_numeric(hourly_full[src], errors="coerce")
                                if transform: s = transform(s)
                                if decimals is not None: s = s.round(decimals)
                                hourly_full[tgt] = s; cols.append(tgt)

                        add_col("temperature_2m", "Température (°C)", 1)
                        add_col("apparent_temperature", "Ressenti (°C)", 1)
                        add_col("precipitation_probability", "Pluie (%)", 0)
                        add_col("wind_speed_10m", "Vent (km/h)", 1)
                        if "wind_direction_10m" in hourly_full.columns:
                            hourly_full["Vent (°)"] = pd.to_numeric(hourly_full["wind_direction_10m"], errors="coerce").round(0)
                            hourly_full["Vent (direction)"] = hourly_full["Vent (°)"].apply(_deg_to_cardinal)
                            cols += ["Vent (°)", "Vent (direction)"]
                        add_col("relative_humidity_2m", "Humidité (%)", 0)
                        add_col("cloud_cover", "Nuages (%)", 0)
                        add_col("visibility", "Visibilité (km)", None, transform=lambda s: s/1000.0)
                        add_col("uv_index", "UV", 0)

                        st.dataframe(hourly_full[cols], use_container_width=True)

        # ============ DROITE ============
        with col_right:
            # Saints
            with st.expander("📿 Saints du jour", expanded=True):
                with st.container(border=True):
                    st.markdown("<div class='card-title'>🕊️ Fête du jour</div>", unsafe_allow_html=True)
                    saints_data = st.session_state.get("saints_data")
                    if saints_data:
                        st.write(f"**Nombre de saints :** {saints_data.get('nombre_saints', 0)}")
                        saints_list = saints_data.get("saints_majeurs", []) or []
                        if saints_list:
                            for i, saint in enumerate(saints_list[:5], start=1):
                                nom = saint.get("valeur", "N/A")
                                resume = saint.get("resume")
                                st.markdown(f"**{i}. {nom}**")
                                if resume:
                                    # CORRECTION 1: Utilisation de st.markdown(..., unsafe_allow_html=True)
                                    # pour interpréter les balises comme <sup>, et style 'small' pour ressembler à une caption.
                                    trunc_resume = resume if len(resume) < 400 else resume[:400] + "…"
                                    st.markdown(f"<small style='opacity:0.75'>{trunc_resume}</small>", unsafe_allow_html=True)
                        else:
                            st.info("Aucun détail de saints majeurs trouvé.")
                    else:
                        st.caption("— En attente d'actualisation —")

            # Horoscope
            with st.expander("🔮 Horoscope du jour", expanded=True):
                with st.container(border=True):
                    st.markdown("<div class='card-title'>✨ Votre horoscope</div>", unsafe_allow_html=True)
                    st.selectbox(
                        "Choisissez votre signe",
                        options=SIGNE_KEYS,
                        format_func=lambda k: SIGNE_LABELS[k],
                        key="signe_sel",
                        on_change=_trigger_horo_refresh,
                    )
                    need_reload = (
                        st.session_state.get("refresh_horoscope", False)
                        or not st.session_state.get("horoscope_data")
                        or st.session_state.get("horoscope_sign_key") != st.session_state.signe_sel
                    )
                    if need_reload:
                        try:
                            st.session_state.horoscope_data = get_horoscope_data(st.session_state.signe_sel)
                            st.session_state.horoscope_sign_key = st.session_state.signe_sel
                            st.toast(f"Horoscope mis à jour pour {SIGNE_LABELS.get(st.session_state.signe_sel, '')}", icon="🔮")
                        finally:
                            st.session_state.refresh_horoscope = False

                    signe_label = SIGNE_LABELS.get(st.session_state.signe_sel, "—")
                    st.write(f"**Signe :** {signe_label}")

                    horoscope_data = st.session_state.get("horoscope_data")
                    if horoscope_data and horoscope_data.get("prediction_francaise"):
                        st.markdown(f"> {horoscope_data['prediction_francaise']}")
                    else:
                        st.caption("— En attente d'actualisation —")

            # Blague
            with st.expander("😄 Blague du jour", expanded=True):
                with st.container(border=True):
                    st.markdown("<div class='card-title'>🎭 Une blague pour sourire</div>", unsafe_allow_html=True)
                    blague_data = st.session_state.get("blague_data")
                    if blague_data:
                        st.write(f"**Type :** {blague_data.get('type', 'N/A')}")
                        q = blague_data.get("joke", "—")
                        a = blague_data.get("answer", "—")
                        st.markdown(f"**Question :** {q}")
                        st.markdown(f'<div class="spoiler-blur"><strong>Réponse :</strong> {a}</div>', unsafe_allow_html=True)
                    else:
                        st.caption("— En attente d'actualisation —")

    # --- ONGLET 2 ---
    with tab_prevision:
        weather_data = st.session_state.get("weather_data")
        daily_list = weather_data.get("daily") if weather_data else []
        
        if not daily_list:
            st.info("⚠️ Pas de données prévisionnelles disponibles.")
        else:
            df_daily = _safe_df(daily_list).copy()
            
            # On vérifie si on a les colonnes de base
            required_basic = ["temperature_2m_max", "temperature_2m_min", "precipitation_sum"]
            
            if "date" in df_daily.columns and all(col in df_daily.columns for col in required_basic):
                df_daily["dt"] = pd.to_datetime(df_daily["date"])
                
                # Formatage du nom du jour
                jours_fr = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
                df_daily["NomJour"] = df_daily["dt"].dt.dayofweek.map(lambda x: jours_fr[x])
                df_daily["Jour"] = df_daily["NomJour"] + " " + df_daily["dt"].dt.strftime("%d")
                
                # Renommer pour les graphs et le tableau
                rename_dict = {
                    "temperature_2m_max": "Max (°C)",
                    "temperature_2m_min": "Min (°C)",
                    "precipitation_sum": "Pluie (mm)",
                    "precipitation_probability_max": "Proba (%)",
                    # NOUVEAUX CHAMPS
                    "wind_speed_10m_max": "Vent (km/h)",
                    "uv_index_max": "UV Max",
                    "apparent_temperature_max": "Ressenti Max (°C)"
                }
                df_chart = df_daily.rename(columns=rename_dict)
                
                # --- GRAPHIQUE ---
                st.subheader("📈 Tendances de la semaine")
                st.caption("Barres bleues : Quantité de pluie (mm) • Lignes : Températures Min/Max")
                _chart_7days(df_chart)
                
                # --- TABLEAU ---
                st.subheader("📋 Détails quotidiens")
                
                # Copie pour affichage
                df_display = df_chart.copy()
                
                # AJOUT DES EMOJIS
                if "weather_code" in df_daily.columns:
                    df_display["Météo"] = df_daily["weather_code"].apply(_get_weather_emoji)

                # Formater heures lever/coucher
                for c in ["sunrise", "sunset"]:
                    if c in df_display.columns:
                        df_display[c] = pd.to_datetime(df_display[c]).dt.strftime("%H:%M")
                
                # ORDRE D'AFFICHAGE
                target_cols = [
                    "Jour", "Météo", 
                    "Min (°C)", "Max (°C)", "Ressenti Max (°C)", 
                    "Pluie (mm)", "Proba (%)",                   
                    "Vent (km/h)", "UV Max",                     
                    "sunrise", "sunset"
                ]
                final_cols = [c for c in target_cols if c in df_display.columns]
                
                # CORRECTION 2 : Configuration des colonnes pour limiter à 1 décimale
                column_config = {
                    "Max (°C)": st.column_config.NumberColumn(format="%.1f"),
                    "Min (°C)": st.column_config.NumberColumn(format="%.1f"),
                    "Ressenti Max (°C)": st.column_config.NumberColumn(format="%.1f"),
                    "Pluie (mm)": st.column_config.NumberColumn(format="%.1f"),
                    "Vent (km/h)": st.column_config.NumberColumn(format="%.1f"),
                    "UV Max": st.column_config.NumberColumn(format="%.1f"),
                    "Proba (%)": st.column_config.NumberColumn(format="%d%%"), # Pas de décimale pour la proba
                }

                st.dataframe(
                    df_display[final_cols].style.background_gradient(subset=["Max (°C)"], cmap="OrRd"),
                    use_container_width=True,
                    hide_index=True,
                    column_config=column_config # Application du formatage
                )
            else:
                st.warning("Données incomplètes. Mettez à jour 'requete_page1.py' avec les nouveaux paramètres.")
                st.dataframe(df_daily)

    # --- ONGLET 3: STATISTIQUES & TENDANCES ---
    with tab_stats:
        st.subheader("📊 Statistiques & Tendances")
        weather_data = st.session_state.get("weather_data")
        
        if not weather_data:
            st.info("Aucune donnée disponible.")
        else:
            daily_list = weather_data.get("daily", [])
            hourly_list = weather_data.get("hourly", [])
            
            if daily_list:
                df_daily = _safe_df(daily_list).copy()
                
                # Moyennes de la semaine
                st.markdown("### 📈 Moyennes de la semaine")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    if "temperature_2m_max" in df_daily and "temperature_2m_min" in df_daily:
                        avg_temp = (pd.to_numeric(df_daily["temperature_2m_max"], errors="coerce").mean() + 
                                   pd.to_numeric(df_daily["temperature_2m_min"], errors="coerce").mean()) / 2
                        st.metric("Température moyenne", f"{avg_temp:.1f} °C")
                
                with col2:
                    if "precipitation_sum" in df_daily:
                        total_precip = pd.to_numeric(df_daily["precipitation_sum"], errors="coerce").sum()
                        st.metric("Précipitations totales", f"{total_precip:.1f} mm")
                
                with col3:
                    if "wind_speed_10m_max" in df_daily:
                        avg_wind = pd.to_numeric(df_daily["wind_speed_10m_max"], errors="coerce").mean()
                        st.metric("Vent moyen (max)", f"{avg_wind:.1f} km/h")
                
                with col4:
                    if "uv_index_max" in df_daily:
                        avg_uv = pd.to_numeric(df_daily["uv_index_max"], errors="coerce").mean()
                        st.metric("UV moyen", f"{avg_uv:.1f}")
                
                # Extrêmes
                st.markdown("### 🔥 Extrêmes de la semaine")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### 🌡️ Températures")
                    if "temperature_2m_max" in df_daily and "date" in df_daily:
                        idx_max = pd.to_numeric(df_daily["temperature_2m_max"], errors="coerce").idxmax()
                        if pd.notna(idx_max):
                            day_max = pd.to_datetime(df_daily.loc[idx_max, "date"]).strftime("%A %d")
                            temp_max = df_daily.loc[idx_max, "temperature_2m_max"]
                            st.success(f"🔥 Jour le plus chaud : **{day_max}** ({temp_max:.1f}°C)")
                    
                    if "temperature_2m_min" in df_daily and "date" in df_daily:
                        idx_min = pd.to_numeric(df_daily["temperature_2m_min"], errors="coerce").idxmin()
                        if pd.notna(idx_min):
                            day_min = pd.to_datetime(df_daily.loc[idx_min, "date"]).strftime("%A %d")
                            temp_min = df_daily.loc[idx_min, "temperature_2m_min"]
                            st.info(f"❄️ Jour le plus froid : **{day_min}** ({temp_min:.1f}°C)")
                
                with col2:
                    st.markdown("#### 💨 Vent & Pluie")
                    if "wind_speed_10m_max" in df_daily and "date" in df_daily:
                        idx_wind = pd.to_numeric(df_daily["wind_speed_10m_max"], errors="coerce").idxmax()
                        if pd.notna(idx_wind):
                            day_wind = pd.to_datetime(df_daily.loc[idx_wind, "date"]).strftime("%A %d")
                            wind_max = df_daily.loc[idx_wind, "wind_speed_10m_max"]
                            st.warning(f"💨 Jour le plus venteux : **{day_wind}** ({wind_max:.1f} km/h)")
                    
                    if "precipitation_sum" in df_daily and "date" in df_daily:
                        idx_rain = pd.to_numeric(df_daily["precipitation_sum"], errors="coerce").idxmax()
                        if pd.notna(idx_rain):
                            day_rain = pd.to_datetime(df_daily.loc[idx_rain, "date"]).strftime("%A %d")
                            rain_max = df_daily.loc[idx_rain, "precipitation_sum"]
                            st.info(f"🌧️ Jour le plus pluvieux : **{day_rain}** ({rain_max:.1f} mm)")
                
                # Graphiques comparatifs
                if hourly_list and len(hourly_list) > 0:
                    st.markdown("### 📉 Évolution température & humidité (24h)")
                    df_h = _safe_df(hourly_list[:24]).copy()
                    if "date" in df_h:
                        df_h["Heure"] = pd.to_datetime(df_h["date"]).dt.strftime("%Hh")
                        
                        if "temperature_2m" in df_h and "relative_humidity_2m" in df_h:
                            fig, ax1 = plt.subplots(figsize=(10, 4))
                            
                            ax1.set_xlabel('Heure')
                            ax1.set_ylabel('Température (°C)', color='tab:red')
                            ax1.plot(df_h["Heure"], pd.to_numeric(df_h["temperature_2m"], errors="coerce"), 
                                    color='tab:red', marker='o', label='Température')
                            ax1.tick_params(axis='y', labelcolor='tab:red')
                            ax1.grid(alpha=0.3)
                            
                            ax2 = ax1.twinx()
                            ax2.set_ylabel('Humidité (%)', color='tab:blue')
                            ax2.plot(df_h["Heure"], pd.to_numeric(df_h["relative_humidity_2m"], errors="coerce"), 
                                    color='tab:blue', marker='s', label='Humidité')
                            ax2.tick_params(axis='y', labelcolor='tab:blue')
                            
                            plt.title('Corrélation Température-Humidité')
                            plt.xticks(rotation=45)
                            plt.tight_layout()
                            st.pyplot(fig)
                            plt.close()

    # --- ONGLET 4: VENT & PRESSION ---
    with tab_vent:
        st.subheader("💨 Vent & Pression")
        weather_data = st.session_state.get("weather_data")
        
        if not weather_data:
            st.info("Aucune donnée disponible.")
        else:
            hourly_list = weather_data.get("hourly", [])
            current = weather_data.get("current", {})
            
            # Données actuelles
            col1, col2, col3 = st.columns(3)
            with col1:
                ws = current.get("wind_speed_10m", 0)
                st.metric("Vent actuel", f"{ws:.1f} km/h")
            with col2:
                wg = current.get("wind_gusts_10m", 0)
                st.metric("Rafales", f"{wg:.1f} km/h")
            with col3:
                press = current.get("pressure_msl", 0)
                st.metric("Pression", f"{press:.0f} hPa")
            
            if hourly_list and len(hourly_list) > 0:
                df_h = _safe_df(hourly_list[:24]).copy()
                
                # Rose des vents (version simplifiée)
                st.markdown("### 🧭 Rose des vents (24h)")
                if "wind_direction_10m" in df_h and "wind_speed_10m" in df_h:
                    directions = pd.to_numeric(df_h["wind_direction_10m"], errors="coerce").dropna()
                    speeds = pd.to_numeric(df_h["wind_speed_10m"], errors="coerce").dropna()
                    
                    if len(directions) > 0:
                        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))
                        
                        # Convertir en radians
                        theta = np.radians(directions)
                        
                        # Tracer les vecteurs
                        colors = plt.cm.viridis(speeds / speeds.max())
                        ax.scatter(theta, speeds, c=colors, s=50, alpha=0.6)
                        
                        ax.set_theta_zero_location('N')
                        ax.set_theta_direction(-1)
                        ax.set_title('Rose des vents - Direction et vitesse', pad=20)
                        ax.set_ylabel('Vitesse (km/h)')
                        
                        st.pyplot(fig)
                        plt.close()
                
                # Graphique vitesse du vent + rafales
                st.markdown("### 💨 Vitesse du vent & rafales (24h)")
                if "date" in df_h:
                    df_h["Heure"] = pd.to_datetime(df_h["date"]).dt.strftime("%Hh")
                    
                    if "wind_speed_10m" in df_h and "wind_gusts_10m" in df_h:
                        fig, ax = plt.subplots(figsize=(10, 4))
                        
                        ax.plot(df_h["Heure"], pd.to_numeric(df_h["wind_speed_10m"], errors="coerce"), 
                               label='Vent', marker='o', color='steelblue')
                        ax.plot(df_h["Heure"], pd.to_numeric(df_h["wind_gusts_10m"], errors="coerce"), 
                               label='Rafales', marker='s', color='orange', alpha=0.7)
                        
                        ax.axhline(y=40, color='r', linestyle='--', alpha=0.5, label='Seuil vent fort (40 km/h)')
                        
                        ax.set_xlabel('Heure')
                        ax.set_ylabel('Vitesse (km/h)')
                        ax.set_title('Évolution du vent')
                        ax.legend()
                        ax.grid(alpha=0.3)
                        plt.xticks(rotation=45)
                        plt.tight_layout()
                        st.pyplot(fig)
                        plt.close()
                        
                        # Alertes vent fort
                        wind_vals = pd.to_numeric(df_h["wind_speed_10m"], errors="coerce")
                        strong_wind = wind_vals[wind_vals >= 40]
                        if len(strong_wind) > 0:
                            st.warning(f"⚠️ Vent fort détecté : {len(strong_wind)} heures avec vent ≥ 40 km/h")
                
                # Pression atmosphérique
                st.markdown("### 🌡️ Pression atmosphérique")
                current = weather_data.get("current", {})
                press_msl = current.get("pressure_msl")
                press_surf = current.get("surface_pressure")
                
                col1, col2 = st.columns(2)
                with col1:
                    if press_msl:
                        st.metric("Pression niveau mer", f"{press_msl:.1f} hPa")
                        if press_msl < 1000:
                            st.info("📉 Basse pression → Temps instable probable")
                        elif press_msl > 1020:
                            st.success("📈 Haute pression → Temps stable")
                        else:
                            st.info("➡️ Pression normale")
                
                with col2:
                    if press_surf:
                        st.metric("Pression surface", f"{press_surf:.1f} hPa")

    # --- ONGLET 5: PRÉCIPITATIONS & HUMIDITÉ ---
    with tab_precip:
        st.subheader("💧 Précipitations & Humidité")
        weather_data = st.session_state.get("weather_data")
        
        if not weather_data:
            st.info("Aucune donnée disponible.")
        else:
            daily_list = weather_data.get("daily", [])
            hourly_list = weather_data.get("hourly", [])
            
            # Accumulation de pluie
            st.markdown("### 🌧️ Accumulation de pluie")
            if daily_list:
                df_d = _safe_df(daily_list).copy()
                if "precipitation_sum" in df_d:
                    precip_vals = pd.to_numeric(df_d["precipitation_sum"], errors="coerce")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("24h", f"{precip_vals.iloc[0]:.1f} mm" if len(precip_vals) > 0 else "N/A")
                    with col2:
                        st.metric("48h", f"{precip_vals.iloc[:2].sum():.1f} mm" if len(precip_vals) >= 2 else "N/A")
                    with col3:
                        st.metric("7 jours", f"{precip_vals.sum():.1f} mm")
            
            # Timeline pluie
            if hourly_list and len(hourly_list) > 0:
                st.markdown("### ⏰ Timeline des précipitations (24h)")
                df_h = _safe_df(hourly_list[:24]).copy()
                
                if "date" in df_h and "precipitation_probability" in df_h:
                    df_h["Heure"] = pd.to_datetime(df_h["date"]).dt.strftime("%Hh")
                    df_h["Proba"] = pd.to_numeric(df_h["precipitation_probability"], errors="coerce")
                    
                    fig, ax = plt.subplots(figsize=(12, 3))
                    
                    # Barres horizontales avec gradient de couleur
                    colors = plt.cm.Blues(df_h["Proba"] / 100)
                    ax.barh(0, 1, left=range(len(df_h)), height=0.8, color=colors, edgecolor='none')
                    
                    # Seuil 50%
                    rain_hours = df_h[df_h["Proba"] >= 50]
                    if len(rain_hours) > 0:
                        for idx in rain_hours.index:
                            ax.axvline(x=idx, color='red', alpha=0.3, linestyle='--')
                    
                    ax.set_xlim(-0.5, len(df_h)-0.5)
                    ax.set_xticks(range(len(df_h)))
                    ax.set_xticklabels(df_h["Heure"], rotation=45, ha='right')
                    ax.set_yticks([])
                    ax.set_xlabel('Heure')
                    ax.set_title('Probabilité de pluie (Bleu foncé = haute probabilité)')
                    ax.grid(axis='x', alpha=0.3)
                    
                    plt.tight_layout()
                    st.pyplot(fig)
                    plt.close()
                    
                    # Identifier les périodes de pluie
                    rain_periods = df_h[df_h["Proba"] >= 50]
                    if len(rain_periods) > 0:
                        debut = rain_periods.iloc[0]["Heure"]
                        fin = rain_periods.iloc[-1]["Heure"]
                        st.warning(f"🌧️ Pluie probable de **{debut}** à **{fin}**")
                    else:
                        st.success("☀️ Pas de pluie significative prévue dans les 24h")
                
                # Humidité
                st.markdown("### 💦 Humidité relative (24h)")
                if "relative_humidity_2m" in df_h:
                    df_h["Humidité"] = pd.to_numeric(df_h["relative_humidity_2m"], errors="coerce")
                    
                    fig, ax = plt.subplots(figsize=(10, 4))
                    ax.fill_between(range(len(df_h)), df_h["Humidité"], alpha=0.3, color='cyan')
                    ax.plot(df_h["Humidité"], marker='o', color='darkblue')
                    ax.axhline(y=70, color='orange', linestyle='--', alpha=0.5, label='Seuil humide (70%)')
                    ax.set_xlabel('Heure')
                    ax.set_ylabel('Humidité (%)')
                    ax.set_title('Évolution de l\'humidité')
                    ax.set_xticks(range(len(df_h)))
                    ax.set_xticklabels(df_h["Heure"], rotation=45)
                    ax.legend()
                    ax.grid(alpha=0.3)
                    plt.tight_layout()
                    st.pyplot(fig)
                    plt.close()
                
                # Risque d'orage
                st.markdown("### ⛈️ Risque d'orage")
                if "weather_code" in df_h:
                    storm_codes = [95, 96, 99]  # Codes orage
                    df_h["code"] = pd.to_numeric(df_h["weather_code"], errors="coerce")
                    storm_hours = df_h[df_h["code"].isin(storm_codes)]
                    
                    if len(storm_hours) > 0:
                        st.error(f"⚠️ Risque d'orage détecté : {len(storm_hours)} heures concernées")
                        for _, row in storm_hours.iterrows():
                            st.write(f"- {row['Heure']}")
                    else:
                        st.success("✅ Pas de risque d'orage dans les 24h")

    # --- ONGLET 6: ENSOLEILLEMENT & UV ---
    with tab_soleil:
        st.subheader("☀️ Ensoleillement & UV")
        weather_data = st.session_state.get("weather_data")
        
        if not weather_data:
            st.info("Aucune donnée disponible.")
        else:
            daily_list = weather_data.get("daily", [])
            hourly_list = weather_data.get("hourly", [])
            
            # Calendrier solaire 7 jours
            if daily_list:
                st.markdown("### 🌅 Calendrier solaire (7 jours)")
                df_d = _safe_df(daily_list[:7]).copy()
                
                if "date" in df_d:
                    df_d["Jour"] = pd.to_datetime(df_d["date"]).dt.strftime("%a %d")
                    
                    display_cols = ["Jour"]
                    if "sunrise" in df_d:
                        df_d["Lever"] = pd.to_datetime(df_d["sunrise"]).dt.strftime("%H:%M")
                        display_cols.append("Lever")
                    if "sunset" in df_d:
                        df_d["Coucher"] = pd.to_datetime(df_d["sunset"]).dt.strftime("%H:%M")
                        display_cols.append("Coucher")
                    if "daylight_duration" in df_d:
                        df_d["Durée jour"] = df_d["daylight_duration"].apply(_sec_to_hm)
                        display_cols.append("Durée jour")
                    if "sunshine_duration" in df_d:
                        df_d["Ensoleillement"] = df_d["sunshine_duration"].apply(_sec_to_hm)
                        display_cols.append("Ensoleillement")
                    
                    st.dataframe(df_d[display_cols], use_container_width=True, hide_index=True)
                    
                    # Évolution durée du jour
                    if "daylight_duration" in df_d:
                        st.markdown("### 📈 Évolution de la durée du jour")
                        fig, ax = plt.subplots(figsize=(10, 4))
                        
                        durations_hours = pd.to_numeric(df_d["daylight_duration"], errors="coerce") / 3600
                        ax.plot(df_d["Jour"], durations_hours, marker='o', color='gold', linewidth=2)
                        ax.fill_between(range(len(df_d)), durations_hours, alpha=0.3, color='yellow')
                        ax.set_xlabel('Jour')
                        ax.set_ylabel('Durée (heures)')
                        ax.set_title('Durée d\'ensoleillement théorique')
                        ax.grid(alpha=0.3)
                        plt.xticks(rotation=45)
                        plt.tight_layout()
                        st.pyplot(fig)
                        plt.close()
            
            # Protection UV
            if hourly_list:
                st.markdown("### 🕶️ Protection UV recommandée")
                df_h = _safe_df(hourly_list[:24]).copy()
                
                if "date" in df_h and "uv_index" in df_h:
                    df_h["Heure"] = pd.to_datetime(df_h["date"]).dt.strftime("%Hh")
                    df_h["UV"] = pd.to_numeric(df_h["uv_index"], errors="coerce")
                    
                    # Graphique UV
                    fig, ax = plt.subplots(figsize=(10, 4))
                    
                    colors = []
                    for uv in df_h["UV"]:
                        if pd.isna(uv): colors.append('gray')
                        elif uv < 3: colors.append('green')
                        elif uv < 6: colors.append('yellow')
                        elif uv < 8: colors.append('orange')
                        elif uv < 11: colors.append('red')
                        else: colors.append('purple')
                    
                    ax.bar(range(len(df_h)), df_h["UV"], color=colors, alpha=0.7)
                    ax.set_xlabel('Heure')
                    ax.set_ylabel('Indice UV')
                    ax.set_title('Indice UV sur 24h (Vert=Faible, Jaune=Modéré, Orange=Élevé, Rouge=Très élevé)')
                    ax.set_xticks(range(len(df_h)))
                    ax.set_xticklabels(df_h["Heure"], rotation=45)
                    ax.grid(axis='y', alpha=0.3)
                    
                    # Légende
                    from matplotlib.patches import Patch
                    legend_elements = [
                        Patch(facecolor='green', label='Faible (0-3)'),
                        Patch(facecolor='yellow', label='Modéré (3-6)'),
                        Patch(facecolor='orange', label='Élevé (6-8)'),
                        Patch(facecolor='red', label='Très élevé (8-11)'),
                        Patch(facecolor='purple', label='Extrême (11+)')
                    ]
                    ax.legend(handles=legend_elements, loc='upper left', fontsize=8)
                    
                    plt.tight_layout()
                    st.pyplot(fig)
                    plt.close()
                    
                    # Recommandations par tranche
                    high_uv = df_h[df_h["UV"] >= 6]
                    if len(high_uv) > 0:
                        st.warning("⚠️ **Protection recommandée :**")
                        st.write("- 🕶️ Lunettes de soleil")
                        st.write("- 🧴 Crème solaire SPF 30+")
                        st.write("- 🧢 Chapeau ou casquette")
                        st.write(f"- ⏰ Heures à risque : {high_uv.iloc[0]['Heure']} - {high_uv.iloc[-1]['Heure']}")

    # --- ONGLET 7: CONFORT & RESSENTIS ---
    with tab_confort:
        st.subheader("🌡️ Confort & Ressentis")
        weather_data = st.session_state.get("weather_data")
        
        if not weather_data:
            st.info("Aucune donnée disponible.")
        else:
            current = weather_data.get("current", {})
            hourly_list = weather_data.get("hourly", [])
            
            # Indices actuels
            st.markdown("### 🎯 Indices de confort actuels")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                temp = current.get("temperature_2m", 0)
                felt = current.get("apparent_temperature", 0)
                st.metric("Température réelle", f"{temp:.1f} °C")
                st.metric("Température ressentie", f"{felt:.1f} °C", delta=f"{felt-temp:.1f}°C")
            
            with col2:
                hum = current.get("relative_humidity_2m", 0)
                st.metric("Humidité", f"{hum:.0f} %")
                
                # Point de rosée (approximation)
                if temp and hum:
                    dew_point = temp - ((100 - hum) / 5)
                    st.metric("Point de rosée", f"{dew_point:.1f} °C")
            
            with col3:
                # Indice de chaleur (Heat Index) - formule simplifiée
                if temp > 27 and hum > 40:
                    heat_index = -8.78 + 1.61*temp + 2.34*hum - 0.14*temp*hum
                    st.metric("Indice de chaleur", f"{heat_index:.1f} °C")
                    if heat_index > 40:
                        st.error("🔥 Chaleur extrême !")
                    elif heat_index > 32:
                        st.warning("⚠️ Inconfort thermique")
                else:
                    st.info("Indice de chaleur non applicable")
            
            # Zone de confort
            st.markdown("### 😊 Zone de confort thermique")
            st.info("""
            **Zone de confort optimal : 18-24°C**
            - En dessous de 18°C : Sensation de froid
            - 18-24°C : Zone de confort
            - Au dessus de 24°C : Sensation de chaleur
            """)
            
            if hourly_list:
                df_h = _safe_df(hourly_list[:24]).copy()
                
                if "date" in df_h and "temperature_2m" in df_h and "apparent_temperature" in df_h:
                    df_h["Heure"] = pd.to_datetime(df_h["date"]).dt.strftime("%Hh")
                    df_h["Temp"] = pd.to_numeric(df_h["temperature_2m"], errors="coerce")
                    df_h["Ressenti"] = pd.to_numeric(df_h["apparent_temperature"], errors="coerce")
                    
                    # Graphique température vs ressenti
                    fig, ax = plt.subplots(figsize=(10, 5))
                    
                    ax.plot(df_h["Heure"], df_h["Temp"], label='Température réelle', 
                           marker='o', color='steelblue', linewidth=2)
                    ax.plot(df_h["Heure"], df_h["Ressenti"], label='Température ressentie', 
                           marker='s', color='coral', linewidth=2, linestyle='--')
                    
                    # Zone de confort
                    ax.axhspan(18, 24, alpha=0.2, color='green', label='Zone de confort')
                    
                    ax.set_xlabel('Heure')
                    ax.set_ylabel('Température (°C)')
                    ax.set_title('Température réelle vs. ressentie avec zone de confort')
                    ax.legend(loc='best')
                    ax.grid(alpha=0.3)
                    plt.xticks(rotation=45)
                    plt.tight_layout()
                    st.pyplot(fig)
                    plt.close()
                    
                    # Recommandations vestimentaires
                    st.markdown("### 👕 Recommandations vestimentaires")
                    avg_temp = df_h["Temp"].mean()
                    
                    if avg_temp < 5:
                        st.info("🧥 **Vêtements chauds recommandés :** Manteau épais, écharpe, gants, bonnet")
                    elif avg_temp < 15:
                        st.info("🧥 **Vêtements mi-saison :** Veste, pull léger")
                    elif avg_temp < 25:
                        st.success("👕 **Vêtements légers :** T-shirt, pantalon léger")
                    else:
                        st.warning("🩳 **Vêtements très légers :** Short, débardeur, pensez à l'hydratation")

    # --- ONGLET 8: JOUR VS NUIT ---
    with tab_jour_nuit:
        st.subheader("🌙 Jour vs Nuit")
        weather_data = st.session_state.get("weather_data")
        
        if not weather_data:
            st.info("Aucune donnée disponible.")
        else:
            hourly_list = weather_data.get("hourly", [])
            daily_list = weather_data.get("daily", [])
            
            if hourly_list and daily_list:
                df_h = _safe_df(hourly_list[:24]).copy()
                
                if "date" in df_h and "temperature_2m" in df_h:
                    df_h["datetime"] = pd.to_datetime(df_h["date"])
                    df_h["Temp"] = pd.to_numeric(df_h["temperature_2m"], errors="coerce")
                    
                    # Identifier jour/nuit
                    if "is_day" in df_h:
                        df_h["is_day"] = pd.to_numeric(df_h["is_day"], errors="coerce")
                        day_data = df_h[df_h["is_day"] == 1]
                        night_data = df_h[df_h["is_day"] == 0]
                    else:
                        # Approximation si pas de is_day
                        df_h["hour"] = df_h["datetime"].dt.hour
                        day_data = df_h[(df_h["hour"] >= 6) & (df_h["hour"] < 20)]
                        night_data = df_h[(df_h["hour"] < 6) | (df_h["hour"] >= 20)]
                    
                    # Comparaison
                    st.markdown("### ☀️🌙 Comparaison Jour vs Nuit")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("#### ☀️ Jour")
                        if len(day_data) > 0:
                            st.metric("Température moyenne", f"{day_data['Temp'].mean():.1f} °C")
                            st.metric("Température max", f"{day_data['Temp'].max():.1f} °C")
                            st.metric("Température min", f"{day_data['Temp'].min():.1f} °C")
                    
                    with col2:
                        st.markdown("#### 🌙 Nuit")
                        if len(night_data) > 0:
                            st.metric("Température moyenne", f"{night_data['Temp'].mean():.1f} °C")
                            st.metric("Température max", f"{night_data['Temp'].max():.1f} °C")
                            st.metric("Température min", f"{night_data['Temp'].min():.1f} °C")
                    
                    # Amplitude thermique
                    if len(day_data) > 0 and len(night_data) > 0:
                        amplitude = day_data['Temp'].mean() - night_data['Temp'].mean()
                        st.info(f"📊 **Amplitude thermique jour/nuit :** {amplitude:.1f} °C")
                    
                    # Heatmap 7 jours
                    st.markdown("### 🔥 Heatmap température (7 jours x 24h)")
                    df_week = _safe_df(hourly_list[:168]).copy()  # 7 jours * 24h
                    
                    if "date" in df_week and "temperature_2m" in df_week:
                        df_week["datetime"] = pd.to_datetime(df_week["date"])
                        df_week["Jour"] = df_week["datetime"].dt.strftime("%a %d")
                        df_week["Heure"] = df_week["datetime"].dt.hour
                        df_week["Temp"] = pd.to_numeric(df_week["temperature_2m"], errors="coerce")
                        
                        # Pivot pour heatmap
                        pivot = df_week.pivot_table(values="Temp", index="Jour", columns="Heure", aggfunc='mean')
                        
                        fig, ax = plt.subplots(figsize=(12, 6))
                        im = ax.imshow(pivot, cmap='RdYlBu_r', aspect='auto')
                        
                        ax.set_xticks(range(24))
                        ax.set_xticklabels([f"{h}h" for h in range(24)])
                        ax.set_yticks(range(len(pivot.index)))
                        ax.set_yticklabels(pivot.index)
                        ax.set_xlabel('Heure')
                        ax.set_ylabel('Jour')
                        ax.set_title('Heatmap des températures (Rouge=Chaud, Bleu=Froid)')
                        
                        cbar = plt.colorbar(im, ax=ax)
                        cbar.set_label('Température (°C)', rotation=270, labelpad=20)
                        
                        plt.tight_layout()
                        st.pyplot(fig)
                        plt.close()
                    
                    # Qualité du sommeil
                    st.markdown("### 😴 Température et qualité du sommeil")
                    st.info("""
                    **Température idéale pour dormir : 16-19°C**
                    
                    Une chambre trop chaude ou trop froide perturbe le sommeil.
                    """)
                    
                    if len(night_data) > 0:
                        night_avg = night_data['Temp'].mean()
                        if 16 <= night_avg <= 19:
                            st.success(f"✅ Température nocturne optimale : {night_avg:.1f}°C")
                        elif night_avg < 16:
                            st.warning(f"❄️ Température nocturne basse : {night_avg:.1f}°C - Pensez à une couverture supplémentaire")
                        else:
                            st.warning(f"🔥 Température nocturne élevée : {night_avg:.1f}°C - Aérez ou utilisez la climatisation")

    # --- ONGLET 9: RECOMMANDATIONS ---
    with tab_reco:
        st.subheader("🎯 Recommandations & Activités")
        weather_data = st.session_state.get("weather_data")
        ville = st.session_state.get("ville_selectionnee", "Ville")
        
        if not weather_data:
            st.info("Aucune donnée disponible.")
        else:
            # Génération automatique des recommandations IA
            st.markdown('<div class="weather-card">', unsafe_allow_html=True)
            st.markdown("### 🤖 Recommandations générées par Intelligence Artificielle")
            st.markdown("""
            <p style="opacity: 0.8; margin-bottom: 1rem;">
            Recommandations personnalisées basées sur la météo actuelle et les spécificités de votre ville.
            </p>
            """, unsafe_allow_html=True)
            
            # Bouton de rafraîchissement uniquement
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                if st.button("🔄 Régénérer", use_container_width=True, key="refresh_reco"):
                    if "ai_recommendations" in st.session_state:
                        del st.session_state.ai_recommendations
                    st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Génération automatique si pas encore en cache
            if "ai_recommendations" not in st.session_state:
                with st.spinner("🤖 Génération de recommandations personnalisées en cours..."):
                    reco_data = generate_recommendations(weather_data, ville)
                    st.session_state.ai_recommendations = reco_data
            
            reco_data = st.session_state.ai_recommendations
            
            if reco_data.get("success"):
                # Afficher les recommandations générées
                st.markdown("---")
                formatted_content = format_recommendations_for_display(reco_data)
                st.markdown(formatted_content, unsafe_allow_html=True)
                
                # Afficher les données météo utilisées
                with st.expander("📊 Données météo utilisées pour la génération"):
                    st.markdown("#### 🌡️ Températures")
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Actuelle", f"{reco_data.get('temp', 0):.1f}°C")
                    col2.metric("Ressentie", f"{reco_data.get('apparent_temp', 0):.1f}°C")
                    col3.metric("Min", f"{reco_data.get('temp_min', 0):.1f}°C")
                    col4.metric("Max", f"{reco_data.get('temp_max', 0):.1f}°C")
                    
                    st.markdown("#### 💧 Humidité & Précipitations")
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Humidité", f"{reco_data.get('humidity', 0):.0f}%")
                    col2.metric("Pluie (max)", f"{reco_data.get('rain_prob', 0):.0f}%")
                    col3.metric("Pluie (moy)", f"{reco_data.get('rain_prob_avg', 0):.0f}%")
                    col4.metric("Précip. totales", f"{reco_data.get('precip_sum', 0):.1f} mm")
                    
                    st.markdown("#### 💨 Vent & Ciel")
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Vent", f"{reco_data.get('wind', 0):.1f} km/h")
                    col2.metric("Rafales", f"{reco_data.get('wind_gusts', 0):.1f} km/h")
                    col3.metric("Nuages", f"{reco_data.get('cloud_cover', 0):.0f}%")
                    col4.metric("Pression", f"{reco_data.get('pressure', 0):.0f} hPa")
                    
                    st.markdown("#### ☀️ Soleil & UV")
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("UV max", f"{reco_data.get('uv', 0):.1f}")
                    sunshine = reco_data.get('sunshine_duration', 0)
                    daylight = reco_data.get('daylight_duration', 0)
                    col2.metric("Ensoleillement", f"{sunshine:.1f}h")
                    col3.metric("Durée du jour", f"{daylight:.1f}h")
                    visibility = reco_data.get('visibility')
                    col4.metric("Visibilité", f"{visibility:.1f} km" if visibility else "N/A")
                    
                    if reco_data.get('temps_next_days'):
                        st.markdown("#### 📈 Tendances (3 prochains jours)")
                        temps_next = reco_data.get('temps_next_days', [])
                        rain_next = reco_data.get('rain_next_days', [])
                        temp_trend = reco_data.get('temp_trend', 'stable')
                        
                        col1, col2, col3 = st.columns(3)
                        if len(temps_next) >= 2:
                            col1.metric("Températures", f"{temps_next[0]:.1f}°C → {temps_next[-1]:.1f}°C", 
                                       delta=f"{temp_trend}")
                        if rain_next:
                            col2.metric("Pluie moyenne", f"{sum(rain_next)/len(rain_next):.0f}%")
                        
                        sunrise = reco_data.get('sunrise', '')
                        sunset = reco_data.get('sunset', '')
                        if sunrise and sunset:
                            col3.metric("Lever/Coucher", f"{sunrise.split()[1][:5]} / {sunset.split()[1][:5]}")
            else:
                st.error(f"❌ Erreur lors de la génération : {reco_data.get('error', 'Inconnue')}")
                st.info("💡 Vérifiez que votre clé API GROQ est correctement configurée dans le fichier .env")
                
                # Affichage de secours avec recommandations basiques
                st.markdown("---")
                st.markdown("### 📝 Recommandations basiques (mode dégradé)")
                
                current = weather_data.get("current", {})
                hourly_list = weather_data.get("hourly", [])
                
                temp = current.get("temperature_2m", 20)
                wind = current.get("wind_speed_10m", 0)
                
                rain_prob = 0
                if hourly_list:
                    df_h = _safe_df(hourly_list[:24])
                    if "precipitation_probability" in df_h:
                        rain_prob = pd.to_numeric(df_h["precipitation_probability"], errors="coerce").max()
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### ☀️ Conditions actuelles")
                    if rain_prob < 30:
                        st.success("✅ Peu de pluie prévue - Activités extérieures possibles")
                    else:
                        st.warning("☔ Risque de pluie - Privilégiez les activités en intérieur")
                    
                    if 15 < temp < 28:
                        st.success("✅ Température agréable pour les activités")
                    elif temp < 15:
                        st.info("🧥 Pensez à vous couvrir")
                    else:
                        st.warning("🔥 Chaleur - Hydratez-vous bien")
                
                with col2:
                    st.markdown("#### 💡 Suggestions rapides")
                    if temp > 15 and rain_prob < 30:
                        st.write("🚴 Sports en extérieur")
                        st.write("🏞️ Randonnée, pique-nique")
                    if rain_prob > 50:
                        st.write("🏛️ Musées, cinéma")
                        st.write("☕ Cafés, restaurants")
                    if wind > 30:
                        st.write("🪁 Cerf-volant")
                        st.write("⛵ Activités nautiques")

    # Footer
    st.markdown("---")
    st.subheader("ℹ️ Informations détaillées")
    with st.expander("🛠️ Données techniques"):
        st.write(f"**Ville :** {st.session_state.ville_selectionnee}")
        st.write(f"**Latitude :** {st.session_state.latitude}")
        st.write(f"**Longitude :** {st.session_state.longitude}")
        st.write(f"**Timestamp :** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    with st.expander("📋 Instructions"):
        st.markdown(
            """
            - Données chargées automatiquement au premier affichage **et** à chaque changement de ville/coordonnées.
            - Bouton **🔄 Actualiser maintenant** pour relancer une récupération manuelle.
            - Graphique **Température** = Température (orange) + Ressenti (bleu).
            - Tableau horaire : replié par défaut.
            - Dans “Météo actuelle” : indicateurs uniformes et **flèche de vent à droite** de la vitesse.
            - Lever/Coucher du soleil en **hh:mm**.
            """
        )
show_data_page()