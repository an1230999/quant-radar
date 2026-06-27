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

st.title("🏦 FX2 机构级全维量化终端 (大结局至尊版)")

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

# ==============================================================================
# ===================== 🎯 模块七：全息连通器·深盘猎杀终端 (V30) =====================
# ==============================================================================
if active_module == "🎯 模块七：全息刚性连通器·深盘猎杀终端 (V30)":
    st.header(f"🎯 {current_match} - V30 全息连通器·深盘猎杀显微镜")
    st.caption("【微创手术终局】专杀竞彩定向卷。当遇到深盘【官方整盘不售标盘】时，启动泊松分布与现存让球纯率，后台一字不差逆向重构出庄家的“幽灵标盘1X2”。")

    st.markdown("### 🎛️ 第一步：深盘战况与基本面基底")
    col_e1, col_e2, col_e3 = st.columns(3)
    with col_e1: m7_tg = safe_number_input("全场大小球期望 (泊松基底)", f"m7_tg_{current_match}", 3.00, format="%.2f", step=0.25)
    with col_e2: m7_hcp = safe_number_input("初始盘面亚指 (主让为负)", f"m7_hcp_{current_match}", -1.50, format="%.2f", step=0.25)
    with col_e3: m7_k = safe_number_input("体彩实际让球数 K (填 -2,-3 或 2,3)", f"m7_k_{current_match}", -2.0, format="%.0f", step=1.0)

    st.write("")
    is_all_std_closed = st.toggle("🚫 【本场标盘官方未开售】(竞彩深盘专属！勾选后标盘整盘隐身，系统通过后台暗物质方程强行逆向还原庄家的幽灵标盘！)", value=True)

    st.markdown("---")
    st.markdown("### 📥 第二步：连通器有效赔率录入")
    opts_std = ["标盘-胜", "标盘-平", "标盘-负"]
    opts_let = [f"让球({int(m7_k)})胜", f"让球({int(m7_k)})平", f"让球({int(m7_k)})负"]

    col_std, col_let = st.columns(2)
    with col_std:
        if is_all_std_closed:
            st.warning("🔒 官方整盘屏蔽标盘，录入区已物理隔离，由泊松代偿引擎在后台逆向解耦。")
        else:
            res_std = render_odds_grid("m7std", current_match, "体彩【标准盘】", opts_std, ["初盘", "临场"], [[1.15, 1.10], [6.50, 7.00], [15.0, 19.0]])

    with col_let:
        res_let = render_odds_grid("m7let", current_match, "体彩【让球盘】", opts_let, ["初盘", "临场"], [[2.10, 1.95], [4.00, 3.80], [2.70, 2.90]])

    calc_key_m7 = f"m7_v30_calc_{current_match}"
    if calc_key_m7 not in st.session_state: st.session_state[calc_key_m7] = False
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚀 启动 V30 幽灵重构与测谎引擎", type="primary", use_container_width=True, key=f"btn_{calc_key_m7}"):
        st.session_state[calc_key_m7] = True

    if st.session_state[calc_key_m7]:
        st.markdown("---")
        try:
            xg_h, xg_a = (m7_tg - m7_hcp)/2.0, (m7_tg + m7_hcp)/2.0
            _, _, _, _, _, P_mat = dixon_coles_full_matrix(xg_h, xg_a, -0.15)
            K_int = int(m7_k)

            p_poisson_exact_1_home = sum(P_mat[h, a] for h in range(8) for a in range(8) if h - a == 1)
            p_poisson_exact_1_away = sum(P_mat[h, a] for h in range(8) for a in range(8) if a - h == 1)
            p_poisson_draw = sum(P_mat[h, a] for h in range(8) for a in range(8) if h == a)
            p_poisson_away_win = sum(P_mat[h, a] for h in range(8) for a in range(8) if a > h)
            p_poisson_home_win = sum(P_mat[h, a] for h in range(8) for a in range(8) if h > a)

            let_c = safe_extract_array(res_let['初盘'])
            let_d = safe_extract_array(res_let['临场'])
            p_let_c, p_let_d = calc_pure_prob_array(let_c), calc_pure_prob_array(let_d)

            pd_show_list = []
            p_std_c_final, p_std_d_final = np.zeros(3), np.zeros(3)

            if is_all_std_closed:
                if K_int < 0: 
                    phantom_w_c = p_let_c[0] + p_let_c[1] + p_poisson_exact_1_home
                    phantom_w_d = p_let_d[0] + p_let_d[1] + p_poisson_exact_1_home
                    rem_c, rem_d = max(1.0 - phantom_w_c, 0.0001), max(1.0 - phantom_w_d, 0.0001)
                    ratio_d_to_a = p_poisson_draw / max((p_poisson_draw + p_poisson_away_win), 0.0001)
                    p_std_c_final = np.round([phantom_w_c, rem_c * ratio_d_to_a, rem_c * (1-ratio_d_to_a)], 4)
                    p_std_d_final = np.round([phantom_w_d, rem_d * ratio_d_to_a, rem_d * (1-ratio_d_to_a)], 4)
                    pd_show_list = [f"👻幽灵重构({p_std_d_final[0]:.4f})", f"👻幽灵重构({p_std_d_final[1]:.4f})", f"👻幽灵重构({p_std_d_final[2]:.4f})"]
                else: 
                    phantom_l_c = p_let_c[2] + p_let_c[1] + p_poisson_exact_1_away
                    phantom_l_d = p_let_d[2] + p_let_d[1] + p_poisson_exact_1_away
                    rem_c, rem_d = max(1.0 - phantom_l_c, 0.0001), max(1.0 - phantom_l_d, 0.0001)
                    ratio_h_to_d = p_poisson_home_win / max((p_poisson_home_win + p_poisson_draw), 0.0001)
                    p_std_c_final = np.round([rem_c * ratio_h_to_d, rem_c * (1-ratio_h_to_d), phantom_l_c], 4)
                    p_std_d_final = np.round([rem_d * ratio_h_to_d, rem_d * (1-ratio_h_to_d), phantom_l_d], 4)
                    pd_show_list = [f"👻幽灵重构({p_std_d_final[0]:.4f})", f"👻幽灵重构({p_std_d_final[1]:.4f})", f"👻幽灵重构({p_std_d_final[2]:.4f})"]
            else:
                std_c = safe_extract_array(res_std['初盘'])
                std_d = safe_extract_array(res_std['临场'])
                p_std_c_final, p_std_d_final = calc_pure_prob_array(std_c), calc_pure_prob_array(std_d)
                pd_show_list = [f"{x:.4f}" for x in p_std_d_final]

            pd_show_list.extend([f"{x:.4f}" for x in p_let_d])
            p_all_c = np.concatenate([p_std_c_final, p_let_c])
            p_all_d = np.concatenate([p_std_d_final, p_let_d])
            d_all = np.round(p_all_d - p_all_c, 4)

            residuals = np.zeros(6)
            if K_int < 0:
                bridge = p_poisson_exact_1_home if abs(K_int)==2 else 0.0
                residuals[0] = round(p_all_d[0] - (p_all_d[3] + p_all_d[4] + bridge), 4)
                residuals[3] = round(p_all_d[3] - (p_all_d[0] - p_all_d[4] - bridge), 4)
                residuals[4] = round(p_all_d[4] - (p_all_d[0] - p_all_d[3] - bridge), 4)
                residuals[5] = round(p_all_d[5] - (p_all_d[1] + p_all_d[2] + bridge), 4)
                residuals[1] = round(p_all_d[1] - (p_all_d[5] - p_all_d[2] - bridge), 4)
                residuals[2] = round(p_all_d[2] - (p_all_d[5] - p_all_d[1] - bridge), 4)
            elif K_int > 0:
                bridge = p_poisson_exact_1_away if abs(K_int)==2 else 0.0
                residuals[3] = round(p_all_d[3] - (p_all_d[0] + p_all_d[1] + bridge), 4)
                residuals[0] = round(p_all_d[0] - (p_all_d[3] - p_all_d[1] - bridge), 4)
                residuals[1] = round(p_all_d[1] - (p_all_d[3] - p_all_d[0] - bridge), 4)
                residuals[2] = round(p_all_d[2] - (p_all_d[4] + p_all_d[5] + bridge), 4)
                residuals[4] = round(p_all_d[4] - (p_all_d[2] - p_all_d[5] - bridge), 4)
                residuals[5] = round(p_all_d[5] - (p_all_d[2] - p_all_d[4] - bridge), 4)
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
                    scripts.append(f"【诱杀红线】跨盘概率被虚假拔高，精算师克扣赔率制造稳赢假象，泊松期望不支撑，坚决排除。")
                elif is_gold:
                    if flow > -0.0100:
                        verdicts.append("💎 全息闭环暗水王")
                        scripts.append(f"【核心定胆】承接对冲纯率！机构在此端承受着最真实的赔付铁壁，全场第一单挑位！")
                    else:
                        verdicts.append("🧊 镜像被弃死冷")
                        scripts.append("传动链与市场流速同步宣判死刑，冷门通道已被物理封焊。")
                elif is_poison:
                    verdicts.append("🩸 负EV抽水深渊")
                    scripts.append("体彩在此抽水率极度丧心病狂，买入即亏损，纯属散户爱国送钱位。")
                elif is_deep_val:
                    verdicts.append("🌟 物理期望金矿")
                    scripts.append("开出赔率远高于泊松物理概率，具备绝对正向博取价值！")
                else:
                    if flow >= 0.0250:
                        verdicts.append("✅ 明牌顺势御流位")
                        scripts.append("【真账实冲盘】连通器传动严丝合缝，且伴随主力资金真金白银狂买，庄家明牌顺流，顺势无脑冲！")
                    elif flow <= -0.0250:
                        verdicts.append("⏬ 顺流全息抛弃位")
                        scripts.append("【真账实弃盘】市场与庄家防线同步放弃此端，资金呈夺路出逃态势，打出概率极低。")
                    elif abs(res) > dyn_thresh * 0.5:
                        verdicts.append("🟡 盘面轻微形变")
                        scripts.append("存在微弱的受力偏移，建议结合模块一的大盘轨迹辅助研判。")
                    else:
                        verdicts.append("⚪ 连通器支点平衡")
                        scripts.append("常规受力过渡位，多空维持物理动态平衡。")

            st.markdown("### 📊 V30 幽灵重构·微创大终局体检表")
            st.caption(f"全盘动态排雷防线上限已物理锁死于：± **{dyn_thresh:.4f}**")
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
            
            gap_slice_1 = p_poisson_exact_1_home if K_int<0 else p_poisson_exact_1_away
            gap_slice_2 = p_let_d[1] 
            gap_ratio = gap_slice_1 / max(gap_slice_2, 0.0001)

            r1, r2, r3 = st.columns(3)
            r1.metric("⚖️ 胜负势能张力轴", f"{(p_all_d[0]-p_all_d[2])*100:+.1f}%", delta="主队占优" if p_all_d[0]>p_all_d[2] else "客队占优")
            r2.metric("🕳️ 刚好赢1球 vs 赢2球 绞杀比", f"{gap_ratio:.2f} 倍", help="若倍率极大，说明卡盘绝杀概率极高")
            
            flow_main = d_all[0] if K_int<0 else d_all[2]
            res_main = residuals[0] if K_int<0 else residuals[2]
            
            if flow_main >= 0.035 and abs(res_main) < 0.012:
                r3.success("定性：🚀 **教科书级物理公平盘 (顺流直冲)**\n\n**数值解码：** 核心项流速 ≥ 3.5% (主力暴力扫货)，且残差极小 (庄家未做账本抵抗)，量价齐升不设防，顺应大势重锤。")
            elif residuals[3 if K_int<0 else 5] < -0.015:
                r3.warning("定性：🎁 **底层暗水偷袭局 (去让球端)**\n\n**数值解码：** 底层核心让球防线出现 < -1.5% 的异常负残差，庄家顶着流速强行压低赔率，肉身筑墙保护下盘。")
            else:
                r3.info("定性：⚖️ **多空精算焦灼对冲局**\n\n**数值解码：** 全盘残差与流量均未触及极端红线，多空势能处于互相绞杀的稳态，无明显单边碾压或做局破绽。")

        except Exception as e:
            st.error("🚨 模块七微创运行异常。")
            st.code(traceback.format_exc())

# ==============================================================================
# ===================== 🔥 模块X：全息综合引擎 (M1+M3+M4) =====================
# ==============================================================================
elif active_module == "🔥 模块X：全息综合引擎 (M1+M3+M4)":
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
            c_odds, d_odds = pd.to_numeric(res_mx['初盘'], errors='coerce'), pd.to_numeric(res_mx['临场'], errors='coerce')
            biao_c, rang_c = calc_pure_prob_array(c_odds[0:3]), calc_pure_prob_array(c_odds[3:6])
            biao_d, rang_d = calc_pure_prob_array(d_odds[0:3]), calc_pure_prob_array(d_odds[3:6])
            prob_c, prob_d = np.concatenate([biao_c, rang_c]), np.concatenate([biao_d, rang_d])
            delta = np.round(prob_d - prob_c, 4)

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
                s_theo[5], u_theo[5] = prob_c[2] - math_hcp, prob_d[2] - math_hcp
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

            st.markdown("---")
            st.markdown("## 🎫 模块三：DC双泊松高阶提纯")
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
            st.markdown("## 🧬 模块四：终极异构验证与对冲引擎")
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
                with c1_4c: total_cap = safe_number_input("💰 资金", f"m4_c_{match_id}", 1000.0, format="%.0f", step=100.0)
                with c2_4c: oa = safe_number_input("赔率 A", f"m4_a_{match_id}", 2.00, format="%.2f", step=0.01)
                with c3_4c: ob = safe_number_input("赔率 B", f"m4_b_{match_id}", 3.00, format="%.2f", step=0.01)
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
# ===================== ⚔️ 模块一：欧亚大盘体系 (独立版) =====================
# ==============================================================================
elif active_module == "⚔️ 模块一：欧亚大盘体系 (独立版)":
    st.header(f"⚔️ {current_match} - 欧亚大盘体系")
    tab1, tab2, tab3 = st.tabs(["🟢 浅水区", "🟡 中水区", "🔴 深水区"])
    
    def render_legacy_m1(wl, match_id):
        z2, z3, z4, z5, z6, _ = render_thresholds("legacy_m1", match_id, wl)
        h_val = safe_number_input("主队亚指让球数", f"m1_legacy_hcp_{match_id}_{wl}", -1.0)
        res_m1 = render_odds_grid("legacy_m1", match_id, wl, opts_m1, ["初盘", "临场"], init_m1)
        if st.button(f"🚀 执行 {wl} 独立精算", key=f"btn_legacy_m1_{wl}"):
            c_odds = pd.to_numeric(res_m1['初盘'], errors='coerce')
            d_odds = pd.to_numeric(res_m1['临场'], errors='coerce')
            biao_c, rang_c = calc_pure_prob_array(c_odds[0:3]), calc_pure_prob_array(c_odds[3:6])
            biao_d, rang_d = calc_pure_prob_array(d_odds[0:3]), calc_pure_prob_array(d_odds[3:6])
            prob_c, prob_d = np.concatenate([biao_c, rang_c]), np.concatenate([biao_d, rang_d])
            delta = np.round(prob_d - prob_c, 4)
            st.write("📊 欧亚大盘分析完成：流速增量 (Delta)", delta)

    with tab1: render_legacy_m1("浅水区", current_match)
    with tab2: render_legacy_m1("中水区", current_match)
    with tab3: render_legacy_m1("深水区", current_match)


# ==============================================================================
# ===================== ⚽ 模块二：进球与比分·微积分测谎仪 (重构完全体) =====================
# ==============================================================================
elif active_module == "⚽ 模块二：进球数多维风控" or active_module == "⚽ 模块二：进球与比分·微积分测谎仪 (重构版)":
    st.header(f"⚽ {current_match} - 模块二：进球与比分·微积分对账舱")
    st.caption("【拓扑路由完全体】环境数据自动无缝继承自模块X，通过微积分概率质量守恒，穿透0-7球数总期权池与无限动态表格录入的比分细分行权价，极致排雷。")

    m2_source_wl = st.radio("📡 选择数据继承源 (同步自模块X大盘参数)：", ["浅水区", "中水区", "深水区"], horizontal=True)

    # 1. 自动穿透继承模块X的数据
    mx_tg_val = st.session_state.get(f"mx_tg_{current_match}_{m2_source_wl}", 2.75)
    mx_hcp_math_val = st.session_state.get(f"mx_hcp_math_{current_match}_{m2_source_wl}", 0.0)
    mx_hcp_bookie_val = st.session_state.get(f"mx_hcp_bookie_{current_match}_{m2_source_wl}", -1.0)
    mx_k_val = st.session_state.get(f"mx_k_{current_match}_{m2_source_wl}", -1.0)
    mx_rho_val = st.session_state.get(f"mx_rho_{current_match}_{m2_source_wl}", -0.15)

    # 提取大盘临场赔率
    m1_std_w = st.session_state.get(f"mx_{current_match}_{m2_source_wl}_r0_c1", 2.32)
    m1_std_d = st.session_state.get(f"mx_{current_match}_{m2_source_wl}_r1_c1", 3.20)
    m1_std_l = st.session_state.get(f"mx_{current_match}_{m2_source_wl}_r2_c1", 2.60)
    m1_let_w = st.session_state.get(f"mx_{current_match}_{m2_source_wl}_r3_c1", 5.30)
    m1_let_d = st.session_state.get(f"mx_{current_match}_{m2_source_wl}_r4_c1", 4.00)
    m1_let_l = st.session_state.get(f"mx_{current_match}_{m2_source_wl}_r5_c1", 1.45)

    st.info(f"📥 **大盘底座环境穿透成功** | 继承源: {m2_source_wl} | 预期大小球(xG): {mx_tg_val:.2f} | 实际让球数K: {int(mx_k_val)} | 让球盘口赔率: [{m1_let_w:.2f}, {m1_let_d:.2f}, {m1_let_l:.2f}]")

    st.markdown("### 📥 第一步：0-7球全量总期权池录入")
    opts_m2_goals = ["0球", "1球", "2球", "3球", "4球", "5球", "6球", "7+球"]
    init_m2_goals = [[11.0, 12.0], [5.0, 5.5], [3.5, 3.6], [3.6, 3.7], [5.0, 5.2], [9.0, 9.5], [17.0, 18.0], [25.0, 28.0]]
    res_m2_goals = render_odds_grid("m2_g_pool", current_match, "体彩【总进球数】", opts_m2_goals, ["初盘", "临场"], init_m2_goals)

    st.markdown("---")
    st.markdown("### ♾️ 第二步：无限自定义动态比分台 (可自由增删比分对账单)")
    st.caption("提示：在表格底部点击 `+ Add row` 可自由无限增加任意一笔要审计的比分，系统将通过拓扑路由公式动态分拣归集。")

    # 初始化比分数据集电器
    if f"m2_editor_df_{current_match}_{m2_source_wl}" not in st.session_state:
        st.session_state[f"m2_editor_df_{current_match}_{m2_source_wl}"] = pd.DataFrame([
            {"比分项 (格式 X-Y)": "1-0", "实际终赔": 7.500},
            {"比分项 (格式 X-Y)": "2-0", "实际终赔": 11.000},
            {"比分项 (格式 X-Y)": "2-1", "实际终赔": 8.500},
            {"比分项 (格式 X-Y)": "1-2", "实际终赔": 13.000},
            {"比分项 (格式 X-Y)": "0-3", "实际终赔": 41.000}
        ])

    edited_scores_df = st.data_editor(
        st.session_state[f"m2_editor_df_{current_match}_{m2_source_wl}"], 
        num_rows="dynamic", 
        use_container_width=True,
        key=f"editor_widget_{current_match}_{m2_source_wl}"
    )

    st.write("")
    if st.button("🚀 启动比分与总球数多维拓扑对账引擎", type="primary", use_container_width=True):
        try:
            # Dixon-Coles 泊松物理基准生成
            xg_h_m2, xg_a_m2 = (mx_tg_val - mx_hcp_math_val)/2.0, (mx_tg_val + mx_hcp_math_val)/2.0
            _, _, _, _, _, P_matrix = dixon_coles_full_matrix(xg_h_m2, xg_a_m2, mx_rho_val)

            p_math_std_w = sum(P_matrix[h, a] for h in range(8) for a in range(8) if h > a)
            p_math_std_d = sum(P_matrix[h, a] for h in range(8) for a in range(8) if h == a)
            p_math_std_l = sum(P_matrix[h, a] for h in range(8) for a in range(8) if h < a)
            
            K_int = int(mx_k_val)
            p_math_let_w = sum(P_matrix[h, a] for h in range(8) for a in range(8) if h - a > -K_int)
            p_math_let_d = sum(P_matrix[h, a] for h in range(8) for a in range(8) if h - a == -K_int)
            p_math_let_l = sum(P_matrix[h, a] for h in range(8) for a in range(8) if h - a < -K_int)
            p_math_all = np.round([p_math_std_w, p_math_std_d, p_math_std_l, p_math_let_w, p_math_let_d, p_math_let_l], 4)

            # 解析大盘临场纯率 (处理未开售/幽灵重构情况)
            is_m2_std_closed = pd.isna(m1_std_w) or m1_std_w <= 0 or pd.isna(m1_std_d) or m1_std_d <= 0
            let_odds_arr = np.array([m1_let_w, m1_let_d, m1_let_l], dtype=float)
            p_let_d_m2 = calc_pure_prob_array(let_odds_arr)

            if is_m2_std_closed:
                if K_int < 0:
                    p_poisson_exact_1_home = sum(P_matrix[h, a] for h in range(8) for a in range(8) if h - a == 1)
                    phantom_w = p_let_d_m2[0] + p_let_d_m2[1] + p_poisson_exact_1_home
                    rem_d = max(1.0 - phantom_w, 0.0001)
                    ratio_d_to_a = p_math_all[1] / max((p_math_all[1] + p_math_all[2]), 0.0001)
                    p_std_d_m2 = np.round([phantom_w, rem_d * ratio_d_to_a, rem_d * (1.0 - ratio_d_to_a)], 4)
                else:
                    p_poisson_exact_1_away = sum(P_matrix[h, a] for h in range(8) for a in range(8) if a - h == 1)
                    phantom_l = p_let_d_m2[2] + p_let_d_m2[1] + p_poisson_exact_1_away
                    rem_d = max(1.0 - phantom_l, 0.0001)
                    ratio_h_to_d = p_math_all[0] / max((p_math_all[0] + p_math_all[1]), 0.0001)
                    p_std_d_m2 = np.round([rem_d * ratio_h_to_d, rem_d * (1.0 - ratio_h_to_d), phantom_l], 4)
                margin_m2 = 0.1150 # 锁盘时采用标准中枢水钱率代偿
            else:
                std_odds_arr = np.array([m1_std_w, m1_std_d, m1_std_l], dtype=float)
                p_std_d_m2 = calc_pure_prob_array(std_odds_arr)
                margin_m2 = np.nansum(1.0 / std_odds_arr) - 1.0

            # 进球数大盘数据解析
            goals_odds_d = safe_extract_array(res_m2_goals['临场'])
            p_goals_d = calc_pure_prob_array(goals_odds_d)

            # 2. 无限伸缩行矩阵分拣循环 (Topology Router Loops)
            score_rows_out = []
            goal_bucket_sums = np.zeros(8)
            macro_biao_sums = {"标胜": 0.0, "标平": 0.0, "标负": 0.0}
            macro_rang_sums = {"让胜": 0.0, "让平": 0.0, "让负": 0.0}

            for index, row in edited_scores_df.iterrows():
                score_str = str(row["比分项 (格式 X-Y)"]).strip()
                odds_val = float(row["实际终赔"])
                if "-" not in score_str or odds_val <= 0: continue

                try:
                    parts = score_str.split("-")
                    X, Y = int(parts[0]), int(parts[1])
                except: continue

                # 💡 核心三行通用拓扑路由计算组
                G = X - Y
                G_hcp = G + K_int
                biao_key = "标胜" if G > 0 else ("标平" if G == 0 else "标负")
                rang_key = "让胜" if G_hcp > 0 else ("让平" if G_hcp == 0 else "让负")
                goal_num = min(X + Y, 7)

                # 比分单点纯概率提纯 (基于大盘抽水因子)
                p_score_pure = (1.0 / odds_val) / (1.0 + margin_m2)
                p_score_pure = round(p_score_pure, 4)

                # 归集进球数与大盘父集抽屉
                goal_bucket_sums[goal_num] += p_score_pure
                macro_biao_sums[biao_key] += p_score_pure
                macro_rang_sums[rang_key] += p_score_pure

                # 获取泊松理论比分纯率用于靶向测谎
                p_math_score = P_matrix[min(X, 7), min(Y, 7)] if X<8 and Y<8 else 0.0001
                score_res = round(p_score_pure - p_math_score, 4)
                score_rmv = round(score_res / max(p_score_pure, 0.0001), 4)

                # 靶向白话单定性
                if score_res > 0.025 and score_rmv > 0.05:
                    sc_verdict = "🚨 畸高诱捕墙"
                    sc_desc = "该比分理论发生概率低，但体彩在微观端给出了不合理的反向超额赔付，纯属诱骗买入的虚胖毒饵。"
                elif score_res < -0.025 and score_rmv < -0.05:
                    sc_verdict = "🛡️ 核心防波堤"
                    sc_desc = "发生概率极高，精算师采取了肉身割肉式的暴力扣赔降水阻击，属于机构誓死防守的交割阵眼！"
                else:
                    sc_verdict = "⚪ 常规对冲中枢"
                    sc_desc = "赔付率处于完美对冲中枢区间，庄家交由自然实力对冲。"

                score_rows_out.append({
                    "核心比分": score_str,
                    "体彩终赔": f"{odds_val:.2f}",
                    "比分纯率": f"{p_score_pure:.4f}",
                    "标盘父集": biao_key,
                    "让球父集": rang_key,
                    "归属球数": f"{goal_num}球",
                    "子盘口残差": f"{score_res:+.4f}",
                    "期权偏度": sc_verdict,
                    "微观审计结论": sc_desc
                })

            st.markdown("### 📊 看板一：微观行权比分自定义测谎表")
            st.dataframe(pd.DataFrame(score_rows_out), hide_index=True, use_container_width=True)

            # 3. 跨维度微积分总池对账 (Goals Mass Check)
            st.markdown("---")
            st.markdown("### 🧮 看板二：【总球数期权池】与【细分行权价积分】总对账单")
            
            goal_checks = []
            for idx, opt_g in enumerate(opts_m2_goals):
                p_pool = p_goals_d[idx]
                p_integral = round(goal_bucket_sums[idx], 4)
                g_residual = round(p_pool - p_integral, 4)
                g_rmv = round(g_residual / max(p_pool, 0.0001), 4)

                if g_residual > 0.0300:
                    g_verdict = "🚨 总池空壳抽水 (割肉陷阱)"
                    g_desc = "总进球数玩法的概率被庄家单边做高（扣低赔率），但底层所有比分却拒不收容此流量！庄家在单向宰杀串关热钱。"
                elif g_residual < -0.0300:
                    g_verdict = "🎁 细分大点漏网爆破"
                    g_desc = "比分积分远远挤爆了球数总池！散户未察觉的高赔细分比分里，庄家在大面积偷偷筑墙泄洪！"
                else:
                    g_verdict = "⚖️ 微积分守恒完美"
                    g_desc = "总玩法池与细分期权交割单完美咬合，无明显结构性错配风险。"

                goal_checks.append({
                    "球数玩法": opt_g,
                    "总池纯率": f"{p_pool:.4f}",
                    "比分积分总和": f"{p_integral:.4f}",
                    "球数积分残差": f"{g_residual:+.4f}",
                    "离散偏度(RMV)": f"{g_rmv*100:+.2f}%",
                    "总池对账裁决": g_verdict,
                    "大白话透视": g_desc
                })
            st.dataframe(pd.DataFrame(goal_checks), hide_index=True, use_container_width=True)

            # 4. 深度宏微观宿敌交叉扫描雷达 (Sub-market Volatility Skew)
            st.markdown("---")
            st.markdown("### 🛰️ 看板三：高级宏微观包含映射雷达")
            
            c1_mx, c2_mx = st.columns(2)
            with c1_mx:
                st.markdown("##### 🏟️ 标盘胜平负大盘积分复核")
                st.write(f"• 临场标盘纯率：[胜 {p_std_d_m2[0]:.4f} | 平 {p_std_d_m2[1]:.4f} | 负 {p_std_d_m2[2]:.4f}]")
                st.write(f"• 录入比分积分：[胜 {macro_biao_sums['标胜']:.4f} | 平 {macro_biao_sums['标平']:.4f} | 负 {macro_biao_sums['标负']:.4f}]")
                # 计算比分承载率
                re_w = macro_biao_sums['标胜']/max(p_std_d_m2[0], 0.0001)
                if re_w < 0.65 and p_std_d_m2[0] > 0.40:
                    st.error("🚨 **【皮热骨冷·空壳死局】** 标盘主胜看起来极大，但下方录入的所有主胜核心比分根本没有赔付流量支撑！坚决排除主胜大热！")
                else:
                    st.success("✅ 大盘指数量价契合度符合正常离散分布。")

            with c2_mx:
                st.markdown("##### 🥅 让球盘受让大一统字典复核")
                st.write(f"• 临场让球纯率：[让胜 {p_let_d_m2[0]:.4f} | 让平 {p_let_d_m2[1]:.4f} | 让负 {p_let_d_m2[2]:.4f}]")
                st.write(f"• 让球映射积分：[让胜 {macro_rang_sums['让胜']:.4f} | 让平 {macro_rang_sums['让平']:.4f} | 让负 {macro_rang_sums['让负']:.4f}]")
                
                # 针对用户疑问：解析3球玩法中的让负并联拆解
                if K_int == -1 and goal_bucket_sums[3] > 0:
                    p_1_2_ratio = sum(float(x["比分纯率"]) for x in score_rows_out if x["核心比分"]=="1-2")
                    p_0_3_ratio = sum(float(x["比分纯率"]) for x in score_rows_out if x["核心比分"]=="0-3")
                    if p_0_3_ratio > 0:
                        skew_ratio = p_1_2_ratio / max(p_0_3_ratio, 0.0001)
                        st.warning(f"🎯 **【3球让负冷门解耦成功】** 在主让-1下，1-2与0-3均属于让负。当前体彩微观实际赔付比率 1-2 vs 0-3 为 **{skew_ratio:.2f}倍**！若该倍率远低于理论8.0倍，说明精算师在用0-3冷门过度吸筹，诱骗散户去踩1-2的死坑！")

        except Exception as e:
            st.error("🚨 拓扑微积分引擎运行故障，请检查数据完整度。")
            st.code(traceback.format_exc())


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
        cols = st.columns(2)
        with cols[0]: m5_ou_val = m5_safe_input("大小球基准盘口 (用于跨盘口锁定)", f"m5_ou_{current_match}", 2.50, format="%.2f", step=0.25)
        with cols[1]: m5_hcp_val = m5_safe_input("亚指让球基准 (用于马尔可夫底座)", f"m5_hcp_{current_match}", -0.50, format="%.2f", step=0.25)
        
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
