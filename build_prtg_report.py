from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

OUT = r"D:\temp\Lap03\Bao_cao_Lab03_Giam_sat_PRTG_SNMP.docx"


def shade(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def margins(cell, top=80, start=120, bottom=80, end=120):
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for name, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{name}"))
        if node is None:
            node = OxmlElement(f"w:{name}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def borders(table, color="D9E2EC"):
    tbl_pr = table._tbl.tblPr
    tbl_borders = tbl_pr.first_child_found_in("w:tblBorders")
    if tbl_borders is None:
        tbl_borders = OxmlElement("w:tblBorders")
        tbl_pr.append(tbl_borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = tbl_borders.find(qn(f"w:{edge}"))
        if el is None:
            el = OxmlElement(f"w:{edge}")
            tbl_borders.append(el)
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "6")
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), color)


def style_table(table, widths=None, header_fill="E8EEF5"):
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    borders(table)
    for r_idx, row in enumerate(table.rows):
        if r_idx == 0:
            tr_pr = row._tr.get_or_add_trPr()
            header = tr_pr.find(qn("w:tblHeader"))
            if header is None:
                header = OxmlElement("w:tblHeader")
                tr_pr.append(header)
            header.set(qn("w:val"), "true")
        for c_idx, cell in enumerate(row.cells):
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            margins(cell)
            if widths and c_idx < len(widths):
                cell.width = widths[c_idx]
            if r_idx == 0:
                shade(cell, header_fill)
                for p in cell.paragraphs:
                    for run in p.runs:
                        run.bold = True


def table(doc, headers, rows, widths=None):
    tbl = doc.add_table(rows=1, cols=len(headers))
    for i, h in enumerate(headers):
        tbl.rows[0].cells[i].text = h
    for row_data in rows:
        cells = tbl.add_row().cells
        for i, v in enumerate(row_data):
            cells[i].text = str(v)
    style_table(tbl, widths=widths)
    doc.add_paragraph()
    return tbl


def code(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.25)
    p.paragraph_format.space_after = Pt(6)
    r = p.add_run(text)
    r.font.name = "Consolas"
    r._element.rPr.rFonts.set(qn("w:eastAsia"), "Consolas")
    r.font.size = Pt(9)
    return p


def callout(doc, title, text, fill="F4F6F9"):
    tbl = doc.add_table(rows=1, cols=1)
    cell = tbl.cell(0, 0)
    shade(cell, fill)
    margins(cell, top=120, bottom=120, start=160, end=160)
    borders(tbl, color="B8C6D6")
    p = cell.paragraphs[0]
    r = p.add_run(title)
    r.bold = True
    r.font.color.rgb = RGBColor(31, 58, 95)
    p.add_run(" " + text)
    doc.add_paragraph()


def image_box(doc, caption, note="Chèn ảnh minh chứng vào khung này."):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    margins(cell, top=220, bottom=220, start=160, end=160)
    borders(tbl, color="9AA6B2")
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("[CHÈN HÌNH ẢNH TẠI ĐÂY]")
    r.bold = True
    r.font.size = Pt(13)
    r.font.color.rgb = RGBColor(120, 120, 120)
    p2 = cell.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r2 = p2.add_run(note)
    r2.italic = True
    r2.font.size = Pt(10)
    r2.font.color.rgb = RGBColor(100, 100, 100)
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cr = cap.add_run(caption)
    cr.italic = True
    cr.font.size = Pt(10)
    cr.font.color.rgb = RGBColor(80, 80, 80)
    doc.add_paragraph()


def setup():
    doc = Document()
    sec = doc.sections[0]
    sec.top_margin = Inches(1)
    sec.bottom_margin = Inches(1)
    sec.left_margin = Inches(1)
    sec.right_margin = Inches(1)
    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
    normal.font.size = Pt(11)
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.1
    for style_name, size, color, before, after in (
        ("Heading 1", 16, "2E74B5", 16, 8),
        ("Heading 2", 13, "2E74B5", 12, 6),
        ("Heading 3", 12, "1F4D78", 8, 4),
    ):
        st = doc.styles[style_name]
        st.font.name = "Calibri"
        st._element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
        st.font.size = Pt(size)
        st.font.bold = True
        st.font.color.rgb = RGBColor.from_string(color)
        st.paragraph_format.space_before = Pt(before)
        st.paragraph_format.space_after = Pt(after)
        st.paragraph_format.keep_with_next = True
    footer = sec.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer.add_run("Lab 03 - PRTG SNMP Monitoring")
    return doc


def h(doc, text, level=1):
    return doc.add_heading(text, level=level)


def p(doc, text):
    return doc.add_paragraph(text)


def b(doc, text):
    return doc.add_paragraph(text, style="List Bullet")


def build():
    doc = setup()
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = title.add_run("BÁO CÁO LAB 03")
    r.bold = True
    r.font.size = Pt(18)
    r.font.color.rgb = RGBColor(11, 37, 69)

    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = sub.add_run("GIÁM SÁT ROUTER, SWITCH, FIREWALL VÀ SERVER BẰNG PRTG NETWORK MONITOR")
    r.bold = True
    r.font.size = Pt(16)
    r.font.color.rgb = RGBColor(46, 116, 181)

    table(
        doc,
        ["Thông tin", "Nội dung"],
        [
            ("Môn học", "Hệ thống giám sát an toàn mạng"),
            ("Sinh viên thực hiện", "................................................"),
            ("Mã sinh viên", "................................................"),
            ("Lớp", "................................................"),
            ("Giảng viên hướng dẫn", "................................................"),
            ("Năm học", "2025 - 2026"),
        ],
        widths=[Inches(2), Inches(4.2)],
    )
    callout(
        doc,
        "Tóm tắt:",
        "Bài lab triển khai PRTG Network Monitor trên Windows để giám sát các thiết bị Router, Switch, Firewall và Server giả lập qua SNMP. "
        "PRTG thu thập các chỉ số CPU, RAM, disk, sessions, load average và traffic counters, sau đó cảnh báo bằng trạng thái sensor, email SMTP Gmail và notification trigger.",
        fill="EAF4FF",
    )
    doc.add_page_break()

    h(doc, "1. Giới thiệu", 1)
    p(doc, "PRTG Network Monitor là công cụ giám sát mạng dạng agentless, hỗ trợ nhiều giao thức như Ping, SNMP, WMI, HTTP, NetFlow và nhiều sensor chuyên dụng. Trong bài lab này, PRTG được dùng để giám sát các thiết bị mạng giả lập bằng SNMP.")
    p(doc, "Mục tiêu của lab là chứng minh quy trình giám sát tập trung: thêm device, cấu hình SNMP credential, tạo sensor, đặt ngưỡng cảnh báo và gửi email khi sensor chuyển Warning hoặc Down/Error.")

    h(doc, "2. Mục tiêu bài lab", 1)
    for item in [
        "Cài đặt và truy cập PRTG Network Monitor trên Windows.",
        "Chạy SNMPSim Dashboard để giả lập Router, Switch, Firewall và Server.",
        "Thêm từng thiết bị vào PRTG bằng địa chỉ 127.0.0.1 và community SNMP riêng.",
        "Tạo SNMP Custom Sensor để đọc CPU, RAM, disk, sessions, load average và interface counters.",
        "Đặt limit cho channel để sensor chuyển Warning hoặc Down/Error khi vượt ngưỡng.",
        "Cấu hình SMTP Gmail và Notification Trigger để gửi email cảnh báo.",
        "Demo tạo sự cố bằng nút Force High Load trên dashboard SNMPSim.",
    ]:
        b(doc, item)

    h(doc, "3. Mô hình triển khai", 1)
    code(
        doc,
        "Windows Host\n"
        "  |-- PRTG Network Monitor: http://127.0.0.1/\n"
        "  |-- SNMPSim Dashboard: http://127.0.0.1:5000\n"
        "  |-- SNMPSim responder: UDP 0.0.0.0:161\n"
        "\n"
        "PRTG Device FortiGate-FW -> 127.0.0.1:161, community fortinet\n"
        "PRTG Device Router-Sim   -> 127.0.0.1:161, community router\n"
        "PRTG Device Switch-Sim   -> 127.0.0.1:161, community switch\n"
        "PRTG Device Ubuntu-Sim   -> 127.0.0.1:161, community ubuntu"
    )
    callout(doc, "Lưu ý:", "Trong lab hiện tại, PRTG và app SNMPSim đều chạy trên cùng máy Windows nên IP device trong PRTG là 127.0.0.1. Nếu đổi SNMPSim sang port 1161 thì PRTG cũng phải sửa SNMP Port thành 1161.", fill="FFF7E6")
    image_box(doc, "Hình 1. Mô hình hoặc dashboard tổng quan PRTG và SNMPSim.", "Chèn ảnh PRTG Root/Local Probe hoặc dashboard SNMPSim đang Running.")

    h(doc, "4. Kiểm tra SNMPSim đang lắng nghe", 1)
    p(doc, "Trước khi thêm sensor, cần kiểm tra SNMPSim có lắng nghe UDP port 161 hay không.")
    code(doc, "netstat -ano -p udp | findstr :161\n\ntasklist /FI \"PID eq <PID_TU_NETSTAT>\"")
    p(doc, "Nếu thấy UDP 0.0.0.0:161 và PID thuộc python.exe hoặc snmpsim-command-responder.exe thì SNMPSim đã chạy đúng.")
    image_box(doc, "Hình 2. Kết quả kiểm tra netstat cho UDP port 161.", "Chèn ảnh CMD/PowerShell có dòng UDP 0.0.0.0:161.")

    h(doc, "5. Danh sách thiết bị và community", 1)
    table(
        doc,
        ["Thiết bị", "Device trong PRTG", "IP/Port", "Community", "Vai trò"],
        [
            ("Firewall", "FortiGate-FW", "127.0.0.1:161", "fortinet", "Giám sát CPU, RAM, disk, sessions"),
            ("Router", "Router-Sim", "127.0.0.1:161", "router", "Giám sát CPU, load, RAM và traffic"),
            ("Switch", "Switch-Sim", "127.0.0.1:161", "switch", "Giám sát CPU, uplink status và traffic"),
            ("Server", "Ubuntu-Sim", "127.0.0.1:161", "ubuntu", "Giám sát CPU, RAM, load và network"),
        ],
        widths=[Inches(1), Inches(1.4), Inches(1.25), Inches(1.1), Inches(2)],
    )

    h(doc, "6. Thêm device vào PRTG", 1)
    p(doc, "Vào Devices -> Local Probe -> Add Device. Với từng thiết bị, nhập Device Name và IPv4 Address/DNS Name là 127.0.0.1.")
    table(
        doc,
        ["Trường", "Giá trị cấu hình"],
        [
            ("Device Name", "FortiGate-FW / Router-Sim / Switch-Sim / Ubuntu-Sim"),
            ("IPv4 Address/DNS Name", "127.0.0.1"),
            ("SNMP Version", "v2c"),
            ("SNMP Port", "161"),
            ("Community String", "fortinet / router / switch / ubuntu tùy thiết bị"),
            ("Inheritance", "Không dùng community public từ parent nếu cấu hình sai"),
        ],
        widths=[Inches(2), Inches(4.2)],
    )
    image_box(doc, "Hình 3. Màn hình Add Device trong PRTG.", "Chèn ảnh form Add Device có Device Name và IP 127.0.0.1.")
    image_box(doc, "Hình 4. Credentials for SNMP Devices.", "Chèn ảnh phần SNMP Version v2c, Community String và SNMP Port.")

    h(doc, "7. Tạo sensor cho Firewall FortiGate-FW", 1)
    p(doc, "Vào device FortiGate-FW -> Add Sensor -> chọn SNMP Custom Sensor. Mỗi OID tạo một sensor riêng.")
    table(
        doc,
        ["Sensor", "OID", "Value Type", "Unit"],
        [
            ("Fortinet CPU", "1.3.6.1.4.1.12356.101.4.1.3.0", "Absolute unsigned integer", "%"),
            ("Fortinet RAM", "1.3.6.1.4.1.12356.101.4.1.4.0", "Absolute unsigned integer", "%"),
            ("Fortinet Disk", "1.3.6.1.4.1.12356.101.4.1.6.0", "Absolute unsigned integer", "%"),
            ("Fortinet Sessions", "1.3.6.1.4.1.12356.101.4.1.8.0", "Absolute unsigned integer", "Count"),
        ],
        widths=[Inches(1.4), Inches(2.6), Inches(1.5), Inches(0.8)],
    )
    image_box(doc, "Hình 5. SNMP Custom Sensor Fortinet CPU.", "Chèn ảnh sensor Fortinet CPU với OID đã cấu hình.")

    h(doc, "8. Tạo sensor cho Router", 1)
    table(
        doc,
        ["Sensor", "OID", "Unit/Ghi chú"],
        [
            ("Router CPU", "1.3.6.1.4.1.9.9.109.1.1.1.1.5.1", "%"),
            ("Router Load 1m", "1.3.6.1.4.1.2021.10.1.3.1", "Count"),
            ("Router RAM Total", "1.3.6.1.4.1.2021.4.5.0", "Bytes"),
            ("Router RAM Available", "1.3.6.1.4.1.2021.4.6.0", "Bytes"),
            ("Router Gi0/0 In", "1.3.6.1.2.1.31.1.1.1.6.2", "Counter/Bytes"),
            ("Router Gi0/0 Out", "1.3.6.1.2.1.31.1.1.1.10.2", "Counter/Bytes"),
        ],
        widths=[Inches(1.6), Inches(3.1), Inches(1.5)],
    )

    h(doc, "9. Tạo sensor cho Switch", 1)
    table(
        doc,
        ["Sensor", "OID", "Unit/Ghi chú"],
        [
            ("Switch CPU", "1.3.6.1.4.1.9.9.109.1.1.1.1.5.1", "%"),
            ("Switch Uplink Status", "1.3.6.1.2.1.2.3.1.2.6", "1 là up, khác 1 là down"),
            ("Switch Uplink In", "1.3.6.1.2.1.31.1.1.1.6.6", "Counter/Bytes"),
            ("Switch Uplink Out", "1.3.6.1.2.1.31.1.1.1.10.6", "Counter/Bytes"),
        ],
        widths=[Inches(1.6), Inches(3.1), Inches(1.5)],
    )

    h(doc, "10. Tạo sensor cho Server Ubuntu-Sim", 1)
    table(
        doc,
        ["Sensor", "OID", "Unit/Ghi chú"],
        [
            ("Ubuntu CPU", "1.3.6.1.4.1.2021.11.9.0", "%"),
            ("Ubuntu RAM Total", "1.3.6.1.4.1.2021.4.5.0", "Bytes"),
            ("Ubuntu RAM Available", "1.3.6.1.4.1.2021.4.6.0", "Bytes"),
            ("Ubuntu Load 1m", "1.3.6.1.4.1.2021.10.1.3.1", "Count"),
        ],
        widths=[Inches(1.6), Inches(3.1), Inches(1.5)],
    )

    h(doc, "11. Cấu hình limit cảnh báo trên channel", 1)
    p(doc, "Sau khi sensor có dữ liệu, vào Overview của sensor, bấm biểu tượng bánh răng ở channel CPU Usage/RAM/Disk để mở Edit Channel. Bật Enable alerting based on limits.")
    table(
        doc,
        ["Sensor/Metric", "Upper Warning Limit", "Upper Error Limit", "Ý nghĩa"],
        [
            ("CPU", "70", "90", "Warning khi >=70%, Down/Error khi >=90%"),
            ("RAM", "70", "90", "Cảnh báo khi thiết bị thiếu bộ nhớ"),
            ("Disk", "80", "90", "Cảnh báo dung lượng disk cao"),
            ("Sessions", "5000", "10000", "Cảnh báo session firewall tăng cao"),
            ("Load average", "5", "10", "Cảnh báo tải server/router cao"),
        ],
        widths=[Inches(1.4), Inches(1.35), Inches(1.35), Inches(2.1)],
    )
    image_box(doc, "Hình 6. Edit Channel CPU Usage và cấu hình Upper Warning/Error Limit.", "Chèn ảnh màn hình Channel Settings đã điền 70/90.")

    h(doc, "12. Cấu hình SMTP Gmail trong PRTG", 1)
    p(doc, "Vào Setup -> System Administration -> Notification Delivery. Chọn Use one SMTP relay server.")
    table(
        doc,
        ["Trường", "Giá trị"],
        [
            ("Delivery Mechanism", "Use one SMTP relay server"),
            ("SMTP Relay Server", "smtp.gmail.com"),
            ("SMTP Relay Port", "587"),
            ("SMTP Relay Authentication", "Use standard SMTP authentication"),
            ("Username", "Tài khoản Gmail gửi cảnh báo"),
            ("Password", "Gmail App Password, không dùng mật khẩu thường"),
            ("Connection Security", "Use SSL/TLS if the server supports it"),
            ("SSL/TLS Method", "TLS 1.2 hoặc Auto-Negotiate"),
            ("Recipient demo", "thongvv.sec@gmail.com"),
        ],
        widths=[Inches(2.1), Inches(4.1)],
    )
    callout(doc, "Bảo mật:", "App Password Gmail là thông tin nhạy cảm. Không nên đưa mật khẩu thật vào báo cáo nộp chính thức; chỉ ghi 'Gmail App Password' hoặc che bớt ký tự.", fill="FFF0F0")
    image_box(doc, "Hình 7. Cấu hình SMTP Delivery trong PRTG.", "Chèn ảnh trang SMTP Delivery sau khi cấu hình Gmail.")

    h(doc, "13. Notification Trigger", 1)
    p(doc, "Limit chỉ làm sensor đổi màu. Muốn gửi email phải thêm Notification Trigger.")
    table(
        doc,
        ["Vị trí", "Cấu hình đề xuất"],
        [
            ("Sensor hoặc Device -> Notifications", "Add State Trigger"),
            ("Warning", "When sensor state is Warning for at least 0 seconds, perform Gmail Alert"),
            ("Down/Error", "When sensor state is Down for at least 0 seconds, perform Gmail Alert"),
            ("Inheritance", "Có thể chọn Only use notification triggers defined above để không chờ trigger mặc định 600 giây"),
        ],
        widths=[Inches(2.2), Inches(4)],
    )
    image_box(doc, "Hình 8. Notification Trigger gửi email khi sensor Warning/Down.", "Chèn ảnh cấu hình Notification Triggers.")

    h(doc, "14. Kịch bản demo", 1)
    table(
        doc,
        ["Bước", "Thao tác", "Kết quả mong muốn"],
        [
            ("1", "Mở SNMPSim Dashboard và xác nhận Running 0.0.0.0:161.", "SNMPSim sẵn sàng trả dữ liệu SNMP."),
            ("2", "Trong PRTG, mở device FortiGate-FW và sensor Fortinet CPU/RAM.", "Sensor có Last Value và trạng thái Up."),
            ("3", "Trên SNMPSim, chọn Fortinet, kéo CPU/RAM lên 100 và bấm Force High Load.", "File .snmprec được cập nhật."),
            ("4", "Chờ PRTG scan interval, ví dụ 60 giây.", "Sensor chuyển Warning hoặc Down/Error."),
            ("5", "Kiểm tra email nhận cảnh báo.", "Gmail nhận email từ PRTG."),
            ("6", "Bấm Reset to Normal trên SNMPSim.", "Sensor phục hồi sau vài chu kỳ scan."),
        ],
        widths=[Inches(0.65), Inches(3.1), Inches(2.45)],
    )
    image_box(doc, "Hình 9. Sensor chuyển Warning/Down sau khi Force High Load.", "Chèn ảnh PRTG sensor màu vàng/đỏ.")
    image_box(doc, "Hình 10. Email cảnh báo nhận được từ PRTG.", "Chèn ảnh Gmail nhận alert.")

    h(doc, "15. Xử lý lỗi thường gặp", 1)
    table(
        doc,
        ["Lỗi", "Nguyên nhân thường gặp", "Cách xử lý"],
        [
            ("SNMP error # -2003 No response", "Sai port, sai community, SNMPSim chưa chạy hoặc port bị chiếm", "Kiểm tra netstat, community, SNMP version v2c, port 161/1161"),
            ("Sensor No data", "OID sai hoặc sensor chưa poll thành công", "Test OID sysName trước, kiểm tra đúng device/community"),
            ("Không gửi email", "SMTP hoặc Notification Trigger chưa đúng", "Test SMTP Settings, kiểm tra Notification Triggers"),
            ("Force High Load lỗi", "Windows khóa file .snmprec khi PRTG/SNMPSim đang đọc", "Restart app sau khi đã sửa code ghi file retry/fallback"),
            ("Không thấy Limit", "Đang ở Settings của sensor chứ chưa vào Channel Settings", "Vào Overview -> bánh răng của channel"),
        ],
        widths=[Inches(1.5), Inches(2.3), Inches(2.4)],
    )

    h(doc, "16. Đánh giá kết quả", 1)
    table(
        doc,
        ["Yêu cầu", "Kết quả đạt được", "Trạng thái"],
        [
            ("Giám sát Firewall", "CPU, RAM, Disk, Sessions qua SNMP Custom Sensor", "Đạt"),
            ("Giám sát Router", "CPU, RAM, Load, Interface counters", "Đạt"),
            ("Giám sát Switch", "CPU, Uplink status, Traffic counters", "Đạt"),
            ("Giám sát Server", "CPU, RAM, Load qua community ubuntu", "Đạt"),
            ("Cảnh báo", "Channel limit + Notification Trigger gửi email", "Đạt"),
        ],
        widths=[Inches(1.5), Inches(3.4), Inches(1)],
    )

    h(doc, "17. Nhận xét và hạn chế", 1)
    h(doc, "17.1 Nhận xét", 2)
    p(doc, "PRTG cho phép tạo mô hình giám sát trực quan và dễ thao tác. Việc dùng SNMP Custom Sensor giúp đọc trực tiếp OID từ thiết bị giả lập. Dashboard PRTG thể hiện rõ trạng thái Up, Warning, Down và lịch sử dữ liệu.")
    h(doc, "17.2 Hạn chế", 2)
    for item in [
        "SNMPSim chỉ là môi trường giả lập, không thay thế hoàn toàn thiết bị thật.",
        "Một số sensor custom cần tạo thủ công từng OID.",
        "Cảnh báo email phụ thuộc SMTP Gmail và App Password.",
        "SMS/Call thật cần dịch vụ ngoài như SMS Gateway, Twilio, PagerDuty hoặc Opsgenie.",
    ]:
        b(doc, item)

    h(doc, "18. Kết luận", 1)
    p(doc, "Bài lab đã xây dựng được hệ thống giám sát Router, Switch, Firewall và Server bằng PRTG Network Monitor qua SNMP. PRTG thu thập metric từ SNMPSim, hiển thị trạng thái sensor, phân loại cảnh báo theo limit và gửi email khi CPU/RAM hoặc các chỉ số khác vượt ngưỡng. Mô hình phù hợp để demo quy trình giám sát mạng tập trung trước khi triển khai trên thiết bị thật.")
    doc.save(OUT)


if __name__ == "__main__":
    build()
    print(OUT)
