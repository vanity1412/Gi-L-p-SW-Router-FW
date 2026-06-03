import fs from "node:fs/promises";
import path from "node:path";

const SKILL_DIR = "C:/Users/vuvan/.codex/plugins/cache/openai-primary-runtime/presentations/26.601.10930/skills/presentations";
const WORKSPACE = "D:/temp/Lap03/outputs/manual-prtg-ppt/presentations/prtg-snmp-monitoring";
const OUT = "C:/Users/vuvan/OneDrive/Máy tính/Bao_cao_Lab03_PRTG_SNMP_Monitoring.pptx";

function pathToFileUrl(p) {
  return `file:///${p.replace(/\\/g, "/").replace(/^([A-Za-z]):/, "$1:")}`;
}

const { ensureArtifactToolWorkspace, importArtifactTool, createSlideContext, saveBlobToFile } =
  await import(pathToFileUrl(`${SKILL_DIR}/scripts/artifact_tool_utils.mjs`));

const slideSize = { width: 1280, height: 720 };
await ensureArtifactToolWorkspace(WORKSPACE);
const artifact = await importArtifactTool(WORKSPACE);
const { Presentation, PresentationFile } = artifact;
const presentation = Presentation.create({ slideSize });
const ctx = createSlideContext(artifact, {
  slideSize,
  workspaceDir: WORKSPACE,
  outputDir: path.dirname(OUT),
  titleFont: "Aptos Display",
  bodyFont: "Aptos",
});

const C = {
  paper: "#F7FAFC",
  ink: "#0B1220",
  muted: "#64748B",
  line: "#D7DEE8",
  card: "#FFFFFF",
  prtg: "#00A9E0",
  green: "#8CC63F",
  blue: "#2563EB",
  cyan: "#06B6D4",
  amber: "#F59E0B",
  red: "#E11D48",
  purple: "#7C3AED",
  dark: "#101827",
  dark2: "#172033",
};

function addText(slide, text, left, top, width, height, opts = {}) {
  return ctx.addText(slide, {
    text,
    left,
    top,
    width,
    height,
    fontSize: opts.fontSize ?? 15,
    bold: opts.bold ?? false,
    color: opts.color ?? C.ink,
    typeface: opts.typeface ?? ctx.fonts.body,
    align: opts.align,
    valign: opts.valign,
    insets: opts.insets ?? { left: 0, right: 0, top: 0, bottom: 0 },
  });
}

function rect(slide, left, top, width, height, fill, line = "#00000000", lineWidth = 0, extra = {}) {
  return ctx.addShape(slide, {
    left,
    top,
    width,
    height,
    fill,
    line: ctx.line(line, lineWidth),
    ...extra,
  });
}

function base(kicker, title, subtitle = "", opts = {}) {
  const dark = opts.dark ?? false;
  const slide = presentation.slides.add();
  rect(slide, 0, 0, 1280, 720, dark ? C.dark : C.paper);
  rect(slide, 0, 0, 1280, 18, dark ? C.prtg : C.green);
  addText(slide, kicker.toUpperCase(), 60, 42, 270, 22, {
    fontSize: 12,
    bold: true,
    color: dark ? "#7DD3FC" : C.prtg,
  });
  addText(slide, title, 60, 78, 790, subtitle ? 86 : 108, {
    fontSize: 34,
    bold: true,
    color: dark ? "#F8FAFC" : C.ink,
    typeface: ctx.fonts.title,
  });
  if (subtitle) {
    addText(slide, subtitle, 60, 165, 820, 44, {
      fontSize: 16,
      color: dark ? "#CBD5E1" : C.muted,
    });
  }
  addText(slide, "Lab 03 | PRTG Network Monitor | SNMP/SNMPSim", 60, 681, 430, 18, {
    fontSize: 10,
    color: dark ? "#94A3B8" : C.muted,
  });
  const page = String(presentation.slides.count).padStart(2, "0");
  addText(slide, page, 1180, 678, 40, 20, { fontSize: 11, color: dark ? "#94A3B8" : C.muted, align: "right" });
  return slide;
}

function card(slide, x, y, w, h, title, body, color = C.prtg) {
  rect(slide, x, y, w, h, C.card, C.line, 1);
  rect(slide, x, y, 6, h, color);
  addText(slide, title, x + 18, y + 15, w - 34, 24, { fontSize: 17, bold: true });
  addText(slide, body, x + 18, y + 47, w - 34, h - 56, { fontSize: 12.5, color: C.muted });
}

function metric(slide, x, y, label, value, color) {
  rect(slide, x, y, 154, 88, "#0F172A", "#243244", 1);
  rect(slide, x, y, 154, 5, color);
  addText(slide, value, x + 16, y + 18, 122, 34, { fontSize: 27, bold: true, color: "#FFFFFF" });
  addText(slide, label, x + 16, y + 56, 122, 20, { fontSize: 11, color: "#CBD5E1" });
}

function pill(slide, x, y, w, text, color, textColor = "#FFFFFF") {
  rect(slide, x, y, w, 28, color, "#00000000", 0);
  addText(slide, text, x + 8, y + 6, w - 16, 16, { fontSize: 11, bold: true, color: textColor, align: "center" });
}

function row(slide, x, y, w, h, cells, widths, opts = {}) {
  const fill = opts.fill ?? "#FFFFFF";
  rect(slide, x, y, w, h, fill, C.line, 1);
  let cur = x;
  cells.forEach((cell, i) => {
    if (i > 0) rect(slide, cur, y, 1, h, C.line);
    addText(slide, cell, cur + 10, y + 8, widths[i] - 20, h - 12, {
      fontSize: opts.fontSize ?? 11.5,
      bold: opts.bold ?? false,
      color: opts.color ?? C.ink,
      typeface: opts.mono ? ctx.fonts.mono : ctx.fonts.body,
    });
    cur += widths[i];
  });
}

function table(slide, x, y, widths, headers, data, opts = {}) {
  const h = opts.rowH ?? 40;
  const w = widths.reduce((a, b) => a + b, 0);
  row(slide, x, y, w, h, headers, widths, { fill: opts.headerFill ?? "#EAF6FB", bold: true, fontSize: opts.fontSize ?? 11.5, color: C.ink });
  data.forEach((r, i) => {
    row(slide, x, y + h * (i + 1), w, h, r, widths, {
      fill: i % 2 ? "#FFFFFF" : "#F8FBFD",
      fontSize: opts.fontSize ?? 11.2,
      mono: opts.monoCols?.includes(i),
    });
  });
}

function screenshotBox(slide, x, y, w, h, label, note = "") {
  rect(slide, x, y, w, h, "#FFFFFF", "#A8B3C2", 1);
  rect(slide, x + 12, y + 12, w - 24, h - 24, "#F3F7FA", "#CBD5E1", 1);
  addText(slide, "[CHÈN ẢNH MINH CHỨNG]", x + 20, y + h / 2 - 24, w - 40, 22, {
    fontSize: 15,
    bold: true,
    color: C.muted,
    align: "center",
  });
  addText(slide, label, x + 20, y + h / 2 + 4, w - 40, 20, {
    fontSize: 11,
    color: C.prtg,
    bold: true,
    align: "center",
  });
  if (note) addText(slide, note, x + 18, y + h - 38, w - 36, 18, { fontSize: 10, color: C.muted, align: "center" });
}

function arrow(slide, x1, y1, x2, y2, color = C.muted) {
  const dx = x2 - x1;
  const dy = y2 - y1;
  const len = Math.max(1, Math.sqrt(dx * dx + dy * dy));
  const angle = Math.atan2(dy, dx);
  const line = rect(slide, (x1 + x2) / 2 - len / 2, (y1 + y2) / 2 - 1, len, 2, color);
  line.rotation = (angle * 180) / Math.PI;
  rect(slide, x2 - 8, y2 - 7, 14, 14, color, "#00000000", 0, { geometry: "triangle" });
}

function deviceNode(slide, x, y, title, role, color, community) {
  rect(slide, x, y, 220, 92, "#FFFFFF", color, 2);
  rect(slide, x + 16, y + 20, 34, 34, color, "#00000000", 0);
  addText(slide, title, x + 62, y + 15, 140, 22, { fontSize: 17, bold: true });
  addText(slide, role, x + 62, y + 39, 140, 17, { fontSize: 10.5, color: C.muted });
  addText(slide, `community: ${community}`, x + 16, y + 65, 190, 16, { fontSize: 10.5, color });
}

function step(slide, x, y, n, title, body, color) {
  rect(slide, x, y, 64, 64, color, "#00000000", 0, { geometry: "ellipse" });
  addText(slide, String(n), x + 20, y + 13, 24, 28, { fontSize: 25, bold: true, color: "#FFFFFF", align: "center" });
  addText(slide, title, x + 82, y + 2, 245, 24, { fontSize: 17, bold: true });
  addText(slide, body, x + 82, y + 31, 270, 42, { fontSize: 12.2, color: C.muted });
}

function triggerRow(slide, x, y, metricName, warning, error, notification, color) {
  rect(slide, x, y, 1050, 52, "#FFFFFF", C.line, 1);
  rect(slide, x, y, 7, 52, color);
  addText(slide, metricName, x + 18, y + 15, 220, 18, { fontSize: 14, bold: true });
  pill(slide, x + 275, y + 12, 160, warning, C.amber);
  pill(slide, x + 465, y + 12, 160, error, C.red);
  addText(slide, notification, x + 660, y + 14, 350, 20, { fontSize: 12.5, color: C.muted });
}

// Slide 1
{
  const slide = presentation.slides.add();
  rect(slide, 0, 0, 1280, 720, C.dark);
  rect(slide, 0, 0, 1280, 18, C.green);
  rect(slide, 815, 0, 465, 720, "#0B1220");
  rect(slide, 855, 92, 310, 72, C.prtg);
  addText(slide, "PRTG NETWORK MONITOR", 880, 114, 260, 25, { fontSize: 18, bold: true, color: "#FFFFFF", align: "center" });
  rect(slide, 870, 235, 246, 246, "#172033", "#2D3B52", 1, { geometry: "ellipse" });
  rect(slide, 930, 295, 126, 126, C.green, "#00000000", 0, { geometry: "ellipse" });
  addText(slide, "SNMP", 956, 337, 78, 28, { fontSize: 21, bold: true, color: "#FFFFFF", align: "center" });
  arrow(slide, 810, 358, 890, 358, "#7DD3FC");
  arrow(slide, 1115, 358, 1190, 358, "#FBBF24");
  addText(slide, "LAB 03", 72, 84, 160, 24, { fontSize: 16, bold: true, color: "#7DD3FC" });
  addText(slide, "Giám sát Router, Switch, Firewall và Server bằng PRTG", 72, 132, 680, 155, {
    fontSize: 44,
    bold: true,
    color: "#F8FAFC",
    typeface: ctx.fonts.title,
  });
  addText(slide, "Từ SNMPSim đến PRTG Sensor, limit cảnh báo, SMTP Gmail và kịch bản demo sự cố CPU/RAM.", 76, 315, 645, 62, {
    fontSize: 19,
    color: "#CBD5E1",
  });
  metric(slide, 76, 450, "Thiết bị", "4", "#7DD3FC");
  metric(slide, 250, 450, "Nhóm metric", "6", "#86EFAC");
  metric(slide, 424, 450, "Alert path", "Web+", "#FBBF24");
  metric(slide, 598, 450, "Demo", "Force", "#FB7185");
  addText(slide, "Windows Host | PRTG web app | SNMPSim UDP 161 | Gmail notification", 76, 635, 660, 22, { fontSize: 13, color: "#94A3B8" });
}

// Slide 2
{
  const slide = base("Mục tiêu", "Lab chứng minh quy trình giám sát tập trung bằng PRTG.", "Điểm quan trọng không chỉ là add device, mà là biết PRTG đang giám sát gì và cảnh báo khi nào.");
  card(slide, 70, 258, 330, 135, "Nguồn dữ liệu", "SNMPSim đọc các file .snmprec để giả lập Firewall, Router, Switch và Server qua SNMPv2c.", C.cyan);
  card(slide, 475, 258, 330, 135, "Thu thập", "PRTG tạo Device và SNMP Custom Sensor, poll OID định kỳ qua UDP port 161.", C.prtg);
  card(slide, 880, 258, 330, 135, "Cảnh báo", "Channel limit đổi trạng thái sensor; Notification Trigger gửi email khi Warning/Down.", C.amber);
  arrow(slide, 405, 326, 467, 326, C.prtg);
  arrow(slide, 810, 326, 872, 326, C.prtg);
  addText(slide, "Kết quả cần trình bày khi bảo vệ", 82, 475, 370, 24, { fontSize: 19, bold: true });
  const proof = [
    ["PRTG đọc được OID", "Sensor có Last Value, trạng thái Up."],
    ["Giả lập sự cố", "Force High Load làm CPU/RAM tăng."],
    ["Sensor đổi màu", "Warning hoặc Down/Error theo limit."],
    ["Có thông báo", "Email nhận được từ PRTG qua SMTP Gmail."],
  ];
  proof.forEach((p, i) => {
    const x = 90 + i * 286;
    rect(slide, x, 530, 42, 42, [C.cyan, C.blue, C.amber, C.green][i], "#00000000", 0, { geometry: "ellipse" });
    addText(slide, String(i + 1), x + 14, 538, 14, 20, { fontSize: 16, bold: true, color: "#FFFFFF", align: "center" });
    addText(slide, p[0], x + 56, 523, 205, 22, { fontSize: 14.5, bold: true });
    addText(slide, p[1], x + 56, 550, 215, 34, { fontSize: 11.5, color: C.muted });
  });
}

// Slide 3
{
  const slide = base("Kiến trúc", "PRTG và SNMPSim cùng chạy trên Windows, device dùng localhost.", "Mỗi thiết bị được phân biệt bằng community string riêng, dù cùng IP 127.0.0.1.");
  deviceNode(slide, 72, 252, "FortiGate-FW", "Firewall security edge", C.red, "fortinet");
  deviceNode(slide, 72, 374, "Router-Sim", "L3 forwarding", C.blue, "router");
  deviceNode(slide, 72, 496, "Switch-Sim", "Core/uplink access", C.green, "switch");
  deviceNode(slide, 72, 618, "Ubuntu-Sim", "Server workload", C.purple, "ubuntu");
  rect(slide, 510, 370, 240, 120, "#0F172A", "#203044", 1);
  addText(slide, "SNMPSim responder", 535, 395, 190, 26, { fontSize: 20, bold: true, color: "#F8FAFC" });
  addText(slide, "UDP 0.0.0.0:161\nData từ *.snmprec\nTrả lời SNMPv2c", 535, 432, 170, 45, { fontSize: 12.5, color: "#CBD5E1" });
  rect(slide, 950, 370, 240, 120, "#FFFFFF", C.prtg, 2);
  addText(slide, "PRTG Core/Probe", 975, 395, 190, 26, { fontSize: 20, bold: true, color: C.ink });
  addText(slide, "Device tree\nSNMP Custom Sensor\nChannel limit + trigger", 975, 432, 180, 45, { fontSize: 12.5, color: C.muted });
  [298, 420, 542, 664].forEach((y) => arrow(slide, 294, y, 505, 430, C.cyan));
  arrow(slide, 755, 430, 945, 430, C.amber);
  addText(slide, "Polling interval đề xuất: 60 giây để demo dễ quan sát.", 530, 536, 610, 22, { fontSize: 14, bold: true, color: C.ink });
  screenshotBox(slide, 800, 570, 330, 82, "Ảnh PRTG Root/Local Probe hoặc dashboard SNMPSim Running");
}

// Slide 4
{
  const slide = base("Thông số lab", "Một bảng cấu hình thống nhất giúp tránh lỗi SNMP error # -2003.", "Trong PRTG, port và community ở device hoặc parent phải khớp đúng với SNMPSim.");
  table(slide, 72, 240, [150, 190, 150, 155, 420], ["Thiết bị", "Device PRTG", "IP/Port", "Community", "Mục tiêu giám sát"], [
    ["Firewall", "FortiGate-FW", "127.0.0.1:161", "fortinet", "CPU, RAM, Disk, Sessions"],
    ["Router", "Router-Sim", "127.0.0.1:161", "router", "CPU, Load, RAM, Interface traffic"],
    ["Switch", "Switch-Sim", "127.0.0.1:161", "switch", "CPU, Uplink status, Traffic counters"],
    ["Server", "Ubuntu-Sim", "127.0.0.1:161", "ubuntu", "CPU, RAM, Load average, Network"],
  ], { rowH: 48, fontSize: 11.5 });
  card(slide, 86, 515, 340, 95, "Trước khi add sensor", "Kiểm tra port bằng netstat và xác nhận PID thuộc python.exe hoặc snmpsim-command-responder.", C.blue);
  card(slide, 470, 515, 340, 95, "Nếu đổi port", "Nếu SNMPSim chạy 1161 thì mọi Device trong PRTG cũng phải dùng SNMP Port 1161.", C.amber);
  card(slide, 854, 515, 340, 95, "Không dùng public", "Community default public thường làm sensor No response nếu parent đang inherit sai.", C.red);
}

// Slide 5
{
  const slide = base("Quy trình triển khai", "Từ Add Device đến sensor có dữ liệu là một chuỗi 6 bước.", "Cứ đi đúng thứ tự này thì dễ biết lỗi nằm ở SNMPSim, credential hay sensor OID.");
  step(slide, 78, 252, 1, "Chạy SNMPSim", "Start responder, kiểm tra Running UDP 161 trên dashboard.", C.cyan);
  step(slide, 78, 382, 2, "Kiểm tra port", "netstat -ano -p udp | findstr :161 để xác nhận process.", C.blue);
  step(slide, 78, 512, 3, "Add Device", "Trong Local Probe, tạo FortiGate/Router/Switch/Ubuntu.", C.prtg);
  step(slide, 610, 252, 4, "SNMP credential", "SNMPv2c, port 161, community đúng từng thiết bị.", C.green);
  step(slide, 610, 382, 5, "Add Sensor", "Chọn SNMP Custom Sensor và nhập đúng OID.", C.amber);
  step(slide, 610, 512, 6, "Limit + Trigger", "Bật channel limit và Notification Trigger gửi email.", C.red);
  [316, 446].forEach((y) => arrow(slide, 415, y, 560, y, C.line));
}

// Slide 6
{
  const slide = base("Giám sát cái gì", "Các metric được chọn theo vai trò từng loại thiết bị.", "Firewall ưu tiên sessions; Router/Switch ưu tiên traffic và uplink; Server ưu tiên CPU/RAM/load.");
  table(slide, 70, 235, [170, 175, 175, 175, 175, 175], ["Metric", "Firewall", "Router", "Switch", "Server", "Khi cảnh báo"], [
    ["CPU", "Có", "Có", "Có", "Có", ">=70 Warning, >=90 Error"],
    ["RAM", "Có", "Có", "Có", "Có", ">=70 Warning, >=90 Error"],
    ["Disk", "Có", "-", "-", "Tuỳ mở rộng", ">=80 Warning, >=90 Error"],
    ["Sessions", "Có", "-", "-", "-", ">=5000 Warning, >=10000 Error"],
    ["Load average", "-", "Có", "-", "Có", ">=5 Warning, >=10 Error"],
    ["Traffic counters", "-", "Gi0/0 In/Out", "Uplink In/Out", "Network", "Tăng bất thường hoặc mất dữ liệu"],
    ["Uplink status", "-", "-", "Có", "-", "Khác 1 là Down/Error"],
  ], { rowH: 42, fontSize: 10.8 });
}

// Slide 7
{
  const slide = base("Firewall sensors", "FortiGate-FW cần sensor cho tải hệ thống và session table.", "Các sensor này đủ để demo lỗi quá tải Firewall khi ép CPU/RAM hoặc tăng sessions.");
  table(slide, 70, 230, [190, 390, 175, 245], ["Sensor", "OID", "Value type", "Cảnh báo đề xuất"], [
    ["Fortinet CPU", "1.3.6.1.4.1.12356.101.4.1.3.0", "Absolute / %", "70 Warning, 90 Error"],
    ["Fortinet RAM", "1.3.6.1.4.1.12356.101.4.1.4.0", "Absolute / %", "70 Warning, 90 Error"],
    ["Fortinet Disk", "1.3.6.1.4.1.12356.101.4.1.6.0", "Absolute / %", "80 Warning, 90 Error"],
    ["Fortinet Sessions", "1.3.6.1.4.1.12356.101.4.1.8.0", "Absolute / Count", "5000 Warning, 10000 Error"],
  ], { rowH: 54, fontSize: 10.6 });
  screenshotBox(slide, 825, 500, 310, 105, "Ảnh SNMP Custom Sensor Fortinet CPU", "OID Settings + Primary Channel");
  card(slide, 78, 505, 330, 100, "Ý nghĩa bảo mật", "Session tăng đột biến có thể liên quan scan, brute force, DDoS nhỏ hoặc cấu hình NAT bất thường.", C.red);
  card(slide, 450, 505, 330, 100, "Ý nghĩa vận hành", "CPU/RAM/Disk cao làm Firewall xử lý chậm, mất packet hoặc trễ VPN.", C.amber);
}

// Slide 8
{
  const slide = base("Router sensors", "Router-Sim tập trung vào CPU, load và lưu lượng interface.", "Với counter dạng octets, PRTG cần hiểu đây là dữ liệu tăng dần theo thời gian.");
  table(slide, 70, 230, [210, 450, 190, 165], ["Sensor", "OID", "Unit/Ghi chú", "Cảnh báo"], [
    ["Router CPU", "1.3.6.1.4.1.9.9.109.1.1.1.1.5.1", "%", "70/90"],
    ["Router Load 1m", "1.3.6.1.4.1.2021.10.1.3.1", "Count", "5/10"],
    ["Router RAM Total", "1.3.6.1.4.1.2021.4.5.0", "Bytes", "Theo RAM used"],
    ["Router RAM Available", "1.3.6.1.4.1.2021.4.6.0", "Bytes", "Low available"],
    ["Router Gi0/0 In", "1.3.6.1.2.1.31.1.1.1.6.2", "Counter/Bytes", "Traffic spike"],
    ["Router Gi0/0 Out", "1.3.6.1.2.1.31.1.1.1.10.2", "Counter/Bytes", "Traffic spike"],
  ], { rowH: 42, fontSize: 10.2 });
  addText(slide, "Ghi chú demo: nếu dùng SNMP Custom Advanced Sensor, đặt Counter mode hoặc channel tính delta/s để traffic có ý nghĩa theo tốc độ.", 88, 604, 1050, 34, {
    fontSize: 14,
    color: C.ink,
    bold: true,
  });
}

// Slide 9
{
  const slide = base("Switch & Server sensors", "Switch giám sát uplink, Server giám sát tài nguyên hệ thống.", "Hai nhóm này bổ sung bức tranh mạng: đường truyền còn sống không và workload server có quá tải không.");
  table(slide, 70, 240, [190, 395, 200, 190], ["Switch sensor", "OID", "Ghi chú", "Cảnh báo"], [
    ["Switch CPU", "1.3.6.1.4.1.9.9.109.1.1.1.1.5.1", "%", "70/90"],
    ["Uplink Status", "1.3.6.1.2.1.2.3.1.2.6", "1 là up", "Khác 1: Error"],
    ["Uplink In", "1.3.6.1.2.1.31.1.1.1.6.6", "Counter/Bytes", "Traffic spike"],
    ["Uplink Out", "1.3.6.1.2.1.31.1.1.1.10.6", "Counter/Bytes", "Traffic spike"],
  ], { rowH: 42, fontSize: 10.2 });
  table(slide, 70, 462, [190, 395, 200, 190], ["Server sensor", "OID", "Ghi chú", "Cảnh báo"], [
    ["Ubuntu CPU", "1.3.6.1.4.1.2021.11.9.0", "%", "70/90"],
    ["RAM Total", "1.3.6.1.4.1.2021.4.5.0", "Bytes", "Tính Used"],
    ["RAM Available", "1.3.6.1.4.1.2021.4.6.0", "Bytes", "Low memory"],
    ["Load 1m", "1.3.6.1.4.1.2021.10.1.3.1", "Count", "5/10"],
  ], { rowH: 36, fontSize: 10.2, headerFill: "#F0FDF4" });
}

// Slide 10
{
  const slide = base("Tạo sensor trong PRTG", "SNMP Custom Sensor là cách nhanh nhất để đọc đúng OID lab.", "Mỗi OID có thể tạo một sensor riêng để dễ đặt limit và nhìn trạng thái.");
  screenshotBox(slide, 70, 235, 420, 260, "Ảnh Add Sensor > SNMP Custom Sensor");
  card(slide, 540, 238, 290, 115, "Basic Sensor Settings", "Đặt tên sensor rõ ràng: Fortinet CPU, Router Load 1m, Switch Uplink In...", C.prtg);
  card(slide, 865, 238, 290, 115, "OID Settings", "Nhập OID, Value Type là Absolute unsigned integer cho CPU/RAM/Disk.", C.blue);
  card(slide, 540, 390, 290, 115, "Sensor Display", "Primary Channel đặt tên theo metric: CPU Usage, RAM Usage, Sessions.", C.green);
  card(slide, 865, 390, 290, 115, "Scanning Interval", "Dùng 60 giây cho demo, hoặc 30 giây nếu muốn thấy cảnh báo nhanh hơn.", C.amber);
  addText(slide, "Mẹo tránh lỗi: trước khi tạo hàng loạt sensor, test một OID sysName hoặc CPU để xác nhận community và port đã đúng.", 90, 570, 1010, 34, {
    fontSize: 15,
    bold: true,
    color: C.ink,
  });
}

// Slide 11
{
  const slide = base("Channel limit", "Limit quyết định sensor chuyển Warning hay Down/Error.", "Trong PRTG, limit nằm trong Edit Channel, không nằm ở màn hình Settings chung của sensor.");
  screenshotBox(slide, 72, 236, 410, 270, "Ảnh Edit Channel CPU Usage", "Enable alerting based on limits");
  triggerRow(slide, 520, 240, "CPU Usage", "Warning >= 70%", "Error >= 90%", "Dùng cho Firewall/Router/Switch/Server", C.prtg);
  triggerRow(slide, 520, 305, "RAM Usage", "Warning >= 70%", "Error >= 90%", "Thiếu bộ nhớ hoặc leak memory", C.blue);
  triggerRow(slide, 520, 370, "Disk Usage", "Warning >= 80%", "Error >= 90%", "Disk gần đầy, giảm khả năng ghi log", C.amber);
  triggerRow(slide, 520, 435, "Sessions", "Warning >= 5000", "Error >= 10000", "Firewall session table tăng bất thường", C.red);
  triggerRow(slide, 520, 500, "Load average", "Warning >= 5", "Error >= 10", "Server/Router quá tải xử lý", C.purple);
  addText(slide, "Limit chỉ đổi trạng thái sensor. Muốn gửi email thì phải cấu hình Notification Trigger ở sensor/device/group.", 86, 585, 1030, 26, {
    fontSize: 14,
    bold: true,
    color: C.red,
  });
}

// Slide 12
{
  const slide = base("Notification delivery", "Email cảnh báo dùng SMTP Gmail, SMS/Call cần gateway ngoài.", "PRTG có email/push tốt; SMS và gọi điện thường triển khai qua nhà cung cấp bên ngoài.");
  table(slide, 70, 232, [230, 300, 450], ["Kênh cảnh báo", "Cấu hình trong PRTG", "Ghi chú demo"], [
    ["Web/Alarm", "Sensor Warning/Down hiển thị trong Alarms", "Luôn có, không cần SMTP"],
    ["Email Gmail", "Setup > Notification Delivery > SMTP relay", "smtp.gmail.com, port 587, App Password"],
    ["SMS", "SMS Delivery hoặc HTTP Notification", "Cần SMS gateway/API; Telegram có thể thay trong demo"],
    ["Call", "Execute HTTP Action/Webhook", "Twilio Voice, PagerDuty, Opsgenie hoặc on-call tool"],
    ["Audio", "Trình duyệt/desktop notification", "Dùng trang alarm mở sẵn hoặc công cụ ngoài phát âm thanh"],
  ], { rowH: 54, fontSize: 11 });
  card(slide, 88, 560, 480, 80, "Bảo mật", "Không đưa Gmail App Password thật vào báo cáo nộp chính thức; chỉ ghi 'App Password' hoặc che bớt ký tự.", C.red);
  card(slide, 635, 560, 480, 80, "Kiểm tra", "Sau khi cấu hình SMTP, bấm Test SMTP Settings và kiểm tra email nhận ở thongvv.sec@gmail.com.", C.green);
}

// Slide 13
{
  const slide = base("Notification Trigger", "Trigger là phần làm email thật sự được gửi.", "Nếu chỉ bật channel limit mà không có trigger, sensor đổi màu nhưng hộp thư có thể không nhận gì.");
  screenshotBox(slide, 72, 235, 420, 260, "Ảnh Notification Triggers trong PRTG");
  card(slide, 545, 240, 540, 82, "Warning trigger", "When sensor state is Warning for at least 0 seconds, perform Gmail Alert.", C.amber);
  card(slide, 545, 344, 540, 82, "Down/Error trigger", "When sensor state is Down for at least 0 seconds, perform Gmail Alert.", C.red);
  card(slide, 545, 448, 540, 82, "Recovery trigger", "When sensor state is no longer Down, perform Gmail Recovery Notification.", C.green);
  addText(slide, "Trong demo nên để 0-30 giây. Trigger mặc định inherited thường chờ 600 giây nên dễ tưởng PRTG không gửi cảnh báo.", 90, 570, 1040, 38, {
    fontSize: 15,
    bold: true,
    color: C.ink,
  });
}

// Slide 14
{
  const slide = base("Kịch bản demo", "Force High Load tạo sự cố, PRTG poll rồi gửi cảnh báo.", "Đây là đoạn nên trình bày live trong buổi bảo vệ lab.");
  const items = [
    ["1", "Mở SNMPSim Dashboard", "Xác nhận responder Running 0.0.0.0:161."],
    ["2", "Mở PRTG Device", "Chọn FortiGate-FW và sensor CPU/RAM."],
    ["3", "Force High Load", "Kéo CPU/RAM lên 100 trên dashboard SNMPSim."],
    ["4", "Chờ scan interval", "Sau 60 giây sensor chuyển Warning/Down."],
    ["5", "Kiểm tra email", "Gmail nhận cảnh báo từ PRTG."],
    ["6", "Reset to Normal", "Sensor phục hồi sau vài chu kỳ scan."],
  ];
  items.forEach((it, i) => {
    const x = i < 3 ? 86 : 680;
    const y = 238 + (i % 3) * 125;
    rect(slide, x, y, 46, 46, [C.cyan, C.prtg, C.amber, C.red, C.green, C.blue][i], "#00000000", 0, { geometry: "ellipse" });
    addText(slide, it[0], x + 16, y + 10, 14, 20, { fontSize: 16, bold: true, color: "#FFFFFF", align: "center" });
    addText(slide, it[1], x + 65, y + 2, 360, 24, { fontSize: 17, bold: true });
    addText(slide, it[2], x + 65, y + 31, 405, 38, { fontSize: 12.5, color: C.muted });
  });
  screenshotBox(slide, 445, 555, 390, 80, "Ảnh sensor vàng/đỏ và email cảnh báo");
}

// Slide 15
{
  const slide = base("Bằng chứng cần chụp", "Các ảnh minh chứng giúp báo cáo và slide thuyết phục hơn.", "Bạn có thể thay trực tiếp các khung dưới đây bằng ảnh từ PRTG/CMD/Gmail.");
  screenshotBox(slide, 70, 235, 330, 130, "1. PRTG Root/Local Probe", "Có device FortiGate/Router/Switch/Ubuntu");
  screenshotBox(slide, 475, 235, 330, 130, "2. Add Device/Credential", "IP 127.0.0.1, SNMPv2c, community");
  screenshotBox(slide, 880, 235, 330, 130, "3. SNMP Custom Sensor", "OID Fortinet CPU hoặc Router Load");
  screenshotBox(slide, 70, 455, 330, 130, "4. Channel Limit", "Warning/Error đã điền");
  screenshotBox(slide, 475, 455, 330, 130, "5. Sensor Warning/Down", "Sau Force High Load");
  screenshotBox(slide, 880, 455, 330, 130, "6. Email Alert", "Gmail nhận cảnh báo PRTG");
}

// Slide 16
{
  const slide = base("Lỗi thường gặp", "Hầu hết lỗi PRTG SNMP nằm ở port, community hoặc OID.", "Bảng này dùng để trả lời nhanh khi demo gặp lỗi.");
  table(slide, 62, 228, [250, 420, 455], ["Lỗi", "Nguyên nhân thường gặp", "Cách xử lý"], [
    ["SNMP error # -2003 No response", "Sai port, sai community, SNMPSim chưa chạy hoặc firewall chặn UDP", "Kiểm tra netstat, SNMPv2c, port 161/1161 và community"],
    ["Sensor No data", "OID không có trong file .snmprec hoặc sensor chưa poll thành công", "Test OID sysName trước, sau đó test từng OID metric"],
    ["Không gửi email", "SMTP chưa đúng hoặc chưa có Notification Trigger", "Test SMTP Settings, thêm State Trigger 0-30 giây"],
    ["Force High Load lỗi", "File .snmprec bị khóa khi PRTG/SNMPSim đang đọc", "Restart app sau bản code retry/fallback, thử lại"],
    ["Không thấy Limit", "Đang ở Settings sensor, chưa vào Edit Channel", "Overview > bánh răng của channel > Enable limits"],
  ], { rowH: 62, fontSize: 10.8, headerFill: "#FEF2F2" });
}

// Slide 17
{
  const slide = base("Đánh giá kết quả", "Lab đáp ứng đủ yêu cầu giám sát thiết bị và cảnh báo.", "PRTG đã đóng vai trò công cụ giám sát tập trung; SNMPSim đóng vai trò thiết bị SNMP giả lập.");
  const results = [
    ["Firewall", "CPU, RAM, Disk, Sessions", "Đạt", C.red],
    ["Router", "CPU, RAM, Load, Interface counters", "Đạt", C.blue],
    ["Switch", "CPU, Uplink status, Traffic counters", "Đạt", C.green],
    ["Server", "CPU, RAM, Load average", "Đạt", C.purple],
    ["Alert", "Channel limit + Notification Trigger + Gmail", "Đạt", C.amber],
  ];
  results.forEach((r, i) => {
    const y = 240 + i * 72;
    rect(slide, 100, y, 40, 40, r[3], "#00000000", 0, { geometry: "ellipse" });
    addText(slide, "✓", 111, y + 5, 18, 22, { fontSize: 20, bold: true, color: "#FFFFFF", align: "center" });
    addText(slide, r[0], 170, y + 2, 160, 24, { fontSize: 18, bold: true });
    addText(slide, r[1], 360, y + 5, 520, 22, { fontSize: 14, color: C.muted });
    pill(slide, 940, y + 6, 92, r[2], C.green);
  });
  card(slide, 150, 620, 880, 54, "Kết luận ngắn", "Mô hình phù hợp để demo quy trình giám sát mạng trước khi triển khai template SNMP trên thiết bị thật.", C.prtg);
}

// Slide 18
{
  const slide = base("Kết luận", "PRTG hoàn thành chuỗi: thu thập metric, phân loại trạng thái, gửi cảnh báo.", "Điểm cần nói khi bảo vệ: lab không chỉ giả lập thiết bị, mà mô phỏng được quy trình vận hành giám sát thực tế.", { dark: true });
  card(slide, 85, 255, 315, 125, "Đã làm được", "Add device, cấu hình SNMP community, tạo sensor OID, đặt limit và gửi email alert.", C.green);
  card(slide, 480, 255, 315, 125, "Hạn chế", "SNMPSim là môi trường lab; SMS/call thật cần gateway hoặc dịch vụ ngoài.", C.amber);
  card(slide, 875, 255, 315, 125, "Hướng phát triển", "Dùng device thật, template sensor, map PRTG và tích hợp SIEM/log syslog.", C.prtg);
  addText(slide, "Thông điệp cuối: biết rõ giám sát chỉ số nào, đặt ngưỡng nào, nhận cảnh báo qua kênh nào.", 122, 485, 1030, 52, {
    fontSize: 24,
    bold: true,
    color: "#F8FAFC",
    align: "center",
  });
  addText(slide, "PRTG + SNMP + Notification Trigger = hệ thống giám sát tập trung có thể demo end-to-end.", 190, 558, 900, 32, {
    fontSize: 17,
    color: "#CBD5E1",
    align: "center",
  });
}

await fs.mkdir(path.dirname(OUT), { recursive: true });
const pptx = await PresentationFile.exportPptx(presentation);
await pptx.save(OUT);

const localCopy = "D:/temp/Lap03/Bao_cao_Lab03_PRTG_SNMP_Monitoring.pptx";
await fs.copyFile(OUT, localCopy);

const previewDir = `${WORKSPACE}/preview`;
await fs.mkdir(previewDir, { recursive: true });
for (let i = 0; i < presentation.slides.count; i += 1) {
  const slide = presentation.slides.getItem(i);
  const png = await presentation.export({ slide, format: "png", scale: 1 });
  await saveBlobToFile(png, `${previewDir}/slide-${String(i + 1).padStart(2, "0")}.png`);
}

console.log(OUT);
