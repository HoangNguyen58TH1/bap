# for i in {1..500}; do echo "=== Run $i/500 ==="; ~/.venvs/bap/bin/python mini_cup.py || break; sleep 1; done

import re
import subprocess
import time
import unicodedata
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from ocrmac import ocrmac
from PIL import Image, ImageOps

# ============================================================
# CONFIG
# ============================================================
ADB_HOST     = "localhost"
INSTANCE_1   = 5555   # host account — creates the room
INSTANCE_2   = 5565   # guest account — joins the room
INSTANCE_3   = 5575   # guest account — joins the room (4 đội)
INSTANCE_4   = 5585   # guest account — joins the room (4 đội)

# INSTANCE_1   = 5645   # host account — creates the room
# INSTANCE_2   = 5655   # guest account — joins the room
# INSTANCE_3   = 5665   # guest account — joins the room (4 đội)
# INSTANCE_4   = 5675   # guest account — joins the room (4 đội)
# Display: 1920x1080 landscape (mCurrentOrientation=1, mOverrideDisplayInfo rotation=1)

# Team count options for Mini Cup (x, y)
TEAM_COUNT_COORDS = {
    2: (663, 988),
    4: (436, 987),
    8: (206, 997),
}
TEAM_COUNT = 4  # active selection

ROOM_KEYPAD_COORDS = {
    "1": (695, 426), "2": (951, 423), "3": (1213, 436),
    "4": (704, 505), "5": (957, 508), "6": (1200, 511),
    "7": (707, 587), "8": (960, 600), "9": (1222, 606),
    "0": (957, 673),
}
ROOM_JOIN_BTN = (1124, 774)
PHAT_BONG_COORDS = [
    (1472, 822), (1580, 824), (1578, 891), (1463, 898),
]

PORTS = {1: INSTANCE_1, 2: INSTANCE_2, 3: INSTANCE_3, 4: INSTANCE_4}
PRIORITY = [1, 2, 3, 4]
ROUND1_PAIRS = [(1, 3), (2, 4)]

SCREENSHOT_DIR = "/Users/hoangnguyen/Oivan/sakani-everything/bap"


# ============================================================
# HELPERS
# ============================================================
def adb(cmd: str, port: int = INSTANCE_1) -> str:
    """Run an adb command against the given instance port."""
    full_cmd = f"adb -s {ADB_HOST}:{port} {cmd}"
    result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip()


def tap(x: int, y: int, label: str = "", port: int = INSTANCE_1, settle: float = 2):
    """Tap a screen coordinate on the given instance."""
    print(f"  → [{tag(port)}] Tap ({x}, {y}) {f'[{label}]' if label else ''}")
    time.sleep(settle)
    adb(f"shell input tap {x} {y}", port=port)


def screenshot(port: int = INSTANCE_1, save_path: str = None):
    """Pull a screenshot from the given instance to local disk."""
    if save_path is None:
        save_path = f"{SCREENSHOT_DIR}/bap_screen_{port}.png"
    adb(f"exec-out screencap -p > {save_path}", port=port)
    print(f"  → Screenshot saved to {save_path}")


def wait(seconds: float, reason: str = ""):
    """Sleep with an optional reason label."""
    print(f"  ⏳ Wait {seconds}s {f'({reason})' if reason else ''}")
    time.sleep(seconds)


def tag(port: int) -> str:
    return f"{port}-ins{next(k for k, v in PORTS.items() if v == port)}"


def winner_of(a: int, b: int) -> int:
    return min(a, b, key=PRIORITY.index)


def loser_of(a: int, b: int) -> int:
    return max(a, b, key=PRIORITY.index)


# ============================================================
# SETUP — connect to BlueStacks instance
# ============================================================
def connect(port: int = INSTANCE_1):
    print(f"[*] Connecting to {ADB_HOST}:{port} ...")
    out = subprocess.run(
        f"adb connect {ADB_HOST}:{port}",
        shell=True, capture_output=True, text=True
    ).stdout.strip()
    print(f"    {out}")


def connect_all():
    for port in PORTS.values():
        connect(port)
    devices = subprocess.run(
        "adb devices", shell=True, capture_output=True, text=True
    ).stdout.strip()
    print(f"[*] Devices:\n{devices}\n")


# ============================================================
# STEP 1 — Dashboard → Bắt đầu trận đấu
# ============================================================
def step1_bat_dau_tran_dau(port: int):
    print(f"[{tag(port)}][1] Tapping 'Bắt đầu trận đấu' ...")
    tap(x=1600, y=1000, label="Bắt đầu trận đấu", port=port)
    wait(1, "waiting for mode selection screen")


# ============================================================
# STEP 2 — Mode selection → Thử thách
# ============================================================
def step2_thu_thach(port: int):
    print(f"[{tag(port)}][2] Tapping 'Thử thách' ...")
    # raw getevent (0x574, 0x282d) → formula: x=(rawY/32767)×1920, y=(1-rawX/32767)×1080
    tap(x=603, y=1034, label="Thử thách", port=port)
    wait(1, "waiting for Thử thách screen")


# ============================================================
# STEP 3 — Thử thách → Mini Cup
# ============================================================
def step3_mini_cup(port: int):
    print(f"[{tag(port)}][3] Tapping 'Mini Cup' ...")
    # raw getevent (0x2878, 0x5ccf) → formula: x=(rawY/32767)×1920, y=(1-rawX/32767)×1080
    tap(x=1392, y=738, label="Mini Cup", port=port)
    wait(0.5, "waiting for Mini Cup screen")


# ============================================================
# STEP 4a — Instance 1: chọn đội → Tạo phòng → Xác nhận
# ============================================================
def step4_tao_phong(port: int = INSTANCE_1):
    x, y = TEAM_COUNT_COORDS[TEAM_COUNT]
    print(f"[{tag(port)}][4] Selecting '{TEAM_COUNT} đội' ...")
    tap(x=x, y=y, label=f"{TEAM_COUNT} đội", port=port)
    wait(1, "waiting for selection to register")

    print(f"[{tag(port)}][4] Tapping 'Tạo phòng' ...")
    # raw getevent (0x0aba, 0x7026) → formula: x=(rawY/32767)×1920, y=(1-rawX/32767)×1080
    tap(x=1682, y=989, label="Tạo phòng", port=port)
    wait(2, "waiting for confirmation popup")

    print(f"[{tag(port)}][4] Tapping 'Xác nhận' ...")
    # raw getevent (0x2d17, 0x4c93)
    tap(x=1149, y=700, label="Xác nhận", port=port)
    wait(1.5, "waiting for room to be created")


# ============================================================
# EXTRACT ROOM CODE — read 6-digit code from instance 1 UI
# ============================================================
ROOM_CODE_CROP = (0.49, 0.80, 0.58, 0.86)  # vùng mã phòng theo tỉ lệ (x1, y1, x2, y2)


def read_room_code(path: str) -> str | None:
    with Image.open(path) as image:
        w, h = image.size
        x1, y1, x2, y2 = ROOM_CODE_CROP
        green = image.crop((int(x1 * w), int(y1 * h), int(x2 * w), int(y2 * h))).split()[1]
    big = green.resize((green.width * 4, green.height * 4), Image.LANCZOS)
    votes = Counter()
    for threshold in (100, 130, 160):
        crop_path = Path(SCREENSHOT_DIR) / f"room_code_crop_{threshold}.png"
        ImageOps.invert(big.point(lambda p: 255 if p > threshold else 0)).save(crop_path)
        for text, _confidence, _bbox in ocrmac.OCR(str(crop_path), language_preference=["en-US"]).recognize():
            match = re.search(r"\d{6}", text)
            if match:
                votes[match.group()] += 1
    print(f"  → OCR votes: {dict(votes)}")
    return votes.most_common(1)[0][0] if votes else None


def get_room_code(port: int = INSTANCE_1, retries: int = 5) -> str:
    for attempt in range(1, retries + 1):
        print(f"[{tag(port)}] Extracting room code via OCR (attempt {attempt}/{retries}) ...")
        screenshot(port=port)
        code = read_room_code(f"{SCREENSHOT_DIR}/bap_screen_{port}.png")
        if code:
            print(f"  → Room code: {code}")
            return code

        wait(1, "room code not visible yet")

    raise RuntimeError(f"Room code not found via OCR. Check {SCREENSHOT_DIR}/bap_screen_{port}.png")


# ============================================================
# STEP 4b — Instance 2: Vào phòng → nhập mã → xác nhận
# ============================================================
def step4_mo_nhap_ma(port: int = INSTANCE_2):
    print(f"[{tag(port)}][4] Tapping 'Vào phòng' ...")
    # raw getevent (0x0b9a, 0x5fcb) → formula: x=(rawY/32767)×1920, y=(1-rawX/32767)×1080
    tap(x=1437, y=982, label="Vào phòng", port=port)
    wait(2, "waiting for room code input screen")


def step4_nhap_ma(room_code: str, port: int = INSTANCE_2):
    print(f"[{tag(port)}][4] Entering room code: {room_code} ...")
    for digit in room_code:
        x, y = ROOM_KEYPAD_COORDS[digit]
        tap(x=x, y=y, label=digit, port=port, settle=0.3)
    wait(2, "waiting for room code input to register")


def step4_vao_phong_confirm(port: int):
    print(f"[{tag(port)}][4] Tapping 'Vào phòng' (confirm) ...")
    tap(x=ROOM_JOIN_BTN[0], y=ROOM_JOIN_BTN[1], label="Vào phòng (confirm)", port=port)
    wait(3, "waiting for room join")


def prepare_join(port: int):
    step1_bat_dau_tran_dau(port)
    step2_thu_thach(port)
    step3_mini_cup(port)
    step4_mo_nhap_ma(port)


def create_room(port: int = INSTANCE_1) -> str:
    step1_bat_dau_tran_dau(port)
    step2_thu_thach(port)
    step3_mini_cup(port)
    step4_tao_phong(port)
    return get_room_code(port)


# ============================================================
# STEP 5 — Xác nhận → Sẵn sàng (lần 1 + lần 2, mọi instance)
# ============================================================
def guest_xac_nhan(port: int):
    print(f"[{tag(port)}][5] Tapping 'Xác nhận' ...")
    # raw getevent (0x2ecb, 0x4a51) → formula: x=(rawY/32767)×1920, y=(1-rawX/32767)×1080
    tap(x=1115, y=685, label="Xác nhận", port=port)


def san_sang_lan_1(port: int):
    print(f"[{tag(port)}][5] Tapping 'Sẵn sàng' lần 1 x3 ...")
    # raw getevent (0x0bd3, 0x6da7)
    for i in range(1, 4):
        tap(x=1645, y=980, label=f"Sẵn sàng lần 1 {i}/3", port=port, settle=0.1)


def san_sang_lan_2(port: int):
    print(f"[{tag(port)}][5] Tapping 'Sẵn sàng' lần 2 x3 ...")
    wait(0.5, "waiting for UI to load before ready 2")
    # raw getevent (0x087b, 0x3f22)
    for i in range(1, 4):
        tap(x=947, y=1008, label=f"Sẵn sàng lần 2 {i}/3", port=port, settle=0.1)


def san_sang_nhom(ports: list):
    for port in ports:
        san_sang_lan_1(port)
    wait(8, "waiting for kit selection screen to load")
    for port in ports:
        san_sang_lan_2(port)


# ============================================================
# STEP 7 — Phát bóng (chạy trên cả 2 instance, chỉ 1 instance có tác dụng)
# ============================================================
def step7_phat_bong(port: int):
    print(f"[{tag(port)}][7] Tapping 'Phát bóng' {len(PHAT_BONG_COORDS)} điểm cùng lúc x3 ...")
    for lan in range(1, 4):
        print(f"  → [{tag(port)}] Phát bóng lần {lan}/3")
        with ThreadPoolExecutor(max_workers=len(PHAT_BONG_COORDS)) as executor:
            list(executor.map(lambda p: adb(f"shell input tap {p[0]} {p[1]}", port=port), PHAT_BONG_COORDS))
        wait(0.3)
    wait(4, "waiting for kickoff")


# ============================================================
# STEP 8 — Chịu thua → Rời trận đấu
# ============================================================
def step8_chiu_thua_roi_tran(port: int):
    print(f"[{tag(port)}][8] Tapping '3 gạch ngang' ...")
    # raw getevent (0x794a, 0x77cb)
    tap(x=1797, y=57, label="3 gạch ngang", port=port)
    wait(1, "waiting for menu")

    print(f"[{tag(port)}][8] Tapping 'Chịu thua' ...")
    # raw getevent (0x6bd0, 0x4d7a)
    tap(x=1162, y=170, label="Chịu thua", port=port)
    wait(1, "waiting for surrender")

    print(f"[{tag(port)}][8] Tapping 'Rời trận đấu' ...")
    # raw getevent (0x1c73, 0x50a2)
    tap(x=1210, y=840, label="Rời trận đấu", port=port)
    wait(1, "waiting after leaving match")


def o_lai_phong(port: int, delay: float = 0):
    time.sleep(delay)
    print(f"[{tag(port)}][8] Tapping 'Ở lại phòng' x10 ...")
    # raw getevent (0x2918, 0x61e9)
    for i in range(1, 11):
        tap(x=1469, y=733, label=f"Ở lại phòng {i}/10", port=port, settle=0.5)


# ============================================================
# STEP 9 — Instance 1: Thoát 2 lần → back → back → dashboard
# ============================================================
def step9_thoat_phong(port: int = INSTANCE_1):
    print(f"[{tag(port)}][9] Tapping exit x2 ...")
    # raw getevent (0x0d3b, 0x6940)
    tap(x=1579, y=968, label="Thoát 1", port=port)
    wait(1, "waiting between exit taps")
    # raw getevent (0x0a1e, 0x62e7)
    tap(x=1484, y=995, label="Thoát 2", port=port)
    wait(2, "waiting for room screen")


def step9_back_1(port: int):
    print(f"[{tag(port)}][9] Tapping back (1) ...")
    # raw getevent (0x7b5c, 0x0818)
    tap(x=121, y=39, label="Back 1", port=port)
    wait(2, "waiting for mode screen")


def step9_back_2(port: int):
    print(f"[{tag(port)}][9] Tapping back (2) ...")
    # raw getevent (same position as previous back tap)
    tap(x=121, y=39, label="Back 2", port=port)
    wait(2, "waiting for dashboard")


# ============================================================
# STEP 10 — Đội thua: back → back → dashboard
# ============================================================
def step10_back_trong_phong(port: int):
    print(f"[{tag(port)}][10] Tapping back (trong phòng) ...")
    # raw getevent (0x7ca8, 0x08d7)
    tap(x=133, y=28, label="Back trong phòng", port=port)
    wait(2, "waiting for mode screen")


def step10_back_bat_dau(port: int):
    print(f"[{tag(port)}][10] Tapping back (bắt đầu trận đấu) ...")
    # raw getevent (0x7b89, 0x08a1)
    tap(x=129, y=38, label="Back bắt đầu trận đấu", port=port)
    wait(2, "waiting for dashboard")


def back_buoc_1(port: int, champion_port: int):
    if port == champion_port:
        step9_back_1(port)
    else:
        step10_back_trong_phong(port)


def back_buoc_2(port: int, champion_port: int):
    if port == champion_port:
        step9_back_2(port)
    else:
        step10_back_bat_dau(port)


def back_ve_dashboard(port: int, max_taps: int = 3):
    for attempt in range(1, max_taps + 1):
        if is_dashboard(port):
            return
        print(f"[{tag(port)}][10] Not on dashboard, tapping back ({attempt}/{max_taps}) ...")
        step10_back_bat_dau(port)


def ve_dashboard(port: int, champion_port: int):
    if port == champion_port:
        step9_thoat_phong(port)
    back_buoc_1(port, champion_port)
    back_buoc_2(port, champion_port)
    if port != champion_port:
        back_ve_dashboard(port)


def ocr_text(path: str) -> str:
    return " ".join(text for text, _confidence, _bbox in ocrmac.OCR(path, language_preference=["en-US"]).recognize())


def normalize_text(text: str) -> str:
    text = text.replace("đ", "d").replace("Đ", "d")
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return " ".join(text.lower().split())


def is_dashboard(port: int) -> bool:
    path = f"{SCREENSHOT_DIR}/bap_check_{port}.png"
    screenshot(port=port, save_path=path)
    text = normalize_text(ocr_text(path))
    found = re.search(r"bat\s*dau\s*tran\s*dau", text) is not None
    print(f"  → [{tag(port)}] Dashboard check: {'OK' if found else 'not dashboard'} | OCR: {text}")
    return found


def ensure_dashboard(port: int):
    if not is_dashboard(port):
        raise RuntimeError(f"[{tag(port)}] Not on dashboard, stopping. Check {SCREENSHOT_DIR}/bap_check_{port}.png")


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    connect_all()

    with ThreadPoolExecutor(max_workers=4) as executor:
        list(executor.map(ensure_dashboard, PORTS.values()))

    # --- Instance 1: create room (4 đội) ---
    with ThreadPoolExecutor(max_workers=4) as executor:
        room_future = executor.submit(create_room, INSTANCE_1)
        list(executor.map(prepare_join, [INSTANCE_2, INSTANCE_3, INSTANCE_4]))
        room_code = room_future.result()

    # --- Instance 2 joins first (bracket slot), then 3 and 4 together ---
    with ThreadPoolExecutor(max_workers=3) as executor:
        list(executor.map(
            lambda port: step4_nhap_ma(room_code, port),
            [INSTANCE_2, INSTANCE_3, INSTANCE_4],
        ))

    with ThreadPoolExecutor(max_workers=3) as executor:
        list(executor.map(step4_vao_phong_confirm, [INSTANCE_2, INSTANCE_3, INSTANCE_4]))

    guest_xac_nhan(INSTANCE_2)
    wait(2, "waiting before instances 3 and 4 confirm Xác nhận")
    with ThreadPoolExecutor(max_workers=2) as executor:
        list(executor.map(guest_xac_nhan, [INSTANCE_3, INSTANCE_4]))
    wait(6, "waiting for guest ready screen to load")

    # --- Round 1: 1 vs 3, 2 vs 4 ---
    san_sang_nhom(list(PORTS.values()))
    wait(9, "waiting for round 1 to load before kickoff")
    for port in PORTS.values():
        step7_phat_bong(port)
    wait(7, "waiting for round 1 to play")

    round1_winners = [winner_of(a, b) for a, b in ROUND1_PAIRS]
    round1_losers = [loser_of(a, b) for a, b in ROUND1_PAIRS]
    with ThreadPoolExecutor(max_workers=len(round1_losers)) as executor:
        list(executor.map(step8_chiu_thua_roi_tran, [PORTS[n] for n in round1_losers]))

    ports = sorted(PORTS[n] for n in round1_winners)
    with ThreadPoolExecutor(max_workers=len(ports)) as executor:
        list(executor.map(o_lai_phong, ports, [0.5 * k for k in range(len(ports))]))

    # --- Final: 2 round-1 winners ---
    champion = winner_of(*round1_winners)
    final_loser = loser_of(*round1_winners)
    wait(5, "waiting for winners to return to room")
    san_sang_nhom([PORTS[n] for n in round1_winners])
    wait(7, "waiting for final to load before kickoff")
    for n in round1_winners:
        step7_phat_bong(PORTS[n])
    wait(14, "waiting for final to play")

    step8_chiu_thua_roi_tran(PORTS[final_loser])

    stay_ports = sorted(PORTS[n] for n in round1_winners if n != final_loser)
    with ThreadPoolExecutor(max_workers=len(stay_ports)) as executor:
        list(executor.map(o_lai_phong, stay_ports, [0.5 * k for k in range(len(stay_ports))]))

    champion_port = PORTS[champion]
    with ThreadPoolExecutor(max_workers=4) as executor:
        list(executor.map(lambda port: ve_dashboard(port, champion_port), PORTS.values()))
