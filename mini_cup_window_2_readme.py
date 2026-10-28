r"""HƯỚNG DẪN CÀI ĐẶT MINI CUP TRÊN WINDOWS (dùng mini_cup_window_2.py)
Mục tiêu: 4 instance BlueStacks 5 (1920x1080 ngang) → adb connect → chạy mini_cup_window_2.py

START
 │
 ├─ 1. CHUẨN BỊ MÁY
 │    ├─ Windows 10/11 64-bit, có quyền Administrator
 │    ├─ BIOS: bật Virtualization (Intel VT-x / AMD-V)
 │    ├─ RAM >= 16GB (4 instance), ổ trống >= 30GB
 │    └─ Ghi lại từ máy mẫu (macOS): DPI đang dùng cho BlueStacks
 │
 ├─ 2. CÀI PYTHON 3.12 (PowerShell)
 │    ├─ winget install -e --id Python.Python.3.12
==> the term winget is not recognize (FXIED)
$progressPreference = 'silentlyContinue'
Write-Host "Installing WinGet PowerShell module from PSGallery..."
Install-PackageProvider -Name NuGet -Force | Out-Null
Install-Module -Name Microsoft.WinGet.Client -Force -Repository PSGallery | Out-Null
Write-Host "Using Repair-WinGetPackageManager cmdlet to bootstrap WinGet..."
Repair-WinGetPackageManager -AllUsers
Write-Host "Done."
 │    │     (khi cài: tick "Add python.exe to PATH")
 │    └─ kiểm tra: py -3.12 --version
 │
 ├─ 3. CÀI TESSERACT OCR (PowerShell)
 │    ├─ winget install -e --id UB-Mannheim.TesseractOCR
 │    │     (nếu ID không tìm thấy: winget search tesseract,
 │    │      hoặc tải installer từ trang UB-Mannheim)
 │    ├─ winget không cài kèm gói tiếng Việt, cần thêm thủ công (PowerShell ADMIN):
 │    │     Invoke-WebRequest -Uri "https://github.com/tesseract-ocr/tessdata_best/raw/main/vie.traineddata" -OutFile "$env:TEMP\vie.traineddata"
 │    │     Copy-Item "$env:TEMP\vie.traineddata" "C:\Program Files\Tesseract-OCR\tessdata\"
 │    └─ kiểm tra:
 │          "C:\Program Files\Tesseract-OCR\tesseract.exe" --list-langs
 │          & "C:\Program Files\Tesseract-OCR\tesseract.exe" --list-langs (FIXED)
 │          (phải có "eng", "osd" và "vie")
 │
 ├─ 4. THƯ VIỆN PYTHON (PowerShell)
 │    ├─ mkdir C:\bap
 │    ├─ cd C:\bap
 │    ├─ py -3.12 -m venv .venv
 │    ├─ Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass (FIXED)
 │    ├─ .\.venv\Scripts\Activate.ps1
 │    └─ pip install pytesseract pillow
 │    └─ .\.venv\Scripts\python.exe -m pip install pytesseract (FXIED)
 │          (không cài ocrmac: chỉ chạy trên macOS)
 │    └─ Đặt mini_cup_window_2.py vào C:\bap
 │
 ├─ 5. CÀI ADB (platform-tools)
 │    ├─ Tải zip "SDK Platform-Tools for Windows" từ:
 │    │     https://developer.android.com/tools/releases/platform-tools
 │    │     (winget không có package này, phải tải zip thủ công)
 │    ├─ Có thư mục C:\platform-tools (trình duyệt có thể đã tự giải nén zip thành thư mục)
 │    │     nếu thư mục nằm chỗ khác (ví dụ Downloads), di chuyển: move "%USERPROFILE%\Downloads\platform-tools" C:\
 │    │     kiểm tra: dir C:\platform-tools\adb.exe
 │    ├─ Thêm C:\platform-tools vào PATH (chạy trong PowerShell, KHÔNG chạy trong cmd):
 │    │     tạm thời (chỉ phiên hiện tại): $env:Path += ";C:\platform-tools"
# Thêm C:\platform-tools vào PATH (System Environment Variables) (FXIED)
$dir = "C:\platform-tools"
if (-not (Test-Path "$dir\adb.exe")) {
    Write-Error "Không tìm thấy adb.exe trong $dir"
} else {
    $current = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $paths = $current -split ";" | ForEach-Object { $_.Trim().TrimEnd("\") }

    if ($paths -notcontains $dir.TrimEnd("\")) {
        [Environment]::SetEnvironmentVariable(
            "Path",
            "$current;$dir",
            "Machine"
        )
        Write-Host "Đã thêm $dir vào System PATH"
    } else {
        Write-Host "$dir đã có trong System PATH"
    }
}
 │    │     vĩnh viễn: Start → "environment variables" → Edit the system environment variables
 │    │             → Environment Variables → User variables → Path → Edit → New → C:\platform-tools
 │    ├─ Đóng hết terminal, mở PowerShell mới, kiểm tra:
 │    │     $env:Path += ";C:\platform-tools"
 │    │     adb version
 │    │     (phải hiện "Android Debug Bridge version ...")
 │    └─ Không dùng HD-Adb.exe của BlueStacks cùng lúc (dễ xung đột adb server)
 │
 ├─ 6. CÀI VÀ CẤU HÌNH BLUESTACKS 5
 │    ├─ Cài BlueStacks 5, mở Multi-instance Manager
 │    ├─ Tạo 4 instance (Pie64 hoặc Android 11)
 │    ├─ Với MỖI instance:
 │    │     Display: Landscape, resolution 1920x1080
 │    │     DPI: giống máy mẫu (macOS)
 │    │     Settings → Advanced: bật Android Debug Bridge (ADB)
 │    │     Đăng nhập game
 │    ├─ Đọc port ADB:
 │    │     C:\ProgramData\BlueStacks_nxt\bluestacks.conf → tìm "adb_port"
 │    │     (Hyper-V: port có thể đổi mỗi lần mở BlueStacks, đọc lại)
 │    └─ Cập nhật INSTANCE_1..4 trong mini_cup_window_2.py nếu port khác
 │
 ├─ 7. KIỂM TRA THEO THỨ TỰ (PowerShell)
 │    ├─ adb kill-server
 │    ├─ adb connect 127.0.0.1:5556        (lặp lại cho từng port)
 │    ├─ adb devices
 │    │     → thấy đủ 4 dòng "device" (không "offline", không "unauthorized")
 │    ├─ adb -s 127.0.0.1:5556 shell wm size
 │    │     → "Physical size: 1920x1080" cho cả 4 máy
 │    ├─ Chụp màn hình → mở PNG xem: đúng màn hình, không đen, không lệch
 │    └─ Dashboard có chữ "Bắt đầu trận đấu" trên cả 4 máy
 │
 ├─ 8. CHẠY
 │    ├─ cd C:\bap
 │    └─ .\.venv\Scripts\python.exe mini_cup_window_2.py
 │          (nếu ensure_dashboard lỗi: mở
 │           %USERPROFILE%\bap_screenshots\bap_check_<port>.png để xem)
 │
END

TROUBLESHOOTING
 ├─ adb devices trống hoặc "offline"
 │    ├─ adb kill-server → adb connect lại từng port
 │    └─ đóng BlueStacks, mở lại, đọc lại adb_port trong bluestacks.conf
 │
 ├─ adb thấy device nhưng tap không ăn
 │    ├─ wm size phải đúng 1920x1080 (sai thì sửa resolution của instance)
 │    ├─ DPI phải giống máy mẫu, nếu không layout UI sẽ lệch
 │    ├─ không minimize cửa sổ BlueStacks, không để cửa sổ bị che hoàn toàn
 │    └─ tăng settle/wait trong mini_cup_window_2.py (Windows có thể chậm hơn macOS)
 │
 ├─ OCR không đọc được "Bắt đầu trận đấu" hoặc mã phòng
 │    ├─ kiểm tra --list-langs có "vie" chưa
 │    ├─ mở ảnh screenshot xem chữ có rõ không (độ phân giải, độ mờ)
 │    └─ nếu vẫn không được: đổi DASHBOARD_RE sang một chữ dễ đọc hơn trên màn hình
 │
 ├─ UnicodeEncodeError khi in tiếng Việt/emoji
 │    └─ đặt biến môi trường: setx PYTHONUTF8 1 rồi mở PowerShell mới
 │
 └─ Hiện popup "Ngắt kết nối với server" trong lúc chạy
      → cần thêm bước phát hiện popup và bấm "Kết nối lại server"

Ghi chú:
 - Test tap/screenshot riêng: tạo file test riêng, không để chung trong mini_cup_window_2.py.
 - Chạy full flow chỉ khi các bước 7 đều OK.
"""
