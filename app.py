import streamlit as st
import re
from typing import List, Dict, Tuple
from pictogram_search import get_similar_pictos, load_picto_index

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

- テキストを入れると、意味の近いピクトグラムを並べます
- 医療現場・学校・飲食店・支援現場などで、
  ことばの理解がむずかしい人／ことばで伝えるのが難しい人へのサポートを想定しています
""")

# サイドバー: オプション
st.sidebar.header("オプション")
granularity = st.sidebar.radio(
    "どの単位でピクト化する？",
    ["文ごと", "単語ごと"],
    help="『文ごと』＝1文に1枚のイメージ候補 / 『単語ごと』＝できるだけ細かく並べる"
)

show_debug = st.sidebar.checkbox(
    "デバッグ情報を表示（マッチした単語など）",
    value=False
)

st.sidebar.markdown("---")
st.sidebar.markdown("© Text2Picto prototype")

# --------------------------
# 入力フォーム
# --------------------------
default_text = "お茶をのみましょう。それから病院にいきます。"
user_text = st.text_area(
    "伝えたい内容（日本語でもやさしい日本語でもOK）",
    value=default_text,
    height=120,
    help="例: ごはんをたべてからおくすりをのもう"
)

if "picto_index" not in st.session_state:
    st.session_state.picto_index = load_picto_index()

# 実行ボタン
run = st.button("ピクトグラムにする 🎨")

# --------------------------
# テキストの分割ロジック
# --------------------------
def split_into_sentences(text: str) -> List[str]:
    # 。！？で区切る（ゆるめ）
    parts = re.split(r"[。！？!?]", text)
    parts = [p.strip() for p in parts if p.strip() != ""]
    return parts

def split_into_words(text: str) -> List[str]:
    # 超ざっくり：助詞とかもそのまま出す
    # 将来的には形態素解析(MeCabなど)を入れる
    # いまは空白と句読点で分ける
    parts = re.split(r"[、。・,.\s]+", text)
    parts = [p.strip() for p in parts if p.strip() != ""]
    return parts

def make_units(text: str, mode: str) -> List[str]:
    if mode == "文ごと":
        return split_into_sentences(text)
    else:
        return split_into_words(text)

# --------------------------
# 表示用の1ブロック描画
# --------------------------
def render_picto_block(
    token: str,
    picto_info: Dict[str, str],
    score: float,
    show_debug: bool
):
    """
    token: 元のテキスト単位（文 or 単語）
    picto_info: {"path": "...", "label": "..."} を想定
    score: 類似度スコア(0-1想定)
    """
    with st.container(border=True):
        cols = st.columns([1,2])
        with cols[0]:
            if picto_info.get("path"):
                st.image(picto_info["path"], use_container_width=True)
            else:
                st.markdown("🖼 (なし)")
        with cols[1]:
            st.markdown(f"**{token}**")
            # ラベル（例えば「飲む」「休憩」などの意味ラベル）
            st.markdown(f"- 候補: `{picto_info.get('label', '不明')}`")
            # スコア
            st.markdown(f"- 類似度: {score:.2f}")
            # 画像が無いときのメッセージ
            if not picto_info.get("path"):
                st.markdown(
                    ":warning: 近いピクトグラムが見つからなかったので、生成候補です（AIで後から作る想定）"
                )
            if show_debug:
                st.code(str(picto_info), language="json")

# --------------------------
# 実行
# --------------------------
if run and user_text.strip():
    st.markdown("## 結果")
    # Step1: 単位に分ける
    units = make_units(user_text, granularity)

    if len(units) == 0:
        st.info("テキストがありません。")
    else:
        # Step2: 各単位に対して、一番近いピクトを検索
        for u in units:
            top_picto, sim_score = get_similar_pictos(
                query_text=u,
                picto_index=st.session_state.picto_index,
                top_k=1
            )[0]  # [(info, score), ...] を想定

            render_picto_block(
                token=u,
                picto_info=top_picto,
                score=sim_score,
                show_debug=show_debug
            )

    st.markdown("---")
    st.caption("※これは試作です。医療・介護・教育など実務利用では必ず人が内容を確認してください。")
else:
    st.markdown("👇 テキストを入れて「ピクトグラムにする 🎨」を押してください。")


# --------------------------
# フッター
# --------------------------
with st.expander("開発メモ（プロトタイプ段階の仮仕様）"):
    st.markdown(
        """
- まずは社内・関係者向けPoCです
- 説明したい内容をそのまま打つだけで、視覚支援カードが並ぶイメージ
- 画像は今はローカルのサンプルを使っています
- 将来的には：
    - 医療・公共施設向けの「よくある指示」セットを事前に用意
    - ピクトが無いときは生成AIで簡易イラストを自動生成
    - 「これはOK」「これは使わないで」みたいな人間レビューを記録
    - 利用ログから、よく使う場面を優先して改善
        """
    )