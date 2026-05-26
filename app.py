import streamlit as st
import json
import os

st.set_page_config(
    page_title="3D打印新手指南",
    layout="wide"
)

# ── CSS ───────────────────────────────────────────────────

def inject_css():
    """注入自定义样式：胶囊按钮、字体行距、徽章、图片占位符"""
    st.markdown("""
    <style>
    /* 页面内容居中并限制最大宽度，增加留白 */
    .block-container {
        max-width: 900px;
        padding-top: 3.5rem;
        padding-bottom: 4rem;
    }

    /* 全局行距和字号 */
    p, li { line-height: 1.95 !important; }

    /* 大标题 */
    h1 {
        font-size: 2.2rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.3px;
    }

    /* 搜索框：圆角、内边距放大 */
    div[data-testid="stTextInput"] input {
        border-radius: 10px !important;
        padding: 0.65rem 1rem !important;
        font-size: 1rem !important;
        border: 1.5px solid #DDDDDD !important;
    }

    /* 所有 st.button 变成胶囊形状 */
    div[data-testid="stButton"] > button {
        border-radius: 999px !important;
        border: 1.5px solid #2E86AB !important;
        color: #2E86AB !important;
        background-color: #FFFFFF !important;
        font-size: 0.9rem !important;
        padding: 0.28rem 1.1rem !important;
        font-weight: 500 !important;
        transition: background-color 0.15s ease, color 0.15s ease;
    }
    div[data-testid="stButton"] > button:hover {
        background-color: #2E86AB !important;
        color: #FFFFFF !important;
    }
    div[data-testid="stButton"] > button:active {
        background-color: #236e8a !important;
        color: #FFFFFF !important;
    }

    /* Tab 标签字号 */
    div[data-testid="stTabs"] button[role="tab"] {
        font-size: 0.95rem !important;
        font-weight: 500 !important;
    }

    /* 难度徽章（行内 HTML）*/
    .badge {
        display: inline-block;
        padding: 3px 14px;
        border-radius: 999px;
        font-size: 0.82rem;
        font-weight: 600;
        margin-bottom: 6px;
    }

    /* 图片占位符 */
    .img-placeholder {
        background: #F7F7F8;
        border: 2px dashed #D5D5D5;
        border-radius: 10px;
        padding: 2.5rem 1rem;
        text-align: center;
        color: #BBBBBB;
        font-size: 0.8rem;
        line-height: 1.8;
    }

    /* 详情页正文大字号 */
    .detail-text {
        font-size: 1.08rem;
        line-height: 2.05;
        color: #2A2A2A;
    }

    /* 适合 / 不适合列表颜色 */
    .item-good { color: #1A7A3A; margin: 3px 0; }
    .item-bad  { color: #B03030; margin: 3px 0; }

    /* 分隔线颜色变浅 */
    hr { border-color: #EBEBEB !important; }

    /* 词云条目 */
    .wc-item {
        text-decoration: none !important;
        display: inline-block;
        line-height: 1.2;
        cursor: pointer;
        transition: transform 0.2s ease, text-shadow 0.2s ease;
    }
    .wc-item:hover {
        transform: scale(1.15);
        text-shadow: 2px 6px 18px rgba(0, 0, 0, 0.25);
        text-decoration: none !important;
    }
    </style>
    """, unsafe_allow_html=True)


# ── 数据工具 ───────────────────────────────────────────────

def load_json(file_path):
    """读取 JSON 文件，返回列表或字典"""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def show_image(image_path):
    """显示图片；文件不存在时显示占位符"""
    if os.path.exists(image_path):
        st.image(image_path, use_container_width=True)
    else:
        st.markdown(
            f'<div class="img-placeholder">图片待放置<br>'
            f'<span style="opacity:0.55;font-size:0.72rem">{image_path}</span></div>',
            unsafe_allow_html=True
        )


def filter_terms(terms, keyword):
    """在中文名、英文名、解释里搜索关键词（不分大小写）"""
    if not keyword.strip():
        return terms
    kw = keyword.lower()
    return [
        t for t in terms
        if kw in (t["term_cn"] + t["term_en"] + t["plain_explanation"]).lower()
    ]


def filter_filaments(filaments, keyword):
    """在名称、介绍、适合/不适合字段里搜索关键词"""
    if not keyword.strip():
        return filaments
    kw = keyword.lower()
    return [
        f for f in filaments
        if kw in (
            f["name"] + f["full_name"] + f["plain_intro"]
            + " ".join(f["good_for"]) + " ".join(f["bad_for"])
        ).lower()
    ]


# ── Session State ──────────────────────────────────────────

def init_state():
    """初始化页面导航状态，默认显示首页"""
    if "page" not in st.session_state:
        st.session_state.page = "home"
    if "selected_type" not in st.session_state:
        st.session_state.selected_type = None   # "term" 或 "filament"
    if "selected_id" not in st.session_state:
        st.session_state.selected_id = None


def go_home():
    """跳回首页"""
    st.session_state.page = "home"
    st.session_state.selected_type = None
    st.session_state.selected_id = None


def go_detail(item_type, item_id):
    """跳转到详情页"""
    st.session_state.page = "detail"
    st.session_state.selected_type = item_type
    st.session_state.selected_id = item_id


# ── 首页 ───────────────────────────────────────────────────

def get_word_size(word):
    """字号 1.0 ~ 5.0rem，步长 0.2，由 hash 决定，同一词永远不变"""
    h = abs(hash(word)) % 21          # 0-20
    return round(1.0 + h * 0.2, 1)   # 1.0, 1.2, …, 5.0


def get_word_color(word):
    """深蓝40% / 深灰30% / 暖橙15% / 浅灰15%，用独立 hash 种子避免与大小相关"""
    h = abs(hash(word + "c")) % 20
    if h <= 7:
        return "#1F4E79"   # 深蓝 40%
    elif h <= 13:
        return "#2C2C2C"   # 深灰 30%
    elif h <= 16:
        return "#C25E3F"   # 暖橙 15%
    else:
        return "#999999"   # 浅灰 15%


def get_word_weight(size):
    """根据字号映射字重：大词加粗、小词常规"""
    if size >= 3.5:
        return 800
    elif size >= 2.5:
        return 600
    elif size >= 1.6:
        return 500
    else:
        return 400


def get_word_offset(word):
    """垂直偏移 0 ~ 2.0rem，制造行间参差感，用独立 hash 种子"""
    h = abs(hash(word + "v")) % 21    # 0-20
    return round(h * 0.1, 1)         # 0.0 ~ 2.0rem


def show_word_cloud(items, id_field, label_field, type_name):
    """把列表渲染成印刷海报式词云，点击词条通过 query params 跳转详情页"""
    if not items:
        st.caption("没有匹配的结果。")
        return

    spans = []
    for item in items:
        label   = item[label_field]
        item_id = item[id_field]
        size    = get_word_size(label)
        color   = get_word_color(label)
        weight  = get_word_weight(size)
        offset  = get_word_offset(label)
        spans.append(
            f'<a class="wc-item" '
            f'href="?nav_type={type_name}&nav_id={item_id}" '
            f'style="font-size:{size}rem;color:{color};'
            f'font-weight:{weight};margin-top:{offset}rem;">'
            f'{label}</a>'
        )

    html = (
        '<div style="display:flex;flex-wrap:wrap;'
        'gap:1rem 1.6rem;align-items:flex-start;padding:1.5rem 0 2.5rem 0;">'
        + "".join(spans)
        + "</div>"
    )
    st.markdown(html, unsafe_allow_html=True)


def render_home(terms_data, filaments_data):
    """渲染首页：标题 + 搜索框 + 两 Tab 标签网格"""

    # 标题区
    st.markdown("# 3D 打印新手指南")
    st.markdown(
        '<p style="color:#777;font-size:1.05rem;margin-top:-10px;margin-bottom:1.5rem;">'
        "把 3D 打印的术语简单易懂地讲清楚，专为零基础新手准备。"
        "</p>",
        unsafe_allow_html=True
    )

    # 搜索框
    search_input = st.text_input(
        label="搜索",
        placeholder="搜索词条或耗材，例如：层高、PLA、支撑……",
        label_visibility="collapsed",
        key="search"
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # 两个 Tab
    tab_terms, tab_filaments = st.tabs(["术语词典", "耗材库"])

    with tab_terms:
        filtered = filter_terms(terms_data, search_input)
        st.caption(f"共 {len(filtered)} 个词条  ·  点击名称查看详情")
        st.markdown("<br>", unsafe_allow_html=True)
        show_word_cloud(filtered, id_field="id", label_field="term_cn", type_name="term")

    with tab_filaments:
        filtered = filter_filaments(filaments_data, search_input)
        st.caption(f"共 {len(filtered)} 种耗材  ·  点击名称查看详情")
        st.markdown("<br>", unsafe_allow_html=True)
        show_word_cloud(filtered, id_field="id", label_field="name", type_name="filament")


# ── 详情页 ─────────────────────────────────────────────────

def render_back_button():
    """渲染返回按钮，点击后回到首页"""
    if st.button("← 返回首页"):
        go_home()
        st.rerun()
    st.markdown("<br>", unsafe_allow_html=True)


def render_term_detail(term):
    """渲染黑话词条详情页"""
    render_back_button()

    st.markdown(f"# {term['term_cn']}")
    st.markdown(
        f'<p style="color:#888;font-size:0.95rem;margin-top:-14px;">{term["term_en"]}</p>',
        unsafe_allow_html=True
    )
    st.divider()

    col_text, col_img = st.columns([3, 2])
    with col_text:
        st.markdown(
            f'<p class="detail-text">{term["plain_explanation"]}</p>',
            unsafe_allow_html=True
        )
    with col_img:
        show_image(term["image"])


def render_filament_detail(filament):
    """渲染耗材详情页"""
    render_back_button()

    # 难度徽章颜色
    badge_style_map = {
        "入门": "background:#E6F4EA;color:#276833",
        "进阶": "background:#FFF3CD;color:#7A5500",
        "高级": "background:#FFEBEB;color:#922020",
    }
    badge_style = badge_style_map.get(filament["difficulty"], "background:#F0F0F0;color:#555")

    st.markdown(f"# {filament['name']}")
    st.markdown(
        f'<p style="color:#888;font-size:0.95rem;margin-top:-14px;">{filament["full_name"]}</p>',
        unsafe_allow_html=True
    )
    st.markdown(
        f'<span class="badge" style="{badge_style}">上手难度：{filament["difficulty"]}</span>',
        unsafe_allow_html=True
    )

    st.divider()

    col_text, col_img = st.columns([3, 2])
    with col_text:
        st.markdown(
            f'<p class="detail-text">{filament["plain_intro"]}</p>',
            unsafe_allow_html=True
        )
        st.markdown("<br>", unsafe_allow_html=True)

        col_good, col_bad = st.columns(2)
        with col_good:
            st.markdown("**适合做**")
            for item in filament["good_for"]:
                st.markdown(
                    f'<p class="item-good">✓ {item}</p>',
                    unsafe_allow_html=True
                )
        with col_bad:
            st.markdown("**不适合做**")
            for item in filament["bad_for"]:
                st.markdown(
                    f'<p class="item-bad">✗ {item}</p>',
                    unsafe_allow_html=True
                )

    with col_img:
        show_image(filament["image"])


# ── 主程序入口 ─────────────────────────────────────────────

inject_css()
init_state()

terms_data     = load_json("data/terms.json")
filaments_data = load_json("data/filaments.json")

# 词云链接点击后会带 nav_type / nav_id 参数回来，在这里统一处理
params = st.query_params
if "nav_type" in params and "nav_id" in params:
    go_detail(params["nav_type"], params["nav_id"])
    st.query_params.clear()
    st.rerun()

if st.session_state.page == "home":
    render_home(terms_data, filaments_data)

elif st.session_state.page == "detail":
    if st.session_state.selected_type == "term":
        # 按 id 找到对应词条
        term = next(
            (t for t in terms_data if t["id"] == st.session_state.selected_id),
            None
        )
        if term:
            render_term_detail(term)
        else:
            st.error("找不到该词条。")
            go_home()
            st.rerun()

    elif st.session_state.selected_type == "filament":
        filament = next(
            (f for f in filaments_data if f["id"] == st.session_state.selected_id),
            None
        )
        if filament:
            render_filament_detail(filament)
        else:
            st.error("找不到该耗材。")
            go_home()
            st.rerun()
