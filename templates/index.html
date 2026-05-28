<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>부서 경비 정산 신청 시스템</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: '맑은 고딕', sans-serif; margin: 30px; background: #fafafa; color: #333; }
        .header-container { background: white; padding: 20px; border-radius: 8px; border: 1px solid #e5e7eb; margin-bottom: 25px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
        .profile { float: left; font-size: 16px; font-weight: bold; line-height: 40px; }
        .logout-btn { float: right; padding: 8px 15px; background: #ef4444; color: white; text-decoration: none; border-radius: 4px; font-size: 14px; }
        .form-box { background: white; padding: 25px; border-radius: 8px; border: 1px solid #e5e7eb; margin-bottom: 30px; }
        
        .btn-toggle-group { display: flex; gap: 8px; margin-bottom: 20px; border-bottom: 1px solid #e2e8f0; padding-bottom: 15px; }
        .btn-toggle { padding: 10px 20px; font-size: 14px; font-weight: bold; border-radius: 6px; border: 1px solid #cbd5e1; background: white; cursor: pointer; transition: all 0.2s; color: #475569; }
        .btn-toggle:hover { background: #f1f5f9; }
        .btn-toggle.active { background: #1e3a8a; color: white; border-color: #1e3a8a; box-shadow: 0 2px 4px rgba(30,58,138,0.2); }

        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 15px; margin-bottom: 25px; }
        .stats-card { background: white; padding: 15px; border-radius: 6px; border: 1px solid #e2e8f0; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
        .stats-card h4 { margin: 0 0 10px 0; color: #475569; font-size: 14px; }
        .stats-card p { margin: 0; font-size: 18px; font-weight: bold; color: #1e3a8a; }
        
        /* 📉 한눈에 들어오도록 튀어나옴 방지 및 크기 슬림화 수정 */
        .chart-container { display: grid; grid-template-columns: 1.2fr 1fr; gap: 20px; margin-top: 15px; margin-bottom: 20px; }
        .chart-box { background: #fff; padding: 15px; border-radius: 6px; border: 1px solid #e2e8f0; height: 210px; min-width: 0; position: relative; }
        .chart-box.wide { grid-column: span 2; height: 180px; min-width: 0; position: relative; }

        /* 화면 창이 아주 작아졌을 때 좌우로 찢어지거나 튀어나오지 않고 아래로 정렬되도록 보정 */
        @media (max-width: 1024px) {
            .chart-container { grid-template-columns: 1fr; }
            .chart-box.wide { grid-column: span 1; }
        }

        table { width: 100%; border-collapse: collapse; background: white; margin-top: 15px; }
        th, td { border: 1px solid #ddd; padding: 10px; text-align: center; font-size: 14px; }
        th { background: #f3f4f6; font-weight: bold; }
        
        .drag-row { cursor: move; transition: background 0.2s; }
        .drag-row:hover { background: #f0fdf4 !important; }
        .drag-row.dragging { opacity: 0.5; background: #bbf7d0 !important; }
        .drag-handle { font-size: 18px; color: #9ca3af; cursor: move; user-select: none; }

        .btn-download { display: inline-block; padding: 10px 20px; background: #10b981; color: white; text-decoration: none; border-radius: 4px; font-weight: bold; margin-top: 15px; margin-right: 10px; }
        .input-group { margin-bottom: 12px; }
        .input-group label { display: block; margin-bottom: 5px; font-weight: bold; font-size: 13px; color: #4b5563; }
        .input-group input, .input-group select { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
        
        .receipt-table-header { display: grid; grid-template-columns: 2fr 2fr 0.5fr; gap: 15px; font-weight: bold; text-align: center; margin-bottom: 8px; background: #f3f4f6; padding: 10px; border-radius: 4px; border: 1px solid #ddd; }
        .receipt-entry-row { display: grid; grid-template-columns: 2fr 2fr 0.5fr; gap: 15px; margin-bottom: 10px; padding: 5px 10px; background: #fff; align-items: center; }
        
        .btn-add-receipt { padding: 10px 20px; background: #10b981; color: white; border: none; border-radius: 4px; font-weight: bold; cursor: pointer; font-size: 14px; margin-bottom: 20px; }
        .btn-remove-receipt { background: #ef4444; color: white; border: none; padding: 10px; border-radius: 4px; cursor: pointer; font-size: 14px; font-weight: bold; }
        .submit-btn { padding: 14px 25px; background: #1e3a8a; color: white; border: none; border-radius: 4px; font-weight: bold; cursor: pointer; font-size: 16px; width: 100%; margin-top: 10px; }
        
        .btn-action { padding: 4px 8px; font-size: 12px; font-weight: bold; border-radius: 3px; border: 1px solid #ccc; cursor: pointer; text-decoration: none; display: inline-block; margin: 2px; }
        .btn-edit { background: #f59e0b; color: white; border: none; }
        .btn-delete { background: #dc2626; color: white; border: none; }
        .btn-order { background: #4b5563; color: white; border: none; padding: 5px 10px; font-size: 13px; border-radius: 4px; cursor: pointer; }
        
        .modal { display: none; position: fixed; z-index: 100; left: 0; top: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.4); overflow-y: auto; }
        .modal-content { background: white; margin: 5% auto; padding: 25px; border-radius: 8px; width: 550px; box-shadow: 0 4px 10px rgba(0,0,0,0.15); }
        .modal-receipt-row { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 8px; background: #f8fafc; padding: 8px; border-radius: 4px; border: 1px solid #e2e8f0; }
    </style>
    <script>
        const globalCategories = [
            {% for cat in categories %} "{{ cat }}", {% endfor %}
        ];

        function addReceiptLine() {
            const container = document.getElementById('receipt_container');
            if(!container) return;
            let categoryOptions = '';
            globalCategories.forEach(cat => {
                categoryOptions += `<option value="${cat}">${cat}</option>`;
            });

            const newRow = document.createElement('div');
            newRow.className = 'receipt-entry-row';
            newRow.innerHTML = `
                <div>
                    <select name="receipt_category" required style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px;">
                        <option value="">-- 경비 구분 선택 --</option>
                        ${categoryOptions}
                    </select>
                </div>
                <div>
                    <input type="number" name="receipt_amount" min="0" placeholder="영수증 금액 입력 (원)" required style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px;">
                </div>
                <div style="text-align: center;">
                    <button type="button" class="btn-remove-receipt" onclick="removeReceiptLine(this)">🗑️ 삭제</button>
                </div>
            `;
            container.appendChild(newRow);
        }

        function removeReceiptLine(button) {
            button.closest('.receipt-entry-row').remove();
        }

        function openEditModal(btnElement) {
            const tripId = btnElement.getAttribute('data-trip-id');
            const date = btnElement.getAttribute('data-date');
            const user = btnElement.getAttribute('data-user');
            const place = btnElement.getAttribute('data-place');
            const content = btnElement.getAttribute('data-content');
            const detailsJson = btnElement.getAttribute('data-details');
            
            document.getElementById('edit_trip_id').value = tripId;
            document.getElementById('edit_date').value = date;
            document.getElementById('edit_user_name').value = user;
            document.getElementById('edit_place').value = place;
            document.getElementById('edit_content').value = content;
            
            const dynamicContainer = document.getElementById('edit_receipts_container');
            dynamicContainer.innerHTML = ''; 
            
            try {
                const details = JSON.parse(detailsJson);
                details.forEach((item) => {
                    let catOptions = '';
                    globalCategories.forEach(cat => {
                        const selected = (cat === item.category) ? 'selected' : '';
                        catOptions += `<option value="${cat}" ${selected}>${cat}</option>`;
                    });

                    const div = document.createElement('div');
                    div.className = 'modal-receipt-row';
                    div.innerHTML = `
                        <input type="hidden" name="sub_receipt_ids" value="${item.id}">
                        <div>
                            <label style="font-size:11px; color:#6b7280; font-weight:bold;">경비 구분</label>
                            <select name="sub_receipt_categories" style="width:100%; padding:6px; border:1px solid #ccc; border-radius:4px;">
                                ${catOptions}
                            </select>
                        </div>
                        <div>
                            <label style="font-size:11px; color:#6b7280; font-weight:bold;">금액 (원)</label>
                            <input type="number" name="sub_receipt_amounts" value="${item.amount}" style="width:100%; padding:6px; border:1px solid #ccc; border-radius:4px;" required>
                        </div>
                    `;
                    dynamicContainer.appendChild(div);
                });
            } catch (e) {
                console.error("데이터 파싱 오류:", e);
            }
            document.getElementById('editModal').style.display = 'block';
        }

        function closeEditModal() {
            document.getElementById('editModal').style.display = 'none';
        }

        document.addEventListener('DOMContentLoaded', () => {
            const tbody = document.getElementById('drag_tbody');
            if(!tbody) return;
            
            tbody.addEventListener('dragstart', (e) => {
                if(e.target.classList.contains('drag-row')) {
                    e.target.classList.add('dragging');
                }
            });
            tbody.addEventListener('dragend', (e) => {
                if(e.target.classList.contains('drag-row')) {
                    e.target.classList.remove('dragging');
                    reCalculateOrders();
                }
            });
            tbody.addEventListener('dragover', (e) => {
                e.preventDefault();
                const draggingRow = tbody.querySelector('.dragging');
                if(!draggingRow) return;
                
                const siblings = [...tbody.querySelectorAll('.drag-row:not(.dragging)')];
                const nextSibling = siblings.find(sibling => {
                    const box = sibling.getBoundingClientRect();
                    return e.clientY <= box.top + box.height / 2;
                });
                
                if(nextSibling) {
                    tbody.insertBefore(draggingRow, nextSibling);
                } else {
                    tbody.appendChild(draggingRow);
                }
            });
            function reCalculateOrders() {
                const rows = tbody.querySelectorAll('.drag-row');
                rows.forEach((row, index) => {
                    const orderInput = row.querySelector('.order-input');
                    if(orderInput) orderInput.value = index + 1;
                });
            }
        });
    </script>
</head>
<body onload="addReceiptLine()">
    <div class="header-container" style="overflow: hidden;">
        <div class="profile">👑 <strong>{{ username }}</strong> 님 [권한 등급: <span style="color:#1e3a8a;">{{ team }}</span>]</div>
        <a href="/logout" class="logout-btn">로그아웃</a>
    </div>

    <div class="form-box" style="background: #eef2f6;">
        <form method="GET" action="/index">
            <label style="font-weight: bold; margin-right: 10px;">📅 마감 월 선택 조회:</label>
            <input type="month" name="search_month" value="{{ current_month }}" onchange="this.form.submit()" style="padding: 8px; border-radius: 4px; border: 1px solid #ccc;">
        </form>
    </div>

    <div class="form-box" style="background: #f8fafc; border: 1px solid #cbd5e1;">
        {% if team == "관리자" %}
        <h3 style="color: #0f172a; margin-top:0; border-bottom: 2px solid #0f172a; padding-bottom:10px;">📊 {{ current_month }} 전사 부서/출장지 통합 대시보드</h3>
        <div class="btn-toggle-group">
            <button type="button" class="btn-toggle active" onclick="filterTeamStats('ALL', this)">🌐 전사 전체보기</button>
            <button type="button" class="btn-toggle" onclick="filterTeamStats('시운전', this)">🛠️ 시운전팀</button>
            <button type="button" class="btn-toggle" onclick="filterTeamStats('생산팀', this)">⚙️ 생산팀</button>
            <button type="button" class="btn-toggle" onclick="filterTeamStats('영업팀', this)">💼 영업팀</button>
            <button type="button" class="btn-toggle" onclick="filterTeamStats('전장팀', this)">🏭 전장팀</button>
        </div>
        {% else %}
        <h3 style="color: #0f172a; margin-top:0; border-bottom: 2px solid #0f172a; padding-bottom:10px;">📊 {{ current_month }} {{ team }} 경비 현황 대시보드</h3>
        {% endif %}

        <div class="stats-grid">
            <div class="stats-card" style="border-top: 4px solid #1e3a8a; background: #f0f4ff;">
                <h4>선택 월 지출 총합</h4>
                <p id="target_total_display" style="color:#1e3a8a; font-size:22px;">{{ "{:,.0f}".format(dashboard_stats.get('총합', 0)) }}원</p>
            </div>
            
            {% if team == "관리자" or team == "시운전" %}
            <div class="stats-card" style="border-top: 4px solid #3b82f6;">
                <h4>시운전팀 고정누적</h4>
                <p>{{ "{:,.0f}".format(dashboard_stats.get('시운전', 0)) }}원</p>
            </div>
            {% endif %}
            
            {% if team == "관리자" or team == "생산팀" %}
            <div class="stats-card" style="border-top: 4px solid #10b981;">
                <h4>생산팀 고정누적</h4>
                <p>{{ "{:,.0f}".format(dashboard_stats.get('생산팀', 0)) }}원</p>
            </div>
            {% endif %}
            
            {% if team == "관리자" or team == "영업팀" %}
            <div class="stats-card" style="border-top: 4px solid #f59e0b;">
                <h4>영업팀 고정누적</h4>
                <p>{{ "{:,.0f}".format(dashboard_stats.get('영업팀', 0)) }}원</p>
            </div>
            {% endif %}

            {% if team == "관리자" or team == "전장팀" %}
            <div class="stats-card" style="border-top: 4px solid #8b5cf6;">
                <h4>전장팀 고정누적</h4>
                 <p>{{ "{:,.0f}".format(dashboard_stats.get('전장팀', 0)) }}원</p>
            </div>
            {% endif %}
        </div>

        <div class="chart-container">
            <div class="chart-box">
                <canvas id="placeBarChart"></canvas>
            </div>
            <div class="chart-box">
                <canvas id="categoryPieChart"></canvas>
            </div>
            <div class="chart-box wide">
                <canvas id="halfYearLineChart"></canvas>
            </div>
        </div>
    </div>

    <script>
        const rawStatsData = {{ raw_stats_json | safe }};
        const userTeam = "{{ team }}";
        const currentMonthStr = "{{ current_month }}"; 
        
        let placeChartObj = null;
        let categoryChartObj = null;
        let lineChartObj = null;

        function getRecent6Months(targetMonth) {
            let result = [];
            let date = new Date(targetMonth + "-01");
            
            for (let i = 5; i >= 0; i--) {
                let d = new Date(date.getFullYear(), date.getMonth() - i, 1);
                let year = d.getFullYear();
                let month = String(d.getMonth() + 1).padStart(2, '0');
                result.push({
                    key: `${year}-${month}`,
                    label: `${d.getMonth() + 1}월`
                });
            }
            return result;
        }

        function filterTeamStats(selectedTeam, btnElement) {
            if (btnElement) {
                document.querySelectorAll('.btn-toggle').forEach(btn => btn.classList.remove('active'));
                btnElement.classList.add('active');
            }

            const filtered = (selectedTeam === 'ALL') 
                ? rawStatsData 
                : rawStatsData.filter(x => x.team === selectedTeam);

            let totalSum = 0;
            let categoryMap = {'교통비': 0, '식대비': 0, '식비': 0, '숙박비': 0, '소모품비': 0, '차량유지비': 0, '기타': 0};
            let placeMap = {};

            filtered.forEach(item => {
                let rawAmount = item.amount || item.total_amount || 0;
                if (typeof rawAmount === 'string') {
                    rawAmount = parseInt(rawAmount.replace(/[^0-9]/g, '')) || 0;
                }
                totalSum += rawAmount;

                const cat = item.std_category || item.category;
                if (categoryMap[cat] !== undefined) {
                    categoryMap[cat] += rawAmount;
                } else {
                    categoryMap['기타'] += rawAmount;
                }

                if (item.place) {
                    placeMap[item.place] = (placeMap[item.place] || 0) + rawAmount;
                }
            });

            document.getElementById('target_total_display').innerText = totalSum.toLocaleString() + "원";

            if (placeChartObj) {
                placeChartObj.data.labels = Object.keys(placeMap).length ? Object.keys(placeMap) : ['데이터 없음'];
                placeChartObj.data.datasets[0].data = Object.values(placeMap).length ? Object.values(placeMap) : [0];
                placeChartObj.options.plugins.title.text = `📍 [${selectedTeam === 'ALL' ? '전사' : selectedTeam}] 출장지별 지출 순위`;
                placeChartObj.update();
            }

            if (categoryChartObj) {
                categoryChartObj.data.datasets[0].data = [
                    categoryMap['교통비'], 
                    (categoryMap['식대비'] + categoryMap['식비']), 
                    categoryMap['소모품비'], 
                    categoryMap['차량유지비'], 
                    categoryMap['기타']
                ];
                categoryChartObj.options.plugins.title.text = `🧾 [${selectedTeam === 'ALL' ? '전사' : selectedTeam}] 항목별 비용 비율`;
                categoryChartObj.update();
            }

            const recent6 = getRecent6Months(currentMonthStr);
            let trendMap = {};
            recent6.forEach(m => trendMap[m.key] = 0);

            filtered.forEach(item => {
                if (selectedTeam === 'ALL' || item.team === selectedTeam) {
                    const fullDate = item.date || item.expense_date || item.month || "";
                    if (fullDate.length >= 7) {
                        const yyyymm = fullDate.substring(0, 7);
                        if (trendMap[yyyymm] !== undefined) {
                            let rawAmount = item.amount || item.total_amount || 0;
                            if (typeof rawAmount === 'string') {
                                rawAmount = parseInt(rawAmount.replace(/[^0-9]/g, '')) || 0;
                            }
                            trendMap[yyyymm] += rawAmount;
                        }
                    }
                }
            });

            const rows = document.querySelectorAll('#drag_tbody .drag-row');
            rows.forEach(row => {
                if (selectedTeam !== 'ALL') {
                    const teamCell = row.querySelector('td:nth-child(3)');
                    if (teamCell && teamCell.innerText.trim() !== selectedTeam) return;
                }
                const tds = row.querySelectorAll('td');
                let dateIdx = (userTeam === "관리자") ? 3 : 2;
                let amtIdx = (userTeam === "관리자") ? 8 : 7;
                
                if (tds[dateIdx] && tds[amtIdx]) {
                    const dateStr = tds[dateIdx].innerText.trim();
                    if (dateStr && dateStr.length >= 7) {
                        const yyyymm = dateStr.substring(0, 7);
                        if (trendMap[yyyymm] !== undefined) {
                            if (yyyymm === currentMonthStr) {
                                trendMap[currentMonthStr] = totalSum; 
                            }
                        }
                    }
                }
            });

            const lineData = recent6.map(m => trendMap[m.key]);
            const lineLabels = recent6.map(m => m.label);

            if (lineChartObj) {
                lineChartObj.data.labels = lineLabels;
                lineChartObj.data.datasets[0].data = lineData;
                lineChartObj.options.plugins.title.text = `📈 [${selectedTeam === 'ALL' ? '전사' : selectedTeam}] 최근 6개월 팀 비용 집계 추이 (단위: 원)`;
                lineChartObj.update();
            }
        }

        window.addEventListener('DOMContentLoaded', () => {
            const placeCtx = document.getElementById('placeBarChart').getContext('2d');
            placeChartObj = new Chart(placeCtx, {
                type: 'bar',
                data: {
                    labels: [],
                    datasets: [{ label: '사용 금액 (원)', data: [], backgroundColor: '#3b82f6', borderWidth: 1 }]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false, // 부모 컨테이너 크기에 반응하도록 변경
                    plugins: { title: { display: true, font:{size:13, bold:true} } }
                }
            });

            const pieCtx = document.getElementById('categoryPieChart').getContext('2d');
            categoryChartObj = new Chart(pieCtx, {
                type: 'pie',
                data: {
                    labels: ['교통/주차비', '식대비', '소모품비', '차량유지비', '기타'],
                    datasets: [{ data: [0, 0, 0, 0, 0], backgroundColor: ['#ef4444', '#3b82f6', '#10b981', '#f59e0b', '#9ca3af'] }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false, // 부모 컨테이너 크기에 반응하도록 변경
                    plugins: { title: { display: true, font:{size:13, bold:true} } }
                }
            });

            const lineCtx = document.getElementById('halfYearLineChart').getContext('2d');
            lineChartObj = new Chart(lineCtx, {
                type: 'line',
                data: {
                    labels: [], 
                    datasets: [{
                        label: '지출 금액 (원)',
                        data: [],
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        fill: true,
                        tension: 0.2,
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false, // 부모 컨테이너 크기에 반응하도록 변경
                    plugins: {
                        title: { display: true, font:{size:13, bold:true} },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    let val = context.parsed.y;
                                    return ' 금액: ' + val.toLocaleString() + ' 원';
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            min: 0,
                            title: { display: true, text: '단위 (원)', font: { size: 11 } },
                            ticks: {
                                callback: function(value) { return value.toLocaleString(); }
                            }
                        }
                    }
                }
            });

            setTimeout(() => {
                if (userTeam === "관리자") {
                    filterTeamStats('ALL', document.querySelector('.btn-toggle'));
                } else {
                    filterTeamStats(userTeam, null);
                }
            }, 100);
        });
    </script>

    <div class="form-box">
        <h3 style="color: #1e3a8a; border-bottom: 2px solid #1e3a8a; padding-bottom: 10px; margin-top: 0;">📝 통합 출장 경비 신청 (영수증 일괄 등록)</h3>
        <form method="POST" action="/expense/add">
            <input type="hidden" name="search_month" value="{{ current_month }}">
            
            <div style="background: #f8fafc; padding: 20px; border-radius: 6px; border: 1px solid #e2e8f0; margin-bottom: 25px;">
                <h4 style="margin: 0 0 15px 0; color: #334155;">💼 핵심 출장 및 사용자 정보</h4>
                <div style="display: grid; grid-template-columns: 1fr 1fr 1.2fr 1.8fr; gap: 15px;">
                    <div class="input-group">
                        <label>지출 일자</label>
                        <input type="date" name="expense_date" required>
                    </div>
                    <div class="input-group">
                        <label>사용자 (이름)</label>
                        <input type="text" name="user_name" placeholder="실사용자 이름" required>
                    </div>
                    <div class="input-group">
                        <label>출장지</label>
                        <input type="text" name="place" placeholder="예: 삼성중공업" required>
                    </div>
                    <div class="input-group">
                        <label>출장 목적 및 내용 (표지 제목)</label>
                        <input type="text" name="content" placeholder="예: SPOT COOLER 점검 지원" required>
                    </div>
                </div>
                {% if team == "관리자" %}
                <div style="margin-top:15px; background:#fff3cd; padding:10px; border-radius:4px; border:1px solid #ffeba2;">
                    <label style="font-weight:bold; font-size:13px;">⚙️ 관리자 전용 대리 등록 권한 -> 대상 팀 선택 : </label>
                    <select name="target_team" style="padding:5px; width:150px; display:inline-block; margin-left:10px;">
                        <option value="시운전">시운전</option>
                        <option value="생산팀">생산팀</option>
                        <option value="영업팀">영업팀</option>
                        <option value="전장팀">전장팀</option>
                    </select>
                </div>
                {% endif %}
            </div>
            
            <h4 style="margin: 0 0 10px 0; color: #334155;">🧾 영수증 내역 입력</h4>
            <div class="receipt-table-header">
                <div>영수증 경비 구분</div>
                <div>영수증 금액 (원)</div>
                <div>관리</div>
            </div>

            <div id="receipt_container"></div>

            <button type="button" class="btn-add-receipt" onclick="addReceiptLine()">➕ 영수증 입력 항목 추가</button>
            <button type="submit" class="submit-btn">🧾 상기 모든 영수증 저장 및 제출하기</button>
        </form>
    </div>

    <div class="form-box">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <h3>📊 {{ current_month }} 등록된 출장 정산 목록 
                {% if team == "관리자" %}<span style="color:#2563eb;">(전사 부서 전체 통합 노출 모드)</span>{% endif %}
                <span style="font-size:12px; color:#10b981; font-weight:normal;">(💡 드래그로 순서 배치 가능)</span>
            </h3>
            <button type="submit" form="orderForm" class="btn-order">🔄 변경된 순번으로 목록 재정렬</button>
        </div>
        
        <form id="orderForm" method="POST" action="/expense/reorder">
            <input type="hidden" name="search_month" value="{{ current_month }}">
            <table>
                <thead>
                    <tr>
                        <th style="width: 40px;">이동</th>
                        <th style="width: 70px;">순번</th>
                        {% if team == "관리자" %}<th style="width: 80px;">신청부서</th>{% endif %}
                        <th>지출일자</th>
                        <th>사용자</th>
                        <th>출장지</th>
                        <th>출장 목적 및 대표 내용</th>
                        <th>포함된 영수증 항목</th>
                        <th>총 금액</th>
                        <th style="width: 120px;">작업</th>
                    </tr>
                </thead>
                <tbody id="drag_tbody">
                    {% for trip in trips %}
                    <tr class="drag-row" draggable="true">
                        <td class="drag-handle">☰</td>
                        <td>
                            <input type="hidden" name="trip_ids" value="{{ trip.trip_id }}">
                            <input type="number" name="display_orders" value="{{ trip.order }}" class="order-input" readonly style="width: 45px; text-align: center; border: none; background:transparent; font-weight:bold;">
                        </td>
                        {% if team == "관리자" %}
                        <td><span style="background:#e2e8f0; padding:2px 6px; border-radius:4px; font-weight:bold; font-size:12px;">{{ trip.team }}</span></td>
                        {% endif %}
                        <td>{{ trip.date }}</td>
                        <td style="font-weight: bold; color: #1e3a8a;">{{ trip.user_name }}</td>
                        <td>{{ trip.place }}</td>
                        <td style="text-align: left;">{{ trip.content }}</td>
                        <td style="text-align: left; font-size: 13px; color: #555;">
                            {% for detail in trip.details %}
                                <span style="background: #f1f5f9; padding: 2px 6px; border-radius: 4px; margin-right:4px; display:inline-block; margin-bottom:2px;">
                                    {{ detail.category }}: {{ "{:,.0f}".format(detail.amount) }}원
                                </span>
                            {% endfor %}
                        </td>
                        <td style="text-align: right; font-weight: bold; color:#10b981;">{{ "{:,.0f}".format(trip.total_amount) }}원</td>
                        <td>
                            <button type="button" class="btn-action btn-edit" 
                                    data-trip-id="{{ trip.trip_id }}"
                                    data-date="{{ trip.date }}"
                                    data-user="{{ trip.user_name }}"
                                    data-place="{{ trip.place }}"
                                    data-content="{{ trip.content }}"
                                    data-details='{{ trip.details_json | safe }}'
                                    onclick="openEditModal(this)">수정</button>
                            <a href="/expense/delete/{{ trip.trip_id }}?search_month={{ current_month }}" class="btn-action btn-delete" onclick="return confirm('이 출장 건에 포함된 모든 영수증 데이터가 일괄 삭제됩니다. 진행하시겠습니까?')">삭제</a>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </form>
        
        {% if team == "관리자" %}
            <div style="margin-top: 15px; background: #f8fafc; padding: 15px; border-radius: 6px; border: 1px solid #cbd5e1;">
                <h4 style="margin:0 0 10px 0;">📥 관리자 전용 마감 문서 개별/전체 다운로드</h4>
                <a href="/download/cover?team=시운전&month={{ current_month }}" class="btn-download" style="background:#3b82f6;">📥 시운전팀 서식 (.xlsx)</a>
                <a href="/download/cover?team=생산팀&month={{ current_month }}" class="btn-download" style="background:#10b981;">📥 생산팀 서식 (.xlsx)</a>
                <a href="/download/cover?team=영업팀&month={{ current_month }}" class="btn-download" style="background:#f59e0b;">📥 영업팀 서식 (.xlsx)</a>
                <a href="/download/cover?team=전장팀&month={{ current_month }}" class="btn-download" style="background:#8b5cf6;">📥 전장팀 서식 (.xlsx)</a>
            </div>
        {% else %}
            <a href="/download/cover?team={{ team }}&month={{ current_month }}" class="btn-download">📥 {{ team }} 정산서 마감 다운로드 (.xlsx)</a>
        {% endif %}
    </div>

    <div id="editModal" class="modal">
        <div class="modal-content">
            <h3 style="margin-top:0; border-bottom: 2px solid #1e3a8a; padding-bottom:10px; color:#1e3a8a;">✏️ 출장 내역 및 영수증 세부 변경</h3>
            <form method="POST" action="/expense/edit">
                <input type="hidden" name="search_month" value="{{ current_month }}">
                <input type="hidden" id="edit_trip_id" name="trip_id">
                
                <div class="input-group">
                    <label>지출 일자</label>
                    <input type="date" id="edit_date" name="expense_date" required>
                </div>
                <div class="input-group">
                    <label>사용자 (이름)</label>
                    <input type="text" id="edit_user_name" name="user_name" required>
                </div>
                <div class="input-group">
                    <label>출장지</label>
                    <input type="text" id="edit_place" name="place" required>
                </div>
                <div class="input-group">
                    <label>출장 목적 및 내용</label>
                    <input type="text" id="edit_content" name="content" required>
                </div>
                
                <h4 style="margin: 15px 0 10px 0; color: #334155;">🧾 영수증 항목 변경</h4>
                <div id="edit_receipts_container"></div>
                
                <div style="margin-top: 20px; display: flex; gap: 10px;">
                    <button type="submit" class="submit-btn" style="margin: 0; width:50%;">💾 수정사항 저장</button>
                    <button type="button" class="submit-btn" style="margin: 0; background:#94a3b8; width:50%;" onclick="closeEditModal()">취소</button>
                </div>
            </form>
        </div>
    </div>
</body>
</html>
