import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import streamlit.components.v1 as components

# 페이지 설정 - TV 전체화면용
st.set_page_config(
    page_title="아자영어 통과현황 (커트 : 뜻 94, 문맥 90, 독해 80)",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS 스타일 - TV 최적화
st.markdown("""
    <style>
    .stApp {
        background-color: #f5f5f5;
    }
    .main {
        padding: 0;
        max-width: 100%;
    }
    /* TV모드: 상단 여백 극단 압축 */
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 0 !important;
    }
    header[data-testid="stHeader"] {
        display: none !important;
    }
    #MainMenu {
        display: none !important;
    }
    footer {
        display: none !important;
    }
    div[data-testid="stDecoration"] {
        display: none !important;
    }
    div[data-testid="stToolbar"] {
        display: none !important;
    }
    div[data-testid="stMetricValue"] {
        font-size: 36px;
    }
    .hero-badge {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 5px 10px;
        border-radius: 15px;
        font-weight: bold;
        display: inline-block;
        margin: 2px;
    }
    /* 개인리포트 다크모드용 */
    .report-dark {
        background-color: #0a0e1a;
        border-radius: 12px;
        padding: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# google_sheets.py import 추가
try:
    from google_sheets import load_data_from_sheets, get_test_data
    GOOGLE_SHEETS_AVAILABLE = True
except ImportError:
    GOOGLE_SHEETS_AVAILABLE = False

# ============================================
# ★★★ master26 시트 URL을 여기에 붙여넣으세요 ★★★
# ============================================
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1DCpUkyWxD2qm_oH4ckr9OzvpKTvXqzZ7lPAHbt9QWmE/edit"
SHEET_NAME = "수업일지"

# 누적 영웅 시작 기준일 (11월 1일)
CUMULATIVE_START_DATE = "2026-01-01"

# 학생 간격 설정 (4개 막대로 변경)
STUDENT_WIDTH = 3.3

# ============================================
# 데이터 로드 함수
# ============================================
@st.cache_data(ttl=10)
def load_data():
    """구글시트 또는 테스트 데이터 로드"""
    if GOOGLE_SHEETS_AVAILABLE and not GOOGLE_SHEET_URL.endswith("YOUR_SHEET_ID/edit"):
        df = load_data_from_sheets(GOOGLE_SHEET_URL, SHEET_NAME)
        if df is not None and not df.empty:
            df = df.rename(columns={'반코드': '반'})
            return df
    
    # 테스트 데이터 (문법점수 추가)
    data = {
        '날짜': ['2025-10-16'] * 30 + ['2025-10-15'] * 30 + ['2025-10-14'] * 30,
        '이름': ['이민규', '박진건', '조항진', '이서준B', '오준혁',
                '권라임', '이선우', '박연우', '오윤성', '박정현',
                '김단율', '이준서', '임지윤', '김제욱', '이정우',
                '송유현', '박정우', '박재범', '이윤일', '김예일',
                '유건영', '민준원', '강민재', '이찬범', '김동호',
                '김태연', '김성우', '백기범', '이제이', '서준택'] * 3,
        '반': ['초등', '초등', '초등', '초등', '초등',
              '중등', '중등', '중등', '중등', '중등',
              '중등', '중등', '중등', '중등', '중등',
              '중등', '수능', '수능', '수능', '수능',
              '수능', '수능', '수능', '수능', '수능',
              '수능', '수능', '중등', '중등', '중등'] * 3,
        '출석': ['출석', '지각', '출석', '출석', '출석',
                '출석', '출석', '지각', '출석', '출석',
                '결석', '출석', '결석', '결석', '결석',
                '출석', '출석', '출석', '지각', '출석',
                '출석', '결석', '출석', '출석', '출석',
                '출석', '출석', '출석', '출석', '출석'] * 3,
        '어휘점수': [87, 100, 97, 92, 88,
                   92, 100, 98, 100, 100,
                   None, 86, None, None, None,
                   94, 98, 96, 94, 92,
                   46, None, 97.5, 96, 98,
                   75, 94, None, 100, 100] * 3,
        '스펠점수': [55, 100, 83, 78, 84,
                   50, 68, 90, 88, 90,
                   None, 48, None, None, None,
                   90, 90, 88, 85, 80,
                   22.5, None, 97.5, 82.5, 87.5,
                   55, 82.5, None, 100, 85] * 3,
        '독해점수': [80, 85, 53, 69, 88,
                   56, 58, 86, 84, 86,
                   None, 73, None, None, None,
                   80, 99, 99, 77, 90,
                   99, None, 100, 77.8, 92.5,
                   93.6, 99, None, 88, 96] * 3,
        '문법점수': [75, 88, 92, 65, 78,
                   82, 95, 70, 88, 91,
                   None, 68, None, None, None,
                   85, 90, 78, 82, 88,
                   72, None, 95, 80, 85,
                   78, 92, None, 88, 90] * 3
    }
    return pd.DataFrame(data)

# ============================================
# 공통 유틸리티 함수들
# ============================================

def is_hero(row):
    """영웅 조건: 어휘 정확히 100점 + 스펠 95점 이상 + 독해 80점 이상"""
    if row['출석'] == '결석':
        return False
    if pd.isna(row['어휘점수']) or pd.isna(row['스펠점수']):
        return False
    try:
        vocab_score = float(str(row['어휘점수']).strip())
        spell_score = float(str(row['스펠점수']).strip())
        is_vocab_100 = vocab_score >= 99.9 and vocab_score <= 100.1
        is_spell_95_plus = spell_score >= 94.9
        if pd.notna(row['독해점수']):
            reading_score = float(str(row['독해점수']).strip())
            is_reading_pass = reading_score >= 79.9
            return is_vocab_100 and is_spell_95_plus and is_reading_pass
        else:
            return is_vocab_100 and is_spell_95_plus
    except (ValueError, TypeError):
        return False

def is_villain(row):
    """빌런 조건: 어휘<80 OR 스펠<60 OR (점수 있는 과목 중 2개 이상 미통과)"""
    if row['출석'] == '결석':
        return False
    if pd.isna(row['어휘점수']) and pd.isna(row['스펠점수']) and pd.isna(row['독해점수']):
        return False
    if pd.notna(row['어휘점수']) and row['어휘점수'] < 80:
        return True
    if pd.notna(row['스펠점수']) and row['스펠점수'] < 60:
        return True
    total_subjects = 0
    fail_count = 0
    if pd.notna(row['어휘점수']):
        total_subjects += 1
        if row['어휘점수'] < 94:
            fail_count += 1
    if pd.notna(row['스펠점수']):
        total_subjects += 1
        if row['스펠점수'] < 90:
            fail_count += 1
    if pd.notna(row['독해점수']):
        total_subjects += 1
        if row['독해점수'] < 80:
            fail_count += 1
    return fail_count >= 2

def mask_name(name):
    """이름의 중간 글자를 마스킹"""
    if len(name) <= 1:
        return name
    elif len(name) == 2:
        return name[0] + '□'
    elif len(name) == 3:
        return name[0] + '□' + name[2]
    else:
        return name[0] + '□' * (len(name) - 2) + name[-1]

def classify_student(row, excluded_students=[]):
    """학생 상태 분류: hero, villain, normal, midterm, absent"""
    if row['출석'] == '결석':
        return 'absent'
    elif pd.isna(row['어휘점수']) and pd.isna(row['스펠점수']) and pd.isna(row['독해점수']):
        return 'midterm'
    elif row['이름'] in excluded_students:
        return 'normal'
    elif is_hero(row):
        return 'hero'
    elif is_villain(row):
        return 'villain'
    else:
        return 'normal'

# ============================================
# 전광판 전용 함수들
# ============================================

def get_monthly_hero_counts(df, selected_date, excluded_students=[]):
    try:
        date_obj = pd.to_datetime(selected_date)
        year_month = date_obj.strftime('%Y-%m')
    except:
        return pd.DataFrame()
    df_copy = df.copy()
    df_copy['날짜_obj'] = pd.to_datetime(df_copy['날짜'], errors='coerce')
    monthly_df = df_copy[df_copy['날짜_obj'].dt.strftime('%Y-%m') == year_month].copy()
    if excluded_students:
        monthly_df = monthly_df[~monthly_df['이름'].isin(excluded_students)]
    monthly_df['is_hero'] = monthly_df.apply(is_hero, axis=1)
    hero_counts = monthly_df[monthly_df['is_hero']].groupby('이름').size().reset_index(name='영웅횟수')
    hero_counts = hero_counts.sort_values('영웅횟수', ascending=False)
    return hero_counts

def get_cumulative_hero_counts(df, selected_date, excluded_students=[]):
    try:
        date_obj = pd.to_datetime(selected_date)
        start_obj = pd.to_datetime(CUMULATIVE_START_DATE)
    except:
        return pd.DataFrame()
    df_copy = df.copy()
    df_copy['날짜_obj'] = pd.to_datetime(df_copy['날짜'], errors='coerce')
    cumul_df = df_copy[(df_copy['날짜_obj'] >= start_obj) & (df_copy['날짜_obj'] <= date_obj)].copy()
    if excluded_students:
        cumul_df = cumul_df[~cumul_df['이름'].isin(excluded_students)]
    cumul_df['is_hero'] = cumul_df.apply(is_hero, axis=1)
    hero_counts = cumul_df[cumul_df['is_hero']].groupby('이름').size().reset_index(name='영웅횟수')
    hero_counts = hero_counts.sort_values('영웅횟수', ascending=False)
    return hero_counts

def render_hero_inline(hero_counts, label, top_n=5):
    if len(hero_counts) == 0:
        return f"<span style='color:#888;font-size:12px;'>{label} | 아직 영웅이 없습니다.</span>"
    top = hero_counts.head(top_n).reset_index(drop=True)
    max_count = top['영웅횟수'].max()
    rank_styles = [
        {'icon': 'S', 'bar': 'linear-gradient(90deg,#FFD700,#FF6B00)', 'badge': 'linear-gradient(135deg,#FFD700,#FF6B00)',
         'text': '#FF6B00', 'glow': '0 0 6px rgba(255,215,0,0.6)', 'name_wt': '900', 'name_sz': '14px', 'count_sz': '14px'},
        {'icon': 'A', 'bar': 'linear-gradient(90deg,#C0C0C0,#8E8E8E)', 'badge': 'linear-gradient(135deg,#C0C0C0,#8E8E8E)',
         'text': '#666', 'glow': 'none', 'name_wt': '700', 'name_sz': '12px', 'count_sz': '12px'},
        {'icon': 'B', 'bar': 'linear-gradient(90deg,#CD7F32,#A0522D)', 'badge': 'linear-gradient(135deg,#CD7F32,#A0522D)',
         'text': '#8B4513', 'glow': 'none', 'name_wt': '700', 'name_sz': '12px', 'count_sz': '12px'},
        {'icon': 'C', 'bar': 'linear-gradient(90deg,#2E8B57,#1B5E37)', 'badge': '#2E8B57',
         'text': '#2E8B57', 'glow': 'none', 'name_wt': '600', 'name_sz': '11px', 'count_sz': '11px'},
        {'icon': 'D', 'bar': 'linear-gradient(90deg,#708090,#4A5568)', 'badge': '#708090',
         'text': '#708090', 'glow': 'none', 'name_wt': '600', 'name_sz': '11px', 'count_sz': '11px'},
    ]
    items_html = ""
    rank_idx = 0
    prev_count = None
    for idx, row_data in top.iterrows():
        masked = mask_name(row_data['이름'])
        count = int(row_data['영웅횟수'])
        pct = (count / max_count) * 100 if max_count > 0 else 0
        if prev_count is not None and count < prev_count:
            rank_idx = idx
        prev_count = count
        s = rank_styles[min(rank_idx, 4)]
        border = f"2px solid #FFD700; box-shadow:{s['glow']}" if rank_idx == 0 else "1px solid rgba(0,0,0,0.1)"
        bar_h = "10px" if rank_idx == 0 else "7px"
        items_html += f"""<div style='display:inline-flex;flex-direction:column;min-width:120px;max-width:180px;
            flex:1;background:#fff;border:{border};border-radius:6px;padding:4px 8px;'>
            <div style='display:flex;align-items:center;gap:4px;margin-bottom:2px;'>
                <span style='background:{s["badge"]};color:#fff;font-weight:800;font-size:10px;
                    padding:1px 5px;border-radius:3px;line-height:1.2;'>{s["icon"]}</span>
                <span style='font-size:{s["name_sz"]};font-weight:{s["name_wt"]};color:#222;
                    white-space:nowrap;overflow:hidden;text-overflow:ellipsis;'>{masked}</span>
                <span style='font-size:{s["count_sz"]};font-weight:800;color:{s["text"]};
                    margin-left:auto;white-space:nowrap;'>{count}회</span>
            </div>
            <div style='background:rgba(0,0,0,0.06);border-radius:5px;height:{bar_h};overflow:hidden;'>
                <div style='background:{s["bar"]};width:{pct}%;height:100%;border-radius:5px;'></div>
            </div>
        </div>"""
    html = f"""<div style='display:flex;align-items:center;gap:6px;flex-wrap:nowrap;'>
        <span style='font-weight:800;font-size:12px;color:#333;white-space:nowrap;min-width:fit-content;'>{label}</span>
        <span style='color:#ccc;'>|</span>
        {items_html}
    </div>"""
    return html

def add_hero_effect(fig, row, x_base):
    masked_name = mask_name(row['이름'])
    vocab_score = float(row['어휘점수'])
    spell_score = float(row['스펠점수'])
    fig.add_trace(go.Bar(
        x=[x_base], y=[vocab_score], width=0.7,
        marker=dict(color='#00C851', line=dict(color='gold', width=4)),
        text=str(int(vocab_score)), textposition='inside',
        textfont=dict(size=12, color='white', family='Arial Black'),
        showlegend=False,
        hovertemplate=f"{masked_name} - 어휘: {vocab_score}점<extra></extra>"
    ))
    fig.add_trace(go.Bar(
        x=[x_base + 0.8], y=[spell_score], width=0.7,
        marker=dict(color='#FFD700', line=dict(color='#00C851', width=4)),
        text=str(int(spell_score)), textposition='inside',
        textfont=dict(size=12, color='white', family='Arial Black'),
        showlegend=False,
        hovertemplate=f"{masked_name} - 스펠: {spell_score}점<extra></extra>"
    ))
    fig.add_annotation(
        text="<b>영웅</b>", x=x_base + 1.2, y=108, showarrow=False,
        font=dict(size=14, color='#00C851', family='Arial Black'),
        bgcolor='#FFD700', bordercolor='#00C851', borderwidth=3
    )
    if pd.notna(row['독해점수']):
        color = '#00C851' if row['독해점수'] >= 80 else '#FF4444'
        fig.add_trace(go.Bar(
            x=[x_base + 1.6], y=[row['독해점수']], width=0.7,
            marker=dict(color=color, line=dict(color='gold', width=3)),
            text=str(int(row['독해점수'])), textposition='auto',
            textfont=dict(size=10, color='white'),
            showlegend=False,
            hovertemplate=f"{masked_name} - 독해: {row['독해점수']}점<extra></extra>"
        ))
    if pd.notna(row.get('문법점수')):
        fig.add_trace(go.Bar(
            x=[x_base + 2.4], y=[row['문법점수']], width=0.7,
            marker=dict(color='#3498db', line=dict(color='gold', width=3)),
            text=str(int(row['문법점수'])), textposition='auto',
            textfont=dict(size=10, color='white'),
            showlegend=False,
            hovertemplate=f"{masked_name} - 문법: {row['문법점수']}점<extra></extra>"
        ))

def add_villain_effect(fig, row, x_base):
    masked_name = mask_name(row['이름'])
    subjects_with_cut = [
        ('어휘점수', 94, x_base),
        ('스펠점수', 90, x_base + 0.8),
        ('독해점수', 80, x_base + 1.6)
    ]
    for subject, threshold, x_pos in subjects_with_cut:
        if pd.notna(row[subject]):
            score = row[subject]
            color = '#00C851' if score >= threshold else '#FF4444'
            fig.add_trace(go.Bar(
                x=[x_pos], y=[score], width=0.7,
                marker=dict(color=color, line=dict(color='#8e44ad', width=3)),
                text=str(int(score)), textposition='auto',
                textfont=dict(size=10, color='white', family='Arial Black'),
                showlegend=False,
                hovertemplate=f"{masked_name} - {subject[:-2]}: {score}점<extra></extra>"
            ))
    if pd.notna(row.get('문법점수')):
        fig.add_trace(go.Bar(
            x=[x_base + 2.4], y=[row['문법점수']], width=0.7,
            marker=dict(color='#3498db', line=dict(color='#8e44ad', width=3)),
            text=str(int(row['문법점수'])), textposition='auto',
            textfont=dict(size=10, color='white'),
            showlegend=False,
            hovertemplate=f"{masked_name} - 문법: {row['문법점수']}점<extra></extra>"
        ))
    fig.add_annotation(
        text="<b>빌런</b>", x=x_base + 1.2, y=108, showarrow=False,
        font=dict(size=14, color='white', family='Arial Black'),
        bgcolor='#8e44ad', bordercolor='#3c096c', borderwidth=2
    )

def add_normal_bars(fig, row, x_base):
    masked_name = mask_name(row['이름'])
    subjects_with_cut = [
        ('어휘점수', 94, x_base),
        ('스펠점수', 90, x_base + 0.8),
        ('독해점수', 80, x_base + 1.6)
    ]
    for subject, threshold, x_pos in subjects_with_cut:
        if pd.notna(row[subject]):
            score = row[subject]
            color = '#00C851' if score >= threshold else '#FF4444'
            fig.add_trace(go.Bar(
                x=[x_pos], y=[score], width=0.7,
                marker_color=color,
                text=str(int(score)), textposition='auto',
                textfont=dict(size=9, color='white'),
                showlegend=False,
                hovertemplate=f"{masked_name} - {subject[:-2]}: {score}점<extra></extra>"
            ))
    if pd.notna(row.get('문법점수')):
        fig.add_trace(go.Bar(
            x=[x_base + 2.4], y=[row['문법점수']], width=0.7,
            marker_color='#3498db',
            text=str(int(row['문법점수'])), textposition='auto',
            textfont=dict(size=9, color='white'),
            showlegend=False,
            hovertemplate=f"{masked_name} - 문법: {row['문법점수']}점<extra></extra>"
        ))

def add_midterm_section(fig, midterm_df, start_x):
    if len(midterm_df) == 0:
        return
    fig.add_vrect(
        x0=start_x - 0.5, x1=start_x + len(midterm_df) * STUDENT_WIDTH,
        fillcolor="rgba(255, 235, 150, 0.1)", layer="below", line_width=0
    )
    for idx, (_, row) in enumerate(midterm_df.iterrows()):
        x_pos = start_x + idx * STUDENT_WIDTH
        masked_name = mask_name(row['이름'])
        for i in range(4):
            fig.add_trace(go.Bar(
                x=[x_pos + i * 0.8], y=[40], width=0.7,
                marker=dict(color='rgba(255, 200, 100, 0.3)',
                           pattern=dict(shape='/', size=8, solidity=0.2)),
                text='내신', textposition='inside', textfont=dict(size=9),
                showlegend=False,
                hovertemplate=f"{masked_name} - 내신기간<extra></extra>"
            ))

def create_dashboard(selected_date, excluded_students=[]):
    df = load_data()
    today_df = df[df['날짜'] == selected_date].copy()
    if excluded_students:
        today_df = today_df[~today_df['이름'].isin(excluded_students)]
    if len(today_df) == 0:
        st.warning(f"{selected_date}에 해당하는 데이터가 없습니다.")
        return None, None
    today_df['status'] = today_df.apply(classify_student, axis=1)
    class_order = {'초등': 1, '중등': 2, '수능': 3, '정시': 4}
    
    hero_df = today_df[today_df['status'] == 'hero'].copy()
    hero_df['class_order'] = hero_df['반'].map(class_order)
    hero_df = hero_df.sort_values(['class_order', '이름'])
    villain_df = today_df[today_df['status'] == 'villain'].copy()
    villain_df['class_order'] = villain_df['반'].map(class_order)
    villain_df = villain_df.sort_values(['class_order', '이름'])
    normal_df = today_df[today_df['status'] == 'normal'].copy()
    normal_df['class_order'] = normal_df['반'].map(class_order)
    normal_df = normal_df.sort_values(['class_order', '이름'])
    midterm_df = today_df[today_df['status'] == 'midterm'].copy()
    midterm_df['class_order'] = midterm_df['반'].map(class_order)
    midterm_df = midterm_df.sort_values(['class_order', '이름'])
    absent_df = today_df[today_df['status'] == 'absent'].copy()
    absent_df['class_order'] = absent_df['반'].map(class_order)
    absent_df = absent_df.sort_values(['class_order', '이름'])
    
    fig = go.Figure()
    
    for idx, (_, row) in enumerate(hero_df.iterrows()):
        x_base = idx * STUDENT_WIDTH
        fig.add_shape(type="rect", x0=x_base - 0.4, x1=x_base + 2.8, y0=0, y1=105,
            line=dict(color="#00C851", width=3), fillcolor="rgba(255,215,0,0.1)", layer="below")
        add_hero_effect(fig, row, x_base)
    
    normal_start = len(hero_df) * STUDENT_WIDTH + 1
    for idx, (_, row) in enumerate(normal_df.iterrows()):
        x_base = normal_start + idx * STUDENT_WIDTH
        fig.add_shape(type="rect", x0=x_base - 0.4, x1=x_base + 2.8, y0=0, y1=105,
            line=dict(color="rgba(100, 100, 100, 0.3)", width=2), fillcolor="rgba(0,0,0,0)", layer="below")
        add_normal_bars(fig, row, x_base)
    
    villain_start = normal_start + len(normal_df) * STUDENT_WIDTH + 1
    for idx, (_, row) in enumerate(villain_df.iterrows()):
        x_base = villain_start + idx * STUDENT_WIDTH
        fig.add_shape(type="rect", x0=x_base - 0.4, x1=x_base + 2.8, y0=0, y1=105,
            line=dict(color="#8e44ad", width=3), fillcolor="rgba(142,68,173,0.1)", layer="below")
        add_villain_effect(fig, row, x_base)
    
    midterm_start = villain_start + len(villain_df) * STUDENT_WIDTH + 1
    add_midterm_section(fig, midterm_df, midterm_start)
    
    absent_start = midterm_start + len(midterm_df) * STUDENT_WIDTH + 1
    if len(absent_df) > 0:
        fig.add_vrect(x0=absent_start - 0.5, x1=absent_start + len(absent_df) * STUDENT_WIDTH,
            fillcolor="rgba(128, 128, 128, 0.1)", layer="below", line_width=0)
    
    fig.add_hline(y=94, line_dash="dash", line_color="rgba(255,0,0,0.3)",
                  annotation_text="어휘 기준 94점", annotation_position="right")
    fig.add_hline(y=80, line_dash="dash", line_color="rgba(0,0,255,0.3)",
                  annotation_text="스펠/독해 기준 80점", annotation_position="right")
    
    all_names = []
    tick_positions = []
    for idx, (_, row) in enumerate(hero_df.iterrows()):
        name = mask_name(row['이름'])
        if row['출석'] == '지각': name += " ⏰"
        all_names.append(name)
        tick_positions.append(idx * STUDENT_WIDTH + 1.2)
    for idx, (_, row) in enumerate(normal_df.iterrows()):
        name = mask_name(row['이름'])
        if row['출석'] == '지각': name += " ⏰"
        all_names.append(name)
        tick_positions.append(normal_start + idx * STUDENT_WIDTH + 1.2)
    for idx, (_, row) in enumerate(villain_df.iterrows()):
        name = mask_name(row['이름'])
        if row['출석'] == '지각': name += " ⏰"
        all_names.append(name)
        tick_positions.append(villain_start + idx * STUDENT_WIDTH + 1.2)
    for idx, (_, row) in enumerate(midterm_df.iterrows()):
        name = mask_name(row['이름'])
        if row['출석'] == '지각': name += " ⏰"
        all_names.append(name)
        tick_positions.append(midterm_start + idx * STUDENT_WIDTH + 1.2)
    for idx, (_, row) in enumerate(absent_df.iterrows()):
        all_names.append(mask_name(row['이름']))
        tick_positions.append(absent_start + idx * STUDENT_WIDTH + 1.2)
    
    fig.update_layout(
        title=None, height=900, margin=dict(l=60, r=60, t=10, b=150),
        xaxis=dict(ticktext=all_names, tickvals=tick_positions, tickfont=dict(size=11), tickangle=0),
        yaxis=dict(range=[0, 115], title=dict(text="점수", font=dict(size=14)), gridcolor='rgba(128,128,128,0.2)'),
        plot_bgcolor='white', paper_bgcolor='#f5f5f5',
        bargap=0.1, bargroupgap=0.05, showlegend=False, hovermode='x'
    )
    
    if len(normal_df) > 0:
        fig.add_vline(x=normal_start - 0.5, line_dash="dot", line_color="#00C851", opacity=0.5)
    if len(villain_df) > 0:
        fig.add_vline(x=villain_start - 0.5, line_dash="dot", line_color="purple", opacity=0.5)
    fig.add_vline(x=midterm_start - 0.5, line_dash="dot", line_color="gray", opacity=0.3)
    if len(absent_df) > 0:
        fig.add_vline(x=absent_start - 0.5, line_dash="dot", line_color="gray", opacity=0.3)
    
    pass_count = sum((normal_df['어휘점수'] >= 94) & (normal_df['스펠점수'] >= 90) & (normal_df['독해점수'] >= 80))
    late_count = len(today_df[today_df['출석'] == '지각'])
    excluded_count = len(excluded_students)
    excluded_text = f" | <span style='color: gray'>제외: {excluded_count}명</span>" if excluded_count > 0 else ""
    summary_text = f"""
    <div style='text-align: center; padding: 10px; background: white; border-radius: 5px;'>
    <b>영웅: {len(hero_df)}명 | 빌런: {len(villain_df)}명 | 정상응시: {len(normal_df)}명 | 내신: {len(midterm_df)}명 | 결석: {len(absent_df)}명 | 지각: {late_count}명 ⏰{excluded_text}</b><br>
    <span style='color: green'>통과: {pass_count}명</span> | 
    <span style='color: red'>재시험: {len(normal_df) - pass_count}명</span> |
    <span style='color: #3498db'>문법: 커트없음</span>
    </div>
    """
    return fig, summary_text


# ============================================
# ★★★ 개인 리포트 전용 함수들 ★★★
# ============================================

def render_report_header(name, ban, month_str, stats):
    """개인 리포트 상단 헤더"""
    hero_pct = stats.get('hero_pct', 0)
    total_days = stats.get('total_days', 0)
    attend_days = stats.get('attend_days', 0)
    hero_days = stats.get('hero_days', 0)
    absent_days = stats.get('absent_days', 0)
    late_days = stats.get('late_days', 0)

    if hero_pct >= 80:
        grade, grade_color, grade_bg = 'S', '#FFD700', 'linear-gradient(135deg,#FFD700,#FF6B00)'
    elif hero_pct >= 60:
        grade, grade_color, grade_bg = 'A', '#C0C0C0', 'linear-gradient(135deg,#C0C0C0,#8E8E8E)'
    elif hero_pct >= 40:
        grade, grade_color, grade_bg = 'B', '#CD7F32', 'linear-gradient(135deg,#CD7F32,#A0522D)'
    elif hero_pct >= 20:
        grade, grade_color, grade_bg = 'C', '#2E8B57', '#2E8B57'
    else:
        grade, grade_color, grade_bg = 'D', '#708090', '#708090'

    return f"""
    <div style="display:flex;align-items:center;gap:20px;padding:16px 24px;
        background:linear-gradient(135deg,#1a2332 0%,#0f1923 100%);
        border:1px solid rgba(255,255,255,0.1);border-radius:16px;margin-bottom:12px;">
        <div style="display:flex;align-items:center;justify-content:center;width:64px;height:64px;
            background:{grade_bg};border-radius:14px;flex-shrink:0;">
            <span style="font-size:32px;font-weight:900;color:#fff;text-shadow:0 2px 4px rgba(0,0,0,0.3);">{grade}</span>
        </div>
        <div style="flex:1;">
            <div style="font-size:24px;font-weight:800;color:#e8e8e8;letter-spacing:-0.5px;">
                {name}
                <span style="font-size:13px;font-weight:500;color:#888;margin-left:8px;
                    padding:3px 10px;border:1px solid #444;border-radius:20px;">{ban}</span>
            </div>
            <div style="font-size:13px;color:#888;margin-top:4px;">
                {month_str} 리포트 &nbsp;|&nbsp;
                출석 {attend_days}/{total_days}일 &nbsp;|&nbsp;
                결석 {absent_days}일 &nbsp;|&nbsp;
                지각 {late_days}일
            </div>
        </div>
        <div style="text-align:center;padding:8px 20px;background:rgba(255,255,255,0.03);
            border:1px solid rgba(255,255,255,0.08);border-radius:12px;">
            <div style="font-size:11px;color:#888;text-transform:uppercase;letter-spacing:1px;">영웅 달성률</div>
            <div style="font-size:30px;font-weight:900;color:{grade_color};margin-top:2px;">{hero_pct:.0f}%</div>
            <div style="font-size:11px;color:#666;">{hero_days}회 / {attend_days}일</div>
        </div>
    </div>"""

def render_summary_cards(attend_df):
    """과목별 요약 카드"""
    subjects = [
        ('어휘점수', 94, '어휘', '#4ade80'),
        ('스펠점수', 90, '문맥', '#facc15'),
        ('독해점수', 80, '독해', '#60a5fa'),
        ('문법점수', None, '문법', '#c084fc'),
    ]
    cards_html = ""
    for col, cutoff, label, color in subjects:
        valid = attend_df[col].dropna()
        if len(valid) == 0:
            cards_html += f"""<div style="flex:1;min-width:140px;background:#1a2332;border:1px solid rgba(255,255,255,0.06);
                border-radius:12px;padding:14px;text-align:center;">
                <div style="font-size:12px;color:#666;">{label}</div>
                <div style="font-size:24px;font-weight:800;color:#444;margin:6px 0;">-</div>
            </div>"""
            continue
        avg = valid.mean()
        high = valid.max()
        low = valid.min()
        pass_rate = (valid >= cutoff).sum() / len(valid) * 100 if cutoff else None

        trend_icon = ""
        if len(valid) >= 3:
            diff = valid.iloc[-3:].mean() - valid.iloc[:3].mean()
            if diff > 2: trend_icon = '<span style="color:#4ade80;font-size:14px;">&#9650;</span>'
            elif diff < -2: trend_icon = '<span style="color:#ef4444;font-size:14px;">&#9660;</span>'
            else: trend_icon = '<span style="color:#888;font-size:12px;">&#9644;</span>'

        pass_html = ""
        if pass_rate is not None:
            pbar_color = color if pass_rate >= 70 else '#ef4444'
            pass_html = f"""<div style="margin-top:8px;">
                <div style="font-size:10px;color:#666;">통과율 {pass_rate:.0f}%</div>
                <div style="background:rgba(255,255,255,0.06);border-radius:4px;height:5px;margin-top:3px;">
                    <div style="background:{pbar_color};width:{pass_rate}%;height:100%;border-radius:4px;"></div>
                </div></div>"""

        cards_html += f"""<div style="flex:1;min-width:140px;background:linear-gradient(135deg,#1a2332,#0f1923);
            border:1px solid rgba(255,255,255,0.06);border-radius:12px;padding:14px;">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <span style="font-size:12px;color:{color};font-weight:700;">{label}</span>{trend_icon}
            </div>
            <div style="font-size:28px;font-weight:900;color:#e0e0e0;margin:6px 0;">{avg:.1f}</div>
            <div style="display:flex;justify-content:space-between;font-size:10px;color:#666;">
                <span>최고 {high:.0f}</span><span>최저 {low:.0f}</span>
            </div>{pass_html}</div>"""

    return f"""<div style="display:flex;gap:10px;flex-wrap:wrap;">{cards_html}</div>"""

def create_trend_chart(attend_df):
    """과목별 점수 추이 차트"""
    fig = make_subplots(rows=2, cols=2,
        subplot_titles=('어휘 (커트 94)', '문맥 (커트 90)', '독해 (커트 80)', '문법 (참고)'),
        vertical_spacing=0.14, horizontal_spacing=0.08)

    subjects = [
        ('어휘점수', 94, 1, 1, '#4ade80'),
        ('스펠점수', 90, 1, 2, '#facc15'),
        ('독해점수', 80, 2, 1, '#60a5fa'),
        ('문법점수', None, 2, 2, '#c084fc'),
    ]
    for col_name, cutoff, r, c, color_pass in subjects:
        sub = attend_df.dropna(subset=[col_name]).copy()
        if len(sub) == 0:
            continue
        dates = sub['날짜'].apply(lambda x: x[5:])  # MM-DD
        scores = sub[col_name]
        colors = [color_pass if (cutoff is None or s >= cutoff) else '#ef4444' for s in scores]

        fig.add_trace(go.Bar(
            x=dates, y=scores, marker_color=colors,
            text=[f"{int(s)}" for s in scores], textposition='outside',
            textfont=dict(size=9, color='#aaa'), showlegend=False,
            hovertemplate='%{x}<br>%{y}점<extra></extra>'
        ), row=r, col=c)

        if len(sub) >= 3:
            z = np.polyfit(range(len(scores)), scores, 1)
            p = np.poly1d(z)
            trend_y = [p(i) for i in range(len(scores))]
            fig.add_trace(go.Scatter(
                x=dates, y=trend_y, mode='lines',
                line=dict(color=color_pass if z[0] >= 0 else '#ef4444', width=2, dash='dot'),
                showlegend=False, hoverinfo='skip'
            ), row=r, col=c)

        if cutoff is not None:
            fig.add_hline(y=cutoff, line_dash="dash", line_color="rgba(255,100,100,0.4)", row=r, col=c)

    fig.update_layout(
        height=480, margin=dict(l=40, r=20, t=40, b=40),
        plot_bgcolor='#0f1923', paper_bgcolor='#f5f5f5',
        font=dict(color='#aaa', size=11), bargap=0.3,
    )
    fig.update_xaxes(showgrid=False, tickfont=dict(size=8, color='#666'), tickangle=-45)
    fig.update_yaxes(range=[0, 110], gridcolor='rgba(255,255,255,0.06)', tickfont=dict(size=9, color='#666'))
    for ann in fig['layout']['annotations']:
        ann['font'] = dict(size=13, color='#555')
    return fig

def render_daily_table(student_df):
    """일별 상세 테이블"""
    rows_html = ""
    for _, row in student_df.iterrows():
        date_short = row['날짜'][5:]
        if row['출석'] == '결석':
            rows_html += f"""<tr style="background:rgba(0,0,0,0.02);">
                <td style="padding:6px 10px;color:#999;font-weight:600;">{date_short}</td>
                <td colspan="4" style="text-align:center;color:#aaa;font-style:italic;">결석</td></tr>"""
            continue
        hero = is_hero(row)
        att = ' <span style="color:#e67e22;font-size:10px;">지각</span>' if row['출석'] == '지각' else ''
        hero_badge = ' <span style="background:linear-gradient(135deg,#FFD700,#FF6B00);color:#fff;font-size:9px;font-weight:800;padding:2px 6px;border-radius:4px;">HERO</span>' if hero else ''
        row_bg = 'rgba(255,215,0,0.06)' if hero else 'white'

        def cell(val, cutoff=None):
            if pd.isna(val): return '<td style="padding:6px 10px;color:#ccc;text-align:center;">-</td>'
            v = float(val)
            if cutoff is None: color = '#8e44ad'
            elif v >= cutoff: color = '#27ae60'
            else: color = '#e74c3c'
            return f'<td style="padding:6px 10px;color:{color};text-align:center;font-weight:700;">{v:.0f}</td>'

        rows_html += f"""<tr style="background:{row_bg};border-bottom:1px solid #eee;">
            <td style="padding:6px 10px;color:#333;font-weight:600;">{date_short}{att}{hero_badge}</td>
            {cell(row['어휘점수'], 94)}{cell(row['스펠점수'], 90)}{cell(row['독해점수'], 80)}{cell(row.get('문법점수'))}</tr>"""

    return f"""<div style="border:1px solid #ddd;border-radius:12px;overflow:hidden;background:white;">
        <table style="width:100%;border-collapse:collapse;font-size:13px;">
            <thead><tr style="background:#f0f0f0;">
                <th style="padding:8px 10px;text-align:left;color:#555;">날짜</th>
                <th style="padding:8px 10px;text-align:center;color:#27ae60;font-weight:700;">어휘<br><span style="font-size:10px;color:#999;">94</span></th>
                <th style="padding:8px 10px;text-align:center;color:#e67e22;font-weight:700;">문맥<br><span style="font-size:10px;color:#999;">90</span></th>
                <th style="padding:8px 10px;text-align:center;color:#2980b9;font-weight:700;">독해<br><span style="font-size:10px;color:#999;">80</span></th>
                <th style="padding:8px 10px;text-align:center;color:#8e44ad;font-weight:700;">문법<br><span style="font-size:10px;color:#999;">-</span></th>
            </tr></thead><tbody>{rows_html}</tbody></table></div>"""


# ============================================
# ★★★ 개인 리포트 페이지 ★★★
# ============================================
def page_student_report():
    """개인 리포트 탭"""
    df = load_data()
    df['날짜'] = df['날짜'].astype(str)
    df = df[(df['날짜'] != 'nan') & (df['날짜'] != '')]
    df['날짜_obj'] = pd.to_datetime(df['날짜'], errors='coerce')

    all_students = sorted(df['이름'].unique().tolist())
    student_classes = df.drop_duplicates('이름').set_index('이름')['반'].to_dict()

    col1, col2 = st.columns([1, 1])
    with col1:
        selected_student = st.selectbox("학생 선택", all_students, index=0)
    with col2:
        months = df['날짜_obj'].dropna().dt.to_period('M').unique().sort_values(ascending=False)
        month_options = [str(m) for m in months]
        selected_month = st.selectbox("월 선택", month_options, index=0)

    student_df = df[df['이름'] == selected_student].copy()
    student_df = student_df[student_df['날짜_obj'].dt.to_period('M').astype(str) == selected_month]
    student_df = student_df.sort_values('날짜').reset_index(drop=True)

    if len(student_df) == 0:
        st.warning("해당 월에 데이터가 없습니다.")
        return

    ban = student_classes.get(selected_student, '?')
    total_days = len(student_df)
    absent_days = int((student_df['출석'] == '결석').sum())
    late_days = int((student_df['출석'] == '지각').sum())
    attend_days = total_days - absent_days
    student_df['is_hero'] = student_df.apply(is_hero, axis=1)
    hero_days = int(student_df['is_hero'].sum())
    hero_pct = (hero_days / attend_days * 100) if attend_days > 0 else 0

    stats = {'total_days': total_days, 'attend_days': attend_days,
             'absent_days': absent_days, 'late_days': late_days,
             'hero_days': hero_days, 'hero_pct': hero_pct}

    # 헤더
    header_html = render_report_header(selected_student, ban, selected_month, stats)
    components.html(
        f"<html><body style='margin:0;padding:0;font-family:sans-serif;background:#f5f5f5;'>{header_html}</body></html>",
        height=110, scrolling=False)

    # 과목별 요약 카드
    attend_df = student_df[student_df['출석'] != '결석']
    cards_html = render_summary_cards(attend_df)
    components.html(
        f"<html><body style='margin:0;padding:0;font-family:sans-serif;background:#f5f5f5;'>{cards_html}</body></html>",
        height=130, scrolling=False)

    # 추이 차트
    st.plotly_chart(create_trend_chart(attend_df), use_container_width=True, config={'displayModeBar': False})

    # 일별 상세 테이블
    st.markdown("**일별 상세**")
    table_html = render_daily_table(student_df)
    table_height = min(60 + len(student_df) * 34, 800)
    components.html(
        f"<html><body style='margin:0;padding:0;font-family:sans-serif;background:#f5f5f5;'>{table_html}</body></html>",
        height=table_height, scrolling=True)


# ============================================
# ★★★ 전광판 페이지 (기존 코드) ★★★
# ============================================
def page_scoreboard():
    """전광판 탭 - 기존 코드 그대로"""
    df = load_data()

    if '날짜' in df.columns:
        df['날짜'] = df['날짜'].astype(str)
        df = df[df['날짜'] != 'nan']
        df = df[df['날짜'] != '']
        available_dates = sorted(df['날짜'].unique())

        if len(available_dates) == 0:
            st.error("날짜 데이터가 없습니다.")
            return

        date_objects = []
        date_mapping = {}
        for d in available_dates:
            date_formats = ['%Y-%m-%d', '%Y. %m. %d', '%Y.%m.%d', '%Y/%m/%d']
            for fmt in date_formats:
                try:
                    date_obj = datetime.strptime(d.strip(), fmt).date()
                    date_objects.append(date_obj)
                    date_mapping[date_obj] = d
                    break
                except:
                    continue

        if date_objects:
            today = datetime.now().date()
            if today in date_objects: default_date = today
            else:
                past_dates = [d for d in date_objects if d <= today]
                default_date = max(past_dates) if past_dates else date_objects[-1]

            title_area = st.container()
            hero_area = st.container()
            graph_area = st.container()
            controls_area = st.container()
            summary_area = st.container()
            legend_area = st.container()
            debug_area = st.container()
            refresh_area = st.container()

            with controls_area:
                ctrl1, ctrl2 = st.columns([1, 2])
                with ctrl1:
                    selected_date = st.date_input("날짜 선택", value=default_date,
                        min_value=date_objects[0], max_value=date_objects[-1], format="YYYY-MM-DD")
                selected_date_str = date_mapping.get(selected_date, available_dates[-1])
                today_students = df[df['날짜'] == selected_date_str]['이름'].unique().tolist()
                today_students.sort()
                with ctrl2:
                    excluded_students = st.multiselect("제외할 학생 선택",
                        options=today_students, default=[],
                        help="선택한 학생은 영웅/빌런 집계 및 그래프에서 제외됩니다")
        else:
            selected_date_str = available_dates[-1]
            excluded_students = []
    else:
        st.error("'날짜' 컬럼이 없습니다.")
        return

    with title_area:
        st.markdown(f"<h1 style='margin:0 0 5px 0;font-size:20px;'>{selected_date_str} | 아자영어 통과현황 (커트 : 뜻 94, 문맥 90, 독해 80, 문법 없음)</h1>", unsafe_allow_html=True)

    try: selected_month_str = pd.to_datetime(selected_date_str).strftime('%m월')
    except: selected_month_str = "이번달"
    try: cumul_start_display = pd.to_datetime(CUMULATIVE_START_DATE).strftime('%Y.%m')
    except: cumul_start_display = "2024.11"

    monthly_hero = get_monthly_hero_counts(df, selected_date_str, excluded_students)
    cumul_hero = get_cumulative_hero_counts(df, selected_date_str, excluded_students)
    monthly_html = render_hero_inline(monthly_hero, f"{selected_month_str} 영웅", top_n=5)
    cumul_html = render_hero_inline(cumul_hero, f"누적({cumul_start_display}~)", top_n=5)

    full_hero_html = f"""<div style='display:flex;flex-direction:column;gap:4px;padding:6px 10px;
        background:#fff;border-radius:8px;border:1px solid #e0e0e0;margin-bottom:5px;'>
        {monthly_html}
        <div style='border-top:1px solid #eee;margin:2px 0;'></div>
        {cumul_html}
    </div>"""

    with hero_area:
        components.html(f"<html><body style='margin:0;padding:0;font-family:sans-serif;background:#f5f5f5;'>{full_hero_html}</body></html>", height=110, scrolling=False)

    fig, summary = create_dashboard(selected_date_str, excluded_students)

    with graph_area:
        if fig is not None:
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    with summary_area:
        if fig is not None:
            st.markdown(summary, unsafe_allow_html=True)
            if excluded_students:
                st.info(f"제외된 학생: {', '.join(excluded_students)}")

    with legend_area:
        st.markdown("""
        <div style='text-align: center; padding: 10px; margin-top: 10px; background: #f0f0f0; border-radius: 5px;'>
        <b>막대 색상:</b> 
        <span style='color: #00C851;'>■ 통과</span> | 
        <span style='color: #FF4444;'>■ 미통과</span> | 
        <span style='color: #3498db;'>■ 문법 (커트없음)</span>
        </div>
        """, unsafe_allow_html=True)

    with debug_area:
        with st.expander("영웅/빌런 판정 상세 정보 (디버깅)"):
            st.info("지각한 학생도 시험을 봤기 때문에 영웅/빌런 판정에 포함됩니다. 문법점수는 커트가 없어 영웅/빌런 판정에 영향을 주지 않습니다.")
            today_df = df[df['날짜'] == selected_date_str].copy()
            if excluded_students:
                st.warning(f"다음 학생들이 제외되었습니다: {', '.join(excluded_students)}")
                today_df = today_df[~today_df['이름'].isin(excluded_students)]
            today_df['is_hero'] = today_df.apply(is_hero, axis=1)
            today_df['is_villain'] = today_df.apply(is_villain, axis=1)

            st.markdown("### 전체 학생 영웅 판정 현황")
            all_students = today_df[(today_df['출석'] != '결석') & (pd.notna(today_df['어휘점수'])) & (pd.notna(today_df['스펠점수']))].copy()
            if len(all_students) > 0:
                for _, row in all_students.iterrows():
                    try:
                        vocab_val = float(str(row['어휘점수']).strip())
                        spell_val = float(str(row['스펠점수']).strip())
                        is_hero_status = "영웅" if row['is_hero'] else "일반"
                        attendance_mark = " (지각)" if row['출석'] == '지각' else ""
                        vocab_ok = "O" if (vocab_val >= 99.9 and vocab_val <= 100.1) else "X"
                        spell_ok = "O" if spell_val >= 94.9 else "X"
                        grammar_text = ""
                        if pd.notna(row.get('문법점수')):
                            grammar_text = f", 문법 {row['문법점수']}점"
                        st.markdown(f"**{row['이름']}**{attendance_mark} [{is_hero_status}]: {vocab_ok} 어휘 {vocab_val}점, {spell_ok} 스펠 {spell_val}점{grammar_text}")
                    except:
                        st.markdown(f"**{row['이름']}**: 데이터 변환 오류")

            st.markdown("---")
            st.markdown("### 영웅으로 판정된 학생들")
            heroes = today_df[today_df['is_hero'] == True]
            if len(heroes) > 0:
                for _, row in heroes.iterrows():
                    vocab_val = float(str(row['어휘점수']).strip())
                    spell_val = float(str(row['스펠점수']).strip())
                    attendance_mark = " (지각)" if row['출석'] == '지각' else ""
                    st.markdown(f"**{row['이름']}**{attendance_mark}: O 어휘 {vocab_val}점, O 스펠 {spell_val}점")
            else:
                st.info("영웅 판정된 학생이 없습니다.")

            st.markdown("### 빌런으로 판정된 학생들")
            villains = today_df[today_df['is_villain'] == True]
            if len(villains) > 0:
                for _, row in villains.iterrows():
                    reasons = []
                    attendance_mark = " (지각)" if row['출석'] == '지각' else ""
                    if pd.notna(row['어휘점수']) and row['어휘점수'] < 80:
                        reasons.append(f"어휘 {row['어휘점수']}점 (80점 미만)")
                    if pd.notna(row['스펠점수']) and row['스펠점수'] < 60:
                        reasons.append(f"스펠 {row['스펠점수']}점 (60점 미만)")
                    total_subjects = 0
                    fail_count = 0
                    fail_details = []
                    if pd.notna(row['어휘점수']):
                        total_subjects += 1
                        if row['어휘점수'] < 94: fail_count += 1; fail_details.append(f"어휘 {row['어휘점수']}점 < 94점")
                    if pd.notna(row['스펠점수']):
                        total_subjects += 1
                        if row['스펠점수'] < 90: fail_count += 1; fail_details.append(f"스펠 {row['스펠점수']}점 < 90점")
                    if pd.notna(row['독해점수']):
                        total_subjects += 1
                        if row['독해점수'] < 80: fail_count += 1; fail_details.append(f"독해 {row['독해점수']}점 < 80점")
                    if fail_count >= 2:
                        reasons.append(f"{total_subjects}과목 중 {fail_count}과목 미통과 ({', '.join(fail_details)})")
                    st.markdown(f"**{row['이름']}**{attendance_mark}: {' | '.join(reasons)}")
            else:
                st.info("빌런 판정된 학생이 없습니다.")

    with refresh_area:
        auto_refresh = st.checkbox("자동 새로고침 (10초)", value=True)
    if auto_refresh:
        time.sleep(10)
        st.rerun()


# ============================================
# ★★★ 메인: 탭으로 전광판 / 개인리포트 전환 ★★★
# ============================================
def main():
    tab1, tab2 = st.tabs(["전광판", "개인 리포트"])
    
    with tab1:
        page_scoreboard()
    
    with tab2:
        page_student_report()

if __name__ == "__main__":
    main()
