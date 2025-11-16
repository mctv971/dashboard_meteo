import streamlit as st
import sys
import os
from datetime import datetime
import pandas as pd
import altair as alt

# Ajouter le répertoire courant au chemin Python pour importer requete_page1
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from requete_page1 import get_weather_data, get_saints_data, get_horoscope_data, get_blague_data
except ImportError as e:
    st.error(f"Erreur d'importation : {e}")
    st.stop()

# ---------- Styles ----------
st.markdown("""
<style>
/* Indicateurs uniformes (appliqués sur des <p>) */
.metric-label{font-size:.9rem;opacity:.8;margin:0 0 4px 0}
.metric-value{font-size:2rem;font-weight:700;line-height:1.1;margin:0}
.metric-unit{font-size:1rem;opacity:.85;margin-left:.2rem}
.metric-sub{font-size:.95rem;opacity:.8;margin:.15rem 0 0 0}

/* Titres dans les containers */
.card-title{font-weight:700;font-size:1.05rem;margin-bottom:8px}
</style>
""", unsafe_allow_html=True)

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
        st.error("❌ Aucune ville sélectionnée. Retournez à la page d'accueil.")
        if st.button("🏠 Retour à l'accueil"):
            st.session_state.page = "accueil"
            st.rerun()
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
                c1.metric("Lever", sunrise)
                c2.metric("Coucher", sunset)
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

        # Tableau complet en bas (expander replié par défaut)
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
                                st.caption(resume if len(resume) < 400 else resume[:400] + "…")
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
                    with st.popover("Voir la réponse"):
                        st.markdown(f"**Réponse :** {a}")
                else:
                    st.caption("— En attente d'actualisation —")

    # Infos
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

if __name__ == "__main__":
    show_data_page()
