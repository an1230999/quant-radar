import streamlit as st
import pandas as pd

# ================= 1. 全局配置与彭博风格主题 =================
st.set_page_config(page_title="FX2 全维足球量化对冲终端", layout="wide", page_icon="📊")
st.title("📊 FX2 全维足球量化对冲终端")
st.markdown("<p style='color:#888; font-size:14px;'>当前状态：多模型矩阵已全面激活。支持标盘、让球盘、欧亚剪刀差、时空双盲对冲、进球数雷达及体彩切片。</p>", unsafe_allow_html=True)
st.markdown("---")

# ================= 2. 侧边栏：多工作表/多模型导航矩阵 =================
st.sidebar.title("🧭 FX2 模型导航矩阵")
water_level = st.sidebar.selectbox("选择分析水区 (对齐Excel工作表)", ["浅水区 (低吸低风险盘)", "中水区 (主流常规盘)", "深水区 (高压高赔冷门盘)"])
model_type = st.sidebar.radio("切换底层量化精算模型", [
    "⚔️ 欧亚全盘对冲与剪刀差引擎",
    "⚽ 进球数时空双盲风控雷达",
    "🎫 体彩 EV 价值切片器"
])

# 侧边栏公用参数控制台
st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ 动态风控参数控制台")
param_red = st.sidebar.number_input("动量变盘红线阈值", value=0.0300, format="%.4f")
param_sig = st.sidebar.number_input("显著流入防线阈值", value=0.0200, format="%.4f")

# ================= 3. 模型一：欧亚全盘对冲与剪刀差引擎 =================
if model_type == "⚔️ 欧亚全盘对冲与剪刀差引擎":
    st.header(f"⚔️ 欧亚全盘对冲与剪刀差 (当前：{water_level})")
    st.subheader("📝 录入标盘与让球盘数据")
    
    # 欧亚大盘数据录入
    cols = st.columns(3)
    with cols[0]:
        st.markdown("### 🟢 标准盘 (胜平负)")
        win_c = st.number_input("标胜初赔", value=1.78)
        win_d = st.number_input("标胜临赔", value=1.58)
        draw_c = st.number_input("标平初赔", value=3.22)
        draw_d = st.number_input("标平临赔", value=3.60)
        loss_c = st.number_input("标负初赔", value=3.90)
        loss_d = st.number_input("标负临赔", value=4.58)
    with cols[1]:
        st.markdown("### 🔵 让球盘 (让胜平负)")
        h_num = st.number_input("让球数 (如-1, +1)", value=-1.0, step=0.5)
        h_win_c = st.number_input("让胜初赔", value=3.55)
        h_win_d = st.number_input("让胜临赔", value=3.18)
        h_draw_c = st.number_input("让平初赔", value=3.40)
        h_draw_d = st.number_input("让平临赔", value=3.00)
        h_loss_c = st.number_input("让负初赔", value=1.81)
        h_loss_d = st.number_input("让负临赔", value=2.08)
    with cols[2]:
        st.markdown("### ⏱️ 时间切片 (T-60)")
        st.caption("首发阵容公布时的中间赔率截面")
        win_t60 = st.number_input("标胜 T-60 赔率", value=1.65)
        h_win_t60 = st.number_input("让胜 T-60 赔率", value=3.30)

    if st.button("🚀 启动全盘双盲对冲演算", type="primary"):
        # 计算初盘临场返还率
        p_return_c = 1 / (1/win_c + 1/draw_c + 1/loss_c)
        p_return_d = 1 / (1/win_d + 1/draw_d + 1/loss_d)
        h_return_c = 1 / (1/h_win_c + 1/h_draw_c + 1/h_loss_c)
        
        # 归一化真实概率变化 Delta
        delta_win = (1/win_d)/sum([1/win_d, 1/draw_d, 1/loss_d]) - (1/win_c)/sum([1/win_c, 1/draw_c, 1/loss_c])
        delta_h_win = (1/h_win_d)/sum([1/h_win_d, 1/h_draw_d, 1/h_loss_d]) - (1/h_win_c)/sum([1/h_win_c, 1/h_draw_c, 1/h_loss_c])
        
        # 计算欧亚剪刀差
        scissor_gap = abs(delta_win - delta_h_win)
        
        st.markdown("---")
        st.subheader("📊 欧亚对冲提纯与轨迹研判")
        
        res_cols = st.columns(4)
        res_cols[0].metric("标盘初盘返还率", f"{p_return_c:.4f}")
        res_cols[1].metric("标盘临场返还率", f"{p_return_d:.4f}")
        res_cols[2].metric("主队胜方真实动量 (Delta)", f"{delta_win:.4f}")
        res_cols[3].metric("欧亚流速剪刀差净值", f"{scissor_gap:.4f}")
        
        # 智能研判逻辑
        st.markdown("### ⚔️ 时空双盲对冲验证结论")
        if scissor_gap <= 0.01:
            st.success("✅ 欧亚流速一致：大盘与让球盘资金流向高度自洽，动量真实，无对冲背离，可顺流顺盘博弈。")
        else:
            st.sidebar.warning("🚨 触发高危剪刀差警报")
            st.error("🚨 严重逻辑背离 (欧亚剪刀差极深)：标准盘与让球盘流速严重撕裂！存在一方恶意诱导或阻盘，极度防冷！")

# ================= 4. 模型二：进球数时空双盲风控雷达 =================
elif model_type == "⚽ 进球数时空双盲风控雷达":
    st.header(f"⚽ 进球数全维风控引擎 (当前：{water_level})")
    
    # 进球数数据编辑器
    goals_data = {
        "选项": ["0球", "1球", "2球", "3球", "4球", "5球", "6球", "7+球", "大球", "小球"],
        "初盘赔率 (C)": [15.0, 5.5, 3.6, 3.45, 4.9, 8.25, 15.0, 22.0, 0.65, 1.75],
        "T-60赔率 (J)": [15.0, 5.6, 3.7, 3.20, 4.8, 8.30, 15.5, 23.0, 0.60, 1.60],
        "临场赔率 (D)": [15.5, 5.9, 3.8, 3.10, 4.7, 8.50, 16.0, 24.0, 0.50, 1.15]
    }
    df_goals = pd.DataFrame(goals_data)
    edited_goals = st.data_editor(df_goals, hide_index=True, use_container_width=True)
    
    if st.button("🚀 执行进球数矩阵扫描", type="primary"):
        # 分离进球数单项和大小球
        df_items = edited_goals.iloc[0:8].copy()
        df_ou = edited_goals.iloc[8:10].copy()
        
        # 归一化计算
        sum_c = sum(1 / df_items['初盘赔率 (C)'])
        sum_j = sum(1 / df_items['T-60赔率 (J)'])
        sum_d = sum(1 / df_items['临场赔率 (D)'])
        
        prob_c = (1 / df_items['初盘赔率 (C)']) / sum_c
        prob_j = (1 / df_items['T-60赔率 (J)']) / sum_j
        prob_d = (1 / df_items['临场赔率 (D)']) / sum_d
        
        df_items['总动量 (Delta)'] = (prob_d - prob_c).round(4)
        df_items['期望值 (EV)'] = (prob_c * df_items['临场赔率 (D)'] - 1).round(4)
        df_items['临场加速度 (V-Delta)'] = (prob_d - prob_j).round(4)
        
        # 智能标签生成
        def process_labels(row):
            d, ev, v = row['总动量 (Delta)'], row['期望值 (EV)'], row['临场加速度 (V-Delta)']
            macro = "🩸 嗜血诱导 (诱大杀猪盘)" if d >= (param_red*1.2) and ev <= -0.22 else ("🎯 精确制导" if d >= param_sig else "⚪ 常规磨损")
            micro = "⚡ 绝杀爆发 (主力砸盘)" if v >= 0.0050 else "⚪ 匀速平稳"
            return macro, micro
            
        df_items[['宏观验证', '微观加速度']] = df_items.apply(process_labels, axis=1, result_type='expand')
        st.dataframe(df_items[['选项', '总动量 (Delta)', '期望值 (EV)', '临场加速度 (V-Delta)', '宏观验证', '微观加速度']], hide_index=True, use_container_width=True)

# ================= 5. 模型三：体彩 EV 价值切片器 =================
elif model_type == "🎫 体彩 EV 价值切片器":
    st.header("🎫 体彩 EV 价值切片器（专攻让球/竞彩漏洞）")
    st.subheader("📝 录入体彩官方赔率与国际纯净概率对照")
    
    ev_data = {
        "竞彩投注项": ["主胜 (标胜)", "平局", "客胜", "让球主胜", "让球平局", "让球客胜"],
        "体彩官方赔率": [1.60, 3.45, 4.35, 2.90, 3.45, 2.02],
        "网大国际纯净概率": [0.5610, 0.2450, 0.1940, 0.2780, 0.2950, 0.4270]
    }
    df_ev = pd.DataFrame(ev_data)
    edited_ev = st.data_editor(df_ev, hide_index=True, use_container_width=True)
    
    if st.button("🚀 切片提取绝对正价值项", type="primary"):
        edited_ev['真实数学 EV'] = (edited_ev['体彩官方赔率'] * edited_ev['网大国际纯净概率'] - 1).round(4)
        
        def ev_judge(val):
            if val > 0: return "🌟 绝对正价值漏洞 (稳赚，强烈推荐！)"
            elif val >= -0.05: return "🟡 低损耗对冲项"
            else: return "🩸 抽水黑洞 (极度亏损，拒绝买入)"
            
        edited_ev['决策定性滤镜'] = edited_ev['真实数学 EV'].apply(ev_judge)
        st.dataframe(edited_ev, hide_index=True, use_container_width=True)
