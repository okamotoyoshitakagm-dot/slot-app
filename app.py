from flask import Flask
from extensions import db, migrate
from models import SlotMachine, SlotPlay, SlotHit
from views.index import top_bp
from machines.disk_up_ultra import disk_up_ultra_bp
from machines.crea_bt import crea_bt_bp  # ← ★ 追加
import os

# アプリ初期化
app = Flask(__name__)

# データベースパス（絶対パス指定）
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'slot.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# DB初期化
db.init_app(app)
migrate.init_app(app, db)

# 🔽 migrate がモデルを検出できるように明示的に import
from models import *

# 🔽 Blueprint を登録
app.register_blueprint(top_bp, url_prefix='/slot')
app.register_blueprint(disk_up_ultra_bp)
app.register_blueprint(crea_bt_bp)  # ← ★ 追加

# ✅ トップルートは Blueprint 側で管理するため不要
# @app.route("/")
# def root_index():
#     return render_template("index.html")

if __name__ == "__main__":
    app.run()
