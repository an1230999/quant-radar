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
    </style>
""", unsafe_allow_html=True)

# 💣 终极核弹级清理缓存 (回滚实战经典增强版)
if "FX2_V_FINAL_ROLLBACK_V1" not in st.session_state:
    st.session_state.clear()
    st.session_state["FX2_V_FINAL_ROLLBACK_V1"] = True

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

st.title("🏦 FX2 机构级全维量化终端 (经典重铸改良版)")

# ================= 3. 核心数学引擎 (强制4位小数精度) =================
def calc_pure_prob_array(arr):
    arr = np.array(arr, dtype=float)
    if pd.isna(arr).any() or (arr <= 0).any():
        return np.full(len(arr), np.nan)
    raw = 1.0 / arr
    return np.round(raw / np.nansum(raw), 4)

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

# ================= 4. 🌟 终极钛合金防闪退矩阵构建器 =================
def safe_number_input(label, state_key, default_val, format="%.4f", step=0.0010):
    wid_key = "wid_" + state_key
    raw_val = st.session_state.get(state_key, default_val)
    try:
        clean_val = float(raw_val)
        if math.isnan(clean_val): clean_val = float(default_val)
    except:
        clean_val = float(default_val)
    st.session_state[state_key] = clean_val
    
    def cb(): st.session_state[state_key] = st.session_state[wid_key]
    return st.number_input(label, value=clean_val, format=format, step=step, key=wid_key, on_change=cb)

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

# ================= 5. 底座初始参数 =================
opts_m1 = ["标盘-胜", "标盘-平", "标盘-负", "让盘-胜", "让盘-平", "让盘-负"]
cols_m1 = ["初盘", "临场"]
init_m1 = [[2.45, 2.32], [3.20, 3.20], [2.45, 2.60], [5.50, 5.30], [4.10, 4.00], [1.42, 1.45]]

opts_m2 = ["0球", "1球", "2球", "3球", "4球", "5球", "6球", "7+球", "大球", "小球"]
cols_m2 = ["初盘(C)", "T-60(J)", "临场(D)"]
init_m2 = [[15.0, 15.5, 15.5], [5.5, 5.8, 5.9], [3.6, 3.7, 3.8], [3.45, 3.30, 3.10], [4.9, 4.8, 4.7], [8.25, 8.4, 8.50], [15.0, 15.5, 16.0], [22.0, 23.0, 24.0], [0.65, 0.60, 0.50], [1.75, 1.40, 1.15]]

opts_m3 = ["标准盘", "让球盘"]
cols_m3 = ["胜", "平", "负", "国彩让球数"]
init_m3 = [[2.32, 3.20, 2.60, 0.0], [5.30, 4.00, 1.45, -1.0]]

opts_m5_g = ["0球", "1球", "2球", "3球", "4球", "5球", "6球", "7+球"]
cols_m5_new = ["365初盘", "365临场", "马会初盘", "马会临场", "体彩初盘", "体彩临场"]
init_m5_g = [[17.0, 17.0, 15.0, 15.0, 17.0, 17.0], [6.5, 6.0, 5.8, 5.5, 6.5, 6.0], [4.0, 4.0, 3.9, 3.8, 4.0, 3.9], [4.0, 3.8, 3.7, 3.6, 3.65, 3.5], [5.0, 5.0, 4.35, 4.2, 4.25, 4.2], [8.0, 8.5, 6.6, 6.5, 7.0, 7.5], [15.0, 16.0, 11.0, 12.0, 12.0, 13.0], [19.0, 21.0, 16.0, 17.0, 18.0, 20.0]]
opts_m5_h = ["胜胜", "胜平", "胜负", "平胜", "平平", "平负", "负胜", "负平", "负负"]
init_m5_h = [[4.3, 4.1, 4.0, 3.8, 3.7, 3.6], [13.0, 13.5, 12.5, 13.0, 13.0, 14.0], [23.0, 25.0, 23.0, 24.0, 26.0, 28.0], [6.5, 6.0, 6.0, 5.8, 6.6, 6.2], [6.0, 5.5, 5.4, 5.2, 5.8, 5.4], [6.0, 6.5, 5.8, 6.2, 6.6, 7.0], [23.0, 25.0, 24.0, 26.0, 28.0, 30.0], [13.0, 13.5, 12.5, 13.0, 13.0, 14.0], [4.0, 3.8, 3.6, 3.5, 3.5, 3.4]]

matches_list = ["⚽ 比赛 1", "⚽ 比赛 2", "⚽ 比赛 3", "⚽ 比赛 4", "⚽ 比赛 5"]

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

# ================= 6. 导航矩阵 =================
st.sidebar.title("🧭 控制台")
current_match = st.radio("🏆 独立沙盒切换：", matches_list, horizontal=True)

active_module = st.sidebar.radio("=== 分析体系 ===", [
    "🏆 模块七：世界杯全息狙击终端 (经典TC主导)", 
    "⚔️ 模块一：欧亚大盘体系 (精准收口版)", 
    "⚽ 模块二：进球数多维风控", 
    "🎫 模块三：高阶工具 (原味DC矩阵)", 
    "🧬 模块四：异构交叉与零和对冲", 
    "🔭 模块五：V15 状态转移与跨盘约束引擎",
    "🎲 模块六：365 核心全息约束 (剧本剥离版)"
])

# ==============================================================================
# ===================== 🏆 模块七：经典回滚增强版 =====================
# ==============================================================================
if active_module == "🏆 模块七：世界杯全息狙击终端 (经典TC主导)":
    st.header(f"🏆 {current_match} - 体彩绝对主导·世界杯全息中控台")
    st.caption("【经典重铸说明】满血恢复 比分雷达 与 M1 合成偏差测谎，保留经典敞口位移判断体系。")

    # --- 战场环境约束开关 ---
    st.markdown("### 🎛️ 世界杯战场环境约束")
    col_sw1, col_sw2 = st.columns(2)
    with col_sw1:
        is_knockout = st.toggle("⚔️ 开启【淘汰赛平局放大器】 (底层自动倾斜 0-0/1-1 等沉闷比分权重)", value=False)
    with col_sw2:
        is_tacit = st.toggle("🤝 开启【默契算分局排雷】 (关闭合成测谎，防止数学失真报错)", value=False)
    
    st.markdown("---")
    
    # --- 基础数据面板录入 ---
    st.markdown("### 📥 核心战斗序列录入区")
    st.info("📌 **体彩(TC) 全局核心基底**：请输入体彩官方的初盘与临场赔率，作为 M1 满血版显微镜运算的基础源。")
    
    col_tg1, col_tg2, col_tg3 = st.columns(3)
    with col_tg1: tg = safe_number_input("全局大小球(进球预期)", f"m7_tg_{current_match}", 2.50, format="%.2f", step=0.25)
    with col_tg2: hcp = safe_number_input("机构初指亚盘(主让为负)", f"m7_hcp_{current_match}", -0.50, format="%.2f", step=0.25)
    with col_tg3: tc_let = safe_number_input("体彩实际让球数", f"m7_tclet_{current_match}", -1.0, format="%.0f", step=1.0)
    
    opts_m7_tc_main = ["体彩 标盘-胜", "体彩 标盘-平", "体彩 标盘-负", "体彩 让球-胜", "体彩 让球-平", "体彩 让球-负"]
    res_m7_tc_main = render_odds_grid("m7_tc_main", current_match, "体彩(TC) 全局核心基底", opts_m7_tc_main, ["初盘", "临场"], [[1.85, 1.80], [3.30, 3.40], [3.80, 4.00], [3.50, 3.40], [3.40, 3.30], [1.90, 1.95]])
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.info("📌 **外维对冲数据池 (365 & 马会)**：用于执行 M4 三向敞口对冲 与 M5 空间共识复核。")
    col_in1, col_in2 = st.columns(2)
    with col_in1:
        res_m7_365 = render_odds_grid("m7_365", current_match, "365 全球基底 (胜/平/负)", ["主胜", "平局", "客胜"], ["初盘", "临场"], [[2.00, 1.95], [3.40, 3.50], [3.60, 3.80]])
    with col_in2:
        res_m7_hk = render_odds_grid("m7_hk", current_match, "马会 亚洲基底 (胜/平/负)", ["主胜", "平局", "客胜"], ["初盘", "临场"], [[1.95, 1.90], [3.20, 3.30], [3.50, 3.70]])
        
    st.markdown("---")
    st.markdown("### 🔭 体彩异常设防比分扫描器")
    st.caption("【经典回滚】输入你认为最可能爆冷的几个核心比分，结合体彩赔率进行极限防线反套。")
    score_opts = ["1-0", "0-0", "1-1", "2-1", "0-1", "2-0"]
    res_m7_scores = render_odds_grid("m7_scores", current_match, "核心比分 体彩临场赔率录入", ["体彩赔率"], score_opts, [[7.0, 9.0, 6.5, 8.0, 10.0, 9.5]])

    calc_key_m7 = f"m7_calc_{current_match}"
    if calc_key_m7 not in st.session_state: st.session_state[calc_key_m7] = False
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚀 执行体彩核心全息透视与排雷", type="primary", use_container_width=True, key=f"btn_{calc_key_m7}"):
        st.session_state[calc_key_m7] = True

    if st.session_state[calc_key_m7]:
        st.markdown("---")
        try:
            tc_c_raw = safe_extract_array(res_m7_tc_main["初盘"])
            tc_d_raw = safe_extract_array(res_m7_tc_main["临场"])
            
            tc_std_c, tc_let_c = tc_c_raw[0:3], tc_c_raw[3:6]
            tc_std_d, tc_let_d = tc_d_raw[0:3], tc_d_raw[3:6]
            
            b365_c = safe_extract_array(res_m7_365["初盘"])
            b365_d = safe_extract_array(res_m7_365["临场"])
            
            hk_c = safe_extract_array(res_m7_hk["初盘"])
            hk_d = safe_extract_array(res_m7_hk["临场"])
            
            p_tc_std_c, p_tc_std_d = calc_pure_prob_array(tc_std_c), calc_pure_prob_array(tc_std_d)
            p_tc_let_c, p_tc_let_d = calc_pure_prob_array(tc_let_c), calc_pure_prob_array(tc_let_d)
            
            p_365_c, p_365_d = calc_pure_prob_array(b365_c), calc_pure_prob_array(b365_d)
            p_hk_c, p_hk_d = calc_pure_prob_array(hk_c), calc_pure_prob_array(hk_d)

            z2, z3, z4 = 0.0100, 0.0070, 0.0040

            # ==========================================
            # 板块一：体彩满血版 6项数据显微镜 (恢复经典测谎)
            # ==========================================
            st.markdown("### 🔬 体彩核心 6 项满血版显微镜 (保留原M1全部运算深度)")
            
            d_tc_std = np.round(p_tc_std_d - p_tc_std_c, 4)
            d_tc_let = np.round(p_tc_let_d - p_tc_let_c, 4)
            deltas = np.concatenate([d_tc_std, d_tc_let])
            
            s_theo, u_theo = np.full(6, np.nan), np.full(6, np.nan)
            t_open, v_open, w_traj, aa_hedge = ["⚪ 无对照"]*6, ["⚪ 无对照"]*6, ["⚪ 无对照"]*6, ["⚪ 动量未达标"]*6
            
            p_c_all = np.concatenate([p_tc_std_c, p_tc_let_c])
            p_d_all = np.concatenate([p_tc_std_d, p_tc_let_d])

            if tc_let < 0:
                s_theo[0], u_theo[0] = p_c_all[3] + p_c_all[4], p_d_all[3] + p_d_all[4]
                s_theo[1], u_theo[1] = p_c_all[5] - p_c_all[2], p_d_all[5] - p_d_all[2]
                s_theo[2], u_theo[2] = p_c_all[5] - p_c_all[1], p_d_all[5] - p_d_all[1]
                s_theo[3], u_theo[3] = p_c_all[0] - p_c_all[4], p_d_all[0] - p_d_all[4]
                s_theo[4], u_theo[4] = p_c_all[0] - p_c_all[3], p_d_all[0] - p_d_all[3]
                s_theo[5], u_theo[5] = p_c_all[1] + p_c_all[2], p_d_all[1] + p_d_all[2]
            elif tc_let > 0:
                s_theo[0], u_theo[0] = p_c_all[3] - p_c_all[1], p_d_all[3] - p_d_all[1]
                s_theo[1], u_theo[1] = p_c_all[3] - p_c_all[0], p_d_all[3] - p_d_all[0]
                s_theo[2], u_theo[2] = p_c_all[4] + p_c_all[5], p_d_all[4] + p_d_all[5]
                s_theo[3], u_theo[3] = p_c_all[0] + p_c_all[1], p_d_all[0] + p_d_all[1]
                s_theo[4], u_theo[4] = p_c_all[2] - p_c_all[5], p_d_all[2] - p_d_all[5]
                s_theo[5], u_theo[5] = p_c_all[2] - p_c_all[4], p_d_all[2] - p_d_all[4]

            s_theo, u_theo = np.round(s_theo, 4), np.round(u_theo, 4)
            for i in range(6):
                c_prob, s_t, d_prob, u_t = p_c_all[i], s_theo[i], p_d_all[i], u_theo[i]
                if not pd.isna(s_t) and not pd.isna(u_t) and not pd.isna(c_prob):
                    diff_c, diff_d = c_prob - s_t, d_prob - u_t
                    t_open[i] = "🔻 极限低开" if diff_c >= z2 else "📉 显著低开" if diff_c >= z3 else "🔺 极限高开" if diff_c <= -z2 else "📈 显著高开" if diff_c <= -z3 else "⚪ 体系平衡"
                    v_open[i] = "🔻 极限低开" if diff_d >= z2 else "📉 显著低开" if diff_d >= z3 else "🔺 极限高开" if diff_d <= -z2 else "📈 显著高开" if diff_d <= -z3 else "⚪ 体系平衡"
                    traj = diff_d - diff_c
                    w_traj[i] = "🚨 剧烈砸盘" if traj >= 0.02 else "📉 步步紧逼" if traj >= 0.01 else "🚨 疯狂拉高" if traj <= -0.02 else "📈 门槛放宽" if traj <= -0.01 else "⚪ 伪装平稳"
                    struct = round(diff_d, 4)
                    if deltas[i] >= z3: aa_hedge[i] = "✅ 黄金共振" if struct >= z4 else "🚨 致命背离" if struct <= -z4 else "🟡 结构中立"
                    elif deltas[i] <= -z3: aa_hedge[i] = "🎁 暗度陈仓" if struct >= z4 else "🧊 真实抛弃" if struct <= -z4 else "⚪ 结构中立"
                    else: aa_hedge[i] = "🌋 静态死防" if struct >= z3 else "🕸️ 静态诱网" if struct <= -z3 else "⚪ 动量未达标"

            # 经典测谎仪回归
            m1_tags = ["⚪ 无异常"] * 6
            if not is_tacit:
                if tc_let == -1.0 and tc_std_d[0] > 0 and tc_let_d[0] > 0:
                    synthetic_diff = tc_std_d[0] - tc_let_d[0]
                    if deltas[0] > 0.015 and synthetic_diff > 0.25: m1_tags[0] = "🔴 虚假造热(无实质防守)"
                    elif deltas[0] > 0.010 and synthetic_diff < 0.15: m1_tags[0] = "🟢 真实深度设防"
            else:
                m1_tags = ["➖ 默契局屏蔽测谎"] * 6

            df_6x = pd.DataFrame({
                "体彩选项": ["标盘-主胜", "标盘-平局", "标盘-客胜", "让球-胜", "让球-平", "让球-负"],
                "初盘纯率": p_c_all,
                "临场纯率": p_d_all,
                "流速(Delta)": deltas,
                "理论基底概率": s_theo,
                "初盘定性": t_open,
                "轨迹研判(重要)": w_traj,
                "时空双杀(M1核)": aa_hedge,
                "合成偏差": m1_tags
            })
            st.dataframe(df_6x.style.format({"初盘纯率": "{:.4f}", "临场纯率": "{:.4f}", "流速(Delta)": "{:.4f}", "理论基底概率": "{:.4f}"}), hide_index=True, use_container_width=True)

            # ==========================================
            # 板块二：三向敞口刺透 (M4 经典版重现)
            # ==========================================
            st.markdown("### 🏦 三极管对冲刺透：多维风险敞口矩阵")
            
            def calc_liab_shift(prob_c, odds_c, prob_d, odds_d):
                liab_c = prob_c * odds_c
                liab_d = prob_d * odds_d
                return np.round(liab_d - liab_c, 4)
                
            shift_tc = calc_liab_shift(p_tc_std_c, tc_std_c, p_tc_std_d, tc_std_d)
            shift_365 = calc_liab_shift(p_365_c, b365_c, p_365_d, b365_d)
            shift_hk = calc_liab_shift(p_hk_c, hk_c, p_hk_d, hk_d)
            
            m4_alerts = ["⚪ 常规"] * 3
            for i in range(3):
                if shift_tc[i] > 0.03 and shift_365[i] < 0.01:
                    m4_alerts[i] = "💣 体彩单边资金堰塞湖 (杀猪诱导)"
                elif shift_tc[i] > 0.03 and shift_365[i] > 0.02:
                    m4_alerts[i] = "🛡️ 全球同步重注涌入 (真实设防)"
                elif shift_tc[i] < -0.03:
                    m4_alerts[i] = "🧊 体彩极速退守放水"
                    
            df_m4 = pd.DataFrame({
                "赛果": ["主胜", "平局", "客胜"],
                "体彩(TC)敞口位移": shift_tc,
                "365 敞口位移": shift_365,
                "马会(HK)敞口位移": shift_hk,
                "资金流向定性": m4_alerts
            })
            st.dataframe(df_m4.style.format({"体彩(TC)敞口位移": "{:.4f}", "365 敞口位移": "{:.4f}", "马会(HK)敞口位移": "{:.4f}"}), hide_index=True)

            # ==========================================
            # 板块三：体彩异常比分防范雷达 (满血复活版)
            # ==========================================
            st.markdown("### 🔭 机构真实底牌：体彩异常设防比分扫描")
            xg_h, xg_a = (tg - hcp) / 2, (tg + hcp) / 2
            df_m, ph2, ph1, pdr, pau, P_col_rounded = dixon_coles_full_matrix(xg_h, xg_a, -0.15, is_knockout)
            
            score_book_odds = safe_extract_array([res_m7_scores[sc][0] for sc in score_opts])
            score_book_probs = calc_pure_prob_array(score_book_odds) 
            
            score_alerts = []
            radar_rows = []
            for i, sc in enumerate(score_opts):
                try:
                    h_g, a_g = int(sc.split('-')[0]), int(sc.split('-')[1])
                    theo_p = round(P_col_rounded[h_g, a_g], 4)
                    real_p = round(score_book_probs[i], 4) if not pd.isna(score_book_probs[i]) else 0
                    
                    ratio = real_p / theo_p if theo_p > 0 else 0
                    tag = "⚪ 正常"
                    
                    if ratio > 1.35 and real_p > 0:
                        tag = "🚨 极端设防 (防打出)"
                        score_alerts.append(f"【比分 {sc}】: 模型理论概率仅 {theo_p*100:.2f}%，体彩强行将其防守率拔高至 {real_p*100:.2f}%！体彩惧怕此比分！")
                    elif ratio < 0.65 and real_p > 0:
                        tag = "🕳️ 高赔诱捕 (不防范)"
                        
                    radar_rows.append({
                        "核心比分": sc,
                        "体彩开出赔率": score_book_odds[i],
                        "理论纯净率": theo_p,
                        "体彩真实防守率": real_p,
                        "体彩设防倍率": round(ratio, 2),
                        "雷达定性": tag
                    })
                except Exception:
                    continue
                
            st.dataframe(pd.DataFrame(radar_rows).style.format({"理论纯净率": "{:.4f}", "体彩真实防守率": "{:.4f}", "体彩开出赔率": "{:.2f}"}), hide_index=True)
            if score_alerts:
                for alert in score_alerts: st.error(alert)

            # ==========================================
            # 板块四：三极管空间拓扑探测 (经典距离版)
            # ==========================================
            st.markdown("### 🧬 最终复核：三极管空间拓扑探测 (标盘离散度)")
            
            d_tc_365 = round(float(np.linalg.norm(np.nan_to_num(p_tc_std_d) - np.nan_to_num(p_365_d))), 4)
            d_hk_365 = round(float(np.linalg.norm(np.nan_to_num(p_hk_d) - np.nan_to_num(p_365_d))), 4)
            d_tc_hk  = round(float(np.linalg.norm(np.nan_to_num(p_tc_std_d) - np.nan_to_num(p_hk_d))), 4)
            
            col_t1, col_t2, col_t3 = st.columns(3)
            col_t1.metric("体彩情绪偏离度 (vs 365)", f"{d_tc_365:.4f}")
            col_t2.metric("马会风控偏离度 (vs 365)", f"{d_hk_365:.4f}")
            col_t3.metric("亚洲内部断层 (体彩 vs 马会)", f"{d_tc_hk:.4f}")
            
            st.markdown("#### 📝 三方庄家底牌剧本定性：")
            if d_tc_365 > 0.05 and d_hk_365 <= 0.03:
                st.error("🌪️ **【剧本一：大陆情绪陷阱】** 365与马会保持冷静，体彩利用球迷情绪单方面疯狂造热！凡体彩大幅降水项全部为诱捕毒饵！")
            elif d_hk_365 > 0.05 and d_tc_365 <= 0.03:
                st.warning("🦇 **【剧本二：亚洲核心防范】** 马会独家大幅收紧防线，脱离全球精算轨道。极大可能代表亚洲核心内幕意图，跟进马会方向！")
            elif d_tc_hk <= 0.025 and d_tc_365 > 0.045:
                st.info("🚧 **【剧本三：亚洲联合壁垒】** 体彩与马会高度重合，联合对抗365模型。亚洲区庄家真实防范意图明显，该区域项打出概率极高，顺势而为！")
            elif d_tc_365 <= 0.035 and d_hk_365 <= 0.035:
                st.success("✅ **【剧本四：全息共振】** 三方机构纯概率空间协方差极小，步调完全一致。市场无情绪扭曲，请直接依靠上方 6 大矩阵的数据流速自行定夺！")
            else:
                st.markdown("> *当前三极管处于混沌状态，各方资金剧烈换手中，请密切关注上方 M4 的敞口警报。*")

        except Exception as e:
            st.error("🚨 模块七运行异常，请检查填写数据。")
            st.code(traceback.format_exc())

# ==============================================================================
# ===================== ⚔️ 模块一：欧亚大盘体系 (精准收口版) =====================
# ==============================================================================
elif active_module == "⚔️ 模块一：欧亚大盘体系 (精准收口版)":
    st.header(f"⚔️ {current_match} - 欧亚大盘体系 (精准收口改良版)")
    st.caption("【唯一核心轴诊断】彻底终结“多项同时报警”的错乱感。系统将强制抓取唯一主导矢量，过滤同向防守噪音。")
    tab1, tab2, tab3 = st.tabs(["🟢 浅水区", "🟡 中水区", "🔴 深水区"])
    
    def render_main_handicap_ui(wl, match_id):
        z2, z3, z4, z5, z6, _ = render_thresholds("m1", match_id, wl)
        col_ext1, _ = st.columns(2)
        with col_ext1: h_val = safe_number_input(f"主队亚指让球数", f"m1_hcp_{match_id}_{wl}", -1.0, format="%.2f", step=0.25)
            
        res_m1 = render_odds_grid("m1", match_id, wl, opts_m1, cols_m1, init_m1)
        calc_key = f"m1_calc_{match_id}_{wl}"
        if calc_key not in st.session_state: st.session_state[calc_key] = False
        if st.button(f"🚀 执行 {wl} 精算", type="primary", key=f"btn_{calc_key}"): st.session_state[calc_key] = True
            
        if st.session_state[calc_key]:
            c_odds, d_odds = pd.to_numeric(res_m1['初盘'], errors='coerce'), pd.to_numeric(res_m1['临场'], errors='coerce')
            biao_c, rang_c = calc_pure_prob_array(c_odds[0:3]), calc_pure_prob_array(c_odds[3:6])
            biao_d, rang_d = calc_pure_prob_array(d_odds[0:3]), calc_pure_prob_array(d_odds[3:6])
            prob_c, prob_d = np.concatenate([biao_c, rang_c]), np.concatenate([biao_d, rang_d])
            delta = np.round(prob_d - prob_c, 4)
            
            ret_c = round(1.0 / np.nansum(1.0 / c_odds[0:3]), 4) if not pd.isna(c_odds[0:3]).any() else 1.0
            ret_d = round(1.0 / np.nansum(1.0 / d_odds[0:3]), 4) if not pd.isna(d_odds[0:3]).any() else 1.0
            theo_odds = np.round(c_odds * (ret_d / ret_c), 4) if ret_c != 0 else c_odds
            dev = np.round(d_odds - theo_odds, 4)
            
            heat = np.where(pd.isna(delta), "➖", np.where(delta >= z2, "🌋 极限防范", np.where(delta >= z3, "🔥 显著设防", np.where(delta >= z4, "📈 温和流入", np.where(delta <= -z2, "🧊 极限抛弃", np.where(delta <= -z3, "📉 显著看衰", np.where(delta <= -z4, "↘️ 温和流出", "⚪ 随机噪音")))))))
            filter_q = np.where(pd.isna(dev), "➖", np.where(dev < -0.02, "🩸 暴击防范(狠)", np.where(dev < 0, "📉 真实降水", np.where((dev > 0) & (d_odds < c_odds), "🚨 虚假降水", np.where(dev > 0, "📈 真实升水", "⚪ 平稳")))))
            
            s_theo, u_theo = np.full(6, np.nan), np.full(6, np.nan)
            t_open, v_open, w_traj, aa_hedge = ["⚪ 无对照"]*6, ["⚪ 无对照"]*6, ["⚪ 无对照"]*6, ["⚪ 动量未达标"]*6
            
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
            
            # 【核心改良】唯一主导矢量探测
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
                    
                    # 唯一性锁定逻辑
                    is_dominant = (delta[i] == max_delta_val and max_delta_val >= z3) or (delta[i] == min_delta_val and min_delta_val <= -z3)
                    
                    if delta[i] >= z3: 
                        if is_dominant:
                            aa_hedge[i] = "✅ 黄金共振(核心轴)" if struct >= z4 else "🚨 致命背离(造热核心)" if struct <= -z4 else "🟡 主流流入"
                        else:
                            aa_hedge[i] = "🟡 防守溢出(非主线)"
                    elif delta[i] <= -z3: 
                        if is_dominant:
                            aa_hedge[i] = "🎁 暗度陈仓(核心轴)" if struct >= z4 else "🧊 极限绞杀(被弃核心)" if struct <= -z4 else "⚪ 主流流出"
                        else:
                            aa_hedge[i] = "⚪ 泄洪波及(非主线)"
                    else: 
                        if struct >= z3: aa_hedge[i] = "🌋 静态死防"
                        elif struct <= -z3: aa_hedge[i] = "🕸️ 静态诱网"
                        else: aa_hedge[i] = "⚪ 动量未达标"

            out_main = pd.DataFrame({"选项": opts_m1, "初纯净概率": prob_c, "临纯净概率": prob_d, "动量(Delta)": delta, "热度测算": heat, "净抽水偏离": dev, "返还率滤镜": filter_q, "底座概率": s_theo, "初盘定性": t_open, "轨迹研判": w_traj, "时空双杀(改良版)": aa_hedge})
            st.markdown("### 📊 欧亚基础底座透视 (主导矢量唯一化)")
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
            st.markdown("### 🥇 顺流资金共识提纯器")
            st.dataframe(out_refiner.fillna(""), hide_index=True, use_container_width=True)

    with tab1: render_main_handicap_ui("浅水区", current_match)
    with tab2: render_main_handicap_ui("中水区", current_match)
    with tab3: render_main_handicap_ui("深水区", current_match)

# ==============================================================================
# ===================== 🎫 模块三：高阶工具 (原汁原味回归) =====================
# ==============================================================================
elif active_module == "🎫 模块三：高阶工具 (原味DC矩阵)":
    st.header(f"🎫 {current_match} - 高阶价值提纯 (经典回滚版)")
    st.caption("【回滚说明】满血恢复最直观的体彩 EV 物理期望切片器。")
    
    st.markdown("### ⚙️ 全局 DC 双泊松底座参数")
    c1, c2, c3 = st.columns(3)
    with c1: tg = safe_number_input("进球盘 (大小球)", f"m3_tg_{current_match}", 2.75, format="%.2f", step=0.25)
    with c2: hcp = safe_number_input("让球盘 (主队亚指)", f"m3_hcp_{current_match}", 0.0, format="%.2f", step=0.25)
    with c3: rho = safe_number_input("DC依赖系数 (ρ)", f"m3_rho_{current_match}", -0.15, format="%.2f", step=0.01)
    
    xg_h, xg_a = (tg - hcp) / 2, (tg + hcp) / 2
    if xg_h < 0 or xg_a < 0: st.error("⚠️ 预期进球为负，请检查盘口！")
    else:
        df_m, ph2, ph1, pdr, pau, P_col_rounded = dixon_coles_full_matrix(xg_h, xg_a, rho)
        tab1, tab2 = st.tabs(["🧮 DC 进球矩阵", "✂️ 体彩 EV 切片器"])
        with tab1:
            rc1, rc2, rc3, rc4 = st.columns(4)
            rc1.metric("DC 大胜(赢2+)", f"{ph2:.4f}"); rc2.metric("DC 恰赢1球", f"{ph1:.4f}")
            rc3.metric("DC 平局", f"{pdr:.4f}"); rc4.metric("DC 客不败", f"{pau:.4f}")
            st.dataframe(df_m.style.format("{:.4f}"), use_container_width=True)

        with tab2:
            res_m3 = render_odds_grid("m3", current_match, "全局体彩赔率录入", opts_m3, cols_m3, init_m3)
            calc_key = f"m3_calc_{current_match}"
            if calc_key not in st.session_state: st.session_state[calc_key] = False
            if st.button("🚀 启动底座联动扫描", key=f"btn_{calc_key}"): st.session_state[calc_key] = True
                
            if st.session_state[calc_key]:
                std_odds = pd.to_numeric([res_m3["胜"][0], res_m3["平"][0], res_m3["负"][0]], errors='coerce')
                let_odds = pd.to_numeric([res_m3["胜"][1], res_m3["平"][1], res_m3["负"][1]], errors='coerce')
                try: tc_let = int(float(res_m3["国彩让球数"][1]))
                except: tc_let = -1
                
                p_std_w = sum(P_col_rounded[i, j] for i in range(8) for j in range(8) if i - j > 0)
                p_std_d = sum(P_col_rounded[i, j] for i in range(8) for j in range(8) if i - j == 0)
                p_std_l = sum(P_col_rounded[i, j] for i in range(8) for j in range(8) if i - j < 0)
                p_let_w = sum(P_col_rounded[i, j] for i in range(8) for j in range(8) if i - j > -tc_let)
                p_let_d = sum(P_col_rounded[i, j] for i in range(8) for j in range(8) if i - j == -tc_let)
                p_let_l = sum(P_col_rounded[i, j] for i in range(8) for j in range(8) if i - j < -tc_let)
                
                intl_prob, tc_odds = np.array([p_std_w, p_std_d, p_std_l, p_let_w, p_let_d, p_let_l]), np.concatenate([std_odds, let_odds])
                ev_vals = np.round(tc_odds * intl_prob - 1, 4)
                judge = np.where(pd.isna(ev_vals), "➖", np.where(ev_vals > 0, "🌟 绝对正价值", np.where(ev_vals >= -0.03, "🟢 极度高潜", np.where(ev_vals >= -0.08, "🟡 合理磨损", np.where(ev_vals >= -0.12, "📉 劣势赔付", np.where(ev_vals >= -0.16, "🚨 杀猪盘预警", "🩸 抽水深渊"))))))
                
                out_df3 = pd.DataFrame({"投注项": ["标准胜", "标准平", "标准负", "让球胜", "让球平", "让球负"], "推演概率": np.round(intl_prob, 4), "数学EV": ev_vals, "雷达定性": judge})
                st.dataframe(out_df3.fillna(""), hide_index=True, use_container_width=True)


# ==============================================================================
# ===================== 🎲 模块六：365 核心全息约束 (剧本剥离版) =====================
# ==============================================================================
elif active_module == "🎲 模块六：365 核心全息约束 (剧本剥离版)":
    st.header(f"🎲 {current_match} - 365 核心全息约束 (人工干预探测版)")
    st.caption("【深度重构版】引入亚欧挤压差、半全场时间动能比及抽水缩表侦测，扒开精算师的微观操盘剧本。")

    opts_m6_std = ["主胜", "平局", "客胜"]
    cols_m6_2 = ["初盘", "临场"]
    init_m6_std = [[2.00, 1.90], [3.50, 3.40], [3.60, 4.00]]

    opts_m6_ah = ["盘口(主让为负)", "上盘水位", "下盘水位"]
    init_m6_ah = [[-0.50, -0.75], [1.95, 2.05], [1.90, 1.85]]

    opts_m6_eh = ["让球数(主让为负)", "让球胜", "让球平", "让球负"]
    init_m6_eh = [[-1.0, -1.0], [3.80, 3.50], [3.60, 3.50], [1.80, 1.90]]

    opts_m6_htft = ["胜/胜", "胜/平", "胜/负", "平/胜", "平/平", "平/负", "负/胜", "负/平", "负/负"]
    init_m6_htft = [[4.33, 4.00], [15.0, 14.0], [29.0, 34.0], [6.5, 6.0], [5.5, 5.0], [6.0, 6.5], [29.0, 34.0], [15.0, 15.0], [4.5, 5.0]]

    tab_std, tab_ah, tab_eh, tab_htft = st.tabs(["📊 365 标盘", "📉 365 亚指", "🥅 365 欧让", "⏱️ 365 半全场"])
    with tab_std: res_m6_std = render_odds_grid("m6std", current_match, "标盘", opts_m6_std, cols_m6_2, init_m6_std)
    with tab_ah: res_m6_ah = render_odds_grid("m6ah", current_match, "亚指", opts_m6_ah, cols_m6_2, init_m6_ah)
    with tab_eh: res_m6_eh = render_odds_grid("m6eh", current_match, "欧让", opts_m6_eh, cols_m6_2, init_m6_eh)
    with tab_htft: res_m6_htft = render_odds_grid("m6htft", current_match, "半/全场", opts_m6_htft, cols_m6_2, init_m6_htft)

    calc_key_m6 = f"m6_calc_{current_match}"
    if calc_key_m6 not in st.session_state: st.session_state[calc_key_m6] = False
    
    st.write("")
    if st.button("🚀 启动 365 剧本剥离与干预探测", type="primary", use_container_width=True, key=f"btn_{calc_key_m6}"):
        st.session_state[calc_key_m6] = True

    if st.session_state[calc_key_m6]:
        st.markdown("---")
        try:
            std_c, std_d = safe_extract_array(res_m6_std['初盘']), safe_extract_array(res_m6_std['临场'])
            ah_c, ah_d = safe_extract_array(res_m6_ah['初盘']), safe_extract_array(res_m6_ah['临场'])
            eh_c, eh_d = safe_extract_array(res_m6_eh['初盘']), safe_extract_array(res_m6_eh['临场'])
            ht_c, ht_d = safe_extract_array(res_m6_htft['初盘']), safe_extract_array(res_m6_htft['临场'])
            
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

            # ----------------------------------------------------
            # 核心升级一：人工干预指数与抽水缩表 (Trader Override Index)
            # ----------------------------------------------------
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
            
            if override_index > 4.0:
                st.error(f"🦇 **【人工紧急避险熔断】** 内部变异系数爆表({override_index:.4f})！365精算师已断开AI自动平衡，针对特定冷门选项进行人工粗暴压水，该项有极大内幕击杀可能！")
            else:
                st.success("💻 **【机器控盘期】** 四大盘口数学传动正常平稳，无剧烈人工干预痕迹，按纯实力流速处理。")
                
            if margin_diff > 0.0200: 
                st.warning(f"🚧 **【极限缩表护盘】** 365临场暴力提升半全场抽水率(+{margin_diff*100:.4f}%)，庄家对该维度失去控盘自信，拒开公平赔率以逼退散户！")

            # ----------------------------------------------------
            # 核心升级二：交叉摩擦评价器
            # ----------------------------------------------------
            delta_std_w = d_std[0] if not pd.isna(d_std[0]) else 0
            delta_ah_up = d_ah[0] if not pd.isna(d_ah[0]) else 0
            delta_eh_d  = d_eh[1] if not pd.isna(d_eh[1]) else 0 
            
            ht_ww = d_ht[0] if not pd.isna(d_ht[0]) else 0
            ht_dw = d_ht[3] if not pd.isna(d_ht[3]) else 0

            def evaluate_m6_item(category, opt_name, delta, p_c, p_d):
                if pd.isna(delta) or p_d == 0: return "➖ 数据缺失或未开盘"
                if category == 'std':
                    if opt_name == "主胜":
                        if delta > 0.015:
                            if delta_ah_up <= -0.015: return "🚨 【诱导陷阱】标盘疯狂造热主队，但亚盘暗中撤防，极大概率赢球输盘或爆冷！"
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
                        if delta_std_w > 0.015 and delta < -0.010 and ht_dw > 0.015: 
                            return "⏱️ 【时间轴剧本暴露】主胜大热但胜胜遭抛弃，资金疯抢“平/胜”！真正重注底牌在下半场！"
                        if delta > 0.015 and delta_std_w > 0.015: return "⚡ 【闪电战】与标盘高度共振，看好主队半场直接建立不可逆优势。"
                    elif opt_name == "平/胜":
                        if delta > 0.015 and delta_std_w > 0.01: return "🔎 【剧本偏移】主胜大势下资金疯抢平胜，严防剧本局或下半场绝杀！"
                    elif opt_name == "平/平":
                        if delta > 0.02: return "🧊 【极限降温】机构重防平平，全场大概率极度沉闷或 0-0 完场。"

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
                st.warning("➖ 欧让盘未录入数据或无开盘，已安全跳过该维度检测。")

            st.markdown("### ⏱️ 365 半/全场剧本 切片")
            df_ht_out = []
            for i in range(9):
                df_ht_out.append({"选项": opts_m6_htft[i], "初盘纯率": f"{p_ht_c[i]:.4f}", "临场纯率": f"{p_ht_d[i]:.4f}", "纯率增量(Δ)": f"{d_ht[i]:.4f}", "深度战术定性": evaluate_m6_item('htft', opts_m6_htft[i], d_ht[i], p_ht_c[i], p_ht_d[i])})
            st.dataframe(pd.DataFrame(df_ht_out), hide_index=True, use_container_width=True)

        except Exception as e:
            st.error("🚨 365 独立模块运行异常，请检查填写数据。")
            st.code(traceback.format_exc())

# ==============================================================================
# ===================== 🔭 模块五：状态转移与跨盘约束引擎 (终极重构版) =====================
# ==============================================================================
elif active_module == "🔭 模块五：V15 状态转移与跨盘约束引擎":
    st.header(f"🔭 {current_match} - V15 状态转移与跨盘约束引擎")
    st.caption("【高阶重构版】摒弃古典静态对比与单双博弈，全面引入 质量加权摩擦当量、马尔可夫转移偏度 与 跨盘口物理锁链，降维透视机构内幕。")
    
    def get_poisson_pmf(k, lam):
        if pd.isna(lam) or lam <= 0: return 1.0 if k == 0 else 0.0
        return math.exp(-lam) * (lam**k) / math.factorial(k)

    def generate_poisson_baselines(tg, hcp):
        if pd.isna(tg) or pd.isna(hcp): return np.zeros(8), np.zeros(9)
        xg_h, xg_a = (tg - hcp) / 2, (tg + hcp) / 2
        goal_probs = np.zeros(8)
        for i in range(10):
            for j in range(10):
                p = get_poisson_pmf(i, xg_h) * get_poisson_pmf(j, xg_a)
                if i+j < 7: goal_probs[i+j] += p
                else: goal_probs[7] += p
                
        ht_xg_h, ht_xg_a = xg_h * 0.45, xg_a * 0.45
        sh_xg_h, sh_xg_a = xg_h * 0.55, xg_a * 0.55
        ht_probs, sh_probs = {"W": 0, "D": 0, "L": 0}, {"W": 0, "D": 0, "L": 0}
        
        for i in range(8):
            for j in range(8):
                p_ht = get_poisson_pmf(i, ht_xg_h) * get_poisson_pmf(j, ht_xg_a)
                p_sh = get_poisson_pmf(i, sh_xg_h) * get_poisson_pmf(j, sh_xg_a)
                if i > j: ht_probs["W"] += p_ht; sh_probs["W"] += p_sh
                elif i == j: ht_probs["D"] += p_ht; sh_probs["D"] += p_sh
                else: ht_probs["L"] += p_ht; sh_probs["L"] += p_sh
                
        htft_math = [
            ht_probs["W"] * (sh_probs["W"] + sh_probs["D"]*0.5),
            ht_probs["W"] * (sh_probs["L"]*0.8 + sh_probs["D"]*0.5),
            ht_probs["W"] * (sh_probs["L"]*0.2),
            ht_probs["D"] * sh_probs["W"],
            ht_probs["D"] * sh_probs["D"],
            ht_probs["D"] * sh_probs["L"],
            ht_probs["L"] * (sh_probs["W"]*0.2),
            ht_probs["L"] * (sh_probs["W"]*0.8 + sh_probs["D"]*0.5),
            ht_probs["L"] * (sh_probs["L"] + sh_probs["D"]*0.5)
        ]
        if np.sum(goal_probs) > 0: goal_probs = goal_probs / np.sum(goal_probs)
        if np.sum(htft_math) > 0: htft_math = np.array(htft_math) / np.sum(htft_math)
        return np.round(goal_probs, 4), np.round(htft_math, 4)

    def m5_safe_input(label, base_key, default_val, format="%.2f", step=0.25):
        wid_key = "w_" + base_key
        if base_key not in st.session_state: st.session_state[base_key] = default_val
        def _cb(): st.session_state[base_key] = st.session_state[wid_key]
        return st.number_input(label, value=st.session_state.get(base_key, default_val), format=format, step=step, key=wid_key, on_change=_cb)

    with st.expander("⚙️ 引擎底座参数 (点击展开设定大盘基准)", expanded=True):
        c1, c2 = st.columns(2)
        with c1: m5_ou_val = m5_safe_input("大小球基准盘口 (用于跨盘口锁定)", f"m5_ou_{current_match}", 2.50, format="%.2f", step=0.25)
        with c2: m5_hcp_val = m5_safe_input("亚指让球基准 (用于马尔可夫底座)", f"m5_hcp_{current_match}", -0.50, format="%.2f", step=0.25)
        
    tab_g, tab_h = st.tabs(["⚽ 进球数全息矩阵录入", "🔵 半全场时空矩阵录入"])
    with tab_g: res_m5_g = render_odds_grid("m5g", current_match, "进球数", opts_m5_g, cols_m5_new, init_m5_g)
    with tab_h: res_m5_h = render_odds_grid("m5h", current_match, "半/全场", opts_m5_h, cols_m5_new, init_m5_h)
    
    calc_key_m5 = f"m5_calc_{current_match}"
    if calc_key_m5 not in st.session_state: st.session_state[calc_key_m5] = False
    
    if st.button("🚀 启动 V15 高阶重构精算引擎", type="primary", use_container_width=True, key=f"btn_{calc_key_m5}"):
        st.session_state[calc_key_m5] = True
        
    if st.session_state[calc_key_m5]:
        st.markdown("---")
        try:
            # 数据解包
            c_365_g, d_365_g = safe_extract_array(res_m5_g['365初盘']), safe_extract_array(res_m5_g['365临场'])
            c_hk_g,  d_hk_g  = safe_extract_array(res_m5_g['马会初盘']), safe_extract_array(res_m5_g['马会临场'])
            c_tc_g,  d_tc_g  = safe_extract_array(res_m5_g['体彩初盘']), safe_extract_array(res_m5_g['体彩临场'])
            
            c_365_h, d_365_h = safe_extract_array(res_m5_h['365初盘']), safe_extract_array(res_m5_h['365临场'])
            c_hk_h,  d_hk_h  = safe_extract_array(res_m5_h['马会初盘']), safe_extract_array(res_m5_h['马会临场'])
            c_tc_h,  d_tc_h  = safe_extract_array(res_m5_h['体彩初盘']), safe_extract_array(res_m5_h['体彩临场'])
            
            p_tc_c_g, p_tc_d_g = calc_pure_prob_array(c_tc_g), calc_pure_prob_array(d_tc_g)
            p_tc_c_h, p_tc_d_h = calc_pure_prob_array(c_tc_h), calc_pure_prob_array(d_tc_h)
            
            math_g, math_h = generate_poisson_baselines(m5_ou_val, m5_hcp_val)

            # ----------------------------------------------------
            # 核心升级一 & 二：质量加权摩擦 与 跨盘口偏度物理锁链 (进球数)
            # ----------------------------------------------------
            fric_g = np.round((p_tc_d_g - math_g) * d_tc_g, 4)
            df_g_rows = []
            
            for i in range(8):
                fric = fric_g[i]
                if pd.isna(fric): tag = "➖"
                elif fric > 0.0800: tag = f"🛡️ 极致割肉护盘 ({fric:+.4f})"
                elif fric > 0.0300: tag = f"🚧 核心风控防线 ({fric:+.4f})"
                elif fric < -0.0800: tag = f"🩸 抽水诱捕陷阱 ({fric:+.4f})"
                elif fric < -0.0300: tag = f"📉 虚高敞口放水 ({fric:+.4f})"
                else: tag = f"⚪ 泊松均衡 ({fric:+.4f})"

                odds_drop = (d_tc_g[i] - c_tc_g[i]) / c_tc_g[i] if c_tc_g[i] > 0 else 0
                if odds_drop < -0.15 and d_tc_g[i] > 8.0:
                    tag += " [⚡定点爆破]"

                df_g_rows.append({
                    "进球数": opts_m5_g[i],
                    "体彩临场": f"{d_tc_g[i]:.2f}",
                    "体彩纯率": f"{p_tc_d_g[i]:.4f}" if not pd.isna(p_tc_d_g[i]) else "➖",
                    "泊松期望": f"{math_g[i]:.4f}" if not pd.isna(math_g[i]) else "➖",
                    "流速(Δ)": f"{(p_tc_d_g[i] - p_tc_c_g[i]):.4f}" if not pd.isna(p_tc_d_g[i]) else "➖",
                    "质量加权摩擦(Friction)": tag
                })
                
            st.markdown("## ⚽ V15.0 进球数微观精算阵列")
            
            # 跨盘口物理锁链检测
            under_idx = math.floor(m5_ou_val) if m5_ou_val > 0 else 0
            if under_idx > 7: under_idx = 7
            tc_under = np.sum(p_tc_d_g[:under_idx+1])
            math_under = np.sum(math_g[:under_idx+1])
            diff_under = round(tc_under - math_under, 4)
            
            if diff_under > 0.0500:
                st.error(f"🚨 **跨盘口逻辑撕裂：** 体彩进球数矩阵在【小球区间(≤{under_idx}球)】发生严重质量塌陷（实际防守远超泊松预期 {diff_under*100:+.2f}%）。若此时外部大小球主盘 {m5_ou_val} 处于大球低水，则为极限虚空诱导！本场真实内核死守小球！")
            elif diff_under < -0.0500:
                st.warning(f"🌪️ **跨盘口逆向撕裂：** 体彩进球数矩阵在【大球区间(>{under_idx}球)】防御力度畸高。若此时外部大小球盘口高开拉阻，说明庄家底层极度畏惧大球穿盘，切勿被表象赔率劝退！")
            else:
                st.success(f"⚖️ **跨盘口物理锁定完美：** 进球数细分结构与 {m5_ou_val} 大小球盘口张力匹配，未见人工强制撕裂痕迹。")

            st.dataframe(pd.DataFrame(df_g_rows), hide_index=True, use_container_width=True)
            
            # ----------------------------------------------------
            # 核心升级三 & 四：马尔可夫转移偏度 与 动态时空衰减 (半全场)
            # ----------------------------------------------------
            st.markdown("<br><hr><br>", unsafe_allow_html=True)
            st.markdown("## 🔵 V15.0 半全场马尔可夫状态转移矩阵")
            
            fric_h = np.round((p_tc_d_h - math_h) * d_tc_h, 4)
            df_h_rows = []
            for i in range(9):
                fric = fric_h[i]
                if pd.isna(fric): tag = "➖"
                elif fric > 0.0800: tag = f"🛡️ 极限拦截 ({fric:+.4f})"
                elif fric > 0.0300: tag = f"🚧 真实防范 ({fric:+.4f})"
                elif fric < -0.0800: tag = f"🩸 剧毒诱导 ({fric:+.4f})"
                elif fric < -0.0300: tag = f"📉 虚高放水 ({fric:+.4f})"
                else: tag = f"⚪ 结构平衡 ({fric:+.4f})"

                odds_drop = (d_tc_h[i] - c_tc_h[i]) / c_tc_h[i] if c_tc_h[i] > 0 else 0
                if odds_drop < -0.20 and d_tc_h[i] > 10.0:
                    tag += " [⚡高赔定向坍塌]"

                df_h_rows.append({
                    "半/全场": opts_m5_h[i],
                    "体彩临场": f"{d_tc_h[i]:.2f}",
                    "体彩纯率": f"{p_tc_d_h[i]:.4f}" if not pd.isna(p_tc_d_h[i]) else "➖",
                    "泊松期望": f"{math_h[i]:.4f}" if not pd.isna(math_h[i]) else "➖",
                    "流速(Δ)": f"{(p_tc_d_h[i] - p_tc_c_h[i]):.4f}" if not pd.isna(p_tc_d_h[i]) else "➖",
                    "马尔可夫摩擦(Friction)": tag
                })
                
            # 马尔可夫剧本剖析
            col_m1, col_m2 = st.columns(2)
            if fric_h[3] > 0.0500 and fric_h[0] < 0.0100:
                col_m1.error("⏱️ **【状态转移剧本曝光】** 庄家放任‘胜/胜’不管，却重金死守‘平/胜’！机构判定上半场极难分出胜负，‘胜/胜’纯属散户填仓炮灰，真实的反杀剧本在下半场！")
            elif fric_h[0] > 0.0500 and fric_h[3] < 0.0100:
                col_m1.success("⚡ **【闪电战偏度曝光】** 庄家对‘胜/胜’进行极限物理降水防守，完全不看好平局过渡。机构认定主队能在上半场迅速摧毁防线建立优势！")
            else:
                col_m1.info("⚪ **【主场动能平稳】** ‘胜/胜’与‘平/胜’状态转移摩擦系数处于常规协同状态。")
                
            if fric_h[4] > 0.0600:
                col_m2.warning("🧊 **【全场冻结偏度】** ‘平/平’呈现极端质量摩擦当量！庄家极其惧怕僵局到底，全场大概率 0-0 或 1-1 沉闷完场，大球慎碰！")
            elif fric_h[4] < -0.0500:
                col_m2.success("💥 **【破冰对攻剧本】** ‘平/平’防线被彻底放弃，机构判定本场双方必分高下，半场极有可能早早破局！")
            else:
                col_m2.info("⚪ **【中场控制平稳】** 僵局维持概率处于理论预期内。")

            st.dataframe(pd.DataFrame(df_h_rows), hide_index=True, use_container_width=True)

        except Exception as e:
            st.error("🚨 **系统捕捉到环境异常**")
            st.warning(f"直接报错原因：`{str(e)}`")
            with st.expander("展开查看详细代码追踪报错"):
                st.code(traceback.format_exc())

# ==============================================================================
# ===================== 🧬 模块四：异构交叉与零和对冲 =====================
# ==============================================================================
elif active_module == "🧬 模块四：异构交叉与零和对冲":
    st.header(f"🧬 {current_match} - 终极异构验证与对冲引擎")
    source_wl = st.radio("📡 选择底层数据提取源 (与模块一联动)：", ["浅水区", "中水区", "深水区"], horizontal=True)
    tab_a, tab_b, tab_c = st.tabs(["🔍 亚盘 vs xG 撕裂检测", "🏦 机构暗水剥离 (凯利敞口)", "⚖️ 荷兰式绝对零和对冲器"])
    
    with tab_a:
        st.markdown("### 🔍 异构交叉验证：盘口物理边界 vs 泊松数学期望")
        try:
            ah_val = float(st.session_state.get(f"m1_hcp_{current_match}_{source_wl}", -1.0))
            tg_val = float(st.session_state.get(f"m3_tg_{current_match}", 2.75))
            hcp_val = float(st.session_state.get(f"m3_hcp_{current_match}", 0.0))
            xg_h, xg_a = (tg_val - hcp_val) / 2, (tg_val + hcp_val) / 2
            xg_diff = round(xg_h - xg_a, 4)
            
            c1, c2, c3 = st.columns(3)
            c1.metric(f"机构物理开盘 ({source_wl}让球)", f"{ah_val}")
            c2.metric("泊松数学推演 (主队净胜球)", f"{xg_diff}")
            mismatch = round(xg_diff - (-ah_val), 4)
            c3.metric("🌪️ 时空撕裂度 (Mismatch)", f"{mismatch}")
            
            if mismatch >= 0.4: st.success("✅ **主队深度价值：** 机构开出的盘口极其保守，但数学期望显示主队碾压，主队极大概率穿盘！")
            elif mismatch <= -0.4: st.error("🚨 **极致诱杀陷阱：** 机构强行开出深盘造热主队，但数学期望极低，坚决去下盘/客队不败！")
            else: st.warning("⚖️ **盘理平衡：** 机构开盘与数学期望严丝合缝，没有明显的结构性漏洞。")
        except KeyError:
            st.error(f"⚠️ 请先在【模块一：{source_wl}】和【模块三】中输入盘口数据。")

    with tab_b:
        st.markdown("### 🏦 机构真实赔付敞口与暗水探测")
        try:
            d_odds = [
                float(st.session_state.get(f"m1_{current_match}_{source_wl}_r0_c1", 2.32)),
                float(st.session_state.get(f"m1_{current_match}_{source_wl}_r1_c1", 3.20)),
                float(st.session_state.get(f"m1_{current_match}_{source_wl}_r2_c1", 2.60))
            ]
            d_odds = np.array(d_odds, dtype=float)
            if np.isnan(d_odds).any() or (d_odds <= 0).any(): raise ValueError("Invalid odds")
            
            implied = 1.0 / d_odds
            margin = np.sum(implied) - 1
            fair_prob = implied / (1 + margin)
            liability = fair_prob * d_odds
            
            df_kelly = pd.DataFrame({"赛果": ["主胜", "平局", "客胜"], f"{source_wl}临场赔率": d_odds, "被动抽水率": [f"{margin*100:.2f}%"]*3, "真实概率": np.round(fair_prob, 4), "⚠️ 机构敞口指数": np.round(liability, 4)})
            st.dataframe(df_kelly, hide_index=True, use_container_width=True)
            max_idx = int(np.argmax(liability))
            max_res = ["主胜", "平局", "客胜"][max_idx]
            st.error(f"💣 **暗水警报：** 当前机构对 **【{max_res}】** 的赔付敞口最为敏感，存在防范动作！")
        except Exception as e:
            st.warning(f"⚠️ 无法核算敞口，请先在【模块一：{source_wl}】确认标盘临场赔率。 (Debug: {e})")

    with tab_c:
        st.markdown("### ⚖️ 荷兰式绝对零和对冲器")
        c1, c2, c3 = st.columns(3)
        with c1: total_capital = safe_number_input("💰 计划投入总资金", f"m4_cap_{current_match}", 1000.0, format="%.0f", step=100.0)
        with c2: odd_a = safe_number_input("选项 A 赔率", f"m4_oddA_{current_match}", 2.00, format="%.2f", step=0.01)
        with c3: odd_b = safe_number_input("选项 B 赔率", f"m4_oddB_{current_match}", 3.00, format="%.2f", step=0.01)
        
        if odd_a > 1 and odd_b > 1:
            implied_a, implied_b = 1/odd_a, 1/odd_b
            total_implied = implied_a + implied_b
            stake_a, stake_b = (implied_a / total_implied) * total_capital, (implied_b / total_implied) * total_capital
            profit = (stake_a * odd_a) - total_capital
            
            col_r1, col_r2, col_r3 = st.columns(3)
            col_r1.success(f"**买入 选项A：** `{stake_a:.2f}` 元")
            col_r2.success(f"**买入 选项B：** `{stake_b:.2f}` 元")
            if profit > 0: col_r3.info(f"**保底净利润：** `+{profit:.2f}` 元")
            else: col_r3.error(f"**不可避免损耗：** `{profit:.2f}` 元")
