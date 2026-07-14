import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# ==========================================
# 1. APP INITIALIZATION & THEME INJECTION
# ==========================================
st.set_page_config(
    page_title="RSG Dynasty Hub",
    page_icon="🏈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
        .stApp {
            background-color: #0b0f14;
            color: #f1f3f5;
            font-family: 'Helvetica Neue', Arial, sans-serif;
        }
        .sports-card {
            background-color: #141a22;
            border-left: 4px solid #991b1b;
            padding: 16px;
            border-radius: 6px;
            margin-bottom: 12px;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.4);
        }
        .stat-box {
            background-color: #1c2430;
            padding: 12px;
            border-radius: 4px;
            text-align: center;
            border: 1px solid #2d3748;
        }
        .stat-val {
            font-size: 22px;
            font-weight: 800;
            color: #f3f4f6;
            margin: 0;
        }
        .stat-lbl {
            font-size: 11px;
            color: #9ca3af;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin: 4px 0 0 0;
        }
        .bracket-card {
            background-color: #141a22;
            border-top: 3px solid #374151;
            padding: 12px;
            border-radius: 6px;
            margin-bottom: 16px;
        }
        .winner-text { color: #34d399 !important; font-weight: bold; }
        .ranking-badge { font-size: 22px; font-weight: 800; color: #ef4444; text-align: center; }
         
        .clean-table {
            width: 100%;
            border-collapse: collapse;
            background-color: #141a22;
            border-radius: 8px;
            overflow: hidden;
            margin-bottom: 20px;
        }
        .clean-table th {
            background-color: #991b1b;
            color: white;
            padding: 12px;
            font-weight: bold;
            text-align: left;
            text-transform: uppercase;
            font-size: 12px;
        }
        .clean-table td {
            padding: 12px;
            border-bottom: 1px solid #242f3d;
            font-size: 14px;
        }
         
        .stTabs [data-baseweb="tab-list"] { gap: 8px; background-color: #141a22; padding: 8px; border-radius: 6px; flex-wrap: wrap;}
        .stTabs [data-baseweb="tab"] { height: 38px; background-color: #0b0f14; border-radius: 4px; color: #9ca3af; padding: 0px 18px; }
        .stTabs [aria-selected="true"] { background-color: #991b1b !important; color: white !important; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. FLEXIBLE DATA IMPORT ENGINE
# ==========================================
SPREADSHEET_ID = "1d__Qek_UlinsGoGlv3Wvpe9iviidOWCnlxH0syi4HzY" 

@st.cache_data(ttl=10)
def load_sheet_tab(sheet_name):
    """Bridges directly to your sheets and scrubs out Google Sheet export bugs"""
    formatted_name = sheet_name.replace(" ", "%20")
    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={formatted_name}"
    try:
        df = pd.read_csv(url)
         
        if 'html' in str(df.columns).lower() or df.empty:
            return pd.DataFrame()

        df = df.dropna(how='all')
         
        # Instantly remove all empty stray columns Google Sheets sometimes exports
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        df.columns = df.columns.str.strip()
         
        # Normalize year and index criteria columns to matching integers
        for col in df.columns:
            if col.lower().strip() in ['year', 'current year', 'seasonindex', 'season_index']:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
        return df
    except Exception as e:
        return pd.DataFrame()

# Helper function to find column names regardless of spaces/underscores
def find_col(df, target_name):
    if df.empty: return None
    normalized_target = target_name.lower().replace("_", "").replace(" ", "")
    for col in df.columns:
        if col.lower().replace("_", "").replace(" ", "") == normalized_target:
            return col
    return None

def get_val(row, target_name, default=""):
    col = find_col(pd.DataFrame([row]), target_name)
    if col and col in row:
        val = row[col]
        if pd.isna(val): return default
        if isinstance(val, (float, np.float64)) and val.is_integer(): return int(val)
        return val
    return default

def fix_sheet_format(val, is_scheme=False):
    """Catches instances where Google Sheets accidentally turns 4-2-5 or W-L records into dates"""
    if pd.isna(val): return ""
    val_str = str(val).strip()
    if val_str in ['nan', 'None', '']: return ""
     
    # Correct date-parsed 4-2-5 schemes
    if is_scheme and "2005-" in val_str:
        parts = val_str.split(" ")[0].split("-")
        if len(parts) == 3: return f"{int(parts[1])}-{int(parts[2])}-5"
         
    # Correct date-parsed records like 10-3
    if not is_scheme and "00:00:00" in val_str:
        parts = val_str.split(" ")[0].split("-")
        if len(parts) == 3: return f"{int(parts[1])}-{int(parts[2])}"
         
    return val_str

# Load core tables
df_current_season = load_sheet_tab("Current Season")
df_coaches    = load_sheet_tab("Coach_Directory")
df_top25      = load_sheet_tab("Top_25")
df_heisman    = load_sheet_tab("Heisman_History")
df_standings  = load_sheet_tab("Conference_Standings")
df_dynasty    = load_sheet_tab("Dynasty Score")
df_nil        = load_sheet_tab("NIL_Payroll")
df_roster     = load_sheet_tab("Roster_Ledger")
df_schedule   = load_sheet_tab("Team_Schedule")
df_team_stats = load_sheet_tab("Team_Stats")
df_game_logs  = load_sheet_tab("Raw_Game_Logs")

# Load stat tables
df_pass       = load_sheet_tab("Passing_Stats")
df_rush       = load_sheet_tab("Rushing_Stats")
df_rec        = load_sheet_tab("Receiving_Stats")
df_def        = load_sheet_tab("Defense_Stats")

# Bracket fallback
df_bracket    = load_sheet_tab("CFB_Playoff_Bracket")
if df_bracket.empty:
    df_bracket = load_sheet_tab("CFB Playoff Bracket")

# ==========================================
# 3. COMPLETE NCAA LOGO ATLAS LOOKUP SERVICE
# ==========================================
def get_team_logo(team_name):
    if not team_name or pd.isna(team_name):
        return "https://a.espncdn.com/i/teamlogos/default-team-logo-500.png"
         
    logo_map = {
        # SEC (16)
        "ALABAMA": "333", "ARKANSAS": "8", "AUBURN": "2", "FLORIDA": "57", "GEORGIA": "61",
        "KENTUCKY": "96", "LSU": "99", "MISSISSIPPI STATE": "2283", "OLE MISS": "145", "MISSISSIPPI": "145",
        "MISSOURI": "142", "OKLAHOMA": "201", "SOUTH CAROLINA": "2579", "TENNESSEE": "2633",
        "TEXAS": "251", "TEXAS A&M": "245", "VANDERBILT": "238",
        
        # BIG TEN (18)
        "ILLINOIS": "356", "INDIANA": "84", "IOWA": "2294", "MARYLAND": "120", "MICHIGAN": "130",
        "MICHIGAN STATE": "127", "MINNESOTA": "135", "NEBRASKA": "158", "NORTHWESTERN": "77",
        "OHIO STATE": "194", "PENN STATE": "213", "PURDUE": "250", "RUTGERS": "164", "UCLA": "26",
        "USC": "30", "SOUTHERN CALIFORNIA": "30", "WASHINGTON": "258", "WISCONSIN": "275", "OREGON": "2483",
        
        # ACC (17)
        "BOSTON COLLEGE": "103", "CLEMSON": "228", "DUKE": "150", "FLORIDA STATE": "52", "FSU": "52",
        "GEORGIA TECH": "59", "LOUISVILLE": "97", "MIAMI": "2390", "NORTH CAROLINA": "153", "UNC": "153",
        "NC STATE": "152", "PITTSBURGH": "221", "PITT": "221", "SYRACUSE": "183", "VIRGINIA": "258",
        "VIRGINIA TECH": "259", "WAKE FOREST": "154", "CALIFORNIA": "25", "CAL": "25", "STANFORD": "24", "SMU": "2567",
        
        # BIG 12 (16)
        "BAYLOR": "239", "BYU": "252", "UCF": "2116", "CENTRAL FLORIDA": "2116", "CINCINNATI": "2132",
        "COLORADO": "38", "HOUSTON": "248", "IOWA STATE": "66", "KANSAS": "2305", "KANSAS STATE": "2306",
        "OKLAHOMA STATE": "197", "TCU": "2628", "TEXAS TECH": "2641", "UTAH": "254", "WEST VIRGINIA": "277",
        "ARIZONA": "12", "ARIZONA STATE": "9",
        
        # MAC (13 - CFB 27 updates included)
        "AKRON": "2006", "BALL STATE": "2050", "BOWLING GREEN": "189", "BUFFALO": "2084",
        "CENTRAL MICHIGAN": "2117", "EASTERN MICHIGAN": "2199", "KENT STATE": "2309", "MIAMI UNIVERSITY": "193", 
        "NORTHERN ILLINOIS": "2459", "NIU": "2459", "OHIO": "195", "TOLEDO": "2649", "WESTERN MICHIGAN": "2711",
        "UMASS": "233", "UMASS": "233",
        
        # SUN BELT (14)
        "APPALACHIAN STATE": "2026", "APP STATE": "2026", "ARKANSAS STATE": "2032", "COASTAL CAROLINA": "324",
        "GEORGIA SOUTHERN": "290", "GEORGIA STATE": "2247", "JAMES MADISON": "256", "JMU": "256", 
        "LOUISIANA": "309", "UL LAFAYETTE": "309", "ULM": "2433", "UL MONROE": "2433",
        "MARSHALL": "276", "OLD DOMINION": "295", "ODU": "295", "SOUTH ALABAMA": "6", "SOUTHERN MISS": "2572",
        "TEXAS STATE": "326", "TROY": "2653",
        
        # MOUNTAIN WEST & PAC-12 SURVIVORS (14)
        "AIR FORCE": "2005", "BOISE STATE": "68", "COLORADO STATE": "36", "FRESNO STATE": "24",
        "HAWAII": "62", "NEVADA": "2440", "UNLV": "2439", "NEW MEXICO": "167", 
        "SAN DIEGO STATE": "21", "SAN DIEGO ST": "21", "SAN DIEGO ST.": "21",
        "SAN JOSE STATE": "23", "UTAH STATE": "328", "WYOMING": "2751", "WASHINGTON STATE": "265", "OREGON STATE": "204",
        
        # AMERICAN (AAC) (14)
        "CHARLOTTE": "2429", "EAST CAROLINA": "151", "ECU": "151", "FAU": "2426", "FLORIDA ATLANTIC": "2426",
        "MEMPHIS": "235", "NAVY": "152", "NORTH TEXAS": "249", "RICE": "242", "SOUTH FLORIDA": "58", "USF": "58",
        "TEMPLE": "218", "TULANE": "216", "TULSA": "202", "UAB": "5", "UTSA": "2636", "ARMY": "349",
        
        # CONFERENCE USA (12 - CFB 27 additions included)
        "FIU": "2229", "JACKSONVILLE STATE": "2334", "LIBERTY": "2335", "LOUISIANA TECH": "2348", 
        "MIDDLE TENNESSEE": "2393", "MTSU": "2393", "NEW MEXICO STATE": "166", "SAM HOUSTON": "2411", 
        "UTEP": "2638", "WESTERN KENTUCKY": "98", "WKU": "98", "KENNESAW STATE": "2558", 
        "DELAWARE": "48", "MISSOURI STATE": "2428",
        
        # INDEPENDENTS & FCS JUMP UPS (4)
        "NOTRE DAME": "87", "CONNECTICUT": "41", "UCONN": "41",
        "SAC STATE": "16", "SACRAMENTO STATE": "16"
    }
    
    clean_key = str(team_name).upper().strip()
    team_id = logo_map.get(clean_key)
    
    if not team_id:
        for key, val in logo_map.items():
            if key in clean_key or clean_key in key:
                team_id = val
                break
                 
    if team_id:
        return f"https://a.espncdn.com/i/teamlogos/ncaa/500/{team_id}.png"
         
    return "https://a.espncdn.com/i/teamlogos/default-team-logo-500.png"

def get_avatar(name):
    return f"https://api.dicebear.com/7.x/initials/svg?seed={name}&backgroundColor=991b1b,141a22,1e3a8a&radius=50"

# ==========================================
# 4. HEADER CONTROL BAR
# ==========================================
years_found = set()
for df in [df_top25, df_heisman, df_standings, df_bracket, df_dynasty, df_coaches, df_nil, df_schedule, df_team_stats]:
    year_col = find_col(df, "year") or find_col(df, "seasonindex") if not df.empty else None
    if year_col:
        years_found.update(df[year_col].dropna().unique())

all_years = sorted(list(years_found), reverse=True) if years_found else [2026]

head_l, head_r = st.columns([8, 4])
with head_l:
    st.markdown("<h1 style='margin-bottom:0; font-weight:800; letter-spacing:-1px;'>🏈 RSG DYNASTY HUB</h1><p style='color:#9ca3af; margin-top:2px; font-size:15px;'>Automated Team Ledger & Coaching Registry</p>", unsafe_allow_html=True)
with head_r:
    selected_year = st.selectbox("📅 TIMELINE SEASON FILTER", options=all_years)

st.markdown("<br>", unsafe_allow_html=True)

# Define Main Tabs
tab_dynasty, tab_coach, tab_team, tab_stats, tab_media, tab_standings, tab_bracket = st.tabs([
    "🏠 DYNASTY SCORES",
    "👔 COACHING PORTAL",
    "🛡️ TEAM OFFICE Hub",
    "🏈 PLAYER STATS",
    "📺 MEDIA CENTER", 
    "📊 STANDINGS", 
    "🏆 BRACKET"
])

# ==========================================
# TAB 1: 🏠 DYNASTY SCORE LEADERBOARD
# ==========================================
with tab_dynasty:
    st.markdown("### 🏆 All-Time Career Dynasty Scores")
    st.markdown("The definitive overall ranking of coaches throughout the entire journey.")
     
    if not df_current_season.empty:
        c_col = find_col(df_current_season, "coach_name")
        s_col = find_col(df_current_season, "dynastyscore")
         
        if c_col and s_col:
            overall_df = df_current_season.sort_values(by=s_col, ascending=False).dropna(subset=[c_col])
             
            html_table = (
                '<table class="clean-table">'
                '<tr>'
                '<th style="width:10%;">Rank</th>'
                '<th style="width:30%;">Coach</th>'
                '<th style="width:30%;">Current Program</th>'
                '<th style="width:30%;">Career Dynasty Score</th>'
                '</tr>'
            )
            for idx, (_, row) in enumerate(overall_df.iterrows(), 1):
                coach_name = str(get_val(row, "coach_name", ""))
                if not coach_name or coach_name.lower() == 'nan': continue
                team = str(get_val(row, "team", ""))
                avatar_url = get_avatar(coach_name)
                logo_url = get_team_logo(team)
                score = get_val(row, "dynastyscore", 0)
                 
                html_table += (
                    '<tr>'
                    f'<td style="font-weight:bold; color:#ef4444;">#{idx}</td>'
                    f'<td style="font-weight:bold;"><img src="{avatar_url}" width="20" style="border-radius:50%; vertical-align:middle; margin-right:8px;">{coach_name}</td>'
                    f'<td style="font-weight:700;"><img src="{logo_url}" width="24" style="vertical-align:middle; margin-right:8px;">{team}</td>'
                    f'<td style="color:#d97706; font-weight:800; font-size:16px;">{score}</td>'
                    '</tr>'
                )
            html_table += "</table>"
            st.markdown(html_table, unsafe_allow_html=True)
             
    st.markdown("<br><hr style='border-color:#2d3748;'><br>", unsafe_allow_html=True)

    st.markdown(f"### 📅 {selected_year} Season Log")
    st.markdown("Track the prestige climb and performance for the currently selected season.")
     
    year_col = find_col(df_dynasty, "year")
    if not df_dynasty.empty and year_col:
        dynasty_df = df_dynasty[df_dynasty[year_col] == selected_year]
        score_col = find_col(dynasty_df, "dynastyscore")
         
        if not dynasty_df.empty and score_col:
            dynasty_df = dynasty_df.sort_values(by=score_col, ascending=False)
             
            html_table = (
                '<table class="clean-table">'
                '<tr>'
                '<th>Rank</th><th>Coach</th><th>Program</th><th>Dynasty Score</th><th>Prestige</th><th>Wins-Losses</th>'
                '</tr>'
            )
            for idx, (_, row) in enumerate(dynasty_df.iterrows(), 1):
                coach_name = str(get_val(row, "coach_name", ""))
                team = str(get_val(row, "team", ""))
                avatar_url = get_avatar(coach_name)
                logo_url = get_team_logo(team)
                d_score = get_val(row, "dynastyscore", 0)
                prestige = get_val(row, "teamprestige", "N/A")
                wins = get_val(row, 'wins', 0)
                losses = get_val(row, 'loses', 0) 
                 
                html_table += (
                    '<tr>'
                    f'<td style="font-weight:bold; color:#ef4444;">#{idx}</td>'
                    f'<td style="font-weight:bold;"><img src="{avatar_url}" width="20" style="border-radius:50%; vertical-align:middle; margin-right:8px;">{coach_name}</td>'
                    f'<td style="font-weight:700;"><img src="{logo_url}" width="24" style="vertical-align:middle; margin-right:8px;">{team}</td>'
                    f'<td style="color:#34d399; font-weight:800;">{d_score}</td>'
                    f'<td>{prestige}⭐</td>'
                    f'<td>{wins}-{losses}</td>'
                    '</tr>'
                )
            html_table += "</table>"
            st.markdown(html_table, unsafe_allow_html=True)
        else:
            st.info("No dynasty scores mapped for this season.")
    else:
        st.info("Dynasty Score tab is empty.")

# ==========================================
# TAB 2: 👔 COACHING PORTAL (WITH DIRECT TEAM STATS OVERVIEW)
# ==========================================
with tab_coach:
    year_col = find_col(df_coaches, "year")
    if not df_coaches.empty and year_col:
        coach_df_year = df_coaches[df_coaches[year_col] == selected_year]
        coach_col = find_col(coach_df_year, "coach_name")
         
        if coach_col and not coach_df_year.empty:
            coach_options = sorted(list(coach_df_year[coach_col].dropna().unique()))
            selected_coach = st.selectbox("👔 SELECT HEAD COACH PROFILE", options=coach_options, key="coach_sel")
             
            coach_profile = coach_df_year[coach_df_year[coach_col] == selected_coach].iloc[0]
             
            st.markdown("<hr style='border-color:#2d3748; margin:10px 0 20px 0;'>", unsafe_allow_html=True)
            prof_l, prof_r = st.columns([1, 5])
             
            coach_name = str(get_val(coach_profile, 'coach_name', ''))
            team = str(get_val(coach_profile, 'team', ''))
            level = get_val(coach_profile, 'level', 0)
            arch = str(get_val(coach_profile, 'archetype', 'COACH')).upper()
            alma = get_val(coach_profile, 'almamater', 'TBD')
            logo_url = get_team_logo(team)
            avatar_url = get_avatar(coach_name)
             
            with prof_l:
                st.image(avatar_url, width=110)
            with prof_r:
                prof_html = (
                    f"<h2 style='margin:0; font-weight:800; color:white;'>COACH {coach_name.upper()}</h2>"
                    f"<p style='font-size:18px; color:#ef4444; margin:2px 0 6px 0; font-weight:bold;'>"
                    f"<img src='{logo_url}' width='22' style='vertical-align:middle; margin-right:8px;'>{team} Head Coach"
                    f"</p>"
                    f"<span style='background-color:#991b1b; padding:4px 8px; border-radius:4px; font-size:12px; font-weight:bold; letter-spacing:1px;'>LVL {level} {arch}</span>"
                    f"<span style='background-color:#1c2430; padding:4px 8px; border-radius:4px; font-size:12px; font-weight:bold; margin-left:6px; border:1px solid #2d3748;'>ALMA MATER: {alma}</span>"
                )
                st.markdown(prof_html, unsafe_allow_html=True)
                 
            st.markdown("<br>", unsafe_allow_html=True)
            m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
             
            c_wins = get_val(coach_profile, 'career_wins', 0)
            c_losses = get_val(coach_profile, 'career_losses', 0)
            nc = get_val(coach_profile, 'nc', 0)
            conf = get_val(coach_profile, 'conf', 0)
            p_wins = get_val(coach_profile, 'playoffwins', 0)
            p_losses = get_val(coach_profile, 'playofflosses', 0)
            prestige = get_val(coach_profile, 'prestige', 'C')
             
            with m_col1:
                st.markdown(f"<div class='stat-box'><p class='stat-val'>{c_wins}-{c_losses}</p><p class='stat-lbl'>Career Record</p></div>", unsafe_allow_html=True)
            with m_col2:
                st.markdown(f"<div class='stat-box'><p class='stat-val'>{nc}</p><p class='stat-lbl'>National Titles</p></div>", unsafe_allow_html=True)
            with m_col3:
                st.markdown(f"<div class='stat-box'><p class='stat-val'>{conf}</p><p class='stat-lbl'>Conf Crowns</p></div>", unsafe_allow_html=True)
            with m_col4:
                st.markdown(f"<div class='stat-box'><p class='stat-val'>{p_wins}-{p_losses}</p><p class='stat-lbl'>Playoff W-L</p></div>", unsafe_allow_html=True)
            with m_col5:
                st.markdown(f"<div class='stat-box'><p class='stat-val' style='color:#34d399;'>{prestige}</p><p class='stat-lbl'>Coach Grade</p></div>", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            
            # --- TACTICS & LATEST GAME BOX SCORE SECTION ---
            details_l, details_r = st.columns([1, 2])
             
            off_scheme = fix_sheet_format(get_val(coach_profile, "offscheme", "TBD"), is_scheme=False)
            def_scheme = fix_sheet_format(get_val(coach_profile, "defscheme", "TBD"), is_scheme=True)
            draft = get_val(coach_profile, "draft", 0)
            t5rec = get_val(coach_profile, "t5rec", 0)
            
            # Aggregate dynamic values from Team_Stats sheet tab
            total_off_yds, total_pass_yds, total_rush_yds, total_pass_tds, total_rush_tds = 0, 0, 0, 0, 0
            total_def_yds, total_def_pass, total_def_rush, takeaways, giveaways = 0, 0, 0, 0, 0
            
            if not df_team_stats.empty:
                ts_team_col = find_col(df_team_stats, "teamName") or find_col(df_team_stats, "team")
                ts_year_col = find_col(df_team_stats, "seasonIndex") or find_col(df_team_stats, "year")
                
                filtered_stats = df_team_stats
                
                # Decoupled filtering: Apply Team filter if team column exists
                if ts_team_col:
                    filtered_stats = filtered_stats[
                        filtered_stats[ts_team_col].astype(str).str.upper().str.strip() == team.upper().strip()
                    ]
                
                # Apply Year filter ONLY if a year column actually exists in the sheet
                if ts_year_col:
                    filtered_stats = filtered_stats[
                        filtered_stats[ts_year_col] == selected_year
                    ]
                
                if not filtered_stats.empty:
                    total_off_yds = int(filtered_stats[find_col(df_team_stats, "offTotalYds")].sum()) if find_col(df_team_stats, "offTotalYds") else 0
                    total_pass_yds = int(filtered_stats[find_col(df_team_stats, "offPassYds")].sum()) if find_col(df_team_stats, "offPassYds") else 0
                    total_rush_yds = int(filtered_stats[find_col(df_team_stats, "offRushYds")].sum()) if find_col(df_team_stats, "offRushYds") else 0
                    total_pass_tds = int(filtered_stats[find_col(df_team_stats, "offPassTDs")].sum()) if find_col(df_team_stats, "offPassTDs") else 0
                    total_rush_tds = int(filtered_stats[find_col(df_team_stats, "offRushTDs")].sum()) if find_col(df_team_stats, "offRushTDs") else 0
                    
                    total_def_yds  = int(filtered_stats[find_col(df_team_stats, "defTotalYds")].sum()) if find_col(df_team_stats, "defTotalYds") else 0
                    total_def_pass = int(filtered_stats[find_col(df_team_stats, "defPassYds")].sum()) if find_col(df_team_stats, "defPassYds") else 0
                    total_def_rush = int(filtered_stats[find_col(df_team_stats, "defRushYds")].sum()) if find_col(df_team_stats, "defRushYds") else 0
                    
                    takeaways = int(filtered_stats[find_col(df_team_stats, "tOTakeaways")].sum()) if find_col(df_team_stats, "tOTakeaways") else 0
                    giveaways = int(filtered_stats[find_col(df_team_stats, "tOGiveAways")].sum()) if find_col(df_team_stats, "tOGiveAways") else 0

            with details_l:
                st.markdown("### 🛠️ Tactical Scheme Data")
                scheme_html = (
                    '<div class="sports-card" style="border-left-color: #2563eb;">'
                    '<table style="width:100%; border:none; background:none;">'
                    f'<tr style="border:none; background:none;"><td style="padding:6px; font-weight:bold; color:#9ca3af; border:none;">OFFENSIVE PLAYBOOK:</td><td style="padding:6px; font-weight:bold; text-align:right; border:none; color:white;">{off_scheme}</td></tr>'
                    f'<tr style="border:none; background:none;"><td style="padding:6px; font-weight:bold; color:#9ca3af; border:none;">DEFENSIVE SCHEME:</td><td style="padding:6px; font-weight:bold; text-align:right; border:none; color:white;">{def_scheme}</td></tr>'
                    f'<tr style="border:none; background:none;"><td style="padding:6px; font-weight:bold; color:#9ca3af; border:none;">DRAFT PICKS:</td><td style="padding:6px; font-weight:bold; text-align:right; border:none; color:white;">{draft}</td></tr>'
                    f'<tr style="border:none; background:none;"><td style="padding:6px; font-weight:bold; color:#9ca3af; border:none;">TOP 5 CLASSES:</td><td style="padding:6px; font-weight:bold; text-align:right; border:none; color:white;">{t5rec}</td></tr>'
                    '</table></div>'
                )
                st.markdown(scheme_html, unsafe_allow_html=True)

            with details_r:
                st.markdown("### 🏟️ Latest Game Box Score")
                if not df_game_logs.empty:
                    gl_team_col = find_col(df_game_logs, "teamName") or find_col(df_game_logs, "team")
                    gl_year_col = find_col(df_game_logs, "seasonIndex") or find_col(df_game_logs, "year")
                    gl_week_col = find_col(df_game_logs, "weekIndex") or find_col(df_game_logs, "week")
                    
                    if gl_team_col and gl_year_col and gl_week_col:
                        team_logs = df_game_logs[
                            (df_game_logs[gl_year_col] == selected_year) & 
                            (df_game_logs[gl_team_col].astype(str).str.upper().str.strip() == team.upper().strip())
                        ]
                        
                        if not team_logs.empty:
                            try:
                                # Standardize week to numeric for accurate sorting of 'latest'
                                team_logs_sorted = team_logs.copy()
                                team_logs_sorted['sort_week'] = pd.to_numeric(team_logs_sorted[gl_week_col].astype(str).str.extract(r'(\d+)')[0], errors='coerce').fillna(0)
                                latest_log = team_logs_sorted.loc[team_logs_sorted['sort_week'].idxmax()]
                                
                                # Extract standard box score variables
                                lwk = get_val(latest_log, "weekIndex") or get_val(latest_log, "week", "N/A")
                                opp = get_val(latest_log, "opponentName") or get_val(latest_log, "opponent", "Unknown")
                                t_score = get_val(latest_log, "teamScore", get_val(latest_log, "pts", 0))
                                o_score = get_val(latest_log, "oppScore", get_val(latest_log, "oppPts", 0))
                                
                                # Evaluate Result (W/L)
                                result = get_val(latest_log, "result") or get_val(latest_log, "wl")
                                if not result or str(result).lower() == 'nan':
                                    result = "W" if int(t_score) > int(o_score) else "L" if int(t_score) < int(o_score) else "T"
                                    
                                wl_color = "#10b981" if str(result).upper() == "W" else "#ef4444"
                                opp_logo = get_team_logo(opp)
                                
                                box_html = f"""
                                <div class="sports-card" style="border-left-color: {wl_color}; padding: 24px;">
                                    <p style="text-align:center; color:#9ca3af; font-weight:bold; letter-spacing:2px; margin-top:0;">WEEK {lwk} RESULT</p>
                                    <table style="width:100%; border:none; background:none;">
                                        <tr style="border:none; background:none;">
                                            <td style="text-align:center; width:40%; border:none;">
                                                <img src="{logo_url}" width="65"><br><span style="font-size:16px; font-weight:800; color:white;">{team.upper()}</span><br><span style="font-size:32px; font-weight:900;">{t_score}</span>
                                            </td>
                                            <td style="text-align:center; width:20%; border:none; color:#9ca3af; font-weight:bold; vertical-align:middle;">
                                                FINAL<br><span style="color:{wl_color}; font-size:24px;">{str(result).upper()}</span>
                                            </td>
                                            <td style="text-align:center; width:40%; border:none;">
                                                <img src="{opp_logo}" width="65"><br><span style="font-size:16px; font-weight:800; color:white;">{str(opp).upper()}</span><br><span style="font-size:32px; font-weight:900;">{o_score}</span>
                                            </td>
                                        </tr>
                                    </table>
                                </div>
                                """
                                st.markdown(box_html, unsafe_allow_html=True)
                            except Exception as e:
                                st.info("Could not render the latest game log formatting.")
                        else:
                            st.info(f"No game logs found for {team} in the {selected_year} season.")
                else:
                    st.info("Raw_Game_Logs data is missing or empty.")

            st.markdown("<br>", unsafe_allow_html=True)
            
            # --- DIRECT TEAM_STATS DISPLAY SECTION ---
            st.markdown("### 📊 Comprehensive Team Stats")
            if not df_team_stats.empty:
                ts_team_col = find_col(df_team_stats, "teamName") or find_col(df_team_stats, "team")
                ts_year_col = find_col(df_team_stats, "seasonIndex") or find_col(df_team_stats, "year")
                
                filtered_stats = df_team_stats
                
                # Decoupled filtering: Apply Team filter if team column exists
                if ts_team_col:
                    filtered_stats = filtered_stats[
                        filtered_stats[ts_team_col].astype(str).str.upper().str.strip() == team.upper().strip()
                    ]
                
                # Apply Year filter ONLY if a year column actually exists in the sheet
                if ts_year_col:
                    filtered_stats = filtered_stats[
                        filtered_stats[ts_year_col] == selected_year
                    ]
                
                if not filtered_stats.empty:
                    # Clean up visual dataframe
                    clean_display_df = filtered_stats.copy()
                    if ts_year_col:
                        clean_display_df = clean_display_df.drop(columns=[ts_year_col], errors='ignore')
                        
                    st.dataframe(clean_display_df, use_container_width=True, hide_index=True)
                else:
                    st.info(f"No entry found in Team_Stats tab for {team} during the {selected_year} season.")
            else:
                st.info("Team_Stats sheet is currently empty.")
        else:
             st.info("No coaches found for this season.")
    else:
        st.info("ℹ️ Coaching data is currently empty.")

# ==========================================
# TAB 3: 🛡️ TEAM OFFICE HUB (WITH SCHEDULES)
# ==========================================
with tab_team:
    st.markdown("### 💰 NIL & Salary Cap Compliance Tracker")
     
    teams_found_list = set()
    if not df_roster.empty and find_col(df_roster, "team") in df_roster.columns:
        teams_found_list.update(df_roster[df_roster[find_col(df_roster, "year")] == selected_year][find_col(df_roster, "team")].dropna().unique())
    if not df_nil.empty and find_col(df_nil, "team") in df_nil.columns:
        teams_found_list.update(df_nil[df_nil[find_col(df_nil, "year")] == selected_year][find_col(df_nil, "team")].dropna().unique())
    if not df_schedule.empty and find_col(df_schedule, "team") in df_schedule.columns:
        teams_found_list.update(df_schedule[df_schedule[find_col(df_schedule, "year")] == selected_year][find_col(df_schedule, "team")].dropna().unique())
        
    teams_avail = sorted(list(teams_found_list))
    
    if teams_avail:
        selected_team = st.selectbox("🛡️ SELECT PROGRAM", options=teams_avail)
        st.markdown("<br>", unsafe_allow_html=True)
         
        # Fetch Financial NIL Data
        n_year_col = find_col(df_nil, "year")
        n_team_col = find_col(df_nil, "team")
        team_nil = df_nil[(df_nil[n_year_col] == selected_year) & (df_nil[n_team_col] == selected_team)] if not df_nil.empty else pd.DataFrame()
         
        if not team_nil.empty:
            st.markdown(f"#### 🏦 {str(selected_team).upper()} Financial Dashboard")
            nil_row = team_nil.iloc[0]
             
            total_budget = float(get_val(nil_row, 'totalbudget', 0))
            unspent = float(get_val(nil_row, 'unspent', 0))
            spent = total_budget - unspent
             
            staff = float(get_val(nil_row, 'staff', 0))
            fac = float(get_val(nil_row, 'facilities', 0))
            recruits = float(get_val(nil_row, 'recruitsnil', 0))
            roster_nil = float(get_val(nil_row, 'rosternil', 0))
            misc = float(get_val(nil_row, 'miscellaneous', 0))
             
            c_pres = get_val(nil_row, 'conferenceprestige', 0)
            b_exp = get_val(nil_row, 'brandexposure', 0)
            s_atm = get_val(nil_row, 'stadiumatmosphere', 0)
            p_trad = get_val(nil_row, 'programtradition', 0)
             
            kpi1, kpi2, kpi3 = st.columns(3)
            with kpi1:
                st.markdown(f"<div class='stat-box' style='border-color:#3b82f6;'><p class='stat-val'>${total_budget:,.0f}K</p><p class='stat-lbl'>Total NIL Budget</p></div>", unsafe_allow_html=True)
            with kpi2:
                st.markdown(f"<div class='stat-box' style='border-color:#ef4444;'><p class='stat-val'>${spent:,.0f}K</p><p class='stat-lbl'>Allocated Funds</p></div>", unsafe_allow_html=True)
            with kpi3:
                st.markdown(f"<div class='stat-box' style='border-color:#10b981;'><p class='stat-val'>${unspent:,.0f}K</p><p class='stat-lbl'>Available Cap Space</p></div>", unsafe_allow_html=True)
             
            st.markdown("<br>", unsafe_allow_html=True)
             
            ch1, ch2 = st.columns(2)
            with ch1:
                st.markdown("<h5 style='text-align:center;'>Cap Space Overview</h5>", unsafe_allow_html=True)
                fig1 = px.pie(
                    values=[spent, unspent], 
                    names=['Allocated', 'Unspent Space'],
                    hole=0.6,
                    color_discrete_sequence=['#ef4444', '#10b981']
                )
                fig1.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(t=10, b=10, l=10, r=10), showlegend=True, font=dict(color="white"))
                st.plotly_chart(fig1, use_container_width=True)
             
            with ch2:
                st.markdown("<h5 style='text-align:center;'>Budget Distribution</h5>", unsafe_allow_html=True)
                exp_vals = [staff, fac, recruits, roster_nil, misc]
                exp_names = ['Staff', 'Facilities', 'Recruits', 'Roster', 'Misc']
                 
                fig2 = px.pie(
                    values=exp_vals, 
                    names=exp_names,
                    hole=0.6,
                    color_discrete_sequence=['#3b82f6', '#8b5cf6', '#f59e0b', '#ec4899', '#64748b']
                )
                fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(t=10, b=10, l=10, r=10), showlegend=True, font=dict(color="white"))
                st.plotly_chart(fig2, use_container_width=True)

            st.markdown("##### 🏛️ Program Grades")
            pg1, pg2, pg3, pg4 = st.columns(4)
            with pg1:
                st.markdown(f"<div class='stat-box'><p class='stat-val' style='color:#f59e0b;'>{c_pres}</p><p class='stat-lbl'>Conf Prestige</p></div>", unsafe_allow_html=True)
            with pg2:
                st.markdown(f"<div class='stat-box'><p class='stat-val' style='color:#f59e0b;'>{b_exp}</p><p class='stat-lbl'>Brand Exposure</p></div>", unsafe_allow_html=True)
            with pg3:
                st.markdown(f"<div class='stat-box'><p class='stat-val' style='color:#f59e0b;'>{s_atm}</p><p class='stat-lbl'>Stadium Atmos.</p></div>", unsafe_allow_html=True)
            with pg4:
                st.markdown(f"<div class='stat-box'><p class='stat-val' style='color:#f59e0b;'>{p_trad}</p><p class='stat-lbl'>Program Tradition</p></div>", unsafe_allow_html=True)
        else:
            st.warning("No NIL Payroll records matching this selection.")
             
        st.markdown("<br><hr style='border-color:#2d3748;'><br>", unsafe_allow_html=True)
        
        # --- SIDE BY SIDE: SCHEDULE & ROSTER ---
        hub_left, hub_right = st.columns(2)
        
        with hub_left:
            if not df_schedule.empty:
                sched_year_col = find_col(df_schedule, "year")
                sched_team_col = find_col(df_schedule, "team")
                if sched_year_col and sched_team_col:
                    team_sched = df_schedule[(df_schedule[sched_year_col] == selected_year) & (df_schedule[sched_team_col] == selected_team)]
                    
                    week_col = find_col(team_sched, "week")
                    if week_col and not team_sched.empty:
                        try:
                            team_sched['sort_week'] = pd.to_numeric(team_sched[week_col].astype(str).str.extract(r'(\d+)')[0], errors='coerce').fillna(99)
                            team_sched = team_sched.sort_values(by='sort_week').drop(columns=['sort_week'])
                        except:
                            pass
                    
                    if not team_sched.empty:
                        st.markdown("### 📅 Program Schedule")
                        sched_table_html = (
                            '<table class="clean-table">'
                            '<tr><th style="width:20%;">Week</th><th style="width:25%;">Location</th><th style="width:55%;">Opponent</th></tr>'
                        )
                        for _, s_row in team_sched.iterrows():
                            wk = get_val(s_row, "week")
                            loc = get_val(s_row, "home_away")
                            opp = get_val(s_row, "opponent")
                            
                            opp_logo = get_team_logo(opp) if str(opp).upper() != "BYE" else "https://a.espncdn.com/i/teamlogos/default-team-logo-500.png"
                            loc_badge = "🏠 HOME" if str(loc).upper() == "HOME" else "✈️ AWAY" if str(loc).upper() == "AWAY" else "💤 BYE"
                            opp_name_formatted = "BYE WEEK" if str(opp).upper() == "BYE" else str(opp).upper()
                            
                            sched_table_html += (
                                '<tr>'
                                f'<td><b>Wk {wk}</b></td>'
                                f'<td><span style="background-color:#1c2430; padding:4px 8px; border-radius:4px; font-weight:bold; font-size:11px;">{loc_badge}</span></td>'
                                f'<td><img src="{opp_logo}" width="22" style="vertical-align:middle; margin-right:8px; background:none;">{opp_name_formatted}</td>'
                                '</tr>'
                            )
                        sched_table_html += '</table>'
                        st.markdown(sched_table_html, unsafe_allow_html=True)
        
        with hub_right:
            r_year_col = find_col(df_roster, "year")
            team_col = find_col(df_roster, "team")
            if not df_roster.empty and r_year_col and team_col:
                team_roster = df_roster[(df_roster[r_year_col] == selected_year) & (df_roster[team_col] == selected_team)]
                if not team_roster.empty:
                    st.markdown("### 📋 Active Roster Ledger")
                    nil_val_col = find_col(team_roster, "nil_value")
                    if nil_val_col:
                        team_roster = team_roster.sort_values(by=nil_val_col, ascending=False)
                     
                    display_cols = []
                    for c in ["player_name", "position", "player_ovr", "class", "nil_value"]:
                        found = find_col(team_roster, c)
                        if found: display_cols.append(found)
                     
                    if display_cols:
                        st.dataframe(team_roster[display_cols], use_container_width=True, hide_index=True, height=600)
                else:
                    st.info("No active roster rows verified for this program.")
    else:
        st.info("Program lists are empty across database tabs.")

# ==========================================
# TAB 4: 🏈 PLAYER STATS
# ==========================================
with tab_stats:
    st.markdown("### 🏈 Player Statistics Database")
    stat_type = st.radio("Select Stat Category", ["Passing", "Rushing", "Receiving", "Defense"], horizontal=True)
    
    stat_map = {
        "Passing": (df_pass, "yards"),
        "Rushing": (df_rush, "yards"),
        "Receiving": (df_rec, "yards"),
        "Defense": (df_def, "tak")
    }
    
    selected_df, sort_metric = stat_map[stat_type]
    
    if not selected_df.empty:
        s_year_col = find_col(selected_df, "year")
        if s_year_col:
            yr_stats = selected_df[selected_df[s_year_col] == selected_year]
            sort_c = find_col(yr_stats, sort_metric)
            if sort_c:
                yr_stats = yr_stats.sort_values(by=sort_c, ascending=False)
             
            st.dataframe(yr_stats.drop(columns=[s_year_col], errors='ignore'), use_container_width=True, hide_index=True)
    else:
        st.info(f"No {stat_type} stats uploaded yet.")

# ==========================================
# TAB 5: 📺 LEAGUE MEDIA CENTER
# ==========================================
with tab_media:
    col_poll, col_awards = st.columns([2, 1])
    
    with col_poll:
        st.markdown("### 📊 CFP National Top 25 Poll")
        year_col = find_col(df_top25, "year")
        rank_col = find_col(df_top25, "rank")
        
        if not df_top25.empty and year_col and rank_col:
            year_poll = df_top25[df_top25[year_col] == selected_year].sort_values(by=rank_col)
            if not year_poll.empty:
                for _, row in year_poll.iterrows():
                    rank = int(get_val(row, "rank", 0))
                    team = str(get_val(row, "team", ""))
                    logo = get_team_logo(team)
                    rec = fix_sheet_format(get_val(row, "record", ""))
                    
                    poll_html = (
                        '<div class="sports-card">'
                        '<table style="width:100%; border:none; background:none; margin:0;">'
                        '<tr style="border:none; background:none;">'
                        f'<td class="ranking-badge" style="width:10%; border:none; padding:0;">#{rank}</td>'
                        f'<td style="width:10%; border:none; padding:0; text-align:center;"><img src="{logo}" width="36"></td>'
                        f'<td style="font-size:17px; font-weight:700; width:60%; border:none; padding:0; padding-left:12px;">{team.upper()}</td>'
                        f'<td style="text-align:right; color:#9ca3af; font-weight:700; font-size:15px; border:none; padding:0;">{rec}</td>'
                        '</tr></table></div>'
                    )
                    st.markdown(poll_html, unsafe_allow_html=True)
            else:
                st.info(f"No Top 25 ranking history logged for the {selected_year} season cycle yet.")
        else:
            st.info("Top 25 sheet data is awaiting entries.")

    with col_awards:
        st.markdown("### 🏆 Heisman Trophy History")
        year_col = find_col(df_heisman, "year")
        if not df_heisman.empty and year_col:
            year_heisman = df_heisman[df_heisman[year_col] == selected_year]
            if not year_heisman.empty:
                for _, row in year_heisman.iterrows():
                    name = str(get_val(row, "name", ""))
                    team = str(get_val(row, "team", ""))
                    pos = get_val(row, "pos", "")
                    
                    team_logo = get_team_logo(team)
                    
                    heisman_html = (
                        '<div class="sports-card" style="text-align:center; border-left:none; border-top:4px solid #d97706; padding:24px 16px;">'
                        '<div style="display:flex; justify-content:center; align-items:center; margin-bottom:16px;">'
                        f'<img src="{team_logo}" width="90" style="z-index:2; position:relative;">'
                        '</div>'
                        f'<h3 style="margin:0; font-weight:800; color:white;">{name.upper()}</h3>'
                        f'<p style="color:#d97706; font-weight:700; margin:4px 0 12px 0; letter-spacing:1px;">{pos} | {team.upper()}</p>'
                        '<div style="background-color:#1c232e; padding:6px; border-radius:4px; font-size:11px; color:#a1a1aa; font-weight:bold; letter-spacing:0.5px;">OFFICIAL HEISMAN TROPHY WINNER</div>'
                        '</div>'
                    )
                    st.markdown(heisman_html, unsafe_allow_html=True)
            else:
                st.info(f"No Heisman award winners recorded for the {selected_year} timeline segment.")
        else:
            st.info("Heisman history tab is awaiting entries.")

# ==========================================
# TAB 6: 📊 CONFERENCE STANDINGS
# ==========================================
with tab_standings:
    st.markdown("### 🏛️ Conference Standings Leaderboard")
    year_col = find_col(df_standings, "year")
    conf_col = find_col(df_standings, "conference")
    rank_col = find_col(df_standings, "rank")
    
    if not df_standings.empty and year_col and conf_col and rank_col:
        year_standings = df_standings[df_standings[year_col] == selected_year]
        if not year_standings.empty:
            unique_conferences = year_standings[conf_col].dropna().unique()
            for conf in unique_conferences:
                conf_df = year_standings[year_standings[conf_col] == conf].sort_values(by=rank_col)
                st.markdown(f"#### 🏷️ {str(conf).upper()} Conference Standings")
                
                conf_html = (
                    '<table class="clean-table">'
                    '<tr>'
                    '<th style="width:10%;">Rank</th>'
                    '<th style="width:50%;">Program School Name</th>'
                    '<th style="width:20%;">Overall W-L</th>'
                    '<th style="width:20%;">Conference W-L</th>'
                    '</tr>'
                )
                for _, row in conf_df.iterrows():
                    rank = int(get_val(row, "rank", 0))
                    team = str(get_val(row, "team", ""))
                    logo = get_team_logo(team)
                    o_wins = int(get_val(row, "overall_wins", 0))
                    o_loss = int(get_val(row, "overall_losses", 0))
                    c_wins = int(get_val(row, "conf_wins", 0))
                    c_loss = int(get_val(row, "conf_losses", 0))
                    
                    conf_html += (
                        '<tr>'
                        f'<td style="font-weight:bold; color:#ef4444;">{rank}</td>'
                        f'<td style="font-weight:700;"><img src="{logo}" width="24" style="vertical-align:middle; margin-right:12px;">{team}</td>'
                        f'<td>{o_wins}-{o_loss}</td>'
                        f'<td style="color:#34d399; font-weight:700;">{c_wins}-{c_loss}</td>'
                        '</tr>'
                    )
                conf_html += "</table>"
                st.markdown(conf_html, unsafe_allow_html=True)
        else:
            st.info(f"No conference data found matching the {selected_year} filter window.")
    else:
        st.info("Conference Standings data sheet is awaiting setup.")

# ==========================================
# TAB 7: 🏆 PLAYOFF BRACKET
# ==========================================
with tab_bracket:
    st.markdown("### 🏆 Playoff Bracket Matrix")
    
    if not df_bracket.empty:
        year_bracket = df_bracket[df_bracket[find_col(df_bracket, "year")] == selected_year]
        
        if not year_bracket.empty:
            def get_game_data(round_name, index):
                matches = year_bracket[year_bracket[find_col(year_bracket, "round")] == round_name]
                if len(matches) > index:
                    return matches.iloc[index]
                return None

            def render_node(round_name, index):
                row = get_game_data(round_name, index)
                if row is None:
                    return "<div class='bracket-card'><i>Pending</i></div>"
                
                t1 = get_val(row, 'team_1')
                t2 = get_val(row, 'team_2')
                s1 = get_val(row, 'score_1')
                s2 = get_val(row, 'score_2')
                seed1 = get_val(row, 'seed_1')
                seed2 = get_val(row, 'seed_2')
                
                t1_win = (str(s1).isdigit() and str(s2).isdigit() and int(s1) > int(s2))
                t2_win = (str(s1).isdigit() and str(s2).isdigit() and int(s2) > int(s1))
                
                return (
                    f"<div class='bracket-card'>"
                    f"<table style='width:100%; border:none; background:none;'>"
                    f"<tr style='background:none; border:none;'><td style='border:none;'><img src='{get_team_logo(t1)}' width='18'> <span {'class=winner-text' if t1_win else ''}>({seed1}) {t1}</span></td><td style='border:none; text-align:right;'>{s1}</td></tr>"
                    f"<tr style='background:none; border:none;'><td style='border:none;'><img src='{get_team_logo(t2)}' width='18'> <span {'class=winner-text' if t2_win else ''}>({seed2}) {t2}</span></td><td style='border:none; text-align:right;'>{s2}</td></tr>"
                    f"</table></div>"
                )

            b1, b2, b3, b4 = st.columns(4)
            with b1:
                st.markdown("🟢 FIRST ROUND")
                for i in range(4): st.markdown(render_node("First Round", i), unsafe_allow_html=True)
            with b2:
                st.markdown("🔵 QUARTERFINALS")
                st.markdown("<div style='height:40px;'></div>", unsafe_allow_html=True)
                for i in range(4): st.markdown(render_node("Quarterfinal", i), unsafe_allow_html=True)
            with b3:
                st.markdown("🟡 SEMIFINALS")
                st.markdown("<div style='height:120px;'></div>", unsafe_allow_html=True)
                for i in range(2): st.markdown(render_node("Semifinal", i), unsafe_allow_html=True)
            with b4:
                st.markdown("🏆 CHAMPIONSHIP")
                st.markdown("<div style='height:240px;'></div>", unsafe_allow_html=True)
                st.markdown(render_node("National Championship", 0), unsafe_allow_html=True)
        else:
            st.info("No bracket data found for this year.")
