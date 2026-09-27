# 📖 HƯỚNG DẪN VẬN HÀNH CONWAY AUTOMATON (LOCAL ANTIGRAVITY ENGINE)

Tài liệu hướng dẫn toàn diện cách khởi động, theo dõi, giao tiếp, nạp vốn an toàn và rút tiền cho Agent **Conway Automaton** chạy bằng trí tuệ nhân tạo **Gemini 3.8 Flash (Antigravity Engine)** trực tiếp trên máy của bạn.

---

## 📌 TỔNG QUAN HỆ THỐNG

- **Mô hình AI sử dụng**: Gemini 3.8 Flash thông qua **Antigravity Local Bridge** (`http://127.0.0.1:8888`).
- **Chi phí suy luận LLM**: **0 VNĐ** (Miễn phí 100%, không tốn tiền API OpenAI/Claude/Groq).
- **Giao diện giám sát Web**: [http://localhost:5050](http://localhost:5050)
- **Mạng Blockchain**: **Base Network (EVM)**
- **Địa chỉ ví Agent**: `0x4b6aCB4709f46EcF64A46b335b8A615E840165Cd`
- **Quyền sở hữu ví**: **Non-Custodial (Tự quản)** — Toàn bộ Private Key nằm trên máy của bạn.

---

## 🚀 1. CÁCH KHỞI ĐỘNG HỆ THỐNG

Chỉ cần chạy **1 lệnh duy nhất** bằng PowerShell:

```powershell
cd D:\agebt\automaton
.\start_automaton.ps1
```

### Hệ thống sẽ tự động thực hiện 3 bước:
1. **Khởi động Antigravity Bridge (Port 8888)**: Cầu nối AI cục bộ phục vụ các lượt tư duy của Agent.
2. **Khởi động Web Control Dashboard (Port 5050)**: Tự động mở trình duyệt hiển thị bảng điều khiển trực quan.
3. **Chạy Automaton Runtime**: Agent bắt đầu chu kỳ phân tích, lập kế hoạch nhiệm vụ và thực thi.

> **Mẹo**: Khi muốn tắt hệ thống, bạn chỉ cần nhấn tổ hợp phím `Ctrl + C` trên cửa sổ PowerShell.

---

## 🖥️ 2. THEO DÕI & GIAO TIẾP VỚI AGENT

### Cách 1: Qua Giao diện Web (Khuyên dùng)
- Truy cập trình duyệt: **[http://localhost:5050](http://localhost:5050)**
- Hoặc mở nhanh bằng lệnh:
  ```powershell
  .\open_dashboard.ps1
  ```
- **Các tính năng trên giao diện**:
  - **Số dư USDC thực tế**: Hiển thị số vốn hiện tại trên mạng Base.
  - **Hàng rào an toàn**: Hiển thị rõ các hạn mức chi tiêu đang bảo vệ ví.
  - **Mục tiêu & Nhiệm vụ**: Xem Agent đang lên kế hoạch làm gì, tiến độ ra sao.
  - **Nhật ký tư duy (Live Stream)**: Xem dòng suy nghĩ thực tế của AI theo thời gian thực.
  - **Hộp chỉ đạo (Prompt Box)**: Gõ tin nhắn/chỉ thị mới cho Agent và bấm **"Gửi Lệnh 🚀"**. Agent sẽ thức dậy và tiếp nhận mệnh lệnh ngay lập tức.

### Cách 2: Kiểm tra nhanh trong Terminal
Nếu bạn muốn kiểm tra trạng thái mà không cần mở trình duyệt:
```powershell
.\check_agent.ps1
```

---

## 🌐 3. TÍCH HỢP TAVILY AI SEARCH (TÌM KIẾM INTERNET THỜI GIAN THỰC)

Agent đã được trang bị công cụ `web_search` được cấp sức mạnh bởi **Tavily AI Search**:
- **Khả năng**: Tự động tìm kiếm thị trường, săn Web3 bounties, tra cứu lỗi kỹ thuật, tài liệu API mới nhất.
- **Cấu hình trên Giao diện Web**:
  1. Mở [http://localhost:5050](http://localhost:5050)
  2. Bấm vào nút **`🌐 Tavily Search`** trên thanh Header.
  3. Bạn có thể xem trạng thái, cập nhật/thay đổi API Key mới, và **thử nghiệm tìm kiếm trực tiếp** ngay trong popup!
- **Cấu hình qua file**: Lưu tại trường `"tavilyApiKey"` trong `~/.automaton/automaton.json` hoặc biến môi trường `TAVILY_API_KEY`.

---

## 🛡️ 4. HÀNG RÀO BẢO VỆ VỐN & CHỐNG LOOP (SPEND LIMITS)

Để phòng tránh rủi ro AI bị lặp vô hạn (Infinite Loop) hoặc đốt sạch vốn khi prompt bị lú lẫn, các chốt chặn an toàn đã được kích hoạt cứng trong file cấu hình:

| Tiêu chuẩn an toàn | Giá trị cấu hình | Ý nghĩa & Cơ chế bảo vệ |
| :--- | :--- | :--- |
| **Giới hạn chi tiêu / ngày** | **$2.00 / ngày** | AI không thể tiêu quá $2 trong 24 giờ dưới mọi hình thức. |
| **Giới hạn mỗi lần chuyển** | **≤ $0.50 / lệnh** | Mỗi giao dịch tối đa 50 cents, tránh chuyển khoản số tiền lớn bất thường. |
| **Giới hạn chi tiêu / giờ** | **≤ $1.00 / giờ** | Ngăn chặn việc dồn tiền tiêu nhanh trong thời gian ngắn. |
| **Quỹ dự trữ bất khả xâm phạm** | **≥ $5.00** | AI tuyệt đối không được phép chi tiêu chạm vào mốc $5 này. |
| **Cooldown chống Loop** | **60 giây** | Bắt buộc phải có khoảng nghỉ tối thiểu 60s giữa 2 giao dịch liên tiếp. |
| **Giới hạn turns chu kỳ** | **10 turns** | Sau tối đa 10 lượt suy luận, Agent bắt buộc phải ngủ nghỉ chu kỳ, ngăn runaway process. |
| **Miền thanh toán x402** | `conway.tech` | Chỉ cho phép thanh toán dịch vụ tự động cho domain được tin cậy. |

---

## 💰 5. HƯỚNG DẪN NẠP VỐN THỬ NGHIỆM

Khi bạn đã sẵn sàng cho Agent thực chiến:

1. **Khuyến cáo số vốn**: Chỉ nạp từ **$10 đến $20 USDC** (Tuyệt đối không nạp số tiền lớn).
2. **Mạng Blockchain**: Phải chọn mạng **Base** (Base Mainnet).
3. **Địa chỉ nhận của Agent**:
   ```
   0x4b6aCB4709f46EcF64A46b335b8A615E840165Cd
   ```
4. **Phí Gas**: Nạp kèm một lượng rất nhỏ ETH mạng Base (khoảng **$0.5 - $1 ETH**) để làm phí giao dịch trên mạng Base.

---

## 💸 6. HƯỚNG DẪN RÚT TIỀN VỀ BẤT CỨ LÚC NÀO

Bạn là người sở hữu chìa khóa Private Key của ví này, do đó bạn có toàn quyền rút tiền về ví cá nhân bất kỳ lúc nào.

### Cách 1: Rút qua MetaMask / Rabby Wallet (Dễ nhất)
1. Mở Web Dashboard tại [http://localhost:5050](http://localhost:5050).
2. Tại thẻ **Ví On-Chain**, bấm **`👁️ Xem Private Key`** rồi bấm **`📋 Copy Private Key`**.
3. Mở tiện ích **MetaMask** $\rightarrow$ Bấm chọn tài khoản $\rightarrow$ **"Import Account" (Nhập tài khoản)** $\rightarrow$ Dán Private Key vào.
4. Chọn mạng **Base**: Số dư USDC và ETH của Agent sẽ hiện lên. Bạn chỉ việc bấm **Gửi (Send)** về ví chính của mình.

### Cách 2: Rút tự động bằng 1 lệnh PowerShell
Chỉ cần chạy lệnh sau trong thư mục dự án:
```powershell
.\withdraw.ps1 0x_dia_chi_vi_ca_nhan_cua_ban
```
Script sẽ tự động quét toàn bộ số dư USDC và ETH trên mạng Base rồi gửi thẳng về địa chỉ ví của bạn.

---

## 📂 7. CÁC TẬP TIN QUAN TRỌNG

- [`start_automaton.ps1`](file:///D:/agebt/automaton/start_automaton.ps1): Script khởi động tất cả (Bridge + Dashboard + Agent).
- [`open_dashboard.ps1`](file:///D:/agebt/automaton/open_dashboard.ps1): Mở nhanh giao diện Dashboard trên trình duyệt.
- [`check_agent.ps1`](file:///D:/agebt/automaton/check_agent.ps1): Kiểm tra trạng thái Agent trong Terminal.
- [`withdraw.ps1`](file:///D:/agebt/automaton/withdraw.ps1): Công cụ kiểm tra và rút tiền tức thì.
- [`C:\Users\phu09\.automaton\automaton.json`](file:///C:/Users/phu09/.automaton/automaton.json): File cấu hình sứ mệnh, hạn mức chi tiêu và tham số chạy.
- [`C:\Users\phu09\.automaton\wallet.json`](file:///C:/Users/phu09/.automaton/wallet.json): Nơi lưu trữ Private Key của Agent trên máy cục bộ.
- [`C:\Users\phu09\.automaton\state.db`](file:///C:/Users/phu09/.automaton/state.db): Cơ sở dữ liệu SQLite lưu toàn bộ lịch sử tư duy, nhiệm vụ, giao dịch.
