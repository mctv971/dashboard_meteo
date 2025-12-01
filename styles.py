"""
Style CSS global pour le dashboard météo
Design moderne, élégant et professionnel
"""

GLOBAL_STYLE = """
<style>
/* ============================================
   VARIABLES CSS PERSONNALISÉES
   ============================================ */
:root {
    --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    --secondary-gradient: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    --success-gradient: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    --warning-gradient: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
    --card-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
    --hover-shadow: 0 15px 40px rgba(0, 0, 0, 0.4);
    --transition-smooth: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    --border-radius: 16px;
}

/* ============================================
   FOND ET CONTENEUR PRINCIPAL
   ============================================ */
.stApp {
    background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%) !important;
    background-attachment: fixed !important;
}

/* Conteneur principal */
.main {
    background: transparent !important;
}

.block-container {
    background: transparent !important;
    padding-top: 3rem !important;
}

/* Animation de fond subtile */
@keyframes gradientShift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

.stApp::before {
    content: '';
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(45deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
    background-size: 400% 400%;
    animation: gradientShift 15s ease infinite;
    pointer-events: none;
    z-index: 0;
}

/* ============================================
   SIDEBAR MODERNE
   ============================================ */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1a1625 0%, #0f0c29 100%) !important;
    border-right: 2px solid rgba(102, 126, 234, 0.3) !important;
    box-shadow: 5px 0 30px rgba(102, 126, 234, 0.2) !important;
}

section[data-testid="stSidebar"] > div {
    background: transparent !important;
    padding-top: 2rem;
}

/* Header du sidebar */
section[data-testid="stSidebar"] .css-1d391kg, 
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] {
    background: transparent !important;
}

/* Navigation links dans la sidebar */
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] li {
    margin: 0.5rem 0;
}

section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a {
    background: rgba(30, 33, 48, 0.6) !important;
    border-radius: 12px !important;
    padding: 0.75rem 1rem !important;
    border: 2px solid transparent !important;
    transition: var(--transition-smooth) !important;
    backdrop-filter: blur(10px) !important;
}

section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover {
    background: linear-gradient(135deg, rgba(102, 126, 234, 0.3) 0%, rgba(118, 75, 162, 0.3) 100%) !important;
    border-color: rgba(102, 126, 234, 0.6) !important;
    transform: translateX(5px) !important;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3) !important;
}

section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"] {
    background: var(--primary-gradient) !important;
    border-color: rgba(255, 255, 255, 0.2) !important;
    box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4) !important;
    font-weight: 700 !important;
}

/* Logo sidebar */
section[data-testid="stSidebar"] h1 {
    background: var(--primary-gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-weight: 800;
    font-size: 2rem;
    text-align: center;
    margin-bottom: 2rem;
    text-shadow: 0 0 30px rgba(102, 126, 234, 0.5);
}

/* Bouton de fermeture sidebar */
section[data-testid="stSidebar"] button[kind="header"] {
    color: rgba(250, 250, 250, 0.8) !important;
}

section[data-testid="stSidebar"] button[kind="header"]:hover {
    background: rgba(102, 126, 234, 0.2) !important;
    color: white !important;
}

/* ============================================
   TITRES AVEC DÉGRADÉS
   ============================================ */
h1, h2, h3 {
    background: linear-gradient(135deg, #667eea 0%, #f093fb 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-weight: 700;
    letter-spacing: -0.5px;
    margin-bottom: 1.5rem;
}

h1 {
    font-size: 3rem !important;
    text-shadow: 0 0 40px rgba(102, 126, 234, 0.3);
}

h2 {
    font-size: 2rem !important;
}

h3 {
    font-size: 1.5rem !important;
}

/* ============================================
   CARTES ET CONTENEURS STYLISÉS
   ============================================ */
div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] {
    background: rgba(30, 33, 48, 0.6);
    backdrop-filter: blur(10px);
    border-radius: var(--border-radius);
    padding: 1.5rem;
    border: 1px solid rgba(255, 255, 255, 0.1);
    box-shadow: var(--card-shadow);
    transition: var(--transition-smooth);
}

div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"]:hover {
    transform: translateY(-5px);
    box-shadow: var(--hover-shadow);
    border-color: rgba(102, 126, 234, 0.5);
}

/* Conteneurs avec bordures */
div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"][style*="border"] {
    background: linear-gradient(135deg, rgba(30, 33, 48, 0.8) 0%, rgba(30, 33, 48, 0.4) 100%);
    border: 2px solid transparent;
    border-radius: var(--border-radius);
    background-clip: padding-box;
    position: relative;
    overflow: hidden;
}

div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"][style*="border"]::before {
    content: '';
    position: absolute;
    inset: 0;
    border-radius: var(--border-radius);
    padding: 2px;
    background: var(--primary-gradient);
    -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
    -webkit-mask-composite: xor;
    mask-composite: exclude;
    opacity: 0.5;
}

/* ============================================
   MÉTRIQUES ÉLÉGANTES
   ============================================ */
div[data-testid="stMetricValue"] {
    font-size: 2.5rem !important;
    font-weight: 800 !important;
    background: var(--success-gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    text-shadow: 0 0 30px rgba(79, 172, 254, 0.5);
}

div[data-testid="stMetricDelta"] {
    font-weight: 600;
}

div[data-testid="stMetricDelta"] svg {
    filter: drop-shadow(0 0 5px currentColor);
}

.metric-label {
    font-size: 0.9rem;
    opacity: 0.8;
    margin: 0 0 8px 0;
    text-transform: uppercase;
    letter-spacing: 1px;
    font-weight: 600;
}

.metric-value {
    font-size: 2.5rem;
    font-weight: 800;
    line-height: 1.1;
    margin: 0;
    background: var(--success-gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.metric-unit {
    font-size: 1.2rem;
    opacity: 0.85;
    margin-left: 0.3rem;
}

.metric-sub {
    font-size: 0.95rem;
    opacity: 0.8;
    margin: 0.3rem 0 0 0;
}

/* ============================================
   BOUTONS MODERNES
   ============================================ */
.stButton > button {
    background: var(--primary-gradient) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.75rem 2rem !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    transition: var(--transition-smooth) !important;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4) !important;
    position: relative;
    overflow: hidden;
}

.stButton > button::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
    transition: left 0.5s;
}

.stButton > button:hover::before {
    left: 100%;
}

.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 25px rgba(102, 126, 234, 0.6) !important;
}

.stButton > button:active {
    transform: translateY(0) !important;
}

/* Bouton primary (rouge-orange) */
.stButton > button[kind="primary"] {
    background: var(--secondary-gradient) !important;
    box-shadow: 0 4px 15px rgba(245, 87, 108, 0.4) !important;
}

.stButton > button[kind="primary"]:hover {
    box-shadow: 0 6px 25px rgba(245, 87, 108, 0.6) !important;
}

/* ============================================
   INPUTS ET SELECTBOX
   ============================================ */
.stTextInput > div > div > input,
.stSelectbox > div > div > div {
    background-color: rgba(30, 33, 48, 0.8) !important;
    border: 2px solid rgba(102, 126, 234, 0.3) !important;
    border-radius: 12px !important;
    color: #fafafa !important;
    font-size: 1rem !important;
    padding: 0.75rem 1rem !important;
    transition: var(--transition-smooth) !important;
}

.stTextInput > div > div > input:focus,
.stSelectbox > div > div > div:focus {
    border-color: rgba(102, 126, 234, 0.8) !important;
    box-shadow: 0 0 20px rgba(102, 126, 234, 0.3) !important;
}

/* ============================================
   TABS ULTRA MODERNES
   ============================================ */
.stTabs [data-baseweb="tab-list"] {
    gap: 12px;
    background: rgba(30, 33, 48, 0.6);
    padding: 8px;
    border-radius: 16px;
    backdrop-filter: blur(10px);
}

.stTabs [data-baseweb="tab"] {
    height: auto;
    min-height: 45px;
    white-space: normal;
    word-wrap: break-word;
    border-radius: 12px;
    padding: 8px 12px;
    font-weight: 600;
    font-size: 0.8rem;
    line-height: 1.2;
    background: rgba(30, 33, 48, 0.8);
    color: rgba(250, 250, 250, 0.7);
    border: 2px solid transparent;
    transition: var(--transition-smooth);
    position: relative;
    overflow: hidden;
    text-align: center;
    display: flex;
    align-items: center;
    justify-content: center;
}

.stTabs [data-baseweb="tab"]::before {
    content: '';
    position: absolute;
    inset: 0;
    background: var(--primary-gradient);
    opacity: 0;
    transition: var(--transition-smooth);
}

.stTabs [data-baseweb="tab"]:hover {
    background: rgba(102, 126, 234, 0.2);
    transform: translateY(-2px);
}

.stTabs [aria-selected="true"] {
    background: var(--primary-gradient) !important;
    color: white !important;
    font-weight: 700;
    box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
    border-color: rgba(255, 255, 255, 0.2);
}

/* ============================================
   EXPANDERS STYLISÉS
   ============================================ */
.streamlit-expanderHeader {
    background: linear-gradient(135deg, rgba(30, 33, 48, 0.8) 0%, rgba(30, 33, 48, 0.4) 100%) !important;
    border-radius: 12px !important;
    border: 2px solid rgba(102, 126, 234, 0.3) !important;
    padding: 1rem 1.5rem !important;
    font-weight: 600 !important;
    font-size: 1.1rem !important;
    transition: var(--transition-smooth) !important;
}

.streamlit-expanderHeader:hover {
    border-color: rgba(102, 126, 234, 0.6) !important;
    background: rgba(102, 126, 234, 0.2) !important;
    transform: translateX(5px);
}

/* ============================================
   DATAFRAMES ET TABLEAUX
   ============================================ */
div[data-testid="stDataFrame"] {
    border-radius: var(--border-radius);
    overflow: hidden;
    box-shadow: var(--card-shadow);
}

div[data-testid="stDataFrame"] table {
    border-collapse: separate;
    border-spacing: 0;
}

div[data-testid="stDataFrame"] thead tr th {
    background: var(--primary-gradient) !important;
    color: white !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    padding: 1rem !important;
}

div[data-testid="stDataFrame"] tbody tr {
    transition: var(--transition-smooth);
}

div[data-testid="stDataFrame"] tbody tr:hover {
    background: rgba(102, 126, 234, 0.1) !important;
    transform: scale(1.01);
}

/* ============================================
   ALERTES ET MESSAGES
   ============================================ */
.stAlert {
    border-radius: 12px !important;
    border-left: 4px solid !important;
    backdrop-filter: blur(10px) !important;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2) !important;
}

div[data-testid="stAlert"][data-baseweb="notification"] {
    animation: slideIn 0.5s ease-out;
}

@keyframes slideIn {
    from {
        opacity: 0;
        transform: translateX(-20px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

/* ============================================
   PROGRESS BAR
   ============================================ */
.stProgress > div > div > div {
    background: var(--primary-gradient) !important;
    border-radius: 10px !important;
    box-shadow: 0 0 20px rgba(102, 126, 234, 0.5) !important;
}

/* ============================================
   TOOLTIPS
   ============================================ */
[data-testid="stTooltipHoverTarget"] {
    transition: var(--transition-smooth);
}

[data-testid="stTooltipHoverTarget"]:hover {
    transform: scale(1.1);
    filter: brightness(1.2);
}

/* ============================================
   SPOILER AMÉLIORÉ
   ============================================ */
.spoiler-blur {
    background: linear-gradient(135deg, rgba(30, 33, 48, 0.9) 0%, rgba(30, 33, 48, 0.7) 100%);
    color: transparent;
    text-shadow: 0 0 15px rgba(102, 126, 234, 0.5);
    border-radius: 12px;
    padding: 1rem;
    cursor: pointer;
    transition: var(--transition-smooth);
    user-select: none;
    border: 2px solid rgba(102, 126, 234, 0.3);
    position: relative;
    overflow: hidden;
}

.spoiler-blur::before {
    content: '👆 Cliquez pour révéler';
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    color: rgba(250, 250, 250, 0.6);
    font-weight: 600;
    font-size: 0.9rem;
    text-shadow: none;
}

.spoiler-blur:hover, .spoiler-blur:active {
    color: var(--text-color);
    text-shadow: none;
    background: linear-gradient(135deg, rgba(102, 126, 234, 0.2) 0%, rgba(118, 75, 162, 0.2) 100%);
    border-color: rgba(102, 126, 234, 0.8);
}

.spoiler-blur:hover::before {
    opacity: 0;
}

/* ============================================
   TITRE DE CARTE
   ============================================ */
.card-title {
    font-weight: 700;
    font-size: 1.2rem;
    margin-bottom: 1rem;
    background: var(--primary-gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

/* ============================================
   SCROLLBAR PERSONNALISÉE
   ============================================ */
::-webkit-scrollbar {
    width: 10px;
    height: 10px;
}

::-webkit-scrollbar-track {
    background: rgba(30, 33, 48, 0.5);
    border-radius: 10px;
}

::-webkit-scrollbar-thumb {
    background: var(--primary-gradient);
    border-radius: 10px;
    border: 2px solid rgba(30, 33, 48, 0.5);
}

::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
}

/* ============================================
   ANIMATIONS GÉNÉRALES
   ============================================ */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes pulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.05); }
}

@keyframes shimmer {
    0% { background-position: -1000px 0; }
    100% { background-position: 1000px 0; }
}

.animate-fade-in {
    animation: fadeIn 0.6s ease-out;
}

.animate-pulse {
    animation: pulse 2s ease-in-out infinite;
}

/* ============================================
   EMOJIS ET ICÔNES ANIMÉS
   ============================================ */
.weather-emoji {
    font-size: 3rem;
    display: inline-block;
    transition: var(--transition-smooth);
}

.weather-emoji:hover {
    transform: scale(1.2) rotate(10deg);
    filter: drop-shadow(0 0 10px rgba(102, 126, 234, 0.6));
}

/* ============================================
   RESPONSIVE
   ============================================ */
@media (max-width: 768px) {
    h1 { font-size: 2rem !important; }
    h2 { font-size: 1.5rem !important; }
    h3 { font-size: 1.2rem !important; }
    
    .metric-value { font-size: 2rem; }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding: 0 16px;
        font-size: 0.9rem;
    }
}

/* ============================================
   FOOTER STYLISÉ
   ============================================ */
footer {
    background: linear-gradient(180deg, transparent 0%, rgba(14, 17, 23, 0.8) 100%);
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    padding: 2rem 0;
    margin-top: 4rem;
}

/* ============================================
   CLASSE UTILITAIRES
   ============================================ */
.glass-effect {
    background: rgba(30, 33, 48, 0.6) !important;
    backdrop-filter: blur(10px) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
}

.gradient-text {
    background: var(--primary-gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.glow-effect {
    box-shadow: 0 0 30px rgba(102, 126, 234, 0.5);
}

/* ============================================
   CARTE MÉTÉO SPÉCIALE
   ============================================ */
.weather-card {
    background: linear-gradient(135deg, rgba(102, 126, 234, 0.2) 0%, rgba(118, 75, 162, 0.2) 100%);
    border-radius: var(--border-radius);
    padding: 2rem;
    border: 2px solid rgba(102, 126, 234, 0.3);
    box-shadow: var(--card-shadow);
    transition: var(--transition-smooth);
    position: relative;
    overflow: hidden;
}

.weather-card::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(255, 255, 255, 0.1) 0%, transparent 70%);
    animation: rotate 10s linear infinite;
}

@keyframes rotate {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

.weather-card:hover {
    transform: translateY(-5px);
    box-shadow: var(--hover-shadow);
    border-color: rgba(102, 126, 234, 0.6);
}
</style>
"""
