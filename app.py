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
    </style>
""", unsafe_allow_html=True)

# 💣 终极核弹级清理缓存 (彻底修复死循环Bug)
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

st.title("🏦 FX2 机构级全维量化终端 (经典重铸改良版)")

# ================= 3. 核心数学引擎 (强制4位小数精度) =================
def calc_pure_prob_array(arr):
    arr = np.array(arr, dtype=float)
    if pd.isna(arr).any() or (arr <= 0).any():
        return np.full(len(arr), np.nan)
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
current_match = st.sidebar.radio("🏆 独立沙盒切换：", matches_list, horizontal=True)

active_module = st.sidebar.radio("=== 分析体系 ===", [
    "🎯 模块七：全息刚性嵌套与三阶平衡矩阵 (V25)",
    "🔥 模块X：全息综合引擎 (M1+M3+M4)",
    "⚽ 模块二：进球数多维风控", 
    "🔭 模块五：V15 状态转移与跨盘约束引擎",
    "🎲 模块六：365 核心全息约束 (剧本剥离版)"
])


# ==============================================================================
# ===================== 🔥 模块X：全息综合引擎 (M1+M3+M4) =====================
# ==============================================================================
if active_module == "🔥 模块X：全息综合引擎 (M1+M3+M4)":
    st.header(f"🔥 {current_match} - 模块X：全息综合引擎 (M1+M3+M4)")
    st.caption("【终极合并工作台】整合了模块一(欧亚底座)、模块三(DC期望)与模块四(异构敞口)。一次录入全局通兑，一键输出三大维度无缝研判。")

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
            # === 全局数据准备 ===
            c_odds, d_odds = pd.to_numeric(res_mx['初盘'], errors='coerce'), pd.to_numeric(res_mx['临场'], errors='coerce')
            biao_c, rang_c = calc_pure_prob_array(c_odds[0:3]), calc_pure_prob_array(c_odds[3:6])
            biao_d, rang_d = calc_pure_prob_array(d_odds[0:3]), calc_pure_prob_array(d_odds[3:6])
            prob_c, prob_d = np.concatenate([biao_c, rang_c]), np.concatenate([biao_d, rang_d])
            delta = np.round(prob_d - prob_c, 4)

            # =========================================================
            # M1：欧亚大盘体系 (精准收口版)
            # =========================================================
            st.markdown("---")
            st.markdown(f"## ⚔️ 模块一：{wl}欧亚基础底座透视")
            
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
                        if is_dominant: aa_hedge[i] = "🎁 暗度陈仓(核心轴)" if struct >= z4 else "🧊 极限绞杀(被弃核心)" if struct <= -z4 else "⚪ 主流流出"
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


            # =========================================================
            # M3：高阶价值提纯 (原味DC矩阵)
            # =========================================================
            st.markdown("---")
            st.markdown("## 🎫 模块三：DC双泊松高阶提纯")
            
            xg_h_m3, xg_a_m3 = (mx_tg - mx_hcp_math) / 2, (mx_tg + mx_hcp_math) / 2
            if xg_h_m3 < 0 or xg_a_m3 < 0: 
                st.error("⚠️ 预期进球为负，请检查泊松底座盘口设置！")
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

            # =========================================================
            # M4：异构交叉与零和对冲
            # =========================================================
            st.markdown("---")
            st.markdown("## 🧬 模块四：终极异构验证与对冲引擎")
            
            tab_m4_a, tab_m4_b, tab_m4_c = st.tabs(["🔍 亚盘 vs xG 撕裂检测", "🏦 机构暗水剥离 (凯利敞口)", "⚖️ 荷兰式绝对零和对冲器"])
            
            with tab_m4_a:
                st.markdown("### 🔍 异构交叉验证：盘口物理边界 vs 泊松数学期望")
                xg_diff = round(xg_h_m3 - xg_a_m3, 4)
                c1_m4, c2_m4, c3_m4 = st.columns(3)
                c1_m4.metric(f"机构物理开盘 ({wl}让球)", f"{mx_hcp_bookie}")
                c2_m4.metric("泊松数学推演 (主队净胜球)", f"{xg_diff}")
                mismatch = round(xg_diff - (-mx_hcp_bookie), 4)
                c3_m4.metric("🌪️ 时空撕裂度 (Mismatch)", f"{mismatch}")
                
                if mismatch >= 0.4: st.success("✅ **主队深度价值：** 机构开出的盘口极其保守，但数学期望显示主队碾压，主队极大概率穿盘！")
                elif mismatch <= -0.4: st.error("🚨 **极致诱杀陷阱：** 机构强行开出深盘造热主队，但数学期望极低，坚决去下盘/客队不败！")
                else: st.warning("⚖️ **盘理平衡：** 机构开盘与数学期望严丝合缝，没有明显的结构性漏洞。")

            with tab_m4_b:
                st.markdown("### 🏦 机构真实赔付敞口与暗水探测")
                d_odds_m4 = d_odds[0:3]
                if np.isnan(d_odds_m4).any() or (d_odds_m4 <= 0).any(): 
                    st.warning("⚠️ 标盘赔率数据缺失，无法核算敞口。")
                else:
                    implied_m4 = 1.0 / d_odds_m4
                    margin_m4 = np.sum(implied_m4) - 1
                    fair_prob_m4 = implied_m4 / (1 + margin_m4)
                    liability_m4 = fair_prob_m4 * d_odds_m4
                    
                    df_kelly = pd.DataFrame({"赛果": ["主胜", "平局", "客胜"], f"{wl}临场赔率": d_odds_m4, "被动抽水率": [f"{margin_m4*100:.2f}%"]*3, "真实概率": np.round(fair_prob_m4, 4), "⚠️ 机构敞口指数": np.round(liability_m4, 4)})
                    st.dataframe(df_kelly, hide_index=True, use_container_width=True)
                    max_idx = int(np.argmax(liability_m4))
                    max_res = ["主胜", "平局", "客胜"][max_idx]
                    st.error(f"💣 **暗水警报：** 当前机构对 **【{max_res}】** 的赔付敞口最为敏感，存在防范动作！")

            with tab_m4_c:
                st.markdown("### ⚖️ 荷兰式绝对零和对冲器")
                c1_4c, c2_4c, c3_4c = st.columns(3)
                with c1_4c: total_capital = safe_number_input("💰 计划投入总资金", f"m4_cap_{match_id}_{wl}", 1000.0, format="%.0f", step=100.0)
                with c2_4c: odd_a = safe_number_input("选项 A 赔率", f"m4_oddA_{match_id}_{wl}", 2.00, format="%.2f", step=0.01)
                with c3_4c: odd_b = safe_number_input("选项 B 赔率", f"m4_oddB_{match_id}_{wl}", 3.00, format="%.2f", step=0.01)
                
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

    with tab_mx_1: render_module_x_ui("浅水区", current_match)
    with tab_mx_2: render_module_x_ui("中水区", current_match)
    with tab_mx_3: render_module_x_ui("深水区", current_match)


# ==============================================================================
# ===================== 🎯 模块七：全息刚性嵌套与三阶平衡矩阵 (V25) =====================
# ==============================================================================
elif active_module == "🎯 模块七：全息刚性嵌套与三阶平衡矩阵 (V25)":
    st.header(f"🎯 {current_match} - V25 全息刚性连通器·三阶融合中控台")
    st.caption("【终极完全体】强行融汇 M1(净抽水防线) 与 M3(泊松物理EV)。自适应代偿让2/3球深盘【标盘未开售】断层，锁死排雷波动率上限(±0.0220)，降维透视体彩国家队定向卷。")

    st.markdown("### 🎛️ 第一步：物理基本面与规则设定")
    col_env1, col_env2, col_env3 = st.columns(3)
    with col_env1: m7_tg = safe_number_input("大小球预期期望 (计算物理纯率)", f"m7_tg_{current_match}", 2.75, format="%.2f", step=0.25)
    with col_env2: m7_hcp = safe_number_input("初始实力亚盘 (主让为负)", f"m7_hcp_{current_match}", -0.50, format="%.2f", step=0.25)
    with col_env3: m7_k = safe_number_input("体彩实际让球数 (K, 主让为负)", f"m7_k_{current_match}", -1.0, format="%.0f", step=1.0)

    st.write("")
    is_std_unopened = st.toggle("🚫 【官方未售标盘模式】(体彩在让2、3球深盘时锁盘专属。启动后台泊松物理纯率强行代偿标盘！)", value=False)

    st.markdown("---")
    st.markdown("### 📥 第二步：绝对连通器赔率录入")
    opts_m7_std = ["主胜", "平局", "客胜"]
    opts_m7_let = ["让球胜", "让球平", "让球负"]
    
    col_std, col_let = st.columns(2)
    with col_std: 
        if is_std_unopened:
            st.warning("🔒 官方锁盘未开售，本区无需填写，系统已自动剥离。")
            res_m7_std = {"初盘": [np.nan]*3, "临场": [np.nan]*3}
        else:
            res_m7_std = render_odds_grid("m7_std", current_match, "体彩【标盘】", opts_m7_std, ["初盘", "临场"], [[1.37, 1.30], [4.50, 4.80], [6.50, 8.00]])
            
    with col_let: 
        res_m7_let = render_odds_grid("m7_let", current_match, "体彩【让球盘】", opts_m7_let, ["初盘", "临场"], [[2.15, 2.05], [3.50, 3.60], [2.65, 2.80]])

    calc_key_m7 = f"m7_calc_{current_match}"
    if calc_key_m7 not in st.session_state: st.session_state[calc_key_m7] = False
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚀 启动 V25 全维连通器融魂引擎", type="primary", use_container_width=True, key=f"btn_{calc_key_m7}"): 
        st.session_state[calc_key_m7] = True
        
    if st.session_state[calc_key_m7]:
        st.markdown("---")
        try:
            # ==========================================
            # 1. 泊松物理基本面基底构建 (M3 灵魂注入)
            # ==========================================
            xg_h, xg_a = (m7_tg - m7_hcp) / 2.0, (m7_tg + m7_hcp) / 2.0
            _, _, _, _, _, P_matrix = dixon_coles_full_matrix(xg_h, xg_a, -0.15)
            
            p_math_std_w = sum(P_matrix[h, a] for h in range(8) for a in range(8) if h > a)
            p_math_std_d = sum(P_matrix[h, a] for h in range(8) for a in range(8) if h == a)
            p_math_std_l = sum(P_matrix[h, a] for h in range(8) for a in range(8) if h < a)
            
            K_int = int(m7_k)
            p_math_let_w = sum(P_matrix[h, a] for h in range(8) for a in range(8) if h - a > -K_int)
            p_math_let_d = sum(P_matrix[h, a] for h in range(8) for a in range(8) if h - a == -K_int)
            p_math_let_l = sum(P_matrix[h, a] for h in range(8) for a in range(8) if h - a < -K_int)
            
            p_math_all = np.round([p_math_std_w, p_math_std_d, p_math_std_l, p_math_let_w, p_math_let_d, p_math_let_l], 4)

            # ==========================================
            # 2. 真实数据解包与代偿隔离
            # ==========================================
            let_c = safe_extract_array(res_m7_let['初盘'])
            let_d = safe_extract_array(res_m7_let['临场'])
            p_let_c, p_let_d = calc_pure_prob_array(let_c), calc_pure_prob_array(let_d)

            if is_std_unopened:
                std_c, std_d = np.array([np.nan]*3), np.array([np.nan]*3)
                p_std_c_calc, p_std_d_calc = p_math_all[0:3], p_math_all[0:3] # 物理代偿注入
            else:
                std_c = safe_extract_array(res_m7_std['初盘'])
                std_d = safe_extract_array(res_m7_std['临场'])
                p_std_c_calc, p_std_d_calc = calc_pure_prob_array(std_c), calc_pure_prob_array(std_d)

            p_all_c = np.concatenate([p_std_c_calc, p_let_c])
            p_all_d = np.concatenate([p_std_d_calc, p_let_d])
            d_all = np.round(p_all_d - p_all_c, 4)

            # ==========================================
            # 3. 计算物理EV (M3魂) 与 净抽水偏离Dev (M1魂)
            # ==========================================
            odds_d_all = np.concatenate([std_d, let_d])
            ev_all = np.round(odds_d_all * p_math_all - 1.0, 4)

            # M1 净抽水偏离计算
            ret_c_std = 1.0 / np.nansum(1.0 / std_c) if not is_std_unopened else 1.0
            ret_d_std = 1.0 / np.nansum(1.0 / std_d) if not is_std_unopened else 1.0
            theo_std_d = std_c * (ret_d_std / ret_c_std) if ret_c_std != 0 else std_c
            dev_std = np.round(std_d - theo_std_d, 4)

            ret_c_let = 1.0 / np.nansum(1.0 / let_c) if not pd.isna(let_c).all() else 1.0
            ret_d_let = 1.0 / np.nansum(1.0 / let_d) if not pd.isna(let_d).all() else 1.0
            theo_let_d = let_c * (ret_d_let / ret_c_let) if ret_c_let != 0 else let_c
            dev_let = np.round(let_d - theo_let_d, 4)
            dev_all = np.concatenate([dev_std, dev_let])

            # ==========================================
            # 4. 刚性断层桥接向量计算 (Bridge Vector)
            # ==========================================
            bridge_val = 0.0
            if K_int < 0 and K_int <= -2:
                bridge_val = sum([P_matrix[h, a] for h in range(8) for a in range(8) if 0 < h - a < -K_int])
            elif K_int > 0 and K_int >= 2:
                bridge_val = sum([P_matrix[h, a] for h in range(8) for a in range(8) if 0 < a - h < K_int])
            bridge_val = round(bridge_val, 4)

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

            # 【核心脑手术】：排雷阈值上限锁死 ±0.0220！防暴击趋势局检测致盲
            valid_deltas = d_all[~pd.isna(d_all)]
            vol = np.std(valid_deltas) if len(valid_deltas)>0 else 0.0100
            dynamic_threshold = min(round(max(vol*1.5, 0.0060), 4), 0.0220)

            rmv = np.zeros(6)
            for i in range(6):
                if p_all_d[i] > 0: rmv[i] = round(residuals[i] / p_all_d[i], 4)

            # ==========================================
            # 5. 生成融魂大终局审计报告
            # ==========================================
            verdicts, scripts, pd_show = [], [], []
            
            for i in range(6):
                is_std = i < 3
                if is_std and is_std_unopened:
                    pd_show.append(f"🔒泊松代偿({p_all_d[i]:.4f})")
                    verdicts.append("🚫 官方锁盘未售")
                    scripts.append("体彩规避深盘单关强胆贴补，拒绝售卖此项。底层已自动代入泊松物理纯率作为镜像支点。")
                    continue
                
                pd_show.append(f"{p_all_d[i]:.4f}" if not pd.isna(p_all_d[i]) else "➖")
                flow, ev, dev, res, r = d_all[i], ev_all[i], dev_all[i], residuals[i], rmv[i]

                is_deep_val = not pd.isna(ev) and ev > 0.0150
                is_poison = not pd.isna(ev) and ev < -0.1600
                is_hard_def = not pd.isna(dev) and dev < -0.0180 # 机构真金白银割肉猛降水

                is_lie = res > dynamic_threshold and r > 0.0450
                is_gold = res < -dynamic_threshold and r < -0.0450

                if is_lie:
                    verdicts.append("🚨 镜像畸高 (造热死坑)")
                    scripts.append(f"【诱杀红线】跨盘概率被虚假拔高({res:+.4f})，精算师克扣赔率制造稳赢假象，泊松期望不支撑，首选排除。")
                elif is_gold:
                    if flow > -0.0100:
                        verdicts.append("💎 全息闭环暗水王")
                        scripts.append(f"【核心定胆】承接对冲纯率！叠加物理期望({ev*100:+.2f}%)，机构承受真实兑付铁壁，全场第一单挑位！")
                    else:
                        verdicts.append("🧊 镜像被弃死冷")
                        scripts.append("传动链与市场流速同步宣判死刑，冷门通道已被物理封焊。")
                elif is_poison:
                    verdicts.append("🩸 负EV抽水深渊")
                    scripts.append(f"【数学铁幕】体彩在此抽水率极度丧心病狂(EV: {ev*100:+.2f}%)，买入即亏损，纯属散户爱国送钱位。")
                elif is_hard_def and flow > 0.0100:
                    verdicts.append("🛡️ 机构肉身防线")
                    scripts.append(f"【真实设防】顶着买入压力强行暴力压水({dev:+.4f})，精算师极度畏惧此赛果打出，强力看好！")
                elif is_deep_val:
                    verdicts.append("🌟 物理期望金矿")
                    scripts.append(f"【价值洼地】开出赔率高于泊松物理概率(EV: {ev*100:+.2f}%)，具备绝对正向博取价值！")
                elif flow >= 0.0350:
                    verdicts.append("🚀 实势共振单边潮")
                    scripts.append("两盘传动严丝合缝且伴随天量热钱涌入，庄家顺御势能，强队恒强单边碾压局。")
                elif flow <= -0.0350:
                    verdicts.append("📉 顺流全息退热")
                    scripts.append("大势已去，双端同步大幅度退水，打出概率渺茫。")
                else:
                    verdicts.append("⚪ 连通器自然换手")
                    scripts.append("常规跷跷板支点，市场动态平衡，无独立做局价值。")

            st.markdown("### 📊 V25 全维连通器·终极融魂审计看板")
            st.caption(f"全盘动态排雷防线上限已物理锁死于：± **{dynamic_threshold:.4f}**")
            
            df_show = pd.DataFrame({
                "投注选项": ["标盘-胜", "标盘-平", "标盘-负", "让盘-胜", "让盘-平", "让盘-负"],
                "临场纯率(Pd)": pd_show,
                "泊松物理EV": [f"{x*100:+.2f}%" if not pd.isna(x) else "➖" for x in ev_all],
                "抽水防线(Dev)": [f"{x:+.4f}" if not pd.isna(x) else "➖" for x in dev_all],
                "刚性残差(Lie_R)": [f"{x:+.4f}" for x in residuals],
                "变异度(RMV)": [f"{x*100:+.2f}%" if not pd.isna(x) else "➖" for x in rmv],
                "全维时空裁决": verdicts,
                "机构底层大白话": scripts
            })
            st.dataframe(df_show, hide_index=True, use_container_width=True)

            st.write("")
            st.markdown("### 🥇 欧亚刚性链传动矢量形变看板 (CTD)")
            ctd_val = round(residuals[0] if K_int < 0 else residuals[3], 4)
            col_c1, col_c2 = st.columns(2)
            col_c1.metric("⚡ 主传动链形变度 (CTD)", f"{ctd_val:+.4f}")
            if abs(ctd_val) > 0.0350:
                col_c2.error("🚨 **【传动链条发生物理撕裂】** 标盘分布与底层让盘防线严重背离，精算师正在用空间断层诱导大单！建议反打跨盘被动泄洪项！")
            else:
                col_c2.success("✅ **【链条传动咬合平稳】** 市场传动流速在合理物理对冲区间，无宏观诱捕断层。")

        except Exception as e:
            st.error("🚨 模块七运行异常，请检查填写数据。")
            st.code(traceback.format_exc())

# ==============================================================================
# ===================== ⚽ 模块二：进球数多维风控 =====================
# ==============================================================================
elif active_module == "⚽ 模块二：进球数多维风控":
    st.header(f"⚽ {current_match} - 进球数全维透视")
    tab1, tab2, tab3 = st.tabs(["🟢 浅水区", "🟡 中水区", "🔴 深水区"])
    def render_goals_ui(wl, match_id):
        z2, z3, z4, z5, z6, v_limit = render_thresholds("m2", match_id, wl)
        col_ext1, col_ext2 = st.columns(2)
        with col_ext1: safe_number_input(f"主队亚指让球", f"m2_hcp_{match_id}_{wl}", -0.75, format="%.2f", step=0.25)
        with col_ext2: safe_number_input(f"大小球盘口", f"m2_ou_{match_id}_{wl}", 2.50, format="%.2f", step=0.25)
        res_m2 = render_odds_grid("m2", match_id, wl, opts_m2, cols_m2, init_m2)
        calc_key = f"m2_calc_{match_id}_{wl}"
        if calc_key not in st.session_state: st.session_state[calc_key] = False
        if st.button(f"🚀 执行 {wl} 扫描", type="primary", key=f"btn_{calc_key}"): st.session_state[calc_key] = True
        if st.session_state[calc_key]:
            c_odds, j_odds, d_odds = pd.to_numeric(res_m2['初盘(C)'], errors='coerce'), pd.to_numeric(res_m2['T-60(J)'], errors='coerce'), pd.to_numeric(res_m2['临场(D)'], errors='coerce')
            c_7, c_ou = calc_pure_prob_array(c_odds[0:8]), calc_pure_prob_array(c_odds[8:10])
            j_7, j_ou = calc_pure_prob_array(j_odds[0:8]), calc_pure_prob_array(j_odds[8:10])
            d_7, d_ou = calc_pure_prob_array(d_odds[0:8]), calc_pure_prob_array(d_odds[8:10])
            prob_c, prob_j, prob_d = np.concatenate([c_7, c_ou]), np.concatenate([j_7, j_ou]), np.concatenate([d_7, d_ou])
            delta, ev, v_delta = np.round(prob_d - prob_c, 4), np.round(prob_c * d_odds - 1, 4), np.round(prob_d - prob_j, 4)
            r_g = np.where(pd.isna(delta), "➖", np.where(delta >= z2*2, "🌋 极度过热", np.where(delta >= z2, "🚨 史诗级重防", np.where(delta >= z3, "🔥 首席主防", np.where(delta >= z4, "🟡 显著流入", np.where(delta >= z5, "↗️ 温和介入", np.where(delta <= -z2*2, "🕳️ 极度冰封", np.where(delta <= -z2, "🧊 极限绞杀", np.where(delta <= -z3, "📉 坚决抛弃", np.where(delta <= -z4, "↘️ 显著流失", np.where(delta <= -z5, "⏬ 微幅流失", "⚪ 边缘震荡")))))))))))
            r_h = np.where(pd.isna(ev), "➖", np.where(ev >= -0.10, "🌟 绝对正价值", np.where(ev >= -0.15, "🟢 极度高潜", np.where(ev >= -0.18, "🟡 合理磨损", np.where(ev >= -0.22, "📉 劣势赔付", np.where(ev >= -0.25, "🚨 杀猪盘预警", "🩸 抽水深渊"))))))
            r_i = np.where(pd.isna(delta) | pd.isna(ev), "➖", np.where((delta >= z2*1.5) & (ev <= -0.25), "🩸 嗜血诱导", np.where((delta >= z3) & (delta < z2*1.5) & (ev <= -0.08) & (ev >= -0.25), "🎯 精确制导", np.where((delta <= -z3) & (ev > 0), "☠️ 淬毒诱饵", "⚪ "))))
            r_l = np.where(pd.isna(v_delta), "➖ ", np.where(v_delta >= v_limit, "⚡ 绝杀爆发", np.where(v_delta <= -v_limit, "🩸 极速撤离", "⚪ 匀速平稳")))
            out_df2 = pd.DataFrame({"选项": opts_m2, "动量(Delta)": delta, "期望值(EV)": ev, "加速度(V)": v_delta, "动量雷达": r_g, "价值仪": r_h, "自动防伪": r_i, "狙击雷达": r_l})
            st.markdown("### 📊 终极进球数扫描雷达")
            st.dataframe(out_df2.fillna(""), hide_index=True, use_container_width=True)
    with tab1: render_goals_ui("浅水区", current_match)
    with tab2: render_goals_ui("中水区", current_match)
    with tab3: render_goals_ui("深水区", current_match)

# ==============================================================================
# ===================== 🔭 模块五：状态转移与跨盘约束引擎 =====================
# ==============================================================================
elif active_module == "🔭 模块五：V15 状态转移与跨盘约束引擎":
    st.header(f"🔭 {current_match} - V15 状态转移与跨盘约束引擎")
    st.caption("【高阶重构版】全面引入 质量加权摩擦当量、马尔可夫转移偏度 与 跨盘口物理锁链，降维透视机构内幕。")
    
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
    if st.button("🚀 启动 V15 高阶重构精算引擎", type="primary", use_container_width=True, key=f"btn_{calc_key_m5}"): st.session_state[calc_key_m5] = True
        
    if st.session_state[calc_key_m5]:
        st.markdown("---")
        try:
            c_365_g, d_365_g = safe_extract_array(res_m5_g['365初盘']), safe_extract_array(res_m5_g['365临场'])
            c_tc_g,  d_tc_g  = safe_extract_array(res_m5_g['体彩初盘']), safe_extract_array(res_m5_g['体彩临场'])
            c_tc_h,  d_tc_h  = safe_extract_array(res_m5_h['体彩初盘']), safe_extract_array(res_m5_h['体彩临场'])
            
            p_tc_c_g, p_tc_d_g = calc_pure_prob_array(c_tc_g), calc_pure_prob_array(d_tc_g)
            p_tc_c_h, p_tc_d_h = calc_pure_prob_array(c_tc_h), calc_pure_prob_array(d_tc_h)
            math_g, math_h = generate_poisson_baselines(m5_ou_val, m5_hcp_val)

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
                if odds_drop < -0.15 and d_tc_g[i] > 8.0: tag += " [⚡定点爆破]"

                df_g_rows.append({"进球数": opts_m5_g[i], "体彩临场": f"{d_tc_g[i]:.2f}", "体彩纯率": f"{p_tc_d_g[i]:.4f}" if not pd.isna(p_tc_d_g[i]) else "➖", "泊松期望": f"{math_g[i]:.4f}" if not pd.isna(math_g[i]) else "➖", "流速(Δ)": f"{(p_tc_d_g[i] - p_tc_c_g[i]):.4f}" if not pd.isna(p_tc_d_g[i]) else "➖", "质量加权摩擦(Friction)": tag})
                
            st.markdown("## ⚽ V15.0 进球数微观精算阵列")
            under_idx = math.floor(m5_ou_val) if m5_ou_val > 0 else 0
            if under_idx > 7: under_idx = 7
            tc_under = np.sum(p_tc_d_g[:under_idx+1])
            math_under = np.sum(math_g[:under_idx+1])
            diff_under = round(tc_under - math_under, 4)
            
            if diff_under > 0.0500: st.error(f"🚨 **跨盘口逻辑撕裂：** 体彩进球数矩阵在【小球区间】发生严重质量塌陷(超物理预期 {diff_under*100:+.2f}%)！")
            elif diff_under < -0.0500: st.warning(f"🌪️ **跨盘口逆向撕裂：** 体彩进球数矩阵在【大球区间】防御力度畸高！")
            else: st.success(f"⚖️ **跨盘口物理锁定完美：** 进球数细分结构与 {m5_ou_val} 大小球盘口匹配。")

            st.dataframe(pd.DataFrame(df_g_rows), hide_index=True, use_container_width=True)
            st.markdown("<br>", unsafe_allow_html=True)
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
                if odds_drop < -0.20 and d_tc_h[i] > 10.0: tag += " [⚡高赔定向坍塌]"

                df_h_rows.append({"半/全场": opts_m5_h[i], "体彩临场": f"{d_tc_h[i]:.2f}", "体彩纯率": f"{p_tc_d_h[i]:.4f}" if not pd.isna(p_tc_d_h[i]) else "➖", "泊松期望": f"{math_h[i]:.4f}" if not pd.isna(math_h[i]) else "➖", "流速(Δ)": f"{(p_tc_d_h[i] - p_tc_c_h[i]):.4f}" if not pd.isna(p_tc_d_h[i]) else "➖", "马尔可夫摩擦(Friction)": tag})
                
            col_m1, col_m2 = st.columns(2)
            if fric_h[3] > 0.0500 and fric_h[0] < 0.0100: col_m1.error("⏱️ **【状态转移剧本曝光】** 庄家重金死守‘平/胜’！真实的反杀剧本在下半场！")
            elif fric_h[0] > 0.0500 and fric_h[3] < 0.0100: col_m1.success("⚡ **【闪电战偏度曝光】** 庄家对‘胜/胜’进行极限物理降水防守！")
            else: col_m1.info("⚪ **【主场动能平稳】** 状态转移基本符合常规。")
            if fric_h[4] > 0.0600: col_m2.warning("🧊 **【全场冻结偏度】** ‘平/平’呈现极端质量摩擦，全场防沉闷绝杀！")
            st.dataframe(pd.DataFrame(df_h_rows), hide_index=True, use_container_width=True)
        except Exception as e:
            st.error("🚨 模块五运行异常。")
            st.code(traceback.format_exc())

# ==============================================================================
# ===================== 🎲 模块六：365 核心全息约束 =====================
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
        except Exception as e:
            st.error("🚨 365 独立模块运行异常，请检查填写数据。")
            st.code(traceback.format_exc())
