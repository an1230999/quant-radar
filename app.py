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
    "🎯 模块七：全息连通器·深盘猎杀终端 (V30)",
    "🔥 模块X：全息综合引擎 (M1+M3+M4)",
    "⚽ 模块二：进球与比分·微积分测谎仪 (重构版)",
    "🔭 模块五：V15 状态转移与跨盘约束引擎",
    "🎲 模块六：365 核心全息约束 (剧本剥离版)",
    "🪐 模块八：北单全息偏度与多维筹码对撞舱 (M8)"
])

# ================= 🛡️ 视线避让同步机制 ====================
current_m2_wl_viewing = st.session_state.get("m2_source_wl_radio", "浅水区")
is_viewing_m2 = (active_module == "⚽ 模块二：进球与比分·微积分测谎仪 (重构版)")
is_viewing_m8 = (active_module == "🪐 模块八：北单全息偏度与多维筹码对撞舱 (M8)")

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
# ===================== 🎯 模块七：全息连通器·深盘猎杀终端 =====================
# ==============================================================================
if active_module == "🎯 模块七：全息连通器·深盘猎杀终端 (V30)":
    st.header(f"🎯 {current_match} - V30 全息连通器·深盘猎杀显微镜")
    st.caption("【微创手术终局】专杀竞彩定向卷。当遇到深盘【官方整盘不售标盘】时，启动泊松分布与现存让球纯率，后台一字不差逆向重构出庄家的“幽灵标盘1X2”。")

    col_e1, col_e2, col_e3 = st.columns(3)
    with col_e1: m7_tg = safe_number_input("全场大小球期望 (泊松基底)", f"m7_tg_{current_match}", 3.00, format="%.2f", step=0.25)
    with col_e2: m7_hcp = safe_number_input("初始盘面亚指 (主让为负)", f"m7_hcp_{current_match}", -1.50, format="%.2f", step=0.25)
    with col_e3: m7_k = safe_number_input("体彩实际让球数 K (填 -2,-3 或 2,3)", f"m7_k_{current_match}", -2.0, format="%.0f", step=1.0)

    is_all_std_closed = st.toggle("🚫 【本场标盘官方未开售】(后台代偿还原幽灵标盘)", value=True)

    opts_std = ["标盘-胜", "标盘-平", "标盘-负"]
    opts_let = [f"让球({int(m7_k)})胜", f"让球({int(m7_k)})平", f"让球({int(m7_k)})负"]

    col_std, col_let = st.columns(2)
    with col_std:
        if is_all_std_closed: st.warning("🔒 官方屏蔽标盘，后台逆向解耦。")
        else: res_std = render_odds_grid("m7std", current_match, "体彩【标准盘】", opts_std, ["初盘", "临场"], [[1.15, 1.10], [6.50, 7.00], [15.0, 19.0]])
    with col_let: res_let = render_odds_grid("m7let", current_match, "体彩【让球盘】", opts_let, ["初盘", "临场"], [[2.10, 1.95], [4.00, 3.80], [2.70, 2.90]])

    calc_key_m7 = f"m7_v30_calc_{current_match}"
    if calc_key_m7 not in st.session_state: st.session_state[calc_key_m7] = False
    if st.button("🚀 启动 V30 幽灵重构与测谎引擎", type="primary", use_container_width=True): st.session_state[calc_key_m7] = True

    if st.session_state[calc_key_m7]:
        try:
            xg_h, xg_a = (m7_tg - m7_hcp)/2.0, (m7_tg + m7_hcp)/2.0
            _, _, _, _, _, P_mat = dixon_coles_full_matrix(xg_h, xg_a, -0.15)
            K_int = int(m7_k)
            p_poisson_exact_1_home = sum(P_mat[h, a] for h in range(8) for a in range(8) if h - a == 1)
            p_poisson_exact_1_away = sum(P_mat[h, a] for h in range(8) for a in range(8) if a - h == 1)
            p_poisson_draw = sum(P_mat[h, a] for h in range(8) for a in range(8) if h == a)
            p_poisson_away_win = sum(P_mat[h, a] for h in range(8) for a in range(8) if a > h)
            p_poisson_home_win = sum(P_mat[h, a] for h in range(8) for a in range(8) if h > a)

            let_c, let_d = safe_extract_array(res_let['初盘']), safe_extract_array(res_let['临场'])
            p_let_c, p_let_d = calc_pure_prob_array(let_c), calc_pure_prob_array(let_d)
            pd_show_list, p_std_c_final, p_std_d_final = [], np.zeros(3), np.zeros(3)

            if is_all_std_closed:
                if K_int < 0: 
                    pw_c, pw_d = p_let_c[0]+p_let_c[1]+p_poisson_exact_1_home, p_let_d[0]+p_let_d[1]+p_poisson_exact_1_home
                    rc, rd = max(1-pw_c, 0.0001), max(1-pw_d, 0.0001)
                    rda = p_poisson_draw / max(p_poisson_draw+p_poisson_away_win, 0.0001)
                    p_std_c_final, p_std_d_final = np.round([pw_c, rc*rda, rc*(1-rda)], 4), np.round([pw_d, rd*rda, rd*(1-rda)], 4)
                else: 
                    pl_c, pl_d = p_let_c[2]+p_let_c[1]+p_poisson_exact_1_away, p_let_d[2]+p_let_d[1]+p_poisson_exact_1_away
                    rc, rd = max(1-pl_c, 0.0001), max(1-pl_d, 0.0001)
                    rhd = p_poisson_home_win / max(p_poisson_home_win+p_poisson_draw, 0.0001)
                    p_std_c_final, p_std_d_final = np.round([rc*rhd, rc*(1-rhd), pl_c], 4), np.round([rd*rhd, rd*(1-rhd), pl_d], 4)
                pd_show_list = [f"👻幽灵({x:.4f})" for x in p_std_d_final]
            else:
                p_std_c_final, p_std_d_final = calc_pure_prob_array(safe_extract_array(res_std['初盘'])), calc_pure_prob_array(safe_extract_array(res_std['临场']))
                pd_show_list = [f"{x:.4f}" for x in p_std_d_final]

            pd_show_list.extend([f"{x:.4f}" for x in p_let_d])
            p_all_c, p_all_d = np.concatenate([p_std_c_final, p_let_c]), np.concatenate([p_std_d_final, p_let_d])
            d_all = np.round(p_all_d - p_all_c, 4)

            residuals = np.zeros(6)
            if K_int < 0:
                bg = p_poisson_exact_1_home if abs(K_int)==2 else 0.0
                residuals[0], residuals[3], residuals[4] = round(p_all_d[0]-(p_all_d[3]+p_all_d[4]+bg),4), round(p_all_d[3]-(p_all_d[0]-p_all_d[4]-bg),4), round(p_all_d[4]-(p_all_d[0]-p_all_d[3]-bg),4)
                residuals[5], residuals[1], residuals[2] = round(p_all_d[5]-(p_all_d[1]+p_all_d[2]+bg),4), round(p_all_d[1]-(p_all_d[5]-p_all_d[2]-bg),4), round(p_all_d[2]-(p_all_d[5]-p_all_d[1]-bg),4)
            elif K_int > 0:
                bg = p_poisson_exact_1_away if abs(K_int)==2 else 0.0
                residuals[3], residuals[0], residuals[1] = round(p_all_d[3]-(p_all_d[0]+p_all_d[1]+bg),4), round(p_all_d[0]-(p_all_d[3]-p_all_d[1]-bg),4), round(p_all_d[1]-(p_all_d[3]-p_all_d[0]-bg),4)
                residuals[2], residuals[4], residuals[5] = round(p_all_d[2]-(p_all_d[4]+p_all_d[5]+bg),4), round(p_all_d[4]-(p_all_d[2]-p_all_d[5]-bg),4), round(p_all_d[5]-(p_all_d[2]-p_all_d[4]-bg),4)
            else: residuals = np.round(np.concatenate([p_all_d[0:3]-p_all_d[3:6], p_all_d[3:6]-p_all_d[0:3]]), 4)

            vol = np.std(d_all[~pd.isna(d_all)])
            dyn_thresh = min(round(max(vol*1.5, 0.0060), 4), 0.0220)
            rmv = np.array([round(residuals[i]/p_all_d[i],4) if p_all_d[i]>0 else 0 for i in range(6)])

            verdicts, scripts, intra, lie_r_show, rmv_show = [], [], [], [], []
            for i in range(6):
                if i < 3 and is_all_std_closed:
                    intra.append("🔒 锁盘"); lie_r_show.append("➖"); rmv_show.append("➖")
                    verdicts.append("🚫 官方未售"); scripts.append("底层代入物理纯率。"); continue

                flow, res, r = d_all[i], residuals[i], rmv[i]
                if flow > 0.025: intra.append("🔥 主力真金狂买")
                elif flow < -0.025: intra.append("🕳️ 筹码夺路出逃")
                else: intra.append("⚪ 散户微幅换手")

                if res > dyn_thresh: lie_r_show.append(f"{res:+.4f} (🔴造热)")
                elif res < -dyn_thresh: lie_r_show.append(f"{res:+.4f} (🟢筑墙)")
                else: lie_r_show.append(f"{res:+.4f} (⚪容差)")

                if r > 0.04: rmv_show.append(f"{r*100:+.2f}% (🔴诱导)")
                elif r < -0.04: rmv_show.append(f"{r*100:+.2f}% (🟢核心)")
                else: rmv_show.append(f"{r*100:+.2f}% (⚪常规)")

                if res > dyn_thresh and r > 0.04: verdicts.append("🚨 镜像畸高 (造热死坑)"); scripts.append(f"制造稳赢假象，坚决排除。")
                elif res < -dyn_thresh and r < -0.04:
                    if flow > -0.01: verdicts.append("💎 全息闭环暗水王"); scripts.append(f"承接对冲纯率，全场第一单挑位！")
                    else: verdicts.append("🧊 镜像被弃死冷"); scripts.append("冷门通道已被物理封焊。")
                else:
                    if flow >= 0.0250: verdicts.append("✅ 明牌顺势御流位"); scripts.append("主力狂买庄家顺流，无脑冲！")
                    elif flow <= -0.0250: verdicts.append("⏬ 顺流全息抛弃位"); scripts.append("市场与庄家同步放弃此端。")
                    else: verdicts.append("⚪ 连通器支点平衡"); scripts.append("常规多空博弈。")

            st.markdown("### 📊 V30 大终局体检表")
            st.dataframe(pd.DataFrame({"选项": opts_std+opts_let, "纯率(Pd)": pd_show_list, "一阶动能": intra, "连通器残差": lie_r_show, "变异度": rmv_show, "时空裁决": verdicts, "精算结论": scripts}), hide_index=True)
        except Exception as e: st.error("🚨 模块七异常。"); st.code(traceback.format_exc())

# ==============================================================================
# ===================== 🔥 模块X：全息综合引擎 (M1+M3+M4) =====================
# ==============================================================================
elif active_module == "🔥 模块X：全息综合引擎 (M1+M3+M4)":
    st.header(f"🔥 {current_match} - 模块X：全息综合引擎")
    tab_mx_1, tab_mx_2, tab_mx_3 = st.tabs(["🟢 浅水区", "🟡 中水区", "🔴 深水区"])

    def render_module_x_ui(wl, match_id):
        z2, z3, z4, z5, z6, _ = render_thresholds("mx", match_id, wl)
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1: mx_tg = safe_number_input("xG期望", f"mx_tg_{match_id}_{wl}", 2.75, step=0.25)
        with c2: mx_hm = safe_number_input("泊松亚指", f"mx_hcp_math_{match_id}_{wl}", 0.0, step=0.25)
        with c3: mx_hb = safe_number_input("机构亚指", f"mx_hcp_bookie_{match_id}_{wl}", -1.0, step=0.25)
        with c4: mx_k = safe_number_input("体彩K数", f"mx_k_{match_id}_{wl}", -1.0, format="%.0f", step=1.0)
        with c5: mx_rho = safe_number_input("DC系数ρ", f"mx_rho_{match_id}_{wl}", -0.15, step=0.01)

        res_mx = render_odds_grid("mx", match_id, wl, opts_m1, cols_m1, init_m1)
        calc_key = f"mx_calc_{match_id}_{wl}"
        if calc_key not in st.session_state: st.session_state[calc_key] = False
        if st.button(f"🚀 执行 {wl} 综合精算", type="primary", key=f"btn_{calc_key}"): st.session_state[calc_key] = True

        if st.session_state[calc_key]:
            c_o, d_o = pd.to_numeric(res_mx['初盘'], errors='coerce'), pd.to_numeric(res_mx['临场'], errors='coerce')
            p_c = np.concatenate([calc_pure_prob_array(c_o[0:3]), calc_pure_prob_array(c_o[3:6])])
            p_d = np.concatenate([calc_pure_prob_array(d_o[0:3]), calc_pure_prob_array(d_o[3:6])])
            delta = np.round(p_d - p_c, 4)

            st.markdown("### ⚔️ M1 欧亚底座透视")
            st.dataframe(pd.DataFrame({"选项": opts_m1, "初纯率": p_c, "临纯率": p_d, "Delta动能": delta}).fillna(""), hide_index=True)

            st.markdown("### 🎫 M3 双泊松提纯 & M4 敞口")
            df_m, ph2, ph1, pdr, pau, P_col = dixon_coles_full_matrix((mx_tg-mx_hm)/2, (mx_tg+mx_hm)/2, mx_rho)
            c_m1, c_m2 = st.columns([1.5, 1])
            with c_m1: st.dataframe(df_m.style.format("{:.4f}"))
            with c_m2:
                intl = np.array([sum(P_col[i,j] for i in range(8) for j in range(8) if i-j>0), sum(P_col[i,j] for i in range(8) for j in range(8) if i-j==0), sum(P_col[i,j] for i in range(8) for j in range(8) if i-j<0), sum(P_col[i,j] for i in range(8) for j in range(8) if i-j>-int(mx_k)), sum(P_col[i,j] for i in range(8) for j in range(8) if i-j==-int(mx_k)), sum(P_col[i,j] for i in range(8) for j in range(8) if i-j<-int(mx_k))])
                st.dataframe(pd.DataFrame({"投注项": opts_m1, "数学EV": np.round(d_o*intl-1, 4)}).fillna(""), hide_index=True)

    with tab_mx_1: render_module_x_ui("浅水区", current_match)
    with tab_mx_2: render_module_x_ui("中水区", current_match)
    with tab_mx_3: render_module_x_ui("深水区", current_match)

# ==============================================================================
# ===================== ⚽ 模块二：体彩竞彩微积分比分测谎 =====================
# ==============================================================================
elif active_module == "⚽ 模块二：进球与比分·微积分测谎仪 (重构版)":
    st.header(f"⚽ {current_match} - 体彩比分对账舱 (31项静默版)")
    m2_wl = st.radio("📡 继承大盘源：", ["浅水区", "中水区", "深水区"], horizontal=True, key="m2_source_wl_radio")
    st.session_state["last_active_m2_match"], st.session_state["last_active_m2_wl"] = current_match, m2_wl
    mx_tg = st.session_state.get(f"mx_tg_{current_match}_{m2_wl}", 2.75)
    mx_hm = st.session_state.get(f"mx_hcp_math_{current_match}_{m2_wl}", 0.0)
    mx_k = st.session_state.get(f"mx_k_{current_match}_{m2_wl}", -1.0)
    mx_rho = st.session_state.get(f"mx_rho_{current_match}_{m2_wl}", -0.15)
    std_w = st.session_state.get(f"mx_{current_match}_{m2_wl}_r0_c1", 2.32)

    res_m2_g = render_odds_grid("m2_g_pool", current_match, f"体彩【进球数】", opts_m5_g, ["初盘", "临场"], init_m5_g)

    b_k = f"m2_base_df_{current_match}_{m2_wl}"
    if b_k not in st.session_state: st.session_state[b_k] = pd.DataFrame([{"比分项": s, "实际终赔": 0.0} for s in ["1-0","2-0","2-1","3-0","3-1","3-2","4-0","4-1","4-2","5-0","5-1","5-2","胜其他","0-0","1-1","2-2","3-3","平其他","0-1","0-2","1-2","0-3","1-3","2-3","0-4","1-4","2-4","0-5","1-5","2-5","负其他"]])
    ed_df = st.data_editor(st.session_state[b_k], disabled=["比分项"], hide_index=True, use_container_width=True, key=f"wid_{b_k}")
    st.session_state[f"m2_shadow_{current_match}_{m2_wl}"] = ed_df

    if st.button("🚀 启动体彩多维拓扑对账", type="primary"):
        try:
            _, _, _, _, _, P_mat = dixon_coles_full_matrix((mx_tg-mx_hm)/2, (mx_tg+mx_hm)/2, mx_rho)
            marg = 0.1150 if pd.isna(std_w) else (1/std_w + 1/st.session_state.get(f"mx_{current_match}_{m2_wl}_r1_c1",3.20) + 1/st.session_state.get(f"mx_{current_match}_{m2_wl}_r2_c1",2.60) - 1.0)
            p_g_d = calc_pure_prob_array(safe_extract_array(res_m2_g['临场']))
            out_sc, gb_s = [], np.zeros(8)

            for _, row in ed_df.iterrows():
                sc_s = str(row["比分项"])
                try: odd_v = float(row["实际终赔"])
                except: continue
                if odd_v <= 1.0: continue

                if sc_s == "胜其他": X, Y, gn = 4, 3, 7
                elif sc_s == "平其他": X, Y, gn = 4, 4, 7
                elif sc_s == "负其他": X, Y, gn = 3, 4, 7
                else: 
                    X, Y = int(sc_s.split("-")[0]), int(sc_s.split("-")[1])
                    gn = min(X+Y, 7)

                pp = round((1.0/odd_v)/max(1+marg,0.0001), 4)
                gb_s[gn] += pp
                pm = P_mat[min(X,7), min(Y,7)] if X<8 and Y<8 else 0.0001
                res = round(pp - pm, 4); rmv = round(res/max(pp,0.0001), 4)
                vd = "🚨 畸高诱捕墙" if res>0.025 and rmv>0.05 else ("🛡️ 核心防波堤" if res<-0.025 and rmv<-0.05 else "⚪ 常规中枢")
                out_sc.append({"核心比分": sc_s, "体彩终赔": odd_v, "比分纯率": pp, "物理期望": pm, "子盘残差": f"{res:+.4f}", "期权偏度": vd})

            st.markdown("#### 📊 看板一：微观比分测谎台")
            if out_sc: st.dataframe(pd.DataFrame(out_sc), hide_index=True)
            else: st.warning("⚠️ 审计台空载。")

            st.markdown("#### 🧮 看板二：球数与积分对账")
            gc = [{"玩法": opts_m5_g[i], "总池": p_g_d[i], "积分": round(gb_s[i],4), "残差": f"{p_g_d[i]-gb_s[i]:+.4f}"} for i in range(8)]
            st.dataframe(pd.DataFrame(gc), hide_index=True)
        except Exception as e: st.error("🚨 故障"); st.code(traceback.format_exc())

# ==============================================================================
# ===================== 🔭 模块五 & 🎲 模块六 =====================
# ==============================================================================
elif active_module == "🔭 模块五：V15 状态转移与跨盘约束引擎":
    st.header(f"🔭 {current_match} - 状态转移与跨盘约束")
    col_e1, col_e2 = st.columns(2)
    with col_e1: m5_ou = safe_number_input("大小球基准盘口", f"m5_ou_{current_match}", 2.50, step=0.25)
    with col_e2: m5_hm = safe_number_input("亚指让球基准", f"m5_hm_{current_match}", -0.50, step=0.25)
    
    t_g, t_h = st.tabs(["⚽ 进球数录入", "🔵 半全场录入"])
    with t_g: res_m5_g = render_odds_grid("m5g", current_match, "进球数", opts_m5_g, cols_m5_new, init_m5_g)
    with t_h: res_m5_h = render_odds_grid("m5h", current_match, "半/全场", opts_m5_h, cols_m5_new, init_m5_h)
    
    if st.button("🚀 启动 V15 状态转移精算", type="primary"):
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

            p_tc_d_g = calc_pure_prob_array(safe_extract_array(res_m5_g['体彩临场']))
            fric_g = np.round((p_tc_d_g - math_g) * safe_extract_array(res_m5_g['体彩临场']), 4)
            st.dataframe(pd.DataFrame([{"进球数": opts_m5_g[i], "纯率": p_tc_d_g[i], "期望": math_g[i], "摩擦当量": f"{fric_g[i]:+.4f}"} for i in range(8)]), hide_index=True)

            p_tc_d_h = calc_pure_prob_array(safe_extract_array(res_m5_h['体彩临场']))
            fric_h = np.round((p_tc_d_h - math_h) * safe_extract_array(res_m5_h['体彩临场']), 4)
            st.dataframe(pd.DataFrame([{"半/全场": opts_m5_h[i], "纯率": p_tc_d_h[i], "期望": math_h[i], "摩擦当量": f"{fric_h[i]:+.4f}"} for i in range(9)]), hide_index=True)
        except Exception as e: st.error("🚨 异常"); st.code(traceback.format_exc())

elif active_module == "🎲 模块六：365 核心全息约束 (剧本剥离版)":
    st.header(f"🎲 {current_match} - 365 剧本剥离")
    res_m6 = render_odds_grid("m6std", current_match, "标盘", ["主胜","平局","客胜"], ["初盘","临场"], [[2.0,1.9],[3.5,3.4],[3.6,4.0]])
    if st.button("🚀 启动 365 流速提取"):
        d_std = np.round(calc_pure_prob_array(safe_extract_array(res_m6['临场'])) - calc_pure_prob_array(safe_extract_array(res_m6['初盘'])), 4)
        st.dataframe(pd.DataFrame({"选项": ["主胜","平局","客胜"], "Δ": d_std}), hide_index=True)
        # ==============================================================================
# ===================== 🪐 模块八：北单专属多维对撞舱 (M8) =====================
# ==============================================================================
elif active_module == "🪐 模块八：北单全息偏度与多维筹码对撞舱 (M8)":
    st.header(f"🪐 {current_match} - M8 北单超级对撞机 (白话解密版)")
    st.caption("【全量闭环/25项专属版】拒绝假大神黑话。左手物理现货，右手北单0.65派奖机制，直白告诉你买谁赚！")

    col_m8_1, col_m8_2, col_m8_3 = st.columns(3)
    with col_m8_1: m8_tg = safe_number_input("大小球期望(xG基底)", f"m8_tg_{current_match}", 2.75, format="%.2f", step=0.25)
    with col_m8_2: m8_hcp = safe_number_input("欧亚实力基准亚指", f"m8_hcp_{current_match}", -0.50, format="%.2f", step=0.25)
    with col_m8_3: m8_dil = safe_number_input("晚高峰散户稀释系数(γ)", f"m8_dil_{current_match}", 0.1250, format="%.4f", step=0.0100, help="预估夜间散户跟风大单对热门SP值的磨损稀释率")

    xg_h_m8, xg_a_m8 = (m8_tg - m8_hcp)/2.0, (m8_tg + m8_hcp)/2.0
    _, _, _, _, _, P_mat_m8 = dixon_coles_full_matrix(xg_h_m8, xg_a_m8, -0.15)

    tab_m8_a, tab_m8_b, tab_m8_c, tab_m8_d = st.tabs(["📊 1X2大盘与胜负过关", "🎯 全量25项比分(北单专属)", "⚖️ 进球数 vs 单双克隆套利", "⏱️ 半全场游资狙击"])

    # ==================== M8 / Tab 1：大盘与过关 ====================
    with tab_m8_a:
        st.markdown("#### ① 胜平负(1X2) 连续PDF对撞")
        res_m8_eu = render_odds_grid("m8_eu", current_match, "左轨：欧洲现货终赔 (Crown/Bet365)", ["主胜/上盘", "平局/中端", "客胜/下盘"], ["现货终赔"], [[2.05], [3.40], [3.60]])
        res_m8_bd = render_odds_grid("m8_bd", current_match, "右轨：北单页面即时SP", ["北单胜(3)", "北单平(1)", "北单负(0)"], ["即时SP"], [[1.85], [3.45], [4.10]])

        st.markdown("#### ② 胜负过关(SFGG) 二元数字期权剥离")
        c_sf1, c_sf2 = st.columns([1, 2])
        with c_sf1: m8_sfgg_k = safe_number_input("官方胜负过关浮动让球", f"m8_sfgg_k_{current_match}", -0.50, format="%.2f", step=0.50)
        with c_sf2: res_m8_sfgg = render_odds_grid("m8_sfgg", current_match, "胜负过关即时SP (无平局)", ["主胜过关", "客胜过关"], ["过关SP"], [[1.55], [2.35]])

        if st.button("🚀 执行 Tab1 基础大盘对撞", key=f"btn_m8_a_{current_match}", type="primary"):
            # 1X2 计算
            eu_d = safe_extract_array(res_m8_eu['现货终赔'])
            p_true_eu = calc_pure_prob_array(eu_d)
            bd_sp = np.where((s:=safe_extract_array(res_m8_bd['即时SP']))<=1, 1.01, s)
            
            p_cw = np.round((0.65/bd_sp)/np.nansum(0.65/bd_sp), 4)
            sp_pred = np.round(bd_sp*(1.0 - ((p_cw**1.38)/np.nansum(p_cw**1.38))*m8_dil), 4)
            ev_1x2 = np.round(p_true_eu * sp_pred - 1.0, 4)

            v1x2 = []
            for e in ev_1x2:
                if e > 0.05: v1x2.append(f"✅ 严重低估！赔率高，值得买入 (+{e*100:.1f}%)")
                elif e > 0: v1x2.append(f"🟢 略微低估，可以轻仓套利 (+{e*100:.1f}%)")
                elif e > -0.06: v1x2.append(f"🟡 常规抽水，买入长期亏钱 ({e*100:.1f}%)")
                else: v1x2.append(f"🚨 散户踩踏！奖金太低，坚决别买 ({e*100:.1f}%)")

            st.markdown("##### 📈 1X2 连续期望体检表")
            st.dataframe(pd.DataFrame({"选项": ["北单胜", "北单平", "北单负"], "欧洲真率": p_true_eu, "彩民驻资": p_cw, "T-60预估SP": sp_pred, "买入划算度(EV)": [f"{x:+.4f}" for x in ev_1x2], "白话建议": v1x2}), hide_index=True)
            
            st.info("💡 **【大盘分析白话说明】**\n"
                    "**买入划算度 (期望EV)** 代表你下注1元长期的盈亏。如果为 **正数**，说明全国散户**不看好**这个选项，导致它的奖金池极其丰厚，属于【高赔率金矿】，值得买入；"
                    "如果为 **负数**，说明散户资金**严重踩踏**，奖金被严重摊薄稀释，属于【赔本赚吆喝】，应坚决规避（就算你看好它能赢，也不要在这个盘口买）。")

            # 胜负过关
            sf_sp = np.where((sf:=safe_extract_array(res_m8_sfgg['过关SP']))<=1, 1.01, sf)
            p_sf_cw = np.round((0.65/sf_sp)/np.nansum(0.65/sf_sp), 4)
            p_sf_w = sum(P_mat_m8[h, a] for h in range(8) for a in range(8) if h - a > -m8_sfgg_k)
            p_sf_true = np.round([p_sf_w, 1.0 - p_sf_w], 4)
            sf_ev = np.round(p_sf_true * sf_sp - 1.0, 4)

            st.markdown("##### ⚔️ 胜负过关测谎单")
            st.dataframe(pd.DataFrame({"选项": ["主过关", "客过关"], "欧洲亚指真率": p_sf_true, "国内散户认为的胜率": p_sf_cw, "认知差": np.round(p_sf_true-p_sf_cw, 4), "买入划算度(EV)": [f"{x:+.4f}" for x in sf_ev]}), hide_index=True)

    # ==================== M8 / Tab 2：25项专属比分 ====================
    with tab_m8_b:
        st.markdown("#### 🎯 北单专属 25 项固定比分交割台")
        b8_k = f"m8_base_sc_{current_match}"
        if b8_k not in st.session_state: 
            sc25 = ["1-0","2-0","2-1","3-0","3-1","3-2","4-0","4-1","4-2","胜其他", "0-0","1-1","2-2","3-3","平其他", "0-1","0-2","1-2","0-3","1-3","2-3","0-4","1-4","2-4","负其他"]
            st.session_state[b8_k] = pd.DataFrame([{"比分": s, "SP": 0.0} for s in sc25])
        
        e_b8 = st.data_editor(st.session_state[b8_k], disabled=["比分"], hide_index=True, use_container_width=True, key=f"wid_{b8_k}")
        st.session_state[f"m8_shadow_{current_match}"] = e_b8

        if st.button("🚀 执行 25项比分显微审计", key=f"btn_m8_b_{current_match}", type="primary"):
            p_all_w = sum(P_mat_m8[h, a] for h in range(8) for a in range(8) if h > a)
            p_all_d = sum(P_mat_m8[h, a] for h in range(8) for a in range(8) if h == a)
            p_all_l = sum(P_mat_m8[h, a] for h in range(8) for a in range(8) if h < a)
            
            p_w_ex = sum([P_mat_m8[int(x.split('-')[0]), int(x.split('-')[1])] for x in ["1-0","2-0","2-1","3-0","3-1","3-2","4-0","4-1","4-2"]])
            p_d_ex = sum([P_mat_m8[int(x.split('-')[0]), int(x.split('-')[1])] for x in ["0-0","1-1","2-2","3-3"]])
            p_l_ex = sum([P_mat_m8[int(x.split('-')[0]), int(x.split('-')[1])] for x in ["0-1","0-2","1-2","0-3","1-3","2-3","0-4","1-4","2-4"]])
            
            p_other_w = max(p_all_w - p_w_ex, 0.0001)
            p_other_d = max(p_all_d - p_d_ex, 0.0001)
            p_other_l = max(p_all_l - p_l_ex, 0.0001)

            o8 = []
            for _, r in e_b8.iterrows():
                sc, sp = str(r["比分"]), float(r["SP"])
                if sp <= 1.0: continue
                p_c = round(0.65/sp, 4)
                if sc == "胜其他": p_m = round(p_other_w, 4)
                elif sc == "平其他": p_m = round(p_other_d, 4)
                elif sc == "负其他": p_m = round(p_other_l, 4)
                else: 
                    X, Y = int(sc.split("-")[0]), int(sc.split("-")[1])
                    p_m = round(P_mat_m8[min(X,7), min(Y,7)], 4)
                
                df = round(p_m - p_c, 4)
                vt = "💎【值得买】散户没买，奖金极高，防冷神单！" if df>0.02 else ("🚨【千万别碰】散户瞎跟风，奖金太低，纯属毒药！" if df<-0.02 else "⚪【赔率正常】可以常规打底")
                o8.append({"比分":sc, "页面SP":sp, "资金驻资率":p_c, "欧洲物理期望":p_m, "概率偏度":f"{df:+.4f}", "白话裁决": vt})
            
            if o8: 
                st.dataframe(pd.DataFrame(o8), hide_index=True, use_container_width=True)
                st.info("💡 **【比分分析白话说明】**\n"
                        "北单25项比分中，**【胜其他】已在后台严格融合了 5-0、5-1、6-x 以及 7+进球等极端赛果的数学积分。**\n"
                        "• **概率偏度 为 正数 (💎)**：代表这个比分极有可能打出，但国内散户**根本没买**。它的SP值处于极度虚高的暴利状态，一旦爆冷直接暴富，强烈建议买入！\n"
                        "• **概率偏度 为 负数 (🚨)**：代表国内散户出于情怀瞎买，把这个比分的池子挤爆了，SP值极低，性价比极差，坚决不要买。")
            else: st.warning("请在上方填入至少1个比分的SP值。")

    # ==================== M8 / Tab 3：克隆双胞胎套利 ====================
    with tab_m8_c:
        st.markdown("#### ⚖️ 「总进球数」 vs 「上下单双」无脑白嫖套利")
        st.caption("这是利用北单官方规则设定的漏洞，帮你找出风险完全一样，但能多赚钱的抽屉！")
        c_g1, c_g2 = st.columns(2)
        with c_g1: res_g8 = render_odds_grid("m8_g", current_match, "总进球即时SP", opts_m5_g, ["SP值"], [[9.5],[4.1],[3.5],[3.8],[5.6],[11],[21],[31]])
        with c_g2: res_p8 = render_odds_grid("m8_p", current_match, "上下单双即时SP", ["下单(1球)", "下双(0+2)", "上双(4+6)", "上单(3+5+7+)"], ["SP值"], [[4.8], [2.6], [4.4], [2.3]])

        if st.button("🚀 启动双胞胎克隆套利扫描", key=f"btn_m8_c_{current_match}", type="primary"):
            sp_g = np.where((s:=safe_extract_array(res_g8['SP值']))<=1, 999, s)
            sp_p = np.where((p:=safe_extract_array(res_p8['SP值']))<=1, 999, p)
            p_g, p_p = np.round(0.65/sp_g, 4), np.round(0.65/sp_p, 4)
            rws = [
                {"套利对比": "【1球】 vs 【下单】", "进球池驻资率": p_g[1], "单双池驻资率": p_p[0], "资金利差": round(p_g[1]-p_p[0],4), "系统直接告诉你怎么买": "👉 无脑买【下单】多白赚利差！" if p_g[1]>p_p[0] else ("👉 无脑买【1球】多赚利差！" if p_g[1]<p_p[0] else "随便买，一样赚")},
                {"套利对比": "【0或2球】 vs 【下双】", "进球池驻资率": round(p_g[0]+p_g[2],4), "单双池驻资率": p_p[1], "资金利差": round((p_g[0]+p_g[2])-p_p[1],4), "系统直接告诉你怎么买": "👉 闭眼买【下双】省本金！" if (p_g[0]+p_g[2])>p_p[1] else "👉 拆开来买【0球】和【2球】！"},
                {"套利对比": "【4或6球】 vs 【上双】", "进球池驻资率": round(p_g[4]+p_g[6],4), "单双池驻资率": p_p[2], "资金利差": round((p_g[4]+p_g[6])-p_p[2],4), "系统直接告诉你怎么买": "👉 闭眼买【上双】省本金！" if (p_g[4]+p_g[6])>p_p[2] else "👉 拆开来买【4球】和【6球】！"},
                {"套利对比": "【3,5,7+球】 vs 【上单】", "进球池驻资率": round(p_g[3]+p_g[5]+p_g[7],4), "单双池驻资率": p_p[3], "资金利差": round((p_g[3]+p_g[5]+p_g[7])-p_p[3],4), "系统直接告诉你怎么买": "👉 闭眼买【上单】省本金！" if (p_g[3]+p_g[5]+p_g[7])>p_p[3] else "👉 拆开来单独买奇数球！"}
            ]
            st.dataframe(pd.DataFrame(rws), hide_index=True, use_container_width=True)
            st.success("💡 **【套利分析白话说明】**\n"
                       "比如【下单】在物理规则上 100% 等于【全场进 1 球】。你在下注时，照着表格里 **“系统直接告诉你怎么买”** 的箭头方向无脑买即可。你承担了完全一样的比赛风险，但结算能拿的钱比别人多得多！")

    # ==================== M8 / Tab 4：半全场老鼠仓 ====================
    with tab_m8_d:
        st.markdown("#### ⏱️ 半全场 9项老鼠仓狙击 (抓取神秘内幕游资)")
        st.caption("散户很少买半全场，这里面藏着知情游资的“剧本脚印”。")
        opts_h8 = ["胜/胜", "胜/平", "胜/负", "平/胜", "平/平", "平/负", "负/胜", "负/平", "负/负"]
        res_h8 = render_odds_grid("m8_htft", current_match, "半全场页面即时SP", opts_h8, ["SP值"], [[3.2],[15.0],[31.0],[5.8],[4.9],[6.5],[31.0],[15.0],[4.6]])
        
        if st.button("🚀 执行老鼠仓足迹扫描", key=f"btn_m8_d_{current_match}", type="primary"):
            sp_hf = np.where((h:=safe_extract_array(res_h8['SP值']))<=1, 999, h)
            p_hf_cw = np.round(0.65/sp_hf, 4)
            
            def pm(k, l): return math.exp(-l)*(l**k)/math.factorial(k) if l>0 else (1.0 if k==0 else 0.0)
            hh, ha, fh, fa = xg_h_m8*0.45, xg_a_m8*0.45, xg_h_m8*0.55, xg_a_m8*0.55
            ph, p2 = {"W":0,"D":0,"L":0}, {"W":0,"D":0,"L":0}
            for x in range(8):
                for y in range(8):
                    _ph, _p2 = pm(x,hh)*pm(y,ha), pm(x,fh)*pm(y,fa)
                    if x>y: ph["W"]+=_ph; p2["W"]+=_p2
                    elif x==y: ph["D"]+=_ph; p2["D"]+=_p2
                    else: ph["L"]+=_ph; p2["L"]+=_p2
            
            m_hf = np.round([
                ph["W"]*(p2["W"]+p2["D"]*0.5), ph["W"]*(p2["L"]*0.8+p2["D"]*0.5), ph["W"]*p2["L"]*0.2,
                ph["D"]*p2["W"], ph["D"]*p2["D"], ph["D"]*p2["L"],
                ph["L"]*p2["W"]*0.2, ph["L"]*(p2["W"]*0.8+p2["D"]*0.5), ph["L"]*(p2["L"]+p2["D"]*0.5)
            ], 4)
            m_hf = np.round(m_hf/np.sum(m_hf), 4)
            fric = np.round(m_hf - p_hf_cw, 4)
            
            h_out = []
            for k in range(9):
                f = fric[k]
                h_out.append({"半全场走向": opts_h8[k], "北单驻资率": p_hf_cw[k], "欧洲时空期望": m_hf[k], "摩擦残差": f"{f:+.4f}", "白话大解密": "🔥 【黄金大冷】散户忘了买，高收益防冷佳选！" if f>0.035 else ("🕳️ 【游资老鼠仓】极度反常的大资金在砸这个结果，小心剧本！" if f<-0.035 else "⚪ 【常规分布】无人做局")})
            st.dataframe(pd.DataFrame(h_out), hide_index=True, use_container_width=True)
            
            st.error("💡 **【老鼠仓分析白话说明】**\n"
                     "半全场池子极小，最容易暴露【内幕游资】的建仓脚印。如果表格里提示 **“🕳️ 游资老鼠仓”**，说明有极度不正常的神秘大资金在赛前死死抱团砸这个选项，暗示可能有“主力轮换/假球剧本/下半场发力绝杀”等内幕，**请务必警惕或选择跟随游资下注**！")
