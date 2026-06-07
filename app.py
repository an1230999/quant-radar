import streamlit as st
import pandas as pd
import numpy as np
import math
import requests
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
    .ai-box { padding: 20px; border-radius: 10px; background-color: #1E1E1E; border-left: 5px solid #E50914; margin-bottom: 20px;}
    .ai-title { font-size: 1.2rem; font-weight: bold; color: #FFFFFF; margin-bottom: 10px;}
    .ai-text { font-size: 1rem; color: #E0E0E0; line-height: 1.6;}
    .highlight { color: #E50914; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

if "FX2_V_FINAL_ULTRA_SMART" not in st.session_state:
    st.session_state.clear()
    st.session_state["FX2_V_FINAL_ULTRA_SMART"] = True

# 全局共享状态字典
if "ai_signals" not in st.session_state:
    st.session_state["ai_signals"] = {"M1": None, "M3": None, "M4": None, "M5": None}

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

# ================= 🌟 AI 全局决策中枢 (UI 顶部) =================
st.title("🏦 FX2 机构级全维量化终端 (终极形态)")

def render_ai_brain():
    sigs = st.session_state["ai_signals"]
    
    if sigs["M1"] is None and sigs["M5"] is None:
        st.markdown('<div class="ai-box"><div class="ai-title">🧠 AI 全局决策中枢 (待命)</div><div class="ai-text">请在下方任意模块执行精算，系统将在此自动合成最终战术指令。</div></div>', unsafe_allow_html=True)
        return

    m1_sig = sigs["M1"] or {}
    m5_sig = sigs["M5"] or {}
    
    score = 50
    tactics = []
    
    # 逻辑分析 1：合成赔率刺透 (M1)
    if m1_sig.get("is_fake_hot"):
        score -= 30
        tactics.append("🚨 【M1 刺透】标盘主胜遭机构**虚假造热**，亚指纯水倒推显示其未设实质防线！主队**极大概率赢球输盘或爆冷**。")
    elif m1_sig.get("is_real_def"):
        score += 30
        tactics.append("🛡️ 【M1 共振】标盘与亚指合成概率**高度吻合且双重设防**，主队获得真实资金护盘。")
        
    # 逻辑分析 2：全息张力拓扑 (M5)
    if m5_sig.get("tension_break"):
        score -= 20
        tactics.append("🌪️ 【M5 拓扑】本土资金池(体彩/马会)与 365 产生**严重张力断裂** (离散度极高)。体彩已进入**独立诱导模式**，凡大幅降水项全部为毒饵！")
    elif m5_sig.get("tension_safe"):
        score += 10
        tactics.append("⚖️ 【M5 拓扑】三家机构数据空间距离安全，全球与本土共识度较高，无明显做局干扰。")

    # 逻辑分析 3：奇偶与进球趋势 (M5)
    if m5_sig.get("m3_val", 0) >= 0.025:
        tactics.append("🎯 【M5 进球】单双资金发生**极值倾斜**，机构对偶数痛下杀手，单数球为全场核心博弈点。")
    elif m5_sig.get("m3_val", 0) <= -0.025:
        tactics.append("🎯 【M5 进球】单双资金发生**极值倾斜**，机构对奇数痛下杀手，双数球为全场核心博弈点。")

    if score >= 80: rating = "<span style='color:#4CAF50;'>S级 (绝对信任) - 可重注出击</span>"
    elif score >= 60: rating = "<span style='color:#FFC107;'>A级 (稳健共识) - 标准仓位配置</span>"
    elif score <= 30: rating = "<span style='color:#E50914;'>☠️ 陷阱级 (重度扭曲) - 坚决反买诱导项</span>"
    else: rating = "<span style='color:#9E9E9E;'>B级 (混沌博弈) - 建议观望或轻仓走地</span>"

    html_content = f"""
    <div class="ai-box">
        <div class="ai-title">🧠 AI 全息战术定调报告</div>
        <div class="ai-text">
            <strong>综合战术评级：</strong> {rating}<br><br>
            <strong>底层雷达扫描结果：</strong><br>
            {'<br>'.join(['• ' + t for t in tactics]) if tactics else '• 基础数据平稳，未捕捉到机构强干预信号。'}
        </div>
    </div>
    """
    st.markdown(html_content, unsafe_allow_html=True)

render_ai_brain()

# ================= 3. 核心数学引擎 =================
def calc_pure_prob_array(arr):
    arr = np.array(arr, dtype=float)
    if pd.isna(arr).any() or (arr <= 0).any():
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

def safe_extract_array(data_list):
    out = []
    for x in data_list:
        try:
            val = float(x)
            out.append(val if not math.isnan(val) else 0.0)
        except:
            out.append(0.0)
    return np.array(out, dtype=float)

# ================= 4. 防闪退矩阵构建 =================
def safe_number_input(label, state_key, default_val, format="%.4f", step=0.0010):
    wid_key = "wid_" + state_key
    if state_key not in st.session_state: st.session_state[state_key] = default_val
    def cb(): st.session_state[state_key] = st.session_state[wid_key]
    if wid_key not in st.session_state: st.session_state[wid_key] = st.session_state[state_key]
    return st.number_input(label, value=st.session_state[wid_key], format=format, step=step, key=wid_key, on_change=cb)

def render_odds_grid(module_key, match_id, wl, options, col_names, init_data):
    st.markdown(f"### 📥 矩阵录入区")
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

# ================= 5. 底座参数 =================
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
cols_m5_new = ["365赔率", "马会赔率", "体彩赔率"]
init_m5_g = [[17.0, 15.0, 17.0], [6.5, 5.8, 6.5], [4.0, 3.9, 4.0], [4.0, 3.7, 3.65], [5.0, 4.35, 4.25], [8.0, 6.6, 7.0], [15.0, 11.0, 12.0], [19.0, 16.0, 18.0]]

opts_m5_h = ["胜胜", "胜平", "胜负", "平胜", "平平", "平负", "负胜", "负平", "负负"]
init_m5_h = [[4.333, 3.95, 3.7], [13.0, 12.5, 13.0], [23.0, 23.0, 26.0], [6.5, 6.0, 6.65], [6.0, 5.4, 5.85], [6.0, 5.8, 6.6], [23.0, 24.0, 28.0], [13.0, 12.5, 13.0], [4.0, 3.65, 3.55]]

matches_list = ["⚽ 比赛 1", "⚽ 比赛 2", "⚽ 比赛 3", "⚽ 比赛 4", "⚽ 比赛 5"]

# ================= 6. 导航 =================
st.sidebar.title("🧭 控制台")
current_match = st.radio("🏆 并发沙盒切换：", matches_list, horizontal=True)

active_module = st.sidebar.radio("=== 分析体系 ===", ["⚔️ M1：智能大盘引擎", "⚽ M2：进球数扫描", "🎫 M3：高维比分定位", "🧬 M4：敞口位移核算", "🔭 M5：三维拓扑全息引擎", "🎲 M6：365约束"])

st.sidebar.markdown("---")
# --- 📡 竞彩足球实时探针 (保留) ---
st.sidebar.markdown("### 📡 竞彩官方接口探针")
st.sidebar.caption("直连 zqcf918.com 内部数据引擎")

if 'api_list_data' not in st.session_state: st.session_state['api_list_data'] = None
if 'api_odds_data' not in st.session_state: st.session_state['api_odds_data'] = None

if st.sidebar.button("🔄 第一步：拉取赛程列表接口", type="primary"):
    with st.spinner("🤖 正在请求 jc 列表接口..."):
        try:
            url_list = "https://www.zqcf918.com/new/website/lottery/jc"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            res = requests.get(url_list, headers=headers, timeout=8)
            if res.status_code == 200: st.session_state['api_list_data'] = res.json()
            else: st.sidebar.error(f"❌ 网站拦截，状态码：{res.status_code}")
        except Exception as e: st.sidebar.error(f"❌ 网络请求报错：{e}")

if st.session_state['api_list_data'] is not None:
    st.sidebar.success("✅ 赛程列表连接成功！")
    with st.sidebar.expander("👉 展开查看【列表 JSON】数据", expanded=False): st.json(st.session_state['api_list_data'])

test_match_id = st.sidebar.text_input("🔗 第二步：输入比赛 ID")

if st.sidebar.button("🔌 测试抓取单场赔率"):
    if test_match_id:
        with st.spinner("🤖 正在请求 getHeadGameInfo..."):
            try:
                url_odds = "https://www.zqcf918.com/new/website/real/time/getHeadGameInfo"
                headers = {'User-Agent': 'Mozilla/5.0'}
                res = requests.get(url_odds, params={'matchId': test_match_id, 'id': test_match_id}, headers=headers, timeout=8)
                if res.status_code == 200: st.session_state['api_odds_data'] = res.json()
                else: st.sidebar.error(f"❌ 网站拦截：{res.status_code}")
            except Exception as e: st.sidebar.error(f"❌ 请求异常：{e}")

if st.session_state['api_odds_data'] is not None:
    st.sidebar.success("✅ 赔率数据连接成功！")
    with st.sidebar.expander("👉 展开查看【赔率 JSON】数据", expanded=False): st.json(st.session_state['api_odds_data'])

# ================= 7. ⚔️ M1：智能大盘引擎 (NEW!) =================
if active_module == "⚔️ M1：智能大盘引擎":
    st.header(f"⚔️ {current_match} - 欧亚大盘体系 (智能风控挂载)")
    st.info("💡 **系统升级：** 系统将根据你选择的比赛资金池级别，自动配置最优的敏感度阈值进行侦测。")
    
    # 智能联赛定级器
    col_level, col_hcp = st.columns(2)
    with col_level:
        league_level = st.selectbox("🌊 选择本场赛事的资金环境：", [
            "🟡 中水区 (常规阈值 - 适合大多数主流联赛)",
            "🔴 深水区 (钝化阈值 - 适合英超、欧冠等海量资金对冲)",
            "🟢 浅水区 (敏感阈值 - 适合日职、次级联赛等浅盘)"
        ])
    
    with col_hcp: 
        h_val = safe_number_input(f"主队亚指让球数", f"m1_hcp_{current_match}", -1.0, format="%.2f", step=0.25)
    
    # 智能阈值映射引擎
    if "浅" in league_level:
        z2, z3, z4, z5 = 0.0300, 0.0200, 0.0120, 0.0080
    elif "深" in league_level:
        z2, z3, z4, z5 = 0.0100, 0.0070, 0.0040, 0.0020
    else: # 中水区默认
        z2, z3, z4, z5 = 0.0200, 0.0130, 0.0080, 0.0050

    st.markdown(f"> *当前系统侦测级别：红线预警阈值已自动锁定至 **{z2*100:.2f}%***")

    res_m1 = render_odds_grid("m1", current_match, "大盘数据", opts_m1, cols_m1, init_m1)
    calc_key = f"m1_calc_{current_match}"
    if calc_key not in st.session_state: st.session_state[calc_key] = False
    
    if st.button(f"🚀 执行精算测谎", type="primary", use_container_width=True, key=f"btn_{calc_key}"): 
        st.session_state[calc_key] = True
        
    if st.session_state[calc_key]:
        c_odds, d_odds = safe_extract_array(res_m1['初盘']), safe_extract_array(res_m1['临场'])
        biao_c, rang_c = calc_pure_prob_array(c_odds[0:3]), calc_pure_prob_array(c_odds[3:6])
        biao_d, rang_d = calc_pure_prob_array(d_odds[0:3]), calc_pure_prob_array(d_odds[3:6])
        prob_c, prob_d = np.concatenate([biao_c, rang_c]), np.concatenate([biao_d, rang_d])
        delta = np.round(prob_d - prob_c, 4)
        
        # --- 🚀 NEW: 合成赔率测谎仪 ---
        is_fake_hot = False
        is_real_def = False
        if h_val <= -0.75 and biao_d[0] > 0 and rang_d[0] > 0:
            synthetic_diff = biao_d[0] - rang_d[0]
            if delta[0] > 0.02 and synthetic_diff > 0.25:
                is_fake_hot = True
            elif delta[0] > 0.015 and synthetic_diff < 0.15:
                is_real_def = True
                
        st.session_state["ai_signals"]["M1"] = {"is_fake_hot": is_fake_hot, "is_real_def": is_real_def}
        # -------------------------------
        
        s_theo, u_theo = np.full(6, np.nan), np.full(6, np.nan)
        t_open, v_open, w_traj, aa_hedge = ["⚪ 无对照"]*6, ["⚪ 无对照"]*6, ["⚪ 无对照"]*6, ["⚪ 动量未达标"]*6
        
        if h_val < 0:
            s_theo[0], u_theo[0] = prob_c[3] + prob_c[4], prob_d[3] + prob_d[4]
            s_theo[1], u_theo[1] = prob_c[5] - prob_c[2], prob_d[5] - prob_d[2]
        elif h_val > 0:
            s_theo[0], u_theo[0] = prob_c[3] - prob_c[1], prob_d[3] - prob_d[1]

        s_theo, u_theo = np.round(s_theo, 4), np.round(u_theo, 4)
        for i in range(6):
            c_prob, s_t, d_prob, u_t = prob_c[i], s_theo[i], prob_d[i], u_theo[i]
            if not pd.isna(s_t) and not pd.isna(u_t) and not pd.isna(c_prob):
                diff_c, diff_d = c_prob - s_t, d_prob - u_t
                t_open[i] = "🔻 极限低开" if diff_c >= z2 else "📉 显著低开" if diff_c >= z3 else "⚪ 体系平衡"
                v_open[i] = "🔻 极限低开" if diff_d >= z2 else "📉 显著低开" if diff_d >= z3 else "⚪ 体系平衡"
                traj = diff_d - diff_c
                w_traj[i] = "🚨 剧烈砸盘" if traj >= 0.02 else "📉 步步紧逼" if traj >= 0.01 else "⚪ 伪装平稳"
                
        out_main = pd.DataFrame({"选项": opts_m1, "初盘纯率": prob_c, "临场纯率": prob_d, "动量(Δ)": delta, "理论基底": s_theo, "初盘定性": t_open, "轨迹研判": w_traj})
        st.markdown("### 📊 大盘底层张力矩阵")
        st.dataframe(out_main.fillna(""), hide_index=True, use_container_width=True)

        if is_fake_hot:
            st.error("💣 **【测谎预警】庄家在标盘强行压低赔率造热，但亚指纯水倒推显示其并未设实质防线！主队极大概率赢球输盘或爆冷！**")
        elif is_real_def:
            st.success("🛡️ **【真实防守】标盘与亚指合成概率高度吻合且双重设防，庄家实实在在阻挡上盘资金打出！**")

# ================= 8. ⚽ 模块二 (原样保留) =================
elif active_module == "⚽ M2：进球数扫描":
    st.header(f"⚽ {current_match} - 进球数多维风控")
    st.info("模块保留。请切换至核心升级模块 M1/M3/M4/M5 体验最新功能。")

# ================= 9. 🎫 M3：高维比分定位 (NEW!) =================
elif active_module == "🎫 M3：高维比分定位":
    st.header(f"🎫 {current_match} - DC 泊松比分敞口扫描器")
    st.info("💡 **深度升级说明：** 引擎将自动计算并定位全场最高概率的 **Top 5 比分集群**，直接刺透机构的极窄防线！")
    
    st.markdown("### ⚙️ 全局 DC 双泊松底座参数")
    c1, c2, c3 = st.columns(3)
    with c1: tg = safe_number_input("进球盘 (大小球)", f"m3_tg_{current_match}", 2.75, format="%.2f", step=0.25)
    with c2: hcp = safe_number_input("让球盘 (主队亚指)", f"m3_hcp_{current_match}", 0.0, format="%.2f", step=0.25)
    with c3: rho = safe_number_input("DC依赖系数 (ρ)", f"m3_rho_{current_match}", -0.15, format="%.2f", step=0.01)
    
    xg_h, xg_a = (tg - hcp) / 2, (tg + hcp) / 2
    if xg_h < 0 or xg_a < 0: st.error("⚠️ 预期进球为负，请检查盘口！")
    else:
        df_m, ph2, ph1, pdr, pau, P_col_rounded = dixon_coles_full_matrix(xg_h, xg_a, rho)
        
        # --- 🚀 NEW: Top 5 比分集群定位 ---
        score_probs = []
        for i in range(8):
            for j in range(8):
                score_probs.append({"比分": f"{i}-{j}", "纯概率": P_col_rounded[i, j]})
        top5_scores = sorted(score_probs, key=lambda x: x["纯概率"], reverse=True)[:5]
        
        st.markdown("### 🎯 机构极限防线定位 (Top 5 核心比分)")
        cols = st.columns(5)
        for idx, item in enumerate(top5_scores):
            cols[idx].metric(f"Top {idx+1} 剧本", item["比分"], f"{item['纯概率']*100:.2f}%", delta_color="off")
            
        if "1-0" in [x["比分"] for x in top5_scores[:2]] or "2-1" in [x["比分"] for x in top5_scores[:2]]:
            st.warning("⚠️ **【战术核查】** 高概率比分集中在『一球小胜』。如果体彩开出主让-1的深盘，切勿冲动，极大概率是卡盘诱导！")
        elif "0-0" in [x["比分"] for x in top5_scores[:2]] or "1-1" in [x["比分"] for x in top5_scores[:2]]:
            st.warning("⚠️ **【战术核查】** 高概率比分集中在『平局集群』。全场闷平风险极高，勿碰主胜。")
        
        st.markdown("---")
        res_m3 = render_odds_grid("m3", current_match, "全局", opts_m3, cols_m3, init_m3)
        calc_key = f"m3_calc_{current_match}"
        if calc_key not in st.session_state: st.session_state[calc_key] = False
        if st.button("🚀 启动底座联动扫描", key=f"btn_{calc_key}"): st.session_state[calc_key] = True
            
        if st.session_state[calc_key]:
            std_odds = safe_extract_array([res_m3["胜"][0], res_m3["平"][0], res_m3["负"][0]])
            let_odds = safe_extract_array([res_m3["胜"][1], res_m3["平"][1], res_m3["负"][1]])
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
            judge = np.where(pd.isna(ev_vals), "➖", np.where(ev_vals > 0, "🌟 绝对正价值", np.where(ev_vals >= -0.08, "🟡 合理磨损", "🩸 抽水深渊")))
            
            out_df3 = pd.DataFrame({"投注项": ["标准胜", "标准平", "标准负", "让球胜", "让球平", "让球负"], "推演概率": np.round(intl_prob, 4), "数学EV": ev_vals, "雷达定性": judge})
            st.dataframe(out_df3.fillna(""), hide_index=True, use_container_width=True)

# ================= 10. 🧬 M4：敞口位移核算 (NEW!) =================
elif active_module == "🧬 M4：敞口位移核算":
    st.header(f"🧬 {current_match} - 机构真实敞口刺透系统")
    st.info("💡 **深度升级说明：** 引入时间位移（Delta Liability）。如果某一项资金暴增，但庄家无降水驱赶动作，将触发【资金堰塞湖】红色警报！")
    
    st.markdown("### 📥 录入标盘资金流")
    col1, col2 = st.columns(2)
    with col1: 
        c_w = safe_number_input("初盘 主胜", f"m4_cw_{current_match}", 2.10)
        c_d = safe_number_input("初盘 平局", f"m4_cd_{current_match}", 3.40)
        c_l = safe_number_input("初盘 客胜", f"m4_cl_{current_match}", 3.50)
    with col2:
        d_w = safe_number_input("临场 主胜", f"m4_dw_{current_match}", 1.95)
        d_d = safe_number_input("临场 平局", f"m4_dd_{current_match}", 3.50)
        d_l = safe_number_input("临场 客胜", f"m4_dl_{current_match}", 3.80)
        
    if st.button("💣 启动动态敞口扫描", type="primary"):
        c_odds = np.array([c_w, c_d, c_l])
        d_odds = np.array([d_w, d_d, d_l])
        
        c_implied = 1.0 / c_odds
        d_implied = 1.0 / d_odds
        
        c_prob = c_implied / np.sum(c_implied)
        d_prob = d_implied / np.sum(d_implied)
        
        c_liab = c_prob * c_odds
        d_liab = d_prob * d_odds
        
        shift = d_liab - c_liab
        
        df_liab = pd.DataFrame({
            "赛果": ["主胜", "平局", "客胜"],
            "初盘风险敞口": np.round(c_liab, 4),
            "临场风险敞口": np.round(d_liab, 4),
            "🔥 敞口偏移量": np.round(shift, 4)
        })
        st.dataframe(df_liab, hide_index=True)
        
        max_shift_idx = np.argmax(shift)
        max_val = shift[max_shift_idx]
        if max_val > 0.03:
            st.error(f"🚨 **【资金堰塞湖爆发】** 机构在 **【{df_liab['赛果'][max_shift_idx]}】** 上的赔付敞口极速恶化（+{max_val*100:.2f}%），且未采取极端降水避险。这极度不符合风控逻辑，极速杀全盘预警！该项绝非真实赛果！")

# ================= 11. 🔭 M5：三维拓扑全息引擎 (NEW!) =================
elif active_module == "🔭 M5：三维拓扑全息引擎":
    st.header(f"🔭 {current_match} - V15 全息量化精算实验室")
    st.info("💡 **深度升级说明：** 引入【余弦相似度张力测试】。通过空间距离，精准测算体彩、马会是否脱离了 365 全球精算轨道，彻底识别独立杀猪局。")

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

    def get_j_warning(dev):
        if pd.isna(dev): return "➖"
        if dev <= -0.15: return "🕳️ SSS级断崖诱导"
        if dev <= -0.08: return "🕸️ SS级高赔陷阱"
        if dev >= 0.12: return "🛡️ SSS级核心压制"
        if dev >= 0.05: return "🛡️ S级温和设防"
        return "⚪ 市场均衡波动"

    def get_k_goal(i, dev, b365, hk, tc, p365, pHK, pTC, m3, rankTC, rankEU, p_math):
        is_even = (i % 2 == 0)
        is_odd = not is_even
        if i == 0 and hk <= 7 and hk > 0: return "☠️ 【极端风控】马会0球跌破7.0，封死平局空间，防0-0闷平！"
        if i == 1 and hk > 0 and b365 > 0 and hk < 4.0: return "🚨 【物理倒挂】马会1球异常低开，重点防范！"
        if b365 > 0 and (hk / b365) <= 0.5: return "🌋 【马会断崖】马会赔率不足365一半！无脑追击！"
        if p365 > 0 and ((pHK / p365) - 1) >= 0.15: return f"🦇 【马会独立重防】马会纯概率高出欧洲 {((pHK/p365 - 1)*100):.2f}%！独家绝密情报，重点防范！"
        if b365 == 4.333: return "🎯 【阻力锚点】365启动4.333，进入对冲博弈盲区"
        
        if not pd.isna(pTC) and not pd.isna(p_math) and p_math > 0 and (pTC - p_math) >= 0.08 and p_math < 0.08:
            return f"🚨 【数学背离】机构强开深盘防守(超泊松期望 {((pTC-p_math)*100):.1f}%)，警惕极小概率事件造热！"
        
        if rankTC < rankEU and dev >= 0.05:
            if (is_even and m3 <= -0.015) or (is_odd and m3 >= 0.015): return "💎 【量化升维】体彩排位越级重防且共振奇偶，核心稳胆！"
            else: return "⚠️ 【排位提升】体彩防守升级，但奇偶无支撑，建议降注。"
        if dev >= 0.08 and p365 >= 0.10: return "🛡️ 【主力压制】主流区体彩超8%重防，打出概率高。"
        if dev <= -0.10 and rankTC > rankEU: return "🕳️ 【双重塌陷】体彩排位下降且降超10%，绝对诱导！"
        if dev <= -0.15: return "☠️ 【数据黑洞】纯概率严重脱节，虚假高赔陷阱。"
        return "⚪ 市场资金均衡，无结构性破绽"

    def get_k_htft(name, dev, b365, hk, tc, p365, pHK, pTC, rankTC, rankEU, n16, p_math):
        last_char = name[-1]
        in_trend = last_char in n16
        if name == "平平" and tc <= 4 and tc > 0: return "✅ 【底线预警】平平压至4.0以下，大概率沉闷。"
        if (name == "胜负" or name == "负胜") and hk < 20 and hk > 0: return "☠️ 【剧本嗅探】马会逆转赔率低于20，防惊天大冷！"
        if b365 == 4.333: return "🎯 【阻力锚点】365精算4.333占位！若吻合全场大势则极易打出临近溢出项！"
        
        if not pd.isna(pTC) and not pd.isna(p_math) and p_math > 0 and (pTC - p_math) >= 0.08 and p_math < 0.05:
            return f"🚨 【数学背离】体彩防守远超泊松期望({p_math*100:.1f}%)，警惕机构做局冷门！"
        
        if rankTC < rankEU and dev >= 0.05:
            if in_trend: return f"💎 【降维打击】体彩越级防守，且吻合宏观【{n16}】，重注定胆！"
            else: return "⚠️ 【跨区设防】排位提升但违背主趋势，谨慎介入。"
        if dev >= 0.12 and p365 >= 0.05: return "🛡️ 【资金堆积】常态概率区遭遇重防，机构真实惧怕项。"
        if dev <= -0.15 and rankTC > rankEU: return "🕳️ 【诱导深渊】体彩排位倒退且大幅放水，死路一条！"
        if dev <= -0.20: return "☠️ 【极寒冰点】偏离度破-20%，填仓诱导项，直接剔除。"
        if dev <= -0.08:
            if in_trend: return f"🕸️ 【顺势毒饵】即便吻合大势，但偏离度进入诱导区({dev*100:.2f}%)，坚决放弃！"
            else: return f"🕸️ 【高赔陷阱】偏离度暴跌({dev*100:.2f}%)，毫无机会。"
        if in_trend:
            if dev > 0: return f"💎 【顺势暗防】吻合大势且体彩暗中降赔(+{dev*100:.2f}%)，核心优选！"
            else: return f"🔎 【潜行顺流】结构健康，且底层暗合全场大势【{n16}】，重点防范！"
        return "⚪ 赔付结构吻合欧亚共识，按兵不动"

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

    with st.expander("⚙️ 引擎底座参数 (点击展开设定大盘基准)", expanded=True):
        c1, c2 = st.columns(2)
        with c1: m5_ou_val = m5_safe_input("大小球基准盘", f"m5_ou_{current_match}", 2.50, format="%.2f", step=0.25)
        with c2: m5_hcp_val = m5_safe_input("亚指让球(主让为负)", f"m5_hcp_{current_match}", -0.50, format="%.2f", step=0.25)
        
    tab_g, tab_h = st.tabs(["⚽ 进球数数据录入", "🔵 半全场数据录入"])
    with tab_g: res_m5_g = m5_render_grid("m5g", current_match, "进球数", opts_m5_g, cols_m5_new, init_m5_g)
    with tab_h: res_m5_h = m5_render_grid("m5h", current_match, "半/全场", opts_m5_h, cols_m5_new, init_m5_h)
    
    calc_key_m5 = f"m5_calc_{current_match}"
    if calc_key_m5 not in st.session_state: st.session_state[calc_key_m5] = False
    
    if st.button("🚀 启动 V15 全息分析引擎", type="primary", use_container_width=True, key=f"btn_{calc_key_m5}"):
        st.session_state[calc_key_m5] = True
        
    if st.session_state[calc_key_m5]:
        st.markdown("---")
        try:
            math_g, math_h = generate_poisson_baselines(m5_ou_val, m5_hcp_val)
            
            g_365 = safe_extract_array(res_m5_g['365赔率'])
            g_hk  = safe_extract_array(res_m5_g['马会赔率'])
            g_tc  = safe_extract_array(res_m5_g['体彩赔率'])
            
            h_365 = safe_extract_array(res_m5_h['365赔率'])
            h_hk  = safe_extract_array(res_m5_h['马会赔率'])
            h_tc  = safe_extract_array(res_m5_h['体彩赔率'])
            
            p365_g, pHK_g, pTC_g = calc_pure_prob_array(g_365), calc_pure_prob_array(g_hk), calc_pure_prob_array(g_tc)
            p365_h, pHK_h, pTC_h = calc_pure_prob_array(h_365), calc_pure_prob_array(h_hk), calc_pure_prob_array(h_tc)
            
            # --- 🚀 NEW: 余弦相似度张力拓扑测试 ---
            dot_product = np.dot(p365_h, pTC_h)
            norm_365 = np.linalg.norm(p365_h)
            norm_tc = np.linalg.norm(pTC_h)
            similarity = dot_product / (norm_365 * norm_tc) if norm_365*norm_tc != 0 else 0
            
            if similarity < 0.985:
                st.session_state["ai_signals"]["M5"] = {"tension_break": True, "tension_safe": False, "m3_val": 0.0}
            else:
                st.session_state["ai_signals"]["M5"] = {"tension_break": False, "tension_safe": True, "m3_val": 0.0}
            
            st.markdown(f"### 🧬 三方共识张力距离: `{similarity:.4f}`")
            if similarity < 0.985:
                st.error("🌪️ **【体系崩塌警报】 本土资金(体彩)的数据分布与全球模型(365)产生严重时空撕裂！体彩已脱离轨道，进入诱导杀猪模式！**")
            else:
                st.success("✅ **【空间收敛】 三方机构的纯净概率空间距离极近，市场无严重内幕分歧，可进行常规参数分析。**")
            # --------------------------------------

            cons_g = np.round((p365_g + pHK_g) / 2, 4)
            cons_h = np.round((p365_h + pHK_h) / 2, 4)
            
            dev_g = np.round((pTC_g / cons_g) - 1, 4)
            dev_h = np.round((pTC_h / cons_h) - 1, 4)

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
            
            if st.session_state["ai_signals"]["M5"]:
                st.session_state["ai_signals"]["M5"]["m3_val"] = m3
            
            odd_devs = [x for x in [dev_g[1], dev_g[3], dev_g[5], dev_g[7]] if not pd.isna(x)]
            is_tear = (max(odd_devs) - min(odd_devs)) >= 0.10 if len(odd_devs) > 0 else False

            m3_text = ""
            if m3 >= 0.025: m3_text = f"🌋 【SSS级防单】极值(+{m3*100:.2f}%)！体彩对奇数痛下杀手，单数球为全场核心稳胆！"
            elif m3 >= 0.015: m3_text = f"🔴 【S级防单】高位(+{m3*100:.2f}%)！宏观资金倒向单数，符合进球数共振条件！"
            elif m3 <= -0.025: m3_text = f"🌋 【SSS级防双】极值({m3*100:.2f}%)！体彩对偶数痛下杀手，双数球为全场核心稳胆！"
            elif m3 <= -0.015: m3_text = f"🔵 【S级防双】高位({m3*100:.2f}%)！宏观资金倒向双数，符合进球数共振条件！"
            elif is_tear: m3_text = f"🌪️ 【内部撕裂】宏观极微({m3*100:.2f}%)，但单数球内部震幅超10%，庄家交叉做局，请以K列独立诊断为准！"
            else: m3_text = f"⚪ 【绝对均衡】差值极微({m3*100:.2f}%)，单双资金完美平衡，无任何做局痕迹。"

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

            st.markdown("## 📊 终极全息雷达阵列")
            
            c_g1, c_g2, c_g3, c_g4 = st.columns([1,1,1,2])
            c_g1.metric("体彩(奇)纯净汇总", f"{tc_odd_sum:.4f}")
            c_g2.metric("外围(奇)共识汇总", f"{eu_odd_sum:.4f}")
            c_g3.metric("🎯 宏观奇偶博弈差", f"{m3:.4f}")
            c_g4.info(m3_text)
            
            st.dataframe(df_g_final, hide_index=True, use_container_width=True)
            
            st.markdown("<br><hr><br>", unsafe_allow_html=True)

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

# ================= 12. 🎲 模块六 =================
elif active_module == "🎲 M6：365约束":
    st.header(f"🎲 {current_match} - 365 内部全息约束引擎")
    st.info("模块保留。")
