# main.py 파일 - 이 전체 코드를 복사하세요!

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime
import time

# 페이지 설정 - TV 전체화면용
st.set_page_config(
    page_title="학원 통과 현황",
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
    </style>
""", unsafe_allow_html=True)

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime
import time

# google_sheets.py import 추가
try:
    from google_sheets import load_data_from_sheets, get_test_data
    GOOGLE_SHEETS_AVAILABLE = True
except ImportError:
    GOOGLE_SHEETS_AVAILABLE = False
    st.warning("google_sheets.py 파일이 없습니다. 테스트 데이터를 사용합니다.")

# 페이지 설정 - TV 전체화면용
st.set_page_config(
    page_title="학원 통과 현황",
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
    </style>
""", unsafe_allow_html=True)

# 구글시트 URL 설정 (여기에 실제 URL 입력!)
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1qW6Cs4FaSp-kEsSDFAyUw0hWzaTVBsSn9WeU8ZW_vd4/edit?gid=368136260#gid=368136260"  # 여기를 수정하세요!
SHEET_NAME = "성적데이터"  # 시트 탭 이름

# 데이터 로드 함수
@st.cache_data(ttl=10)  # 10초마다 새로고침
def load_data():
    """구글시트 또는 테스트 데이터 로드"""
    
    # 구글시트 연동 시도
    if GOOGLE_SHEETS_AVAILABLE and not GOOGLE_SHEET_URL.endswith("YOUR_SHEET_ID/edit"):
        df = load_data_from_sheets(GOOGLE_SHEET_URL, SHEET_NAME)
        if df is not None and not df.empty:
            st.success("✅ 구글시트 연결 성공!")
            return df
    
    # 구글시트 연동 실패시 테스트 데이터
    st.info("📌 테스트 데이터를 사용 중입니다. 구글시트를 연결하려면:")
    st.code("""
1. credentials.json 파일을 현재 폴더에 넣기
2. main.py의 GOOGLE_SHEET_URL 수정
3. 구글시트에 서비스 계정 이메일 공유
    """)
    
    # 테스트 데이터 반환
    if GOOGLE_SHEETS_AVAILABLE:
        return get_test_data()
    else:
        # google_sheets.py가 없을 때 기본 테스트 데이터
        data = {
            '날짜': ['2025-05-25'] * 30 + ['2025-05-24'] * 30 + ['2025-05-23'] * 30,
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
            '출석': ['출석', '출석', '출석', '출석', '출석',
                    '출석', '출석', '출석', '출석', '출석',
                    '결석', '출석', '결석', '결석', '결석',
                    '출석', '출석', '출석', '출석', '출석',
                    '출석', '결석', '출석', '출석', '출석',
                    '출석', '출석', '출석', '출석', '출석'] * 3,
            '어휘점수': [87, 100, 97, 92, 88,
                       92, 100, 98, 100, 100,
                       None, 86, None, None, None,
                       94, 98, 96, 94, 92,
                       46, None, 97.5, 96, 98,
                       82, 94, None, 100, 100] * 3,
            '스펠점수': [55, 100, 83, 78, 84,
                       50, 68, 90, 88, 90,
                       None, 48, None, None, None,
                       90, 90, 88, 85, 80,
                       22.5, None, 97.5, 82.5, 87.5,
                       80, 82.5, None, 100, 85] * 3,
            '독해점수': [80, 85, 53, 69, 88,
                       56, 58, 86, 84, 86,
                       None, 73, None, None, None,
                       80, 99, 99, 77, 90,
                       99, None, 100, 77.8, 92.5,
                       93.6, 99, None, 88, 96] * 3
        }
        df = pd.DataFrame(data)
        return df

# 학생 상태 분류 함수
def classify_student(row):
    """학생 상태 분류: normal, midterm, absent"""
    if row['출석'] == '결석':
        return 'absent'
    elif pd.isna(row['어휘점수']) and pd.isna(row['스펠점수']) and pd.isna(row['독해점수']):
        return 'midterm'
    else:
        return 'normal'

# 영웅 효과 추가 함수
def add_hero_effect(fig, row, x_base):
    """어휘+스펠 100점 영웅 효과"""
    # 무지개 그라디언트 막대 - 어휘
    fig.add_trace(go.Bar(
        x=[x_base],
        y=[100],
        width=0.7,
        marker=dict(
            color=[100],
            colorscale='Rainbow',
            cmin=0, cmax=100,
            showscale=False,
            line=dict(color='gold', width=3)
        ),
        text='100',
        textposition='inside',
        textfont=dict(size=12, color='white', family='Arial Black'),
        showlegend=False,
        hovertemplate=f"{row['이름']} - 어휘: 100점<extra></extra>"
    ))
    
    # 무지개 그라디언트 막대 - 스펠
    fig.add_trace(go.Bar(
        x=[x_base + 0.8],
        y=[100],
        width=0.7,
        marker=dict(
            color=[100],
            colorscale='Turbo',
            cmin=0, cmax=100,
            showscale=False,
            line=dict(color='gold', width=3)
        ),
        text='100',
        textposition='inside',
        textfont=dict(size=12, color='white', family='Arial Black'),
        showlegend=False,
        hovertemplate=f"{row['이름']} - 스펠: 100점<extra></extra>"
    ))
    
    # "영웅출현" 텍스트
    fig.add_annotation(
        text="<b>영웅출현</b>",
        x=x_base + 0.8,
        y=108,
        showarrow=False,
        font=dict(size=14, color='red', family='Arial Black'),
        bgcolor='yellow',
        bordercolor='red',
        borderwidth=2
    )
    
    # 독해 점수 (일반 막대지만 금테두리)
    if pd.notna(row['독해점수']):
        color = '#00C851' if row['독해점수'] >= 80 else '#FF4444'
        fig.add_trace(go.Bar(
            x=[x_base + 1.6],
            y=[row['독해점수']],
            width=0.7,
            marker=dict(
                color=color,
                line=dict(color='gold', width=2)
            ),
            text=str(int(row['독해점수'])),
            textposition='auto',
            textfont=dict(size=10, color='white'),
            showlegend=False,
            hovertemplate=f"{row['이름']} - 독해: {row['독해점수']}점<extra></extra>"
        ))

# 일반 막대 추가 함수
def add_normal_bars(fig, row, x_base):
    """일반 학생 막대 추가"""
    subjects = [
        ('어휘점수', 94, x_base),
        ('스펠점수', 80, x_base + 0.8),
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
                hovertemplate=f"{row['이름']} - {subject[:-2]}: {score}점<extra></extra>"
            ))

# 내신 미니차트 추가 함수
def add_midterm_section(fig, midterm_df, start_x):
    """내신 학생들 미니차트"""
    if len(midterm_df) == 0:
        return
    
    # 내신 구간 배경
    fig.add_vrect(
        x0=start_x - 0.5,
        x1=start_x + len(midterm_df) * 3,
        fillcolor="rgba(255, 235, 150, 0.1)",
        layer="below",
        line_width=0
    )
    
    # 내신 텍스트 표시
    for idx, (_, row) in enumerate(midterm_df.iterrows()):
        x_pos = start_x + idx * 3
        
        # 내신 표시 (빗금 패턴)
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
                hovertemplate=f"{row['이름']} - 내신기간<extra></extra>"
            ))

# 메인 대시보드 생성 함수
def create_dashboard(selected_date):
    """전체 대시보드 생성"""
    df = load_data()
    
    # 선택한 날짜 데이터만 필터링
    today_df = df[df['날짜'] == selected_date].copy()
    
    if len(today_df) == 0:
        st.warning(f"{selected_date}에 해당하는 데이터가 없습니다.")
        return None, None
    
    # 학생 상태 분류
    today_df['status'] = today_df.apply(classify_student, axis=1)
    
    # 그룹별 분리 및 정렬
    class_order = {'초등': 1, '중등': 2, '수능': 3}
    
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
    
    # 1. 정상 응시자 처리
    for idx, (_, row) in enumerate(normal_df.iterrows()):
        x_base = idx * 2.5  # 간격 조정
        
        # 학생별 3개 막대를 감싸는 테두리
        fig.add_shape(
            type="rect",
            x0=x_base - 0.4, 
            x1=x_base + 2.0,
            y0=0, 
            y1=105,
            line=dict(
                color="rgba(100, 100, 100, 0.3)",  # 연한 회색 테두리
                width=2
            ),
            fillcolor="rgba(0,0,0,0)",  # 투명 배경
            layer="below"
        )
        
        # 영웅 체크
        if row['어휘점수'] == 100 and row['스펠점수'] == 100:
            add_hero_effect(fig, row, x_base)
        else:
            add_normal_bars(fig, row, x_base)
    
    # 2. 내신 구간
    midterm_start = len(normal_df) * 2.5 + 1
    add_midterm_section(fig, midterm_df, midterm_start)
    
    # 3. 결석 구간 배경
    absent_start = midterm_start + len(midterm_df) * 3 + 1
    if len(absent_df) > 0:
        fig.add_vrect(
            x0=absent_start - 0.5,
            x1=absent_start + len(absent_df) * 3,
            fillcolor="rgba(128, 128, 128, 0.1)",
            layer="below",
            line_width=0
        )
    
    # 기준선 추가
    fig.add_hline(y=94, line_dash="dash", line_color="rgba(255,0,0,0.3)",
                  annotation_text="어휘 기준 94점", annotation_position="right")
    fig.add_hline(y=80, line_dash="dash", line_color="rgba(0,0,255,0.3)",
                  annotation_text="스펠/독해 기준 80점", annotation_position="right")
    
    # 이름 리스트 생성
    all_names = []
    all_colors = []
    tick_positions = []
    
    # 정상 응시자
    for idx, (_, row) in enumerate(normal_df.iterrows()):
        all_names.append(row['이름'])
        tick_positions.append(idx * 2.5 + 0.8)
        # 반별 색상
        if row['반'] == '초등':
            all_colors.append('#4A90E2')
        elif row['반'] == '중등':
            all_colors.append('#F5A623')
        else:
            all_colors.append('#BD10E0')
    
    # 내신
    for idx, (_, row) in enumerate(midterm_df.iterrows()):
        all_names.append(row['이름'])
        tick_positions.append(midterm_start + idx * 3 + 0.8)
        all_colors.append('orange')
    
    # 결석
    for idx, (_, row) in enumerate(absent_df.iterrows()):
        all_names.append(row['이름'])
        tick_positions.append(absent_start + idx * 3 + 0.8)
        all_colors.append('gray')
    
    # 레이아웃 설정
    fig.update_layout(
        title={
            'text': f"<b>통과 현황 - {selected_date}</b>",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 24, 'color': 'black'}
        },
        height=900,  # TV 높이에 맞춤
        margin=dict(l=60, r=60, t=100, b=150),
        xaxis=dict(
            ticktext=all_names,
            tickvals=tick_positions,
            tickfont=dict(size=11),
            tickangle=0
        ),
        yaxis=dict(
            range=[0, 115],
            title=dict(
                text="점수",
                font=dict(size=14)
            ),
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
    fig.add_vline(x=midterm_start - 0.5, line_dash="dot", line_color="gray", opacity=0.3)
    if len(absent_df) > 0:
        fig.add_vline(x=absent_start - 0.5, line_dash="dot", line_color="gray", opacity=0.3)
    
    # 요약 정보
    summary_text = f"""
    <div style='text-align: center; padding: 10px; background: white; border-radius: 5px;'>
    <b>정상응시: {len(normal_df)}명 | 내신: {len(midterm_df)}명 | 결석: {len(absent_df)}명</b><br>
    <span style='color: green'>통과: {sum((normal_df['어휘점수'] >= 94) & (normal_df['스펠점수'] >= 80) & (normal_df['독해점수'] >= 80))}명</span> | 
    <span style='color: red'>재시험: {len(normal_df) - sum((normal_df['어휘점수'] >= 94) & (normal_df['스펠점수'] >= 80) & (normal_df['독해점수'] >= 80))}명</span>
    </div>
    """
    
    return fig, summary_text

# Streamlit 앱 메인
def main():
    # 타이틀
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1 style='text-align: center;'>📊 학원 통과 현황</h1>", unsafe_allow_html=True)
    
    # 날짜 선택 위젯
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # 가능한 날짜 목록 가져오기
        df = load_data()
        
        # 날짜 데이터 정리 (NaN 제거, 문자열 변환)
        if '날짜' in df.columns:
            # NaN 제거하고 문자열로 변환
            df['날짜'] = df['날짜'].astype(str)
            df = df[df['날짜'] != 'nan']
            df = df[df['날짜'] != '']
            
            available_dates = sorted(df['날짜'].unique())
            
            if len(available_dates) == 0:
                st.error("날짜 데이터가 없습니다. 구글시트를 확인하세요.")
                return
        else:
            st.error("'날짜' 컬럼이 없습니다. 구글시트 헤더를 확인하세요.")
            return
        
        # 날짜 선택 박스
        selected_date = st.selectbox(
            "날짜 선택:",
            options=available_dates,
            index=len(available_dates)-1,  # 기본값: 최신 날짜
            format_func=lambda x: x  # 날짜 포맷 (필요시 수정)
        )
    
    # 대시보드 생성 (선택한 날짜 전달)
    fig, summary = create_dashboard(selected_date)
    
    # 데이터가 있는 경우에만 표시
    if fig is not None:
        # 그래프 표시
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        # 요약 정보 표시
        st.markdown(summary, unsafe_allow_html=True)
    
    # 자동 새로고침 체크박스
    auto_refresh = st.checkbox("자동 새로고침 (10초)", value=False)
    if auto_refresh:
        time.sleep(10)
        st.rerun()

if __name__ == "__main__":
    main()