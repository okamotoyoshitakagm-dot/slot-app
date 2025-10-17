from extensions import db

class SlotMachine(db.Model):
    __tablename__ = 'slot_machines'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    # SlotPlaysとのリレーション
    plays = db.relationship('SlotPlay', backref='machine', lazy=True)


class SlotPlay(db.Model):
    __tablename__ = 'slot_plays'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(10), nullable=False)  # 'YYYY-MM-DD'形式
    username = db.Column(db.String(100), nullable=False)
    slot_machine_id = db.Column(db.Integer, db.ForeignKey('slot_machines.id'), nullable=False)
    start_game = db.Column(db.Integer, nullable=False)
    end_game = db.Column(db.Integer, nullable=False)

    # 汎用カウント（用途未定）
    count1 = db.Column(db.Integer, nullable=True)
    count2 = db.Column(db.Integer, nullable=True)
    count3 = db.Column(db.Integer, nullable=True)
    count4 = db.Column(db.Integer, nullable=True)
    count5 = db.Column(db.Integer, nullable=True)
    count6 = db.Column(db.Integer, nullable=True)
    count7 = db.Column(db.Integer, nullable=True)
    count8 = db.Column(db.Integer, nullable=True)
    count9 = db.Column(db.Integer, nullable=True)
    count10 = db.Column(db.Integer, nullable=True)

    # 自由テキスト（用途未定）
    text_1 = db.Column(db.String(255), nullable=True)
    text_2 = db.Column(db.String(255), nullable=True)
    text_3 = db.Column(db.String(255), nullable=True)
    text_4 = db.Column(db.String(255), nullable=True)
    text_5 = db.Column(db.String(255), nullable=True)
    text_6 = db.Column(db.String(255), nullable=True)
    text_7 = db.Column(db.String(255), nullable=True)
    text_8 = db.Column(db.String(255), nullable=True)
    text_9 = db.Column(db.String(255), nullable=True)
    text_10 = db.Column(db.String(255), nullable=True)

    shop_name = db.Column(db.String(100), nullable=True)  # 店舗名
    difference = db.Column(db.Integer, nullable=True)     # 差枚数（±対応）


    # SlotHitsとのリレーション
    hits = db.relationship('SlotHit', backref='play', lazy=True)





class SlotHit(db.Model):
    __tablename__ = 'slot_hits'

    id = db.Column(db.Integer, primary_key=True)
    slot_play_id = db.Column(db.Integer, db.ForeignKey('slot_plays.id'), nullable=False)
    hit_game = db.Column(db.Integer, nullable=False)
    bonus_type = db.Column(db.String(50), nullable=False)
    flag = db.Column(db.String(50), nullable=True)

    # 汎用カウント要素（追加分）
    count_1 = db.Column(db.Integer, nullable=True)
    count_2 = db.Column(db.Integer, nullable=True)
    count_3 = db.Column(db.Integer, nullable=True)
    count_4 = db.Column(db.Integer, nullable=True)
    count_5 = db.Column(db.Integer, nullable=True)

    # 汎用テキスト要素（追加分）
    text_1 = db.Column(db.String(255), nullable=True)
    text_2 = db.Column(db.String(255), nullable=True)
    text_3 = db.Column(db.String(255), nullable=True)
    text_4 = db.Column(db.String(255), nullable=True)
    text_5 = db.Column(db.String(255), nullable=True)
