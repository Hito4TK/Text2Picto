from typing import List, Dict, Tuple
from sentence_transformers import SentenceTransformer, util
import fugashi

# -------------------------
# Sentence-BERT モデル読込
# -------------------------
model = SentenceTransformer("sonoisa/sentence-bert-base-ja-mean-tokens")
tagger = fugashi.Tagger()

# -------------------------
# ピクト辞書
# -------------------------
def load_picto_index():
    return [
        {"label": "飲む", "keywords": ["飲む", "お茶", "水をのむ", "drink"], "path": "data/pictos/drink.png"},
        {"label": "病院", "keywords": ["病院", "いしゃ", "診察", "hospital"], "path": "data/pictos/hospital.png"},
        {"label": "待つ", "keywords": ["待つ", "待機", "wait"], "path": "data/pictos/wait.png"},
        {"label": "食べる", "keywords": ["ごはん", "たべる", "食事", "eat"], "path": "data/pictos/eat.png"},
        {"label": "おくすり", "keywords": ["薬", "おくすり", "medicine"], "path": "data/pictos/medicine.png"},
        {"label": "禁止", "keywords": ["禁止", "だめ", "stop", "do not"], "path": "data/pictos/do_not.png"},
        {"label": "ポテト", "keywords": ["ポテト", "じゃがいも", "フライドポテト"], "path": "data/pictos/french_fried_potato.png"},
    ]

# -------------------------
# 文分割（fugashi）
# -------------------------
def split_into_short_chunks(text: str) -> List[str]:
    """
    文を自然な短文単位に分割する（fugashi版・最終調整）
    """
    chunks = []
    buf = ""
    for word in tagger(text):
        surface = word.surface
        pos = word.feature.pos1

        # 句読点で文を区切る
        if surface in ["。", "！", "？"]:
            if buf.strip():
                chunks.append(buf.strip("。、 "))
            buf = ""
            continue

        buf += surface

        # 助詞・助動詞などで区切るが、短すぎる場合は保留
        if pos in ["助詞", "助動詞", "終助詞"] and len(buf) >= 6:
            # 「に」＋動詞 のような構造を後で結合しやすいよう残す
            chunks.append(buf.strip("。、 "))
            buf = ""

    # 残りを追加
    if buf.strip():
        chunks.append(buf.strip("。、 "))

    # 空要素除去
    chunks = [c for c in chunks if c and not all(ch in "。、！？" for ch in c)]

    # 「に」「を」「が」「で」など文末助詞で終わっている場合、次と結合
    merged = []
    for chunk in chunks:
        if merged and any(merged[-1].endswith(p) for p in ["に", "を", "が", "で"]):
            merged[-1] += chunk
        else:
            merged.append(chunk)

    return merged

# -------------------------
# 意味ベース類似度検索
# -------------------------
def embed(text: str):
    return model.encode(text, convert_to_tensor=True)

def get_similar_pictos(query_text: str, picto_index: List[Dict[str, str]], top_k: int = 2):
    """
    query_text に意味的に近いピクトグラムを複数返す。
    return: [(picto_entry, score), ...] スコア高い順
    """
    query_vec = embed(query_text)
    scored = []
    for entry in picto_index:
        kw_vecs = [embed(k) for k in entry["keywords"]]
        picto_vec = sum(kw_vecs) / len(kw_vecs)
        score = float(util.cos_sim(query_vec, picto_vec))
        scored.append((entry, score))

    # スコア降順
    scored.sort(key=lambda x: x[1], reverse=True)

    # 上位 top_k 件を返す
    out = []
    for (entry, s) in scored[:top_k]:
        candidate = dict(entry)
        if s < 0.35:
            candidate["path"] = None
            candidate["label"] = "生成候補（まだ登録なし）"
        out.append((candidate, s))
    return out