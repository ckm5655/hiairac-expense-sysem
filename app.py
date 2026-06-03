import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import calendar
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import io
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- [구글 시트 연동 설정] ---
CREDENTIALS_FILE = "credentials.json"  # 구글 API JSON 키 파일 이름
SPREADSHEET_NAME = "vacation_data"     # 구글 스프레드시트 파일 이름

# --- [사내 아웃룩 연동] 메일 발송을 위한 핵심 설정 ---
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "ckm5655@gmail.com"
SENDER_PASSWORD = "qoycvfxxcexgoygb"

def get_gspread_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
    client = gspread.authorize(creds)
    return client

def load_data():
    if not os.path.exists(CREDENTIALS_FILE):
        st.error(f"❌ '{CREDENTIALS_FILE}' 파일이 없습니다. 구글 API 키를 먼저 설정해주세요.")
        st.stop()
    try:
        client = get_gspread_client()
        sheet = client.open(SPREADSHEET_NAME)
        
        # Employees 데이터 로드
        ws_emp = sheet.worksheet("Employees")
        df_emp = pd.DataFrame(ws_emp.get_all_records())
        if not df_emp.empty:
            df_emp['ID'] = df_emp['ID'].astype(str)
            df_emp['PASSWORD'] = df_emp['PASSWORD'].astype(str)
            numeric_cols = ['연차기초', '사용', '연차계획', '연차잔액']
            for col in numeric_cols:
                if col in df_emp.columns:
                    df_emp[col] = pd.to_numeric(df_emp[col].replace('', 0), errors='coerce').astype(float)
        
        # PLANS 데이터 로드
        ws_plans = sheet.worksheet("PLANS")
        df_plans = pd.DataFrame(ws_plans.get_all_records())
        if not df_plans.empty:
            df_plans['Date'] = df_plans['Date'].astype(str)
            df_plans['Emp_ID'] = df_plans['Emp_ID'].astype(str)
            
        for col in ["Reason", "Manager_Sign"]:
            if col not in df_plans.columns:
                df_plans[col] = ""
            else:
                df_plans[col] = df_plans[col].fillna("").astype(str)
                
        return df_emp, df_plans
    except Exception as e:
        st.error(f"❌ 구글 시트 로드 오류: {e}")
        st.stop()

def load_notices():
    try:
        client = get_gspread_client()
        sheet = client.open(SPREADSHEET_NAME)
        ws_notices = sheet.worksheet("NOTICES")
        df_notices = pd.DataFrame(ws_notices.get_all_records())
        if df_notices.empty:
            return pd.DataFrame(columns=["ID", "날짜", "제목", "내용"])
        return df_notices
    except:
        return pd.DataFrame(columns=["ID", "날짜", "제목", "내용"])

def save_all_data(df_emp, df_plans, df_notices):
    try:
        client = get_gspread_client()
        sheet = client.open(SPREADSHEET_NAME)
        
        # 데이터프레임의 결측치(NaN)를 빈 문자열로 변환하고, JSON 오류 방지를 위해 모든 데이터를 문자열로 캐스팅
        df_emp_clean = df_emp.fillna("").astype(str)
        df_plans_clean = df_plans.fillna("").astype(str)
        df_notices_clean = df_notices.fillna("").astype(str)

        # 1. Employees 업데이트
        ws_emp = sheet.worksheet("Employees")
        ws_emp.clear()
        ws_emp.update([df_emp_clean.columns.values.tolist()] + df_emp_clean.values.tolist())

        # 2. PLANS 업데이트
        ws_plans = sheet.worksheet("PLANS")
        ws_plans.clear()
        ws_plans.update([df_plans_clean.columns.values.tolist()] + df_plans_clean.values.tolist())

        # 3. NOTICES 업데이트
        ws_notices = sheet.worksheet("NOTICES")
        ws_notices.clear()
        ws_notices.update([df_notices_clean.columns.values.tolist()] + df_notices_clean.values.tolist())
        
    except Exception as e:
        st.error(f"❌ 구글 시트 저장 실패: {e}")

def save_data(df_emp, df_plans):
    save_all_data(df_emp, df_plans, load_notices())

def save_notices(df_notices):
    df_emp, df_plans = load_data()
    save_all_data(df_emp, df_plans, df_notices)

df_emp, df_plans = load_data()

def send_vacation_email(user_email, user_name, target_date):
    subject = f"[스마트연차시스템] {user_name}님, 7일 후 연차(예정일: {target_date}) 안내드립니다."
    body = f"""안녕하세요.
곧 예정된 연차 일정을 미리 안내드립니다.

■ 대상자 : {user_name} 사원
■ 사용일자 : {target_date}

연차 사용 전 진행 중인 업무 및 인수인계 사항을 최종 확인하여 주시기 바랍니다.
긴급사항 발생 시 부서 내 담당자와 공유 부탁드립니다.
감사합니다."""

    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = user_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, user_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        return False

st.set_page_config(page_title="사내 연차 관리 시스템", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'user_info': None})

if not st.session_state['logged_in']:
    st.title("🔐 사내 연차 관리 시스템")
    with st.form("login"):
        i_id, i_pw = st.text_input("ID(사번)"), st.text_input("비밀번호", type="password")
        if st.form_submit_button("로그인"):
            user = df_emp[(df_emp['ID'] == i_id) & (df_emp['PASSWORD'] == i_pw)]
            if not user.empty:
                st.session_state.update({'logged_in': True, 'user_info': user.iloc[0]})
                st.rerun()
            else: st.error("정보가 올바르지 않습니다.")
    st.stop()

user_info = df_emp[df_emp['ID'] == st.session_state['user_info']['ID']].iloc[0]

st.sidebar.title(f"👤 {user_info['이름']} ({user_info['permission']})")
menu = ["📢 공지사항(연차촉진)", "🏠 내 연차 신청/현황", "📑 신청서 출력"]
if user_info['permission'] in ["팀장", "총괄"]:
    menu += ["✅ 팀원 승인/반려 관리", "📅 연차 현황 달력", "📊 부서/전사 모니터링"]
if user_info['permission'] == "총괄":
    menu += ["🌐 [총괄] 전사 통합 관리"]

choice = st.sidebar.radio("메뉴 이동", menu)
if st.sidebar.button("로그아웃"):
    st.session_state['logged_in'] = False
    st.rerun()

# --- 📢 공지사항 ---
if choice == "📢 공지사항(연차촉진)":
    st.header("📢 전사 공지사항 (연차촉진 안내)")
    df_notices = load_notices()
    if df_notices.empty:
        st.info("현재 등록된 공지사항이 없습니다.")
    else:
        for idx, row in df_notices.iloc[::-1].iterrows():
            with st.expander(f"📌 [{row['날짜']}] {row['제목']}", expanded=True):
                st.write(row['내용'])
                st.caption("작성자: 최고관리자(총괄)")

# --- 🏠 내 연차 신청/현황 ---
elif choice == "🏠 내 연차 신청/현황":
    st.header("📅 나의 연차 현황")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("기초 연차", f"{user_info['연차기초']}일")
    c2.metric("사용 완료", f"{user_info['사용']}일")
    c3.metric("연차 계획", f"{user_info['연차계획']}일")
    c4.metric("남은 잔액", f"{user_info['연차잔액']}일")
    st.divider()
    
    col_l, col_r = st.columns([1, 2])
    with col_l:
        st.subheader("📝 신규 신청")
        v_date = st.date_input("날짜 선택")
        v_type = st.selectbox("구분", ["연차", "오전반차", "오후반차", "연차계획"])
        v_reason = st.text_input("✍️ 신청 사유", placeholder="예: 개인 용무, 정기 휴가 등")
        
        if st.button("신청서 제출하기"):
            d_str = v_date.strftime("%Y-%m-%d")
            dup_check = df_plans[(df_plans['Emp_ID'] == user_info['ID']) & (df_plans['Date'] == d_str) & (df_plans['Status'] != '반려')]
            if not dup_check.empty:
                st.error(f"❌ {d_str} 날짜에 이미 신청(대기/승인)된 내역이 있습니다.")
            else:
                final_reason = v_reason if v_reason.strip() else "개인 용무"
                st.session_state.update({'confirm_apply': True, 'temp_date': d_str, 'temp_type': v_type, 'temp_reason': final_reason})

        if st.session_state.get('confirm_apply'):
            st.warning(f"⚠️ {st.session_state['temp_date']} [{st.session_state['temp_type']}] 신청하시겠습니까?")
            if st.button("✅ 최종 확인"):
                new_id = int(df_plans["ID"].max() + 1) if not df_plans.empty else 1
                new_row = {"ID": new_id, "Emp_ID": user_info['ID'], "Date": st.session_state['temp_date'], "Status": "대기", "Type": st.session_state['temp_type'], "Reason": st.session_state['temp_reason'], "Manager_Sign": ""}
                df_plans = pd.concat([df_plans, pd.DataFrame([new_row])], ignore_index=True)
                save_data(df_emp, df_plans); st.success("신청되었습니다!"); del st.session_state['confirm_apply']; st.rerun()

    with col_r:
        st.subheader("🔍 나의 최근 신청 내역")
        my_h = df_plans[df_plans['Emp_ID'] == user_info['ID']].sort_values(by="Date", ascending=False)
        for idx, row in my_h.iterrows():
            cols = st.columns([3, 2, 2])
            cols[0].write(f"📅 {row['Date']} ({row['Type']})")
            cols[1].write(f"상태: {row['Status']}")
            if row['Type'] == "연차계획" and cols[2].button("연차로 변경", key=f"btn_{row['ID']}"):
                df_plans.at[idx, "Type"] = "연차"
                if row['Status'] == "승인":
                    df_emp.loc[df_emp["ID"] == user_info['ID'], ["사용","연차잔액","연차계획"]] += [1.0, -1.0, -1.0]
                save_data(df_emp, df_plans); st.rerun()

# --- 📑 신청서 출력 ---
elif choice == "📑 신청서 출력":
    st.header("🖨️ 연차 신청서 출력")
    approved_h = df_plans[(df_plans['Emp_ID'] == user_info['ID']) & (df_plans['Status'] == '승인')]
    if approved_h.empty:
        st.info("출력 가능한 승인된 연차 내역이 없습니다.")
    else:
        doc_list = approved_h.apply(lambda x: f"[{x['ID']}] {x['Date']} ({x['Type']})", axis=1).tolist()
        s_doc = st.selectbox("출력할 항목을 선택하세요", doc_list)
        s_id = int(s_doc.split(']')[0].replace('[', ''))
        doc = approved_h[approved_h['ID'] == s_id].iloc[0]
        
        print_reason = doc['Reason'] if pd.notna(doc.get('Reason')) and str(doc.get('Reason')).strip() != "" else "개인 용무"
        print_sign = doc['Manager_Sign'] if pd.notna(doc.get('Manager_Sign')) and str(doc.get('Manager_Sign')).strip() != "nan" else ""
        apply_date_str = datetime.now().strftime('%Y년 %m월 %d일')
        
        html_template = f"""
        <div style="border: 1px solid #000; padding: 40px; background-color: white; color: black; font-family: 'Malgun Gothic'; width: 700px; margin: 0 auto;">
            <div style="display: flex; justify-content: flex-end;">
                <table style="border-collapse: collapse; border: 1px solid black; text-align: center; color: black;">
                    <tr>
                        <th rowspan="2" style="border: 1px solid black; padding: 5px; width: 30px; background: #f2f2f2; font-size: 13px;">결<br>재</th>
                        <th style="border: 1px solid black; padding: 5px; width: 80px; background: #f2f2f2; font-size: 13px;">담당</th>
                        <th style="border: 1px solid black; padding: 5px; width: 80px; background: #f2f2f2; font-size: 13px;">팀장승인</th>
                        <th style="border: 1px solid black; padding: 5px; width: 80px; background: #f2f2f2; font-size: 13px;">대표승인</th>
                    </tr>
                    <tr>
                        <td style="border: 1px solid black; height: 55px; font-weight: bold; vertical-align: middle; font-size: 14px;">{user_info['이름']}</td>
                        <td style="border: 1px solid black; height: 55px; font-weight: bold; vertical-align: middle; color: blue; font-size: 14px;">{print_sign}</td>
                        <td style="border: 1px solid black; height: 55px; vertical-align: middle;"></td>
                    </tr>
                </table>
            </div>
            <h1 style="text-align: center; margin-top: 15px; color: black; font-size: 28px; letter-spacing: 5px;">연 차 휴 가 신 청 서</h1>
            <br><br>
            <table style="width: 100%; border-collapse: collapse; border: 1px solid black; color: black; font-size: 14px;">
                <tr>
                    <th style="border: 1px solid black; padding: 12px; background: #f2f2f2; width: 20%; font-weight: bold;">성 명</th>
                    <td style="border: 1px solid black; padding: 12px; width: 30%;">{user_info['이름']}</td>
                    <th style="border: 1px solid black; padding: 12px; background: #f2f2f2; width: 20%; font-weight: bold;">사 번</th>
                    <td style="border: 1px solid black; padding: 12px; width: 30%;">{user_info['ID']}</td>
                </tr>
                <tr>
                    <th style="border: 1px solid black; padding: 12px; background: #f2f2f2; font-weight: bold;">부 서</th>
                    <td style="border: 1px solid black; padding: 12px;">{user_info['팀']}</td>
                    <th style="border: 1px solid black; padding: 12px; background: #f2f2f2; font-weight: bold;">직 위</th>
                    <td style="border: 1px solid black; padding: 12px;">{user_info['permission']}</td>
                </tr>
                <tr>
                    <th style="border: 1px solid black; padding: 12px; background: #f2f2f2; font-weight: bold;">휴가 일자</th>
                    <td colspan="3" style="border: 1px solid black; padding: 12px;">{doc['Date']}</td>
                </tr>
                <tr>
                    <th style="border: 1px solid black; padding: 12px; background: #f2f2f2; font-weight: bold;">휴가 구분</th>
                    <td colspan="3" style="border: 1px solid black; padding: 12px;">{doc['Type']}</td>
                </tr>
                <tr>
                    <th style="border: 1px solid black; padding: 12px; background: #f2f2f2; height: 100px; font-weight: bold;">신청 사유</th>
                    <td colspan="3" style="border: 1px solid black; padding: 12px; vertical-align: top;">{print_reason}</td>
                </tr>
            </table>
            <br><br>
            <p style="text-align: center; margin-top: 40px; font-size: 16px; color: black;">위와 같이 연차 휴가를 신청하오니 승인하여 주시기 바랍니다.</p>
            <p style="text-align: center; margin-top: 30px; font-size: 14px; color: black;">{apply_date_str}</p>
            <br>
            <p style="text-align: right; margin-top: 20px; padding-right: 40px; font-size: 15px; color: black;">신청인 : <b style="font-size: 16px;">{user_info['이름']}</b> (인)</p>
            <br><br>
            <h2 style="text-align: center; margin-top: 20px; color: black; font-size: 22px; letter-spacing: 2px;">하이에어공조(주) 귀하</h2>
        </div>
        """

        pdf_script = f"""
        <script>
            function printPDF() {{
                var printWindow = window.open('', '_blank', 'width=800,height=900');
                printWindow.document.write('<html><head><title>연차휴가신청서_{user_info['이름']}</title>');
                printWindow.document.write('<style>body {{ margin: 0; padding: 20px; background: #fff; }}</style></head><body>');
                printWindow.document.write({repr(html_template)});
                printWindow.document.write('</body></html>');
                printWindow.document.close();
                printWindow.focus();
                setTimeout(function() {{
                    printWindow.print();
                    printWindow.close();
                }}, 250);
            }}
        </script>
        <button onclick="printPDF()" style="background-color: #FF4B4B; color: white; border: none; padding: 10px 20px; font-size: 15px; font-weight: bold; border-radius: 5px; cursor: pointer; margin-bottom: 20px; width: 100%;">
            📥 연차신청서 PDF 다운로드 / 즉시 인쇄하기
        </button>
        """
        st.components.v1.html(pdf_script, height=60)
        st.markdown(html_template, unsafe_allow_html=True)

# --- ✅ 팀원 승인/반려 관리 ---
elif choice == "✅ 팀원 승인/반려 관리":
    st.header("📥 팀원 결재 관리")
    pending = df_plans[df_plans["Status"] == "대기"].merge(df_emp[['ID', '이름', '팀']], left_on='Emp_ID', right_on='ID')
    display_df = pending[pending['팀'] == user_info['팀']] if user_info['permission'] == "팀장" else pending
    
    if display_df.empty:
        st.info("현재 결재 대기 중인 내역이 없습니다.")
    else:
        all_selected = st.checkbox("전체 선택/해제")

        display_df = display_df.copy()
        display_df['선택'] = all_selected
        
        display_df_view = display_df.rename(columns={'Reason': '신청 사유'})
        edited = st.data_editor(display_df_view[['선택','ID_x','이름','팀','Date','Type','신청 사유']], hide_index=True, use_container_width=True)
        s_ids = edited[edited['선택'] == True]['ID_x'].tolist()
        
        if s_ids:
            col_b1, col_b2 = st.columns(2)
            if col_b1.button(f"✅ {len(s_ids)}건 일괄 승인", use_container_width=True):
                for t_id in s_ids:
                    idx = df_plans[df_plans["ID"] == t_id].index[0]
                    e_id, v_type = df_plans.at[idx, "Emp_ID"], str(df_plans.at[idx, "Type"])
                    df_plans.at[idx, "Status"] = "승인"
                    df_plans.at[idx, "Manager_Sign"] = str(user_info['이름'])
                    val = 0.5 if "반차" in v_type else 1.0
                    if "연차계획" in v_type:
                        df_emp.loc[df_emp["ID"] == e_id, "연차계획"] += val
                    else:
                        df_emp.loc[df_emp["ID"] == e_id, ["사용","연차잔액"]] += [val, -val]
                save_data(df_emp, df_plans); st.success("승인 처리 완료!"); st.rerun()
            
            if col_b2.button(f"❌ {len(s_ids)}건 일괄 반려", use_container_width=True):
                for t_id in s_ids:
                    idx = df_plans[df_plans["ID"] == t_id].index[0]
                    df_plans.at[idx, "Status"] = "반려"
                    df_plans.at[idx, "Manager_Sign"] = "반려됨"
                save_data(df_emp, df_plans); st.warning("반려 처리 완료!"); st.rerun()

# --- 📅 연차 현황 달력 ---
elif choice == "📅 연차 현황 달력":
    st.header("🗓️ 연차 현황 달력")
    all_p = df_plans.merge(df_emp[['ID', '이름', '팀']], left_on='Emp_ID', right_on='ID')
    cal_p = all_p[all_p['Status'] == '승인']
    if user_info['permission'] == "팀장": cal_p = cal_p[cal_p['팀'] == user_info['팀']]
    
    t = datetime.now()
    y_col, m_col = st.columns(2)
    s_y = y_col.selectbox("연도", [t.year, t.year+1])
    s_m = m_col.selectbox("월", range(1, 13), index=t.month-1)
    
    cal_list = calendar.monthcalendar(s_y, s_m)
    st.write(f"### {s_y}년 {s_m}월")
    c_heads = st.columns(7)
    for i, d_name in enumerate(["월","화","수","목","금","토","일"]): c_heads[i].write(f"**{d_name}**")
    
    for week in cal_list:
        c_days = st.columns(7)
        for i, day in enumerate(week):
            if day != 0:
                target_dt = f"{s_y}-{s_m:02d}-{day:02d}"
                evs = cal_p[cal_p['Date'] == target_dt]
                txt = f"**{day}**"
                for _, ev in evs.iterrows():
                    color = "#E3F2FD" if "반차" not in ev['Type'] else "#FFFDE7"
                    txt += f"\n<div style='font-size:0.7em; background:{color}; padding:2px; border-radius:3px; margin-top:2px; color:black;'>{ev['이름']}</div>"
                c_days[i].markdown(txt, unsafe_allow_html=True)
        st.divider()

# --- 📊 부서/전사 모니터링 ---
elif choice == "📊 부서/전사 모니터링":
    if user_info['permission'] == "총괄":
        st.header("🌐 전사 임직원 연차 현황")
        st.dataframe(df_emp[['팀', 'ID', '이름', '연차기초', '사용', '연차계획', '연차잔액']], use_container_width=True, hide_index=True, height=600)
    else:
        st.header(f"🚩 {user_info['팀']} 부서 연차 현황")
        dept_df = df_emp[df_emp['팀'] == user_info['팀']]
        st.dataframe(dept_df[['ID', '이름', '연차기초', '사용', '연차계획', '연차잔액']], use_container_width=True, hide_index=True)

# --- 🌐 [총괄] 전사 통합 관리 ---
elif choice == "🌐 [총괄] 전사 통합 관리":
    # 혹시 모를 로컬 백업용 (엑셀 파일 메모리 생성 유지)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_emp.to_excel(writer, sheet_name="Employees", index=False)
        df_plans.to_excel(writer, sheet_name="PLANS", index=False)
        load_notices().to_excel(writer, sheet_name="NOTICES", index=False)
    buffer.seek(0)
    st.download_button("📥 현재 구글시트 최신 데이터를 엑셀 백업본으로 다운로드", data=buffer, file_name="vacation_data_backup.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
    st.divider()

    tab_list, tab_stat, tab_notice, tab_mail, tab_emp = st.tabs(["📋 전사 로그 관리", "📈 월간 사용 통계", "📝 연차촉진 공지사항 관리", "📧 내일 연차자 메일 발송", "👥 임직원 정보 관리"])
    
    with tab_list:
        all_logs = df_plans.merge(df_emp[['ID', '이름', '팀']], left_on='Emp_ID', right_on='ID')
        all_logs['선택'] = False
        ed_logs = st.data_editor(all_logs[['선택','ID_x','이름','팀','Date','Type','Status']], hide_index=True)
        del_ids = ed_logs[ed_logs['선택'] == True]['ID_x'].tolist()
        if del_ids and st.button("🗑️ 선택 항목 삭제 및 수치 복구"):
            for di in del_ids:
                row = df_plans[df_plans['ID'] == di].iloc[0]
                if row['Status'] == '승인':
                    v = 0.5 if "반차" in row['Type'] else 1.0
                    if "연차계획" in row['Type']: df_emp.loc[df_emp['ID']==row['Emp_ID'], '연차계획'] -= v
                    else: df_emp.loc[df_emp['ID']==row['Emp_ID'], ['사용','연차잔액']] += [-v, v]
            df_plans = df_plans[~df_plans['ID'].isin(del_ids)]
            save_data(df_emp, df_plans); st.rerun()
            
    with tab_stat:
        for_s_date = st.date_input("기준 월 선택")
        t_month = for_s_date.strftime("%Y-%m")
        m_plans = df_plans[(df_plans['Date'].str.startswith(t_month)) & (df_plans['Status'] == '승인')].copy()
        m_plans['val'] = m_plans['Type'].apply(lambda x: 0.5 if "반차" in str(x) else 1.0)
        
        def get_vacation_days_str(group):
            date_strings = []
            for _, r in group.sort_values(by="Date").iterrows():
                try:
                    day_num = int(r['Date'].split('-')[2])
                    if "오전반차" in str(r['Type']): date_strings.append(f"{day_num}일(오전)")
                    elif "오후반차" in str(r['Type']): date_strings.append(f"{day_num}일(오후)")
                    else: date_strings.append(f"{day_num}일")
                except: date_strings.append(r['Date'])
            return ", ".join(date_strings)
        
        if not m_plans.empty:
            u_sum = m_plans.groupby('Emp_ID')['val'].sum().reset_index()
            u_dates = m_plans.groupby('Emp_ID').apply(get_vacation_days_str).reset_index(name='사용일')
            u_stat = u_sum.merge(u_dates, on='Emp_ID', how='left')
        else:
            u_stat = pd.DataFrame(columns=['Emp_ID', 'val', '사용일'])
        total_stat = df_emp[['팀','ID','이름']].merge(u_stat, left_on='ID', right_on='Emp_ID', how='left')
        total_stat['val'] = total_stat['val'].fillna(0); total_stat['사용일'] = total_stat['사용일'].fillna("-")
        st.dataframe(total_stat[['팀', 'ID', '이름', 'val', '사용일']].rename(columns={'val': '사용한 일수', 'ID': '사번'}), use_container_width=True, hide_index=True, height=600)

    with tab_notice:
        st.subheader("📝 연차촉진 공지사항 관리")
        df_notices = load_notices()
        tab_add, tab_edit = st.tabs(["등록", "수정/삭제"])
        with tab_add:
            with st.form("공지사항 등록 폼", clear_on_submit=True):
                n_title = st.text_input("공지사항 제목")
                n_content = st.text_area("공지 내용", height=300)
                if st.form_submit_button("📢 공지사항 등록하기") and n_title and n_content:
                    new_n_id = int(df_notices["ID"].max() + 1) if not df_notices.empty else 1
                    new_notice = pd.DataFrame([{"ID": new_n_id, "날짜": datetime.now().strftime("%Y-%m-%d"), "제목": n_title, "내용": n_content}])
                    save_notices(pd.concat([df_notices, new_notice], ignore_index=True)); st.success("🎉 등록 완료!"); st.rerun()
        with tab_edit:
            if not df_notices.empty:
                edit_target = st.selectbox("수정/삭제할 공지사항 선택", df_notices["제목"].tolist())
                target_row = df_notices[df_notices["제목"] == edit_target].iloc[0]
                with st.form("공지사항 수정 폼"):
                    e_title = st.text_input("제목", value=target_row["제목"])
                    e_content = st.text_area("내용", value=target_row["내용"], height=200)
                    col_e1, col_e2 = st.columns(2)
                    if col_e1.form_submit_button("💾 수정 저장"):
                        df_notices.loc[df_notices["제목"] == edit_target, ["제목", "내용"]] = [e_title, e_content]
                        save_notices(df_notices); st.success("수정 완료!"); st.rerun()
                    if col_e2.form_submit_button("🗑️ 영구 삭제", type="primary"):
                        save_notices(df_notices[df_notices["제목"] != edit_target]); st.warning("삭제 완료!"); st.rerun()

    with tab_mail:
        st.subheader("📧 아웃룩 메일 서버 연동 향후 7일간 연차자 확인")
        date_range = [(datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(1, 8)]
        tm_vacations = df_plans[(df_plans['Date'].isin(date_range)) & (df_plans['Status'] == '승인')]
        if tm_vacations.empty:
            st.warning("향후 7일간 승인된 연차 대상자가 없습니다.")
        else:
            mail_targets = tm_vacations.merge(df_emp[['ID', '이름', 'EMAIL']], left_on='Emp_ID', right_on='ID').sort_values(by='Date')
            st.dataframe(mail_targets[['Date', '이름', 'Type', 'EMAIL']], hide_index=True, use_container_width=True)
            if st.button("🚀 위 대상자 전원에게 안내 메일 즉시 일괄 발송"):
                success_count = 0
                for _, row in mail_targets.iterrows():
                    if "@" in str(row['EMAIL']):
                        if send_vacation_email(str(row['EMAIL']).strip(), row['이름'], row['Date']): success_count += 1
                st.success(f"🎉 총 {success_count}명의 대상 직원에게 안내 메일을 발송했습니다!")

    with tab_emp:
        st.subheader("👥 임직원 정보 관리")
        
        if 'emp_save_success' in st.session_state and st.session_state['emp_save_success']:
            st.success("✅ 임직원 정보가 성공적으로 업데이트되었습니다.")
            st.session_state['emp_save_success'] = False
            
        edited_emp = st.data_editor(df_emp, num_rows="dynamic", use_container_width=True, height=400)
        
        if st.button("💾 임직원 정보 변경 사항 저장"):
            save_all_data(edited_emp, df_plans, load_notices())
            st.session_state['emp_save_success'] = True
            st.rerun()
