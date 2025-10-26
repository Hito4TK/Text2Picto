from typing import List, Dict, Tuple
import math

# picto_index のイメージ:
# [
#   {
#     "label": "飲む",
#     "keywords": ["飲む", "のみます", "おちゃ", "お茶をのむ", "水をのむ", "drink", "take a drink"],
#     "path": "data/pictos/drink.png"
#   },
#   {
#     "label": "病院",
#     "keywords": ["びょういん", "病院", "いしゃ", "doctor", "hospital", "診察"],
#     "path": "data/pictos/hospital.png"
#   },
#   ...
# ]

def load_picto_index() -> List[Dict[str, str]]:
    # 本当はJSONなどからロードする
    # ここではハードコードの例
    return [
        {
            "label": "飲む",
            "keywords": ["飲む", "のみます", "おちゃ", "お茶", "水をのむ", "drink", "のもう"],
            "path": "data/pictos/drink.png"
        },
        {
            "label": "病院",
            "keywords": ["病院", "びょういん", "いしゃ", "先生にみてもらう", "hospital", "診察"],
            "path": "data/pictos/hospital.png"
        },
        {
            "label": "待つ",
            "keywords": ["まつ", "まってください", "待って", "待機", "待合室", "待合しつ", "wait"],
            "path": "data/pictos/wait.png"
        },
        {
            "label": "ごはん/食べる",
            "keywords": ["ごはん", "たべる", "ごはんをたべる", "ご飯", "食事", "ごはんの時間", "eat", "meal"],
            "path": "data/pictos/eat.png"
        },
        {
            "label": "おくすり",
            "keywords": ["薬", "くすり", "おくすり", "medicine", "薬をのむ", "おくすりのむ"],
            "path": "data/pictos/medicine.png"
        },
    ]

def simple_similarity(a: str, b: str) -> float:
    """
    超プリミティブな類似度:
    - 部分一致の長さベース
    - 後で埋め込みに差し替える
    """
    a = a.lower()
    b = b.lower()
    # 共通部分長っぽいものを取る
    score = 0.0
    for token in [a, b]:
        # ざっくり: aがbに含まれる、bがaに含まれる で加点
        if a in b or b in a:
            score = 1.0
    # ちょい工夫: 文字の重なり率
    overlap = len(set(a) & set(b))
    denom = max(len(set(a) | set(b)), 1)
    score = max(score, overlap / denom)
    return score

def score_against_picto(query: str, picto_entry: Dict[str, str]) -> float:
    # query と picto_entry["keywords"] の最大値をそのピクトのスコアに
    return max(simple_similarity(query, kw) for kw in picto_entry["keywords"])

def get_similar_pictos(
    query_text: str,
    picto_index: List[Dict[str, str]],
    top_k: int = 1
) -> List[Tuple[Dict[str, str], float]]:
    """
    query_text にいちばん近いピクトグラム候補を返す
    return: [(picto_entry, score), ...] スコア高い順
    """
    scored = []
    for entry in picto_index:
        s = score_against_picto(query_text, entry)
        scored.append((entry, s))

    # スコアでソート
    scored.sort(key=lambda x: x[1], reverse=True)

    # top_k件だけ返す。スコアがめちゃ低い(0.0付近)なら
    # pathをNoneにして「生成候補」にするなどもできる
    out = []
    for (entry, s) in scored[:top_k]:
        candidate = dict(entry)  # copy
        if s < 0.2:
            # 閾値より低い → 既存ピクトなし扱い
            candidate["path"] = None
            candidate["label"] = "生成候補（まだ登録なし）"
        out.append((candidate, s))
    return out