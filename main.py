import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime
import time

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
    .villain-badge {
        background: linear-gradient(135deg, #8e44ad 0%, #3c096c 100%);
        color: white;
        padding: 5px 10px;
        border-radius: 15px;
        font-weight: bold;
        display: inline-block;
        margin: 2px;
    }
    </style>
""", unsafe_allow_html=True)

# google_sheets.py import 추가
try:
    from google_sheets import load_data_from_sheets, get_test_data
    GOOGLE_SHEETS_AVAILABLE = True
except ImportError:
    GOOGLE_SHEETS_AVAILABLE = False

# 구글시트 URL 설정
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1qW6Cs4FaSp-kEsSDFAyUw0hWzaTVBsSn9WeU8ZW_vd4/edit?gid=368136260#gid=368136260"
SHEET_NAME = "성적데이터"

# 데이터 로드 함수
@st.cache_data(ttl=10)
def load_data():
    """구글시트 또는 테스트 데이터 로드"""
    if GOOGLE_SHEETS_AVAILABLE and not GOOGLE_SHEET_URL.endswith("YOUR_SHEET_ID/edit"):
        df = load_data_from_sheets(GOOGLE_SHEET_URL, SHEET_NAME)
        if df is not None and not df.empty:
            return df
    
    # 테스트 데이터
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
                   93.6, 99, None, 88, 96] * 3
    }
    return pd.DataFrame(data)

# 영웅 판정 함수
def is_hero(row):
    """영웅 조건: 어휘 정확히 100점 + 스펠 95점 이상 + 독해 80점 이상"""
    # 결석한 학생만 제외 (출석, 지각 모두 포함)
    if row['출석'] == '결석':
        return False
    
    # 점수가 없으면 영웅 아님
    if pd.isna(row['어휘점수']) or pd.isna(row['스펠점수']):
        return False
    
    try:
        # 어휘 정확히 100점 AND 스펠 95점 이상
        # 문자열일 수도 있으니 변환하고, 소수점 비교
        vocab_score = float(str(row['어휘점수']).strip())
        spell_score = float(str(row['스펠점수']).strip())
        
        # 소수점 오차 고려해서 99.9 이상을 100으로 간주
        is_vocab_100 = vocab_score >= 99.9 and vocab_score <= 100.1
        is_spell_95_plus = spell_score >= 94.9
        
        # 독해 점수가 있는 경우, 80점 이상이어야 함
        if pd.notna(row['독해점수']):
            reading_score = float(str(row['독해점수']).strip())
            is_reading_pass = reading_score >= 79.9  # 80점 이상
            return is_vocab_100 and is_spell_95_plus and is_reading_pass
        else:
            # 독해 점수가 없으면 어휘+스펠만으로 판단
            return is_vocab_100 and is_spell_95_plus
            
    except (ValueError, TypeError):
        return False

# 빌런 판정 함수
def is_villain(row):
    """빌런 조건: 어휘<80 OR 스펠<60 OR (점수 있는 과목 중 2개 이상 미통과)"""
    # 결석한 학생만 제외 (출석, 지각 모두 포함)
    if row['출석'] == '결석':
        return False
    
    # 점수가 하나도 없으면 내신으로 분류 (빌런 아님)
    if pd.isna(row['어휘점수']) and pd.isna(row['스펠점수']) and pd.isna(row['독해점수']):
        return False
    
    # 즉시 빌런 조건 1: 어휘 < 80점
    if pd.notna(row['어휘점수']) and row['어휘점수'] < 80:
        return True
    
    # 즉시 빌런 조건 2: 스펠 < 60점
    if pd.notna(row['스펠점수']) and row['스펠점수'] < 60:
        return True
    
    # 조건 3: 점수가 있는 과목 중 2개 이상 미통과
    # 점수가 있는 과목과 미통과 과목을 따로 카운트
    total_subjects = 0  # 점수가 기록된 과목 수
    fail_count = 0      # 미통과 과목 수
    
    # 어휘 체크 (기준: 94점)
    if pd.notna(row['어휘점수']):
        total_subjects += 1
        if row['어휘점수'] < 94:
            fail_count += 1
    
    # 스펠 체크 (기준: 90점)
    if pd.notna(row['스펠점수']):
        total_subjects += 1
        if row['스펠점수'] < 90:
            fail_count += 1
    
    # 독해 체크 (기준: 80점)
    if pd.notna(row['독해점수']):
        total_subjects += 1
        if row['독해점수'] < 80:
            fail_count += 1
    
    # 2개 이상 미통과면 빌런
    # (2과목만 있고 2과목 미통과도 빌런, 3과목 있고 2개 이상 미통과도 빌런)
    return fail_count >= 2

# 월별 칭호 집계 함수
def get_monthly_badges(df, selected_date, excluded_students=[]):
    """해당 월의 영웅/빌런 칭호 집계"""
    # 선택한 날짜의 연월 추출
    try:
        date_obj = pd.to_datetime(selected_date)
        year_month = date_obj.strftime('%Y-%m')
    except:
        return pd.DataFrame(), pd.DataFrame()
    
    # 해당 월 데이터 필터링
    df['날짜_obj'] = pd.to_datetime(df['날짜'], errors='coerce')
    monthly_df = df[df['날짜_obj'].dt.strftime('%Y-%m') == year_month].copy()
    
    # 제외할 학생 필터링
    if excluded_students:
        monthly_df = monthly_df[~monthly_df['이름'].isin(excluded_students)]
    
    # 영웅 집계
    monthly_df['is_hero'] = monthly_df.apply(is_hero, axis=1)
    hero_counts = monthly_df[monthly_df['is_hero']].groupby('이름').size().reset_index(name='영웅횟수')
    hero_counts = hero_counts.sort_values('영웅횟수', ascending=False)
    
    # 빌런 집계
    monthly_df['is_villain'] = monthly_df.apply(is_villain, axis=1)
    villain_counts = monthly_df[monthly_df['is_villain']].groupby('이름').size().reset_index(name='빌런횟수')
    villain_counts = villain_counts.sort_values('빌런횟수', ascending=False)
    
    return hero_counts, villain_counts

# 이름 마스킹 함수
def mask_name(name):
    """이름의 중간 글자를 □로 마스킹"""
    if len(name) <= 1:
        return name
    elif len(name) == 2:
        return name[0] + '□'
    elif len(name) == 3:
        return name[0] + '□' + name[2]
    else:  # 4글자 이상
        # 첫 글자와 마지막 글자만 남기고 나머지 □
        return name[0] + '□' * (len(name) - 2) + name[-1]

# 학생 상태 분류 함수
def classify_student(row, excluded_students=[]):
    """학생 상태 분류: hero, villain, normal, midterm, absent"""
    if row['출석'] == '결석':
        return 'absent'
    elif pd.isna(row['어휘점수']) and pd.isna(row['스펠점수']) and pd.isna(row['독해점수']):
        return 'midterm'
    # 제외된 학생은 영웅/빌런 판정하지 않고 normal로 처리
    elif row['이름'] in excluded_students:
        return 'normal'
    elif is_hero(row):
        return 'hero'
    elif is_villain(row):
        return 'villain'
    else:
        return 'normal'

# 영웅 효과 추가 함수
def add_hero_effect(fig, row, x_base):
    """어휘+스펠 100점 영웅 효과 - 통과 느낌의 색상"""
    masked_name = mask_name(row['이름'])
    
    # 실제 점수 가져오기
    vocab_score = float(row['어휘점수'])
    spell_score = float(row['스펠점수'])
    
    # 골드-그린 그라디언트 막대 - 어휘
    fig.add_trace(go.Bar(
        x=[x_base],
        y=[vocab_score],
        width=0.7,
        marker=dict(
            color='#00C851',  # 밝은 초록색
            line=dict(color='gold', width=4)
        ),
        text=str(int(vocab_score)),
        textposition='inside',
        textfont=dict(size=12, color='white', family='Arial Black'),
        showlegend=False,
        hovertemplate=f"{masked_name} - 어휘: {vocab_score}점<extra></extra>"
    ))
    
    # 골드-그린 그라디언트 막대 - 스펠
    fig.add_trace(go.Bar(
        x=[x_base + 0.8],
        y=[spell_score],
        width=0.7,
        marker=dict(
            color='#FFD700',  # 골드
            line=dict(color='#00C851', width=4)
        ),
        text=str(int(spell_score)),
        textposition='inside',
        textfont=dict(size=12, color='white', family='Arial Black'),
        showlegend=False,
        hovertemplate=f"{masked_name} - 스펠: {spell_score}점<extra></extra>"
    ))
    
    # "영웅" 텍스트 - 골드 배경
    fig.add_annotation(
        text="<b>영웅</b>",
        x=x_base + 0.8,
        y=108,
        showarrow=False,
        font=dict(size=14, color='#00C851', family='Arial Black'),
        bgcolor='#FFD700',
        bordercolor='#00C851',
        borderwidth=3
    )
    
    # 독해 점수
    if pd.notna(row['독해점수']):
        color = '#00C851' if row['독해점수'] >= 80 else '#FF4444'
        fig.add_trace(go.Bar(
            x=[x_base + 1.6],
            y=[row['독해점수']],
            width=0.7,
            marker=dict(
                color=color,
                line=dict(color='gold', width=3)
            ),
            text=str(int(row['독해점수'])),
            textposition='auto',
            textfont=dict(size=10, color='white'),
            showlegend=False,
            hovertemplate=f"{masked_name} - 독해: {row['독해점수']}점<extra></extra>"
        ))

# 빌런 효과 추가 함수
def add_villain_effect(fig, row, x_base):
    """빌런 효과 - 일반 막대(초록/빨강) + 보라 테두리 + 빌런 라벨"""
    masked_name = mask_name(row['이름'])
    
    subjects = [
        ('어휘점수', 94, x_base),
        ('스펠점수', 90, x_base + 0.8),
        ('독해점수', 80, x_base + 1.6)
    ]
    
    for subject, threshold, x_pos in subjects:
        if pd.notna(row[subject]):
            score = row[subject]
            # 일반 학생과 동일한 색상 (통과: 초록, 미통과: 빨강)
            color = '#00C851' if score >= threshold else '#FF4444'
            
            fig.add_trace(go.Bar(
                x=[x_pos],
                y=[score],
                width=0.7,
                marker=dict(
                    color=color,
                    line=dict(color='#8e44ad', width=3)  # 보라색 테두리
                ),
                text=str(int(score)),
                textposition='auto',
                textfont=dict(size=10, color='white', family='Arial Black'),  # 크고 굵게
                showlegend=False,
                hovertemplate=f"{masked_name} - {subject[:-2]}: {score}점<extra></extra>"
            ))
    
    # "빌런" 텍스트만 유지
    fig.add_annotation(
        text="<b>빌런</b>",
        x=x_base + 0.8,
        y=108,
        showarrow=False,
        font=dict(size=14, color='white', family='Arial Black'),
        bgcolor='#8e44ad',
        bordercolor='#3c096c',
        borderwidth=2
    )

# 일반 막대 추가 함수
def add_normal_bars(fig, row, x_base):
    """일반 학생 막대 추가"""
    masked_name = mask_name(row['이름'])
    
    subjects = [
        ('어휘점수', 94, x_base),
        ('스펠점수', 90, x_base + 0.8),
        ('독해점수', 80, x_base + 1.6)
    ]
    
    for subject, threshold, x_pos in subjects:
        if pd.notna(row[subject]):
            score = row[subject]
            color = '#00C851' if score >= threshold else '#FF4444'
            
            fig.add_trace(go.Bar(
                x=[x_pos],
                y=[score],
                width=0.7,
                marker_color=color,
                text=str(int(score)),
                textposition='auto',
                textfont=dict(size=9, color='white'),
                showlegend=False,
                hovertemplate=f"{masked_name} - {subject[:-2]}: {score}점<extra></extra>"
            ))

# 내신 미니차트 추가 함수
def add_midterm_section(fig, midterm_df, start_x):
    """내신 학생들 미니차트"""
    if len(midterm_df) == 0:
        return
    
    fig.add_vrect(
        x0=start_x - 0.5,
        x1=start_x + len(midterm_df) * 3,
        fillcolor="rgba(255, 235, 150, 0.1)",
        layer="below",
        line_width=0
    )
    
    for idx, (_, row) in enumerate(midterm_df.iterrows()):
        x_pos = start_x + idx * 3
        masked_name = mask_name(row['이름'])
        
        for i in range(3):
            fig.add_trace(go.Bar(
                x=[x_pos + i * 0.8],
                y=[40],
                width=0.7,
                marker=dict(
                    color='rgba(255, 200, 100, 0.3)',
                    pattern=dict(shape='/', size=8, solidity=0.2)
                ),
                text='내신',
                textposition='inside',
                textfont=dict(size=9),
                showlegend=False,
                hovertemplate=f"{masked_name} - 내신기간<extra></extra>"
            ))

# 메인 대시보드 생성 함수
def create_dashboard(selected_date, excluded_students=[]):
    """전체 대시보드 생성"""
    df = load_data()
    
    # 선택한 날짜 데이터만 필터링
    today_df = df[df['날짜'] == selected_date].copy()
    
    # 제외할 학생 필터링
    if excluded_students:
        today_df = today_df[~today_df['이름'].isin(excluded_students)]
    
    if len(today_df) == 0:
        st.warning(f"{selected_date}에 해당하는 데이터가 없습니다.")
        return None, None
    
    # 학생 상태 분류
    today_df['status'] = today_df.apply(classify_student, axis=1)
    
    # 그룹별 분리 및 정렬
    class_order = {'초등': 1, '중등': 2, '수능': 3}
    
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
    
    # Figure 생성
    fig = go.Figure()
    
    # 1. 영웅들
    for idx, (_, row) in enumerate(hero_df.iterrows()):
        x_base = idx * 2.5
        fig.add_shape(
            type="rect",
            x0=x_base - 0.4, 
            x1=x_base + 2.0,
            y0=0, 
            y1=105,
            line=dict(color="#00C851", width=3),  # 초록 테두리
            fillcolor="rgba(255,215,0,0.1)",  # 골드 배경
            layer="below"
        )
        add_hero_effect(fig, row, x_base)
    
    # 2. 정상 응시자
    normal_start = len(hero_df) * 2.5 + 1
    for idx, (_, row) in enumerate(normal_df.iterrows()):
        x_base = normal_start + idx * 2.5
        fig.add_shape(
            type="rect",
            x0=x_base - 0.4, 
            x1=x_base + 2.0,
            y0=0, 
            y1=105,
            line=dict(color="rgba(100, 100, 100, 0.3)", width=2),
            fillcolor="rgba(0,0,0,0)",
            layer="below"
        )
        add_normal_bars(fig, row, x_base)
    
    # 3. 빌런들
    villain_start = normal_start + len(normal_df) * 2.5 + 1
    for idx, (_, row) in enumerate(villain_df.iterrows()):
        x_base = villain_start + idx * 2.5
        fig.add_shape(
            type="rect",
            x0=x_base - 0.4, 
            x1=x_base + 2.0,
            y0=0, 
            y1=105,
            line=dict(color="#8e44ad", width=3),
            fillcolor="rgba(142,68,173,0.1)",
            layer="below"
        )
        add_villain_effect(fig, row, x_base)
    
    # 4. 내신 구간
    midterm_start = villain_start + len(villain_df) * 2.5 + 1
    add_midterm_section(fig, midterm_df, midterm_start)
    
    # 5. 결석 구간
    absent_start = midterm_start + len(midterm_df) * 3 + 1
    if len(absent_df) > 0:
        fig.add_vrect(
            x0=absent_start - 0.5,
            x1=absent_start + len(absent_df) * 3,
            fillcolor="rgba(128, 128, 128, 0.1)",
            layer="below",
            line_width=0
        )
    
    # 기준선
    fig.add_hline(y=94, line_dash="dash", line_color="rgba(255,0,0,0.3)",
                  annotation_text="어휘 기준 94점", annotation_position="right")
    fig.add_hline(y=80, line_dash="dash", line_color="rgba(0,0,255,0.3)",
                  annotation_text="스펠/독해 기준 80점", annotation_position="right")
    
    # 이름 리스트 생성
    all_names = []
    tick_positions = []
    
    # 영웅
    for idx, (_, row) in enumerate(hero_df.iterrows()):
        name = mask_name(row['이름'])
        if row['출석'] == '지각':
            name += " ⏰"
        all_names.append(name)
        tick_positions.append(idx * 2.5 + 0.8)
    
    # 정상
    for idx, (_, row) in enumerate(normal_df.iterrows()):
        name = mask_name(row['이름'])
        if row['출석'] == '지각':
            name += " ⏰"
        all_names.append(name)
        tick_positions.append(normal_start + idx * 2.5 + 0.8)
    
    # 빌런
    for idx, (_, row) in enumerate(villain_df.iterrows()):
        name = mask_name(row['이름'])
        if row['출석'] == '지각':
            name += " ⏰"
        all_names.append(name)
        tick_positions.append(villain_start + idx * 2.5 + 0.8)
    
    # 내신
    for idx, (_, row) in enumerate(midterm_df.iterrows()):
        name = mask_name(row['이름'])
        if row['출석'] == '지각':
            name += " ⏰"
        all_names.append(name)
        tick_positions.append(midterm_start + idx * 3 + 0.8)
    
    # 결석
    for idx, (_, row) in enumerate(absent_df.iterrows()):
        all_names.append(mask_name(row['이름']))
        tick_positions.append(absent_start + idx * 3 + 0.8)
    
    # 레이아웃
    fig.update_layout(
        title={
            'text': f"<b>통과 현황 - {selected_date}</b>",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 24, 'color': 'black'}
        },
        height=900,
        margin=dict(l=60, r=60, t=100, b=150),
        xaxis=dict(
            ticktext=all_names,
            tickvals=tick_positions,
            tickfont=dict(size=11),
            tickangle=0
        ),
        yaxis=dict(
            range=[0, 115],
            title=dict(text="점수", font=dict(size=14)),
            gridcolor='rgba(128,128,128,0.2)'
        ),
        plot_bgcolor='white',
        paper_bgcolor='#f5f5f5',
        bargap=0.1,
        bargroupgap=0.05,
        showlegend=False,
        hovermode='x'
    )
    
    # 구간 구분선
    if len(normal_df) > 0:
        fig.add_vline(x=normal_start - 0.5, line_dash="dot", line_color="#00C851", opacity=0.5)  # 초록
    if len(villain_df) > 0:
        fig.add_vline(x=villain_start - 0.5, line_dash="dot", line_color="purple", opacity=0.5)
    fig.add_vline(x=midterm_start - 0.5, line_dash="dot", line_color="gray", opacity=0.3)
    if len(absent_df) > 0:
        fig.add_vline(x=absent_start - 0.5, line_dash="dot", line_color="gray", opacity=0.3)
    
    # 통과자 수 계산
    pass_count = sum((normal_df['어휘점수'] >= 94) & (normal_df['스펠점수'] >= 90) & (normal_df['독해점수'] >= 80))
    
    # 지각 학생 수 계산
    late_count = len(today_df[today_df['출석'] == '지각'])
    
    # 제외된 학생 수
    excluded_count = len(excluded_students)
    
    # 요약 정보
    excluded_text = f" | <span style='color: gray'>제외: {excluded_count}명</span>" if excluded_count > 0 else ""
    summary_text = f"""
    <div style='text-align: center; padding: 10px; background: white; border-radius: 5px;'>
    <b>영웅: {len(hero_df)}명 | 빌런: {len(villain_df)}명 | 정상응시: {len(normal_df)}명 | 내신: {len(midterm_df)}명 | 결석: {len(absent_df)}명 | 지각: {late_count}명 ⏰{excluded_text}</b><br>
    <span style='color: green'>통과: {pass_count}명</span> | 
    <span style='color: red'>재시험: {len(normal_df) - pass_count}명</span>
    </div>
    """
    
    return fig, summary_text

# Streamlit 앱 메인
def main():
    # 데이터 로드
    df = load_data()
    
    # 날짜 선택 및 학생 제외 기능
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
            col1, col2 = st.columns([1, 2])
            with col1:
                selected_date = st.date_input(
                    "날짜 선택",
                    value=date_objects[-1],
                    min_value=date_objects[0],
                    max_value=date_objects[-1],
                    format="YYYY-MM-DD"
                )
            selected_date_str = date_mapping.get(selected_date, available_dates[-1])
            
            # 해당 날짜의 학생 목록 가져오기
            today_students = df[df['날짜'] == selected_date_str]['이름'].unique().tolist()
            today_students.sort()
            
            with col2:
                excluded_students = st.multiselect(
                    "제외할 학생 선택 (집계에서 제외됩니다)",
                    options=today_students,
                    default=[],
                    help="선택한 학생은 영웅/빌런 집계 및 그래프에서 제외됩니다"
                )
        else:
            selected_date_str = available_dates[-1]
            excluded_students = []
    else:
        st.error("'날짜' 컬럼이 없습니다.")
        return
    
    # 타이틀
    st.markdown("<h1 style='margin-bottom: 10px;'>📊 아자영어 통과현황 (커트 : 뜻 94, 문맥 90, 독해 80)</h1>", unsafe_allow_html=True)
    
    # 월별 칭호 통계 - 좌우 2단으로 컴팩트하게
    col_hero, col_villain = st.columns(2)
    
    hero_counts, villain_counts = get_monthly_badges(df, selected_date_str, excluded_students)
    
    with col_hero:
        st.markdown("### 🦸‍♂️ 영웅 Top 5")
        if len(hero_counts) > 0:
            hero_html = "<div style='display: flex; flex-wrap: wrap; gap: 10px; align-items: center;'>"
            for idx, row in hero_counts.head(5).iterrows():
                masked_name = mask_name(row['이름'])
                hero_html += f"<span style='font-size: 13px; margin-right: 5px;'><b>{masked_name}</b></span>"
                for i in range(int(row['영웅횟수'])):
                    hero_html += """<span style='display: inline-block; background: yellow; color: red; 
                                  border: 1px solid red; padding: 2px 5px; margin: 0 2px;
                                  border-radius: 3px; font-weight: bold; font-size: 10px;'>영웅</span>"""
                hero_html += "<span style='margin-right: 15px;'></span>"  # 학생 간 간격
            hero_html += "</div>"
            st.markdown(hero_html, unsafe_allow_html=True)
        else:
            st.info("아직 영웅이 없습니다.")
    
    with col_villain:
        st.markdown("### 🦹 빌런 Top 5")
        if len(villain_counts) > 0:
            villain_html = "<div style='display: flex; flex-wrap: wrap; gap: 10px; align-items: center;'>"
            for idx, row in villain_counts.head(5).iterrows():
                masked_name = mask_name(row['이름'])
                villain_html += f"<span style='font-size: 13px; margin-right: 5px;'><b>{masked_name}</b></span>"
                for i in range(int(row['빌런횟수'])):
                    villain_html += """<span style='display: inline-block; background: #8e44ad; color: white; 
                                  border: 1px solid #3c096c; padding: 2px 5px; margin: 0 2px;
                                  border-radius: 3px; font-weight: bold; font-size: 10px;'>빌런</span>"""
                villain_html += "<span style='margin-right: 15px;'></span>"  # 학생 간 간격
            villain_html += "</div>"
            st.markdown(villain_html, unsafe_allow_html=True)
        else:
            st.info("아직 빌런이 없습니다.")
    
    # 그래프는 전체 너비 사용
    fig, summary = create_dashboard(selected_date_str, excluded_students)
    
    if fig is not None:
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        st.markdown(summary, unsafe_allow_html=True)
        
        # 제외된 학생 표시
        if excluded_students:
            st.info(f"🚫 제외된 학생: {', '.join(excluded_students)}")
    
    # 디버깅 정보 (접을 수 있는 섹션)
    with st.expander("🔍 영웅/빌런 판정 상세 정보 (디버깅)"):
        st.info("⏰ 표시는 지각한 학생입니다. 지각한 학생도 시험을 봤기 때문에 영웅/빌런 판정에 포함됩니다.")
        
        today_df = df[df['날짜'] == selected_date_str].copy()
        
        # 제외할 학생 필터링 (디버깅에도 반영)
        if excluded_students:
            st.warning(f"🚫 다음 학생들이 제외되었습니다: {', '.join(excluded_students)}")
            today_df = today_df[~today_df['이름'].isin(excluded_students)]
        
        today_df['is_hero'] = today_df.apply(is_hero, axis=1)
        today_df['is_villain'] = today_df.apply(is_villain, axis=1)
        
        # 모든 학생의 영웅 판정 상태 보기
        st.markdown("### 📋 전체 학생 영웅 판정 현황")
        all_students = today_df[(today_df['출석'] != '결석') & 
                                (pd.notna(today_df['어휘점수'])) & 
                                (pd.notna(today_df['스펠점수']))].copy()
        
        if len(all_students) > 0:
            for _, row in all_students.iterrows():
                try:
                    vocab_val = float(str(row['어휘점수']).strip())
                    spell_val = float(str(row['스펠점수']).strip())
                    is_hero_status = "🦸 영웅" if row['is_hero'] else "일반"
                    attendance_mark = "⏰" if row['출석'] == '지각' else ""
                    
                    # 영웅 조건 체크
                    vocab_ok = "✅" if (vocab_val >= 99.9 and vocab_val <= 100.1) else "❌"
                    spell_ok = "✅" if spell_val >= 94.9 else "❌"
                    
                    st.markdown(f"**{row['이름']}** {attendance_mark} [{is_hero_status}]: {vocab_ok} 어휘 {vocab_val}점, {spell_ok} 스펠 {spell_val}점")
                except:
                    st.markdown(f"**{row['이름']}**: 데이터 변환 오류")
        
        st.markdown("---")
        
        st.markdown("### 🦸 영웅으로 판정된 학생들")
        heroes = today_df[today_df['is_hero'] == True]
        if len(heroes) > 0:
            for _, row in heroes.iterrows():
                vocab_val = float(str(row['어휘점수']).strip())
                spell_val = float(str(row['스펠점수']).strip())
                attendance_mark = " ⏰" if row['출석'] == '지각' else ""
                st.markdown(f"**{row['이름']}**{attendance_mark}: ✅ 어휘 {vocab_val}점, ✅ 스펠 {spell_val}점")
        else:
            st.info("영웅 판정된 학생이 없습니다.")
        
        st.markdown("### 🔍 영웅 후보 (거의 다 된 학생들)")
        # 시험 본 학생들 중 영웅이 아닌 학생 (출석 또는 지각)
        candidates = today_df[(today_df['출석'] != '결석') & 
                              (today_df['is_hero'] == False) &
                              (pd.notna(today_df['어휘점수'])) &
                              (pd.notna(today_df['스펠점수']))]
        # 어휘 90점 이상이거나 스펠 85점 이상인 학생들만
        candidates = candidates[(candidates['어휘점수'] >= 90) | (candidates['스펠점수'] >= 85)]
        
        if len(candidates) > 0:
            for _, row in candidates.iterrows():
                vocab_status = "✅" if row['어휘점수'] >= 100 else f"❌ {row['어휘점수']}점"
                spell_status = "✅" if row['스펠점수'] >= 95 else f"❌ {row['스펠점수']}점"
                attendance_mark = " ⏰" if row['출석'] == '지각' else ""
                st.markdown(f"**{row['이름']}**{attendance_mark}: 어휘 {vocab_status} (100점 필요), 스펠 {spell_status} (95점 필요)")
        
        st.markdown("---")
        
        st.markdown("### 🦹 빌런으로 판정된 학생들")
        villains = today_df[today_df['is_villain'] == True]
        if len(villains) > 0:
            for _, row in villains.iterrows():
                reasons = []
                attendance_mark = " ⏰" if row['출석'] == '지각' else ""
                
                # 즉시 빌런 조건 체크
                if pd.notna(row['어휘점수']) and row['어휘점수'] < 80:
                    reasons.append(f"🔥 어휘 {row['어휘점수']}점 (80점 미만 - 즉시 빌런)")
                if pd.notna(row['스펠점수']) and row['스펠점수'] < 60:
                    reasons.append(f"🔥 스펠 {row['스펠점수']}점 (60점 미만 - 즉시 빌런)")
                
                # 미통과 과목 카운트
                total_subjects = 0
                fail_count = 0
                fail_details = []
                
                if pd.notna(row['어휘점수']):
                    total_subjects += 1
                    if row['어휘점수'] < 94:
                        fail_count += 1
                        fail_details.append(f"어휘 {row['어휘점수']}점 < 94점")
                
                if pd.notna(row['스펠점수']):
                    total_subjects += 1
                    if row['스펠점수'] < 90:
                        fail_count += 1
                        fail_details.append(f"스펠 {row['스펠점수']}점 < 90점")
                
                if pd.notna(row['독해점수']):
                    total_subjects += 1
                    if row['독해점수'] < 80:
                        fail_count += 1
                        fail_details.append(f"독해 {row['독해점수']}점 < 80점")
                
                # 2개 이상 미통과 체크
                if fail_count >= 2:
                    reasons.append(f"💀 {total_subjects}과목 중 {fail_count}과목 미통과 ({', '.join(fail_details)})")
                
                st.markdown(f"**{row['이름']}**{attendance_mark}: {' | '.join(reasons)}")
        else:
            st.info("빌런 판정된 학생이 없습니다.")
    
    # 자동 새로고침
    auto_refresh = st.checkbox("자동 새로고침 (10초)", value=False)
    if auto_refresh:
        time.sleep(10)
        st.rerun()

if __name__ == "__main__":
    main()# 빌런 판정 함수
def is_villain(row):
    """빌런 조건: 어휘<80 OR 스펠<60 OR (점수 있는 과목 중 2개 이상 미통과)"""
    if row['출석'] != '출석':
        return False
    
    # 점수가 하나도 없으면 내신으로 분류 (빌런 아님)
    if pd.isna(row['어휘점수']) and pd.isna(row['스펠점수']) and pd.isna(row['독해점수']):
        return False
    
    # 즉시 빌런 조건 1: 어휘 < 80점
    if pd.notna(row['어휘점수']) and row['어휘점수'] < 80:
        return True
    
    # 즉시 빌런 조건 2: 스펠 < 60점
    if pd.notna(row['스펠점수']) and row['스펠점수'] < 60:
        return True
    
    # 조건 3: 점수가 있는 과목 중 2개 이상 미통과
    # 점수가 있는 과목과 미통과 과목을 따로 카운트
    total_subjects = 0  # 점수가 기록된 과목 수
    fail_count = 0      # 미통과 과목 수
    
    # 어휘 체크 (기준: 94점)
    if pd.notna(row['어휘점수']):
        total_subjects += 1
        if row['어휘점수'] < 94:
            fail_count += 1
    
    # 스펠 체크 (기준: 90점)
    if pd.notna(row['스펠점수']):
        total_subjects += 1
        if row['스펠점수'] < 90:
            fail_count += 1
    
    # 독해 체크 (기준: 80점)
    if pd.notna(row['독해점수']):
        total_subjects += 1
        if row['독해점수'] < 80:
            fail_count += 1
    
    # 2개 이상 미통과면 빌런
    # (2과목만 있고 2과목 미통과도 빌런, 3과목 있고 2개 이상 미통과도 빌런)
    return fail_count >= 2



