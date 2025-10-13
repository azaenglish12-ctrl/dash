# google_sheets.py
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import streamlit as st
import os

# 구글시트 API 권한 범위
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

@st.cache_resource
def init_google_sheets():
    """구글시트 연결 초기화"""
    try:
        # Streamlit Cloud에서 실행 중인지 확인
        if "gcp_service_account" in st.secrets:
            # Streamlit Cloud - Secrets 사용
            creds = Credentials.from_service_account_info(
                st.secrets["gcp_service_account"],
                scopes=SCOPES
            )
            client = gspread.authorize(creds)
            return client
        else:
            # 로컬 - credentials.json 사용
            try:
                creds = Credentials.from_service_account_file(
                    'credentials.json',
                    scopes=SCOPES
                )
                client = gspread.authorize(creds)
                return client
            except FileNotFoundError:
                st.error("credentials.json 파일을 찾을 수 없습니다!")
                return None
                
    except Exception as e:
        st.error(f"구글시트 연결 실패: {e}")
        st.info("Secrets 설정을 확인하세요.")
        return None

@st.cache_data(ttl=10)  # 10초마다 캐시 갱신 
def load_data_from_sheets(sheet_url, worksheet_name="시트1"):
    """구글시트에서 데이터 로드"""
    try:
        client = init_google_sheets()
        if not client:
            return None
        
        # URL에서 시트 열기
        sheet = client.open_by_url(sheet_url)
        
        # 워크시트 선택
        worksheet = sheet.worksheet(worksheet_name)
        
        # 모든 데이터 가져오기
        data = worksheet.get_all_records()
        
        # DataFrame으로 변환
        df = pd.DataFrame(data)
        
        # 빈 문자열을 None으로 변환
        df = df.replace('', None)
        
        # 숫자 컬럼 변환
        numeric_columns = ['어휘점수', '스펠점수', '독해점수']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 날짜 형식 통일 (필요시)
        if '날짜' in df.columns:
            # 빈 문자열과 NaN 제거
            df = df[df['날짜'].notna()]
            df = df[df['날짜'] != '']
            
            # 날짜를 문자열로 변환 (YYYY-MM-DD 형식 유지)
            df['날짜'] = df['날짜'].astype(str).str.strip()
            
            # 엑셀 날짜 숫자 처리 (44000 같은 숫자를 날짜로 변환)
            try:
                # 숫자로 된 날짜가 있는지 확인
                numeric_dates = pd.to_numeric(df['날짜'], errors='coerce')
                if numeric_dates.notna().any():
                    # 엑셀 날짜 변환 (1900-01-01 기준)
                    df.loc[numeric_dates.notna(), '날짜'] = pd.to_datetime('1899-12-30') + pd.to_timedelta(numeric_dates[numeric_dates.notna()], 'D')
                    df['날짜'] = pd.to_datetime(df['날짜']).dt.strftime('%Y-%m-%d')
            except:
                pass
        
        return df
        
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        st.info("시트 URL과 시트명을 확인하세요.")
        return None

def get_test_data():
    """연결 실패시 테스트 데이터"""
    data = {
        '날짜': ['2025-05-25'] * 10,
        '이름': ['이민규', '박진건', '권라임', '이선우', '박연우',
                '오윤성', '박정현', '김단율', '이준서', '민준원'],
        '반': ['초등', '초등', '중등', '중등', '중등',
              '중등', '중등', '중등', '중등', '수능'],
        '출석': ['출석', '출석', '출석', '출석', '출석',
                '출석', '출석', '결석', '출석', '결석'],
        '어휘점수': [87, 100, 92, 100, 98, 100, 100, None, 86, None],
        '스펠점수': [55, 100, 50, 68, 90, 88, 90, None, 48, None],
        '독해점수': [80, 85, 56, 58, 86, 84, 86, None, 73, None]
    }
    return pd.DataFrame(data)
