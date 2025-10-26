import streamlit as st
from typing import List, Dict
from pictogram_search import (
    get_similar_pictos,
    load_picto_index,
    split_into_short_chunks,
)

# --------------------------
# ページ基本設定
# --------------------------
st.set_page_config(
    page_title="Text2Picto",
    page_icon="🖼️",
    layout="wide"
)

# --------------------------
# ヘッダー / 説明
# --------------------------
st.markdown("""
# Text2Picto 🧠➡🖼
文章をやさしい絵に変換するサポートツール（試作版）

- 入力したテキストの内容を、意味の近いピクトグラムに変換します
- 医療・教育・支援現場などで、言葉での理解や表現が難しい人への支援を想定
""")

# --------------------------
# サイドバー: オプション
# --------------------------
st.sidebar.header("オプション")

granularity = st.sidebar.radio(
    "どの単位でピクト化する？",
    ["文ごと", "短い区切り（おすすめ）", "単語ごと"],
    help="""
『文ごと』：句点などで区切って1文＝1枚  
『短い区切り』：日本語の文節っぽいまとまりで分割（おすすめ）  
『単語ごと』：細かく単語レベルで分ける
"""
)

show_debug = st.sidebar.checkbox("デバッグ情報を表示", value=False)

st.sidebar.markdown("---")
st.sidebar.caption("© Text2Picto prototype")

# --------------------------
# 入力フォーム
# --------------------------
default_text = "お茶をのみましょう。それから病院にいきます。"
user_text = st.text_area(
    "伝えたい内容（日本語でもやさしい日本語でもOK）",
    value=default_text,
    height=120,
    help="例：ごはんをたべてからおくすりをのもう"
)

# --------------------------
# セッション管理
# --------------------------
if "picto_index" not in st.session_state:
    st.session_state.picto_index = load_picto_index()

run = st.button("ピクトグラムにする 🎨")

# --------------------------
# 簡易テキスト分割（バックアップ用）
# --------------------------
import re

def split_into_sentences(text: str) -> List[str]:
    parts = re.split(r"[。！？!?]", text)
    return [p.strip() for p in parts if p.strip()]

def split_into_words(text: str) -> List[str]:
    parts = re.split(r"[、。・,.\s]+", text)
    return [p.strip() for p in parts if p.strip()]

def make_units(text: str, mode: str) -> List[str]:
    """ユーザー選択に応じて分割方式を切り替える"""
    if mode == "文ごと":
        return split_into_sentences(text)
    elif mode == "短い区切り（おすすめ）":
        return split_into_short_chunks(text)
    else:
        return split_into_words(text)

def is_prohibited(text: str) -> bool:
    """
    この文は「～してはいけません」「だめです」などの禁止表現を含むか？
    """
    patterns = [
        "てはいけません",
        "てはだめ",
        "てはダメ",
        "だめです",
        "ダメです",
        "禁止",
        "いけません",
        "やめて",
        "やめなさい",
        "しないでください",
        "しちゃだめ",
        "しちゃダメ",
    ]
    return any(pat in text for pat in patterns)

# --------------------------
# ピクトブロック描画
# --------------------------
def render_picto_block(token: str, picto_info: Dict[str, str], score: float, show_debug: bool):
    """1つのテキスト単位を画像と共に表示"""
    with st.container(border=True):
        cols = st.columns([1, 2])
        with cols[0]:
            if picto_info.get("path"):
                st.image(picto_info["path"], use_container_width=True)
            else:
                st.markdown("🖼 (なし)")
        with cols[1]:
            st.markdown(f"**{token}**")
            st.markdown(f"- 候補: `{picto_info.get('label', '不明')}`")
            st.markdown(f"- 類似度: {score:.2f}")
            if not picto_info.get("path"):
                st.markdown(":warning: 近いピクトグラムが見つからなかったので、生成候補です。")
            if show_debug:
                st.code(str(picto_info), language="json")

# --------------------------
# メイン処理
# --------------------------
if run and user_text.strip():
    st.markdown("## 結果")

    units = make_units(user_text, granularity)

    if not units:
        st.info("テキストがありません。")
    else:
        for u in units:
            # 1) ベクトル検索でいちばん近いピクト（例：ポテト、病院 など）
            results = get_similar_pictos(
                query_text=u,
                picto_index=st.session_state.picto_index,
                top_k=1
            )

            for top_picto, sim_score in results:
                render_picto_block(
                    token=u,
                    picto_info=top_picto,
                    score=sim_score,
                    show_debug=show_debug
                )

            # 2) 禁止表現なら、禁止ピクトも必ず追加で表示
            if is_prohibited(u):
                ban_entry = next(
                    (p for p in st.session_state.picto_index if p["label"] == "禁止"),
                    None
                )
                if ban_entry is not None:
                    render_picto_block(
                        token="（やってはだめ）",
                        picto_info=ban_entry,
                        score=1.00,
                        show_debug=show_debug
                    )

    st.markdown("---")
    st.caption("※これは試作版です。医療・教育などの実務利用では必ず人が内容を確認してください。")

else:
    st.markdown("👇 テキストを入れて「ピクトグラムにする 🎨」を押してください。")

# --------------------------
# 開発メモ
# --------------------------
with st.expander("開発メモ（プロトタイプ段階の仮仕様）"):
    st.markdown("""
- 現在は Sentence-BERT による意味類似度検索を使用  
- fugashi(MeCab系) により、日本語の文を自然な短いまとまりに分割  
- 簡単な禁止ルール（「〜てはいけません」など）で 🚫 を強制表示  
- 今後の予定：
    - AIによるピクト生成機能
    - PDF出力（視覚スケジュールカード）
    - 医療・公共施設で使える語彙セット整備
""")