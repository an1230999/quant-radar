import streamlit as st
import pandas as pd
import numpy as np
import math

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
    .stDataFrame { font-size: 0.9rem; }
    </style>
""", unsafe_allow_html=True)

# ================= 2. 🔐 核心防盗门：访问密码 =================
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        st.markdown("<h2 style='text-align: center; margin-top: 100px;'>🔒 FX2 全维量化终端 - 访问受限</h2>", unsafe_allow_html=True)
        pwd = st.text_input("请输入访问密钥：", type="password", key="pwd_input")
        col1, col2, col3 = st.columns([1,1,1])
        with col2:
            if st.button("🚀 解锁终端", use_container_width=True):
                if pwd == "FX888":  # <--- 在此修改密码
                    st.session_state["password_correct"] = True
                    st.rerun()
                else:
                    st.error("❌ 密钥验证失败，请重新输入。")
        return False
    return True

if not check_password():
    st.stop()

st.title("🏦 FX2 全维量化对冲终端 (异构交叉对冲版)")

# ================= 3. 核心数学引擎 =================
def calc_pure_prob_array(arr):
    arr = np.array(arr, dtype=float)
    if np.isnan(arr).any() or (arr == 0).any():
        return np.full(len(arr), np.nan)
    raw = 1.0 / arr
    return np.round(raw / np.nansum(raw), 4)

def dixon_coles_full_matrix(lambda_, mu_, rho_):
    def poisson_pmf_array(lam, max_k):
        pmf = np.zeros(max_k + 1)
        if lam <= 0: return pmf
        for k in range(max_k + 1):
            pmf[k] = math.exp(-lam) * (lam**k) / math.factorial(k)
        return pmf
    max_calc = 15 
    px = poisson_pmf_array(lambda_, max_calc)
    py = poisson_pmf_array(mu_, max_calc)
    P = np.outer(px, py)
    P[0, 0] *= (1 - lambda_ * mu_ * rho_)
    P[1, 0] *= (1 + lambda_ * rho_)
    P[0, 1] *= (1 + mu_ * rho_)
    P[1, 1] *= (1 - rho_)
    P = np.clip(P, 0, 1)
    P = P / P.sum() 
    
    P_col = np.zeros((8, 8))
    P_col[:7, :7] = P[:7, :7]
    P_col[7, :7] = np.sum(P[7:, :7], axis=0) 
    P_col[:7, 7] = np.sum(P[:7, 7:], axis=1) 
    P_col[7, 7] = np.sum(P[7:, 7:])          
    
    P_col_rounded = np.round(P_col, 4)
    p_hw2 = np.sum(np.tril(P_col_rounded, -2))
    p_hw1 = np.sum(np.diag(P_col_rounded, -1))
    p_draw = np.sum(np.diag(P_col_rounded, 0))
    p_au = np.sum(np.triu(P_col_rounded, 0))
    
    cols = [f"客进{i}" for i in range(7)] + ["客进7+"]
    idx = [f"主进{i}" for i in range(7)] + ["主进7+"]
    return pd.DataFrame(P_col_rounded, columns=cols, index=idx), p_hw2, p_hw1, p_draw, p_au, P_col_rounded

# ================= 4. 🌟 终极影子保险箱 =================
def safe_number_input(label, shadow_key, default_val, format="%.4f", step=0.0010):
    widget_key = "wid_" + shadow_key
    if shadow_key not in st.session_state: st.session_state[shadow_key] = default_val
    if widget_key not in st.session_state: st.session_state[widget_key] = st.session_state[shadow_key]
    val = st.number_input(label, format=format, step=step, key=widget_key)
    st.session_state[shadow_key] = val
    return val

def safe_data_editor(shadow_key, default_df):
    edit_state_key = shadow_key + "_edits"
    widget_key = "wid_" + shadow_key
    if edit_state_key in st.session_state and widget_key not in st.session_state:
        st.session_state[widget_key] = st.session_state[edit_state_key]
    edited_df = st.data_editor(default_df, hide_index=True, num_rows="fixed", use_container_width=True, key=widget_key)
    st.session_state[edit_state_key] = st.session_state[widget_key]
    return edited_df

# ================= 5. 不可变原初数据表底座 =================
init_df_1 = pd.DataFrame([
    ["标盘-胜", 2.45, 2.32], ["标盘-平", 3.20, 3.20], ["标盘-负", 2.45, 2.60],
    ["让盘-胜", 5.50, 5.30], ["让盘-平", 4.10, 4.00], ["让盘-负", 1.42, 1.45]
], columns=["玩法选项", "初盘", "临场"])

init_df_2 = pd.DataFrame({
    "玩法选项": ["0球", "1球", "2球", "3球", "4球", "5球", "6球", "7+球", "大球", "小球"],
    "初盘(C)": [15.0, 5.5, 3.6, 3.45, 4.9, 8.25, 15.0, 22.0, 0.65, 1.75],
    "T-60(J)": [None]*10, "临场(D)": [15.5, 5.9, 3.8, 3.10, 4.7, 8.50, 16.0, 24.0, 0.50, 1.15]
})

init_df_3 = pd.DataFrame({
    "TC盘口": ["标准盘", "让球盘"], "胜": [2.32, 5.30], "平": [3.20, 4.00],
    "负": [2.60, 1.45], "国彩让球数": [0, -1]
})

matches_list = ["⚽ 比赛 1", "⚽ 比赛 2", "⚽ 比赛 3", "⚽ 比赛 4", "⚽ 比赛 5"]

if "FX2_V_FINAL_12" not in st.session_state:
    st.session_state.clear()
    for m in matches_list:
        st.session_state[f"m4_cap_{m}"] = 1000.0
        st.session_state[f"m4_oddA_{m}"] = 2.00
        st.session_state[f"m4_oddB_{m}"] = 3.00
    st.session_state["FX2_V_FINAL_12"] = True

def get_thresholds_defaults(wl):
    if "深水区" in wl: return [0.0100, 0.0070, 0.0040, 0.0020, 999.0, 0.0020]
    elif "中水区" in wl: return [0.0200, 0.0130, 0.0080, 0.0050, 999.0, 0.0050]
    else: return [0.0300, 0.0200, 0.0120, 0.0080, 999.0, 0.0080]

def render_thresholds(mod, match, wl):
    defs = get_thresholds_defaults(wl)
    with st.expander(f"⚙️ {wl} 专属风控阈值微调 (点击展开)"):
        cols = st.columns(6)
        with cols[0]: z2 = safe_number_input("Z2 (红线)", f"{mod}_z2_{match}_{wl}", defs[0])
        with cols[1]: z3 = safe_number_input("Z3 (显著)", f"{mod}_z3_{match}_{wl}", defs[1])
        with cols[2]: z4 = safe_number_input("Z4 (警戒)", f"{mod}_z4_{match}_{wl}", defs[2])
        with cols[3]: z5 = safe_number_input("Z5 (温和)", f"{mod}_z5_{match}_{wl}", defs[3])
        with cols[4]: z6 = safe_number_input("Z6 (高赔)", f"{mod}_z6_{match}_{wl}", defs[4], format="%.1f", step=1.0)
        with cols[5]: v  = safe_number_input("T-60加速", f"{mod}_v_{match}_{wl}", defs[5])
    return z2, z3, z4, z5, z6, v

# ================= 6. 赛事导航与侧边栏 =================
current_match = st.radio("🏆 切换独立比赛流 (每场赛事数据独立封存，永不丢失)：", matches_list, horizontal=True)

st.sidebar.title("🧭 矩阵控制台")
active_module = st.sidebar.radio("=== 核心风控体系 ===", [
    "⚔️ 模块一：欧亚大盘体系",
    "⚽ 模块二：进球数多维风控",
    "🎫 模块三：高阶工具 (DC矩阵)",
    "🧬 模块四：异构交叉与零和对冲"
])

# ================= 7. 模块一：欧亚大盘 =================
if active_module == "⚔️ 模块一：欧亚大盘体系":
    st.header(f"⚔️ {current_match} - 欧亚大盘体系")
    tab1, tab2, tab3 = st.tabs(["🟢 浅水区", "🟡 中水区", "🔴 深水区"])
    
    def render_main_handicap_ui(wl, match_id):
        z2, z3, z4, z5, z6, _ = render_thresholds("m1", match_id, wl)
        st.markdown(f"### 📥 {wl} 数据录入区")
        col_ext1, _ = st.columns(2)
        with col_ext1:
            h_val = safe_number_input(f"主队亚指让球数", f"m1_hcp_{match_id}_{wl}", -1.0, format="%.2f", step=0.25)
            
        df_cur = safe_data_editor(f"m1_df_{match_id}_{wl}", init_df_1)
        calc_key = f"m1_calc_{match_id}_{wl}"
        if calc_key not in st.session_state: st.session_state[calc_key] = False
        
        if st.button(f"🚀 执行 {wl} 精算", type="primary", key=f"btn_{calc_key}"):
            st.session_state[calc_key] = True
            
        if st.session_state[calc_key]:
            opts = df_cur['玩法选项'].values
            c_odds, d_odds = pd.to_numeric(df_cur['初盘'], errors='coerce').values, pd.to_numeric(df_cur['临场'], errors='coerce').values
            biao_c, rang_c = calc_pure_prob_array(c_odds[0:3]), calc_pure_prob_array(c_odds[3:6])
            biao_d, rang_d = calc_pure_prob_array(d_odds[0:3]), calc_pure_prob_array(d_odds[3:6])
            prob_c, prob_d = np.concatenate([biao_c, rang_c]), np.concatenate([biao_d, rang_d])
            delta = np.round(prob_d - prob_c, 4)
            
            ret_c = round(1.0 / np.nansum(1.0 / c_odds[0:3]), 4) if not np.isnan(c_odds[0:3]).any() else 1.0
            ret_d = round(1.0 / np.nansum(1.0 / d_odds[0:3]), 4) if not np.isnan(d_odds[0:3]).any() else 1.0
            dev = np.round(d_odds - (c_odds * (ret_d / ret_c)), 4)
            
            heat = np.where(delta >= z2, "🌋 极限防范", np.where(delta >= z3, "🔥 显著设防", np.where(delta >= z4, "📈 温和流入",
                   np.where(delta <= -z2, "🧊 极限抛弃", np.where(delta <= -z3, "📉 显著看衰", np.where(delta <= -z4, "↘️ 温和流出", "⚪ 随机噪音"))))))
            filter_q = np.where(dev < -0.02, "🩸 暴击防范(狠)", np.where(dev < 0, "📉 真实降水", np.where((dev > 0) & (d_odds < c_odds), "🚨 虚假降水", np.where(dev > 0, "📈 真实升水", "⚪ 平稳"))))
            
            s_theo, u_theo = np.full(6, np.nan), np.full(6, np.nan)
            t_open, v_open, w_traj, aa_hedge = ["⚪ 无对照"]*6, ["⚪ 无对照"]*6, ["⚪ 无对照"]*6, ["⚪ 动量未达标"]*6
            if h_val != 0:
                if h_val < 0:
                    s_theo[0], u_theo[0] = prob_c[3] + prob_c[4], prob_d[3] + prob_d[4]
                    s_theo[1], u_theo[1] = prob_c[5] - prob_c[2], prob_d[5] - prob_d[2]
                    s_theo[2], u_theo[2] = prob_c[5] - prob_c[1], prob_d[5] - prob_d[1]
                    s_theo[3], u_theo[3] = prob_c[0] - prob_c[4], prob_d[0] - prob_d[4]
                    s_theo[4], u_theo[4] = prob_c[0] - prob_c[3], prob_d[0] - prob_d[3]
                    s_theo[5], u_theo[5] = prob_c[1] + prob_c[2], prob_d[1] + prob_d[2]
                else:
                    s_theo[0], u_theo[0] = prob_c[3] - prob_c[1], prob_d[3] - prob_d[1]
                    s_theo[1], u_theo[1] = prob_c[3] - prob_c[0], prob_d[3] - prob_d[0]
                    s_theo[2], u_theo[2] = prob_c[4] + prob_c[5], prob_d[4] + prob_d[5]
                    s_theo[3], u_theo[3] = prob_c[0] + prob_c[1], prob_d[0] + prob_d[1]
                    s_theo[4], u_theo[4] = prob_c[2] - prob_c[5], prob_d[2] - prob_d[5]
                    s_theo[5], u_theo[5] = prob_c[2] - prob_c[4], prob_d[2] - prob_d[4]
                s_theo, u_theo = np.round(s_theo, 4), np.round(u_theo, 4)
                for i in range(6):
                    c_prob, s_t, d_prob, u_t = prob_c[i], s_theo[i], prob_d[i], u_theo[i]
                    if not np.isnan(s_t) and not np.isnan(u_t):
                        diff_c, diff_d = c_prob - s_t, d_prob - u_t
                        t_open[i] = "🔻 极限低开" if diff_c >= z2 else "📉 显著低开" if diff_c >= z3 else "🔺 极限高开" if diff_c <= -z2 else "📈 显著高开" if diff_c <= -z3 else "⚪ 体系平衡"
                        v_open[i] = "🔻 极限低开" if diff_d >= z2 else "📉 显著低开" if diff_d >= z3 else "🔺 极限高开" if diff_d <= -z2 else "📈 显著高开" if diff_d <= -z3 else "⚪ 体系平衡"
                        traj = diff_d - diff_c
                        w_traj[i] = "🚨 剧烈砸盘" if traj >= 0.02 else "📉 步步紧逼" if traj >= 0.01 else "🚨 疯狂拉高" if traj <= -0.02 else "📈 门槛放宽" if traj <= -0.01 else "⚪ 伪装平稳"
                        struct = round(diff_d, 4)
                        if delta[i] >= z3: aa_hedge[i] = "✅ 黄金共振" if struct >= z4 else "🚨 致命背离" if struct <= -z4 else "🟡 结构中立"
                        elif delta[i] <= -z3: aa_hedge[i] = "🎁 暗度陈仓" if struct >= z4 else "🧊 真实抛弃" if struct <= -z4 else "⚪ 结构中立"
                        else: aa_hedge[i] = "🌋 静态死防" if struct >= z3 else "🕸️ 静态诱网" if struct <= -z3 else "⚪ 动量未达标"

            out_main = pd.DataFrame({"选项": opts, "初纯净概率": prob_c, "临纯净概率": prob_d, "动量(Delta)": delta, "热度测算": heat, "净抽水偏离": dev, "返还率滤镜": filter_q, "底座概率": s_theo, "初盘定性": t_open, "轨迹研判": w_traj, "时空双杀": aa_hedge})
            st.markdown("### 📊 欧亚基础底座透视")
            st.dataframe(out_main.fillna(""), hide_index=True, use_container_width=True)

            ranks = pd.Series(delta).rank(method='min', ascending=False).values 
            refiner_text = []
            for i in range(6):
                r, d, odd = ranks[i], delta[i], c_odds[i]
                if r == 1: txt = "🌋 史诗级重防" if d >= z2*1.5 else "🌋 绝对防范极值" if d >= z2 else "🔥 首席主防" if d >= z3 else "🟡 相对领跑" if d >= z4 else "📈 微弱榜首" if d >= z5 else "⚪ 虚空榜首"
                elif d > 0: txt = "💣 史诗级暗盘" if d >= z2*1.5 else "💣 隐蔽杀机" if d >= z2 else "🛡️ 独立重防" if d >= z3 else "📈 顺流吸筹" if d >= z4 else "↗️ 温和介入" if d >= z5 else "⚪ 边缘流入"
                elif odd >= z6: txt = "🎭 终极恐吓" if d <= -z2*1.5 else "🚧 高赔壁垒" if d <= -z2 else "📉 顺势驱赶" if d <= -z3 else "↘️ 显著退热" if d <= -z4 else "⏬ 微幅流失" if d <= -z5 else "⚪ 自然震荡"
                else: txt = "🩸 绝望深渊" if d <= -z2*1.5 else "🧊 极限绞杀" if d <= -z2 else "📉 坚决抛弃" if d <= -z3 else "↘️ 显著退热" if d <= -z4 else "⏬ 微幅流失" if d <= -z5 else "⚪ 自然震荡"
                refiner_text.append(txt)
                
            out_refiner = pd.DataFrame({"提纯选项": opts, "偏移量": delta, "热度排名": ranks, "单项研判": refiner_text})
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

# ================= 8. 模块二：进球数风控 =================
elif active_module == "⚽ 模块二：进球数多维风控":
    st.header(f"⚽ {current_match} - 进球数全维透视")
    tab1, tab2, tab3 = st.tabs(["🟢 浅水区", "🟡 中水区", "🔴 深水区"])

    def render_goals_ui(wl, match_id):
        z2, z3, z4, z5, z6, v_limit = render_thresholds("m2", match_id, wl)
        st.markdown(f"### 📥 {wl} 数据录入区")
        col_ext1, col_ext2 = st.columns(2)
        with col_ext1: safe_number_input(f"主队亚指让球", f"m2_hcp_{match_id}_{wl}", -0.75, format="%.2f", step=0.25)
        with col_ext2: safe_number_input(f"大小球盘口", f"m2_ou_{match_id}_{wl}", 2.50, format="%.2f", step=0.25)
            
        df_cur = safe_data_editor(f"m2_df_{match_id}_{wl}", init_df_2)
        calc_key = f"m2_calc_{match_id}_{wl}"
        if calc_key not in st.session_state: st.session_state[calc_key] = False
        
        if st.button(f"🚀 执行 {wl} 扫描", type="primary", key=f"btn_{calc_key}"):
            st.session_state[calc_key] = True
            
        if st.session_state[calc_key]:
            opts = df_cur['玩法选项'].values
            c_odds, j_odds, d_odds = pd.to_numeric(df_cur['初盘(C)'], errors='coerce').values, pd.to_numeric(df_cur['T-60(J)'], errors='coerce').values, pd.to_numeric(df_cur['临场(D)'], errors='coerce').values
            c_7, c_ou = calc_pure_prob_array(c_odds[0:8]), calc_pure_prob_array(c_odds[8:10])
            j_7, j_ou = calc_pure_prob_array(j_odds[0:8]), calc_pure_prob_array(j_odds[8:10])
            d_7, d_ou = calc_pure_prob_array(d_odds[0:8]), calc_pure_prob_array(d_odds[8:10])
            prob_c, prob_j, prob_d = np.concatenate([c_7, c_ou]), np.concatenate([j_7, j_ou]), np.concatenate([d_7, d_ou])
            delta, ev, v_delta = np.round(prob_d - prob_c, 4), np.round(prob_c * d_odds - 1, 4), np.round(prob_d - prob_j, 4)
            
            r_g = np.where(delta >= z2*2, "🌋 极度过热", np.where(delta >= z2, "🚨 史诗级重防", np.where(delta >= z3, "🔥 首席主防", np.where(delta >= z4, "🟡 显著流入", np.where(delta >= z5, "↗️ 温和介入", np.where(delta <= -z2*2, "🕳️ 极度冰封", np.where(delta <= -z2, "🧊 极限绞杀", np.where(delta <= -z3, "📉 坚决抛弃", np.where(delta <= -z4, "↘️ 显著流失", np.where(delta <= -z5, "⏬ 微幅流失", "⚪ 边缘震荡"))))))))))
            r_h = np.where(ev >= -0.10, "🌟 绝对正价值", np.where(ev >= -0.15, "🟢 极度高潜", np.where(ev >= -0.18, "🟡 合理磨损", np.where(ev >= -0.22, "📉 劣势赔付", np.where(ev >= -0.25, "🚨 杀猪盘预警", "🩸 抽水深渊")))))
            r_i = np.where((delta >= z2*1.5) & (ev <= -0.25), "🩸 嗜血诱导", np.where((delta >= z3) & (delta < z2*1.5) & (ev <= -0.08) & (ev >= -0.25), "🎯 精确制导", np.where((delta <= -z3) & (ev > 0), "☠️ 淬毒诱饵", "⚪ ")))
            r_l = np.where(np.isnan(v_delta), "➖ ", np.where(v_delta >= v_limit, "⚡ 绝杀爆发", np.where(v_delta <= -v_limit, "🩸 极速撤离", "⚪ 匀速平稳")))
            
            out_df2 = pd.DataFrame({"选项": opts, "动量(Delta)": delta, "期望值(EV)": ev, "加速度(V)": v_delta, "动量雷达": r_g, "价值仪": r_h, "自动防伪": r_i, "狙击雷达": r_l})
            st.markdown("### 📊 终极进球数扫描雷达")
            st.dataframe(out_df2.fillna(""), hide_index=True, use_container_width=True)
            
            if not np.isnan(c_7).all():
                even_prob, odd_prob = round(float(np.nansum(c_7[[0,2,4,6]])), 4), round(float(np.nansum(c_7[[1,3,5,7]])), 4)
                h_val2 = st.session_state[f"m2_hcp_{match_id}_{wl}"]
                ou_val = st.session_state[f"m2_ou_{match_id}_{wl}"]
                if abs(h_val2) <= 0.25: core_g = "0球, 1球, 2球"
                elif abs(h_val2) <= 0.75: core_g = "2球, 3球"
                elif abs(h_val2) <= 1.25: core_g = "3球, 4球"
                else: core_g = "4球, 5+球"
                min_idx = np.nanargmin(c_odds[0:8])
                match_s = "✅ 亚欧完美共振" if str(opts[min_idx][0]) in core_g else "🚨 严重逻辑背离"
                
                c1, c2, c3, c4 = st.columns(4)
                c1.info(f"⚖️ 奇偶结构 -> 偶: {even_prob} | 奇: {odd_prob}")
                c2.info(f"🎯 亚指核心区 -> {core_g}")
                c3.info(f"🗺️ 交叉共振 -> {match_s}")
                c4.info(f"⚽ 大小球盘口 -> {ou_val}")

    with tab1: render_goals_ui("浅水区", current_match)
    with tab2: render_goals_ui("中水区", current_match)
    with tab3: render_goals_ui("深水区", current_match)

# ================= 9. 模块三：体彩高阶工具 =================
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
            st.markdown("### 📥 录入官方盘口与让球数")
            df_cur = safe_data_editor(f"m3_df_{current_match}", init_df_3)
            calc_key = f"m3_calc_{current_match}"
            if calc_key not in st.session_state: st.session_state[calc_key] = False
            if st.button("🚀 启动底座联动扫描", key=f"btn_{calc_key}"): st.session_state[calc_key] = True
                
            if st.session_state[calc_key]:
                std_odds, let_odds = pd.to_numeric(df_cur.iloc[0, 1:4], errors='coerce').values, pd.to_numeric(df_cur.iloc[1, 1:4], errors='coerce').values
                try: tc_let = int(float(df_cur.iloc[1, 4]))
                except: tc_let = -1
                p_std_w = sum(P_col_rounded[i, j] for i in range(8) for j in range(8) if i - j > 0)
                p_std_d = sum(P_col_rounded[i, j] for i in range(8) for j in range(8) if i - j == 0)
                p_std_l = sum(P_col_rounded[i, j] for i in range(8) for j in range(8) if i - j < 0)
                p_let_w = sum(P_col_rounded[i, j] for i in range(8) for j in range(8) if i - j > -tc_let)
                p_let_d = sum(P_col_rounded[i, j] for i in range(8) for j in range(8) if i - j == -tc_let)
                p_let_l = sum(P_col_rounded[i, j] for i in range(8) for j in range(8) if i - j < -tc_let)
                
                intl_prob, tc_odds = np.array([p_std_w, p_std_d, p_std_l, p_let_w, p_let_d, p_let_l]), np.concatenate([std_odds, let_odds])
                ev_vals = np.round(tc_odds * intl_prob - 1, 4)
                judge = np.where(ev_vals > 0, "🌟 绝对正价值", np.where(ev_vals >= -0.03, "🟢 极度高潜", np.where(ev_vals >= -0.08, "🟡 合理磨损", np.where(ev_vals >= -0.12, "📉 劣势赔付", np.where(ev_vals >= -0.16, "🚨 杀猪盘预警", "🩸 抽水深渊")))))
                
                out_df3 = pd.DataFrame({"投注项": ["标准胜", "标准平", "标准负", "让球胜", "让球平", "让球负"], "推演概率": np.round(intl_prob, 4), "数学EV": ev_vals, "雷达定性": judge})
                st.dataframe(out_df3.fillna(""), hide_index=True, use_container_width=True)

# ================= 10. 🌟全新：模块四：异构交叉与零和对冲 =================
elif active_module == "🧬 模块四：异构交叉与零和对冲":
    st.header(f"🧬 {current_match} - 终极异构验证与对冲引擎")
    
    tab_a, tab_b, tab_c = st.tabs(["🔍 亚盘 vs xG 撕裂检测", "🏦 机构暗水剥离 (凯利敞口)", "⚖️ 荷兰式绝对零和对冲器"])
    
    with tab_a:
        st.markdown("### 🔍 异构交叉验证：盘口物理边界 vs 泊松数学期望")
        st.info("原理：自动提取【模块一：浅水区】的让球盘，与【模块三】算出的泊松预期净胜球进行撕裂度对比。如果让球盘远超数学期望，即为极致诱导或深水设伏！")
        
        # 尝试跨模块提取数据
        try:
            ah_val = st.session_state[f"m1_hcp_{current_match}_浅水区"]
            tg_val = st.session_state.get(f"m3_tg_{current_match}", 2.75)
            hcp_val = st.session_state.get(f"m3_hcp_{current_match}", 0.0)
            xg_h, xg_a = (tg_val - hcp_val) / 2, (tg_val + hcp_val) / 2
            xg_diff = round(xg_h - xg_a, 4)
            
            c1, c2, c3 = st.columns(3)
            c1.metric("机构物理开盘 (主队让球)", f"{ah_val}")
            c2.metric("泊松数学推演 (主队净胜球)", f"{xg_diff}")
            
            mismatch = round(xg_diff - (-ah_val), 4) # ah_val是负数代表让球
            c3.metric("🌪️ 时空撕裂度 (Mismatch)", f"{mismatch}")
            
            if mismatch >= 0.4:
                st.success("✅ **主队深度价值 (Deep Value)：** 机构开出的盘口极其保守，但数学期望显示主队碾压，主队极大概率穿盘！")
            elif mismatch <= -0.4:
                st.error("🚨 **极致诱杀陷阱 (Bull Trap)：** 机构强行开出深盘造热主队，但数学期望极低，坚决去下盘/客队不败！")
            else:
                st.warning("⚖️ **盘理平衡：** 机构开盘与数学期望严丝合缝，没有明显的结构性漏洞，需依靠模块一的资金动量决断。")
        except KeyError:
            st.error("⚠️ 请先在【模块一：浅水区】和【模块三】中输入盘口数据。")

    with tab_b:
        st.markdown("### 🏦 机构真实赔付敞口与暗水探测")
        st.info("原理：通过临场赔率反算机构的资金盈亏平衡点。如果某一项赔率极高，但它的【赔付敞口指数】却异常大，说明机构在悄悄吸收冷门重注！")
        
        try:
            df_m1 = st.session_state[f"m1_df_{current_match}_浅水区"]
            d_odds = pd.to_numeric(df_m1['临场'][0:3], errors='coerce').values
            if np.isnan(d_odds).any(): raise ValueError
            
            implied = 1.0 / d_odds
            margin = np.sum(implied) - 1
            fair_prob = implied / (1 + margin)
            liability = fair_prob * d_odds # 简化的敞口指数
            
            df_kelly = pd.DataFrame({
                "赛果": ["主胜", "平局", "客胜"],
                "临场赔率": d_odds,
                "被动抽水率": [f"{margin*100:.2f}%"]*3,
                "真实概率 (剥离抽水)": np.round(fair_prob, 4),
                "⚠️ 机构赔付敞口指数": np.round(liability, 4)
            })
            
            st.dataframe(df_kelly, hide_index=True, use_container_width=True)
            max_idx = np.argmax(liability)
            st.error(f"💣 **暗水警报：** 当前机构对 **【{df_kelly['赛果'][max_idx]}】** 的赔付敞口最为敏感，存在防范动作！")
        except:
            st.warning("⚠️ 请先在【模块一：浅水区】输入完整的标盘临场赔率。")

    with tab_c:
        st.markdown("### ⚖️ 荷兰式绝对零和对冲器 (Dutching Calculator)")
        st.info("实战用途：当你通过前面三个模块确定了两个可能的赛果（例如防主胜和防平），在此输入总资金，系统会精准计算筹码分配，确保无论打出哪个结果，你的利润完全一致！")
        
        cap_key = f"m4_cap_{current_match}"
        oddA_key = f"m4_oddA_{current_match}"
        oddB_key = f"m4_oddB_{current_match}"
        
        c1, c2, c3 = st.columns(3)
        with c1: total_capital = safe_number_input("💰 计划投入总资金", cap_key, 1000.0, format="%.0f", step=100.0)
        with c2: odd_a = safe_number_input("选项 A 赔率 (如主胜)", oddA_key, 2.00, format="%.2f", step=0.01)
        with c3: odd_b = safe_number_input("选项 B 赔率 (如平局)", oddB_key, 3.00, format="%.2f", step=0.01)
        
        if odd_a > 1 and odd_b > 1:
            implied_a, implied_b = 1/odd_a, 1/odd_b
            total_implied = implied_a + implied_b
            
            stake_a = (implied_a / total_implied) * total_capital
            stake_b = (implied_b / total_implied) * total_capital
            
            return_a = stake_a * odd_a
            return_b = stake_b * odd_b
            profit = return_a - total_capital
            
            st.markdown("#### 🎯 终极执行指令：")
            col_r1, col_r2, col_r3 = st.columns(3)
            col_r1.success(f"**买入 选项A：** `{stake_a:.2f}` 元")
            col_r2.success(f"**买入 选项B：** `{stake_b:.2f}` 元")
            
            if profit > 0:
                col_r3.info(f"**绝对保底净利润：** `+{profit:.2f}` 元")
            else:
                col_r3.error(f"**不可避免损耗：** `{profit:.2f}` 元 (无法形成无风险套利)")
        else:
            st.warning("请确保赔率大于 1.00")
