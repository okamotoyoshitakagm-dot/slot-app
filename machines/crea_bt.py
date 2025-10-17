# /root/slot-app/machines/crea_bt.py
from flask import Blueprint, render_template, request, redirect, url_for, abort
from models import SlotPlay, SlotMachine, SlotHit
from extensions import db

# URLは /slot/crea-bt/...
crea_bt_bp = Blueprint("crea_bt", __name__, url_prefix="/slot/crea-bt")

# トップ（簡易）
@crea_bt_bp.route("/")
def top():
    return "クレアの秘宝伝 BT トップページ（仮）"

# プレイ詳細
@crea_bt_bp.route("/play/<int:slot_play_id>", methods=["GET", "POST"], endpoint="play_detail")
def play_detail(slot_play_id: int):
    play = SlotPlay.query.get(slot_play_id)
    if not play:
        abort(404)

    machine = SlotMachine.query.get(play.slot_machine_id)
    # URL直打ち対策：対象機種のみ許可
    if not machine or machine.name != "クレアの秘宝伝 BT":
        abort(404, description="未対応の機種です")

    # POST：基本更新（終了G／店舗／差枚）
    if request.method == "POST":
        end_game = request.form.get("end_game")
        shop_name = request.form.get("shop_name")
        difference = request.form.get("difference")

        if end_game not in (None, ""):
            try:
                play.end_game = int(end_game)
            except ValueError:
                pass

        play.shop_name = shop_name or None

        if difference not in (None, ""):
            try:
                play.difference = int(difference)
            except ValueError:
                pass

        db.session.commit()
        return redirect(url_for("crea_bt.play_detail", slot_play_id=slot_play_id))

    # GET：表示用データ
    hits = (
        SlotHit.query
        .filter_by(slot_play_id=slot_play_id)
        .order_by(SlotHit.hit_game, SlotHit.id)
        .all()
    )

    total_games = None
    if play.start_game is not None and play.end_game is not None and play.end_game >= play.start_game:
        total_games = play.end_game - play.start_game

    return render_template(
        "slot/crea_bt_detail.html",  # 最小テンプレ（先に作っておく）
        play=play,
        machine=machine,
        hits=hits,
        total_games=total_games,
    )

# 当たり追加
@crea_bt_bp.route("/add-hit/<int:slot_play_id>", methods=["POST"], endpoint="add_hit")
def add_hit(slot_play_id: int):
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
                flag=flag or None,
            )
            db.session.add(new_hit)
            db.session.commit()
        except ValueError:
            pass

    return redirect(url_for("crea_bt.play_detail", slot_play_id=slot_play_id))

# 当たり削除
@crea_bt_bp.route("/delete-hit/<int:hit_id>", methods=["POST"], endpoint="delete_hit")
def delete_hit(hit_id: int):
    hit = SlotHit.query.get(hit_id)
    if not hit:
        abort(404)

    slot_play_id = hit.slot_play_id
    db.session.delete(hit)
    db.session.commit()
    return redirect(url_for("crea_bt.play_detail", slot_play_id=slot_play_id))
