# 🎨 Streamlit Styling Guide

## Custom CSS for Figma-like Designs

### 1. Typography & Colors

```python
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global font family */
    .stApp {
        font-family: 'Inter', sans-serif;
    }
    
    /* Custom color variables */
    :root {
        --primary-color: #667eea;
        --secondary-color: #764ba2;
        --success-color: #10b981;
        --warning-color: #f59e0b;
        --error-color: #ef4444;
        --text-primary: #1f2937;
        --text-secondary: #6b7280;
        --background: #f8fafc;
    }
</style>
""", unsafe_allow_html=True)
```

### 2. Card Components

```python
def create_card(title, content, color="white"):
    st.markdown(f"""
    <div style="
        background: {color};
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        margin: 1rem 0;
        border: 1px solid #e5e7eb;
    ">
        <h3 style="margin: 0 0 1rem 0; color: var(--text-primary);">{title}</h3>
        <p style="margin: 0; color: var(--text-secondary);">{content}</p>
    </div>
    """, unsafe_allow_html=True)
```

### 3. Button Styles

```python
def styled_button(text, key, style="primary"):
    styles = {
        "primary": "background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;",
        "secondary": "background: #f3f4f6; color: #374151; border: 1px solid #d1d5db;",
        "success": "background: #10b981; color: white;",
        "danger": "background: #ef4444; color: white;"
    }
    
    return st.markdown(f"""
    <style>
        div[data-testid="stButton"] > button[key="{key}"] {{
            {styles[style]}
            border: none;
            border-radius: 8px;
            padding: 0.5rem 1rem;
            font-weight: 500;
            transition: all 0.2s;
        }}
        div[data-testid="stButton"] > button[key="{key}"]:hover {{
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}
    </style>
    """, unsafe_allow_html=True)
```

### 4. Layout Patterns

#### Responsive Grid Layout

```python
def responsive_grid(items, cols_desktop=3, cols_mobile=1):
    # Desktop layout
    if st.get_option("browser.gatherUsageStats"):  # Simple desktop detection
        cols = st.columns(cols_desktop)
        for i, item in enumerate(items):
            with cols[i % cols_desktop]:
                item()
    else:
        # Mobile layout
        for item in items:
            item()
```

#### Hero Section

```python
def hero_section(title, subtitle, image_url=None):
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 4rem 2rem;
        border-radius: 16px;
        text-align: center;
        margin: 2rem 0;
        color: white;
    ">
        <h1 style="font-size: 3rem; margin: 0 0 1rem 0;">{}</h1>
        <p style="font-size: 1.25rem; opacity: 0.9; margin: 0;">{}</p>
    </div>
    """.format(title, subtitle), unsafe_allow_html=True)
```

### 5. Advanced Components

#### Progress Bar

```python
def custom_progress_bar(value, max_value, label):
    percentage = (value / max_value) * 100
    st.markdown(f"""
    <div style="margin: 1rem 0;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
            <span>{label}</span>
            <span>{value}/{max_value}</span>
        </div>
        <div style="
            background: #e5e7eb;
            height: 8px;
            border-radius: 4px;
            overflow: hidden;
        ">
            <div style="
                background: linear-gradient(90deg, #10b981, #059669);
                height: 100%;
                width: {percentage}%;
                transition: width 0.3s ease;
            "></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
```

#### Stats Card

```python
def stats_card(title, value, change, icon="📊"):
    change_color = "#10b981" if change >= 0 else "#ef4444"
    change_symbol = "+" if change >= 0 else ""
    
    st.markdown(f"""
    <div style="
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        border: 1px solid #e5e7eb;
    ">
        <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
            <span style="font-size: 1.5rem; margin-right: 0.5rem;">{icon}</span>
            <span style="color: #6b7280; font-size: 0.875rem;">{title}</span>
        </div>
        <div style="font-size: 2rem; font-weight: 700; color: #1f2937; margin-bottom: 0.25rem;">
            {value}
        </div>
        <div style="color: {change_color}; font-size: 0.875rem;">
            {change_symbol}{change}% from last month
        </div>
    </div>
    """, unsafe_allow_html=True)
```

### 6. Mobile Responsiveness

```python
# Add this CSS for mobile responsiveness
st.markdown("""
<style>
    @media (max-width: 768px) {
        .stApp > div {
            padding: 1rem;
        }
        
        .metric-card {
            margin-bottom: 1rem;
        }
        
        .main-header {
            font-size: 2rem !important;
        }
    }
</style>
""", unsafe_allow_html=True)
```

### 7. Dark Mode Toggle

```python
def dark_mode_toggle():
    dark_mode = st.checkbox("🌙 Dark Mode")
    
    if dark_mode:
        st.markdown("""
        <style>
            .stApp {
                background-color: #1f2937;
                color: white;
            }
            .card {
                background-color: #374151 !important;
                color: white !important;
            }
        </style>
        """, unsafe_allow_html=True)
    
    return dark_mode
```

## 🚀 Tips for Figma to Streamlit Conversion

1. **Extract Colors**: Use Figma's color picker to get exact hex codes
2. **Measure Spacing**: Note padding, margins, and gaps from your design
3. **Typography**: Match font families, sizes, and weights
4. **Components**: Break down complex designs into reusable functions
5. **Responsive**: Test your app on different screen sizes
6. **Images**: Export assets from Figma and use `st.image()`
7. **Icons**: Use emoji or icon fonts like Font Awesome

## 📱 Running Your App

1. Save your code in `app.py`
2. Open terminal in your project folder
3. Run: `streamlit run app.py`
4. Your app will open in your browser at `http://localhost:8501`