from flask import Blueprint, render_template, abort, request, redirect, url_for
from models import SlotPlay, SlotMachine, SlotHit
from extensions import db




disk_up_ultra_bp = Blueprint("disk_up_ultra", __name__, url_prefix="/slot/disk-up-ultra")

# トップページ（仮）
@disk_up_ultra_bp.route("/")
def top():
    return "Disk Up Ultra トップページ（仮）"

# プレイ詳細ページ
@disk_up_ultra_bp.route("/play/<int:slot_play_id>", methods=["GET", "POST"], endpoint="play_detail")
def play_detail(slot_play_id):
    play = SlotPlay.query.get(slot_play_id)
    if not play:
        abort(404)

    machine = SlotMachine.query.get(play.slot_machine_id)
    if not machine or machine.name != "ディスクアップ ULTRAREMIX":
        abort(404, description="未対応の機種です")

    three_prob = None
    total_games = None

    if request.method == "POST":
        # 入力処理
        end_game_input = request.form.get("end_game")
        if end_game_input:
            try:
                play.end_game = int(end_game_input)
            except ValueError:
                pass

        count1_input = request.form.get("count1")
        three_prob_input = request.form.get("three_prob")
        try:
            play.count1 = int(count1_input) if count1_input else None
        except ValueError:
            play.count1 = None

        three_prob = three_prob_input

        # ★追加処理：3枚役確率から対象ゲーム数（count2）を逆算して保存
        try:
            if play.count1 is not None and three_prob_input:
                prob_value = float(three_prob_input.replace("1/", "").strip())
                play.count2 = round(play.count1 * prob_value)
            else:
                play.count2 = None
        except ValueError:
            play.count2 = None

        db.session.commit()

        # ★ POST後の分岐
        action = request.form.get("action")
        if action == "analyze":
            return redirect(url_for("disk_up_ultra.analyze", slot_play_id=slot_play_id))
        else:
            return redirect(url_for("disk_up_ultra.play_detail", slot_play_id=slot_play_id))

    # GETまたはPOST後再表示
    hits = SlotHit.query.filter_by(slot_play_id=slot_play_id).order_by(SlotHit.id.desc()).all()

    if play.start_game is not None and play.end_game is not None:
        total_games = play.end_game - play.start_game

    bb_count = sum(1 for h in hits if h.bonus_type in ["赤BB", "白BB", "黒BB", "異色BB"])
    rb_count = sum(1 for h in hits if h.bonus_type == "RB")

    # 信頼区間のデータ計算
    trust_65, trust_95 = calculate_trust_interval_counts(play, hits)

    return render_template(
        "disk_up_ultra/disk_up_ultra.html",
        play=play,
        machine=machine,
        hits=hits,
        bb_count=bb_count,
        rb_count=rb_count,
        total_games=total_games,
        three_prob=three_prob,
        trust_65=trust_65,
        trust_95=trust_95,
    )




# 当たり追加処理
@disk_up_ultra_bp.route("/add-hit/<int:slot_play_id>", methods=["POST"], endpoint="add_hit")
def add_hit(slot_play_id):
    play = SlotPlay.query.get(slot_play_id)
    if not play:
        abort(404)

    hit_game = request.form.get("hit_game")
    bonus_type = request.form.get("bonus_type")
    flag = request.form.get("flag")

    if hit_game and bonus_type:
        try:
            new_hit = SlotHit(
                slot_play_id=slot_play_id,
                hit_game=int(hit_game),
                bonus_type=bonus_type,
                flag=flag or None
            )
            db.session.add(new_hit)
            db.session.commit()
        except ValueError:
            pass

    return redirect(url_for("disk_up_ultra.play_detail", slot_play_id=slot_play_id))

# 当たり削除処理
@disk_up_ultra_bp.route("/delete-hit/<int:hit_id>", methods=["POST"], endpoint="delete_hit")
def delete_hit(hit_id):
    hit = SlotHit.query.get(hit_id)
    if not hit:
        abort(404)

    slot_play_id = hit.slot_play_id
    db.session.delete(hit)
    db.session.commit()

    return redirect(url_for("disk_up_ultra.play_detail", slot_play_id=slot_play_id))



# 設定分析処理
@disk_up_ultra_bp.route("/analyze/<int:slot_play_id>", methods=["GET"], endpoint="analyze")
def analyze(slot_play_id):
    play = SlotPlay.query.get(slot_play_id)
    if not play:
        abort(404)

    machine = SlotMachine.query.get(play.slot_machine_id)
    if not machine or machine.name != "ディスクアップ ULTRAREMIX":
        abort(404, description="未対応の機種です")

    hits = SlotHit.query.filter_by(slot_play_id=slot_play_id).all()

    if play.start_game is not None and play.end_game is not None:
        total_games = play.end_game - play.start_game
    else:
        total_games = 0

    rb = sum(1 for h in hits if h.bonus_type == "RB")
    bb = sum(1 for h in hits if h.bonus_type in ["赤BB", "白BB", "黒BB", "異色BB"])
    total_bonus = rb + bb

    count_three = play.count1 or 0

    def count_flag_partial(keyword):
        return sum(1 for h in hits if h.flag and keyword in h.flag)

    count_a2 = count_flag_partial("リーチ目役 A2")
    count_d2 = count_flag_partial("リーチ目役 D2")
    count_g2 = count_flag_partial("リーチ目役 G2")
    count_t2 = count_flag_partial("リーチ目役 T2")
    count_t3 = count_flag_partial("リーチ目役 T3")
    count_reach = count_a2 + count_d2 + count_g2 + count_t2 + count_t3

    def make_row(label, count):
        prob = f"1/{round(total_games / count, 1)}" if count > 0 else "-"
        return {"label": label, "count": count, "prob": prob}

    rows = [
        make_row("ボーナス合算", total_bonus),
        make_row("RB", rb),
        make_row("３枚役", count_three),
        make_row("リーチ目役合算", count_reach),
        make_row("┗ A2", count_a2),
        make_row("┗ D2", count_d2),
        make_row("┗ G2", count_g2),
        make_row("┗ T2", count_t2),
        make_row("┗ T3", count_t3),
    ]

    # ✅ RB中の設定示唆（text_1）を集計・確率化
    def count_hint(hint_label):
        return sum(1 for h in hits if h.bonus_type == "RB" and h.text_1 == hint_label)

    def make_hint_row(count):
        if rb == 0:
            return {"count": 0, "prob": "－"}
        return {"count": count, "prob": f"1/{round(rb / count, 1)}"} if count > 0 else {"count": 0, "prob": "－"}

    rbhints = {
        "奇数":   make_hint_row(count_hint("奇数")),
        "偶数":   make_hint_row(count_hint("偶数")),
        "2以上": make_hint_row(count_hint("2以上")),
        "5以上": make_hint_row(count_hint("5以上")),
        "6濃厚": make_hint_row(count_hint("6濃厚")),
    }

    # ✅ 信頼区間の計算
    trust_65, trust_95 = calculate_trust_interval_counts(play, hits)

    # ✅ trust_65/95 から RB示唆系のみ抽出
    def extract_rbhint_trust(trust_all):
        result = {}
        for setting in ["1", "2", "5", "6"]:
            result[setting] = {
                "奇数": trust_all[setting].get("RB示唆_奇数", "-"),
                "偶数": trust_all[setting].get("RB示唆_偶数", "-"),
                "2以上": trust_all[setting].get("RB示唆_2以上", "-"),
                "5以上": trust_all[setting].get("RB示唆_5以上", "-"),
                "6濃厚": trust_all[setting].get("RB示唆_6濃厚", "-"),
            }
        return result

    trust_65_rbhint = extract_rbhint_trust(trust_65)
    trust_95_rbhint = extract_rbhint_trust(trust_95)

    return render_template(
        "disk_up_ultra/analyze.html",
        play=play,
        machine=machine,
        total_games=total_games,
        rows=rows,
        trust_65=trust_65,
        trust_95=trust_95,
        rbhints=rbhints,
        trust_65_rbhint=trust_65_rbhint,
        trust_95_rbhint=trust_95_rbhint,
    )



#信頼区間計算
def calculate_trust_interval_counts(play, hits):
    """
    各設定ごとの信頼区間（65%, 95%）の出現回数レンジと、実測回数に基づく評価スコアを返す。
    """
    from math import floor

    total_games = (play.end_game or 0) - (play.start_game or 0)
    games_three = play.count2 or total_games  # 3枚役用
    rb_count = sum(1 for h in hits if h.bonus_type == "RB")

    # --- 設定別の出現率データ（RB示唆追加） ---
    data_definitions = {
        "ボーナス合算": {1: 1/181.8, 2: 1/178.2, 5: 1/162.3, 6: 1/146.5},
        "RB":          {1: 1/495.3, 2: 1/477.2, 5: 1/398.6, 6: 1/334.1},
        "３枚役":       {1: 1/13.7,  2: 1/13.4,  5: 1/12.9,  6: 1/12.6},
        "合算":        {1: 1/624.2, 2: 1/595.8, 5: 1/478.4, 6: 1/383.3},
        "A2":          {1: 1/16384.0, 2: 1/13107.2, 5: 1/8192.0, 6: 1/5461.3},
        "D2":          {1: 1/2340.6,  2: 1/2259.9,  5: 1/1820.4,  6: 1/1560.4},
        "G2":          {1: 1/3276.8,  2: 1/3120.8,  5: 1/2730.7,  6: 1/2340.6},
        "T2":          {1: 1/1337.5,  2: 1/1310.7,  5: 1/1074.4,  6: 1/851.1},
        "T3":          {1: 1/16384.0, 2: 1/13107.2, 5: 1/8192.0, 6: 1/5461.3},
        # ⬇ 追加：設定示唆のRB出現率
        "RB示唆_奇数":   {1: 1/1.82,  2: 1/2.22,  5: 1/1.74,   6: 1/2.17},
        "RB示唆_偶数":   {1: 1/2.22,  2: 1/1.86,  5: 1/2.53,   6: 1/2.00},
        "RB示唆_2以上": {1: None,   2: 1/90.91, 5: 1/49.50, 6: 1/49.50},
        "RB示唆_5以上": {1: None,   2: None,    5: 1/108.70, 6: 1/108.70},
        "RB示唆_6濃厚": {1: None,   2: None,    5: None,     6: 1/108.70},
    }

    # --- 実測値カウント ---
    actual_counts = {
        "ボーナス合算": sum(1 for h in hits if h.bonus_type in ["赤BB", "白BB", "黒BB", "異色BB", "RB"]),
        "RB":          rb_count,
        "３枚役":       play.count1 or 0,
        "A2":          sum(1 for h in hits if h.flag and "リーチ目役 A2" in h.flag),
        "D2":          sum(1 for h in hits if h.flag and "リーチ目役 D2" in h.flag),
        "G2":          sum(1 for h in hits if h.flag and "リーチ目役 G2" in h.flag),
        "T2":          sum(1 for h in hits if h.flag and "リーチ目役 T2" in h.flag),
        "T3":          sum(1 for h in hits if h.flag and "リーチ目役 T3" in h.flag),
        # ⬇ 追加：text_1からカウント
        "RB示唆_奇数":   sum(1 for h in hits if h.bonus_type == "RB" and h.text_1 == "奇数"),
        "RB示唆_偶数":   sum(1 for h in hits if h.bonus_type == "RB" and h.text_1 == "偶数"),
        "RB示唆_2以上": sum(1 for h in hits if h.bonus_type == "RB" and h.text_1 == "2以上"),
        "RB示唆_5以上": sum(1 for h in hits if h.bonus_type == "RB" and h.text_1 == "5以上"),
        "RB示唆_6濃厚": sum(1 for h in hits if h.bonus_type == "RB" and h.text_1 == "6濃厚"),
    }
    actual_counts["合算"] = (
        actual_counts["A2"] +
        actual_counts["D2"] +
        actual_counts["G2"] +
        actual_counts["T2"] +
        actual_counts["T3"]
    )

    # --- 信頼区間の補助関数 ---
    def get_range(probability, trials):
        if probability is None or trials == 0:
            return {"65": (0, 0), "95": (0, 0), "expected": 0}
        expected = trials * probability
        delta65 = expected * 0.2
        delta95 = expected * 0.4
        return {
            "65": (floor(expected - delta65), floor(expected + delta65)),
            "95": (floor(expected - delta95), floor(expected + delta95)),
            "expected": floor(expected)
        }

    def evaluate(actual, low, high):
        if high <= low:
            return 50
        score = round(100 * (actual - low) / (high - low))
        return max(0, min(100, score))

    trust_65 = {}
    trust_95 = {}

    for setting in [1, 2, 5, 6]:
        s_key = str(setting)
        trust_65[s_key] = {}
        trust_95[s_key] = {}

        for key, probs in data_definitions.items():
            prob = probs.get(setting)
            # 無効なデータはスキップ（例：設定1に2以上示唆なし）
            if prob is None:
                trust_65[s_key][key] = "-"
                trust_95[s_key][key] = "-"
                continue

            games = games_three if key == "３枚役" else (rb_count if key.startswith("RB示唆") else total_games)
            rng = get_range(prob, games)
            actual = actual_counts.get(key, 0)

            low65, high65 = rng["65"]
            low95, high95 = rng["95"]

            trust_65[s_key][key] = f"{low65}〜{high65}（{evaluate(actual, low65, high65)}）"
            trust_95[s_key][key] = f"{low95}〜{high95}（{evaluate(actual, low95, high95)}）"

    return trust_65, trust_95



# 設定示唆の更新処理
@disk_up_ultra_bp.route("/update-text-1/<int:hit_id>", methods=["POST"], endpoint="update_text_1")
def update_text_1(hit_id):
    hit = SlotHit.query.get(hit_id)
    if not hit:
        abort(404)

    new_text = request.form.get("text_1")
    hit.text_1 = new_text or None
    db.session.commit()

    return redirect(url_for("disk_up_ultra.play_detail", slot_play_id=hit.slot_play_id))



# 集計処理
from models import SlotHit
from collections import defaultdict

# フラグ一覧（全27種）
FLAGS = [
    "リーチ目役 A1", "リーチ目役 A2",
    "リーチ目役 B1", "リーチ目役 B2", "リーチ目役 B3",
    "リーチ目役 C1", "リーチ目役 C2", "リーチ目役 C3",
    "リーチ目役 D1", "リーチ目役 D2",
    "リーチ目役 E",
    "リーチ目役 F",
    "リーチ目役 G1", "リーチ目役 G2",
    "リーチ目役 T1", "リーチ目役 T2", "リーチ目役 T3",
    "ハズレ目 A",
    "リプレイ B",
    "3枚役 C1", "3枚役 C2",
    "チェリー D1", "チェリー D2",
    "スイカA E1", "スイカB E2"
]

BB_TYPES = {"黒BB", "赤BB", "白BB", "異色BB"}
RB_TYPES = {"RB"}

def format_rate(count, total_games):
    if count == 0 or total_games == 0:
        return "–"
    rate = total_games / count
    return f"1/{rate:.1f}"

def aggregate(slot_plays):
    # 総ゲーム数・差枚数
    total_games = sum(p.end_game - p.start_game for p in slot_plays)
    total_difference = sum(p.difference or 0 for p in slot_plays)

    play_ids = [p.id for p in slot_plays]
    if not play_ids:
        return {
            "total_games": 0,
            "total_difference": 0,
            "total_bb": 0,
            "total_bb_rate": "–",
            "total_rb": 0,
            "total_rb_rate": "–",
            "flags": [],
            "count_plays": 0
        }

    # SlotHitの取得
    hits = SlotHit.query.filter(SlotHit.slot_play_id.in_(play_ids)).all()

    # フラグごとのBB/RBカウント初期化
    flag_summary = {flag: {"bb": 0, "rb": 0} for flag in FLAGS}
    total_bb = 0
    total_rb = 0

    for hit in hits:
        if hit.bonus_type in BB_TYPES:
            total_bb += 1
            if hit.flag in flag_summary:
                flag_summary[hit.flag]["bb"] += 1
        elif hit.bonus_type in RB_TYPES:
            total_rb += 1
            if hit.flag in flag_summary:
                flag_summary[hit.flag]["rb"] += 1

    result = {
        "total_games": total_games,
        "total_difference": total_difference,
        "total_bb": total_bb,
        "total_bb_rate": format_rate(total_bb, total_games),
        "total_rb": total_rb,
        "total_rb_rate": format_rate(total_rb, total_games),
        "flags": [],
        "count_plays": len(slot_plays)
    }

    for flag in FLAGS:
        bb_count = flag_summary[flag]["bb"]
        rb_count = flag_summary[flag]["rb"]
        result["flags"].append({
            "name": flag,
            "bb_count": bb_count,
            "bb_rate": format_rate(bb_count, total_games),
            "rb_count": rb_count,
            "rb_rate": format_rate(rb_count, total_games),
        })

    return result
