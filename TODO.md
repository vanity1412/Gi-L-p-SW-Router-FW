Đóng vai là một Full-stack Developer và Network Automation Engineer chuyên nghiệp. Hãy viết cho tôi một ứng dụng Web (Web Dashboard) để quản lý hệ thống giả lập thiết bị mạng bằng SNMPSim.

1. Công nghệ sử dụng:

Backend: Python với Flask hoặc FastAPI (vì SNMPSim cũng chạy bằng Python nên dễ quản lý tiến trình).

Frontend: HTML, CSS, JavaScript (sử dụng Bootstrap 5 để làm giao diện hiện đại và thư viện Vis.js hoặc Cytoscape.js để vẽ sơ đồ Topology liên kết thiết bị).

2. Luồng hoạt động và Chức năng yêu cầu:

Quản lý file .snmprec: Backend có khả năng đọc các file .snmprec (ví dụ: fortinet.snmprec, router.snmprec, ubuntu.snmprec, switch.snmprec) từ một thư mục data/. Nó cần dùng Regex hoặc xử lý chuỗi để bóc tách các giá trị OID hiện tại (Tên thiết bị, CPU, RAM, trạng thái Port) và hiển thị lên Dashboard.

Thay đổi thông số (Chỉnh sửa động): Trên giao diện Web, tôi có thể nhập giá trị mới (ví dụ: đổi CPU từ 25% lên 90%, hoặc đổi RAM). Khi bấm "Save", Backend sẽ tìm đúng dòng OID đó trong file .snmprec tương ứng và ghi đè giá trị mới.

Điều khiển tiến trình (Start/Stop): Có nút trên Web để chạy lệnh khởi động snmpsim-command-responder hoặc tắt tiến trình này đi (dùng thư viện subprocess hoặc psutil của Python).

Sơ đồ mạng (Topology): Có một tab hiển thị sơ đồ mạng trực quan gồm 4 Node (Fortinet, Router, Switch, Ubuntu). Khi click vào một Node trên sơ đồ, nó sẽ hiện ra bảng thông số (IP, CPU, RAM) bên cạnh.

3. Dữ liệu đầu vào (Cấu trúc file):
Dưới đây là dữ liệu mẫu của 4 thiết bị mà tôi đang có. Hãy dựa vào các mã OID này để viết hàm parser (đọc/ghi) cho Backend.

Fortinet (IP: 192.168.122.132):

Tên (sysName): 1.3.6.1.2.1.1.5.0

CPU: 1.3.6.1.4.1.12356.101.4.1.3.0

RAM: 1.3.6.1.4.1.12356.101.4.1.4.0

Router (IP: 192.168.122.134):

Tên: 1.3.6.1.2.1.1.5.0

CPU (Cisco OID): 1.3.6.1.4.1.9.9.109.1.1.1.1.5.1

Ubuntu (IP: 192.168.122.133):

Tên: 1.3.6.1.2.1.1.5.0

CPU (UCD-SNMP): 1.3.6.1.4.1.2021.11.9.0

RAM Total: 1.3.6.1.4.1.2021.4.5.0

RAM Avail: 1.3.6.1.4.1.2021.4.6.0

Switch (IP: 192.168.122.135):

Tên: 1.3.6.1.2.1.1.5.0

Hãy viết mã nguồn chi tiết, chia thành cấu trúc thư mục rõ ràng (ví dụ: app.py, templates/index.html, v.v.) và hướng dẫn tôi cách chạy dự án này trên môi trường Windows.