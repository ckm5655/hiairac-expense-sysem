@app.route('/download/cover')
def download_cover():
    target_team = request.args.get('team')
    target_month = request.args.get('month', datetime.date.today().strftime('%Y-%m'))
    
    if not target_team.endswith('팀') and target_team != "시운전":
        target_team += "팀"
        
    raw_data = [x for x in ALL_EXPENSES if x.get('team') == target_team and x.get('date', '').startswith(target_month)]
    # 전체 기초 정렬 (날짜 순)
    raw_data.sort(key=lambda x: x.get('date', ''))
    
    # --- [데이터 가공] 1번 시트용: 건별 일괄 합산 로직 ---
    aggregated = {}
    for exp in raw_data:
        key = (exp.get('date', ''), exp.get('content', ''), exp.get('place', ''), exp.get('user_name', ''))
        amt = exp.get('amount', 0)
        cat = exp.get('category', '기타')
        
        if key not in aggregated:
            aggregated[key] = {
                "date": key[0], "content": key[1], "place": key[2], "user_name": key[3],
                "total": 0, "교통비": 0, "식대비": 0, "숙박비": 0, "차량유지비": 0, "기타": 0
            }
            
        aggregated[key]["total"] += amt
        
        if cat in ["교통비", "주차비"]:
            aggregated[key]["교통비"] += amt
        elif cat in ["식비", "식대비"]:
            aggregated[key]["식대비"] += amt
        elif cat == "숙박비":
            aggregated[key]["숙박비"] += amt
        elif cat == "차량유지비":
            aggregated[key]["차량유지비"] += amt
        else: # 소모품비와 기타는 기타로 병합
            aggregated[key]["기타"] += amt

    sorted_cover_rows = list(aggregated.values())
    sorted_cover_rows.sort(key=lambda x: x['date'])
    
    # --- [엑셀 생성 시작] ---
    wb = openpyxl.Workbook()
    
    # 공통 디자인 자원 설정
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

    # -------------------------------------------------------------
    # 📑 첫 번째 시트: 정산서 표지 (건별 합산)
    # -------------------------------------------------------------
    ws1 = wb.active
    ws1.title = f"{target_month[5:7]}월 정산서"
    ws1.views.sheetView[0].showGridLines = True
    
    # 제목 및 결재란 (H~K열 배치)
    ws1.merge_cells('A1:D2')
    ws1['A1'] = f"{target_month[5:7]}월 개인경비 사용내역"
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
    ws1['A4'] = f"작성일자: {datetime.date.today().strftime('%Y년 %m월 %d일')}  /  부서: {target_team}"
    ws1['A4'].font = font_main
    ws1.row_dimensions[4].height = 24

    # 11개 열 헤더
    headers1 = ["순번", "일자", "내 용", "출장지", "금액(합계)", "교통비", "식대비", "숙박비", "차량유지비", "기타", "사용자"]
    for col_idx, h in enumerate(headers1, 1):
        cell = ws1.cell(row=5, column=col_idx, value=h)
        cell.font = font_header; cell.alignment = align_center; cell.border = thin_border; cell.fill = fill_header
    ws1.row_dimensions[5].height = 32

    # 데이터 작성
    r_idx = 6
    for idx, row_data in enumerate(sorted_cover_rows, 1):
        ws1.cell(row=r_idx, column=1, value=idx).alignment = align_center
        ws1.cell(row=r_idx, column=2, value=row_data['date'][5:]).alignment = align_center
        ws1.cell(row=r_idx, column=3, value=row_data['content']).alignment = align_left
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

    # 표지 합계행
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

    # 가지급금 마감 라인 수식 세팅
    budget_map = {"생산팀": 500000, "영업팀": 500000, "시운전팀": 1000000, "전장팀": 800000, "시운전": 1000000}
    team_budget = budget_map.get(target_team, 0)
    budget_str = f"{team_budget:,.0f}" if team_budget > 0 else "0"
    
    r_idx += 2
    ws1.merge_cells(start_row=r_idx, start_column=1, end_row=r_idx, end_column=11)
    summary_cell = ws1.cell(row=r_idx, column=1)
    
    if team_budget > 0:
        summary_cell.value = f'="가지급금금액(이월잔액포함) [ {budget_str} ]   -   총경비사용금액 [ " & TEXT(E{sum_row_idx}, "#,##0") & " ]   =   잔액 [ " & TEXT({team_budget}-E{sum_row_idx}, "#,##0") & " ]"'
    else:
        summary_cell.value = f'="가지급금금액(이월잔액포함) [ 0 ]   -   총경비사용금액 [ " & TEXT(E{sum_row_idx}, "#,##0") & " ]   =   잔액 [ " & TEXT(0-E{sum_row_idx}, "#,##0") & " ]"'
        
    summary_cell.font = Font(name='맑은 고딕', size=12, bold=True, color='1F2937')
    summary_cell.alignment = align_center
    ws1.row_dimensions[r_idx].height = 36

    # 규격 강제 세팅 (A=3, C=30, 나머지=10)
    widths1 = {1: 3, 2: 10, 3: 30, 4: 10, 5: 10, 6: 10, 7: 10, 8: 10, 9: 10, 10: 10, 11: 10}
    for col_idx, w in widths1.items():
        ws1.column_dimensions[openpyxl.utils.get_column_letter(col_idx)].width = w

    # -------------------------------------------------------------
    # 📑 두 번째 시트: 상세내역 (개별 데이터 나열)
    # -------------------------------------------------------------
    ws2 = wb.create_sheet(title="상세내역")
    ws2.views.sheetView[0].showGridLines = True
    
    # 타이틀 영역
    ws2.merge_cells('A1:C2')
    ws2['A1'] = "지출 항목별 상세 증빙내역"
    ws2['A1'].font = Font(name='맑은 고딕', size=14, bold=True, color='374151')
    ws2['A1'].alignment = Alignment(horizontal='left', vertical='center')
    
    ws2.row_dimensions[1].height = 20
    ws2.row_dimensions[4].height = 28
    
    # 상세 내역 헤더 (8개 구조)
    headers2 = ["순번", "사용일자", "성명", "경비구분", "지출 내용 및 세부 목적", "출장지", "사용 금액", "비고(영수증확인)"]
    for col_idx, h in enumerate(headers2, 1):
        cell = ws2.cell(row=4, column=col_idx, value=h)
        cell.font = font_header; cell.alignment = align_center; cell.border = thin_border; cell.fill = fill_header
        
    # 개별 로우 순차 기록
    d_idx = 5
    for idx, exp in enumerate(raw_data, 1):
        ws2.cell(row=d_idx, column=1, value=idx).alignment = align_center
        ws2.cell(row=d_idx, column=2, value=exp.get('date', '')[5:]).alignment = align_center
        ws2.cell(row=d_idx, column=3, value=exp.get('user_name', '')).alignment = align_center
        ws2.cell(row=d_idx, column=4, value=exp.get('category', '')).alignment = align_center
        ws2.cell(row=d_idx, column=5, value=exp.get('content', '')).alignment = align_left
        ws2.cell(row=d_idx, column=6, value=exp.get('place', '')).alignment = align_center
        
        amt_cell = ws2.cell(row=d_idx, column=7, value=exp.get('amount', 0))
        amt_cell.number_format = '#,##0'; amt_cell.alignment = align_right
        
        ws2.cell(row=d_idx, column=8, value="확인완료").alignment = align_center
        
        for c in range(1, 9):
            cell = ws2.cell(row=d_idx, column=c)
            cell.border = thin_border
            cell.font = font_main
            
        ws2.row_dimensions[d_idx].height = 24
        d_idx += 1
        
    # 상세내역 총계행
    ws2.merge_cells(start_row=d_idx, start_column=1, end_row=d_idx, end_column=6)
    ws2.cell(row=d_idx, column=1, value="총 상세 지출액 합계").font = font_sum
    ws2.cell(row=d_idx, column=1).alignment = align_center
    
    for c in range(1, 9):
        cell = ws2.cell(row=d_idx, column=c)
        cell.border = thin_border; cell.fill = fill_sum
        
    sum_cell2 = ws2.cell(row=d_idx, column=7, value=f"=SUM(G5:G{d_idx-1})")
    sum_cell2.font = font_sum; sum_cell2.number_format = '#,##0'; sum_cell2.alignment = align_right
    ws2.row_dimensions[d_idx].height = 26
    
    # 2번 시트용 가독성 너비 배정 (순번=4, 내용=32, 금액=14 등)
    widths2 = [4, 11, 10, 12, 32, 15, 14, 16]
    for i, w in enumerate(widths2, 1):
        ws2.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w

    # --- [파일 반환] ---
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    filename = f"정산서_{target_team}_{target_month}.xlsx"
    return send_file(output, as_attachment=True, download_name=filename, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
