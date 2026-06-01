from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# 기본 더미 데이터
MOCK_TRIPS = [
    {
        "trip_id": "1",
        "order": 1,
        "team": "시운전팀",
        "date": "2026-05-10",
        "user": "홍길동",
        "place": "삼성중공업",
        "content": "SPOT COOLER 점검 지원",
        "items_desc": "교통비: 50,000원 | 식대비: 30,000원",
        "total_amount": 80000,
        "details_json": json.dumps([
            {"id": "r1", "category": "교통비", "amount": 50000},
            {"id": "r2", "category": "식대비", "amount": 30000}
        ], ensure_ascii=False)
    }
]

CATEGORIES = ["교통비", "교통/주차비", "식대비", "식비", "숙박비", "소모품비", "차량유지비", "기타"]

@app.route('/')
def home():
    session['username'] = '관리자님'
    session['team'] = '관리자' 
    return redirect(url_for('index'))

@app.route('/index')
def index():
    username = session.get('username', '게스트')
    team = session.get('team', '시운전팀')
    
    current_month = request.args.get('search_month', datetime.now().strftime('%Y-%m'))
    month_start_date = f"{current_month}-01"
    month_end_date = f"{current_month}-31"
    
    # 해당 월 데이터만 필터링
    filtered_trips = [t for t in MOCK_TRIPS if t.get('date', '').startswith(current_month)]
    filtered_trips = sorted(filtered_trips, key=lambda x: x.get('order', 999))
    
    raw_stats_list = []
    dashboard_stats = {'총합': 0, '시운전': 0, '시운전팀': 0, '생산팀': 0, '영업팀': 0, '전장팀': 0}
    
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
                "category": item.get('category', '기타'),
                "std_category": item.get('category', '기타'),
                "amount": int(item.get('amount', 0))
            }
            raw_stats_list.append(stat_item)
            
            if t.get('date', '').startswith(current_month):
                amt = int(item.get('amount', 0))
                dashboard_stats['총합'] += amt
                
                norm_team = t.get('team', '').replace('팀', '').strip()
                if norm_team in ['시운전', '시운전팀']:
                    dashboard_stats['시운전'] += amt
                elif norm_team == '생산':
                    dashboard_stats['생산팀'] += amt
                elif norm_team == '영업':
                    dashboard_stats['영업팀'] += amt
                elif norm_team == '전장':
                    dashboard_stats['전장팀'] += amt
                    
                if t.get('team') in dashboard_stats:
                    dashboard_stats[t['team']] += amt

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
    # 📌 폼 데이터 수신 변수명 일치 작업 완료 (date, user, place, content)
    date = request.form.get('date', '')
    user = request.form.get('user', '')
    place = request.form.get('place', '')
    content = request.form.get('content', '')
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
            # 영수증 내역 텍스트 생성
            desc_parts.append(f"{cat}: {amt:,}원")
            
    # 누락되었던 items_desc(포함된 영수증 항목) 결합
    items_desc = " | ".join(desc_parts) if desc_parts else "등록된 영수증 없음"
    
    new_id = str(len(MOCK_TRIPS) + 1)
    new_order = len(MOCK_TRIPS) + 1
    
    MOCK_TRIPS.append({
        "trip_id": new_id,
        "order": new_order,
        "team": user_team,
        "date": date,
        "user": user,          # 사용자가 안나오는 현상 해결
        "place": place,
        "content": content,    # 출장 목적 및 내용이 안나오는 현상 해결
        "items_desc": items_desc, # 포함된 영수증 항목이 안나오는 현상 해결
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
    return "로그아웃 되었습니다."

if __name__ == '__main__':
    app.run(debug=True, port=5000)
