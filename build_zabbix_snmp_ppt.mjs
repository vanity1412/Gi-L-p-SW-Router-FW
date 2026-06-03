import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const SKILL_DIR = "C:/Users/vuvan/.codex/plugins/cache/openai-primary-runtime/presentations/26.601.10930/skills/presentations";
const WORKSPACE = "D:/temp/Lap03/outputs/manual-snmp-ppt/presentations/zabbix-snmp";
const OUT = "D:/temp/Lap03/Bao_cao_Lab03_Zabbix_SNMP_Router_Switch_Firewall.pptx";
const ASSETS = "D:/temp/Lap03/ppt_assets";

const { ensureArtifactToolWorkspace, importArtifactTool, createSlideContext, saveBlobToFile } =
  await import(pathToFileUrl(`${SKILL_DIR}/scripts/artifact_tool_utils.mjs`));

function pathToFileUrl(p) {
  return `file:///${p.replace(/\\/g, "/").replace(/^([A-Za-z]):/, "$1:")}`;
}

const slideSize = { width: 1280, height: 720 };
await ensureArtifactToolWorkspace(WORKSPACE);
const artifact = await importArtifactTool(WORKSPACE);
const { Presentation, PresentationFile } = artifact;
const presentation = Presentation.create({ slideSize });
const ctx = createSlideContext(artifact, {
  slideSize,
  workspaceDir: WORKSPACE,
  assetDir: ASSETS,
  outputDir: path.dirname(OUT),
  titleFont: "Aptos Display",
  bodyFont: "Aptos",
});

const C = {
  ink: "#0B1220",
  paper: "#F7FAFC",
  card: "#FFFFFF",
  muted: "#64748B",
  blue: "#2563EB",
  cyan: "#06B6D4",
  green: "#10B981",
  amber: "#F59E0B",
  red: "#EF4444",
  navy: "#111827",
  line: "#CBD5E1",
  deep: "#07111F",
};

function slideBase(kicker, title, subtitle = "", dark = false) {
  const slide = presentation.slides.add();
  ctx.addShape(slide, {
    left: 0,
    top: 0,
    width: 1280,
    height: 720,
    fill: dark ? C.deep : C.paper,
    line: ctx.line("#00000000", 0),
  });
  ctx.addText(slide, {
    text: kicker.toUpperCase(),
    left: 64,
    top: 34,
    width: 220,
    height: 24,
    fontSize: 12,
    bold: true,
    color: dark ? "#93C5FD" : C.blue,
    typeface: ctx.fonts.body,
  });
  ctx.addShape(slide, {
    left: 64,
    top: 64,
    width: 58,
    height: 3,
    fill: dark ? "#38BDF8" : C.blue,
    line: ctx.line("#00000000", 0),
  });
  ctx.addText(slide, {
    text: title,
    left: 64,
    top: 82,
    width: 760,
    height: subtitle ? 82 : 102,
    fontSize: 34,
    bold: true,
    color: dark ? "#F8FAFC" : C.ink,
    typeface: ctx.fonts.title,
    insets: { left: 0, right: 0, top: 0, bottom: 0 },
  });
  if (subtitle) {
    ctx.addText(slide, {
      text: subtitle,
      left: 64,
      top: 166,
      width: 790,
      height: 44,
      fontSize: 17,
      color: dark ? "#CBD5E1" : C.muted,
      insets: { left: 0, right: 0, top: 0, bottom: 0 },
    });
  }
  ctx.addText(slide, {
    text: "Lab 03 | Zabbix SNMP Monitoring",
    left: 64,
    top: 680,
    width: 300,
    height: 20,
    fontSize: 10,
    color: dark ? "#94A3B8" : "#64748B",
  });
  return slide;
}

function addCard(slide, x, y, w, h, title, body, color = C.blue) {
  ctx.addShape(slide, {
    left: x,
    top: y,
    width: w,
    height: h,
    fill: C.card,
    line: ctx.line("#E2E8F0", 1),
  });
  ctx.addShape(slide, {
    left: x,
    top: y,
    width: 5,
    height: h,
    fill: color,
    line: ctx.line("#00000000", 0),
  });
  ctx.addText(slide, {
    text: title,
    left: x + 18,
    top: y + 16,
    width: w - 32,
    height: 26,
    fontSize: 17,
    bold: true,
    color: C.ink,
  });
  ctx.addText(slide, {
    text: body,
    left: x + 18,
    top: y + 48,
    width: w - 32,
    height: h - 58,
    fontSize: 13,
    color: C.muted,
    insets: { left: 0, right: 0, top: 0, bottom: 0 },
  });
}

function addMetric(slide, x, y, label, value, color) {
  ctx.addShape(slide, {
    left: x,
    top: y,
    width: 156,
    height: 90,
    fill: "#0F172A",
    line: ctx.line("#1E293B", 1),
  });
  ctx.addText(slide, {
    text: value,
    left: x + 14,
    top: y + 14,
    width: 130,
    height: 36,
    fontSize: 28,
    bold: true,
    color,
  });
  ctx.addText(slide, {
    text: label,
    left: x + 14,
    top: y + 52,
    width: 130,
    height: 24,
    fontSize: 12,
    color: "#CBD5E1",
  });
}

function addFlowNode(slide, x, y, w, h, title, body, color) {
  ctx.addShape(slide, {
    left: x,
    top: y,
    width: w,
    height: h,
    fill: "#FFFFFF",
    line: ctx.line(color, 2),
  });
  ctx.addText(slide, {
    text: title,
    left: x + 16,
    top: y + 14,
    width: w - 32,
    height: 24,
    fontSize: 17,
    bold: true,
    color,
  });
  ctx.addText(slide, {
    text: body,
    left: x + 16,
    top: y + 45,
    width: w - 32,
    height: h - 54,
    fontSize: 12,
    color: C.muted,
  });
}

function addArrow(slide, x1, y1, x2, y2, color = "#94A3B8") {
  const dx = x2 - x1;
  const dy = y2 - y1;
  const len = Math.max(1, Math.sqrt(dx * dx + dy * dy));
  const angle = Math.atan2(dy, dx);
  const cx = (x1 + x2) / 2;
  const cy = (y1 + y2) / 2;
  const line = ctx.addShape(slide, {
    left: cx - len / 2,
    top: cy - 1,
    width: len,
    height: 2,
    fill: color,
    line: ctx.line("#00000000", 0),
  });
  line.rotation = (angle * 180) / Math.PI;
  ctx.addShape(slide, {
    geometry: "triangle",
    left: x2 - 8,
    top: y2 - 7,
    width: 14,
    height: 14,
    fill: color,
    line: ctx.line("#00000000", 0),
  });
}

async function addScreenshot(slide, img, x, y, w, h, fit = "contain") {
  ctx.addShape(slide, {
    left: x - 4,
    top: y - 4,
    width: w + 8,
    height: h + 8,
    fill: "#FFFFFF",
    line: ctx.line("#CBD5E1", 1),
  });
  await ctx.addImage(slide, {
    path: `${ASSETS}/${img}`,
    left: x,
    top: y,
    width: w,
    height: h,
    fit,
    alt: img,
  });
}

async function buildSlides() {
  // 1 Cover
  let slide = presentation.slides.add();
  ctx.addShape(slide, { left: 0, top: 0, width: 1280, height: 720, fill: C.deep, line: ctx.line("#00000000", 0) });
  await ctx.addImage(slide, { path: `${ASSETS}/image1.png`, left: 610, top: 80, width: 610, height: 420, fit: "cover", alt: "SNMPSim dashboard" });
  ctx.addShape(slide, { left: 570, top: 0, width: 710, height: 720, fill: "#07111FAA", line: ctx.line("#00000000", 0) });
  ctx.addText(slide, { text: "LAB 03", left: 72, top: 78, width: 180, height: 28, fontSize: 15, bold: true, color: "#38BDF8" });
  ctx.addText(slide, {
    text: "Giám sát Router, Switch, Firewall bằng Zabbix",
    left: 72,
    top: 132,
    width: 720,
    height: 138,
    fontSize: 48,
    bold: true,
    color: "#F8FAFC",
    typeface: ctx.fonts.title,
  });
  ctx.addText(slide, {
    text: "SNMP polling qua SNMPSim, trigger cảnh báo và gửi alert qua Web, Email, Telegram/SMS hoặc call gateway.",
    left: 76,
    top: 296,
    width: 590,
    height: 60,
    fontSize: 20,
    color: "#CBD5E1",
  });
  addMetric(slide, 76, 430, "Thiết bị", "4", "#38BDF8");
  addMetric(slide, 252, 430, "Metric chính", "7", "#34D399");
  addMetric(slide, 428, 430, "Alert", "Web+", "#FBBF24");
  ctx.addText(slide, { text: "Router | Switch | Firewall | Server", left: 76, top: 630, width: 460, height: 22, fontSize: 14, color: "#94A3B8" });

  // 2 Thesis
  slide = slideBase("Mục tiêu", "Zabbix biến dữ liệu SNMP thành cảnh báo vận hành tập trung.", "Bài lab chứng minh đủ ba lớp: nguồn metric, thu thập định kỳ, và cảnh báo khi vượt ngưỡng.");
  addCard(slide, 70, 270, 330, 150, "Nguồn dữ liệu", "SNMPSim giả lập Router, Switch, Firewall và Server. Mỗi thiết bị có community riêng và OID riêng.", C.cyan);
  addCard(slide, 475, 270, 330, 150, "Thu thập", "Zabbix poll SNMPv2c qua UDP 1161. Items đọc CPU, RAM, disk, sessions, traffic counters và load average.", C.blue);
  addCard(slide, 880, 270, 330, 150, "Cảnh báo", "Triggers phân loại Warning/High. Actions gửi Web, Email, Telegram/SMS hoặc call gateway.", C.amber);
  addArrow(slide, 405, 345, 468, 345);
  addArrow(slide, 810, 345, 873, 345);
  ctx.addText(slide, { text: "Kết quả cần chứng minh", left: 86, top: 505, width: 320, height: 24, fontSize: 18, bold: true, color: C.ink });
  ["snmpwalk trả về sysName/OID", "Latest data có giá trị cập nhật", "Problems xuất hiện khi Force High Load", "Action log ghi nhận alert đã gửi"].forEach((t, i) => {
    ctx.addShape(slide, { left: 92 + i * 285, top: 552, width: 18, height: 18, geometry: "ellipse", fill: [C.green, C.blue, C.amber, C.red][i], line: ctx.line("#00000000", 0) });
    ctx.addText(slide, { text: t, left: 118 + i * 285, top: 547, width: 230, height: 42, fontSize: 13, color: C.muted });
  });

  // 3 Architecture
  slide = slideBase("Kiến trúc", "Một IP, nhiều community: mô hình lab gọn nhưng đủ thiết bị.", "Tất cả host Zabbix trỏ về 127.0.0.1:1161, phân biệt bằng SNMP community.");
  addFlowNode(slide, 70, 280, 220, 116, "Firewall", "community: fortinet\nCPU/RAM/Disk/Sessions", C.red);
  addFlowNode(slide, 70, 430, 220, 116, "Router", "community: router\nCPU/Load/Traffic", C.blue);
  addFlowNode(slide, 70, 580, 220, 86, "Switch", "community: switch\nUplink/Traffic", C.green);
  addFlowNode(slide, 520, 342, 250, 130, "SNMPSim", "UDP 1161\nSNMPv2c responder\nData từ *.snmprec", C.cyan);
  addFlowNode(slide, 955, 342, 250, 130, "Zabbix", "Hosts + Items\nTriggers + Actions\nDashboard + Problems", C.amber);
  addArrow(slide, 295, 338, 515, 392, C.cyan);
  addArrow(slide, 295, 488, 515, 410, C.cyan);
  addArrow(slide, 295, 620, 515, 432, C.cyan);
  addArrow(slide, 775, 407, 950, 407, C.amber);
  await addScreenshot(slide, "image2.png", 810, 520, 360, 110, "contain");
  ctx.addText(slide, { text: "Proof: snmpwalk kiểm tra community trước khi add host vào Zabbix.", left: 810, top: 640, width: 360, height: 24, fontSize: 12, color: C.muted });

  // 4 SNMPSim dashboard
  slide = slideBase("Nguồn metric", "Dashboard SNMPSim giúp chủ động tạo sự cố để demo Zabbix.", "Không cần thiết bị thật: kéo CPU/RAM lên cao, Zabbix sẽ poll được giá trị thay đổi.");
  await addScreenshot(slide, "image1.png", 72, 245, 720, 405, "cover");
  addCard(slide, 845, 250, 310, 104, "Topology", "Firewall, Router, Switch và Server hiển thị trong một sơ đồ mạng.", C.blue);
  addCard(slide, 845, 382, 310, 104, "Realtime metrics", "CPU, RAM, disk, sessions, traffic và load average cập nhật liên tục.", C.green);
  addCard(slide, 845, 514, 310, 104, "Force / Reset", "Tạo high load để trigger Zabbix, sau đó reset về normal để recovery.", C.amber);

  // 5 Host setup
  slide = slideBase("Cấu hình Zabbix", "Mỗi thiết bị là một host SNMP riêng trong Zabbix.", "Điểm mấu chốt: cùng IP/port, khác community.");
  await addScreenshot(slide, "image8.png", 72, 240, 345, 395, "contain");
  await addScreenshot(slide, "image4.png", 455, 265, 670, 295, "contain");
  addTableLike(slide, 835, 575, [
    ["Firewall", "fortinet"],
    ["Router", "router"],
    ["Switch", "switch"],
  ]);
  ctx.addText(slide, { text: "Host interface: SNMP | IP: 127.0.0.1 | Port: 1161 | Version: SNMPv2", left: 455, top: 590, width: 650, height: 22, fontSize: 14, bold: true, color: C.ink });

  // 6 Firewall
  slide = slideBase("Firewall", "FortiGate-FW tập trung vào tải hệ thống và session table.", "Các OID vendor Fortinet giúp Zabbix theo dõi CPU, RAM, Disk và số phiên kết nối.");
  await addScreenshot(slide, "image5.png", 68, 244, 640, 330, "contain");
  addOidPanel(slide, 748, 238, "Fortinet OID", [
    ["CPU", "1.3.6.1.4.1.12356.101.4.1.3.0"],
    ["RAM", "1.3.6.1.4.1.12356.101.4.1.4.0"],
    ["Disk", "1.3.6.1.4.1.12356.101.4.1.6.0"],
    ["Sessions", "1.3.6.1.4.1.12356.101.4.1.8.0"],
  ]);
  addCard(slide, 68, 590, 260, 74, "Warning", "CPU/RAM >= 70%; Disk >= 80%; Sessions >= 5000", C.amber);
  addCard(slide, 355, 590, 260, 74, "Critical", "CPU/RAM/Disk >= 90%; sessions tăng bất thường", C.red);

  // 7 Router + Switch
  slide = slideBase("Router & Switch", "Router/Switch cần giám sát cả sức tải lẫn traffic đường truyền.", "Counter SNMP tăng dần nên Zabbix phải dùng Store value: Delta speed per second.");
  await addScreenshot(slide, "image6.png", 70, 245, 545, 240, "contain");
  await addScreenshot(slide, "image7.png", 665, 245, 545, 240, "contain");
  addCard(slide, 88, 525, 480, 98, "Router-Sim", "CPU Cisco OID, RAM UCD, load average 1m, Gi0/0 In/Out octets.", C.blue);
  addCard(slide, 682, 525, 480, 98, "Switch-Sim", "CPU, RAM, uplink status, uplink In/Out octets theo ifIndex 6.", C.green);

  // 8 Trigger
  slide = slideBase("Trigger", "Ngưỡng cảnh báo được thiết kế theo mức vận hành dễ giải thích.", "Warning dùng cho dấu hiệu quá tải; High dùng khi ảnh hưởng dịch vụ hoặc uplink down.");
  await addScreenshot(slide, "image9.png", 70, 240, 330, 395, "contain");
  addTriggerRow(slide, 455, 245, "Firewall CPU critical", "last(/FortiGate-FW/fortinet.cpu)>=90", "High", C.red);
  addTriggerRow(slide, 455, 330, "Router load high", "last(/Router-Sim/router.load.1m)>=5", "Warning", C.amber);
  addTriggerRow(slide, 455, 415, "Switch uplink down", "last(/Switch-Sim/switch.uplink.status)<>1", "High", C.red);
  addTriggerRow(slide, 455, 500, "Fortinet sessions high", "last(/FortiGate-FW/fortinet.sessions)>=5000", "Average", C.blue);

  // 9 Alerts
  slide = slideBase("Alerting", "Zabbix không chỉ hiển thị Problem, mà còn gửi thông báo ra ngoài.", "Email đã chạy; Telegram thay SMS trong lab; call cần webhook đến Twilio/PagerDuty/Opsgenie.");
  await addScreenshot(slide, "image10.png", 72, 244, 380, 235, "contain");
  await addScreenshot(slide, "image13.png", 500, 255, 650, 250, "contain");
  addCard(slide, 82, 535, 245, 88, "Web + Audio", "Problems widget và frontend sound khi trình duyệt Zabbix đang mở.", C.blue);
  addCard(slide, 365, 535, 245, 88, "Email", "SMTP Gmail bằng App Password; kiểm tra Reports -> Action log.", C.green);
  addCard(slide, 648, 535, 245, 88, "Telegram/SMS", "Telegram Bot thay SMS; SMS thật cần gateway ngoài.", C.amber);
  addCard(slide, 931, 535, 245, 88, "Call", "Webhook đến Twilio Voice hoặc nền tảng on-call.", C.red);

  // 10 Evidence
  slide = slideBase("Kết quả demo", "Latest data và Problems là hai bằng chứng chính khi bảo vệ.", "Một bên chứng minh Zabbix thu thập được metric; bên kia chứng minh trigger đã hoạt động.");
  await addScreenshot(slide, "image11.png", 70, 245, 520, 210, "contain");
  await addScreenshot(slide, "image12.png", 650, 245, 520, 210, "contain");
  addCard(slide, 100, 500, 440, 100, "Latest data", "CPU/RAM/Traffic có giá trị cập nhật theo chu kỳ poll. Đây là bằng chứng thu thập thành công.", C.blue);
  addCard(slide, 680, 500, 440, 100, "Problems", "Khi Force High Load, trigger sinh Problem và kích hoạt action cảnh báo.", C.red);

  // 11 Closing
  slide = slideBase("Kết luận", "Lab hoàn thành chuỗi giám sát tập trung từ metric đến cảnh báo.", "Mô hình đủ để demo quy trình trước khi triển khai template SNMP cho thiết bị thật.");
  const checks = [
    ["SNMPSim", "Giả lập Router, Switch, Firewall, Server qua SNMPv2c"],
    ["Zabbix Items", "Thu thập CPU, RAM, Disk, Sessions, Load và Traffic counters"],
    ["Triggers", "Phân loại Warning/High theo ngưỡng dễ giải thích"],
    ["Alerts", "Web, Email, Telegram/SMS, Call gateway và Audio frontend"],
  ];
  checks.forEach((row, i) => {
    const y = 250 + i * 86;
    ctx.addShape(slide, { left: 92, top: y, width: 36, height: 36, geometry: "ellipse", fill: [C.cyan, C.blue, C.amber, C.green][i], line: ctx.line("#00000000", 0) });
    ctx.addText(slide, { text: "✓", left: 101, top: y + 3, width: 24, height: 24, fontSize: 22, bold: true, color: "#FFFFFF" });
    ctx.addText(slide, { text: row[0], left: 150, top: y - 2, width: 180, height: 26, fontSize: 20, bold: true, color: C.ink });
    ctx.addText(slide, { text: row[1], left: 345, top: y + 2, width: 720, height: 28, fontSize: 16, color: C.muted });
  });
  ctx.addShape(slide, { left: 870, top: 250, width: 270, height: 250, fill: "#0F172A", line: ctx.line("#1E293B", 1) });
  ctx.addText(slide, { text: "Hướng phát triển", left: 895, top: 278, width: 210, height: 30, fontSize: 20, bold: true, color: "#F8FAFC" });
  ctx.addText(slide, { text: "• Dùng template SNMP chính thức\n• Tích hợp SIEM/Wazuh cho log\n• Webhook SMS/Call thật\n• Dashboard NOC hoàn chỉnh", left: 895, top: 330, width: 220, height: 130, fontSize: 15, color: "#CBD5E1" });
}

function addTableLike(slide, x, y, rows) {
  rows.forEach((r, i) => {
    const yy = y + i * 34;
    ctx.addShape(slide, { left: x, top: yy, width: 260, height: 30, fill: i % 2 ? "#F8FAFC" : "#EEF6FF", line: ctx.line("#CBD5E1", 1) });
    ctx.addText(slide, { text: r[0], left: x + 12, top: yy + 6, width: 110, height: 18, fontSize: 12, bold: true, color: C.ink });
    ctx.addText(slide, { text: r[1], left: x + 138, top: yy + 6, width: 100, height: 18, fontSize: 12, color: C.blue });
  });
}

function addOidPanel(slide, x, y, title, rows) {
  ctx.addShape(slide, { left: x, top: y, width: 410, height: 320, fill: "#0F172A", line: ctx.line("#1E293B", 1) });
  ctx.addText(slide, { text: title, left: x + 22, top: y + 22, width: 260, height: 28, fontSize: 21, bold: true, color: "#F8FAFC" });
  rows.forEach((r, i) => {
    const yy = y + 72 + i * 52;
    ctx.addText(slide, { text: r[0], left: x + 22, top: yy, width: 92, height: 22, fontSize: 14, bold: true, color: "#38BDF8" });
    ctx.addText(slide, { text: r[1], left: x + 120, top: yy, width: 260, height: 22, fontSize: 12, color: "#CBD5E1", typeface: ctx.fonts.mono });
  });
}

function addTriggerRow(slide, x, y, name, expr, sev, color) {
  ctx.addShape(slide, { left: x, top: y, width: 690, height: 68, fill: "#FFFFFF", line: ctx.line("#E2E8F0", 1) });
  ctx.addShape(slide, { left: x, top: y, width: 7, height: 68, fill: color, line: ctx.line("#00000000", 0) });
  ctx.addText(slide, { text: name, left: x + 22, top: y + 10, width: 250, height: 22, fontSize: 16, bold: true, color: C.ink });
  ctx.addText(slide, { text: expr, left: x + 22, top: y + 38, width: 510, height: 18, fontSize: 11, color: C.muted, typeface: ctx.fonts.mono });
  ctx.addShape(slide, { left: x + 570, top: y + 18, width: 86, height: 30, fill: color, line: ctx.line("#00000000", 0) });
  ctx.addText(slide, { text: sev, left: x + 570, top: y + 24, width: 86, height: 18, fontSize: 12, bold: true, align: "center", color: "#FFFFFF" });
}

await buildSlides();

await fs.mkdir(path.dirname(OUT), { recursive: true });
const pptx = await PresentationFile.exportPptx(presentation);
await pptx.save(OUT);

// Render previews for QA.
const previewDir = "D:/temp/Lap03/outputs/manual-snmp-ppt/presentations/zabbix-snmp/preview";
await fs.mkdir(previewDir, { recursive: true });
for (let i = 0; i < presentation.slides.count; i += 1) {
  const slide = presentation.slides.getItem(i);
  const png = await presentation.export({ slide, format: "png", scale: 1 });
  await saveBlobToFile(png, `${previewDir}/slide-${String(i + 1).padStart(2, "0")}.png`);
}
console.log(OUT);
