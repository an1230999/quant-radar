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
    """彻底抛弃 Pandas切片，使用最纯粹的一维数组运算，100%免疫报错"""
    arr = np.array(arr, dtype=float)
    if np.isnan(arr).any() or (arr == 0).any():
        return np.full(len(arr), np.nan)
    raw = 1.0 / arr
    return np.round(raw / np.nansum(raw), 4)

def safe_style(df, cols):
    """防弹级样式渲染，免疫任何版本的样式报错"""
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
    try:
        if hasattr(df.style, 'map'):
            return df.style.map(highlight_alerts, subset=cols)
        else:
            return df.style.applymap(highlight_alerts, subset=cols)
    except Exception:
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

# ================= 4. 模块一：欧亚大盘 (输入与输出防弹隔离) =================
if active_module == "⚔️ 模块一：欧亚大盘体系 (包揽标盘让盘的浅中深)":
    st.header("⚔️ 欧亚大盘体系分析模块")
    tab1, tab2, tab3 = st.tabs(["🟢 浅水区 (标/让)", "🟡 中水区 (标/让)", "🔴 深水区 (标/让)"])
    
    def render_main_handicap_ui(water_level):
        st.markdown(f"### 📥 {water_level} 数据录入区")
        cols_in = ["玩法选项", "初盘", "临场"]
        init_data_1 = [
            ["标盘-胜", 1.78, 1.58], ["标盘-平", 3.22, 3.60], ["标盘-负", 3.90, 4.58],
            ["让盘-胜", 3.55, 3.18], ["让盘-平", 3.40, 3.00], ["让盘-负", 1.81, 2.08]
        ]
        df_in = pd.DataFrame(init_data_1, columns=cols_in)
        
        # 用户只看到并编辑这一个干净的小表格
        edited_1 = st.data_editor(df_in, hide_index=True, num_rows="fixed", use_container_width=True, key=f"in1_v8_{water_level}")
        
        if st.button(f"🚀 执行 {water_level} 终极研判与对冲推演", type="primary", key=f"btn1_v8_{water_level}"):
            # 绝对安全的底层提取
            opts = edited_1['玩法选项'].values
            c_odds = pd.to_numeric(edited_1['初盘'], errors='coerce').values
            d_odds = pd.to_numeric(edited_1['临场'], errors='coerce').values
            
            biao_c = calc_pure_prob_array(c_odds[0:3])
            rang_c = calc_pure_prob_array(c_odds[3:6])
            biao_d = calc_pure_prob_array(d_odds[0:3])
            rang_d = calc_pure_prob_array(d_odds[3:6])
            
            prob_c = np.concatenate([biao_c, rang_c])
            prob_d = np.concatenate([biao_d, rang_d])
            delta = np.round(prob_d - prob_c, 4)
            dev = np.round(d_odds - c_odds, 4)
            
            heat = np.where(delta >= 0.03, "🌋 极限防范",
                   np.where(delta >= 0.02, "🔥 显著设防",
                   np.where(delta >= 0.008, "🟡 温和流入",
                   np.where(delta <= -0.03, "🧊 极限抛弃",
                   np.where(delta <= -0.02, "📉 显著看衰", 
                   np.where(delta <= -0.008, "↘️ 资金流出", "⚪ 随机噪音"))))))
            
            judge = np.where((delta >= 0.015) & (dev <= 0), "✅ 黄金共振 (时空双杀，闭眼上)",
                    np.where((delta <= -0.015) & (dev >= 0), "🧊 真实抛弃 (时空双杀，坚决规避)",
                    np.where((delta >= 0.01) & (dev > 0), "☠️ 虚假诱导防范 (升水造热)", 
                    np.where((delta <= -0.01) & (dev < 0), "🕸️ 静态诱网 (深水设伏)", 
                    np.where((delta >= 0.02) & (dev < 0), "🩸 真实暴击防范 (剥削极狠)", 
                    np.where((delta <= -0.02) & (dev > 0), "📈 真实升水抛弃", "⚪ 体系平衡 (伪装平稳)"))))))
            
            # 【核心护城河】完全重新构建一张新表，从根源切断 Pandas 赋值报错
            out_df1 = pd.DataFrame({
                "玩法选项": opts, "初盘": c_odds, "临场": d_odds,
                "初概率": prob_c, "临概率": prob_d, "动量(Delta)": delta,
                "七阶热度测算": heat, "理论应有赔率": c_odds, "净抽水偏离": dev,
                "🎯 终极单项研判 (时空双杀)": judge
            })
            
            st.markdown("### 📊 终极推演雷达监控矩阵")
            st.dataframe(safe_style(out_df1, ['七阶热度测算', '🎯 终极单项研判 (时空双杀)']), hide_index=True, use_container_width=True)
            
            st.markdown("### ⚔️ 欧亚剪刀差极值深度研判 (主客双向解析)")
            biao_c_odds = c_odds[0:3]
            if not np.isnan(biao_c_odds).any() and not (biao_c_odds == 0).any():
                return_rate_biao = round(1.0 / np.sum(1.0 / biao_c_odds), 4)
            else:
                return_rate_biao = 0.0
                
            gap_home = round(delta[0] - (delta[3] + delta[4]), 4)
            gap_away = round((delta[1] + delta[2]) - delta[5], 4)
            
            st.info(f"📊 标盘大盘基础返还率： **{return_rate_biao}**")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### ⚔️ 主队【让球方】阵营流速")
                st.metric("主队剪刀差净值", f"{gap_home:.4f}")
                if abs(gap_home) > 0.01: st.error("🚨 严重背离：主队欧亚流速撕裂！存在深层诱导或阻盘。")
                else: st.success("✅ 欧亚流速一致：主队资金自洽，无异常。")
                    
            with col2:
                st.markdown("#### 🛡️ 客队【受让方】阵营流速")
                st.metric("客队剪刀差净值", f"{gap_away:.4f}")
                if abs(gap_away) > 0.01: st.error("🚨 严重背离：客队欧亚流速撕裂！极度防备下盘爆冷！")
                else: st.success("✅ 欧亚流速一致：客队下盘资金自洽，无异常。")

    with tab1: render_main_handicap_ui("浅水区")
    with tab2: render_main_handicap_ui("中水区")
    with tab3: render_main_handicap_ui("深水区")

# ================= 5. 模块二：进球数风控 (输入与输出防弹隔离) =================
elif active_module == "⚽ 模块二：进球数多维风控 (包揽进球数的浅中深)":
    st.header("⚽ 进球数与大小球全维透视模块")
    tab1, tab2, tab3 = st.tabs(["🟢 浅水区 (进球数)", "🟡 中水区 (进球数)", "🔴 深水区 (进球数)"])

    def render_goals_ui(water_level):
        st.markdown(f"### 📥 {water_level} 数据录入区")
        col_ext1, col_ext2 = st.columns(2)
        with col_ext1:
            h_handicap = st.number_input(f"【外部变量】主队亚指让球 ({water_level})", value=-0.75, step=0.25, key=f"ext_v8_{water_level}")
        st.caption("注：没空看盘时 T-60(J) 列可直接留空！系统将静默 L 列雷达，绝对不影响动量和EV。")
        
        goals_data = {
            "玩法选项": ["0球", "1球", "2球", "3球", "4球", "5球", "6球", "7+球", "大球", "小球"],
            "初盘(C)": [15.0, 5.5, 3.6, 3.45, 4.9, 8.25, 15.0, 22.0, 0.65, 1.75],
            "T-60(J)": [None]*10, 
            "临场(D)": [15.5, 5.9, 3.8, 3.10, 4.7, 8.50, 16.0, 24.0, 0.50, 1.15]
        }
        df_in2 = pd.DataFrame(goals_data)
        edited_2 = st.data_editor(df_in2, hide_index=True, num_rows="fixed", use_container_width=True, key=f"in2_v8_{water_level}")
        
        if st.button(f"🚀 执行 {water_level} 深度风控扫描", type="primary", key=f"btn2_v8_{water_level}"):
            opts = edited_2['玩法选项'].values
            c_odds = pd.to_numeric(edited_2['初盘(C)'], errors='coerce').values
            j_odds = pd.to_numeric(edited_2['T-60(J)'], errors='coerce').values
            d_odds = pd.to_numeric(edited_2['临场(D)'], errors='coerce').values
            
            c_7, c_ou = calc_pure_prob_array(c_odds[0:8]), calc_pure_prob_array(c_odds[8:10])
            j_7, j_ou = calc_pure_prob_array(j_odds[0:8]), calc_pure_prob_array(j_odds[8:10])
            d_7, d_ou = calc_pure_prob_array(d_odds[0:8]), calc_pure_prob_array(d_odds[8:10])
            
            prob_c = np.concatenate([c_7, c_ou])
            prob_j = np.concatenate([j_7, j_ou])
            prob_d = np.concatenate([d_7, d_ou])
            
            delta = np.round(prob_d - prob_c, 4)
            ev = np.round(prob_c * d_odds - 1, 4)
            v_delta = np.round(prob_d - prob_j, 4)
            
            r_g = np.where(delta >= z2 * 2, "🌋 极度过热",
                  np.where(delta >= z2, "🚨 史诗重防",
                  np.where(delta >= z3, "🔥 首席主防",
                  np.where(delta <= -z2 * 2, "🕳️ 极度冰封",
                  np.where(delta <= -z3, "🧊 极限绞杀", "⚪ 边缘震荡")))))
            
            r_h = np.where(ev >= -0.10, "🌟 绝对正价值",
                  np.where(ev >= -0.15, "🟢 极度高潜",
                  np.where(ev <= -0.25, "🩸 抽水深渊",
                  np.where(ev <= -0.20, "🚨 杀猪预警", "🟡 合理磨损"))))
            
            r_i = np.where((delta >= z2 * 1.5) & (ev <= -0.25), "🩸 嗜血诱导 (100%杀猪盘)",
                  np.where((delta >= z3) & (delta < z2 * 1.5) & (ev <= -0.08) & (ev >= -0.25), "🎯 精确制导 (核心真实)",
                  np.where((delta <= -z3) & (ev > 0), "☠️ 淬毒诱饵 (弃防)", "⚪ 体系平衡")))
            
            r_l = np.where(np.isnan(v_delta), "➖ 无T-60不计算",
                  np.where(v_delta >= v_limit, "⚡ 绝杀爆发",
                  np.where(v_delta <= -v_limit, "🩸 极速撤离", "⚪ 匀速平稳")))
            
            # 【核心护城河】建新表，物理隔离
            out_df2 = pd.DataFrame({
                "玩法选项": opts, "初盘(C)": c_odds, "临场(D)": d_odds,
                "总动量(Delta)": delta, "期望值(EV)": ev, "加速度(V-Delta)": v_delta,
                "动量雷达 (G列)": r_g, "EV价值仪 (H列)": r_h, "防伪验证 (I列)": r_i, "主力狙击 (L列)": r_l
            })
            
            st.markdown("### 📊 终极进球数扫描雷达")
            st.dataframe(safe_style(out_df2, ['动量雷达 (G列)', 'EV价值仪 (H列)', '防伪验证 (I列)', '主力狙击 (L列)']), hide_index=True, use_container_width=True)
            
            st.markdown("### 📐 静态底座 X 光透视分析")
            c_7_arr = c_odds[0:8]
            if not np.isnan(c_7_arr).all():
                try:
                    even_prob = round(float(np.nansum(c_7[[0,2,4,6]])), 4)
                    odd_prob = round(float(np.nansum(c_7[[1,3,5,7]])), 4)
                    
                    if abs(h_handicap) <= 0.25: core_goals = "0球, 1球, 2球"
                    elif abs(h_handicap) <= 0.75: core_goals = "2球, 3球"
                    elif abs(h_handicap) <= 1.25: core_goals = "3球, 4球"
                    else: core_goals = "4球, 5+球"
                    
                    min_idx = np.nanargmin(c_7_arr)
                    best_goal = opts[min_idx]
                    match_status = "✅ 亚欧完美共振" if str(best_goal[0]) in core_goals else "🚨 严重逻辑背离"
                    
                    b_col1, b_col2, b_col3 = st.columns(3)
                    b_col1.info(f"⚖️ 奇偶比 -> 偶数: {even_prob} | 奇数: {odd_prob}")
                    b_col2.info(f"🎯 亚指推演核心区 -> {core_goals}")
                    b_col3.info(f"🗺️ 交叉共振 -> {match_status}")
                except Exception:
                    pass

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
        st.markdown("### 📥 录入国彩与国际纯净概率")
        ev_data = {
            "投注项": ["胜", "平", "负", "让胜", "让平", "让负"],
            "国彩官方赔率": [1.60, 3.45, 4.35, 2.90, 3.45, 2.02],
            "国际纯净概率": [0.5610, 0.2450, 0.1940, 0.2780, 0.2950, 0.4270]
        }
        df_in3 = pd.DataFrame(ev_data)
        edited_3 = st.data_editor(df_in3, hide_index=True, num_rows="fixed", use_container_width=True, key="in3_v8")
        
        if st.button("🚀 计算体彩绝对 EV"):
            tc_odds = pd.to_numeric(edited_3['国彩官方赔率'], errors='coerce').values
            intl_prob = pd.to_numeric(edited_3['国际纯净概率'], errors='coerce').values
            ev_vals = np.round(tc_odds * intl_prob - 1, 4)
            
            judge = np.where(ev_vals > 0, "🌟 绝对正价值漏洞 (稳赚，强烈推荐！)", 
                    np.where(ev_vals >= -0.05, "🟡 低损耗对冲项", "🩸 抽水黑洞 (极度亏损，拒绝买入)"))
            
            out_df3 = pd.DataFrame({
                "投注项": edited_3['投注项'].values, "国彩官方赔率": tc_odds,
                "国际纯净概率": intl_prob, "真实数学 EV": ev_vals, "决策定性滤镜": judge
            })
            st.markdown("### 📊 体彩 EV 套利扫描矩阵")
            st.dataframe(safe_style(out_df3, ['决策定性滤镜']), hide_index=True, use_container_width=True)
