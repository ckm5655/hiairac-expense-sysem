import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
import plotly.express as px
from streamlit_gsheets import GSheetsConnection
import re
import uuid

st.set_page_config(page_title="우리집 가계부", page_icon="💕", layout="centered")

st.markdown("""
<style>
    /* 월 네비게이션 1줄 강제 고정 및 모바일 밀림 방지 */
    div[data-testid="stHorizontalBlock"]:has(.month-nav-anchor) {
        flex-wrap: nowrap !important;
        align-items: center !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.month-nav-anchor) > div {
        min-width: 0 !important; 
        padding-left: 2px !important;
        padding-right: 2px !important;
    }
    
    /* 투명 버튼화 (내역 전체 영역 터치 가능 및 1줄 고정) */
    button[kind="tertiary"] {
        text-align: left !important;
        justify-content: flex-start !important;
        padding: 12px 8px !important;
        border-radius: 8px !important;
        border: none !important;
        background-color: transparent !important;
        border-bottom: 1px solid #f0f4f8 !important;
        color: #1e293b !important;
        margin-bottom: 2px !important;
        height: auto !important;
    }
    button[kind="tertiary"]:hover {
        background-color: #f8fafc !important;
    }
    button[kind="tertiary"] div {
        width: 100%;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        font-size: 14px;
    }
    
    /* 설정 탭 버튼용 얇은 여백 */
    .settings-btn button[kind="tertiary"] {
        padding: 8px 4px !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 🔒 비밀번호 인증 로직 시작 ---
def check_password():
    """비밀번호가 일치하면 True를 반환합니다."""
    # 이미 인증을 통과했다면 패스
    if st.session_state.get("password_correct", False):
        return True

    # 세련된 잠금 화면 UI
    st.markdown("""
    <style>
        @keyframes slideDown {
            from { opacity: 0; transform: translateY(-30px); }
            to { opacity: 1; transform: translateY(0); }
        }
        @keyframes pulseLock {
            0% { transform: scale(1); }
            50% { transform: scale(1.08); }
            100% { transform: scale(1); }
        }
        .lock-wrapper {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 50px 30px;
            margin-top: 8vh;
            background: linear-gradient(145deg, #ffffff, #f8fafc);
            border-radius: 28px;
            box-shadow: 0 20px 40px rgba(15, 23, 42, 0.08), 0 1px 3px rgba(0,0,0,0.02);
            border: 1px solid #f1f5f9;
            animation: slideDown 0.7s cubic-bezier(0.16, 1, 0.3, 1) forwards;
            max-width: 400px;
            margin-left: auto;
            margin-right: auto;
            text-align: center;
        }
        .lock-emoji {
            font-size: 65px;
            margin-bottom: 15px;
            animation: pulseLock 2.5s infinite ease-in-out;
            filter: drop-shadow(0 10px 15px rgba(59, 130, 246, 0.2));
        }
        .lock-title {
            font-size: 30px;
            font-weight: 800;
            margin-bottom: 10px;
            background: linear-gradient(90deg, #0f172a, #3b82f6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: -0.5px;
        }
        .lock-desc {
            font-size: 15px;
            color: #64748b;
            line-height: 1.6;
            margin-bottom: 10px;
            font-weight: 500;
        }
    </style>
    
    <div class="lock-wrapper">
        <div class="lock-emoji">🔐</div>
        <div class="lock-title">우리집 가계부</div>
        <div class="lock-desc">프라이빗 자산 관리를 시작합니다.<br>안전한 접속을 위해 비밀번호를 입력해주세요.</div>
    </div>
    <br>
    """, unsafe_allow_html=True)

    def password_entered():
        # secrets에 저장된 비밀번호를 가져옴 (기본값: 1234)
        correct_pw = st.secrets.get("app_password", "1234")
        if st.session_state["password_input"] == str(correct_pw):
            st.session_state["password_correct"] = True
            del st.session_state["password_input"] # 보안상 입력값 삭제
        else:
            st.session_state["password_correct"] = False

    st.text_input("🔑", type="password", on_change=password_entered, key="password_input", placeholder="비밀번호를 입력하고 Enter를 누르세요", label_visibility="collapsed")

    if "password_correct" in st.session_state and not st.session_state["password_correct"]:
        st.error("🚫 비밀번호가 일치하지 않습니다. 다시 시도해주세요.")

    return False

# 인증을 통과하지 못하면 여기서 앱 실행을 멈춤 (아래 가계부 내용은 안 보임)
if not check_password():
    st.stop()
# --- 🔒 비밀번호 인증 로직 끝 ---

def custom_progress_bar(current, target, is_expense=True, label=""):
    if target <= 0: return
    ratio = current / target
    pct = min(ratio * 100, 100)
    
    if is_expense:
        if ratio < 0.5: color = "#28a745" # 안전(초록)
        elif ratio < 0.8: color = "#ffc107" # 경고(노랑)
        else: color = "#dc3545" # 위험(빨강)
    else:
        color = "#3b82f6" # 저축(파랑)
        
    st.markdown(f"""
    <div style="margin-bottom: 10px; padding: 15px; background-color: white; border-radius: 10px; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">
        <div style="display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 15px; font-weight: bold; color: #1e293b;">
            <span>{label}</span>
            <span style="color: #0f172a;">{current:,.0f} / {target:,.0f}원 ({ratio*100:.1f}%)</span>
        </div>
        <div style="width: 100%; background-color: #e2e8f0; border-radius: 8px; height: 12px; overflow: hidden;">
            <div style="width: {pct}%; background-color: {color}; height: 100%; border-radius: 8px; transition: width 0.5s ease-in-out;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def parse_amount(expr):
    try:
        expr = str(expr).replace(',', '').replace(' ', '')
        clean_expr = re.sub(r'[^0-9+\-*/().]', '', expr)
        if not clean_expr: return 0
        return int(eval(clean_expr))
    except: return 0

conn = st.connection("gsheets", type=GSheetsConnection)
default_columns = ["id", "date", "type", "amount", "asset_out", "asset_in", "category", "memo"]

@st.cache_data(show_spinner=False, ttl="10m")
def fetch_gsheets_data():
    try:
        df_raw = conn.read(worksheet="Transactions", ttl=0)
        settings_raw = conn.read(worksheet="Settings", ttl=0)
        
        # 데이터가 아예 없는 경우에만 뼈대 생성 (원본 데이터 보호 로직)
        if df_raw is None or (not df_raw.empty and 'amount' not in df_raw.columns):
            df_raw = pd.DataFrame(columns=default_columns)
            
        if settings_raw is None or (not settings_raw.empty and '설정구분' not in settings_raw.columns):
            settings_raw = pd.DataFrame(columns=["설정구분", "항목이름", "계좌종류", "연결계좌", "정산일", "결제일", "초기잔액"])
            
        return df_raw, settings_raw, True, ""
    except Exception as e:
        # 에러 발생 시 덮어쓰지 않고 빈 껍데기만 임시 반환하여 원본 보호
        return pd.DataFrame(columns=default_columns), pd.DataFrame(), False, str(e)

df, settings_df, use_gsheets, gsheets_error_msg = fetch_gsheets_data()
if not df.empty and 'id' in df.columns: df['id'] = df['id'].astype(str)

def save_settings():
    if use_gsheets:
        rows = []
        for cat in st.session_state.exp_categories: rows.append({"설정구분": "지출분류", "항목이름": cat})
        for cat in st.session_state.inc_categories: rows.append({"설정구분": "수입분류", "항목이름": cat})
        for atype in st.session_state.asset_types: rows.append({"설정구분": "자산종류", "항목이름": atype})
        
        rows.append({"설정구분": "예산목표", "항목이름": "월지출", "초기잔액": st.session_state.monthly_budget})
        for acc_name, goal in st.session_state.asset_goals.items():
            rows.append({"설정구분": "자산목표", "항목이름": acc_name, "초기잔액": goal})
            
        for acc_name, acc_data in st.session_state.accounts.items():
            rows.append({
                "설정구분": "계좌", "항목이름": acc_name, "계좌종류": acc_data.get("type"), "연결계좌": acc_data.get("linked"),
                "정산일": acc_data.get("settle_day"), "결제일": acc_data.get("pay_day"), "초기잔액": acc_data.get("initial_balance")
            })
        new_settings_df = pd.DataFrame(rows, columns=["설정구분", "항목이름", "계좌종류", "연결계좌", "정산일", "결제일", "초기잔액"])
        try: 
            conn.update(worksheet="Settings", data=new_settings_df)
            fetch_gsheets_data.clear() 
        except Exception: pass

def save_data(new_df):
    if use_gsheets:
        conn.update(worksheet="Transactions", data=new_df)
        fetch_gsheets_data.clear() 
    else: st.session_state.transactions = new_df

if 'exp_categories' not in st.session_state: st.session_state.exp_categories = ["식사/음료", "마트/생필품", "교통/차량", "문화/생활", "주거/통신", "개인사용"]
if 'inc_categories' not in st.session_state: st.session_state.inc_categories = ["월급", "기타수입", "보너스"]
if 'asset_types' not in st.session_state: st.session_state.asset_types = ["은행", "예적금", "투자", "신용카드", "체크카드", "집계제외"]
if 'monthly_budget' not in st.session_state: st.session_state.monthly_budget = 1000000
if 'asset_goals' not in st.session_state: st.session_state.asset_goals = {}
if 'accounts' not in st.session_state:
    st.session_state.accounts = {
        "국민은행": {"type": "은행", "linked": None, "settle_day": None, "pay_day": None, "initial_balance": 0},
        "신한카드": {"type": "신용카드", "linked": "국민은행", "settle_day": 1, "pay_day": 14, "initial_balance": 0},
    }
if 'current_date' not in st.session_state: st.session_state.current_date = date.today()
if 'edit_tx_id' not in st.session_state: st.session_state.edit_tx_id = None 

if not settings_df.empty and '설정구분' in settings_df.columns:
    def get_list(col_name): return settings_df[settings_df['설정구분'] == col_name]['항목이름'].dropna().astype(str).str.strip().tolist()
    
    exp = get_list('지출분류')
    if exp: st.session_state.exp_categories = [x for x in exp if x and x != 'nan']
    if "개인사용" not in st.session_state.exp_categories: st.session_state.exp_categories.append("개인사용")
    
    inc = get_list('수입분류')
    if inc: st.session_state.inc_categories = [x for x in inc if x and x != 'nan']
    
    atypes = get_list('자산종류')
    if atypes: st.session_state.asset_types = [x for x in atypes if x and x != 'nan']
    for req_type in ["은행", "예적금", "투자", "신용카드", "체크카드", "집계제외"]:
        if req_type not in st.session_state.asset_types:
            st.session_state.asset_types.append(req_type)
    
    budget_df = settings_df[settings_df['설정구분'] == '예산목표']
    if not budget_df.empty:
        try: st.session_state.monthly_budget = int(float(budget_df.iloc[0]['초기잔액']))
        except: pass
        
    asset_goals_df = settings_df[settings_df['설정구분'] == '자산목표']
    loaded_goals = {}
    for _, row in asset_goals_df.iterrows():
        try: loaded_goals[str(row['항목이름']).strip()] = int(float(row['초기잔액']))
        except: pass
    if loaded_goals: st.session_state.asset_goals = loaded_goals
    
    acc_df = settings_df[settings_df['설정구분'] == '계좌']
    if not acc_df.empty:
        loaded_accs = {}
        for _, row in acc_df.iterrows():
            name = str(row['항목이름']).strip()
            if not name or name == 'nan': continue
            def safe_int(v):
                try: return int(float(v)) if pd.notna(v) and str(v).strip() not in ['', 'nan'] else None
                except: return None
            l_acc = str(row['연결계좌']).strip()
            loaded_accs[name] = {
                "type": str(row['계좌종류']).strip() if pd.notna(row['계좌종류']) and str(row['계좌종류']).strip() != 'nan' else "은행",
                "linked": l_acc if l_acc and l_acc != 'nan' else None,
                "settle_day": safe_int(row['정산일']), "pay_day": safe_int(row['결제일']), "initial_balance": safe_int(row['초기잔액']) or 0
            }
        if loaded_accs: st.session_state.accounts = loaded_accs

target_year, target_month = st.session_state.current_date.year, st.session_state.current_date.month

def calculate_historical_balances(data_df, accounts_dict):
    if data_df.empty: return {}
    temp_df = data_df.sort_values(by=['date', 'id'], kind='mergesort', ascending=[True, True]).copy()
    run_bals = {acc: data.get('initial_balance', 0) for acc, data in accounts_dict.items()}
    hist_bals = {}
    
    for idx, row in temp_df.iterrows():
        r_id = str(row['id'])
        out_bal, in_bal = None, None
        amt = float(row['amount']) if pd.notna(row['amount']) else 0
        
        real_out = row['asset_out']
        if real_out in accounts_dict and accounts_dict[real_out]['type'] == '체크카드':
            real_out = accounts_dict[real_out].get('linked')
            
        real_in = row['asset_in']
        if real_in in accounts_dict and accounts_dict[real_in]['type'] == '체크카드':
            real_in = accounts_dict[real_in].get('linked')
        
        if row['type'] == '지출' and real_out in run_bals:
            run_bals[real_out] -= amt
            out_bal = run_bals[real_out]
        elif row['type'] == '수입' and real_in in run_bals:
            run_bals[real_in] += amt
            in_bal = run_bals[real_in]
        elif row['type'] == '이체':
            if real_out in run_bals:
                run_bals[real_out] -= amt
                out_bal = run_bals[real_out]
            if real_in in run_bals:
                run_bals[real_in] += amt
                in_bal = run_bals[real_in]
                
        hist_bals[r_id] = {'out': out_bal, 'in': in_bal}
    return hist_bals

historical_balances = calculate_historical_balances(df, st.session_state.accounts)

st.markdown("<h3 style='text-align:center;'>💕 우리집 가계부</h3>", unsafe_allow_html=True)
col1, col2, col3 = st.columns([1, 2.5, 1], vertical_alignment="center")

with col1:
    if st.button("◀", use_container_width=True, key="prev_month_btn"):
        st.session_state.current_date = date(target_year, target_month, 1) - timedelta(days=1)
        st.rerun()
with col2:
    st.markdown("<span class='month-nav-anchor'></span>", unsafe_allow_html=True)
    with st.popover(f"📅 {target_year}년 {target_month}월", use_container_width=True):
        p_c1, p_c2 = st.columns(2)
        with p_c1: j_y = st.number_input("연도", 2000, 2100, target_year)
        with p_c2: j_m = st.number_input("월", 1, 12, target_month)
        if st.button("🚀 이동", use_container_width=True, type="primary"):
            st.session_state.current_date = date(j_y, j_m, 1)
            st.rerun()
with col3:
    if st.button("▶", use_container_width=True, key="next_month_btn"):
        last_day = calendar.monthrange(target_year, target_month)[1]
        st.session_state.current_date = date(target_year, target_month, last_day) + timedelta(days=1)
        st.rerun()
st.write("") 

if not df.empty and 'date' in df.columns:
    df['date'] = pd.to_datetime(df['date']).dt.date
    month_df = df[(pd.to_datetime(df['date']).dt.year == target_year) & (pd.to_datetime(df['date']).dt.month == target_month)]
    year_df = df[pd.to_datetime(df['date']).dt.year == target_year]
else: 
    month_df = pd.DataFrame(columns=default_columns)
    year_df = pd.DataFrame(columns=default_columns)

@st.dialog("✏️ 내역 수정 및 삭제")
def edit_transaction_dialog(row_id):
    global df
    if df.empty or row_id not in df['id'].values:
        st.error("이미 삭제되었거나 존재하지 않는 내역입니다.")
        return
        
    row = df[df['id'] == row_id].iloc[0]
    idx_type = ["지출", "수입", "이체"].index(row['type']) if row['type'] in ["지출", "수입", "이체"] else 0
    e_type = st.radio("유형", ["지출", "수입", "이체"], horizontal=True, index=idx_type)
    e_date = st.date_input("날짜", row['date'])
    e_amt_str = st.text_input("금액 (계산식 가능)", value=str(row['amount']))
    e_amt = parse_amount(e_amt_str)
    
    cat_list = st.session_state.exp_categories if e_type == "지출" else st.session_state.inc_categories if e_type == "수입" else ["이체"]
    idx_cat = cat_list.index(row['category']) if row['category'] in cat_list else 0
    e_cat = st.selectbox("분류", cat_list, index=idx_cat)
    e_memo = st.text_input("메모", value=row['memo'])
    
    acc_list = ["-"] + list(st.session_state.accounts.keys())
    e_out, e_in = "-", "-"
    if e_type == "지출":
        e_out = st.selectbox("결제수단", acc_list, index=acc_list.index(row['asset_out']) if row['asset_out'] in acc_list else 0)
    elif e_type == "수입":
        e_in = st.selectbox("입금처", acc_list, index=acc_list.index(row['asset_in']) if row['asset_in'] in acc_list else 0)
    else:
        e_out = st.selectbox("출금", acc_list, index=acc_list.index(row['asset_out']) if row['asset_out'] in acc_list else 0)
        e_in = st.selectbox("입금", acc_list, index=acc_list.index(row['asset_in']) if row['asset_in'] in acc_list else 0)
        
    c_save, c_del = st.columns(2)
    if c_save.button("💾 저장", use_container_width=True):
        df.loc[df['id'] == row_id, ['date', 'type', 'amount', 'category', 'memo', 'asset_out', 'asset_in']] = [
            e_date, e_type, e_amt, e_cat, e_memo, e_out if e_out != "-" else None, e_in if e_in != "-" else None
        ]
        save_data(df)
        st.session_state.current_date = e_date 
        st.rerun()
    if c_del.button("🗑 삭제", type="primary", use_container_width=True):
        df = df[df['id'] != row_id]
        save_data(df)
        st.rerun()

@st.dialog("📝 분류 설정 수정")
def edit_category_dialog(state_key, item_name, is_system_asset=False):
    items = st.session_state[state_key]
    new_item = st.text_input("새 이름", value=item_name)
    
    c1, c2 = st.columns(2)
    if c1.button("💾 저장", use_container_width=True, type="primary"):
        if new_item and new_item != item_name and new_item not in items:
            idx = items.index(item_name)
            items[idx] = new_item
            
            global df
            if state_key == "exp_categories": df.loc[(df['type'] == '지출') & (df['category'] == item_name), 'category'] = new_item
            elif state_key == "inc_categories": df.loc[(df['type'] == '수입') & (df['category'] == item_name), 'category'] = new_item
            if state_key != "asset_types": save_data(df)
            
            save_settings()
            st.rerun()
        elif new_item == item_name:
            st.rerun()
        else:
            st.error("중복된 이름이거나 빈 칸입니다.")
            
    if c2.button("🗑️ 삭제", use_container_width=True):
        if len(items) <= 1 and not is_system_asset:
            st.error("최소 1개는 유지해야 합니다.")
        else:
            items.remove(item_name)
            save_settings()
            st.rerun()

@st.dialog("💳 자산 계좌 수정")
def edit_account_dialog(acc_name):
    info = st.session_state.accounts[acc_name]
    m_name = st.text_input("자산 이름", acc_name)
    m_type = st.selectbox("종류", st.session_state.asset_types, index=st.session_state.asset_types.index(info['type']) if info['type'] in st.session_state.asset_types else 0)
    m_init = st.number_input("초기 잔액", value=info.get('initial_balance', 0), step=10000)
    
    m_link = info.get('linked')
    m_set = info.get('settle_day') or 1
    m_pay = info.get('pay_day') or 14
    
    if m_type in ["신용카드", "체크카드"]:
        bl = [k for k, v in st.session_state.accounts.items() if v['type'] not in ['신용카드', '체크카드', '집계제외'] and k != acc_name]
        m_link = st.selectbox("연결 계좌", ["-"] + bl, index=bl.index(m_link)+1 if m_link in bl else 0)
    if m_type == "신용카드":
        m_set = st.number_input("정산 기준일 (시작일)", 1, 31, m_set)
        m_pay = st.number_input("결제 출금일", 1, 31, m_pay)
        
    c1, c2 = st.columns(2)
    if c1.button("💾 저장", use_container_width=True, type="primary"):
        new_info = {
            'type': m_type, 'initial_balance': m_init,
            'linked': m_link if m_type in ["신용카드", "체크카드"] and m_link != "-" else None,
            'settle_day': m_set if m_type == "신용카드" else None,
            'pay_day': m_pay if m_type == "신용카드" else None
        }
        
        temp_dict = {}
        for k, v in st.session_state.accounts.items():
            if k == acc_name: temp_dict[m_name] = new_info
            else: temp_dict[k] = v
        st.session_state.accounts = temp_dict
        
        if m_name != acc_name:
            global df
            df.loc[df['asset_out'] == acc_name, 'asset_out'] = m_name
            df.loc[df['asset_in'] == acc_name, 'asset_in'] = m_name
            save_data(df)
            
        save_settings()
        st.rerun()
        
    if c2.button("🗑️ 삭제", use_container_width=True):
        del st.session_state.accounts[acc_name]
        save_settings()
        st.rerun()

@st.dialog("📊 상세 내역 조회")
def chart_detail_dialog(chart_title, cat_name, cat_amt, cat_pct, detail_df):
    st.markdown(f"#### 🏷️ {cat_name} 상세 내역")
    st.markdown(f"**총 {cat_amt:,.0f}원** ({cat_pct:.1f}%)")
    st.divider()
    
    if detail_df.empty:
        st.info("해당 기간에 등록된 내역이 없습니다.")
    else:
        for _, row in detail_df.iterrows():
            render_transaction_item(row, f"cd_{row['id']}", show_date=True, is_readonly=True)

def format_acc_with_bal(acc_name, bal):
    if bal is None: return acc_name
    return f"{acc_name} 💳{bal:,.0f}원"

def render_transaction_item(row, prefix_key, show_date=False, is_readonly=False):
    row_id = str(row['id'])
    h_bals = historical_balances.get(row_id, {'out': None, 'in': None})
    
    if row['type'] == '지출': 
        icon, amt_str = "🔴", f"-{row['amount']:,.0f}원"
        acc_info = format_acc_with_bal(row['asset_out'], h_bals['out'])
    elif row['type'] == '수입': 
        icon, amt_str = "🔵", f"+{row['amount']:,.0f}원"
        acc_info = format_acc_with_bal(row['asset_in'], h_bals['in'])
    else: 
        icon, amt_str = "🔄", f"{row['amount']:,.0f}원"
        acc_info = f"{format_acc_with_bal(row['asset_out'], h_bals['out'])}➔{format_acc_with_bal(row['asset_in'], h_bals['in'])}"
    
    date_prefix = f"{pd.to_datetime(row['date']).strftime('%m.%d')} | " if show_date else ""
    display_text = f"{date_prefix}{icon} {amt_str} ┃ {row['memo']} ({row['category']} · {acc_info})"
    
    if is_readonly:
        st.markdown(f"""
        <div style="padding: 12px 8px; border-bottom: 1px solid #f0f4f8; color: #1e293b; font-size: 14px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
            {display_text}
        </div>
        """, unsafe_allow_html=True)
    else:
        if st.button(display_text, key=f"{prefix_key}_{row_id}", type="tertiary", use_container_width=True):
            st.session_state.edit_tx_id = row_id
            st.rerun()

if st.session_state.edit_tx_id:
    tx_id_to_edit = st.session_state.edit_tx_id
    st.session_state.edit_tx_id = None 
    edit_transaction_dialog(tx_id_to_edit)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📒 내역", "📊 통계", "🔍 검색", "💰 자산", "⚙ 설정"])

with tab1:
    stat_month_df = month_df[month_df['category'] != '개인사용']
    total_inc = stat_month_df[stat_month_df['type'] == '수입']['amount'].sum() if not stat_month_df.empty else 0
    total_exp = stat_month_df[stat_month_df['type'] == '지출']['amount'].sum() if not stat_month_df.empty else 0
    
    custom_progress_bar(total_exp, st.session_state.monthly_budget, is_expense=True, label="🎯 이번 달 지출 예산")
    
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("수입", f"{total_inc:,.0f} 원")
    col_b.metric("지출", f"{total_exp:,.0f} 원")
    col_c.metric("합계", f"{total_inc - total_exp:,.0f} 원")
    st.caption("💡 *'개인사용' 분류는 위 통계 실적 합산에서 제외됩니다.*")
    
    today = date.today()
    if target_year == today.year and target_month == today.month:
        if today.month == 1: prev_m, prev_y = 12, today.year - 1
        else: prev_m, prev_y = today.month - 1, today.year
        max_days = calendar.monthrange(prev_y, prev_m)[1]
        compare_day = min(today.day, max_days)
        
        prev_df = df[(pd.to_datetime(df['date']).dt.year == prev_y) & 
                     (pd.to_datetime(df['date']).dt.month == prev_m) & 
                     (pd.to_datetime(df['date']).dt.day <= compare_day)]
        prev_df = prev_df[prev_df['category'] != '개인사용']
        prev_exp = prev_df[prev_df['type'] == '지출']['amount'].sum() if not prev_df.empty else 0
        
        if prev_exp > 0:
            diff = total_exp - prev_exp
            if diff > 0: st.error(f"🚨 지난달 {compare_day}일 기준보다 **{diff:,.0f}원 더** 쓰고 있어요!")
            elif diff < 0: st.success(f"🎉 지난달 {compare_day}일 기준보다 **{abs(diff):,.0f}원 덜** 썼어요!")
    else:
        if target_month == 1: prev_m, prev_y = 12, target_year - 1
        else: prev_m, prev_y = target_month - 1, target_year
        prev_df = df[(pd.to_datetime(df['date']).dt.year == prev_y) & (pd.to_datetime(df['date']).dt.month == prev_m)]
        prev_df = prev_df[prev_df['category'] != '개인사용']
        prev_exp = prev_df[prev_df['type'] == '지출']['amount'].sum() if not prev_df.empty else 0
        
        if prev_exp > 0:
            diff = total_exp - prev_exp
            if diff > 0: st.error(f"📉 전월 대비 **{diff:,.0f}원 더** 썼네요.")
            elif diff < 0: st.success(f"📈 전월 대비 **{abs(diff):,.0f}원 덜** 썼습니다.")
            
    st.divider()

    with st.expander("➕ 새로운 내역 등록하기", expanded=False):
        tx_type = st.radio("유형", ["지출", "수입", "이체"], horizontal=True)
        tx_date = st.date_input("날짜", st.session_state.current_date)
        tx_amt_str = st.text_input("금액 (계산식 가능)", value="")
        tx_amt = parse_amount(tx_amt_str)
        if tx_amt_str: st.caption(f"↳ 계산 금액: **{tx_amt:,.0f} 원**")
        
        tx_cat = st.selectbox("분류", st.session_state.exp_categories if tx_type == "지출" else st.session_state.inc_categories if tx_type == "수입" else ["이체"])
        tx_memo = st.text_input("메모")
        
        acc_out, acc_in = "-", "-"
        if tx_type == "지출": acc_out = st.selectbox("결제수단", ["-"] + list(st.session_state.accounts.keys()))
        elif tx_type == "수입": acc_in = st.selectbox("입금처", ["-"] + list(st.session_state.accounts.keys()))
        else:
            c1, c2 = st.columns(2)
            with c1: acc_out = st.selectbox("출금", ["-"] + list(st.session_state.accounts.keys()))
            with c2: acc_in = st.selectbox("입금", ["-"] + list(st.session_state.accounts.keys()))
            
        if st.button("등록 완료", use_container_width=True, type="primary"):
            if tx_amt <= 0: st.error("금액을 정확히 입력하세요.")
            else:
                new_row = {"id": str(uuid.uuid4()), "date": tx_date, "type": tx_type, "amount": tx_amt, 
                           "asset_out": acc_out if acc_out != "-" else None, "asset_in": acc_in if acc_in != "-" else None, 
                           "category": tx_cat, "memo": tx_memo}
                updated_df = pd.DataFrame([new_row]) if df.empty else pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                save_data(updated_df)
                st.session_state.current_date = tx_date
                st.rerun()

    if not month_df.empty:
        sorted_dates = sorted(month_df['date'].unique(), reverse=True)
        days_kr = ["월", "화", "수", "목", "금", "토", "일"]
        
        for d in sorted_dates:
            group = month_df[month_df['date'] == d].sort_values(by=['date', 'id'], ascending=[False, False])
            day_idx = pd.to_datetime(d).weekday()
            
            day_inc = group[group['type'] == '수입']['amount'].sum()
            day_exp = group[group['type'] == '지출']['amount'].sum()
            
            st.markdown(f"""
            <div style='margin-top:15px; margin-bottom:5px; padding:6px 10px; background-color: #f1f5f9; border-radius: 6px; border-left: 4px solid #3b82f6;'>
                <b style='color:#0f172a; font-size: 15px;'>{d.day}일 ({days_kr[day_idx]})</b> 
                <span style='font-size:13px; color:#475569; float:right; font-weight:bold;'>수 {day_inc:,.0f} | 지 <span style='color:#dc2626'>{day_exp:,.0f}</span></span>
            </div>
            """, unsafe_allow_html=True)
            
            for _, row in group.iterrows():
                render_transaction_item(row, "t1", show_date=False)
    else: st.info("이번 달 내역이 없습니다.")

with tab2:
    period_m, period_y = st.tabs([f"📅 {target_month}월", f"🗓️ {target_year}년"])
    
    def render_chart_with_details(df_sub, group_col, chart_title, prefix_key, color_theme):
        if df_sub.empty or 'category' not in df_sub.columns:
            st.info("해당 내역이 없습니다. (개인사용 제외)")
            return

        df_sub = df_sub[df_sub['category'] != '개인사용']
        
        if df_sub.empty:
            st.info("해당 내역이 없습니다. (개인사용 제외)")
            return

        sum_df = df_sub.groupby(group_col)['amount'].sum().reset_index().sort_values(by='amount', ascending=False)
        total_amt = sum_df['amount'].sum()
        
        sum_df['root'] = f"총액<br>{total_amt:,.0f}원"
        
        fig = px.sunburst(
            sum_df, 
            path=['root', group_col], 
            values='amount',
            color=group_col,
            color_discrete_sequence=color_theme
        )
        
        fig.update_traces(
            texttemplate='<b>%{label}</b><br>%{value:,.0f}원', 
            textfont=dict(color='black', size=14), 
            insidetextfont=dict(color='black'), 
            hovertemplate='<b>%{label}</b><br>%{value:,.0f}원<extra></extra>',
            marker=dict(line=dict(color='#ffffff', width=2)),
            insidetextorientation='auto' 
        )
        
        fig.update_layout(
            margin=dict(t=10, b=10, l=10, r=10),
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            clickmode='event+select'
        )
        
        st.markdown(f"<div style='margin-bottom: 5px; font-size:14px; font-weight:bold; color:#3b82f6; text-align:center;'>👇 차트 조각을 터치하면 상세 내역이 열립니다!</div>", unsafe_allow_html=True)

        click_state_key = f"last_clicked_{prefix_key}"
        if click_state_key not in st.session_state:
            st.session_state[click_state_key] = None

        chart_selection = st.plotly_chart(
            fig, 
            use_container_width=True, 
            key=f"chart_{prefix_key}",
            on_select="rerun" 
        )

        if chart_selection and "selection" in chart_selection:
            points = chart_selection["selection"].get("points", [])
            if points:
                pt = points[0]
                selected_cat = pt.get("label")
                
                if selected_cat and "총액" not in selected_cat and selected_cat in sum_df[group_col].values:
                    if st.session_state[click_state_key] != selected_cat:
                        st.session_state[click_state_key] = selected_cat
                        
                        cat_amt = sum_df[sum_df[group_col] == selected_cat]['amount'].sum()
                        cat_pct = (cat_amt / total_amt) * 100
                        detail_df = df_sub[df_sub[group_col] == selected_cat].sort_values(by=['date', 'id'], ascending=[False, False])
                        
                        chart_detail_dialog(chart_title, selected_cat, cat_amt, cat_pct, detail_df)
            else:
                st.session_state[click_state_key] = None

    def render_stats(data_df, period_key):
        exp_df = data_df[data_df['type'] == '지출'] if not data_df.empty else pd.DataFrame(columns=default_columns)
        inc_df = data_df[data_df['type'] == '수입'] if not data_df.empty else pd.DataFrame(columns=default_columns)

        stat_t1, stat_t2, stat_t3 = st.tabs(["지출 (분류별)", "지출 (결제수단별)", "수입 (분류별)"])
        
        with stat_t1: render_chart_with_details(exp_df, 'category', "지출 분류", f"{period_key}_exp_cat", px.colors.qualitative.Pastel)
        with stat_t2: render_chart_with_details(exp_df, 'asset_out', "결제 수단", f"{period_key}_exp_acc", px.colors.qualitative.Set3)
        with stat_t3: render_chart_with_details(inc_df, 'category', "수입 분류", f"{period_key}_inc_cat", px.colors.qualitative.Set2)

    with period_m: render_stats(month_df, "month")
    with period_y: render_stats(year_df, "year")

with tab3:
    st.subheader("🔍 내역 통합 검색")
    sq = st.text_input("검색어 (메모, 분류, 금액, 결제수단)", placeholder="예: 마트, 15000, 국민은행")
    
    if sq and not df.empty:
        sq_low = sq.lower()
        s_df = df[
            df['memo'].astype(str).str.lower().str.contains(sq_low) |
            df['category'].astype(str).str.lower().str.contains(sq_low) |
            df['amount'].astype(str).str.contains(sq_low) |
            df['asset_out'].astype(str).str.lower().str.contains(sq_low) |
            df['asset_in'].astype(str).str.lower().str.contains(sq_low)
        ]
        
        st.markdown(f"**총 {len(s_df)}건의 검색 결과가 있습니다.**")
        if not s_df.empty:
            s_df = s_df.sort_values(by=["date", "id"], ascending=[False, False])
            for _, row in s_df.iterrows():
                render_transaction_item(row, "s", show_date=True)
    elif sq: st.info("검색 결과가 없습니다.")

with tab4:
    balances = {acc: data.get('initial_balance', 0) for acc, data in st.session_state.accounts.items()}
    if not df.empty:
        for _, row in df.iterrows():
            amt = float(row['amount']) if pd.notna(row['amount']) else 0
            r_out, r_in = row['asset_out'], row['asset_in']
            if r_out in st.session_state.accounts and st.session_state.accounts[r_out]['type'] == '체크카드':
                r_out = st.session_state.accounts[r_out].get('linked')
            if r_in in st.session_state.accounts and st.session_state.accounts[r_in]['type'] == '체크카드':
                r_in = st.session_state.accounts[r_in].get('linked')
                
            if row['type'] == '지출' and r_out in balances: balances[r_out] -= amt
            elif row['type'] == '수입' and r_in in balances: balances[r_in] += amt
            elif row['type'] == '이체':
                if r_out in balances: balances[r_out] -= amt
                if r_in in balances: balances[r_in] += amt

    total_assets = sum(bal for acc, bal in balances.items() if acc in st.session_state.accounts and st.session_state.accounts[acc]['type'] in ['은행', '예적금', '투자'])
    
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #4f46e5, #3b82f6); padding:20px; border-radius:12px; text-align:center; margin-top:10px; margin-bottom:25px; color:white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
        <h4 style='margin:0; font-size:15px; font-weight:normal; opacity:0.9;'>💎 총 자산 (입출금 + 저축성)</h4>
        <h1 style='margin:10px 0 0 0; font-size:32px;'>{total_assets:,.0f} 원</h1>
    </div>
    """, unsafe_allow_html=True)

    banks = {acc: bal for acc, bal in balances.items() if acc in st.session_state.accounts and st.session_state.accounts[acc]['type'] == '은행'}
    if banks:
        st.markdown("#### 🏦 입출금 자산 (은행)")
        for acc, bal in banks.items():
            st.markdown(f"""
            <div style="margin-bottom: 10px; padding: 15px; background-color: white; border-radius: 10px; border: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 15px; font-weight: bold; color: #1e293b;">🏦 {acc}</span>
                <span style="font-size: 16px; font-weight: bold; color: #0f172a;">{bal:,.0f} 원</span>
            </div>
            """, unsafe_allow_html=True)
            
    savings = {acc: bal for acc, bal in balances.items() if acc in st.session_state.accounts and st.session_state.accounts[acc]['type'] in ['예적금', '투자']}
    if savings:
        st.markdown("<h4 style='margin-top:20px;'>🌱 저축성 자산 (예적금/투자)</h4>", unsafe_allow_html=True)
        for acc, bal in savings.items():
            goal = st.session_state.asset_goals.get(acc, 0)
            icon = "🌱" if st.session_state.accounts[acc]['type'] == '예적금' else "📈"
            if goal > 0:
                custom_progress_bar(bal, goal, is_expense=False, label=f"{icon} {acc} 목표")
            else:
                st.markdown(f"""
                <div style="margin-bottom: 10px; padding: 15px; background-color: white; border-radius: 10px; border: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 15px; font-weight: bold; color: #1e293b;">{icon} {acc}</span>
                    <span style="font-size: 16px; font-weight: bold; color: #0f172a;">{bal:,.0f} 원</span>
                </div>
                """, unsafe_allow_html=True)
                
    cc_accounts = {k: v for k, v in st.session_state.accounts.items() if v['type'] == '신용카드'}
    if cc_accounts:
        st.markdown("<h4 style='margin-top:20px;'>💳 신용카드 결제 예정금</h4>", unsafe_allow_html=True)
        for acc, conf in cc_accounts.items():
            linked_acc = conf.get('linked')
            settle_day = conf.get('settle_day') or 1
            
            if target_month == 1: prev_m, prev_y = 12, target_year - 1
            else: prev_m, prev_y = target_month - 1, target_year
                
            _, prev_last_day = calendar.monthrange(prev_y, prev_m)
            actual_s_day = min(settle_day, prev_last_day)
            def_start = date(prev_y, prev_m, actual_s_day)
            
            if settle_day == 1:
                _, last_day = calendar.monthrange(prev_y, prev_m)
                def_end = date(prev_y, prev_m, last_day)
            else:
                _, curr_last_day = calendar.monthrange(target_year, target_month)
                actual_e_day = min(settle_day - 1, curr_last_day)
                def_end = date(target_year, target_month, max(1, actual_e_day))
            
            with st.container(border=True):
                st.markdown(f"<div style='font-size:15px; font-weight:bold; color:#1e293b; margin-bottom:10px;'>💳 {acc} <span style='font-size:13px; color:#64748b; font-weight:normal;'>(연결: {linked_acc if linked_acc and linked_acc != '-' else '없음'})</span></div>", unsafe_allow_html=True)
                
                c1, c2 = st.columns(2)
                with c1: dr = st.date_input("이용 기간", value=(def_start, def_end), key=f"dr_{acc}_{target_year}_{target_month}")
                with c2: pd_date = st.date_input("결제(출금)일", value=date(target_year, target_month, conf.get('pay_day') or 14), key=f"pd_{acc}_{target_year}_{target_month}")
                    
                bill_amt = 0
                memo_text = ""
                already_paid = False
                
                if isinstance(dr, tuple) and len(dr) == 2:
                    s_dt, e_dt = dr
                    memo_text = f"{acc} 대금 정산 ({s_dt.strftime('%m.%d')}~{e_dt.strftime('%m.%d')})"
                    
                    if not df.empty:
                        temp_dates = pd.to_datetime(df['date']).dt.date
                        mask = (temp_dates >= s_dt) & (temp_dates <= e_dt)
                        df_period = df[mask]
                        exp = df_period[(df_period['asset_out'] == acc) & (df_period['type'] == '지출')]['amount'].sum()
                        ref = df_period[(df_period['asset_in'] == acc) & (df_period['type'] == '수입')]['amount'].sum()
                        bill_amt = exp - ref
                        
                        paid_df = df[(df['type'] == '이체') & (df['asset_in'] == acc) & (df['memo'] == memo_text)]
                        if not paid_df.empty:
                            already_paid = True

                c_info, c_btn = st.columns([7, 3], vertical_alignment="center")
                with c_info:
                    if already_paid: st.success(f"✅ 결제 완료 ({bill_amt:,.0f}원)")
                    elif bill_amt > 0: st.info(f"결제 예정액 : **{bill_amt:,.0f} 원**")
                    elif bill_amt < 0: st.success(f"환불 초과 (-{-bill_amt:,.0f} 원)")
                    else: st.success("결제 대금이 없습니다. ✅")
                        
                with c_btn:
                    if bill_amt > 0 and not already_paid:
                        if not linked_acc or linked_acc == "-": st.caption("연결계좌 없음")
                        else:
                            if st.button("💳 결제", key=f"pay_{acc}_{target_year}_{target_month}", use_container_width=True, type="primary"):
                                if linked_acc in balances and balances[linked_acc] < bill_amt:
                                    st.error(f"연결 계좌 잔액 부족!")
                                else:
                                    new_row = {
                                        "id": str(uuid.uuid4()), "date": pd_date, "type": "이체", 
                                        "amount": int(bill_amt), "asset_out": linked_acc, "asset_in": acc, 
                                        "category": "이체", "memo": memo_text
                                    }
                                    updated_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True) if not df.empty else pd.DataFrame([new_row])
                                    save_data(updated_df)
                                    st.session_state.current_date = pd_date
                                    st.rerun()

    excluded_accs = {acc: bal for acc, bal in balances.items() if acc in st.session_state.accounts and st.session_state.accounts[acc]['type'] == '집계제외'}
    if excluded_accs:
        st.markdown("<h4 style='margin-top:20px;'>👻 예외 자산 (집계 제외)</h4>", unsafe_allow_html=True)
        for acc, bal in excluded_accs.items():
            st.markdown(f"""
            <div style="margin-bottom: 10px; padding: 15px; background-color: #f8fafc; border-radius: 10px; border: 1px dashed #cbd5e1; display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 15px; font-weight: bold; color: #64748b;">👻 {acc}</span>
                <span style="font-size: 16px; font-weight: bold; color: #64748b;">{bal:,.0f} 원</span>
            </div>
            """, unsafe_allow_html=True)

with tab5:
    st.subheader("⚙ 가계부 설정")
    
    with st.expander("🎯 예산 및 자산 목표 설정", expanded=False):
        st.write("이번 달 예산과 저축 목표를 설정하면 게이지 바가 나타납니다.")
        new_budget = st.number_input("이번 달 총 지출 예산", value=st.session_state.monthly_budget, step=100000)
        
        st.write("##### 🌱 예적금/투자 모으기 목표")
        new_asset_goals = {}
        has_savings = any(info['type'] in ['예적금', '투자'] for info in st.session_state.accounts.values())
        
        for acc_name, info in st.session_state.accounts.items():
            if info['type'] in ["예적금", "투자"]: 
                val = st.session_state.asset_goals.get(acc_name, 0)
                new_val = st.number_input(f"[{acc_name}] 목표액 (0은 미설정)", value=val, step=1000000)
                if new_val > 0: new_asset_goals[acc_name] = new_val
        
        if not has_savings:
            st.warning("등록된 '예적금' 또는 '투자' 자산이 없습니다. 먼저 하단의 자산 목록에서 추가해주세요.")
                
        if st.button("목표 저장하기", type="primary", use_container_width=True):
            st.session_state.monthly_budget = new_budget
            st.session_state.asset_goals = new_asset_goals
            save_settings()
            st.rerun()

    def render_inline_list(items, title, state_key, is_system=False):
        with st.expander(f"📝 {title}", expanded=False):
            if not items: st.caption("등록된 항목이 없습니다.")
            
            for i in range(len(items)):
                item = items[i]
                c_btn, c_up, c_dn = st.columns([7, 1.5, 1.5], vertical_alignment="center")
                
                with c_btn:
                    st.markdown("<div class='settings-btn'>", unsafe_allow_html=True)
                    if is_system and item in ["신용카드", "체크카드", "은행", "예적금", "투자", "집계제외"]:
                        st.button(f"🔒 {item}", key=f"btn_{title}_{item}", type="tertiary", use_container_width=True, disabled=True)
                    else:
                        if st.button(f"• {item}", key=f"btn_{title}_{item}", type="tertiary", use_container_width=True):
                            edit_category_dialog(state_key, item, is_system)
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                with c_up:
                    if i > 0 and st.button("🔼", key=f"up_{state_key}_{item}", use_container_width=True):
                        items[i-1], items[i] = items[i], items[i-1]
                        save_settings()
                        st.rerun()
                with c_dn:
                    if i < len(items) - 1 and st.button("🔽", key=f"dn_{state_key}_{item}", use_container_width=True):
                        items[i+1], items[i] = items[i], items[i+1]
                        save_settings()
                        st.rerun()
            
            st.divider()
            c_new, c_add = st.columns([7, 3])
            new_item = c_new.text_input("새 항목 이름", key=f"new_{title}", placeholder="항목 입력", label_visibility="collapsed")
            if c_add.button("추가", key=f"add_{title}", use_container_width=True):
                if new_item and new_item not in items:
                    items.append(new_item)
                    save_settings()
                    st.rerun()

    render_inline_list(st.session_state.exp_categories, "지출 분류 관리", "exp_categories")
    render_inline_list(st.session_state.inc_categories, "수입 분류 관리", "inc_categories")
    render_inline_list(st.session_state.asset_types, "자산 종류 관리", "asset_types", is_system=True)

    with st.expander("💳 자산(계좌/카드) 목록 및 순서 관리", expanded=False):
        acc_keys = list(st.session_state.accounts.items())
        
        for i, (acc_name, info) in enumerate(acc_keys):
            c_btn, c_up, c_dn = st.columns([7, 1.5, 1.5], vertical_alignment="center")
            with c_btn:
                st.markdown("<div class='settings-btn'>", unsafe_allow_html=True)
                if st.button(f"💳 {acc_name} ({info['type']})", key=f"btn_acc_{acc_name}", type="tertiary", use_container_width=True):
                    edit_account_dialog(acc_name)
                st.markdown("</div>", unsafe_allow_html=True)
            
            with c_up:
                if i > 0 and st.button("🔼", key=f"up_{acc_name}", use_container_width=True):
                    acc_keys[i-1], acc_keys[i] = acc_keys[i], acc_keys[i-1]
                    st.session_state.accounts = dict(acc_keys)
                    save_settings()
                    st.rerun()
            with c_dn:
                if i < len(acc_keys)-1 and st.button("🔽", key=f"dn_{acc_name}", use_container_width=True):
                    acc_keys[i+1], acc_keys[i] = acc_keys[i], acc_keys[i+1]
                    st.session_state.accounts = dict(acc_keys)
                    save_settings()
                    st.rerun()

        st.divider()
        st.write("##### ➕ 새로운 자산 등록")
        n_acc_name = st.text_input("새 계좌/카드 이름", key="na_name")
        n_acc_type = st.selectbox("종류 선택", st.session_state.asset_types, key="na_type")
        n_init = st.number_input("초기 잔액", value=0, step=10000, key="na_init")
        n_linked, n_settle, n_pay = None, None, None
        
        if n_acc_type in ["신용카드", "체크카드"]:
            bl = [k for k, v in st.session_state.accounts.items() if v['type'] not in ['신용카드', '체크카드', '집계제외']]
            n_linked = st.selectbox("연결 계좌", ["-"] + bl, key="na_link")
        if n_acc_type == "신용카드":
            n_settle = st.number_input("정산 기준일 (매월 시작일)", 1, 31, 1, key="na_set")
            n_pay = st.number_input("결제 출금일", 1, 31, 14, key="na_pay")
            
        if st.button("자산 등록", key="na_btn", use_container_width=True, type="primary"):
            if n_acc_name and n_acc_name not in st.session_state.accounts:
                st.session_state.accounts[n_acc_name] = {
                    "type": n_acc_type, "linked": n_linked if n_linked != "-" else None,
                    "settle_day": n_settle, "pay_day": n_pay, "initial_balance": n_init
                }
                save_settings()
                st.rerun()

if not use_gsheets:
    st.error(f"🚨 구글 시트 연동 오류: {gsheets_error_msg}")
    if "429" in gsheets_error_msg or "Quota exceeded" in gsheets_error_msg:
        st.warning("💡 **구글 시트 1분당 호출 제한(60회)에 도달했습니다.**\n\n이전의 과도한 새로고침이나 잦은 접속으로 인해 구글 측에서 일시적으로 앱을 1분간 차단한 상태입니다. 구글의 제한은 매 분 리셋되므로, **조금만 기다리신 후 아래 버튼을 눌러주세요!**")
        if st.button("🔄 다시 시도하기 (1분 뒤 클릭)", use_container_width=True, type="primary"):
            fetch_gsheets_data.clear()
            st.rerun()
