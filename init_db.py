from app import app
from extensions import db

with app.app_context():
    db.create_all()
    print("✅ DB テーブル作成完了")
