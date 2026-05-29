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
    "admin": {"password": "01234", "name": "관리자", "team": "관리자"},
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
    
    categories_list = ["교통비", "주차비", "식비", "식대비", "숙박비", "소모품비", "차량유지비","택배/운반비", "기타"]
    
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
        
    raw_data = [x for x in ALL_EXPENSES if x.get('team') == target_team and x.get('date', '').startswith(target_month)]
    
    # 🔥 [중요] 6번 조건: 같은 날짜, 같은 내용, 같은 출장지, 같은 사용자는 한 줄로 묶어서 비용 합산
    aggregated = {}
    for exp in raw_data:
        # 그룹핑 키 생성 (날짜, 내용, 출장지, 사용자 조합)
        key = (exp.get('date', ''), exp.get('content', ''), exp.get('place', ''), exp.get('user_name', ''))
        amt = exp.get('amount', 0)
        cat = exp.get('category', '기타')
        
        if key not in aggregated:
            aggregated[key] = {
                "date": key[0], "content": key[1], "place": key[2], "user_name": key[3],
                "total": 0, "교통비": 0, "식대비": 0, "숙박비": 0, "차량유지비": 0, "기타": 0
            }
            
        aggregated[key]["total"] += amt
        
        # 1번 조건: 소모품비와 기타는 '기타'로 합산 매핑
        if cat in ["교통비", "주차비"]:
            aggregated[key]["교통비"] += amt
        elif cat in ["식비", "식대비"]:
            aggregated[key]["식대비"] += amt
        elif cat == "숙박비":
            aggregated[key]["숙박비"] += amt
        elif cat == "차량유지비":
            aggregated[key]["차량유지비"] += amt
        else: # 소모품비, 기타 등등은 전부기타로 병합
            aggregated[key]["기타"] += amt

    # 정렬 (날짜 순)
    sorted_rows = list(aggregated.values())
    sorted_rows.sort(key=lambda x: x['date'])
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"{target_month[5:7]}월 정산서"
    ws.views.sheetView[0].showGridLines = True
    
    # 7번 조건: 전체 글자 크기 상향 정의
    font_title = Font(name='맑은 고딕', size=18, bold=True, color='1E3A8A')
    font_header = Font(name='맑은 고딕', size=11, bold=True)
    font_main = Font(name='맑은 고딕', size=10)
    font_sum = Font(name='맑은 고딕', size=11, bold=True)
    
    thin_border = Border(
        left=Side(style='thin', color='A0AEC0'), right=Side(style='thin', color='A0AEC0'),
        top=Side(style='thin', color='A0AEC0'), bottom=Side(style='thin', color='A0AEC0')
    )
    fill_header = PatternFill(start_color='F3F4F6', end_color='F3F4F6', fill_type='solid')
    fill_sum = PatternFill(start_color='EBF5FF', end_color='EBF5FF', fill_type='solid')
    
    # 3번 조건: 셀에 맞춤(shrink_to_fit) 공통 셋업용 얼라인먼트
    align_center = Alignment(horizontal='center', vertical='center', shrink_to_fit=True)
    align_right = Alignment(horizontal='right', vertical='center', shrink_to_fit=True)
    align_left = Alignment(horizontal='left', vertical='center', shrink_to_fit=True)

    # 제목 및 결재란 세팅 (11개 열 기준 정렬 보정)
    ws.merge_cells('A1:D2')
    ws['A1'] = f"{target_month[5:7]}월 개인경비 사용내역"
    ws['A1'].font = font_title
    ws['A1'].alignment = Alignment(horizontal='left', vertical='center')

    approve_headers = ["작성", "검토", "검토", "승인"]
    for i, h in enumerate(approve_headers):
        col_idx = 8 + i # H, I, J, K열에 균등 배치
        cell = ws.cell(row=1, column=col_idx, value=h)
        cell.font = font_header; cell.alignment = align_center; cell.border = thin_border
        cell.fill = PatternFill(start_color='F9FAFB', end_color='F9FAFB', fill_type='solid')
        ws.merge_cells(start_row=2, start_column=col_idx, end_row=3, end_column=col_idx)
        for r in range(2, 4): ws.cell(row=r, column=col_idx).border = thin_border
        
    # 5번 조건: 행 높이 대폭 상향
    ws.row_dimensions[1].height = 24
    ws.row_dimensions[2].height = 24
    ws.row_dimensions[3].height = 24

    ws.merge_cells('A4:D4')
    ws['A4'] = f"작성일자: {datetime.date.today().strftime('%Y년 %m월 %d일')}  /  부서: {target_team}"
    ws['A4'].font = font_main
    ws.row_dimensions[4].height = 24

    # 표 헤더 (소모품비 제외된 11개 체제)
    headers = ["순번", "일자", "내 용", "출장지", "금액(합계)", "교통비", "식대비", "숙박비", "차량유지비", "기타", "사용자"]
    for col_idx, h in enumerate(headers, 1):
        cell = ws.cell(row=5, column=col_idx, value=h)
        cell.font = font_header; cell.alignment = align_center; cell.border = thin_border; cell.fill = fill_header
    ws.row_dimensions[5].height = 32

    # 데이터 입력 바인딩
    r_idx = 6
    for idx, row_data in enumerate(sorted_rows, 1):
        ws.cell(row=r_idx, column=1, value=idx).alignment = align_center
        ws.cell(row=r_idx, column=2, value=row_data['date'][5:]).alignment = align_center
        ws.cell(row=r_idx, column=3, value=row_data['content']).alignment = align_left
        ws.cell(row=r_idx, column=4, value=row_data['place']).alignment = align_center
        
        # 합계 금액 세팅
        t_cell = ws.cell(row=r_idx, column=5, value=row_data['total'])
        t_cell.font = Font(name='맑은 고딕', size=10, bold=True); t_cell.number_format = '#,##0'; t_cell.alignment = align_right
        
        # 분류 금액 바인딩
        categories_keys = ["교통비", "식대비", "숙박비", "차량유지비", "기타"]
        for c_idx, cat_name in enumerate(categories_keys, 6):
            v_cell = ws.cell(row=r_idx, column=c_idx)
            v_cell.value = row_data[cat_name] if row_data[cat_name] > 0 else ""
            v_cell.number_format = '#,##0'; v_cell.alignment = align_right
            
        # 4번 조건: K열 사용자명 무조건 가운데 정렬
        ws.cell(row=r_idx, column=11, value=row_data['user_name']).alignment = align_center
        
        for c in range(1, 12):
            cell = ws.cell(row=r_idx, column=c)
            if c != 5: cell.font = font_main
            cell.border = thin_border
            
        ws.row_dimensions[r_idx].height = 28
        r_idx += 1

    # 합계행 디자인 및 수식
    sum_row_idx = r_idx
    ws.merge_cells(start_row=sum_row_idx, start_column=1, end_row=sum_row_idx, end_column=4)
    footer_label = ws.cell(row=sum_row_idx, column=1, value="합   계")
    footer_label.font = font_sum; footer_label.alignment = align_center
    
    for c in range(1, 12):
        cell = ws.cell(row=sum_row_idx, column=c)
        cell.border = thin_border; cell.fill = fill_sum
    
    for c in range(5, 11):
        col_letter = openpyxl.utils.get_column_letter(c)
        sum_cell = ws.cell(row=sum_row_idx, column=c, value=f"=SUM({col_letter}6:{col_letter}{sum_row_idx-1})")
        sum_cell.font = font_sum; sum_cell.number_format = '#,##0'; sum_cell.alignment = align_right
        
    ws.cell(row=sum_row_idx, column=11).alignment = align_center
    ws.row_dimensions[sum_row_idx].height = 30

    # 하단 마감 정산 정보 및 동적 텍스트 연산식
    budget_map = {"생산팀": 500000, "영업팀": 500000, "시운전팀": 1000000, "전장팀": 800000, "시운전": 1000000}
    team_budget = budget_map.get(target_team, 0)
    budget_str = f"{team_budget:,.0f}" if team_budget > 0 else "0"
    
    r_idx += 2
    ws.merge_cells(start_row=r_idx, start_column=1, end_row=r_idx, end_column=11)
    summary_cell = ws.cell(row=r_idx, column=1)
    
    if team_budget > 0:
        summary_cell.value = f'="가지급금금액(이월잔액포함) [ {budget_str} ]   -   총경비사용금액 [ " & TEXT(E{sum_row_idx}, "#,##0") & " ]   =   잔액 [ " & TEXT({team_budget}-E{sum_row_idx}, "#,##0") & " ]"'
    else:
        summary_cell.value = f'="가지급금금액(이월잔액포함) [ 0 ]   -   총경비사용금액 [ " & TEXT(E{sum_row_idx}, "#,##0") & " ]   =   잔액 [ " & TEXT(0-E{sum_row_idx}, "#,##0") & " ]"'
        
    summary_cell.font = Font(name='맑은 고딕', size=12, bold=True, color='1F2937')
    summary_cell.alignment = align_center
    ws.row_dimensions[r_idx].height = 36

    # 2번 조건: 가로 너비 조건 고정 (A=3, C=30, 나머지=10)
    widths = {1: 3, 2: 10, 3: 30, 4: 10, 5: 10, 6: 10, 7: 10, 8: 10, 9: 10, 10: 10, 11: 10}
    for col_idx, w in widths.items():
        ws.column_dimensions[openpyxl.utils.get_column_letter(col_idx)].width = w

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    filename = f"정산서_{target_team}_{target_month}.xlsx"
    return send_file(output, as_attachment=True, download_name=filename, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@app.route('/backup/download')
def backup_download():
    # 현재 서버에 있는 expenses.json을 내 컴퓨터로 다운로드
    if os.path.exists(DATA_FILE):
        return send_file(DATA_FILE, as_attachment=True, download_name="expenses_backup.json")
    return "백업 파일이 없습니다.", 404

@app.route('/backup/upload', methods=['POST'])
def backup_upload():
    if 'file' not in request.files:
        return "파일이 없습니다."
    file = request.files['file']
    if file.filename == '':
        return "파일을 선택해주세요."
    
    # 업로드한 파일을 서버의 expenses.json으로 덮어쓰기
    file.save(DATA_FILE)
    
    # 서버 메모리의 ALL_EXPENSES도 새로고침
    global ALL_EXPENSES
    ALL_EXPENSES = load_data()
    
    return "<script>alert('데이터 복구가 완료되었습니다!'); location.href='/index';</script>"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
