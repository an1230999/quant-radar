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

# 强制核弹级清理：粉毁旧版本引发的一切残留
if "FX2_V_FINAL_31" not in st.session_state:
    st.session_state.clear()
    st.session_state["FX2_V_FINAL_31"] = True

# ================= 2. 🔐 核心防盗门：访问密码 =================
def check_password():
    if "password_correct" not in st.session_state: st.session_state["password_correct"] = False
    if not st.session_state["password_correct"]:
        st.markdown("<h2 style='text-align: center; margin-top: 100px;'>🔒 FX2 全维量化终端 - 访问受限</h2>", unsafe_allow_html=True)
        pwd = st.text_input("请输入访问密钥：", type="password", key="pwd_input")
        col1, col2, col3 = st.columns([1,1,1])
        with col2:
            if st.button("🚀 解锁终端", use_container_width=True):
                if pwd == "FX888":  # <--- 在此修改专属密码
                    st.session_state["password_correct"] = True
                    st.rerun()
                else:
                    st.error("❌ 密钥验证失败，请重新输入。")
        return False
    return True

if not check_password(): st.stop()
st.title("🏦 FX2 全维量化对冲终端 (V14.0满血版 + V15全息复刻引擎)")

# ================= 3. 核心数学引擎 (全抗 NaN 防御) =================
def calc_pure_prob_array(arr):
    arr = np.array(arr, dtype=float)
    if pd.isna(arr).any() or (arr == 0).any():
        return np.full(len(arr), np.nan)
    raw = 1.0 / arr
    return np.round(raw / np.nansum(raw), 4)

def dixon_coles_full_matrix(lambda_, mu_, rho_):
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
    return pd.DataFrame(P_col_rounded, columns=cols, index=idx), p_hw2, p_hw1, p_draw, p_au, P_col_rounded

# ================= 4. 🌟 终极防闪退墙 (废除表格，改用矩阵) =================
def safe_number_input(label, state_key, default_val, format="%.4f", step=0.0010):
    wid_key = "wid_" + state_key
    if state_key not in st.session_state: st.session_state[state_key] = default_val
    def cb(): st.session_state[state_key] = st.session_state[wid_key]
    if wid_key not in st.session_state: st.session_state[wid_key] = st.session_state[state_key]
    return st.number_input(label, value=st.session_state[wid_key], format=format, step=step, key=wid_key, on_change=cb)

def render_odds_grid(module_key, match_id, wl, options, col_names, init_data):
    st.markdown(f"### 📥 {wl} 矩阵录入区")
    num_cols = len(col_names)
    grid_cols = st.columns([1.5] + [1] * num_cols)
    grid_cols[0].markdown("**玩法选项**")
    for j, cname in enumerate(col_names): grid_cols[j+1].markdown(f"**{cname}**")
        
    results = {cname: [] for cname in col_names}
    for i, opt in enumerate(options):
        cols = st.columns([1.5] + [1] * num_cols)
        cols[0].markdown(f"*{opt}*")
        for j, cname in enumerate(col_names):
            state_key, wid_key = f"{module_key}_{match_id}_{wl}_r{i}_c{j}", f"wid_{module_key}_{match_id}_{wl}_r{i}_c{j}"
            if state_key not in st.session_state: st.session_state[state_key] = init_data[i][j]
            def make_cb(s=state_key, w=wid_key):
                def cb(): st.session_state[s] = st.session_state[w]
                return cb
            if wid_key not in st.session_state: st.session_state[wid_key] = st.session_state[state_key]
            
            val = cols[j+1].number_input(f"隐藏{i}{j}", value=st.session_state[wid_key], format="%.3f", step=0.05, key=wid_key, on_change=make_cb(), label_visibility="collapsed")
            results[cname].append(val)
    return results

# ================= 5. 底座初始数据参数 =================
opts_m1 = ["标盘-胜", "标盘-平", "标盘-负", "让盘-胜", "让盘-平", "让盘-负"]
cols_m1 = ["初盘", "临场"]
init_m1 = [[2.45, 2.32], [3.20, 3.20], [2.45, 2.60], [5.50, 5.30], [4.10, 4.00], [1.42, 1.45]]

opts_m2 = ["0球", "1球", "2球", "3球", "4球", "5球", "6球", "7+球", "大球", "小球"]
cols_m2 = ["初盘(C)", "T-60(J)", "临场(D)"]
init_m2 = [[15.0, None, 15.5], [5.5, None, 5.9], [3.6, None, 3.8], [3.45, None, 3.10], [4.9, None, 4.7], [8.25, None, 8.50], [15.0, None, 16.0], [22.0, None, 24.0], [0.65, None, 0.50], [1.75, None, 1.15]]

opts_m3 = ["标准盘", "让球盘"]
cols_m3 = ["胜", "平", "负", "国彩让球数"]
init_m3 = [[2.32, 3.20, 2.60, 0.0], [5.30, 4.00, 1.45, -1.0]]

# M5 参数
opts_m5_g = ["0球", "1球", "2球", "3球", "4球", "5球", "6球", "7+球"]
cols_m5_new = ["365赔率", "马会赔率", "体彩赔率"]
init_m5_g = [[17.0, 15.0, 17.0], [6.5, 5.8, 6.5], [4.0, 3.9, 4.0], [4.0, 3.7, 3.65], [5.0, 4.35, 4.25], [8.0, 6.6, 7.0], [15.0, 11.0, 12.0], [19.0, 16.0, 18.0]]

opts_m5_h = ["胜胜", "胜平", "胜负", "平胜", "平平", "平负", "负胜", "负平", "负负"]
init_m5_h = [[4.333, 3.95, 3.7], [13.0, 12.5, 13.0], [23.0, 23.0, 26.0], [6.5, 6.0, 6.65], [6.0, 5.4, 5.85], [6.0, 5.8, 6.6], [23.0, 24.0, 28.0], [13.0, 12.5, 13.0], [4.0, 3.65, 3.55]]

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
current_match = st.radio("🏆 切换并发赛事 (独立加密封存，切换永不丢失)：", matches_list, horizontal=True)
st.sidebar.title("🧭 矩阵控制台")
active_module = st.sidebar.radio("=== 核心风控体系 ===", ["⚔️ 模块一：欧亚大盘体系", "⚽ 模块二：进球数多维风控", "🎫 模块三：高阶工具 (DC矩阵)", "🧬 模块四：异构交叉与零和对冲", "🔭 模块五：V15 全息精算引擎"])

# ================= 7. 模块一：欧亚大盘 (保留原样无损) =================
if active_module == "⚔️ 模块一：欧亚大盘体系":
    st.header(f"⚔️ {current_match} - 欧亚大盘体系")
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
            for i in range(6):
                c_prob, s_t, d_prob, u_t = prob_c[i], s_theo[i], prob_d[i], u_theo[i]
                if not pd.isna(s_t) and not pd.isna(u_t) and not pd.isna(c_prob):
                    diff_c, diff_d = c_prob - s_t, d_prob - u_t
                    t_open[i] = "🔻 极限低开" if diff_c >= z2 else "📉 显著低开" if diff_c >= z3 else "🔺 极限高开" if diff_c <= -z2 else "📈 显著高开" if diff_c <= -z3 else "⚪ 体系平衡"
                    v_open[i] = "🔻 极限低开" if diff_d >= z2 else "📉 显著低开" if diff_d >= z3 else "🔺 极限高开" if diff_d <= -z2 else "📈 显著高开" if diff_d <= -z3 else "⚪ 体系平衡"
                    traj = diff_d - diff_c
                    w_traj[i] = "🚨 剧烈砸盘" if traj >= 0.02 else "📉 步步紧逼" if traj >= 0.01 else "🚨 疯狂拉高" if traj <= -0.02 else "📈 门槛放宽" if traj <= -0.01 else "⚪ 伪装平稳"
                    struct = round(diff_d, 4)
                    if delta[i] >= z3: aa_hedge[i] = "✅ 黄金共振" if struct >= z4 else "🚨 致命背离" if struct <= -z4 else "🟡 结构中立"
                    elif delta[i] <= -z3: aa_hedge[i] = "🎁 暗度陈仓" if struct >= z4 else "🧊 真实抛弃" if struct <= -z4 else "⚪ 结构中立"
                    else: aa_hedge[i] = "🌋 静态死防" if struct >= z3 else "🕸️ 静态诱网" if struct <= -z3 else "⚪ 动量未达标"

            out_main = pd.DataFrame({"选项": opts_m1, "初纯净概率": prob_c, "临纯净概率": prob_d, "动量(Delta)": delta, "热度测算": heat, "净抽水偏离": dev, "返还率滤镜": filter_q, "底座概率": s_theo, "初盘定性": t_open, "轨迹研判": w_traj, "时空双杀": aa_hedge})
            st.markdown("### 📊 欧亚基础底座透视")
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

            gap_h = round((delta[3] + delta[4]) - delta[0], 4) if h_val < 0 else round(delta[3] - (delta[0] + delta[1]), 4)
            gap_a = round(delta[5] - (delta[1] + delta[2]), 4) if h_val < 0 else round((delta[1] + delta[2]) - delta[5], 4)
            c1, c2 = st.columns(2)
            c1.metric(f"主队【让{abs(h_val)}球方】流速净值", f"{gap_h:.4f}")
            c2.metric(f"客队【受让{abs(h_val)}球方】流速净值", f"{gap_a:.4f}")

    with tab1: render_main_handicap_ui("浅水区", current_match)
    with tab2: render_main_handicap_ui("中水区", current_match)
    with tab3: render_main_handicap_ui("深水区", current_match)

# ================= 8. 模块二：进球数多维风控 (绝对不变) =================
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
            
            if not pd.isna(c_7).all():
                even_prob, odd_prob = round(float(np.nansum(c_7[[0,2,4,6]])), 4), round(float(np.nansum(c_7[[1,3,5,7]])), 4)
                h_val2 = st.session_state[f"m2_hcp_{match_id}_{wl}"]
                ou_val = st.session_state[f"m2_ou_{match_id}_{wl}"]
                if abs(h_val2) <= 0.25: core_g = "0球, 1球, 2球"
                elif abs(h_val2) <= 0.75: core_g = "2球, 3球"
                elif abs(h_val2) <= 1.25: core_g = "3球, 4球"
                else: core_g = "4球, 5+球"
                min_idx = np.nanargmin(c_odds[0:8])
                match_s = "✅ 亚欧完美共振" if str(opts_m2[min_idx]) in core_g else "🚨 严重逻辑背离"
                
                c1, c2, c3, c4 = st.columns(4)
                c1.info(f"⚖️ 奇偶结构 -> 偶: {even_prob} | 奇: {odd_prob}")
                c2.info(f"🎯 亚指核心区 -> {core_g}")
                c3.info(f"🗺️ 交叉共振 -> {match_s}")
                c4.info(f"⚽ 大小球盘口 -> {ou_val}")

    with tab1: render_goals_ui("浅水区", current_match)
    with tab2: render_goals_ui("中水区", current_match)
    with tab3: render_goals_ui("深水区", current_match)

# ================= 9. 模块三：高阶工具 (绝对不变) =================
elif active_module == "🎫 模块三：高阶工具 (DC矩阵)":
    st.header(f"🎫 {current_match} - 高阶价值提纯")
    
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
            res_m3 = render_odds_grid("m3", current_match, "全局", opts_m3, cols_m3, init_m3)
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

# ================= 10. 模块四：异构交叉与零和对冲 (绝对不变) =================
elif active_module == "🧬 模块四：异构交叉与零和对冲":
    st.header(f"🧬 {current_match} - 终极异构验证与对冲引擎")
    source_wl = st.radio("📡 选择底层数据提取源 (与模块一联动)：", ["浅水区", "中水区", "深水区"], horizontal=True)
    tab_a, tab_b, tab_c = st.tabs(["🔍 亚盘 vs xG 撕裂检测", "🏦 机构暗水剥离 (凯利敞口)", "⚖️ 荷兰式绝对零和对冲器"])
    
    with tab_a:
        st.markdown("### 🔍 异构交叉验证：盘口物理边界 vs 泊松数学期望")
        st.info(f"原理：自动提取【模块一：{source_wl}】的让球盘，与【模块三】算出的泊松预期净胜球进行对比。如果让球盘远超数学期望，即为极致诱导！")
        try:
            ah_val = st.session_state.get(f"m1_hcp_{current_match}_{source_wl}", -1.0)
            tg_val = st.session_state.get(f"m3_tg_{current_match}", 2.75)
            hcp_val = st.session_state.get(f"m3_hcp_{current_match}", 0.0)
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
        st.info("原理：通过临场赔率反算机构的资金盈亏平衡点。如果某一项赔付敞口指数异常大，说明机构在悄悄吸收冷门重注！")
        try:
            d_odds = [
                st.session_state.get(f"m1_{current_match}_{source_wl}_r0_c1", 2.32),
                st.session_state.get(f"m1_{current_match}_{source_wl}_r1_c1", 3.20),
                st.session_state.get(f"m1_{current_match}_{source_wl}_r2_c1", 2.60)
            ]
            d_odds = pd.to_numeric(d_odds, errors='coerce')
            if np.isnan(d_odds).any(): raise ValueError
            
            implied = 1.0 / d_odds
            margin = np.sum(implied) - 1
            fair_prob = implied / (1 + margin)
            liability = fair_prob * d_odds
            
            df_kelly = pd.DataFrame({"赛果": ["主胜", "平局", "客胜"], f"{source_wl}临场赔率": d_odds, "被动抽水率": [f"{margin*100:.2f}%"]*3, "真实概率": np.round(fair_prob, 4), "⚠️ 机构敞口指数": np.round(liability, 4)})
            st.dataframe(df_kelly, hide_index=True, use_container_width=True)
            max_idx = np.argmax(liability)
            st.error(f"💣 **暗水警报：** 当前机构对 **【{df_kelly['赛果'][max_idx]}】** 的赔付敞口最为敏感，存在防范动作！")
        except:
            st.warning(f"⚠️ 请先在【模块一：{source_wl}】确认标盘临场赔率。")

    with tab_c:
        st.markdown("### ⚖️ 荷兰式绝对零和对冲器 (Dutching Calculator)")
        c1, c2, c3 = st.columns(3)
        with c1: total_capital = safe_number_input("💰 计划投入总资金", f"m4_cap_{current_match}", 1000.0, format="%.0f", step=100.0)
        with c2: odd_a = safe_number_input("选项 A 赔率", f"m4_oddA_{current_match}", 2.00, format="%.2f", step=0.01)
        with c3: odd_b = safe_number_input("选项 B 赔率", f"m4_oddB_{current_match}", 3.00, format="%.2f", step=0.01)
        
        if odd_a > 1 and odd_b > 1:
            implied_a, implied_b = 1/odd_a, 1/odd_b
            total_implied = implied_a + implied_b
            stake_a, stake_b = (implied_a / total_implied) * total_capital, (implied_b / total_implied) * total_capital
            profit = (stake_a * odd_a) - total_capital
            
            st.markdown("#### 🎯 终极执行指令：")
            col_r1, col_r2, col_r3 = st.columns(3)
            col_r1.success(f"**买入 选项A：** `{stake_a:.2f}` 元")
            col_r2.success(f"**买入 选项B：** `{stake_b:.2f}` 元")
            if profit > 0: col_r3.info(f"**保底净利润：** `+{profit:.2f}` 元")
            else: col_r3.error(f"**不可避免损耗：** `{profit:.2f}` 元")

# ================= 11. 模块五：V15 全息精算引擎 (Excel 1:1 完美复刻版) =================
elif active_module == "🔭 模块五：V15 全息精算引擎":
    st.header(f"🔭 {current_match} - V15 全息量化精算实验室")
    st.caption("【硬核复刻版】完全还原 Excel 原生 J列/K列 战术文案面板，剥离所有渲染 BUG，极限防闪退。")
    
    # --- 原生泊松引擎 ---
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

    # --- Excel 原生逻辑重构 (J列 偏离梯度预警) ---
    def get_j_warning(dev):
        if pd.isna(dev): return "➖"
        if dev <= -0.15: return "🕳️ SSS级断崖诱导"
        if dev <= -0.08: return "🕸️ SS级高赔陷阱"
        if dev >= 0.12: return "🛡️ SSS级核心压制"
        if dev >= 0.05: return "🛡️ S级温和设防"
        return "⚪ 市场均衡波动"

    # --- Excel 原生逻辑重构 (K列 进球数终极决断) ---
    def get_k_goal(i, dev, b365, hk, tc, p365, pHK, pTC, m3, rankTC, rankEU, p_math):
        is_even = (i % 2 == 0)
        is_odd = not is_even
        
        if i == 0 and hk <= 7 and hk > 0: 
            return "☠️ 【极端风控】马会0球跌破7.0，封死平局空间，防0-0闷平！"
        if i == 1 and hk > 0 and b365 > 0 and hk < 4.0: 
            return "🚨 【物理倒挂】马会1球异常低开，重点防范！"
        if b365 > 0 and (hk / b365) <= 0.5: 
            return "🌋 【马会断崖】马会赔率不足365一半！无脑追击！"
        if p365 > 0 and ((pHK / p365) - 1) >= 0.15: 
            return f"🦇 【马会独立重防】马会纯概率高出欧洲 {((pHK/p365 - 1)*100):.2f}%！独家绝密情报，重点防范！"
        if b365 == 4.333: 
            return "🎯 【阻力锚点】365启动4.333，进入对冲博弈盲区"
        
        # 融入泊松暗防逻辑
        if not pd.isna(pTC) and not pd.isna(p_math) and p_math > 0 and (pTC - p_math) >= 0.08 and p_math < 0.08:
            return f"🚨 【数学背离】机构强开深盘防守(超泊松期望 {((pTC-p_math)*100):.1f}%)，警惕极小概率事件造热！"
        
        if rankTC < rankEU and dev >= 0.05:
            if (is_even and m3 <= -0.015) or (is_odd and m3 >= 0.015): 
                return "💎 【量化升维】体彩排位越级重防且共振奇偶，核心稳胆！"
            else: 
                return "⚠️ 【排位提升】体彩防守升级，但奇偶无支撑，建议降注。"
        if dev >= 0.08 and p365 >= 0.10: 
            return "🛡️ 【主力压制】主流区体彩超8%重防，打出概率高。"
        if dev <= -0.10 and rankTC > rankEU: 
            return "🕳️ 【双重塌陷】体彩排位下降且降超10%，绝对诱导！"
        if dev <= -0.15: 
            return "☠️ 【数据黑洞】纯概率严重脱节，虚假高赔陷阱。"
        
        return "⚪ 市场资金均衡，无结构性破绽"

    # --- Excel 原生逻辑重构 (K列 半全场终极决断) ---
    def get_k_htft(name, dev, b365, hk, tc, p365, pHK, pTC, rankTC, rankEU, n16, p_math):
        last_char = name[-1]
        in_trend = last_char in n16
        
        if name == "平平" and tc <= 4 and tc > 0: 
            return "✅ 【底线预警】平平压至4.0以下，大概率沉闷。"
        if (name == "胜负" or name == "负胜") and hk < 20 and hk > 0: 
            return "☠️ 【剧本嗅探】马会逆转赔率低于20，防惊天大冷！"
        if b365 == 4.333: 
            return "🎯 【阻力锚点】365精算4.333占位！若吻合全场大势则极易打出临近溢出项！"
        
        # 融入泊松暗防逻辑
        if not pd.isna(pTC) and not pd.isna(p_math) and p_math > 0 and (pTC - p_math) >= 0.08 and p_math < 0.05:
            return f"🚨 【数学背离】体彩防守远超泊松期望({p_math*100:.1f}%)，警惕机构做局冷门！"
        
        if rankTC < rankEU and dev >= 0.05:
            if in_trend: return f"💎 【降维打击】体彩越级防守，且吻合宏观【{n16}】，重注定胆！"
            else: return "⚠️ 【跨区设防】排位提升但违背主趋势，谨慎介入。"
        if dev >= 0.12 and p365 >= 0.05: 
            return "🛡️ 【资金堆积】常态概率区遭遇重防，机构真实惧怕项。"
        if dev <= -0.15 and rankTC > rankEU: 
            return "🕳️ 【诱导深渊】体彩排位倒退且大幅放水，死路一条！"
        if dev <= -0.20: 
            return "☠️ 【极寒冰点】偏离度破-20%，填仓诱导项，直接剔除。"
        if dev <= -0.08:
            if in_trend: return f"🕸️ 【顺势毒饵】即便吻合大势，但偏离度进入诱导区({dev*100:.2f}%)，坚决放弃！"
            else: return f"🕸️ 【高赔陷阱】偏离度暴跌({dev*100:.2f}%)，毫无机会。"
        if in_trend:
            if dev > 0: return f"💎 【顺势暗防】吻合大势且体彩暗中降赔(+{dev*100:.2f}%)，核心优选！"
            else: return f"🔎 【潜行顺流】结构健康，且底层暗合全场大势【{n16}】，重点防范！"
            
        return "⚪ 赔付结构吻合欧亚共识，按兵不动"


    # --- 防报错模块五专用渲染 ---
    def m5_safe_input(label, base_key, default_val, format="%.2f", step=0.25):
        wid_key = "w_" + base_key
        if base_key not in st.session_state: st.session_state[base_key] = default_val
        def _cb(): st.session_state[base_key] = st.session_state[wid_key]
        return st.number_input(label, value=st.session_state.get(base_key, default_val), format=format, step=step, key=wid_key, on_change=_cb)

    def m5_render_grid(module_key, match_id, wl, options, col_names, init_data):
        st.markdown(f"### 📥 {wl} 矩阵数据录入")
        num_cols = len(col_names)
        grid_cols = st.columns([1.5] + [1] * num_cols)
        grid_cols[0].markdown("**玩法选项**")
        for j, cname in enumerate(col_names): grid_cols[j+1].markdown(f"**{cname}**")
            
        results = {cname: [] for cname in col_names}
        for i, opt in enumerate(options):
            cols = st.columns([1.5] + [1] * num_cols)
            cols[0].markdown(f"*{opt}*")
            for j, cname in enumerate(col_names):
                base_key = f"{module_key}_{match_id}_{wl}_r{i}_c{j}"
                wid_key = f"w_{base_key}"
                if base_key not in st.session_state: st.session_state[base_key] = init_data[i][j]
                def make_cb(b=base_key, w=wid_key):
                    def cb(): st.session_state[b] = st.session_state[w]
                    return cb
                val = cols[j+1].number_input(f"隐藏{i}{j}", value=st.session_state.get(base_key, init_data[i][j]), format="%.3f", step=0.05, key=wid_key, on_change=make_cb(), label_visibility="collapsed")
                results[cname].append(val)
        return results

    # --- UI 部署 ---
    with st.expander("⚙️ 引擎底座参数 (点击展开设定大盘基准)", expanded=True):
        c1, c2 = st.columns(2)
        with c1: m5_ou_val = m5_safe_input("大小球基准盘", f"m5_ou_{current_match}", 2.50, format="%.2f", step=0.25)
        with c2: m5_hcp_val = m5_safe_input("亚指让球(主让为负)", f"m5_hcp_{current_match}", -0.50, format="%.2f", step=0.25)
        st.info("💡 系统将根据这组盘口生成底层的绝对数学基准线，用于隐秘拦截不合理选项。")
        
    tab_g, tab_h = st.tabs(["⚽ 进球数数据录入", "🔵 半全场数据录入"])
    with tab_g: res_m5_g = m5_render_grid("m5g", current_match, "进球数", opts_m5_g, cols_m5_new, init_m5_g)
    with tab_h: res_m5_h = m5_render_grid("m5h", current_match, "半/全场", opts_m5_h, cols_m5_new, init_m5_h)
    
    calc_key_m5 = f"m5_calc_{current_match}"
    if calc_key_m5 not in st.session_state: st.session_state[calc_key_m5] = False
    
    st.write("")
    if st.button("🚀 启动 V15 全息分析引擎", type="primary", use_container_width=True, key=f"btn_{calc_key_m5}"):
        st.session_state[calc_key_m5] = True
        
    if st.session_state[calc_key_m5]:
        st.markdown("---")
        try:
            # 1. 终极安全数据抽取与转换 (修正了列名提取暗号，绝对不会报 KeyError)
            math_g, math_h = generate_poisson_baselines(m5_ou_val, m5_hcp_val)
            g_365 = np.nan_to_num(np.array(res_m5_g['365赔率'], dtype=float), nan=0.0)
            g_hk  = np.nan_to_num(np.array(res_m5_g['马会赔率'], dtype=float), nan=0.0)
            g_tc  = np.nan_to_num(np.array(res_m5_g['体彩赔率'], dtype=float), nan=0.0)
            
            h_365 = np.nan_to_num(np.array(res_m5_h['365赔率'], dtype=float), nan=0.0)
            h_hk  = np.nan_to_num(np.array(res_m5_h['马会赔率'], dtype=float), nan=0.0)
            h_tc  = np.nan_to_num(np.array(res_m5_h['体彩赔率'], dtype=float), nan=0.0)
            
            p365_g, pHK_g, pTC_g = calc_pure_prob_array(g_365), calc_pure_prob_array(g_hk), calc_pure_prob_array(g_tc)
            p365_h, pHK_h, pTC_h = calc_pure_prob_array(h_365), calc_pure_prob_array(h_hk), calc_pure_prob_array(h_tc)
            
            cons_g = np.round((p365_g + pHK_g) / 2, 4)
            cons_h = np.round((p365_h + pHK_h) / 2, 4)
            
            dev_g = np.round((pTC_g / cons_g) - 1, 4)
            dev_h = np.round((pTC_h / cons_h) - 1, 4)

            # 2. 核心大势推演
            tcW = float(pTC_h[0] + pTC_h[3] + pTC_h[6]) if not np.isnan(pTC_h).any() else 0.0
            tcD = float(pTC_h[1] + pTC_h[4] + pTC_h[7]) if not np.isnan(pTC_h).any() else 0.0
            tcL = float(pTC_h[2] + pTC_h[5] + pTC_h[8]) if not np.isnan(pTC_h).any() else 0.0
            
            trends = [{"n": "胜", "v": tcW}, {"n": "平", "v": tcD}, {"n": "负", "v": tcL}]
            trends.sort(key=lambda x: x["v"], reverse=True)
            n16 = "【未定】"
            if tcW > 0 or tcD > 0 or tcL > 0:
                n16 = "【双轨】" + trends[0]["n"] + trends[1]["n"] if (trends[0]["v"] - trends[1]["v"]) <= 0.03 else trends[0]["n"]

            tc_odd_sum = float(pTC_g[1]+pTC_g[3]+pTC_g[5]+pTC_g[7]) if not np.isnan(pTC_g).any() else 0.0
            eu_odd_sum = float(cons_g[1]+cons_g[3]+cons_g[5]+cons_g[7]) if not np.isnan(cons_g).any() else 0.0
            m3 = round(tc_odd_sum - eu_odd_sum, 4)
            
            # 内部撕裂检测 (安全过滤掉所有的NaN值防止计算崩溃)
            odd_devs = [x for x in [dev_g[1], dev_g[3], dev_g[5], dev_g[7]] if not pd.isna(x)]
            if len(odd_devs) > 0:
                is_tear = (max(odd_devs) - min(odd_devs)) >= 0.10
            else:
                is_tear = False

            m3_text = ""
            if m3 >= 0.025: m3_text = f"🌋 【SSS级防单】极值(+{m3*100:.2f}%)！体彩对奇数痛下杀手，单数球为全场核心稳胆！"
            elif m3 >= 0.015: m3_text = f"🔴 【S级防单】高位(+{m3*100:.2f}%)！宏观资金倒向单数，符合进球数共振条件！"
            elif m3 <= -0.025: m3_text = f"🌋 【SSS级防双】极值({m3*100:.2f}%)！体彩对偶数痛下杀手，双数球为全场核心稳胆！"
            elif m3 <= -0.015: m3_text = f"🔵 【S级防双】高位({m3*100:.2f}%)！宏观资金倒向双数，符合进球数共振条件！"
            elif is_tear: m3_text = f"🌪️ 【内部撕裂】宏观极微({m3*100:.2f}%)，但单数球内部震幅超10%，庄家交叉做局，请以K列独立诊断为准！"
            else: m3_text = f"⚪ 【绝对均衡】差值极微({m3*100:.2f}%)，单双资金完美平衡，无任何做局痕迹。"

            # 3. 构建进球数表列 (使用 if else 防止 NaN 打印出来不美观)
            df_g_rows = []
            for i in range(8):
                rankTC = sum(1 for v in pTC_g if v > pTC_g[i]) + 1
                rankEU = sum(1 for v in p365_g if v > p365_g[i]) + 1
                
                j_warn = get_j_warning(dev_g[i])
                k_dec = get_k_goal(i, dev_g[i], g_365[i], g_hk[i], g_tc[i], p365_g[i], pHK_g[i], pTC_g[i], m3, rankTC, rankEU, math_g[i])
                
                df_g_rows.append({
                    "进球数": opts_m5_g[i],
                    "365赔率": f"{g_365[i]:.2f}",
                    "马会赔率": f"{g_hk[i]:.2f}",
                    "体彩赔率": f"{g_tc[i]:.2f}",
                    "365纯净率": f"{p365_g[i]:.4f}" if not pd.isna(p365_g[i]) else "➖",
                    "马会纯净率": f"{pHK_g[i]:.4f}" if not pd.isna(pHK_g[i]) else "➖",
                    "体彩纯净率": f"{pTC_g[i]:.4f}" if not pd.isna(pTC_g[i]) else "➖",
                    "欧亚共识基准线": f"{cons_g[i]:.4f}" if not pd.isna(cons_g[i]) else "➖",
                    "体彩结构偏离率": f"{dev_g[i]:.4f}" if not pd.isna(dev_g[i]) else "➖",
                    "偏离梯度预警": j_warn,
                    "进球数跨维特殊值与终极决断": k_dec
                })

            # 4. 构建半全场表列
            df_h_rows = []
            for i in range(9):
                rankTC = sum(1 for v in pTC_h if v > pTC_h[i]) + 1
                rankEU = sum(1 for v in p365_h if v > p365_h[i]) + 1
                
                j_warn = get_j_warning(dev_h[i])
                k_dec = get_k_htft(opts_m5_h[i], dev_h[i], h_365[i], h_hk[i], h_tc[i], p365_h[i], pHK_h[i], pTC_h[i], rankTC, rankEU, n16, math_h[i])
                
                df_h_rows.append({
                    "半/全场": opts_m5_h[i],
                    "365赔率": f"{h_365[i]:.2f}",
                    "马会赔率": f"{h_hk[i]:.2f}",
                    "体彩赔率": f"{h_tc[i]:.2f}",
                    "365纯净率": f"{p365_h[i]:.4f}" if not pd.isna(p365_h[i]) else "➖",
                    "马会纯净率": f"{pHK_h[i]:.4f}" if not pd.isna(pHK_h[i]) else "➖",
                    "体彩纯净率": f"{pTC_h[i]:.4f}" if not pd.isna(pTC_h[i]) else "➖",
                    "欧亚共识基准线": f"{cons_h[i]:.4f}" if not pd.isna(cons_h[i]) else "➖",
                    "体彩结构偏离率": f"{dev_h[i]:.4f}" if not pd.isna(dev_h[i]) else "➖",
                    "偏离梯度预警": j_warn,
                    "半全场跨维特殊值与终极决断": k_dec
                })

            df_g_final = pd.DataFrame(df_g_rows)
            df_h_final = pd.DataFrame(df_h_rows)

            # 5. UI 排版输出 (完美一比一还原Excel截图)
            st.markdown("## 📊 V15.0 终极全息雷达阵列 (原貌重现版)")
            
            # --- 进球数展示区 ---
            c_g1, c_g2, c_g3, c_g4 = st.columns([1,1,1,2])
            c_g1.metric("体彩(奇)纯净汇总", f"{tc_odd_sum:.4f}")
            c_g2.metric("外围(奇)共识汇总", f"{eu_odd_sum:.4f}")
            c_g3.metric("🎯 宏观奇偶博弈差", f"{m3:.4f}")
            c_g4.info(m3_text)
            
            st.dataframe(df_g_final, hide_index=True, use_container_width=True)
            
            st.markdown("<br><hr><br>", unsafe_allow_html=True)

            # --- 半全场展示区 ---
            c_h1, c_h2, c_h3, c_h4 = st.columns([1,1,1,2])
            c_h1.metric("体彩宏观全场(胜)纯率", f"{tcW:.4f}")
            c_h2.metric("体彩宏观全场(平)纯率", f"{tcD:.4f}")
            c_h3.metric("体彩宏观全场(负)纯率", f"{tcL:.4f}")
            c_h4.success(f"**🎯 体彩全场总趋势定调： {n16}**")
            
            st.dataframe(df_h_final, hide_index=True, use_container_width=True)

        except Exception as e:
            st.error("🚨 **系统捕捉到环境异常**")
            st.warning(f"直接报错原因：`{str(e)}`")
            with st.expander("展开查看详细代码追踪报错"):
                st.code(traceback.format_exc())
