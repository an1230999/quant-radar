import streamlit as st
import pandas as pd
import numpy as np

# ================= 1. 全局配置与UI优化 =================
st.set_page_config(page_title="FX2 量化对冲终端", layout="wide", page_icon="🏦")

# 自定义CSS，让表格和界面更紧凑专业
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

# ================= 2. 核心数学引擎 (锁死 4 位小数精度) =================
# 纯净概率归一化引擎
def calc_pure_prob(odds_series):
    # 将 0 或空值替换为无穷大，避免除以零报错
    safe_odds = pd.to_numeric(odds_series, errors='coerce').fillna(np.inf)
    safe_odds = safe_odds.replace(0, np.inf)
    raw_prob = 1 / safe_odds
    return (raw_prob / raw_prob.sum()).round(4)

# 雷达防伪验证引擎 (完全复刻 Excel 的 G, H, I, L 列，不缩水)
def generate_goal_radars(df, z2, z3, v_limit):
    # G列：动量雷达扫描仪
    df['动量雷达 (G列)'] = np.where(df['总动量(Delta)'] >= z2 * 2, "🌋 极度过热",
                          np.where(df['总动量(Delta)'] >= z2, "🚨 史诗重防",
                          np.where(df['总动量(Delta)'] >= z3, "🔥 首席主防",
                          np.where(df['总动量(Delta)'] <= -z2 * 2, "🕳️ 极度冰封",
                          np.where(df['总动量(Delta)'] <= -z3, "🧊 极限绞杀", "⚪ 边缘震荡")))))
    
    # H列：EV 价值分级仪
    df['EV价值仪 (H列)'] = np.where(df['期望值(EV)'] >= -0.10, "🌟 绝对正价值",
                          np.where(df['期望值(EV)'] >= -0.15, "🟢 极度高潜",
                          np.where(df['期望值(EV)'] <= -0.25, "🩸 抽水深渊",
                          np.where(df['期望值(EV)'] <= -0.20, "🚨 杀猪预警", "🟡 合理磨损"))))
    
    # I列：母子集防伪验证
    df['防伪验证 (I列)'] = np.where((df['总动量(Delta)'] >= z2 * 1.5) & (df['期望值(EV)'] <= -0.25), "🩸 嗜血诱导 (100%杀猪盘)",
                          np.where((df['总动量(Delta)'] >= z3) & (df['总动量(Delta)'] < z2 * 1.5) & (df['期望值(EV)'] <= -0.08) & (df['期望值(EV)'] >= -0.25), "🎯 精确制导 (核心真实)",
                          np.where((df['总动量(Delta)'] <= -z3) & (df['期望值(EV)'] > 0), "☠️ 淬毒诱饵 (弃防)", "")))
    
    # L列：加速度主力雷达
    df['主力狙击 (L列)'] = np.where(df['加速度(V-Delta)'] >= v_limit, "⚡ 绝杀爆发",
                          np.where(df['加速度(V-Delta)'] <= -v_limit, "🩸 极速撤离", "⚪ 匀速平稳"))
    return df

# ================= 3. 侧边栏：三大核心模块切换 =================
st.sidebar.title("🧭 系统矩阵控制台")
active_module = st.sidebar.radio("=== 核心风控模块 ===", [
    "⚔️ 模块一：欧亚大盘体系 (标盘/让球)",
    "⚽ 模块二：进球数多维风控 (球数/大小)",
    "🎫 模块三：体彩高阶工具 (DC/EV切片)"
])

st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ 动态阈值微调")
z2 = st.sidebar.number_input("宏观红线 (Z2)", value=0.0120, format="%.4f")
z3 = st.sidebar.number_input("显著防线 (Z3)", value=0.0080, format="%.4f")
v_limit = st.sidebar.number_input("极速加速度", value=0.0050, format="%.4f")

# ================= 4. 模块一：欧亚大盘体系 (浅/中/深水区) =================
if active_module == "⚔️ 模块一：欧亚大盘体系 (标盘/让球)":
    st.header("⚔️ 欧亚大盘体系分析模块")
    tab1, tab2, tab3 = st.tabs(["🟢 浅水区", "🟡 中水区", "🔴 深水区"])
    
    def render_main_handicap_ui(water_level):
        st.markdown(f"### {water_level} 数据录入矩阵")
        
        # 构建与 Excel 完美对应的数据列
        cols = ["玩法选项", "初盘赔率", "临场赔率", "初盘理论概率", "临场理论概率", "真实动量(Delta)", "七阶热度测算", "时空双盲对冲", "理论应有赔率", "净抽水偏离", "终极滤镜"]
        init_data = [
            ["标盘-胜", 1.78, 1.58, 0.0, 0.0, 0.0, "", "", 0.0, 0.0, ""],
            ["标盘-平", 3.22, 3.60, 0.0, 0.0, 0.0, "", "", 0.0, 0.0, ""],
            ["标盘-负", 3.90, 4.58, 0.0, 0.0, 0.0, "", "", 0.0, 0.0, ""],
            ["让盘-胜", 3.55, 3.18, 0.0, 0.0, 0.0, "", "", 0.0, 0.0, ""],
            ["让盘-平", 3.40, 3.00, 0.0, 0.0, 0.0, "", "", 0.0, 0.0, ""],
            ["让盘-负", 1.81, 2.08, 0.0, 0.0, 0.0, "", "", 0.0, 0.0, ""]
        ]
        df = pd.DataFrame(init_data, columns=cols)
        
        # 用户在网页直接填写前三列
        edited_df = st.data_editor(df, hide_index=True, disabled=cols[3:], use_container_width=True)
        
        if st.button(f"执行 {water_level} 全盘推演", type="primary", key=f"btn_{water_level}"):
            # 剥离标盘与让盘独立计算归一化
            biao_c = calc_pure_prob(edited_df.loc[0:2, '初盘赔率'])
            biao_d = calc_pure_prob(edited_df.loc[0:2, '临场赔率'])
            rang_c = calc_pure_prob(edited_df.loc[3:5, '初盘赔率'])
            rang_d = calc_pure_prob(edited_df.loc[3:5, '临场赔率'])
            
            edited_df.loc[0:2, '初盘理论概率'] = biao_c.values
            edited_df.loc[0:2, '临场理论概率'] = biao_d.values
            edited_df.loc[3:5, '初盘理论概率'] = rang_c.values
            edited_df.loc[3:5, '临场理论概率'] = rang_d.values
            
            edited_df['真实动量(Delta)'] = (edited_df['临场理论概率'] - edited_df['初盘理论概率']).round(4)
            
            # 计算大盘返还率及剪刀差
            return_rate_biao = (1 / (1/edited_df.loc[0, '初盘赔率'] + 1/edited_df.loc[1, '初盘赔率'] + 1/edited_df.loc[2, '初盘赔率'])).round(4)
            delta_win = edited_df.loc[0, '真实动量(Delta)']
            delta_h_win = edited_df.loc[3, '真实动量(Delta)']
            scissor_gap = abs(delta_win - delta_h_win).round(4)
            
            st.success("运算完成！底层数据已更新，剪刀差预警已激活。")
            st.dataframe(edited_df, hide_index=True, use_container_width=True)
            
            # 底部对冲结论面板
            st.markdown("### ⚔️ 欧亚剪刀差极值深度研判")
            col1, col2, col3 = st.columns(3)
            col1.metric("标盘初盘返还率", return_rate_biao)
            col2.metric("欧亚剪刀差净值", scissor_gap)
            if scissor_gap > 0.01:
                col3.error("🚨 严重逻辑背离 (欧亚流速撕裂)")
            else:
                col3.success("✅ 欧亚流速一致")

    with tab1: render_main_handicap_ui("浅水区")
    with tab2: render_main_handicap_ui("中水区")
    with tab3: render_main_handicap_ui("深水区")

# ================= 5. 模块二：进球数多维风控 (浅/中/深水区) =================
elif active_module == "⚽ 模块二：进球数多维风控 (球数/大小)":
    st.header("⚽ 进球数与大小球全维透视模块")
    tab1, tab2, tab3 = st.tabs(["🟢 浅水区 (球数)", "🟡 中水区 (球数)", "🔴 深水区 (球数)"])

    def render_goals_ui(water_level):
        st.markdown(f"### {water_level} 赔率实时追踪矩阵")
        
        # 构建进球数基础框架
        goals_data = {
            "玩法选项": ["0球", "1球", "2球", "3球", "4球", "5球", "6球", "7+球", "大球", "小球"],
            "初盘(C)": [15.0, 5.5, 3.6, 3.45, 4.9, 8.25, 15.0, 22.0, 0.65, 1.75],
            "T-60(J)": [15.0, 5.6, 3.7, 3.20, 4.8, 8.30, 15.5, 23.0, 0.60, 1.60],
            "临场(D)": [15.5, 5.9, 3.8, 3.10, 4.7, 8.50, 16.0, 24.0, 0.50, 1.15]
        }
        df_input = pd.DataFrame(goals_data)
        
        # 外部变量控制区
        col_ext1, col_ext2 = st.columns(2)
        with col_ext1:
            h_handicap = st.number_input(f"【外部变量】主队亚指让球 ({water_level})", value=-0.75, step=0.25, key=f"ext_{water_level}")
        
        edited_df = st.data_editor(df_input, hide_index=True, use_container_width=True, key=f"df_{water_level}")
        
        if st.button(f"执行 {water_level} 深度扫描", type="primary", key=f"btn_g_{water_level}"):
            df = edited_df.copy()
            
            # 分解 0-7+ (0至7行) 和 大小球 (8至9行) 独立归一化计算
            prob_c_7 = calc_pure_prob(df.loc[0:7, '初盘(C)'])
            prob_j_7 = calc_pure_prob(df.loc[0:7, 'T-60(J)'])
            prob_d_7 = calc_pure_prob(df.loc[0:7, '临场(D)'])
            
            # 写入结果计算核心列
            df['总动量(Delta)'] = 0.0
            df['期望值(EV)'] = 0.0
            df['加速度(V-Delta)'] = 0.0
            
            df.loc[0:7, '总动量(Delta)'] = (prob_d_7 - prob_c_7).round(4)
            df.loc[0:7, '期望值(EV)'] = (prob_c_7 * df.loc[0:7, '临场(D)'] - 1).round(4)
            df.loc[0:7, '加速度(V-Delta)'] = (prob_d_7 - prob_j_7).round(4)
            
            # 运行防伪雷达引擎
            df = generate_goal_radars(df, z2, z3, v_limit)
            
            # 渲染高亮表格
            def highlight_alerts(val):
                if isinstance(val, str) and ('🩸' in val or '☠️' in val or '🚨' in val):
                    return 'background-color: rgba(255, 0, 0, 0.2); color: #ffcccc;'
                elif isinstance(val, str) and ('🎯' in val or '⚡' in val or '🌟' in val):
                    return 'background-color: rgba(0, 255, 0, 0.2); color: #ccffcc;'
                return ''
            
            st.dataframe(df.style.applymap(highlight_alerts, subset=['动量雷达 (G列)', 'EV价值仪 (H列)', '防伪验证 (I列)', '主力狙击 (L列)']), hide_index=True, use_container_width=True)
            
            # ================= 底座结构分析面板 (奇偶与交叉映射) =================
            st.markdown("### 📐 静态底座 X 光透视分析")
            
            # 提取 0-7+ 的初盘概率算奇偶比
            even_prob = (prob_c_7.iloc[[0,2,4,6]].sum()).round(4)
            odd_prob = (prob_c_7.iloc[[1,3,5,7]].sum()).round(4)
            
            # 亚指映射逻辑
            if abs(h_handicap) <= 0.25: core_goals = "0球, 1球, 2球"
            elif abs(h_handicap) <= 0.75: core_goals = "2球, 3球"
            elif abs(h_handicap) <= 1.25: core_goals = "3球, 4球"
            else: core_goals = "4球, 5+球"
            
            static_min_odds_index = df.loc[0:7, '初盘(C)'].idxmin()
            static_highest_prob_goal = df.loc[static_min_odds_index, '玩法选项']
            
            match_status = "✅ 亚欧完美共振" if str(static_highest_prob_goal[0]) in core_goals else "🚨 严重逻辑背离"
            
            b_col1, b_col2, b_col3 = st.columns(3)
            b_col1.info(f"⚖️ 奇偶结构比 -> 偶数: {even_prob} | 奇数: {odd_prob}")
            b_col2.info(f"🎯 亚指推演核心区 -> {core_goals}")
            b_col3.info(f"🗺️ 交叉防伪雷达 -> {match_status}")

    with tab1: render_goals_ui("浅水区")
    with tab2: render_goals_ui("中水区")
    with tab3: render_goals_ui("深水区")

# ================= 6. 模块三：体彩高阶工具 (DC/EV) =================
elif active_module == "🎫 模块三：体彩高阶工具 (DC/EV切片)":
    st.header("🎫 高阶价值提纯与转换矩阵")
    tab1, tab2 = st.tabs(["✂️ 体彩 EV 价值切片器", "🧮 DC 进球概率矩阵转化"])
    
    with tab1:
        st.markdown("### ✂️ 国彩官方赔率 vs 国际纯净概率套利测算")
        ev_data = {
            "投注项": ["胜", "平", "负", "让胜", "让平", "让负"],
            "国彩官方赔率": [1.60, 3.45, 4.35, 2.90, 3.45, 2.02],
            "国际纯净概率": [0.5610, 0.2450, 0.1940, 0.2780, 0.2950, 0.4270]
        }
        df_ev = pd.DataFrame(ev_data)
        edited_ev = st.data_editor(df_ev, hide_index=True, use_container_width=True)
        
        if st.button("计算体彩绝对 EV"):
            edited_ev['真实 EV'] = (edited_ev['国彩官方赔率'] * edited_ev['国际纯净概率'] - 1).round(4)
            edited_ev['滤镜结论'] = np.where(edited_ev['真实 EV'] > 0, "🌟 绝对漏洞可打", "🩸 强力抽水规避")
            st.dataframe(edited_ev, hide_index=True, use_container_width=True)
            
    with tab2:
        st.markdown("### 🧮 DC (Double Chance) 进球基础概率映射矩阵")
        st.caption("此处预留完整 DC 双重概率映射数据流，可直接将进球数概率反向倒推至具体比分落点。")
        # DC 占位表格，完美对齐 Excel DC 矩阵排版
        dc_data = pd.DataFrame(np.zeros((6, 6)), columns=["客进0", "客进1", "客进2", "客进3", "客进4", "客进5+"], index=["主进0", "主进1", "主进2", "主进3", "主进4", "主进5+"])
        st.data_editor(dc_data, use_container_width=True)
