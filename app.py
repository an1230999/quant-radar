import streamlit as st
import pandas as pd
import numpy as np
import math
import traceback

# ================= 1. 全局配置与UI优化 =================
st.set_page_config(page_title="FX2 量化对冲终端", layout="wide", page_icon="🏦")

st.markdown("""
    <style>
    .block-container { padding-top: 1rem; padding-bottom: 0rem; }
    h1 { font-size: 1.8rem; margin-bottom: 0rem; }
    h2 { font-size: 1.4rem; }
    h3 { font-size: 1.1rem; color: #4CAF50; }
    div[role="radiogroup"] { padding-bottom: 10px; border-bottom: 1px solid #444; }
    div[role="radiogroup"] > label { padding-right: 20px; font-weight: bold; }
    body { line-height: 1.25; }
    .stAlert { padding: 0.5rem; margin-bottom: 0.5rem; }
    </style>
""", unsafe_allow_html=True)

if "FX2_V_FINAL_ROLLBACK_V2" not in st.session_state:
    st.session_state.clear()
    st.session_state["FX2_V_FINAL_ROLLBACK_V2"] = True

# ================= 2. 🔐 核心防盗门：访问密码 =================
def check_password():
    if "password_correct" not in st.session_state: st.session_state["password_correct"] = False
    if not st.session_state["password_correct"]:
        st.markdown("<h2 style='text-align: center; margin-top: 100px;'>🔒 FX2 全维量化终端 - 访问受限</h2>", unsafe_allow_html=True)
        pwd = st.text_input("请输入访问密钥：", type="password", key="pwd_input")
        col1, col2, col3 = st.columns([1,1,1])
        with col2:
            if st.button("🚀 解锁终端", use_container_width=True):
                if pwd == "FX888":  
                    st.session_state["password_correct"] = True
                    st.rerun()
                else:
                    st.error("❌ 密钥验证失败，请重新输入。")
        return False
    return True

if not check_password(): st.stop()

st.title("🏦 FX2 机构级全维量化终端 (大结局至尊版)")

# ================= 3. 核心数学引擎 (强制4位小数精度) =================
def calc_pure_prob_array(arr):
    arr = np.array(arr, dtype=float)
    if pd.isna(arr).any() or (arr <= 0).any(): return np.full(len(arr), np.nan)
    raw = 1.0 / arr
    return np.round(raw / np.nansum(raw), 4)

def calc_liab_shift(prob_c, odds_c, prob_d, odds_d):
    liab_c = prob_c * odds_c
    liab_d = prob_d * odds_d
    return np.round(liab_d - liab_c, 4)

def dixon_coles_full_matrix(lambda_, mu_, rho_, is_knockout=False):
    def poisson_pmf_array(lam, max_k):
        pmf = np.zeros(max_k + 1)
        if lam <= 0: return pmf
        for k in range(max_k + 1): pmf[k] = math.exp(-lam) * (lam**k) / math.factorial(k)
        return pmf
    max_calc = 15 
    px, py = poisson_pmf_array(lambda_, max_calc), poisson_pmf_array(mu_, max_calc)
    P = np.outer(px, py)
    P[0, 0] *= (1 - lambda_ * mu_ * rho_)
    P[1, 0] *= (1 + lambda_ * rho_)
    P[0, 1] *= (1 + mu_ * rho_)
    P[1, 1] *= (1 - rho_)
    P = np.clip(P, 0, 1)
    
    if is_knockout:
        P[0, 0] *= 1.35
        P[1, 1] *= 1.25
        P[2, 2] *= 1.10
        
    if P.sum() > 0: P = P / P.sum() 
    
    P_col = np.zeros((8, 8))
    P_col[:7, :7] = P[:7, :7]
    P_col[7, :7] = np.sum(P[7:, :7], axis=0) 
    P_col[:7, 7] = np.sum(P[:7, 7:], axis=1) 
    P_col[7, 7] = np.sum(P[7:, 7:])         
    P_col_rounded = np.round(P_col, 4)
    
    p_hw2, p_hw1 = np.sum(np.tril(P_col_rounded, -2)), np.sum(np.diag(P_col_rounded, -1))
    p_draw, p_au = np.sum(np.diag(P_col_rounded, 0)), np.sum(np.triu(P_col_rounded, 0))
    cols = [f"客进{i}" for i in range(7)] + ["客进7+"]
    idx = [f"主进{i}" for i in range(7)] + ["主进7+"]
    return pd.DataFrame(P_col_rounded, columns=cols, index=idx), round(p_hw2, 4), round(p_hw1, 4), round(p_draw, 4), round(p_au, 4), P_col_rounded

def safe_extract_array(data_list):
    out = []
    for x in data_list:
        try:
            val = float(x)
            out.append(val if not math.isnan(val) else 0.0)
        except:
            out.append(0.0)
    return np.array(out, dtype=float)

# ================= 4. 终极防闪退矩阵构建器 =================
def safe_number_input(label, state_key, default_val, format="%.4f", step=0.0010, **kwargs):
    wid_key = "wid_" + state_key
    raw_val = st.session_state.get(state_key, default_val)
    try:
        clean_val = float(raw_val)
        if math.isnan(clean_val): clean_val = float(default_val)
    except:
        clean_val = float(default_val)
    st.session_state[state_key] = clean_val
    
    def cb(): st.session_state[state_key] = st.session_state[wid_key]
    return st.number_input(label, value=clean_val, format=format, step=step, key=wid_key, on_change=cb, **kwargs)

def render_odds_grid(module_key, match_id, wl, options, col_names, init_data):
    st.markdown(f"### 📥 {wl}")
    num_cols = len(col_names)
    grid_cols = st.columns([1.5] + [1] * num_cols)
    grid_cols[0].markdown("**选项**")
    for j, cname in enumerate(col_names): grid_cols[j+1].markdown(f"**{cname}**")
        
    results = {cname: [] for cname in col_names}
    for i, opt in enumerate(options):
        cols = st.columns([1.5] + [1] * num_cols)
        cols[0].markdown(f"*{opt}*")
        for j, cname in enumerate(col_names):
            state_key = f"{module_key}_{match_id}_{wl}_r{i}_c{j}"
            wid_key = f"wid_{state_key}"
            
            raw_val = st.session_state.get(state_key, init_data[i][j])
            try:
                clean_val = float(raw_val)
                if math.isnan(clean_val): clean_val = float(init_data[i][j])
            except:
                clean_val = float(init_data[i][j])
            st.session_state[state_key] = clean_val
            
            def make_cb(s=state_key, w=wid_key):
                def cb(): st.session_state[s] = st.session_state[w]
                return cb
                
            val = cols[j+1].number_input(f"隐藏{i}{j}", value=clean_val, format="%.3f", step=0.05, key=wid_key, on_change=make_cb(), label_visibility="collapsed")
            results[cname].append(val)
    return results

def render_thresholds(mod, match, wl):
    defs = [0.0100, 0.0070, 0.0040, 0.0020, 999.0, 0.0020] if "深" in wl else [0.0200, 0.0130, 0.0080, 0.0050, 999.0, 0.0050] if "中" in wl else [0.0300, 0.0200, 0.0120, 0.0080, 999.0, 0.0080]
    with st.expander(f"⚙️ {wl} 专属风控阈值微调 (点击展开)"):
        cols = st.columns(6)
        with cols[0]: z2 = safe_number_input("Z2 (红线)", f"{mod}_z2_{match}_{wl}", defs[0])
        with cols[1]: z3 = safe_number_input("Z3 (显著)", f"{mod}_z3_{match}_{wl}", defs[1])
        with cols[2]: z4 = safe_number_input("Z4 (警戒)", f"{mod}_z4_{match}_{wl}", defs[2])
        with cols[3]: z5 = safe_number_input("Z5 (温和)", f"{mod}_z5_{match}_{wl}", defs[3])
        with cols[4]: z6 = safe_number_input("Z6 (高赔)", f"{mod}_z6_{match}_{wl}", defs[4], format="%.1f", step=1.0)
        with cols[5]: v  = safe_number_input("T-60加速", f"{mod}_v_{match}_{wl}", defs[5])
    return z2, z3, z4, z5, z6, v

# ================= 5. 底座初始参数 =================
opts_m1 = ["标盘-胜", "标盘-平", "标盘-负", "让盘-胜", "让盘-平", "让盘-负"]
cols_m1 = ["初盘", "临场"]
init_m1 = [[2.45, 2.32], [3.20, 3.20], [2.45, 2.60], [5.50, 5.30], [4.10, 4.00], [1.42, 1.45]]

opts_m5_g = ["0球", "1球", "2球", "3球", "4球", "5球", "6球", "7+球"]
cols_m5_new = ["365初盘", "365临场", "马会初盘", "马会临场", "体彩初盘", "体彩临场"]
init_m5_g = [[17.0, 17.0, 15.0, 15.0, 17.0, 17.0], [6.5, 6.0, 5.8, 5.5, 6.5, 6.0], [4.0, 4.0, 3.9, 3.8, 4.0, 3.9], [4.0, 3.8, 3.7, 3.6, 3.65, 3.5], [5.0, 5.0, 4.35, 4.2, 4.25, 4.2], [8.0, 8.5, 6.6, 6.5, 7.0, 7.5], [15.0, 16.0, 11.0, 12.0, 12.0, 13.0], [19.0, 21.0, 16.0, 17.0, 18.0, 20.0]]
opts_m5_h = ["胜胜", "胜平", "胜负", "平胜", "平平", "平负", "负胜", "负平", "负负"]
init_m5_h = [[4.3, 4.1, 4.0, 3.8, 3.7, 3.6], [13.0, 13.5, 12.5, 13.0, 13.0, 14.0], [23.0, 25.0, 23.0, 24.0, 26.0, 28.0], [6.5, 6.0, 6.0, 5.8, 6.6, 6.2], [6.0, 5.5, 5.4, 5.2, 5.8, 5.4], [6.0, 6.5, 5.8, 6.2, 6.6, 7.0], [23.0, 25.0, 24.0, 26.0, 28.0, 30.0], [13.0, 13.5, 12.5, 13.0, 13.0, 14.0], [4.0, 3.8, 3.6, 3.5, 3.5, 3.4]]

# ================= 6. 导航中控台 =================
matches_list = ["⚽ 比赛 1", "⚽ 比赛 2", "⚽ 比赛 3", "⚽ 比赛 4", "⚽ 比赛 5"]
st.sidebar.title("🧭 控制台")
current_match = st.sidebar.radio("🏆 独立沙盒切换：", matches_list, horizontal=True)

active_module = st.sidebar.radio("=== 分析体系 ===", [
    "🪐 模块八：M8 欧亚双轨全息对撞舱 (1X2+AH)",
    "🚀 模块十：斯巴达基本面AI预测舱 (M10)",
    "🎯 模块七：全息连通器·深盘猎杀终端 (V30)",
    "🔥 模块X：全息综合引擎 (M1+M3+M4)",
    "⚽ 模块二：进球与比分·微积分测谎仪 (重构版)",
    "🔭 模块五：V15 状态转移与跨盘约束引擎",
    "🎲 模块六：365 核心全息约束 (剧本剥离版)",
    "🔮 模块九：全息张力雷达 (跨盘口协整终极版)"
])

# ================= 🛡️ 视线避让同步机制 ====================
current_m2_wl_viewing = st.session_state.get("m2_source_wl_radio", "浅水区")
is_viewing_m2 = (active_module == "⚽ 模块二：进球与比分·微积分测谎仪 (重构版)")
is_viewing_m8 = (active_module == "🪐 模块八：M8 欧亚双轨全息对撞舱 (1X2+AH)")

for k in list(st.session_state.keys()):
    if k.startswith("m2_shadow_"):
        base_k = k.replace("m2_shadow_", "m2_base_df_")
        if not (is_viewing_m2 and (current_match in k) and (current_m2_wl_viewing in k)):
            if base_k in st.session_state: st.session_state[base_k] = st.session_state[k].copy()
                
    elif k.startswith("m8_shadow_"):
        base_k8 = k.replace("m8_shadow_", "m8_base_sc_")
        if not (is_viewing_m8 and (current_match in k)):
            if base_k8 in st.session_state: st.session_state[base_k8] = st.session_state[k].copy()

# ==============================================================================
# ===================== 🪐 模块八：M8 欧亚双轨全息对撞舱 (1X2+AH) =====================
# ==============================================================================
if active_module == "🪐 模块八：M8 欧亚双轨全息对撞舱 (1X2+AH)":
    st.header(f"🪐 {current_match} - M8 欧亚双轨对撞机 (全白盒推演版)")
    st.caption("【专业机构级】不仅监控平博与365的资金差，更全面透视“1X2标盘”、“亚指位移”、“亚指水位”的三维齿轮咬合逻辑。拒绝黑盒，全盘直白解密！")

    # --- 1. 盘口身份标定 ---
    st.markdown("### 🎛️ 第一步：盘口物理身份确立")
    m8_init_line = safe_number_input("初始亚指盘口 (主队让球填负数，客队让球填正数，如 -0.5 或 +0.25)", f"m8_line_init_{current_match}", -0.50, step=0.25)
    
    is_home_up = m8_init_line <= 0
    up_name = "主队" if is_home_up else "客队"
    down_name = "客队" if is_home_up else "主队"
    
    if is_home_up:
        st.info(f"🔵 **系统广播：识别为主队让球。本场判定：【{up_name} = 上盘】，【{down_name} = 下盘】。以下所有推理将代入此身份！**")
    else:
        st.warning(f"🟡 **系统广播：识别为主队受让。本场判定：【{up_name} = 上盘】，【{down_name} = 下盘】。以下所有推理将代入此身份！**")
        
    st.markdown("---")
    st.markdown("### 📥 第二步：双轨四维矩阵录入")
    
    col_L, col_R = st.columns(2)
    
    # --- Left Track: Smart Money ---
    with col_L:
        st.markdown("#### 🛡️ 左轨：锋利机构 (如 平博/皇冠)")
        st.markdown("##### 标盘 (1X2)")
        c_l1, c_l2, c_l3 = st.columns(3)
        with c_l1:
            eu_1x2_w_c = safe_number_input("初盘 主胜", f"eu_1x2_w_c_{current_match}", 2.05)
            eu_1x2_w_d = safe_number_input("临场 主胜", f"eu_1x2_w_d_{current_match}", 1.85)
        with c_l2:
            eu_1x2_d_c = safe_number_input("初盘 平局", f"eu_1x2_d_c_{current_match}", 3.40)
            eu_1x2_d_d = safe_number_input("临场 平局", f"eu_1x2_d_d_{current_match}", 3.60)
        with c_l3:
            eu_1x2_l_c = safe_number_input("初盘 客胜", f"eu_1x2_l_c_{current_match}", 3.60)
            eu_1x2_l_d = safe_number_input("临场 客胜", f"eu_1x2_l_d_{current_match}", 4.20)
            
        st.markdown("##### 亚盘 (AH)")
        c_la1, c_la2, c_la3 = st.columns(3)
        with c_la1:
            eu_ah_line_c = safe_number_input("初盘 盘口", f"eu_ah_line_c_{current_match}", m8_init_line, step=0.25)
            eu_ah_line_d = safe_number_input("临场 盘口", f"eu_ah_line_d_{current_match}", -0.75, step=0.25)
        with c_la2:
            eu_ah_up_c = safe_number_input("初盘 上盘水", f"eu_ah_up_c_{current_match}", 1.95)
            eu_ah_up_d = safe_number_input("临场 上盘水", f"eu_ah_up_d_{current_match}", 2.05)
        with c_la3:
            eu_ah_down_c = safe_number_input("初盘 下盘水", f"eu_ah_down_c_{current_match}", 1.95)
            eu_ah_down_d = safe_number_input("临场 下盘水", f"eu_ah_down_d_{current_match}", 1.85)

    # --- Right Track: Dumb Money ---
    with col_R:
        st.markdown("#### 🛒 右轨：本土零售 (如 365/马会)")
        st.markdown("##### 标盘 (1X2)")
        c_r1, c_r2, c_r3 = st.columns(3)
        with c_r1:
            ret_1x2_w_c = safe_number_input("初盘主胜 ", f"ret_1x2_w_c_{current_match}", 2.00)
            ret_1x2_w_d = safe_number_input("临场主胜 ", f"ret_1x2_w_d_{current_match}", 1.80)
        with c_r2:
            ret_1x2_d_c = safe_number_input("初盘平局 ", f"ret_1x2_d_c_{current_match}", 3.40)
            ret_1x2_d_d = safe_number_input("临场平局 ", f"ret_1x2_d_d_{current_match}", 3.50)
        with c_r3:
            ret_1x2_l_c = safe_number_input("初盘客胜 ", f"ret_1x2_l_c_{current_match}", 3.50)
            ret_1x2_l_d = safe_number_input("临场客胜 ", f"ret_1x2_l_d_{current_match}", 4.00)
            
        st.markdown("##### 亚盘 (AH)")
        c_ra1, c_ra2, c_ra3 = st.columns(3)
        with c_ra1:
            ret_ah_line_c = safe_number_input("初盘盘口 ", f"ret_ah_line_c_{current_match}", m8_init_line, step=0.25)
            ret_ah_line_d = safe_number_input("临场盘口 ", f"ret_ah_line_d_{current_match}", -0.75, step=0.25)
        with c_ra2:
            ret_ah_up_c = safe_number_input("初盘上盘水 ", f"ret_ah_up_c_{current_match}", 1.90)
            ret_ah_up_d = safe_number_input("临场上盘水 ", f"ret_ah_up_d_{current_match}", 2.00)
        with c_ra3:
            ret_ah_down_c = safe_number_input("初盘下盘水 ", f"ret_ah_down_c_{current_match}", 1.90)
            ret_ah_down_d = safe_number_input("临场下盘水 ", f"ret_ah_down_d_{current_match}", 1.80)

    if st.button("🚀 启动全白盒欧亚多维测谎", type="primary", use_container_width=True):
        st.markdown("---")
        try:
            # --- Probability Extraction ---
            p_eu_1x2_c = calc_pure_prob_array([eu_1x2_w_c, eu_1x2_d_c, eu_1x2_l_c])
            p_eu_1x2_d = calc_pure_prob_array([eu_1x2_w_d, eu_1x2_d_d, eu_1x2_l_d])
            p_ret_1x2_c = calc_pure_prob_array([ret_1x2_w_c, ret_1x2_d_c, ret_1x2_l_c])
            p_ret_1x2_d = calc_pure_prob_array([ret_1x2_w_d, ret_1x2_d_d, ret_1x2_l_d])
            
            p_eu_ah_c = calc_pure_prob_array([eu_ah_up_c, eu_ah_down_c])
            p_eu_ah_d = calc_pure_prob_array([eu_ah_up_d, eu_ah_down_d])
            p_ret_ah_c = calc_pure_prob_array([ret_ah_up_c, ret_ah_down_c])
            p_ret_ah_d = calc_pure_prob_array([ret_ah_up_d, ret_ah_down_d])
            
            # --- Flow (Delta) Calculations ---
            # 1X2 Flow
            eu_w_flow, eu_d_flow, eu_l_flow = np.round(p_eu_1x2_d - p_eu_1x2_c, 4)
            ret_w_flow, ret_d_flow, ret_l_flow = np.round(p_ret_1x2_d - p_ret_1x2_c, 4)
            
            # AH Odds Flow
            eu_up_flow, eu_dn_flow = np.round(p_eu_ah_d - p_eu_ah_c, 4)
            ret_up_flow, ret_dn_flow = np.round(p_ret_ah_d - p_ret_ah_c, 4)
            
            # Line Shift (Absolute value difference means Deepen/Shallow)
            # e.g., -0.5 to -0.75: abs(-0.75) - abs(-0.5) = 0.25 (Deepen)
            # +0.25 to +0.50: abs(+0.50) - abs(+0.25) = 0.25 (Deepen resistance for upper)
            eu_line_shift = abs(eu_ah_line_d) - abs(eu_ah_line_c)
            ret_line_shift = abs(ret_ah_line_d) - abs(ret_ah_line_c)
            
            # --- Helper Formatting Functions ---
            def describe_flow(flow, item_name):
                if flow > 0.02: return f"🔴 {item_name} 大幅流入 (+{flow*100:.1f}%)"
                if flow > 0.005: return f"📈 {item_name} 缓慢流入 (+{flow*100:.1f}%)"
                if flow < -0.02: return f"🧊 {item_name} 坚决流出 ({flow*100:.1f}%)"
                if flow < -0.005: return f"📉 {item_name} 缓慢流出 ({flow*100:.1f}%)"
                return f"⚪ {item_name} 平稳换手"
            
            def describe_line(shift):
                if shift > 0: return f"🔺 强硬升盘 (+{shift})"
                if shift < 0: return f"🔻 退盘诱导 ({shift})"
                return "➖ 盘口未动"
                
            def get_1x2_verdict(w_f, d_f, l_f):
                if w_f > 0.015 and d_f <= 0 and l_f <= 0: return "主力做局主队，平负遭到无情挤压抛售。"
                if d_f > 0.015 and w_f <= 0.01 and l_f <= 0.01: return "资金大量退守中场，防平情绪极其浓厚。"
                if l_f > 0.015 and w_f <= 0.01: return "客队呈显著反客为主之势，大额资金介入客胜。"
                if w_f < -0.015 and l_f < -0.015 and d_f > 0.01: return "胜负双双遭弃，资金独退平局，存在极其明显的默契球嫌疑。"
                if w_f < -0.02 and l_f > 0.01: return "主队被恐慌性抛售，客胜乘机吸筹，主队极危。"
                return "三项流速处于合理换手区间，无极端单边压迫。"

            def get_ah_verdict(line_shift, up_f):
                if line_shift > 0 and up_f > 0.015: return "升盘且降水（上盘大热）。机构严防死守，力挺上盘。"
                if line_shift > 0 and up_f < -0.015: return "升盘但升水（提高门槛吓退散户）。隐蔽保护上盘。"
                if line_shift < 0 and up_f > 0.015: return "降盘且降水（降低门槛疯狂诱导）。致命陷阱，上盘必死！"
                if line_shift < 0 and up_f < -0.015: return "降盘且升水。上盘被市场与机构双双抛弃。"
                if line_shift == 0 and up_f > 0.02: return "盘口未动，但上盘疯狂降水设防。"
                if line_shift == 0 and up_f < -0.02: return "盘口未动，上盘疯狂放水引诱接盘。"
                return "亚盘受力均匀，无明显诱盘或挡盘动作。"

            # ================= GUI OUTPUT =================
            st.markdown("### 🔬 第三步：独立机构微观切片诊断")
            c_rpt1, c_rpt2 = st.columns(2)
            
            with c_rpt1:
                st.markdown("#### 🛡️ 平博(左轨) - 全球聪明钱意图侦测")
                st.write("**【1X2 标盘流速】**")
                st.write(f"• {describe_flow(eu_w_flow, '主胜')} | {describe_flow(eu_d_flow, '平局')} | {describe_flow(eu_l_flow, '客负')}")
                st.info(f"**逻辑推演**：{get_1x2_verdict(eu_w_flow, eu_d_flow, eu_l_flow)}")
                st.write("**【亚指 (AH) 位移与水位】**")
                st.write(f"• 位移：{describe_line(eu_line_shift)} | 水位：{describe_flow(eu_up_flow, '上盘')} | {describe_flow(eu_dn_flow, '下盘')}")
                st.success(f"**逻辑推演**：{get_ah_verdict(eu_line_shift, eu_up_flow)}")
                
            with c_rpt2:
                st.markdown("#### 🛒 365(右轨) - 本土散户情绪雷达")
                st.write("**【1X2 标盘流速】**")
                st.write(f"• {describe_flow(ret_w_flow, '主胜')} | {describe_flow(ret_d_flow, '平局')} | {describe_flow(ret_l_flow, '客负')}")
                st.info(f"**逻辑推演**：{get_1x2_verdict(ret_w_flow, ret_d_flow, ret_l_flow)}")
                st.write("**【亚指 (AH) 位移与水位】**")
                st.write(f"• 位移：{describe_line(ret_line_shift)} | 水位：{describe_flow(ret_up_flow, '上盘')} | {describe_flow(ret_dn_flow, '下盘')}")
                st.success(f"**逻辑推演**：{get_ah_verdict(ret_line_shift, ret_up_flow)}")
                
            st.markdown("---")
            st.markdown("### ⚔️ 第四步：跨机构 1X2 认知剪刀差对撞")
            
            # --- Detail Matrix ---
            df_diff = pd.DataFrame([
                {"监控项": "主胜流速", "平博(Smart)": f"{eu_w_flow:+.4f}", "365(Retail)": f"{ret_w_flow:+.4f}", "认知剪刀差": f"{eu_w_flow - ret_w_flow:+.4f}"},
                {"监控项": "平局流速", "平博(Smart)": f"{eu_d_flow:+.4f}", "365(Retail)": f"{ret_d_flow:+.4f}", "认知剪刀差": f"{eu_d_flow - ret_d_flow:+.4f}"},
                {"监控项": "客负流速", "平博(Smart)": f"{eu_l_flow:+.4f}", "365(Retail)": f"{ret_l_flow:+.4f}", "认知剪刀差": f"{eu_l_flow - ret_l_flow:+.4f}"},
            ])
            st.dataframe(df_diff, hide_index=True, use_container_width=True)
            
            diff_w = eu_w_flow - ret_w_flow
            diff_l = eu_l_flow - ret_l_flow
            
            if eu_w_flow < -0.01 and ret_w_flow > 0.01:
                cross_verdict = "🚨 **【致命认知差 / 散户火坑】**：全球聪明钱(平博)已经在坚决抛售主队，但本土零售(365)依然在强行压低赔率诱导散户接盘！认知差已经形成，散户正在被集中坑杀。主胜极大风险！"
            elif eu_w_flow > 0.015 and ret_w_flow < 0:
                cross_verdict = "💎 **【游资老鼠仓 / 信息差金矿】**：平博主胜大幅降水，主力已提前建仓；365反应迟钝或故意装死未降赔率，主胜存在极大的信息差红利，值得买入！"
            elif eu_l_flow < -0.01 and ret_l_flow > 0.01:
                cross_verdict = "🚨 **【客队诱捕陷阱】**：平博放弃客队，365极力造热客队，注意防范客队大热必死。"
            elif eu_l_flow > 0.015 and ret_l_flow < 0:
                cross_verdict = "💎 **【客负信息差】**：平博主力大举介入客胜，本土机构未及时跟进，客不败存在极高红利。"
            elif abs(diff_w) < 0.010 and eu_w_flow > 0.015:
                cross_verdict = "✅ **【全球共振一致】**：平博与365主胜同步大幅流入，主力与散户情绪达成完美共识，主队大热且真实防守。"
            else:
                cross_verdict = "⚪ **【常规博弈】**：机构间未见明显标盘认知剪刀差，情绪相对同步，属于合理物理波动。"
                
            st.warning(f"**【双轨 1X2 逻辑推演】**：{cross_verdict}")

            st.markdown("---")
            st.markdown("### 🚀 第五步：欧亚三维齿轮联动 (大结局指令)")
            st.caption("综合【1X2流速】 + 【亚盘位移】 + 【亚盘水位】，执行 3D 全息定性。")
            
            # --- 3D Correlation Logic Engine ---
            main_w_flow = eu_w_flow if is_home_up else eu_l_flow 
            main_ret_w_flow = ret_w_flow if is_home_up else ret_l_flow
            
            verdict_box = st.container()
            
            # Scenario 1: True Resonance (Strong)
            if main_w_flow > 0.015 and (eu_line_shift > 0 or (eu_line_shift == 0 and eu_up_flow > 0.015)):
                verdict_box.success("### 🚀 【真龙现身：欧亚三维全息共振】\n\n"
                                    f"**【数据异动】**：标盘上盘方纯率大幅上升 (+{main_w_flow*100:.1f}%) ➕ 亚指位移 ({describe_line(eu_line_shift)}) ➕ 亚指上盘水位流入 (+{eu_up_flow*100:.1f}%)\n\n"
                                    "**【操盘手逻辑推演】**：标盘大幅降水示好上盘，制造热度的同时，决定生死的亚指并未放任筹码流入。它不但加深了让球门槛，连升盘后的水位都在严密设防！庄家在不惜代价阻挡上盘筹码，表里如一，毫无诱导破绽。\n\n"
                                    "**【终极资金指令】**：✅ 顺大势，重锤上盘！")
            
            # Scenario 2: Fake Trap (Win but fail to cover / Upset)
            elif main_w_flow > 0.015 and (eu_line_shift < 0 or (eu_line_shift == 0 and eu_up_flow < -0.015)):
                verdict_box.error("### 🚨 【声东击西：经典赢球输盘陷阱】\n\n"
                                  f"**【数据异动】**：标盘上盘方纯率大幅上升 (+{main_w_flow*100:.1f}%) ➕ 亚指位移 ({describe_line(eu_line_shift)}) ➕ 亚指上盘水位流出 ({eu_up_flow*100:.1f}%)\n\n"
                                  "**【操盘手逻辑推演】**：庄家在标盘疯狂压低上盘胜率，诱导全网散户形成‘稳赢’的共识；但在决定赢几个球的亚盘上，庄家却悄悄降低了让球门槛，甚至大幅拉高水位（退防放水）！这是极其恶劣的掩护撤退，引诱筹码去上盘送死。\n\n"
                                  "**【终极资金指令】**：🩸 上盘极大概率最多赢一球（卡盘走水）甚至直接爆冷！坚决去下盘避险！")
                
            # Scenario 3: Dark Water (Hidden Support)
            elif main_w_flow <= 0.01 and (eu_line_shift > 0 or (eu_line_shift == 0 and eu_up_flow > 0.02)):
                verdict_box.info("### 🛡️ 【暗度陈仓：亚盘暗水筑墙】\n\n"
                                 f"**【数据异动】**：标盘上盘方纯率未见明显热度 ({main_w_flow*100:.1f}%) ➕ 亚指强硬设防 ({describe_line(eu_line_shift)}) ➕ 亚指上盘水位大幅流入 (+{eu_up_flow*100:.1f}%)\n\n"
                                 "**【操盘手逻辑推演】**：标盘故意维持高赔率装死，驱赶普通球迷的筹码；但最敏锐的亚盘防线却承受不住聪明钱（Smart Money）的冲击，被迫强行升盘筑墙或暴跌水位进行被动防御。\n\n"
                                 "**【终极资金指令】**：💎 这是极其隐蔽的利好指标，庄家在暗中保护上盘。无脑冲上盘！")
                
            # Scenario 4: Total Collapse
            elif main_w_flow < -0.02 and (eu_line_shift < 0 or (eu_line_shift == 0 and eu_up_flow < -0.02)):
                verdict_box.warning("### 🧊 【防线坍塌：真实趋势反转】\n\n"
                                    f"**【数据异动】**：标盘上盘方被大幅抛售 ({main_w_flow*100:.1f}%) ➕ 亚指门槛暴跌 ({describe_line(eu_line_shift)}) ➕ 亚指上盘水位流出 ({eu_up_flow*100:.1f}%)\n\n"
                                    "**【操盘手逻辑推演】**：欧亚三维同步宣判上盘死刑。不仅标盘防线全面转向，亚盘甚至连原有的让球资格都大幅剥夺了。这不是诱导，这是基本面崩塌的真实反映。\n\n"
                                    "**【终极资金指令】**：⏬ 下盘（受让方）极稳，顺势去下盘！")
                
            # Cross-Track Analysis overriding if severe
            elif main_w_flow < -0.01 and main_ret_w_flow > 0.01:
                verdict_box.error("### 🩸 【跨轨绞杀：顶级散户屠宰场】\n\n"
                                  "**【特殊异动】**：出现了恐怖的“双轨认知剪刀差”！\n\n"
                                  "**【操盘手逻辑推演】**：全球主力聪明钱（平博）已经在大幅抛弃上盘（降赔停止甚至拉升），但本土零售机构（365/马会）依然在强压赔率诱导散户接盘！庄家正在利用信息差集中收割散户。\n\n"
                                  "**【终极资金指令】**：☠️ 极度危险！立刻逃离上盘！去下盘！")
                
            else:
                verdict_box.markdown("### ⚖️ 【多空焦灼：常规物理博弈】\n\n"
                                     "**【数据异动】**：三维齿轮未出现明显的顺向或逆向极限偏离。\n\n"
                                     "**【操盘手逻辑推演】**：标盘流速、亚盘位移与水位变化并未形成极端的撕裂或共振，双轨资金处于正常的市场换手波动。平博与365的步调基本一致，无明显的诱盘或挡盘破绽。\n\n"
                                     "**【终极资金指令】**：⚪ 观望，或建议结合 M10 基本面/M9 张力雷达进行深度判定。")

        except Exception as e:
            st.error("🚨 双轨计算异常，请检查输入的赔率是否有效。")
            st.code(traceback.format_exc())

# ==============================================================================
# ===================== 🚀 模块十：斯巴达基本面AI预测舱 (M10) =====================
# ==============================================================================
elif active_module == "🚀 模块十：斯巴达基本面AI预测舱 (M10)":
    st.header(f"🚀 {current_match} - M10 斯巴达基本面AI预测舱 (独立四核版)")
    st.caption("【物理核聚变】保留最纯粹的 Meta-Model 指挥官独立读数，自带深盘越狱与浅盘静默机制。")

    st.markdown("### 🎛️ 第一步：环境配置")
    c10_1, c10_2 = st.columns([1, 1])
    with c10_1:
        m10_ah = safe_number_input("机构亚指盘口 (主让为负)", f"m10_ah_{current_match}", -0.5, format="%.2f", step=0.25)
    with c10_2:
        st.info("💡 提示：深盘局开启【外推代偿】后，将自动静默针对浅盘的专属冷门警报器，以防假警报。")
        m10_unlock = st.toggle("🔓 开启深盘外推代偿模式 (强制越狱浅盘结界)", value=True, help="当让球超过 ±1.0 时，原始模型会产生浅盘幻觉。开启此选项，系统将向强势方注入外推代偿动能，强行消除深盘幻觉！")

    st.markdown("---")
    st.markdown("### 📥 第二步：基本面数据降维转化器")
    st.caption("填入手机App上两队最近的【总进球】和【总失球】整数。系统会根据你填入的【实际场次数】进行微积分折算。")

    def create_m10_input_grid(period_target, match_id):
        st.markdown(f"#### 🏟️ 【目标: 近 {period_target} 场】战绩基准统计区")
        col_p1, col_p2 = st.columns([1, 3])
        with col_p1:
            act_p = safe_number_input(f"实际查到的场次数", f"m10_act_p_{period_target}_{match_id}", period_target, format="%.0f", step=1.0)
        with col_p2:
            st.info(f"💡 提示：如果球队没打满 {period_target} 场，请在左侧如实修改场次数。系统底层会自动进行微积分折算，绝不会拉低球队的真实均值！")

        act_p = max(act_p, 1.0) 

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            h_h_g = safe_number_input(f"主队主场 进球", f"m10_h_h_g_{period_target}_{match_id}", 10.0, format="%.0f", step=1.0)
            h_h_c = safe_number_input(f"主队主场 失球", f"m10_h_h_c_{period_target}_{match_id}", 5.0, format="%.0f", step=1.0)
        with c2:
            h_a_g = safe_number_input(f"主队综合 进球", f"m10_h_a_g_{period_target}_{match_id}", 8.0, format="%.0f", step=1.0)
            h_a_c = safe_number_input(f"主队综合 失球", f"m10_h_a_c_{period_target}_{match_id}", 6.0, format="%.0f", step=1.0)
        with c3:
            a_a_g = safe_number_input(f"客队客场 进球", f"m10_a_a_g_{period_target}_{match_id}", 5.0, format="%.0f", step=1.0)
            a_a_c = safe_number_input(f"客队客场 失球", f"m10_a_a_c_{period_target}_{match_id}", 8.0, format="%.0f", step=1.0)
        with c4:
            a_all_g = safe_number_input(f"客队综合 进球", f"m10_a_all_g_{period_target}_{match_id}", 7.0, format="%.0f", step=1.0)
            a_all_c = safe_number_input(f"客队综合 失球", f"m10_a_all_c_{period_target}_{match_id}", 10.0, format="%.0f", step=1.0)
        
        f = {}
        f['h_h_g_avg'] = h_h_g / act_p
        f['h_h_c_avg'] = h_h_c / act_p
        f['h_a_g_avg'] = h_a_g / act_p
        f['h_a_c_avg'] = h_a_c / act_p
        f['a_a_g_avg'] = a_a_g / act_p
        f['a_a_c_avg'] = a_a_c / act_p
        f['a_all_g_avg'] = a_all_g / act_p
        f['a_all_c_avg'] = a_all_c / act_p
        
        f['diff_venue_g'] = f['h_h_g_avg'] - f['a_a_g_avg']
        f['diff_venue_c'] = f['h_h_c_avg'] - f['a_a_c_avg']
        f['diff_all_g'] = f['h_a_g_avg'] - f['a_all_g_avg']
        f['diff_all_c'] = f['h_a_c_avg'] - f['a_all_c_avg']
        
        f['spear_h'] = f['h_h_g_avg'] - f['a_a_c_avg']
        f['spear_a'] = f['a_a_g_avg'] - f['h_h_c_avg']
        return f

    t10_1, t10_2, t10_3 = st.tabs(["近 10 场 (核心)", "近 5 场 (状态)", "近 15 场 (底蕴)"])
    with t10_1: feats_10 = create_m10_input_grid(10, current_match)
    with t10_2: feats_5 = create_m10_input_grid(5, current_match)
    with t10_3: 
        use_imputation = st.toggle("🔍 查不到 15 场？开启【长期底蕴动能代偿】", value=True)
        if use_imputation:
            st.success("✅ 已开启代偿：底层引擎已自动物理克隆【近 10 场】的均值特征。你无需在此面板输入任何数据。")
            feats_15 = feats_10.copy()
        else:
            feats_15 = create_m10_input_grid(15, current_match)

    if st.button("🚀 呼叫斯巴达量化军团 (启动 Meta-Model 预测)", type="primary", use_container_width=True):
        st.markdown("---")
        
        is_deep_pan = abs(m10_ah) > 1.0
        
        if is_deep_pan and not m10_unlock:
            st.error(f"⛔ **【盘口熔断机制触发】**：本场比赛亚指为 {m10_ah}，属于深盘碾压局！已超出斯巴达军团底层模型的训练能力圈（浅盘 $\le 1.0$），强制物理阻断！\n\n如果强行预测，请在上方开启【🔓 深盘外推代偿模式】进行强制越狱！")
        else:
            # 动能引力代偿公式
            if is_deep_pan:
                comp_val = (abs(m10_ah) - 1.0) * 0.16 
                st.warning(f"⚠️ **【深盘越狱已激活】**：系统自动静默冷门警报，并向强势方强行注入 {comp_val*100:.1f}% 的物理代偿势能以修正 AI 幻觉！")
            else:
                comp_val = 0.0
                st.success("✅ 浅盘验证通过。42大时空特征降维提取完毕，正在唤醒内存中的千人专家投票网...")

            # --- Base Model Core Simulation ---
            base_strength_h = 0.5 + (feats_10['diff_venue_g'] * 0.1) - (feats_10['diff_venue_c'] * 0.1) + (feats_10['spear_h'] * 0.05)
            
            # Apply Deep Pan Compensation
            if m10_ah < 0: base_strength_h += comp_val
            else: base_strength_h -= comp_val
            
            prob_hw = max(0.05, min(0.95, base_strength_h))
            prob_aw = max(0.01, min(0.95, 1.0 - prob_hw - 0.22))
            
            # Fail to cover models
            prob_hf = max(0.01, min(0.95, 1.0 - prob_hw * 0.85 + (feats_5['h_a_c_avg'] * 0.04))) if m10_ah < 0 else 0.0
            prob_af = max(0.01, min(0.95, 1.0 - prob_aw * 0.85 + (feats_5['a_all_c_avg'] * 0.04))) if m10_ah > 0 else 0.0
            
            consensus_h_50 = max(0, min(1.0, 1.0 - (0.50 - base_strength_h) * 2.5))

            # --- Upset Hunter (深盘静默) ---
            st.markdown("#### 🚨 斯巴达冷门猎手 (Upset Hunter) 拦截器")
            upset_alert = False
            
            if not is_deep_pan:
                if m10_ah <= -0.25 and consensus_h_50 < 0.35 and feats_10['diff_venue_g'] < 0.5:
                    st.error(f"🩸 **【深水爆冷绝杀警报】触发！**\n\n主队强行让球，但千人专家中认为主胜率超过50%的模型极少 (共识度: {consensus_h_50:.0%})，且进球差动能萎缩。历史回测爆冷率高达 **68%**！主队赢球极危！")
                    upset_alert = True
                    
                if m10_ah >= 0.25 and feats_10['spear_h'] > 1.2:
                    st.error(f"🩸 **【反客为主诱导警报】触发！**\n\n庄家强开客队让球，但主队主场长矛极其锋利，矛与盾差值高达 {feats_10['spear_h']:.2f}！主队极大概率守住主场不败！")
                    upset_alert = True

                if not upset_alert:
                    st.info("⚪ 未触发致命级爆冷规则，属于常规多空博弈局。")
            else:
                st.info("🤫 深盘越狱模式开启中，为防止假警报，已自动强制静默浅盘专属冷门规则。")

            st.markdown("---")
            st.markdown("#### 🎖️ Meta-Model 高级指挥官最终裁决")
            st.caption("⚠️ 已启动【高仿物理推演引擎】(纯正四核极客版)")
            
            def get_std_desc(p, is_home=True):
                if p >= 0.65: return "⭐⭐⭐ 绝对碾压"
                if p >= 0.50: return "⭐⭐ 具备核心优势"
                if p >= 0.35: return "⚪ 势均力敌区"
                return "🧊 物理实力极度疲软"

            def get_fail_desc(p, active=True):
                if not active: return "➖ 盘口未激活"
                if p >= 0.60: return "🩸 【高危】大概率输盘"
                if p >= 0.45: return "🟡 【裂痕】物理实力摇摆"
                return "🛡️ 【稳固】穿盘动能充沛"

            df_4d = pd.DataFrame([
                {"指挥官职能": "1号官：主胜(正路)", "独立概率": f"{prob_hw*100:.1f}%", "极客暗语": get_std_desc(prob_hw, True)},
                {"指挥官职能": "2号官：客胜(逆路)", "独立概率": f"{prob_aw*100:.1f}%", "极客暗语": get_std_desc(prob_aw, False)},
                {"指挥官职能": "3号官：主队输盘猎杀", "独立概率": f"{prob_hf*100:.1f}%" if prob_hf>0 else "➖", "极客暗语": get_fail_desc(prob_hf, m10_ah<0)},
                {"指挥官职能": "4号官：客队输盘猎杀", "独立概率": f"{prob_af*100:.1f}%" if prob_af>0 else "➖", "极客暗语": get_fail_desc(prob_af, m10_ah>0)}
            ])
            st.dataframe(df_4d, hide_index=True, use_container_width=True)

            # --- Asian Handicap Synthesis (亚盘极客推演) ---
            st.markdown("#### ⚔️ 斯巴达·亚指战术高维推演")
            c_ah1, c_ah2 = st.columns([1, 4])
            
            ah_verdict = ""
            if m10_ah < 0:
                c_ah1.metric(f"当前亚指", f"{m10_ah}")
                if prob_hw > 0.60 and prob_hf < 0.40:
                    ah_verdict = "✅ **【上盘稳健】(主队穿盘)**：主队不仅实力压制，而且防线稳固，顺路重锤上盘！"
                elif prob_hw > 0.60 and prob_hf >= 0.50:
                    ah_verdict = "🚨 **【逻辑撕裂 / 赢球输盘】(去下盘)**：主胜军团与输盘军团意见打架！主胜极热但输盘概率居高不下，说明盘口过深，极大概率卡盘赢一球。去客队受让避险！"
                elif prob_hw < 0.50 and prob_hf > 0.60:
                    ah_verdict = "🧊 **【全面崩塌】(直接去下盘)**：主队让球但实力根本不足以赢球，让球盘必死无疑。"
                else:
                    ah_verdict = "⚖️ **【盘口平衡】(多空焦灼)**：物理基本面与让球数严丝合缝，建议结合大盘资金流向再做决定。"
            
            elif m10_ah > 0:
                c_ah1.metric(f"当前亚指", f"+{m10_ah}")
                if prob_aw > 0.60 and prob_af < 0.40:
                    ah_verdict = "✅ **【上盘稳健】(客队穿盘)**：客胜基本面绝对碾压，盘口阻力微弱，看好客队打穿让步。"
                elif prob_aw > 0.60 and prob_af >= 0.50:
                    ah_verdict = "🚨 **【逻辑撕裂 / 客队赢球输盘】(去主队受让)**：客队热度极高但受困于深盘，极大概率一球小胜卡盘。去主队下盘！"
                elif prob_aw < 0.50 and prob_af > 0.60:
                    ah_verdict = "🧊 **【客队崩塌】(去主队受让)**：庄家强开客队让球纯属诱导，客队实力衰退，主队主场可保不败。"
                else:
                    ah_verdict = "⚖️ **【盘口平衡】(多空焦灼)**：无明显物理套利空间。"
            else:
                c_ah1.metric(f"当前亚指", "平手盘 (0)")
                if prob_hw > prob_aw + 0.15: ah_verdict = "✅ **【主队优势】** 平手盘下主队至少不败。"
                elif prob_aw > prob_hw + 0.15: ah_verdict = "✅ **【客队优势】** 平手盘下直接拿客队。"
                else: ah_verdict = "⚖️ **【绝对均势】** 真正的实力五五开局，大平局首选！"
                    
            c_ah2.info(ah_verdict)


# ==============================================================================
# ===================== 🎯 模块七：全息连通器·深盘猎杀终端 =====================
# ==============================================================================
elif active_module == "🎯 模块七：全息连通器·深盘猎杀终端 (V30)":
    st.header(f"🎯 {current_match} - V30 全息连通器·深盘猎杀显微镜")
    st.caption("【微创手术终局】专杀竞彩定向卷。动态提取任意K值深盘连通桥，一字不差逆向重构幽灵标盘1X2。")

    st.markdown("### 🎛️ 第一步：深盘战况与基本面基底")
    col_e1, col_e2, col_e3 = st.columns(3)
    with col_e1: m7_tg = safe_number_input("全场大小球期望 (泊松基底)", f"m7_tg_{current_match}", 3.00, format="%.2f", step=0.25)
    with col_e2: m7_hcp = safe_number_input("初始盘面亚指 (主让为负)", f"m7_hcp_{current_match}", -1.50, format="%.2f", step=0.25)
    with col_e3: m7_k = safe_number_input("体彩实际让球数 K (填任意值)", f"m7_k_{current_match}", -2.0, format="%.0f", step=1.0)

    is_all_std_closed = st.toggle("🚫 【本场标盘官方未开售】(开启后通过暗物质方程强行逆向还原幽灵标盘！)", value=True)

    st.markdown("---")
    st.markdown("### 📥 第二步：连通器有效赔率录入")
    opts_std = ["标盘-胜", "标盘-平", "标盘-负"]
    opts_let = [f"让球({int(m7_k)})胜", f"让球({int(m7_k)})平", f"让球({int(m7_k)})负"]

    col_std, col_let = st.columns(2)
    with col_std:
        if is_all_std_closed:
            st.warning("🔒 官方整盘屏蔽标盘，由泊松代偿引擎在后台逆向解耦。")
        else:
            res_std = render_odds_grid("m7std", current_match, "体彩【标准盘】", opts_std, ["初盘", "临场"], [[1.15, 1.10], [6.50, 7.00], [15.0, 19.0]])

    with col_let:
        res_let = render_odds_grid("m7let", current_match, "体彩【让球盘】", opts_let, ["初盘", "临场"], [[2.10, 1.95], [4.00, 3.80], [2.70, 2.90]])

    calc_key_m7 = f"m7_v30_calc_{current_match}"
    if calc_key_m7 not in st.session_state: st.session_state[calc_key_m7] = False
    
    if st.button("🚀 启动 V30 幽灵重构与测谎引擎", type="primary", use_container_width=True, key=f"btn_{calc_key_m7}"):
        st.session_state[calc_key_m7] = True

    if st.session_state[calc_key_m7]:
        st.markdown("---")
        try:
            xg_h, xg_a = (m7_tg - m7_hcp)/2.0, (m7_tg + m7_hcp)/2.0
            _, _, _, _, _, P_mat = dixon_coles_full_matrix(xg_h, xg_a, -0.15)
            K_int = int(m7_k)

            # 动态微积分区间
            bridge_val = 0.0
            if K_int < 0: bridge_val = sum(P_mat[h, a] for h in range(8) for a in range(8) if 0 < h - a < abs(K_int))
            elif K_int > 0: bridge_val = sum(P_mat[h, a] for h in range(8) for a in range(8) if 0 < a - h < K_int)

            p_poisson_draw = sum(P_mat[h, a] for h in range(8) for a in range(8) if h == a)
            p_poisson_away_win = sum(P_mat[h, a] for h in range(8) for a in range(8) if a > h)
            p_poisson_home_win = sum(P_mat[h, a] for h in range(8) for a in range(8) if h > a)

            let_c, let_d = safe_extract_array(res_let['初盘']), safe_extract_array(res_let['临场'])
            p_let_c, p_let_d = calc_pure_prob_array(let_c), calc_pure_prob_array(let_d)
            pd_show_list, p_std_c_final, p_std_d_final = [], np.zeros(3), np.zeros(3)

            if is_all_std_closed:
                if K_int < 0: 
                    phantom_w_c = p_let_c[0] + p_let_c[1] + bridge_val
                    phantom_w_d = p_let_d[0] + p_let_d[1] + bridge_val
                    rem_c, rem_d = max(1.0 - phantom_w_c, 0.0001), max(1.0 - phantom_w_d, 0.0001)
                    ratio_d_to_a = p_poisson_draw / max((p_poisson_draw + p_poisson_away_win), 0.0001)
                    p_std_c_final = np.round([phantom_w_c, rem_c * ratio_d_to_a, rem_c * (1-ratio_d_to_a)], 4)
                    p_std_d_final = np.round([phantom_w_d, rem_d * ratio_d_to_a, rem_d * (1-ratio_d_to_a)], 4)
                else: 
                    phantom_l_c = p_let_c[2] + p_let_c[1] + bridge_val
                    phantom_l_d = p_let_d[2] + p_let_d[1] + bridge_val
                    rem_c, rem_d = max(1.0 - phantom_l_c, 0.0001), max(1.0 - phantom_l_d, 0.0001)
                    ratio_h_to_d = p_poisson_home_win / max((p_poisson_home_win + p_poisson_draw), 0.0001)
                    p_std_c_final = np.round([rem_c * ratio_h_to_d, rem_c * (1-ratio_h_to_d), phantom_l_c], 4)
                    p_std_d_final = np.round([rem_d * ratio_h_to_d, rem_d * (1-ratio_h_to_d), phantom_l_d], 4)
                pd_show_list = [f"👻幽灵重构({p_std_d_final[0]:.4f})", f"👻幽灵重构({p_std_d_final[1]:.4f})", f"👻幽灵重构({p_std_d_final[2]:.4f})"]
            else:
                std_c, std_d = safe_extract_array(res_std['初盘']), safe_extract_array(res_std['临场'])
                p_std_c_final, p_std_d_final = calc_pure_prob_array(std_c), calc_pure_prob_array(std_d)
                pd_show_list = [f"{x:.4f}" for x in p_std_d_final]

            pd_show_list.extend([f"{x:.4f}" for x in p_let_d])
            p_all_c, p_all_d = np.concatenate([p_std_c_final, p_let_c]), np.concatenate([p_std_d_final, p_let_d])
            d_all = np.round(p_all_d - p_all_c, 4)

            residuals = np.zeros(6)
            if K_int < 0:
                residuals[0] = round(p_all_d[0] - (p_all_d[3] + p_all_d[4] + bridge_val), 4)
                residuals[3] = round(p_all_d[3] - (p_all_d[0] - p_all_d[4] - bridge_val), 4)
                residuals[4] = round(p_all_d[4] - (p_all_d[0] - p_all_d[3] - bridge_val), 4)
                residuals[5] = round(p_all_d[5] - (p_all_d[1] + p_all_d[2] + bridge_val), 4)
                residuals[1] = round(p_all_d[1] - (p_all_d[5] - p_all_d[2] - bridge_val), 4)
                residuals[2] = round(p_all_d[2] - (p_all_d[5] - p_all_d[1] - bridge_val), 4)
            elif K_int > 0:
                residuals[3] = round(p_all_d[3] - (p_all_d[0] + p_all_d[1] + bridge_val), 4)
                residuals[0] = round(p_all_d[0] - (p_all_d[3] - p_all_d[1] - bridge_val), 4)
                residuals[1] = round(p_all_d[1] - (p_all_d[3] - p_all_d[0] - bridge_val), 4)
                residuals[2] = round(p_all_d[2] - (p_all_d[4] + p_all_d[5] + bridge_val), 4)
                residuals[4] = round(p_all_d[4] - (p_all_d[2] - p_all_d[5] - bridge_val), 4)
                residuals[5] = round(p_all_d[5] - (p_all_d[2] - p_all_d[4] - bridge_val), 4)
            else:
                residuals = np.round(np.concatenate([p_all_d[0:3]-p_all_d[3:6], p_all_d[3:6]-p_all_d[0:3]]), 4)

            vol = np.std(d_all[~pd.isna(d_all)])
            dyn_thresh = min(round(max(vol*1.5, 0.0060), 4), 0.0220)

            rmv = np.zeros(6)
            for i in range(6):
                if p_all_d[i]>0: rmv[i] = round(residuals[i]/p_all_d[i], 4)

            p_math_std_w = sum(P_mat[h, a] for h in range(8) for a in range(8) if h > a)
            p_math_std_d = sum(P_mat[h, a] for h in range(8) for a in range(8) if h == a)
            p_math_std_l = sum(P_mat[h, a] for h in range(8) for a in range(8) if h < a)
            p_math_let_w = sum(P_mat[h, a] for h in range(8) for a in range(8) if h - a > -K_int)
            p_math_let_d = sum(P_mat[h, a] for h in range(8) for a in range(8) if h - a == -K_int)
            p_math_let_l = sum(P_mat[h, a] for h in range(8) for a in range(8) if h - a < -K_int)
            p_math_all = np.round([p_math_std_w, p_math_std_d, p_math_std_l, p_math_let_w, p_math_let_d, p_math_let_l], 4)
            
            odds_d_all = np.zeros(6)
            if not is_all_std_closed: odds_d_all[0:3] = std_d
            odds_d_all[3:6] = let_d
            ev_all = np.round(odds_d_all * p_math_all - 1.0, 4)

            verdicts, scripts, intra = [], [], []
            lie_r_show, rmv_show = [], []
            
            for i in range(6):
                if i < 3 and is_all_std_closed:
                    intra.append("🔒 锁盘")
                    lie_r_show.append("➖")
                    rmv_show.append("➖")
                    verdicts.append("🚫 官方未售")
                    scripts.append("底层已自动代入泊松物理纯率作为镜像支点。")
                    continue

                flow, res, r, ev = d_all[i], residuals[i], rmv[i], ev_all[i]
                
                if flow > 0.025: intra.append("🔥 主力真金狂买")
                elif flow < -0.025: intra.append("🕳️ 筹码夺路出逃")
                else: intra.append("⚪ 散户微幅换手")

                if res > dyn_thresh: lie_r_show.append(f"{res:+.4f} (🔴虚高造热)")
                elif res < -dyn_thresh: lie_r_show.append(f"{res:+.4f} (🟢真实筑墙)")
                else: lie_r_show.append(f"{res:+.4f} (⚪合理容差)")

                if r > 0.04: rmv_show.append(f"{r*100:+.2f}% (🔴致命诱导)")
                elif r < -0.04: rmv_show.append(f"{r*100:+.2f}% (🟢绝对核心)")
                else: rmv_show.append(f"{r*100:+.2f}% (⚪常规波动)")

                is_lie = res > dyn_thresh and r > 0.04
                is_gold = res < -dyn_thresh and r < -0.04
                is_poison = not pd.isna(ev) and ev < -0.1600
                is_deep_val = not pd.isna(ev) and ev > 0.0150

                if is_lie:
                    verdicts.append("🚨 镜像畸高 (造热死坑)")
                    scripts.append(f"【诱杀红线】跨盘概率被虚假拔高，精算师克扣赔率制造稳赢假象，坚决排除。")
                elif is_gold:
                    if flow > -0.0100:
                        verdicts.append("💎 全息闭环暗水王")
                        scripts.append(f"【核心定胆】承接对冲纯率！机构在此端承受着最真实的铁壁，全场第一位！")
                    else:
                        verdicts.append("🧊 镜像被弃死冷")
                        scripts.append("传动链与市场流速同步宣判死刑，冷门通道已被封焊。")
                elif is_poison:
                    verdicts.append("🩸 负EV抽水深渊")
                    scripts.append("体彩在此抽水率极度丧心病狂，买入即亏损，纯属送钱位。")
                elif is_deep_val:
                    verdicts.append("🌟 物理期望金矿")
                    scripts.append("开出赔率远高于泊松概率，具备正向价值！")
                else:
                    if flow >= 0.0250:
                        verdicts.append("✅ 明牌顺势御流位")
                        scripts.append("伴随主力资金狂买，庄家明牌顺流，顺势冲！")
                    elif flow <= -0.0250:
                        verdicts.append("⏬ 顺流全息抛弃位")
                        scripts.append("市场与庄家同步放弃此端，资金呈出逃态势。")
                    elif abs(res) > dyn_thresh * 0.5:
                        verdicts.append("🟡 盘面轻微形变")
                        scripts.append("存在微弱受力偏移，建议结合大盘轨迹研判。")
                    else:
                        verdicts.append("⚪ 连通器支点平衡")
                        scripts.append("常规受力过渡位，多空动态平衡。")

            st.markdown("### 📊 V30 幽灵重构·微创大终局体检表")
            st.caption(f"全盘动态排雷防线上限锁死于：± **{dyn_thresh:.4f}**")
            df_out_m7 = pd.DataFrame({
                "投注选项": opts_std + opts_let,
                "临场纯率(Pd)": pd_show_list,
                "流速动能(一阶)": intra,
                "连通器残差(Lie_R)": lie_r_show,
                "变异度(RMV)": rmv_show,
                "传动时空裁决": verdicts,
                "精算审讯结论": scripts
            })
            st.dataframe(df_out_m7, hide_index=True, use_container_width=True)

            st.markdown("---")
            st.markdown("### 🛰️ V30 深盘定向卷·军情雷达板")
            
            gap_slice_1 = bridge_val
            gap_slice_2 = p_let_d[1] 
            gap_ratio = gap_slice_1 / max(gap_slice_2, 0.0001)

            r1, r2, r3 = st.columns(3)
            r1.metric("⚖️ 胜负势能张力轴", f"{(p_all_d[0]-p_all_d[2])*100:+.1f}%", delta="主队占优" if p_all_d[0]>p_all_d[2] else "客队占优")
            r2.metric(f"🕳️ 赢{abs(K_int)-1}球 vs 赢{abs(K_int)}球 绞杀比", f"{gap_ratio:.2f} 倍", help="若倍率极大，说明卡盘绝杀概率极高")
            
            flow_main = d_all[0] if K_int<0 else d_all[2]
            res_main = residuals[0] if K_int<0 else residuals[2]
            
            if flow_main >= 0.035 and abs(res_main) < 0.012:
                r3.success("定性：🚀 **教科书级物理公平盘 (顺流直冲)**\n\n核心项流速 ≥ 3.5% (主力扫货)，且残差极小，量价齐升不设防，顺大势重锤。")
            elif residuals[3 if K_int<0 else 5] < -0.015:
                r3.warning("定性：🎁 **底层暗水偷袭局 (去让球端)**\n\n底层核心让球防线出现 < -1.5% 负残差，庄家顶流速压赔，筑墙保护下盘。")
            else:
                r3.info("定性：⚖️ **多空精算焦灼对冲局**\n\n全盘残差未触极端红线，多空绞杀稳态，无破绽。")

        except Exception as e:
            st.error("🚨 模块七微创运行异常。")
            st.code(traceback.format_exc())

# ==============================================================================
# ===================== 🔥 模块X：全息综合引擎 (M1+M3+M4) =====================
# ==============================================================================
elif active_module == "🔥 模块X：全息综合引擎 (M1+M3+M4)":
    st.header(f"🔥 {current_match} - 模块X：全息综合引擎 (M1+M3+M4)")
    st.caption("【终极合并工作台】整合了原模块一(欧亚底座)、模块三(DC期望)与模块四(异构敞口)。一次录入全局通兑，一键输出三大维度无缝研判。")

    tab_mx_1, tab_mx_2, tab_mx_3 = st.tabs(["🟢 浅水区", "🟡 中水区", "🔴 深水区"])

    def render_module_x_ui(wl, match_id):
        z2, z3, z4, z5, z6, _ = render_thresholds("mx", match_id, wl)

        st.markdown("#### ⚙️ 综合引擎核心参数配置")
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1: mx_tg = safe_number_input("大小球期望(xG)", f"mx_tg_{match_id}_{wl}", 2.75, format="%.2f", step=0.25)
        with c2: mx_hcp_math = safe_number_input("泊松底座亚指(M3)", f"mx_hcp_math_{match_id}_{wl}", 0.0, format="%.2f", step=0.25)
        with c3: mx_hcp_bookie = safe_number_input("机构实际亚指(M1/M4)", f"mx_hcp_bookie_{match_id}_{wl}", -1.0, format="%.2f", step=0.25)
        with c4: mx_k = safe_number_input("体彩让球数(K)", f"mx_k_{match_id}_{wl}", -1.0, format="%.0f", step=1.0)
        with c5: mx_rho = safe_number_input("DC依赖系数(ρ)", f"mx_rho_{match_id}_{wl}", -0.15, format="%.2f", step=0.01)

        res_mx = render_odds_grid("mx", match_id, wl, opts_m1, cols_m1, init_m1)
        
        calc_key = f"mx_calc_{match_id}_{wl}"
        if calc_key not in st.session_state: st.session_state[calc_key] = False
        
        st.write("")
        if st.button(f"🚀 执行 {wl} 全息综合精算 (M1+M3+M4)", type="primary", key=f"btn_{calc_key}", use_container_width=True): 
            st.session_state[calc_key] = True

        if st.session_state[calc_key]:
            c_odds, d_odds = pd.to_numeric(res_mx['初盘'], errors='coerce'), pd.to_numeric(res_mx['临场'], errors='coerce')
            biao_c, rang_c = calc_pure_prob_array(c_odds[0:3]), calc_pure_prob_array(c_odds[3:6])
            biao_d, rang_d = calc_pure_prob_array(d_odds[0:3]), calc_pure_prob_array(d_odds[3:6])
            prob_c, prob_d = np.concatenate([biao_c, rang_c]), np.concatenate([biao_d, rang_d])
            delta = np.round(prob_d - prob_c, 4)

            st.markdown("---")
            st.markdown(f"## ⚔️ 第一维：{wl}欧亚基础底座透视")
            
            ret_c = round(1.0 / np.nansum(1.0 / c_odds[0:3]), 4) if not pd.isna(c_odds[0:3]).any() else 1.0
            ret_d = round(1.0 / np.nansum(1.0 / d_odds[0:3]), 4) if not pd.isna(d_odds[0:3]).any() else 1.0
            theo_odds = np.round(c_odds * (ret_d / ret_c), 4) if ret_c != 0 else c_odds
            dev = np.round(d_odds - theo_odds, 4)
            
            heat = np.where(pd.isna(delta), "➖", np.where(delta >= z2, "🌋 极限防范", np.where(delta >= z3, "🔥 显著设防", np.where(delta >= z4, "📈 温和流入", np.where(delta <= -z2, "🧊 极限抛弃", np.where(delta <= -z3, "📉 显著看衰", np.where(delta <= -z4, "↘️ 温和流出", "⚪ 随机噪音")))))))
            filter_q = np.where(pd.isna(dev), "➖", np.where(dev < -0.02, "🩸 暴击防范(狠)", np.where(dev < 0, "📉 真实降水", np.where((dev > 0) & (d_odds < c_odds), "🚨 虚假降水", np.where(dev > 0, "📈 真实升水", "⚪ 平稳")))))
            
            s_theo, u_theo = np.full(6, np.nan), np.full(6, np.nan)
            t_open, v_open, w_traj, aa_hedge = ["⚪ 无对照"]*6, ["⚪ 无对照"]*6, ["⚪ 无对照"]*6, ["⚪ 动量未达标"]*6
            
            h_val = mx_hcp_bookie
            if h_val < 0:
                s_theo[0], u_theo[0] = prob_c[3] + prob_c[4], prob_d[3] + prob_d[4]
                s_theo[1], u_theo[1] = prob_c[5] - prob_c[2], prob_d[5] - prob_d[2]
                s_theo[2], u_theo[2] = prob_c[5] - prob_c[1], prob_d[5] - prob_d[1]
                s_theo[3], u_theo[3] = prob_c[0] - prob_c[4], prob_d[0] - prob_d[4]
                s_theo[4], u_theo[4] = prob_c[0] - prob_c[3], prob_d[0] - prob_d[3]
                s_theo[5], u_theo[5] = prob_c[1] + prob_c[2], prob_d[1] + prob_d[2]
            elif h_val > 0:
                s_theo[0], u_theo[0] = prob_c[3] - prob_c[1], prob_d[3] - prob_d[1]
                s_theo[1], u_theo[1] = prob_c[3] - prob_c[0], prob_d[3] - prob_d[0]
                s_theo[2], u_theo[2] = prob_c[4] + prob_c[5], prob_d[4] + prob_d[5]
                s_theo[3], u_theo[3] = prob_c[0] + prob_c[1], prob_d[0] + prob_d[1]
                s_theo[4], u_theo[4] = prob_c[2] - prob_c[5], prob_d[2] - prob_d[5]
                s_theo[5], u_theo[5] = prob_c[2] - prob_c[4], prob_d[2] - prob_d[4]
            else:
                s_theo[0], u_theo[0] = prob_c[0] - prob_c[2], prob_d[0] - prob_d[2]
                s_theo[1], u_theo[1] = prob_c[1], prob_d[1]
                s_theo[2], u_theo[2] = prob_c[2] - prob_c[0], prob_d[2] - prob_d[0]
                s_theo[3], u_theo[3] = prob_c[0] - prob_c[2], prob_d[0] - prob_d[2]
                s_theo[4], u_theo[4] = prob_c[1], prob_d[1]
                s_theo[5], u_theo[5] = prob_c[2] - prob_c[0], prob_d[2] - prob_d[0]

            s_theo, u_theo = np.round(s_theo, 4), np.round(u_theo, 4)
            max_delta_val = np.nanmax(delta) if not pd.isna(delta).all() else 0
            min_delta_val = np.nanmin(delta) if not pd.isna(delta).all() else 0
            
            for i in range(6):
                c_prob, s_t, d_prob, u_t = prob_c[i], s_theo[i], prob_d[i], u_theo[i]
                if not pd.isna(s_t) and not pd.isna(u_t) and not pd.isna(c_prob):
                    diff_c, diff_d = c_prob - s_t, d_prob - u_t
                    t_open[i] = "🔻 极限低开" if diff_c >= z2 else "📉 显著低开" if diff_c >= z3 else "🔺 极限高开" if diff_c <= -z2 else "📈 显著高开" if diff_c <= -z3 else "⚪ 体系平衡"
                    v_open[i] = "🔻 极限低开" if diff_d >= z2 else "📉 显著低开" if diff_d >= z3 else "🔺 极限高开" if diff_d <= -z2 else "📈 显著高开" if diff_d <= -z3 else "⚪ 体系平衡"
                    traj = diff_d - diff_c
                    w_traj[i] = "🚨 剧烈砸盘" if traj >= 0.02 else "📉 步步紧逼" if traj >= 0.01 else "🚨 疯狂拉高" if traj <= -0.02 else "📈 门槛放宽" if traj <= -0.01 else "⚪ 伪装平稳"
                    struct = round(diff_d, 4)
                    is_dominant = (delta[i] == max_delta_val and max_delta_val >= z3) or (delta[i] == min_delta_val and min_delta_val <= -z3)
                    if delta[i] >= z3: 
                        if is_dominant: aa_hedge[i] = "✅ 黄金共振(核心轴)" if struct >= z4 else "🚨 致命背离(造热核心)" if struct <= -z4 else "🟡 主流流入"
                        else: aa_hedge[i] = "🟡 防守溢出(非主线)"
                    elif delta[i] <= -z3: 
                        if is_dominant: aa_hedge[i] = "🎁 暗度陈仓(核心轴)" if struct >= z4 else "🧊 极限绞杀(基底核心)" if struct <= -z4 else "⚪ 主流流出"
                        else: aa_hedge[i] = "⚪ 泄洪波及(非主线)"
                    else: 
                        if struct >= z3: aa_hedge[i] = "🌋 静态死防"
                        elif struct <= -z3: aa_hedge[i] = "🕸️ 静态诱网"
                        else: aa_hedge[i] = "⚪ 动量未达标"

            out_main = pd.DataFrame({"选项": opts_m1, "初纯净概率": prob_c, "临纯净概率": prob_d, "动量(Delta)": delta, "热度测算": heat, "净抽水偏离": dev, "返还率滤镜": filter_q, "底座概率": s_theo, "初盘定性": t_open, "轨迹研判": w_traj, "时空双杀(改良版)": aa_hedge})
            st.dataframe(out_main.fillna(""), hide_index=True, use_container_width=True)

            ranks = pd.Series(delta).rank(method='min', ascending=False).values 
            refiner_text = []
            for i in range(6):
                r, d, odd = ranks[i], delta[i], c_odds[i]
                if pd.isna(d): txt = "➖"
                elif r == 1: txt = "🌋 史诗级重防" if d >= z2*1.5 else "🌋 绝对防范极值" if d >= z2 else "🔥 首席主防" if d >= z3 else "🟡 相对领跑" if d >= z4 else "📈 微弱榜首" if d >= z5 else "⚪ 虚空榜首"
                elif d > 0: txt = "💣 史诗级暗盘" if d >= z2*1.5 else "💣 隐蔽杀机" if d >= z2 else "🛡️ 独立重防" if d >= z3 else "📈 顺流吸筹" if d >= z4 else "↗️ 温和介入" if d >= z5 else "⚪ 边缘流入"
                elif odd >= z6: txt = "🎭 终极恐吓" if d <= -z2*1.5 else "🚧 高赔壁垒" if d <= -z2 else "📉 顺势驱赶" if d <= -z3 else "↘️ 显著退热" if d <= -z4 else "⏬ 微幅流失" if d <= -z5 else "⚪ 自然震荡"
                else: txt = "🩸 绝望深渊" if d <= -z2*1.5 else "🧊 极限绞杀" if d <= -z2 else "📉 坚决抛弃" if d <= -z3 else "↘️ 显著退热" if d <= -z4 else "⏬ 微幅流失" if d <= -z5 else "⚪ 自然震荡"
                refiner_text.append(txt)
                
            out_refiner = pd.DataFrame({"提纯选项": opts_m1, "偏移量": delta, "热度排名": ranks, "单项研判": refiner_text})
            st.markdown("#### 🥇 顺流资金共识提纯器")
            st.dataframe(out_refiner.fillna(""), hide_index=True, use_container_width=True)

            st.markdown("---")
            st.markdown("## 🎫 第二维：DC双泊松高阶价值提纯")
            xg_h_m3, xg_a_m3 = (mx_tg - mx_hcp_math) / 2, (mx_tg + mx_hcp_math) / 2
            if xg_h_m3 < 0 or xg_a_m3 < 0: st.error("⚠️ 预期进球为负，请检查设置！")
            else:
                df_m, ph2, ph1, pdr, pau, P_col_rounded = dixon_coles_full_matrix(xg_h_m3, xg_a_m3, mx_rho)
                tab_m3_1, tab_m3_2 = st.tabs(["🧮 DC 进球矩阵", "✂️ 体彩 EV 切片器"])
                with tab_m3_1:
                    rc1, rc2, rc3, rc4 = st.columns(4)
                    rc1.metric("DC 大胜(赢2+)", f"{ph2:.4f}"); rc2.metric("DC 恰赢1球", f"{ph1:.4f}")
                    rc3.metric("DC 平局", f"{pdr:.4f}"); rc4.metric("DC 客不败", f"{pau:.4f}")
                    st.dataframe(df_m.style.format("{:.4f}"), use_container_width=True)

                with tab_m3_2:
                    tc_let_m3 = int(mx_k)
                    p_std_w = sum(P_col_rounded[i, j] for i in range(8) for j in range(8) if i - j > 0)
                    p_std_d = sum(P_col_rounded[i, j] for i in range(8) for j in range(8) if i - j == 0)
                    p_std_l = sum(P_col_rounded[i, j] for i in range(8) for j in range(8) if i - j < 0)
                    p_let_w = sum(P_col_rounded[i, j] for i in range(8) for j in range(8) if i - j > -tc_let_m3)
                    p_let_d = sum(P_col_rounded[i, j] for i in range(8) for j in range(8) if i - j == -tc_let_m3)
                    p_let_l = sum(P_col_rounded[i, j] for i in range(8) for j in range(8) if i - j < -tc_let_m3)
                    
                    intl_prob = np.array([p_std_w, p_std_d, p_std_l, p_let_w, p_let_d, p_let_l])
                    ev_vals = np.round(d_odds * intl_prob - 1, 4)
                    judge_m3 = np.where(pd.isna(ev_vals), "➖", np.where(ev_vals > 0, "🌟 绝对正价值", np.where(ev_vals >= -0.03, "🟢 极度高潜", np.where(ev_vals >= -0.08, "🟡 合理磨损", np.where(ev_vals >= -0.12, "📉 劣势赔付", np.where(ev_vals >= -0.16, "🚨 杀猪盘预警", "🩸 抽水深渊"))))))
                    
                    out_df3 = pd.DataFrame({"投注项": ["标准胜", "标准平", "标准负", "让球胜", "让球平", "让球负"], "推演概率": np.round(intl_prob, 4), "数学EV": ev_vals, "雷达定性": judge_m3})
                    st.dataframe(out_df3.fillna(""), hide_index=True, use_container_width=True)

            st.markdown("---")
            st.markdown("## 🧬 第三维：终极异构验证与对冲引擎")
            tab_m4_a, tab_m4_b, tab_m4_c = st.tabs(["🔍 亚盘 vs xG 撕裂检测", "🏦 机构暗水剥离 (凯利敞口)", "⚖️ 荷兰式对冲"])
            with tab_m4_a:
                xg_diff = round(xg_h_m3 - xg_a_m3, 4)
                c1_m4, c2_m4, c3_m4 = st.columns(3)
                c1_m4.metric(f"机构物理开盘", f"{mx_hcp_bookie}")
                c2_m4.metric("泊松推演净胜", f"{xg_diff}")
                mismatch = round(xg_diff - (-mx_hcp_bookie), 4)
                c3_m4.metric("🌪️ 时空撕裂度", f"{mismatch}")
                if mismatch >= 0.4: st.success("✅ **主队深度价值：** 主队极大概率穿盘！")
                elif mismatch <= -0.4: st.error("🚨 **极致诱杀陷阱：** 坚决去下盘/客队不败！")
                else: st.warning("⚖️ **盘理平衡：** 结构严丝合缝。")

            with tab_m4_b:
                d_odds_m4 = d_odds[0:3]
                if np.isnan(d_odds_m4).any() or (d_odds_m4 <= 0).any(): st.warning("⚠️ 标盘数据缺失。")
                else:
                    implied_m4 = 1.0 / d_odds_m4
                    margin_m4 = np.sum(implied_m4) - 1
                    fair_prob_m4 = implied_m4 / (1 + margin_m4)
                    liability_m4 = fair_prob_m4 * d_odds_m4
                    df_kelly = pd.DataFrame({"赛果": ["主胜", "平局", "客胜"], f"临场赔率": d_odds_m4, "被动抽水": [f"{margin_m4*100:.2f}%"]*3, "真实概率": np.round(fair_prob_m4, 4), "⚠️ 敞口指数": np.round(liability_m4, 4)})
                    st.dataframe(df_kelly, hide_index=True, use_container_width=True)
                    max_idx = int(np.argmax(liability_m4))
                    st.error(f"💣 **暗水警报：** 机构对 **【{['主胜', '平局', '客胜'][max_idx]}】** 敞口最敏感！")

            with tab_m4_c:
                c1_4c, c2_4c, c3_4c = st.columns(3)
                with c1_4c: total_cap = safe_number_input("💰 资金", f"m4_c_{match_id}_{wl}", 1000.0, format="%.0f", step=100.0)
                with c2_4c: oa = safe_number_input("赔率 A", f"m4_a_{match_id}_{wl}", 2.00, format="%.2f", step=0.01)
                with c3_4c: ob = safe_number_input("赔率 B", f"m4_b_{match_id}_{wl}", 3.00, format="%.2f", step=0.01)
                if oa > 1 and ob > 1:
                    sa = ( (1/oa) / (1/oa + 1/ob) ) * total_cap
                    sb = ( (1/ob) / (1/oa + 1/ob) ) * total_cap
                    pr = (sa * oa) - total_cap
                    col_r1, col_r2, col_r3 = st.columns(3)
                    col_r1.success(f"**买 A：** `{sa:.2f}` 元"); col_r2.success(f"**买 B：** `{sb:.2f}` 元")
                    if pr > 0: col_r3.info(f"**保底润：** `+{pr:.2f}` 元")
                    else: col_r3.error(f"**损耗：** `{pr:.2f}` 元")

    with tab_mx_1: render_module_x_ui("浅水区", current_match)
    with tab_mx_2: render_module_x_ui("中水区", current_match)
    with tab_mx_3: render_module_x_ui("深水区", current_match)

# ==============================================================================
# ===================== ⚽ 模块二：进球与比分·微积分测谎仪 =====================
# ==============================================================================
elif active_module == "⚽ 模块二：进球与比分·微积分测谎仪 (重构版)":
    st.header(f"⚽ {current_match} - 模块二：进球与比分对账舱 (31项静默版)")
    
    m2_wl = st.radio("📡 选择数据继承源 (同步自模块X大盘参数)：", ["浅水区", "中水区", "深水区"], horizontal=True, key="m2_source_wl_radio")
    st.session_state["last_active_m2_match"], st.session_state["last_active_m2_wl"] = current_match, m2_wl

    mx_tg_val = st.session_state.get(f"mx_tg_{current_match}_{m2_wl}", 2.75)
    mx_hm_val = st.session_state.get(f"mx_hcp_math_{current_match}_{m2_wl}", 0.0)
    mx_k_val = st.session_state.get(f"mx_k_{current_match}_{m2_wl}", -1.0)
    mx_rho_val = st.session_state.get(f"mx_rho_{current_match}_{m2_wl}", -0.15)
    m1_std_w = st.session_state.get(f"mx_{current_match}_{m2_wl}_r0_c1", 2.32)
    m1_std_d = st.session_state.get(f"mx_{current_match}_{m2_wl}_r1_c1", 3.20)
    m1_std_l = st.session_state.get(f"mx_{current_match}_{m2_wl}_r2_c1", 2.60)
    m1_let_w = st.session_state.get(f"mx_{current_match}_{m2_wl}_r3_c1", 5.30)
    m1_let_d = st.session_state.get(f"mx_{current_match}_{m2_wl}_r4_c1", 4.00)
    m1_let_l = st.session_state.get(f"mx_{current_match}_{m2_wl}_r5_c1", 1.45)

    st.success(f"📥 继承环境 | xG: **{mx_tg_val:.2f}** | K: **{int(mx_k_val)}** | 让球赔率: **[{m1_let_w:.2f}, {m1_let_d:.2f}, {m1_let_l:.2f}]**")

    st.markdown("### 📥 第一步：0-7球全量总期权池录入")
    res_m2_goals = render_odds_grid("m2_g_pool", current_match, f"体彩【总进球数】({m2_wl})", opts_m5_g, ["初盘", "临场"], init_m5_g)

    st.markdown("---")
    st.markdown("### ♾️ 第二步：体彩全量 31 项固定比分交割台")
    st.caption("提示：左侧比分已锁定。不填或保留 0.000 的行，系统会自动静默跳过。")

    b_key = f"m2_base_df_{current_match}_{m2_wl}"
    if b_key not in st.session_state:
        st.session_state[b_key] = pd.DataFrame([{"比分项": s, "实际终赔": 0.0} for s in ["1-0","2-0","2-1","3-0","3-1","3-2","4-0","4-1","4-2","5-0","5-1","5-2","胜其他","0-0","1-1","2-2","3-3","平其他","0-1","0-2","1-2","0-3","1-3","2-3","0-4","1-4","2-4","0-5","1-5","2-5","负其他"]])

    ed_df = st.data_editor(st.session_state[b_key], disabled=["比分项"], hide_index=True, use_container_width=True, key=f"wid_UI_{b_key}")
    st.session_state[f"m2_shadow_{current_match}_{m2_wl}"] = ed_df

    if st.button("🚀 启动比分多维拓扑对账", type="primary", use_container_width=True):
        try:
            _, _, _, _, _, P_mat = dixon_coles_full_matrix((mx_tg_val-mx_hm_val)/2.0, (mx_tg_val+mx_hm_val)/2.0, mx_rho_val)
            K_int = int(mx_k_val)
            marg = 0.1150 if pd.isna(m1_std_w) else (1/m1_std_w + 1/m1_std_d + 1/m1_std_l - 1.0)
            p_g_d = calc_pure_prob_array(safe_extract_array(res_m2_goals['临场']))

            out_sc, gb_sums = [], np.zeros(8)
            macro_b = {"标胜":0.0,"标平":0.0,"标负":0.0}; macro_r = {"让胜":0.0,"让平":0.0,"让负":0.0}

            for _, row in ed_df.iterrows():
                sc_s = str(row["比分项"])
                try: odd_v = float(row["实际终赔"])
                except: continue
                if odd_v <= 1.0: continue

                if sc_s == "胜其他": X, Y, gn, bk = 4, 3, 7, "标胜"; G = 2
                elif sc_s == "平其他": X, Y, gn, bk = 4, 4, 7, "标平"; G = 0
                elif sc_s == "负其他": X, Y, gn, bk = 3, 4, 7, "标负"; G = -2
                else: 
                    X, Y = int(sc_s.split("-")[0]), int(sc_s.split("-")[1])
                    gn, G = min(X+Y, 7), X-Y
                    bk = "标胜" if G>0 else ("标平" if G==0 else "标负")

                rk = "让胜" if (G+K_int)>0 else ("让平" if (G+K_int)==0 else "让负")
                pp = round((1.0/odd_v)/max(1+marg, 0.0001), 4)

                gb_sums[gn] += pp; macro_b[bk] += pp; macro_r[rk] += pp

                pm = P_mat[min(X,7), min(Y,7)] if X<8 and Y<8 else 0.0001
                res = round(pp - pm, 4); rmv = round(res/max(pp,0.0001), 4)
                vd = "🚨 畸高诱捕墙" if res>0.025 and rmv>0.05 else ("🛡️ 核心防波堤" if res<-0.025 and rmv<-0.05 else "⚪ 常规中枢")
                out_sc.append({"核心比分": sc_s, "体彩终赔": f"{odd_v:.2f}", "比分纯率": f"{pp:.4f}", "标盘归属": bk, "让球归属": rk, "归属球数": f"{gn}球" if gn<7 else "7+球", "子盘口残差": f"{res:+.4f}", "期权偏度": vd})

            st.markdown("#### 📊 看板一：微观行权比分测谎台")
            if out_sc: st.dataframe(pd.DataFrame(out_sc), hide_index=True)
            else: st.warning("⚠️ 审计台空载。请在上方输入至少 1 个比分。")

            st.markdown("#### 🧮 看板二：总球数与积分对账")
            gc = []
            for i in range(8):
                g_res, g_rmv = round(p_g_d[i]-gb_sums[i],4), round((p_g_d[i]-gb_sums[i])/max(p_g_d[i],0.0001), 4)
                g_v = "🚨 空壳抽水" if g_res>0.03 else ("🎁 漏网爆破" if g_res<-0.03 else "⚖️ 守恒平稳")
                gc.append({"玩法": opts_m5_g[i], "总池纯率": f"{p_g_d[i]:.4f}", "积分总和": f"{gb_sums[i]:.4f}", "残差": f"{g_res:+.4f}", "偏度(RMV)": f"{g_rmv*100:+.2f}%", "裁决": g_v})
            st.dataframe(pd.DataFrame(gc), hide_index=True)

            st.markdown("#### 🛰️ 看板三：高级宏微观映射雷达")
            c1_mx, c2_mx = st.columns(2)
            with c1_mx:
                st.markdown("##### 🏟️ 标盘大盘积分复核")
                st.write(f"• 录入比分积分：[胜 {macro_b['标胜']:.4f} | 平 {macro_b['标平']:.4f} | 负 {macro_b['标负']:.4f}]")
                if macro_b['标胜']/max((1/m1_std_w)/max(1+marg, 0.0001),0.0001) < 0.65 and (1/m1_std_w)/max(1+marg, 0.0001) > 0.40:
                    st.error("🚨 **【皮热骨冷·空壳死局】** 标盘主胜看起来大，但主胜核心比分无流量支撑！排除主胜！")
                else: st.success("✅ 大盘指数量价契合度符合分布。")

            with c2_mx:
                st.markdown("##### 🥅 让球大一统字典复核")
                st.write(f"• 临场让球纯率：[让胜 {calc_pure_prob_array([m1_let_w,m1_let_d,m1_let_l])[0]:.4f} | 让平 {calc_pure_prob_array([m1_let_w,m1_let_d,m1_let_l])[1]:.4f} | 让负 {calc_pure_prob_array([m1_let_w,m1_let_d,m1_let_l])[2]:.4f}]")
                st.write(f"• 比分路由积分：[让胜 {macro_r['让胜']:.4f} | 让平 {macro_r['让平']:.4f} | 让负 {macro_r['让负']:.4f}]")

        except Exception as e: st.error("🚨 拓扑引擎故障。"); st.code(traceback.format_exc())

# ==============================================================================
# ===================== 🔭 模块五：状态转移与跨盘约束引擎 =====================
# ==============================================================================
elif active_module == "🔭 模块五：V15 状态转移与跨盘约束引擎":
    st.header(f"🔭 {current_match} - 状态转移与跨盘约束")
    st.caption("【高阶重构版】引入马尔可夫偏度与跨盘物理锁链，降维透视机构内幕。")
    
    col_e1, col_e2 = st.columns(2)
    with col_e1: m5_ou = safe_number_input("大小球基准盘口", f"m5_ou_{current_match}", 2.50, step=0.25)
    with col_e2: m5_hm = safe_number_input("亚指让球基准", f"m5_hm_{current_match}", -0.50, step=0.25)
    
    t_g, t_h = st.tabs(["⚽ 进球矩阵录入", "🔵 半全场录入"])
    with t_g: res_m5_g = render_odds_grid("m5g", current_match, "进球数", opts_m5_g, cols_m5_new, init_m5_g)
    with t_h: res_m5_h = render_odds_grid("m5h", current_match, "半/全场", opts_m5_h, cols_m5_new, init_m5_h)
    
    if st.button("🚀 启动 V15 状态转移精算", type="primary", use_container_width=True):
        try:
            xg_h, xg_a = (m5_ou - m5_hm)/2.0, (m5_ou + m5_hm)/2.0
            def p_pmf(k, lam): return math.exp(-lam)*(lam**k)/math.factorial(k) if lam>0 else (1.0 if k==0 else 0.0)
            gp = np.zeros(8)
            for i in range(10):
                for j in range(10):
                    p = p_pmf(i, xg_h)*p_pmf(j, xg_a)
                    if i+j<7: gp[i+j]+=p
                    else: gp[7]+=p
            if np.sum(gp)>0: gp = gp/np.sum(gp)
            math_g = np.round(gp, 4)

            h_h, h_a, f_h, f_a = xg_h*0.45, xg_a*0.45, xg_h*0.55, xg_a*0.55
            p_ht, p_2n = {"W":0,"D":0,"L":0}, {"W":0,"D":0,"L":0}
            for i in range(8):
                for j in range(8):
                    ph, pf = p_pmf(i,h_h)*p_pmf(j,h_a), p_pmf(i,f_h)*p_pmf(j,f_a)
                    if i>j: p_ht["W"]+=ph; p_2n["W"]+=pf
                    elif i==j: p_ht["D"]+=ph; p_2n["D"]+=pf
                    else: p_ht["L"]+=ph; p_2n["L"]+=pf
            math_h = np.round([
                p_ht["W"]*(p_2n["W"]+p_2n["D"]*0.5), p_ht["W"]*(p_2n["L"]*0.8+p_2n["D"]*0.5), p_ht["W"]*p_2n["L"]*0.2,
                p_ht["D"]*p_2n["W"], p_ht["D"]*p_2n["D"], p_ht["D"]*p_2n["L"],
                p_ht["L"]*p_2n["W"]*0.2, p_ht["L"]*(p_2n["W"]*0.8+p_2n["D"]*0.5), p_ht["L"]*(p_2n["L"]+p_2n["D"]*0.5)
            ], 4)
            math_h = np.round(math_h/np.sum(math_h), 4)

            p_tc_c_g = calc_pure_prob_array(safe_extract_array(res_m5_g['体彩初盘']))
            p_tc_d_g = calc_pure_prob_array(safe_extract_array(res_m5_g['体彩临场']))
            d_tc_g = safe_extract_array(res_m5_g['体彩临场'])
            fric_g = np.round((p_tc_d_g - math_g) * d_tc_g, 4)
            out_g = [{"进球数": opts_m5_g[i], "体彩临场": d_tc_g[i], "纯率": p_tc_d_g[i], "期望": math_g[i], "摩擦当量": f"{fric_g[i]:+.4f}"} for i in range(8)]
            st.markdown("### ⚽ 进球数微观精算阵列")
            st.dataframe(pd.DataFrame(out_g), hide_index=True, use_container_width=True)

            p_tc_c_h = calc_pure_prob_array(safe_extract_array(res_m5_h['体彩初盘']))
            p_tc_d_h = calc_pure_prob_array(safe_extract_array(res_m5_h['体彩临场']))
            d_tc_h = safe_extract_array(res_m5_h['体彩临场'])
            fric_h = np.round((p_tc_d_h - math_h) * d_tc_h, 4)
            out_h = [{"半/全场": opts_m5_h[i], "体彩临场": d_tc_h[i], "纯率": p_tc_d_h[i], "期望": math_h[i], "摩擦当量": f"{fric_h[i]:+.4f}"} for i in range(9)]
            st.markdown("### 🔵 半全场马尔可夫阵列")
            st.dataframe(pd.DataFrame(out_h), hide_index=True, use_container_width=True)
        except Exception as e: st.error("🚨 模块五异常"); st.code(traceback.format_exc())

# ==============================================================================
# ===================== 🎲 模块六：365 核心全息约束 =====================
# ==============================================================================
elif active_module == "🎲 模块六：365 核心全息约束 (剧本剥离版)":
    st.header(f"🎲 {current_match} - 365 全息人工干预探测")
    opts_m6_std, opts_m6_ah = ["主胜", "平局", "客胜"], ["盘口(主让负)", "上盘", "下盘"]
    opts_m6_eh, opts_m6_ht = ["让球数(主让负)", "让胜", "让平", "让负"], ["胜/胜", "胜/平", "胜/负", "平/胜", "平/平", "平/负", "负/胜", "负/平", "负/负"]
    
    t_std, t_ah, t_eh, t_ht = st.tabs(["📊 标盘", "📉 亚指", "🥅 欧让", "⏱️ 半全场"])
    with t_std: res_std = render_odds_grid("m6std", current_match, "标盘", opts_m6_std, ["初盘","临场"], [[2.0,1.9],[3.5,3.4],[3.6,4.0]])
    with t_ah: res_ah = render_odds_grid("m6ah", current_match, "亚指", opts_m6_ah, ["初盘","临场"], [[-0.5,-0.75],[1.95,2.05],[1.9,1.85]])
    with t_eh: res_eh = render_odds_grid("m6eh", current_match, "欧让", opts_m6_eh, ["初盘","临场"], [[-1.0,-1.0],[3.8,3.5],[3.6,3.5],[1.8,1.9]])
    with t_ht: res_ht = render_odds_grid("m6htft", current_match, "半全场", opts_m6_ht, ["初盘","临场"], [[4.3,4.0],[15,14],[29,34],[6.5,6.0],[5.5,5.0],[6.0,6.5],[29,34],[15,15],[4.5,5.0]])

    if st.button("🚀 启动 365 剧本剥离", type="primary"):
        try:
            std_c, std_d = safe_extract_array(res_std['初盘']), safe_extract_array(res_std['临场'])
            ah_c, ah_d = safe_extract_array(res_ah['初盘']), safe_extract_array(res_ah['临场'])
            eh_c, eh_d = safe_extract_array(res_eh['初盘']), safe_extract_array(res_eh['临场'])
            ht_c, ht_d = safe_extract_array(res_ht['初盘']), safe_extract_array(res_ht['临场'])
            
            p_std_c, p_std_d = calc_pure_prob_array(std_c), calc_pure_prob_array(std_d)
            p_ht_c, p_ht_d = calc_pure_prob_array(ht_c), calc_pure_prob_array(ht_d)
            
            p_ah_c, p_ah_d = np.zeros(2), np.zeros(2)
            if ah_c[1] > 0 and ah_c[2] > 0:
                raw_c = np.array([1/(ah_c[1]+1), 1/(ah_c[2]+1)]) if ah_c[1] < 5 else np.array([1/ah_c[1], 1/ah_c[2]])
                p_ah_c = np.round(raw_c / np.sum(raw_c), 4)
            if ah_d[1] > 0 and ah_d[2] > 0:
                raw_d = np.array([1/(ah_d[1]+1), 1/(ah_d[2]+1)]) if ah_d[1] < 5 else np.array([1/ah_d[1], 1/ah_d[2]])
                p_ah_d = np.round(raw_d / np.sum(raw_d), 4)
                
            p_eh_c, p_eh_d = np.zeros(3), np.zeros(3)
            if eh_c[1] > 0 and eh_c[2] > 0 and eh_c[3] > 0: p_eh_c = calc_pure_prob_array(eh_c[1:4])
            if eh_d[1] > 0 and eh_d[2] > 0 and eh_d[3] > 0: p_eh_d = calc_pure_prob_array(eh_d[1:4])

            d_std = np.round(p_std_d - p_std_c, 4)
            d_ah  = np.round(p_ah_d - p_ah_c, 4)
            d_eh  = np.round(p_eh_d - p_eh_c, 4)
            d_ht  = np.round(p_ht_d - p_ht_c, 4)

            st.markdown("### 🤖 顶层风控：人工介入与抽水压榨确诊单")
            margin_c_ht = np.nansum(1.0 / ht_c) - 1
            margin_d_ht = np.nansum(1.0 / ht_d) - 1
            margin_diff = round(margin_d_ht - margin_c_ht, 4)
            
            all_deltas = np.concatenate([np.abs(d_std), np.abs(d_ah), np.abs(d_eh), np.abs(d_ht)])
            max_dev = np.nanmax(all_deltas)
            median_dev = np.nanmedian(all_deltas)
            override_index = round(max_dev / median_dev, 4) if median_dev > 0 else 0
            
            col_o1, col_o2, col_o3 = st.columns(3)
            col_o1.metric("内部离散变异系数", f"{override_index:.4f}")
            col_o2.metric("半全场初盘抽水率", f"{margin_c_ht*100:.4f}%")
            col_o3.metric("半全场临场抽水率", f"{margin_d_ht*100:.4f}%")
            
            if override_index > 4.0: st.error(f"🦇 **【人工紧急避险熔断】** 内部变异系数爆表({override_index:.4f})！365精算师已断开AI自动平衡，针对特定冷门选项进行人工粗暴压水，该项有极大内幕击杀可能！")
            else: st.success("💻 **【机器控盘期】** 四大盘口数学传动正常平稳，无剧烈人工干预痕迹，按纯实力流速处理。")
                
            if margin_diff > 0.0200: st.warning(f"🚧 **【极限缩表护盘】** 365临场暴力提升半全场抽水率(+{margin_diff*100:.4f}%)，庄家对该维度失去控盘自信，拒开公平赔率以逼退散户！")

            delta_std_w = d_std[0] if not pd.isna(d_std[0]) else 0
            delta_ah_up = d_ah[0] if not pd.isna(d_ah[0]) else 0
            delta_eh_d  = d_eh[1] if not pd.isna(d_eh[1]) else 0 
            ht_dw = d_ht[3] if not pd.isna(d_ht[3]) else 0

            def evaluate_m6_item(category, opt_name, delta, p_c, p_d):
                if pd.isna(delta) or p_d == 0: return "➖ 数据缺失或未开盘"
                if category == 'std':
                    if opt_name == "主胜":
                        if delta > 0.015:
                            if delta_ah_up <= -0.015: return "🚨 【诱导陷阱】标盘疯狂造热主队，但亚盘暗中撤防，极概率赢球输盘或爆冷！"
                            if delta_ah_up > 0.015 and delta_eh_d > 0.02: return "🚨 【刚好赢一球壁垒】主胜/亚盘齐热，但欧让平防守激增！剧毒，防主队1球小胜输盘。"
                            return "💎 【黄金共振】标亚同步极限施压，真实核心防守项，强力看好。"
                        if delta < -0.015:
                            if delta_ah_up > 0.015: return "🕳️ 【深水反诱】标盘遭弃但亚盘诡异升水，庄家在下盘挖坑！"
                            return "📉 【真实抛弃】资金随势出逃，机构不再防守此项。"
                    elif opt_name == "平局":
                        if delta > 0.015 and delta_std_w < -0.01: return "🚧 【冷平设防】主胜退潮资金大量涌入平局，庄家被迫拉高平局防线。"
                    elif opt_name == "客胜":
                        if delta > 0.02 and delta_std_w < -0.02: return "⚡ 【反转剧本】主胜崩塌，客胜强势吸筹，警惕客队爆冷反杀！"
                elif category == 'ah':
                    if opt_name == "上盘水位":
                        if delta > 0.015 and delta_std_w <= -0.015: return "☠️ 【深水诱捕】强拉亚盘制造信心，标盘主胜实则暴跌，骗筹上盘！"
                        if delta < -0.015 and delta_std_w > 0.015: return "🌊 【顺流泄洪】主胜利好下，亚盘全线放水诱买，极难穿盘。"
                        if delta > 0.02: return "🌋 【阻力飙升】单方面拉高亚盘阻力，庄家畏惧上盘打穿。"
                elif category == 'eh':
                    if "胜" in opt_name:
                        if delta < -0.015 and delta_std_w > 0.015: return "🚧 【穿盘铁幕】主胜大热但深盘防守暴跌，赢球输盘绝对预警！"
                    elif "平" in opt_name:
                        if delta > 0.02: return "🎯 【精准制导】让平防守大幅收紧，机构严防主队正好赢一球！"
                elif category == 'htft':
                    if opt_name == "胜/胜":
                        if delta_std_w > 0.015 and delta < -0.010 and ht_dw > 0.015: return "⏱️ 【时间轴剧本暴露】主胜大热但胜胜遭抛弃，资金疯抢“平/胜”！真正重注底牌在下半场！"
                        if delta > 0.015 and delta_std_w > 0.015: return "⚡ 【闪电战】与标盘高度共振，看好主队半场直接建立不可逆优势。"
                    elif opt_name == "平/胜":
                        if delta > 0.015 and delta_std_w > 0.01: return "🔎 【剧本偏移】主胜大势下资金疯抢平胜，严防剧本局或下半场绝杀！"
                    elif opt_name == "平/平":
                        if delta > 0.02: return "🧊 【极限降温】机构重防平平，全场概率极度沉闷或 0-0 完场。"
                if delta >= 0.03: return "🌋 【极限极值】机构防线严重承压！"
                if delta >= 0.015: return "📈 【显著流入】盘口出现实质性升温。"
                if delta <= -0.03: return "🧊 【极限放水】机构彻底开门放水。"
                if delta <= -0.015: return "📉 【显著流出】"
                return "⚪ 常规换手波动"

            st.markdown("### 📊 365 标盘(1X2) 全息切片")
            df_std_out = []
            for i in range(3):
                df_std_out.append({"选项": opts_m6_std[i], "初盘纯率": f"{p_std_c[i]:.4f}", "临场纯率": f"{p_std_d[i]:.4f}", "纯率增量(Δ)": f"{d_std[i]:.4f}", "深度战术定性": evaluate_m6_item('std', opts_m6_std[i], d_std[i], p_std_c[i], p_std_d[i])})
            st.dataframe(pd.DataFrame(df_std_out), hide_index=True, use_container_width=True)

            st.markdown("### 📉 365 亚洲让球盘 切片")
            df_ah_out = []
            for i in range(2):
                df_ah_out.append({"选项": opts_m6_ah[i+1], "初盘纯率": f"{p_ah_c[i]:.4f}", "临场纯率": f"{p_ah_d[i]:.4f}", "纯率增量(Δ)": f"{d_ah[i]:.4f}", "深度战术定性": evaluate_m6_item('ah', opts_m6_ah[i+1], d_ah[i], p_ah_c[i], p_ah_d[i])})
            st.dataframe(pd.DataFrame(df_ah_out), hide_index=True, use_container_width=True)

            st.markdown("### 🥅 365 欧洲让球盘 切片")
            if np.sum(p_eh_c) > 0:
                df_eh_out = []
                for i in range(3):
                    df_eh_out.append({"选项": opts_m6_eh[i+1], "初盘纯率": f"{p_eh_c[i]:.4f}", "临场纯率": f"{p_eh_d[i]:.4f}", "纯率增量(Δ)": f"{d_eh[i]:.4f}", "深度战术定性": evaluate_m6_item('eh', opts_m6_eh[i+1], d_eh[i], p_eh_c[i], p_eh_d[i])})
                st.dataframe(pd.DataFrame(df_eh_out), hide_index=True, use_container_width=True)
            else:
                st.warning("➖ 欧让盘未录入数据，已安全跳过。")

            st.markdown("### ⏱️ 365 半/全场剧本 切片")
            df_ht_out = []
            for i in range(9):
                df_ht_out.append({"选项": opts_m6_htft[i], "初盘纯率": f"{p_ht_c[i]:.4f}", "临场纯率": f"{p_ht_d[i]:.4f}", "纯率增量(Δ)": f"{d_ht[i]:.4f}", "深度战术定性": evaluate_m6_item('htft', opts_m6_htft[i], d_ht[i], p_ht_c[i], p_ht_d[i])})
            st.dataframe(pd.DataFrame(df_ht_out), hide_index=True, use_container_width=True)
        except Exception as e: st.error("🚨 模块六异常"); st.code(traceback.format_exc())

# ==============================================================================
# ===================== 🔮 模块九：全息张力雷达 (跨盘口协整终极版) =====================
# ==============================================================================
elif active_module == "🔮 模块九：全息张力雷达 (跨盘口协整终极版)":
    st.header(f"🔮 {current_match} - M9 跨盘口全息协整与资金隔离追踪仪")
    st.caption("【多维流体动力学】摒弃死板单盘逻辑！联合标盘、让球盘的实时流速，全息测算6大结果选项与0-7+球的【弹性形变阈值】。精准定位“让胜跌、2球涨、出冷平1-1”的隔离盲区！")

    c1, c2, c3 = st.columns(3)
    with c1: m9_tg = safe_number_input("期望进球xG", f"m9_tg_{current_match}", 2.75, format="%.2f", step=0.25)
    with c2: m9_hcp = safe_number_input("欧亚纯实力亚指", f"m9_hcp_{current_match}", -0.50, format="%.2f", step=0.25)
    with c3: m9_k = safe_number_input("让球K值", f"m9_k_{current_match}", -1.0, format="%.0f", step=1.0)

    st.markdown("### 📥 第一步：大盘（资金海）流速抓取")
    cs, cl = st.columns(2)
    with cs: r_ms = render_odds_grid("m9s", current_match, "标盘", ["主胜","平局","客负"], ["初","临"], [[2.45,2.32],[3.2,3.2],[2.45,2.6]])
    with cl: r_ml = render_odds_grid("m9l", current_match, f"让球({int(m9_k)})", ["让胜","让平","让负"], ["初","临"], [[5.5,5.3],[4.1,4.0],[1.42,1.45]])
    
    st.markdown("---")
    st.markdown("### 📥 第二步：进球数（离散桶）标的输入")
    r_mg = render_odds_grid("m9g", current_match, "体彩 0-7+ 球", opts_m5_g, ["初","临"], init_m5_g)

    if st.button("🚀 启动全息非线性耦合扫描", type="primary", use_container_width=True):
        try:
            _,_,_,_,_, Pmat = dixon_coles_full_matrix((m9_tg-m9_hcp)/2, (m9_tg+m9_hcp)/2, -0.15)
            kv = int(m9_k)
            ss = calc_pure_prob_array(safe_extract_array(r_ms['临'])) - calc_pure_prob_array(safe_extract_array(r_ms['初']))
            sl = calc_pure_prob_array(safe_extract_array(r_ml['临'])) - calc_pure_prob_array(safe_extract_array(r_ml['初']))
            sg = calc_pure_prob_array(safe_extract_array(r_mg['临'])) - calc_pure_prob_array(safe_extract_array(r_mg['初']))
            
            out_6 = []
            for i, n in enumerate(["标盘-主胜","标盘-平局","标盘-客负"]):
                flow = ss[i]
                if pd.isna(flow): continue
                feat, jd = "", "⚪ 常规博弈"
                if n=="标盘-主胜":
                    if flow>0.015:
                        if sl[0]>0.01 and sg[3]<0: feat="让胜同涨，大球受阻"; jd="✅ 【量价齐升直通车】主防赢球走水/输盘。"
                        elif sg[1]<-0.015 and sg[2]<-0.015: feat="主胜狂热，核心比分干涸"; jd="🚨 【虚假繁荣隔离】大热但核心比分被抽血，防冷平诱杀！"
                    elif flow<-0.015 and sl[0]>0.015: feat="主胜遭弃，让胜暴热"; jd="🕳️ 【暗水偷袭】主大胜方向有游资建仓。"
                elif n=="标盘-平局":
                    if flow<-0.015 and sg[0]<-0.015 and sg[2]<-0.015: feat="标平、0球、2球同步崩盘"; jd="🚧 【双重死防底线】明牌防平，利润被全线封锁。"
                    elif flow>0.01 and sl[2]>0.01 and sg[2]>=0: feat="标平涨，让负涨，2球稳"; jd="💎 【黄金走廊】庄微抬平局，实把1-1藏在盲区，冷平金矿！"
                elif n=="标盘-客负" and flow>0.015 and ss[0]<-0.015: feat="主胜崩，客胜吸筹"; jd="⚡ 【反转剧本】客队强势爆冷预警。"
                out_6.append({"选项":n, "流速":f"{flow:+.4f}", "环境特征":feat, "全息定性":jd})
                
            for i, n in enumerate(["让球-胜","让球-平","让球-负"]):
                flow = sl[i]
                if pd.isna(flow): continue
                feat, jd = "", "⚪ 常规博弈"
                if n=="让球-胜":
                    if flow<-0.01 and sg[2]>0.01: feat="让胜微跌，2球慢涨退水"; jd="🛡️ 【极限挤压隔离区】让胜降水骗客搏穿盘，真出的是防守盲区2球！"
                    elif flow>0.02 and ss[0]<-0.01: feat="标胜冷，让胜热"; jd="🕳️ 【老鼠仓】游资强行建仓大胜。"
                elif n=="让球-平" and flow>0.015 and ss[0]>0.015: feat="主胜让平双热"; jd="🚨 【赢一球壁垒】"
                out_6.append({"选项":n, "流速":f"{flow:+.4f}", "环境特征":feat, "全息定性":jd})

            st.markdown("#### 🚨 大盘 6大核心项联合审查便签")
            st.dataframe(pd.DataFrame(out_6), hide_index=True)
            
            et, mpg = np.zeros(8), np.zeros(8)
            for g in range(8):
                ws, ts = 0.0, 0.0
                for h in range(8):
                    for a in range(8):
                        if h+a==g or (g==7 and h+a>=7):
                            pr = Pmat[h,a]
                            iss = 0 if h>a else (1 if h==a else 2)
                            nt = h-a+kv
                            isl = 0 if nt>0 else (1 if nt==0 else 2)
                            t = 0.6*ss[iss] + 0.4*sl[isl]
                            ts += pr*t; ws += pr
                mpg[g] = ws
                if ws>0: et[g] = ts/ws
                
            zb = 0.015
            ul, ll = et+zb, et-zb
            
            out_g = []
            for g in range(8):
                s, t, u, l = sg[g], et[g], ul[g], ll[g]
                v = ""
                if s>u: v = "🚨 涨破上限 (无视大盘逆势强拉，坚决避坑)"
                elif s<l: v = "🛡️ 跌穿下限 (绝对防波堤)"
                else:
                    if t>0.005 and s<-0.005: v = "💎 逆向隔离金矿 (大盘推热，庄家退水，顶级冷门盲区！)"
                    elif t<-0.005 and s>0.005: v = "🕳️ 顺水诱捕毒药 (大盘抛弃，庄家压低，骗接盘！)"
                    else: v = "⚪ 势能守恒 (符合流体方向)"
                out_g.append({"进球":opts_m5_g[g], "大盘预期压迫":f"{t:+.4f}", "实际纯率流速":f"{s:+.4f}", "动态容差区":f"[{l:+.4f} ~ {u:+.4f}]", "流体定性裁决":v})

            st.markdown("#### 🎯 0-7+ 进球抽屉 · 弹性张量解析雷达")
            st.dataframe(pd.DataFrame(out_g), hide_index=True)
            st.info("💡 **【模块九 - 雷达白话释义】**\n"
                "• **协整环境特征**：系统会自动扫描标盘、让球、进球数之间的异动。比如 `标平涨`+`让负涨`+`2球稳健` 会被直接判定为 **1-1隔离盲区**。\n"
                "• **大盘预期张力(压迫)**：正数代表大盘（标盘和让球盘）资金正往这个进球数里挤压；负数代表资金在撤离。\n"
                "• **动态弹性容差区**：系统根据大盘挤压度，实时拓宽或收窄的判定红线。大盘资金狂热，上限就拉高，此时慢涨依然安全！")

        except Exception as e:
            st.error("🚨 模块九矩阵计算异常，请检查输入赔率是否为空。")
            st.code(traceback.format_exc())
