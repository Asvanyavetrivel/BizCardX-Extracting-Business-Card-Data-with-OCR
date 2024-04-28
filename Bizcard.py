import streamlit as st
from streamlit_option_menu import option_menu
import easyocr
from PIL import Image
import pandas as pd
import numpy as np
import re
import io
import os
import psycopg2



def extract_text(image_path):

  input_img=Image.open(image_path)

  #convert image to array format
  image_array=np.array(input_img)

  reader = easyocr.Reader(['en'], gpu=False)
  details=reader.readtext(image_array,detail=0)

  return details, input_img

def process_text(details):
    data = {
        "name": "",
        "designation": "",
        "contact": [],
        "email": "",
        "website":[],
        "street": "",
        "city": "",
        "state": "",
        "pincode": "",
        "company": []
    }

    for i in range(len(details)):
        match1 = re.findall('([0-9]+ [A-Z]+ [A-Za-z]+)., ([a-zA-Z]+). ([a-zA-Z]+)', details[i])
        match2 = re.findall('([0-9]+ [A-Z]+ [A-Za-z]+)., ([a-zA-Z]+)', details[i])
        match3 = re.findall('^[E].+[a-z]', details[i])
        match4 = re.findall('([A-Za-z]+) ([0-9]+)', details[i])
        match5 = re.findall('([0-9]+ [a-zA-z]+)', details[i])
        match6 = re.findall('.com$', details[i])
        match7 = re.findall('([0-9]+)', details[i])
        if i == 0:
            data["name"] = details[i]
        elif i == 1:
            data["designation"] = details[i]
        elif '-' in details[i]:
            data["contact"].append(details[i])
        elif '@' in details[i]:
            data["email"] = details[i]
        elif "WWW" in details[i] or "www" in details[i] or "Www" in details[i] or "wWw" in details[i] or "wwW" in details[i]:
            small= details[i].lower()
            data["website"].append(small)
        elif match6:
            pass
        elif match1:
            data["street"] = match1[0][0]
            data["city"] = match1[0][1]
            data["state"] = match1[0][2]
        elif match2:
            data["street"] = match2[0][0]
            data["city"] = match2[0][1]
        elif match3:
            data["city"] = match3[0]
        elif match4:
            data["state"] = match4[0][0]
            data["pincode"] = match4[0][1]
        elif match5:
            data["street"] = match5[0] + ' St,'
        elif match7:
            data["pincode"] = match7[0]
        else:
            data["company"].append(details[i])

    data["contact"] = " & ".join(data["contact"])
    # Joining company names with space
    data["company"] = " ".join(data["company"])
    return data

# SETTING PAGE CONFIGURATIONS
st.set_page_config(page_title="BizCardX: Extracting Business Card Data with OCR | By Asvanya",
                   layout="wide",
                   initial_sidebar_state="expanded")
st.markdown("<h1 style='text-align: center; color: blue;'>BizCardX: Extracting Business Card Data with OCR</h1>",
            unsafe_allow_html=True)

# SETTING-UP BACKGROUND IMAGE
def setting_bg():
    st.markdown(f""" <style>.stApp {{
                        background:url("https://images.unsplash.com/photo-1528460033278-a6ba57020470?w=500&auto=format&fit=crop&q=60&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxzZWFyY2h8OHx8cGxhaW4lMjBiYWNrZ3JvdW5kfGVufDB8fDB8fHww");
                        background-size: cover}}
                     </style>""", unsafe_allow_html=True)
    
setting_bg()

# CREATING OPTION MENU
selected = option_menu(None, ["Home","Upload & Extract","Modify","Delete"],
                       icons=["house-door-fill","cloud-upload","pencil-square","x"],
                       default_index=0,
                       orientation="horizontal",
                       styles={"nav-link": {"font-size": "35px", "text-align": "centre", "margin": "-2px", "--hover-color": "#6495ED"},
                               "icon": {"font-size": "35px"},
                               "container" : {"max-width": "6000px"},
                               "nav-link-selected": {"background-color": "#6495ED"}})


# HOME MENU
if selected == "Home":
    st.markdown("<h3 style='text-align: left; color: blue;'>Project Overview:</h3>",
            unsafe_allow_html=True)  
    st.markdown("""<h5 style='text-align: left; color: black;'>BizCardX is a user-friendly tool for extracting information from business cards.
    - The tool uses OCR technology to recognize text on business cards and extracts the data into a SQL database after classification using regular expressions.
    - Users can access the extracted information using a GUI built using streamlit.
    - The BizCardX application is a simple and intuitive user interface that guides users through the process of uploading the business card image and extracting its information.
    - The extracted information would be displayed in a clean and organized manner, and users would be able to easily add it to the database with the click of a button.
    - Further the data stored in database can be easily Read, updated and deleted by user as per the requirement.</h5>""",
            unsafe_allow_html=True)
   
    st.markdown("<h3 style='text-align: left; color: blue;'>Technologies Used:</h3>",
            unsafe_allow_html=True) 
    st.markdown("<h4 style='text-align: left; color: black;'>Python,easyOCR, Streamlit, SQL, Pandas</h4>",
            unsafe_allow_html=True)             
    st.balloons()


if selected == "Upload & Extract":
    img = st.file_uploader("Upload the Image", type= ["png","jpg","jpeg"])
    if img is not None:
      st.image(img, width= 300)
      text_image, input_img= extract_text(img)
      text_dict = process_text(text_image)

      if text_dict:
        st.success("TEXT IS EXTRACTED SUCCESSFULLY")
      df= pd.DataFrame([text_dict])
      Image_bytes=io.BytesIO()
      input_img.save(Image_bytes, format="PNG")
      image_data=Image_bytes.getvalue()
      data={"Image":[image_data]}
      df1=pd.DataFrame(data)
      Concatenate_df=pd.concat([df,df1],axis=1)  #column wise concatination
      Concatenate_df
      
      button_1 = st.button("Save", use_container_width = True)

      if button_1:
          
          mydb = psycopg2.connect(host="localhost",
                        user="postgres",
                        password="2112",
                        database= "bizcard3",
                        port = "5432"
                        )

          cursor = mydb.cursor()


        # Table creation
          create_query = '''create table if not exists bizcard_details(Name varchar(100),
                                Designation varchar(100),  
                                Contact varchar(100),
                                Email varchar(100),
                                Website text,
                                Street text,
                                City text,
                                State text,
                                Pincode varchar(100),
                                Company varchar(100),
                                Image text)'''
          cursor.execute(create_query)
          mydb.commit()

          insert_query = '''INSERT into bizcard_details( Name,
                                                    Designation,
                                                    Contact,
                                                    Email,
                                                    Website,
                                                    Street,
                                                    City,
                                                    State,
                                                    Pincode,
                                                    Company,
                                                    Image)
                                                    VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'''
                        

          values=Concatenate_df.values.tolist()[0]
          cursor.execute(insert_query,values)
          mydb.commit()

          st.success("SAVED SUCCESSFULLY")

if selected == "Modify":
    method=st.selectbox("Select the method",['Preview','Modify']) 

    if method=="Preview":
        mydb = psycopg2.connect(host="localhost",
                        user="postgres",
                        password="2112",
                        database= "bizcard3",
                        port = "5432"
                        )

        cursor = mydb.cursor()

        select_query = "SELECT * FROM bizcard_details"

        cursor.execute(select_query)
        table = cursor.fetchall()
        mydb.commit()


        table_df = pd.DataFrame(table, columns=("NAME", "DESIGNATION","CONTACT", "EMAIL", "WEBSITE",
                                            "STREET","CITY","STATE","PINCODE","COMPANY","IMAGE"))
        st.dataframe(table_df)

    if method == "Modify":
            mydb = psycopg2.connect(host="localhost",
                            user="postgres",
                            password="2112",
                            database= "bizcard3",
                            port = "5432"
                            )

            cursor = mydb.cursor()

            select_query = "SELECT * FROM bizcard_details"

            cursor.execute(select_query)
            table = cursor.fetchall()
            mydb.commit()

            table_df = pd.DataFrame(table, columns=("NAME", "DESIGNATION","CONTACT", "EMAIL", "WEBSITE",
                                                "STREET","CITY","STATE","PINCODE","COMPANY","IMAGE"))
            st.dataframe(table_df)


            col1,col2 = st.columns(2)
            with col1:
                # Allow the user to select a name from the fetched records
                selected_name = st.selectbox("Select the Name", table_df["NAME"])

            df_3 = table_df[table_df["NAME"] == selected_name]
            st.markdown("<h3 style='text-align: left; color: blue;'>Before Modification:</h3>",
            unsafe_allow_html=True)
            st.dataframe(df_3)

            df_4 = df_3.copy()

            col1,col2 = st.columns(2)
            with col1:
                mo_name = st.text_input("Name", df_3["NAME"].unique()[0])
                mo_desi = st.text_input("Designation", df_3["DESIGNATION"].unique()[0])
                mo_contact = st.text_input("Contact", df_3["CONTACT"].unique()[0])
                mo_email = st.text_input("Email", df_3["EMAIL"].unique()[0])
                mo_website = st.text_input("Website", df_3["WEBSITE"].unique()[0])

                df_4["NAME"] = mo_name
                df_4["DESIGNATION"] = mo_desi
                df_4["CONTACT"] = mo_contact
                df_4["EMAIL"] = mo_email
                df_4["WEBSITE"] = mo_website

            with col2:
        
                
                mo_street = st.text_input("Street", df_3["STREET"].unique()[0])
                mo_city = st.text_input("City", df_3["CITY"].unique()[0])
                mo_state = st.text_input("State", df_3["STATE"].unique()[0])
                mo_pincode = st.text_input("Pincode", df_3["PINCODE"].unique()[0])
                mo_com = st.text_input("Company", df_3["COMPANY"].unique()[0])
                #mo_image = st.text_input("Image", df_3["IMAGE"].unique()[0])

            
                df_4["STREET"] = mo_street
                df_4["CITY"] = mo_city
                df_4["STATE"] = mo_state
                df_4["PINCODE"] = mo_pincode
                df_4["COMPANY"] = mo_com
                #df_4["IMAGE"] = mo_image
                
            col1,col2= st.columns(2)
            with col1:
                button_3 = st.button("Modify", use_container_width = True)  
            st.markdown("<h3 style='text-align: left; color: blue;'>After Modification:</h3>",
            unsafe_allow_html=True)
            st.dataframe(df_4)

if selected == "Delete":
    
    mydb = psycopg2.connect(host="localhost",
                        user="postgres",
                        password="2112",
                        database= "bizcard3",
                        port = "5432"
                        )

    cursor = mydb.cursor()

    col1,col2 = st.columns(2)
    with col1:
    
        select_query = "SELECT NAME FROM bizcard_details"

        cursor.execute(select_query)
        table1 = cursor.fetchall()
        mydb.commit()

        names = []
        for i in table1:
         names.append(i[0])

        name_select = st.selectbox("Select the name", names)

    with col2:
        select_query = f"SELECT DESIGNATION FROM bizcard_details WHERE NAME ='{name_select}'"
        cursor.execute(select_query)
        table2 = cursor.fetchall()
        mydb.commit()

        designations = []

        for j in table2:
         designations.append(j[0])
        designation_select = st.selectbox("Select the designation", options = designations)
        
        if name_select and designation_select:
            col1,col2,col3 = st.columns(3)
            

            with col1:
                st.write(f"Selected Name : {name_select}")
                st.write("")
                st.write("")
                st.write("")
                st.write(f"Selected Designation : {designation_select}")

            with col2:
                    st.write("")
                    st.write("")
                    st.write("")
                    st.write("")
                    remove = st.button("Delete", use_container_width= True)

                    if remove:

                        cursor.execute(f"DELETE FROM bizcard_details WHERE NAME ='{name_select}' AND DESIGNATION = '{designation_select}'")
                        mydb.commit()

                        st.warning("DELETED")

          
       
