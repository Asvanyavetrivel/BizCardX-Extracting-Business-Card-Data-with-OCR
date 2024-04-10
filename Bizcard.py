import streamlit as st
from streamlit_option_menu import option_menu
import easyocr
from PIL import Image
import pandas as pd
import numpy as np
import re
import io
import psycopg2

# Function Definition
def image_to_text(path):
  # Open Image
  input_img= Image.open(path)

  #Convert Image to Array
  image_arr= np.array(input_img)
  #OCR Initialization
  reader= easyocr.Reader(['en'])

  #Perform OCR
  text= reader.readtext(image_arr, detail= 0)
  
  #Return Result
  return text, input_img

# Function Definition
def extracted_text(texts):
  
  #Initializing an Empty Dictionary
  extrd_dict = {"NAME":[], "DESIGNATION":[], "COMPANY_NAME":[], "CONTACT":[], "EMAIL":[], "WEBSITE":[],
                "ADDRESS":[], "PINCODE":[]}
  
  # Appending Text to Categories (category 1-Name,category 2-Destination)
  extrd_dict["NAME"].append(texts[0])
  extrd_dict["DESIGNATION"].append(texts[1])
  
  # Loop through texts starting from the third element
  for i in range(2,len(texts)):
    
    # Check for Contact Information
    if texts[i].startswith("+") or (texts[i].replace("-","").isdigit() and '-' in texts[i]):

      extrd_dict["CONTACT"].append(texts[i])
    
    #Check for Email
    elif "@" in texts[i] and ".com" in texts[i]:
      extrd_dict["EMAIL"].append(texts[i])
    
    #Check for Website
    elif "WWW" in texts[i] or "www" in texts[i] or "Www" in texts[i] or "wWw" in texts[i] or "wwW" in texts[i]:
      small= texts[i].lower()
      extrd_dict["WEBSITE"].append(small)
    
    # Check for Pincode or State Name
    elif "Tamil Nadu" in texts[i] or "TamilNadu" in texts[i] or texts[i].isdigit():
      extrd_dict["PINCODE"].append(texts[i])
    
    # Check for Company Name
    elif re.match(r'^[A-Za-z]', texts[i]):
      extrd_dict["COMPANY_NAME"].append(texts[i])
    
    #  Fallback to Address
    else:
      remove_colon= re.sub(r'[,;]','',texts[i])
      extrd_dict["ADDRESS"].append(remove_colon)


  # Iterate Over extrd_dict Items
  for key,value in extrd_dict.items():

    # Concatenate Values and Update Dictionary
    if len(value)>0:
      concadenate= " ".join(value)
      extrd_dict[key] = [concadenate]
    
    #Handle Empty Categories
    else:
      value = "NA"
      extrd_dict[key] = [value]

  # Return the Final Dictionary
  return extrd_dict

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

# UPLOAD AND EXTRACT MENU

if selected == "Upload & Extract":

  #File Upload Prompt
  img = st.file_uploader("Upload the Image", type= ["png","jpg","jpeg"])

  if img is not None:
    # Display Uploaded Image
    st.image(img, width= 300)

    #Image Processing
    text_image, input_img= image_to_text(img)
    
    #Extracted Text Processing
    text_dict = extracted_text(text_image)

    if text_dict:
      st.success("TEXT IS EXTRACTED SUCCESSFULLY")
    
    # Display Extracted Information
    df= pd.DataFrame(text_dict)


    #Converting Image to Bytes

    Image_bytes = io.BytesIO()
    input_img.save(Image_bytes, format= "PNG")
    image_data = Image_bytes.getvalue()

    #Creating DataFrame for Image Data
    data = {"IMAGE":[image_data]}
    df_1 = pd.DataFrame(data)
   
    #Concatenate DataFrames
    concat_df = pd.concat([df,df_1],axis= 1)

    st.dataframe(concat_df)
    
    # Save Button
    button_1 = st.button("Save", use_container_width = True)

    if button_1:
        # Database Operations:Connection Establishment
        mydb = psycopg2.connect(host="localhost",
                                    user="postgres",
                                    password="2112",
                                    database= "bizcardx",
                                    port = "5432"
                                    )

        cursor = mydb.cursor()
      #Table Creation

        create_table_query = '''CREATE TABLE IF NOT EXISTS bizcard_details(name varchar(225),
                                                                            designation varchar(225),
                                                                            company_name varchar(225),
                                                                            contact varchar(225),
                                                                            email varchar(225),
                                                                            website text,
                                                                            address text,
                                                                            pincode varchar(225),
                                                                            image text)'''

        cursor.execute(create_table_query)
        mydb.commit()

        # Insert Query

        insert_query = '''INSERT INTO bizcard_details(name, designation, company_name,contact, email, website, address,
                                                        pincode, image)

                                                        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)'''

        datas = concat_df.values.tolist()[0]
        cursor.execute(insert_query,datas)
        mydb.commit()
        
        # Success Message
        st.success("SAVED SUCCESSFULLY")


# Selection of Method-Modify,Preview
if selected == "Modify":
    method=st.selectbox("Select the method",['Preview','Modify'])
    
    # Preview Method
    if method=="Preview":

      # Connect to the PostgreSQL database
      mydb = psycopg2.connect(host="localhost",
                                    user="postgres",
                                    password="2112",
                                    database= "bizcardx",
                                    port = "5432"
                                    )

      cursor = mydb.cursor()

     #SELECT query to fetch all records from the 'bizcard_details' table
      select_query = "SELECT * FROM bizcard_details"

      cursor.execute(select_query)
      table = cursor.fetchall()
      mydb.commit()
      
       # Display the fetched records as a DataFrame
      table_df = pd.DataFrame(table, columns=("NAME", "DESIGNATION", "COMPANY_NAME", "CONTACT", "EMAIL", "WEBSITE",
                                            "ADDRESS", "PINCODE", "IMAGE"))
      st.dataframe(table_df)

    # Modify Method
    if method == "Modify":
        # PostgreSQL database-Connection
        mydb = psycopg2.connect(host="localhost",
                                        user="postgres",
                                        password="2112",
                                        database= "bizcardx",
                                        port = "5432"
                                        )

        cursor = mydb.cursor()

        #SELECT query to fetch all records from the 'bizcard_details' table
        select_query = "SELECT * FROM bizcard_details"

        cursor.execute(select_query)
        table = cursor.fetchall()
        mydb.commit()
        
        # Display the fetched records as a DataFrame
        table_df = pd.DataFrame(table, columns=("NAME", "DESIGNATION", "COMPANY_NAME", "CONTACT", "EMAIL", "WEBSITE",
                                                "ADDRESS", "PINCODE", "IMAGE"))

        col1,col2 = st.columns(2)
        with col1:
            # Allow the user to select a name from the fetched records
            selected_name = st.selectbox("Select the name", table_df["NAME"])

        df_3 = table_df[table_df["NAME"] == selected_name]
        st.dataframe(df_3)

        df_4 = df_3.copy()
        

        # Display the details of the selected record and provide input fields to modify them
        col1,col2 = st.columns(2)
        with col1:
         mo_name = st.text_input("Name", df_3["NAME"].unique()[0])
         mo_desi = st.text_input("Designation", df_3["DESIGNATION"].unique()[0])
         mo_com_name = st.text_input("Company_name", df_3["COMPANY_NAME"].unique()[0])
         mo_contact = st.text_input("Contact", df_3["CONTACT"].unique()[0])
         mo_email = st.text_input("Email", df_3["EMAIL"].unique()[0])

         df_4["NAME"] = mo_name
         df_4["DESIGNATION"] = mo_desi
         df_4["COMPANY_NAME"] = mo_com_name
         df_4["CONTACT"] = mo_contact
         df_4["EMAIL"] = mo_email

        with col2:
      
            mo_website = st.text_input("Website", df_3["WEBSITE"].unique()[0])
            mo_addre = st.text_input("Address", df_3["ADDRESS"].unique()[0])
            mo_pincode = st.text_input("Pincode", df_3["PINCODE"].unique()[0])
            mo_image = st.text_input("Image", df_3["IMAGE"].unique()[0])

            df_4["WEBSITE"] = mo_website
            df_4["ADDRESS"] = mo_addre
            df_4["PINCODE"] = mo_pincode
            df_4["IMAGE"] = mo_image
            
            # Update the modified record in the DataFrame
            st.dataframe(df_4)

        col1,col2= st.columns(2)
        with col1:
            button_3 = st.button("Modify", use_container_width = True)

        if button_3:

            mydb = psycopg2.connect(host="localhost",
                                            user="postgres",
                                            password="2112",
                                            database= "bizcardx",
                                            port = "5432"
                                            )

            cursor = mydb.cursor()
             
            # Delete the existing record corresponding to the selected name from the database
            cursor.execute(f"DELETE FROM bizcard_details WHERE NAME = '{selected_name}'")
            mydb.commit()

       
            # Insert the modified record into the database
            insert_query = '''INSERT INTO bizcard_details(name, designation, company_name,contact, email, website, address,
                                                            pincode, image)

                                                            VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)'''

            datas = df_4.values.tolist()[0]
            cursor.execute(insert_query,datas)
            mydb.commit()
            
             # Display a success message indicating the modification was successful
            st.success("MODIFYED SUCCESSFULLY")

if selected == "Delete":
  
  # Connection to the Database
  mydb = psycopg2.connect(host="localhost",
                                    user="postgres",
                                    password="2112",
                                    database= "bizcardx",
                                    port = "5432"
                                    )

  cursor = mydb.cursor()

  col1,col2 = st.columns(2)
  with col1:
    
    # User Input - Selecting Name:
    select_query = "SELECT NAME FROM bizcard_details"

    cursor.execute(select_query)
    table1 = cursor.fetchall()
    mydb.commit()

    names = []

    for i in table1:
      names.append(i[0])

    name_select = st.selectbox("Select the name", names)

  with col2:
    # Filtering - Selecting Designation
    select_query = f"SELECT DESIGNATION FROM bizcard_details WHERE NAME ='{name_select}'"

    cursor.execute(select_query)
    table2 = cursor.fetchall()
    mydb.commit()

    designations = []

    for j in table2:
      designations.append(j[0])

    designation_select = st.selectbox("Select the designation", options = designations)
  
  # Confirmation and Deletion
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
