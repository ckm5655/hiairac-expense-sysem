import datetime
import os
import uuid
import json
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, send_file
import openpyxl
from openpyxl.styles import Font, Border, Side, Alignment, PatternFill
from io import BytesIO
from datetime import datetime
from dateutil.relativedelta import relativedelta

app = Flask(__name__)
app.secret_key = "trip_unified_advanced_system_2026"

# 🗄️ SQLite 데이터베이스 파일명 고정
DB_FILE = "expense_system.db"

USER_CREDENTIALS = {
    "admin": {"password": "1234", "name": "관리자", "team": "관리자"},
    "생산": {"password": "1234", "name": "생산", "team": "생산팀"},
    "영업": {"password": "1234", "name": "영업", "team": "영업팀"},
    "시운전": {"password": "1234", "name": "시운전", "team": "시운전팀"},
    "전장": {"password": "1234", "name": "전장", "team": "전장팀"}
}

ACCOUNT_MAPPING = {
    "교통비": "512", "주차비": "512", "식비": "512",
    "차량유지비": "522", "운반비": "524", "통신비": "513",
    "소모품비": "530", "택배비": "524", "수수료": "531", "기타": "-"
}

ADVANCE_DB = {"시운전팀": 500000, "생산팀": 300000, "영업팀": 1000000, "전장팀": 700000, "관리자": 0}

def convert_to_standard_category(user_category):
    if user_category in ["교통비", "주차비"]: return "교통비"
    elif user_category in ["식비", "식대비"]: return "식대비"
    elif user_category == "숙박비": return "숙박비"
    elif user_category in ["소모품", "소모품비"]: return "소모품비"
    elif user_category in ["차량유지비", "유류비"]: return "차량유지비"
    else: return "기타"

# 🛠️ SQLite DB 및 테이블 생성 초기화 함수
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id TEXT PRIMARY KEY,
            trip_id TEXT,
            display_order INTEGER,
            date TEXT,
            place TEXT,
            content TEXT,
            category TEXT,
            amount INTEGER,
            user_name TEXT,
            team TEXT
        )
    ''')
    conn.commit()
    
    # 데이터가 없을 시 기본 샘플 데이터 자동 생성
    cursor.execute("SELECT COUNT(*) FROM expenses")
    if cursor.fetchone()[0] == 0:
        sample_data = [
            ("e1", "t1", 1, "2026-04-15", "삼성중공업", "SPOT COOLER 점검 지원", "식비", 12000, "곽무성", "시운전팀"),
            ("e2", "t1", 1, "2026-04-15", "삼성중공업", "SPOT COOLER 점검 지원", "주차비", 5000, "곽무성", "시운전팀"),
            ("e3", "t2", 2, "2026-04-16", "현대삼호", "PRECOOLER 납품 실사", "소모품비", 25000, "김휘권", "시운전팀"),
            ("e4", "t3", 1, "2026-04-10", "울산공장", "생산 라인 설비 소모품 조달", "소모품비", 240000, "박생산", "생산팀"),
            ("e5", "t4", 1, "2026-04-18", "서울본사", "바이어 기술 미팅 및 식대", "식비", 185000, "최영업", "영업팀"),
            ("e6", "t4", 1, "2026-04-18", "서울본사", "바이어 기술 미팅 및 식대", "교통비", 63000, "최영업", "영업팀"),
            ("e7", "t5", 3, "2026-04-22", "삼성중공업", "시운전 장비 추가 정비", "교통비", 45000, "곽무성", "시운전팀"),
            ("e8", "t6", 2, "2026-04-25", "울산공장", "생산 2라인 부품 원재료 구매", "기타", 120000, "이생산", "생산팀")
        ]
        cursor.executemany('''
            INSERT INTO expenses (id, trip_id, display_order, date, place, content, category, amount, user_name, team)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', sample_data)
        conn.commit()
    conn.close()

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = dict_factory
    return conn

# 구동 시점에 DB 점검 수행
init_db()

def get_unified_trips(target_month, team_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if team_name == "관리자":
        cursor.execute("SELECT * FROM expenses WHERE date LIKE ?", (target_month + '%',))
    else:
        cursor.execute("SELECT * FROM expenses WHERE team = ? AND date LIKE ?", (team_name, target_month + '%'))
    
    filtered = cursor.fetchall()
    conn.close()
    
    trip_groups = {}
    for exp in filtered:
        tid = exp['trip_id']
        if tid not in trip_groups:
            trip_groups[tid] = {
                "trip_id": tid, "order": exp['display_order'], "date": exp['date'],
                "user_name": exp['user_name'], "place": exp['place'],
                "content": exp['content'], "team": exp['team'], "total_amount": 0, "details": []
            }
        trip_groups[tid]["total_amount"] += exp['amount']
        trip_groups[tid]["details"].append({
            "id": exp['id'], "category": exp['category'], "amount": exp['amount']
        })
    
    for tid, data in trip_groups.items():
        data["details_json"] = json.dumps(data["details"])
        
    return sorted(trip_groups.values(), key=lambda x: (x['team'], x['order']))


@app.route('/')
def home():
    if 'username' in session: return redirect(url_for('index'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password').strip()
        
        if username in USER_CREDENTIALS and USER_CREDENTIALS[username]['password'] == password:
            session['username'] = USER_CREDENTIALS[username]['name']
            session['user_id'] = username
            session['team'] = USER_CREDENTIALS[username]['team']
            return redirect(url_for('index'))
        else:
            error = "아이디 또는 비밀번호가 올바르지 않습니다."
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/index', methods=['GET'])
def index():
    if 'username' not in session: return redirect(url_for('login'))
    
    current_month = request.args.get('search_month', "2026-04")
    user_team = session['team']
    
    unified_trips = get_unified_trips(current_month, user_team)
    
    target_date = datetime.strptime(current_month, "%Y-%m")
    start_month = (target_date - relativedelta(months=5)).strftime("%Y-%m")
    end_month = target_date.strftime("%Y-%m")

    conn = get_db_connection()
    cursor = conn.cursor()
    
    if user_team == "관리자":
        cursor.execute("SELECT * FROM expenses WHERE substr(date, 1, 7) BETWEEN ? AND ?", (start_month, end_month))
    else:
        cursor.execute("SELECT * FROM expenses WHERE team = ? AND substr(date, 1, 7) BETWEEN ? AND ?", (user_team, start_month, end_month))
        
    filtered_data = cursor.fetchall()
    conn.close()
    
    raw_stats_list = []
    dashboard_stats = {'총합': 0, '시운전팀': 0, '생산팀': 0, '영업팀': 0, '전장팀': 0}
    
    for item in filtered_data:
        t_name = item['team']
        if not t_name.endswith('팀') and t_name != '관리자':
            t_name += '팀'
            
        dashboard_stats[t_name] = dashboard_stats.get(t_name, 0) + item['amount']
        dashboard_stats['총합'] += item['amount']
        
        raw_stats_list.append({
            'team': t_name,
            'place': item['place'],
            'std_category': convert_to_standard_category(item['category']),
            'amount': item['amount'],
            'date': item['date']
        })

    return render_template(
        'index.html', 
        username=session['username'], team=user_team, 
        trips=unified_trips, categories=list(ACCOUNT_MAPPING.keys()), 
        current_month=current_month,
        dashboard_stats=dashboard_stats,
        raw_stats_json=json.dumps(raw_stats_list)
    )

@app.route('/admin', methods=['GET'])
def admin_page():
    if 'username' not in session or session['team'] != "관리자":
        return redirect(url_for('login'))
        
    selected_team = request.args.get('team', '시운전팀')
    target_month = request.args.get('month', '2026-04')
    
    if not selected_team.endswith('팀') and selected_team != '관리자':
        selected_team += '팀'

    conn = get_db_connection()
    cursor = conn.cursor()
    
    if selected_team == "관리자":
        cursor.execute("SELECT * FROM expenses WHERE date LIKE ? ORDER BY date DESC, display_order ASC", (target_month + '%',))
    else:
        cursor.execute("SELECT * FROM expenses WHERE team = ? AND date LIKE ? ORDER BY display_order ASC", (selected_team, target_month + '%'))
        
    expenses = cursor.fetchall()
    conn.close()
    
    processed_expenses = []
    for exp in expenses:
        day_only = exp['date'].split('-')[2] if '-' in exp['date'] else exp['date']
        processed_expenses.append({
            'team': exp['team'],
            'date': int(day_only),
            'user_name': exp['user_name'],
            'place': exp['place'],
            'content': exp['content'],
            'category': exp['category'],
            'amount': exp['amount']
        })

    return render_template(
        'admin.html', 
        expenses=processed_expenses, 
        selected_team=selected_team,
        current_month=target_month
    )

@app.route('/expense/add', methods=['POST'])
def add_expense():
    if 'username' not in session: return redirect(url_for('login'))
    
    current_month = request.form.get('search_month')
    expense_date = request.form.get('expense_date')
    user_name = request.form.get('user_name').strip()
    place = request.form.get('place').strip()
    content = request.form.get('content').strip()
    categories = request.form.getlist('receipt_category')
    amounts = request.form.getlist('receipt_amount')

    if session['team'] == "관리자":
        chosen_team = request.form.get('target_team', '시운전팀')
    else:
        chosen_team = session['team']
        
    if not chosen_team.endswith('팀') and chosen_team != '관리자':
        chosen_team += '팀'

    new_trip_id = str(uuid.uuid4())
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(display_order) FROM expenses WHERE team = ?", (chosen_team,))
    row = cursor.fetchone()
    max_order = row['MAX(display_order)'] if row else 0
    assigned_order = (max_order if max_order else 0) + 1

    for i in range(len(categories)):
        amt_str = amounts[i].strip()
        if not amt_str: continue 
        
        cursor.execute('''
            INSERT INTO expenses (id, trip_id, display_order, date, place, content, category, amount, user_name, team)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (str(uuid.uuid4()), new_trip_id, assigned_order, expense_date, place, content, categories[i], int(amt_str), user_name, chosen_team))
        
    conn.commit()
    conn.close()
    return redirect(url_for('index', search_month=current_month))

@app.route('/expense/reorder', methods=['POST'])
def reorder_expense():
    current_month = request.form.get('search_month')
    trip_ids = request.form.getlist('trip_ids')
    display_orders = request.form.getlist('display_orders')

    conn = get_db_connection()
    cursor = conn.cursor()
    for i in range(len(trip_ids)):
        cursor.execute('''
            UPDATE expenses SET display_order = ? WHERE trip_id = ?
        ''', (int(display_orders[i]), trip_ids[i]))
    conn.commit()
    conn.close()
    return redirect(url_for('index', search_month=current_month))

@app.route('/expense/edit', methods=['POST'])
def edit_expense():
    current_month = request.form.get('search_month')
    target_trip_id = request.form.get('trip_id')
    
    new_date = request.form.get('expense_date')
    new_user = request.form.get('user_name').strip()
    new_place = request.form.get('place').strip()
    new_content = request.form.get('content').strip()
    
    sub_ids = request.form.getlist('sub_receipt_ids')
    sub_categories = request.form.getlist('sub_receipt_categories')
    sub_amounts = request.form.getlist('sub_receipt_amounts')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE expenses SET date = ?, user_name = ?, place = ?, content = ? WHERE trip_id = ?
    ''', (new_date, new_user, new_place, new_content, target_trip_id))
    
    for i in range(len(sub_ids)):
        cursor.execute('''
            UPDATE expenses SET category = ?, amount = ? WHERE id = ?
        ''', (sub_categories[i], int(sub_amounts[i]), sub_ids[i]))
        
    conn.commit()
    conn.close()
    return redirect(url_for('index', search_month=current_month))

@app.route('/expense/delete/<string:trip_id>', methods=['GET'])
def delete_expense(trip_id):
    current_month = request.args.get('search_month')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM expenses WHERE trip_id = ?", (trip_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index', search_month=current_month))

@app.route('/download/cover')
def download_cover():
    if 'username' not in session: return redirect(url_for('login'))

    selected_team = request.args.get('team', session['team'])
    target_month = request.args.get('month', "2026-04")
    
    if not selected_team.endswith('팀') and selected_team != '관리자':
        selected_team += '팀'
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM expenses WHERE team = ? AND date LIKE ? ORDER BY display_order ASC", (selected_team, target_month + '%'))
    raw_data = cursor.fetchall()
    conn.close()
    
    wb = openpyxl.Workbook()
    ws1 = wb.active
    ws1.title = "표지시트"
    ws1.views.sheetView[0].showGridLines = True
    
    font_title = Font(name="맑은 고딕", size=16, bold=True)
    font_bold = Font(name="맑은 고딕", size=10, bold=True)
    font_main = Font(name="맑은 고딕", size=10)
    gray_fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
    thin_border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
    
    month_data = target_month.split('-')
    ws1['A2'] = f" {month_data[1]}월 개인경비 사용내역 ({selected_team}) "
    ws1['A2'].font = font_title
    
    ws1.merge_cells('H2:H3'); ws1['H2'] = "결\n재"
    ws1['I2'] = "담당"; ws1['J2'] = "팀장"; ws1['K2'] = "소장"
    for r in [2, 3]:
        for c in ['H', 'I', 'J', 'K']:
            ws1[f"{c}{r}"].border = thin_border
            ws1[f"{c}{r}"].alignment = Alignment(horizontal='center', vertical='center')
            if r == 2 or c == 'H': ws1[f"{c}{r}"].fill = gray_fill
            
    grouped_events = {}
    for exp in raw_data:
        group_key = exp['trip_id']
        std_cat = convert_to_standard_category(exp['category'])
        if group_key not in grouped_events:
            grouped_events[group_key] = {
                "date": f"{int(exp['date'].split('-')[2])}일" if '-' in exp['date'] else exp['date'], 
                "content": exp['content'], "place": exp['place'],
                "user_name": exp['user_name'], "min_order": exp['display_order'], "금액": 0,
                "교통비": 0, "식대비": 0, "숙박비": 0, "소모품비": 0, "차량유지비": 0, "기타": 0
            }
        grouped_events[group_key]["금액"] += exp['amount']
        grouped_events[group_key][std_cat] += exp['amount']
        
    sorted_events = sorted(grouped_events.values(), key=lambda x: x['min_order'])
    
    headers1 = ["순번", "일자", "내      용", "출장지", "금액", "교통비", "식대비", "숙박비", "소모품비", "차량유지비", "기타", "사용자"]
    for col_idx, text in enumerate(headers1, 1):
        cell = ws1.cell(row=7, column=col_idx, value=text)
        cell.font = font_bold; cell.fill = gray_fill; cell.border = thin_border; cell.alignment = Alignment(horizontal='center')

    r_idx = 8
    for idx, ev in enumerate(sorted_events, 1):
        row_values = [idx, ev['date'], ev['content'], ev['place'], ev['금액'], ev['교통비'], ev['식대비'], ev['숙박비'], ev['소모품비'], ev['차량유지비'], ev['기타'], ev['user_name']]
        for c_idx, val in enumerate(row_values, 1):
            cell = ws1.cell(row=r_idx, column=c_idx, value=val)
            cell.font = font_main; cell.border = thin_border
            if c_idx in [1, 2, 4, 12]: cell.alignment = Alignment(horizontal='center')
            elif c_idx == 3: cell.alignment = Alignment(horizontal='left')
            else: cell.alignment = Alignment(horizontal='right'); cell.number_format = '#,##0'
        r_idx += 1

    ws1.cell(row=r_idx, column=3, value="합계").font = font_bold
    ws1.cell(row=r_idx, column=3).alignment = Alignment(horizontal='center')
    for c_idx, ltr in enumerate(['E','F','G','H','I','J','K'], start=5):
        cell = ws1.cell(row=r_idx, column=c_idx, value=f"=SUM({ltr}8:{ltr}{r_idx-1})")
        cell.font = font_bold; cell.border = thin_border; cell.alignment = Alignment(horizontal='right'); cell.number_format = '#,##0'
    for c in [1, 2, 4, 12]: ws1.cell(row=r_idx, column=c).border = thin_border

    r_idx += 2
    ws1.cell(row=r_idx, column=2, value="▶ 부서 정산 수령금 대조 현황").font = font_bold
    advance_amt = ADVANCE_DB.get(selected_team, 0)
    
    ws1.cell(row=r_idx+1, column=2, value="부서 가지급금 총액").fill = gray_fill; ws1.cell(row=r_idx+1, column=3, value=advance_amt).number_format = '#,##0'
    ws1.cell(row=r_idx+2, column=2, value="실제 경비 집행 총액").fill = gray_fill; ws1.cell(row=r_idx+2, column=3, value=f"=E{r_idx-2}").number_format = '#,##0'
    ws1.cell(row=r_idx+3, column=2, value="정산 정산 잔액 (+/-)").fill = gray_fill; ws1.cell(row=r_idx+3, column=3, value=f"=C{r_idx+1}-C{r_idx+2}").font = font_bold; ws1.cell(row=r_idx+3, column=3).number_format = '#,##0'
    for k in range(1, 4):
        ws1.cell(row=r_idx+k, column=2).border = thin_border; ws1.cell(row=r_idx+k, column=3).border = thin_border

    ws2 = wb.create_sheet(title="경비시트")
    ws2.views.sheetView[0].showGridLines = True
    ws2['A1'] = f" {month_data[1]}월 개인경비 사용내역 ({selected_team}) "
    ws2['A1'].font = font_title
    
    headers2 = ["일자", "영수증번호", "내용", "출장지", "구분", "금액", "사용자", "계정코드"]
    for col_idx, text in enumerate(headers2, 1):
        cell = ws2.cell(row=5, column=col_idx, value=text)
        cell.font = font_bold; cell.fill = gray_fill; cell.border = thin_border; cell.alignment = Alignment(horizontal='center')
        
    r_idx2 = 6
    last_trip_id = None
    receipt_seq = 1
    for exp in raw_data:
        if last_trip_id == exp['trip_id']: receipt_seq += 1
        else: receipt_seq = 1; last_trip_id = exp['trip_id']
            
        day_val = int(exp['date'].split('-')[2]) if '-' in exp['date'] else exp['date']
        ac_code = ACCOUNT_MAPPING.get(exp['category'], "-")
        
        ws2.cell(row=r_idx2, column=1, value=day_val).alignment = Alignment(horizontal='center')
        ws2.cell(row=r_idx2, column=2, value=receipt_seq).alignment = Alignment(horizontal='center')
        ws2.cell(row=r_idx2, column=3, value=exp['content']).alignment = Alignment(horizontal='left')
        ws2.cell(row=r_idx2, column=4, value=exp['place']).alignment = Alignment(horizontal='center')
        ws2.cell(row=r_idx2, column=5, value=exp['category']).alignment = Alignment(horizontal='center')
        
        amt_cell = ws2.cell(row=r_idx2, column=6, value=exp['amount'])
        amt_cell.alignment = Alignment(horizontal='right'); amt_cell.number_format = '#,##0'
        
        ws2.cell(row=r_idx2, column=7, value=exp['user_name']).alignment = Alignment(horizontal='center')
        ws2.cell(row=r_idx2, column=8, value=ac_code).alignment = Alignment(horizontal='center')
        
        for c in range(1, 9):
            ws2.cell(row=r_idx2, column=c).font = font_main; ws2.cell(row=r_idx2, column=c).border = thin_border
        r_idx2 += 1
        
    ws2.cell(row=r_idx2, column=3, value="총 합계").font = font_bold; ws2.cell(row=r_idx2, column=3).alignment = Alignment(horizontal='center')
    sum_cell = ws2.cell(row=r_idx2, column=6, value=f"=SUM(F6:F{r_idx2-1})")
    sum_cell.font = font_bold; sum_cell.border = thin_border; sum_cell.alignment = Alignment(horizontal='right'); sum_cell.number_format = '#,##0'
    for c in [1,2,4,5,7,8]: ws2.cell(row=r_idx2, column=c).border = thin_border

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return send_file(output, as_attachment=True, download_name=f"{target_month}_{selected_team}_경비정산서.xlsx")

@app.route('/download/convert')
def download_convert():
    if 'username' not in session or session['team'] != "관리자":
        return redirect(url_for('login'))

    selected_team = request.args.get('team', '시운전팀')
    target_month = request.args.get('month', '2026-04')
    
    if not selected_team.endswith('팀') and selected_team != '관리자':
        selected_team += '팀'

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM expenses WHERE team = ? AND date LIKE ? ORDER BY display_order ASC", (selected_team, target_month + '%'))
    raw_data = cursor.fetchall()
    conn.close()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "ERP_UPLOAD"
    
    headers = ["일자", "부서명", "사원명", "계정코드", "계정명", "금액", "적요"]
    for col_idx, text in enumerate(headers, 1):
        ws.cell(row=1, column=col_idx, value=text)

    r_idx = 2
    for exp in raw_data:
        day_val = exp['date'].split('-')[2] if '-' in exp['date'] else exp['date']
        ac_code = ACCOUNT_MAPPING.get(exp['category'], "-")
        
        ws.cell(row=r_idx, column=1, value=int(day_val))
        ws.cell(row=r_idx, column=2, value=exp['team'])
        ws.cell(row=r_idx, column=3, value=exp['user_name'])
        ws.cell(row=r_idx, column=4, value=ac_code)
        ws.cell(row=r_idx, column=5, value=exp['category'])
        ws.cell(row=r_idx, column=6, value=exp['amount'])
        ws.cell(row=r_idx, column=7, value=f"{exp['place']} - {exp['content']}")
        r_idx += 1

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return send_file(output, as_attachment=True, download_name=f"ERP_CONVERT_{target_month}_{selected_team}.xlsx")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
