import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------
# Firebase 설정
# ---------------------
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# ---------------------
# 세션 상태 초기화
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# ---------------------
# 홈 페이지 클래스
# ---------------------
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Home")
        if st.session_state.get("logged_in"):
            st.success(f"{st.session_state.get('user_email')}님 환영합니다.")

        st.markdown("""
            ---
            **인구 추세 (Population Trends) 데이터셋**  
            - 출처: 통계청 또는 공공 데이터 포털  
            - 설명: 연도별, 시도별 총인구 및 남녀 인구 수를 포함한 인구 변화 추이 데이터  
            - 주요 변수:
              - `연도`: 해당 인구 데이터가 수집된 연도  
              - `시도`: 행정구역(예: 서울특별시, 부산광역시 등)  
              - `총인구수`: 해당 지역의 전체 인구 수  
              - `남자`: 남성 인구 수  
              - `여자`: 여성 인구 수
        """)

# ---------------------
# 로그인 페이지 클래스
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인 성공!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("로그인 실패")

# ---------------------
# 회원가입 페이지 클래스
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("성명")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대전화번호")

        if st.button("회원가입"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("회원가입 실패")

# ---------------------
# 비밀번호 찾기 페이지 클래스
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기")
        email = st.text_input("이메일")
        if st.button("비밀번호 재설정 메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 전송했습니다.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("이메일 전송 실패")

# ---------------------
# 사용자 정보 수정 페이지 클래스
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")

        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별",
            ["선택 안함", "남성", "여성"],
            index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함"))
        )
        phone = st.text_input("휴대전화번호", value=st.session_state.get("user_phone", ""))

        uploaded_file = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("수정"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone

            firestore.child("users").child(new_email.replace(".", "_")).update({
                "email": new_email,
                "name": name,
                "gender": gender,
                "phone": phone,
                "profile_image_url": st.session_state.get("profile_image_url", "")
            })

            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1)
            st.rerun()

# ---------------------
# 로그아웃 페이지 클래스
# ---------------------
class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()

# ---------------------
# EDA 페이지 클래스
# ---------------------
class EDA:
    def __init__(self):
        st.title("📊 Population Trends EDA")

        uploaded_file = st.file_uploader("Upload population_trends.csv", type="csv")
        if not uploaded_file:
            st.info("Please upload population_trends.csv file")
            return

        df = pd.read_csv(uploaded_file)
        df.replace('-', 0, inplace=True)
        df[['인구', '출생아수(명)', '사망자수(명)']] = df[['인구', '출생아수(명)', '사망자수(명)']].apply(
            pd.to_numeric, errors='coerce').fillna(0).astype(int)

        df = df[df['지역'] != '전국'].copy()
        df['diff'] = df.sort_values(['지역', '연도']).groupby('지역')['인구'].diff()

        region_en = {
            "서울": "Seoul", "부산": "Busan", "대구": "Daegu", "인천": "Incheon",
            "광주": "Gwangju", "대전": "Daejeon", "울산": "Ulsan", "세종": "Sejong",
            "경기": "Gyeonggi", "강원": "Gangwon", "충북": "Chungbuk", "충남": "Chungnam",
            "전북": "Jeonbuk", "전남": "Jeonnam", "경북": "Gyeongbuk", "경남": "Gyeongnam",
            "제주": "Jeju"
        }
        df['region_en'] = df['지역'].map(region_en)

        tabs = st.tabs(["📌 Basic Stats", "📈 Yearly Trend", "🏙️ Regional Analysis", "🔄 Change Analysis", "🗺️ Visualization"])

        with tabs[0]:
            st.header("📌 Basic Statistics")
            buffer = io.StringIO()
            df.info(buf=buffer)
            st.text(buffer.getvalue())
            st.dataframe(df.describe())

        with tabs[1]:
            st.header("📈 Yearly Population Trend (Nationwide)")
            nat = pd.read_csv(uploaded_file)
            nat.replace('-', 0, inplace=True)
            nat[['인구', '출생아수(명)', '사망자수(명)']] = nat[['인구', '출생아수(명)', '사망자수(명)']].apply(pd.to_numeric, errors='coerce').fillna(0).astype(int)
            national = nat[nat['지역'] == '전국'].copy().sort_values('연도')
            recent = national.tail(3)
            net = recent['출생아수(명)'].mean() - recent['사망자수(명)'].mean()
            pred = int(national['인구'].iloc[-1] + net * (2035 - national['연도'].iloc[-1]))
            fig, ax = plt.subplots()
            ax.plot(national['연도'], national['인구'], marker='o', label='Actual')
            ax.plot(2035, pred, 'ro', label='Forecast')
            ax.annotate(f"{pred:,}", (2035, pred), textcoords="offset points", xytext=(-30, 10))
            ax.set_title("National Population Forecast")
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")
            ax.legend()
            st.pyplot(fig)

        with tabs[2]:
            st.header("🏙️ Regional Population Change (5 Years)")
            now = df[df['연도'] == df['연도'].max()][['지역', '인구']].set_index('지역')
            past = df[df['연도'] == df['연도'].max() - 5][['지역', '인구']].set_index('지역')
            change = now.join(past, lsuffix='_now', rsuffix='_past')
            change['diff'] = (change['인구_now'] - change['인구_past']) // 1000
            change['rate'] = ((change['인구_now'] - change['인구_past']) / change['인구_past'] * 100).round(2)
            change['region_en'] = change.index.map(region_en)
            fig1, ax1 = plt.subplots(figsize=(8, 6))
            sorted_diff = change.sort_values(by='diff', ascending=False)
            sns.barplot(data=sorted_diff, y='region_en', x='diff', ax=ax1, palette='coolwarm')
            ax1.set_title("Population Change (thousands)")
            ax1.set_xlabel("Change")
            for i, v in enumerate(sorted_diff['diff']):
                ax1.text(v + 1 if v > 0 else v - 3, i, f"{v}", va='center')
            st.pyplot(fig1)

            fig2, ax2 = plt.subplots(figsize=(8, 6))
            sorted_rate = change.sort_values(by='rate', ascending=False)
            sns.barplot(data=sorted_rate, y='region_en', x='rate', ax=ax2, palette='Spectral')
            ax2.set_title("Population Growth Rate (%)")
            ax2.set_xlabel("Growth Rate")
            for i, v in enumerate(sorted_rate['rate']):
                ax2.text(v + 0.5 if v > 0 else v - 2, i, f"{v}%", va='center')
            st.pyplot(fig2)

        with tabs[3]:
            st.header("🔄 Top 100 Year-over-Year Population Changes")
            top = df.dropna(subset=['diff']).sort_values(by='diff', ascending=False).head(100)
            view = top[['연도', '지역', '인구', 'diff']].copy()
            view['인구'] = view['인구'].map('{:,}'.format)
            view['diff'] = view['diff'].astype(int).map('{:,}'.format)

            def color_diff(val):
                val = int(val.replace(',', ''))
                return 'background-color: #add8e6' if val > 0 else 'background-color: #f08080'

            styled = view.style.applymap(color_diff, subset=['diff'])
            st.dataframe(styled, use_container_width=True)

        with tabs[4]:
            st.header("🗺️ Stacked Area Chart by Region")
            pivot = df.pivot_table(index='연도', columns='region_en', values='인구', aggfunc='sum').fillna(0) / 1000
            fig3, ax3 = plt.subplots(figsize=(12, 6))
            pivot.plot.area(ax=ax3, cmap='tab20')
            ax3.set_title("Regional Population Area Chart")
            ax3.set_xlabel("Year")
            ax3.set_ylabel("Population (thousands)")
            ax3.legend(title="Region", loc='upper left', bbox_to_anchor=(1, 1))
            st.pyplot(fig3)


# ---------------------
# 페이지 객체 생성
# ---------------------
Page_Login    = st.Page(Login,    title="Login",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="Logout",  icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA,      title="EDA",     icon="📊", url_path="eda")

# ---------------------
# 네비게이션 실행
# ---------------------
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()