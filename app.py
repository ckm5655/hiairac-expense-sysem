import subprocess
import sys

# 서버 실행 시 필요한 라이브러리가 없으면 알아서 자동 설치하는 로직
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

# 💡 부서명 불일치 해결을 위한 텍스트 표준화 도우미 함수
def is_match_team(db_team, target_team):
    if not db_team or not target_team:
        return False
    # 서로 공백을 제거하고 '팀' 글자를 떼어낸 순수 키워드로 비교 (ex: '시운전' == '시운전')
    return db_team.replace('팀', '').strip() == target_team.replace('팀', '').strip()

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
    
    # 1. 이번 달 기준 데이터 필터링
    month_data = [x for x in ALL_EXPENSES if x.get('date', '').startswith(current_month)]
    
    # 🌟 [핵심 수정] 일반 팀 로그인 시 '시운전' / '시운전팀' 유연하게 동시 매칭되도록 보정
    if user_team != "관리자":
        month_data = [x for x in month_data if is_match_team(x.get('team', ''), user_team)]
        
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
        
    # 2. 대시보드 상단 미니 통계 (선택한 '당월' 전체 부서 기준 합계 및 안전 보정)
    dashboard_stats = {"총합": 0, "시운전": 0, "생산팀": 0, "영업팀": 0, "전장팀": 0}
    all_month_data = [x for x in ALL_EXPENSES if x.get('date', '').startswith(current_month)]
    
    for x in all_month_data:
        dashboard_stats["총합"] += x['amount']
        t_name = x.get('team', '')
        if "시운전" in t_name: dashboard_stats["시운전"] += x['amount']
        elif "생산" in t_name: dashboard_stats["생산팀"] += x['amount']
        elif "영업" in t_name: dashboard_stats["영업팀"] += x['amount']
        elif "전장" in t_name: dashboard_stats["전장팀"] += x['amount']
        
    # 3. 그래프용 최근 6개월 범위 데이터 수집 로직
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
    global ALL_EXPENSES
    
    trip_id = request.form.get('edit_trip_id')
    expense_date = request.form.get('edit_date')
    user_name = request.form.get('edit_user_name')
    place = request.form.get('edit_place')
    content = request.form.get('edit_content')
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

# 🌟 [대대적 전면 보수] 전사 통합 엑셀 다운로드 및 부서별 내용 실종 방지 기능 구현
@app.route('/download/cover')
def download_cover():
    target_team = request.args.get('team', 'ALL')
    target_month = request.args.get('month', datetime.date.today().strftime('%Y-%m'))
    
    # 전사 전체('ALL')인 경우와 특정 부서인 경우 구분 필터링
    if target_team == 'ALL':
        raw_data = [x for x in ALL_EXPENSES if x.get('date', '').startswith(target_month)]
        display_team_title = "전사 통합"
    else:
        raw_data = [x for x in ALL_EXPENSES if is_match_team(x.get('team', ''), target_team) and x.get('date', '').startswith(target_month)]
        display_team_title = target_team
        if not display_team_title.endswith('팀') and display_team_title != "시운전":
            display_team_title += "팀"

    raw_data.sort(key=lambda x: (x.get('order', 999), x.get('date', '')))
    
    # --- [데이터 가공] 1번 시트용: 건별 일괄 합산 로직 ---
    aggregated = {}
    for exp in raw_data:
        # 부서 구분도 유니크 키에 포함시켜 전사 통합 출력 시 데이터 분별력 유도
        key = (exp.get('date', ''), exp.get('content', ''), exp.get('place', ''), exp.get('user_name', ''), exp.get('team', ''))
        amt = exp.get('amount', 0)
        cat = exp.get('category', '기타')
        
        if key not in aggregated:
            aggregated[key] = {
                "date": key[0], "content": key[1], "place": key[2], "user_name": key[3], "team": key[4],
                "total": 0, "교통비": 0, "식대비": 0, "숙박비": 0, "차량유지비": 0, "기타": 0
            }
            
        aggregated[key]["total"] += amt
        
        if cat in ["교통비", "주차비", "교통/주차비"]:
            aggregated[key]["교통비"] += amt
        elif cat in ["식비", "식대비"]:
            aggregated[key]["식대비"] += amt
        elif cat == "숙박비":
            aggregated[key]["숙박비"] += amt
        elif cat == "차량유지비":
            aggregated[key]["차량유지비"] += amt
        else: 
            aggregated[key]["기타"] += amt

    sorted_cover_rows = list(aggregated.values())
    
    wb = openpyxl.Workbook()
    
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
    
    align_center = Alignment(horizontal='center', vertical='center', shrink_to_fit=True)
    align_right = Alignment(horizontal='right', vertical='center', shrink_to_fit=True)
    align_left = Alignment(horizontal='left', vertical='center', shrink_to_fit=True)

    ws1 = wb.active
    ws1.title = f"{target_month[5:7]}월 정산서"
    ws1.views.sheetView[0].showGridLines = True
    
    ws1.merge_cells('A1:D2')
    ws1['A1'] = f"{target_month[5:7]}월 경비 사용내역서"
    ws1['A1'].font = font_title
    ws1['A1'].alignment = Alignment(horizontal='left', vertical='center')

    approve_headers = ["작성", "검토", "검토", "승인"]
    for i, h in enumerate(approve_headers):
        col_idx = 8 + i
        cell = ws1.cell(row=1, column=col_idx, value=h)
        cell.font = font_header; cell.alignment = align_center; cell.border = thin_border
        cell.fill = PatternFill(start_color='F9FAFB', end_color='F9FAFB', fill_type='solid')
        ws1.merge_cells(start_row=2, start_column=col_idx, end_row=3, end_column=col_idx)
        for r in range(2, 4): ws1.cell(row=r, column=col_idx).border = thin_border
        
    ws1.row_dimensions[1].height = 24
    ws1.row_dimensions[2].height = 24
    ws1.row_dimensions[3].height = 24

    ws1.merge_cells('A4:D4')
    ws1['A4'] = f"작성일자: {datetime.date.today().strftime('%Y년 %m월 %d일')}  /  부서: {display_team_title}"
    ws1['A4'].font = font_main
    ws1.row_dimensions[4].height = 24

    headers1 = ["순번", "일자", "내 용", "출장지", "금액(합계)", "교통비", "식대비", "숙박비", "차량유지비", "기타", "사용자"]
    for col_idx, h in enumerate(headers1, 1):
        cell = ws1.cell(row=5, column=col_idx, value=h)
        cell.font = font_header; cell.alignment = align_center; cell.border = thin_border; cell.fill = fill_header
    ws1.row_dimensions[5].height = 32

    r_idx = 6
    for idx, row_data in enumerate(sorted_cover_rows, 1):
        ws1.cell(row=r_idx, column=1, value=idx).alignment = align_center
        ws1.cell(row=r_idx, column=2, value=row_data['date'][5:]).alignment = align_center
        # 전사 모드일 때는 내용 앞에 부서명을 함께 표시해 시인성 확대
        display_content = f"[{row_data['team']}] {row_data['content']}" if target_team == 'ALL' else row_data['content']
        ws1.cell(row=r_idx, column=3, value=display_content).alignment = align_left
        ws1.cell(row=r_idx, column=4, value=row_data['place']).alignment = align_center
        
        t_cell = ws1.cell(row=r_idx, column=5, value=row_data['total'])
        t_cell.font = Font(name='맑은 고딕', size=10, bold=True); t_cell.number_format = '#,##0'; t_cell.alignment = align_right
        
        categories_keys = ["교통비", "식대비", "숙박비", "차량유지비", "기타"]
        for c_idx, cat_name in enumerate(categories_keys, 6):
            v_cell = ws1.cell(row=r_idx, column=c_idx)
            v_cell.value = row_data[cat_name] if row_data[cat_name] > 0 else ""
            v_cell.number_format = '#,##0'; v_cell.alignment = align_right
            
        ws1.cell(row=r_idx, column=11, value=row_data['user_name']).alignment = align_center
        
        for c in range(1, 12):
            cell = ws1.cell(row=r_idx, column=c)
            if c != 5: cell.font = font_main
            cell.border = thin_border
            
        ws1.row_dimensions[r_idx].height = 28
        r_idx += 1

    sum_row_idx = r_idx
    ws1.merge_cells(start_row=sum_row_idx, start_column=1, end_row=sum_row_idx, end_column=4)
    ws1.cell(row=sum_row_idx, column=1, value="합   계").font = font_sum
    ws1.cell(row=sum_row_idx, column=1).alignment = align_center
    
    for c in range(1, 12):
        cell = ws1.cell(row=sum_row_idx, column=c)
        cell.border = thin_border; cell.fill = fill_sum
    
    for c in range(5, 11):
        col_letter = openpyxl.utils.get_column_letter(c)
        sum_cell = ws1.cell(row=sum_row_idx, column=c, value=f"=SUM({col_letter}6:{col_letter}{sum_row_idx-1})")
        sum_cell.font = font_sum; sum_cell.number_format = '#,##0'; sum_cell.alignment = align_right
        
    ws1.cell(row=sum_row_idx, column=11).alignment = align_center
    ws1.row_dimensions[sum_row_idx].height = 30

    budget_map = {"생산팀": 500000, "영업팀": 500000, "시운전팀": 1000000, "전장팀": 800000, "시운전": 1000000}
    team_budget = budget_map.get(display_team_title, 0) if target_team != 'ALL' else 0
    budget_str = f"{team_budget:,.0f}" if team_budget > 0 else "0"
    
    r_idx += 2
    ws1.merge_cells(start_row=r_idx, start_column=1, end_row=r_idx, end_column=11)
    summary_cell = ws1.cell(row=r_idx, column=1)
    
    if team_budget > 0:
        summary_cell.value = f'="가지급금금액(이월잔액포함) [ {budget_str} ]   -   총경비사용금액 [ " & TEXT(E{sum_row_idx}, "#,##0") & " ]   =   잔액 [ " & TEXT({team_budget}-E{sum_row_idx}, "#,##0") & " ]"'
    else:
        summary_cell.value = f'="전체 통합 경비 합계액 [ " & TEXT(E{sum_row_idx}, "#,##0") & " ] 원"'
        
    summary_cell.font = Font(name='맑은 고딕', size=12, bold=True, color='1F2937')
    summary_cell.alignment = align_center
    ws1.row_dimensions[r_idx].height = 36

    widths1 = {1: 5, 2: 10, 3: 35, 4: 15, 5: 12, 6: 10, 7: 10, 8: 10, 9: 10, 10: 10, 11: 10}
    for col_idx, w in widths1.items():
        ws1.column_dimensions[openpyxl.utils.get_column_letter(col_idx)].width = w

    # 📑 두 번째 시트: 상세내역
    ws2 = wb.create_sheet(title="상세내역")
    ws2.views.sheetView[0].showGridLines = True
    
    ws2.merge_cells('A1:C2')
    ws2['A1'] = "지출 항목별 상세 증빙내역"
    ws2['A1'].font = Font(name='맑은 고딕', size=14, bold=True, color='374151')
    ws2['A1'].alignment = Alignment(horizontal='left', vertical='center')
    
    ws2.row_dimensions[1].height = 20
    ws2.row_dimensions[4].height = 28
    
    headers2 = ["순번", "사용일자", "부서명", "성명", "경비구분", "지출 내용 및 세부 목적", "출장지", "사용 금액", "비고"]
    for col_idx, h in enumerate(headers2, 1):
        cell = ws2.cell(row=4, column=col_idx, value=h)
        cell.font = font_header; cell.alignment = align_center; cell.border = thin_border; cell.fill = fill_header
        
    d_idx = 5
    for idx, exp in enumerate(raw_data, 1):
        ws2.cell(row=d_idx, column=1, value=idx).alignment = align_center
        ws2.cell(row=d_idx, column=2, value=exp.get('date', '')[5:]).alignment = align_center
        ws2.cell(row=d_idx, column=3, value=exp.get('team', '')).alignment = align_center
        ws2.cell(row=d_idx, column=4, value=exp.get('user_name', '')).alignment = align_center
        ws2.cell(row=d_idx, column=5, value=exp.get('category', '')).alignment = align_center
        ws2.cell(row=d_idx, column=6, value=exp.get('content', '')).alignment = align_left
        ws2.cell(row=d_idx, column=7, value=exp.get('place', '')).alignment = align_center
        
        amt_cell = ws2.cell(row=d_idx, column=8, value=exp.get('amount', 0))
        amt_cell.number_format = '#,##0'; amt_cell.alignment = align_right
        
        ws2.cell(row=d_idx, column=9, value="확인완료").alignment = align_center
        
        for c in range(1, 10):
            cell = ws2.cell(row=d_idx, column=c)
            cell.border = thin_border
            cell.font = font_main
            
        ws2.row_dimensions[d_idx].height = 24
        d_idx += 1
        
    ws2.merge_cells(start_row=d_idx, start_column=1, end_row=d_idx, end_column=7)
    ws2.cell(row=d_idx, column=1, value="총 상세 지출액 합계").font = font_sum
    ws2.cell(row=d_idx, column=1).alignment = align_center
    
    for c in range(1, 10):
        cell = ws2.cell(row=d_idx, column=c)
        cell.border = thin_border; cell.fill = fill_sum
        
    sum_cell2 = ws2.cell(row=d_idx, column=8, value=f"=SUM(H5:H{d_idx-1})")
    sum_cell2.font = font_sum; sum_cell2.number_format = '#,##0'; sum_cell2.alignment = align_right
    ws2.row_dimensions[d_idx].height = 26
    
    widths2 = [5, 11, 12, 10, 12, 32, 15, 14, 12]
    for i, w in enumerate(widths2, 1):
        ws2.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    filename = f"정산서_{target_team}_{target_month}.xlsx"
    return send_file(output, as_attachment=True, download_name=filename, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@app.route('/backup/download')
def backup_download():
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
    
    file.save(DATA_FILE)
    
    global ALL_EXPENSES
    ALL_EXPENSES = load_data()
    
    return "<script>alert('데이터 복구가 완료되었습니다!'); location.href='/index';</script>"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
