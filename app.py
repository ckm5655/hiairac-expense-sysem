from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # 세션 암호화 키

USER_CREDENTIALS = {
    "admin": {"password": "01234", "name": "관리자", "team": "관리자"},
    "생산": {"password": "1234", "name": "생산", "team": "생산팀"},
    "영업": {"password": "1234", "name": "영업", "team": "영업팀"},
    "시운전": {"password": "1234", "name": "시운전", "team": "시운전팀"},
    "전장": {"password": "1234", "name": "전장", "team": "전장팀"}
}

MOCK_TRIPS = [
    {
        "trip_id": "1",
        "order": 1,
        "team": "시운전팀",
        "date": "2026-05-10",
        "user": "홍길동",
        "place": "삼성중공업",
        "content": "SPOT COOLER 점검 지원",
        "items_desc": "교통비: 50,000원 | 식비: 30,000원",
        "total_amount": 80000,
        "details_json": json.dumps([
            {"id": "r1", "category": "교통비", "amount": 50000},
            {"id": "r2", "category": "식비", "amount": 30000}
        ], ensure_ascii=False)
    },
    {
        "trip_id": "2",
        "order": 2,
        "team": "생산팀",
        "date": "2026-05-15",
        "user": "김철수",
        "place": "울산공장",
        "content": "생산 라인 설비 세팅",
        "items_desc": "숙박비: 70,000원 | 식비: 25,000원",
        "total_amount": 95000,
        "details_json": json.dumps([
            {"id": "r3", "category": "숙박비", "amount": 70000},
            {"id": "r4", "category": "식비", "amount": 25000}
        ], ensure_ascii=False)
    }
]

CATEGORIES = ["교통비", "주차비", "식비", "숙박비", "소모품비", "차량유지비", "운반비", "기타"]

@app.route('/')
def login_page():
    if 'username' in session:
        return redirect(url_for('index'))
    
    html = """
    <!DOCTYPE html><html><head><meta charset="UTF-8"><title>경비 정산 로그인</title>
    <style>
        body { font-family: '맑은 고딕', sans-serif; background: #f0f4f8; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .login-box { background: white; padding: 40px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center; width: 300px; }
        input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
        button { width: 100%; padding: 12px; background: #1e3a8a; color: white; border: none; border-radius: 4px; font-weight: bold; cursor: pointer; font-size: 15px; }
    </style>
    </head><body>
    <div class="login-box">
        <h2 style="color:#1e3a8a; margin-bottom:20px;">경비 정산 시스템</h2>
        <form action="/login" method="post">
            <input type="text" name="username" placeholder="아이디 (예: admin, 시운전)" required>
            <input type="password" name="password" placeholder="비밀번호" required>
            <button type="submit">로그인</button>
        </form>
    </div>
    </body></html>
    """
    return html

@app.route('/login', methods=['POST'])
def do_login():
    uid = request.form.get('username')
    upass = request.form.get('password')
    if uid in USER_CREDENTIALS and USER_CREDENTIALS[uid]['password'] == upass:
        session['user_id'] = uid
        session['username'] = USER_CREDENTIALS[uid]['name']
        session['team'] = USER_CREDENTIALS[uid]['team']
        return redirect(url_for('index'))
    return "<script>alert('아이디 또는 비밀번호가 올바르지 않습니다.'); history.back();</script>"

@app.route('/index')
def index():
    if 'username' not in session:
        return redirect(url_for('login_page'))
        
    username = session.get('username', '게스트')
    team = session.get('team', '시운전팀')
    
    current_month = request.args.get('search_month', datetime.now().strftime('%Y-%m'))
    month_start_date = f"{current_month}-01"
    month_end_date = f"{current_month}-31"
    
    filtered_trips = [t for t in MOCK_TRIPS if t['date'].startswith(current_month)]
    filtered_trips = sorted(filtered_trips, key=lambda x: x['order'])
    
    raw_stats_list = []
    # 📌 이중 키워드('시운전', '시운전팀')를 삭제하고 하나의 키워드로만 관리
    dashboard_stats = {'총합': 0, '시운전팀': 0, '생산팀': 0, '영업팀': 0, '전장팀': 0}
    
    for t in MOCK_TRIPS:
        try:
            details = json.loads(t.get('details_json', '[]'))
        except:
            details = []
            
        for item in details:
            stat_item = {
                "date": t.get('date', ''),
                "team": t.get('team', ''),
                "place": t.get('place', ''),
                "user": t.get('user', '알수없음'), 
                "category": item.get('category', '기타'),
                "std_category": item.get('category', '기타'),
                "amount": int(item.get('amount', 0))
            }
            raw_stats_list.append(stat_item)
            
            # 선택한 마감 월의 데이터 합산
            if t.get('date', '').startswith(current_month):
                amt = int(item.get('amount', 0))
                dashboard_stats['총합'] += amt
                
                # 📌 부서명을 무조건 'OO팀' 포맷으로 단일화하여 딱 1번만 합산 (중복 카운팅 해결)
                raw_team = t.get('team', '').strip()
                if raw_team == '시운전':
                    std_team = '시운전팀'
                elif not raw_team.endswith('팀') and raw_team != '관리자':
                    std_team = raw_team + '팀'
                else:
                    std_team = raw_team
                
                if std_team in dashboard_stats:
                    dashboard_stats[std_team] += amt

    return render_template(
        'index.html',
        username=username,
        team=team,
        current_month=current_month,
        month_start_date=month_start_date,
        month_end_date=month_end_date,
        trips=filtered_trips,
        categories=CATEGORIES,
        dashboard_stats=dashboard_stats,
        raw_stats_json=json.dumps(raw_stats_list, ensure_ascii=False)
    )

@app.route('/expense/add', methods=['POST'])
def add_expense():
    expense_date = request.form.get('expense_date')
    user_name = request.form.get('user_name')
    place = request.form.get('place')
    content = request.form.get('content')
    search_month = request.form.get('search_month', datetime.now().strftime('%Y-%m'))
    
    user_team = session.get('team', '시운전팀')
    if user_team == "관리자" and request.form.get('target_team'):
        user_team = request.form.get('target_team')
        
    receipt_categories = request.form.getlist('receipt_category')
    receipt_amounts = request.form.getlist('receipt_amount')
    
    details = []
    total_amount = 0
    desc_parts = []
    
    for i in range(len(receipt_categories)):
        cat = receipt_categories[i]
        try:
            amt = int(receipt_amounts[i]) if receipt_amounts[i] else 0
        except ValueError:
            amt = 0
            
        if cat and amt > 0:
            rid = f"r_{datetime.now().strftime('%Y%m%d%H%M%S')}_{i}"
            details.append({"id": rid, "category": cat, "amount": amt})
            total_amount += amt
            desc_parts.append(f"{cat}: {amt:,}원")
            
    items_desc = " | ".join(desc_parts) if desc_parts else "등록된 영수증 없음"
    
    new_id = str(len(MOCK_TRIPS) + 1)
    new_order = len(MOCK_TRIPS) + 1
    
    MOCK_TRIPS.append({
        "trip_id": new_id,
        "order": new_order,
        "team": user_team,
        "date": expense_date,
        "user": user_name,
        "place": place,
        "content": content,
        "items_desc": items_desc,
        "total_amount": total_amount,
        "details_json": json.dumps(details, ensure_ascii=False)
    })
    
    return redirect(url_for('index', search_month=search_month))

@app.route('/expense/edit_submit', methods=['POST'])
def edit_submit():
    trip_id = request.form.get('trip_id')
    date = request.form.get('date')
    user = request.form.get('user')
    place = request.form.get('place')
    content = request.form.get('content')
    search_month = request.form.get('search_month')
    
    sub_ids = request.form.getlist('sub_receipt_ids')
    sub_categories = request.form.getlist('sub_receipt_categories')
    sub_amounts = request.form.getlist('sub_receipt_amounts')
    
    for t in MOCK_TRIPS:
        if t['trip_id'] == trip_id:
            t['date'] = date
            t['user'] = user
            t['place'] = place
            t['content'] = content
            
            new_details = []
            total_amount = 0
            desc_parts = []
            
            for i in range(len(sub_ids)):
                try:
                    amt = int(sub_amounts[i])
                except:
                    amt = 0
                cat = sub_categories[i]
                
                new_details.append({"id": sub_ids[i], "category": cat, "amount": amt})
                total_amount += amt
                desc_parts.append(f"{cat}: {amt:,}원")
                
            t['total_amount'] = total_amount
            t['items_desc'] = " | ".join(desc_parts)
            t['details_json'] = json.dumps(new_details, ensure_ascii=False)
            break
            
    return redirect(url_for('index', search_month=search_month))

@app.route('/expense/reorder', methods=['POST'])
def reorder():
    trip_ids = request.form.getlist('trip_ids')
    search_month = request.form.get('search_month')
    
    for index, tid in enumerate(trip_ids):
        for t in MOCK_TRIPS:
            if t['trip_id'] == tid:
                t['order'] = index + 1
                break
                
    return redirect(url_for('index', search_month=search_month))

@app.route('/expense/delete/<trip_id>')
def delete_expense(trip_id):
    global MOCK_TRIPS
    search_month = request.args.get('search_month', datetime.now().strftime('%Y-%m'))
    MOCK_TRIPS = [t for t in MOCK_TRIPS if t['trip_id'] != trip_id]
    return redirect(url_for('index', search_month=search_month))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
