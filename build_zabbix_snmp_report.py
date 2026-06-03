from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


OUT = r"D:\temp\Lap03\Bao_cao_Lab03_Giam_sat_Router_Switch_Firewall_Zabbix.docx"


def set_cell_shading(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_margins(cell, top=80, start=120, bottom=80, end=120):
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


def set_table_borders(table, color="D9E2EC"):
    tbl_pr = table._tbl.tblPr
    borders = tbl_pr.first_child_found_in("w:tblBorders")
    if borders is None:
        borders = OxmlElement("w:tblBorders")
        tbl_pr.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = borders.find(qn(f"w:{edge}"))
        if el is None:
            el = OxmlElement(f"w:{edge}")
            borders.append(el)
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "6")
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), color)


def style_table(table, widths=None, header_fill="E8EEF5"):
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    set_table_borders(table)
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
            set_cell_margins(cell)
            if widths and c_idx < len(widths):
                cell.width = widths[c_idx]
            if r_idx == 0:
                set_cell_shading(cell, header_fill)
                for p in cell.paragraphs:
                    for run in p.runs:
                        run.bold = True


def add_table(doc, headers, rows, widths=None):
    table = doc.add_table(rows=1, cols=len(headers))
    for i, h in enumerate(headers):
        table.rows[0].cells[i].text = h
    for row_data in rows:
        cells = table.add_row().cells
        for i, v in enumerate(row_data):
            cells[i].text = str(v)
    style_table(table, widths=widths)
    doc.add_paragraph()
    return table


def add_code(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.25)
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(6)
    run = p.add_run(text)
    run.font.name = "Consolas"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Consolas")
    run.font.size = Pt(9)
    return p


def add_callout(doc, title, text, fill="F4F6F9"):
    table = doc.add_table(rows=1, cols=1)
    cell = table.cell(0, 0)
    set_cell_shading(cell, fill)
    set_cell_margins(cell, top=120, bottom=120, start=160, end=160)
    set_table_borders(table, color="B8C6D6")
    p = cell.paragraphs[0]
    r = p.add_run(title)
    r.bold = True
    r.font.color.rgb = RGBColor(31, 58, 95)
    p.add_run(" " + text)
    doc.add_paragraph()


def add_image_placeholder(doc, caption, note="Dán ảnh minh chứng vào khung này."):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    cell = table.cell(0, 0)
    cell.width = Inches(6.4)
    set_cell_shading(cell, "FFFFFF")
    set_cell_margins(cell, top=220, bottom=220, start=160, end=160)
    set_table_borders(table, color="9AA6B2")
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
    cap.paragraph_format.space_after = Pt(10)
    cr = cap.add_run(caption)
    cr.italic = True
    cr.font.size = Pt(10)
    cr.font.color.rgb = RGBColor(80, 80, 80)
    return table


def setup_doc():
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
    footer.add_run("Lab 03 - Zabbix SNMP Monitoring")
    return doc


def heading(doc, text, level=1):
    return doc.add_heading(text, level=level)


def para(doc, text):
    return doc.add_paragraph(text)


def bullet(doc, text):
    return doc.add_paragraph(text, style="List Bullet")


def build():
    doc = setup_doc()

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("BÁO CÁO LAB 03")
    r.bold = True
    r.font.size = Pt(18)
    r.font.color.rgb = RGBColor(11, 37, 69)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("GIÁM SÁT ROUTER, SWITCH, FIREWALL BẰNG ZABBIX QUA SNMP")
    r.bold = True
    r.font.size = Pt(16)
    r.font.color.rgb = RGBColor(46, 116, 181)

    add_table(
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
        widths=[Inches(2.0), Inches(4.2)],
    )

    add_callout(
        doc,
        "Tóm tắt:",
        "Bài lab xây dựng mô hình giám sát Router, Switch và Firewall bằng Zabbix thông qua giao thức SNMP. "
        "Các thiết bị được giả lập bằng SNMPSim, Zabbix thu thập các chỉ số CPU, RAM, disk, session, load average "
        "và traffic counters, sau đó tạo trigger cảnh báo khi vượt ngưỡng.",
        fill="EAF4FF",
    )

    doc.add_page_break()

    heading(doc, "1. Giới thiệu", 1)
    para(
        doc,
        "Trong quản trị mạng, việc theo dõi trạng thái Router, Switch và Firewall là nhiệm vụ quan trọng để phát hiện sớm "
        "các sự cố như quá tải CPU, thiếu RAM, lưu lượng bất thường, interface down hoặc số lượng session tăng cao. "
        "Zabbix là công cụ giám sát mã nguồn mở có khả năng thu thập dữ liệu qua SNMP, hiển thị dashboard và gửi cảnh báo."
    )
    para(
        doc,
        "Trong bài lab này, các thiết bị mạng được giả lập bằng SNMPSim. Mỗi thiết bị có một community riêng và một tập OID riêng. "
        "Zabbix sẽ tạo host SNMP tương ứng để poll dữ liệu định kỳ, sau đó dùng trigger để cảnh báo."
    )

    heading(doc, "2. Mục tiêu bài lab", 1)
    for item in [
        "Cài đặt và chạy SNMPSim để giả lập Router, Switch, Firewall và Server.",
        "Kiểm tra dữ liệu SNMP bằng công cụ snmpwalk trên Ubuntu.",
        "Thêm các host Router, Switch, Firewall vào Zabbix bằng SNMPv2c.",
        "Tạo item giám sát CPU, RAM, disk, sessions, load average và traffic counters.",
        "Tạo trigger cảnh báo Warning/Critical khi chỉ số vượt ngưỡng.",
        "Cấu hình cảnh báo qua Web, Email, Telegram/SMS hoặc Call gateway nếu cần.",
        "Xây dựng dashboard Zabbix để theo dõi tình trạng thiết bị tập trung.",
    ]:
        bullet(doc, item)

    heading(doc, "3. Mô hình triển khai", 1)
    add_code(
        doc,
        "SNMPSim Dashboard / SNMP Agent giả lập\n"
        "        |\n"
        "        |-- UDP 1161, SNMPv2c\n"
        "        |\n"
        "Zabbix Server\n"
        "        |\n"
        "        |-- Items: CPU, RAM, Disk, Sessions, Traffic, Load\n"
        "        |-- Triggers: Warning/Critical\n"
        "        |-- Actions: Web, Email, Telegram/SMS, Call gateway\n"
        "        |\n"
        "Dashboard / Problems / Latest data"
    )
    add_callout(
        doc,
        "Lưu ý:",
        "Nếu Ubuntu đã có dịch vụ snmpd chiếm port 161, nên chạy SNMPSim ở port 1161 để tránh xung đột. "
        "Trong Zabbix, tất cả host SNMP giả lập sẽ dùng IP 127.0.0.1 và port 1161, khác nhau ở community.",
        fill="FFF7E6",
    )
    add_image_placeholder(
        doc,
        "Hình 1. Mô hình giám sát Router, Switch, Firewall bằng Zabbix qua SNMP.",
        "Chèn sơ đồ topology hoặc ảnh dashboard SNMPSim/Zabbix tổng quan.",
    )

    heading(doc, "4. Danh sách thiết bị giám sát", 1)
    add_table(
        doc,
        ["Thiết bị", "Host Zabbix", "Community", "Vai trò", "Chỉ số chính"],
        [
            ("Firewall", "FortiGate-FW", "fortinet", "Tường lửa/gateway bảo vệ mạng", "CPU, RAM, Disk, Sessions"),
            ("Router", "Router-Sim", "router", "Định tuyến và gateway", "CPU, RAM, Load, Interface traffic"),
            ("Switch", "Switch-Sim", "switch", "Chuyển mạch nội bộ", "CPU, RAM, Uplink status, Traffic counters"),
            ("Server", "Ubuntu-Sim", "ubuntu", "Máy chủ Linux giả lập", "CPU, RAM, Load, Network traffic"),
        ],
        widths=[Inches(1.0), Inches(1.25), Inches(0.9), Inches(1.6), Inches(1.7)],
    )

    heading(doc, "5. Cài đặt và chạy SNMPSim", 1)
    para(doc, "Trên máy Ubuntu chạy lab, vào thư mục project SNMPSim và chạy ứng dụng Flask.")
    add_code(
        doc,
        "pip install -r requirements.txt\n"
        "export SNMPSIM_ENDPOINT=\"0.0.0.0:1161\"\n"
        "python app.py"
    )
    para(
        doc,
        "Sau khi chạy, mở dashboard web để kiểm tra trạng thái SNMPSim. Dashboard cho phép xem topology, xem metric realtime, "
        "ép CPU/RAM cao để giả lập sự cố và reset thiết bị về trạng thái bình thường."
    )
    add_image_placeholder(
        doc,
        "Hình 2. Dashboard SNMPSim hiển thị trạng thái Running và topology thiết bị.",
        "Chèn ảnh màn hình dashboard SNMPSim đang Running ở port 1161.",
    )

    heading(doc, "6. Kiểm tra SNMP bằng snmpwalk", 1)
    para(doc, "Trước khi thêm host vào Zabbix, cần kiểm tra SNMPSim trả dữ liệu đúng.")
    add_code(
        doc,
        "snmpwalk -v2c -c fortinet udp:127.0.0.1:1161 1.3.6.1.2.1.1.5.0\n"
        "snmpwalk -v2c -c router   udp:127.0.0.1:1161 1.3.6.1.2.1.1.5.0\n"
        "snmpwalk -v2c -c switch   udp:127.0.0.1:1161 1.3.6.1.2.1.1.5.0\n"
        "snmpwalk -v2c -c ubuntu   udp:127.0.0.1:1161 1.3.6.1.2.1.1.5.0"
    )
    para(doc, "Nếu lệnh trả về sysName của thiết bị thì SNMP đã hoạt động đúng.")
    add_image_placeholder(
        doc,
        "Hình 3. Kết quả snmpwalk kiểm tra community fortinet/router/switch.",
        "Chèn ảnh terminal có kết quả snmpwalk trả về sysName hoặc OID metric.",
    )

    heading(doc, "7. Cấu hình host trong Zabbix", 1)
    para(doc, "Vào Data collection -> Hosts -> Create host. Mỗi thiết bị tạo một host riêng.")
    add_table(
        doc,
        ["Trường cấu hình", "FortiGate-FW", "Router-Sim", "Switch-Sim"],
        [
            ("Host name", "FortiGate-FW", "Router-Sim", "Switch-Sim"),
            ("Host group", "SNMPSim Lab", "SNMPSim Lab", "SNMPSim Lab"),
            ("Interface", "SNMP", "SNMP", "SNMP"),
            ("IP address", "127.0.0.1", "127.0.0.1", "127.0.0.1"),
            ("Port", "1161", "1161", "1161"),
            ("SNMP version", "SNMPv2", "SNMPv2", "SNMPv2"),
            ("Community", "fortinet", "router", "switch"),
        ],
        widths=[Inches(1.5), Inches(1.55), Inches(1.55), Inches(1.55)],
    )
    add_image_placeholder(
        doc,
        "Hình 4. Cấu hình host SNMP trong Zabbix.",
        "Chèn ảnh màn hình Create host/Edit host với IP 127.0.0.1, port 1161 và community.",
    )

    heading(doc, "8. Item giám sát Firewall", 1)
    add_table(
        doc,
        ["Tên item", "Key", "OID", "Kiểu", "Đơn vị"],
        [
            ("System name", "fortinet.sysname", "1.3.6.1.2.1.1.5.0", "Character", ""),
            ("CPU usage", "fortinet.cpu", "1.3.6.1.4.1.12356.101.4.1.3.0", "Numeric unsigned", "%"),
            ("RAM usage", "fortinet.ram", "1.3.6.1.4.1.12356.101.4.1.4.0", "Numeric unsigned", "%"),
            ("Disk usage", "fortinet.disk", "1.3.6.1.4.1.12356.101.4.1.6.0", "Numeric unsigned", "%"),
            ("Sessions", "fortinet.sessions", "1.3.6.1.4.1.12356.101.4.1.8.0", "Numeric unsigned", "sessions"),
        ],
        widths=[Inches(1.35), Inches(1.3), Inches(2.35), Inches(1.1), Inches(0.65)],
    )
    add_image_placeholder(
        doc,
        "Hình 5. Các item SNMP của Firewall trong Zabbix.",
        "Chèn ảnh danh sách item hoặc Latest data của FortiGate-FW.",
    )

    heading(doc, "9. Item giám sát Router", 1)
    add_table(
        doc,
        ["Tên item", "Key", "OID", "Kiểu", "Ghi chú"],
        [
            ("System name", "router.sysname", "1.3.6.1.2.1.1.5.0", "Character", "Tên router"),
            ("CPU usage", "router.cpu", "1.3.6.1.4.1.9.9.109.1.1.1.1.5.1", "Numeric unsigned", "Đơn vị %"),
            ("RAM total", "router.ram.total", "1.3.6.1.4.1.2021.4.5.0", "Numeric unsigned", "B"),
            ("RAM available", "router.ram.avail", "1.3.6.1.4.1.2021.4.6.0", "Numeric unsigned", "B"),
            ("Load average 1m", "router.load.1m", "1.3.6.1.4.1.2021.10.1.3.1", "Numeric float", "Load 1 phút"),
            ("Gi0/0 In", "router.if.gi0.in", "1.3.6.1.2.1.31.1.1.1.6.2", "Numeric unsigned", "Store value: Delta speed per second"),
            ("Gi0/0 Out", "router.if.gi0.out", "1.3.6.1.2.1.31.1.1.1.10.2", "Numeric unsigned", "Store value: Delta speed per second"),
        ],
        widths=[Inches(1.25), Inches(1.3), Inches(2.25), Inches(1.05), Inches(1.05)],
    )
    add_image_placeholder(
        doc,
        "Hình 6. Các item SNMP của Router trong Zabbix.",
        "Chèn ảnh Latest data/Items của Router-Sim.",
    )

    heading(doc, "10. Item giám sát Switch", 1)
    add_table(
        doc,
        ["Tên item", "Key", "OID", "Kiểu", "Ghi chú"],
        [
            ("System name", "switch.sysname", "1.3.6.1.2.1.1.5.0", "Character", "Tên switch"),
            ("CPU usage", "switch.cpu", "1.3.6.1.4.1.9.9.109.1.1.1.1.5.1", "Numeric unsigned", "Đơn vị %"),
            ("RAM total", "switch.ram.total", "1.3.6.1.4.1.2021.4.5.0", "Numeric unsigned", "B"),
            ("RAM available", "switch.ram.avail", "1.3.6.1.4.1.2021.4.6.0", "Numeric unsigned", "B"),
            ("Uplink status", "switch.uplink.status", "1.3.6.1.2.1.2.3.1.2.6", "Numeric unsigned", "1 là up, khác 1 là down"),
            ("Uplink In", "switch.uplink.in", "1.3.6.1.2.1.31.1.1.1.6.6", "Numeric unsigned", "Delta speed per second"),
            ("Uplink Out", "switch.uplink.out", "1.3.6.1.2.1.31.1.1.1.10.6", "Numeric unsigned", "Delta speed per second"),
        ],
        widths=[Inches(1.25), Inches(1.3), Inches(2.25), Inches(1.05), Inches(1.05)],
    )
    add_image_placeholder(
        doc,
        "Hình 7. Các item SNMP của Switch trong Zabbix.",
        "Chèn ảnh Latest data/Items của Switch-Sim.",
    )

    heading(doc, "11. Trigger cảnh báo", 1)
    add_table(
        doc,
        ["Thiết bị", "Tên trigger", "Expression", "Severity"],
        [
            ("Firewall", "Fortinet CPU high", "last(/FortiGate-FW/fortinet.cpu)>=70", "Warning"),
            ("Firewall", "Fortinet CPU critical", "last(/FortiGate-FW/fortinet.cpu)>=90", "High"),
            ("Firewall", "Fortinet RAM high", "last(/FortiGate-FW/fortinet.ram)>=70", "Warning"),
            ("Firewall", "Fortinet disk high", "last(/FortiGate-FW/fortinet.disk)>=80", "Warning"),
            ("Firewall", "Fortinet sessions high", "last(/FortiGate-FW/fortinet.sessions)>=5000", "Average"),
            ("Router", "Router CPU high", "last(/Router-Sim/router.cpu)>=70", "Warning"),
            ("Router", "Router load high", "last(/Router-Sim/router.load.1m)>=5", "Warning"),
            ("Switch", "Switch CPU high", "last(/Switch-Sim/switch.cpu)>=70", "Warning"),
            ("Switch", "Switch uplink down", "last(/Switch-Sim/switch.uplink.status)<>1", "High"),
        ],
        widths=[Inches(1.0), Inches(1.55), Inches(3.0), Inches(0.85)],
    )
    add_image_placeholder(
        doc,
        "Hình 8. Cấu hình trigger cảnh báo CPU/RAM/Interface trong Zabbix.",
        "Chèn ảnh trigger expression hoặc danh sách trigger.",
    )

    heading(doc, "12. Cấu hình cảnh báo", 1)
    para(doc, "Trong Zabbix, cảnh báo được gửi thông qua Media type và Action.")
    for item in [
        "Web alert: hiển thị tại Monitoring -> Problems và Dashboard.",
        "Email alert: cấu hình SMTP Gmail bằng App Password.",
        "Telegram/SMS: dùng Telegram Bot hoặc SMS Gateway qua Webhook.",
        "Call: dùng Webhook đến Twilio Voice, PagerDuty hoặc Opsgenie.",
        "Audio: bật Frontend notification sound trong User settings của Zabbix.",
    ]:
        bullet(doc, item)
    add_code(
        doc,
        "Alerts -> Actions -> Trigger actions -> Create action\n"
        "Condition: Trigger severity >= Warning\n"
        "Operation: Send message to users Admin\n"
        "Send only to: Email / Telegram / Twilio Call"
    )
    add_image_placeholder(
        doc,
        "Hình 9. Action gửi cảnh báo qua Email/Telegram/Call gateway.",
        "Chèn ảnh cấu hình Trigger action hoặc Media của user Admin.",
    )

    heading(doc, "13. Dashboard và kiểm tra kết quả", 1)
    add_table(
        doc,
        ["Mục kiểm tra", "Vị trí trong Zabbix", "Kết quả đúng"],
        [
            ("Latest data", "Monitoring -> Latest data", "CPU/RAM/Traffic có giá trị cập nhật"),
            ("Problems", "Monitoring -> Problems", "Trigger xuất hiện khi vượt ngưỡng"),
            ("Graphs", "Monitoring -> Hosts -> Graphs", "Traffic counters thay đổi theo thời gian"),
            ("Action log", "Reports -> Action log", "Email/Telegram/Call gửi thành công hoặc có lỗi rõ ràng"),
            ("Dashboard", "Dashboards", "Hiển thị tổng quan Router, Switch, Firewall"),
        ],
        widths=[Inches(1.4), Inches(2.1), Inches(2.7)],
    )
    add_image_placeholder(
        doc,
        "Hình 10. Latest data hiển thị giá trị SNMP của Router, Switch, Firewall.",
        "Chèn ảnh Monitoring -> Latest data.",
    )
    add_image_placeholder(
        doc,
        "Hình 11. Problems hiển thị cảnh báo khi CPU/RAM vượt ngưỡng.",
        "Chèn ảnh Monitoring -> Problems sau khi Force High Load.",
    )
    add_image_placeholder(
        doc,
        "Hình 12. Action log xác nhận cảnh báo đã được gửi.",
        "Chèn ảnh Reports -> Action log có trạng thái gửi Email/Telegram thành công.",
    )

    heading(doc, "14. Kịch bản demo", 1)
    add_table(
        doc,
        ["Bước", "Thao tác", "Kết quả cần chứng minh"],
        [
            ("1", "Chạy SNMPSim ở port 1161.", "Dashboard báo Running 0.0.0.0:1161."),
            ("2", "Test snmpwalk từng community.", "Trả về sysName của Fortinet, Router, Switch."),
            ("3", "Tạo host và item trong Zabbix.", "Latest data có giá trị SNMP."),
            ("4", "Kéo CPU/RAM Firewall lên 90 trên dashboard SNMPSim.", "Trigger Fortinet CPU critical xuất hiện."),
            ("5", "Quan sát Problems và Email/Telegram.", "Cảnh báo gửi tới admin."),
            ("6", "Reset thiết bị về Normal.", "Problem được recovery sau chu kỳ poll."),
        ],
        widths=[Inches(0.6), Inches(2.8), Inches(2.8)],
    )

    heading(doc, "15. Đánh giá kết quả", 1)
    add_table(
        doc,
        ["Yêu cầu", "Kết quả đạt được", "Trạng thái"],
        [
            ("Giám sát Firewall", "Thu thập CPU, RAM, Disk, Sessions", "Đạt"),
            ("Giám sát Router", "Thu thập CPU, RAM, Load, Interface traffic", "Đạt"),
            ("Giám sát Switch", "Thu thập CPU, RAM, Uplink status, Traffic counters", "Đạt"),
            ("Cảnh báo", "Trigger Warning/High khi vượt ngưỡng", "Đạt"),
            ("Dashboard", "Theo dõi tập trung trên Zabbix", "Đạt"),
        ],
        widths=[Inches(1.55), Inches(3.35), Inches(1.0)],
    )

    heading(doc, "16. Nhận xét và hạn chế", 1)
    heading(doc, "16.1 Nhận xét", 2)
    para(
        doc,
        "Mô hình giám sát bằng Zabbix qua SNMP giúp quản trị viên theo dõi tập trung trạng thái Router, Switch và Firewall. "
        "Các chỉ số định lượng như CPU, RAM, disk, sessions và traffic counters hỗ trợ phát hiện sớm sự cố hiệu năng hoặc đường truyền."
    )
    heading(doc, "16.2 Hạn chế", 2)
    for item in [
        "SNMPSim là môi trường giả lập, không phản ánh đầy đủ toàn bộ hành vi thiết bị thật.",
        "Traffic counter cần cấu hình Delta speed per second để Zabbix hiển thị tốc độ thay vì chỉ số tăng dần.",
        "SMS và call thật cần dịch vụ ngoài như SMS Gateway, Twilio, PagerDuty hoặc Opsgenie.",
        "Nếu triển khai thật, nên dùng template SNMP chính thức của từng hãng thiết bị để có nhiều OID hơn.",
    ]:
        bullet(doc, item)

    heading(doc, "17. Kết luận", 1)
    para(
        doc,
        "Bài lab đã xây dựng được mô hình giám sát Router, Switch và Firewall bằng Zabbix qua SNMP. "
        "Zabbix thu thập được các chỉ số quan trọng, hiển thị trên dashboard, tạo trigger cảnh báo và gửi thông báo khi có sự cố. "
        "Mô hình phù hợp để demo quy trình giám sát mạng tập trung trước khi triển khai trên thiết bị thật."
    )

    doc.save(OUT)


if __name__ == "__main__":
    build()
    print(OUT)
