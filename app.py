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
    </style>
""", unsafe_allow_html=True)

st.title("🏦 FX2 全维量化对冲终端")
st.markdown("---")

# ================= 2. 终极防弹引擎：纯 Numpy 暴力算力 =================
def calc_pure_prob_array(arr):
    """彻底抛弃 Pandas，使用最纯粹的 Numpy 一维数组运算，100%免疫报错"""
    arr = np.array(arr, dtype=float)
    if np.isnan(arr).any() or (arr == 0).any():
        return np.full(len(arr), np.nan)
    raw = 1.0 / arr
    return np.round(raw / np.nansum(raw), 4)

def generate_goal_radars(df, z2, z3, v_limit):
    delta_vals = df['总动量(Delta)'].values
    ev_vals = df['期望值(EV)'].values
    v_vals = df['加速度(V-Delta)'].values

    df['动量雷达 (G列)'] = np.where(delta_vals >= z2 * 2, "🌋 极度过热",
                          np.where(delta_vals >= z2, "🚨 史诗重防",
                          np.where(delta_vals >= z3, "🔥 首席主防",
                          np.where(delta_vals <= -z2 * 2, "🕳️ 极度冰封",
                          np.where(delta_vals <= -z3, "🧊 极限绞杀", "⚪ 边缘震荡")))))
    
    df['EV价值仪 (H列)'] = np.where(ev_vals >= -0.10, "🌟 绝对正价值",
                          np.where(ev_vals >= -0.15, "🟢 极度高潜",
                          np.where(ev_vals <= -0.25, "🩸 抽水深渊",
                          np.where(ev_vals <= -0.20, "🚨 杀猪预警", "🟡 合理磨损"))))
    
    df['防伪验证 (I列)'] = np.where((delta_vals >= z2 * 1.5) & (ev_vals <= -0.25), "🩸 嗜血诱导 (100%杀猪盘)",
                          np.where((delta_vals >= z3) & (delta_vals < z2 * 1.5) & (ev_vals <= -0.08) & (ev_vals >= -0.25), "🎯 精确制导 (核心真实)",
                          np.where((delta_vals <= -z3) & (ev_vals > 0), "☠️ 淬毒诱饵 (弃防)", "")))
    
    df['主力狙击 (L列)'] = np.where(pd.isna(v_vals), "➖ 无T-60不计算",
                          np.where(v_vals >= v_limit, "⚡ 绝杀爆发",
                          np.where(v_vals <= -v_limit, "🩸 极速撤离", "⚪ 匀速平稳")))
    return df

def dixon_coles_full_matrix(lambda_, mu_, rho_):
    def poisson_pmf_array(lam, max_k):
        pmf = np.zeros(max_k + 1)
        if lam <= 0:
            pmf[0] = 1.0
            return pmf
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
    p_home_win_2plus = np.sum(np.tril(P, -2))
    p_home_win_1 = np.sum(np.diag(P, -1))
    p_draw = np.sum(np.diag(P, 0))
    p_away_unbeaten = np.sum(np.triu(P, 0))
    P_collapsed = np.zeros((8, 8))
    P_collapsed[:7, :7] = P[:7, :7]
    P_collapsed[7, :7] = np.sum(P[7:, :7], axis=0) 
    P_collapsed[:7, 7] = np.sum(P[:7, 7:], axis=1) 
    P_collapsed[7, 7] = np.sum(P[7:, 7:])          
    cols = [f"客进{i}" for i in range(7)] + ["客进7+"]
    idx = [f"主进{i}" for i in range(7)] + ["主进7+"]
    return pd.DataFrame(P_collapsed, columns=cols, index=idx), p_home_win_2plus, p_home_win_1, p_draw, p_away_unbeaten

# ================= 3. 侧边栏 =================
st.sidebar.title("🧭 系统矩阵控制台")
active_module = st.sidebar.radio("=== 核心风控三大模块 ===", [
    "⚔️ 模块一：欧亚大盘体系 (包揽标盘让盘的浅中深)",
    "⚽ 模块二：进球数多维风控 (包揽进球数的浅中深)",
    "🎫 模块三：体彩高阶工具 (DC矩阵 / EV切片器)"
])

st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ 动态阈值微调")
z2 = st.sidebar.number_input("宏观红线 (Z2)", value=0.0120, format="%.4f")
z3 = st.sidebar.number_input("显著防线 (Z3)", value=0.0080, format="%.4f")
v_limit = st.sidebar.number_input("极速加速度", value=0.0050, format="%.4f")

def highlight_alerts(val):
    if pd.isna(val) or val == "": return ''
    if isinstance(val, str):
        if '🩸' in val or '☠️' in val or '🚨' in val or '🕳️' in val or '🧊' in val or '📉' in val or '🕸️' in val:
            return 'background-color: rgba(255, 0, 0, 0.2); color: #ffcccc;'
        elif '🎯' in val or '⚡' in val or '🌟' in val or '🟢' in val or '🔥' in val or '🌋' in val or '📈' in val or '✅' in val:
            return 'background-color: rgba(0, 255, 0, 0.2); color: #ccffcc;'
        elif '➖' in val:
            return 'color: #888888;'
    return ''

# ================= 4. 模块一：欧亚大盘 (纯Numpy核弹级稳定重构) =================
if active_module == "⚔️ 模块一：欧亚大盘体系 (包揽标盘让盘的浅中深)":
    st.header("⚔️ 欧亚大盘体系分析模块")
    tab1, tab2, tab3 = st.tabs(["🟢 浅水区 (标/让)", "🟡 中水区 (标/让)", "🔴 深水区 (标/让)"])
    
    def render_main_handicap_ui(water_level):
        st.markdown(f"### {water_level} 数据录入矩阵")
        cols = ["玩法选项", "初盘", "临场", "初概率", "临概率", "动量(Delta)", "七阶热度测算", "理论应有赔率", "净抽水偏离", "🎯 终极单项研判 (时空双杀)"]
        init_data = [
            ["标盘-胜", 1.78, 1.58, 0.0, 0.0, 0.0, "", 0.0, 0.0, ""],
            ["标盘-平", 3.22, 3.60, 0.0, 0.0, 0.0, "", 0.0, 0.0, ""],
            ["标盘-负", 3.90, 4.58, 0.0, 0.0, 0.0, "", 0.0, 0.0, ""],
            ["让盘-胜", 3.55, 3.18, 0.0, 0.0, 0.0, "", 0.0, 0.0, ""],
            ["让盘-平", 3.40, 3.00, 0.0, 0.0, 0.0, "", 0.0, 0.0, ""],
            ["让盘-负", 1.81, 2.08, 0.0, 0.0, 0.0, "", 0.0, 0.0, ""]
        ]
        df = pd.DataFrame(init_data, columns=cols)
        # v6 密钥：彻底摧毁任何形式的浏览器脏缓存
        edited_df = st.data_editor(df, hide_index=True, num_rows="fixed", disabled=cols[3:], use_container_width=True, key=f"main_v6_{water_level}")
        
        if st.button(f"执行 {water_level} 单项研判与对冲推演", type="primary", key=f"btn_m_v6_{water_level}"):
            res_df = edited_df.copy()
            
            # 【提取纯粹的一维 Numpy 数组，完全切断 Pandas 关联】
            c_odds = pd.to_numeric(res_df['初盘'], errors='coerce').values
            d_odds = pd.to_numeric(res_df['临场'], errors='coerce').values
            
            # 【暴力数学矩阵运算】
            biao_c = calc_pure_prob_array(c_odds[0:3])
            rang_c = calc_pure_prob_array(c_odds[3:6])
            biao_d = calc_pure_prob_array(d_odds[0:3])
            rang_d = calc_pure_prob_array(d_odds[3:6])
            
            # 直接赋值完整的列，物理上免疫任何赋值报错
            res_df['初概率'] = np.concatenate([biao_c, rang_c])
            res_df['临概率'] = np.concatenate([biao_d, rang_d])
            res_df['动量(Delta)'] = np.round(res_df['临概率'].values - res_df['初概率'].values, 4)
            
            # 填充 NaN 为 0，防止后续 np.where 报错
            delta_vals = res_df['动量(Delta)'].fillna(0).values
            
            res_df['七阶热度测算'] = np.where(delta_vals >= 0.03, "🌋 极限防范",
                                        np.where(delta_vals >= 0.02, "🔥 显著设防",
                                        np.where(delta_vals >= 0.008, "🟡 温和流入",
                                        np.where(delta_vals <= -0.03, "🧊 极限抛弃",
                                        np.where(delta_vals <= -0.02, "📉 显著看衰", 
                                        np.where(delta_vals <= -0.008, "↘️ 资金流出", "⚪ 随机噪音"))))))
            
            res_df['理论应有赔率'] = c_odds
            res_df['净抽水偏离'] = np.round(d_odds - c_odds, 4)
            dev_vals = res_df['净抽水偏离'].fillna(0).values
            
            res_df['🎯 终极单项研判 (时空双杀)'] = np.where(
                (delta_vals >= 0.015) & (dev_vals <= 0), "✅ 黄金共振 (时空双杀，闭眼上)",
            np.where(
                (delta_vals <= -0.015) & (dev_vals >= 0), "🧊 真实抛弃 (时空双杀，坚决规避)",
            np.where(
                (delta_vals >= 0.01) & (dev_vals > 0), "☠️ 虚假诱导防范 (升水造热)", 
            np.where(
                (delta_vals <= -0.01) & (dev_vals < 0), "🕸️ 静态诱网 (深水设伏)", 
            np.where(
                (delta_vals >= 0.02) & (dev_vals < 0), "🩸 真实暴击防范 (剥削极狠)", 
            np.where(
                (delta_vals <= -0.02) & (dev_vals > 0), "📈 真实升水抛弃", "⚪ 体系平衡 (伪装平稳)"))))))

            # 关键修复：使用 .map 而不是 .applymap
            styled = res_df.style.map(highlight_alerts, subset=['七阶热度测算', '🎯 终极单项研判 (时空双杀)'])
            st.dataframe(styled, hide_index=True, use_container_width=True)
            
            st.markdown("### ⚔️ 欧亚剪刀差极值深度研判 (主客双向解析)")
            # 安全防呆运算大盘返还率
            biao_c_odds = c_odds[0:3]
            if not np.isnan(biao_c_odds).any() and not (biao_c_odds == 0).any():
                return_rate_biao = round(1.0 / np.sum(1.0 / biao_c_odds), 4)
            else:
                return_rate_biao = 0.0
            
            delta_home_std = delta_vals[0] if len(delta_vals) > 0 else 0
            delta_home_hcp = (delta_vals[3] + delta_vals[4]) if len(delta_vals) > 5 else 0
            gap_home = round(delta_home_std - delta_home_hcp, 4)
            
            delta_away_std = (delta_vals[1] + delta_vals[2]) if len(delta_vals) > 2 else 0
            delta_away_hcp = delta_vals[5] if len(delta_vals) > 5 else 0
            gap_away = round(delta_away_std - delta_away_hcp, 4)
            
            st.info(f"📊 标盘大盘基础返还率： **{return_rate_biao}**")
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### ⚔️ 主队【让球方】阵营流速")
                st.metric("主队剪刀差净值", f"{gap_home:.4f}")
                if abs(gap_home) > 0.01:
                    st.error("🚨 严重背离：主队欧亚流速撕裂！存在深层诱导或阻盘。")
                else:
                    st.success("✅ 欧亚流速一致：主队资金自洽，无异常。")
                    
            with col2:
                st.markdown("#### 🛡️ 客队【受让方】阵营流速")
                st.metric("客队剪刀差净值", f"{gap_away:.4f}")
                if abs(gap_away) > 0.01:
                    st.error("🚨 严重背离：客队欧亚流速撕裂！极度防备下盘爆冷！")
                else:
                    st.success("✅ 欧亚流速一致：客队下盘资金自洽，无异常。")

    with tab1: render_main_handicap_ui("浅水区")
    with tab2: render_main_handicap_ui("中水区")
    with tab3: render_main_handicap_ui("深水区")

# ================= 5. 模块二：进球数风控 (同样采用无情数组灌装) =================
elif active_module == "⚽ 模块二：进球数多维风控 (包揽进球数的浅中深)":
    st.header("⚽ 进球数与大小球全维透视模块")
    tab1, tab2, tab3 = st.tabs(["🟢 浅水区 (进球数)", "🟡 中水区 (进球数)", "🔴 深水区 (进球数)"])

    def render_goals_ui(water_level):
        st.markdown(f"### {water_level} 赔率实时追踪矩阵")
        goals_data = {
            "玩法选项": ["0球", "1球", "2球", "3球", "4球", "5球", "6球", "7+球", "大球", "小球"],
            "初盘(C)": [15.0, 5.5, 3.6, 3.45, 4.9, 8.25, 15.0, 22.0, 0.65, 1.75],
            "T-60(J)": [None]*10, 
            "临场(D)": [15.5, 5.9, 3.8, 3.10, 4.7, 8.50, 16.0, 24.0, 0.50, 1.15]
        }
        df_input = pd.DataFrame(goals_data)
        col_ext1, col_ext2 = st.columns(2)
        with col_ext1:
            h_handicap = st.number_input(f"【外部变量】主队亚指让球 ({water_level})", value=-0.75, step=0.25, key=f"ext_v6_{water_level}")
        
        st.caption("注：没空看盘时 T-60(J) 列可直接留空！系统将静默 L 列雷达，绝对不影响动量和EV。")
        edited_df = st.data_editor(df_input, hide_index=True, num_rows="fixed", use_container_width=True, key=f"goal_v6_{water_level}")
        
        if st.button(f"执行 {water_level} 深度风控扫描", type="primary", key=f"btn_g_v6_{water_level}"):
            res_df = edited_df.copy()
            
            # 【直接提取底层数字列，摧毁一切 Pandas 关联】
            c_odds = pd.to_numeric(res_df['初盘(C)'], errors='coerce').values
            j_odds = pd.to_numeric(res_df['T-60(J)'], errors='coerce').values
            d_odds = pd.to_numeric(res_df['临场(D)'], errors='coerce').values
            
            c_7 = calc_pure_prob_array(c_odds[0:8])
            c_ou = calc_pure_prob_array(c_odds[8:10])
            j_7 = calc_pure_prob_array(j_odds[0:8])
            j_ou = calc_pure_prob_array(j_odds[8:10])
            d_7 = calc_pure_prob_array(d_odds[0:8])
            d_ou = calc_pure_prob_array(d_odds[8:10])
            
            # 完整灌入，神仙也报不了错
            res_df['初概率'] = np.concatenate([c_7, c_ou])
            res_df['J概率'] = np.concatenate([j_7, j_ou])
            res_df['临概率'] = np.concatenate([d_7, d_ou])
            
            res_df['总动量(Delta)'] = np.round(res_df['临概率'].values - res_df['初概率'].values, 4)
            res_df['期望值(EV)'] = np.round(res_df['初概率'].values * d_odds - 1, 4)
            res_df['加速度(V-Delta)'] = np.round(res_df['临概率'].values - res_df['J概率'].values, 4)
            
            # 填充 NaN 避免后续雷达函数报错
            res_df['总动量(Delta)'] = res_df['总动量(Delta)'].fillna(0)
            res_df['期望值(EV)'] = res_df['期望值(EV)'].fillna(0)
            res_df['加速度(V-Delta)'] = res_df['加速度(V-Delta)'].fillna(0)
            
            res_df = generate_goal_radars(res_df, z2, z3, v_limit)
            
            # 使用 .map
            styled = res_df[['玩法选项', '初盘(C)', '临场(D)', '总动量(Delta)', '期望值(EV)', '加速度(V-Delta)', '动量雷达 (G列)', 'EV价值仪 (H列)', '防伪验证 (I列)', '主力狙击 (L列)']].style.map(highlight_alerts, subset=['动量雷达 (G列)', 'EV价值仪 (H列)', '防伪验证 (I列)', '主力狙击 (L列)'])
            st.dataframe(styled, hide_index=True, use_container_width=True)
            
            st.markdown("### 📐 静态底座 X 光透视分析")
            if not np.isnan(c_7).all():
                try:
                    even_prob = round(float(np.nansum(c_7[[0,2,4,6]])), 4)
                    odd_prob = round(float(np.nansum(c_7[[1,3,5,7]])), 4)
                    
                    if abs(h_handicap) <= 0.25: core_goals = "0球, 1球, 2球"
                    elif abs(h_handicap) <= 0.75: core_goals = "2球, 3球"
                    elif abs(h_handicap) <= 1.25: core_goals = "3球, 4球"
                    else: core_goals = "4球, 5+球"
                    
                    # 使用纯 numpy 获取最小值索引
                    static_min_odds_index = np.nanargmin(c_odds[0:8])
                    static_highest_prob_goal = res_df['玩法选项'].values[static_min_odds_index]
                    match_status = "✅ 亚欧完美共振" if static_highest_prob_goal[0] in core_goals else "🚨 严重逻辑背离"
                    
                    b_col1, b_col2, b_col3 = st.columns(3)
                    b_col1.info(f"⚖️ 奇偶比 -> 偶数: {even_prob} | 奇数: {odd_prob}")
                    b_col2.info(f"🎯 亚指推演核心区 -> {core_goals}")
                    b_col3.info(f"🗺️ 交叉共振 -> {match_status}")
                except Exception:
                    pass

    with tab1: render_goals_ui("浅水区")
    with tab2: render_goals_ui("中水区")
    with tab3: render_goals_ui("深水区")

# ================= 6. 模块三：高级工具 (保持完美运转状态) =================
elif active_module == "🎫 模块三：体彩高阶工具 (DC矩阵 / EV切片器)":
    st.header("🎫 高阶价值提纯与转换矩阵")
    tab1, tab2 = st.tabs(["🧮 DC 进球双泊松矩阵", "✂️ 体彩 EV 价值切片器"])
    
    with tab1:
        st.markdown("### ⚙️ 参数设置")
        col1, col2, col3 = st.columns(3)
        total_goals = col1.number_input("进球盘 (大小球)", value=2.50, step=0.25)
        handicap = col2.number_input("让球盘 (主队亚指)", value=-0.50, step=0.25)
        rho = col3.number_input("DC依赖系数 (ρ, 默认-0.15)", value=-0.15, step=0.01)
        
        xg_home = (total_goals - handicap) / 2
        xg_away = (total_goals + handicap) / 2
        
        st.markdown("### 🧮 计算得出 预期进球数 (xG)")
        c1, c2 = st.columns(2)
        c1.metric("主队预期进球 (xG)", f"{xg_home:.4f}")
        c2.metric("客队预期进球 (xG)", f"{xg_away:.4f}")
        
        if xg_home < 0 or xg_away < 0:
            st.error("⚠️ 预期进球为负数，请检查盘口！")
        else:
            df_matrix, p_hw2, p_hw1, p_draw, p_au = dixon_coles_full_matrix(xg_home, xg_away, rho)
            st.markdown("### 📊 核心赛果概率提纯")
            rc1, rc2, rc3, rc4 = st.columns(4)
            rc1.metric("DC 大胜概率 (赢2球+)", f"{p_hw2:.4f}")
            rc2.metric("DC 恰好赢1球概率", f"{p_hw1:.4f}")
            rc3.metric("DC 平局概率", f"{p_draw:.4f}")
            rc4.metric("DC 客队不败概率", f"{p_au:.4f}")
            
            st.markdown("### 🥅 DC 双泊松进球落点矩阵 (0-7+)")
            st.dataframe(df_matrix.style.format("{:.4f}"), use_container_width=True)

    with tab2:
        st.markdown("### ✂️ 国彩官方赔率 vs 国际纯净概率套利测算")
        ev_data = {
            "投注项": ["胜", "平", "负", "让胜", "让平", "让负"],
            "国彩官方赔率": [1.60, 3.45, 4.35, 2.90, 3.45, 2.02],
            "国际纯净概率": [0.5610, 0.2450, 0.1940, 0.2780, 0.2950, 0.4270]
        }
        df_ev = pd.DataFrame(ev_data)
        edited_ev = st.data_editor(df_ev, hide_index=True, use_container_width=True, key="ev_v6")
        
        if st.button("计算体彩绝对 EV"):
            edited_ev['真实数学 EV'] = (edited_ev['国彩官方赔率'] * edited_ev['国际纯净概率'] - 1).round(4)
            edited_ev['决策定性滤镜'] = np.where(edited_ev['真实数学 EV'] > 0, "🌟 绝对正价值漏洞 (稳赚，强烈推荐！)", 
                                       np.where(edited_ev['真实数学 EV'] >= -0.05, "🟡 低损耗对冲项", "🩸 抽水黑洞 (极度亏损，拒绝买入)"))
            styled = edited_ev.style.map(highlight_alerts, subset=['决策定性滤镜'])
            st.dataframe(styled, hide_index=True, use_container_width=True)
