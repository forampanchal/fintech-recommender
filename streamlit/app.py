import streamlit as st
import requests
import plotly.graph_objects as go

# ─────────────────────────────
# Config
# ─────────────────────────────
API_URL = "https://web-production-f724d.up.railway.app"

st.set_page_config(
    page_title="Fintech Product Recommender",
    page_icon="🏦",
    layout="wide"
)

# ─────────────────────────────
# Helper
# ─────────────────────────────


def score_color(score):
    if score > 70:
        return "#34a853"
    elif score > 40:
        return "#fa7b17"
    else:
        return "#ea4335"


# ─────────────────────────────
# Custom CSS
# ─────────────────────────────
st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    font-weight: 800;
    background: linear-gradient(90deg, #1a73e8, #0d47a1);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.5rem;
}
.sub-header {
    color: #666;
    font-size: 1.1rem;
    margin-bottom: 2rem;
}
.rec-card {
    background: #1e293b;
    border-radius: 12px;
    padding: 1.2rem;
    margin: 0.5rem 0;
    border: 1px solid #334155;
}
            
.rec-title {
    color: #ffffff;
    font-size: 1.1rem;
    font-weight: 600;
}
.rec-text {
    color: #e2e8f0;
    margin-top: 0.5rem;
}
.type-badge-cross {
    background: #34a853;
    color: white;
    border-radius: 20px;
    padding: 0.2rem 0.8rem;
    font-size: 0.8rem;
}
.rec-card:hover {
    transform: scale(1.01);
    transition: 0.2s;
}
.type-badge-up {
    background: #fa7b17;
    color: white;
    border-radius: 20px;
    padding: 0.2rem 0.8rem;
    font-size: 0.8rem;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────
# Header
# ─────────────────────────────
st.markdown('<p class="main-header">🏦 Fintech Product Recommender</p>',
            unsafe_allow_html=True)
st.markdown('<p class="sub-header">AI-powered banking product recommendations using Hybrid ML</p>',
            unsafe_allow_html=True)

# ─────────────────────────────
# Tabs
# ─────────────────────────────
tab1, tab2 = st.tabs(["🔍 Existing Customer", "✨ New Customer"])

# ═══════════════════════════════
# TAB 1 — Existing Customer
# ═══════════════════════════════
with tab1:
    st.subheader("Enter Customer ID")

    col1, col2 = st.columns([2, 1])
    with col1:
        customer_id = st.text_input(
            "Customer ID",
            placeholder="e.g. C_00001",
            label_visibility="collapsed"
        )
    with col2:
        search_btn = st.button("🔍 Get Recommendations",
                               type="primary", use_container_width=True)

    if search_btn and customer_id:
        with st.spinner("Generating recommendations..."):
            try:
                response = requests.get(
                    f"{API_URL}/recommend/{customer_id}", timeout=10)

                if response.status_code == 200:
                    data = response.json()
                    profile = data['profile']
                    spending = data['spending']
                    recs = data['recommendations']
                    current = data['current_products']

                    st.divider()

                    # Profile
                    st.markdown("### 👤 Customer Profile")
                    c1, c2, c3, c4, c5 = st.columns(5)
                    c1.metric("Age", profile['age'])
                    c2.metric("Income", profile['income'])
                    c3.metric("Credit Score", profile['credit_score'])
                    c4.metric("Segment", profile['segment'])
                    c5.metric("Tenure", f"{profile['tenure_months']} months")

                    st.divider()

                    col_left, col_right = st.columns([1, 1])

                    with col_left:
                        st.markdown("### 📊 Spending Behavior")
                        spending_data = {
                            k: float(v.replace('%', ''))
                            for k, v in spending.items()
                        }
                        fig = go.Figure(go.Bar(
                            x=list(spending_data.values()),
                            y=list(spending_data.keys()),
                            orientation='h',
                            marker_color='#1a73e8'
                        ))
                        fig.update_layout(
                            height=250,
                            margin=dict(l=0, r=0, t=0, b=0),
                            xaxis_title="Percentage (%)",
                            plot_bgcolor='white'
                        )
                        st.plotly_chart(fig, use_container_width=True)

                        st.markdown("### 💳 Current Products")
                        for p in current:
                            st.markdown(f"✅ {p}")

                    with col_right:
                        st.markdown("### 🎯 Recommendations")
                        for rec in recs:
                            badge_class = "type-badge-up" if rec['type'] == 'upsell' else "type-badge-cross"
                            color = score_color(rec['score'])
                            st.markdown(f"""
                            <div class="rec-card">
                                <div style="display:flex; justify-content:space-between; align-items:center">
                                    <div>
                                        <span style="font-size:1.5rem">{rec['emoji']}</span>
                                        <span class="rec-title">#{rec['rank']} {rec['product']}</span>
                                    </div>
                                    <div>
                                        <span style="background:{color}; color:white; border-radius:20px; padding:0.2rem 0.8rem; font-weight:600">{rec['score']}%</span>
                                        &nbsp;
                                        <span class="{badge_class}">{rec['type']}</span>
                                    </div>
                                </div>
                                <p class="rec-text">💡 {rec['reason']}</p>
                            </div>
                            """, unsafe_allow_html=True)

                elif response.status_code == 404:
                    st.error(
                        f"❌ Customer '{customer_id}' not found. Try C_00001 to C_10000")
                else:
                    st.error("Something went wrong. Please try again.")

            except Exception as e:
                st.error(
                    f"Cannot connect to API. Make sure FastAPI is running! Error: {e}")

# ═══════════════════════════════
# TAB 2 — New Customer
# ═══════════════════════════════
with tab2:
    st.subheader("Enter Your Financial Profile")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Demographics**")
        age = st.slider("Age", 18, 70, 28)
        income = st.slider("Annual Income ($)", 20000,
                           400000, 75000, step=5000)
        credit_score = st.slider("Credit Score", 500, 850, 720)
        segment = st.selectbox(
            "Customer Segment",
            ["young_professional", "mid_career", "family",
             "high_net_worth", "near_retirement"]
        )

    with col2:
        st.markdown("**Spending Habits (must total ≤ 100%)**")
        travel = st.slider("✈️ Travel", 0, 100, 20)
        dining = st.slider("🍽️ Dining", 0, 100, 15)
        groceries = st.slider("🛒 Groceries", 0, 100, 15)
        rent = st.slider("🏠 Rent/Housing", 0, 100, 25)
        shopping = st.slider("🛍️ Shopping", 0, 100, 10)

        total = travel + dining + groceries + rent + shopping
        remaining = max(0, 100 - total)

        st.progress(min(total, 100))

        if total > 100:
            st.error(f"⚠️ Total: {total}% — please reduce by {total - 100}%")
        elif total == 100:
            st.success(f"✅ Total: {total}% — perfect!")
        else:
            st.info(
                f"ℹ️ Total: {total}% — {remaining}% goes to entertainment/healthcare/utilities")

    get_recs_btn = st.button(
        "✨ Get My Recommendations",
        type="primary",
        use_container_width=True,
        disabled=(total > 100)
    )

    if get_recs_btn and total <= 100:
        entertainment = remaining // 3
        healthcare = remaining // 3
        utilities = remaining - entertainment - healthcare

        payload = {
            "age": age,
            "income": float(income),
            "credit_score": credit_score,
            "segment": segment,
            "travel_pct": travel / 100,
            "dining_pct": dining / 100,
            "groceries_pct": groceries / 100,
            "rent_pct": rent / 100,
            "shopping_pct": shopping / 100,
            "entertainment_pct": entertainment / 100,
            "healthcare_pct": healthcare / 100,
            "utilities_pct": utilities / 100
        }

        with st.spinner("Generating personalized recommendations..."):
            try:
                response = requests.post(
                    f"{API_URL}/recommend/profile",
                    json=payload, timeout=10
                )

                if response.status_code == 200:
                    data = response.json()
                    recs = data['recommendations']
                    summary = data['profile_summary']

                    st.divider()

                    st.markdown("### 👤 Your Profile")
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Age", summary['age'])
                    c2.metric("Income", summary['income'])
                    c3.metric("Credit Score", summary['credit_score'])
                    c4.metric("Segment", summary['segment'])

                    st.markdown("### 🎯 Your Personalized Recommendations")

                    for rec in recs:
                        badge_class = "type-badge-up" if rec['type'] == 'upsell' else "type-badge-cross"
                        color = score_color(rec['score'])
                        st.markdown(f"""
                        <div class="rec-card">
                            <div style="display:flex; justify-content:space-between; align-items:center">
                                <div>
                                    <span style="font-size:1.5rem">{rec['emoji']}</span>
                                    <span class="rec-title">#{rec['rank']} {rec['product']}</span>
                                </div>
                                <div>
                                    <span style="background:{color}; color:white; border-radius:20px; padding:0.2rem 0.8rem; font-weight:600">{rec['score']}%</span>
                                    &nbsp;
                                    <span class="{badge_class}">{rec['type']}</span>
                                </div>
                            </div>
                            <p class="rec-text">💡 {rec['reason']}</p>
                        </div>
                        """, unsafe_allow_html=True)

                else:
                    st.error("Something went wrong. Please try again.")

            except requests.exceptions.Timeout:
                st.error("⏱ API timeout — server is slow, try again")

            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot connect to API — backend may be down")

            except Exception as e:
                st.error(f"Unexpected error: {e}")
