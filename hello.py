import streamlit as st
import pandas as pd
import sqlite3

# Connect to DB
conn = sqlite3.connect("brickviews_realestate.db", check_same_thread=False)
#conn = sqlite3.connect("brickview.db", check_same_thread=False)
conn.execute("PRAGMA journal_mode=WAL;")

# create cursor
cursor = conn.cursor()

st.title("🏠 BrickView Real Estate Intelligence")

# Create tabs for the 5 filters
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Introduction", "Filter & Explorer", "Visualizations", "CURD Operation", "SQL Queries"]
)

# 1. Introduction
with tab1:
    st.header("Introduction")
    st.write("Welcome to BrickView — Real Estate Intelligence Platform.")
    #st.write("Explore buyers, investors, loans, and property insights interactively.")

# 2. Filter & Explorer
with tab2:
    st.header("Filter & Explorer")
    city = st.selectbox("Select City", ["Los Angeles", "Chicago", "Houston"])
    property_types = st.multiselect("Property Type", ["Apartment", "Condo", "House", "Townhouse"])
    price_range = st.slider("Price Range", 500000, 5000000, (1000000, 3000000))

    # Get agents dynamically from DB
    agents_df = pd.read_sql("SELECT Agent_ID, Name FROM agents;", conn)
    #st.write(agents_df.column)
    # Add "ALL" option
    agent_options = ["ALL"] + agents_df["Agent_ID"].tolist()
    agent = st.selectbox("Select Agent", agent_options)
    
    #agent = st.selectbox("Select Agent", ["A0047", "A0048", "A0049", "A0050"])  # Example IDs

    date_range = st.date_input("Listed From / Listed To", [])

    # Build query dynamically
    query = f"""
    SELECT l.city, l.property_type, l.price, l.date_listed, a.name AS agent_name,b.buyer_type
    FROM listings l
    JOIN buyers b ON l.listing_id = b.sale_id
    JOIN agents a ON l.agent_id = a.agent_id
    WHERE l.city = '{city}'
    AND l.property_type IN ({','.join([f"'{pt}'" for pt in property_types])})
    AND l.price BETWEEN {price_range[0]} AND {price_range[1]}
    AND a.agent_id = '{agent}'
    """
    # Only filter by agent if not "ALL"
    if agent != "ALL":
        query += f" AND a.agent_id = '{agent}'"

    # Add date filter if selected
    if len(date_range) == 2:
        query += f" AND l.date_listed BETWEEN '{date_range[0]}' AND '{date_range[1]}'"

    df = pd.read_sql(query, conn)

    st.subheader("Filtered Results")
    st.dataframe(df)

# 3. Visualizations
with tab3:
    st.header("Visualizations")
    query1 = """
    SELECT buyer_type,
           ROUND(COUNT() * 100.0 / (SELECT COUNT() FROM buyers), 2) AS percentage
    FROM buyers
    WHERE buyer_type IN ('Investor', 'End User')
    GROUP BY buyer_type;
    """
    df1 = pd.read_sql(query1, conn)
    st.subheader("Buyer Type Distribution")
    st.bar_chart(df1.set_index("buyer_type"))

    query2 = """select Property_Type, count(*) AS Property_count, AVG(Sqft) as avg_sqft
    from listings
    where Property_Type IN ('House', 'Townhouse','Apartment')
    group by Property_Type; """
 
    df2 = pd.read_sql(query2,conn)
    st.subheader("Property Type Distribution")
    #pie chart using ploty
    import plotly.express as px
    fig = px.pie(df2, values = "Property_count", names="Property_Type",
                title = "property count by Type")
    st.plotly_chart(fig) 

    query3 = """
    SELECT City, AVG(price) AS avg_price
    FROM listings
    GROUP BY City;"""
    df3 = pd.read_sql(query3, conn)

    st.subheader("Average Price per City")
    st.line_chart(df3.set_index("City"))

# 4. CURD Operation
with tab4:
    st.header("CURD Operation")
    st.write("Perform Create, Update, Read, Delete operations here.")

    # Step 1: Select table
    tables = ["listings", "property_attributes", "agents", "sales", "buyers"]
    selected_table = st.selectbox("Select a table:", tables)

    # Step 2: Select CRUD option
    crud_option = st.radio("Choose an operation:", ["View", "Add", "Update", "Delete"])

    # VIEW → show all rows
    if crud_option == "View":
      df = pd.read_sql(f"SELECT * FROM {selected_table}", conn)
      st.dataframe(df)

    # ADD → show form with column names
    elif crud_option == "Add" and selected_table == "listings":
        # Form must wrap all inputs + sumbit button
        with st.form("add_listing"):
            new_id = st.text_input("Listing_ID")
            city = st.text_input("City")
            property_type = st.text_input("Property_Type")
            price = st.number_input("Price", min_value=0.0)
            size = st.number_input("Size (Sqft)", min_value=0)
            date_listed = st.date_input("Date_Listed")
            agent_id = st.text_input("Agent_ID")
            latitude = st.number_input("Latitude")
            longitude = st.number_input("Longitude")
            #submit button inside the form
            submitted = st.form_submit_button("Insert Record")

        if submitted:
            cursor.execute("""
                INSERT INTO listings (Listing_ID, City, Property_Type, Price, Sqft, Date_Listed, Agent_ID, Latitude, Longitude)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (new_id, city, property_type, price, size, date_listed, agent_id, latitude, longitude))
            conn.commit()
            st.success("New listing added successfully!")

    elif crud_option == "Add" and selected_table == "property_attributes":
            # Form must wrap all inputs + sumbit button
            with st.form("add_listing"):
                new_id = st.text_input("attribute_id")
                listing_id = st.text_input("listing_id")
                bedrooms = st.number_input("bedrooms", min_value=0)
                bathrooms = st.number_input("bathrooms", min_value=0)
                floor_number = st.number_input("floor_number", min_value=0)
                total_floors = st.number_input("total_floors", min_value=0)
                year_built = st.text_input("year_built")
                is_rented = st.text_input("is_rented")
                tenant_count = st.text_input("tenant_count")
                furnishing_status = st.text_input("furnishing_status")
                metro_distance_km = st.number_input("metro_distance_km",min_value=0.0 )
                parking_available = st.text_input("parking_available")
                power_backup = st.text_input("power_backup")
                                
                submitted = st.form_submit_button("Insert Record")
    
            if submitted:
                cursor.execute("""
                    INSERT INTO listings (attribute_id, listing_id, bedrooms, bathrooms, floor_number, total_floors, year_built, is_rented, tenant_count, furnishing_status, metro_distance_km,parking_available,power_backup)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ? ,?, ?, ?, ?)
                """, (new_id, listing_id , bedrooms , bathrooms , floor_number, total_floors , year_built , is_rented, tenant_count, furnishing_status, metro_distance_km, parking_available, power_backup))
                conn.commit()
                st.success("New listing added successfully!")        

    elif crud_option == "Add" and selected_table == "agents":
            # Form must wrap all inputs + sumbit button
            with st.form("add_listing"):
                new_id = st.text_input("Agent_ID")
                Name = st.text_input("Name")
                Phone = st.text_input("Phone")
                Email = st.text_input("Email")
                commission_rate = st.number_input("commission_rate")
                deals_closed = st.number_input("deals_closed")
                rating = st.number_input("rating",min_value=0.0, max_value=0.0)
                experience_years = st.number_input("experience_years",min_value=0, step=1)
                avg_closing_days = st.number_input("avg_closing_days",min_value=0, step=1)
                                                
                submitted = st.form_submit_button("Insert Record")
    
            if submitted:
                cursor.execute("""
                    INSERT INTO listings (Agent_ID, Name, Phone, Email, commission_rate, deals_closed, rating, experience_years, avg_closing_days)                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ? ,?, ?, ?, ?)
                """, (new_id, Name , Phone , Email , commission_rate, deals_closed , rating , experience_years, avg_closing_days))
                conn.commit()
                st.success("New listing added successfully!")

    elif crud_option == "Add" and selected_table == "sales":
            # Form must wrap all inputs + sumbit button
            with st.form("add_listing"):
                new_id = st.text_input("Listing_ID")
                Sale_Price = st.number_input("Sale_Price", min_value =0.0)
                Date_Sold = st.date_input("Date_Sold")
                Days_on_Market = st.number_input("Days_on_Market")
                                                               
                submitted = st.form_submit_button("Insert Record")
    
            if submitted:
                cursor.execute("""
                    INSERT INTO listings (Listing_ID, Sale_Price, Date_Sold, Days_on_Market)
					VALUES (?, ?, ?, ?)
                """, (new_id, Sale_Price , Date_Sold , Days_on_Market ))
                conn.commit()
                st.success("New listing added successfully!")
				
    elif crud_option == "Add" and selected_table == "buyers":
            # Form must wrap all inputs + sumbit button
            with st.form("add_listing"):
                new_id = st.text_input("buyer_id")
                sale_id = st.text_input("sale_id")
                buyer_type = st.text_input("buyer_type")
                payment_mode = st.text_input("payment_mode")
                loan_taken = st.text_input("loan_taken")
                loan_provider = st.text_input("loan_provider")
                loan_amount = st.number_input("loan_amount")
                                                               
                submitted = st.form_submit_button("Insert Record")
    
            if submitted:
                cursor.execute("""
                    INSERT INTO listings (buyer_id, sale_id, buyer_type, payment_mode,loan_taken,loan_provider,loan_amount)
					VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (new_id, sale_id , buyer_type , payment_mode ,loan_taken,loan_provider,loan_amount))
                conn.commit()
                st.success("New listing added successfully!")

# UPDATE option
    if crud_option == "Update" and selected_table == "listings":
        # Step 1: Show existing records
        df = pd.read_sql("SELECT * FROM listings", conn)
        st.dataframe(df)

        # Step 2: Select record to update
        record_id = st.selectbox("Select Listing ID to update", df["Listing_ID"].tolist())

        # Step 3: Fetch old values for that record
        old_values = df[df["Listing_ID"] == record_id].iloc[0]

        # Step 4: Pre-fill form with old values
        new_city = st.text_input("City", value=old_values["City"])
        new_type = st.text_input("Property Type", value=old_values["Property_Type"])
        new_price = st.number_input("New Price",value=float(old_values["Price"]))
        new_size = st.number_input("New Size (sqft)",value=int(old_values["Sqft"]))

        # Step 4: Update button
        if st.button("Update Record"):
            cursor.execute("""
                UPDATE listings
                SET City = ?, Property_Type = ?, Price = ?, Sqft = ?
                WHERE Listing_ID = ?
                """, (new_city, new_type, new_price, new_size, record_id))
            conn.commit()
            st.success(f"Listing {record_id} updated successfully!")
        # Refresh the table view
        #df = pd.read_sql("SELECT * FROM listings", conn)
        #st.dataframe(df)

    if crud_option == "Update" and selected_table == "property_attributes":
        # Step 1: Show existing records
        df = pd.read_sql("SELECT * FROM property_attributes", conn)
        st.dataframe(df)
        # Column lowercase issue this one table only so we can rename the datafram column name 
        id_column = "listing_id" if "listing_id" in df.columns else "Listing_ID"
        record_id = st.selectbox("Select Listing ID to update", df[id_column].tolist())

        # Step 2: Select record to update
        #record_id = st.selectbox("Select Listing ID to update", df["listing_id"].tolist())

        # Step 3: Fetch old values for that record
        old_values = df[df["listing_id"] == record_id].iloc[0]

        # Step 4: Pre-fill form with old values
        new_bedrooms = st.number_input("Bedrooms", value=old_values["bedrooms"])
        new_bathrooms = st.number_input("Bathrooms Type", value=old_values["bathrooms"])
        new_metro_distance_km = st.number_input("New Metro distance",value=float(old_values["metro_distance_km"]))

        # Step 4: Update button
        if st.button("Update Record"):
            cursor.execute("""
                UPDATE property_attributes
                SET bedrooms = ?, bathrooms = ?, metro_distance_km = ?
                WHERE listing_id = ?
                """, (new_bedrooms, new_bathrooms, new_metro_distance_km,record_id))
            conn.commit()
            st.success(f"Listing {record_id} updated successfully!")

    if crud_option == "Update" and selected_table == "agents":
        # Step 1: Show existing records
        df = pd.read_sql("SELECT * FROM agents", conn)
        st.dataframe(df)

        # Step 2: Select record to update
        record_id = st.selectbox("Select Listing ID to update", df["Agent_ID"].tolist())

        # Step 3: Fetch old values for that record
        old_values = df[df["Agent_ID"] == record_id].iloc[0]

        # Step 4: Pre-fill form with old values
        new_Phone = st.text_input("Phone", value=old_values["Phone"])
        new_Email = st.text_input("Email", value=old_values["Email"])
        new_commission_rate = st.number_input("commission_rate",value=float(old_values["commission_rate"]))

        # Step 4: Update button
        if st.button("Update Record"):
            cursor.execute("""
                UPDATE agents
                SET Phone = ?, Email = ?, commission_rate = ?
                WHERE Agent_ID = ?
                """, (new_Phone, new_Email, new_commission_rate,record_id))
            conn.commit()
            st.success(f"Listing {record_id} updated successfully!")
        # Refresh the table view
        #df = pd.read_sql("SELECT * FROM agents", conn)
        #st.dataframe(df)

    if crud_option == "Update" and selected_table == "sales":
        # Step 1: Show existing records
        df = pd.read_sql("SELECT * FROM sales", conn)
        st.dataframe(df)

        # Step 2: Select record to update
        record_id = st.selectbox("Select Listing ID to update", df["Listing_ID"].tolist())

        # Step 3: Fetch old values for that record
        old_values = df[df["Listing_ID"] == record_id].iloc[0]

        # Step 4: Pre-fill form with old values
        new_Sale_Price = st.number_input("Sale_Price", value=float(old_values["Sale_Price"]))
        new_Date_Sold = st.date_input("Date_Sold", value=old_values["Date_Sold"])
        new_Days_on_Market = st.number_input("Days_on_Market",value=float(old_values["Days_on_Market"]))

            # Step 4: Update button
        if st.button("Update Record"):
                cursor.execute("""
                    UPDATE sales
                    SET Sale_Price = ?, Date_Sold = ?, Days_on_Market = ?
                    WHERE Listing_ID = ?
                    """, (new_Sale_Price, new_Date_Sold, new_Days_on_Market,record_id))
                conn.commit()
                st.success(f"Listing {record_id} updated successfully!")
        # Refresh the table view
        #df = pd.read_sql("SELECT * FROM sales", conn)
        #st.dataframe(df)

    if crud_option == "Update" and selected_table == "buyers":
        # Step 1: Show existing records
        df = pd.read_sql("SELECT * FROM buyers", conn)
        st.dataframe(df)

        # Step 2: Select record to update
        record_id = st.selectbox("Select Buyer ID to update", df["buyer_id"].tolist())

        # Step 3: Fetch old values for that record
        old_values = df[df["buyer_id"] == record_id].iloc[0]

        # Step 4: Pre-fill form with old values
        new_sale_id = st.text_input("sale_id", value=old_values["sale_id"])
        new_buyer_type = st.text_input("buyer_type", value=old_values["buyer_type"])
        new_loan_amount = st.number_input("loan_amount",value=float(old_values["loan_amount"]))

        # Step 4: Update button
        if st.button("Update Record"):
            cursor.execute("""
                UPDATE buyers
                SET sale_id = ?, buyer_type = ?, loan_amount = ?
                WHERE buyer_id = ?
                """, (new_sale_id, new_buyer_type, new_loan_amount,record_id))
            conn.commit()
            st.success(f"Listing {record_id} updated successfully!")
        # Refresh the table view
        #df = pd.read_sql("SELECT * FROM buyers", conn)
        #st.dataframe(df)

#DELETION PART
    if crud_option == "Delete" and selected_table == "listings":
        # Step 1: Show existing records
        df = pd.read_sql("SELECT * FROM listings", conn)
        st.dataframe(df)

        # Step 2: Select record to update
        record_id = st.selectbox("Select ID to update", df["Listing_ID"].tolist())

        # Step 3: Fetch old values for that record
        #old_values = df[df["Listing_ID"] == record_id].iloc[0]

        # Step 4: Delete button
        if st.button("Delete Record"):
            cursor.execute("""
                Delete from listings
                WHERE Listing_ID = ?
                """, [record_id])
            conn.commit()
            st.success(f"Listing {record_id} Delete successfully!")
    
    if crud_option == "Delete" and selected_table == "property_attributes":
        # Step 1: Show existing records
        df = pd.read_sql("SELECT * FROM property_attributes", conn)
        st.dataframe(df)

        # Step 2: Select record to Delete
        record_id = st.selectbox("Select ID to Delete", df["listing_id"].tolist())

        # Step 3: Fetch old values for that record
        old_values = df[df["listing_id"] == record_id].iloc[0]

        # Step 4: Delete button
        if st.button("Delete Record"):
            cursor.execute("""
                Delete from property_attributes
                WHERE listing_id = ?
                """, [record_id])
            conn.commit()
            st.success(f"Listing {record_id} Deleted successfully!")
               
    if crud_option == "Delete" and selected_table == "agents":
        # Step 1: Show existing records
        df = pd.read_sql("SELECT * FROM agents", conn)
        st.dataframe(df)

        # Step 2: Select record to Delete
        record_id = st.selectbox("Select ID to Delete", df["Agent_ID"].tolist())

        # Step 3: Fetch old values for that record
        old_values = df[df["Agent_ID"] == record_id].iloc[0]

        # Step 4: Delete button
        if st.button("Delete Record"):
            cursor.execute("""
                Delete from agents
                WHERE Agent_ID = ?
                """, [record_id])
            conn.commit()
            st.success(f"Listing {record_id} Deleted successfully!")
            
    if crud_option == "Delete" and selected_table == "sales":
        # Step 1: Show existing records
        df = pd.read_sql("SELECT * FROM sales", conn)
        st.dataframe(df)

        # Step 2: Select record to Delete
        record_id = st.selectbox("Select ID to Delete", df["Listing_ID"].tolist())

        # Step 3: Fetch old values for that record
        old_values = df[df["Listing_ID"] == record_id].iloc[0]

        # Step 4: Delete button
        if st.button("Delete Record"):
            cursor.execute("""
                Delete from sales
                WHERE Listing_ID = ?
                """, [record_id])
            conn.commit()
            st.success(f"Listing {record_id} Deleted successfully!")   

    if crud_option == "Delete" and selected_table == "buyers":
        # Step 1: Show existing records
        df = pd.read_sql("SELECT * FROM buyers", conn)
        st.dataframe(df)

        # Step 2: Select record to Delete
        record_id = st.selectbox("Select ID to Delete", df["buyer_id"].tolist())

        # Step 3: Fetch old values for that record
        old_values = df[df["buyer_id"] == record_id].iloc[0]

        # Step 4: Delete button
        if st.button("Delete Record"):
            cursor.execute("""
                Delete from buyers
                WHERE buyer_id = ?
                """, [record_id])
            conn.commit()
            st.success(f"Listing {record_id} Deleted successfully!")            
# 5. SQL Queries
with tab5:
    st.header("SQL Queries")
    # Step 1: Define analysis questions
    questions = {
        "Average listing price by city?": "select city, AVG(price) as avg_price from listings group by city",
        "Average price per square foot by property type?": "Select Property_Type, AVG(Sqft) as avg_sqft from listings group by Property_Type",
        "Which cities have the highest average property prices?": " select city, avg(price) as avg_price from listings group by city order by avg_price DESC",
        "Which property types sell the fastest?": """
             SELECT l.Property_Type,COUNT(*) AS property_count,ROUND(AVG(s.Days_on_Market), 2) AS avg_days_on_market FROM listings l
             JOIN sales s 
             ON l.Listing_ID = s.Listing_ID
             GROUP BY l.Property_Type
             ORDER BY avg_days_on_market ASC """,
        "Which listings took more than 90 days to sell?": """
             SELECT l.City,l.Property_Type,l.Date_Listed,s.Date_Sold,JULIANDAY(s.Date_Sold) - JULIANDAY(l.Date_Listed) AS days_between
             FROM listings l
             JOIN sales s 
              ON l.Listing_ID = s.Listing_ID
             WHERE JULIANDAY(s.Date_Sold) - JULIANDAY(l.Date_Listed) > 90
             ORDER BY days_between DESC """
        }

    # Step 2: Show questions as radio buttons
    selected_question = st.radio("Choose a query:", list(questions.keys()))

    # Step 3: Run query only when button clicked
    if st.button("Run Query"):
        query = questions[selected_question]
        df = pd.read_sql(query, conn)
        st.dataframe(df)