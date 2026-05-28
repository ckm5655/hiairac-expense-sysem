import subprocess
import sys

# [치트키] 서버 실행 시 필요한 라이브러리가 없으면 알아서 자동 설치하는 로직
try:
    from flask import Flask, render_template, request, redirect, url_for, session, send_file
    import openpyxl
except ModuleNotFoundError:
    print("필수 라이브러리가 누락되어 자동 설치를 시작합니다...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "flask", "openpyxl"])
    from flask import Flask, render_template, request, redirect, url_for, session, send_file
    import openpyxl

import datetime
import os
import uuid
import json
from openpyxl.styles import Font, Border, Side, Alignment, PatternFill
from io import BytesIO

app = Flask(__name__)
app.secret_key = "trip_unified_advanced_system_2026"

USER_CREDENTIALS = {
    "admin": {"password": "1234", "name": "관리자", "team": "관리자"},
    "생산": {"password": "1234", "name": "생산", "team": "생산팀"},
    "영업": {"password": "1234", "name": "영업", "team": "영업팀"},
    "시운전": {"password": "1234", "name": "시운전", "team": "시운전팀"},
    "전장": {"password": "1234", "name": "전장", "team": "전장팀"}
}

ACCOUNT_MAPPING = {
    "교통비": "512", "주차비": "512", "식비": "512", "식대비": "512",
    "차량유지비": "522", "운반비": "524", "통신비": "513",
    "소모품비": "530", "택배비": "524", "수수료": "531", "숙박비": "512", "기타": "533"
}

DATA_FILE = "expenses.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print("데이터 로딩 실패:", e)
            return []
    return []

def save_data():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(ALL_EXPENSES, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print("데이터 저장 실패:", e)

ALL_EXPENSES = load_data()

@app.route('/')
def login_page():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def do_login():
    uid = request.form.get('username')
    upass = request.form.get('password')
    if uid in USER_CREDENTIALS and USER_CREDENTIALS[uid]['password'] == upass:
        session['user_id'] = uid
        session['username'] = USER_CREDENTIALS[uid]['name']
        session['team'] = USER_CREDENTIALS[uid]['team']
        return redirect(url_for('index_page'))
    return "<script>alert('로그인 정보가 올바르지 않습니다.'); history.back();</script>"

@app.route('/logout')
def do_logout():
    session.clear()
    return redirect(url_for('login_page'))

@app.route('/index')
def index_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    
    current_month = request.args.get('search_month', datetime.date.today().strftime('%Y-%m'))
    user_team = session['team']
    
    categories_list = ["교통비", "주차비", "식비", "식대비", "숙박비", "소모품비", "차량유지비", "기타"]
    
    # 1. 이번 달 기준 팀별/개인별 정산 목록 필터링
    month_data = [x for x in ALL_EXPENSES if x.get('date', '').startswith(current_month)]
    if user_team != "관리자":
        month_data = [x for x in month_data if x.get('team') == user_team]
        
    month_data.sort(key=lambda x: x.get('order', 999))
    
    trips_map = {}
    for exp in month_data:
        tid = exp['trip_id']
        if tid not in trips_map:
            trips_map[tid] = {
                'trip_id': tid,
                'order': exp.get('order', 1),
                'team': exp.get('team', ''),
                'date': exp.get('date', ''),
                'user_name': exp.get('user_name', ''),
                'place': exp.get('place', ''),
                'content': exp.get('content', ''),
                'details': [],
                'total_amount': 0
            }
        trips_map[tid]['details'].append({
            'id': exp['id'],
            'category': exp['category'],
            'amount': exp['amount']
        })
        trips_map[tid]['total_amount'] += exp['amount']
        
    trips_list = list(trips_map.values())
    trips_list.sort(key=lambda x: x['order'])
    
    for t in trips_list:
        t['details_json'] = json.dumps(t['details'], ensure_ascii=False)
        
    # 2. 대시보드 상단 미니 통계 (선택한 '당월' 전체 부서 기준 합계)
    dashboard_stats = {"총합": 0, "시운전": 0, "생산팀": 0, "영업팀": 0, "전장팀": 0}
    all_month_data = [x for x in ALL_EXPENSES if x.get('date', '').startswith(current_month)]
    for x in all_month_data:
        dashboard_stats["총합"] += x['amount']
        t_name = x['team']
        if "시운전" in t_name: dashboard_stats["시운전"] += x['amount']
        elif "생산" in t_name: dashboard_stats["생산팀"] += x['amount']
        elif "영업" in t_name: dashboard_stats["영업팀"] += x['amount']
        elif "전장" in t_name: dashboard_stats["전장팀"] += x['amount']
        
    # 3. 📊 그래프용 최근 6개월 범위 데이터 수집 로직
    try:
        base_date = datetime.datetime.strptime(current_month, "%Y-%m")
    except:
        try:
            base_date = datetime.datetime.strptime(current_month + "-01", "%Y-%m-%d")
        except:
            base_date = datetime.datetime.today()

    start_year = base_date.year
    start_month_num = base_date.month - 5
    while start_month_num <= 0:
        start_month_num += 12
        start_year -= 1
        
    start_month_str = f"{start_year}-{start_month_num:02d}"
    end_month_str = current_month

    raw_stats = []
    for x in ALL_EXPENSES:
        data_month = x.get('date', '')[:7]
        if start_month_str <= data_month <= end_month_str:
            raw_stats.append({
                'team': x['team'],
                'date': x['date'],
                'place': x['place'],
                'category': x['category'],
                'amount': x['amount']
            })
        
    return render_template('index.html', 
                           username=session['username'], 
                           team=user_team,
                           current_month=current_month,
                           categories=categories_list,
                           trips=trips_list,
                           dashboard_stats=dashboard_stats,
                           raw_stats_json=json.dumps(raw_stats, ensure_ascii=False))

@app.route('/expense/add', methods=['POST'])
def add_expense():
    if 'user_id' not in session: return redirect(url_for('login_page'))
    
    user_team = session['team']
    if user_team == "관리자":
        user_team = request.form.get('target_team', '시운전팀')
        if not user_team.endswith('팀') and user_team != "시운전":
            user_team += "팀"

    expense_date = request.form.get('expense_date')
    user_name = request.form.get('user_name')
    place = request.form.get('place')
    content = request.form.get('content')
    search_month = request.form.get('search_month')
    
    categories = request.form.getlist('receipt_category')
    amounts = request.form.getlist('receipt_amount')
    
    trip_id = str(uuid.uuid4())
    
    current_month = expense_date[:7]
    existing_orders = [x.get('order', 0) for x in ALL_EXPENSES if x.get('date', '').startswith(current_month)]
    next_order = max(existing_orders) + 1 if existing_orders else 1
    
    for cat, amt in zip(categories, amounts):
        if not cat or not amt: continue
        new_item = {
            "id": str(uuid.uuid4()),
            "trip_id": trip_id,
            "order": next_order,
            "team": user_team,
            "date": expense_date,
            "user_name": user_name,
            "place": place,
            "content": content,
            "category": cat,
            "amount": int(amt)
        }
        ALL_EXPENSES.append(new_item)
    
    save_data()
    return redirect(url_for('index_page', search_month=search_month))

@app.route('/expense/edit', methods=['POST'])
def edit_expense():
    if 'user_id' not in session: return redirect(url_for('login_page'))
    
    trip_id = request.form.get('trip_id')
    expense_date = request.form.get('expense_date')
    user_name = request.form.get('user_name')
    place = request.form.get('place')
    content = request.form.get('content')
    search_month = request.form.get('search_month')
    
    sub_ids = request.form.getlist('sub_receipt_ids')
    sub_cats = request.form.getlist('sub_receipt_categories')
    sub_amts = request.form.getlist('sub_receipt_amounts')
    
    sub_map = {}
    for sid, scat, samt in zip(sub_ids, sub_cats, sub_amts):
        sub_map[sid] = {'category': scat, 'amount': int(samt)}
        
    for x in ALL_EXPENSES:
        if x['trip_id'] == trip_id:
            x['date'] = expense_date
            x['user_name'] = user_name
            x['place'] = place
            x['content'] = content
            
            sid = x['id']
            if sid in sub_map:
                x['category'] = sub_map[sid]['category']
                x['amount'] = sub_map[sid]['amount']
                
    save_data()
    return redirect(url_for('index_page', search_month=search_month))

@app.route('/expense/delete/<trip_id>')
def delete_expense(trip_id):
    if 'user_id' not in session: return redirect(url_for('login_page'))
    global ALL_EXPENSES
    search_month = request.args.get('search_month')
    
    ALL_EXPENSES = [x for x in ALL_EXPENSES if x['trip_id'] != trip_id]
    
    save_data()
    return redirect(url_for('index_page', search_month=search_month))

@app.route('/expense/reorder', methods=['POST'])
def reorder_expenses():
    if 'user_id' not in session: return redirect(url_for('login_page'))
    
    trip_ids = request.form.getlist('trip_ids')
    search_month = request.form.get('search_month')
    
    order_map = {tid: idx + 1 for idx, tid in enumerate(trip_ids)}
    
    for x in ALL_EXPENSES:
        tid = x['trip_id']
        if tid in order_map:
            x['order'] = order_map[tid]
            
    save_data()
    return redirect(url_for('index_page', search_month=search_month))

@app.route('/download/cover')
def download_cover():
    target_team = request.args.get('team')
    target_month = request.args.get('month', datetime.date.today().strftime('%Y-%m'))
    
    if not target_team.endswith('팀') and target_team != "시운전":
        target_team += "팀"
        
    team_data = [x for x in ALL_EXPENSES if x.get('team') == target_team and x.get('date', '').startswith(target_month)]
    team_data.sort(key=lambda x: (x.get('order', 999), x.get('date', '')))
    
    wb = openpyxl.Workbook()
    ws1 = wb.active
    ws1.title = "정산서 표지"
    ws1.views.sheetView[0].showGridLines = True
    
    font_title = Font(name='맑은 고딕', size=16, bold=True)
    font_main = Font(name='맑은 고딕', size=10, bold=False)
    font_bold = Font(name='맑은 고딕', size=11, bold=True)
    
    thin_border = Border(
        left=Side(style='thin', color='000000'), right=Side(style='thin', color='000000'),
        top=Side(style='thin', color='000000'), bottom=Side(style='thin', color='000000')
    )
    double_bottom_border = Border(
        left=Side(style='thin', color='000000'), right=Side(style='thin', color='000000'),
        top=Side(style='thin', color='000000'), bottom=Side(style='double', color='000000')
    )
    
    fill_gray = PatternFill(start_color='F2F2F2', end_color='F2F2F2', fill_type='solid')
    fill_accent = PatternFill(start_color='E2EFDA', end_color='E2EFDA', fill_type='solid')
    
    ws1.merge_cells('A1:H2')
    title_cell = ws1['A1']
    title_cell.value = f"출 장 경 비 정 산 서 ({target_team})"
    title_cell.font = font_title
    title_cell.alignment = Alignment(horizontal='center', vertical='center')
    
    headers = ["순번", "결재", "출장지", "기간 및 일수", "출장 목적 및 대표 내용", "교통비/주차비", "식대비", "합계 금액"]
    for col_idx, h in enumerate(headers, 1):
        cell = ws1.cell(row=4, column=col_idx, value=h)
        cell.font = font_bold; cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.border = thin_border; cell.fill = fill_gray
    ws1.row_dimensions[4].height = 28
    
    trips_map = {}
    for exp in team_data:
        tid = exp['trip_id']
        if tid not in trips_map:
            trips_map[tid] = {
                'order': exp.get('order', 1),
                'date': exp['date'],
                'place': exp['place'],
                'content': exp['content'],
                'trans_park': 0,
                'food': 0,
                'total': 0
            }
        amt = exp['amount']
        cat = exp['category']
        if cat in ["교통비", "주차비", "차량유지비"]:
            trips_map[tid]['trans_park'] += amt
        elif cat in ["식비", "식대비"]:
            trips_map[tid]['food'] += amt
        else:
            trips_map[tid]['food'] += amt
        trips_map[tid]['total'] += amt
        
    sorted_trips = list(trips_map.values())
    sorted_trips.sort(key=lambda x: x['order'])
    
    r_idx = 5
    for idx, t in enumerate(sorted_trips, 1):
        ws1.cell(row=r_idx, column=1, value=idx).alignment = Alignment(horizontal='center')
        ws1.cell(row=r_idx, column=2, value="").alignment = Alignment(horizontal='center')
        ws1.cell(row=r_idx, column=3, value=t['place']).alignment = Alignment(horizontal='center')
        
        try:
            dt = datetime.datetime.strptime(t['date'], "%Y-%m-%d")
            date_str = dt.strftime("%m/%d")
        except:
            date_str = t['date']
            
        ws1.cell(row=r_idx, column=4, value=date_str).alignment = Alignment(horizontal='center')
        ws1.cell(row=r_idx, column=5, value=t['content']).alignment = Alignment(horizontal='left')
        
        c6 = ws1.cell(row=r_idx, column=6, value=t['trans_park'])
        c6.number_format = '#,##0'; c6.alignment = Alignment(horizontal='right')
        
        c7 = ws1.cell(row=r_idx, column=7, value=t['food'])
        c7.number_format = '#,##0'; c7.alignment = Alignment(horizontal='right')
        
        c8 = ws1.cell(row=r_idx, column=8, value=f"=SUM(F{r_idx}:G{r_idx})")
        c8.number_format = '#,##0'; c8.alignment = Alignment(horizontal='right'); c8.font = font_bold
        
        for c in range(1, 9):
            ws1.cell(row=r_idx, column=c).font = font_main if c != 8 else font_bold
            ws1.cell(row=r_idx, column=c).border = thin_border
        r_idx += 1
        
    ws1.merge_cells(start_row=r_idx, start_column=1, end_row=r_idx, end_column=5)
    sum_label = ws1.cell(row=r_idx, column=1, value="합   계")
    sum_label.font = font_bold; sum_label.alignment = Alignment(horizontal='center')
    
    sf = ws1.cell(row=r_idx, column=6, value=f"=SUM(F5:F{r_idx-1})")
    sf.number_format = '#,##0'; sf.alignment = Alignment(horizontal='right'); sf.font = font_bold
    
    sg = ws1.cell(row=r_idx, column=7, value=f"=SUM(G5:G{r_idx-1})")
    sg.number_format = '#,##0'; sg.alignment = Alignment(horizontal='right'); sg.font = font_bold
    
    sh = ws1.cell(row=r_idx, column=8, value=f"=SUM(H5:H{r_idx-1})")
    sh.number_format = '#,##0'; sh.alignment = Alignment(horizontal='right'); sh.font = font_bold; sh.fill = fill_accent
    
    for c in range(1, 9):
        ws1.cell(row=r_idx, column=c).border = double_bottom_border
        if c >= 6: ws1.cell(row=r_idx, column=c).font = font_bold
        
    col_widths1 = [6, 8, 18, 14, 35, 15, 15, 18]
    for i, w in enumerate(col_widths1, 1):
        ws1.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w
        
    ws2 = wb.create_sheet(title="ERP 변환용")
    ws2.views.sheetView[0].showGridLines = True
    
    headers2 = ["신청부서", "일자", "상세내역", "출장지 명칭", "원래구분", "지출금액", "사용자명", "계정코드"]
    for col_idx, h in enumerate(headers2, 1):
        cell = ws2.cell(row=5, column=col_idx, value=h)
        cell.font = font_bold; cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.border = thin_border; cell.fill = fill_gray
    ws2.row_dimensions[5].height = 24
    
    r_idx2 = 6
    for exp in team_data:
        ws2.cell(row=r_idx2, column=1, value=exp['team']).alignment = Alignment(horizontal='center')
        ws2.cell(row=r_idx2, column=2, value=exp['date']).alignment = Alignment(horizontal='center')
        ws2.cell(row=r_idx2, column=3, value=exp['content']).alignment = Alignment(horizontal='left')
        ws2.cell(row=r_idx2, column=4, value=exp['place']).alignment = Alignment(horizontal='center')
        ws2.cell(row=r_idx2, column=5, value=exp['category']).alignment = Alignment(horizontal='center')
        
        amt_cell = ws2.cell(row=r_idx2, column=6, value=exp['amount'])
        amt_cell.alignment = Alignment(horizontal='right'); amt_cell.number_format = '#,##0'
        
        ws2.cell(row=r_idx2, column=7, value=exp['user_name']).alignment = Alignment(horizontal='center')
        
        ac_code = ACCOUNT_MAPPING.get(exp['category'], "533")
        ws2.cell(row=r_idx2, column=8, value=ac_code).alignment = Alignment(horizontal='center')
        
        for c in range(1, 9):
            ws2.cell(row=r_idx2, column=c).font = font_main; ws2.cell(row=r_idx2, column=c).border = thin_border
        r_idx2 += 1
        
    if r_idx2 > 6:
        ws2.cell(row=r_idx2, column=3, value="총 합계").font = font_bold; ws2.cell(row=r_idx2, column=3).alignment = Alignment(horizontal='center')
        sum_cell = ws2.cell(row=r_idx2, column=6, value=f"=SUM(F6:F{r_idx2-1})")
        sum_cell.font = font_bold; sum_cell.alignment = Alignment(horizontal='right'); sum_cell.number_format = '#,##0'; sum_cell.fill = fill_accent
        ws2.cell(row=r_idx2, column=6).border = double_bottom_border
        
    col_widths2 = [12, 14, 35, 18, 14, 15, 12, 10]
    for i, w in enumerate(col_widths2, 1):
        ws2.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w
        
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    filename = f"출장정산_{target_team}_{target_month}.xlsx"
    return send_file(output, as_attachment=True, download_name=filename, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
