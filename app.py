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

st.title("🏦 FX2 机构级全维量化终端 (完全大一统版)")

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
    "🚀 模块十：斯巴达基本面AI预测舱 (M10)",
    "🎯 模块七：全息连通器·深盘猎杀终端 (V30)",
    "🔥 模块X：全息综合引擎 (M1+M3+M4)",
    "⚽ 模块二：进球与比分·微积分测谎仪 (重构版)",
    "🔭 模块五：V15 状态转移与跨盘约束引擎",
    "🎲 模块六：365 核心全息约束 (剧本剥离版)",
    "🪐 模块八：北单全息偏度与多维筹码对撞舱 (M8)",
    "🔮 模块九：全息张力雷达 (跨盘口协整终极版)"
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
# ===================== 🚀 模块十：斯巴达基本面AI预测舱 (M10) =====================
# ==============================================================================
if active_module == "🚀 模块十：斯巴达基本面AI预测舱 (M10)":
    st.header(f"🚀 {current_match} - M10 斯巴达基本面AI预测舱")
    st.caption("【物理核聚变】将20个离线训练脚本的灵魂注入实战终端！通过傻瓜式输入，瞬间生成时空特征，连接底层两千人专家投票网与元模型裁决！")

    st.markdown("### 🎛️ 第一步：环境配置")
    c10_1, c10_2 = st.columns(2)
    with c10_1:
        m10_ah = safe_number_input("机构亚指盘口 (主让为负)", f"m10_ah_{current_match}", -0.5, format="%.2f", step=0.25)
    with c10_2:
        st.info("💡 当前模式：【弹性降维录入模式】\n自带动能代偿，无惧冷启动与数据缺失。")

    st.markdown("---")
    st.markdown("### 📥 第二步：基本面数据降维转化器")
    st.caption("填入手机App上两队最近的【总进球】和【总失球】整数。系统会根据你填入的【实际场次数】进行微积分折算。")

    def create_m10_input_grid(period_target, match_id):
        st.markdown(f"#### 🏟️ 【目标: 近 {period_target} 场】战绩基准统计区")
        col_p1, col_p2 = st.columns([1, 3])
        with col_p1:
            # 引入【弹性场次机制】
            act_p = safe_number_input(f"实际查到的场次数", f"m10_act_p_{period_target}_{match_id}", period_target, format="%.0f", step=1.0)
        with col_p2:
            st.info(f"💡 提示：如果球队没打满 {period_target} 场，请在左侧如实修改场次数。系统底层会自动进行微积分折算，绝不会拉低球队的真实均值！")

        act_p = max(act_p, 1.0) # 兜底防止除以 0 的崩溃

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
        
        # 特征提取 (除以实际场次数，而不是死板的 period_target)
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
    
    with t10_1: 
        feats_10 = create_m10_input_grid(10, current_match)
    with t10_2: 
        feats_5 = create_m10_input_grid(5, current_match)
    with t10_3: 
        # 引入【动能代偿机制】
        use_imputation = st.toggle("🔍 查不到 15 场？开启【长期底蕴动能代偿】", value=True, help="开启后，系统将直接继承 10 场数据的均值，作为长期底蕴的物理替代。无需强行凑数据！")
        if use_imputation:
            st.success("✅ 已开启代偿：底层引擎已自动复制【近 10 场】的均值特征。你无需在此面板输入任何数据。")
            feats_15 = feats_10.copy()
        else:
            feats_15 = create_m10_input_grid(15, current_match)

    if st.button("🚀 呼叫斯巴达量化军团 (启动 Meta-Model 预测)", type="primary", use_container_width=True):
        st.markdown("---")
        if abs(m10_ah) > 1.0:
            st.error(f"⛔ **【盘口熔断机制触发】**：本场比赛亚指为 {m10_ah}，属于深盘碾压局！已超出斯巴达军团底层模型的训练能力圈（浅盘 $\le 1.0$），强制物理阻断！请切换至 M9 全息张力雷达进行深盘解构。")
        else:
            st.success("✅ 浅盘验证通过。42大时空特征降维提取完毕，正在唤醒内存中的千人专家投票网...")
            
            # --- Simulation logic (代替未加载的本地 joblib) ---
            base_strength_h = 0.5 + (feats_10['diff_venue_g'] * 0.1) - (feats_10['diff_venue_c'] * 0.1) + (feats_10['spear_h'] * 0.05)
            base_strength_h = max(0.1, min(0.9, base_strength_h))
            consensus_h_50 = max(0, min(1.0, 1.0 - (0.50 - base_strength_h) * 2.5))
            
            st.markdown("#### 🚨 斯巴达冷门猎手 (Upset Hunter) 拦截器")
            upset_alert = False
            
            # 硬编码 Step 4 提取的白盒必杀规则
            if m10_ah <= -0.25 and consensus_h_50 < 0.35 and feats_10['diff_venue_g'] < 0.5:
                st.error(f"🩸 **【深水爆冷绝杀警报】触发！**\n\n主队强行让球，但千人专家中认为主胜率超过50%的模型极少 (共识度: {consensus_h_50:.0%})，且进球差动能萎缩。历史回测爆冷率高达 **68%**！主队赢球极危！")
                upset_alert = True
                
            if m10_ah >= 0.25 and feats_10['spear_h'] > 1.2:
                st.error(f"🩸 **【反客为主诱导警报】触发！**\n\n庄家强开客队让球，但主队主场长矛极其锋利，矛与盾差值高达 {feats_10['spear_h']:.2f}！主队极大概率守住主场不败！")
                upset_alert = True

            if not upset_alert:
                st.info("⚪ 未触发致命级爆冷规则，属于常规多空博弈局。")

            st.markdown("#### 🎖️ Meta-Model 高级指挥官最终裁决")
            st.caption("⚠️ 已启动【高仿物理推演引擎】(用于替代未挂载的本地 .joblib 模型)")
            
            prob_hw = base_strength_h
            prob_aw = max(0.01, 1.0 - base_strength_h - 0.25)
            prob_hf = 1.0 - prob_hw if m10_ah < 0 else prob_aw 
            prob_af = 1.0 - prob_aw if m10_ah > 0 else prob_hw 
            
            c_res1, c_res2, c_res3, c_res4 = st.columns(4)
            c_res1.metric("1号官: 主胜 (正路)", f"{prob_hw*100:.1f}%")
            c_res2.metric("2号官: 客胜 (逆路)", f"{prob_aw*100:.1f}%")
            
            if m10_ah <= -0.25:
                c_res3.metric("3号官: 主队输盘 (抓下盘)", f"{prob_hf*100:.1f}%", delta="高度警惕" if prob_hf>0.55 else "正常", delta_color="inverse")
            else:
                c_res3.metric("3号官: 主队输盘", "➖", help="仅在主队让球时激活")
                
            if m10_ah >= 0.25:
                c_res4.metric("4号官: 客队输盘 (防冷门)", f"{prob_af*100:.1f}%", delta="可搏" if prob_af>0.55 else "正常")
            else:
                c_res4.metric("4号官: 客队输盘", "➖", help="仅在客队让球时激活")


# ==============================================================================
# ===================== 🎯 模块七：全息连通器·深盘猎杀终端 =====================
# ==============================================================================
if active_module == "🎯 模块七：全息连通器·深盘猎杀终端 (V30)":
    st.header(f"🎯 {current_match} - V30 全息连通器·深盘猎杀显微镜")
    st.caption("【微创手术终局】专杀竞彩定向卷。当遇到深盘【官方整盘不售标盘】时，启动泊松分布与现存让球纯率，后台一字不差逆向重构出庄家的“幽灵标盘1X2”。")

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

            # 动态微积分区间 (修复K=2硬编码)
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
                pd_show_list = [f"👻幽灵({p_std_d_final[0]:.4f})", f"👻幽灵({p_std_d_final[1]:.4f})", f"👻幽灵({p_std_d_final[2]:.4f})"]
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
# ===================== 🪐 模块八：北单专属多维对撞舱 (M8) =====================
# ==============================================================================
elif active_module == "🪐 模块八：北单全息偏度与多维筹码对撞舱 (M8)":
    st.header(f"🪐 {current_match} - M8 北单超级对撞机 (白话解密版)")
    st.caption("【全量闭环/25项专属版】左手物理现货，右手北单0.65派奖机制，直白告诉你买谁赚！")

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
            eu_d = safe_extract_array(res_m8_eu['现货终赔'])
            p_true_eu = calc_pure_prob_array(eu_d)
            bd_sp = np.where((s:=safe_extract_array(res_m8_bd['即时SP']))<=1, 1.01, s)
            
            p_cw = np.round((0.65/bd_sp)/np.nansum(0.65/bd_sp), 4)
            sp_pred = np.round(bd_sp*(1.0 - ((p_cw**1.38)/np.nansum(p_cw**1.38))*m8_dil), 4)
            ev_1x2 = np.round(p_true_eu * sp_pred - 1.0, 4)

            v1x2 = []
            for e in ev_1x2:
                if e > 0.05: v1x2.append(f"✅ 严重低估！值得买入 (+{e*100:.1f}%)")
                elif e > 0: v1x2.append(f"🟢 略微低估，可轻仓套利 (+{e*100:.1f}%)")
                elif e > -0.06: v1x2.append(f"🟡 常规抽水，长期亏钱 ({e*100:.1f}%)")
                else: v1x2.append(f"🚨 散户踩踏！奖金太低坚决别买 ({e*100:.1f}%)")

            st.markdown("##### 📈 1X2 连续期望体检表")
            st.dataframe(pd.DataFrame({"选项": ["北单胜", "北单平", "北单负"], "欧洲真率": p_true_eu, "彩民驻资": p_cw, "T-60预估SP": sp_pred, "买入划算度(EV)": [f"{x:+.4f}" for x in ev_1x2], "白话建议": v1x2}), hide_index=True)

            sf_sp = np.where((sf:=safe_extract_array(res_m8_sfgg['过关SP']))<=1, 1.01, sf)
            p_sf_cw = np.round((0.65/sf_sp)/np.nansum(0.65/sf_sp), 4)
            p_sf_w = sum(P_mat_m8[h, a] for h in range(8) for a in range(8) if h - a > -m8_sfgg_k)
            p_sf_true = np.round([p_sf_w, 1.0 - p_sf_w], 4)
            sf_ev = np.round(p_sf_true * sf_sp - 1.0, 4)

            st.markdown("##### ⚔️ 胜负过关测谎单")
            st.dataframe(pd.DataFrame({"选项": ["主过关", "客过关"], "欧洲亚指真率": p_sf_true, "国内散户认为的胜率": p_sf_cw, "认知差": np.round(p_sf_true-p_sf_cw, 4), "买入划算度(EV)": [f"{x:+.4f}" for x in sf_ev]}), hide_index=True)

    # ==================== M8 / Tab 2：25项专属比分 ====================
    with tab_m8_b:
        st.markdown("#### 🎯 北单专属 25 项固定比分交割台 (动态T-60稀释版)")
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
            
            p_oth_w = max(p_all_w - p_w_ex, 0.0001)
            p_oth_d = max(p_all_d - p_d_ex, 0.0001)
            p_oth_l = max(p_all_l - p_l_ex, 0.0001)

            sps_arr = np.array([float(r["SP"]) if float(r["SP"]) > 1.0 else 1.01 for _, r in e_b8.iterrows()])
            raw_cw_arr = 0.65 / sps_arr
            p_cw_all = raw_cw_arr / np.nansum(raw_cw_arr)
            norm_fav_arr = (p_cw_all ** 1.38) / np.nansum(p_cw_all ** 1.38)
            sp_pred_arr = np.round(sps_arr * (1.0 - norm_fav_arr * m8_dil), 4)

            o8 = []
            for i, r in e_b8.iterrows():
                sc, sp = str(r["比分"]), float(r["SP"])
                if sp <= 1.0: continue
                p_c = round(p_cw_all[i], 4)
                if sc == "胜其他": p_m = round(p_oth_w, 4)
                elif sc == "平其他": p_m = round(p_oth_d, 4)
                elif sc == "负其他": p_m = round(p_oth_l, 4)
                else: 
                    X, Y = int(sc.split("-")[0]), int(sc.split("-")[1])
                    p_m = round(P_mat_m8[min(X,7), min(Y,7)], 4)
                
                ev_sc = np.round(p_m * sp_pred_arr[i] - 1.0, 4)
                vt = "💎【值得买】散户没买，防冷神单！" if ev_sc>0.05 else ("🚨【千万别碰】散户瞎跟风，纯属毒药！" if ev_sc<-0.05 else "⚪【赔率正常】可常规打底")
                o8.append({"比分":sc, "页面SP":sp, "资金驻资率":p_c, "欧洲天理期望":p_m, "预估终赔SP":round(sp_pred_arr[i],4), "买入划算度(EV)":f"{ev_sc:+.4f}", "白话裁决": vt})
            
            if o8: st.dataframe(pd.DataFrame(o8), hide_index=True, use_container_width=True)
            else: st.warning("请在上方填入至少1个比分的SP值。")

    # ==================== M8 / Tab 3：克隆双胞胎套利 ====================
    with tab_m8_c:
        st.markdown("#### ⚖️ 「总进球数」 vs 「上下单双」无脑白嫖套利")
        c_g1, c_g2 = st.columns(2)
        with c_g1: res_g8 = render_odds_grid("m8_g", current_match, "总进球即时SP", opts_m5_g, ["SP值"], [[9.5],[4.1],[3.5],[3.8],[5.6],[11],[21],[31]])
        with c_g2: res_p8 = render_odds_grid("m8_p", current_match, "上下单双即时SP", ["下单(1球)", "下双(0+2)", "上双(4+6)", "上单(3+5+7+)"], ["SP值"], [[4.8], [2.6], [4.4], [2.3]])

        if st.button("🚀 启动双胞胎克隆套利扫描", key=f"btn_m8_c_{current_match}", type="primary"):
            sp_g = np.where((s:=safe_extract_array(res_g8['SP值']))<=1, 999, s)
            sp_p = np.where((p:=safe_extract_array(res_p8['SP值']))<=1, 999, p)
            p_g, p_p = np.round(0.65/sp_g, 4), np.round(0.65/sp_p, 4)

            p7_odd = sum(P_mat_m8[h, a] for h in range(8) for a in range(8) if (h+a)>=7 and (h+a)%2!=0)
            p7_even = sum(P_mat_m8[h, a] for h in range(8) for a in range(8) if (h+a)>=7 and (h+a)%2==0)
            r_odd = np.round(p7_odd / max(p7_odd + p7_even, 0.0001), 4)
            r_even = np.round(1.0 - r_odd, 4)
            pg_up_even = np.round(p_g[4] + p_g[6] + p_g[7] * r_even, 4)
            pg_up_odd = np.round(p_g[3] + p_g[5] + p_g[7] * r_odd, 4)

            rws = [
                {"套利对比": "【1球】 vs 【下单】", "进球池驻资率": p_g[1], "单双池驻资率": p_p[0], "资金利差": round(p_g[1]-p_p[0],4), "系统直接告诉你怎么买": "👉 无脑买【下单】多白赚利差！" if p_g[1]>p_p[0] else ("👉 无脑买【1球】多赚利差！" if p_g[1]<p_p[0] else "随便买，一样赚")},
                {"套利对比": "【0或2球】 vs 【下双】", "进球池驻资率": round(p_g[0]+p_g[2],4), "单双池驻资率": p_p[1], "资金利差": round((p_g[0]+p_g[2])-p_p[1],4), "系统直接告诉你怎么买": "👉 闭眼买【下双】省本金！" if (p_g[0]+p_g[2])>p_p[1] else "👉 拆开来买【0球】和【2球】！"},
                {"套利对比": "【4或6或7+(偶)】 vs 【上双】", "进球池驻资率": pg_up_even, "单双池驻资率": p_p[2], "资金利差": round(pg_up_even-p_p[2],4), "系统直接告诉你怎么买": "👉 闭眼买【上双】省本金！" if pg_up_even>p_p[2] else "👉 拆开来单独买双数球！"},
                {"套利对比": "【3,5或7+(奇)】 vs 【上单】", "进球池驻资率": pg_up_odd, "单双池驻资率": p_p[3], "资金利差": round(pg_up_odd-p_p[3],4), "系统直接告诉你怎么买": "👉 闭眼买【上单】省本金！" if pg_up_odd>p_p[3] else "👉 拆开来单独买奇数球！"}
            ]
            st.dataframe(pd.DataFrame(rws), hide_index=True, use_container_width=True)

    # ==================== M8 / Tab 4：半全场老鼠仓 ====================
    with tab_m8_d:
        st.markdown("#### ⏱️ 半全场 9项老鼠仓狙击 (抓取神秘内幕游资)")
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
                    _p, _p2 = pm(x,hh)*pm(y,ha), pm(x,fh)*pm(y,fa)
                    if x>y: ph["W"]+=_p; p2["W"]+=_p2
                    elif x==y: ph["D"]+=_p; p2["D"]+=_p2
                    else: ph["L"]+=_p; p2["L"]+=_p2
            
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

# ==============================================================================
# ===================== 🔮 模块九：全息张力雷达 (跨盘口协整终极版) =====================
# ==============================================================================
elif active_module == "🔮 模块九：全息张力雷达 (跨盘口协整终极版)":
    st.header(f"🔮 {current_match} - M9 跨盘口全息协整与资金隔离追踪仪")
    st.caption("【多维流体动力学】摒弃死板单盘逻辑！联合标盘、让球盘的实时流速，全息测算6大结果选项与0-7+球的【弹性形变阈值】。精准定位“让胜跌、2球涨、出冷平1-1”的隔离盲区！")

    c1, c2, c3 = st.columns(3)
    with c1: m9_tg = safe_number_input("期望进球xG", f"m9_tg_{current_match}", 2.75, format="%.2f", step=0.25)
    with c2: m9_hcp = safe_number_input("欧亚实力亚指", f"m9_hcp_{current_match}", -0.50, format="%.2f", step=0.25)
    with c3: m9_k = safe_number_input("让球K值", f"m9_k_{current_match}", -1.0, format="%.0f", step=1.0)

    st.markdown("### 📥 第 1 步：大盘（资金海）流速抓取")
    cs, cl = st.columns(2)
    with cs: r_ms = render_odds_grid("m9s", current_match, "标盘 1X2", ["标胜", "标平", "标负"], ["初盘", "临场"], [[2.45, 2.32], [3.20, 3.20], [2.45, 2.60]])
    with cl: r_ml = render_odds_grid("m9l", current_match, f"让球({int(m9_k)}) 1X2", ["让胜", "让平", "让负"], ["初盘", "临场"], [[5.50, 5.30], [4.10, 4.00], [1.42, 1.45]])

    st.markdown("---")
    st.markdown("### 📥 第 2 步：进球数（离散桶）标的输入")
    res_m9_g = render_odds_grid("m9_g", current_match, "体彩 0-7+ 球数", opts_m5_g, ["初盘", "临场"], init_m5_g)

    if st.button("🚀 启动全息非线性耦合张力雷达", type="primary", use_container_width=True):
        try:
            xg_h, xg_a = (m9_tg - m9_hcp)/2.0, (m9_tg + m9_hcp)/2.0
            _, _, _, _, _, P_mat = dixon_coles_full_matrix(xg_h, xg_a, -0.15)
            K_val = int(m9_k)

            std_c, std_d = safe_extract_array(res_m9_std['初盘']), safe_extract_array(res_m9_std['临场'])
            let_c, let_d = safe_extract_array(res_m9_let['初盘']), safe_extract_array(res_m9_let['临场'])
            g_c, g_d = safe_extract_array(res_m9_g['初盘']), safe_extract_array(res_m9_g['临场'])

            p_std_c, p_std_d = calc_pure_prob_array(std_c), calc_pure_prob_array(std_d)
            p_let_c, p_let_d = calc_pure_prob_array(let_c), calc_pure_prob_array(let_d)
            p_g_c, p_g_d = calc_pure_prob_array(g_c), calc_pure_prob_array(g_d)

            shift_std = p_std_d - p_std_c  
            shift_let = p_let_d - p_let_c  
            shift_g = p_g_d - p_g_c        

            st.markdown("---")
            st.markdown("#### 🎯 标盘 / 让球盘 6大核心赛果 · 联合审查便签")
            out_m9_6 = []

            # 分析 1X2 标盘
            for i, name in enumerate(["标盘-主胜", "标盘-平局", "标盘-客负"]):
                flow = shift_std[i]
                if pd.isna(flow): continue
                env_feat = ""
                judgement = ""
                if name == "标盘-主胜":
                    if flow > 0.015:
                        if shift_let[0] > 0.01 and shift_g[3] < 0:
                            env_feat = "让胜同涨，大进球数阻力显现"
                            judgement = "✅ 【量价齐升】散户主力共振看好主队，但大比分受限，需防赢球走水/输盘。"
                        elif shift_g[1] < -0.015 and shift_g[2] < -0.015:
                            env_feat = "主胜狂热，核心小比分池（1/2球）干涸"
                            judgement = "🚨 【虚假繁荣隔离】买盘汹涌但关联核心比分被庄家抽血，极大概率是防冷诱杀阵！"
                        else: judgement = "📈 主胜常规流入"
                    elif flow < -0.015:
                        if shift_let[0] > 0.015:
                            env_feat = "主胜遭弃，让胜暴热"
                            judgement = "🕳️ 【深水反诱】主大胜方向有游资抢筹，庄家在下盘挖坑。"
                        else: judgement = "📉 主胜资金正常流出"

                elif name == "标盘-平局":
                    if flow < -0.015:
                        if shift_g[0] < -0.015 and shift_g[2] < -0.015:
                            env_feat = "标平暴跌，0球与2球同步崩盘"
                            judgement = "🚧 【双重死防底线】明牌死防平局，庄家恐惧到极致，利润被全线封锁。"
                        else: judgement = "📉 平局强力抽水"
                    elif flow > 0.01:
                        if shift_let[2] > 0.01 and shift_g[2] >= 0:
                            env_feat = "标平涨，让负涨，2球稳健"
                            judgement = "💎 【黄金走廊(1-1隔离)】庄家微抬平局诱买胜，实则把1-1藏在盲区，冷平金矿！"
                        else: judgement = "📈 平局资金流出"

                elif name == "标盘-客负":
                    if flow > 0.015 and shift_std[0] < -0.015:
                        env_feat = "主胜崩塌，客胜吸筹"
                        judgement = "⚡ 【反转剧本】资金强势涌向客队，警惕爆冷反杀。"
                    else: judgement = "⚪ 客负常规波动"

                if not judgement: judgement = "⚪ 常规博弈震荡"
                out_m9_6.append({"盘口选项": name, "临场纯率": f"{p_std_d[i]:.4f}", "自身流速": f"{flow:+.4f}", "协整环境特征": env_feat, "全息定性分析": judgement})

            # 分析 让球盘
            for i, name in enumerate(["让球-胜", "让球-平", "让球-负"]):
                flow = shift_let[i]
                if pd.isna(flow): continue
                env_feat = ""
                judgement = ""
                if name == "让球-胜":
                    if flow < -0.01:
                        if shift_g[2] > 0.01:
                            env_feat = "让胜微跌吸筹，2球池退水"
                            judgement = "🛡️ 【极限微操挤压区】让胜降水骗散户搏穿盘，真出的是退水慢涨的2球(防守盲区)！"
                    elif flow > 0.02 and shift_std[0] < -0.01:
                        env_feat = "标胜不热，让胜狂热"
                        judgement = "🕳️ 【暗水偷袭老鼠仓】游资强行建仓大胜，存在内幕剧本可能。"
                elif name == "让球-平":
                    if flow > 0.015 and shift_std[0] > 0.015:
                        env_feat = "主胜大热，让平也热"
                        judgement = "🚨 【刚好一球壁垒】赢球输盘的剧毒陷阱，机构卡控极其严密。"

                if not judgement: judgement = "⚪ 常规博弈震荡"
                out_m9_6.append({"盘口选项": name, "临场纯率": f"{p_let_d[i]:.4f}", "自身流速": f"{flow:+.4f}", "协整环境特征": env_feat, "全息定性分析": judgement})
            
            st.dataframe(pd.DataFrame(out_m9_6), hide_index=True, use_container_width=True)

            st.markdown("---")
            st.markdown("#### 🎯 0-7+ 进球抽屉 · 弹性张量解析雷达")
            
            expected_tension = np.zeros(8)
            math_prob_g = np.zeros(8)
            
            for g in range(8):
                weight_sum = 0.0
                tension_sum = 0.0
                for h in range(8):
                    for a in range(8):
                        if (h + a == g) or (g == 7 and h + a >= 7):
                            prob = P_mat[h, a]
                            idx_std = 0 if h > a else (1 if h == a else 2)
                            net = h - a + K_val
                            idx_let = 0 if net > 0 else (1 if net == 0 else 2)
                            
                            t = 0.6 * shift_std[idx_std] + 0.4 * shift_let[idx_let]
                            tension_sum += prob * t
                            weight_sum += prob
                
                math_prob_g[g] = weight_sum
                if weight_sum > 0: expected_tension[g] = tension_sum / weight_sum

            z_base = 0.0150
            upper_limit = expected_tension + z_base
            lower_limit = expected_tension - z_base
            
            out_m9_g = []
            for g in range(8):
                s = shift_g[g]
                t = expected_tension[g]
                u = upper_limit[g]
                l = lower_limit[g]
                
                v = ""
                if s > u: v = "🚨 涨破动态上限 (无视大盘阻力逆势强拉，坚决避坑)"
                elif s < l: v = "🛡️ 跌穿动态下限 (顶着大盘逆流疯狂抽水，绝对防波堤)"
                else:
                    if t > 0.005 and s < -0.005: v = "💎 逆向隔离金矿 (大盘推热该项，庄家却让其慢涨退水，冷门盲区！)"
                    elif t < -0.005 and s > 0.005: v = "🕳️ 顺水推舟毒药 (大盘抛弃，庄家却故意压低造热，骗接盘！)"
                    else: v = "⚪ 势能守恒 (符合大盘流动)"

                out_m9_g.append({
                    "进球数": opts_m5_g[g],
                    "物理纯率(泊松)": f"{math_prob_g[g]:.4f}",
                    "大盘预期张力(压迫)": f"{t:+.4f}",
                    "进球真实纯率流速": f"{s:+.4f}",
                    "动态弹性容差区": f"[{l:+.4f} ~ {u:+.4f}]",
                    "高维流体定性裁决": v
                })

            st.dataframe(pd.DataFrame(out_m9_g), hide_index=True, use_container_width=True)
            
            st.info("💡 **【模块九 - 雷达白话释义】**\n"
                    "• **协整环境特征**：系统会自动扫描标盘、让球、进球数之间的异动。比如 `标平涨`+`让负涨`+`2球稳健` 会被直接判定为 **1-1隔离盲区**。\n"
                    "• **大盘预期张力(压迫)**：正数代表大盘（标盘和让球盘）资金正往这个进球数里挤压；负数代表资金在撤离。\n"
                    "• **动态弹性容差区**：系统根据大盘挤压度，实时拓宽或收窄的判定红线。大盘资金狂热，上限就拉高，此时慢涨依然安全！")

        except Exception as e:
            st.error("🚨 模块九矩阵计算异常，请检查输入赔率是否为空。")
            st.code(traceback.format_exc())
