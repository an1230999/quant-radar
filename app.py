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
    .stDataFrame { font-size: 0.9rem; }
    </style>
""", unsafe_allow_html=True)

st.title("🏦 FX2 全维量化对冲终端")
st.markdown("---")

# ================= 2. 终极防弹引擎 (Numpy底层) =================
def calc_pure_prob_array(arr):
    arr = np.array(arr, dtype=float)
    if np.isnan(arr).any() or (arr == 0).any():
        return np.full(len(arr), np.nan)
    raw = 1.0 / arr
    return np.round(raw / np.nansum(raw), 4)

def safe_style(df, cols):
    def highlight_alerts(val):
        if pd.isna(val) or val == "": return ''
        if isinstance(val, str):
            if any(x in val for x in ['🩸', '☠️', '🚨', '🕳️', '🧊', '📉', '🕸️', '💣', '🔻']):
                return 'background-color: rgba(255, 0, 0, 0.2); color: #ffcccc;'
            elif any(x in val for x in ['🎯', '⚡', '🌟', '🟢', '🔥', '🌋', '📈', '✅', '🛡️', '🔺']):
                return 'background-color: rgba(0, 255, 0, 0.2); color: #ccffcc;'
            elif any(x in val for x in ['➖', '⚪', '⚠️']):
                return 'color: #888888;'
            elif any(x in val for x in ['🟡', '↗️', '↘️', '⏬']):
                return 'color: #ffd700;'
        return ''
    try:
        if hasattr(df.style, 'map'): return df.style.map(highlight_alerts, subset=cols)
        else: return df.style.applymap(highlight_alerts, subset=cols)
    except Exception: return df

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
    
    P_col = np.zeros((8, 8))
    P_col[:7, :7] = P[:7, :7]
    P_col[7, :7] = np.sum(P[7:, :7], axis=0) 
    P_col[:7, 7] = np.sum(P[:7, 7:], axis=1) 
    P_col[7, 7] = np.sum(P[7:, 7:])          
    
    # 核心：必须提前四舍五入到4位，完美对齐 Excel 的 SUMPRODUCT 底层计算
    P_col_rounded = np.round(P_col, 4)
    
    p_hw2 = np.sum(np.tril(P_col_rounded, -2))
    p_hw1 = np.sum(np.diag(P_col_rounded, -1))
    p_draw = np.sum(np.diag(P_col_rounded, 0))
    p_au = np.sum(np.triu(P_col_rounded, 0))
    
    cols = [f"客进{i}" for i in range(7)] + ["客进7+"]
    idx = [f"主进{i}" for i in range(7)] + ["主进7+"]
    return pd.DataFrame(P_col_rounded, columns=cols, index=idx), p_hw2, p_hw1, p_draw, p_au, P_col_rounded

# ================= 3. 动态多阶阈值控制台 =================
st.sidebar.title("🧭 动态参数控制台")
active_module = st.sidebar.radio("=== 核心风控三大模块 ===", [
    "⚔️ 模块一：欧亚大盘体系 (包揽浅中深)",
    "⚽ 模块二：进球数多维风控 (包揽浅中深)",
    "🎫 模块三：高阶工具 (DC矩阵/EV切片)"
])
st.sidebar.markdown("---")
z2 = st.sidebar.number_input("极限红线阈值 (Z2)", value=0.0200, format="%.4f")
z3 = st.sidebar.number_input("显著防线阈值 (Z3)", value=0.0130, format="%.4f")
z4 = st.sidebar.number_input("警戒防线阈值 (Z4)", value=0.0090, format="%.4f")
z5 = st.sidebar.number_input("温和波动阈值 (Z5)", value=0.0050, format="%.4f")
z6 = st.sidebar.number_input("高赔阻盘分水岭 (Z6)", value=999.0, format="%.1f")
v_limit = st.sidebar.number_input("T-60极速加速度", value=0.0050, format="%.4f")

# ================= 4. 模块一：欧亚大盘 (完整搭载顺流提纯器) =================
if active_module == "⚔️ 模块一：欧亚大盘体系 (包揽浅中深)":
    st.header("⚔️ 欧亚大盘体系分析模块")
    tab1, tab2, tab3 = st.tabs(["🟢 浅水区 (标/让)", "🟡 中水区 (标/让)", "🔴 深水区 (标/让)"])
    
    def render_main_handicap_ui(water_level):
        st.markdown(f"### 📥 {water_level} 数据录入区")
        col_ext1, _ = st.columns(2)
        with col_ext1:
            h_val = st.number_input(f"主队亚指让球数 (决定底层映射)", value=-1.0, step=0.25, key=f"hcp_v10_{water_level}")
            
        cols_in = ["玩法选项", "初盘", "临场"]
        init_data_1 = [
            ["标盘-胜", 2.45, 2.32], ["标盘-平", 3.20, 3.20], ["标盘-负", 2.45, 2.60],
            ["让盘-胜", 5.50, 5.30], ["让盘-平", 4.10, 4.00], ["让盘-负", 1.42, 1.45]
        ]
        df_in = pd.DataFrame(init_data_1, columns=cols_in)
        edited_1 = st.data_editor(df_in, hide_index=True, num_rows="fixed", use_container_width=True, key=f"in1_v10_{water_level}")
        
        if st.button(f"🚀 执行 {water_level} 全维精算", type="primary", key=f"btn1_v10_{water_level}"):
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
            
            ret_c = round(1.0 / np.nansum(1.0 / c_odds[0:3]), 4) if not np.isnan(c_odds[0:3]).any() else 1.0
            ret_d = round(1.0 / np.nansum(1.0 / d_odds[0:3]), 4) if not np.isnan(d_odds[0:3]).any() else 1.0
            theo_odds = np.round(c_odds * (ret_d / ret_c), 4) if ret_c != 0 else c_odds
            dev = np.round(d_odds - theo_odds, 4)
            
            heat = np.where(delta >= z2, "🌋 极限防范 (变盘红线)",
                   np.where(delta >= z3, "🔥 显著设防 (主力风控)",
                   np.where(delta >= z4, "📈 资金温和流入",
                   np.where(delta <= -z2, "🧊 极限抛弃 (彻底看死)",
                   np.where(delta <= -z3, "📉 显著看衰 (机构放弃)", 
                   np.where(delta <= -z4, "↘️ 资金温和流出", "⚪ 随机噪音 (散户买卖)"))))))
                   
            filter_q = np.where(dev < -0.02, "🩸 真实暴击防范 (剥削极狠)",
                       np.where(dev < 0, "📉 真实降水",
                       np.where((dev > 0) & (d_odds < c_odds), "🚨 虚假降水 (诱导陷阱！)",
                       np.where(dev > 0, "📈 真实升水抛弃", "⚪ 平稳"))))
            
            s_theo, u_theo = np.full(6, np.nan), np.full(6, np.nan)
            t_open, v_open, w_traj, aa_hedge = ["⚪ 无对照"]*6, ["⚪ 无对照"]*6, ["⚪ 无对照"]*6, ["⚪ 动量未达标"]*6
            
            if h_val != 0:
                s_theo[0] = round(prob_c[3] + prob_c[4], 4) if h_val < 0 else round(prob_c[3] - prob_c[1], 4)
                u_theo[0] = round(prob_d[3] + prob_d[4], 4) if h_val < 0 else round(prob_d[3] - prob_d[1], 4)
                
                for i, (c_prob, s_t, d_prob, u_t) in enumerate(zip([prob_c[0]], [s_theo[0]], [prob_d[0]], [u_theo[0]])):
                    diff_c = c_prob - s_t
                    t_open[0] = "🔻 极限低开" if diff_c >= z2 else "📉 显著低开" if diff_c >= z3 else "🔺 极限高开" if diff_c <= -z2 else "📈 显著高开" if diff_c <= -z3 else "⚪ 体系平衡"
                    diff_d = d_prob - u_t
                    v_open[0] = "🔻 极限低开" if diff_d >= z2 else "📉 显著低开" if diff_d >= z3 else "🔺 极限高开" if diff_d <= -z2 else "📈 显著高开" if diff_d <= -z3 else "⚪ 体系平衡"
                    
                    traj = (d_prob - u_t) - (c_prob - s_t)
                    w_traj[0] = "🚨 临场剧烈砸盘" if traj >= 0.02 else "📉 步步紧逼" if traj >= 0.01 else "🚨 疯狂拉高赔率" if traj <= -0.02 else "📈 门槛放宽" if traj <= -0.01 else "⚪ 伪装平稳"
                    
                    struct = round(d_prob - u_t, 4)
                    if delta[0] >= z3:
                        aa_hedge[0] = "✅ 黄金共振 (时空双杀闭眼上)" if struct >= z4 else "🚨 致命背离 (动量大热结构虚高!)" if struct <= -z4 else "🟡 结构中立"
                    elif delta[0] <= -z3:
                        aa_hedge[0] = "🎁 暗度陈仓 (表面退热底层死防)" if struct >= z4 else "🧊 真实抛弃 (时空双杀规避)" if struct <= -z4 else "⚪ 结构中立"
                    else:
                        aa_hedge[0] = "🌋 静态死防 (盘口未动底层死防)" if struct >= z3 else "🕸️ 静态诱网 (盘口未动底层虚高)" if struct <= -z3 else "⚪ 动量未达标"

            out_main = pd.DataFrame({
                "玩法选项": opts, "初纯净概率": prob_c, "临纯净概率": prob_d, "真实动量(Delta)": delta,
                "七阶热度测算仪": heat, "绝对净抽水偏离": dev, "相对返还率滤镜": filter_q,
                "底座理论概率": s_theo, "初盘开盘定性": t_open, "🎯 操盘轨迹研判": w_traj, "⚔️ 时空双杀验证": aa_hedge
            })
            
            st.markdown("### 📊 第一阶段：欧亚基础底座透视")
            st.dataframe(safe_style(out_main, ['七阶热度测算仪', '相对返还率滤镜', '初盘开盘定性', '🎯 操盘轨迹研判', '⚔️ 时空双杀验证']), hide_index=True, use_container_width=True)

            # ================= 顺流资金共识提纯器 =================
            ranks = pd.Series(delta).rank(method='min', ascending=False).values 
            
            refiner_text = []
            for i in range(6):
                r = ranks[i]
                d = delta[i]
                odd = c_odds[i]
                
                if r == 1:
                    txt = "🌋 史诗级重防" if d >= z2*1.5 else "🌋 绝对防范极值" if d >= z2 else "🔥 首席主防阵地" if d >= z3 else "🟡 相对领跑" if d >= z4 else "📈 微弱榜首" if d >= z5 else "⚪ 虚空榜首 (假热)"
                elif d > 0:
                    txt = "💣 史诗级暗盘 (极度危险)" if d >= z2*1.5 else "💣 隐蔽杀机 (爆出率高)" if d >= z2 else "🛡️ 独立重防" if d >= z3 else "📈 顺流吸筹" if d >= z4 else "↗️ 温和介入" if d >= z5 else "⚪ 边缘流入"
                elif odd >= z6:
                    txt = "🎭 终极恐吓 (暗藏杀机)" if d <= -z2*1.5 else "🚧 高赔壁垒 (防爆大冷)" if d <= -z2 else "📉 顺势驱赶" if d <= -z3 else "↘️ 显著退热" if d <= -z4 else "⏬ 微幅流失" if d <= -z5 else "⚪ 自然震荡"
                else:
                    txt = "🩸 绝望深渊 (彻底死亡)" if d <= -z2*1.5 else "🧊 极限绞杀出局" if d <= -z2 else "📉 坚决抛弃" if d <= -z3 else "↘️ 显著退热" if d <= -z4 else "⏬ 微幅流失" if d <= -z5 else "⚪ 自然震荡"
                refiner_text.append(txt)
                
            out_refiner = pd.DataFrame({
                "【顺流资金共识提纯器】": opts, "纯净概率偏移量": delta, "单项资金热度排名": ranks, "终极单项研判": refiner_text
            })
            st.markdown("### 🥇 第二阶段：顺流资金共识提纯器 (自动寻冷)")
            st.dataframe(safe_style(out_refiner, ['终极单项研判']), hide_index=True, use_container_width=True)

            # ================= 欧亚剪刀差 =================
            st.markdown("### ⚔️ 第三阶段：欧亚剪刀差极值研判")
            gap_home = round((delta[3] + delta[4]) - delta[0], 4) if h_val < 0 else round(delta[3] - (delta[0] + delta[1]), 4)
            gap_away = round(delta[5] - (delta[1] + delta[2]), 4) if h_val < 0 else round((delta[1] + delta[2]) - delta[5], 4)
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"#### ⚔️ 主队【让{abs(h_val)}球方】流速")
                st.metric("主队剪刀差净值", f"{gap_home:.4f}")
                if gap_home >= z4: st.error("🚨 虚假穿盘诱导 (深盘涨幅异常超越底座，防爆大冷)" if h_val < 0 else "🚨 受让过热 (实则掩护客胜)")
                elif gap_home <= -z4: st.success(f"🛡️ 精确死防边界 (防主队赢球输盘/走水)" if h_val < 0 else "🛡️ 真实防爆冷 (极大概率主队直接赢球)")
                else: st.info("⚪ 欧亚流速一致")
            with c2:
                st.markdown(f"#### 🛡️ 客队【受让{abs(h_val)}球方】流速")
                st.metric("客队剪刀差净值", f"{gap_away:.4f}")
                if abs(gap_away) >= z4: st.error("🚨 严重背离：下盘欧亚流速撕裂！")
                else: st.info("⚪ 欧亚流速一致")

    with tab1: render_main_handicap_ui("浅水区")
    with tab2: render_main_handicap_ui("中水区")
    with tab3: render_main_handicap_ui("深水区")

# ================= 5. 模块二：进球数风控 =================
elif active_module == "⚽ 模块二：进球数多维风控 (包揽浅中深)":
    st.header("⚽ 进球数与大小球全维透视模块")
    tab1, tab2, tab3 = st.tabs(["🟢 浅水区 (进球数)", "🟡 中水区 (进球数)", "🔴 深水区 (进球数)"])

    def render_goals_ui(water_level):
        st.markdown(f"### 📥 {water_level} 数据录入区")
        col_ext1, _ = st.columns(2)
        with col_ext1:
            h_val2 = st.number_input(f"主队亚指让球", value=-0.75, step=0.25, key=f"ext_v10_{water_level}")
        
        goals_data = {
            "玩法选项": ["0球", "1球", "2球", "3球", "4球", "5球", "6球", "7+球", "大球", "小球"],
            "初盘(C)": [15.0, 5.5, 3.6, 3.45, 4.9, 8.25, 15.0, 22.0, 0.65, 1.75],
            "T-60(J)": [None]*10, "临场(D)": [15.5, 5.9, 3.8, 3.10, 4.7, 8.50, 16.0, 24.0, 0.50, 1.15]
        }
        df_in2 = pd.DataFrame(goals_data)
        edited_2 = st.data_editor(df_in2, hide_index=True, num_rows="fixed", use_container_width=True, key=f"in2_v10_{water_level}")
        
        if st.button(f"🚀 执行 {water_level} 进球数雷达扫描", type="primary", key=f"btn2_v10_{water_level}"):
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
            
            r_g = np.where(delta >= z2*2, "🌋 极度过热 (诱导陷阱!)",
                  np.where(delta >= z2, "🚨 史诗级重防 (无视成本死命防守)",
                  np.where(delta >= z3, "🔥 首席主防阵地 (全场焦点)",
                  np.where(delta >= z4, "🟡 显著流入 (防守意愿尚可)",
                  np.where(delta >= z5, "↗️ 温和介入 (存在微弱暗水)",
                  np.where(delta <= -z2*2, "🕳️ 极度冰封 (彻底死亡)",
                  np.where(delta <= -z2, "🧊 极限绞杀出局 (遭联合抛弃)",
                  np.where(delta <= -z3, "📉 坚决抛弃 (主动不设防)",
                  np.where(delta <= -z4, "↘️ 显著流失 (打出阻力极大)",
                  np.where(delta <= -z5, "⏬ 微幅流失 (意图尚不坚决)", "⚪ 边缘震荡"))))))))))
            
            r_h = np.where(ev >= -0.10, "🌟 绝对正价值 (漏洞，稳赚)",
                  np.where(ev >= -0.15, "🟢 极度高潜 (突破重围)",
                  np.where(ev >= -0.18, "🟡 合理磨损 (常规抽水区)",
                  np.where(ev >= -0.22, "📉 劣势赔付 (吃水较深)",
                  np.where(ev >= -0.25, "🚨 杀猪盘预警 (极易出冷)", "🩸 抽水深渊 (坚决规避)")))))
            
            r_i = np.where((delta >= z2*1.5) & (ev <= -0.25), "🩸 嗜血诱导 (100%杀猪盘！)",
                  np.where((delta >= z3) & (delta < z2*1.5) & (ev <= -0.08) & (ev >= -0.25), "🎯 精确制导 (真实核心赛果！)",
                  np.where((delta <= -z3) & (ev > 0), "☠️ 淬毒诱饵 (绝对不碰！)", "⚪ ")))
            
            r_l = np.where(np.isnan(v_delta), "➖ ",
                  np.where(v_delta >= z3, "⚡ 绝杀爆发 (重金突袭直接上！)",
                  np.where(v_delta <= -z3, "🩸 极速撤离 (绝对杀猪盘！)", "⚪ 匀速平稳")))
            
            out_df2 = pd.DataFrame({
                "选项": opts, "动量(Delta)": delta, "期望值(EV)": ev, "加速度(V)": v_delta,
                "G列 (动量雷达)": r_g, "H列 (价值仪)": r_h, "I列 (自动防伪)": r_i, "L列 (狙击雷达)": r_l
            })
            
            st.markdown("### 📊 终极进球数扫描雷达")
            st.dataframe(safe_style(out_df2, ['G列 (动量雷达)', 'H列 (价值仪)', 'I列 (自动防伪)', 'L列 (狙击雷达)']), hide_index=True, use_container_width=True)
            
            st.markdown("### 📐 静态底座 X 光透视分析")
            if not np.isnan(c_7).all():
                even_prob = round(float(np.nansum(c_7[[0,2,4,6]])), 4)
                odd_prob = round(float(np.nansum(c_7[[1,3,5,7]])), 4)
                
                if abs(h_val2) <= 0.25: core_g = "0球, 1球, 2球"
                elif abs(h_val2) <= 0.75: core_g = "2球, 3球"
                elif abs(h_val2) <= 1.25: core_g = "3球, 4球"
                else: core_g = "4球, 5+球"
                
                min_idx = np.nanargmin(c_odds[0:8])
                match_s = "✅ 亚欧完美共振" if str(opts[min_idx][0]) in core_g else "🚨 严重逻辑背离"
                
                c1, c2, c3 = st.columns(3)
                c1.info(f"⚖️ 奇偶结构 -> 偶: {even_prob} | 奇: {odd_prob}")
                c2.info(f"🎯 亚指核心区 -> {core_g}")
                c3.info(f"🗺️ 交叉共振 -> {match_s}")

    with tab1: render_goals_ui("浅水区")
    with tab2: render_goals_ui("中水区")
    with tab3: render_goals_ui("深水区")

# ================= 6. 模块三：体彩高阶工具 (联动底座版) =================
elif active_module == "🎫 模块三：高阶工具 (DC矩阵/EV切片)":
    st.header("🎫 高阶价值提纯与转换矩阵")
    
    st.markdown("### ⚙️ 全局 DC 双泊松底座参数")
    st.caption("注：在此处填写的进球数与亚指参数，将同时驱动下方【DC矩阵】与【体彩EV切片器】的概率推演。")
    c1, c2, c3 = st.columns(3)
    tg = c1.number_input("进球盘 (大小球)", value=2.75, step=0.25, key="dc_tg")
    hcp = c2.number_input("让球盘 (主队亚指)", value=0.0, step=0.25, key="dc_hcp")
    rho = c3.number_input("DC依赖系数 (ρ)", value=-0.15, step=0.01, key="dc_rho")
    
    xg_h, xg_a = (tg - hcp) / 2, (tg + hcp) / 2
    
    if xg_h < 0 or xg_a < 0:
        st.error("⚠️ 预期进球为负，检查盘口是否填反！")
    else:
        st.markdown(f"**主队预期进球 (xG):** `{xg_h:.4f}` &nbsp;|&nbsp; **客队预期进球 (xG):** `{xg_a:.4f}`")
        df_m, ph2, ph1, pdr, pau, P_col_rounded = dixon_coles_full_matrix(xg_h, xg_a, rho)
        
        tab1, tab2 = st.tabs(["🧮 DC 进球双泊松矩阵", "✂️ 体彩 EV 价值切片器 (联动底座)"])
        
        with tab1:
            st.markdown("### 📊 核心赛果概率提纯")
            rc1, rc2, rc3, rc4 = st.columns(4)
            rc1.metric("DC 大胜概率(赢2+)", f"{ph2:.4f}")
            rc2.metric("DC 恰赢1球", f"{ph1:.4f}")
            rc3.metric("DC 平局概率", f"{pdr:.4f}")
            rc4.metric("DC 客不败", f"{pau:.4f}")
            st.markdown("### 🥅 DC 双泊松进球落点矩阵 (0-7+)")
            st.dataframe(df_m.style.format("{:.4f}"), use_container_width=True)

        with tab2:
            st.markdown("### 📥 录入国彩官方盘口与让球数")
            
            df_in3 = pd.DataFrame({
                "TC盘口": ["标准盘", "让球盘"],
                "胜": [2.32, 5.30],
                "平": [3.20, 4.00],
                "负": [2.60, 1.45],
                "国彩让球数": [0, -1]
            })
            edited_3 = st.data_editor(df_in3, hide_index=True, num_rows="fixed", use_container_width=True, key="in3_v10")
            
            if st.button("🚀 启动底座联动套利扫描"):
                std_odds = pd.to_numeric(edited_3.iloc[0, 1:4], errors='coerce').values
                let_odds = pd.to_numeric(edited_3.iloc[1, 1:4], errors='coerce').values
                
                # 严谨转换用户输入的让球数，防止报错
                try: tc_let = int(float(edited_3.iloc[1, 4]))
                except: tc_let = -1
                
                # Excel 里的 SUMPRODUCT 完全对齐计算 (精确到4位小数后动态相加)
                p_std_w = sum(P_col_rounded[i, j] for i in range(8) for j in range(8) if i - j > 0)
                p_std_d = sum(P_col_rounded[i, j] for i in range(8) for j in range(8) if i - j == 0)
                p_std_l = sum(P_col_rounded[i, j] for i in range(8) for j in range(8) if i - j < 0)
                
                p_let_w = sum(P_col_rounded[i, j] for i in range(8) for j in range(8) if i - j > -tc_let)
                p_let_d = sum(P_col_rounded[i, j] for i in range(8) for j in range(8) if i - j == -tc_let)
                p_let_l = sum(P_col_rounded[i, j] for i in range(8) for j in range(8) if i - j < -tc_let)
                
                intl_prob = np.array([p_std_w, p_std_d, p_std_l, p_let_w, p_let_d, p_let_l])
                tc_odds = np.concatenate([std_odds, let_odds])
                
                ev_vals = np.round(tc_odds * intl_prob - 1, 4)
                
                judge = np.where(ev_vals > 0, "🌟 绝对正价值 (机构漏洞，稳赚套利区)", 
                        np.where(ev_vals >= -0.03, "🟢 极度高潜 (无限逼近零损耗，暗盘首选)", 
                        np.where(ev_vals >= -0.08, "🟡 合理磨损 (常规抽水区间，可搏)", 
                        np.where(ev_vals >= -0.12, "📉 劣势赔付 (吃水较深，需动量支持)", 
                        np.where(ev_vals >= -0.16, "🚨 杀猪盘预警 (严重亏损区间，极易出冷)", "🩸 抽水深渊 (数学期望极度恶劣，坚决规避)")))))
                
                out_names = ["标准胜 EV", "标准平 EV", "标准负 EV", "让球胜 EV", "让球平 EV", "让球负 EV"]
                out_df3 = pd.DataFrame({"投注项": out_names, "推演纯净概率": np.round(intl_prob, 4), "数学EV": ev_vals, "【交易信号雷达】": judge})
                
                st.markdown("### 📊 体彩 EV 套利扫描矩阵")
                st.dataframe(safe_style(out_df3, ['【交易信号雷达】']), hide_index=True, use_container_width=True)
