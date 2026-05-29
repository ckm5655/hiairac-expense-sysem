from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # 세션 암호화 키

# 시스템 테스트용 모의 데이터 (DB 구조에 맞게 연동 가능)
# 차트가 완벽히 작동하려면 데이터 항목 내 금액(amount)이 '정수(int)'여야 합니다.
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

CATEGORIES = ["교통비", "교통/주차비", "식대비", "식비", "숙박비", "소모품비", "차량유지비", "기타"]

@app.route('/')
def home():
    # 세션 테스트용 로그인 처리 (필요시 로그인 시스템 연동)
    session['username'] = '관리자님'
    session['team'] = '관리자' 
    return redirect(url_for('index'))

@app.route('/index')
def index():
    username = session.get('username', '게스트')
    team = session.get('team', '시운전팀')
    
    # 상단 날짜 필터 (기본값: 현재 년-월)
    current_month = request.args.get('search_month', datetime.now().strftime('%Y-%m'))
    
    month_start_date = f"{current_month}-01"
    month_end_date = f"{current_month}-31"
    
    # 1. 목록에 노출할 리스트 데이터 필터링 (선택 월 기준)
    filtered_trips = [t for t in MOCK_TRIPS if t['date'].startswith(current_month)]
    filtered_trips = sorted(filtered_trips, key=lambda x: x['order'])
    
    # 2. 대시보드 연동용 통합 원본 데이터 가공 (★가장 중요)
    raw_stats_list = []
    dashboard_stats = {'총합': 0, '시운전': 0, '시운전팀': 0, '생산팀': 0, '영업팀': 0, '전장팀': 0}
    
    for t in MOCK_TRIPS:
        try:
            details = json.loads(t['details_json'])
        except:
            details = []
            
        for item in details:
            # 자바스크립트 차트 엔진이 정상 분류할 수 있도록 규격 동기화
            stat_item = {
                "date": t['date'],
                "team": t['team'],
                "place": t['place'],
                "category": item.get('category', '기타'),
                "std_category": item.get('category', '기타'),
                "amount": int(item.get('amount', 0))
            }
            raw_stats_list.append(stat_item)
            
            # 선택 월 기준 상단 카드 요약 누적
            if t['date'].startswith(current_month):
                amt = int(item.get('amount', 0))
                dashboard_stats['총합'] += amt
                
                norm_team = t['team'].replace('팀', '').strip()
                if norm_team in ['시운전', '시운전팀']:
                    dashboard_stats['시운전'] += amt
                elif norm_team == '생산':
                    dashboard_stats['생산팀'] += amt
                elif norm_team == '영업':
                    dashboard_stats['영업팀'] += amt
                elif norm_team == '전장':
                    dashboard_stats['전장팀'] += amt
                    
                if t['team'] in dashboard_stats:
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
    expense_date = request.form.get('expense_date')
    user_name = request.form.get('user_name')
    place = request.form.get('place')
    content = request.form.get('content')
    search_month = request.form.get('search_month', datetime.now().strftime('%Y-%m'))
    
    user_team = session.get('team', '시운전팀')
    if user_team == "관리자" and request.form.get('target_team'):
        user_team = request.form.get('target_team')
        
    # HTML 동적 입력 폼의 다중 데이터 수신 (getlist 메서드 사용)
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
    
    # 수정 모달 팝업 내부 다중 데이터 처리
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
