# views/index.py
from flask import Blueprint, render_template, request, redirect, url_for
from models import db, SlotPlay, SlotMachine, SlotHit
from datetime import datetime

top_bp = Blueprint("top", __name__)

@top_bp.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        date = request.form.get("date")
        username = request.form.get("user_name")
        slot_machine_id = int(request.form.get("machine_id"))
        start_game = int(request.form.get("start_game", 0))  # ← 追加

        new_play = SlotPlay(
            date=date,
            username=username,
            slot_machine_id=slot_machine_id,
            start_game=start_game,  # ← ここに反映
            end_game=start_game     # ← 初期値として同じ値で登録
        )
        db.session.add(new_play)
        db.session.commit()
        return redirect(url_for("top.index"))

    plays = db.session.query(SlotPlay, SlotMachine)\
        .outerjoin(SlotMachine, SlotPlay.slot_machine_id == SlotMachine.id)\
        .order_by(SlotPlay.date.desc())\
        .all()

    machines = SlotMachine.query.all()

    return render_template("slot/index.html", plays=plays, machines=machines)

@top_bp.route("/delete/<int:slot_play_id>", methods=["POST"])
def delete_play(slot_play_id):
    play = SlotPlay.query.get_or_404(slot_play_id)
    SlotHit.query.filter_by(slot_play_id=slot_play_id).delete()
    db.session.delete(play)
    db.session.commit()
    return redirect(url_for("top.index"))


@top_bp.route("/update_play/<int:slot_play_id>", methods=["POST"])
def update_play(slot_play_id):
    play = SlotPlay.query.get_or_404(slot_play_id)

    shop_name = request.form.get("shop_name")
    difference = request.form.get("difference")

    if shop_name is not None:
        play.shop_name = shop_name

    if difference is not None:
        try:
            play.difference = int(difference)
        except ValueError:
            play.difference = None  # またはエラーハンドリング

    db.session.commit()
    return redirect(url_for("top.index"))


@top_bp.route("/aggregate", methods=["GET"])
def aggregate():
    # 機種一覧（id, name のタプル形式）
    machines = [(m.id, m.name) for m in SlotMachine.query.order_by(SlotMachine.name).all()]

    # 店舗名一覧（非nullで重複なし）
    shops = [s[0] for s in db.session.query(SlotPlay.shop_name).distinct().filter(SlotPlay.shop_name.isnot(None)).all()]

    # ユーザー名一覧（重複なし）
    usernames = [u[0] for u in db.session.query(SlotPlay.username).distinct().filter(SlotPlay.username.isnot(None)).all()]

    # 日付から年・月抽出
    all_dates = db.session.query(SlotPlay.date).distinct().all()
    years = sorted({d[0].split("-")[0] for d in all_dates if d[0]})
    months = sorted({d[0].split("-")[1] for d in all_dates if d[0]})

    # -------------------------------
    # 集計処理部分
    # -------------------------------
    result = None
    debug_info = None  # ← デバッグ用変数を初期化

    selected_machine_id = request.args.get("machine_id", type=int)  # ← 修正ポイント
    selected_year = request.args.get("year")
    selected_month = request.args.get("month")
    selected_shop = request.args.get("shop")
    selected_user = request.args.get("username")

    if selected_machine_id:
        machine = SlotMachine.query.get(selected_machine_id)

        # 遊戯データをフィルターして取得
        query = SlotPlay.query.filter(SlotPlay.slot_machine_id == selected_machine_id)
        if selected_year:
            query = query.filter(SlotPlay.date.like(f"{selected_year}-%"))
        if selected_month:
            query = query.filter(SlotPlay.date.like(f"%-{selected_month.zfill(2)}-%"))
        if selected_shop:
            query = query.filter(SlotPlay.shop_name == selected_shop)
        if selected_user:
            query = query.filter(SlotPlay.username == selected_user)

        slot_plays = query.all()

        # 🐛 デバッグ情報にslot_playsの中身を渡す
        debug_info = {
            "selected_machine_id": selected_machine_id,
            "slot_plays_count": len(slot_plays),
            "slot_plays": [
                {
                    "id": p.id,
                    "date": p.date,
                    "username": p.username,
                    "machine_id": p.slot_machine_id
                } for p in slot_plays
            ]
        }

        if machine:
            try:
                import importlib
                # 機種名とモジュール名を明示的にマッピング
                module_map = {
                    "ディスクアップ ULTRAREMIX": "disk_up_ultra",
                    # 他機種を追加可能
                }
                module_name = module_map.get(machine.name)
                if not module_name:
                    result = f"未対応機種: {machine.name}"
                else:
                    module = importlib.import_module(f"machines.{module_name}")
                    result = module.aggregate(slot_plays)
            except ModuleNotFoundError:
                result = f"未対応機種: {machine.name}"
            except Exception as e:
                result = f"エラー: {str(e)}"

    # -------------------------------

    return render_template(
        "slot/aggregate.html",
        machines=machines,
        shops=shops,
        usernames=usernames,
        years=years,
        months=months,
        result=result,
        debug_info=debug_info  # ← テンプレートに渡す
    )
