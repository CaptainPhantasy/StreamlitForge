"""Deployment page - Generate deployment configurations for various platforms."""

import streamlit as st
from pathlib import Path


def render():
    """Render the Deployment page."""
    
    st.title("🚀 Deployment")
    
    st.markdown("""
    Generate deployment configurations for your Streamlit applications.
    Select a platform and customize the settings for your deployment.
    """)
    
    # Check for project
    if not st.session_state.current_project:
        st.warning("Please select or create a project first.")
        if st.button("Go to Projects"):
            st.session_state.active_tab = "📁 Projects"
            st.rerun()
        return
    
    project = st.session_state.current_project
    st.caption(f"Project: **{project.get('name', 'Untitled')}** | {project.get('path', '')}")
    
    # Import deployment module
    from streamlitforge.deployment import DeploymentManager, DeploymentConfigGenerator, ProjectInfo
    
    manager = DeploymentManager()
    generator = DeploymentConfigGenerator()
    
    # Platform selection
    st.subheader("Select Platform")
    
    platforms = manager.list_platforms()
    cols = st.columns(4)
    
    selected_platform = st.session_state.get("selected_platform", "docker")
    
    for idx, platform in enumerate(platforms):
        with cols[idx % 4]:
            is_selected = platform["id"] == selected_platform
            btn_type = "primary" if is_selected else "secondary"
            free_label = "🆓" if platform.get("free_tier") else "💰"
            if st.button(
                f"{free_label} {platform['name']}", 
                key=f"platform_{platform['id']}",
                type=btn_type,
                use_container_width=True,
            ):
                st.session_state.selected_platform = platform["id"]
                st.rerun()
    
    st.divider()
    
    # Configuration
    st.subheader("Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        project_name = st.text_input("Project Name", value=project.get("name", "my-app"))
        port = st.number_input("Port", min_value=1024, max_value=65535, value=project.get("port", 8501))
    
    with col2:
        python_version = st.selectbox("Python Version", ["3.8", "3.9", "3.10", "3.11", "3.12"], index=3)
        include_data_volume = st.checkbox("Include Data Volume", value=True)
    
    st.divider()
    
    # Generate configuration
    st.subheader("Generated Configuration")
    
    project_info = ProjectInfo(
        name=project_name,
        path=project.get("path", ""),
        port=port,
        python_version=python_version,
    )
    
    # Show all config types for Docker
    if selected_platform == "docker":
        tab_dockerfile, tab_compose, tab_render, tab_railway, tab_procfile = st.tabs([
            "Dockerfile", "docker-compose.yml", "render.yaml", "railway.toml", "Procfile"
        ])
        
        with tab_dockerfile:
            dockerfile_content = generator.generate_dockerfile(project_info)
            st.code(dockerfile_content, language="dockerfile")
            st.download_button(
                "Download Dockerfile",
                dockerfile_content,
                "Dockerfile",
                mime="text/plain",
                use_container_width=True,
            )
        
        with tab_compose:
            compose_content = generator.generate_docker_compose(project_info)
            st.code(compose_content, language="yaml")
            st.download_button(
                "Download docker-compose.yml",
                compose_content,
                "docker-compose.yml",
                mime="text/yaml",
                use_container_width=True,
            )
        
        with tab_render:
            render_content = generator.generate_render_yaml(project_info)
            st.code(render_content, language="yaml")
            st.download_button(
                "Download render.yaml",
                render_content,
                "render.yaml",
                mime="text/yaml",
                use_container_width=True,
            )
        
        with tab_railway:
            railway_content = generator.generate_railway_toml(project_info)
            st.code(railway_content, language="toml")
            st.download_button(
                "Download railway.toml",
                railway_content,
                "railway.toml",
                mime="text/plain",
                use_container_width=True,
            )
        
        with tab_procfile:
            procfile_content = generator.generate_procfile(project_info)
            st.code(procfile_content, language="plaintext")
            st.download_button(
                "Download Procfile",
                procfile_content,
                "Procfile",
                mime="text/plain",
                use_container_width=True,
            )
    
    elif selected_platform == "render":
        render_content = generator.generate_render_yaml(project_info)
        st.code(render_content, language="yaml")
        st.download_button(
            "Download render.yaml",
            render_content,
            "render.yaml",
            mime="text/yaml",
            use_container_width=True,
        )
    
    elif selected_platform == "railway":
        railway_content = generator.generate_railway_toml(project_info)
        st.code(railway_content, language="toml")
        st.download_button(
            "Download railway.toml",
            railway_content,
            "railway.toml",
            mime="text/plain",
            use_container_width=True,
        )
    
    elif selected_platform == "heroku":
        procfile_content = generator.generate_procfile(project_info)
        st.code(procfile_content, language="plaintext")
        st.download_button(
            "Download Procfile",
            procfile_content,
            "Procfile",
            mime="text/plain",
            use_container_width=True,
        )
    
    else:
        # Generic Docker fallback for other platforms
        st.info(f"Generating Docker configuration for {selected_platform}")
        dockerfile_content = generator.generate_dockerfile(project_info)
        st.code(dockerfile_content, language="dockerfile")
        st.download_button(
            "Download Dockerfile",
            dockerfile_content,
            "Dockerfile",
            mime="text/plain",
            use_container_width=True,
        )
    
    st.divider()
    
    # Quick deploy actions
    st.subheader("Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📁 Generate All Files", use_container_width=True, type="primary"):
            project_path = Path(project.get("path", ""))
            if project_path.exists():
                result = manager.generate_config(project_info, "docker")
                if result.success:
                    st.success(f"Created {len(result.files_created)} files!")
                    for f in result.files_created:
                        st.caption(f"✅ {f}")
                else:
                    st.error(result.message)
            else:
                st.error("Project path does not exist")
    
    with col2:
        if st.button("📋 Copy Docker Command", use_container_width=True):
            st.code(f"docker build -t {project_name} . && docker run -p {port}:{port} {project_name}")
    
    with col3:
        if st.button("📖 View Docs", use_container_width=True):
            st.session_state.active_tab = "📚 Knowledge"
            st.rerun()
