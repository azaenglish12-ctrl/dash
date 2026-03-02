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
# ★★★ 개인 리포트 페이지 ★★★
# ============================================
def create_student_dashboard(student_df, student_name):
    """개인 리포트용 대시보드 - 전광판과 동일한 디자인, 날짜 시계열 순서"""

    student_df = student_df.copy().sort_values('날짜').reset_index(drop=True)
    student_df['status'] = student_df.apply(classify_student, axis=1)

    fig = go.Figure()

    all_labels = []
    tick_positions = []

    hero_count = 0
    villain_count = 0
    normal_count = 0
    midterm_count = 0
    absent_count = 0
    late_count = 0

    for idx, (_, row) in enumerate(student_df.iterrows()):
        x_base = idx * STUDENT_WIDTH
        status = row['status']

        # 날짜 라벨
        try:
            d = pd.to_datetime(row['날짜'])
            label = f"{d.month}/{d.day}"
        except:
            label = row['날짜']
        if row['출석'] == '지각':
            label += " ⏰"
            late_count += 1

        all_labels.append(label)
        tick_positions.append(x_base + 1.2)

        if status == 'hero':
            fig.add_shape(type="rect", x0=x_base - 0.4, x1=x_base + 2.8, y0=0, y1=105,
                line=dict(color="#00C851", width=3), fillcolor="rgba(255,215,0,0.1)", layer="below")
            add_hero_effect(fig, row, x_base)
            hero_count += 1
        elif status == 'villain':
            fig.add_shape(type="rect", x0=x_base - 0.4, x1=x_base + 2.8, y0=0, y1=105,
                line=dict(color="#8e44ad", width=3), fillcolor="rgba(142,68,173,0.1)", layer="below")
            add_villain_effect(fig, row, x_base)
            villain_count += 1
        elif status == 'midterm':
            for i in range(4):
                fig.add_trace(go.Bar(
                    x=[x_base + i * 0.8], y=[40], width=0.7,
                    marker=dict(color='rgba(255, 200, 100, 0.3)',
                               pattern=dict(shape='/', size=8, solidity=0.2)),
                    text='내신', textposition='inside', textfont=dict(size=9),
                    showlegend=False, hovertemplate=f"{label} - 내신기간<extra></extra>"
                ))
            midterm_count += 1
        elif status == 'absent':
            fig.add_vrect(x0=x_base - 0.4, x1=x_base + 2.8,
                fillcolor="rgba(128, 128, 128, 0.08)", layer="below", line_width=0)
            absent_count += 1
        else:
            fig.add_shape(type="rect", x0=x_base - 0.4, x1=x_base + 2.8, y0=0, y1=105,
                line=dict(color="rgba(100, 100, 100, 0.3)", width=2), fillcolor="rgba(0,0,0,0)", layer="below")
            add_normal_bars(fig, row, x_base)
            normal_count += 1

    # 기준선
    fig.add_hline(y=94, line_dash="dash", line_color="rgba(255,0,0,0.3)",
                  annotation_text="어휘 기준 94점", annotation_position="right")
    fig.add_hline(y=80, line_dash="dash", line_color="rgba(0,0,255,0.3)",
                  annotation_text="스펠/독해 기준 80점", annotation_position="right")

    fig.update_layout(
        title=None, height=900,
        margin=dict(l=60, r=60, t=10, b=150),
        xaxis=dict(ticktext=all_labels, tickvals=tick_positions,
                   tickfont=dict(size=12), tickangle=0),
        yaxis=dict(range=[0, 115], title=dict(text="점수", font=dict(size=14)),
                   gridcolor='rgba(128,128,128,0.2)'),
        plot_bgcolor='white', paper_bgcolor='#f5f5f5',
        bargap=0.1, bargroupgap=0.05,
        showlegend=False, hovermode='x'
    )

    summary_text = f"""
    <div style='text-align: center; padding: 10px; background: white; border-radius: 5px;'>
    <b>영웅: {hero_count}일 | 빌런: {villain_count}일 | 정상응시: {normal_count}일 | 내신: {midterm_count}일 | 결석: {absent_count}일 | 지각: {late_count}일 ⏰</b>
    </div>
    """

    return fig, summary_text


def page_student_report():
    """개인 리포트 탭"""
    try:
        df = load_data()

        if df is None or len(df) == 0:
            st.error("데이터를 불러올 수 없습니다.")
            return

        # 컬럼 확인 및 없는 컬럼 기본값 추가
        for col in ['어휘점수', '스펠점수', '독해점수', '문법점수']:
            if col not in df.columns:
                df[col] = None
        if '반' not in df.columns:
            if '반코드' in df.columns:
                df = df.rename(columns={'반코드': '반'})
            else:
                df['반'] = '미지정'
        if '출석' not in df.columns:
            df['출석'] = '출석'

        # 점수 컬럼 숫자 변환
        for col in ['어휘점수', '스펠점수', '독해점수', '문법점수']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        df['날짜'] = df['날짜'].astype(str).str.strip()
        df = df[(df['날짜'] != 'nan') & (df['날짜'] != '') & (df['날짜'] != 'None')]

        if len(df) == 0:
            st.error("유효한 날짜 데이터가 없습니다.")
            return

        # 날짜 변환
        df['날짜_obj'] = pd.to_datetime(df['날짜'], errors='coerce', format='mixed')
        if df['날짜_obj'].isna().all():
            for fmt in ['%Y-%m-%d', '%Y. %m. %d', '%Y.%m.%d', '%Y/%m/%d']:
                try:
                    df['날짜_obj'] = pd.to_datetime(df['날짜'], format=fmt, errors='coerce')
                    if df['날짜_obj'].notna().any():
                        break
                except:
                    continue

        valid_mask = df['날짜_obj'].notna()
        df.loc[valid_mask, '날짜'] = df.loc[valid_mask, '날짜_obj'].dt.strftime('%Y-%m-%d')
        df = df[valid_mask].copy()

        if len(df) == 0:
            st.error("날짜를 파싱할 수 없습니다.")
            return

        all_students = sorted(df['이름'].unique().tolist())
        if len(all_students) == 0:
            st.error("학생 데이터가 없습니다.")
            return

        student_classes = df.drop_duplicates('이름').set_index('이름')['반'].to_dict()

        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            selected_student = st.selectbox("학생 선택", all_students, index=0)

        # 해당 학생의 데이터 날짜 범위 확인
        student_all = df[df['이름'] == selected_student].copy()
        if len(student_all) == 0:
            st.warning("해당 학생의 데이터가 없습니다.")
            return

        min_date = student_all['날짜_obj'].min().date()
        max_date = student_all['날짜_obj'].max().date()
        today = datetime.now().date()

        # 월 목록 (프리셋용)
        months = sorted(student_all['날짜_obj'].dropna().dt.to_period('M').unique(), reverse=True)

        # 기간 선택 옵션
        period_options = []
        # 기간 선택 옵션 - "1월~현재"를 맨 앞(기본값)으로
        period_options = ["1월~현재"]
        for m in months:
            period_options.append(str(m))
        period_options.append("최근 2개월")
        period_options.append("최근 3개월")
        period_options.append("최근 6개월")
        period_options.append("전체")
        period_options.append("직접 선택")

        with col2:
            selected_period = st.selectbox("기간", period_options, index=0)

        # 기간에 따라 시작/종료 날짜 결정
        if selected_period == "직접 선택":
        if selected_period == "1월~현재":
            start_date = pd.Timestamp("2026-01-01")
            end_date = pd.Timestamp(today)
            period_display = "2026년 1월~현재"
        elif selected_period == "직접 선택":
            with col3:
                custom_start = st.date_input("시작일", value=max(min_date, today - timedelta(days=90)),
                    min_value=min_date, max_value=max_date, format="YYYY-MM-DD")
            start_date = pd.Timestamp(custom_start)
            end_date = pd.Timestamp(today)
            period_display = f"{custom_start.strftime('%m/%d')}~현재"
        elif selected_period == "최근 2개월":
            start_date = pd.Timestamp(today - timedelta(days=60))
            end_date = pd.Timestamp(today)
            period_display = "최근 2개월"
        elif selected_period == "최근 3개월":
            start_date = pd.Timestamp(today - timedelta(days=90))
            end_date = pd.Timestamp(today)
            period_display = "최근 3개월"
        elif selected_period == "최근 6개월":
            start_date = pd.Timestamp(today - timedelta(days=180))
            end_date = pd.Timestamp(today)
            period_display = "최근 6개월"
        elif selected_period == "전체":
            start_date = pd.Timestamp(min_date)
            end_date = pd.Timestamp(today)
            period_display = "전체"
        else:
            # 월 선택
            try:
                period_obj = pd.Period(selected_period)
                start_date = pd.Timestamp(period_obj.start_time)
                end_date = pd.Timestamp(period_obj.end_time)
                period_display = pd.to_datetime(selected_period).strftime('%Y년 %m월')
            except:
                start_date = pd.Timestamp(min_date)
                end_date = pd.Timestamp(today)
                period_display = selected_period

        # 필터링
        student_df = student_all[
            (student_all['날짜_obj'] >= start_date) & 
            (student_all['날짜_obj'] <= end_date)
        ].copy()
        student_df = student_df.sort_values('날짜').reset_index(drop=True)

        if len(student_df) == 0:
            st.warning("해당 기간에 데이터가 없습니다.")
            return

        ban = student_classes.get(selected_student, '?')
        total_days = len(student_df)
        absent_days = int((student_df['출석'] == '결석').sum())
        late_days = int((student_df['출석'] == '지각').sum())
        attend_days = total_days - absent_days
        student_df['is_hero'] = student_df.apply(is_hero, axis=1)
        hero_days = int(student_df['is_hero'].sum())
        hero_pct = (hero_days / attend_days * 100) if attend_days > 0 else 0

        # 타이틀
        st.markdown(
            f"<h1 style='margin:0 0 5px 0;font-size:20px;'>"
            f"{selected_student} ({ban}) | {period_display} 개인현황 "
            f"(영웅 {hero_days}회/{attend_days}일 = {hero_pct:.0f}%)</h1>",
            unsafe_allow_html=True
        )

        # ★ 전광판과 동일한 차트 생성
        fig, summary = create_student_dashboard(student_df, selected_student)

        if fig is not None:
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            st.markdown(summary, unsafe_allow_html=True)

        st.markdown("""
        <div style='text-align: center; padding: 10px; margin-top: 10px; background: #f0f0f0; border-radius: 5px;'>
        <b>막대 색상:</b> 
        <span style='color: #00C851;'>■ 통과</span> | 
        <span style='color: #FF4444;'>■ 미통과</span> | 
        <span style='color: #3498db;'>■ 문법 (커트없음)</span> |
        <b>X축 = 날짜순 (금테=영웅 / 보라테=빌런 / 회색=정상)</b>
        </div>
        """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"개인 리포트 로드 중 오류 발생: {e}")
        import traceback
        st.code(traceback.format_exc())


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
# ★★★ 메인: 라디오 버튼으로 전광판 / 개인리포트 전환 ★★★
# ============================================
def main():
    page = st.radio("", ["전광판", "개인 리포트"], horizontal=True, label_visibility="collapsed")
    st.markdown("<hr style='margin:0 0 5px 0;padding:0;border-color:#eee;'>", unsafe_allow_html=True)

    if page == "전광판":
        page_scoreboard()
    else:
        page_student_report()

if __name__ == "__main__":
    main()
