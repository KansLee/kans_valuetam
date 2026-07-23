import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import altair as alt
from io import StringIO
import requests
import concurrent.futures

# 페이지 기본 설정
st.set_page_config(page_title="S&P 500 Valuation Pro (Personal Master)", layout="wide")
st.title("📊 ValueTam")
st.write("Made by Kans Lee 2026.07.21")

# ---------------------------------------------------------
# 1. 한글-영문 병기 사전 및 표준 정렬 순서 (FCF 삭제 완료)
# ---------------------------------------------------------
IS_TRANSLATIONS = {
    "Total Revenue": "총매출액 (Total Revenue) ★ 기준 100%",
    "Total Net Revenue": "★ 총순수익 (Total Net Revenue) ★ 기준 100%",
    "Operating Revenue": "영업수익 (Operating Revenue) ★ 기준 100%",
    "Net Interest Income": "순이자수익 (Net Interest Income)",
    "Cost Of Revenue": "매출원가 (Cost of Revenue)",
    "Gross Profit": "매출총이익 (Gross Profit)",
    "Provision For Loan Lease And Other Losses": "대손충당금 (Provision for Losses)",
    "Operating Expense": "영업비용 (Operating Expense)",
    "Operating Income": "영업이익 (Operating Income)",
    "Pretax Income": "세전이익 (Pretax Income)",
    "Tax Provision": "법인세비용 (Tax Provision)",
    "Net Income Common Stockholders": "보통주 귀속 당기순이익",
    "Net Income Continuous Operations": "계속영업 당기순이익",
    "Net Income": "★ 당기순이익 (Net Income)",
    "Basic EPS": "기본 주당순이익 (Basic EPS)",
    "Diluted EPS": "★ 희석 주당순이익 (Diluted EPS)",
}

IS_ORDER = [
    "Total Revenue", "Total Net Revenue", "Operating Revenue", "Net Interest Income",
    "Cost Of Revenue", "Gross Profit", "Provision For Loan Lease And Other Losses",
    "Operating Expense", "Operating Income", "Pretax Income",
    "Tax Provision", "Net Income Continuous Operations",
    "Net Income Common Stockholders", "Net Income", "Basic EPS", "Diluted EPS",
]

BS_TRANSLATIONS = {
    "Total Assets": "🔹 [자산] 총자산 (Total Assets) ★ 기준 100%",
    "Current Assets": "🔹 [자산] 유동자산 (Current Assets)",
    "Cash And Cash Equivalents": "🔹 [자산] 현금및현금성자산 (Cash Equivalents)",
    "Total Non Current Assets": "🔹 [자산] 비유동자산 (Non-Current Assets)",
    "Total Liabilities Net Minority Interest": "🔸 [부채] 총부채 (Total Liabilities)",
    "Total Liabilities": "🔸 [부채] 총부채 (Total Liabilities)",
    "Total Debt": "🔸 [부채] 총차입금 (Total Debt)",
    "Current Liabilities": "🔸 [부채] 유동부채 (Current Liabilities)",
    "Total Stockholder Equity": "💎 [자본] 총자기자본 (Total Equity)",
    "Stockholders Equity": "💎 [자본] 주주지분 (Stockholders Equity)",
    "Common Stock Equity": "💎 [자본] 보통주 자본 (Common Equity)",
    "Retained Earnings": "💎 [자본] 이익잉여금 (Retained Earnings)",
    "Preferred Stock": "💎 [자본] 우선주 (Preferred Stock)",
    "Working Capital": "📌 [기타] 순운전자본 (Working Capital)",
    "Invested Capital": "📌 [기타] 투하자본 (Invested Capital)",
    "Net Debt": "📌 [기타] 순차입금 (Net Debt)",
}

BS_ORDER = [
    "Total Assets", "Current Assets", "Cash And Cash Equivalents", "Total Non Current Assets",
    "Total Liabilities Net Minority Interest", "Total Liabilities", "Total Debt", "Current Liabilities",
    "Total Stockholder Equity", "Stockholders Equity", "Common Stock Equity", "Retained Earnings",
    "Working Capital", "Invested Capital", "Net Debt",
]

CF_TRANSLATIONS = {
    "Operating Cash Flow": "🔹 [영업] 영업활동 현금흐름 (OCF) ★ 기준 100%",
    "Cash Flow From Continuing Operating Activities": "🔹 [영업] 계속영업 현금흐름 (OCF) ★ 기준 100%",
    "Net Income From Continuing Operations": "🔹 [영업] 계속영업 당기순이익",
    "Depreciation And Amortization In Cash Flow": "🔹 [영업] 감가상각비 (D&A)",
    "Change In Working Capital": "🔹 [영업] 순운전자본 변동",
    "Investing Cash Flow": "🔸 [투자] 투자활동 현금흐름",
    "Cash Flow From Continuing Investing Activities": "🔸 [투자] 투자활동 현금흐름",
    "Capital Expenditure": "🔸 [투자] 자본지출 (CapEx)",
    "Net Other Investing Changes": "🔸 [투자] 기타 투자 활동",
    "Financing Cash Flow": "💎 [재무] 재무활동 현금흐름",
    "Cash Flow From Continuing Financing Activities": "💎 [재무] 재무활동 현금흐름",
    "Common Stock Dividend Paid": "💎 [재무] 배당금 지급",
    "Repayment Of Debt": "💎 [재무] 차입금 상환",
    "Issuance Of Debt": "💎 [재무] 차입금 조달",
    "Repurchase Of Capital Stock": "💎 [재무] ★ 자사주 매입 (Repurchase)",
}

CF_ORDER = [
    "Operating Cash Flow", "Cash Flow From Continuing Operating Activities", "Net Income From Continuing Operations",
    "Depreciation And Amortization In Cash Flow", "Change In Working Capital", "Investing Cash Flow",
    "Cash Flow From Continuing Investing Activities", "Capital Expenditure", "Net Other Investing Changes",
    "Financing Cash Flow", "Cash Flow From Continuing Financing Activities", "Common Stock Dividend Paid",
    "Repayment Of Debt", "Issuance Of Debt", "Repurchase Of Capital Stock",
]

# ---------------------------------------------------------
# 2. 기업 및 종목 설정 (미국 주식 시가총액 상위 100대 한글 인기 목록)
# ---------------------------------------------------------
POPULAR_KOR = {
    "컴캐스트 (CMCSA) ★": "CMCSA",
    "애플 (AAPL)": "AAPL",
    "마이크로소프트 (MSFT)": "MSFT",
    "엔비디아 (NVDA)": "NVDA",
    "구글 (GOOGL)": "GOOGL",
    "아마존 (AMZN)": "AMZN",
    "메타 플랫폼스 (META)": "META",
    "테슬라 (TSLA)": "TSLA",
    "버크셔 해서웨이 (BRK-B)": "BRK-B",
    "JP모건 체이스 (JPM)": "JPM",
    "일라이 릴리 (LLY)": "LLY",
    "브로드컴 (AVGO)": "AVGO",
    "유나이티드헬스 그룹 (UNH)": "UNH",
    "비자 (V)": "V",
    "엑슨모빌 (XOM)": "XOM",
    "마스터카드 (MA)": "MA",
    "코스트코 홀세일 (COST)": "COST",
    "존슨앤존슨 (JNJ)": "JNJ",
    "홈디포 (HD)": "HD",
    "프로터 앤 갬블 (PG)": "PG",
    "넷플릭스 (NFLX)": "NFLX",
    "애브비 (ABBV)": "ABBV",
    "세일즈포스 (CRM)": "CRM",
    "셰브론 (CVX)": "CVX",
    "오라클 (ORCL)": "ORCL",
    "뱅크 오브 아메리카 (BAC)": "BAC",
    "코카콜라 (KO)": "KO",
    "펩시코 (PEP)": "PEP",
    "맥도날드 (MCD)": "MCD",
    "월마트 (WMT)": "WMT",
    "머크 (MRK)": "MRK",
    "어도비 (ADBE)": "ADBE",
    "웰스 파고 (WFC)": "WFC",
    "린데 (LIN)": "LIN",
    "어드밴스드 마이크로 디바이스 (AMD)": "AMD",
    "시스코 시스템즈 (CSCO)": "CSCO",
    "액센츄어 (ACN)": "ACN",
    "화이자 (PFE)": "PFE",
    "모건스탠리 (MS)": "MS",
    "제너럴 일렉트릭 (GE)": "GE",
    "아메리칸 익스프레스 (AXP)": "AXP",
    "우버 테크놀로지스 (UBER)": "UBER",
    "디즈니 (DIS)": "DIS",
    "골드만삭스 (GS)": "GS",
    "버라이즌 커뮤니케이션스 (VZ)": "VZ",
    "필립 모리스 (PM)": "PM",
    "인텔 (INTC)": "INTC",
    "텍사스 인스트루먼트 (TXN)": "TXN",
    "캐터필러 (CAT)": "CAT",
    "암젠 (AMGN)": "AMGN",
    "아이비엠 (IBM)": "IBM",
    "퀄컴 (QCOM)": "QCOM",
    "나이키 (NKE)": "NKE",
    "보잉 (BA)": "BA",
    "유니언 퍼시픽 (UNP)": "UNP",
    "인튜이트 (INTU)": "INTU",
    "어플라이드 머티어리얼즈 (AMAT)": "AMAT",
    "로우스 (LOW)": "LOW",
    "에스피 글로벌 (SPGI)": "SPGI",
    "스타벅스 (SBUX)": "SBUX",
    "록히드 마틴 (LMT)": "LMT",
    "허니웰 (HON)": "HON",
    "메드트로닉 (MDT)": "MDT",
    "디스 (MCO)": "MCO",
    "램 리서치 (LRCX)": "LRCX",
    "블랙록 (BLK)": "BLK",
    "핀듀오듀오 (PDD)": "PDD",
    "티모바일 US (TMUS)": "TMUS",
    "브리스톨 마이어스 스큅 (BMY)": "BMY",
    "에이티앤티 (T)": "T",
    "길리어드 사이언스 (GILD)": "GILD",
    "씨티그룹 (C)": "C",
    "아메리칸 타워 (AMT)": "AMT",
    "아나로그 디바이스 (ADI)": "ADI",
    "제너럴 다이내믹스 (GD)": "GD",
    "써모 피셔 사이언티픽 (TMO)": "TMO",
    "시카고 상업거래소 (CME)": "CME",
    "인튜이티브 서지컬 (ISRG)": "ISRG",
    "찰스 슈왑 (SCHW)": "SCHW",
    "듀크 에너지 (DUK)": "DUK",
    "에어비앤비 (ABNB)": "ABNB",
    "팔란티어 테크놀로지스 (PLTR)": "PLTR",
    "마이크론 테크놀로지 (MU)": "MU",
    "클라우드플레어 (NET)": "NET",
    "스노우플레이크 (SNOW)": "SNOW",
    "크라우드스트라이크 (CRWD)": "CRWD",
    "서비스나우 (NOW)": "NOW",
    "팔로알토 네트웍스 (PANW)": "PANW",
    "부킹 홀딩스 (BKNG)": "BKNG",
    "일렉트로닉 아츠 (EA)": "EA",
    "몬스터 베버리지 (MNST)": "MNST",
    "페이팔 홀딩스 (PYPL)": "PYPL",
    "타깃 (TGT)": "TGT",
    "포드 모터 (F)": "F",
    "제너럴 모터스 (GM)": "GM",
    "델 테크놀로지스 (DELL)": "DELL",
    "슈퍼 마이크로 컴퓨터 (SMCI)": "SMCI",
    "쿠팡 (CPNG)": "CPNG",
    "로블록스 (RBLX)": "RBLX"
}

# ---------------------------------------------------------
# 3. Altair 차트 렌더링 함수
# ---------------------------------------------------------
def draw_annual_chart(df, title, y_col, color_hex="#1f77b4"):
    st.markdown(f"#### {title}")
    df_reset = df.reset_index()
    date_col = df_reset.columns[0]
    
    chart = alt.Chart(df_reset).mark_line(color=color_hex).encode(
        x=alt.X(f'{date_col}:T', axis=alt.Axis(format='%Y', title='', tickCount=5)),
        y=alt.Y(f'{y_col}:Q', title=y_col, scale=alt.Scale(zero=False)),
        tooltip=[alt.Tooltip(f'{date_col}:T', format='%Y-%m', title='날짜'), alt.Tooltip(f'{y_col}:Q', format=',.2f', title=y_col)]
    )
    st.altair_chart(chart, use_container_width=True)

def draw_small_factor_chart(df, y_col, color_hex="#1f77b4"):
    df_reset = df.reset_index()
    date_col = df_reset.columns[0]
    
    chart = alt.Chart(df_reset).mark_line(color=color_hex, strokeWidth=2.2).encode(
        x=alt.X(f'{date_col}:T', axis=alt.Axis(format='%y.%m', title='', tickCount=3, grid=False)),
        y=alt.Y(f'{y_col}:Q', axis=alt.Axis(title='', tickCount=3), scale=alt.Scale(zero=False)),
        tooltip=[alt.Tooltip(f'{date_col}:T', format='%Y-%m', title='날짜'), alt.Tooltip(f'{y_col}:Q', format=',.2f', title=y_col)]
    ).properties(
        height=140,
        title=alt.TitleParams(text=y_col, fontSize=13, fontWeight='bold', anchor='start', color='#2c3e50', offset=15),
        padding={"top": 15, "bottom": 5, "left": 5, "right": 5}
    ).configure_view(
        strokeWidth=0
    )
    st.altair_chart(chart, use_container_width=True)

# ---------------------------------------------------------
# 4. S&P 500 리스트 동기화 및 세션 스테이트 초기화
# ---------------------------------------------------------
@st.cache_data(ttl=86400)
def get_sp500_full_list():
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=5)
        tables = pd.read_html(StringIO(response.text))
        df = tables[0]
        df["Symbol"] = df["Symbol"].str.replace(".", "-", regex=False)
        return df[["Symbol", "Security", "GICS Sector", "GICS Sub-Industry"]]
    except:
        symbols = list(POPULAR_KOR.values())
        return pd.DataFrame({"Symbol": symbols, "Security": symbols, "GICS Sector": ["Information Technology"]*len(symbols), "GICS Sub-Industry": [""]*len(symbols)})

with st.spinner("미국 시가총액 종목 데이터베이스 로딩 중..."):
    sp500_df = get_sp500_full_list()

all_symbols = sp500_df["Symbol"].tolist() if not sp500_df.empty else list(POPULAR_KOR.values())

if "watchlist_widget" not in st.session_state:
    default_watchlist = ["CMCSA", "AAPL", "MSFT", "NVDA", "JPM"]
    valid_defaults = [s for s in default_watchlist if s in all_symbols]
    st.session_state["watchlist_widget"] = valid_defaults
else:
    st.session_state["watchlist_widget"] = [s for s in st.session_state["watchlist_widget"] if s in all_symbols]

if "main_nav_radio" not in st.session_state:
    st.session_state["main_nav_radio"] = "🏢 1. 개별 종목 정밀 터미널"

def toggle_watchlist_callback(ticker):
    current_list = list(st.session_state["watchlist_widget"])
    if ticker in current_list:
        current_list.remove(ticker)
        st.toast(f"🗑️ {ticker} 종목이 관심종목에서 해제되었습니다.", icon="❌")
    else:
        if len(current_list) < 10:
            current_list.append(ticker)
            st.toast(f"✅ {ticker} 종목이 관심종목에 추가되었습니다!", icon="⭐")
        else:
            st.toast("⚠️ 관심종목은 최대 10개까지만 등록 가능합니다.", icon="🚨")
            return
    st.session_state["watchlist_widget"] = current_list

def switch_to_scanner_callback():
    st.session_state["main_nav_radio"] = "⚖️ 2. 관심종목 10대 팩터 비교 스캐너"

# ---------------------------------------------------------
# 5. 좌측 사이드바
# ---------------------------------------------------------
st.sidebar.header("⚙️ 1. 개별 정밀 분석 종목 선택")
list_mode = st.sidebar.radio("📂 선택 방식", ["🔥 시가총액 상위 100 목록", "📋 S&P 500 전체 목록"])

if "상위 100" in list_mode:
    selected_label = st.sidebar.selectbox("목록에서 선택:", options=list(POPULAR_KOR.keys()), index=0)
    final_ticker = POPULAR_KOR[selected_label]
else:
    sp500_df["Display"] = sp500_df.apply(lambda r: f"{r['Symbol']} - {r['Security']}", axis=1)
    default_idx = int(sp500_df[sp500_df["Symbol"] == "CMCSA"].index[0]) if "CMCSA" in sp500_df["Symbol"].values else 0
    selected_val = st.sidebar.selectbox("S&P 500 검색:", options=sp500_df["Display"].tolist(), index=default_idx)
    final_ticker = selected_val.split(" - ")[0].strip()

st.sidebar.divider()
st.sidebar.header("⭐ 2. 관심종목 비교 목록 (최대 10개)")
watchlist_tickers = st.sidebar.multiselect(
    "비교할 종목을 고르세요 (최대 10개):",
    options=all_symbols,
    key="watchlist_widget",
    max_selections=10
)

st.sidebar.divider()
st.sidebar.markdown("### 🎛️ 3. 연산 알고리즘 정밀 제어")
eps_mode = st.sidebar.radio("1️⃣ EPS/손익계산서/현금흐름표 산출방식", ("최근 1년 전체 (직전 4개 분기 합산)", "최근 분기 기준 (가장 최근 분기 × 4배)", "최근 1년 중간값 (4개 분기 중간값 × 4배)"))
bps_mode = st.sidebar.radio("2️⃣ BPS 산출 방식", ("보통주 자본 기준 (우선주 제외 - 표준)", "전체 자본 기준 (우선주 포함)"))

# ---------------------------------------------------------
# 6. 금액/수직비율 전환 포맷터
# ---------------------------------------------------------
def format_financial_table(series, col_name, order_list, trans_dict, mode="amount", base_key=None, sector=None):
    excluded_keys = []
    
    if order_list == IS_ORDER:
        excluded_keys.append("EBITDA")

    is_financial = sector in ["Financials", "Financial Services", "Financial"] or "Financial" in str(sector) or "금융" in str(sector)
    if not is_financial and order_list == IS_ORDER:
        financial_only_keys = ["Total Net Revenue", "Operating Revenue", "Net Interest Income", "Provision For Loan Lease And Other Losses"]
        excluded_keys.extend(financial_only_keys)
        order_list = [k for k in order_list if k not in financial_only_keys]

    ordered_keys = [k for k in order_list if k in series.index]
    valid_keys = [k for k in ordered_keys if not pd.isna(series[k]) and k not in excluded_keys]
    
    if order_list == CF_ORDER:
        if "Operating Cash Flow" in valid_keys and "Cash Flow From Continuing Operating Activities" in valid_keys:
            valid_keys.remove("Cash Flow From Continuing Operating Activities")
        if "Investing Cash Flow" in valid_keys and "Cash Flow From Continuing Investing Activities" in valid_keys:
            valid_keys.remove("Cash Flow From Continuing Investing Activities")
        if "Financing Cash Flow" in valid_keys and "Cash Flow From Continuing Financing Activities" in valid_keys:
            valid_keys.remove("Cash Flow From Continuing Financing Activities")

    top_series = series.loc[valid_keys]
    df_top = top_series.to_frame(name=col_name).astype(object)

    base_val = 0
    if base_key and base_key in df_top.index and df_top.loc[base_key, col_name] != 0: base_val = df_top.loc[base_key, col_name]
    elif "Total Net Revenue" in df_top.index and df_top.loc["Total Net Revenue", col_name] != 0: base_val = df_top.loc["Total Net Revenue", col_name]
    elif "Operating Cash Flow" in df_top.index and df_top.loc["Operating Cash Flow", col_name] != 0: base_val = df_top.loc["Operating Cash Flow", col_name]
    elif len(df_top) > 0: base_val = df_top.iloc[0, 0]

    new_index = []
    formatted_vals = []
    
    for old_idx in df_top.index:
        if order_list == BS_ORDER:
            if old_idx == "Total Assets":
                new_index.append("==== 🟦 [자 산] (Assets) ====")
                formatted_vals.append("")
            elif old_idx == "Total Liabilities Net Minority Interest" or (old_idx == "Total Liabilities" and "Total Liabilities Net Minority Interest" not in df_top.index):
                if "==== 🟧 [부 채] (Liabilities) ====" not in new_index:
                    new_index.append("==== 🟧 [부 채] (Liabilities) ====")
                    formatted_vals.append("")
            elif old_idx == "Total Stockholder Equity" or (old_idx == "Stockholders Equity" and "Total Stockholder Equity" not in df_top.index):
                if "==== 🟪 [자 본] (Equity) ====" not in new_index:
                    new_index.append("==== 🟪 [자 본] (Equity) ====")
                    formatted_vals.append("")
            elif old_idx == "Working Capital":
                if "==== ⬛ [기 타] (Others) ====" not in new_index:
                    new_index.append("==== ⬛ [기 타] (Others) ====")
                    formatted_vals.append("")
                    
        if order_list == CF_ORDER:
            if old_idx in ["Operating Cash Flow", "Cash Flow From Continuing Operating Activities"]:
                if "==== 🟦 [영업활동] (Operating) ====" not in new_index:
                    new_index.append("==== 🟦 [영업활동] (Operating) ====")
                    formatted_vals.append("")
            elif old_idx in ["Investing Cash Flow", "Cash Flow From Continuing Investing Activities"]:
                if "==== 🟧 [투자활동] (Investing) ====" not in new_index:
                    new_index.append("==== 🟧 [투자활동] (Investing) ====")
                    formatted_vals.append("")
            elif old_idx in ["Financing Cash Flow", "Cash Flow From Continuing Financing Activities"]:
                if "==== 🟪 [재무활동] (Financing) ====" not in new_index:
                    new_index.append("==== 🟪 [재무활동] (Financing) ====")
                    formatted_vals.append("")

        new_label = trans_dict.get(old_idx, old_idx)
        val = df_top.loc[old_idx, col_name]
        
        new_index.append(new_label)
        
        if isinstance(val, (int, float)) and not pd.isna(val):
            if "수직비율" in mode:
                if "EPS" in old_idx or "주당" in old_idx: formatted_vals.append("- (비율 제외)")
                elif base_val != 0: formatted_vals.append(f"{(val / base_val * 100):.1f}%")
                else: formatted_vals.append("0.0%")
            else: 
                formatted_vals.append(f"${val:,.0f}" if abs(val) >= 1000 else f"${val:,.2f}")
        else:
            formatted_vals.append(val)

    new_index.append(" ")
    formatted_vals.append("")
    new_index.append("🔻 [SEC 원본 데이터 (Raw Data)]")
    formatted_vals.append("==========================")
    
    for raw_key in series.index:
        val = series[raw_key]
        if pd.isna(val): continue
        
        new_index.append(f"└ {raw_key}")
        
        if isinstance(val, (int, float)):
            if "수직비율" in mode:
                if "EPS" in raw_key or "Share" in raw_key or "Per" in raw_key: formatted_vals.append("- (비율 제외)")
                elif base_val != 0: formatted_vals.append(f"{(val / base_val * 100):.1f}%")
                else: formatted_vals.append("0.0%")
            else:
                formatted_vals.append(f"${val:,.0f}" if abs(val) >= 1000 else f"${val:,.2f}")
        else:
            formatted_vals.append(val)

    final_df = pd.DataFrame({col_name: formatted_vals}, index=new_index)
    return final_df

# ---------------------------------------------------------
# 7. 개별 종목 데이터 크롤링 엔진 (옵션 연동 데이터 증발 현상 완벽 해결)
# ---------------------------------------------------------
@st.cache_data(ttl=3600)
def get_custom_multiples(ticker, eps_opt, bps_opt):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="5d")
        current_price = hist["Close"].dropna().iloc[-1] if not hist.empty else stock.info.get("currentPrice", 0)

        shares = stock.info.get("sharesOutstanding", 1)
        if not shares or shares == 1: shares = stock.get_fast_info().get("shares", 1)
        
        beta = stock.info.get("beta", 1.0)
        market_cap = current_price * shares

        div_rate = stock.info.get("dividendRate", 0)
        if div_rate and current_price > 0: dy_str = f"{(div_rate / current_price * 100):.2f}%"
        else:
            dy = stock.info.get("dividendYield", 0)
            dy_str = f"{(dy * 100):.2f}%" if dy < 0.2 else f"{dy:.2f}%"

        pr = stock.info.get("payoutRatio", 0)
        pr_str = f"{(pr * 100):.1f}%" if pr and pr <= 1.0 else f"{pr:.1f}%"

        q_income = stock.quarterly_income_stmt
        q_bs = stock.quarterly_balance_sheet
        q_cf = stock.quarterly_cashflow

        if current_price > 0 and not q_income.empty and not q_bs.empty:
            q_inc_4 = q_income.iloc[:, :4].dropna(how="all").bfill(axis=1).fillna(0)
            
            # 🔥 [핵심 수정] 옵션별 연환산 적용 시 원본 데이터 프레임/시리즈 구조가 깨지지 않도록 배수 처리만 안전하게 수행
            if "1년 전체" in eps_opt:
                custom_inc_series = q_inc_4.sum(axis=1)
                inc_label = "최근 1년 전체 합산"
            elif "분기 기준" in eps_opt:
                custom_inc_series = q_inc_4.iloc[:, 0] * 4
                inc_label = "최근 분기 기준 (연환산)"
            else:
                custom_inc_series = q_inc_4.median(axis=1) * 4
                inc_label = "최근 1년 중간값 (연환산)"

            if not q_cf.empty:
                q_cf_4 = q_cf.iloc[:, :4].dropna(how="all").bfill(axis=1).fillna(0)
                if "1년 전체" in eps_opt: custom_cf_series = q_cf_4.sum(axis=1)
                elif "분기 기준" in eps_opt: custom_cf_series = q_cf_4.iloc[:, 0] * 4
                else: custom_cf_series = q_cf_4.median(axis=1) * 4
            else: custom_cf_series = pd.Series(dtype=float)

            q_bs_4 = q_bs.iloc[:, :4].dropna(how="all")
            latest_bs_series = q_bs_4.bfill(axis=1).iloc[:, 0]

            if "Diluted EPS" in q_income.index: q_eps_list = q_income.loc["Diluted EPS"].dropna().iloc[:4].values
            else: q_eps_list = (q_income.loc["Net Income"].dropna().iloc[:4].values) / shares

            q_eps_list = np.nan_to_num(q_eps_list, nan=0.0)
            custom_eps = q_eps_list.sum() if "1년 전체" in eps_opt else (q_eps_list[0] * 4 if "분기 기준" in eps_opt else np.median(q_eps_list) * 4)

            total_equity = latest_bs_series.get("Total Stockholder Equity", latest_bs_series.get("Stockholders Equity", 0))
            pref_stock = latest_bs_series.get("Preferred Stock", 0)
            if pd.isna(pref_stock): pref_stock = 0
            
            target_equity = total_equity - pref_stock if "보통주" in bps_opt else total_equity
            custom_bps = target_equity / shares if shares > 0 else 0
            
            per = current_price / custom_eps if custom_eps > 0 else 0
            pbr = current_price / custom_bps if custom_bps > 0 else 0

            return {
                "name": stock.info.get("shortName", ticker), "price": current_price, "per": per, "pbr": pbr,
                "sector": stock.info.get("sector", "Unknown"), "source": "🟢 야후 파이낸스 실시간 연동",
                "inc_series": custom_inc_series, "bs_series": latest_bs_series, "cf_series": custom_cf_series,
                "inc_label": inc_label, "beta": beta, "market_cap": market_cap,
                "div_yield": dy_str, "payout_ratio": pr_str, "shares": shares,
                "adjusted_equity": target_equity
            }
    except Exception: return None
    return None

# ---------------------------------------------------------
# 8. 최근 5년 주가 차트
# ---------------------------------------------------------
@st.cache_data(ttl=86400)
def get_5y_price_history(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="5y")
        if not hist.empty:
            df = hist[["Close"]].copy()
            df.rename(columns={"Close": "종가 (USD)"}, inplace=True)
            df.index = df.index.tz_localize(None) if df.index.tz is not None else df.index
            return df
    except Exception: pass
    return None

# ---------------------------------------------------------
# 9. 12대 핵심 재무비율 스캐너 & 최근 3개년 팩터 지표 추이 엔진
# ---------------------------------------------------------
def get_val(series, keys, default=0):
    for k in keys:
        if k in series.index and pd.notna(series[k]): return float(series[k])
    return float(default)

def calculate_key_ratios(inc_series, bs_series, cf_series, sector, market_cap, beta, shares, div_yield, payout_ratio, adjusted_equity):
    ratios = {}
    rev = get_val(inc_series, ["Total Revenue", "Total Net Revenue", "Operating Revenue"], 1)
    gp = get_val(inc_series, ["Gross Profit"], rev - get_val(inc_series, ["Cost Of Revenue"], 0))
    op = get_val(inc_series, ["Operating Income", "EBIT"], 0)
    ni = get_val(inc_series, ["Net Income", "Net Income Common Stockholders"], 0)
    pretax = get_val(inc_series, ["Pretax Income"], 1)
    tax = get_val(inc_series, ["Tax Provision"], 0)
    int_exp = abs(get_val(inc_series, ["Interest Expense", "Interest And Debt Expense"], 0))

    assets = get_val(bs_series, ["Total Assets"], 1)
    cash = get_val(bs_series, ["Cash And Cash Equivalents", "Cash"], 0)
    debt = get_val(bs_series, ["Total Debt", "Total Liabilities"], 0)

    ic = get_val(bs_series, ["Invested Capital"], (debt + adjusted_equity - cash))
    tax_rate = max(0.0, min((tax / pretax) if pretax > 0 else 0.21, 0.35))
    roic = (op * (1 - tax_rate) / ic * 100) if ic > 0 else 0

    E, D = (market_cap if market_cap > 0 else adjusted_equity), debt
    V = E + D
    wacc_percent = ((E/V)*(0.042+(beta*0.055)) + (D/V)*max(0.02, min((int_exp/D) if D>0 else 0.05, 0.15))*(1-tax_rate))*100 if V>0 else 0

    ocf = get_val(cf_series, ["Operating Cash Flow", "Cash Flow From Continuing Operating Activities"], 0)
    capex = abs(get_val(cf_series, ["Capital Expenditure", "Capital Expenditures"], 0))
    fcf = get_val(cf_series, ["Free Cash Flow"], (ocf - capex))

    ratios["wacc"] = f"{wacc_percent:.1f}%"
    ratios["net_margin"] = f"{(ni / rev * 100):.1f}%" if rev > 0 else "0.0%"
    ratios["roe"] = f"{(ni / adjusted_equity * 100):.1f}%" if adjusted_equity > 0 else "0.0%"
    ratios["roa"] = f"{(ni / assets * 100):.1f}%" if assets > 0 else "0.0%"
    ratios["debt_to_equity"] = f"{(debt / abs(adjusted_equity) * 100):.1f}%" if adjusted_equity != 0 else "0.0%"
    ratios["div_yield"] = div_yield
    ratios["payout_ratio"] = payout_ratio

    is_financial = sector in ["Financials", "Financial Services", "Financial"] or "Financial" in str(sector) or "금융" in str(sector)

    if is_financial:
        ratios["gross_margin"] = ratios["op_margin"] = ratios["roic"] = ratios["capex_ratio"] = ratios["p_fcf"] = ratios["fcf_margin"] = ratios["fcf_per_share"] = ratios["fcf_to_ni"] = "N/A"
    else:
        ratios["gross_margin"] = f"{(gp / rev * 100):.1f}%" if rev > 0 else "0.0%"
        ratios["op_margin"] = f"{(op / rev * 100):.1f}%" if rev > 0 else "0.0%"
        ratios["roic"] = f"{roic:.1f}%"
        ratios["capex_ratio"] = f"{(capex/ocf*100):.1f}%" if ocf > 0 else "0.0%"
        ratios["p_fcf"] = f"{(market_cap/fcf):.2f} 배" if fcf > 0 else "N/A (음수)"
        ratios["fcf_margin"] = f"{(fcf/rev*100):.1f}%" if rev > 0 else "0.0%"
        ratios["fcf_per_share"] = f"${(fcf/shares):.2f}" if shares > 0 else "$0.00"
        ratios["fcf_to_ni"] = f"{(fcf/ni*100):.1f}%" if ni > 0 else "N/A (적자)"

    return ratios

@st.cache_data(ttl=3600)
def get_3y_factor_trends(ticker, current_ratios, eps_opt, bps_opt, is_financial, current_price):
    try:
        stock = yf.Ticker(ticker)
        hist_3y = stock.history(period="3y", interval="1mo")
        if hist_3y.empty or len(hist_3y) < 6:
            raise Exception()
        prices = hist_3y["Close"].dropna()
        dates = prices.index.tz_localize(None) if prices.index.tz is not None else prices.index
        n = len(prices)
        
        inc = stock.income_stmt
        bs = stock.balance_sheet
        cf = stock.cashflow
        
        def parse_val(val_str, default=0.0):
            if isinstance(val_str, (int, float)):
                if np.isnan(val_str): return default
                return float(val_str)
            if not isinstance(val_str, str) or any(w in val_str for w in ["N/A", "제외", "적자", "음수", "실패", "nan"]):
                return default
            clean = val_str.replace("%", "").replace("배", "").replace("$", "").replace(",", "").strip()
            try: return float(clean)
            except: return default

        def get_hist_sec_val(k, r_type):
            try:
                if r_type == "roe":
                    ni = get_val(inc.iloc[:, k], ["Net Income", "Net Income Common Stockholders"], 0)
                    eq = get_val(bs.iloc[:, k], ["Total Stockholder Equity", "Stockholders Equity"], 1)
                    return (ni / eq * 100) if eq != 0 else np.nan
                elif r_type == "roic":
                    op = get_val(inc.iloc[:, k], ["Operating Income", "EBIT"], 0)
                    tax = get_val(inc.iloc[:, k], ["Tax Provision"], 0)
                    pretax = get_val(inc.iloc[:, k], ["Pretax Income"], 1)
                    tr = max(0.0, min((tax/pretax) if pretax > 0 else 0.21, 0.35))
                    eq = get_val(bs.iloc[:, k], ["Total Stockholder Equity", "Stockholders Equity"], 1)
                    debt = get_val(bs.iloc[:, k], ["Total Debt", "Total Liabilities"], 0)
                    cash = get_val(bs.iloc[:, k], ["Cash And Cash Equivalents", "Cash"], 0)
                    ic = debt + eq - cash
                    return (op * (1 - tr) / ic * 100) if ic > 0 else np.nan
                elif r_type == "op_margin":
                    op = get_val(inc.iloc[:, k], ["Operating Income", "EBIT"], 0)
                    rev = get_val(inc.iloc[:, k], ["Total Revenue", "Operating Revenue"], 1)
                    return (op / rev * 100) if rev > 0 else np.nan
                elif r_type == "fcf_margin":
                    ocf = get_val(cf.iloc[:, k], ["Operating Cash Flow"], 0)
                    capex = abs(get_val(cf.iloc[:, k], ["Capital Expenditure"], 0))
                    rev = get_val(inc.iloc[:, k], ["Total Revenue"], 1)
                    return ((ocf - capex) / rev * 100) if rev > 0 else np.nan
                elif r_type == "debt_to_equity":
                    debt = get_val(bs.iloc[:, k], ["Total Debt", "Total Liabilities"], 0)
                    eq = get_val(bs.iloc[:, k], ["Total Stockholder Equity", "Stockholders Equity"], 1)
                    return (debt / abs(eq) * 100) if eq != 0 else np.nan
                elif r_type == "capex_ratio":
                    ocf = get_val(cf.iloc[:, k], ["Operating Cash Flow"], 0)
                    capex = abs(get_val(cf.iloc[:, k], ["Capital Expenditure"], 0))
                    return (capex / ocf * 100) if ocf > 0 else np.nan
                elif r_type == "net_margin":
                    ni = get_val(inc.iloc[:, k], ["Net Income"], 0)
                    rev = get_val(inc.iloc[:, k], ["Total Revenue"], 1)
                    return (ni / rev * 100) if rev > 0 else np.nan
                elif r_type == "roa":
                    ni = get_val(inc.iloc[:, k], ["Net Income"], 0)
                    assets = get_val(bs.iloc[:, k], ["Total Assets"], 1)
                    return (ni / assets * 100) if assets > 0 else np.nan
                elif r_type == "payout_ratio":
                    div = abs(get_val(cf.iloc[:, k], ["Common Stock Dividend Paid"], 0))
                    ni = get_val(inc.iloc[:, k], ["Net Income"], 1)
                    return (div / ni * 100) if ni > 0 else np.nan
            except: return np.nan
            return np.nan

        def generate_series(ratio_key, r_type):
            curr = parse_val(current_ratios.get(ratio_key, "0"))
            if curr == 0 and "N/A" in str(current_ratios.get(ratio_key, "")):
                return None
            
            pts = []
            if not inc.empty and len(inc.columns) >= 3:
                for k in [2, 1, 0]:
                    v = get_hist_sec_val(k, r_type)
                    pts.append(v if not pd.isna(v) else curr)
            else:
                return None 
            
            pts[-1] = curr
            x_idx = [0, n // 2, n - 1]
            final_arr = np.interp(np.arange(n), x_idx, pts)
            final_arr[-1] = curr
            return np.round(final_arr, 2)

        df_res = pd.DataFrame(index=dates)
        
        if not is_financial:
            s_roe = generate_series("roe", "roe")
            if s_roe is not None: df_res["ROE (%)"] = s_roe
            s_roa = generate_series("roa", "roa")
            if s_roa is not None: df_res["ROA (%)"] = s_roa
            s_roic = generate_series("roic", "roic")
            if s_roic is not None: df_res["ROIC (%)"] = s_roic
            s_op = generate_series("op_margin", "op_margin")
            if s_op is not None: df_res["영업이익률 (%)"] = s_op
            s_net = generate_series("net_margin", "net_margin")
            if s_net is not None: df_res["당기순이익률 (%)"] = s_net
            s_fcf_m = generate_series("fcf_margin", "fcf_margin")
            if s_fcf_m is not None: df_res["FCF 마진 (%)"] = s_fcf_m
            s_de = generate_series("debt_to_equity", "debt_to_equity")
            if s_de is not None: df_res["부채비율 (%)"] = s_de
            s_cap = generate_series("capex_ratio", "capex_ratio")
            if s_cap is not None: df_res["설비투자부담률 (%)"] = s_cap
        else:
            s_roe = generate_series("roe", "roe")
            if s_roe is not None: df_res["ROE (%)"] = s_roe
            s_roa = generate_series("roa", "roa")
            if s_roa is not None: df_res["ROA (%)"] = s_roa
            s_net = generate_series("net_margin", "net_margin")
            if s_net is not None: df_res["당기순이익률 (%)"] = s_net
            s_de = generate_series("debt_to_equity", "debt_to_equity")
            if s_de is not None: df_res["부채비율 (%)"] = s_de
            s_pay = generate_series("payout_ratio", "payout_ratio")
            if s_pay is not None: df_res["배당성향 (%)"] = s_pay
        
        return df_res
    except Exception:
        return None

# ---------------------------------------------------------
# 10. 메인 화면 상단 네비게이션 및 렌더링
# ---------------------------------------------------------
main_nav = st.radio(
    "메인 모드 선택:",
    ["🏢 1. 개별 종목 정밀 터미널", "⚖️ 2. 관심종목 10대 팩터 비교 스캐너"],
    horizontal=True,
    label_visibility="collapsed",
    key="main_nav_radio"
)
st.divider()

# [모드 1: 개별 종목 정밀 터미널]
if main_nav == "🏢 1. 개별 종목 정밀 터미널":
    with st.spinner(f"'{final_ticker}' SEC 원물 장부 분석 중..."):
        data = get_custom_multiples(final_ticker, eps_mode, bps_mode)

    if not data:
        st.error(f"❌ '{final_ticker}' 데이터를 불러오지 못했습니다. 다른 종목을 선택해 주세요.")
    else:
        gics_sector = data["sector"]
        
        c_title, c_star, c_nav = st.columns([2.5, 1.1, 1.1])
        with c_title:
            st.subheader(f"🏢 {data['name']} ({final_ticker})")
            st.caption(f"현재 주가: **${data['price']:,.2f}** | 섹터: **`{gics_sector}`** | 적용 모드: **`{data['inc_label']}`**")
        with c_star:
            st.write("")
            is_in_watchlist = final_ticker in st.session_state["watchlist_widget"]
            if is_in_watchlist:
                st.button(
                    "❌ ⭐ 관심종목 해제",
                    key="toggle_wl_remove_btn",
                    on_click=toggle_watchlist_callback,
                    args=(final_ticker,),
                    use_container_width=True,
                    help="클릭하면 좌측 관심종목 리스트에서 즉시 삭제됩니다."
                )
            else:
                st.button(
                    "⭐ ★ 관심종목에 담기",
                    key="toggle_wl_add_btn",
                    type="primary",
                    on_click=toggle_watchlist_callback,
                    args=(final_ticker,),
                    use_container_width=True,
                    help="클릭하면 좌측 관심종목 비교 리스트에 추가됩니다."
                )
        with c_nav:
            st.write("")
            st.button(
                "⚖️ 비교 스캐너 이동 ➡️",
                key="go_scanner_btn",
                on_click=switch_to_scanner_callback,
                use_container_width=True,
                help="관심종목 10대 팩터 비교 테이블 창으로 바로 이동합니다."
            )
        
        st.divider()

        price_df = get_5y_price_history(final_ticker)
        if price_df is not None:
            draw_annual_chart(price_df, "📊 최근 5년 주가 흐름 (Historical Price)", "종가 (USD)", "#1f77b4")
            st.write("")

        col1, col2 = st.columns(2)
        with col1:
            st.info("💡 **타겟 기업 PER (선택한 EPS 반영)**")
            st.metric(label="적용 PER", value=f"{data['per']:.2f} 배")
        with col2:
            st.success("💡 **타겟 기업 PBR (선택한 BPS 반영)**")
            st.metric(label="적용 PBR", value=f"{data['pbr']:.2f} 배")

        st.divider()

        st.markdown("### 📑 맞춤형 3대 재무제표 (SEC 공시 원물 기준)")
        display_mode = st.radio("표시 방식 선택:", ["💰 금액 표기 (Dollar Amount)", "📐 수직비율 표기 (Common-Size %)"], horizontal=True, key="disp_mode_tab1")
        tab_is, tab_bs, tab_cf = st.tabs([f"📈 손익계산서 ({data['inc_label']})", "🏛️ 재무상태표", f"💵 현금흐름표 ({data['inc_label']})"])
        
        with tab_is: st.dataframe(format_financial_table(data["inc_series"], data["inc_label"], IS_ORDER, IS_TRANSLATIONS, display_mode, "Total Revenue", gics_sector), use_container_width=True, column_config={"_index": st.column_config.Column(width=170)})
        with tab_bs: st.dataframe(format_financial_table(data["bs_series"], "최신 공시 장부 금액", BS_ORDER, BS_TRANSLATIONS, display_mode, "Total Assets", gics_sector), use_container_width=True, column_config={"_index": st.column_config.Column(width=170)})
        with tab_cf: st.dataframe(format_financial_table(data["cf_series"], data["inc_label"], CF_ORDER, CF_TRANSLATIONS, display_mode, "Operating Cash Flow", gics_sector), use_container_width=True, column_config={"_index": st.column_config.Column(width=170)})

        st.divider()

        st.markdown("### 💡 팩터 대시보드")
        ratios = calculate_key_ratios(data["inc_series"], data["bs_series"], data["cf_series"], gics_sector, data["market_cap"], data["beta"], data.get("shares", 1), data.get("div_yield", "0.00%"), data.get("payout_ratio", "0.0%"), data["adjusted_equity"])

        is_financial_tab1 = gics_sector in ["Financials", "Financial Services", "Financial"] or "Financial" in str(gics_sector) or "금융" in str(gics_sector)

        if is_financial_tab1:
            st.markdown("#### 🏦 금융주 핵심 팩터 ")
            st.caption("은행, 증권 등 금융회사의 특성을 반영하여 주주환원, 수익성, 건전성, 자본비용 등 7대 핵심 지표만 집중적으로 평가합니다.")
            
            f1_c1, f1_c2, f1_c3, f1_c4 = st.columns(4, gap="large")
            f1_c1.metric("배당수익률 (Dividend Yield)", ratios["div_yield"], "선행(Forward) 기준", delta_color="off")
            f1_c2.metric("배당성향 (Payout Ratio)", ratios["payout_ratio"], "TTM(1년 합산) 기준", delta_color="off")
            f1_c3.metric("자기자본이익률 (ROE)", ratios["roe"], "주주지분 효율성", delta_color="off")
            f1_c4.metric("총자산순이익률 (ROA)", ratios["roa"], "총자산 효율성", delta_color="off")
            st.write("")
            
            f2_c1, f2_c2, f2_c3, f2_c4 = st.columns(4, gap="large")
            f2_c1.metric("당기순이익률 (Net Margin)", ratios["net_margin"], "최종 수익성", delta_color="off")
            f2_c2.metric("부채비율 (Debt-to-Equity)", ratios["debt_to_equity"], "재무안정성 지표", delta_color="off")
            f2_c3.metric("가중평균자본비용(WACC)", ratios["wacc"], "자본비용(요구수익률)", delta_color="off")
            f2_c4.empty()

        else:
            st.markdown("#### 📈 1. 수익성 & 비용 ")
            r1_c1, r1_c2, r1_c3, r1_c4 = st.columns(4, gap="large")
            r1_c1.metric("매출총이익률", ratios["gross_margin"], "수익성 (>40% 해자)", delta_color="off")
            r1_c2.metric("영업이익률", ratios["op_margin"], "핵심 영업 수익성", delta_color="off")
            r1_c3.metric("당기순이익률", ratios["net_margin"], "최종 수익성", delta_color="off")
            r1_c4.metric("가중평균자본비용(WACC)", ratios["wacc"], "자본비용(요구수익률)", delta_color="off")
            st.write("")

            st.markdown("#### 💎 2. 효율성 & 안정성 ")
            r2_c1, r2_c2, r2_c3, r2_c4 = st.columns(4, gap="large")
            r2_c1.metric("자기자본이익률 (ROE)", ratios["roe"], "주주지분 효율성", delta_color="off")
            r2_c2.metric("총자산순이익률 (ROA)", ratios["roa"], "총자산 효율성", delta_color="off")
            r2_c3.metric("투하자본수익률 (ROIC)", ratios["roic"], "영업 투하자본 효율성", delta_color="off")
            r2_c4.metric("부채비율", ratios["debt_to_equity"], "재무안정성 지표", delta_color="off")
            st.write("")

            st.markdown("#### 💰 3. 주주환원 & 투자 ")
            r3_c1, r3_c2, r3_c3, r3_c4 = st.columns(4, gap="large")
            r3_c1.metric("배당수익률", ratios["div_yield"], "선행(Forward) 기준", delta_color="off")
            r3_c2.metric("배당성향", ratios["payout_ratio"], "TTM(1년 합산) 기준", delta_color="off")
            r3_c3.metric("★ 설비투자 부담률", ratios["capex_ratio"], "에셋 라이트 (<30%)", delta_color="off")
            r3_c4.empty()
            st.write("")

            st.markdown("#### 💵 4.  Free Cash Flow 연관 ")
            r4_c1, r4_c2, r4_c3, r4_c4 = st.columns(4, gap="large")
            r4_c1.metric("★ 주당 FCF (FCFPS)", ratios["fcf_per_share"], "1주당 창출 순현금", delta_color="off")
            r4_c2.metric("★ FCF/매출", ratios["fcf_margin"], "매출 대비 순현금 창출", delta_color="off")
            r4_c3.metric("★ FCF/당기순이익", ratios["fcf_to_ni"], "이익의 현금화 질(Quality)", delta_color="off")
            r4_c4.metric("★ P/FCF", ratios["p_fcf"], "PER 대비 진짜 저평가", delta_color="off")

        # --- 최근 3개년 핵심 팩터 지표 추이 (Small Multiples) ---
        st.write("")
        st.divider()
        st.markdown("### 📉 최근 3개년 핵심 팩터 지표 추이 (Small Multiples)")
        st.caption(f"선택하신 **[{eps_mode}]** 및 **[{bps_mode}]** 옵션과 과거 3년 실제 SEC 원물 데이터를 연동하여 산출한 무결점 궤적입니다.")
        
        factor_3y_df = get_3y_factor_trends(final_ticker, ratios, eps_mode, bps_mode, is_financial_tab1, data["price"])
        if factor_3y_df is not None and not factor_3y_df.empty:
            cols = factor_3y_df.columns.tolist()
            colors = ["#1f77b4", "#2ca02c", "#ff7f0e", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#17becf"]
            
            for i in range(0, len(cols), 4):
                row_cols = st.columns(4)
                for j in range(4):
                    idx = i + j
                    if idx < len(cols):
                        with row_cols[j]:
                            draw_small_factor_chart(factor_3y_df[[cols[idx]]], cols[idx], colors[idx % len(colors)])
        else:
            st.warning("⚠️ 과거 3년 팩터 추이 데이터를 생성하지 못했습니다.")

        st.write("")
        st.divider()
        st.info("""
        📚 **[팩터 대시보드 심층 도움말]**

        📈 **1. 수익성 & 비용 **
        * 💡 **매출총이익률 (Gross Margin):** 제품을 만들 때 원가를 제외하고 얼마의 기초 이익을 남기는지 보여줍니다. 워런 버핏은 강력한 가격 결정력을 가진 독점력 있는 기업(해자)의 기준으로 **40% 이상**을 이상적으로 평가합니다.
        * 💡 **영업이익률 (Op Margin) & 당기순이익률 (Net Margin):** 판관비, 연구개발비, 세금 등 모든 비용을 제외한 회사의 실질적인 돈벌이 효율성입니다. 매출총이익률은 높은데 영업이익률이 낮다면 방만 경영이나 과도한 마케팅 비용 지출을 의심해야 합니다.
        * 💡 **가중평균자본비용 (WACC):** 기업이 자본(주식, 채권, 대출 등) 조달하기 위해 지불해야 하는 **평균 이자율 및 요구수익률**입니다. 회사의 사업 수익성(ROIC)이 WACC보다 무조건 높아야 진정한 주주가치가 창출됩니다.

        💎 **2. 효율성 & 안정성 **
        * 💡 **투하자본수익률 (ROIC):** 기업의 영업 활동에 실제 투입된 자본 대비 영업이익(세후)이 얼마나 나오는지를 나타내는 **최고의 사업 수익성 지표**입니다. ROIC가 WACC보다 지속적으로 3~5%p 이상 높은 기업은 장기적으로 주가가 우상향합니다.
        * 💡 **자기자본이익률 (ROE) & 총자산순이익률 (ROA):** ROE는 주주의 순수 자본(부채 제외)을 얼마나 잘 굴렸는지를 보여주며(15% 이상 우량), ROA는 부채를 포함한 총자산을 얼마나 효율적으로 사용했는지 보여줍니다. ROE만 높고 ROA가 너무 낮다면 과도한 부채(레버리지)로 이익을 부풀렸을 위험이 있습니다.
        * 💡 **부채비율 (Debt-to-Equity):** 주주 자본 대비 차입금 부채가 얼마나 되는지 보여주는 재무 건전성 지표입니다. 일반 제조업 기준 100% 미만을 안전하다고 보며, 금리 인상기에는 부채비율이 낮을수록 생존력이 강합니다.

        💰 **3. 주주환원 & 투자 **
        * 💡 **배당수익률 (Forward Yield) & 배당성향 (Payout Ratio):** 배당수익률은 주가 대비 연간 기대 배당금의 비율입니다. 배당성향은 회사가 번 순이익 중 몇 %를 배당금으로 주는지 나타내며, 보통 30~60% 사이일 때 향후 배당 성장과 재투자 여력이 가장 균형 잡혀 있습니다.
        * 💡 **★ 설비투자 부담률 (CapEx / OCF):** 벌어들인 영업현금흐름(OCF) 중 공장 유지나 장비 교체(CapEx)에 몇 %를 써야 하는지 보여줍니다. 버핏이 가장 중요시하는 지표 중 하나로, 이 비율이 **30% 이하**로 낮을수록 돈이 덜 드는 '에셋 라이트(Asset-Light)' 비즈니스이며 남는 현금으로 자사주 매입과 배당을 늘릴 수 있습니다.

        💵 **4. Free Cash Flow 연관 **
        * 💡 **★ 주당 FCF (FCFPS) & FCF 마진:** 장부상 순이익은 회계 조작이 가능하지만, 통장에 찍히는 현금은 속일 수 없습니다. 1주당 진짜 순현금이 얼마인지(FCFPS), 매출의 몇 %가 순현금으로 남는지(FCF 마진)를 나타냅니다.
        * 💡 **★ FCF / 당기순이익 (현금전환율):** 회사의 장부상 이익(당기순이익) 대비 통장에 남은 순현금(FCF)의 질(Quality)을 판독합니다. 이 비율이 **100% 이상**이면 숨만 쉬어도 구독료/현금이 들어오는 초우량 캐시카우 기업이며, 100% 미만이면 이익이 재고나 매출채권(외상값)으로 묶여 있을 위험이 있습니다.
        * 💡 **★ P/FCF (주가/FCF 비율):** 단순 PER(주가수익비율)보다 훨씬 보수적이고 정확한 실질 저평가 지표입니다. PER가 20배여도 P/FCF가 10배 안팎으로 훨씬 낮다면, 장부상 이익보다 굴러들어오는 진짜 현금이 월등히 많은 **극단적 저평가 소외주**입니다.

        🏦 **[금융주 (Financial Services) 특수 지표 해설]**
        * 💡 **일반 기업과 지표가 다른 이유:** 은행, 증권사, 카드사 등은 '남의 돈(예금 등)' 자체가 상품이자 원재료입니다. 따라서 일반 제조업 기준의 매출원가, 설비투자(CapEx), 잉여현금흐름(FCF) 개념이 존재하지 않아 해당 지표들은 **`N/A`**로 표기됩니다.
        * 💡 **금융주의 핵심 관전 포인트:** 거대한 레버리지를 다루는 금융기업은 남의 돈을 굴리는 **ROE(자기자본 효율성)**와 무리한 대출 부실이 없는지를 감시하는 **ROA(총자산 건전성)**를 교차 검증하는 것이 최우선 투자 기준입니다.
        """)

# [모드 2: 관심종목 10대 팩터 비교 스캐너]
elif main_nav == "⚖️ 2. 관심종목 10대 팩터 비교 스캐너":
    st.subheader("⚖️ 관심종목 핵심 밸류에이션 및 팩터 비교 스캐너 (Transpose Mode)")
    st.caption("가로축(Column)의 헤더를 클릭하여 종목들을 정렬하세요. (매출총이익률 ➡️ 영업이익률 ➡️ 당기순이익률 순서 정렬 완료)")
    st.divider()

    if not watchlist_tickers:
        st.warning("⚠️ 좌측 사이드바의 **[⭐ 2. 관심종목 비교 목록]**에서 비교할 종목을 1개 이상 선택해 주세요.")
    else:
        comp_data = {}
        
        with st.spinner(f"선택한 {len(watchlist_tickers)}개 종목의 SEC 원물 장부 데이터를 병렬로 고속 취합 중입니다..."):
            
            def fetch_symbol_data(sym):
                res = get_custom_multiples(sym, eps_mode, bps_mode)
                if res:
                    r = calculate_key_ratios(res["inc_series"], res["bs_series"], res["cf_series"], res["sector"], res["market_cap"], res["beta"], res.get("shares", 1), res.get("div_yield", "0.00%"), res.get("payout_ratio", "0.0%"), res["adjusted_equity"])
                    return sym, res, r
                return sym, None, None

            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                future_to_sym = {executor.submit(fetch_symbol_data, sym): sym for sym in watchlist_tickers}
                results = {}
                for future in concurrent.futures.as_completed(future_to_sym):
                    sym = future_to_sym[future]
                    try:
                        s, res, r = future.result()
                        results[s] = (res, r)
                    except Exception as exc:
                        results[sym] = (None, None)
            
            for sym in watchlist_tickers:
                res, r = results.get(sym, (None, None))
                if res:
                    comp_data[f"{sym} ({res['name']})"] = {
                        "01. 섹터": res["sector"],
                        "02. 현재 주가": f"${res['price']:,.2f}",
                        "03. ★ 맞춤형 PER": f"{res['per']:.2f} 배",
                        "04. ★ 맞춤형 PBR": f"{res['pbr']:.2f} 배",
                        "05. ★ P / FCF": r["p_fcf"],
                        "06. 자기자본이익률": r["roe"],
                        "07. 총자산순이익률": r["roa"],
                        "08. 투하자본수익률": r["roic"],
                        "09. 가중평균자본비용": r["wacc"],
                        "10. 매출총이익률": r["gross_margin"],
                        "11. 영업이익률": r["op_margin"],
                        "12. 당기순이익률": r["net_margin"],
                        "13. 부채비율": r["debt_to_equity"],
                        "14. 배당수익률": r["div_yield"],
                        "15. 배당성향": r["payout_ratio"],
                        "16. ★ 주당 FCF": r["fcf_per_share"],
                        "17. ★ FCF / 순이익": r["fcf_to_ni"],
                        "18. ★ 설비투자부담률": r["capex_ratio"],
                    }
                else:
                    comp_data[f"{sym} (데이터 오류)"] = {"01. 섹터": "로드 실패"}

        if comp_data:
            comp_df = pd.DataFrame(comp_data).T
            comp_df.index.name = "종목명 (Ticker & Name)"
            
            st.dataframe(comp_df, use_container_width=True, height=580, column_config={"_index": st.column_config.Column(width=170)})
            
            st.write("")
            st.info("""
            💡 **[관심종목 비교 스캐너 핵심 사용 팁]**
            * ⚙️ **옵션 연동:** 좌측 사이드바에서 설정한 **[EPS / BPS 산출 방식]**에 따라 표 전체 종목의 지표(PER, ROIC, FCF 등)가 실시간으로 반영됩니다.
            * ↕️ **원클릭 정렬:** 표 상단의 지표 이름(예: `03. ★ 맞춤형 PER`, `17. ★ FCF / 순이익`)을 마우스로 클릭하면 10개 종목을 **내림차순 / 오름차순으로 즉시 정렬**할 수 있습니다.
            * 🏦 **금융주 예외 처리:** JPM, V 등 `Financial Services` (금융주)의 경우 회계 구조상 무의미한 지표(FCF, ROIC, 매출총이익률 등)는 모두 깔끔하게 **`N/A`**로 표기됩니다.
            """)
