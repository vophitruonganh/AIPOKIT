# Hướng dẫn cho Product Owner (không nằm trong plugin, chỉ để người đọc)

## Cài đặt (làm theo đúng thứ tự)

**Chuẩn bị** (kiểm tra trong Terminal):
- Claude Code đã cài và đăng nhập: gõ `claude --version` thấy số phiên bản. Chưa có thì cài ở https://claude.com/claude-code rồi chạy `claude` một lần để đăng nhập.
- Mac cần Homebrew: gõ `brew --version`. Chưa có thì cài ở https://brew.sh.
- Python 3: gõ `python3 --version`. Chưa có thì chạy `brew install python`.
- Windows: dùng WSL (Ubuntu) và làm như Linux.

**Cài (chọn một cách):**

- **Cách A, khuyên dùng:** mở Terminal (Cmd + Space, gõ Terminal, Enter), dán lệnh sau rồi Enter:

  ```bash
  git clone https://github.com/vophitruonganh/AIPOKIT.git ~/AIPOKIT && bash ~/AIPOKIT/install.sh
  ```

- **Cách B, ngay trong Claude Code:** gõ lần lượt `/plugin marketplace add vophitruonganh/AIPOKIT`, rồi `/plugin install po-kit-spec@aipokit`, rồi `/po-kit-spec:setup`.
- **Cách C, từ file zip:** tải zip (nút Code, chọn Download ZIP) vào Downloads, rồi chạy `unzip -oq ~/Downloads/AIPOKIT-main.zip -d /tmp/aipokit && bash /tmp/aipokit/*/install.sh`.

Script tự làm hết: chép plugin vào `~/.po-kit`, đăng ký và cài plugin vào Claude Code, cài công cụ xuất Word/PDF (graphviz, LibreOffice, thư viện Python trong venv riêng `~/.po-kit/venv`, không đụng Python hệ thống), rồi kiểm tra môi trường. Cài thành công khi cuối màn hình có `Status: ✔ enabled` và `Environment OK`. Các dòng `WARNING: Cache entry…` và `FutureWarning: fitz…` là vô hại.

**Kiểm tra:** mở một phiên Claude Code **mới**, gõ `/po-kit-spec:` và thấy danh sách lệnh.

**Dùng lần đầu:**
```bash
mkdir -p ~/specs/ten-san-pham && cd ~/specs/ten-san-pham && claude
```
Trong Claude Code gõ `/po-kit-spec:start`, chọn tab, app hoặc dán URL. Trả lời một lượt câu hỏi (mục đích, môi trường, vai trò, gõ "ok" để duyệt danh sách cấm, ngôn ngữ). Tự đăng nhập khi Claude nhắc, rồi trả lời "xong". Cuối cùng nhận SRS Word và PDF trong thư mục đó.

**Cập nhật:** `cd ~/AIPOKIT && git pull && bash install.sh`. **Gỡ:** `claude plugin uninstall po-kit-spec@aipokit && claude plugin marketplace remove aipokit && rm -rf ~/.po-kit`

**Lỗi thường gặp:**
| Thấy gì | Làm gì |
| --- | --- |
| `claude: command not found` | Cài Claude Code, mở cửa sổ Terminal mới |
| `brew: command not found` | Cài Homebrew ở https://brew.sh |
| `externally-managed-environment` | Đừng tự chạy pip, chạy lại lệnh cài (đã dùng venv riêng) |
| Không thấy lệnh `/po-kit-spec:` | Mở phiên Claude Code mới, kiểm tra `claude plugin list` |
| `MISSING: dot` hoặc `soffice` | `brew install graphviz` hoặc `brew install --cask libreoffice`, rồi gõ `/po-kit-spec:setup` |
| Menu start không hiện tab trình duyệt | Dán URL thay vào |

## Cài đặt (một lần)
Trong Claude Code gõ hai lệnh:
```
/plugin marketplace add <tổ-chức>/po-kit
/plugin install po-kit-spec@aipokit
```
Cần bật kết nối điều khiển Chrome và Claude Docs.

## Dùng
1. (Không bắt buộc) `/po-kit-spec:setup-standards [thư mục mẫu]`: dạy plugin quy trình, mẫu tài liệu và ngôn ngữ của team bạn.
2. `/po-kit-spec:build-spec <địa chỉ app>`: Claude hỏi một lần (tài khoản từng vai trò, việc cấm, ngôn ngữ), rồi làm. Bạn duyệt ở 3 cổng.
3. `/po-kit-spec:export-srs <thư mục md>`: ra Word và PDF theo mẫu SRS có sẵn, đúng ngôn ngữ đã chọn.
4. `/po-kit-spec:export-custom <file mẫu>`: ra tài liệu theo mẫu bất kỳ của bạn.
5. `/po-kit-spec:add-language <mã>`: thêm ngôn ngữ xuất mới (có sẵn: en, vi).

## Chọn ngôn ngữ
Có hai lựa chọn: ngôn ngữ nội dung spec, và ngôn ngữ tài liệu xuất. Mọi hướng dẫn nội bộ của plugin bằng tiếng Anh để tiết kiệm token; bạn vẫn làm việc với Claude bằng tiếng Việt.

## Dùng với Codex hoặc ChatGPT (chưa kiểm thử trên hai công cụ này)
- **Codex:** chạy `bash portable/install-codex.sh po-kit-spec --global`, thêm Playwright MCP vào `~/.codex/config.toml` (xem `portable/README.md`), rồi nói với Codex: "dùng skill po-kit-spec dựng spec cho <địa chỉ app>".
- **ChatGPT:** tạo Custom GPT hoặc Project, dán `portable/chatgpt/po-kit-spec/instructions.md` vào phần Instructions, tải 3 file trong `knowledge/` lên. Bản này chỉ viết và rà spec từ tài liệu anh đưa, không crawl app, không lint, không xuất SRS.


## Cập nhật v1.1: cách tài liệu thể hiện phần chưa chắc, trang đọc, chọn model

- **Không còn nhãn tiếng Anh trong tài liệu xuất.** Quy tắc nghiệp vụ và tiêu chí chấp nhận nằm trong bảng có cột Trạng thái (Đã quan sát, Suy từ API, Đề xuất, Chờ xác nhận).
- **Cần xác nhận:** mỗi điểm chưa chắc có mã TBD, người trả lời, ưu tiên, kết quả kiểm tra và cột Hạn chốt để PO điền. Đầu mục có dòng "Mức hoàn chỉnh".
- **Giả định, phụ thuộc, lịch sử thay đổi** khai trong `config.json` (`assumptions`, `dependencies`, `revisions`).
- **Trang đọc trên web:** `/po-kit-spec:export-reader <thư mục md>` tạo một trang có mục lục, tìm kiếm, khối gập, nổi bật phần Cần xác nhận.
- **Chọn model và effort theo độ phức tạp:** xem `references/model-routing.md`; tên model chỉ nằm trong `scripts/models.json`.

## Cập nhật v1.2: đi hết mọi tính năng, không bỏ sót

- **Đi hết toàn bộ app.** Bước khảo sát đi qua mọi menu, menu con, tab, tab con, chế độ xem, bộ lọc và toàn bộ giá trị trong dropdown, nút, cột, hành động trên từng dòng, xem chi tiết, form và cửa sổ bật lên. Form và cửa sổ chỉ mở ra xem rồi đóng lại, không lưu. Việc này làm lại cho từng vai trò có tài khoản.
- **Bảng kiểm kê `inventory.md`.** Mỗi phần tử thấy trên app là một dòng: nhãn đúng như trên màn hình, loại, trạng thái (đã đi, đã mở chỉ đọc, bị chặn vì an toàn, cần dữ liệu, cần vai trò khác, lỗi) và tính năng phụ trách nó. Mỗi màn hình còn được quét giao diện tự động để bắt các nút hoặc tab dễ bị sót.
- **Cổng kiểm tra độ phủ.** `scripts/inventory_check.py` chặn quy trình khi còn mục chưa đi, hoặc khi một phần tử có trên app mà spec không nhắc tới. `/po-kit-spec:lint` cũng chạy kiểm tra này nếu thấy file kiểm kê.
- **Khi viết brief, chỉ cấm lưu, không cấm mở form.** Nếu cấm bấm "Thêm mới" hay "Điều chỉnh" thì toàn bộ trường trong form sẽ thành "chưa xác nhận". Ở một lần chạy thật, 64 trên 118 câu hỏi không kiểm được chủ yếu vì lý do này. Nên dùng thêm một tài khoản có dữ liệu thật hoặc dữ liệu thử.

## Cập nhật v1.3: vòng chốt với PO

1. `/po-kit-spec:po-sheet <thư mục md>`: xuất file Excel gồm mọi câu hỏi mở và quy tắc "Đề xuất". Có cột người trả lời, ưu tiên, bộ lọc và sheet tổng hợp theo người trả lời.
2. PO điền cột **Quyết định**:
   - **Đồng ý**: giữ giả định hoặc đề xuất hiện tại.
   - **Sửa**: ghi nội dung đúng.
   - **Từ chối**: không áp dụng, ghi lý do.
   - **Kiểm trên app**: chuyển QA kiểm trên app.

   PO điền thêm người chốt và ngày. Dòng nào chưa trả lời thì để trống.
3. `/po-kit-spec:po-import <thư mục md> <file đã trả lời>`:
   - Lưu bản cũ vào `versions/`.
   - Ghi câu trả lời với trạng thái **PO đã chốt** (ai chốt, ngày nào). Quy tắc được đổi nhãn theo quyết định.
   - Tăng phiên bản, thêm dòng lịch sử thay đổi.
   - Xuất `changes-v<cũ>-v<mới>.md` cho dev và QA. Plugin cũng cập nhật lại luồng, trường, tiêu chí và test case theo quyết định.
4. Xuất lại SRS. Trong tài liệu, cột Trạng thái hiện "PO đã chốt", và dòng "Mức hoàn chỉnh" tính cả phần PO đã chốt.
5. `/po-kit-spec:diff <bản cũ> <bản mới>`: so sánh hai phiên bản bất kỳ.

Mã TBD, BR và BUG giữ ổn định giữa các phiên bản để ticket không bị lệch.

## Cập nhật v1.4: dùng cho mọi website hoặc app, tự chạy không vướng

- **Không gắn với website nào.** Bỏ hết ví dụ, selector và mẹo riêng của một trang. Plugin dựa trên nhãn hiển thị, vai trò và đường dẫn, nên dùng được cho mọi website và web app.
- **Đọc được app mobile.** Mỗi lần chạy chọn một "driver": trình duyệt (web), `adb` (Android), hoặc ảnh chụp màn hình do bạn gửi (iOS hay app khác). Xem `references/drivers.md`.
- **Tự kiểm tra truy cập trước.** Nếu mạng phía Claude bị chặn, plugin tự chuyển sang trình duyệt trên máy bạn và chỉ báo một dòng.
- **Bạn tự đăng nhập, Claude không bao giờ gõ mật khẩu.** Phase 0 chỉ hỏi cần đi những vai trò nào. Tới mỗi vai trò, Claude nhắn "đăng nhập vai trò X rồi trả lời xong". Nên dùng một profile trình duyệt riêng cho mỗi vai trò để khỏi phải đăng xuất.
- **Hỏi môi trường.** Trên production, plugin chỉ đọc tuyệt đối: không gửi form, không tạo bản ghi TEST. Trên staging hoặc dev thì được thử gửi form sai để đọc thông báo lỗi và được tạo bản ghi TEST.
- **Chỉ còn một cổng duyệt** là danh sách hành động cấm. Danh sách tính năng sau recon được gửi để bạn xem nhưng không chặn quy trình. Các mục Cannot verify không bắt bạn duyệt riêng nữa mà đi thẳng vào file Excel cho PO.
- **Chạy lại khi app có bản mới không bị đổi số.** `inventory_diff.py` ghép kiểm kê mới với kiểm kê cũ: phần tử cũ giữ mã, phần tử mới được thêm mã, phần tử biến mất ghi "Removed". Chỉ những tính năng bị ảnh hưởng mới phải viết lại.
- **Xuất theo template riêng có bước so trang.** `export-custom` so trang mẫu với trang xuất ra và liệt kê chỗ lệch trước khi giao.

## Cập nhật v1.4.1: vòng PO thành phần mở rộng tuỳ chọn

- Mặc định plugin dừng ở bước xuất tài liệu. Vòng PO (xuất Excel → PO quyết định → nạp lại) không còn là bước bắt buộc.
- Ở Phase 0, plugin hỏi thêm spec dùng để làm gì: ghi lại hiện trạng, hay làm căn cứ để xây, sửa hoặc test.
- Sau khi giao SRS, agent tự đếm số câu hỏi ưu tiên cao và số quy tắc đề xuất (`po_sheet_export.py <md> --count`), rồi hỏi bạn đúng một câu kèm khuyến nghị:
  - Spec chỉ để ghi lại hiện trạng, hoặc không còn điểm nào chặn: khuyên bỏ qua.
  - Spec làm căn cứ để xây, sửa hoặc test và còn điểm ưu tiên cao: khuyên dùng, và chỉ đưa các điểm ưu tiên cao.
- Không trả lời hoặc trả lời "không" thì bỏ qua, và agent không hỏi lại cho phiên bản đó. Bạn vẫn có thể gọi `/po-kit-spec:po-sheet` bất cứ lúc nào.
- Quy tắc chi tiết nằm ở `references/po-loop-decision.md`.
