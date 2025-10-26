import streamlit as st

st.set_page_config(page_title="Text2Picto", page_icon="🖼", layout="wide")

st.title("Text2Picto 🖼")
st.write("テキストから、わかりやすいピクトグラム表現を提案するアプリ（試作版）")

user_text = st.text_area("伝えたい内容を入力してください", height=120)

if st.button("ピクトグラム案を表示"):
    if not user_text.strip():
        st.warning("まず文章を入力してください。")
    else:
        st.success("このあとはピクトグラム候補を表示する予定です。今はダミーです。")

        cols = st.columns(3)
        demo_icons = ["🚫", "🧼", "🍽", "🔇", "🪥", "🛑"]
        for i, icon in enumerate(demo_icons):
            with cols[i % 3]:
                st.markdown(
                    f"""
                    <div style="font-size:48px;text-align:center;border:1px solid #ccc;border-radius:8px;padding:16px;margin-bottom:12px;">
                        {icon}
                    </div>
                    <div style="text-align:center;color:#555;">
                        ラベル例
                    </div>
                    """,
                    unsafe_allow_html=True,
                )