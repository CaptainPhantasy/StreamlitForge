"""CLI-to-App Converter page - Convert CLI scripts to Streamlit apps."""

import streamlit as st
from pathlib import Path
import tempfile


def render():
    """Render the CLI-to-App Converter page."""
    
    st.title("🔄 CLI-to-App Converter")
    
    st.markdown("""
    Upload a CLI script and automatically convert it to a beautiful Streamlit application.
    Supports argparse, click, and other CLI frameworks.
    """)
    
    # Import converter module
    from streamlitforge.converter import CLIToEnterpriseConverter, ConversionOptions
    
    converter = CLIToEnterpriseConverter()
    
    # File upload
    st.subheader("Upload CLI Script")
    
    uploaded_file = st.file_uploader(
        "Upload a Python CLI script",
        type=["py"],
        help="Upload a CLI script that uses argparse, click, or similar",
    )
    
    if uploaded_file is not None:
        # Save to temp file for processing
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(uploaded_file.getvalue().decode("utf-8"))
            temp_path = f.name
        
        # Parse the script
        st.subheader("Detected CLI Arguments")
        
        with st.spinner("Analyzing CLI script..."):
            args = converter.parse_cli_script(temp_path)
        
        if args:
            st.success(f"Found {len(args)} CLI arguments!")
            
            # Display detected arguments
            for arg in args:
                with st.container(border=True):
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.markdown(f"**--{arg.name}**")
                        if arg.help_text:
                            st.caption(arg.help_text)
                    with col2:
                        badge = "📝" if arg.arg_type == "str" else "🔢" if arg.arg_type in ("int", "float") else "✅"
                        st.markdown(f"{badge} `{arg.arg_type}`")
                        if arg.default is not None:
                            st.caption(f"Default: `{arg.default}`")
                        if arg.choices:
                            st.caption(f"Choices: {arg.choices}")
        else:
            st.warning("No CLI arguments detected. Make sure your script uses argparse with add_argument() calls.")
        
        st.divider()
        
        # Conversion options
        st.subheader("Conversion Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            add_sidebar = st.checkbox("Add Sidebar", value=True, help="Put inputs in a sidebar")
            add_progress = st.checkbox("Progress Bar", value=True)
            add_export = st.checkbox("Export Results", value=True)
            add_dark_mode = st.checkbox("Dark Mode Support", value=True)
        
        with col2:
            add_auth = st.checkbox("Add Authentication", value=False)
            auth_provider = st.selectbox("Auth Provider", ["streamlit", "google", "okta"], disabled=not add_auth)
            add_logging = st.checkbox("Add Logging", value=True)
            add_validation = st.checkbox("Input Validation", value=True)
        
        export_formats = st.multiselect(
            "Export Formats",
            ["csv", "json", "excel", "parquet"],
            default=["csv", "json"],
        )
        
        st.divider()
        
        # Output settings
        st.subheader("Output Settings")
        
        output_name = st.text_input("App Name", value=uploaded_file.name.replace(".py", "_app"))
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Convert to Streamlit App", type="primary", use_container_width=True):
                options = ConversionOptions(
                    add_sidebar=add_sidebar,
                    add_progress_bar=add_progress,
                    add_export=add_export,
                    add_dark_mode=add_dark_mode,
                    add_auth=add_auth,
                    auth_provider=auth_provider,
                    add_logging=add_logging,
                    export_formats=export_formats,
                    add_input_validation=add_validation,
                )
                
                with tempfile.TemporaryDirectory() as tmpdir:
                    result = converter.generate_app(temp_path, tmpdir, options)
                    
                    # Store result in session state
                    st.session_state.conversion_result = result
                    st.session_state.conversion_output_dir = tmpdir
                    
                    # Read generated app
                    app_file = Path(result.output_path) / "app.py"
                    if app_file.exists():
                        st.session_state.generated_app_code = app_file.read_text()
                    
                    st.success(f"Converted! {result.cli_args_converted} arguments converted.")
                    st.rerun()
        
        # Show generated code if available
        if "generated_app_code" in st.session_state:
            st.divider()
            st.subheader("Generated Streamlit App")
            
            tab_code, tab_files = st.tabs(["app.py", "All Files"])
            
            with tab_code:
                code = st.session_state.generated_app_code
                st.code(code, language="python")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        "⬇️ Download app.py",
                        code,
                        f"{output_name}.py",
                        mime="text/x-python",
                        use_container_width=True,
                    )
                with col2:
                    if st.button("📋 Use in Current Project", use_container_width=True):
                        if st.session_state.current_project:
                            project_path = Path(st.session_state.current_project.get("path", ""))
                            app_file = project_path / "src" / "app.py"
                            app_file.parent.mkdir(parents=True, exist_ok=True)
                            app_file.write_text(code)
                            st.success("Saved to current project!")
                        else:
                            st.warning("No project selected")
            
            with tab_files:
                result = st.session_state.get("conversion_result")
                if result:
                    for f in result.files_created:
                        st.caption(f"📄 {Path(f).name}")
                    
                    if result.warnings:
                        st.warning("Warnings:")
                        for w in result.warnings:
                            st.caption(f"⚠️ {w}")
    
    else:
        # Show example
        st.subheader("Example CLI Script")
        
        with st.expander("View Example (argparse)", expanded=True):
            example_code = '''import argparse

def main():
    parser = argparse.ArgumentParser(description="Process data")
    parser.add_argument("--input", type=str, help="Input file path")
    parser.add_argument("--output", type=str, default="output.csv", help="Output file")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose mode")
    parser.add_argument("--count", type=int, default=10, help="Number of items")
    parser.add_argument("--format", choices=["csv", "json"], default="csv")
    
    args = parser.parse_args()
    
    # Your CLI logic here
    print(f"Processing {args.input} -> {args.output}")

if __name__ == "__main__":
    main()
'''
            st.code(example_code, language="python")
        
        st.info("👆 Upload a CLI script above to convert it to a Streamlit app")
    
    # Widget mapping reference
    st.divider()
    with st.expander("📖 CLI to Streamlit Widget Mapping"):
        st.markdown("""
        | CLI Argument Type | Streamlit Widget |
        |-------------------|------------------|
        | `str` | `st.text_input` |
        | `int` | `st.number_input` (step=1) |
        | `float` | `st.number_input` (step=0.01) |
        | `store_true/false` | `st.checkbox` |
        | `choices=[...]` | `st.selectbox` |
        | File path | `st.file_uploader` |
        """)
