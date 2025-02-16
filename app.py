import streamlit as st
from streamlit_option_menu import option_menu

from YourMaterialTopic.test_with_your_material import test_with_your_material_interface
from UsageGuide.usage_guide import usage_guide_interface
from MaterialUploader.upload_material import material_uploader_interface

def home():
    st.title("Welcome to AI-PrepMaster")
    if st.button("login"):
        st.session_state["uploaded_and_analyzed"] = False

    st.sidebar.markdown(
        f"""
        <h1 style="font-size: 35px">Welcome, <strong>dfd </h1>
        """,
        unsafe_allow_html = True
    )
    
    
    with st.sidebar:
        choice = option_menu(
            menu_title="Functionalities",
            options=['Topic Mastery Zone', 'Test With Topics',
                    'Upload Your Material','Test With Your Own Material','Download OMR','OMR Checking','Usage Guide'],
            menu_icon='none',
            default_index=6,
            styles={
                "container": {"padding": "5!important","background-color":'black'},
    "icon": {"color": "white", "font-size": "23px"}, 
    "nav-link": {"color":"white","font-size": "25px", "text-align": "left", "margin":"0px", "--hover-color": "gray"},
    "nav-link-selected": {"background-color": "#02ab21"},}
        )


        

        

        
    if choice == "Test With Your Own Material":
        test_with_your_material_interface()
        
    elif choice == "Upload Your Material":
        material_uploader_interface()
        
    elif choice == "Usage Guide":
        usage_guide_interface()
    

    
    if st.sidebar.button("Logout"):
        # st.session_state["logged_in"] = False
        # st.session_state.pop("username", None)
        # st.session_state["page"] = "Login"
        st.session_state['uploaded_and_analyzed'] = False
        st.rerun()

home()