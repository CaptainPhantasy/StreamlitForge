"""Projects management page."""

import streamlit as st
from pathlib import Path
import shutil


def render():
    """Render the Projects page."""
    
    st.title("📁 Projects")
    
    tab_list, tab_new, tab_import = st.tabs(["List", "New Project", "Import"])
    
    with tab_list:
        st.subheader("Your Projects")
        
        pm = st.session_state.project_manager
        projects = pm.list_projects()
        
        if projects:
            for project in projects:
                with st.container(border=True):
                    col1, col2, col3 = st.columns([3, 2, 2])
                    
                    with col1:
                        st.markdown(f"### {project.get('name', 'Untitled')}")
                        st.caption(f"📁 {project.get('path', 'No path')}")
                        
                        project_path = Path(project.get('path', ''))
                        if project_path.exists():
                            file_count = len(list(project_path.rglob("*.py")))
                            st.caption(f"{file_count} Python files")
                    
                    with col2:
                        st.metric("Port", project.get('port', 'Not assigned'))
                        st.caption(f"Created: {project.get('created', 'Unknown')[:10]}")
                    
                    with col3:
                        if st.button("📂 Open", key=f"open_{project.get('path')}", type="primary"):
                            st.session_state.current_project = project
                            st.session_state.active_tab = "🤖 AI Builder"
                            st.rerun()
                        
                        if st.button("🗑️ Delete", key=f"del_{project.get('path')}"):
                            try:
                                pm.delete_project(project.get('path'))
                                if st.session_state.current_project == project:
                                    st.session_state.current_project = None
                                st.rerun()
                            except Exception as e:
                                st.error(str(e))
        else:
            st.info("No projects yet. Create a new project to get started!")
    
    with tab_new:
        st.subheader("Create New Project")
        
        with st.form("new_project_form"):
            name = st.text_input("Project Name", placeholder="my_awesome_app")
            
            col1, col2 = st.columns(2)
            with col1:
                path = st.text_input("Location", value=str(Path.home() / "streamlit_projects"))
            with col2:
                template = st.selectbox("Template", ["blank", "dashboard", "chat", "data_explorer"])
            
            col3, col4 = st.columns(2)
            with col3:
                create_venv = st.checkbox("Create virtual environment", value=True)
            with col4:
                # Git init not in API but we'll note it
                st.caption("Git repo initialized automatically")
            
            submitted = st.form_submit_button("Create Project", type="primary")
            
            if submitted and name:
                try:
                    project_dir = st.session_state.project_manager.create_project(
                        project_name=name,
                        parent_dir=path,
                        template=template if template != "blank" else None,
                        create_venv=create_venv,
                    )
                    
                    # Get project info for session
                    project = {
                        "name": name,
                        "path": str(project_dir),
                        "port": st.session_state.port_manager.get_port(str(project_dir)),
                    }
                    st.session_state.current_project = project
                    st.success(f"✅ Created project: {name}")
                    st.balloons()
                    st.session_state.active_tab = "🤖 AI Builder"
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to create project: {e}")
    
    with tab_import:
        st.subheader("Import Existing Project")
        
        with st.form("import_project_form"):
            import_path = st.text_input("Project Path", placeholder="/path/to/existing/streamlit/app")
            import_name = st.text_input("Project Name (optional)", placeholder="Uses folder name if empty")
            
            submitted = st.form_submit_button("Import Project", type="primary")
            
            if submitted and import_path:
                try:
                    project_path = Path(import_path)
                    if not project_path.exists():
                        st.error("Path does not exist")
                    else:
                        py_files = list(project_path.glob("*.py"))
                        if not py_files:
                            st.error("No Python files found")
                        else:
                            name = import_name or project_path.name
                            port = st.session_state.port_manager.get_port(str(project_path))
                            
                            project = {
                                "name": name,
                                "path": str(project_path),
                                "port": port,
                            }
                            
                            # Register it
                            pm._register_project(project_path, port)
                            st.session_state.current_project = project
                            st.success(f"✅ Imported: {name}")
                            st.session_state.active_tab = "🤖 AI Builder"
                            st.rerun()
                except Exception as e:
                    st.error(f"Failed to import: {e}")
