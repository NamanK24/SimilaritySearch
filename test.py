import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from rapidfuzz import fuzz, process
import numpy as np

def calculate_name_similarity(name1, name2):
    """Calculate similarity between two names using fuzzy matching"""
    if pd.isna(name1) or pd.isna(name2):
        return 0
    return fuzz.ratio(str(name1).lower(), str(name2).lower())

def calculate_date_proximity(date1, date2):
    """Calculate how close two dates are to each other"""
    try:
        d1 = pd.to_datetime(date1)
        d2 = pd.to_datetime(date2)
        difference = abs((d1 - d2).days)
  
        if difference <= 30:
            return 100 - (difference * (100/30))
        return 0
    except:
        return 0

def search_patterns(df, fname, lname, dob, threshold=60):
    """
    Search for patterns in the dataset using fuzzy matching
    Returns exact and similar matches
    """
    
    df['fname_similarity'] = df['Fname'].apply(lambda x: calculate_name_similarity(x, fname))
    df['lname_similarity'] = df['Lname'].apply(lambda x: calculate_name_similarity(x, lname))
    df['dob_proximity'] = df['DOB'].apply(lambda x: calculate_date_proximity(x, dob))
    

    df['total_similarity'] = (
        df['fname_similarity'] * 0.4 + 
        df['lname_similarity'] * 0.4 + 
        df['dob_proximity'] * 0.2
    )
    
    
    exact_matches = df[
        (df['fname_similarity'] >= 95) & 
        (df['lname_similarity'] >= 95) & 
        (df['dob_proximity'] >= 95)
    ].copy()
    
  
    similar_matches = df[
        (df['total_similarity'] >= threshold) & 
        ~df.index.isin(exact_matches.index)
    ].copy()
    
    return exact_matches, similar_matches

def main():
    st.title("Pattern Search Application")
    
    
    uploaded_file = st.file_uploader("Upload your CSV file", type=['csv'])
    
    if uploaded_file is not None:
      
        try:
            df = pd.read_csv(uploaded_file)
            required_columns = ['Fname', 'Lname', 'DOB']
            
            # Check if required columns exist
            if not all(col in df.columns for col in required_columns):
                st.error("CSV must contain columns: Fname, Lname, DOB")
                return
            
            # Display sample of the uploaded data
            st.subheader("Sample of uploaded data:")
            st.dataframe(df.head())
            
            # Search inputs
            col1, col2, col3 = st.columns(3)
            with col1:
                search_fname = st.text_input("First Name")
            with col2:
                search_lname = st.text_input("Last Name")
            with col3:
                search_dob = st.date_input("Date of Birth")
            
            similarity_threshold = st.slider(
                "Similarity Threshold (%)", 
                min_value=0, 
                max_value=100, 
                value=60
            )
            
            if st.button("Search"):
                if search_fname or search_lname:  # At least one name should be provided
                    # Convert date to string format matching the CSV
                    search_dob_str = search_dob.strftime('%Y-%m-%d')
                    
                    # Perform search
                    exact_matches, similar_matches = search_patterns(
                        df, 
                        search_fname, 
                        search_lname, 
                        search_dob_str,
                        similarity_threshold
                    )
                    
                    # Display results
                    st.subheader("Exact Matches")
                    if len(exact_matches) > 0:
                        results_df = exact_matches[['Fname', 'Lname', 'DOB', 'total_similarity']]
                        results_df['Match Score'] = results_df['total_similarity'].round(2)
                        st.dataframe(results_df.drop('total_similarity', axis=1))
                    else:
                        st.write("No exact matches found.")
                    
                    st.subheader("Similar Matches")
                    if len(similar_matches) > 0:
                        results_df = similar_matches[['Fname', 'Lname', 'DOB', 'total_similarity']]
                        results_df['Match Score'] = results_df['total_similarity'].round(2)
                        # Sort by similarity score
                        results_df = results_df.sort_values('Match Score', ascending=False)
                        st.dataframe(results_df.drop('total_similarity', axis=1))
                    else:
                        st.write("No similar matches found.")
                else:
                    st.warning("Please enter at least one name to search.")
                    
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
    else:
        st.info("Please upload a CSV file to begin.")
        

if __name__ == "__main__":
    main()