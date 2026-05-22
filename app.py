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

# ================= 2. 核心数学引擎 =================
def calc_pure_prob(odds_series):
    safe_odds = pd.to_numeric(odds_series, errors='coerce')
    if safe_odds.isna().any() or (safe_odds == 0).any():
        return pd.Series([np.nan] * len(odds_series), index=odds_series.index)
    raw_prob = 1 / safe_odds
    sum_prob = raw_prob.sum()
    return (raw_prob / sum_prob).round(4)

def generate_goal_radars(df, z2, z3, v_limit):
    df['动量雷达 (G列)'] = np.where(df['总动量(Delta)'] >= z2 * 2, "🌋 极度过热",
                          np.where(df['总动量(Delta)'] >= z2, "🚨 史诗重防",
                          np.where(df['总动量(Delta)'] >= z3, "🔥 首席主防",
                          np.where(df['总动量(Delta)'] <= -z2 * 2, "🕳️ 极度冰封",
                          np.where(df['总动量(Delta)'] <= -z3, "🧊 极限绞杀", "⚪ 边缘震荡")))))
    
    df['EV价值仪 (H列)'] = np.where(df['期望值(EV)'] >= -0.10, "🌟 绝对正价值",
                          np.where(df['期望值(EV)'] >= -0.15, "🟢 极度高潜",
                          np.where(df['期望值(EV)'] <= -0.25, "🩸 抽水深渊",
                          np.where(df['期望值(EV)'] <= -0.20, "🚨 杀猪预警", "🟡 合理磨损"))))
    
    df['防伪验证 (I列)'] = np.where((df['总动量(Delta)'] >= z2 * 1.5) & (df['期望值(EV)'] <= -0.25), "🩸 嗜血诱导 (100%杀猪盘)",
                          np.where((df['总动量(Delta)'] >= z3) & (df['总动量(Delta)'] < z2 * 1.5) & (df['期望值(EV)'] <= -0.08) & (df['期望值(EV)'] >= -0.25), "🎯 精确制导 (核心真实)",
                          np.where((df['总动量(Delta)'] <= -z3) & (df['期望值(EV)'] > 0), "☠️ 淬毒诱饵 (弃防)", "")))
    
    df['主力狙击 (L列)'] = np.where(pd.isna(df['加速度(V-Delta)']), "➖ 无T-60不计算",
                          np.where(df['加速度(V-Delta)'] >= v_limit, "⚡ 绝杀爆发",
                          np.where(df['加速度(V-Delta)'] <= -v_limit, "🩸 极速撤离", "⚪ 匀速平稳")))
    return df

def poisson_pmf_array(lam, max_k):
    pmf = np.zeros(max_k + 1)
    if lam <= 0:
        pmf[0] = 1.0
        return pmf
    for k in range(max_k + 1):
        pmf[k] = math.exp(-lam) * (lam**k) / math.factorial(k)
    return pmf

def dixon_coles_full_matrix(lambda_, mu_, rho_):
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
        if '🩸' in val or '☠️' in val or '🚨' in val or '🕳️' in val or '🧊' in val or '📉' in val:
            return 'background-color: rgba(255, 0, 0, 0.2); color: #ffcccc;'
        elif '🎯' in val or '⚡' in val or '🌟' in val or '🟢' in val or '🔥' in val or '🌋' in val or '📈' in val or '✅' in val:
            return 'background-color: rgba(0, 255, 0, 0.2); color: #ccffcc;'
        elif '➖' in val:
            return 'color: #888888;'
    return ''

# ================= 4. 模块一：欧亚大盘 (修复全列拼接赋值) =================
if active_module == "⚔️ 模块一：欧亚大盘体系 (包揽标盘让盘的浅中深)":
    st.header("⚔️ 欧亚大盘体系分析模块")
    tab1, tab2, tab3 = st.tabs(["🟢 浅水区 (标/让)", "🟡 中水区 (标/让)", "🔴 深水区 (标/让)"])
    
    def render_main_handicap_ui(water_level):
        st.markdown(f"### {water_level} 数据录入矩阵")
        cols = ["玩法选项", "初盘", "临场", "初概率", "临概率", "动量(Delta)", "七阶热度测算", "理论应有赔率", "净抽水偏离", "终极防伪滤镜", "时空双盲对冲"]
        init_data = [
            ["标盘-胜", 1.78, 1.58, 0.0, 0.0, 0.0, "", 0.0, 0.0, "", ""],
            ["标盘-平", 3.22, 3.60, 0.0, 0.0, 0.0, "", 0.0, 0.0, "", ""],
            ["标盘-负", 3.90, 4.58, 0.0, 0.0, 0.0, "", 0.0, 0.0, "", ""],
            ["让盘-胜", 3.55, 3.18, 0.0, 0.0, 0.0, "", 0.0, 0.0, "", ""],
            ["让盘-平", 3.40, 3.00, 0.0, 0.0, 0.0, "", 0.0, 0.0, "", ""],
            ["让盘-负", 1.81, 2.08, 0.0, 0.0, 0.0, "", 0.0, 0.0, "", ""]
        ]
        df = pd.DataFrame(init_data, columns=cols)
        edited_df = st.data_editor(df, hide_index=True, disabled=cols[3:], use_container_width=True, key=f"e_{water_level}")
        
        if st.button(f"执行 {water_level} 单项研判与对冲推演", type="primary", key=f"btn_{water_level}"):
            # 核心修正：计算切片后，直接用 concat 拼接成整列，彻底规避 loc 赋值报错
            biao_c = calc_pure_prob(edited_df.loc[0:2, '初盘'])
            biao_d = calc_pure_prob(edited_df.loc[0:2, '临场'])
            rang_c = calc_pure_prob(edited_df.loc[3:5, '初盘'])
            rang_d = calc_pure_prob(edited_df.loc[3:5, '临场'])
            
            edited_df['初概率'] = pd.concat([biao_c, rang_c])
            edited_df['临概率'] = pd.concat([biao_d, rang_d])
            
            edited_df['动量(Delta)'] = (edited_df['临概率'] - edited_df['初概率']).round(4)
            
            edited_df['七阶热度测算'] = np.where(edited_df['动量(Delta)'] >= 0.03, "🌋 极限防范",
                                        np.where(edited_df['动量(Delta)'] >= 0.02, "🔥 显著设防",
                                        np.where(edited_df['动量(Delta)'] >= 0.008, "🟡 温和流入",
                                        np.where(edited_df['动量(Delta)'] <= -0.03, "🧊 极限抛弃",
                                        np.where(edited_df['动量(Delta)'] <= -0.02, "📉 显著看衰", 
                                        np.where(edited_df['动量(Delta)'] <= -0.008, "↘️ 资金流出", "⚪ 随机噪音"))))))
            
            edited_df['理论应有赔率'] = edited_df['初盘']
            edited_df['净抽水偏离'] = (edited_df['临场'] - edited_df['理论应有赔率']).round(4)
            
            edited_df['终极防伪滤镜'] = np.where((edited_df['动量(Delta)'] >= 0.02) & (edited_df['净抽水偏离'] < 0), "🩸 真实暴击防范 (剥削极狠)",
                                       np.where((edited_df['动量(Delta)'] <= -0.02) & (edited_df['净抽水偏离'] > 0), "📈 真实升水抛弃",
                                       np.where((edited_df['动量(Delta)'] >= 0.02) & (edited_df['净抽水偏离'] > 0), "☠️ 虚假诱导防范 (造热)", "⚪ 体系平衡")))

            edited_df['时空双盲对冲'] = np.where(
                (edited_df['动量(Delta)'] >= 0.015) & (edited_df['净抽水偏离'] <= 0), "✅ 黄金共振 (时空双杀，闭眼上)",
            np.where(
                (edited_df['动量(Delta)'] <= -0.015) & (edited_df['净抽水偏离'] >= 0), "🧊 真实抛弃 (时空双杀，坚决规避)",
            np.where(
                (edited_df['动量(Delta)'] >= 0.01) & (edited_df['净抽水偏离'] > 0), "☠️ 虚假诱导防范", 
            np.where(
                (edited_df['动量(Delta)'] <= -0.01) & (edited_df['净抽水偏离'] < 0), "🕸️ 静态诱网 (深水设伏)", "⚪ 伪装平稳"))))

            st.dataframe(edited_df.style.applymap(highlight_alerts, subset=['七阶热度测算', '终极防伪滤镜', '时空双盲对冲']), hide_index=True, use_container_width=True)
            
            st.markdown("### ⚔️ 欧亚剪刀差极值深度研判 (主客双向解析)")
            return_rate_biao = (1 / (1/edited_df.loc[0, '初盘'] + 1/edited_df.loc[1, '初盘'] + 1/edited_df.loc[2, '初盘'])).round(4)
            
            delta_home_std = edited_df.loc[0, '动量(Delta)']
            delta_home_hcp = edited_df.loc[3, '动量(Delta)'] + edited_df.loc[4, '动量(Delta)']
            gap_home = round(delta_home_std - delta_home_hcp, 4)
            
            delta_away_std = edited_df.loc[1, '动量(Delta)'] + edited_df.loc[2, '动量(Delta)']
            delta_away_hcp = edited_df.loc[5, '动量(Delta)']
            gap_away = round(delta_away_std - delta_away_hcp, 4)
            
            st.info(f"📊 标盘大盘基础返还率： **{return_rate_biao}**")
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### ⚔️ 主队【让球方】阵营流速")
                st.caption("公式：标胜动量 🆚 (让胜动量 + 让平动量)")
                st.metric("主队剪刀差净值", f"{gap_home:.4f}")
                if abs(gap_home) > 0.01:
                    st.error("🚨 严重背离：主队欧亚流速撕裂！存在深层诱导或阻盘。")
                else:
                    st.success("✅ 欧亚流速一致：主队资金自洽，无异常。")
                    
            with col2:
                st.markdown("#### 🛡️ 客队【受让方】阵营流速")
                st.caption("公式：(标平动量 + 标负动量) 🆚 让负动量")
                st.metric("客队剪刀差净值", f"{gap_away:.4f}")
                if abs(gap_away) > 0.01:
                    st.error("🚨 严重背离：客队欧亚流速撕裂！极度防备下盘爆冷！")
                else:
                    st.success("✅ 欧亚流速一致：客队下盘资金自洽，无异常。")

    with tab1: render_main_handicap_ui("浅水区")
    with tab2: render_main_handicap_ui("中水区")
    with tab3: render_main_handicap_ui("深水区")

# ================= 5. 模块二：进球数风控 (修复全列拼接赋值) =================
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
            h_handicap = st.number_input(f"【外部变量】主队亚指让球 ({water_level})", value=-0.75, step=0.25, key=f"ext_{water_level}")
        
        st.caption("注：没空看盘时 T-60(J) 列可直接留空！系统将静默 L 列雷达，绝对不影响动量和EV。")
        edited_df = st.data_editor(df_input, hide_index=True, use_container_width=True, key=f"df_{water_level}")
        
        if st.button(f"执行 {water_level} 深度风控扫描", type="primary", key=f"btn_g_{water_level}"):
            df = edited_df.copy()
            
            # 核心修正：全列直接拼接计算，消灭所有的切片赋值
            prob_c_7 = calc_pure_prob(df.loc[0:7, '初盘(C)'])
            prob_j_7 = calc_pure_prob(df.loc[0:7, 'T-60(J)'])
            prob_d_7 = calc_pure_prob(df.loc[0:7, '临场(D)'])
            
            prob_c_ou = calc_pure_prob(df.loc[8:9, '初盘(C)'])
            prob_j_ou = calc_pure_prob(df.loc[8:9, 'T-60(J)'])
            prob_d_ou = calc_pure_prob(df.loc[8:9, '临场(D)'])
            
            prob_c_all = pd.concat([prob_c_7, prob_c_ou])
            prob_j_all = pd.concat([prob_j_7, prob_j_ou])
            prob_d_all = pd.concat([prob_d_7, prob_d_ou])
            
            df['总动量(Delta)'] = (prob_d_all - prob_c_all).round(4)
            df['期望值(EV)'] = (prob_c_all * df['临场(D)'] - 1).round(4)
            df['加速度(V-Delta)'] = (prob_d_all - prob_j_all).round(4)
            
            df = generate_goal_radars(df, z2, z3, v_limit)
            st.dataframe(df.style.applymap(highlight_alerts, subset=['动量雷达 (G列)', 'EV价值仪 (H列)', '防伪验证 (I列)', '主力狙击 (L列)']), hide_index=True, use_container_width=True)
            
            st.markdown("### 📐 静态底座 X 光透视分析")
            if not prob_c_7.isna().all():
                even_prob = (prob_c_7.iloc[[0,2,4,6]].sum()).round(4)
                odd_prob = (prob_c_7.iloc[[1,3,5,7]].sum()).round(4)
                
                if abs(h_handicap) <= 0.25: core_goals = "0球, 1球, 2球"
                elif abs(h_handicap) <= 0.75: core_goals = "2球, 3球"
                elif abs(h_handicap) <= 1.25: core_goals = "3球, 4球"
                else: core_goals = "4球, 5+球"
                
                static_min_odds_index = df.loc[0:7, '初盘(C)'].idxmin()
                static_highest_prob_goal = df.loc[static_min_odds_index, '玩法选项']
                match_status = "✅ 亚欧完美共振" if str(static_highest_prob_goal[0]) in core_goals else "🚨 严重逻辑背离"
                
                b_col1, b_col2, b_col3 = st.columns(3)
                b_col1.info(f"⚖️ 奇偶比 -> 偶数: {even_prob} | 奇数: {odd_prob}")
                b_col2.info(f"🎯 亚指推演核心区 -> {core_goals}")
                b_col3.info(f"🗺️ 交叉共振 -> {match_status}")

    with tab1: render_goals_ui("浅水区")
    with tab2: render_goals_ui("中水区")
    with tab3: render_goals_ui("深水区")

# ================= 6. 模块三：高级工具 =================
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
        edited_ev = st.data_editor(df_ev, hide_index=True, use_container_width=True)
        
        if st.button("计算体彩绝对 EV"):
            edited_ev['真实数学 EV'] = (edited_ev['国彩官方赔率'] * edited_ev['国际纯净概率'] - 1).round(4)
            edited_ev['决策定性滤镜'] = np.where(edited_ev['真实数学 EV'] > 0, "🌟 绝对正价值漏洞 (稳赚，强烈推荐！)", 
                                       np.where(edited_ev['真实数学 EV'] >= -0.05, "🟡 低损耗对冲项", "🩸 抽水黑洞 (极度亏损，拒绝买入)"))
            st.dataframe(edited_ev, hide_index=True, use_container_width=True)
